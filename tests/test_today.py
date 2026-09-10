# -*- coding: utf-8 -*-
"""«Bugungi darslarim» - bir bosishda bugungi darslar ro'yxati."""

import os
import sys

from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import database as db

HERE = os.path.dirname(os.path.abspath(__file__))

os.makedirs(os.path.join(HERE, "_tmp"), exist_ok=True)
DB = os.path.join(HERE, "_tmp", "test_today.db")

if os.path.exists(DB):
    os.remove(DB)

db.DB_NAME = DB
db.create_tables()
db.migrate_schema()

db.add_teacher("Karimov Aziz", "Fortepiano")
db.add_teacher("Sobirova Nilufar", "Fortepiano")

CHAT = 555

ok, bad = [], []


def check(label, cond):
    (ok if cond else bad).append(label)


# ==========================
# SOXTA BOT
# ==========================


class Msg:
    def __init__(self, text=""):
        self.text = text
        self.chat = type("C", (), {"id": CHAT})()
        self.message_id = 1


class FakeBot:

    def __init__(self):
        self.handlers = []
        self.messages = []

    def message_handler(self, **kwargs):
        func = kwargs.get("func")

        def wrap(fn):
            self.handlers.append((func, fn))
            return fn

        return wrap

    def callback_query_handler(self, func):
        def wrap(fn):
            return fn
        return wrap

    def send_message(self, chat_id, text, reply_markup=None):
        self.messages.append(text)
        return Msg()

    def edit_message_text(self, text, *a, **k):
        self.messages.append(text)

    def answer_callback_query(self, *a, **k):
        pass

    def register_next_step_handler(self, *a, **k):
        pass

    def send(self, text):
        message = Msg(text)

        for func, fn in self.handlers:
            if func is None or func(message):
                fn(message)
                return True

        return False

    def last(self):
        return self.messages[-1] if self.messages else ""


bot = FakeBot()

import handlers.teacher_schedule as ts

selected = {CHAT: "Karimov Aziz"}

ts.register_teacher_schedule(bot, selected)

BUTTON = "📅 Bugungi darslarim"


# ==========================
# VAQTNI QOTIRISH
# ==========================


class FakeDatetime(datetime):

    FIXED = None

    @classmethod
    def now(cls, tz=None):
        return cls.FIXED


ts.datetime = FakeDatetime


# ==========================
# 1. DARS YO'Q
# ==========================

# 2026-09-14 - dushanba, soat 09:00
FakeDatetime.FIXED = FakeDatetime(2026, 9, 14, 9, 0)

bot.send(BUTTON)

check("dars yo'qligi aytildi", "darsingiz yo'q" in bot.last())
check("kun nomi ko'rsatildi", "Dushanba" in bot.last())


# ==========================
# 2. BUGUNGI DARSLAR CHIQADI
# ==========================

slot_a = db.create_slot("Karimov Aziz", "Mutaxassislik", "Dushanba", "09:30", "2/4", 45)
slot_b = db.create_slot("Karimov Aziz", "Ansambl", "Dushanba", "08:00", "2/9", 45)

# boshqa kunniki - chiqmasligi kerak
db.create_slot("Karimov Aziz", "Solfedjio", "Seshanba", "10:00", "2/5", 45)

db.add_student_to_slot(slot_a, "Aliyev Ali", "Karimov Aziz")
db.add_student_to_slot(slot_a, "Valiyeva Vali", "Karimov Aziz")

bot.send(BUTTON)

text = bot.last()

check("ikkita dars sanaldi", "2 ta dars" in text)
check("bugungi dars bor", "Mutaxassislik" in text)
check("boshqa kun aralashmadi", "Solfedjio" not in text)
check("xona ko'rsatildi", "2/4-xona" in text)
check("o'quvchilar ko'rsatildi", "Aliyev Ali" in text and "Valiyeva Vali" in text)
check("o'quvchisizda izoh bor", "biriktirilmagan" in text)

# vaqt bo'yicha tartib: 08:00 09:30 dan oldin

check("vaqt bo'yicha tartiblandi", text.index("08:00") < text.index("09:30"))


# ==========================
# 3. HOZIR / KEYIN BELGILARI
# ==========================

check("keyingi dars belgilandi", "daqiqadan keyin" in text)

# 09:45 - slot_a (09:30-10:15) ketayotgan payt
FakeDatetime.FIXED = FakeDatetime(2026, 9, 14, 9, 45)

bot.send(BUTTON)

check("ketayotgan dars belgilandi", "hozir" in bot.last())
check("o'tgan dars belgilandi", "✅" in bot.last())


# ==========================
# 4. JO'RNAVOZLIK HAM CHIQADI
# ==========================

other = db.create_slot("Sobirova Nilufar", "Xor", "Dushanba", "11:00", "1/23", 45)

db.add_concertmaster(other, "Karimov Aziz")

bot.send(BUTTON)

check("jo'rnavozlik darsi ham chiqdi", "Xor" in bot.last())
check("dars egasi ko'rsatildi", "Sobirova Nilufar" in bot.last())


# ==========================
# 5. YAKSHANBA
# ==========================

# 2026-09-13 - yakshanba
FakeDatetime.FIXED = FakeDatetime(2026, 9, 13, 10, 0)

bot.send(BUTTON)

check("yakshanba crash bermadi", "yakshanba" in bot.last().lower())


# ==========================
# 6. O'QITUVCHI TANLANMAGAN
# ==========================

selected.pop(CHAT)

FakeDatetime.FIXED = FakeDatetime(2026, 9, 14, 9, 0)

bot.send(BUTTON)

check("tanlanmaganda ogohlantiradi", "Avval o'qituvchini tanlang" in bot.last())


# ==========================
# NATIJA
# ==========================

print()
for line in ok:
    print("  OK   " + line)

for line in bad:
    print("  XATO " + line)

print()
print(str(len(ok)) + " ta o'tdi, " + str(len(bad)) + " ta xato")

sys.exit(1 if bad else 0)
