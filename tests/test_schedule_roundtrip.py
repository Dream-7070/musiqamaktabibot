# -*- coding: utf-8 -*-
"""
Taklif generatori chiqargan faylni import oqimi o'qiy oladimi.

Bu ikki modul orasidagi CHOK:

    services/schedule_export.py  - variantni Excel qilib yozadi
    services/schedule_import.py  - o'qituvchi qaytargan faylni o'qiydi

Ikkalasi alohida yozilgan va ular orasida yozma shartnoma yo'q -
faqat "parser shu formatni tushunadi" degan kelishuv bor. Shuning
uchun chok sinov bilan mahkamlanadi.

Nega aynan shu sinov kerak: bir vaqtlar eksport hamma variantni
BITTA faylning alohida varaqlariga yozardi, import esa faqat
birinchi varaqni o'qiydi. Natijada o'qituvchi 2-variantni tanlab
qayta yuborsa, bot jimgina 1-variantni olardi - xato bildirmasdan,
noto'g'ri jadval bilan.
"""

import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import openpyxl

from services.schedule_export import export_variant_to_excel, variant_filename
from services.schedule_import import read_workbook, format_time


ok, bad = [], []


def check(label, cond):
    (ok if cond else bad).append(label)


TMP = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_tmp")

os.makedirs(TMP, exist_ok=True)


def lesson(day, start, end, subject, who, room="2/14", class_name="3"):

    return {
        "day": day,
        "start": start,
        "end": end,
        "subject": subject,
        "who": who,
        "room": room,
        "class_name": class_name,
        "duration_minutes": 45,
    }


VARIANTS = [
    {
        "complete": True,
        "lessons": [
            lesson("Dushanba", "8:00", "8:45", "Mutaxassislik", "Murodov Otabek"),
            lesson("Payshanba", "9:00", "9:45", "Mutaxassislik", "Murodov Otabek"),
            lesson("Dushanba", "8:50", "9:15", "Tanlangan fan",
                   "Kenjaboyev Asadbek", room="1/23 (Zal)", class_name="2"),
        ],
    },
    {
        "complete": True,
        "lessons": [
            lesson("Seshanba", "13:00", "13:45", "Mutaxassislik", "Murodov Otabek"),
        ],
    },
    {
        "complete": False,
        "lessons": [
            lesson("Juma", "10:00", "10:45", "Mutaxassislik", "Murodov Otabek"),
        ],
        "unplaced": [{"who": "Anvarov Abdulaziz"}],
    },
]


def write(variant, index):

    handle, path = tempfile.mkstemp(suffix=".xlsx", dir=TMP)

    os.close(handle)

    export_variant_to_excel("Kamolov Oybek", variant, path, index)

    return path


# ==========================
# 1. HAR VARIANT - ALOHIDA BITTA VARAQLI FAYL
# ==========================


for index, variant in enumerate(VARIANTS, start=1):

    path = write(variant, index)

    try:
        names = openpyxl.load_workbook(path).sheetnames

    finally:
        os.remove(path)

    check("variant " + str(index) + ": faylda bitta varaq",
          len(names) == 1)


check("fayl nomi variantni ko'rsatadi",
      variant_filename("Kamolov Oybek", 2) == "Kamolov_Oybek_variant_2.xlsx")


# ==========================
# 2. HAR BIR VARIANT O'ZI O'QILADI
# ==========================
#
# Eng muhim tekshiruv: 2-variant faylidan 2-variant chiqishi
# kerak, 1-variant emas.


expected = [
    ("Dushanba", 3),
    ("Seshanba", 1),
    ("Juma", 1),
]

for index, variant in enumerate(VARIANTS, start=1):

    path = write(variant, index)

    try:
        result = read_workbook(path)

    finally:
        os.remove(path)

    lessons = result["sheet"]["lessons"]

    check("variant " + str(index) + ": darslar soni mos",
          len(lessons) == expected[index - 1][1])

    days = {item["day"] for item in lessons}

    check("variant " + str(index) + ": aynan o'sha variant o'qildi",
          expected[index - 1][0] in days)


# ==========================
# 3. MA'LUMOT YO'QOLMAYDI
# ==========================


path = write(VARIANTS[0], 1)

try:
    result = read_workbook(path)

finally:
    os.remove(path)

lessons = result["sheet"]["lessons"]

first = next(
    (item for item in lessons
     if item["day"] == "Dushanba" and item["start"] == 8 * 60),
    None
)

check("vaqt to'g'ri o'qildi", first and format_time(first["start"]) == "8:00")

check("dars davomiyligi to'g'ri", first and first["minutes"] == 45)

check("fan bloki o'qildi", first and first["subject"] == "Mutaxassislik")

check("o'quvchi o'qildi", first and first["who"] == "Murodov Otabek")

check("sinf o'qildi", first and first["class"] == "3")

check("xona qavs ichidan o'qildi", first and first["room"] == "2/14")


zal = next(
    (item for item in lessons if item["subject"] == "Tanlangan fan"),
    None
)

check("boshqa xonadagi dars o'z xonasini saqladi",
      zal and "1/23" in (zal["room"] or ""))

check("eksport fayli savol tug'dirmaydi", not result["questions"])

check("eksport faylida xato topilmadi",
      not [item for item in result["issues"] if item["level"] == "error"])


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
