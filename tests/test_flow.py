# -*- coding: utf-8 -*-
"""
Dars qo'shish oqimini boshdan-oxir sinaydi.

Haqiqiy bot o'rniga soxta bot ishlatiladi: handlerlar
ro'yxatga olinadi va callback'lar ketma-ket yuboriladi.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import database as db

os.makedirs(os.path.join(os.path.dirname(os.path.abspath(__file__)), "_tmp"), exist_ok=True)
DB = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                  "_tmp", "test_flow.db")

if os.path.exists(DB):
    os.remove(DB)

db.DB_NAME = DB
db.create_tables()
db.migrate_schema()

db.add_teacher("Karimov A.", "Fortepiano")

CHAT = 555


# ==========================
# SOXTA BOT
# ==========================

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

ok, bad = [], []


def check(label, cond):
    (ok if cond else bad).append(label)


def find(buttons, fragment):
    for text, data in buttons:
        if fragment in text:
            return data
    return None


# ==========================
# 1. FAN RO'YXATI
# ==========================

bot.fire("tsch:new")
text, buttons = bot.last()

check("fan ro'yxati chiqdi (" + str(len(buttons)) + " ta tugma)",
      len(buttons) > 5)

check("Mutaxassislik bor", find(buttons, "Mutaxassislik") is not None)
check("Solfedjio bor", find(buttons, "Solfedjio") is not None)
check("Chizmatasvir yo'q (boshqa bo'lim)",
      find(buttons, "Chizmatasvir") is None)


# ==========================
# 2. SINF
# ==========================

bot.fire(find(buttons, "Mutaxassislik"))
text, buttons = bot.last()

check("sinf so'raldi", "sinf" in text.lower())
check("7 ta sinf tugmasi (Fortepiano 7 yillik): " + str(len(buttons)),
      len(buttons) == 7)


# ==========================
# 3. KUN
# ==========================

bot.fire(find(buttons, "3-sinf"))
text, buttons = bot.last()

check("kun so'raldi", "kun" in text.lower())
check("6 kun (yakshanbasiz)", len(buttons) == 6)
check("Shanba bor", find(buttons, "Shanba") is not None)
check("Yakshanba yo'q", find(buttons, "Yakshanba") is None)


# ==========================
# 4. REJA VA DAVOMIYLIK
# ==========================

bot.fire(find(buttons, "Dushanba"))
text, buttons = bot.last()

check("reja ko'rsatildi: " + text.split("\n")[0][:44],
      "Reja" in text)

check("Mutaxassislik 3-sinf 2 soat deb topildi", "2 soat" in text)

check("bo'linish taklif qilindi (2 soat >= chegara)",
      "nechta soat" in text.lower() or "Qolgan" in text)


# ==========================
# 5. DARS VAQTLARI
# ==========================

# 1 soat tanlaymiz - kunlarga bo'lib qo'yamiz
bot.fire(find(buttons, "1 soat"))
text, buttons = bot.last()

check("vaqt so'raldi", "vaqt" in text.lower())

times = [t for t, _ in buttons]

check("10 ta vaqt tugmasi: " + str(len(times)), len(times) == 10)
check("birinchi vaqt 08:00-08:45", times[0] == "08:00-08:45")
check("oxirgi vaqt 16:20-17:05", times[-1] == "16:20-17:05")
check("tushlik ustida vaqt yo'q",
      not any(t.startswith("12:") for t in times))


# ==========================
# 6. XONA VA SAQLASH
# ==========================

bot.fire(buttons[0][1])
text, buttons = bot.last()

check("xona so'raldi", "xona" in text.lower())

# Xona endi qo'lda yozilmaydi - qat'iy ro'yxatdan tanlanadi
ROOM_CODES = db.get_room_codes()

room_labels = [t for t, _ in buttons]

check("hamma xona tugma bo'lib chiqdi: " + str(len(room_labels)),
      len(room_labels) == len(ROOM_CODES))
check("birinchi xona 1/5", room_labels[0] == "1/5")
check("oxirgi xona 2/19b", room_labels[-1] == "2/19b")
check("hech biri band emas (baza bo'sh)",
      not any("🔒" in t for t in room_labels))
check("bu vaqtda hamma xona bo'sh deyildi",
      "barcha xonalar bo'sh" in text.lower())

bot.fire(find(buttons, "2/4"))

slots = db.get_teacher_slots("Karimov A.")

check("dars saqlandi: " + str(slots), len(slots) == 1)

if slots:
    slot_id, subject, day, time, room = slots[0]
    check("fan to'g'ri", subject == "Mutaxassislik")
    check("kun to'g'ri", day == "Dushanba")
    check("vaqt to'g'ri: " + time, time == "08:00")
    check("xona to'g'ri", room == "2/4")
    check("sinf saqlandi", db.get_slot_class(slot_id) == "3")
    check("davomiylik 45 daqiqa", db.get_slot_duration(slot_id) == 45)


# ==========================
# 6b. BO'LAK QO'YILGACH DARROV DAVOM ETADI
# ==========================

text, buttons = bot.last()

check("saqlangach qolgan soat taklif qilindi: "
      + text.split(chr(10))[0][:46],
      "qoldi" in text)

check("darrov kun tugmalari chiqdi (fan/sinf qayta so'ralmadi)",
      find(buttons, "Chorshanba") is not None)

check("keyinroq qoldirish tugmasi bor",
      find(buttons, "Keyinroq") is not None)

# davom etamiz - fan va sinf saqlanib qolganini tekshiramiz
bot.fire(find(buttons, "Payshanba"))
text, buttons = bot.last()

check("qolgan soat 1 deb ko'rsatildi", "Qolgan: 1 soat" in text)

bot.fire(find(buttons, "1 soat"))
_, buttons = bot.last()
bot.fire(buttons[0][1])
text, buttons = bot.last()

# Payshanba - boshqa kun, shuning uchun 2/4 yana bo'sh
check("boshqa kuni 2/4 bo'sh ko'rindi",
      find(buttons, "2/4") is not None)

bot.fire(find(buttons, "2/4"))

slots = db.get_teacher_slots("Karimov A.")

check("ikkinchi bo'lak saqlandi: " + str(len(slots)) + " ta dars",
      len(slots) == 2)

check("reja to'ldi - endi taklif qilinmaydi",
      "qoldi" not in bot.last()[0])


# ==========================
# 7. REJA TO'LGACH OGOHLANTIRADI
# ==========================
#
# 6b da 2 soat to'liq qo'yildi. Yana qo'shmoqchi bo'lsak
# bot ogohlantirishi kerak - lekin to'smasligi kerak.

bot.fire("tsch:new")
_, buttons = bot.last()
bot.fire(find(buttons, "Mutaxassislik"))
_, buttons = bot.last()
bot.fire(find(buttons, "3-sinf"))
_, buttons = bot.last()
bot.fire(find(buttons, "Shanba"))
text, buttons = bot.last()

check("reja to'lgani aytildi", "allaqachon" in text)

check("lekin to'smaydi - tugmalar bor", len(buttons) > 0)


# ==========================
# 8. BAND VAQT CHIQARILMAYDI
# ==========================

bot.fire(find(buttons, "1 soat"))
text, buttons = bot.last()

times = [t for t, _ in buttons]

check("Chorshanbada 10 ta vaqt (boshqa kun band emas)",
      len(times) == 10)

# Dushanba band - o'sha kunni tekshiramiz
bot.fire("tsch:new")
_, b = bot.last()
bot.fire(find(b, "Solfedjio"))
_, b = bot.last()
bot.fire(find(b, "1-sinf"))
_, b = bot.last()
bot.fire(find(b, "Dushanba"))
text, b = bot.last()

# bo'linmaydigan fanda davomiylik so'ralmaydi: bot xabar
# beradi va darrov vaqtlarga o'tadi, shuning uchun oxirgidan
# oldingi xabarni tekshiramiz
notice = bot.messages[-2][0]

check("Solfedjio 1-sinf 1,5 soat - bo'linmaydi: " + notice.split(chr(10))[-1][:40],
      "bo'linmaydi" in notice and "1,5 soat" in notice)

times = [t for t, _ in bot.last()[1]]

check("08:00 band, shuning uchun chiqmadi: " + str(times[:2]),
      not any(t.startswith("08:00") for t in times))


# ==========================
# 9. BAND XONA KIM TOMONIDAN BAND QILINGANI
# ==========================
#
# Boshqa o'qituvchi ayni kun va vaqtga dars qo'ymoqchi.
# 2/4 xonasi Karimov A. tomonidan band - buni ko'rishi kerak.

db.add_teacher("Aliyev Bobur", "Fortepiano")

OTHER = 777

bot2 = FakeBot()
register_teacher_schedule(bot2, {OTHER: "Aliyev Bobur"})


class Msg2(Msg):
    def __init__(self, text=""):
        Msg.__init__(self, text)
        self.chat = type("C", (), {"id": OTHER})()


class Call2(Call):
    def __init__(self, data):
        Call.__init__(self, data)
        self.message = Msg2()


def fire2(data):
    call = Call2(data)
    for func, fn in bot2.callbacks:
        if func(call):
            fn(call)
            return True
    return False


fire2("tsch:new")
_, b = bot2.last()
fire2(find(b, "Mutaxassislik"))
_, b = bot2.last()
fire2(find(b, "3-sinf"))
_, b = bot2.last()
fire2(find(b, "Dushanba"))
_, b = bot2.last()
fire2(find(b, "1 soat"))
_, b = bot2.last()

# 08:00 - Karimov A. shu vaqtda 2/4 da dars o'tadi
slot_time = [x for x in b if x[0].startswith("08:00")]
fire2(slot_time[0][1])

text, b = bot2.last()

room_buttons = b
labels = [t for t, _ in b]

check("band xona qulf bilan belgilandi",
      "🔒 2/4" in labels)

check("bo'sh xonada qulf yo'q", "2/5" in labels)

check("band xonalar ro'yxati chiqdi", "Band xonalar" in text)

check("kim band qilgani yozildi: "
      + [ln for ln in text.split(chr(10)) if "2/4" in ln][0][:40],
      "2/4 - Karimov A." in text)

# band xonani bossa - kim bandligini aytadi, ro'yxat yopilmaydi
fire2(find(room_buttons, "🔒 2/4"))
text, b = bot2.last()

check("bosilganda ham o'qituvchi ismi ko'rsatildi",
      "Karimov A." in text and "band" in text)

check("jo'rnavozlik taklif qilindi",
      find(b, "jo'rnavoz") is not None)

check("band xonaga dars saqlanmadi",
      len(db.get_teacher_slots("Aliyev Bobur")) == 0)

# bo'sh xonani tanlasa - saqlanadi
fire2(find(room_buttons, "2/5"))

check("bo'sh xona tanlangach saqlandi",
      len(db.get_teacher_slots("Aliyev Bobur")) == 1)


# ==========================
# 10. O'QUVCHISI BOR DARSNI O'CHIRISH - OGOHLANTIRADI
# ==========================
#
# Bekorga bosilib ketsa o'quvchilar yo'qolib qolmasin (buni
# ochib olmasdan turib avval o'quvchisiz dars o'chirilishi
# to'g'ridan-to'g'ri ishlashini ham tekshiramiz).

empty_slot = db.create_slot(
    "Karimov A.", "Mutaxassislik", "Juma", "10:00", "1/5", 45
)

bot.fire("tsch:view:" + str(empty_slot))
text, buttons = bot.last()

del_data = find(buttons, "butunlay o'chirish")

check("o'quvchisiz darsda to'g'ridan-to'g'ri o'chirish tugmasi",
      del_data == "tsch:delslot:" + str(empty_slot))

bot.fire(del_data)

check("o'quvchisiz dars darrov o'chdi",
      db.get_slot(empty_slot) is None)

# endi o'quvchisi bor dars

full_slot = db.create_slot(
    "Karimov A.", "Mutaxassislik", "Juma", "11:00", "1/5", 45
)

db.add_student_to_slot(full_slot, "Bir bola", "Karimov A.")

bot.fire("tsch:view:" + str(full_slot))
text, buttons = bot.last()

ask_data = find(buttons, "butunlay o'chirish")

check("o'quvchisi bor darsda so'rovga yo'naladi",
      ask_data == "tsch:delslotask:" + str(full_slot))

bot.fire(ask_data)
text, buttons = bot.last()

check("ogohlantirish sonni ko'rsatadi", "1 ta o'quvchi" in text)

check("hali o'chmagan", db.get_slot(full_slot) is not None)

confirm_data = find(buttons, "Ha, o'quvchilar bilan")

check("tasdiqlash tugmasi bor", confirm_data is not None)

bot.fire(confirm_data)

check("tasdiqlangach o'chdi", db.get_slot(full_slot) is None)


# ==========================
print()
for line in ok:
    print("  OK   " + line)
for line in bad:
    print("  XATO " + line)
print()
print(str(len(ok)) + " ta o'tdi, " + str(len(bad)) + " ta xato")

sys.exit(1 if bad else 0)
