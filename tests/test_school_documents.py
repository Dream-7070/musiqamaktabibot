# -*- coding: utf-8 -*-
"""
Maktabning umumiy hujjatlari: ish rejasi, kadastr, guvohnoma,
INN, maktab pasporti, nizom.

Bular biror odamga emas, maktabning o'ziga tegishli. Shu sababli
bo'limga bir nechta rol kiradi: admin, direktor, yordamchi va
xo'jalik mudiri - hammasi ham ko'radi, ham yuklaydi. O'qituvchi
esa kirmasligi kerak.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import database as db
from db.migrations import run_migrations

os.makedirs(os.path.join(os.path.dirname(os.path.abspath(__file__)), "_tmp"),
            exist_ok=True)

DB = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                  "_tmp", "test_school_documents.db")

if os.path.exists(DB):
    os.remove(DB)

db.DB_NAME = DB
run_migrations(verbose=False)

ADMIN = 999
DIREKTOR = 111
YORDAMCHI = 222
MUDIR = 333
OQITUVCHI = 444

db.add_staff_directly(DIREKTOR, "direktor", "Direktor")
db.add_staff_directly(YORDAMCHI, "yordamchi", "Yordamchi")
db.add_staff_directly(MUDIR, "xojalik_mudiri", "Surobov F.F")


class Msg:
    def __init__(self, text="", chat_id=ADMIN):
        self.text = text
        self.chat = type("C", (), {"id": chat_id})()
        self.message_id = 1
        self.content_type = "text"


class Call:
    def __init__(self, data, chat_id=ADMIN):
        self.data = data
        self.id = "1"
        self.message = Msg(chat_id=chat_id)


def _buttons(markup):
    out = []
    if markup is not None:
        for row in markup.keyboard:
            for b in row:
                out.append((b.text, b.callback_data))
    return out


class FakeBot:

    def __init__(self):
        self.callbacks = []
        self.msg_handlers = []
        self.messages = []

    def callback_query_handler(self, func):
        def wrap(fn):
            self.callbacks.append((func, fn))
            return fn
        return wrap

    def message_handler(self, func=None, content_types=None, **kw):
        def wrap(fn):
            self.msg_handlers.append((func, fn))
            return fn
        return wrap

    def send_message(self, chat_id, text, reply_markup=None, **k):
        self.messages.append((text, _buttons(reply_markup)))
        return Msg(chat_id=chat_id)

    def edit_message_text(self, text, chat_id=None, message_id=None,
                          reply_markup=None, *a, **k):
        self.messages.append((text, _buttons(reply_markup)))

    def answer_callback_query(self, *a, **k):
        pass

    def send(self, text, chat_id=ADMIN):
        message = Msg(text, chat_id)
        for func, fn in self.msg_handlers:
            if func is None or func(message):
                fn(message)
                return

    def fire(self, data, chat_id=ADMIN):
        call = Call(data, chat_id)
        for func, fn in self.callbacks:
            if func(call):
                fn(call)
                return

    def last(self):
        return self.messages[-1]


import handlers.school_documents as sd

bot = FakeBot()
sd.register_school_documents(bot, [ADMIN])

ok, bad = [], []


def check(label, cond):
    (ok if cond else bad).append(label)


# ==========================
# 1. RUXSAT
# ==========================

for label, uid in (
    ("admin", ADMIN),
    ("direktor", DIREKTOR),
    ("yordamchi", YORDAMCHI),
    ("xo'jalik mudiri", MUDIR),
):
    bot.send(sd.BUTTON, chat_id=uid)

    check(label + " bo'limni ochdi", "Maktab hujjatlari" in bot.last()[0])


bot.send(sd.BUTTON, chat_id=OQITUVCHI)

check("O'qituvchi kira olmadi", "rahbariyat" in bot.last()[0])


# ==========================
# 2. TURLAR RO'YXATI
# ==========================

bot.send(sd.BUTTON, chat_id=MUDIR)

labels = [t for t, _ in bot.last()[1]]

check("Oltita tur ko'rsatildi: " + str(len(labels)), len(labels) == 6)

check("Kerakli turlar bor",
      any("ish rejasi" in t.lower() for t in labels)
      and any("kadastr" in t.lower() for t in labels)
      and any("nizom" in t.lower() for t in labels)
      and any("inn" in t.lower() for t in labels)
      and any("pasport" in t.lower() for t in labels)
      and any("guvohnoma" in t.lower() for t in labels))

check("Boshida hammasi ⚠️ (yuklanmagan)",
      sum(1 for t in labels if "⚠️" in t) == 6)


# ==========================
# 3. YUKLANGANDAN KEYIN BELGI O'ZGARADI
# ==========================

db.save_school_document("nizom", "nizom.pdf", 2048, "d1", "http://x",
                        uploaded_by=MUDIR)

bot.send(sd.BUTTON, chat_id=DIREKTOR)

labels = [t for t, _ in bot.last()[1]]

check("Yuklangani ✅ bo'ldi",
      any(t.startswith("✅") and "Nizom" in t for t in labels))

check("Qolganlari ⚠️ bo'lib qoldi",
      sum(1 for t in labels if "⚠️" in t) == 5)

check("Fayl soni ko'rsatildi",
      any("(1 ta)" in t for t in labels))


# ==========================
# 4. TUR ICHI - FAYL RO'YXATI
# ==========================

bot.fire("sd:t:nizom", chat_id=YORDAMCHI)

text, buttons = bot.last()

check("Fayl nomi ko'rindi", "nizom.pdf" in text)

check("Havola ko'rindi", "http://x" in text)

check("Yuklash tugmasi bor",
      any("Fayl yuklash" in t for t, _ in buttons))


# ==========================
# 5. BIR TURDA BIR NECHTA FAYL
# ==========================
#
# Ish rejasi har yili yangilanadi - eskisi o'chirilmaydi.

db.save_school_document("nizom", "nizom_2026.pdf", 3000, "d2", "http://y",
                        uploaded_by=DIREKTOR)

bot.fire("sd:t:nizom", chat_id=ADMIN)

text = bot.last()[0]

check("Ikkala fayl ham ro'yxatda",
      "nizom.pdf" in text and "nizom_2026.pdf" in text)


# ==========================
# 6. BEGONA KIRA OLMAYDI (callback orqali ham)
# ==========================

avval = len(bot.messages)

bot.fire("sd:t:nizom", chat_id=OQITUVCHI)

check("O'qituvchi callback orqali ham ko'ra olmadi",
      len(bot.messages) == avval)


# ==========================
# 7. QIDIRUV BO'LIMIDAN KIRISH
# ==========================
#
# Admin bu yerga «🔍 Hujjat qidirish» ichidan kiradi - o'qituvchi
# va o'quvchi hujjatlari bilan bitta joyda tursin.

bot.fire("sd:open", chat_id=ADMIN)

check("Qidiruv bo'limidan ochildi", "Maktab hujjatlari" in bot.last()[0])

avval = len(bot.messages)

bot.fire("sd:open", chat_id=OQITUVCHI)

check("Qidiruvdan ham begona kira olmadi", len(bot.messages) == avval)


print()

for line in ok:
    print("  OK   " + line)

for line in bad:
    print("  XATO " + line)

print()
print(str(len(ok)) + " ta o'tdi, " + str(len(bad)) + " ta xato")

sys.exit(1 if bad else 0)
