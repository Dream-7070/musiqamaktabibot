# -*- coding: utf-8 -*-
# ==========================
# db/subjects.py
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
#   db.students: get_department_for_teacher


# ==========================
# FANLAR
# ==========================
#
# Umumiy fanlar (teacher IS NULL) hammaga ko'rinadi.
# O'qituvchi o'ziga qo'shgan fanlar faqat o'ziga ko'rinadi -
# masalan Tasviriy san'atda "Rang tasvir", "Qalam tasvir".
#
# lesson_type: 'yakka' yoki 'guruh'
# ==========================


LESSON_TYPES = {
    "yakka": "👤 Yakka tartibdagi",
    "guruh": "👥 Guruhli"
}


def ensure_subjects_table():

    db = connect()
    cursor = db.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS subjects(
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            teacher     TEXT,
            name        TEXT,
            lesson_type TEXT DEFAULT 'yakka'
        )
    """)

    # umumiy fanlarni bir marta urug'lantiramiz

    cursor.execute("SELECT COUNT(*) FROM subjects WHERE teacher IS NULL")

    if cursor.fetchone()[0] == 0:

        defaults = [
            ("Mutaxassislik",   "yakka"),
            ("Solfedjio",       "guruh"),
            ("San'at tarixi",   "guruh"),
            ("Musiqa adabiyoti", "guruh"),
            ("Xor",             "guruh"),
            ("Nazariy fanlar",  "guruh"),
            ("Tanlangan fan",   "yakka")
        ]

        # "Ansambl" bu yerdan chiqarib tashlandi - reja bo'yicha u
        # faqat ba'zi mutaxassisliklarda bor (cholg'u yo'nalishlari)
        # va aynan o'sha yerda "yakka" tartibda, hammaga umumiy
        # "guruh" fan sifatida noto'g'ri edi. Endi kerakli
        # o'qituvchiga reja o'zi taklif qiladi (SUBJECT_TYPES orqali),
        # boshqalarga esa admin kerak bo'lsa qo'lda qo'shadi.

        cursor.executemany(
            "INSERT INTO subjects (teacher, name, lesson_type) VALUES (NULL,?,?)",
            defaults
        )

    db.commit()
    db.close()


def get_subjects_for_teacher(teacher):
    """
    Umumiy + o'ziniki:
    [(id, name, lesson_type, is_own), ...]
    """

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        """
        SELECT id, name, lesson_type, (teacher IS NOT NULL)
        FROM subjects
        WHERE teacher IS NULL OR teacher=?
        ORDER BY (teacher IS NOT NULL), name
        """,
        (teacher,)
    )

    data = cursor.fetchall()

    db.close()

    return data


def get_own_subjects(teacher):
    """Faqat o'qituvchi o'zi qo'shganlari."""

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        """
        SELECT id, name, lesson_type FROM subjects
        WHERE teacher=? ORDER BY name
        """,
        (teacher,)
    )

    data = cursor.fetchall()

    db.close()

    return data


def add_subject(teacher, name, lesson_type):
    """Allaqachon bor bo'lsa - False."""

    if lesson_type not in LESSON_TYPES:
        return False

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        """
        SELECT id FROM subjects
        WHERE name=? AND (teacher IS NULL OR teacher=?)
        """,
        (name, teacher)
    )

    if cursor.fetchone():
        db.close()
        return False

    cursor.execute(
        "INSERT INTO subjects (teacher, name, lesson_type) VALUES (?,?,?)",
        (teacher, name, lesson_type)
    )

    db.commit()
    db.close()

    return True


def delete_subject(subject_id, teacher):
    """Faqat o'zi qo'shgan fanni o'chira oladi."""

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        "DELETE FROM subjects WHERE id=? AND teacher=?",
        (subject_id, teacher)
    )

    changed = cursor.rowcount

    db.commit()
    db.close()

    return changed > 0



