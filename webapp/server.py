# ==========================
# webapp/server.py
# MINI APP - BACKEND (Flask)
# ==========================
#
# Telegram Mini App uchun API. Har bir so'rov "initData"
# bilan keladi va HMAC orqali tekshiriladi - shuning uchun
# soxta so'rov bilan boshqa odamning ma'lumotini olib
# bo'lmaydi.
#
# Uchta rol bor: parent (ota-ona), teacher (o'qituvchi),
# admin (direktor). Rol Telegram ID orqali avtomatik
# aniqlanadi - foydalanuvchi tanlamaydi.
#
# ==========================


import os
import sys
from datetime import datetime

sys.path.insert(
    0,
    os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))
    )
)

from flask import Flask, request, jsonify, send_from_directory

import telebot

from config import TOKEN, ADMIN_IDS

from webapp.auth import validate_init_data

from services.group_capacity import notify_if_overcapacity

from data.curriculum import department_subjects, subject_has_concertmaster

# Faqat xabar yuborish uchun - long-polling yo'q, shuning uchun
# asosiy bot (main.py) bilan "409 Conflict" bermaydi.
_notify_bot = telebot.TeleBot(TOKEN, threaded=False)

from database import (
    get_school_name,
    get_parent,
    get_parent_students_with_id,
    get_parent_student_link,
    get_student_info,
    get_department_for_teacher,
    get_student_payment_history,
    get_student_full_schedule,

    find_teacher_binding,
    get_departments,
    get_teachers_by_department,
    get_teacher_by_id,
    slot_allows_concertmaster,
    set_view_as,
    get_view_as,
    clear_view_as,

    DAYS_OF_WEEK,
    get_teacher_slots,
    get_slot,
    get_slot_students,
    get_slot_concertmasters,
    add_concertmaster,
    remove_concertmaster,
    get_subjects_for_teacher,
    get_own_subjects,
    get_subject,
    get_concertmaster_slots,
    can,
    get_teacher_permissions,
    get_audit_log,
    log_action,
    get_archived_students,
    restore_student,
    normalize_time,
    ACADEMIC_HOURS,
    hours_label,
    hours_to_minutes,
    available_lesson_times,
    get_slot_duration,
    find_room_conflict,
    get_room_availability,
    get_rooms,
    get_room_codes,
    add_room,
    delete_room,
    find_teacher_conflict,
    find_student_conflict,
    get_subject_type,
    LESSON_TYPES,
    create_slot,
    delete_slot,
    add_student_to_slot,
    remove_slot_student,
    get_slot_student_row,
    search_students,
    get_slots_for_day,

    get_students,
    get_student_fee,
    FEE_PRIVILEGED,
    FEE_OPTIONS,
    CLASS_OPTIONS,
    add_student,
    find_metrika_duplicate,
    has_paid_this_month,

    get_monthly_debt_rows,
    get_staff_role,
    search_teachers_by_name
)


STATIC_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "static"
)

app = Flask(__name__, static_folder=STATIC_DIR)


# ==========================
# KUTILMAGAN XATOLAR - HAR DOIM JSON
# ==========================
#
# Standart Flask kutilmagan xatoda HTML 500 sahifasini qaytaradi.
# Frontend esa har doim JSON kutadi (api() funksiyasi javobni
# res.json() qiladi) - HTML kelsa parsing xatosi chiqadi va
# Mini App oq ekran bo'lib qotib qoladi, foydalanuvchi nima
# bo'lganini bilmay qoladi.
#
# Bu yerda xato serverning o'z logiga to'liq yoziladi (traceback
# bilan - shuning uchun sababi keyin topiladi), foydalanuvchiga esa
# oddiy JSON xato ketadi.


@app.errorhandler(Exception)
def _handle_unexpected_error(error):

    from werkzeug.exceptions import HTTPException

    if isinstance(error, HTTPException):
        return jsonify(error=error.description or "Xato"), error.code

    app.logger.exception("Kutilmagan xato: %s %s", request.method, request.path)

    return jsonify(error="Serverda kutilmagan xato yuz berdi. Qaytadan urinib ko'ring."), 500


# ==========================
# AUTENTIFIKATSIYA
# ==========================


def _authenticated_user():
    """
    So'rov header'idagi initData ni tekshiradi.
    Muvaffaqiyatli bo'lsa Telegram user dict, aks holda None.
    """

    init_data = (
        request.headers.get("X-Telegram-Init-Data")
        or request.args.get("init_data", "")
    )

    ok, result = validate_init_data(init_data, TOKEN)

    if not ok:
        return None

    return result


def _require_parent():

    user = _authenticated_user()

    if not user:
        return None, (jsonify(error="Ruxsat yo'q"), 401)

    parent = get_parent(user["id"])

    if not parent:
        return None, (jsonify(error="Ota-ona sifatida ro'yxatdan o'tmagansiz"), 403)

    return parent, None


def _viewed_teacher(user_id):
    """
    Admin "ko'rish rejimi"da bo'lsa - o'sha o'qituvchining ismi.

    Rejim botda tanlanadi va bazada saqlanadi (`db/view_as.py`),
    shuning uchun Mini App boshqa jarayon bo'lsa ham xuddi shu
    tanlovni ko'radi.
    """

    if not _is_director(user_id):
        return None

    return get_view_as(user_id)


