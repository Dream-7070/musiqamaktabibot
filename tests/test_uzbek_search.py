# -*- coding: utf-8 -*-
# ==========================
# tests/test_uzbek_search.py
# ==========================
#
# O'zbekcha yozuv farqlari bilan qidiruv.
#
# Haqiqiy voqea: bazada "Maxmudov Bexruz Ma'sudjon ugli" bor
# edi, xodim "behruz" deb qidirdi va HECH NARSA topilmadi.
# ==========================


import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import database as db

from db.uzbek import matches, normalize


TMP = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_tmp")

os.makedirs(TMP, exist_ok=True)

DB_FILE = os.path.join(TMP, "uzbek_search.db")

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


# ==========================
# NORMALLASHTIRISH
# ==========================

print("normalize / matches:")

check("x = h (Bexruz ~ Behruz)", matches("behruz", "Maxmudov Bexruz"))
check("teskari yo'nalish ham", matches("Maxmudov", "Mahmudov Behruz"))
check("o' = u (o'g'li ~ ugli)", matches("o'g'li", "Ma'sudjon ugli"))
check("g' = g", matches("gulnora", "G'ulnora"))
check("apostrof turlari", normalize("o\u2018qish") == normalize("o'qish"))
check("bo'sh so'rov mos kelmaydi", not matches("", "har qanday"))
check("begona so'z mos kelmaydi", not matches("solfedjio", "Mutaxassislik"))
check("ch buzilmaydi", normalize("cholg'u") == "cholgu")


# ==========================
# HAQIQIY QIDIRUV
# ==========================

print("search_students:")

db.add_student("Tojiboyeva Kamola", "Maxmudov Bexruz Ma'sudjon ugli",
               "2015-01-01", "AA1234567", "3")

topildi = db.search_students("behruz")

check("'behruz' -> 'Bexruz' topildi", len(topildi) == 1)

check("'maxmudov' topadi", len(db.search_students("maxmudov")) == 1)

check("'mahmudov' ham topadi", len(db.search_students("mahmudov")) == 1)

check("bo'sh so'rov bo'sh natija", db.search_students("") == [])

check("begona nom topilmaydi", db.search_students("Alisher") == [])


print("search_teachers_by_name:")

db.seed_teachers([("Tojiboyeva Kamola", "Xalq cholg'u")])

check("o'qituvchi topildi", len(db.search_teachers_by_name("tojiboyeva")) == 1)

check("2 harf - juda qisqa", db.search_teachers_by_name("to") == [])


print()

if xatolar:
    print("XATOLAR: " + str(len(xatolar)))
    sys.exit(1)

print("test_uzbek_search: hammasi joyida")
