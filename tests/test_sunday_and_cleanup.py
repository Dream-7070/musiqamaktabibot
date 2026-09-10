# -*- coding: utf-8 -*-
"""Yakshanba (dam olish kuni) va dars o'chirilganda jo'rnavozning tozalanishi."""

import os
import sys

from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import database as db

os.makedirs(os.path.join(os.path.dirname(os.path.abspath(__file__)), "_tmp"), exist_ok=True)
DB = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                  "_tmp", "test_sunday_and_cleanup.db")

if os.path.exists(DB):
    os.remove(DB)

db.DB_NAME = DB
db.create_tables()
db.migrate_schema()

db.add_teacher("Karimov Aziz", "Fortepiano")
db.add_teacher("Sobirova Nilufar", "Fortepiano")

import webapp.server as ws

client = ws.app.test_client()

ok, bad = [], []


def check(label, cond):
    (ok if cond else bad).append(label)


CURRENT = {"id": 999}

ws._authenticated_user = lambda: CURRENT
ws.ADMIN_IDS = [999]
ws.find_teacher_binding = lambda uid: None


# ==========================
# 1. YAKSHANBA - CRASH BO'LMASLIGI KERAK
# ==========================
#
# DAYS_OF_WEEK da 6 kun bor, weekday() esa yakshanbada 6
# qaytaradi. Ilgari shu yerda IndexError chiqardi.

class FakeDatetime(datetime):

    FIXED = None

    @classmethod
    def now(cls, tz=None):
        return cls.FIXED


real_datetime = ws.datetime

# 2026-09-13 - yakshanba
FakeDatetime.FIXED = FakeDatetime(2026, 9, 13, 11, 30)
ws.datetime = FakeDatetime

r = client.get("/api/admin/live")

check("yakshanba crash bermadi", r.status_code == 200)

data = r.get_json()

check("kun nomi Yakshanba", data["day"] == "Yakshanba")
check("dars ro'yxati bo'sh", data["live"] == [])
check("vaqt ko'rsatildi", data["now"] == "11:30")


# ==========================
# 2. ODDIY KUN ILGARIDEK ISHLAYDI
# ==========================

slot_id = db.create_slot(
    "Karimov Aziz", "Akkompanement", "Dushanba", "11:00", "2/4", 45
)

db.add_student_to_slot(slot_id, "Aliyev Ali", "Karimov Aziz")

# 2026-09-14 - dushanba, 11:30 (dars 11:00-11:45)
FakeDatetime.FIXED = FakeDatetime(2026, 9, 14, 11, 30)

data = client.get("/api/admin/live").get_json()

check("dushanba kuni ishladi", data["day"] == "Dushanba")
check("ketayotgan dars ko'rindi", len(data["live"]) == 1)
check("o'quvchisi bilan", data["live"][0]["students"] == ["Aliyev Ali"])

ws.datetime = real_datetime


# ==========================
# 3. DARS O'CHSA - JO'RNAVOZ HAM O'CHADI
# ==========================

db.add_concertmaster(slot_id, "Sobirova Nilufar")

check("jo'rnavoz biriktirildi",
      len(db.get_slot_concertmasters(slot_id)) == 1)

db.delete_slot(slot_id)

check("dars o'chdi", db.get_slot(slot_id) is None)
check("jo'rnavoz yozuvi ham o'chdi",
      len(db.get_slot_concertmasters(slot_id)) == 0)
check("o'quvchi yozuvi ham o'chdi",
      len(db.get_slot_students(slot_id)) == 0)

# bazada umuman yetim qator qolmadimi

conn = db.connect()

left = conn.execute(
    """
    SELECT COUNT(*) FROM slot_concertmasters
    WHERE slot_id NOT IN (SELECT id FROM schedule_slots)
    """
).fetchone()[0]

conn.close()

check("yetim jo'rnavoz qatori yo'q", left == 0)


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
