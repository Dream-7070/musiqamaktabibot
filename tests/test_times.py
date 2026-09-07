# -*- coding: utf-8 -*-
"""Dars vaqtlari tarmog'i, davomiylik va o'quv rejasi."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import database as db

os.makedirs(os.path.join(os.path.dirname(os.path.abspath(__file__)), "_tmp"), exist_ok=True)
DB = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                  "_tmp", "test_times.db")

if os.path.exists(DB):
    os.remove(DB)

db.DB_NAME = DB
db.create_tables()
db.migrate_schema()

ok, bad = [], []


def check(label, cond):
    (ok if cond else bad).append(label)


# ==========================
# VAQT TARMOG'I
# ==========================

check("10 ta dars vaqti: " + str(len(db.LESSON_TIMES)),
      len(db.LESSON_TIMES) == 10)

check("birinchi dars 08:00", db.LESSON_TIMES[0] == "08:00")
check("oxirgi dars 16:20", db.LESSON_TIMES[-1] == "16:20")

check("tushlik ustida dars yo'q",
      "12:05" not in db.LESSON_TIMES and "12:10" not in db.LESSON_TIMES)

check("tushlikdan keyin 13:00 dan boshlanadi",
      db.LESSON_TIMES[5] == "13:00")

check("yakshanba olib tashlandi",
      "Yakshanba" not in db.DAYS_OF_WEEK and len(db.DAYS_OF_WEEK) == 6)

check("shanba bor", "Shanba" in db.DAYS_OF_WEEK)


# ==========================
# DAVOMIYLIK
# ==========================

check("0,5 soat = 25 daqiqa", db.hours_to_minutes(0.5) == 25)
check("1 soat = 45 daqiqa", db.hours_to_minutes(1) == 45)
check("1,5 soat = 70 daqiqa", db.hours_to_minutes(1.5) == 70)
check("2 soat = 90 daqiqa", db.hours_to_minutes(2) == 90)
check("3 soat = 135 daqiqa", db.hours_to_minutes(3) == 135)
check("4 soat = 180 daqiqa", db.hours_to_minutes(4) == 180)

check("yorliq: " + db.hours_label(1.5),
      db.hours_label(1.5) == "1,5 soat (1 soat 10 daqiqa)")


# ==========================
# MAVJUD VAQTLAR
# ==========================

counts = {h: len(db.available_lesson_times(db.hours_to_minutes(h)))
          for h in db.ACADEMIC_HOURS}

check("1 soat -> 10 ta vaqt", counts[1] == 10)
check("2 soat -> 8 ta vaqt", counts[2] == 8)
check("3 soat -> 6 ta vaqt", counts[3] == 6)
check("4 soat -> 4 ta vaqt", counts[4] == 4)

four = db.available_lesson_times(180)

check("4 soatlik dars 09:40 da boshlana olmaydi (tushlik)",
      "09:40" not in [s for s, _ in four])

check("4 soatlik dars 08:00-11:00", four[0] == ("08:00", "11:00"))

check("oxirgi 1 soatlik dars aynan 17:05 da tugaydi",
      db.available_lesson_times(45)[-1] == ("16:20", "17:05"))

check("11:20 dagi 45 daqiqalik dars aynan tushlikda tugaydi",
      ("11:20", "12:05") in db.available_lesson_times(45))


# ==========================
# DAVOMIYLIK BILAN TO'QNASHUV
# ==========================

db.add_teacher("Karimov A.", "Fortepiano")
db.add_teacher("Ismoilova N.", "Fortepiano")

slot = db.create_slot("Karimov A.", "Mutaxassislik", "Dushanba",
                      "08:00", "12", 90)

check("davomiylik saqlandi", db.get_slot_duration(slot) == 90)

check("90 daqiqalik dars 08:50 ni ham to'sadi",
      db.find_room_conflict("Dushanba", "08:50", "12", 45) is not None)

check("09:40 bo'sh (dars 09:30 da tugaydi)",
      db.find_room_conflict("Dushanba", "09:40", "12", 45) is None)

check("o'qituvchi 08:50 da band",
      db.find_teacher_conflict("Karimov A.", "Dushanba", "08:50", 45)
      is not None)

check("boshqa xonada 08:50 bo'sh",
      db.find_room_conflict("Dushanba", "08:50", "7", 45) is None)


# ==========================
# O'QUV REJASI
# ==========================

from data.curriculum import CURRICULUM, WEEKS_PER_YEAR

check("35 ta mutaxassislik", len(CURRICULUM) == 35)

check("Fortepiano 7 yillik",
      CURRICULUM["Fortepiano ijrochiligi"]["years"] == 7)

check("Tasviriy yo'nalish 5 yillik",
      CURRICULUM["Dastgohli rangtasvir"]["years"] == 5)

fp = CURRICULUM["Fortepiano ijrochiligi"]["subjects"]

check("Fortepiano mutaxassislik 1-sinfda 2 soat",
      fp["Mutaxassislik"]["1"] == 2)

check("Fortepiano mutaxassislik 7-sinfda 3 soat",
      fp["Mutaxassislik"]["7"] == 3)

check("Ansambl 1-2 sinfda yo'q, 3-sinfdan boshlanadi",
      "1" not in fp["Ansambl"] and fp["Ansambl"]["3"] == 0.5)

check("Solfedjio 1-6 sinfda 1,5 soat",
      all(fp["Solfedjio"][str(c)] == 1.5 for c in range(1, 7)))

# har bir fan umumiy soati bilan mos kelishi kerak
mismatch = 0
for name, data in CURRICULUM.items():
    for subject, hours in data["subjects"].items():
        if not hours:
            mismatch += 1
        for cls in hours:
            if int(cls) > data["years"]:
                mismatch += 1

check("hech bir fan mavjud bo'lmagan sinfga tegishli emas",
      mismatch == 0)

check("Xoreografiyada 4 soatlik fan bor",
      CURRICULUM["Klassik raqs ijrochiligi"]["subjects"]
      ["Mutaxassislik (klassik raqs)"]["4"] == 4)


# ==========================
print()
for line in ok:
    print("  OK   " + line)
for line in bad:
    print("  XATO " + line)
print()
print(str(len(ok)) + " ta o'tdi, " + str(len(bad)) + " ta xato")

sys.exit(1 if bad else 0)
