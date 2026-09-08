# -*- coding: utf-8 -*-
# ==========================
# db/miniapp.py
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
# MINI APP UCHUN QO'SHIMCHA
# ==========================


def get_parent_students_with_id(parent_id):
    """Ota-ona kartochkasi uchun: [(link_id, teacher, student), ...]"""

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        """
        SELECT id, teacher, student
        FROM parent_students
        WHERE parent_id=?
        """,
        (parent_id,)
    )

    data = cursor.fetchall()

    db.close()

    return data


def get_parent_student_link(link_id):
    """Bitta bog'lanish yozuvi: (id, parent_id, teacher, student) yoki None."""

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        """
        SELECT id, parent_id, teacher, student
        FROM parent_students
        WHERE id=?
        """,
        (link_id,)
    )

    row = cursor.fetchone()

    db.close()

    return row


def get_student_payment_history(teacher, student):
    """To'liq tarix: [(month, status, amount, date), ...] - eng yangisi birinchi."""

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        """
        SELECT month, status, COALESCE(amount, 0), date
        FROM payments
        WHERE teacher=? AND student=?
        ORDER BY id DESC
        """,
        (teacher, student)
    )

    data = cursor.fetchall()

    db.close()

    return data


# ==========================
# MINI APP - QO'SHIMCHA (admin/o'qituvchi ekranlari)
# ==========================


def get_slots_for_day(day_of_week):
    """
    Bugungi kunning BARCHA o'qituvchilaridagi darslari:
    [(id, teacher, subject, time, room, duration_minutes), ...]
    """

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        """
        SELECT id, teacher, subject, time, room, COALESCE(duration_minutes, 45)
        FROM schedule_slots
        WHERE day_of_week=?
        ORDER BY time
        """,
        (day_of_week,)
    )

    data = cursor.fetchall()

    db.close()

    return data


def get_slot_student_row(row_id):
    """(id, slot_id, student, student_teacher) yoki None - egalikni tekshirish uchun."""

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        """
        SELECT id, slot_id, student, student_teacher
        FROM schedule_slot_students
        WHERE id=?
        """,
        (row_id,)
    )

    row = cursor.fetchone()

    db.close()

    return row
