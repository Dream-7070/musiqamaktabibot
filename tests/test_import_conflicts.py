# -*- coding: utf-8 -*-
"""Jadvalni import qilishdagi to'qnashuvlar."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import database as db
import telebot

# Avoid bot init in module load
import handlers.schedule_excel as se

os.makedirs(os.path.join(os.path.dirname(os.path.abspath(__file__)), "_tmp"), exist_ok=True)
DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_tmp", "test_import_conflicts.db")

if os.path.exists(DB):
    os.remove(DB)

db.DB_NAME = DB
db.create_tables()
db.migrate_schema()

ok, bad = [], []

def check(label, cond):
    (ok if cond else bad).append(label)

db.add_teacher("Karimov A.", "Fortepiano")
db.add_teacher("Ismoilova N.", "Fortepiano")

db.add_student("Karimov A.", "Ali Valiyev", "2015-01-01", "I-TV 1111111", "3", 123600)
db.add_student("Ismoilova N.", "Ali Valiyev", "2015-01-01", "I-TV 1111111", "3", 123600)

db.add_room("12", "")
db.add_room("13", "")

# 1. Boshqa o'qituvchi xonani band qilgan
slot1 = db.create_slot("Ismoilova N.", "Fortepiano", "Dushanba", "09:00", "12", 45, "")
plan1 = {
    "add": [{"day": "Dushanba", "start": 540, "minutes": 45, "room": "12", "people": [("Ali Valiyev", "Karimov A.")]}],
    "move": [], "remove": [], "keep": [], "blocked": []
}
res1 = se.find_plan_conflicts("Karimov A.", plan1)
check("1. Boshqa o'qituvchi xonada", len(res1["add"]) == 0 and len(res1["blocked"]) == 1 and "xona band" in res1["blocked"][0]["reason"])

# 2. Xuddi shu vaqt, lekin boshqa xona
plan2 = {
    "add": [{"day": "Dushanba", "start": 540, "minutes": 45, "room": "13", "people": [("Vali Aliyev", "Karimov A.")]}],
    "move": [], "remove": [], "keep": [], "blocked": []
}
res2 = se.find_plan_conflicts("Karimov A.", plan2)
check("2. Boshqa xonada", len(res2["add"]) == 1 and len(res2["blocked"]) == 0)

# 3. O'quvchi boshqa o'qituvchi darsida (slot1 Ismoilova darsi)
db.add_student_to_slot(slot1, "Ali Valiyev", "Ismoilova N.")
plan3 = {
    "add": [{"day": "Dushanba", "start": 540, "minutes": 45, "room": "13", "people": [("Ali Valiyev", "Karimov A.")]}],
    "move": [], "remove": [], "keep": [], "blocked": []
}
res3 = se.find_plan_conflicts("Karimov A.", plan3)
check("3. O'quvchi band", len(res3["add"]) == 0 and len(res3["blocked"]) == 1 and "Ali Valiyev" in res3["blocked"][0]["reason"])

# 4. O'zining darsi remove da
slot2 = db.create_slot("Karimov A.", "Fortepiano", "Seshanba", "10:00", "12", 45, "")
plan4 = {
    "add": [{"day": "Seshanba", "start": 600, "minutes": 45, "room": "12", "people": []}],
    "move": [], "remove": [{"slot_id": slot2}], "keep": [], "blocked": []
}
res4 = se.find_plan_conflicts("Karimov A.", plan4)
check("4. O'zi remove da bo'lsa", len(res4["add"]) == 1 and len(res4["blocked"]) == 0)

# 5. O'qituvchi jo'rnavoz
db.add_teacher("Qosimov B.", "Vokal")
slot3 = db.create_slot("Qosimov B.", "Vokal", "Chorshanba", "11:00", "12", 45, "")
ok_add = db.add_concertmaster(slot3, "Karimov A.")
check("5a. add_concertmaster success", ok_add)
check("5b. slot has concertmaster", "Karimov A." in db.get_slot_concertmasters(slot3))

plan5 = {
    "add": [{"day": "Chorshanba", "start": 660, "minutes": 45, "room": "13", "people": []}],
    "move": [], "remove": [], "keep": [], "blocked": []
}
res5 = se.find_plan_conflicts("Karimov A.", plan5)
check("5. O'qituvchi jo'rnavoz", len(res5["add"]) == 0 and len(res5["blocked"]) == 1 and "boshqa darsdasiz" in res5["blocked"][0]["reason"])

# 6. Fayl ichida 2 add ustma-ust
plan6 = {
    "add": [
        {"day": "Payshanba", "start": 720, "minutes": 45, "room": "12", "people": [], "who": "X"},
        {"day": "Payshanba", "start": 720, "minutes": 45, "room": "13", "people": [], "who": "Y"}
    ],
    "move": [], "remove": [], "keep": [], "blocked": []
}
res6 = se.find_plan_conflicts("Karimov A.", plan6)
check("6. Fayl ichida ustma-ust", len(res6["add"]) == 0 and len(res6["blocked"]) == 2)

# 7. move eski xonasi, yangisi band
slot4 = db.create_slot("Karimov A.", "Fortepiano", "Juma", "12:00", "12", 45, "")
slot5 = db.create_slot("Ismoilova N.", "Fortepiano", "Juma", "13:00", "13", 45, "")
plan7 = {
    "add": [],
    "move": [
        {
            "old": {"slot_id": slot4},
            "new": {"day": "Juma", "start": 780, "minutes": 45, "room": "13", "people": []}
        }
    ],
    "remove": [], "keep": [], "blocked": []
}
res7 = se.find_plan_conflicts("Karimov A.", plan7)
check("7. move -> band", len(res7["move"]) == 0 and len(res7["blocked"]) == 1 and "xona band" in res7["blocked"][0]["reason"] and len(res7["remove"]) == 0)


print()
for line in ok:
    print("  OK   " + line)
for line in bad:
    print("  XATO " + line)
print()
print(str(len(ok)) + " ta o'tdi, " + str(len(bad)) + " ta xato")

sys.exit(1 if bad else 0)
