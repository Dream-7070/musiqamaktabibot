# -*- coding: utf-8 -*-
"""Fan tahrirlash va jo'rnavozning o'zi biriktirilishi."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import database as db

os.makedirs(os.path.join(os.path.dirname(os.path.abspath(__file__)), "_tmp"), exist_ok=True)
DB = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                  "_tmp", "test_edit.db")

if os.path.exists(DB):
    os.remove(DB)

db.DB_NAME = DB
db.create_tables()
db.migrate_schema()

ok, bad = [], []


def check(label, cond):
    (ok if cond else bad).append(label)


db.add_teacher("Berdiqulov I.", "Tasviriy san'at")
db.add_teacher("Ismoilova N.", "Fortepiano")

db.add_subject("Berdiqulov I.", "Rang tasvir", "yakka")
db.add_subject("Berdiqulov I.", "Qalam tasvir", "guruh")

rang = [s for s in db.get_own_subjects("Berdiqulov I.") if s[1] == "Rang tasvir"][0][0]
qalam = [s for s in db.get_own_subjects("Berdiqulov I.") if s[1] == "Qalam tasvir"][0][0]


# ==========================
# FAN TAHRIRLASH
# ==========================

slot_a = db.create_slot("Berdiqulov I.", "Rang tasvir", "Dushanba", "14:00", "5")
slot_b = db.create_slot("Berdiqulov I.", "Rang tasvir", "Chorshanba", "16:00", "5")
slot_c = db.create_slot("Berdiqulov I.", "Qalam tasvir", "Juma", "10:00", "5")

check("fan bo'yicha dars soni: 2",
      db.count_slots_using_subject("Berdiqulov I.", "Rang tasvir") == 2)

res, info = db.rename_subject(rang, "Berdiqulov I.", "Akvarel")
check("nom o'zgardi (eskisi " + str(info) + ")", res and info == "Rang tasvir")

check("fan ro'yxatida yangi nom",
      "Akvarel" in [s[1] for s in db.get_own_subjects("Berdiqulov I.")])

check("dars jadvali ham yangilandi",
      db.get_slot(slot_a)[2] == "Akvarel" and db.get_slot(slot_b)[2] == "Akvarel")

check("boshqa fandagi dars tegilmadi",
      db.get_slot(slot_c)[2] == "Qalam tasvir")

check("nom orqali tur topilyapti",
      db.get_subject_type("Berdiqulov I.", "Akvarel") == "yakka")

res, info = db.rename_subject(qalam, "Berdiqulov I.", "Akvarel")
check("takroriy nomga o'zgartirib bo'lmaydi: " + str(info),
      res is False and "allaqachon" in info)

res, info = db.rename_subject(qalam, "Berdiqulov I.", "Solfedjio")
check("umumiy fan nomi bilan to'qnashmaydi", res is False)

res, info = db.rename_subject(qalam, "Berdiqulov I.", "A")
check("juda qisqa nom rad etildi", res is False)

res, info = db.rename_subject(rang, "Ismoilova N.", "O'zimniki")
check("begona fan nomini o'zgartira olmaydi", res is False)

check("tur yakka -> guruh",
      db.set_subject_type(rang, "Berdiqulov I.", "guruh"))

check("tur saqlandi",
      db.get_subject_type("Berdiqulov I.", "Akvarel") == "guruh")

check("begona fan turini o'zgartira olmaydi",
      db.set_subject_type(rang, "Ismoilova N.", "yakka") is False)

check("noto'g'ri tur rad etildi",
      db.set_subject_type(rang, "Berdiqulov I.", "boshqa") is False)


# ==========================
# JO'RNAVOZ O'ZI BIRIKTIRILADI
# ==========================

db.add_teacher("Yusupov K.", "Fortepiano")

check("o'zini biriktirdi", db.add_concertmaster(slot_a, "Ismoilova N."))
check("ikkinchisi ham", db.add_concertmaster(slot_a, "Yusupov K."))

mine = db.get_concertmaster_slots("Ismoilova N.")
check("o'z ro'yxatida ko'rinadi",
      len(mine) == 1 and mine[0][0] == slot_a and mine[0][1] == "Berdiqulov I.")

check("darsda ikkalasi bor",
      len(db.get_slot_concertmasters(slot_a)) == 2)

db.remove_concertmaster(slot_a, "Ismoilova N.")
check("o'zi chiqdi, ikkinchisi qoldi",
      db.get_slot_concertmasters(slot_a) == ["Yusupov K."])

check("bog'lanmagan o'qituvchining chat_id si yo'q",
      db.get_teacher_chat_id("Berdiqulov I.") is None)


# ==========================
print()
for line in ok:
    print("  OK   " + line)
for line in bad:
    print("  XATO " + line)
print()
print(str(len(ok)) + " ta o'tdi, " + str(len(bad)) + " ta xato")

sys.exit(1 if bad else 0)
