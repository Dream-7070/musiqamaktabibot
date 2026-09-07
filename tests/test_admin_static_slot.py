# -*- coding: utf-8 -*-
"""
Admin - istalgan vaqtga dars qo'shish (07:15 kabi jadvaldan
tashqari vaqt) va o'quvchisi bor darsni o'chirishda ogohlantirish.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import database as db

os.makedirs(os.path.join(os.path.dirname(os.path.abspath(__file__)), "_tmp"), exist_ok=True)
DB = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                  "_tmp", "test_admin_static_slot.db")

if os.path.exists(DB):
    os.remove(DB)

db.DB_NAME = DB
db.create_tables()
db.migrate_schema()

db.add_teacher("Karimov Aziz", "Fortepiano")

ADMIN = 999

ok, bad = [], []


def check(label, cond):
    (ok if cond else bad).append(label)


def find(buttons, fragment):
    for text, data in buttons:
        if fragment in text:
            return data
    return None


class Msg:
    def __init__(self, text=""):
        self.text = text
        self.chat = type("C", (), {"id": ADMIN})()
        self.message_id = 1


class Call:
    def __init__(self, data):
        self.data = data
        self.id = "1"
        self.message = Msg()


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
        buttons = []
        if reply_markup is not None:
            for row in reply_markup.keyboard:
                for b in row:
                    buttons.append((b.text, b.callback_data))
        self.messages.append((text, buttons))
        return Msg()

    def edit_message_text(self, text, chat_id, message_id, reply_markup=None):
        buttons = []
        if reply_markup is not None:
            for row in reply_markup.keyboard:
                for b in row:
                    buttons.append((b.text, b.callback_data))
        self.messages.append((text, buttons))

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

    def last(self):
        return self.messages[-1] if self.messages else ("", [])


bot = FakeBot()

import config
config.ADMIN_IDS = [ADMIN]

import handlers.admin_schedule as adsch
adsch.ADMIN_IDS = [ADMIN]
adsch.register_admin_schedule(bot)


# ==========================
# 1. BO'LIM -> O'QITUVCHI -> "YANGI DARS QO'SHISH"
# ==========================

bot.fire("adsch:dept:0")
text, buttons = bot.last()

teacher_btn = find(buttons, "Karimov Aziz")

check("Fortepiano bo'limida Karimov Aziz bor", teacher_btn is not None)

bot.fire(teacher_btn)
text, buttons = bot.last()

new_btn = find(buttons, "Yangi dars qo'shish")

check("'Yangi dars qo'shish' tugmasi bor", new_btn is not None)

bot.fire(new_btn)
text, buttons = bot.last()

check("fan ro'yxati chiqdi", len(buttons) > 3)
check("Mutaxassislik bor", find(buttons, "Mutaxassislik") is not None)


# ==========================
# 2. FAN -> SINF -> KUN -> ISTALGAN VAQT
# ==========================

bot.fire(find(buttons, "Mutaxassislik"))
text, buttons = bot.last()

check("sinf so'raldi", "sinf" in text.lower())

bot.fire(find(buttons, "3-sinf"))
text, buttons = bot.last()

check("kun so'raldi", "kun" in text.lower())

bot.fire(find(buttons, "Dushanba"))
text, _ = bot.last()

check("erkin vaqt so'raldi", "vaqt" in text.lower() or "soat" in text.lower())
check("next_step o'rnatildi", bot.next_step is not None)

# Bu - butun testning ma'nosi: o'qituvchining tayyor
# jadvalida YO'Q vaqt, masalan 07:15.

bot.next_step(Msg("07:15"))
text, buttons = bot.last()

check("davomiylik so'raldi", "davomiyl" in text.lower())
check("1 soat tugmasi bor", find(buttons, "1 soat") is not None)


# ==========================
# 3. DAVOMIYLIK -> XONA -> SAQLASH
# ==========================

bot.fire(find(buttons, "1 soat"))
text, buttons = bot.last()

check("xona so'raldi", "xona" in text.lower())
check("31 ta xona tugmasi bor", len(buttons) == 31)

bot.fire(find(buttons, "2/4"))

slots = db.get_teacher_slots("Karimov Aziz")

check("dars 07:15 da saqlandi", len(slots) == 1)

if slots:
    slot_id, subject, day, time, room = slots[0]
    check("vaqt aynan 07:15 - jadval katakchasiga cheklanmadi", time == "07:15")
    check("xona to'g'ri", room == "2/4")
    check("fan to'g'ri", subject == "Mutaxassislik")


# ==========================
# 4. XUDDI SHU VAQTGA IKKINCHI DARS - O'QITUVCHI BAND
# ==========================

bot.fire("adsch:dept:0")
_, buttons = bot.last()
bot.fire(find(buttons, "Karimov Aziz"))
_, buttons = bot.last()
bot.fire(find(buttons, "Yangi dars qo'shish"))
_, buttons = bot.last()
bot.fire(find(buttons, "Solfedjio"))
_, buttons = bot.last()
bot.fire(find(buttons, "3-sinf"))
_, buttons = bot.last()
bot.fire(find(buttons, "Dushanba"))

bot.next_step(Msg("07:15"))
_, buttons = bot.last()
bot.fire(find(buttons, "1 soat"))
text, _ = bot.last()

check("o'qituvchi bandligi aytildi", "band" in text.lower())

check(
    "ikkinchi dars saqlanmadi",
    len(db.get_teacher_slots("Karimov Aziz")) == 1
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
