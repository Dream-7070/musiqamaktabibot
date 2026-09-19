# -*- coding: utf-8 -*-
"""Mini App buxgalter endpointlari."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import database as db

os.makedirs(os.path.join(os.path.dirname(os.path.abspath(__file__)), "_tmp"), exist_ok=True)
DB = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                  "_tmp", "test_webapp_buxgalter.db")

if os.path.exists(DB):
    os.remove(DB)

db.DB_NAME = DB
db.create_tables()
db.migrate_schema()

db.add_teacher("Karimov Aziz", "Fortepiano")
db.add_student("Karimov Aziz", "Toshmatov Ali", "2015-01-01", "AA1111111", class_name="1", monthly_fee=500000)
db.add_student("Karimov Aziz", "Imtiyozli Vali", "2015-01-01", "AA2222222", class_name="1", monthly_fee=db.FEE_PRIVILEGED)

import webapp.server as ws

client = ws.app.test_client()

ok, bad = [], []

def check(label, cond):
    (ok if cond else bad).append(label)

CURRENT = {"id": 111}
ws._authenticated_user = lambda: CURRENT
ws.ADMIN_IDS = [999]

ws.find_teacher_binding = lambda uid: (
    ("Karimov Aziz", "Fortepiano") if uid == 111 else None
)

def _mock_get_staff_role(uid):
    if uid == 222:
        return "buxgalter"
    return None

ws.get_staff_role = _mock_get_staff_role

# Replace _tell_bot so it doesn't try to use the network
ws._tell_bot = lambda chat_id, text: None

def as_teacher():
    CURRENT["id"] = 111

def as_buxgalter():
    CURRENT["id"] = 222

pay_id_1 = db.create_payment_request("Karimov Aziz", "Toshmatov Ali", "2026-09", 500000, "drive_1", "link_1", 111)

as_teacher()
r = client.get("/api/buxgalter/pending")
check("Oddiy o'qituvchi kirolmaydi", r.status_code in (401, 403))

as_buxgalter()
r = client.get("/api/buxgalter/pending")
check("Buxgalter kira oladi", r.status_code == 200)
data = r.get_json()["payments"]
check("Kutilayotgan kvitansiyalar keldi", len(data) == 1 and data[0]["student"] == "Toshmatov Ali")

r = client.post(f"/api/buxgalter/payments/{pay_id_1}/approve")
check("Tasdiqlandi", r.status_code == 200)

r = client.get("/api/buxgalter/pending")
data = r.get_json()["payments"]
check("Pendingdan chiqdi", len(data) == 0)

r = client.post(f"/api/buxgalter/payments/{pay_id_1}/approve")
check("Ikkinchi marta tasdiqlash 404", r.status_code == 404)

r = client.get("/api/buxgalter/debt?month=2026-09")
data = r.get_json()
rows = data["rows"]
toshmatov = [r for r in rows if r["student"] == "Toshmatov Ali"][0]
vali = [r for r in rows if r["student"] == "Imtiyozli Vali"][0]

check("Toshmatov paid=true", toshmatov["paid"] == True)
check("Imtiyozli qarzda emas", vali["paid"] == True)

r = client.get("/api/buxgalter/report?month=2026-09")
data = r.get_json()
expected = data["expected"]
collected = data["collected"]
debt = data["debt"]
check("Totals matematikasi togri", expected == collected + debt)

print()
for line in ok:
    print("  OK   " + line)

for line in bad:
    print("  XATO " + line)

print()
print(str(len(ok)) + " ta o'tdi, " + str(len(bad)) + " ta xato")

sys.exit(1 if bad else 0)
