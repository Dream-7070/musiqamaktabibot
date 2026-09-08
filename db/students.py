# -*- coding: utf-8 -*-
# ==========================
# db/students.py
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
#   db.parents: find_students_by_metrika


# ==========================
# STUDENTS
# ==========================


def add_student(
        teacher,
        student,
        birth_date,
        metrika,
        class_name,
        monthly_fee=0
):

    db = connect()
    cursor = db.cursor()


    cursor.execute(
        """
        INSERT INTO students
        (
        teacher,
        student,
        birth_date,
        metrika,
        class_name,
        monthly_fee
        )

        VALUES (?,?,?,?,?,?)
        """,
        (
            teacher,
            student,
            birth_date,
            metrika,
            class_name,
            monthly_fee
        )
    )


    db.commit()
    db.close()



def get_students(teacher):

    db = connect()
    cursor = db.cursor()


    cursor.execute(
        """
        SELECT student
        FROM students
        WHERE teacher=? AND COALESCE(archived, 0) = 0
        """,
        (
            teacher,
        )
    )


    data = cursor.fetchall()

    db.close()


    return [
        item[0]
        for item in data
    ]



def get_all_students():

    db = connect()
    cursor = db.cursor()


    cursor.execute(
        """
        SELECT teacher,student
        FROM students
        WHERE COALESCE(archived, 0) = 0
        """
    )


    data = cursor.fetchall()

    db.close()


    return data



def get_student_info(student, teacher):

    db = connect()
    cursor = db.cursor()


    cursor.execute(
        """
        SELECT *
        FROM students
        WHERE student=?
        AND teacher=?
        """,
        (
            student,
            teacher
        )
    )


    data = cursor.fetchone()

    db.close()

    return data



def update_student(
        old_name,
        new_name,
        teacher
):

    db = connect()
    cursor = db.cursor()


    cursor.execute(
        """
        UPDATE students
        SET student=?
        WHERE student=?
        AND teacher=?
        """,
        (
            new_name,
            old_name,
            teacher
        )
    )


    db.commit()
    db.close()



def delete_student(
        teacher,
        student
):

    db = connect()
    cursor = db.cursor()


    cursor.execute(
        """
        DELETE FROM students
        WHERE teacher=?
        AND student=?
        """,
        (
            teacher,
            student
        )
    )


    db.commit()
    db.close()
    # ==========================
# DOCUMENTS (KO'P FAYLLI)
# ==========================


def save_document(
        teacher,
        document_type,
        file_id
):

    db = connect()
    cursor = db.cursor()


    cursor.execute(
        """
        INSERT INTO documents
        (
        teacher,
        document_type,
        file_id
        )

        VALUES (?,?,?)
        """,
        (
            teacher,
            document_type,
            file_id
        )
    )


    db.commit()
    db.close()



def get_documents(
        teacher,
        document_type
):

    db = connect()
    cursor = db.cursor()


    cursor.execute(
        """
        SELECT file_id
        FROM documents
        WHERE teacher=?
        AND document_type=?
        ORDER BY id ASC
        """,
        (
            teacher,
            document_type
        )
    )


    data = cursor.fetchall()

    db.close()


    return [
        item[0]
        for item in data
    ]



def delete_document(
        teacher,
        document_type
):

    db = connect()
    cursor = db.cursor()


    cursor.execute(
        """
        DELETE FROM documents
        WHERE teacher=?
        AND document_type=?
        """,
        (
            teacher,
            document_type
        )
    )


    db.commit()
    db.close()


# ==========================
# O'QUVCHI OYLIK BADAL
# ==========================


def get_student_fee(teacher, student):

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        """
        SELECT monthly_fee
        FROM students
        WHERE teacher=? AND student=?
        """,
        (teacher, student)
    )

    row = cursor.fetchone()

    db.close()

    return row[0] if row and row[0] else 0


