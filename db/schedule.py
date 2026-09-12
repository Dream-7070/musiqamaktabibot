# -*- coding: utf-8 -*-
# ==========================
# db/schedule.py
# ==========================
#
# Bu fayl ilgari database.py ning bir qismi edi (5100+ satr).
# database.py hozir FASAD - u shu paketdagi hamma narsani
# qayta eksport qiladi, shuning uchun `from database import X`
# hamma joyda o'zgarishsiz ishlayveradi.
#
# ==========================


import sqlite3

from db.uzbek import filter_matches, sort_key

from datetime import datetime

# Bu modul quyidagi modullardagi nomlarni ishlatadi
# (database.py fasadi ularni yuklashda joylashtiradi):
#   db.core: connect
#   db.students: get_student_enrollments
#   db.subjects: get_subject_type


# ==========================
# DARS JADVALI
# ==========================
#
# Har bir o'qituvchi o'z "vaqt katakchalarini" (slot) tuzadi:
# kun + soat + fan + xona. Keyin shu katakchaga o'quvchilarni
# qo'shadi - hatto ular boshqa o'qituvchining o'quvchisi
# bo'lsa ham (masalan, solfedjio o'qituvchisi butun maktabdan
# o'quvchi qo'sha oladi).
#
# Natijada bitta o'quvchi bir nechta o'qituvchidan yig'ilgan
# to'liq haftalik jadvalga ega bo'ladi.
# ==========================


# 2026 o'quv rejasi: o'quv haftasining davomiyligi 6 kun.
# Yakshanba dam olish kuni - unga dars qo'yilmaydi.

DAYS_OF_WEEK = [
    "Dushanba",
    "Seshanba",
    "Chorshanba",
    "Payshanba",
    "Juma",
    "Shanba"
]


SUBJECTS = [
    "Mutaxassislik",
    "Solfedjio",
    "San'at tarixi",
    "Musiqa adabiyoti",
    "Ansambl",
    "Xor",
    "Nazariy fanlar",
    "Tanlangan fan",
    "Boshqa"
]


_DAY_ORDER = {day: i for i, day in enumerate(DAYS_OF_WEEK)}


def create_slot(teacher, subject, day_of_week, time, room,
                duration_minutes=None, class_name=None):

    # vaqt bir xil ko'rinishda saqlansin - to'qnashuvni
    # tekshirish uchun bu muhim

    time = normalize_time(time) or (time or "").strip()

    duration_minutes = duration_minutes or DEFAULT_DURATION

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        """
        INSERT INTO schedule_slots
        (teacher, subject, day_of_week, time, room,
         duration_minutes, class_name)
        VALUES (?,?,?,?,?,?,?)
        """,
        (teacher, subject, day_of_week, time, room,
         duration_minutes, class_name)
    )

    slot_id = cursor.lastrowid

    db.commit()
    db.close()

    return slot_id


def update_slot_schedule(slot_id, day_of_week, time, room, duration_minutes=None):
    """
    Darsning kuni/vaqti/xonasini o'zgartiradi - fan, sinf,
    o'quvchilar va jo'rnavozlar tegilmaydi.

    Xonani tuzatish uchun butun darsni o'chirib qayta yaratish
    o'quvchilarni yo'qotib qo'yardi (schedule_slot_students
    kaskad o'chadi) - shu funksiya aynan shu muammoni oldini
    olish uchun qo'shildi.
    """

    time = normalize_time(time) or (time or "").strip()

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        """
        UPDATE schedule_slots
        SET day_of_week=?, time=?, room=?, duration_minutes=?
        WHERE id=?
        """,
        (day_of_week, time, room, duration_minutes or DEFAULT_DURATION, slot_id)
    )

    changed = cursor.rowcount

    db.commit()
    db.close()

    return changed > 0


def get_teacher_last_pick(teacher):
    """
    Oxirgi qo'shilgan darsning fani va sinfi - (subject, class_name)
    yoki hech narsa bo'lmasa None.

    "Oxirgisidek" tezkor tugmasi uchun: fan va sinfni qayta
    so'ramasdan, to'g'ridan-to'g'ri kun/vaqt/xonaga o'tkazadi.
    """

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        """
        SELECT subject, class_name FROM schedule_slots
        WHERE teacher=?
        ORDER BY id DESC
        LIMIT 1
        """,
        (teacher,)
    )

    row = cursor.fetchone()

    db.close()

    return row if row else None


