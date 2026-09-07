# -*- coding: utf-8 -*-
"""Bitta bola ikki mutaxassislikda + bo'lakni davom ettirish."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import database as db

os.makedirs(os.path.join(os.path.dirname(os.path.abspath(__file__)), "_tmp"), exist_ok=True)
DB = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                  "_tmp", "test_multi.db")

if os.path.exists(DB):
    os.remove(DB)

db.DB_NAME = DB
db.create_tables()
db.migrate_schema()

ok, bad = [], []


def check(label, cond):
    (ok if cond else bad).append(label)


db.add_teacher("Karimov A.", "Fortepiano")
db.add_teacher("Aliyev B.", "Xalq cholg'u")

ITV = "I-TV 0860700"

db.add_student("Karimov A.", "Ali Valiyev", "2015-01-01", ITV, "3", 123600)


# ==========================
# 1. ITV TEKSHIRUVI
# ==========================

found = db.find_metrika_duplicate(ITV, teacher="Karimov A.")
check("shu o'qituvchida - to'sadi", found and found[0] == "same_teacher")

found = db.find_metrika_duplicate(ITV, teacher="Aliyev B.")
check("boshqa o'qituvchida - ruxsat, ma'lumot beradi",
      found and found[0] == "other_teacher" and found[2] == "Ali Valiyev")

check("yangi raqam toza",
      db.find_metrika_duplicate("I-TV 999", teacher="Aliyev B.") is None)

check("o'zini tahrirlaganda to'smaydi",
      db.find_metrika_duplicate(ITV, teacher="Karimov A.",
                                exclude_teacher="Karimov A.",
                                exclude_student="Ali Valiyev") is None)


# ==========================
# 2. IKKINCHI MUTAXASSISLIK
# ==========================

# badali boshqacha, mustaqil
db.add_student("Aliyev B.", "Ali Valiyev", "2015-01-01", ITV, "3", 82400)

check("Fortepianoda badal 123600",
      db.get_student_fee("Karimov A.", "Ali Valiyev") == 123600)

check("Xalq cholg'usida badal 82400 - mustaqil",
      db.get_student_fee("Aliyev B.", "Ali Valiyev") == 82400)

enrollments = db.get_student_enrollments("Karimov A.", "Ali Valiyev")

check("ikkala yozuvi topildi: " + str(len(enrollments)),
      len(enrollments) == 2)

check("ikkinchi tarafdan ham bir xil",
      set(db.get_student_enrollments("Aliyev B.", "Ali Valiyev"))
      == set(enrollments))

check("guvohnomasiz o'quvchi - faqat o'zi",
      len(db.get_student_enrollments("Karimov A.", "Yo'q bola")) == 1)


# ==========================
# 3. TO'QNASHUV - BOLA BITTA
# ==========================

slot_fp = db.create_slot("Karimov A.", "Mutaxassislik", "Dushanba",
                         "08:00", "12", 90, "3")

db.add_student_to_slot(slot_fp, "Ali Valiyev", "Karimov A.")

# Aliyev o'sha vaqtga doira darsiga yozmoqchi - bola band
busy = db.find_student_conflict(
    "Ali Valiyev", "Aliyev B.", "Dushanba", "08:50", 45
)

check("fortepiano vaqtida doiraga yozib bo'lmaydi: "
      + (busy[2] if busy else "yo'q"),
      busy is not None)

check("dars tugagach bo'sh",
      db.find_student_conflict("Ali Valiyev", "Aliyev B.",
                               "Dushanba", "09:40", 45) is None)

check("boshqa kun bo'sh",
      db.find_student_conflict("Ali Valiyev", "Aliyev B.",
                               "Seshanba", "08:00", 45) is None)

# boshqa bola ta'sirlanmaydi
db.add_student("Karimov A.", "Zebo Karimova", "2015-02-02", "I-TV 222", "2", 123600)

check("boshqa bola band emas",
      db.find_student_conflict("Zebo Karimova", "Karimov A.",
                               "Dushanba", "08:00", 45) is None)


# ==========================
# 4. OTA-ONA IKKALASIGA ULANADI
# ==========================

matches = db.find_students_by_metrika(ITV)

check("ITV bo'yicha 2 yozuv topildi", len(matches) == 2)

db.add_parent(999, "Valiyev Otabek", "+998901234567")
parent = db.get_parent(999)

for teacher, student in matches:
    db.link_parent_student(parent[0], teacher, student)

children = db.get_parent_students(parent[0])

check("ota-ona ikkala yozuvni ko'radi: " + str(len(children)),
      len(children) == 2)


# ==========================
# 5. EXCEL
# ==========================

from services.reports import build_students_report

rows = db.get_students_report_rows()

buffer, name = build_students_report(rows)

import io as _io
import openpyxl

ws = openpyxl.load_workbook(_io.BytesIO(buffer.getvalue())).active

values = [
    [str(c) if c is not None else "" for c in row]
    for row in ws.iter_rows(values_only=True)
]

ali = [r for r in values if r[0] == "Ali Valiyev"]

check("Excelda ikki qator", len(ali) == 2)

check("ikkalasida ham izoh bor",
      all("2 bo'limda" in r[6] for r in ali))

check("badallar har xil ko'rinadi",
      {r[5] for r in ali} == {"123600", "82400"})

summary = [r for r in values if r[0] == "JAMI"]

check("xulosada bola soni ajratilgan: " + (summary[0][6] if summary else "?"),
      summary and "3 ta yozuv, 2 ta bola" in summary[0][6])


# ==========================
# 6. BO'LAKNI DAVOM ETTIRISH
# ==========================

from data.curriculum import planned_hours

norm = planned_hours("Fortepiano", "Mutaxassislik", "3")

check("reja 2 soat", norm == [2])

done = db.scheduled_hours("Karimov A.", "Mutaxassislik", "3")

check("90 daqiqalik dars = 2 soat, reja to'ldi", done == 2)

# endi 45 daqiqalik qilib qo'yamiz - 1 soat qolishi kerak
db.delete_slot(slot_fp)

part = db.create_slot("Karimov A.", "Mutaxassislik", "Dushanba",
                      "08:00", "12", 45, "3")

remaining = norm[0] - db.scheduled_hours("Karimov A.", "Mutaxassislik", "3")

check("1 soat qo'yilgach 1 soat qoldi", remaining == 1)

db.create_slot("Karimov A.", "Mutaxassislik", "Chorshanba",
               "08:00", "12", 45, "3")

remaining = norm[0] - db.scheduled_hours("Karimov A.", "Mutaxassislik", "3")

check("ikkinchi bo'lakdan keyin 0 qoldi", remaining == 0)


# ==========================
print()
for line in ok:
    print("  OK   " + line)
for line in bad:
    print("  XATO " + line)
print()
print(str(len(ok)) + " ta o'tdi, " + str(len(bad)) + " ta xato")

sys.exit(1 if bad else 0)