def _require_teacher():
    """Muvaffaqiyatli bo'lsa (teacher_name, None), aks holda (None, xato_javob)."""

    user = _authenticated_user()

    if not user:
        return None, (jsonify(error="Ruxsat yo'q"), 401)

    binding = find_teacher_binding(user["id"])

    if binding:
        return binding[0], None

    # o'qituvchi emas, lekin admin uni "ko'rish rejimi"da ochgan

    viewed = _viewed_teacher(user["id"])

    if viewed:
        return viewed, None

    return None, (jsonify(error="Siz tasdiqlangan o'qituvchi emassiz"), 403)


def _is_director(user_id):
    """Admin yoki direktor - ikkalasi ham boshqaruv panelini ko'radi."""

    return user_id in ADMIN_IDS or get_staff_role(user_id) == "direktor"


def _require_admin():

    user = _authenticated_user()

    if not user or not _is_director(user["id"]):
        return None, (jsonify(error="Ruxsat yo'q"), 401)

    return user, None


def _require_superadmin():
    """
    Faqat haqiqiy admin (ADMIN_IDS). Direktor ham bu yerga
    kira olmaydi.

    O'zgarishlar tarixi va arxiv shu darajaga tegishli: ular
    kim nima qilganini ko'rsatadi, ya'ni xodimlar ustidan
    nazorat vositasi - bu faqat maktab rahbariyatining
    o'zida qolishi kerak.
    """

    user = _authenticated_user()

    if not user or user["id"] not in ADMIN_IDS:
        return None, (jsonify(error="Ruxsat yo'q"), 403)

    return user, None


# ==========================
# STATIK SAHIFA
# ==========================


@app.route("/")
def index():
    return send_from_directory(STATIC_DIR, "index.html")


@app.route("/<path:filename>")
def static_files(filename):
    return send_from_directory(STATIC_DIR, filename)


# ==========================
# API: KIM MEN? (rol aniqlash)
# ==========================


# Mini App sarlavhasida ko'rinadigan maktab nomi bazadan olinadi -
# kodda qattiq yozilmaydi, chunki bot bir nechta maktabda ishlaydi.


def _whoami_javob(**fields):

    fields.setdefault("school", get_school_name())

    return jsonify(**fields)


@app.route("/api/whoami")
def api_whoami():

    user = _authenticated_user()

    if not user:
        return jsonify(error="Ruxsat yo'q"), 401

    # Ko'rish rejimi admin panelidan ustun turadi: admin
    # o'qituvchini tanlagan bo'lsa - unga xuddi o'sha
    # o'qituvchining Mini App'i ochiladi.

    viewed = _viewed_teacher(user["id"])

    if viewed:
        return _whoami_javob(
            role="teacher",
            teacher=viewed,
            department=get_department_for_teacher(viewed),
            viewing_as=viewed
        )

    if user["id"] in ADMIN_IDS:
        return _whoami_javob(role="admin", is_admin=True)

    staff_role = get_staff_role(user["id"])

    if staff_role == "direktor":
        return _whoami_javob(role="admin", staff="direktor", is_admin=False)

    if staff_role:
        return _whoami_javob(role="staff", staff=staff_role)

    binding = find_teacher_binding(user["id"])

    if binding:
        return _whoami_javob(role="teacher", teacher=binding[0], department=binding[1])

    parent = get_parent(user["id"])

    if parent:
        return _whoami_javob(role="parent")

    return _whoami_javob(role=None)


# ==========================
# API: OTA-ONA - MENING FARZANDLARIM
# ==========================


@app.route("/api/me")
def api_me():

    parent, error = _require_parent()

    if error:
        return error

    children = [
        {"link_id": link_id, "student": student, "teacher": teacher}
        for link_id, teacher, student in get_parent_students_with_id(parent[0])
    ]

    return jsonify(parent_name=parent[2], children=children)


@app.route("/api/child/<int:link_id>")
def api_child(link_id):

    parent, error = _require_parent()

    if error:
        return error

    link = get_parent_student_link(link_id)

    if not link or link[1] != parent[0]:
        return jsonify(error="Topilmadi"), 404

    _, _, teacher, student = link

    info = get_student_info(student, teacher)

    if not info:
        return jsonify(error="O'quvchi ma'lumoti topilmadi"), 404

    department = get_department_for_teacher(teacher)

    payments = [
        {"month": m, "status": s, "amount": a, "date": d}
        for m, s, a, d in get_student_payment_history(teacher, student)
    ]

    schedule = _format_schedule(get_student_full_schedule(teacher, student))

    fee = info[6] if len(info) > 6 else 0

    privileged = (fee == FEE_PRIVILEGED)

    return jsonify(
        student=student,
        teacher=teacher,
        department=department,
        class_name=info[5],
        monthly_fee=0 if privileged else fee,
        privileged=privileged,
        payments=payments,
        schedule=schedule
    )


def _format_schedule(rows):

    return [
        {
            "subject": subject,
            "day": day,
            "time": time,
            "room": room,
            "teacher": slot_teacher,
            "concertmasters": get_slot_concertmasters(slot_id)
        }
        for subject, day, time, room, slot_teacher, slot_id in rows
    ]


# ==========================
# API: O'QITUVCHI - O'Z JADVALI
# ==========================


