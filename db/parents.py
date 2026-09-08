# -*- coding: utf-8 -*-
# ==========================
# db/parents.py
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
#   db.documents: get_student_documents


# ==========================
# PARENTS
# ==========================


def add_parent(
        telegram_id,
        name,
        phone
):

    db = connect()
    cursor = db.cursor()


    cursor.execute(
        """
        INSERT OR IGNORE INTO parents
        (
        telegram_id,
        name,
        phone
        )

        VALUES (?,?,?)
        """,
        (
            telegram_id,
            name,
            phone
        )
    )


    db.commit()
    db.close()



def get_parent(telegram_id):

    db = connect()
    cursor = db.cursor()


    cursor.execute(
        """
        SELECT *
        FROM parents
        WHERE telegram_id=?
        """,
        (
            telegram_id,
        )
    )


    data = cursor.fetchone()

    db.close()

    return data



def link_parent_student(
        parent_id,
        teacher,
        student
):

    db = connect()
    cursor = db.cursor()


    cursor.execute(
        """
        INSERT INTO parent_students
        (
        parent_id,
        teacher,
        student
        )

        VALUES (?,?,?)
        """,
        (
            parent_id,
            teacher,
            student
        )
    )


    db.commit()
    db.close()



def get_parent_students(parent_id):

    db = connect()
    cursor = db.cursor()


    cursor.execute(
        """
        SELECT teacher,student
        FROM parent_students
        WHERE parent_id=?
        """,
        (parent_id,)
    )


    data = cursor.fetchall()

    db.close()

    return data


# ==========================
# PARENT DOCUMENT ACCESS
# ==========================


def get_parent_student_documents(
        teacher,
        student,
        doc_type
):

    return get_student_documents(
        teacher,
        student,
        doc_type
    )



# Eski kodlar uchun moslama

def get_parent_student_document(
        teacher,
        student,
        doc_type
):

    return get_parent_student_documents(
        teacher,
        student,
        doc_type
    )


# ==========================
# OTA-ONA - ITV (METRIKA) ORQALI TOPISH
# ==========================
#
# Ota-ona farzandini ro'yxatdan tanlamaydi (bu xavfsizsiz edi -
# har kim istalgan bolani "o'zimniki" deb belgilay olardi).
# Buning o'rniga tug'ilganlik guvohnomasidagi ITV raqamini
# kiritadi - bu raqamni faqat hujjat egasi biladi.
# ==========================


import re as _re


def _normalize_metrika(value):

    return _re.sub(r"[^A-Za-z0-9]", "", value or "").upper()


def find_students_by_metrika(query):
    """ITV raqami bo'yicha o'quvchi(lar)ni topadi: [(teacher, student), ...]"""

    target = _normalize_metrika(query)

    if not target:
        return []

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        "SELECT teacher, student, metrika FROM students "
        "WHERE COALESCE(archived, 0) = 0"
    )

    rows = cursor.fetchall()

    db.close()

    return [
        (teacher, student)
        for teacher, student, metrika in rows
        if _normalize_metrika(metrika) == target
    ]


# ==========================
# OTA-ONA ALOQASI
# ==========================


def get_parents_of_student(teacher, student):
    """[(telegram_id, name), ...] - shu o'quvchiga ulangan ota-onalar."""

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        """
        SELECT p.telegram_id, p.name
        FROM parent_students ps
        JOIN parents p ON p.id = ps.parent_id
        WHERE ps.teacher=? AND ps.student=?
          AND p.telegram_id IS NOT NULL
        """,
        (teacher, student)
    )

    data = cursor.fetchall()

    db.close()

    return data


def get_students_report_rows():
    """
    Excel ro'yxati uchun xom ma'lumot:
    [(student, class_name, department, teacher, metrika, monthly_fee), ...]

    Arxivdagilar chiqarilmaydi. Saralash reports.py da - u yerda
    sinf raqami matndan ajratiladi va alifbo tartibi qo'llanadi.
    """

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        """
        SELECT s.student,
               COALESCE(s.class_name, ''),
               COALESCE(t.department, ''),
               s.teacher,
               COALESCE(s.metrika, ''),
               COALESCE(s.monthly_fee, 0)
        FROM students s
        LEFT JOIN teachers t ON t.name = s.teacher
        WHERE COALESCE(s.archived, 0) = 0
        """
    )

    data = cursor.fetchall()

    db.close()

    return data