def get_teacher_slots(teacher):
    """[(id, subject, day_of_week, time, room), ...] - hafta kuni tartibida."""

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        """
        SELECT id, subject, day_of_week, time, room
        FROM schedule_slots
        WHERE teacher=?
        """,
        (teacher,)
    )

    rows = cursor.fetchall()

    db.close()

    rows.sort(key=lambda r: (_DAY_ORDER.get(r[2], 99), r[3]))

    return rows


def get_slot_duration(slot_id):
    """Dars davomiyligi (daqiqa)."""

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        "SELECT COALESCE(duration_minutes, ?) FROM schedule_slots WHERE id=?",
        (DEFAULT_DURATION, slot_id)
    )

    row = cursor.fetchone()

    db.close()

    return row[0] if row else DEFAULT_DURATION


def get_slot(slot_id):
    """(id, teacher, subject, day_of_week, time, room) yoki None."""

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        """
        SELECT id, teacher, subject, day_of_week, time, room
        FROM schedule_slots
        WHERE id=?
        """,
        (slot_id,)
    )

    row = cursor.fetchone()

    db.close()

    return row


def delete_slot(slot_id):

    db = connect()
    cursor = db.cursor()

    cursor.execute("DELETE FROM schedule_slots WHERE id=?", (slot_id,))

    cursor.execute(
        "DELETE FROM schedule_slot_students WHERE slot_id=?",
        (slot_id,)
    )

    # Jo'rnavozlar ham shu darsga bog'langan - ilgari bu qator
    # yo'q edi va dars o'chgach yetim yozuv qolib ketardi.

    cursor.execute(
        "DELETE FROM slot_concertmasters WHERE slot_id=?",
        (slot_id,)
    )

    db.commit()
    db.close()


def get_slot_students(slot_id):
    """[(row_id, student, student_teacher), ...]"""

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        """
        SELECT id, student, student_teacher
        FROM schedule_slot_students
        WHERE slot_id=?
        ORDER BY student
        """,
        (slot_id,)
    )

    data = cursor.fetchall()

    db.close()

    return data


def add_student_to_slot(slot_id, student, student_teacher):
    """Allaqachon qo'shilgan bo'lsa qayta qo'shmaydi."""

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        """
        SELECT id FROM schedule_slot_students
        WHERE slot_id=? AND student=? AND student_teacher=?
        """,
        (slot_id, student, student_teacher)
    )

    if cursor.fetchone():
        db.close()
        return False

    cursor.execute(
        """
        INSERT INTO schedule_slot_students (slot_id, student, student_teacher)
        VALUES (?,?,?)
        """,
        (slot_id, student, student_teacher)
    )

    db.commit()
    db.close()

    return True


def remove_slot_student(row_id):

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        "DELETE FROM schedule_slot_students WHERE id=?",
        (row_id,)
    )

    db.commit()
    db.close()


def search_students(query, limit=15):
    """
    Butun maktab bo'yicha o'quvchi qidirish: [(teacher, student), ...]

    Qidiruv O'ZBEKCHA YOZUV FARQLARINI hisobga oladi: "behruz"
    so'rovi "Bexruz" ni ham topadi (db/uzbek.py). Ilgari oddiy
    LIKE ishlatilardi va xodim mavjud o'quvchini topa olmasdi.

    Solishtirish Python tomonida bajariladi - SQLite'da bunday
    normallashtirish yo'q. O'quvchilar soni maktab miqyosida
    kichik (yuzlab), shuning uchun bu sezilarli emas.
    """

    text = (query or "").strip()

    if not text:
        return []

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        """
        SELECT DISTINCT teacher, student
        FROM students
        WHERE COALESCE(archived, 0) = 0
        """
    )

    rows = cursor.fetchall()

    db.close()

    found = filter_matches(text, rows, key=lambda row: row[1])

    found.sort(key=lambda row: sort_key(text, row[1]))

    return found[:limit]