@app.route("/api/teacher/me")
def api_teacher_me():

    teacher, error = _require_teacher()

    if error:
        return error

    # Fanlar ro'yxati BOT BILAN BIR XIL manbadan olinadi:
    # 2026-reja, o'qituvchining bo'limi bo'yicha + o'zi qo'shganlari
    # (handlers/teacher_schedule.py dagi mantiq).
    #
    # Ilgari bu yerda faqat `get_subjects_for_teacher` turardi -
    # u umumiy 8 ta nomni qaytaradi ("Mutaxassislik", "Solfedjio"...).
    # Natijada Mini App'da rejadagi haqiqiy fan (masalan "Notani
    # varaqdan o'qish") umuman ko'rinmasdi va o'qituvchi uni qo'lda,
    # ko'pincha xato yozib qo'shishga majbur bo'lardi. Dars yaratish
    # tekshiruvi (api_teacher_create_slot) esa allaqachon rejani
    # qabul qilardi - ya'ni ro'yxatgina orqada qolgan edi.

    department = get_department_for_teacher(teacher)

    plan = [name for name, _ in department_subjects(department)]

    own = [row[1] for row in get_own_subjects(teacher)]

    names = plan + [n for n in own if n not in plan]

    if not names:
        names = [row[1] for row in get_subjects_for_teacher(teacher)]

    return jsonify(
        teacher=teacher,
        department=department,
        permissions=get_teacher_permissions(teacher),
        subjects=names,
        subject_types={name: get_subject_type(teacher, name) for name in names},
        lesson_types=LESSON_TYPES,
        days=DAYS_OF_WEEK,
        academic_hours=[
            {
                "hours": hours,
                "label": hours_label(hours),
                "minutes": hours_to_minutes(hours),
                "times": [
                    {"start": start, "end": end}
                    for start, end in
                    available_lesson_times(hours_to_minutes(hours))
                ]
            }
            for hours in ACADEMIC_HOURS
        ]
    )


# ==========================
# API: FANLAR - ENDI ADMINDA
# ==========================
#
# Ilgari o'qituvchi Mini App orqali o'ziga fan qo'sha, nomini
# o'zgartira va o'chira olardi. Amalda bu chalkashlik keltirdi:
# bitta fan bir necha xil yozilib ketdi va jadval reja bilan
# mos kelmay qoldi.
#
# Endi ro'yxat o'quv rejasidan keladi (/api/teacher/me), rejada
# yo'q fanni esa admin qo'shadi. Quyidagi manzillar ESKI ilova
# ochilib qolgan holat uchun qoldirilgan - 403 va tushunarli
# izoh qaytaradi, oq ekran bo'lmaydi.


_FAN_IZOHI = (
    "Fan qo'shish va tahrirlash administratorga o'tkazildi. "
    "Dars qo'shayotganda fanni ro'yxatdan tanlaysiz."
)


@app.route("/api/teacher/subjects", methods=["POST"])
def api_teacher_add_subject():

    return jsonify(error=_FAN_IZOHI), 403


@app.route("/api/teacher/subjects/<int:subject_id>", methods=["PATCH", "DELETE"])
def api_teacher_edit_subject(subject_id):

    return jsonify(error=_FAN_IZOHI), 403


@app.route("/api/teacher/subjects")
def api_teacher_subjects():
    """
    Bo'sh ro'yxat - eski ilova ochilib qolsa xato bermasin.
    Fan tanlash ro'yxati /api/teacher/me da keladi.
    """

    _teacher, error = _require_teacher()

    if error:
        return error

    return jsonify(subjects=[], moved=_FAN_IZOHI)


@app.route("/api/teacher/slots")
def api_teacher_slots():

    teacher, error = _require_teacher()

    if error:
        return error

    slots = []

    for slot_id, subject, day, time, room in get_teacher_slots(teacher):

        slots.append({
            "id": slot_id,
            "subject": subject,
            "lesson_type": get_subject_type(teacher, subject),
            "day": day,
            "time": time,
            "room": room,
            "student_count": len(get_slot_students(slot_id)),
            "concertmasters": get_slot_concertmasters(slot_id)
        })

    return jsonify(slots=slots)


@app.route("/api/teacher/rooms")
def api_teacher_rooms():
    """Tanlangan kun va vaqt uchun xonalar: qaysi biri bo'sh, qaysi biri band."""

    teacher, error = _require_teacher()

    if error:
        return error

    day = request.args.get("day")

    if day not in DAYS_OF_WEEK:
        return jsonify(error="Kun noto'g'ri"), 400

    time = normalize_time(request.args.get("time") or "")

    if not time:
        return jsonify(error="Soatni 15:00 ko'rinishida yozing"), 400

    try:
        hours = float(request.args.get("hours") or 1)

    except (TypeError, ValueError):
        return jsonify(error="Dars davomiyligi noto'g'ri"), 400

    if hours not in ACADEMIC_HOURS:
        return jsonify(error="Dars davomiyligi noto'g'ri"), 400

    return jsonify(rooms=get_room_availability(
        day, time, hours_to_minutes(hours)
    ))


# ==========================
# API: ADMIN - XONALAR
# ==========================


@app.route("/api/admin/rooms")
def api_admin_rooms():

    user, error = _require_admin()

    if error:
        return error

    return jsonify(rooms=get_rooms())


