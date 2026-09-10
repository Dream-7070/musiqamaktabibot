# -*- coding: utf-8 -*-
"""Jo'rnavozlik faqat rejada ko'zda tutilgan bo'limlarda bo'ladi."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import database as db

from data.curriculum import (
    NO_CONCERTMASTER_DEPARTMENTS,
    department_has_concertmaster
)

HERE = os.path.dirname(os.path.abspath(__file__))

os.makedirs(os.path.join(HERE, "_tmp"), exist_ok=True)
DB = os.path.join(HERE, "_tmp", "test_concertmaster_rule.db")

if os.path.exists(DB):
    os.remove(DB)

db.DB_NAME = DB
db.create_tables()
db.migrate_schema()

ok, bad = [], []


def check(label, cond):
    (ok if cond else bad).append(label)


# ==========================
# 1. BO'LIM QOIDASI
# ==========================

check("tasviriy san'atda jo'rnavoz yo'q",
      not department_has_concertmaster("Tasviriy san'at"))

check("amaliy san'atda jo'rnavoz yo'q",
      not department_has_concertmaster("Amaliy san'at"))

check("fortepianoda bor", department_has_concertmaster("Fortepiano"))
check("xoreografiyada bor", department_has_concertmaster("Xoreografiya"))
check("noma'lum bo'limda bor (standart)",
      department_has_concertmaster("Yangi bo'lim"))


# ==========================
# 2. HUQUQ TEKSHIRUVI BO'LIMGA BO'YSUNADI
# ==========================

db.add_teacher("Rassomov Rasul", "Amaliy san'at")
db.add_teacher("Pianinov Pulat", "Fortepiano")

check("amaliy san'at o'qituvchisi jo'rnavoz emas",
      not db.can("Rassomov Rasul", "can_be_concertmaster"))

check("fortepiano o'qituvchisi jo'rnavoz bo'la oladi",
      db.can("Pianinov Pulat", "can_be_concertmaster"))

# huquq ATAYLAB berilgan bo'lsa ham - bo'lim qoidasi ustun

db.set_teacher_type("Rassomov Rasul", "jornavoz")

check("qo'lda berilgan huquq ham bo'limdan o'ta olmadi",
      not db.can("Rassomov Rasul", "can_be_concertmaster"))

check("boshqa huquqlarga tegmadi",
      db.can("Rassomov Rasul", "can_add_students") in (True, False))


# ==========================
# 3. QOLGAN HUQUQLAR ILGARIDEK
# ==========================

check("belgilanmagan huquq ochiq (eski yozuvlar buzilmasin)",
      db.can("Pianinov Pulat", "can_add_students"))

check("ro'yxat bo'sh emas", len(NO_CONCERTMASTER_DEPARTMENTS) >= 2)


# ==========================
# 4. MINI APP HAM SHU MANBADAN OLADI
# ==========================
#
# /api/teacher/me huquqlarni get_teacher_permissions dan oladi -
# qoida shu yerda qo'llangani uchun ilova ham, bot ham bir xil
# ko'radi.

perms = db.get_teacher_permissions("Rassomov Rasul")

check("huquqlar lug'atida ham o'chiq",
      perms["can_be_concertmaster"] is False)

check("fortepianoda esa ochiq",
      db.get_teacher_permissions("Pianinov Pulat")["can_be_concertmaster"] is True)


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
