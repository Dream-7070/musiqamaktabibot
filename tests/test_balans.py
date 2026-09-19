# -*- coding: utf-8 -*-
"""Avans va qisman to'lovlar tekshiruvi."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import database as db

os.makedirs(os.path.join(os.path.dirname(os.path.abspath(__file__)), "_tmp"), exist_ok=True)
DB = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                  "_tmp", "test_balans.db")

if os.path.exists(DB):
    os.remove(DB)

db.DB_NAME = DB
db.create_tables()
db.migrate_schema()

ok, bad = [], []


def check(label, cond):
    (ok if cond else bad).append(label)

def run():
    db.add_teacher("T1", "Fortepiano")

    # 1. To'liq to'lov (avans 0, qarz 0)
    db.add_student("T1", "Bola 1", "2015-01-01", "I-TV 001", "1", 123600)
    pid1 = db.create_payment_request("T1", "Bola 1", "2026-09", 123600, "f", "l", 1)
    db.approve_payment(pid1, 1, received=123600)
    
    st1 = db.month_payment_state("T1", "Bola 1", "2026-09", 123600)
    check("1. To'liq to'lov -> paid=True", st1["paid"] == True)
    check("1. To'liq to'lov -> qarz=0", st1["debt"] == 0.0)
    check("1. To'liq to'lov -> avans=0", st1["balance"] == 0.0)

    # 2. Qisman to'lov (qarz qoladi)
    db.add_student("T1", "Bola 2", "2015-01-02", "I-TV 002", "1", 123600)
    pid2 = db.create_payment_request("T1", "Bola 2", "2026-09", 50000, "f", "l", 1)
    db.approve_payment(pid2, 1, received=50000)
    
    st2 = db.month_payment_state("T1", "Bola 2", "2026-09", 123600)
    check("2. Qisman to'lov -> paid=False", st2["paid"] == False)
    check("2. Qisman to'lov -> qarz=73600", st2["debt"] == 73600.0)

    # 3. Yana 73600 tushdi -> paid=True, qarz 0
    pid3 = db.create_payment_request("T1", "Bola 2", "2026-09", 73600, "f", "l", 1)
    db.approve_payment(pid3, 1, received=73600)
    
    st3 = db.month_payment_state("T1", "Bola 2", "2026-09", 123600)
    check("3. Yana to'lov -> paid=True", st3["paid"] == True)
    check("3. Yana to'lov -> qarz=0", st3["debt"] == 0.0)

    # 4. Ortiqcha to'lov -> avans
    db.add_student("T1", "Bola 3", "2015-01-03", "I-TV 003", "1", 123600)
    pid4 = db.create_payment_request("T1", "Bola 3", "2026-09", 125000, "f", "l", 1)
    db.approve_payment(pid4, 1, received=125000)
    
    st4 = db.month_payment_state("T1", "Bola 3", "2026-09", 123600)
    check("4. Ortiqcha to'lov -> paid=True", st4["paid"] == True)
    check("4. Ortiqcha to'lov -> avans=1400", st4["balance"] == 1400.0)

    # 5. Keyingi oyda avans ishlatilishi
    # get_monthly_debt_rows ni chaqirganda avtomatik ishlatilishi kerak.
    rows = db.get_monthly_debt_details("2026-10")
    b3_row = [r for r in rows if r["student"] == "Bola 3"][0]

    check("5. Avans ishlatildi -> covered=1400", b3_row["covered"] == 1400.0)
    check("5. Avans ishlatildi -> qarz=122200", b3_row["debt"] == 122200.0)
    check("5. Avans ishlatildi -> balans=0", db.get_student_balance("T1", "Bola 3") == 0.0)

    # 6. Imtiyozli bola (FEE_PRIVILEGED = -1) hech qachon qarzdor emas
    db.add_student("T1", "Bola Imtiyoz", "2015-01-04", "I-TV 004", "1", db.FEE_PRIVILEGED)
    rows2 = db.get_monthly_debt_details("2026-10")
    b4_row = [r for r in rows2 if r["student"] == "Bola Imtiyoz"][0]

    check("6. Imtiyozli bola -> paid=True", b4_row["paid"] is True)
    check("6. Imtiyozli bola -> qarz=0", b4_row["debt"] == 0.0)

    # 7. Eski tasdiqlangan kvitansiya (buxgalter summa belgilamagan)
    #    ham hisobga olinsin - aks holda bola qarzdor bo'lib qolardi.

    db.add_student("T1", "Bola Eski", "2015-01-05", "I-TV 005", "1", 123600)

    pid5 = db.create_payment_request("T1", "Bola Eski", "2026-09", 124000, "f", "l", 1)

    db.approve_payment(pid5, 1)

    st5 = db.month_payment_state("T1", "Bola Eski", "2026-09", 123600)

    check("7. Summasiz tasdiqlangan to'lov hisobga olindi", st5["covered"] > 0)
    check("7. Summasiz to'lovda ham qarz yo'q", st5["paid"] is True)

    print(f"\\n✅ OK: {len(ok)}")
    if bad:
        print(f"❌ XATO: {len(bad)}")
        for b in bad:
            print("  -", b)
        sys.exit(1)

if __name__ == "__main__":
    run()