@app.route("/api/admin/rooms", methods=["POST"])
def api_admin_add_room():

    user, error = _require_admin()

    if error:
        return error

    data = request.get_json(silent=True) or {}

    ok, result = add_room(data.get("code"), data.get("name"))

    if not ok:
        return jsonify(error=result), 400

    log_action(
        str(user["id"]), "xona qo'shdi",
        result["label"], "Mini App", actor_role="admin"
    )

    return jsonify(room=result)


@app.route("/api/admin/rooms/<int:room_id>", methods=["DELETE"])
def api_admin_delete_room(room_id):

    user, error = _require_admin()

    if error:
        return error

    ok, result = delete_room(room_id)

    if not ok:
        return jsonify(error=result), 400

    log_action(
        str(user["id"]), "xonani o'chirdi",
        result["label"], "Mini App", actor_role="admin"
    )

    return jsonify(ok=True)


@app.route("/api/teacher/slots", methods=["POST"])
def api_teacher_create_slot():

    teacher, error = _require_teacher()

    if error:
        return error

    data = request.get_json(silent=True) or {}

    subject = data.get("subject")
    day = data.get("day")
    time = data.get("time")
    room = data.get("room")

    if not can(teacher, "can_manage_schedule"):
        return jsonify(error="Sizda dars jadvali tuzish huquqi yo'q"), 403

    # Ruxsat etilgan fanlar: 2026-reja (bo'lim bo'yicha) + o'zi
    # qo'shganlari + eski umumiy fanlar - botning fan tanlash
    # ro'yxati bilan bir xil manba (aks holda Mini App'da "Fan
    # noto'g'ri" chiqadi, botda esa xuddi shu fan tanlanaveradi).

    department = get_department_for_teacher(teacher)

    allowed = (
        {name for name, _ in department_subjects(department)}
        | {row[1] for row in get_subjects_for_teacher(teacher)}
    )

    if subject not in allowed:
        return jsonify(error="Fan noto'g'ri"), 400

    if day not in DAYS_OF_WEEK:
        return jsonify(error="Kun noto'g'ri"), 400

    if not time or not room:
        return jsonify(error="Soat va xona kiritilishi shart"), 400

    time = normalize_time(time)

    if not time:
        return jsonify(error="Soatni 15:00 ko'rinishida yozing"), 400

    room = room.strip()

    # xona qat'iy ro'yxatdan tanlanadi - qo'lda yozilmaydi

    if room not in get_room_codes():
        return jsonify(error="Bunday xona yo'q. Ro'yxatdan tanlang."), 400


    # davomiylik - akademik soatdan kelib chiqadi

    try:
        hours = float(data.get("hours") or 1)

    except (TypeError, ValueError):
        return jsonify(error="Dars davomiyligi noto'g'ri"), 400

    if hours not in ACADEMIC_HOURS:
        return jsonify(error="Dars davomiyligi noto'g'ri"), 400

    duration = hours_to_minutes(hours)


    # vaqt maktab jadvalidagi tayyor katakcha bo'lishi kerak -
    # tushlik ustidan yoki kun oxiridan oshib ketmasin

    allowed_times = [s for s, _ in available_lesson_times(duration)]

    if time not in allowed_times:
        return jsonify(error=(
            "Bu vaqtga " + hours_label(hours) + " dars sig'maydi. "
            "Mumkin bo'lgan vaqtlar: " + ", ".join(allowed_times)
        )), 400


    # o'qituvchi shu vaqtda band emasmi (o'z darsi yoki jo'rnavozligi)

    busy = find_teacher_conflict(teacher, day, time, duration)

    if busy:
        return jsonify(error=(
            "Siz " + day + " kuni " + time + " da bandsiz: "
            + busy[2] + " (" + busy[1] + ", " + busy[4] + "-xona)"
        )), 409


    # xonani bir vaqtda bitta dars egallaydi - qolganlar
    # o'sha darsga jo'rnavoz bo'lib qo'shiladi

    taken = find_room_conflict(day, time, room, duration)

    if taken:
        return jsonify(
            error=(
                room + "-xona " + day + " kuni " + taken[3] + " da band: "
                + taken[2] + " (" + taken[1] + ")."
                + (
                    " Shu darsda jo'rnavozlik qilmoqchi bo'lsangiz - "
                    "«Jo'rnavozligim» orqali biriktiriling."
                    if can(teacher, "can_be_concertmaster") else ""
                )
            ),
            conflict_slot_id=taken[0]
        ), 409

    slot_id = create_slot(teacher, subject, day, time, room, duration)

    return jsonify(id=slot_id)


def _own_slot_or_error(teacher, slot_id):
    """Slot shu o'qituvchiniki bo'lsa slot qatorini, aks holda xato javobini qaytaradi."""

    slot = get_slot(slot_id)

    if not slot or slot[1] != teacher:
        return None, (jsonify(error="Topilmadi"), 404)

    return slot, None


@app.route("/api/teacher/slots/<int:slot_id>")
def api_teacher_slot_detail(slot_id):

    teacher, error = _require_teacher()

    if error:
        return error

    slot, error = _own_slot_or_error(teacher, slot_id)

    if error:
        return error

    _, _, subject, day, time, room = slot

    students = [
        {"row_id": row_id, "student": student, "teacher": student_teacher}
        for row_id, student, student_teacher in get_slot_students(slot_id)
    ]

    return jsonify(
        id=slot_id, subject=subject, day=day, time=time, room=room,
        lesson_type=get_subject_type(teacher, subject),
        concertmasters=get_slot_concertmasters(slot_id),
        students=students
    )


