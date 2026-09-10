# -*- coding: utf-8 -*-
# ==========================
# tests/test_specialties.py
# ==========================
#
# O'qituvchi yo'nalishlari va fan ro'yxatining qisqarishi.
#
# Sabab: "Amaliy san'at"da 13 ta yo'nalish bor, shuning uchun
# o'sha bo'lim o'qituvchisiga 34 ta fan chiqardi - ko'pchiligi
# boshqa kasbniki. Aynan shundan noto'g'ri fan tanlangan.
# ==========================


import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import database as db

from data.curriculum import specialties_for, specialty_subjects


TMP = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_tmp")

os.makedirs(TMP, exist_ok=True)

DB_FILE = os.path.join(TMP, "specialties.db")

if os.path.exists(DB_FILE):
    os.remove(DB_FILE)

db.DB_NAME = DB_FILE

db.create_tables()
db.migrate_schema()


xatolar = []


def check(nom, shart):

    if shart:
        print("  OK   " + nom)

    else:
        print("  XATO " + nom)
        xatolar.append(nom)


AMALIY = "Amaliy san'at"

USTA = "Test Usta"

db.seed_teachers([(USTA, AMALIY)])


# ==========================
# BOSHLANG'ICH HOLAT
# ==========================

print("belgilanmagan holat:")

check("yo'nalish bo'sh", db.get_teacher_specialties(USTA) == [])

check("yorliq 'belgilanmagan'", db.teacher_specialty_label(USTA) == "belgilanmagan")

butun_bolim = db.plan_subject_names(USTA)

check("butun bo'lim fanlari ko'rinadi (10 dan ko'p)", len(butun_bolim) > 10)


# ==========================
# BITTA YO'NALISH
# ==========================

print("bitta yo'nalish:")

db.set_teacher_specialties(USTA, ["Badiiy kashtachilik"])

check("saqlandi", db.get_teacher_specialties(USTA) == ["Badiiy kashtachilik"])

bitta = db.plan_subject_names(USTA)

kutilgan = {n for n, _ in specialty_subjects("Badiiy kashtachilik")}

check("ro'yxat qisqardi", len(bitta) < len(butun_bolim))

check("aynan o'sha yo'nalish fanlari", set(bitta) == kutilgan)

check("boshqa kasb fani yo'q",
      "Mutaxassislik (badiiy zargarlik)" not in bitta)


# ==========================
# IKKITA YO'NALISH
# ==========================

print("ikkita yo'nalish:")

yoqildi = db.toggle_teacher_specialty(USTA, "Liboslar dizayni")

check("toggle True qaytardi", yoqildi is True)

check("ikkitasi ham bor",
      db.get_teacher_specialties(USTA) == ["Badiiy kashtachilik", "Liboslar dizayni"])

ikkita = db.plan_subject_names(USTA)

check("fanlar yig'indisi", len(ikkita) > len(bitta))

check("kashtachilik fani hamon bor",
      "Mutaxassislik (badiiy kashtachilik)" in ikkita)

check("libos fani ham qo'shildi",
      "Mutaxassislik (liboslar dizayni)" in ikkita)

ochirildi = db.toggle_teacher_specialty(USTA, "Liboslar dizayni")

check("toggle False qaytardi", ochirildi is False)

check("bittaga qaytdi", db.get_teacher_specialties(USTA) == ["Badiiy kashtachilik"])


# ==========================
# O'ZI QO'SHILGAN FAN
# ==========================
#
# Admin qo'shgan, rejada yo'q fan ham ro'yxatda qolishi kerak -
# aks holda o'sha fandagi darslar "noto'g'ri fan" bo'lib qolardi.

print("rejadan tashqari fan:")

db.add_subject(USTA, "Maxsus to'garak", "guruh")

check("admin qo'shgan fan ro'yxatda",
      "Maxsus to'garak" in db.plan_subject_names(USTA))


# ==========================
# CHEKKA HOLATLAR
# ==========================

print("chekka holatlar:")

db.set_teacher_specialties(USTA, ["Bunday yo'nalish yo'q"])

check("eskirgan yo'nalish - butun bo'limga qaytadi",
      len(db.plan_subject_names(USTA)) > 10)

db.set_teacher_specialties(USTA, [])

check("bo'shatish ishlaydi", db.get_teacher_specialties(USTA) == [])

check("takror qo'shilmaydi (unique)",
      db.set_teacher_specialties(USTA, ["Grafika", "Grafika"]) == ["Grafika"])

check("bo'limda bitta yo'nalish bo'lsa tanlash shart emas",
      len(specialties_for("Fortepiano")) == 1)


print()

if xatolar:
    print("XATOLAR: " + str(len(xatolar)))
    sys.exit(1)

print("test_specialties: hammasi joyida")
