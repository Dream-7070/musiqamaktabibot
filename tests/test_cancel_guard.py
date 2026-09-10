# -*- coding: utf-8 -*-
"""
Menyu tugmasini bosish (yoki /cancel) matnli kiritishni bekor
qiladi - tugma matni bolaning ismi/sanasi sifatida yozilib
qolmasligi kerak.

Bugungi voqea: o'qituvchi adashib "⬅️ Ortga" bossa, bot buni
ism deb bazaga yozib yuborardi.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import database as db

os.makedirs(os.path.join(os.path.dirname(os.path.abspath(__file__)), "_tmp"), exist_ok=True)
DB = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                  "_tmp", "test_cancel_guard.db")

if os.path.exists(DB):
    os.remove(DB)

db.DB_NAME = DB
db.create_tables()
db.migrate_schema()

db.add_teacher("Karimov A.", "Fortepiano")

CHAT = 777

ok, bad = [], []


def check(label, cond):
    (ok if cond else bad).append(label)


class Msg:
    def __init__(self, text=""):
        self.text = text
        self.chat = type("C", (), {"id": CHAT})()
        self.message_id = 1


class Call:
    def __init__(self, data):
        self.data = data
        self.id = "1"
        self.message = Msg()


class FakeBot:
    """
    test_flow.py dagi FakeBot'dan farqi: message_handler ham
    ro'yxatga olinadi va send_text() orqali chaqirish mumkin -
    "➕ O'quvchi qo'shish" kabi menyu tugmalarini sinash uchun.
    """

    def __init__(self):
        self.callbacks = []
        self.text_handlers = []
        self.messages = []
        self.next_step = None

    def callback_query_handler(self, func):
        def wrap(fn):
            self.callbacks.append((func, fn))
            return fn
        return wrap

    def message_handler(self, **kwargs):
        func = kwargs.get("func")

        def wrap(fn):
            if func is not None:
                self.text_handlers.append((func, fn))
            return fn
        return wrap

    def send_message(self, chat_id, text, reply_markup=None):
        buttons = []
        if reply_markup is not None:
            for row in reply_markup.keyboard:
                for b in row:
                    buttons.append((b.text, b.callback_data))
        self.messages.append((text, buttons))
        return Msg()

    def edit_message_text(self, text, *a, **k):
        self.messages.append((text, []))

    def answer_callback_query(self, *a, **k):
        pass

    def register_next_step_handler(self, message, fn):
        self.next_step = fn

    def fire(self, data):
        call = Call(data)
        for func, fn in self.callbacks:
            if func(call):
                fn(call)
                return True
        return False

    def send_text(self, text):
        """Foydalanuvchi pastki menyudan tugma bosgandek yoki
        oddiy matn yozgandek - message_handler yoki next_step
        orqali yo'naladi."""

        msg = Msg(text)

        if self.next_step is not None:
            handler = self.next_step
            self.next_step = None
            handler(msg)
            return True

        for func, fn in self.text_handlers:
            if func(msg):
                fn(msg)
                return True

        return False

    def last(self):
        return self.messages[-1] if self.messages else ("", [])


bot = FakeBot()

from handlers.students import register_students
import handlers.students as students_module

selected = {CHAT: "Karimov A."}
register_students(bot, selected)


# ==========================
# 1. ISM O'RNIGA MENYU TUGMASI BOSILSA
# ==========================

bot.send_text("➕ O'quvchi qo'shish")
text, _ = bot.last()

check("ism so'raldi", "ism" in text.lower())

bot.send_text("⬅️ Ortga")
text, _ = bot.last()

check("bekor qilindi deyildi", "Bekor qilindi" in text)

check(
    "vaqtinchalik holat tozalandi",
    CHAT not in students_module.student_temp
)

check(
    "«⬅️ Ortga» ism sifatida saqlanmadi",
    "⬅️ Ortga" not in db.get_students("Karimov A.")
)


