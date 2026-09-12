# -*- coding: utf-8 -*-
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import database as db

os.makedirs(os.path.join(os.path.dirname(os.path.abspath(__file__)), "_tmp"), exist_ok=True)
DB = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                  "_tmp", "test_lesson_variants.db")

if os.path.exists(DB):
    os.remove(DB)

db.DB_NAME = DB
db.create_tables()
db.migrate_schema()

db.add_teacher("Test Teacher", "Fortepiano")

import webapp.server as ws

client = ws.app.test_client()

ok, bad = [], []


def check(label, cond):
    (ok if cond else bad).append(label)


# Mocking authentication for webapp
CURRENT = {"id": 111}
ws._authenticated_user = lambda: CURRENT
ws.find_teacher_binding = lambda uid: ("Test Teacher", "Fortepiano") if uid == 111 else None

# ==========================
# 1. variant_minutes
# ==========================
check("variant_minutes(1.5) == [65, 70]", db.variant_minutes(1.5) == [65, 70])
check("variant_minutes(1) == [45]", db.variant_minutes(1) == [45])

# ==========================
# 2. is_valid_variant
# ==========================
check("is_valid_variant(1.5, 65) is True", db.is_valid_variant(1.5, 65) is True)
check("is_valid_variant(1.5, 70) is True", db.is_valid_variant(1.5, 70) is True)
check("is_valid_variant(1.5, 67) is False", db.is_valid_variant(1.5, 67) is False)
check("is_valid_variant(1, 65) is False", db.is_valid_variant(1, 65) is False)
check("is_valid_variant(2, 65) is False", db.is_valid_variant(2, 65) is False)

# ==========================
# 3. variant_label
# ==========================
check("variant_label(1.5, 65) ichida 1 soat 5 daqiqa", "1 soat 5 daqiqa" in db.variant_label(1.5, 65))
check("variant_label(1.5, 70) ichida 1 soat 10 daqiqa", "1 soat 10 daqiqa" in db.variant_label(1.5, 70))

# ==========================
# 4. Reja hisobi buzilmaydi
# ==========================
# bitta 65
slot1 = db.create_slot("Test Teacher", "Mutaxassislik", "Dushanba", "08:00", "1", 65, "1")
check("65 min -> 1.5 soat", db.scheduled_hours("Test Teacher", "Mutaxassislik", "1") == 1.5)

# bitta 70
db.delete_slot(slot1)
slot2 = db.create_slot("Test Teacher", "Mutaxassislik", "Dushanba", "08:00", "1", 70, "1")
check("70 min -> 1.5 soat", db.scheduled_hours("Test Teacher", "Mutaxassislik", "1") == 1.5)

# ikkita 65 -> 3.0
db.delete_slot(slot2)
slot3 = db.create_slot("Test Teacher", "Mutaxassislik", "Dushanba", "08:00", "1", 65, "1")
slot4 = db.create_slot("Test Teacher", "Mutaxassislik", "Seshanba", "08:00", "1", 65, "1")
check("ikkita 65 -> 3.0 soat", db.scheduled_hours("Test Teacher", "Mutaxassislik", "1") == 3.0)

# 65 + 70 -> 3.0
db.delete_slot(slot3)
db.delete_slot(slot4)
slot5 = db.create_slot("Test Teacher", "Mutaxassislik", "Dushanba", "08:00", "1", 65, "1")
slot6 = db.create_slot("Test Teacher", "Mutaxassislik", "Seshanba", "08:00", "1", 70, "1")
check("65 + 70 -> 3.0 soat", db.scheduled_hours("Test Teacher", "Mutaxassislik", "1") == 3.0)
db.delete_slot(slot5)
db.delete_slot(slot6)

# ==========================
# 5. Mini App POST /api/teacher/slots
# ==========================
times_65 = db.available_lesson_times(65)
times_70 = db.available_lesson_times(70)

t65_start = times_65[0][0]
t70_start = times_70[1][0]

r_65 = client.post("/api/teacher/slots", json={
    "subject": "Mutaxassislik", "day": "Chorshanba",
    "time": t65_start, "hours": 1.5, "minutes": 65, "room": "2/4", "class": "1"
})
check("minutes: 65 -> 200", r_65.status_code == 200)
if r_65.status_code != 200:
    print(r_65.get_json())
slot_65_id = r_65.get_json().get("id", -1)
check("get_slot_duration == 65", db.get_slot_duration(slot_65_id) == 65)

r_67 = client.post("/api/teacher/slots", json={
    "subject": "Mutaxassislik", "day": "Chorshanba",
    "time": "14:00", "hours": 1.5, "minutes": 67, "room": "2/4", "class": "1"
})
check("minutes: 67 -> 400", r_67.status_code == 400)

r_none = client.post("/api/teacher/slots", json={
    "subject": "Mutaxassislik", "day": "Payshanba",
    "time": t70_start, "hours": 1.5, "room": "2/4", "class": "1"
})
check("minutes berilmagan -> 200", r_none.status_code == 200)
if r_none.status_code != 200:
    print(r_none.get_json())
slot_none_id = r_none.get_json().get("id", -1)
check("default 1.5 -> 70", db.get_slot_duration(slot_none_id) == 70)


# ==========================
# 6. /api/teacher/me javobida variantlar
# ==========================
r_me = client.get("/api/teacher/me")
data_me = r_me.get_json()
variants_1_5 = [v for v in data_me["academic_hours"] if v["hours"] == 1.5]
check("hours == 1.5 bo'lgan ikkita element", len(variants_1_5) == 2)
minutes_set = {v["minutes"] for v in variants_1_5}
check("minutes lari {65, 70}", minutes_set == {65, 70})

print()
for line in ok:
    print("  OK   " + line)

for line in bad:
    print("  XATO " + line)

print()
print(str(len(ok)) + " ta o'tdi, " + str(len(bad)) + " ta xato")

# Cleanup
if os.path.exists(DB):
    os.remove(DB)

sys.exit(1 if bad else 0)
