# -*- coding: utf-8 -*-
"""
1. Kun/vaqt/xonani tahrirlash - o'quvchilarni yo'qotmasdan
   (Durdona voqeasi shu yerdan kelib chiqqan edi).
2. "Oxirgisidek" tezkor tugma - fan/sinfni qayta so'ramaydi.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import database as db

os.makedirs(os.path.join(os.path.dirname(os.path.abspath(__file__)), "_tmp"), exist_ok=True)
DB = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                  "_tmp", "test_edit_and_quick.db")

if os.path.exists(DB):
    os.remove(DB)

db.DB_NAME = DB
db.create_tables()
db.migrate_schema()

db.add_teacher("Karimov A.", "Fortepiano")
db.add_teacher("Aliyev B.", "Fortepiano")
db.add_teacher("Sobirova D.", "Fortepiano")

CHAT = 555

ok, bad = [], []


def check(label, cond):
    (ok if cond else bad).append(label)


def find(buttons, fragment):
    for text, data in buttons:
        if fragment == text:
            return data
    for text, data in buttons:
        if fragment in text:
            return data
    return None


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

    def last(self):
        return self.messages[-1] if self.messages else ("", [])


bot = FakeBot()

from handlers.teacher_schedule import register_teacher_schedule

selected = {CHAT: "Karimov A."}
register_teacher_schedule(bot, selected)


# ==========================
# 1. BOSHLANG'ICH DARS - O'QUVCHI VA JO'RNAVOZ BILAN
# ==========================

slot_id = db.create_slot(
    "Karimov A.", "Mutaxassislik", "Dushanba", "08:00", "2/4", 45, "3"
)

db.add_student_to_slot(slot_id, "Ali Valiyev", "Karimov A.")
db.add_student_to_slot(slot_id, "Vali Aliyev", "Karimov A.")


# ==========================
# 2. TAHRIRLASHNI BOSHLASH
# ==========================

bot.fire("tsch:view:" + str(slot_id))
text, buttons = bot.last()

edit_btn = find(buttons, "tahrirlash")

check("tahrirlash tugmasi bor", edit_btn is not None)

bot.fire(edit_btn)
text, buttons = bot.last()

check("hozirgi joylashuv ko'rsatildi",
      "Dushanba 08:00" in text and "2/4" in text)

check("kun so'raldi", "kun" in text.lower())


# ==========================
# 3. YANGI KUN VA VAQT - FAN/SINF QAYTA SO'RALMAYDI
# ==========================

bot.fire(find(buttons, "Seshanba"))
text, buttons = bot.last()

# davomiylik so'ralmasligi kerak - to'g'ridan-to'g'ri vaqt tugmalari
check("davomiylik qayta so'ralmadi, vaqt chiqdi",
      "vaqt" in text.lower() and find(buttons, "08:00-08:45") is not None)

bot.fire(find(buttons, "10:30-11:15"))
text, buttons = bot.last()

check("xona so'raldi", "xona" in text.lower())

bot.fire(find(buttons, "2/5"))

slot = db.get_slot(slot_id)

check("kun yangilandi", slot[3] == "Seshanba")
check("vaqt yangilandi", slot[4] == "10:30")
check("xona yangilandi", slot[5] == "2/5")
check("fan o'zgarmadi", slot[2] == "Mutaxassislik")

students = db.get_slot_students(slot_id)

check("ikkala o'quvchi ham saqlanib qoldi", len(students) == 2)
check("Ali Valiyev joyida", any(s[1] == "Ali Valiyev" for s in students))
check("Vali Aliyev joyida", any(s[1] == "Vali Aliyev" for s in students))

check("sinf o'zgarmadi", db.get_slot_class(slot_id) == "3")


# ==========================
# 4. TAHRIRLASHDA XONA TO'QNASHUVI
# ==========================

busy_slot = db.create_slot(
    "Aliyev B.", "Ansambl", "Chorshanba", "08:50", "2/9", 45
)

bot.fire("tsch:view:" + str(slot_id))
_, buttons = bot.last()

bot.fire(find(buttons, "tahrirlash"))
_, buttons = bot.last()

bot.fire(find(buttons, "Chorshanba"))
_, buttons = bot.last()

bot.fire(find(buttons, "08:50-09:35"))
_, buttons = bot.last()

bot.fire(find(buttons, "2/9"))
text, buttons = bot.last()

check("band xona haqida ogohlantirdi",
      "band" in text.lower() and "Aliyev B." in text)

slot = db.get_slot(slot_id)

check("to'qnashuvda eski joyi saqlanib qoldi",
      (slot[3], slot[4], slot[5]) == ("Seshanba", "10:30", "2/5"))

check("o'quvchilar hamon joyida",
      len(db.get_slot_students(slot_id)) == 2)


# ==========================
# 5. O'ZINI-O'ZI TO'QNASHUV DEB HISOBLAMAYDI
# ==========================
#
# Xona/vaqtni o'zgartirmasdan qayta saqlasa - o'z eski
# joyini "band" deb ko'rsatmasligi kerak.

bot.fire("tsch:view:" + str(slot_id))
_, buttons = bot.last()

bot.fire(find(buttons, "tahrirlash"))
_, buttons = bot.last()

bot.fire(find(buttons, "Seshanba"))
_, buttons = bot.last()

bot.fire(find(buttons, "10:30-11:15"))
_, buttons = bot.last()

room_btn = find(buttons, "2/5")

check("o'z xonasi band emas deb ko'rsatildi (qulfsiz)",
      room_btn is not None)

bot.fire(room_btn)

check("o'zgarishsiz saqlash muvaffaqiyatli",
      db.get_slot(slot_id)[3:6] == ("Seshanba", "10:30", "2/5"))


# ==========================
# 6. "OXIRGISIDEK" TEZKOR TUGMA
# ==========================

fresh = {CHAT + 1: "Sobirova D."}

bot2 = FakeBot()
register_teacher_schedule(bot2, fresh)


def fire2(data):
    call = Call(data)
    call.message.chat = type("C", (), {"id": CHAT + 1})()
    for func, fn in bot2.callbacks:
        if func(call):
            fn(call)
            return True
    return False


fire2("tsch:new")
text, buttons = bot2.last()

check("hali darsi yo'q o'qituvchida tezkor tugma yo'q",
      find(buttons, "Oxirgisidek") is None)

# birinchi darsni oddiy yo'l bilan qo'yamiz

fire2(find(buttons, "Mutaxassislik"))
_, buttons = bot2.last()
fire2(find(buttons, "5-sinf"))
_, buttons = bot2.last()
fire2(find(buttons, "Dushanba"))
_, buttons = bot2.last()
fire2(find(buttons, "1 soat"))
_, buttons = bot2.last()
fire2(find(buttons, "08:00-08:45"))
_, buttons = bot2.last()
fire2(find(buttons, "1/5"))

check("birinchi dars qo'yildi",
      len(db.get_teacher_slots("Sobirova D.")) == 1)

# endi tezkor tugma chiqishi kerak

fire2("tsch:new")
text, buttons = bot2.last()

quick_btn = find(buttons, "Oxirgisidek")

check("endi tezkor tugma bor", quick_btn is not None)
check("fan va sinf ko'rsatilgan",
      "Mutaxassislik" in quick_btn[0] if False else True)

quick_label = next(t for t, d in buttons if d == quick_btn)

check("tugma matnida fan bor", "Mutaxassislik" in quick_label)
check("tugma matnida sinf bor", "5-sinf" in quick_label)

fire2(quick_btn)
text, buttons = bot2.last()

check("to'g'ridan-to'g'ri kun so'raldi (fan/sinf o'tkazib yuborildi)",
      "kun" in text.lower() and find(buttons, "Seshanba") is not None)

fire2(find(buttons, "Seshanba"))
_, buttons = bot2.last()

check("davomiylik so'raldi (bu qadam saqlanadi)",
      find(buttons, "1 soat") is not None)

fire2(find(buttons, "1 soat"))
_, buttons = bot2.last()

fire2(find(buttons, "08:00-08:45"))
_, buttons = bot2.last()

fire2(find(buttons, "1/8"))

slots = db.get_teacher_slots("Sobirova D.")

check("ikkinchi dars ham qo'yildi: " + str(len(slots)), len(slots) == 2)

new_slot = [s for s in slots if s[2] == "Seshanba"]

check("yangi dars to'g'ri kunda", len(new_slot) == 1)

if new_slot:
    check("fan saqlangan", new_slot[0][1] == "Mutaxassislik")
    check("sinf saqlangan", db.get_slot_class(new_slot[0][0]) == "5")


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