def get_student_full_schedule(teacher, student):
    """
    Shu o'quvchining BARCHA o'qituvchilardan yig'ilgan haftalik
    jadvali: [(subject, day_of_week, time, room, slot_teacher, slot_id), ...]
    """

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        """
        SELECT sl.subject, sl.day_of_week, sl.time, sl.room, sl.teacher, sl.id
        FROM schedule_slot_students ss
        JOIN schedule_slots sl ON sl.id = ss.slot_id
        WHERE ss.student_teacher=? AND ss.student=?
        """,
        (teacher, student)
    )

    rows = cursor.fetchall()

    db.close()

    rows.sort(key=lambda r: (_DAY_ORDER.get(r[1], 99), r[2]))

    return rows


# ==========================
# JADVAL TO'QNASHUVLARI
# ==========================
#
# Qoidalar:
#
#   1. Bitta o'quvchi bir vaqtda ikki xil darsda bo'la olmaydi.
#      Lekin AYNI darsda bir nechta o'qituvchi bo'lishi mumkin
#      (biri mutaxassislik, qolganlari jo'rnavoz) - bu bitta
#      dars bo'lgani uchun to'qnashuv emas.
#
#   2. Bitta xonani bir vaqtda ikki xil dars egallay olmaydi.
#      Xonani bitta mutaxassislik o'qituvchisi oladi, boshqalar
#      shu darsga jo'rnavoz bo'lib qo'shiladi.
#
#   3. Bitta o'qituvchi bir vaqtda ikki xil darsda bo'la olmaydi
#      (o'z darsi ham, jo'rnavozligi ham hisobga olinadi).
#
# Vaqt matn sifatida yozilgani uchun avval normallashtiriladi,
# so'ng dars davomiyligi bilan kesishuv tekshiriladi.
# ==========================


DEFAULT_DURATION = 45


def normalize_time(text):
    """
    '9:5', '15.00', '1500', '15' -> '09:05' / '15:00'
    Tushunib bo'lmasa - None.
    """

    raw = (text or "").strip()

    if not raw:
        return None

    digits = ""

    for ch in raw:
        if ch.isdigit():
            digits += ch
        elif ch in ":.- ":
            digits += ":"
        else:
            return None

    parts = [p for p in digits.split(":") if p]

    if not parts:
        return None

    if len(parts) == 1:

        block = parts[0]

        if len(block) <= 2:
            hour, minute = block, "0"

        elif len(block) == 3:
            hour, minute = block[0], block[1:]

        elif len(block) == 4:
            hour, minute = block[:2], block[2:]

        else:
            return None

    else:
        hour, minute = parts[0], parts[1]

    try:
        hour = int(hour)
        minute = int(minute)

    except ValueError:
        return None

    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        return None

    return "{:02d}:{:02d}".format(hour, minute)


def time_to_minutes(text):
    """'15:00' -> 900. Noto'g'ri bo'lsa None."""

    normalized = normalize_time(text)

    if not normalized:
        return None

    hour, minute = normalized.split(":")

    return int(hour) * 60 + int(minute)


def _same_room(a, b):
    """'12', ' 12 ', '12-xona' bir xil xona deb qaraladi."""

    def clean(value):
        return "".join(
            ch for ch in (value or "").lower() if ch.isalnum()
        ).replace("xona", "")

    return clean(a) == clean(b) and clean(a) != ""


def get_overlapping_slots(day, time, duration=None, exclude_slot_id=None):
    """
    Shu kuni va shu vaqt oralig'ida kesishadigan darslar:
    [(id, teacher, subject, time, room), ...]
    """

    start = time_to_minutes(time)

    if start is None:
        return []

    duration = duration or DEFAULT_DURATION

    end = start + duration

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        """
        SELECT id, teacher, subject, time, room,
               COALESCE(duration_minutes, ?)
        FROM schedule_slots
        WHERE day_of_week=?
        """,
        (DEFAULT_DURATION, day)
    )

    rows = cursor.fetchall()

    db.close()

    hits = []

    for slot_id, teacher, subject, slot_time, room, slot_duration in rows:

        if exclude_slot_id and slot_id == exclude_slot_id:
            continue

        other_start = time_to_minutes(slot_time)

        if other_start is None:
            continue

        other_end = other_start + (slot_duration or DEFAULT_DURATION)

        if start < other_end and other_start < end:
            hits.append((slot_id, teacher, subject, slot_time, room))

    return hits