def rename_subject(subject_id, teacher, new_name):
    """
    Fan nomini o'zgartiradi. Faqat o'zi qo'shgan fanni.

    Dars jadvalida fan nomi matn sifatida yozilgan, shuning uchun
    shu o'qituvchining eski nomli darslari ham yangilanadi - aks
    holda ular fandan uzilib qolar edi.
    """

    new_name = (new_name or "").strip()

    if len(new_name) < 2:
        return False, "Fan nomi juda qisqa"

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        "SELECT name FROM subjects WHERE id=? AND teacher=?",
        (subject_id, teacher)
    )

    row = cursor.fetchone()

    if not row:
        db.close()
        return False, "Fan topilmadi"

    old_name = row[0]

    if old_name == new_name:
        db.close()
        return True, old_name

    # shu nomdagi fan allaqachon bormi (umumiy yoki o'ziniki)

    cursor.execute(
        """
        SELECT id FROM subjects
        WHERE name=? AND (teacher IS NULL OR teacher=?)
        """,
        (new_name, teacher)
    )

    if cursor.fetchone():
        db.close()
        return False, "Bunday nomli fan allaqachon bor"

    cursor.execute(
        "UPDATE subjects SET name=? WHERE id=? AND teacher=?",
        (new_name, subject_id, teacher)
    )

    cursor.execute(
        "UPDATE schedule_slots SET subject=? WHERE teacher=? AND subject=?",
        (new_name, teacher, old_name)
    )

    db.commit()
    db.close()

    return True, old_name


def set_subject_type(subject_id, teacher, lesson_type):
    """Yakka <-> guruhli. Faqat o'zi qo'shgan fanni."""

    if lesson_type not in LESSON_TYPES:
        return False

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        "UPDATE subjects SET lesson_type=? WHERE id=? AND teacher=?",
        (lesson_type, subject_id, teacher)
    )

    changed = cursor.rowcount

    db.commit()
    db.close()

    return changed > 0


def count_slots_using_subject(teacher, name):
    """Shu fan bo'yicha nechta dars vaqti tuzilgan."""

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        "SELECT COUNT(*) FROM schedule_slots WHERE teacher=? AND subject=?",
        (teacher, name)
    )

    count = cursor.fetchone()[0]

    db.close()

    return count

def get_subject(subject_id):
    """(id, teacher, name, lesson_type) yoki None."""

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        "SELECT id, teacher, name, lesson_type FROM subjects WHERE id=?",
        (subject_id,)
    )

    row = cursor.fetchone()

    db.close()

    return row


def get_subject_type(teacher, name):
    """
    Fan yakka tartibdami yoki guruhli - 'yakka' / 'guruh'.

    Ustuvorlik:
      1. `subjects` jadvalida aniq yozuv bo'lsa (o'qituvchining o'zi
         yoki admin belgilagan) - o'sha ishlatiladi
      2. bo'lmasa - 2026-yil o'quv rejasi shu fan haqida nima
         deyishini so'raymiz (data.curriculum.subject_type_for)
      3. u ham jim tursa - "yakka" (xavfsiz standart)
    """

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        """
        SELECT lesson_type FROM subjects
        WHERE name=? AND (teacher=? OR teacher IS NULL)
        ORDER BY (teacher IS NULL)
        LIMIT 1
        """,
        (name, teacher)
    )

    row = cursor.fetchone()

    db.close()

    if row:
        return row[0]

    from data.curriculum import subject_type_for

    department = get_department_for_teacher(teacher)

    return subject_type_for(department, name) or "yakka"


def admin_set_subject_type(teacher, name, lesson_type):
    """
    Fan turini shu bitta o'qituvchi uchun belgilaydi - admin ishlatadi.

    Umumiy yoki reja fanini o'zgartirmaydi (boshqalarga tegmaydi) -
    aynan shu o'qituvchi uchun alohida yozuv yaratadi yoki
    yangilaydi. Bu reja jim turgan holatlar uchun (masalan amaliy
    san'atdagi guruh darslari) va noto'g'ri belgilangan hollarni
    tuzatish uchun kerak.
    """

    if lesson_type not in LESSON_TYPES:
        return False

    name = (name or "").strip()

    if not name:
        return False

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        "SELECT id FROM subjects WHERE name=? AND teacher=?",
        (name, teacher)
    )

    row = cursor.fetchone()

    if row:
        cursor.execute(
            "UPDATE subjects SET lesson_type=? WHERE id=?",
            (lesson_type, row[0])
        )
    else:
        cursor.execute(
            "INSERT INTO subjects (teacher, name, lesson_type) VALUES (?,?,?)",
            (teacher, name, lesson_type)
        )

    db.commit()
    db.close()

    return True
