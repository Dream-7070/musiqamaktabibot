# -*- coding: utf-8 -*-
"""Jo'rnavozlik faqat rejada ko'zda tutilgan bo'limlarda bo'ladi."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import database as db

from data.curriculum import (
    NO_CONCERTMASTER_DEPARTMENTS,
    department_has_concertmaster,
    subject_has_concertmaster
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
check("teatrda o'qituvchining o'zi jo'rnavoz bo'lolmaydi",
      not department_has_concertmaster("Teatr san'ati"))

# Nazariya o'qituvchisi musiqachi - xor va jamoa ijrochiligiga
# jo'rlik qila oladi, shuning uchun ro'yxatda yo'q.

check("nazariyada esa bo'la oladi",
      department_has_concertmaster("Nazariya"))

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
# 5. QAYSI DARSGA JO'RNAVOZ QO'YILADI (fan bo'yicha)
# ==========================
#
# Reja jo'rnavoz soatini fan bo'yicha ajratadi:
#   4.4  fortepiano   - akkompanement, jamoa ijrochiligi,
#                       tanlangan fan, yig'ma
#   5.15 xoreografiya - mutaxassislik, raqs fanlari, tanlangan fan
#   6.9  aktyorlik    - sahna harakati, vokal, ritmika va raqs
#   7.4  barcha       - tanlangan fan

CASES = [
    ("Xalq cholg'u", "Mutaxassislik", True),
    ("Xoreografiya", "Mutaxassislik (xalq raqsi ijrochiligi)", True),
    ("Xoreografiya", "Zamonaviy raqs", True),
    ("Fortepiano", "Akkompanement", True),
    ("Fortepiano", "Jamoa ijrochiligi (xor, vokal ansambli)", True),
    ("Amaliy san'at", "Tanlangan fan", True),
    ("Teatr san'ati", "Sahna harakati", True),

    ("Fortepiano", "Mutaxassislik", False),
    ("Fortepiano", "Solfedjio", False),
    ("Fortepiano", "Notani varaqdan o'qish", False),
    ("Tasviriy san'at", "Rang tasvir", False),
    ("Amaliy san'at", "Mutaxassislik (liboslar dizayni)", False),
    ("Xoreografiya", "Raqs san'ati tarixi", False),
]

wrong = [
    (dept, subj) for dept, subj, expected in CASES
    if subject_has_concertmaster(dept, subj) is not expected
]

check("fan qoidasi rejaga mos: " + str(wrong), not wrong)

# tanlangan fan har qanday yo'nalishda - 7.4-band

check("tanlangan fan hamma yerda",
      all(subject_has_concertmaster(d, "Tanlangan fan")
          for d in ["Fortepiano", "Tasviriy san'at", "Teatr san'ati"]))


# ==========================
# 6. BAZA HAM SHU QOIDANI QO'LLAYDI
# ==========================

db.add_teacher("Rassomova Roza", "Tasviriy san'at")

rang = db.create_slot("Rassomova Roza", "Rang tasvir", "Dushanba", "10:00", "5")
tanl = db.create_slot("Rassomova Roza", "Tanlangan fan", "Seshanba", "10:00", "5")

allowed, subject = db.slot_allows_concertmaster(rang)

check("rang tasvirga jo'rnavoz qo'yib bo'lmaydi", not allowed)
check("sababi uchun fan nomi qaytdi", subject == "Rang tasvir")

check("baza ham rad etdi",
      db.add_concertmaster(rang, "Pianinov Pulat") is False)

check("yozuv ham qo'shilmadi",
      db.get_slot_concertmasters(rang) == [])

check("tanlangan fanga esa mumkin",
      db.slot_allows_concertmaster(tanl)[0])

check("va biriktirildi",
      db.add_concertmaster(tanl, "Pianinov Pulat"))


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
