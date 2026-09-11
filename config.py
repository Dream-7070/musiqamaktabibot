# -*- coding: utf-8 -*-
# ==========================
# config.py
# SOZLAMALAR - .env FAYLIDAN
# ==========================
#
# Ilgari token, admin ID va manzil shu faylning ichida yozilgan
# edi. Bitta maktab uchun bu yetarli edi, lekin bot bir nechta
# maktabda ishlaydigan bo'lgach - har maktabga alohida config.py
# tahrirlash xatoga olib keladigan yo'l.
#
# Endi hamma qiymat `.env` faylidan o'qiladi. KOD hamma maktabda
# BIR XIL bo'ladi, faqat .env farq qiladi.
#
# Namuna uchun: .env.example ni ko'ring.
#
# ==========================


import os
import sys

from dotenv import load_dotenv


BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# .env loyiha ildizida turadi. Agar yo'q bo'lsa - xato emas:
# qiymatlar tizim environment'idan ham kelishi mumkin (systemd
# `EnvironmentFile=` yoki Docker shunday beradi).

load_dotenv(os.path.join(BASE_DIR, ".env"))


# ==========================
# YORDAMCHILAR
# ==========================


def _talab(key):
    """Bo'lishi SHART bo'lgan qiymat. Yo'q bo'lsa - darhol to'xtaydi."""

    value = (os.getenv(key) or "").strip()

    if not value:
        sys.exit(
            "XATO: .env faylida " + key + " ko'rsatilmagan.\n"
            "Namuna uchun .env.example ga qarang."
        )

    return value


def _ixtiyoriy(key, default=""):

    value = os.getenv(key)

    return default if value is None else value.strip()


def _idlar(key):
    """"111,222" -> [111, 222]. Bo'sh va noto'g'ri qiymatlar tashlanadi."""

    result = []

    for part in _ixtiyoriy(key).replace(";", ",").split(","):

        part = part.strip()

        if not part:
            continue

        try:
            result.append(int(part))

        except ValueError:
            sys.exit(
                "XATO: " + key + " ichidagi '" + part
                + "' raqam emas. Telegram ID faqat raqamlardan iborat."
            )

    return result


def _yol(key, default_name):
    """
    Fayl yo'li. Nisbiy berilgan bo'lsa - loyiha papkasiga nisbatan
    hisoblanadi, shunda systemd qaysi papkadan ishga tushirishidan
    qat'i nazar bir xil fayl topiladi.
    """

    value = _ixtiyoriy(key) or default_name

    if os.path.isabs(value):
        return value

    return os.path.join(BASE_DIR, value)


# ==========================
# MAKTAB
# ==========================
#
# SCHOOL_SLUG - texnik nom: papka, servis va subdomen shundan
# yasaladi (masalan "19bmsm" -> 19bmsm.cybermate.uz).
#
# SCHOOL_NAME - foydalanuvchi ko'radigan to'liq nom. Bu qiymat
# birinchi ishga tushishda bazadagi `settings` jadvaliga ham
# yoziladi (db/school.py), shundan keyin uni admin bot orqali
# o'zgartirishi mumkin.

SCHOOL_SLUG = _ixtiyoriy("SCHOOL_SLUG", "maktab")

SCHOOL_NAME = _ixtiyoriy("SCHOOL_NAME", "Bolalar musiqa va san'at maktabi")


# ==========================
# TELEGRAM
# ==========================

TOKEN = _talab("BOT_TOKEN")

ADMIN_IDS = _idlar("ADMIN_IDS")

if not ADMIN_IDS:
    sys.exit(
        "XATO: .env faylida ADMIN_IDS bo'sh. Kamida bitta admin "
        "Telegram ID si ko'rsatilishi shart, aks holda botni "
        "hech kim boshqara olmaydi."
    )


# eski kod bilan moslik uchun (birinchi admin)

ADMIN_ID = ADMIN_IDS[0]


# ==========================
# MINI APP
# ==========================
#
# HTTPS bo'lishi shart (Telegram talabi). Bo'sh qoldirilsa
# "Farzandim" tugmasi ko'rinmaydi, bot buzilmaydi.

WEBAPP_URL = _ixtiyoriy("WEBAPP_URL")

# gunicorn shu portda tinglaydi, nginx subdomendan shu yerga uzatadi.
# Har maktabga BOSHQA port beriladi.

WEBAPP_PORT = int(_ixtiyoriy("WEBAPP_PORT", "8000"))


# ==========================
# BAZA
# ==========================
#
# Har maktabning o'z fayli. Bir serverda bir nechta maktab
# ishlaganda bu yo'llar KESISHMASLIGI shart.

DB_PATH = _yol("DB_PATH", "school.db")


# ==========================
# GOOGLE DRIVE
# ==========================
#
# Har maktabning O'Z Google akkaunti bo'ladi - hujjatlar
# maktabning o'zida saqlanadi, kvota ham alohida.

# IKKI XIL ULANISH USULI BOR:
#
# 1. OAUTH (odam nomidan) - SHAXSIY GMAIL UCHUN YAGONA YO'L
#    GOOGLE_CREDENTIALS_FILE + GOOGLE_TOKEN_FILE.
#    Token bir marta `scripts/get_token.py` bilan olinadi.
#    Google Cloud'da ilova "Testing" holatida qolsa token
#    7 KUNDA o'ladi - aynan shu sabab 2026-09-10 da Drive
#    ishlamay qolgan edi. Ilovani "In production" ga o'tkazing.
#
# 2. SERVICE ACCOUNT - FAQAT GOOGLE WORKSPACE + SHARED DRIVE
#    GOOGLE_SERVICE_ACCOUNT_FILE va DRIVE_ROOT_FOLDER_ID beriladi.
#    Brauzer, rozilik oynasi va muddat yo'q - lekin SHAXSIY
#    Gmail bilan ISHLAMAYDI: service account'ning Drive kvotasi
#    yo'q, shuning uchun papka yaratadi-yu, fayl yuklashda
#    403 "do not have storage quota" qaytaradi. Nosozlik faqat
#    birinchi yuklashda bilinadi. Batafsil izoh -
#    services/gdrive.py -> use_service_account().
#
# Service account fayli ko'rsatilgan VA mavjud bo'lsa - doim
# o'sha ishlatiladi, OAuth ga qaralmaydi.

GOOGLE_SERVICE_ACCOUNT_FILE = _ixtiyoriy("GOOGLE_SERVICE_ACCOUNT_FILE")

if GOOGLE_SERVICE_ACCOUNT_FILE:
    GOOGLE_SERVICE_ACCOUNT_FILE = _yol("GOOGLE_SERVICE_ACCOUNT_FILE", "")

GOOGLE_CREDENTIALS_FILE = _yol("GOOGLE_CREDENTIALS_FILE", "credentials.json")

GOOGLE_TOKEN_FILE = _yol("GOOGLE_TOKEN_FILE", "token.json")


# Ildiz papka.
#
# Service account'ning O'Z Drive'i yo'q, shuning uchun u yangi
# ildiz papka YARATA OLMAYDI - unga tayyor papkaning ID si
# beriladi (papka manzilidagi /folders/<ID> qismi).
#
# OAuth usulida esa papka nom bo'yicha topiladi/yaratiladi.

DRIVE_ROOT_FOLDER_ID = _ixtiyoriy("DRIVE_ROOT_FOLDER_ID")

DRIVE_ROOT_FOLDER = _ixtiyoriy("DRIVE_ROOT_FOLDER", "Maktab arxivi")