@app.route("/api/teacher/slots/<int:slot_id>", methods=["DELETE"])
def api_teacher_delete_slot(slot_id):

    teacher, error = _require_teacher()

    if error:
        return error

    _, error = _own_slot_or_error(teacher, slot_id)

    if error:
        return error

    delete_slot(slot_id)

    return jsonify(ok=True)


@app.route("/api/teacher/search_students")
def api_teacher_search_students():

    _, error = _require_teacher()

    if error:
        return error

    query = request.args.get("q", "").strip()

    if len(query) < 2:
        return jsonify(results=[])

    results = [
        {"teacher": teacher, "student": student}
        for teacher, student in search_students(query)
    ]

    return jsonify(results=results)


@app.route("/api/teacher/slots/<int:slot_id>/students", methods=["POST"])
def api_teacher_add_student(slot_id):

    teacher, error = _require_teacher()

    if error:
        return error

    slot, error = _own_slot_or_error(teacher, slot_id)

    if error:
        return error

    data = request.get_json(silent=True) or {}

    student = data.get("student")
    student_teacher = data.get("teacher")

    if not student or not student_teacher:
        return jsonify(error="Ma'lumot yetarli emas"), 400


    # o'quvchi bir vaqtda ikki xil darsda bo'la olmaydi.
    # Shu darsning o'zi hisobga olinmaydi - bitta darsda
    # bir nechta o'qituvchi bo'lishi mumkin.

    busy = find_student_conflict(
        student, student_teacher, slot[3], slot[4],
        get_slot_duration(slot_id), exclude_slot_id=slot_id
    )

    if busy:
        return jsonify(error=(
            student + " " + slot[3] + " kuni " + slot[4]
            + " da boshqa darsda: " + busy[2] + " (" + busy[1]
            + ", " + busy[4] + "-xona)"
        )), 409

    added = add_student_to_slot(slot_id, student, student_teacher)

    if added:
        notify_if_overcapacity(_notify_bot.send_message, slot_id)

    return jsonify(ok=True, added=added)


# ==========================
# API: JO'RNAVOZLAR
# ==========================
#
# Bitta darsga bir nechta jo'rnavoz biriktirilishi mumkin
# (ansambl, xor, mutaxassislik darslarida). Faqat dars egasi
# o'zgartira oladi.
# ==========================


@app.route("/api/teacher/search_teachers")
def api_teacher_search_teachers():

    _, error = _require_teacher()

    if error:
        return error

    query = request.args.get("q", "").strip()

    if len(query) < 3:
        return jsonify(teachers=[])

    return jsonify(teachers=[
        {"name": name, "department": department}
        for _tid, name, department, _status in search_teachers_by_name(query)
    ])


@app.route("/api/teacher/teacher_slots")
def api_teacher_other_slots():
    """Boshqa o'qituvchining dars vaqtlari - jo'rnavozlik tanlash uchun."""

    me, error = _require_teacher()

    if error:
        return error

    owner = request.args.get("teacher", "").strip()

    if not owner:
        return jsonify(slots=[])

    slots = []

    department = get_department_for_teacher(owner)

    for slot_id, subject, day, time, room in get_teacher_slots(owner):

        # Rejada jo'rnavoz soati ajratilmagan fanlar ro'yxatda
        # umuman ko'rsatilmaydi - bosib bo'lmaydigan qatorni
        # ko'rsatib turishdan foyda yo'q.

        if not subject_has_concertmaster(department, subject):
            continue

        slots.append({
            "id": slot_id,
            "subject": subject,
            "lesson_type": get_subject_type(owner, subject),
            "day": day,
            "time": time,
            "room": room,
            "joined": me in get_slot_concertmasters(slot_id)
        })

    return jsonify(teacher=owner, slots=slots)


@app.route("/api/teacher/concertmaster")
def api_teacher_my_concertmaster_slots():
    """O'zim jo'rnavozlik qilayotgan darslar."""

    teacher, error = _require_teacher()

    if error:
        return error

    return jsonify(slots=[
        {
            "id": slot_id,
            "owner": owner,
            "subject": subject,
            "day": day,
            "time": time,
            "room": room
        }
        for slot_id, owner, subject, day, time, room
        in get_concertmaster_slots(teacher)
    ])


@app.route("/api/teacher/concertmaster", methods=["POST"])
def api_teacher_join_as_concertmaster():
    """Jo'rnavozning o'zi darsga biriktiriladi."""

    teacher, error = _require_teacher()

    if error:
        return error

    slot_id = (request.get_json(silent=True) or {}).get("slot_id")

    slot = get_slot(slot_id) if slot_id else None

    if not slot:
        return jsonify(error="Dars topilmadi"), 404

    if slot[1] == teacher:
        return jsonify(error="Bu o'z darsingiz"), 400

    if not can(teacher, "can_be_concertmaster"):
        return jsonify(error="Sizda jo'rnavozlik huquqi yo'q"), 403

    # Reja jo'rnavoz soatini faqat sanalgan fanlarga ajratadi -
    # solfedjio yoki rang tasvir darsiga jo'rnavoz qo'yilmaydi.

    allowed, subject = slot_allows_concertmaster(slot_id)

    if not allowed:
        return jsonify(error=(
            "«" + str(subject) + "» fani uchun o'quv rejasida "
            "jo'rnavoz soati ajratilmagan"
        )), 400

    busy = find_teacher_conflict(
        teacher, slot[3], slot[4],
        get_slot_duration(slot_id), exclude_slot_id=slot_id
    )

    if busy:
        return jsonify(error=(
            "Siz " + slot[3] + " kuni " + slot[4] + " da bandsiz: "
            + busy[2] + " (" + busy[1] + ", " + busy[4] + "-xona)"
        )), 409

    add_concertmaster(slot_id, teacher)

    return jsonify(ok=True)


