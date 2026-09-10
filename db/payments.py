# -*- coding: utf-8 -*-
# ==========================
# db/payments.py
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
#   db.students: FEE_PRIVILEGED


# ==========================
# PAYMENTS
# ==========================


def add_payment(
        teacher,
        student,
        month,
        status,
        date
):

    db = connect()
    cursor = db.cursor()


    cursor.execute(
        """
        INSERT INTO payments
        (
        teacher,
        student,
        month,
        status,
        date
        )

        VALUES (?,?,?,?,?)
        """,
        (
            teacher,
            student,
            month,
            status,
            date
        )
    )


    db.commit()
    db.close()



def get_student_payments(
        teacher,
        student
):

    db = connect()
    cursor = db.cursor()


    cursor.execute(
        """
        SELECT month,status,date
        FROM payments
        WHERE teacher=?
        AND student=?
        ORDER BY id DESC
        """,
        (
            teacher,
            student
        )
    )


    data = cursor.fetchall()

    db.close()

    return data



def delete_payment(
        teacher,
        student,
        month
):

    db = connect()
    cursor = db.cursor()


    cursor.execute(
        """
        DELETE FROM payments
        WHERE teacher=?
        AND student=?
        AND month=?
        """,
        (
            teacher,
            student,
            month
        )
    )


    db.commit()
    db.close()


# ==========================
# TO'LOV KVITANSIYALARI
# ==========================


def create_payment_request(
        teacher,
        student,
        month,
        amount,
        drive_file_id,
        drive_link,
        submitted_by
):

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        """
        INSERT INTO payments
        (
            teacher, student, month, status, date,
            amount, drive_file_id, drive_link,
            submitted_by, created_at
        )
        VALUES (?,?,?,'kutilmoqda',datetime('now','localtime'),?,?,?,?,datetime('now','localtime'))
        """,
        (teacher, student, month, amount, drive_file_id, drive_link, submitted_by)
    )

    row_id = cursor.lastrowid

    db.commit()
    db.close()

    return row_id


def get_payment(payment_id):

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        """
        SELECT id, teacher, student, month, status, amount,
               drive_file_id, drive_link, submitted_by, reviewed_by
        FROM payments WHERE id=?
        """,
        (payment_id,)
    )

    row = cursor.fetchone()

    db.close()

    return row


def approve_payment(payment_id, reviewed_by):
    """Qaytaradi: (teacher, student, month, submitted_by) yoki None."""

    row = get_payment(payment_id)

    if not row or row[4] != "kutilmoqda":
        return None

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        """
        UPDATE payments
        SET status='tasdiqlandi', reviewed_by=?, reviewed_at=datetime('now','localtime')
        WHERE id=?
        """,
        (reviewed_by, payment_id)
    )

    db.commit()
    db.close()

    return (row[1], row[2], row[3], row[8])


def reject_payment(payment_id, reviewed_by):
    """Qaytaradi: (teacher, student, month, submitted_by) yoki None."""

    row = get_payment(payment_id)

    if not row or row[4] != "kutilmoqda":
        return None

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        """
        UPDATE payments
        SET status='rad_etildi', reviewed_by=?, reviewed_at=datetime('now','localtime')
        WHERE id=?
        """,
        (reviewed_by, payment_id)
    )

    db.commit()
    db.close()

    return (row[1], row[2], row[3], row[8])


def get_pending_payments():
    """Buxgalter paneli uchun - hali ko'rib chiqilmagan barcha kvitansiyalar."""

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        """
        SELECT id, teacher, student, month, amount, drive_file_id, submitted_by
        FROM payments
        WHERE status='kutilmoqda'
        ORDER BY id ASC
        """
    )

    data = cursor.fetchall()

    db.close()

    return data


def has_paid_this_month(teacher, student, month):

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        """
        SELECT 1 FROM payments
        WHERE teacher=? AND student=? AND month=? AND status='tasdiqlandi'
        """,
        (teacher, student, month)
    )

    row = cursor.fetchone()

    db.close()

    return row is not None


def get_unpaid_students(teacher, month):
    """Shu oy uchun hali tasdiqlangan to'lovi yo'q o'quvchilar: [(student, fee), ...]"""

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        """
        SELECT student, COALESCE(monthly_fee, 0)
        FROM students
        WHERE teacher=? AND COALESCE(archived, 0) = 0
        """,
        (teacher,)
    )

    all_students = cursor.fetchall()

    cursor.execute(
        """
        SELECT student FROM payments
        WHERE teacher=? AND month=? AND status='tasdiqlandi'
        """,
        (teacher, month)
    )

    paid = {r[0] for r in cursor.fetchall()}

    db.close()

    return [
        (student, fee)
        for student, fee in all_students
        if student not in paid and fee != FEE_PRIVILEGED
    ]


def get_monthly_debt_rows(month):
    """
    Direktor hisobot uchun xom ma'lumot:
    [(teacher, department, student, fee, to'langanmi, imtiyozlimi), ...]
    """

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        """
        SELECT teacher, student, COALESCE(monthly_fee, 0)
        FROM students
        WHERE COALESCE(archived, 0) = 0
        ORDER BY teacher, student
        """
    )

    students = cursor.fetchall()

    cursor.execute(
        """
        SELECT teacher, student FROM payments
        WHERE month=? AND status='tasdiqlandi'
        """,
        (month,)
    )

    paid = {(r[0], r[1]) for r in cursor.fetchall()}

    cursor.execute("SELECT name, department FROM teachers")

    dept_map = dict(cursor.fetchall())

    db.close()

    rows = []

    for teacher, student, fee in students:

        privileged = (fee == FEE_PRIVILEGED)

        rows.append((
            teacher,
            dept_map.get(teacher, "Boshqa"),
            student,
            0 if privileged else fee,
            privileged or (teacher, student) in paid,
            privileged
        ))

    return rows



def get_teacher_chat_id(name):
    """O'qituvchining Telegram chat_id si - bog'lanmagan bo'lsa None."""

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        """
        SELECT telegram_id FROM teachers
        WHERE name=? AND status='approved' AND telegram_id IS NOT NULL
        LIMIT 1
        """,
        (name,)
    )

    row = cursor.fetchone()

    db.close()

    return row[0] if row else None


def get_approved_teacher_accounts():
    """Eslatma yuborish uchun: [(name, telegram_id), ...] - faqat bog'langanlar."""

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        "SELECT name, telegram_id FROM teachers WHERE status='approved' AND telegram_id IS NOT NULL"
    )

    data = cursor.fetchall()

    db.close()

    return data
