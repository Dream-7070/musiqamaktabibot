# -*- coding: utf-8 -*-
# ==========================
# db/audit.py
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
# O'ZGARISHLAR TARIXI
# ==========================
#
# 17 (kelajakda 58) kishi bitta bazani tahrirlaydi. To'lov
# summasi o'zgarsa yoki o'quvchi yo'qolsa - kim qilganini
# bilish kerak.
# ==========================


def log_action(actor, action, target="", details="", actor_role="o'qituvchi"):
    """Yozuv qo'shadi. Hech qachon asosiy amalni to'xtatmaydi."""

    try:

        db = connect()
        cursor = db.cursor()

        cursor.execute(
            """
            INSERT INTO audit_log (at, actor, actor_role, action, target, details)
            VALUES (?,?,?,?,?,?)
            """,
            (
                datetime.now().strftime("%Y-%m-%d %H:%M"),
                actor or "?",
                actor_role,
                action,
                target,
                details
            )
        )

        db.commit()
        db.close()

    except Exception:
        # tarix yozilmagani uchun ish to'xtamasin
        pass


def get_audit_log(limit=50, query=None):
    """[(at, actor, actor_role, action, target, details), ...] - yangisi birinchi."""

    db = connect()
    cursor = db.cursor()

    if query:

        like = "%" + query + "%"

        cursor.execute(
            """
            SELECT at, actor, actor_role, action, target, details
            FROM audit_log
            WHERE actor LIKE ? OR target LIKE ? OR action LIKE ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (like, like, like, limit)
        )

    else:

        cursor.execute(
            """
            SELECT at, actor, actor_role, action, target, details
            FROM audit_log
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,)
        )

    data = cursor.fetchall()

    db.close()

    return data
