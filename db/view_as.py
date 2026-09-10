# -*- coding: utf-8 -*-
# ==========================
# db/view_as.py
# ==========================
#
# ADMIN - "KO'RISH REJIMI" (o'qituvchi sifatida ko'rish)
#
# Admin biror o'qituvchini tanlaydi va bot menyusi ham, Mini App
# ham unga xuddi o'sha o'qituvchida ko'rinadigan holda ochiladi
# (o'sha o'qituvchining huquqlari, jadvali, o'quvchilari).
#
# Tanlov XOTIRADA emas, BAZADA saqlanadi: bot va Mini App ikkita
# alohida jarayon (`main.py` va gunicorn), lekin bitta `school.db`
# bilan ishlaydi. Bazada saqlangani uchun botda tanlangan
# o'qituvchi Mini App'da ham ko'rinadi va bot qayta ishga
# tushganda rejim yo'qolmaydi.
#
# ==========================


import sqlite3

from datetime import datetime

# Bu modul quyidagi modullardagi nomlarni ishlatadi
# (database.py fasadi ularni yuklashda joylashtiradi):
#   db.core: connect


def _ensure_table(cursor):
    """Jadval yo'q bo'lsa yaratadi (settings jadvali kabi - migratsiyasiz)."""

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS admin_view_as(
            admin_id     INTEGER PRIMARY KEY,
            teacher_name TEXT NOT NULL,
            started_at   TEXT
        )
    """)


def set_view_as(admin_id, teacher_name):
    """Admin uchun ko'rish rejimini yoqadi (yoki boshqa o'qituvchiga almashtiradi)."""

    db = connect()
    cursor = db.cursor()

    _ensure_table(cursor)

    cursor.execute(
        """
        INSERT INTO admin_view_as (admin_id, teacher_name, started_at)
        VALUES (?,?,?)
        ON CONFLICT(admin_id) DO UPDATE SET
            teacher_name = excluded.teacher_name,
            started_at   = excluded.started_at
        """,
        (
            admin_id,
            teacher_name,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
    )

    db.commit()
    db.close()


def get_view_as(admin_id):
    """
    Admin hozir kim sifatida ko'rayotganini qaytaradi (ism), rejim
    yoqilmagan bo'lsa - None.

    O'qituvchi bazadan o'chirilgan yoki nomi o'zgargan bo'lsa rejim
    o'z-o'zidan bekor qilinadi - aks holda admin yo'q odamning
    paneliga tushib qolardi.
    """

    db = connect()
    cursor = db.cursor()

    _ensure_table(cursor)

    cursor.execute(
        "SELECT teacher_name FROM admin_view_as WHERE admin_id=?",
        (admin_id,)
    )

    row = cursor.fetchone()

    if not row:

        db.close()

        return None

    name = row[0]

    exists = False

    try:

        cursor.execute(
            "SELECT 1 FROM teachers WHERE name=? LIMIT 1",
            (name,)
        )

        exists = cursor.fetchone() is not None

    except sqlite3.Error:

        exists = False

    if not exists:

        cursor.execute(
            "DELETE FROM admin_view_as WHERE admin_id=?",
            (admin_id,)
        )

        db.commit()
        db.close()

        return None

    db.close()

    return name


def clear_view_as(admin_id):
    """Ko'rish rejimini o'chiradi - admin o'z paneliga qaytadi."""

    db = connect()
    cursor = db.cursor()

    _ensure_table(cursor)

    cursor.execute(
        "DELETE FROM admin_view_as WHERE admin_id=?",
        (admin_id,)
    )

    db.commit()
    db.close()


def get_all_view_as():
    """Hozir ko'rish rejimida turgan barcha adminlar: (admin_id, ism, vaqt)."""

    db = connect()
    cursor = db.cursor()

    _ensure_table(cursor)

    cursor.execute(
        """
        SELECT admin_id, teacher_name, started_at
        FROM admin_view_as
        ORDER BY started_at
        """
    )

    rows = cursor.fetchall()

    db.close()

    return rows
