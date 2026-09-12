# -*- coding: utf-8 -*-
"""
Xo'jalik mudiri paneli: texnik xodim va lavozim qo'shish.

Texnik xodim botdan foydalanmaydi - yozuvini mudir yuritadi.
Shuning uchun bu yerda tekshiriladigan asosiy narsa: faqat mudir
(yoki admin) kira oladi, xodim to'rt qadamda qo'shiladi va
hujjatlari to'liq emasligi ko'rinib turadi.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import database as db
from db.migrations import run_migrations

os.makedirs(os.path.join(os.path.dirname(os.path.abspath(__file__)), "_tmp"),
            exist_ok=True)

DB = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                  "_tmp", "test_tech_staff.db")

if os.path.exists(DB):
    os.remove(DB)

db.DB_NAME = DB
run_migrations(verbose=False)

MUDIR = 111
BEGONA = 222
ADMIN = 999

db.add_staff_directly(MUDIR, "xojalik_mudiri", "Surobov F.F")

# 008-migratsiya tabeldagi mavjud xodimlarni oldindan qo'shadi,
# shuning uchun sonlar NISBIY tekshiriladi.

BOSHLANGICH = len(db.get_tech_staff())


# ==========================
# SOXTA BOT
# ==========================


class Msg:
    def __init__(self, text="", chat_id=MUDIR):
        self.text = text
        self.chat = type("C", (), {"id": chat_id})()
        self.message_id = 1
        self.content_type = "text"


class Call:
    def __init__(self, data, chat_id=MUDIR):
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
        self.next_step = None

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

    def register_next_step_handler(self, message, fn):
        self.next_step = fn

    # --- sinov yordamchilari ---

    def send(self, text, chat_id=MUDIR):
        message = Msg(text, chat_id)
        for func, fn in self.msg_handlers:
            if func is None or func(message):
                fn(message)
                return

    def answer(self, text, chat_id=MUDIR):
        """Oxirgi so'ralgan matnli qadamga javob beradi."""
        fn, self.next_step = self.next_step, None
        if fn:
            fn(Msg(text, chat_id))

    def fire(self, data, chat_id=MUDIR):
        call = Call(data, chat_id)
        for func, fn in self.callbacks:
            if func(call):
                fn(call)
                return

    def last(self):
        return self.messages[-1]


import handlers.tech_staff as tx

bot = FakeBot()
tx.register_tech_staff(bot, [ADMIN])

ok, bad = [], []


def check(label, cond):
    (ok if cond else bad).append(label)


# ==========================
# 1. RUXSAT
# ==========================

bot.send(tx.BUTTON_STAFF, chat_id=BEGONA)

check("Begona odam kira olmadi", "xo'jalik mudiri uchun" in bot.last()[0])

bot.send(tx.BUTTON_STAFF, chat_id=MUDIR)

check("Mudir ro'yxatni ko'rdi", "Texnik xodimlar" in bot.last()[0])


# ==========================
# 2. LAVOZIM QO'SHISH
# ==========================

avval = len(db.get_tech_positions())

bot.send(tx.BUTTON_POSITIONS)

check("Lavozimlar ro'yxati chiqdi", "Lavozimlar" in bot.last()[0])

check("Boshlang'ich lavozimlar bor (tabeldan)", avval >= 9)

bot.fire("tx:newpos")
bot.answer("Bog'bon")

check("Yangi lavozim qo'shildi",
      len(db.get_tech_positions()) == avval + 1)

bot.fire("tx:newpos")
bot.answer("Bog'bon")

check("Takror lavozim qo'shilmadi",
      len(db.get_tech_positions()) == avval + 1
      and "allaqachon bor" in bot.messages[-2][0])


# ==========================
# 3. BEKOR QILISH
# ==========================
#
# Menyu tugmasi bosilsa, u nom sifatida bazaga yozilib qolmasligi
# kerak - shuning uchun har matnli qadamda qo'riqchi bor.

bot.fire("tx:newpos")
bot.answer(tx.BUTTON_STAFF)

check("Menyu tugmasi lavozim nomi bo'lib qolmadi",
      len(db.get_tech_positions()) == avval + 1)


# ==========================
# 4. XODIM QO'SHISH
# ==========================

bot.fire("tx:new")

labels = [t for t, _ in bot.last()[1]]

check("Lavozim tanlash ro'yxati chiqdi", "Farrosh" in labels)

bot.fire("tx:pos:Farrosh")
bot.answer("Karimova Dilnoza")
bot.answer("6")
bot.answer("1067640")

rows = db.get_tech_staff()

check("Xodim bazaga yozildi", len(rows) == BOSHLANGICH + 1)

yangi = [r for r in rows if r[1] == "Karimova Dilnoza"]

check("Ma'lumotlari to'g'ri saqlandi: " + str(yangi[0][1:5] if yangi else None),
      yangi
      and yangi[0][2] == "Farrosh"
      and yangi[0][3] == "6"
      and yangi[0][4] == 1067640)

kartochka = bot.last()[0]

check("Karta ochildi va stavka o'qiladigan ko'rinishda",
      "Karimova Dilnoza" in kartochka and "1 067 640" in kartochka)

check("Yetishmayotgan hujjatlar sanaldi",
      "Yetishmayapti" in kartochka)


# ==========================
# 5. NOTO'G'RI STAVKA QAYTA SO'RALADI
# ==========================

bot.fire("tx:new")
bot.fire("tx:pos:Qorovul")
bot.answer("Asraqulov Elmurod")
bot.answer("10")
bot.answer("raqam emas")

check("Raqam bo'lmasa qayta so'raldi", "Faqat raqam" in bot.last()[0])

bot.answer("702863")

check("Keyin to'g'ri saqlandi", len(db.get_tech_staff()) == BOSHLANGICH + 2)


# ==========================
# 6. HUJJAT YETISHMASLIGI RO'YXATDA KO'RINADI
# ==========================

bot.send(tx.BUTTON_STAFF)

labels = [t for t, _ in bot.last()[1]]

check("Ro'yxatda hujjati to'liq emaslar ⚠️ bilan",
      sum(1 for t in labels if "⚠️" in t) == BOSHLANGICH + 2)

staff_id = [r for r in db.get_tech_staff() if r[1] == "Karimova Dilnoza"][0][0]

db.save_tech_document(staff_id, "pasport", "p.pdf", 10, "d1", "http://x")

check("Hujjat yuklangach yetishmaydiganlar kamaydi",
      len(db.get_tech_missing_documents(staff_id)) == 6)


# ==========================
# 7. ISHDAN BO'SHATISH YOZUVNI O'CHIRMAYDI
# ==========================

bot.fire("tx:fire:" + str(staff_id))

check("Faol ro'yxatdan chiqdi", len(db.get_tech_staff()) == BOSHLANGICH + 1)

check("Yozuvning o'zi qoldi (eski tabel uchun kerak)",
      len(db.get_tech_staff(only_active=False)) == BOSHLANGICH + 2)

check("Hujjatlari ham joyida",
      len(db.list_tech_documents(staff_id)) == 1)


print()

for line in ok:
    print("  OK   " + line)

for line in bad:
    print("  XATO " + line)

print()
print(str(len(ok)) + " ta o'tdi, " + str(len(bad)) + " ta xato")

sys.exit(1 if bad else 0)