def find_room_conflict(day, time, room, duration=None, exclude_slot_id=None):
    """Xona shu vaqtda band bo'lsa - o'sha darsni qaytaradi, aks holda None."""

    for slot in get_overlapping_slots(day, time, duration, exclude_slot_id):

        if _same_room(slot[4], room):
            return slot

    return None


def get_rooms():
    """[{'id':.., 'code':'2/4', 'name':'', 'label':'2/4'}, ...] - tartib bilan."""

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        "SELECT id, code, name FROM rooms ORDER BY position, id"
    )

    rows = cursor.fetchall()

    db.close()

    return [
        {
            "id": row[0],
            "code": row[1],
            "name": row[2] or "",
            "label": row[1] + (" - " + row[2] if row[2] else ""),
        }
        for row in rows
    ]


def get_room_codes():
    """Faqat xona raqamlari: ['1/5', '1/8', ...]"""

    return [r["code"] for r in get_rooms()]


def add_room(code, name=""):
    """
    Yangi xona qo'shadi.

    (True, xona) yoki (False, sabab) qaytaradi. Takroriy raqam
    qo'shilmaydi - _same_room bo'yicha solishtiriladi, ya'ni
    '2/4' va '2.4' bir xil xona deb qaraladi.
    """

    code = (code or "").strip()
    name = (name or "").strip()

    if not code:
        return False, "Xona raqami bo'sh"

    if len(code) > 30:
        return False, "Xona raqami juda uzun"

    for room in get_rooms():

        if _same_room(room["code"], code):
            return False, "Bunday xona allaqachon bor: " + room["label"]

    db = connect()
    cursor = db.cursor()

    cursor.execute("SELECT COALESCE(MAX(position), -1) + 1 FROM rooms")

    position = cursor.fetchone()[0]

    cursor.execute(
        "INSERT INTO rooms(code, name, position) VALUES(?,?,?)",
        (code, name, position)
    )

    room_id = cursor.lastrowid

    db.commit()
    db.close()

    return True, {
        "id": room_id,
        "code": code,
        "name": name,
        "label": code + (" - " + name if name else ""),
    }


def delete_room(room_id):
    """
    Xonani o'chiradi.

    Unda dars bor bo'lsa o'chirilmaydi - jadval buzilib qolmasin.
    """

    rooms = {r["id"]: r for r in get_rooms()}

    room = rooms.get(room_id)

    if not room:
        return False, "Xona topilmadi"

    db = connect()
    cursor = db.cursor()

    cursor.execute("SELECT room FROM schedule_slots")

    used = sum(
        1 for (value,) in cursor.fetchall()
        if _same_room(value, room["code"])
    )

    if used:
        db.close()
        return False, (
            "Bu xonada " + str(used) + " ta dars bor. "
            "Avval o'sha darslarni boshqa xonaga ko'chiring."
        )

    cursor.execute("DELETE FROM rooms WHERE id=?", (room_id,))

    db.commit()
    db.close()

    return True, room


def get_slot_group_status(slot_id):
    """
    Guruh darsi hajmi meʼyorga mos keladimi.

    None qaytadi - agar dars yakka tartibda bo'lsa (meʼyor tegishli
    emas). Aks holda:
        {'count': 8, 'min': 6, 'max': 11, 'status': 'ok'}
    status: 'kam' (min dan past), 'ok', 'ortiq' (max dan yuqori)
    """

    slot = get_slot(slot_id)

    if not slot:
        return None

    _, teacher, subject, _, _, _ = slot

    if get_subject_type(teacher, subject) != "guruh":
        return None

    from data.curriculum import group_size_norm

    low, high = group_size_norm(subject)

    count = len(get_slot_students(slot_id))

    if count < low:
        status = "kam"
    elif count > high:
        status = "ortiq"
    else:
        status = "ok"

    return {"count": count, "min": low, "max": high, "status": status}


