# -*- coding: utf-8 -*-
"""
Fan turi (yakka/guruh) reja bo'yicha to'g'ri aniqlanishi va
guruh hajmi nazorati.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import database as db

os.makedirs(os.path.join(os.path.dirname(os.path.abspath(__file__)), "_tmp"), exist_ok=True)
DB = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                  "_tmp", "test_curriculum_types.db")

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
# 1. "ANSAMBL" ENDI UMUMIY EMAS
# ==========================

common = {row[1] for row in db.get_subjects_for_teacher("Hech kim")}

check("Ansambl umumiy ro'yxatda yo'q", "Ansambl" not in common)
check("Mutaxassislik hali ham umumiy", "Mutaxassislik" in common)
check("7 ta umumiy fan qoldi", len(common) == 7)


# ==========================
# 2. REJA BO'YICHA TUR - CHOLG'U YO'NALISHI
# ==========================

db.add_teacher("Karimov Aziz", "Fortepiano")

check("Fortepianoda Mutaxassislik - yakka",
      db.get_subject_type("Karimov Aziz", "Mutaxassislik") == "yakka")

check("Fortepianoda Ansambl - yakka (reja shunday deydi)",
      db.get_subject_type("Karimov Aziz", "Ansambl") == "yakka")

check("Fortepianoda Solfedjio - guruh",
      db.get_subject_type("Karimov Aziz", "Solfedjio") == "guruh")

check("Fortepianoda Jamoa ijrochiligi - guruh",
      db.get_subject_type("Karimov Aziz", "Jamoa ijrochiligi") == "guruh")


# ==========================
# 3. REJA JIM TURGAN BO'LIM - STANDART YAKKA
# ==========================

db.add_teacher("Yo'ldasheva Durdona", "Amaliy san'at")

check(
    "Amaliy san'atda nomsiz fan - standart yakka",
    db.get_subject_type(
        "Yo'ldasheva Durdona", "Mutaxassislik (liboslar dizayni)"
    ) == "yakka"
)


# ==========================
# 4. ADMIN BITTA O'QITUVCHI UCHUN TUZATADI
# ==========================
#
# Durdonaning holati aynan shu - reja jim, lekin amalda guruh.

changed = db.admin_set_subject_type(
    "Yo'ldasheva Durdona", "Mutaxassislik (liboslar dizayni)", "guruh"
)

check("admin tuzatishi qabul qilindi", changed is True)

check(
    "endi guruh deb ko'rinadi",
    db.get_subject_type(
        "Yo'ldasheva Durdona", "Mutaxassislik (liboslar dizayni)"
    ) == "guruh"
)

check(
    "boshqa o'qituvchiga tegmaydi",
    db.get_subject_type("Karimov Aziz", "Mutaxassislik") == "yakka"
)

# qayta chaqirilsa - yangilaydi, ikkilanmaydi
db.admin_set_subject_type(
    "Yo'ldasheva Durdona", "Mutaxassislik (liboslar dizayni)", "yakka"
)

rows = [
    r for r in db.get_own_subjects("Yo'ldasheva Durdona")
    if r[1] == "Mutaxassislik (liboslar dizayni)"
]

check("bitta yozuv, ikkitaga aylanmadi", len(rows) == 1)
check("qayta chaqirilganda yangilandi", rows[0][2] == "yakka")


# ==========================
# 5. GURUH HAJMI - MEʼYORDAN ORTIQ
# ==========================

slot_id = db.create_slot(
    "Karimov Aziz", "Solfedjio", "Dushanba", "10:00", "2/1", 45
)

for i in range(11):
    db.add_student_to_slot(slot_id, "Bola" + str(i), "Karimov Aziz")

status = db.get_slot_group_status(slot_id)

check("11 nafarda hali meʼyor ichida", status["status"] == "ok")

db.add_student_to_slot(slot_id, "Bola11", "Karimov Aziz")

status = db.get_slot_group_status(slot_id)

check("12 nafarda meʼyordan ortiq", status["status"] == "ortiq")
check("son to'g'ri hisoblandi", status["count"] == 12)
check("meʼyor 6-11 deb qaytdi", (status["min"], status["max"]) == (6, 11))


# ==========================
# 6. GURUH HAJMI - MEʼYORDAN KAM
# ==========================

small_slot = db.create_slot(
    "Karimov Aziz", "Solfedjio", "Seshanba", "10:00", "2/2", 45
)

db.add_student_to_slot(small_slot, "Yolg'iz1", "Karimov Aziz")
db.add_student_to_slot(small_slot, "Yolg'iz2", "Karimov Aziz")

status = db.get_slot_group_status(small_slot)

check("2 nafarda meʼyordan kam", status["status"] == "kam")

understaffed = db.get_understaffed_groups()

check(
    "kunlik ro'yxatda ko'rindi",
    any(g["subject"] == "Solfedjio" and g["day"] == "Seshanba"
        for g in understaffed)
)

check(
    "ortiqcha guruh bu ro'yxatda yo'q (u alohida - real vaqtda)",
    not any(g["day"] == "Dushanba" for g in understaffed)
)


# ==========================
# 7. YAKKA DARSDA MEʼYOR TEKSHIRILMAYDI
# ==========================

yakka_slot = db.create_slot(
    "Karimov Aziz", "Mutaxassislik", "Chorshanba", "10:00", "2/3", 45
)

db.add_student_to_slot(yakka_slot, "Bitta bola", "Karimov Aziz")

check(
    "yakka darsda status None",
    db.get_slot_group_status(yakka_slot) is None
)


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
