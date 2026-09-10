# -*- coding: utf-8 -*-
# ==========================
# db/core.py
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
#   db.subjects: ensure_subjects_table
#   db.schedule: ensure_concertmaster_table


# ==========================
# DATABASE
# ==========================

import sqlite3

from datetime import datetime


DB_NAME = "school.db"


# ==========================
# MENYU MATNLARI (bekor qilishni aniqlash uchun)
# ==========================
#
# `bot.register_next_step_handler` foydalanuvchining KEYINGI matnli
# xabarini kutadi - qaysi tugma bosilgan bo'lishidan qat'i nazar.
# Foydalanuvchi ism/sana kabi narsa kiritish o'rniga pastki doimiy
# menyudan biror tugmani bossa (masalan "⬅️ Ortga"), o'sha tugma
# matni xatolik bilan maʼlumot sifatida bazaga yozilib ketishi
# mumkin edi.
#
# Bu ro'yxat - ilovadagi barcha pastki menyu (ReplyKeyboardMarkup)
# tugmalarining matni. Next-step qadamlari shu ro'yxatga qarshi
# tekshiradi va mos kelsa - kiritishni bekor qiladi.
#
# Faqat pastki DOIMIY menyu (types.KeyboardButton) tegishli -
# Inline tugmalar bosilganda matn umuman yuborilmaydi (callback
# keladi), shuning uchun ular bu yerda yo'q.

MENU_BUTTON_TEXTS = frozenset([
    "✅ Tugatish",
    "✏️ O'qituvchi tahrirlash",
    "✏️ Tahrirlash",
    "➕ Farzand qo'shish",
    "➕ O'qituvchi qo'shish",
    "➕ O'quvchi qo'shish",
    "⬅️ Ortga",
    "👤 Farzandim",
    "👥 Xodimlar",
    "👨‍🎓 O'quvchilar",
    "👨‍🎓 O‘quvchilar ro‘yxati",
    "👨‍🏫 O'qituvchi rejimi",
    "👨‍🏫 O'qituvchilar",
    "💳 Badal cheki",
    "💳 To'lov kvitansiyasi",
    "📅 Bugungi darslarim",
    "📂 Hujjatlar",
    "📂 O‘quvchi hujjatlari",
    "📄 Hujjatlar",
    "📄 Ota-ona arizasi",
    "📊 Oylik hisobot (Excel)",
    "📊 Statistika",
    "📋 Kutilayotgan kvitansiyalar",
    "📋 Ma'lumot",
    "📋 O'qituvchilar ro'yxati",
    "📋 O'quvchilar ro'yxati",
    "📋 O'quvchilar ro'yxati (Excel)",
    "📜 O'zgarishlar tarixi",
    "📤 O‘quvchi yuklash",
    "📤 Yuklash",
    "📥 O‘quvchi yuklab olish",
    "📥 Yuklab olish",
    "🔍 Hujjat qidirish",
    "🔑 O'qituvchi huquqlari",
    "🗄 O'quvchilar arxivi",
    "🚪 Ko'rish rejimidan chiqish",
    "🗑 O'qituvchi o'chirish",
    "🗑 O‘chirish",
    "🗑 O‘quvchi o‘chirish",
    "🗓 Dars jadvali",
    "🗓 Dars jadvallari",
    "🚪 Xonalar",
])


def is_cancel_text(text):
    """
    Matnli kiritish o'rniga menyu tugmasi bosilganmi yoki
    /cancel buyrug'i yuborilganmi.

    True bo'lsa - chaqiruvchi kiritishni bekor qilishi, saqlangan
    vaqtinchalik holatni tozalashi va foydalanuvchini xavfsiz
    menyuga qaytarishi kerak.
    """

    text = (text or "").strip()

    return text in MENU_BUTTON_TEXTS or text.lower() == "/cancel"


# ==========================
# CONNECT
# ==========================
#
# VPS da bot va Mini App (gunicorn) BIR VAQTDA shu bazaga
# yozadi. Standart sozlamada bu "database is locked" xatosiga
# olib keladi, shuning uchun:
#
#   WAL      - o'qish va yozish bir-birini bloklamaydi
#   timeout  - band bo'lsa xato bermay, 30 soniya kutadi
# ==========================


_wal_ready = False