def get_understaffed_groups():
    """
    Meʼyordan kam guruhlar - kunlik eslatma uchun.

    [{'teacher':.., 'subject':.., 'day':.., 'time':.., 'count':..,
      'min':..}, ...]
    """

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        "SELECT id, teacher, subject, day_of_week, time FROM schedule_slots"
    )

    rows = cursor.fetchall()

    db.close()

    result = []

    for slot_id, teacher, subject, day, time in rows:

        status = get_slot_group_status(slot_id)

        if status and status["status"] == "kam":

            result.append({
                "teacher": teacher,
                "subject": subject,
                "day": day,
                "time": time,
                "count": status["count"],
                "min": status["min"],
            })

    return result


def get_room_availability(day, time, duration=None, exclude_slot_id=None):
    """
    Har bir xona shu kuni, shu vaqtda bo'shmi yoki bandmi.

    [{'room': '2/4', 'name': '', 'label': '2/4', 'busy': False,
      'teacher': None, 'subject': None, 'time': None,
      'slot_id': None}, ...]

    Tartib `rooms` jadvalidagidek saqlanadi - o'qituvchi ro'yxatni
    har safar bir xil ko'radi.
    """

    overlapping = get_overlapping_slots(day, time, duration, exclude_slot_id)

    result = []

    for room in get_rooms():

        taken = None

        for slot in overlapping:

            if _same_room(slot[4], room["code"]):
                taken = slot
                break

        entry = {
            "room": room["code"],
            "name": room["name"],
            "label": room["label"],
            "busy": bool(taken),
            "slot_id": None,
            "teacher": None,
            "subject": None,
            "time": None,
        }

        if taken:

            slot_id, owner, subject, slot_time, _ = taken

            entry["slot_id"] = slot_id
            entry["teacher"] = owner
            entry["subject"] = subject
            entry["time"] = slot_time

        result.append(entry)

    return result


def find_teacher_conflict(teacher, day, time, duration=None, exclude_slot_id=None):
    """
    O'qituvchi shu vaqtda boshqa darsda bandmi.
    O'z darsi ham, jo'rnavozlik qilayotgani ham hisobga olinadi.
    """

    for slot in get_overlapping_slots(day, time, duration, exclude_slot_id):

        if slot[1] == teacher:
            return slot

        if teacher in get_slot_concertmasters(slot[0]):
            return slot

    return None


def find_student_conflict(
        student, student_teacher, day, time,
        duration=None, exclude_slot_id=None
):
    """
    O'quvchi shu vaqtda boshqa darsga yozilganmi.

    AYNI darsda bir nechta o'qituvchi bo'lishi to'qnashuv emas -
    shuning uchun exclude_slot_id orqali o'sha dars chiqarib
    tashlanadi.

    Bola ikki mutaxassislikda o'qiyotgan bo'lsa (masalan
    fortepiano va doira), bazada ikkita yozuv bo'ladi. Bola
    esa bitta - shuning uchun ikkala yozuvi ham tekshiriladi:
    fortepiano darsi vaqtida doira darsiga yozib bo'lmaydi.
    """

    enrollments = set(get_student_enrollments(student_teacher, student))

    for slot in get_overlapping_slots(day, time, duration, exclude_slot_id):

        for _, name, owner in get_slot_students(slot[0]):

            if (owner, name) in enrollments:
                return slot

    return None


def find_slot_student_conflicts(slot_id, day, time, duration=None):
    """
    Dars ko'chirilsa, uning o'quvchilaridan qaysi biri o'z boshqa
    darsi bilan to'qnashishini aniqlaydi.

    [(o'quvchi_ismi, to'qnashgan_slot), ...] - to'qnashuv bo'lmasa
    bo'sh ro'yxat.
    """
    conflicts = []
    seen = set()

    for _, student, student_teacher in get_slot_students(slot_id):
        if student in seen:
            continue

        conflict = find_student_conflict(
            student, student_teacher, day, time,
            duration, exclude_slot_id=slot_id
        )
        if conflict:
            conflicts.append((student, conflict))
            seen.add(student)

    return conflicts


# ==========================
# JO'RNAVOZLAR (konsertmeysterlar)
# ==========================
#
# Bitta darsga bir nechta jo'rnavoz biriktirilishi mumkin
# (ansambl, xor darslarida). Dars o'zi bitta bo'lib qoladi -
# faqat unga qo'shimcha o'qituvchilar biriktiriladi.
# ==========================


