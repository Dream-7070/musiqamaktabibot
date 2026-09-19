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


def approve_payment(payment_id, reviewed_by, received=None):
    """Qaytaradi: (teacher, student, month, submitted_by) yoki None."""

    row = get_payment(payment_id)

    if not row or row[4] != "kutilmoqda":
        return None

    db = connect()
    cursor = db.cursor()

    if received is not None:
        cursor.execute(
            """
            UPDATE payments
            SET status='tasdiqlandi', reviewed_by=?, reviewed_at=datetime('now','localtime'), received_amount=?
            WHERE id=?
            """,
            (reviewed_by, received, payment_id)
        )
    else:
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


# ==========================
# BANK KOMISSIYASI
# ==========================
#
# Ota-ona 123 600 so'm to'laydi, maktab hisobiga 123 229,20 tushadi -
# bank 0,3% ushlab qoladi. Bazadagi summa SHU SABABLI o'zgarmaydi:
# badal - ota-ona to'laydigan summa, komissiya esa bankning ishi.
# Ikkisi aralashsa qarz hisobi buziladi (bola to'la to'lagan bo'lsa
# ham qarzdor bo'lib qolardi).
#
# Foiz sozlamada turadi - bank yoki to'lov turi o'zgarsa, kodga
# tegmasdan buxgalterning o'zi yangilaydi.
# ==========================


COMMISSION_KEY = "payment_commission_percent"

DEFAULT_COMMISSION = 0.3


def get_commission_percent():
    """Sozlamadagi komissiya foizi. Yo'q yoki buzuq bo'lsa - 0.3."""

    qiymat = get_setting(COMMISSION_KEY)

    if qiymat is None:
        return DEFAULT_COMMISSION

    try:
        return float(qiymat)

    except (TypeError, ValueError):
        return DEFAULT_COMMISSION


def set_commission_percent(value):
    """Qaytaradi: (True, foiz) yoki (False, sabab)."""

    try:
        foiz = float(value)

    except (TypeError, ValueError):
        return False, "Noto'g'ri qiymat"

    if foiz < 0 or foiz > 100:
        return False, "Foiz 0 va 100 oralig'ida bo'lishi kerak"

    set_setting(COMMISSION_KEY, str(foiz))

    return True, foiz


def net_amount(amount, percent=None):
    """Komissiya ayirilgandan keyin bankka tushadigan summa."""

    if percent is None:
        percent = get_commission_percent()

    return round(float(amount) * (1 - float(percent) / 100), 2)


def commission_amount(amount, percent=None):
    """Bank ushlab qoladigan summa."""

    if percent is None:
        percent = get_commission_percent()

    return round(float(amount) - net_amount(amount, percent), 2)

import math

def gross_amount(net_target, percent=None):
    """
    Komissiya ushlangandan keyin net_target tushishi uchun qancha to'lash kerakligini qaytaradi.
    Masalan: 123600 -> 123972
    """
    if percent is None:
        percent = get_commission_percent()
    return math.ceil(float(net_target) / (1 - float(percent) / 100))

def get_month_paid_total(month):
    db = connect()
    cursor = db.cursor()
    cursor.execute(
        "SELECT COUNT(*), COALESCE(SUM(amount),0) FROM payments WHERE month=? AND status='tasdiqlandi'",
        (month,)
    )
    row = cursor.fetchone()
    db.close()
    return row

def suggested_received(amount, percent=None):
    return net_amount(amount, percent)

def get_month_received_total(month):
    db = connect()
    cursor = db.cursor()
    cursor.execute(
        "SELECT amount, received_amount FROM payments WHERE month=? AND status='tasdiqlandi'",
        (month,)
    )
    rows = cursor.fetchall()
    db.close()
    
    total = 0
    for r in rows:
        if r[1] is not None:
            total += r[1]
        else:
            total += net_amount(r[0])
            
    return (len(rows), total)

def get_reviewed_payments(month=None, status=None, limit=200):
    db = connect()
    cursor = db.cursor()
    query = """
        SELECT id, teacher, student, month, amount, status, reviewed_by, reviewed_at, drive_file_id, received_amount
        FROM payments
        WHERE status IN ('tasdiqlandi', 'rad_etildi')
    """
    params = []
    if month:
        query += " AND month=?"
        params.append(month)
    if status:
        query += " AND status=?"
        params.append(status)
        
    query += " ORDER BY reviewed_at DESC, id DESC LIMIT ?"
    params.append(limit)
    
    cursor.execute(query, tuple(params))
    data = cursor.fetchall()
    db.close()
    return data

def get_payment_months():
    db = connect()
    cursor = db.cursor()
    cursor.execute("SELECT DISTINCT month FROM payments ORDER BY month DESC")
    data = [r[0] for r in cursor.fetchall()]
    db.close()
    return data
