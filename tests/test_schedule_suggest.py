# -*- coding: utf-8 -*-
"""
Jadval taklifidagi smena tanlash oqimi.

Ilgari o'quvchi tugmasi har bosilganda holat aylanardi
(farqi yo'q -> tushlikgacha -> tushlikdan keyin -> kerak emas).
Maktab xodimlari buni tushunmasdi, shuning uchun endi ism
bosilganda aniq tugmali menyu ochiladi.

Shu sinov aylanish qaytib kelmasligini ham tekshiradi.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import database as db

os.makedirs(os.path.join(os.path.dirname(os.path.abspath(__file__)), "_tmp"),
            exist_ok=True)

DB = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                  "_tmp", "test_schedule_suggest.db")

if os.path.exists(DB):
    os.remove(DB)

db.DB_NAME = DB
db.create_tables()
db.migrate_schema()

db.add_teacher("Karimov Aziz", "Fortepiano")

db.add_student("Karimov Aziz", "Aliyev Ali", "2015-01-01", "ITV001", "1", 100000)
db.add_student("Karimov Aziz", "Sobirova Nilufar", "2015-02-02", "ITV002", "1", 100000)

CHAT = 777


# ==========================
# SOXTA BOT
# ==========================
#
# test_flow.py dagi FakeBot dan farqi: bu yerda
# edit_message_text ham tugmalarni yozib boradi - bu oqim
# xabarni joyida almashtiradi, aks holda tugmalar ko'rinmay
# qolardi va sinov yolg'on yiqilardi.


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


def _buttons(reply_markup):

    buttons = []

    if reply_markup is not None:
        for row in reply_markup.keyboard:
            for b in row:
                buttons.append((b.text, b.callback_data))

    return buttons


class FakeBot:

    def __init__(self):
        self.callbacks = []
        self.messages = []
        self.msg_handlers = []

    def callback_query_handler(self, func):
        def wrap(fn):
            self.callbacks.append((func, fn))
            return fn
        return wrap

    def message_handler(self, func=None, **kwargs):
        def wrap(fn):
            self.msg_handlers.append((func, fn))
            return fn
        return wrap

    def send_message(self, chat_id, text, reply_markup=None, **k):
        self.messages.append((text, _buttons(reply_markup)))
        return Msg()

    def edit_message_text(self, text, chat_id=None, message_id=None,
                          reply_markup=None, *a, **k):
        self.messages.append((text, _buttons(reply_markup)))

    def answer_callback_query(self, *a, **k):
        pass

    def send_document(self, *a, **k):
        pass

    def register_next_step_handler(self, *a, **k):
        pass

    # --- sinov uchun yordamchilar ---

    def send(self, text):
        message = Msg(text)
        for func, fn in self.msg_handlers:
            if func is None or func(message):
                fn(message)
                return

    def fire(self, data):
        call = Call(data)
        for func, fn in self.callbacks:
            if func(call):
                fn(call)
                return

    def last(self):
        return self.messages[-1]


import handlers.schedule_suggest as suggest

bot = FakeBot()
selected = {CHAT: "Karimov Aziz"}

suggest.register_schedule_suggest(bot, selected)

ok, bad = [], []


def check(label, cond):
    (ok if cond else bad).append(label)


def holat(name):
    return suggest.ctx[CHAT]["students"][name]


# ==========================
# 1. RO'YXAT - HOLAT SO'Z BILAN
# ==========================

bot.send(suggest.BUTTON)

text, buttons = bot.last()

labels = [t for t, _ in buttons]

check("Ro'yxatda holat so'z bilan yozilgan: " + str(labels[:1]),
      any("farqi yo'q" in t for t in labels))

check("Aylanish haqidagi chalkash izoh olib tashlangan",
      "almashadi" not in text)


# ==========================
# 2. ISM BOSILGANDA MENYU OCHILADI
# ==========================

bot.fire("sug:stu:0")

text, buttons = bot.last()

labels = [t for t, _ in buttons]

check("Menyuda 5 ta tugma: " + str(len(labels)), len(labels) == 5)

check("Menyuda aniq variantlar bor",
      any("Tushlikgacha" in t for t in labels)
      and any("Tushlikdan keyin" in t for t in labels)
      and any("Orqaga" in t for t in labels))

birinchi = suggest.ctx[CHAT]["order"][0]

check("Menyu ochilishi holatni O'ZGARTIRMAYDI", holat(birinchi) == "none")


# ==========================
# 3. AYLANISH QAYTMASIN (REGRESSIYA)
# ==========================
#
# Ilgari har bosishda holat almashardi. Ikki marta bosilsa ham
# holat joyida turishi kerak.

bot.fire("sug:stu:0")
bot.fire("sug:stu:0")

check("Ikki marta bosilsa ham holat o'zgarmadi", holat(birinchi) == "none")


# ==========================
# 4. MENYUDAN TANLASH SAQLANADI
# ==========================

bot.fire("sug:shift:0:before")

check("Holat 'before' bo'lib saqlandi", holat(birinchi) == "before")

text, buttons = bot.last()

labels = [t for t, _ in buttons]

check("Tanlagach ro'yxatga qaytildi",
      any(birinchi in t and "tushlikgacha" in t for t in labels))


# ==========================
# 5. JORIY HOLAT MENYUDA BELGILANADI
# ==========================

bot.fire("sug:stu:0")

labels = [t for t, _ in bot.last()[1]]

check("Joriy holat ✅ bilan belgilangan",
      any("✅" in t and "Tushlikgacha" in t for t in labels))


# ==========================
# 6. ORQAGA - HOLATNI O'ZGARTIRMAYDI
# ==========================

bot.fire("sug:shift:0:back")

check("Orqaga holatni o'zgartirmadi", holat(birinchi) == "before")

labels = [t for t, _ in bot.last()[1]]

check("Orqaga ro'yxatni ko'rsatdi",
      any("Davom etish" in t for t in labels))


# ==========================
# 7. QATNASHMAYDI HOLATI
# ==========================

bot.fire("sug:stu:1")
bot.fire("sug:shift:1:skip")

ikkinchi = suggest.ctx[CHAT]["order"][1]

check("Ikkinchi o'quvchi 'skip' bo'ldi", holat(ikkinchi) == "skip")

labels = [t for t, _ in bot.last()[1]]

check("Ro'yxatda 'qatnashmaydi' deb yozildi",
      any(ikkinchi in t and "qatnashmaydi" in t for t in labels))


# ==========================
# 8. GURUHLI DARSLAR TAKLIFI
# ==========================
#
# Xonalar bosqichidan keyin bot guruhli fanlar uchun taklif
# ko'rsatadi. Guruhlar sinf bo'yicha tuziladi, o'qituvchi
# keraksizini o'chirib qo'yishi mumkin.

# oldingi qadamlarda ikkinchi o'quvchi "skip" bo'lgan edi -
# uni qaytaramiz, aks holda guruhga faqat bitta bola tushadi

bot.fire("sug:stu:1")
bot.fire("sug:shift:1:none")

bot.fire("sug:stu:done")     # o'quvchilar -> kunlar
bot.fire("sug:day:done")     # kunlar -> xonalar
bot.fire("sug:room:done")    # xonalar -> guruhlar

text, buttons = bot.last()

labels = [t for t, _ in buttons]

check("Guruh taklifi ko'rsatildi", "guruh" in text.lower())

check("Guruhli fanlar ro'yxatda bor: " + str(labels[:1]),
      any("Solfedjio" in t for t in labels))

check("Guruh sinf va soni bilan yozilgan",
      any("1-sinf" in t and "2 ta" in t for t in labels))

check("Me'yordan kichik guruh ⚠️ bilan belgilandi",
      any("⚠️" in t for t in labels))

check("Yakka fan guruhlar ro'yxatiga tushmadi",
      not any("Mutaxassislik" in t for t in labels))

guruhlar = suggest.ctx[CHAT]["groups"]

check("Har guruhda a'zolar (ism, sinf) ko'rinishida",
      guruhlar and isinstance(guruhlar[0]["members"][0], tuple)
      and len(guruhlar[0]["members"][0]) == 2)


# ==========================
# 9. GURUHNI O'CHIRIB QO'YISH
# ==========================

check("Guruh boshida yoqilgan", guruhlar[0]["on"] is True)

bot.fire("sug:grp:0")

check("Bosilganda o'chdi", guruhlar[0]["on"] is False)

labels = [t for t, _ in bot.last()[1]]

check("O'chirilgani ▫️ bilan ko'rsatildi",
      any(t.startswith("▫️") for t in labels))


# ==========================
# 10. TASDIQLANGANDA DARSLAR TO'G'RI QURILADI
# ==========================
#
# generate_variants ni ushlab qolamiz - haqiqiy hisoblash va
# Excel kerak emas, bizga faqat unga nima uzatilgani muhim.

tutilgan = {}


def soxta_generate(teacher, lessons, allowed_days, preferred_rooms=None,
                   max_variants=3):
    tutilgan["lessons"] = lessons
    return []


suggest.generate_variants = soxta_generate

bot.fire("sug:grp:done")

lessons = tutilgan.get("lessons", [])

guruh_darslari = [l for l in lessons if l["is_group"]]
yakka_darslari = [l for l in lessons if not l["is_group"]]

check("Yakka darslar ham bor", len(yakka_darslari) == 2)

check("O'chirilgan guruh yuborilmadi",
      len(guruh_darslari) == len(guruhlar) - 1)

check("Guruh darsida members to'ldirilgan",
      guruh_darslari and guruh_darslari[0]["members"]
      and len(guruh_darslari[0]["members"]) == 2)

check("Guruh darsining nomi fan va sinfdan yasalgan",
      guruh_darslari and "-sinf" in guruh_darslari[0]["who"])

check("Guruh darsi is_group=True bilan ketdi",
      all(l["is_group"] is True for l in guruh_darslari))


print()

for line in ok:
    print("  OK   " + line)

for line in bad:
    print("  XATO " + line)

print()
print(str(len(ok)) + " ta o'tdi, " + str(len(bad)) + " ta xato")

sys.exit(1 if bad else 0)
