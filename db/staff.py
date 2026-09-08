# -*- coding: utf-8 -*-
# ==========================
# db/staff.py
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
# XODIMLAR (BUXGALTER)
# ==========================
#
#   status:
#     pending  - so'rov yuborilgan, admin javobini kutmoqda
#     approved - tasdiqlangan
#     rejected - rad etilgan
# ==========================


def request_staff(telegram_id, role, full_name, username):
    """
    So'rov yuboradi. Qaytaradi:
      "ok"       - yangi so'rov yaratildi
      "already"  - allaqachon tasdiqlangan
      "pending"  - so'rov ko'rib chiqilmoqda
    """

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        "SELECT id, status FROM staff WHERE telegram_id=? AND role=?",
        (telegram_id, role)
    )

    row = cursor.fetchone()

    if row:

        _, status = row

        if status == "approved":
            db.close()
            return "already"

        if status == "pending":
            db.close()
            return "pending"

        # rejected bo'lgan bo'lsa - qayta so'rov beradi

        cursor.execute(
            """
            UPDATE staff
            SET status='pending', full_name=?, username=?, requested_at=datetime('now')
            WHERE id=?
            """,
            (full_name, username, row[0])
        )

    else:

        cursor.execute(
            """
            INSERT INTO staff (telegram_id, role, full_name, username, status)
            VALUES (?,?,?,?,'pending')
            """,
            (telegram_id, role, full_name, username)
        )

    db.commit()
    db.close()

    return "ok"


def get_staff_request(telegram_id):

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        """
        SELECT id, telegram_id, role, full_name, username, status
        FROM staff WHERE telegram_id=?
        """,
        (telegram_id,)
    )

    row = cursor.fetchone()

    db.close()

    return row


def approve_staff(telegram_id):
    """Qaytaradi: (telegram_id, full_name) yoki None."""

    row = get_staff_request(telegram_id)

    if not row or row[5] != "pending":
        return None

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        "UPDATE staff SET status='approved' WHERE telegram_id=?",
        (telegram_id,)
    )

    db.commit()
    db.close()

    return (row[1], row[3])


def reject_staff(telegram_id):
    """Qaytaradi: telegram_id yoki None."""

    row = get_staff_request(telegram_id)

    if not row or row[5] != "pending":
        return None

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        "UPDATE staff SET status='rejected' WHERE telegram_id=?",
        (telegram_id,)
    )

    db.commit()
    db.close()

    return row[1]


def is_staff(telegram_id, role):

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        "SELECT 1 FROM staff WHERE telegram_id=? AND role=? AND status='approved'",
        (telegram_id, role)
    )

    row = cursor.fetchone()

    db.close()

    return row is not None


def get_staff_ids(role):

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        "SELECT telegram_id FROM staff WHERE role=? AND status='approved'",
        (role,)
    )

    data = [r[0] for r in cursor.fetchall()]

    db.close()

    return data


# ==========================
# XODIMLARNI ADMIN QO'SHADI
# ==========================


STAFF_ROLES = {
    "buxgalter": "🧮 Buxgalter",
    "direktor":  "🏫 Direktor",
    "yordamchi": "🤝 Yordamchi"
}


def add_staff_directly(telegram_id, role, full_name):
    """Admin qo'shadi - tasdiq talab qilinmaydi, darhol faol."""

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        """
        INSERT INTO staff (telegram_id, role, full_name, status)
        VALUES (?,?,?,'approved')
        ON CONFLICT(telegram_id) DO UPDATE SET
            role=excluded.role,
            full_name=excluded.full_name,
            status='approved'
        """,
        (telegram_id, role, full_name)
    )

    db.commit()
    db.close()


def list_staff():
    """[(id, telegram_id, role, full_name, status), ...]"""

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        """
        SELECT id, telegram_id, role, COALESCE(full_name, ''), status
        FROM staff
        ORDER BY role, full_name
        """
    )

    data = cursor.fetchall()

    db.close()

    return data


def remove_staff(staff_id):
    """Qaytaradi: (telegram_id, role, full_name) yoki None."""

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        "SELECT telegram_id, role, COALESCE(full_name,'') FROM staff WHERE id=?",
        (staff_id,)
    )

    row = cursor.fetchone()

    if not row:
        db.close()
        return None

    cursor.execute("DELETE FROM staff WHERE id=?", (staff_id,))

    db.commit()
    db.close()

    return row


def get_staff_role(telegram_id):
    """Tasdiqlangan xodimning roli yoki None."""

    db = connect()
    cursor = db.cursor()

    cursor.execute(
        "SELECT role FROM staff WHERE telegram_id=? AND status='approved'",
        (telegram_id,)
    )

    row = cursor.fetchone()

    db.close()

    return row[0] if row else None
