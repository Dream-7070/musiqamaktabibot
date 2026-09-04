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

from config import TOKEN, ADMIN_IDS

from webapp.auth import validate_init_data

from database import (
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

    DAYS_OF_WEEK,
    SUBJECTS,
    get_teacher_slots,
    get_slot,
    get_slot_students,
    create_slot,
    delete_slot,
    add_student_to_slot,
    remove_slot_student,
    get_slot_student_row,
    search_students,
    get_slots_for_day,

    get_students,
    get_student_fee,
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


def _require_teacher():
    """Muvaffaqiyatli bo'lsa (teacher_name, None), aks holda (None, xato_javob)."""

    user = _authenticated_user()

    if not user:
        return None, (jsonify(error="Ruxsat yo'q"), 401)

    binding = find_teacher_binding(user["id"])

    if not binding:
        return None, (jsonify(error="Siz tasdiqlangan o'qituvchi emassiz"), 403)

    return binding[0], None


def _is_director(user_id):
    """Admin yoki direktor - ikkalasi ham boshqaruv panelini ko'radi."""

    return user_id in ADMIN_IDS or get_staff_role(user_id) == "direktor"


def _require_admin():

    user = _authenticated_user()

    if not user or not _is_director(user["id"]):
        return None, (jsonify(error="Ruxsat yo'q"), 401)

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


@app.route("/api/whoami")
def api_whoami():

    user = _authenticated_user()

    if not user:
        return jsonify(error="Ruxsat yo'q"), 401

    if user["id"] in ADMIN_IDS:
        return jsonify(role="admin")

    staff_role = get_staff_role(user["id"])

    if staff_role == "direktor":
        return jsonify(role="admin", staff="direktor")

    if staff_role:
        return jsonify(role="staff", staff=staff_role)

    binding = find_teacher_binding(user["id"])

    if binding:
        return jsonify(role="teacher", teacher=binding[0], department=binding[1])

    parent = get_parent(user["id"])

    if parent:
        return jsonify(role="parent")

    return jsonify(role=None)


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

    return jsonify(
        student=student,
        teacher=teacher,
        department=department,
        class_name=info[5],
        monthly_fee=info[6] if len(info) > 6 else 0,
        payments=payments,
        schedule=schedule
    )


def _format_schedule(rows):

    return [
        {"subject": subject, "day": day, "time": time, "room": room, "teacher": slot_teacher}
        for subject, day, time, room, slot_teacher in rows
    ]


# ==========================
# API: O'QITUVCHI - O'Z JADVALI
# ==========================


@app.route("/api/teacher/me")
def api_teacher_me():

    teacher, error = _require_teacher()

    if error:
        return error

    return jsonify(
        teacher=teacher,
        department=get_department_for_teacher(teacher),
        subjects=SUBJECTS,
        days=DAYS_OF_WEEK
    )


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
            "day": day,
            "time": time,
            "room": room,
            "student_count": len(get_slot_students(slot_id))
        })

    return jsonify(slots=slots)


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

    if subject not in SUBJECTS:
        return jsonify(error="Fan noto'g'ri"), 400

    if day not in DAYS_OF_WEEK:
        return jsonify(error="Kun noto'g'ri"), 400

    if not time or not room:
        return jsonify(error="Soat va xona kiritilishi shart"), 400

    slot_id = create_slot(teacher, subject, day, time.strip(), room.strip())

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

    _, error = _own_slot_or_error(teacher, slot_id)

    if error:
        return error

    data = request.get_json(silent=True) or {}

    student = data.get("student")
    student_teacher = data.get("teacher")

    if not student or not student_teacher:
        return jsonify(error="Ma'lumot yetarli emas"), 400

    added = add_student_to_slot(slot_id, student, student_teacher)

    return jsonify(ok=True, added=added)


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

        students.append({
            "student": student,
            "fee": get_student_fee(teacher, student),
            "paid": has_paid_this_month(teacher, student, month)
        })

    return jsonify(month=month, students=students)


# ==========================
# API: ADMIN/DIREKTOR
# ==========================


@app.route("/api/admin/live")
def api_admin_live():

    _, error = _require_admin()

    if error:
        return error

    now = datetime.now()

    today = DAYS_OF_WEEK[now.weekday()]

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

    for teacher, dept, student, fee, paid in rows:

        entry = summary.setdefault(
            teacher, {"department": dept, "total": 0, "unpaid": 0, "debt": 0}
        )

        entry["total"] += 1

        if not paid:
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
