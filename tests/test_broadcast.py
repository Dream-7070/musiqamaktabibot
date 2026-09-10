# -*- coding: utf-8 -*-
"""Bir nechta adminga yuborilgan xabarnoma: biri javob bersa hammasida yopiladi."""

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import database as db

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

os.makedirs(os.path.join(HERE, "_tmp"), exist_ok=True)
DB = os.path.join(HERE, "_tmp", "test_broadcast.db")

if os.path.exists(DB):
    os.remove(DB)

db.DB_NAME = DB
db.create_tables()
db.migrate_schema()

ok, bad = [], []


def check(label, cond):
    (ok if cond else bad).append(label)


ADMIN_A = 111
ADMIN_B = 222


# ==========================
# 1. IKKI ADMINGA YUBORILGAN NUSXALAR
# ==========================

db.remember_broadcast("teacher_request", 7, ADMIN_A, 1001)
db.remember_broadcast("teacher_request", 7, ADMIN_B, 2002)

copies = dict(db.get_broadcast_copies("teacher_request", 7))

check("ikkala nusxa eslab qolindi", len(copies) == 2)
check("A ning xabari", copies[ADMIN_A] == 1001)
check("B ning xabari", copies[ADMIN_B] == 2002)


# ==========================
# 2. BOSHQA SO'ROV ARALASHMAYDI
# ==========================

db.remember_broadcast("teacher_request", 8, ADMIN_A, 3003)
db.remember_broadcast("payment", 7, ADMIN_A, 4004)

check("boshqa so'rov alohida",
      db.get_broadcast_copies("teacher_request", 8) == [(ADMIN_A, 3003)])
check("boshqa tur alohida",
      db.get_broadcast_copies("payment", 7) == [(ADMIN_A, 4004)])


# ==========================
# 3. QAYTA YUBORILSA - YANGI message_id
# ==========================

db.remember_broadcast("teacher_request", 7, ADMIN_A, 1111)

check("nusxa ikkilanmadi",
      len(db.get_broadcast_copies("teacher_request", 7)) == 2)
check("message_id yangilandi",
      dict(db.get_broadcast_copies("teacher_request", 7))[ADMIN_A] == 1111)


# ==========================
# 4. JAVOB BERILGACH TOZALANADI
# ==========================

db.clear_broadcast("teacher_request", 7)

check("hal bo'lgan so'rov o'chdi",
      db.get_broadcast_copies("teacher_request", 7) == [])
check("qolganlariga tegmadi",
      db.get_broadcast_copies("teacher_request", 8) == [(ADMIN_A, 3003)])


# ==========================
# 5. ESKIRGANLARI TOZALANADI
# ==========================

conn = db.connect()

conn.execute(
    """
    INSERT INTO broadcast_messages (kind, ref_id, chat_id, message_id, created_at)
    VALUES ('teacher_request', 99, 333, 9999, datetime('now','localtime','-40 days'))
    """
)

conn.commit()
conn.close()

check("eski yozuv bor",
      db.get_broadcast_copies("teacher_request", 99) != [])

removed = db.prune_broadcasts(30)

check("eski yozuv tozalandi", removed == 1)
check("eskisi yo'q",
      db.get_broadcast_copies("teacher_request", 99) == [])
check("yangilariga tegmadi",
      db.get_broadcast_copies("teacher_request", 8) == [(ADMIN_A, 3003)])


# ==========================
# 6. main.py TO'G'RI ULANGANMI
# ==========================
#
# main.py ni import qilib bo'lmaydi (import paytida bot polling
# boshlaydi), shuning uchun manba matni tekshiriladi - bu
# `test_cancel_coverage.py` dagi yondashuvning o'zi.

source = open(os.path.join(ROOT, "main.py"), encoding="utf-8").read()

check("o'qituvchi so'rovi broadcast orqali yuboriladi",
      '_broadcast_to_admins(\n            "teacher_request"' in source)

check("tasdiqlashda hamma nusxa yopiladi",
      source.count('_close_broadcast(\n        "teacher_request"') == 2)

check("kvitansiya nusxalari eslab qolinadi",
      'remember_broadcast("payment", payment_id, staff_id' in source)

check("kvitansiyada ham hamma nusxa yopiladi",
      source.count('_close_broadcast(\n        "payment"') == 2)

check("eski bir nusxali _mark_reviewed olib tashlandi",
      "_mark_reviewed" not in source)

# tugmali xabarnoma endi qo'lda ADMIN_IDS bo'ylab yuborilmasin

# `_broadcast_to_admins` ning o'zi ichida aylanma bor - u
# hisobga olinmaydi, qolgan joylar tekshiriladi.

start = source.index("def _broadcast_to_admins")
end = source.index("def _close_broadcast")

outside = source[:start] + source[end:]

manual = re.findall(
    r"for admin_id in ADMIN_IDS:(.{0,600}?)(?=\ndef |\n@bot|\Z)",
    outside,
    re.S
)

check("tugmali xabar qo'lda tarqatilmaydi",
      not any("reply_markup" in block for block in manual))


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