def set_student_fee(teacher, student, amount):

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        """
        UPDATE students
        SET monthly_fee=?
        WHERE teacher=? AND student=?
        """,
        (amount, teacher, student)
    )

    db.commit()
    db.close()


def get_department_for_teacher(name):

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        "SELECT department FROM teachers WHERE name=? LIMIT 1",
        (name,)
    )

    row = cursor.fetchone()

    db.close()

    return row[0] if row else "Boshqa"


# ==========================
# TUG'ILGANLIK GUVOHNOMASI TAKRORI
# ==========================
#
# Bitta bola bazaga ikki marta kirib qolsa - dars jadvali
# ikkiga bo'linadi, to'lovi ikki joyda hisoblanadi, ota-ona
# ITV kiritganda esa "bir nechta mos yozuv" chiqadi.
# ==========================


def find_metrika_duplicate(metrika, teacher=None,
                           exclude_teacher=None, exclude_student=None):
    """
    Shu guvohnoma raqami bo'yicha nima topilgani.

    Qaytaradi: (holat, teacher, student)

        "same_teacher"  - shu o'qituvchida allaqachon bor.
                          Bu xato: bitta bola bitta o'qituvchida
                          ikki marta turmasligi kerak.

        "other_teacher" - boshqa o'qituvchida bor. Bu XATO EMAS:
                          bola ikkinchi mutaxassislikka ham
                          kirayotgan bo'lishi mumkin (masalan
                          fortepiano va doira). Ma'lumotlarini
                          qayta yozmaslik uchun ko'chirib olamiz.

        None            - bunday raqam yo'q.
    """

    matches = find_students_by_metrika(metrika)

    other = None

    for found_teacher, found_student in matches:

        if found_teacher == exclude_teacher and found_student == exclude_student:
            continue

        if teacher and found_teacher == teacher:
            return ("same_teacher", found_teacher, found_student)

        if other is None:
            other = ("other_teacher", found_teacher, found_student)

    return other


def get_student_metrika(teacher, student):
    """O'quvchining guvohnoma raqami."""

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        "SELECT metrika FROM students WHERE teacher=? AND student=?",
        (teacher, student)
    )

    row = cursor.fetchone()

    db.close()

    return row[0] if row else None


def get_student_enrollments(teacher, student):
    """
    Shu BOLAning barcha yozuvlari: [(teacher, student), ...]

    Bola ikki mutaxassislikda o'qisa - ikkita yozuv qaytadi.
    Guvohnoma raqami bo'lmasa - faqat o'zi.
    """

    metrika = get_student_metrika(teacher, student)

    if not metrika:
        return [(teacher, student)]

    found = find_students_by_metrika(metrika)

    return found or [(teacher, student)]


# ==========================
# BADAL SUMMALARI
# ==========================
#
# Maktabda aniq belgilangan summalar. O'qituvchi o'quvchi
# qo'shayotganda yoki tahrirlayotganda shulardan birini
# tanlaydi - qo'lda yozmaydi (xato bo'lmasligi uchun).
# ==========================


MONTHLY_FEES = [123600, 82400, 86600, 57700]


# Kam ta'minlangan oilalarning bolalari badal to'lamaydi.
# monthly_fee=0 "hali kiritilmagan" degani bo'lgani uchun
# imtiyoz uchun alohida belgi kerak - -1 shu vazifani bajaradi:
# eski so'rovlar (0 yoki NULL) tegilmasdan ishlayveradi.

FEE_PRIVILEGED = -1


# tugmalarda ko'rsatiladigan to'liq tanlov ro'yxati

FEE_OPTIONS = MONTHLY_FEES + [FEE_PRIVILEGED]


def fee_label(fee):
    """Badal summasini o'qiladigan matnga aylantiradi."""

    if fee == FEE_PRIVILEGED:
        return "🎖 Imtiyozli (bepul)"

    if not fee:
        return "kiritilmagan"

    return "{:,}".format(fee).replace(",", " ") + " so'm"


# ==========================
# O'QUVCHI MA'LUMOTINI TAHRIRLASH
# ==========================


