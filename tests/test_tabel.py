# -*- coding: utf-8 -*-
"""
Oylik tabel hisobi.

Kutilayotgan qiymatlar maktabning HAQIQIY tabel faylidan olingan
(Iyul 2026 varag'i): dam kunlari 5, 12, 19, 26 va to'liq ishlagan
xodimda AK=27, AL=216.

Tabel istisno bo'yicha ishlaydi: hamma kun "+" deb hisoblanadi,
faqat dam kunlari va istisnolar (K, M, O, X, Y) saqlanadi.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import database as db
from db.migrations import run_migrations

os.makedirs(os.path.join(os.path.dirname(os.path.abspath(__file__)), "_tmp"),
            exist_ok=True)

DB = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                  "_tmp", "test_tabel.db")

if os.path.exists(DB):
    os.remove(DB)

db.DB_NAME = DB
run_migrations(verbose=False)

ok, bad = [], []


def check(label, cond):
    (ok if cond else bad).append(label)


# ==========================
# 1. DAM KUNLARI TAKLIFI
# ==========================

taklif = db.suggested_rest_days(2026, 7)

check("Iyul 2026: yakshanbalar topildi (haqiqiy fayl bilan bir xil): "
      + str(taklif),
      taklif == [5, 12, 19, 26])

yanvar = db.suggested_rest_days(2026, 1)

check("Yanvarda bayramlar ham qo'shildi (1 va 14)",
      1 in yanvar and 14 in yanvar)

check("8-mart bayram sifatida tanildi", 8 in db.suggested_rest_days(2026, 3))

check("Iyulda bayram yo'q - faqat yakshanbalar",
      all(kun in (5, 12, 19, 26) for kun in taklif))


# ==========================
# 2. TASDIQLASH
# ==========================

check("Tasdiqlanmagan oy shunday ko'rinadi",
      not db.is_month_confirmed(2026, 7))

db.set_rest_days(2026, 7, taklif)

check("Tasdiqlangandan keyin holat o'zgardi",
      db.is_month_confirmed(2026, 7))

check("Dam kunlari saqlandi", db.get_rest_days(2026, 7) == [5, 12, 19, 26])


# ==========================
# 3. TO'LIQ ISHLAGAN XODIM
# ==========================

sid = db.add_tech_staff("Karimova Dilnoza", "Farrosh", "6", 1067640)

r = db.month_row(sid, 2026, 7)

check("Ishlangan kunlar = 27 (faylda AK=27)", r["ishlangan"] == 27)

check("Soatlar = 216 (faylda AL=216)", r["soat"] == 216)

check("Yakshanba D bilan belgilandi", r["days"][5] == "D")

check("Oddiy kun + bilan", r["days"][6] == "+")

check("Istisno ustunlari nol",
      r["K"] == 0 and r["M"] == 0 and r["O"] == 0
      and r["X"] == 0 and r["Y"] == 0)


# ==========================
# 4. KASALLIK VARAQASI - ORALIQ
# ==========================

db.set_mark_range(sid, 2026, 7, 6, 10, "K")

r = db.month_row(sid, 2026, 7)

check("5 kun kasallik sanaldi", r["K"] == 5)

check("Ishlangan kunlar shuncha kamaydi", r["ishlangan"] == 22)

check("Soat ham qayta hisoblandi", r["soat"] == 22 * 8)

check("Belgi to'g'ri qo'yildi", r["days"][6] == "K" and r["days"][10] == "K")


# ==========================
# 5. TA'TIL ICHIDAGI YAKSHANBA DAM KUNI BO'LIB QOLADI
# ==========================
#
# Mehnat ta'tili 13-20 iyul: ichida 19-iyul yakshanba bor.
# Tabelda u baribir D bo'lib turishi kerak, M emas.

db.set_mark_range(sid, 2026, 7, 13, 20, "M")

r = db.month_row(sid, 2026, 7)

check("Yakshanba ta'til belgisini olmadi", r["days"][19] == "D")

check("Qolgan kunlar ta'til bo'ldi",
      r["days"][13] == "M" and r["days"][20] == "M")

check("Mehnat ta'tili kunlari sanaldi (yakshanbasiz)", r["M"] == 7)


# ==========================
# 6. QOLGAN BELGILAR
# ==========================

db.set_mark(sid, 2026, 7, 21, "O")
db.set_mark(sid, 2026, 7, 22, "X")
db.set_mark(sid, 2026, 7, 23, "Y")

r = db.month_row(sid, 2026, 7)

check("O - o'z hisobidan ta'til", r["O"] == 1)
check("X - xizmat safari", r["X"] == 1)
check("Y - sababsiz kelmagan", r["Y"] == 1)

check("Belgilar ro'yxati to'liq (K, M, O, X, Y)",
      set(db.TABEL_MARKS) == {"K", "M", "O", "X", "Y"})


# ==========================
# 7. BELGINI OLIB TASHLASH
# ==========================

db.set_mark(sid, 2026, 7, 23, None)

r = db.month_row(sid, 2026, 7)

check("Belgi olib tashlandi va kun yana ish kuni bo'ldi",
      r["Y"] == 0 and r["days"][23] == "+")


# ==========================
# 8. QO'SHIMCHA DAM KUNI
# ==========================
#
# Ko'chma bayramlar (Ramazon, Qurbon hayiti) har yili siljiydi -
# ularni mudir qo'lda qo'shadi.

avval = db.month_row(sid, 2026, 7)["ishlangan"]

db.toggle_rest_day(2026, 7, 4)

keyin = db.month_row(sid, 2026, 7)

check("Qo'shimcha dam kuni ishlangan kunni kamaytirdi",
      keyin["ishlangan"] == avval - 1)

check("O'sha kun D bo'ldi", keyin["days"][4] == "D")

db.toggle_rest_day(2026, 7, 4)

check("Qaytarib olindi",
      db.month_row(sid, 2026, 7)["ishlangan"] == avval)


# ==========================
# 9. OY UZUNLIGI
# ==========================

check("Fevral 2026 - 28 kun", db.days_in_month(2026, 2) == 28)
check("Kabisa yili 2028 - 29 kun", db.days_in_month(2028, 2) == 29)


print()

for line in ok:
    print("  OK   " + line)

for line in bad:
    print("  XATO " + line)

print()
print(str(len(ok)) + " ta o'tdi, " + str(len(bad)) + " ta xato")

sys.exit(1 if bad else 0)
