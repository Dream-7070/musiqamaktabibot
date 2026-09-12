# -*- coding: utf-8 -*-
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import database as db

os.makedirs(os.path.join(os.path.dirname(os.path.abspath(__file__)), "_tmp"), exist_ok=True)
DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_tmp", "test_schedule_planner.db")

if os.path.exists(DB):
    os.remove(DB)

db.DB_NAME = DB
db.create_tables()
db.migrate_schema()

from services.schedule_planner import generate_variants
from database import DAYS_OF_WEEK

ok, bad = [], []

def check(label, cond):
    (ok if cond else bad).append(label)

# 1. Asosiy: 6 ta o'quvchi, barcha 6 kun ruxsat etilgan
lessons = [{"who": "Bola%d" % i, "subject": "Mutaxassislik", "class_name": "1",
            "duration_minutes": 45, "is_group": False, "members": None}
           for i in range(1, 7)]

variants = generate_variants("Karimov Aziz", lessons, list(DAYS_OF_WEEK), None, max_variants=3)

v1_days = [l["day"] for l in variants[0]["lessons"]]
unique_days = set(v1_days)
day_counts = {day: v1_days.count(day) for day in unique_days}

check("1. Darslar kamida 4 xil kunga taqsimlansin", len(unique_days) >= 4)
check("1. Hech bir kunda 2 tadan ko'p bo'lmasin", all(count <= 2 for count in day_counts.values()))

# 2. Bitta bolaning ikki darsi har xil kunda
lessons_one_kid = [
    {"who": "Bola1", "duration_minutes": 45},
    {"who": "Bola1", "duration_minutes": 45},
]
variants_one_kid = generate_variants("Karimov Aziz", lessons_one_kid, list(DAYS_OF_WEEK), None, max_variants=1)
v_one_days = [l["day"] for l in variants_one_kid[0]["lessons"]]
check("2. Ikkita dars bitta kunga tushmasin", v_one_days[0] != v_one_days[1])

# 3. Variantlar bir-biridan farq qilsin
check("3. Variantlar bir xil bo'lmasin",
      variants[0]["lessons"] != variants[1]["lessons"] and
      variants[1]["lessons"] != variants[2]["lessons"])

# 4. Cheklov hurmat qilinadi
lessons_juma = [{"who": "Bola1", "duration_minutes": 45}]
variants_juma = generate_variants("Karimov Aziz", lessons_juma, ["Juma"], None, max_variants=1)
check("4. Dars faqat Jumaga tushsin", all(l["day"] == "Juma" for l in variants_juma[0]["lessons"]))

# 5. Smena filtri buzilmasin
lessons_shift = [
    {"who": "Bola1", "duration_minutes": 45, "shift": "tushlikgacha"},
    {"who": "Bola2", "duration_minutes": 45, "shift": "tushlikdan_keyin"}
]
variants_shift = generate_variants("Karimov Aziz", lessons_shift, list(DAYS_OF_WEEK), None, max_variants=1)
v_shift = variants_shift[0]["lessons"]

def time_to_min(t):
    h, m = t.split(":")
    return int(h) * 60 + int(m)

shift_ok = True
for l in v_shift:
    if l["who"] == "Bola1" and time_to_min(l["end"]) > db.LUNCH_START:
        shift_ok = False
    if l["who"] == "Bola2" and time_to_min(l["start"]) < db.LUNCH_END:
        shift_ok = False
check("5. Smena filtri ishladi", shift_ok)

# 6. Joylashtirib bo'lmasa unplaced to'ldiriladi
lessons_too_many = [{"who": "Bola%d" % i, "duration_minutes": 45} for i in range(1, 10)]
variants_too_many = generate_variants("Karimov Aziz", lessons_too_many, ["Yakshanba"], None, max_variants=1)
check("6. complete False bo'lsin", variants_too_many[0]["complete"] == False)
check("6. unplaced bo'sh emas", len(variants_too_many[0]["unplaced"]) > 0)

print()
for line in ok:
    print("  OK   " + line)

for line in bad:
    print("  XATO " + line)

print()
print(str(len(ok)) + " ta o'tdi, " + str(len(bad)) + " ta xato")

sys.exit(1 if bad else 0)
