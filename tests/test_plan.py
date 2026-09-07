# -*- coding: utf-8 -*-
"""O'quv rejasi bilan bog'lanish: fanlar, sinf, davomiylik, bo'linish."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import database as db
from data.curriculum import (
    CURRICULUM, DEPARTMENT_SPECIALTIES, MIN_SPLITTABLE_HOURS,
    department_subjects, department_years, planned_hours, weekly_norm
)

os.makedirs(os.path.join(os.path.dirname(os.path.abspath(__file__)), "_tmp"), exist_ok=True)
DB = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                  "_tmp", "test_plan.db")

if os.path.exists(DB):
    os.remove(DB)

db.DB_NAME = DB
db.create_tables()
db.migrate_schema()

ok, bad = [], []


def check(label, cond):
    (ok if cond else bad).append(label)


# ==========================
# MA'LUMOT BUTUNLIGI
# ==========================

check("35 ta mutaxassislik", len(CURRICULUM) == 35)
check("14 ta bo'lim bog'landi", len(DEPARTMENT_SPECIALTIES) == 14)

linked = {s for v in DEPARTMENT_SPECIALTIES.values() for s in v}
check("bog'lanmagan mutaxassislik yo'q: " + str(sorted(set(CURRICULUM) - linked)),
      set(CURRICULUM) == linked)

names = {s for d in CURRICULUM.values() for s in d["subjects"]}
check("fan nomlari toza (qavs yopilgan)",
      all(n.count("(") == n.count(")") for n in names))
check("fan nomi kichik harf bilan boshlanmaydi",
      all(n[0].isupper() for n in names))


# ==========================
# TA'LIM MUDDATI
# ==========================

check("Fortepiano 7 yil", department_years("Fortepiano") == 7)
check("Tasviriy san'at 5 yil", department_years("Tasviriy san'at") == 5)
check("Xoreografiya 5 yil", department_years("Xoreografiya") == 5)
check("Xoreografiyada 3 ta yo'nalish",
      len(DEPARTMENT_SPECIALTIES["Xoreografiya"]) == 3)


# ==========================
# BO'LIM FANLARI
# ==========================

fp = [n for n, _ in department_subjects("Fortepiano")]
check("Fortepianoda 10 ta fan: " + str(len(fp)), len(fp) == 10)
check("Fortepianoda Mutaxassislik bor", "Mutaxassislik" in fp)

ts = [n for n, _ in department_subjects("Tasviriy san'at")]
check("Tasviriyda solfedjio yo'q", "Solfedjio" not in ts)
check("Tasviriyda Chizmatasvir bor", "Chizmatasvir" in ts)


# ==========================
# REJADAGI SOAT
# ==========================

check("Mutaxassislik 3-sinf = 2 soat",
      planned_hours("Fortepiano", "Mutaxassislik", "3") == [2])

check("Mutaxassislik 7-sinf = 3 soat",
      planned_hours("Fortepiano", "Mutaxassislik", "7") == [3])

check("Solfedjio 1-sinf = 1,5 soat",
      planned_hours("Fortepiano", "Solfedjio", "1") == [1.5])

check("O'zbek raqs 4-sinf = 4 soat",
      planned_hours("Xoreografiya", "O\u2018zbek raqs", "4") == [4])

check("Ansambl 1-sinfda rejada yo'q",
      planned_hours("Fortepiano", "Ansambl", "1") == [])

check("Fortepiano 3-sinf normasi 9,5 soat",
      weekly_norm("Fortepiano ijrochiligi", "3") == 9.5)


# ==========================
# BO'LINISH QOIDASI
# ==========================

check("chegara 2 soat", MIN_SPLITTABLE_HOURS == 2)

check("1,5 soat bo'linmaydi", 1.5 < MIN_SPLITTABLE_HOURS)
check("0,5 soat bo'linmaydi", 0.5 < MIN_SPLITTABLE_HOURS)
check("2 soat bo'linadi", 2 >= MIN_SPLITTABLE_HOURS)
check("4 soat bo'linadi", 4 >= MIN_SPLITTABLE_HOURS)


# ==========================
# QO'YILGAN SOATNI HISOBLASH
# ==========================

db.add_teacher("Karimov A.", "Fortepiano")

check("boshida 0", db.scheduled_hours("Karimov A.", "Mutaxassislik", "3") == 0)

db.create_slot("Karimov A.", "Mutaxassislik", "Dushanba", "08:00", "12", 45, "3")

check("1 soat qo'yildi",
      db.scheduled_hours("Karimov A.", "Mutaxassislik", "3") == 1)

db.create_slot("Karimov A.", "Mutaxassislik", "Chorshanba", "08:00", "12", 45, "3")

check("2 soat bo'ldi - reja to'ldi",
      db.scheduled_hours("Karimov A.", "Mutaxassislik", "3") == 2)

check("boshqa sinf alohida hisoblanadi",
      db.scheduled_hours("Karimov A.", "Mutaxassislik", "4") == 0)

db.create_slot("Karimov A.", "Solfedjio", "Juma", "10:30", "7", 70, "1")

check("1,5 soatlik dars 1,5 deb hisoblanadi",
      db.scheduled_hours("Karimov A.", "Solfedjio", "1") == 1.5)

check("90 daqiqalik bitta dars ham 2 soat",
      db.hours_to_minutes(2) == 90)

check("sinf slotda saqlandi", db.get_slot_class(1) == "3")


# ==========================
print()
for line in ok:
    print("  OK   " + line)
for line in bad:
    print("  XATO " + line)
print()
print(str(len(ok)) + " ta o'tdi, " + str(len(bad)) + " ta xato")

sys.exit(1 if bad else 0)