# ==========================
# 2. SANA O'RNIGA /cancel
# ==========================

bot.send_text("➕ O'quvchi qo'shish")
_, _ = bot.last()

bot.send_text("Ali Valiyev")
text, _ = bot.last()

check("sana so'raldi", "sana" in text.lower())

check(
    "ism vaqtincha saqlanган edi",
    students_module.student_temp.get(CHAT, {}).get("name") == "Ali Valiyev"
)

bot.send_text("/cancel")
text, _ = bot.last()

check("/cancel ham bekor qildi", "Bekor qilindi" in text)

check(
    "holat butunlay tozalandi",
    CHAT not in students_module.student_temp
)


# ==========================
# 3. GUVOHNOMA RAQAMI O'RNIGA MENYU TUGMASI
# ==========================

bot.send_text("➕ O'quvchi qo'shish")
bot.send_text("Vali Aliyev")
bot.send_text("2015-05-05")
text, _ = bot.last()

check("guvohnoma so'raldi", "guvohnoma" in text.lower())

bot.send_text("👨‍🎓 O'quvchilar")
text, _ = bot.last()

check("shu bosqichda ham bekor bo'ldi", "Bekor qilindi" in text)

check(
    "yarim to'ldirilgan yozuv qolmadi",
    CHAT not in students_module.student_temp
)

check(
    "hech qanday o'quvchi yaratilmadi",
    len(db.get_students("Karimov A.")) == 0
)


# ==========================
# 4. HAQIQIY QIYMAT BILAN TO'LIQ O'TADI (nazorat uchun)
# ==========================

bot.send_text("➕ O'quvchi qo'shish")
bot.send_text("Sara Karimova")
bot.send_text("2016-01-01")
bot.send_text("I-TV 1234567")
bot.fire("newcls:3")
bot.fire("newfee:0")

students = db.get_students("Karimov A.")

check("haqiqiy maʼlumot bilan o'quvchi yaratildi", len(students) == 1)

if students:
    check("ismi to'g'ri saqlandi", "Sara Karimova" in students)


# ==========================
# 4b. ESKIRGAN TUGMA BOTNI YIQITMASLIGI KERAK
# ==========================
#
# Inline tugmalar chatda qolib ketadi. O'qituvchi yarim yo'lda
# tashlab ketgan qo'shishning "badal" tugmasini keyinroq bossa,
# o'sha payt yangi qo'shish endi boshlangan bo'lishi mumkin -
# ism/sana hali yo'q. Ilgari bot shu yerda KeyError bilan
# yiqilardi (jonli serverda 10-sentabrda ro'y berdi).

before = len(db.get_students("Karimov A."))

bot.send_text("➕ O'quvchi qo'shish")
bot.send_text("Yarim Qolgan")

crashed = False

try:
    bot.fire("newfee:0")

except Exception:
    crashed = True

check("eskirgan tugma botni yiqitmadi", not crashed)
check("chala o'quvchi yaratilmadi",
      len(db.get_students("Karimov A.")) == before)


# ==========================
# 5. TAHRIRLASHNI BEKOR QILISH
# ==========================
#
# "✏️ Ism-familiyani o'zgartirish" -> yangi qiymat so'raladi ->
# o'qituvchi adashib menyu tugmasini bossa - eski ism saqlanib
# qolishi kerak, buzilib qolmasligi kerak.

students_module.selected_students[CHAT] = "Sara Karimova"

bot.fire("edf:student")
text, _ = bot.last()

check("yangi qiymat so'raldi", "yozing" in text.lower())

bot.send_text("🚪 Xonalar")
text, _ = bot.last()

check("tahrirlash ham bekor bo'ldi", "Bekor qilindi" in text)

check(
    "edit_temp tozalandi",
    CHAT not in students_module.edit_temp
)

students = db.get_students("Karimov A.")

check(
    "ism buzilmadi (\"Xonalar\" deb yozilmadi)",
    not any("Xonalar" in s for s in students)
)


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