def ensure_concertmaster_table():

    db = connect()
    cursor = db.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS slot_concertmasters(
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            slot_id INTEGER,
            teacher TEXT
        )
    """)

    cursor.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_slot_cm
        ON slot_concertmasters(slot_id, teacher)
    """)

    db.commit()
    db.close()


def slot_allows_concertmaster(slot_id):
    """
    Shu darsga jo'rnavoz biriktirish mumkinmi (reja bo'yicha).

    Qaytaradi (mumkinmi, fan_nomi) - fan nomi xabar matnida
    ishlatiladi. Dars topilmasa (False, None).
    """

    from data.curriculum import subject_has_concertmaster

    slot = get_slot(slot_id)

    if not slot:
        return False, None

    _, owner, subject, _, _, _ = slot

    department = get_department_for_teacher(owner)

    return subject_has_concertmaster(department, subject), subject


def add_concertmaster(slot_id, teacher):
    """
    Allaqachon biriktirilgan yoki reja ruxsat bermasa - False.

    Reja jo'rnavoz soatini har bir fanga emas, faqat sanalgan
    fanlarga ajratadi (`subject_has_concertmaster`). Tekshiruv
    shu yerda ham turadi - interfeys o'zgarsa ham qoida
    buzilmasin.
    """

    allowed, _ = slot_allows_concertmaster(slot_id)

    if not allowed:
        return False


    db = connect()
    cursor = db.cursor()

    cursor.execute(
        "SELECT id FROM slot_concertmasters WHERE slot_id=? AND teacher=?",
        (slot_id, teacher)
    )

    if cursor.fetchone():
        db.close()
        return False

    cursor.execute(
        "INSERT INTO slot_concertmasters (slot_id, teacher) VALUES (?,?)",
        (slot_id, teacher)
    )

    db.commit()
    db.close()

    return True


def remove_concertmaster(slot_id, teacher):

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        "DELETE FROM slot_concertmasters WHERE slot_id=? AND teacher=?",
        (slot_id, teacher)
    )

    db.commit()
    db.close()


def get_slot_concertmasters(slot_id):
    """['Ismoilova N.', ...]"""

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        "SELECT teacher FROM slot_concertmasters WHERE slot_id=? ORDER BY teacher",
        (slot_id,)
    )

    data = [r[0] for r in cursor.fetchall()]

    db.close()

    return data


def get_concertmaster_slots(teacher):
    """
    Shu o'qituvchi jo'rnavoz bo'lgan darslar:
    [(slot_id, asosiy_oqituvchi, subject, day, time, room), ...]
    """

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        """
        SELECT s.id, s.teacher, s.subject, s.day_of_week, s.time, s.room
        FROM slot_concertmasters cm
        JOIN schedule_slots s ON s.id = cm.slot_id
        WHERE cm.teacher=?
        """,
        (teacher,)
    )

    rows = cursor.fetchall()

    db.close()

    rows.sort(key=lambda r: (_DAY_ORDER.get(r[3], 99), r[4]))

    return rows


# ==========================
# DARS VAQTLARI
# ==========================
#
# 2026 o'quv rejasi: 1 akademik soat = 45 daqiqa, darslar
# oralig'idagi tanaffus 5 daqiqa, o'quv haftasi 6 kun.
#
# Maktab kuni 08:00 dan 17:05 gacha, 12:05-13:00 tushlik.
# Shu qoidalardan aniq 10 ta dars vaqti kelib chiqadi:
# tushlikkacha 5 ta, tushlikdan keyin 5 ta.
#
# Vaqt qo'lda yozilmaydi - shu ro'yxatdan tanlanadi.
# ==========================


LESSON_MINUTES = 45
BREAK_MINUTES = 5

DAY_START = 8 * 60          # 08:00
DAY_END = 17 * 60 + 5       # 17:05

LUNCH_START = 12 * 60 + 5   # 12:05
LUNCH_END = 13 * 60         # 13:00


