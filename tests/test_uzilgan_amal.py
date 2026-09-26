# -*- coding: utf-8 -*-
"""Uzilib qolgan "qo'lda vaqt" amali botni qulatmasligi kerak.

Real holat: o'qituvchidan dars vaqti so'ralgan, u javob yozgunicha
boshqa tugmani bosgan - ctx yangisiga almashgan. Keyin yozilgan
vaqt eski next_step_handler ga tushgan va bot
KeyError: 'duration' bilan qulagan (24-sentabr, jonli serverda).
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import database as db

os.makedirs(os.path.join(os.path.dirname(os.path.abspath(__file__)), "_tmp"),
            exist_ok=True)

DB = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                  "_tmp", "test_uzilgan_amal.db")

if os.path.exists(DB):
    os.remove(DB)

db.DB_NAME = DB
db.create_tables()
db.migrate_schema()

db.add_teacher("Karimov A.", "Torli cholg'ular")

CHAT = 555


class Msg:
    def __init__(self, text=""):
        self.text = text
        self.chat = type("C", (), {"id": CHAT})()
        self.message_id = 1


class FakeBot:

    def __init__(self):
        self.callbacks = []
        self.messages = []
        self.next_step = None

    def callback_query_handler(self, func):
        def wrap(fn):
            self.callbacks.append((func, fn))
            return fn
        return wrap

    def message_handler(self, **kwargs):
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

    def register_next_step_handler(self, message, fn):
        self.next_step = fn

    def last(self):
        return self.messages[-1] if self.messages else ""


bot = FakeBot()

from handlers.teacher_schedule import register_teacher_schedule

register_teacher_schedule(bot, {CHAT: "Karimov A."})

ok, bad = [], []


def check(label, cond):
    (ok if cond else bad).append(label)


import types as _t

from handlers.teacher_schedule import ctx


def custom_time_handler():
    """register ichidagi new_slot_custom_time ni topadi."""

    for _shart, fn in bot.callbacks:

        for cell in (fn.__closure__ or []):

            val = cell.cell_contents

            if isinstance(val, _t.FunctionType) and                val.__name__ == "new_slot_custom_time":
                return val

    return None


handler = custom_time_handler()

check("handler topildi", handler is not None)

if handler:

    # Aynan 1387-qatordagi qayta boshlash shunday ctx yasaydi:
    # fan va sinf bor, davomiylik ham, kun ham yo'q.

    ctx[CHAT] = {
        "subject": "Fortepiano",
        "class": "1",
        "names": []
    }

    qulamadi = True

    try:
        handler(Msg("10:55"))

    except KeyError:
        qulamadi = False

    check("KeyError bilan qulamadi", qulamadi)

    check(
        "foydalanuvchiga tushuntirildi",
        "uzilib" in bot.last().lower()
    )

    check("uzilgan amal tozalandi", CHAT not in ctx)


print()

for label in ok:
    print("  OK   " + label)

for label in bad:
    print("  XATO " + label)

print()
print(len(ok), "ta o'tdi,", len(bad), "ta xato")

if bad:
    sys.exit(1)
