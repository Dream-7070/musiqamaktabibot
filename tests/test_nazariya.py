# -*- coding: utf-8 -*-
"""Nazariya bo'limi."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import database as db
from data.curriculum import (
    THEORY_DEPARTMENT, THEORY_SUBJECTS,
    department_subjects, department_years, planned_hours
)
from data.teachers import departments as SEED_DEPARTMENTS

os.makedirs(os.path.join(os.path.dirname(os.path.abspath(__file__)), "_tmp"), exist_ok=True)
DB = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                  "_tmp", "test_naz.db")

if os.path.exists(DB):
    os.remove(DB)

db.DB_NAME = DB
db.create_tables()
db.migrate_schema()

ok, bad = [], []


def check(label, cond):
    (ok if cond else bad).append(label)


# ==========================
# BO'LIM MAVJUDLIGI
# ==========================

check("Nazariya seed ro'yxatida", "Nazariya" in SEED_DEPARTMENTS)
check("THEORY_DEPARTMENT to'g'ri", THEORY_DEPARTMENT == "Nazariya")

# baza bo'sh - lekin bo'lim baribir ko'rinishi kerak
check("o'qituvchisiz ham ro'yxatda ko'rinadi",
      "Nazariya" in db.get_departments())

db.add_teacher("Berdiqulov I.", "Nazariya")

check("o'qituvchi qo'shilgach ham bitta marta",
      db.get_departments().count("Nazariya") == 1)


# ==========================
# FANLAR
# ==========================

subjects = [n for n, _ in department_subjects("Nazariya")]

check("nazariy fanlar: " + str(len(subjects)), len(subjects) == 10)

check("Solfedjio bor", "Solfedjio" in subjects)
check("Musiqa adabiyoti bor", "Xorij musiqa adabiyoti" in subjects)
check("Maqom alifbosi bor", "Maqom alifbosi" in subjects)

check("mutaxassislik yo'q", "Mutaxassislik" not in subjects)
check("chizmatasvir yo'q", "Chizmatasvir" not in subjects)
check("san'at tarixi yo'q (o'z bo'limida)",
      "Tasviriy va amaliy san'at tarixi" not in subjects
      and "Raqs san\u2019ati tarixi" not in subjects)

check("hammasi THEORY_SUBJECTS ichida",
      all(s in THEORY_SUBJECTS for s in subjects))


# ==========================
# SOAT
# ==========================

check("Nazariya 7 yilgacha (barcha yo'nalish)",
      department_years("Nazariya") == 7)

check("Solfedjio 1-sinf aniq: 1,5",
      planned_hours("Nazariya", "Solfedjio", "1") == [1.5])

check("Solfedjio 5-sinf ikki xil: 1,5 va 2",
      planned_hours("Nazariya", "Solfedjio", "5") == [1.5, 2])

check("boshqa bo'limga ta'sir qilmadi",
      len(department_subjects("Fortepiano")) == 10)


# ==========================
# HUQUQLAR
# ==========================

db.set_teacher_type("Berdiqulov I.", "umumiy")

perms = db.get_teacher_permissions("Berdiqulov I.")

check("o'quvchi qo'sha olmaydi", perms["can_add_students"] is False)
check("jadval tuza oladi", perms["can_manage_schedule"] is True)
check("jo'rnavozlik qila olmaydi", perms["can_be_concertmaster"] is False)


# ==========================
# DARS QO'YISH
# ==========================

slot = db.create_slot("Berdiqulov I.", "Solfedjio", "Seshanba",
                      "10:30", "7", db.hours_to_minutes(1.5), "1")

check("1,5 soatlik dars 70 daqiqa",
      db.get_slot_duration(slot) == 70)

check("qo'yilgan soat 1,5",
      db.scheduled_hours("Berdiqulov I.", "Solfedjio", "1") == 1.5)

# boshqa o'qituvchining o'quvchisini qo'sha oladi
db.add_teacher("Karimov A.", "Fortepiano")
db.add_student("Karimov A.", "Ali Valiyev", "2015-01-01", "I-TV 1", "1", 123600)

check("boshqa o'qituvchining o'quvchisi qo'shildi",
      db.add_student_to_slot(slot, "Ali Valiyev", "Karimov A."))

check("darsda o'quvchi bor", len(db.get_slot_students(slot)) == 1)


# ==========================
print()
for line in ok:
    print("  OK   " + line)
for line in bad:
    print("  XATO " + line)
print()
print(str(len(ok)) + " ta o'tdi, " + str(len(bad)) + " ta xato")

sys.exit(1 if bad else 0)