def minutes_to_time(minutes):
    """500 -> '08:20'"""

    return "{:02d}:{:02d}".format(minutes // 60, minutes % 60)


def _build_lesson_starts():

    starts = []

    moment = DAY_START

    while moment + LESSON_MINUTES <= DAY_END:

        # tushlik ustidan o'tib ketmasin
        if LUNCH_START <= moment < LUNCH_END or (
            moment < LUNCH_START and moment + LESSON_MINUTES > LUNCH_START
        ):
            moment = LUNCH_END
            continue

        starts.append(moment)

        moment += LESSON_MINUTES + BREAK_MINUTES

    return starts


LESSON_STARTS = _build_lesson_starts()

LESSON_TIMES = [minutes_to_time(m) for m in LESSON_STARTS]


# Haftalik akademik soat -> bitta darsning davomiyligi.
#
# soat x 45 daqiqa, so'ng 5 daqiqaga yaxlitlanadi:
#   0,5 -> 25    1 -> 45    1,5 -> 70
#   2   -> 90    3 -> 135   4   -> 180

ACADEMIC_HOURS = [0.5, 1, 1.5, 2, 3, 4]


# (akademik soat, daqiqa). 1,5 soat = 67,5 daqiqa - butun son emas,
# shuning uchun ikki variant bor: 65 (pastga) va 70 (yuqoriga).
# Nizom ikkalasini ham taqiqlamaydi, tanlov maktabniki.

LESSON_VARIANTS = [
    (0.5, 25),
    (1, 45),
    (1.5, 65),
    (1.5, 70),
    (2, 90),
    (3, 135),
    (4, 180),
]

def variant_minutes(hours):
    """Shu akademik soat uchun mumkin bo'lgan davomiyliklar: [65, 70]."""
    return [m for h, m in LESSON_VARIANTS if float(h) == float(hours)]

def is_valid_variant(hours, minutes):
    """(1.5, 65) -> True, (1.5, 67) -> False."""
    return (float(hours), int(minutes)) in [(float(h), m) for h, m in LESSON_VARIANTS]

def variant_label(hours, minutes):
    """1.5, 65 -> '1,5 soat (1 soat 5 daqiqa)'"""
    hours_val = float(hours)
    minutes_val = int(minutes)
    
    text = ("%g" % hours_val).replace(".", ",") + " soat"
    
    if minutes_val >= 60:
        rest = minutes_val % 60
        inner = str(minutes_val // 60) + " soat"
        if rest:
            inner += " " + str(rest) + " daqiqa"
    else:
        inner = str(minutes_val) + " daqiqa"
        
    return text + " (" + inner + ")"

def hours_to_minutes(hours):

    exact = float(hours) * LESSON_MINUTES

    return int((exact + 4.999) // 5 * 5)


def hours_label(hours):
    """1.5 -> '1,5 soat (1 soat 10 daqiqa)'"""
    return variant_label(hours, hours_to_minutes(hours))


def available_lesson_times(duration_minutes):
    """
    Shu davomiylikdagi dars sig'adigan boshlanish vaqtlari:
    [('08:00', '09:30'), ...]

    Tushlikka yoki kun oxiriga urilib qoladiganlari chiqarilmaydi -
    shuning uchun noto'g'ri vaqt tanlash imkoni yo'q.
    """

    result = []

    for start in LESSON_STARTS:

        end = start + duration_minutes

        if end > DAY_END:
            continue

        if start < LUNCH_START and end > LUNCH_START:
            continue

        result.append((minutes_to_time(start), minutes_to_time(end)))

    return result


def get_slot_class(slot_id):
    """Dars qaysi sinf uchun ekani."""

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        "SELECT class_name FROM schedule_slots WHERE id=?", (slot_id,)
    )

    row = cursor.fetchone()

    db.close()

    return row[0] if row else None


def scheduled_hours(teacher, subject, class_name):
    """
    Shu o'qituvchi shu fandan shu sinfga haftasiga nechta akademik
    soat qo'ygan.

    Reja normasiga yetdimi yoki yana qoldimi - shuni bilish uchun.
    """

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        """
        SELECT COALESCE(duration_minutes, ?)
        FROM schedule_slots
        WHERE teacher=? AND subject=? AND COALESCE(class_name,'')=?
        """,
        (DEFAULT_DURATION, teacher, subject, str(class_name or ""))
    )

    total = sum(row[0] for row in cursor.fetchall())

    db.close()

    # daqiqadan akademik soatga qaytaramiz
    return round(total / float(LESSON_MINUTES) * 2) / 2.0

# ==========================
# EXCEL'DAGI FAN NOMLARI
# ==========================
#
# services/schedule_import.py fayldan fan nomini o'qiydi.
# Tanimaganini taxmin qilib qo'ymaydi - o'qituvchidan so'raydi,
# javob esa shu yerga yoziladi (migrations/004_fan_nomlari.sql).
#
# Lug'at butun maktab uchun umumiy: bitta o'qituvchi "Jo'rnavoz;il"
# nimani anglatishini aytsa, boshqasining faylida ham ishlaydi.


def get_subject_aliases():
    """{"jo'rnavoz;il": "Jo'rnavozlik", ...}"""

    db = connect()
    cursor = db.cursor()

    cursor.execute("SELECT alias, subject FROM subject_aliases")

    rows = cursor.fetchall()

    db.close()

    return {row[0]: row[1] for row in rows}


def add_subject_alias(alias, subject, teacher=None):
    """
    Nomni lug'atga qo'shadi.

    `alias` normallashtirilgan holda kelishi kerak
    (schedule_import.normalize) - qidiruv ham shunday bo'ladi.
    """

    alias = (alias or "").strip()

    if not alias or not subject:
        return

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        """
        INSERT INTO subject_aliases (alias, subject, teacher)
        VALUES (?,?,?)
        ON CONFLICT(alias) DO UPDATE SET subject=excluded.subject
        """,
        (alias, subject, teacher)
    )

    db.commit()
    db.close()



