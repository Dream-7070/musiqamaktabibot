# -*- coding: utf-8 -*-
# ==========================
# tests/test_specialty_reminder.py
# ==========================
#
# Yo'nalish belgilash eslatmasi.
#
# Eng muhim talab: ro'yxat bo'shagach eslatma O'Z-O'ZIDAN
# to'xtashi kerak - aks holda ish tugagach ham admin har kuni
# keraksiz xabar olaveradi.
# ==========================


import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import database as db

TMP = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_tmp")

os.makedirs(TMP, exist_ok=True)

DB_FILE = os.path.join(TMP, "specialty_reminder.db")

if os.path.exists(DB_FILE):
    os.remove(DB_FILE)

db.DB_NAME = DB_FILE

db.create_tables()
db.migrate_schema()

from services import specialty_reminder as sr


xatolar = []


def check(nom, shart):

    if shart:
        print("  OK   " + nom)

    else:
        print("  XATO " + nom)
        xatolar.append(nom)


class SoxtaBot:
    """Haqiqiy Telegram o'rniga - yuborilganlarni yig'ib boradi."""

    def __init__(self):
        self.yuborilgan = []

    def send_message(self, chat_id, text, reply_markup=None):
        self.yuborilgan.append((chat_id, text, reply_markup))


# ==========================
# KIMGA YUBORILADI
# ==========================

print("manzil:")

from config import ADMIN_IDS

check("sozlama bo'lmasa - barcha adminlarga",
      sr._targets() == list(ADMIN_IDS))

db.set_setting(sr.TARGET_KEY, "1898799278")

check("sozlama bo'lsa - faqat o'shanga",
      sr._targets() == [1898799278])

db.set_setting(sr.TARGET_KEY, "111, 222")

check("bir nechta ID ham ishlaydi", sr._targets() == [111, 222])

db.set_setting(sr.TARGET_KEY, "buzuq")

check("buzuq qiymatda adminlarga qaytadi",
      sr._targets() == list(ADMIN_IDS))

db.set_setting(sr.TARGET_KEY, "1898799278")


# ==========================
# BO'SH RO'YXAT
# ==========================

print("ro'yxat bo'sh:")

bot = SoxtaBot()

check("hech kim yo'q - hech narsa yuborilmaydi", sr.send_once(bot) == 0)

check("xabar ketmadi", bot.yuborilgan == [])


# ==========================
# BELGILANMAGAN O'QITUVCHI BOR
# ==========================

print("belgilanmagan o'qituvchi bor:")

AMALIY = "Amaliy san'at"

db.seed_teachers([("Test Usta", AMALIY), ("Test Pianochi", "Fortepiano")])

pending = db.teachers_without_specialty()

check("ko'p yo'nalishli bo'lim - ro'yxatga tushdi",
      any(r[1] == "Test Usta" for r in pending))

check("bitta yo'nalishli bo'lim - ro'yxatda YO'Q",
      not any(r[1] == "Test Pianochi" for r in pending))

bot = SoxtaBot()

check("bitta manzilga yuborildi", sr.send_once(bot) == 1)

chat_id, text, markup = bot.yuborilgan[0]

check("aynan 2-adminga ketdi", chat_id == 1898799278)

check("matnda o'qituvchi ismi bor", "Test Usta" in text)

check("matnda pianochi yo'q", "Test Pianochi" not in text)

check("tugma bor", markup is not None and len(markup.keyboard) >= 1)

tugma = markup.keyboard[0][0]

check("tugma yo'nalish ekraniga olib boradi",
      tugma.callback_data.startswith("adyon:new:"))

check("callback to'rt qismdan iborat",
      len(tugma.callback_data.split(":")) == 4)


# ==========================
# ISH TUGAGACH TO'XTAYDI
# ==========================

print("ish tugagach:")

db.set_teacher_specialties("Test Usta", ["Badiiy kashtachilik"])

bot = SoxtaBot()

check("belgilangach eslatma to'xtadi", sr.send_once(bot) == 0)

check("xabar ketmadi", bot.yuborilgan == [])


print()

if xatolar:
    print("XATOLAR: " + str(len(xatolar)))
    sys.exit(1)

print("test_specialty_reminder: hammasi joyida")
