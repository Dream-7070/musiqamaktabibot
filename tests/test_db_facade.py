# -*- coding: utf-8 -*-
"""
database.py fasadi to'g'ri ishlashini tekshiradi.

Kod db/ paketidagi 11 ta modulga ajratilgan, lekin tashqi kod
uchun kirish nuqtasi hamon `database` moduli. Shu sinov quyidagini
kafolatlaydi:

  1. Har bir modul ALOHIDA import qilinadi (sirkulyar import yo'q)
  2. Fasad hamma nomni chiqaradi
  3. `database.DB_NAME = ...` haqiqatan bazani almashtiradi
     (aks holda sinovlar haqiqiy school.db ga yozib yuborardi)
  4. Modullararo chaqiruvlar ishlaydi (fasad bog'lagani uchun)
"""

import importlib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

ok, bad = [], []


def check(label, cond):
    (ok if cond else bad).append(label)


MODULES = [
    "core", "teachers", "students", "documents", "parents",
    "payments", "staff", "subjects", "schedule", "audit", "miniapp",
]


# ==========================
# 1. HAR BIR MODUL ALOHIDA YUKLANADI
# ==========================
#
# Agar modullar bir-birini import qilsa, halqali bog'liqlik
# tufayli shu yerda "circular import" xatosi chiqardi.

for name in MODULES:

    try:
        importlib.import_module("db." + name)
        check("db." + name + " alohida yuklandi", True)

    except Exception as e:
        check("db." + name + " alohida yuklandi (" + str(e)[:60] + ")", False)


# ==========================
# 2. FASAD HAMMA NOMNI CHIQARADI
# ==========================

import database as db

check("fasad __all__ bor", hasattr(db, "__all__"))
check("190 dan ortiq nom eksport qilindi: " + str(len(db.__all__)),
      len(db.__all__) > 190)

# har bir moduldagi ommaviy nom fasadda ham bo'lishi kerak
for name in MODULES:

    mod = importlib.import_module("db." + name)

    import types as _types

    # sqlite3, datetime kabi import qilingan modullar hisobga olinmaydi -
    # fasad faqat funksiya va konstantalarni chiqaradi
    missing = [
        n for n in dir(mod)
        if not n.startswith("_")
        and not isinstance(getattr(mod, n), _types.ModuleType)
        and not hasattr(db, n)
    ]

    check("db." + name + " nomlari fasadda bor" +
          ("" if not missing else ": " + ", ".join(missing[:5])),
          not missing)


# eng ko'p ishlatiladigan nomlar joyida
for fn in ["connect", "create_tables", "migrate_schema", "add_student",
           "get_students", "create_slot", "get_room_availability",
           "is_cancel_text", "log_action", "get_subject_type",
           "find_teacher_conflict", "add_parent", "approve_payment"]:
    check("database." + fn + " mavjud", hasattr(db, fn))


# ==========================
# 3. DB_NAME ALMASHTIRISH ISHLAYDI
# ==========================
#
# Bu eng muhim tekshiruv: qiymat endi db/core.py da turadi,
# lekin sinovlar `db.DB_NAME = ...` deb fasadga yozadi.

from db import core, students as students_mod, schedule as schedule_mod

_tmp = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "_tmp", "test_db_facade.db"
)

os.makedirs(os.path.dirname(_tmp), exist_ok=True)

if os.path.exists(_tmp):
    os.remove(_tmp)

db.DB_NAME = _tmp

check("fasadda o'zgardi", db.DB_NAME == _tmp)
check("db.core ga uzatildi", core.DB_NAME == _tmp)
check("students moduli ham ko'radi", students_mod.DB_NAME == _tmp)
check("schedule moduli ham ko'radi", schedule_mod.DB_NAME == _tmp)

db.create_tables()
db.migrate_schema()

check("yangi bazaga yozildi", os.path.exists(_tmp))


# ==========================
# 4. MODULLARARO CHAQIRUVLAR ISHLAYDI
# ==========================
#
# Masalan db/schedule.py dagi get_subject_type() aslida
# db/subjects.py da, get_room_availability() esa db/core.py
# dagi connect() ni ishlatadi.

db.add_teacher("Fasad Sinov", "Fortepiano")

slot = db.create_slot("Fasad Sinov", "Solfedjio", "Dushanba", "08:00", "2/1", 45)

check("dars yaratildi (schedule -> core)", slot is not None)

check("fan turi aniqlandi (schedule -> subjects -> curriculum)",
      db.get_subject_type("Fasad Sinov", "Solfedjio") == "guruh")

check("xonalar ro'yxati keldi (schedule -> core -> rooms)",
      len(db.get_room_availability("Dushanba", "08:00", 45)) == 31)

db.add_student("Fasad Sinov", "Sinov Bola", "2015-01-01",
               "I-TV 9999999", "3", 57700)

check("o'quvchi qo'shildi (students -> core)",
      "Sinov Bola" in db.get_students("Fasad Sinov"))

db.log_action("Fasad Sinov", "sinov amali", "maqsad", "tafsilot")

check("jurnal yozuvi qo'shildi (audit -> core)",
      len(db.get_audit_log()) > 0)


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
