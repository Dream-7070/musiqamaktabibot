# -*- coding: utf-8 -*-
# ==========================
# db/teachers.py
# ==========================
#
# Bu fayl ilgari database.py ning bir qismi edi (5100+ satr).
# database.py hozir FASAD - u shu paketdagi hamma narsani
# qayta eksport qiladi, shuning uchun `from database import X`
# hamma joyda o'zgarishsiz ishlayveradi.
#
# ==========================


import sqlite3

from datetime import datetime

# Bu modul quyidagi modullardagi nomlarni ishlatadi
# (database.py fasadi ularni yuklashda joylashtiradi):
#   db.core: connect


# ==========================
# TEACHERS
# ==========================


def add_teacher(name, department):

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        """
        INSERT INTO teachers
        (
        name,
        department
        )
        VALUES (?,?)
        """,
        (
            name,
            department
        )
    )

    db.commit()
    db.close()



def get_all_teachers():

    db = connect()
    cursor = db.cursor()


    cursor.execute(
        """
        SELECT name,department
        FROM teachers
        """
    )


    data = cursor.fetchall()

    db.close()

    return data



def move_teacher_department(teacher_id, new_department):
    """
    O'qituvchini boshqa bo'limga ko'chiradi.
    Bog'lanish (telegram_id, status) saqlanib qoladi.

    Qaytaradi: (name, old_department) yoki:
      None      - o'qituvchi topilmadi
      "exists"  - yangi bo'limda shu ism allaqachon bor
    """

    row = get_teacher_by_id(teacher_id)

    if not row:
        return None

    name = row[1]
    old_department = row[2]

    if old_department == new_department:
        return (name, old_department)

    if teacher_exists(name, new_department):
        return "exists"

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        "UPDATE teachers SET department=? WHERE id=?",
        (new_department, teacher_id)
    )

    # hujjatlar teacher nomi orqali bog'langan, bo'lim ustuni
    # faqat Drive papka yo'lini tanlashda ishlatiladi - shu yerda
    # yangilash shart emas, chunki mavjud fayllar joyida qoladi

    db.commit()
    db.close()

    return (name, old_department)


def rename_teacher(teacher_id, new_name):
    """
    O'qituvchini id bo'yicha tahrirlaydi - ism to'qnashuvi bo'lmaydi.
    Bog'liq o'quvchilar yozuvidagi ismni ham yangilaydi.
    """

    row = get_teacher_by_id(teacher_id)

    if not row:
        return None

    old_name = row[1]

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        "UPDATE teachers SET name=? WHERE id=?",
        (new_name, teacher_id)
    )

    cursor.execute(
        "UPDATE students SET teacher=? WHERE teacher=?",
        (new_name, old_name)
    )

    db.commit()
    db.close()

    return old_name



def update_teacher(old_name, new_name):

    db = connect()
    cursor = db.cursor()


    cursor.execute(
        """
        UPDATE teachers
        SET name=?
        WHERE name=?
        """,
        (
            new_name,
            old_name
        )
    )


    cursor.execute(
        """
        UPDATE students
        SET teacher=?
        WHERE teacher=?
        """,
        (
            new_name,
            old_name
        )
    )


    db.commit()
    db.close()



def delete_teacher(name):

    db = connect()
    cursor = db.cursor()


    cursor.execute(
        """
        DELETE FROM teachers
        WHERE name=?
        """,
        (
            name,
        )
    )


    db.commit()
    db.close()


# ==========================
# O'QITUVCHI RO'YXATI (bo'lim / ism)
# ==========================
#
# Ro'yxat endi fayldan emas, bazadan o'qiladi - shuning uchun
# admin panelidan qo'shilgan yangi o'qituvchi darhol ko'rinadi,
# botni qayta ishga tushirish shart emas.
# ==========================


def seed_teachers(pairs):
    """
    Boshlang'ich ro'yxatni bazaga yozadi (faqat yo'q bo'lganlarini).
    pairs: [(name, department), ...]
    Bir necha marta chaqirish xavfsiz.
    """

    db = connect()
    cursor = db.cursor()

    added = 0

    for name, department in pairs:

        cursor.execute(
            "SELECT id FROM teachers WHERE name=? AND department=?",
            (name, department)
        )

        if cursor.fetchone():
            continue

        cursor.execute(
            "INSERT INTO teachers (name, department, status) VALUES (?,?,'open')",
            (name, department)
        )

        added += 1

    db.commit()
    db.close()

    return added


def get_departments():
    """Bo'limlar ro'yxatini birinchi qo'shilgan tartibida qaytaradi."""

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        """
        SELECT department
        FROM teachers
        GROUP BY department
        ORDER BY MIN(id)
        """
    )

    data = [row[0] for row in cursor.fetchall()]

    db.close()


    # Hali o'qituvchisi yo'q bo'lim ham ro'yxatda tursin -
    # aks holda unga birinchi o'qituvchini qo'shib bo'lmaydi
    # (Nazariya bo'limi shunday holatda edi).

    try:
        from data.teachers import departments as seeded

        for name in seeded:
            if name not in data:
                data.append(name)

    except ImportError:
        pass

    return data