@app.route("/api/teacher/concertmaster", methods=["DELETE"])
def api_teacher_leave_as_concertmaster():
    """Jo'rnavoz o'zini darsdan chiqaradi."""

    teacher, error = _require_teacher()

    if error:
        return error

    slot_id = (request.get_json(silent=True) or {}).get("slot_id")

    if not slot_id:
        return jsonify(error="Dars tanlanmagan"), 400

    remove_concertmaster(slot_id, teacher)

    return jsonify(ok=True)


@app.route("/api/teacher/slots/<int:slot_id>/concertmasters", methods=["DELETE"])
def api_teacher_remove_concertmaster(slot_id):

    teacher, error = _require_teacher()

    if error:
        return error

    _, error = _own_slot_or_error(teacher, slot_id)

    if error:
        return error

    name = ((request.get_json(silent=True) or {}).get("teacher") or "").strip()

    if not name:
        return jsonify(error="O'qituvchi tanlanmagan"), 400

    remove_concertmaster(slot_id, name)

    return jsonify(ok=True)


@app.route("/api/teacher/slot_students/<int:row_id>", methods=["DELETE"])
def api_teacher_remove_student(row_id):

    teacher, error = _require_teacher()

    if error:
        return error

    row = get_slot_student_row(row_id)

    if not row:
        return jsonify(error="Topilmadi"), 404

    _, slot_id, _, _ = row

    _, error = _own_slot_or_error(teacher, slot_id)

    if error:
        return error

    remove_slot_student(row_id)

    return jsonify(ok=True)


@app.route("/api/teacher/students")
def api_teacher_students():

    teacher, error = _require_teacher()

    if error:
        return error

    month = datetime.now().strftime("%Y-%m")

    students = []

    for student in get_students(teacher):

        fee = get_student_fee(teacher, student)

        privileged = (fee == FEE_PRIVILEGED)

        students.append({
            "student": student,
            "fee": 0 if privileged else fee,
            "privileged": privileged,
            "paid": privileged or has_paid_this_month(teacher, student, month)
        })

    return jsonify(month=month, students=students)


# ==========================
# API: O'QITUVCHI - YANGI O'QUVCHI
# ==========================
#
# Botda bu 3 ta matn + 2 ta tugma (ism, sana, guvohnoma, sinf,
# badal) - beshta alohida qadam. Mini App'da hammasi bitta
# ekranda to'ldiriladi va bir marta yuboriladi.
#
# Qoidalar botdagi bilan bir xil (`handlers/students.py`):
# guvohnoma raqami bolani aniqlaydi, shu o'qituvchida takror
# bo'lishi mumkin emas, boshqa o'qituvchida bo'lsa - bu ikkinchi
# mutaxassislik, ma'lumoti qayta yozilmaydi.


@app.route("/api/teacher/student_form")
def api_teacher_student_form():
    """Forma uchun ma'lumotnoma: sinflar va badal summalari."""

    _, error = _require_teacher()

    if error:
        return error

    return jsonify(
        classes=CLASS_OPTIONS,
        fees=FEE_OPTIONS,
        privileged_fee=FEE_PRIVILEGED
    )


@app.route("/api/teacher/students", methods=["POST"])
def api_teacher_create_student():

    teacher, error = _require_teacher()

    if error:
        return error

    data = request.get_json(silent=True) or {}

    student = str(data.get("student") or "").strip()

    birth_date = str(data.get("birth_date") or "").strip()

    metrika = str(data.get("metrika") or "").strip()

    class_name = str(data.get("class_name") or "").strip()

    same_child = bool(data.get("same_child"))

    try:
        monthly_fee = int(data.get("monthly_fee"))

    except (TypeError, ValueError):
        return jsonify(error="Oylik badal tanlanmadi"), 400

    if not 3 <= len(student) <= 80:
        return jsonify(error="Ism-familiya 3-80 belgi bo'lishi kerak"), 400

    # bo'sh joy va tirelar hisobga olinmaydi - odamlar turlicha yozadi

    digits = "".join(ch for ch in metrika if ch.isalnum())

    if not 5 <= len(digits) <= 20:
        return jsonify(error="Guvohnoma raqami noto'g'ri"), 400

    if not _valid_birth(birth_date):
        return jsonify(
            error="Tug'ilgan sana YYYY-MM-DD yoki KK.OO.YYYY ko'rinishida"
        ), 400

    if class_name not in CLASS_OPTIONS:
        return jsonify(error="Bunday sinf yo'q"), 400

    if monthly_fee not in FEE_OPTIONS:
        return jsonify(error="Bunday badal summasi yo'q"), 400

    found = find_metrika_duplicate(metrika, teacher=teacher)

    if found and found[0] == "same_teacher":

        return jsonify(
            error="Bu guvohnoma raqami ro'yxatingizda bor: " + found[2]
        ), 409

    if found and found[0] == "other_teacher":

        other_teacher, other_student = found[1], found[2]

        info = get_student_info(other_student, other_teacher)

        if not same_child:

            # Bola ikkinchi mutaxassislikka kiryaptimi? Buni
            # o'qituvchi tasdiqlashi kerak - frontend so'raydi va
            # same_child bilan qayta yuboradi.

            return jsonify(
                needs_confirm=True,
                other_teacher=other_teacher,
                other_student=other_student,
                birth_date=info[3] if info else "",
                other_class=info[5] if info else ""
            ), 409

        # Tasdiqlandi. Bolaning SHAXSIY ma'lumoti (ism, tug'ilgan
        # sana) qayta yozilmaydi - u bolaga tegishli.
        #
        # SINF esa ko'chirilmaydi: u mutaxassislikka bog'liq.
        # Bola fortepianoda 3-sinf bo'lsa ham, doirani endi
        # boshlayotgan bo'lishi mumkin - u yerda 1-sinf. Badal
        # ham shunday. Ikkalasini o'qituvchining o'zi belgilaydi.

        if info:

            birth_date = info[3]

    add_student(
        teacher,
        student,
        birth_date,
        metrika,
        class_name,
        monthly_fee
    )

    log_action(teacher, "o'quvchi qo'shdi", student, "Mini App")

    return jsonify(ok=True, student=student)


