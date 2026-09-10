# -*- coding: utf-8 -*-
# ==========================
# db/broadcasts.py
# ==========================
#
# BIR NECHTA ODAMGA YUBORILGAN XABARNI KEYIN YOPISH
#
# Tugmali xabarnoma (masalan o'qituvchi akkaunt so'rovi) bir
# vaqtning o'zida BIR NECHTA adminga yuboriladi. Biri "Tasdiqlash"
# ni bosgach, qolganlarnikida tugmalar hamon turaverardi: ikkinchi
# admin bosganda «So'rov topilmadi yoki eskirgan» chiqardi va
# xabar ikkilangandek tuyulardi.
#
# Buning uchun yuborilgan HAR BIR nusxaning (chat_id, message_id)
# si eslab qolinadi - keyin ularning hammasi natija matniga
# almashtiriladi.
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
        CREATE TABLE IF NOT EXISTS broadcast_messages(
            kind       TEXT NOT NULL,
            ref_id     INTEGER NOT NULL,
            chat_id    INTEGER NOT NULL,
            message_id INTEGER NOT NULL,
            created_at TEXT,
            PRIMARY KEY (kind, ref_id, chat_id)
        )
    """)


def remember_broadcast(kind, ref_id, chat_id, message_id):
    """
    Yuborilgan nusxani eslab qoladi.

    `kind` - xabarnoma turi ('teacher_request', 'payment'),
    `ref_id` - qaysi yozuv haqidaligi (o'qituvchi/to'lov id si).

    Xatolik bo'lsa jim o'tadi: bu faqat qulaylik uchun yuritiladigan
    daftar, uning ishlamay qolishi asosiy amalni to'xtatmasligi kerak.
    """

    db = None

    try:

        db = connect()

        cursor = db.cursor()

        _ensure_table(cursor)

        cursor.execute(
            """
            INSERT INTO broadcast_messages
                (kind, ref_id, chat_id, message_id, created_at)
            VALUES (?,?,?,?,?)
            ON CONFLICT(kind, ref_id, chat_id) DO UPDATE SET
                message_id = excluded.message_id,
                created_at = excluded.created_at
            """,
            (
                kind,
                ref_id,
                chat_id,
                message_id,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
        )

        db.commit()

    except sqlite3.Error:
        pass

    finally:

        if db:
            db.close()


def get_broadcast_copies(kind, ref_id):
    """Shu xabarnomaning barcha nusxalari: [(chat_id, message_id), ...]."""

    db = None

    try:

        db = connect()

        cursor = db.cursor()

        _ensure_table(cursor)

        cursor.execute(
            """
            SELECT chat_id, message_id
            FROM broadcast_messages
            WHERE kind=? AND ref_id=?
            """,
            (kind, ref_id)
        )

        return [(row[0], row[1]) for row in cursor.fetchall()]

    except sqlite3.Error:
        return []

    finally:

        if db:
            db.close()


def clear_broadcast(kind, ref_id):
    """Xabarnoma hal bo'lgach daftardan o'chiradi."""

    db = None

    try:

        db = connect()

        cursor = db.cursor()

        _ensure_table(cursor)

        cursor.execute(
            "DELETE FROM broadcast_messages WHERE kind=? AND ref_id=?",
            (kind, ref_id)
        )

        db.commit()

    except sqlite3.Error:
        pass

    finally:

        if db:
            db.close()


def prune_broadcasts(days=30):
    """
    Eskirgan yozuvlarni tozalaydi.

    Javobsiz qolgan xabarnomalar (hech kim tasdiqlamagan yoki rad
    etmagan) aks holda daftarda abadiy to'planib qolardi.
    """

    db = None

    try:

        db = connect()

        cursor = db.cursor()

        _ensure_table(cursor)

        cursor.execute(
            """
            DELETE FROM broadcast_messages
            WHERE created_at < datetime('now','localtime',?)
            """,
            ("-" + str(days) + " days",)
        )

        db.commit()

        return cursor.rowcount

    except sqlite3.Error:
        return 0

    finally:

        if db:
            db.close()
