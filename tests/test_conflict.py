# -*- coding: utf-8 -*-
"""Jadval to'qnashuvlari va ITV takrori."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import database as db

os.makedirs(os.path.join(os.path.dirname(os.path.abspath(__file__)), "_tmp"), exist_ok=True)
DB = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                  "_tmp", "test_conflict.db")

if os.path.exists(DB):
    os.remove(DB)

db.DB_NAME = DB
db.create_tables()
db.migrate_schema()

ok, bad = [], []


def check(label, cond):
    (ok if cond else bad).append(label)


db.add_teacher("Karimov A.", "Fortepiano")     # mutaxassislik
db.add_teacher("Ismoilova N.", "Fortepiano")   # jo'rnavoz
db.add_teacher("Berdiqulov I.", "Nazariy")     # solfedjio
db.add_teacher("Yusupov K.", "Torli")

db.add_student("Karimov A.", "Ali Valiyev", "2015-01-01", "I-TV 1111111", "3", 123600)
db.add_student("Yusupov K.", "Zebo Karimova", "2015-02-02", "I-TV 2222222", "3", 82400)


# ==========================
# VAQT NORMALLASHTIRISH
# ==========================

check("15.00 -> 15:00", db.normalize_time("15.00") == "15:00")
check("9:5 -> 09:05", db.normalize_time("9:5") == "09:05")
check("1500 -> 15:00", db.normalize_time("1500") == "15:00")
check("noto'g'ri vaqt rad etiladi", db.normalize_time("25:00") is None)

slot1 = db.create_slot("Karimov A.", "Akkompanement", "Dushanba", "15.00", "12")
check("slot vaqti normallashib saqlandi", db.get_slot(slot1)[4] == "15:00")


# ==========================
# XONA TO'QNASHUVI
# ==========================

hit = db.find_room_conflict("Dushanba", "15:00", "12")
check("bir xil vaqt+xona band: " + str(hit and hit[1]),
      hit is not None and hit[1] == "Karimov A.")

check("dars ichida kesishsa ham band (15:30)",
      db.find_room_conflict("Dushanba", "15:30", "12") is not None)

check("dars tugagach bo'sh (15:45)",
      db.find_room_conflict("Dushanba", "15:45", "12") is None)

check("boshqa xona bo'sh",
      db.find_room_conflict("Dushanba", "15:00", "5") is None)

check("boshqa kun bo'sh",
      db.find_room_conflict("Seshanba", "15:00", "12") is None)

check("'12-xona' ham xuddi shu xona",
      db.find_room_conflict("Dushanba", "15:00", "12-xona") is not None)

check("o'zini tekshirganda band emas",
      db.find_room_conflict("Dushanba", "15:00", "12",
                            exclude_slot_id=slot1) is None)


# ==========================
# O'QITUVCHI TO'QNASHUVI
# ==========================

check("dars egasi shu vaqtda band",
      db.find_teacher_conflict("Karimov A.", "Dushanba", "15:00") is not None)

check("boshqa o'qituvchi band emas",
      db.find_teacher_conflict("Ismoilova N.", "Dushanba", "15:00") is None)

db.add_concertmaster(slot1, "Ismoilova N.")

check("jo'rnavoz ham o'sha vaqtda band hisoblanadi",
      db.find_teacher_conflict("Ismoilova N.", "Dushanba", "15:00") is not None)

check("jo'rnavoz o'sha darsning o'zini tekshirsa - band emas",
      db.find_teacher_conflict("Ismoilova N.", "Dushanba", "15:00",
                               exclude_slot_id=slot1) is None)


# ==========================
# O'QUVCHI TO'QNASHUVI
# ==========================

db.add_student_to_slot(slot1, "Ali Valiyev", "Karimov A.")

# Berdiqulov boshqa xonada, o'sha vaqtda solfedjio ochadi
slot2 = db.create_slot("Berdiqulov I.", "Solfedjio", "Dushanba", "15:00", "7")

hit = db.find_student_conflict(
    "Ali Valiyev", "Karimov A.", "Dushanba", "15:00", exclude_slot_id=slot2
)

check("o'quvchi shu vaqtda boshqa darsda: " + str(hit and hit[2]),
      hit is not None and hit[2] == "Akkompanement")

check("band bo'lmagan o'quvchi qo'shilaveradi",
      db.find_student_conflict("Zebo Karimova", "Yusupov K.",
                               "Dushanba", "15:00",
                               exclude_slot_id=slot2) is None)

check("boshqa vaqtda o'quvchi bo'sh",
      db.find_student_conflict("Ali Valiyev", "Karimov A.",
                               "Dushanba", "16:00",
                               exclude_slot_id=slot2) is None)


# ==========================
# AYNI DARSDA KO'P O'QITUVCHI - TO'QNASHUV EMAS
# ==========================
#
# Karimov mutaxassislik o'tadi, Ismoilova jo'rnavozlik qiladi,
# o'quvchi esa bitta - bu bitta dars, to'qnashuv bo'lmasligi kerak.

check("ayni darsda 2 o'qituvchi - to'qnashuv yo'q",
      "Ismoilova N." in db.get_slot_concertmasters(slot1)
      and db.find_student_conflict(
          "Ali Valiyev", "Karimov A.", "Dushanba", "15:00",
          exclude_slot_id=slot1) is None)


# ==========================
# ITV TAKRORI
# ==========================

check("mavjud ITV boshqa o'qituvchida topiladi",
      db.find_metrika_duplicate("I-TV 1111111", teacher="Berdiqulov I.")
      == ("other_teacher", "Karimov A.", "Ali Valiyev"))

check("shu o'qituvchining o'zida - takror deb to'siladi",
      db.find_metrika_duplicate("I-TV 1111111", teacher="Karimov A.")
      == ("same_teacher", "Karimov A.", "Ali Valiyev"))

check("bo'shliq/registr farq qilmaydi",
      db.find_metrika_duplicate("itv1111111") is not None)

check("yangi ITV toza",
      db.find_metrika_duplicate("I-TV 9999999") is None)

check("o'zini tahrirlaganda takror hisoblanmaydi",
      db.find_metrika_duplicate("I-TV 1111111",
                                exclude_teacher="Karimov A.",
                                exclude_student="Ali Valiyev") is None)


# ==========================
print()
for line in ok:
    print("  OK   " + line)
for line in bad:
    print("  XATO " + line)
print()
print(str(len(ok)) + " ta o'tdi, " + str(len(bad)) + " ta xato")

sys.exit(1 if bad else 0)