def _valid_birth(text):
    """Sana ikki ko'rinishda qabul qilinadi: 2015-03-21 yoki 21.03.2015."""

    for fmt in ("%Y-%m-%d", "%d.%m.%Y"):

        try:
            datetime.strptime(text, fmt)

            return True

        except ValueError:
            pass

    return False


# ==========================
# API: ADMIN/DIREKTOR
# ==========================


@app.route("/api/admin/live")
def api_admin_live():

    _, error = _require_admin()

    if error:
        return error

    now = datetime.now()

    # DAYS_OF_WEEK da 6 kun (Dushanba-Shanba), weekday() esa
    # yakshanbada 6 qaytaradi - ro'yxatdan tashqari. Ilgari shu
    # yerda IndexError chiqib, har yakshanba "Hozir" bo'limi
    # ishlamay qolardi.

    weekday = now.weekday()

    if weekday >= len(DAYS_OF_WEEK):

        return jsonify(
            day="Yakshanba",
            now=now.strftime("%H:%M"),
            live=[]
        )

    today = DAYS_OF_WEEK[weekday]

    now_minutes = now.hour * 60 + now.minute

    live = []

    for slot_id, teacher, subject, time, room, duration in get_slots_for_day(today):

        try:
            hh, mm = time.split(":")
            start_minutes = int(hh) * 60 + int(mm)

        except (ValueError, AttributeError):
            continue

        if start_minutes <= now_minutes <= start_minutes + duration:

            students = [
                s for _, s, _ in get_slot_students(slot_id)
            ]

            live.append({
                "teacher": teacher,
                "subject": subject,
                "time": time,
                "room": room,
                "students": students
            })

    return jsonify(day=today, now=now.strftime("%H:%M"), live=live)


@app.route("/api/admin/departments")
def api_admin_departments():

    _, error = _require_admin()

    if error:
        return error

    return jsonify(departments=get_departments())


@app.route("/api/admin/teachers")
def api_admin_teachers():

    _, error = _require_admin()

    if error:
        return error

    dept = request.args.get("dept", "")

    teachers = [
        {"id": tid, "name": name, "status": status}
        for tid, name, status in get_teachers_by_department(dept)
    ]

    return jsonify(teachers=teachers)


def _tell_bot(chat_id, text):
    """
    Mini App'dagi amal haqida botga xabar beradi.

    Pastdagi doimiy menyu ham tozalanadi - aks holda eski
    tugmalar qolib, ular boshqa rol nomidan ishlayverardi.
    """

    try:

        _notify_bot.send_message(
            chat_id,
            text,
            reply_markup=telebot.types.ReplyKeyboardRemove()
        )

    except Exception:
        pass


# ==========================
# API: ADMIN - O'QITUVCHI SIFATIDA KO'RISH
# ==========================
#
# Tanlov bazada saqlanadi, shuning uchun Mini App'da yoqilgan
# rejim botda ham (va aksincha) darhol ko'rinadi.


@app.route("/api/admin/view-as", methods=["POST"])
def api_admin_view_as():

    user, error = _require_admin()

    if error:
        return error

    data = request.get_json(silent=True) or {}

    row = get_teacher_by_id(int(data.get("teacher_id") or 0))

    if not row:
        return jsonify(error="O'qituvchi topilmadi"), 404

    name = row[1]

    set_view_as(user["id"], name)

    log_action(
        str(user["id"]),
        "ko'rish rejimi yoqildi",
        target=name,
        details="Mini App",
        actor_role="admin"
    )

    _tell_bot(
        user["id"],
        "👁 Ko'rish rejimi yoqildi: " + name + "."
        + "\n\nBot menyusini ham o'sha o'qituvchinikiga "
        + "almashtirish uchun /start yuboring."
    )

    return jsonify(ok=True, teacher=name)