def get_teachers_by_department(department):
    """Bo'lim ichidagi o'qituvchilar (id, name, status)."""

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        """
        SELECT id, name, status
        FROM teachers
        WHERE department=?
        ORDER BY id ASC
        """,
        (department,)
    )

    data = cursor.fetchall()

    db.close()

    return data


def get_teacher_by_name(name, department):

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        """
        SELECT id, name, department, telegram_id, status,
               pending_telegram_id, pending_username, pending_full_name
        FROM teachers
        WHERE name=? AND department=?
        """,
        (name, department)
    )

    row = cursor.fetchone()

    db.close()

    return row


def get_teacher_by_id(teacher_id):

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        """
        SELECT id, name, department, telegram_id, status,
               pending_telegram_id, pending_username, pending_full_name
        FROM teachers
        WHERE id=?
        """,
        (teacher_id,)
    )

    row = cursor.fetchone()

    db.close()

    return row


def find_teacher_binding(telegram_id):
    """Shu Telegram ID tasdiqlangan o'qituvchimi - bo'lsa (name, department) qaytaradi."""

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        """
        SELECT name, department
        FROM teachers
        WHERE telegram_id=? AND status='approved'
        """,
        (telegram_id,)
    )

    row = cursor.fetchone()

    db.close()

    return row


def teacher_exists(name, department):

    return get_teacher_by_name(name, department) is not None


# ==========================
# AKKAUNT SO'ROVI (tasdiqlash oqimi)
# ==========================


def request_teacher_binding(teacher_id, telegram_id, username, full_name):
    """
    So'rov yuboradi. Qaytaradi:
      "ok"            - so'rov yuborildi, admin javobini kutmoqda
      "already_mine"  - so'rovchi allaqachon shu o'qituvchiga tasdiqlangan
      "taken"         - boshqa kimdir allaqachon tasdiqlangan
      "pending_self"  - so'rovchining o'zi allaqachon so'rov yuborgan
      "pending_other" - boshqa kimdir so'rov yuborib, javob kutilmoqda
    """

    row = get_teacher_by_id(teacher_id)

    if not row:
        return "not_found"

    _, name, department, telegram_id_db, status, pending_id, _, _ = row

    if status == "approved":

        if telegram_id_db == telegram_id:
            return "already_mine"

        return "taken"

    if status == "pending":

        if pending_id == telegram_id:
            return "pending_self"

        return "pending_other"

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        """
        UPDATE teachers
        SET status='pending',
            pending_telegram_id=?,
            pending_username=?,
            pending_full_name=?
        WHERE id=?
        """,
        (telegram_id, username, full_name, teacher_id)
    )

    db.commit()
    db.close()

    return "ok"


def approve_teacher_binding(teacher_id):
    """Tasdiqlaydi. Qaytaradi: (telegram_id, name, department) yoki None."""

    row = get_teacher_by_id(teacher_id)

    if not row or row[4] != "pending":
        return None

    _, name, department, _, _, pending_id, _, _ = row

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        """
        UPDATE teachers
        SET status='approved',
            telegram_id=?,
            pending_telegram_id=NULL,
            pending_username=NULL,
            pending_full_name=NULL
        WHERE id=?
        """,
        (pending_id, teacher_id)
    )

    db.commit()
    db.close()

    return (pending_id, name, department)


def reject_teacher_binding(teacher_id):
    """Rad etadi. Qaytaradi: pending_telegram_id yoki None."""

    row = get_teacher_by_id(teacher_id)

    if not row or row[4] != "pending":
        return None

    pending_id = row[5]

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        """
        UPDATE teachers
        SET status='open',
            pending_telegram_id=NULL,
            pending_username=NULL,
            pending_full_name=NULL
        WHERE id=?
        """,
        (teacher_id,)
    )

    db.commit()
    db.close()

    return pending_id


def unbind_teacher(teacher_id):
    """Admin uchun: mavjud bog'lanishni bekor qiladi (o'qituvchi ishdan ketsa)."""

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        """
        UPDATE teachers
        SET status='open',
            telegram_id=NULL,
            pending_telegram_id=NULL,
            pending_username=NULL,
            pending_full_name=NULL
        WHERE id=?
        """,
        (teacher_id,)
    )

    db.commit()
    db.close()


# ==========================
# O'QITUVCHINI ISM BO'YICHA QIDIRISH
# ==========================
#
# O'qituvchi botga kirganda butun maktab tuzilmasini
# ko'rmasligi kerak - u faqat o'z ismini yozadi.
# ==========================