STUDENT_FIELDS = {
    "student":     "Ism-familiya",
    "birth_date":  "Tug'ilgan sana",
    "metrika":     "Tug'ilganlik guvohnomasi",
    "class_name":  "Sinf",
    "monthly_fee": "Oylik badal"
}


def update_student_field(teacher, student, field, value):
    """
    Bitta maydonni yangilaydi. field faqat STUDENT_FIELDS
    ichidan bo'lishi mumkin (SQL xavfsizligi uchun).
    """

    if field not in STUDENT_FIELDS:
        return False

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        "UPDATE students SET " + field + "=? WHERE teacher=? AND student=?",
        (value, teacher, student)
    )

    # ism o'zgarsa - bog'liq yozuvlarni ham yangilaymiz

    if field == "student":

        for table in ("student_documents", "payments", "parent_students"):
            cursor.execute(
                "UPDATE " + table + " SET student=? WHERE teacher=? AND student=?",
                (value, teacher, student)
            )

        cursor.execute(
            """
            UPDATE schedule_slot_students SET student=?
            WHERE student_teacher=? AND student=?
            """,
            (value, teacher, student)
        )

    db.commit()
    db.close()

    return True


def get_students_without_fee(teacher):
    """Badal summasi kiritilmagan o'quvchilar."""

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        """
        SELECT student FROM students
        WHERE teacher=? AND (monthly_fee IS NULL OR monthly_fee = 0)
          AND COALESCE(archived, 0) = 0
        ORDER BY student
        """,
        (teacher,)
    )

    data = [r[0] for r in cursor.fetchall()]

    db.close()

    return data


# ==========================
# O'QUVCHI ARXIVI
# ==========================


def archive_student(teacher, student, reason=""):
    """Maktabdan ketgan o'quvchini arxivga oladi (o'chirmaydi)."""

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        """
        UPDATE students
        SET archived=1, archived_at=?, archive_reason=?
        WHERE teacher=? AND student=?
        """,
        (datetime.now().strftime("%Y-%m-%d"), reason, teacher, student)
    )

    changed = cursor.rowcount

    db.commit()
    db.close()

    return changed > 0


def restore_student(teacher, student):
    """Arxivdan qaytaradi."""

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        """
        UPDATE students
        SET archived=0, archived_at=NULL, archive_reason=NULL
        WHERE teacher=? AND student=?
        """,
        (teacher, student)
    )

    changed = cursor.rowcount

    db.commit()
    db.close()

    return changed > 0


def get_archived_students(teacher=None):
    """[(teacher, student, archived_at, reason), ...]"""

    db = connect()
    cursor = db.cursor()

    if teacher:

        cursor.execute(
            """
            SELECT teacher, student, archived_at, archive_reason
            FROM students
            WHERE archived=1 AND teacher=?
            ORDER BY archived_at DESC, student
            """,
            (teacher,)
        )

    else:

        cursor.execute(
            """
            SELECT teacher, student, archived_at, archive_reason
            FROM students
            WHERE archived=1
            ORDER BY archived_at DESC, student
            """
        )

    data = cursor.fetchall()

    db.close()

    return data


def is_archived(teacher, student):

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        "SELECT COALESCE(archived, 0) FROM students WHERE teacher=? AND student=?",
        (teacher, student)
    )

    row = cursor.fetchone()

    db.close()

    return bool(row[0]) if row else False


# ==========================
# SINFLAR
# ==========================
#
# Ilgari sinf qo'lda yozilardi va baza chalkash bo'lib ketgan
# edi: "5", "5-sinf", "3 sinf", "2 - sinf", hatto "4 sonf" va
# "7272". Endi tayyor tugmadan tanlanadi va faqat raqam
# saqlanadi - "1" dan "7" gacha.
# ==========================


CLASS_OPTIONS = ["1", "2", "3", "4", "5", "6", "7"]


def class_button_label(value):
    return str(value) + "-sinf"