@app.route("/api/admin/view-as", methods=["DELETE"])
def api_admin_view_as_stop():

    user, error = _require_admin()

    if error:
        return error

    name = get_view_as(user["id"])

    clear_view_as(user["id"])

    if name:
        log_action(
            str(user["id"]),
            "ko'rish rejimi o'chirildi",
            target=name,
            details="Mini App",
            actor_role="admin"
        )

    # Bot alohida jarayon - rejim shu yerda o'chirilganini
    # bilmaydi. Xabar yuborilmasa, botdagi menyu o'sha
    # o'qituvchinikida qolib ketardi.

    _tell_bot(
        user["id"],
        "✅ Ko'rish rejimi tugadi.\n\n"
        "Admin panel uchun /admin buyrug'ini yuboring."
    )

    return jsonify(ok=True)


@app.route("/api/admin/teacher/<int:teacher_id>/slots")
def api_admin_teacher_slots(teacher_id):

    _, error = _require_admin()

    if error:
        return error

    row = get_teacher_by_id(teacher_id)

    if not row:
        return jsonify(error="Topilmadi"), 404

    name = row[1]

    slots = []

    for slot_id, subject, day, time, room in get_teacher_slots(name):

        slots.append({
            "id": slot_id,
            "subject": subject,
            "day": day,
            "time": time,
            "room": room,
            "student_count": len(get_slot_students(slot_id))
        })

    return jsonify(teacher=name, slots=slots)


@app.route("/api/admin/slot/<int:slot_id>")
def api_admin_slot_detail(slot_id):

    _, error = _require_admin()

    if error:
        return error

    slot = get_slot(slot_id)

    if not slot:
        return jsonify(error="Topilmadi"), 404

    _, teacher, subject, day, time, room = slot

    students = [
        {"student": student, "teacher": student_teacher}
        for _, student, student_teacher in get_slot_students(slot_id)
    ]

    return jsonify(
        teacher=teacher, subject=subject, day=day, time=time, room=room,
        lesson_type=get_subject_type(teacher, subject),
        concertmasters=get_slot_concertmasters(slot_id),
        students=students
    )


@app.route("/api/admin/report")
def api_admin_report():

    _, error = _require_admin()

    if error:
        return error

    month = request.args.get("month") or datetime.now().strftime("%Y-%m")

    rows = get_monthly_debt_rows(month)

    summary = {}

    for teacher, dept, student, fee, paid, privileged in rows:

        entry = summary.setdefault(
            teacher,
            {"department": dept, "total": 0, "free": 0, "unpaid": 0, "debt": 0}
        )

        entry["total"] += 1

        if privileged:
            entry["free"] += 1

        elif not paid:
            entry["unpaid"] += 1
            entry["debt"] += fee

    teachers = [
        {"teacher": t, **data}
        for t, data in sorted(summary.items(), key=lambda x: x[1]["debt"], reverse=True)
    ]

    return jsonify(
        month=month,
        teachers=teachers,
        total_debt=sum(t["debt"] for t in teachers),
        total_unpaid=sum(t["unpaid"] for t in teachers)
    )


@app.route("/api/admin/audit")
def api_admin_audit():
    """O'zgarishlar tarixi - kim, qachon, nimani o'zgartirgan."""

    _, error = _require_superadmin()

    if error:
        return error

    query = request.args.get("q", "").strip() or None

    return jsonify(entries=[
        {
            "at": at,
            "actor": actor,
            "role": actor_role,
            "action": action,
            "target": target,
            "details": details
        }
        for at, actor, actor_role, action, target, details
        in get_audit_log(limit=100, query=query)
    ])


@app.route("/api/admin/archive")
def api_admin_archive():
    """Arxivdagi o'quvchilar."""

    _, error = _require_superadmin()

    if error:
        return error

    return jsonify(students=[
        {
            "teacher": teacher,
            "student": student,
            "archived_at": at,
            "reason": reason
        }
        for teacher, student, at, reason in get_archived_students()
    ])


@app.route("/api/admin/archive/restore", methods=["POST"])
def api_admin_restore():
    """Arxivdan qaytaradi."""

    user, error = _require_superadmin()

    if error:
        return error

    data = request.get_json(silent=True) or {}

    teacher = (data.get("teacher") or "").strip()
    student = (data.get("student") or "").strip()

    if not teacher or not student:
        return jsonify(error="O'quvchi tanlanmagan"), 400

    if not restore_student(teacher, student):
        return jsonify(error="Topilmadi"), 404

    log_action(
        str(user.get("id")), "o'quvchini arxivdan qaytardi",
        student, teacher, actor_role="admin"
    )

    return jsonify(ok=True)


@app.route("/api/admin/search")
def api_admin_search():
    """Direktor uchun umumiy qidiruv: o'quvchi + o'qituvchi."""

    _, error = _require_admin()

    if error:
        return error

    query = request.args.get("q", "").strip()

    if len(query) < 2:
        return jsonify(students=[], teachers=[])

    students = [
        {"student": student, "teacher": teacher}
        for teacher, student in search_students(query, limit=20)
    ]

    teachers = [
        {"id": tid, "name": name, "department": dept}
        for tid, name, dept, _ in search_teachers_by_name(query, limit=10)
    ]

    return jsonify(students=students, teachers=teachers)


if __name__ == "__main__":

    port = int(os.environ.get("PORT", 5000))

    app.run(host="0.0.0.0", port=port, debug=True)
