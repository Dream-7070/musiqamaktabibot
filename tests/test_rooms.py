# -*- coding: utf-8 -*-
"""Xona tanlash: ro'yxat, bandlik va kim band qilgani."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import database as db
from data.rooms import ROOMS

os.makedirs(os.path.join(os.path.dirname(os.path.abspath(__file__)), "_tmp"), exist_ok=True)
DB = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                  "_tmp", "test_rooms.db")

if os.path.exists(DB):
    os.remove(DB)

db.DB_NAME = DB
db.create_tables()
db.migrate_schema()

ok = []
bad = []


def check(label, cond):
    (ok if cond else bad).append(label)


def room(rooms, name):
    for r in rooms:
        if r["room"] == name:
            return r
    return None


# ==========================
# 1. RO'YXATNING O'ZI
# ==========================

check("28 ta xona", len(ROOMS) == 28)
check("nuqta emas, chiziqcha bilan", all("." not in r for r in ROOMS))
check("1/5 birinchi", ROOMS[0] == "1/5")
check("2/19b oxirgi", ROOMS[-1] == "2/19b")
check("takror xona yo'q", len(ROOMS) == len(set(ROOMS)))

# _same_room nuqta/chiziqchani tashlab yuboradi - ikki xil xona
# bir xil ko'rinib qolmasligi kerak
keys = ["".join(c for c in r.lower() if c.isalnum()) for r in ROOMS]
check("xona kalitlari to'qnashmaydi", len(keys) == len(set(keys)))


# ==========================
# 2. BO'SH VAQTDA HAMMASI BO'SH
# ==========================

rooms = db.get_room_availability("Dushanba", "08:00", 45)

check("hamma xona qaytdi", len(rooms) == len(ROOMS))
check("tartib saqlandi", [r["room"] for r in rooms] == ROOMS)
check("hech biri band emas", all(not r["busy"] for r in rooms))
check("bo'sh xonada o'qituvchi yo'q", all(r["teacher"] is None for r in rooms))


# ==========================
# 3. BAND XONA VA KIM BAND QILGANI
# ==========================

db.add_teacher("Karimov Aziz", "Fortepiano")
db.add_teacher("Aliyev Bobur", "Xalq cholg'u")

slot = db.create_slot("Karimov Aziz", "Mutaxassislik",
                      "Dushanba", "08:00", "2/4", 45)

rooms = db.get_room_availability("Dushanba", "08:00", 45)

r24 = room(rooms, "2/4")

check("2/4 band bo'ldi", r24["busy"] is True)
check("kim band qilgani ko'rsatildi", r24["teacher"] == "Karimov Aziz")
check("fan ko'rsatildi", r24["subject"] == "Mutaxassislik")
check("vaqt ko'rsatildi", r24["time"] == "08:00")
check("slot id berildi (jo'rnavozlik uchun)", r24["slot_id"] == slot)

check("qo'shni xona bo'sh qoldi", room(rooms, "2/5")["busy"] is False)
check("faqat bittasi band", sum(1 for r in rooms if r["busy"]) == 1)


# ==========================
# 4. BOSHQA KUN / BOSHQA VAQT
# ==========================

other_day = db.get_room_availability("Seshanba", "08:00", 45)
check("boshqa kuni bo'sh", room(other_day, "2/4")["busy"] is False)

later = db.get_room_availability("Dushanba", "10:00", 45)
check("boshqa vaqtda bo'sh", room(later, "2/4")["busy"] is False)


# ==========================
# 5. USTMA-UST TUSHISH (uzun dars)
# ==========================
#
# 08:00 da 45 daqiqalik dars bor. 07:30 da boshlanadigan
# 90 daqiqalik dars uning ustiga tushadi.

overlap = db.get_room_availability("Dushanba", "07:30", 90)
check("kesishgan vaqt band deb topildi", room(overlap, "2/4")["busy"] is True)

# 09:00 - tegmaydi
apart = db.get_room_availability("Dushanba", "09:00", 45)
check("kesishmagan vaqt bo'sh", room(apart, "2/4")["busy"] is False)


# ==========================
# 6. IKKI XONA BAND
# ==========================

db.create_slot("Aliyev Bobur", "Ansambl", "Dushanba", "08:00", "1/14 a", 45)

rooms = db.get_room_availability("Dushanba", "08:00", 45)

check("ikkinchi xona ham band", room(rooms, "1/14 a")["busy"] is True)
check("ikkinchisini boshqa o'qituvchi band qilgan",
      room(rooms, "1/14 a")["teacher"] == "Aliyev Bobur")
check("endi ikkitasi band", sum(1 for r in rooms if r["busy"]) == 2)
check("1/14 b hali bo'sh", room(rooms, "1/14 b")["busy"] is False)


# ==========================
# 7. TAHRIRLASHDA O'ZINI HISOBLAMASLIK
# ==========================

excluded = db.get_room_availability("Dushanba", "08:00", 45,
                                    exclude_slot_id=slot)

check("o'z darsi chiqarib tashlanganda xona bo'sh",
      room(excluded, "2/4")["busy"] is False)
check("boshqa dars baribir band", room(excluded, "1/14 a")["busy"] is True)


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