def connect():

    global _wal_ready

    conn = sqlite3.connect(DB_NAME, timeout=30)

    conn.execute("PRAGMA busy_timeout=30000")

    if not _wal_ready:

        try:
            conn.execute("PRAGMA journal_mode=WAL")
            _wal_ready = True

        except sqlite3.Error:
            # WAL qo'llab-quvvatlanmasa ham bot ishlayveradi
            pass

    return conn


# ==========================
# CREATE TABLES
# ==========================

def create_tables():

    db = connect()
    cursor = db.cursor()


    # O'QITUVCHILAR

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS teachers(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        name TEXT,

        department TEXT

    )
    """)


    # O'QUVCHILAR

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS students(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        teacher TEXT,

        student TEXT,

        birth_date TEXT,

        metrika TEXT,

        class_name TEXT

    )
    """)


    # O'QITUVCHI HUJJATLARI

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS documents(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        teacher TEXT,

        document_type TEXT,

        file_id TEXT

    )
    """)


    # O'QUVCHI HUJJATLARI

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS student_documents(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        teacher TEXT,

        student TEXT,

        document_type TEXT,

        file_id TEXT

    )
    """)


    # OTA-ONALAR

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS parents(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        telegram_id INTEGER UNIQUE,

        name TEXT,

        phone TEXT

    )
    """)


    # OTA-ONA FARZAND

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS parent_students(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        parent_id INTEGER,

        teacher TEXT,

        student TEXT

    )
    """)


    # TO'LOVLAR

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS payments(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        teacher TEXT,

        student TEXT,

        month TEXT,

        status TEXT,

        date TEXT

    )
    """)


    # XODIMLAR (buxgalter va h.k. - o'z-o'zidan ro'yxatdan o'tadi,
    # admin tasdiqlaydi)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS staff(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        telegram_id INTEGER UNIQUE,

        role TEXT,

        full_name TEXT,

        username TEXT,

        status TEXT DEFAULT 'pending',

        -- 'localtime' - SQLite'da datetime('now') HAR DOIM UTC
        -- (TZ o'zgaruvchisi unga ta'sir qilmaydi). Eslatma:
        -- DEFAULT faqat YANGI yaratilgan bazaga tegishli,
        -- mavjud jadval ustuni eski holida qoladi.
        requested_at TEXT DEFAULT (datetime('now','localtime'))

    )
    """)


    # DARS JADVALI
    #
    # Har bir o'qituvchi o'zining haftalik "vaqt katakchalarini"
    # (kun+soat+fan+xona) tuzadi, so'ng shu katakchaga
    # o'quvchilarni (hatto boshqa o'qituvchiniki bo'lsa ham)
    # qo'shadi. Shunday qilib bitta o'quvchi bir nechta
    # o'qituvchidan yig'ilgan to'liq haftalik jadvalga ega bo'ladi.

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS schedule_slots(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        teacher TEXT,

        subject TEXT,

        day_of_week TEXT,

        time TEXT,

        room TEXT,

        duration_minutes INTEGER DEFAULT 45

    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS schedule_slot_students(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        slot_id INTEGER,

        student TEXT,

        student_teacher TEXT

    )
    """)


    db.commit()
    db.close()

    # keyinroq qo'shilgan jadvallar (fayl oxirida ta'riflangan)

    ensure_concertmaster_table()
    ensure_subjects_table()


# ==========================
# SOZLAMALAR (kalit-qiymat)
# ==========================
#
# Kichik holatlarni saqlash uchun: masalan kunlik eslatma
# oxirgi marta qachon yuborilgani. Bot qayta ishga tushsa
# ham eslatma takror yuborilmaydi.
# ==========================


def _ensure_settings_table(cursor):

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings(
            key   TEXT PRIMARY KEY,
            value TEXT
        )
    """)


def get_setting(key, default=None):

    db = connect()
    cursor = db.cursor()

    _ensure_settings_table(cursor)

    cursor.execute("SELECT value FROM settings WHERE key=?", (key,))

    row = cursor.fetchone()

    db.close()

    return row[0] if row else default


def set_setting(key, value):

    db = connect()
    cursor = db.cursor()

    _ensure_settings_table(cursor)

    cursor.execute(
        """
        INSERT INTO settings (key, value) VALUES (?,?)
        ON CONFLICT(key) DO UPDATE SET value=excluded.value
        """,
        (key, str(value))
    )

    db.commit()
    db.close()
