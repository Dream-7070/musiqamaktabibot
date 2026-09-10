# -*- coding: utf-8 -*-
"""Uchta yangi imkoniyatni toza baza ustida tekshiradi."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import database as db

os.makedirs(os.path.join(os.path.dirname(os.path.abspath(__file__)), "_tmp"), exist_ok=True)
DB = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                  "_tmp", "test_all.db")

if os.path.exists(DB):
    os.remove(DB)

db.DB_NAME = DB
db.create_tables()
db.migrate_schema()

ok = []
bad = []


def check(label, cond):
    (ok if cond else bad).append(label)


# ==========================
# 1. IMTIYOZLI BADAL
# ==========================

db.add_teacher("Berdiqulov I.", "Tasviriy san'at")
db.add_teacher("Ismoilova N.", "Fortepiano")

db.add_student("Berdiqulov I.", "Ali Valiyev", "2015-01-01", "I-TV 1111111", "3", 123600)
db.add_student("Berdiqulov I.", "Zebo Karimova", "2015-02-02", "I-TV 2222222", "3",
               db.FEE_PRIVILEGED)
db.add_student("Berdiqulov I.", "Sardor Aliyev", "2015-03-03", "I-TV 3333333", "3", 0)

check("imtiyozli saqlandi",
      db.get_student_fee("Berdiqulov I.", "Zebo Karimova") == db.FEE_PRIVILEGED)

check("imtiyozli yorlig'i",
      "Imtiyozli" in db.fee_label(db.FEE_PRIVILEGED))

check("oddiy summa yorlig'i",
      db.fee_label(123600) == "123 600 so'm")

check("kiritilmagan yorlig'i",
      db.fee_label(0) == "kiritilmagan")

# eslatma: faqat badali kiritilmagan (0) o'quvchi chiqishi kerak
no_fee = db.get_students_without_fee("Berdiqulov I.")
check("eslatmada faqat kiritilmagani: " + str(no_fee),
      no_fee == ["Sardor Aliyev"])

# qarzdorlar: imtiyozli chiqmasligi kerak
unpaid = [s for s, f in db.get_unpaid_students("Berdiqulov I.", "2026-09")]
check("qarzdorlarda imtiyozli yo'q: " + str(unpaid),
      "Zebo Karimova" not in unpaid and "Ali Valiyev" in unpaid)

# hisobot
rows = db.get_monthly_debt_rows("2026-09")
zebo = [r for r in rows if r[2] == "Zebo Karimova"][0]
check("hisobotda imtiyozli belgisi va qarzi 0",
      zebo[3] == 0 and zebo[4] is True and zebo[5] is True)

from services.reports import build_debt_report
buf, fname = build_debt_report("2026-09", rows)
check("Excel hisobot yaratildi (" + str(len(buf.getvalue())) + " bayt)",
      len(buf.getvalue()) > 3000)


# ==========================
# 2. O'QITUVCHI FANLARI
# ==========================

check("umumiy fanlar bor",
      len(db.get_subjects_for_teacher("Berdiqulov I.")) == 7)

check("rang tasvir qo'shildi",
      db.add_subject("Berdiqulov I.", "Rang tasvir", "yakka"))

check("qalam tasvir qo'shildi",
      db.add_subject("Berdiqulov I.", "Qalam tasvir", "guruh"))

check("takroriy fan qo'shilmadi",
      db.add_subject("Berdiqulov I.", "Rang tasvir", "yakka") is False)

check("umumiy fan nomi bilan takror bo'lmaydi",
      db.add_subject("Berdiqulov I.", "Solfedjio", "guruh") is False)

mine = db.get_subjects_for_teacher("Berdiqulov I.")
check("o'ziga 9 ta fan ko'rinadi: " + str(len(mine)), len(mine) == 9)

check("boshqa o'qituvchiga ko'rinmaydi",
      len(db.get_subjects_for_teacher("Ismoilova N.")) == 7)

check("yakka turi to'g'ri",
      db.get_subject_type("Berdiqulov I.", "Rang tasvir") == "yakka")

check("guruh turi to'g'ri",
      db.get_subject_type("Berdiqulov I.", "Qalam tasvir") == "guruh")

check("umumiy fan turi to'g'ri",
      db.get_subject_type("Ismoilova N.", "Solfedjio") == "guruh")

rang_id = [s[0] for s in db.get_own_subjects("Berdiqulov I.") if s[1] == "Rang tasvir"][0]

check("begona o'qituvchi fanni o'chira olmaydi",
      db.delete_subject(rang_id, "Ismoilova N.") is False)


# ==========================
# 3. JO'RNAVOZLAR (bir nechta)
# ==========================

# Jo'rnavoz faqat rejada shu soat ajratilgan fanga
# biriktiriladi - rang tasvir darsiga qo'yib bo'lmaydi.

slot = db.create_slot("Ismoilova N.", "Akkompanement", "Dushanba", "14:00", "5")

db.add_student_to_slot(slot, "Ali Valiyev", "Berdiqulov I.")

check("1-jo'rnavoz qo'shildi", db.add_concertmaster(slot, "Ismoilova N."))
db.add_teacher("Yusupov K.", "Fortepiano")
check("2-jo'rnavoz qo'shildi", db.add_concertmaster(slot, "Yusupov K."))
check("takroriy jo'rnavoz qo'shilmadi",
      db.add_concertmaster(slot, "Ismoilova N.") is False)

cms = db.get_slot_concertmasters(slot)
check("ikkalasi ham darsda: " + str(cms), len(cms) == 2)

cm_slots = db.get_concertmaster_slots("Ismoilova N.")
check("jo'rnavoz o'z jadvalida ko'radi",
      len(cm_slots) == 1 and cm_slots[0][1] == "Ismoilova N."
      and cm_slots[0][2] == "Akkompanement")

db.remove_concertmaster(slot, "Ismoilova N.")
check("bittasi o'chirildi, ikkinchisi qoldi",
      db.get_slot_concertmasters(slot) == ["Yusupov K."])

sch = db.get_student_full_schedule("Berdiqulov I.", "Ali Valiyev")
check("o'quvchi jadvalida slot_id bor: " + str(sch),
      len(sch) == 1 and sch[0][5] == slot)


# ==========================
print()
for line in ok:
    print("  OK   " + line)
for line in bad:
    print("  XATO " + line)
print()
print(str(len(ok)) + " ta o'tdi, " + str(len(bad)) + " ta xato")

sys.exit(1 if bad else 0)