def search_teachers_by_name(query, limit=10):
    """[(id, name, department, status), ...]"""

    text = (query or "").strip()

    if len(text) < 3:
        return []

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        """
        SELECT id, name, department, COALESCE(status, 'open')
        FROM teachers
        WHERE name LIKE ?
        ORDER BY name
        LIMIT ?
        """,
        ("%" + text + "%", limit)
    )

    data = cursor.fetchall()

    db.close()

    return data


# ==========================
# O'QITUVCHI TURLARI VA HUQUQLARI
# ==========================
#
# Tur - bu tayyor shablon: admin turni tanlaydi, huquqlar
# avtomatik qo'yiladi. Keyin kerak bo'lsa bitta huquqni
# alohida yoqib/o'chirib qo'yish mumkin (masalan pianinochi
# ham mutaxassislik o'qituvchisi, ham jo'rnavoz bo'lishi
# mumkin).
# ==========================


TEACHER_TYPES = {
    "mutaxassislik": {
        "label": "\U0001F3AF Mutaxassislik o'qituvchisi",
        "hint": "O'z o'quvchilari bor, jadval tuzadi, jo'rnavozlik ham qila oladi",
        "can_add_students": 1,
        "can_manage_schedule": 1,
        "can_be_concertmaster": 1
    },
    "umumiy": {
        "label": "\U0001F4D6 Umumiy fan o'qituvchisi",
        "hint": "Solfedjio, san'at tarixi kabi guruhli darslar. O'z o'quvchisi yo'q",
        "can_add_students": 0,
        "can_manage_schedule": 1,
        "can_be_concertmaster": 0
    },
    "jornavoz": {
        "label": "\U0001F3B9 Jo'rnavoz",
        "hint": "Boshqalarning darslarida jo'rnavozlik qiladi, o'zi jadval tuzmaydi",
        "can_add_students": 0,
        "can_manage_schedule": 0,
        "can_be_concertmaster": 1
    }
}


PERMISSION_LABELS = {
    "can_add_students":     "\U0001F468\u200D\U0001F393 O'quvchi qo'sha oladi",
    "can_manage_schedule":  "\U0001F5D3 Dars jadvali tuza oladi",
    "can_be_concertmaster": "\U0001F3B9 Jo'rnavozlik qila oladi"
}


def get_teacher_permissions(name):
    """
    {'type':..., 'can_add_students':bool, ...}

    O'qituvchi topilmasa yoki huquqlar hali belgilanmagan bo'lsa -
    hammasi ochiq (eski holat buzilmasin).
    """

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        """
        SELECT teacher_type,
               COALESCE(can_add_students, 1),
               COALESCE(can_manage_schedule, 1),
               COALESCE(can_be_concertmaster, 1)
        FROM teachers
        WHERE name=?
        LIMIT 1
        """,
        (name,)
    )

    row = cursor.fetchone()

    db.close()

    if not row:
        return {
            "type": None,
            "can_add_students": True,
            "can_manage_schedule": True,
            "can_be_concertmaster": True
        }

    return {
        "type": row[0],
        "can_add_students": bool(row[1]),
        "can_manage_schedule": bool(row[2]),
        "can_be_concertmaster": bool(row[3])
    }


def can(name, permission):
    """Qisqa yordamchi: can(teacher, 'can_add_students')."""

    return get_teacher_permissions(name).get(permission, True)


def set_teacher_type(name, type_key):
    """Turni qo'yadi va huquqlarni shu tur bo'yicha to'ldiradi."""

    preset = TEACHER_TYPES.get(type_key)

    if not preset:
        return False

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        """
        UPDATE teachers
        SET teacher_type=?,
            can_add_students=?,
            can_manage_schedule=?,
            can_be_concertmaster=?
        WHERE name=?
        """,
        (
            type_key,
            preset["can_add_students"],
            preset["can_manage_schedule"],
            preset["can_be_concertmaster"],
            name
        )
    )

    changed = cursor.rowcount

    db.commit()
    db.close()

    return changed > 0


def toggle_teacher_permission(name, permission):
    """Bitta huquqni teskarisiga o'giradi. Yangi qiymatni qaytaradi."""

    if permission not in PERMISSION_LABELS:
        return None

    current = get_teacher_permissions(name)[permission]

    new_value = 0 if current else 1

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        "UPDATE teachers SET " + permission + "=? WHERE name=?",
        (new_value, name)
    )

    db.commit()
    db.close()

    return bool(new_value)


def get_teachers_without_type():
    """Turi hali belgilanmagan tasdiqlangan o'qituvchilar."""

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        """
        SELECT name, department FROM teachers
        WHERE status='approved' AND (teacher_type IS NULL OR teacher_type='')
        ORDER BY name
        """
    )

    data = cursor.fetchall()

    db.close()

    return data