def custom_time_fits(time, duration_minutes):
    """
    Qo'lda kiritilgan vaqt maktab kuniga sig'adimi.

    Tayyor katakchalar ro'yxati (`available_lesson_times`) har bir
    darsni 45 daqiqa deb faraz qiladi: 08:00, 08:50, 09:40...
    Haqiqiy jadvalda esa turli uzunlikdagi darslar ketma-ket
    keladi - masalan 09:40-10:50 (1,5 soat) tugagach keyingisi
    10:55 da boshlanadi. Bunday vaqt tayyor ro'yxatda yo'q.

    Shuning uchun o'qituvchi vaqtni qo'lda ham kirita oladi, biz
    esa faqat kun chegarasi va tushlikni tekshiramiz.

    (bo'ladi, sabab) qaytaradi.
    """

    # Qat'iy hh:mm. normalize_time o'zi juda erkin: "1055" ni ham,
    # "10.55" ni ham qabul qiladi, "10:5" ni esa jimgina "10:05"
    # qilib yuboradi - odam 10:50 demoqchi bo'lgan bo'lsa, dars
    # boshqa vaqtga tushib qolardi. Shuning uchun ko'rinishni
    # oldindan tekshiramiz.

    matn = str(time or "").strip()

    bo_laklar = matn.split(":")

    if (len(bo_laklar) != 2
            or not bo_laklar[0].isdigit()
            or len(bo_laklar[1]) != 2
            or not bo_laklar[1].isdigit()
            or len(bo_laklar[0]) > 2):

        return False, "Vaqtni 10:55 ko'rinishida yozing (soat:daqiqa)."

    time = normalize_time(matn)

    if not time:
        return False, "Vaqtni 10:55 ko'rinishida yozing (soat:daqiqa)."

    hour, minute = time.split(":")

    boshi = int(hour) * 60 + int(minute)

    if boshi % 5:
        return False, "Vaqt 5 daqiqaga karrali bo'lsin (masalan 10:55)."

    oxiri = boshi + int(duration_minutes or DEFAULT_DURATION)

    if boshi < DAY_START:
        return False, "Maktab " + minutes_to_time(DAY_START) + " da ochiladi."

    if oxiri > DAY_END:
        return False, (
            "Dars " + minutes_to_time(DAY_END) + " dan oshib ketadi."
        )

    # tushlik ustidan o'tib ketmasin

    if boshi < LUNCH_END and oxiri > LUNCH_START:
        return False, (
            "Tushlik vaqtiga to'g'ri keladi ("
            + minutes_to_time(LUNCH_START) + "-"
            + minutes_to_time(LUNCH_END) + ")."
        )

    return True, ""
