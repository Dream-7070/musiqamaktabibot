# -*- coding: utf-8 -*-
"""
Mini App: kutilmagan xato har doim JSON qaytaradi, HTML emas -
aks holda frontend res.json() da qotib qoladi (oq ekran).
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import database as db

os.makedirs(os.path.join(os.path.dirname(os.path.abspath(__file__)), "_tmp"), exist_ok=True)
DB = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                  "_tmp", "test_webapp_errors.db")

if os.path.exists(DB):
    os.remove(DB)

db.DB_NAME = DB
db.create_tables()
db.migrate_schema()

import webapp.server as ws

client = ws.app.test_client()

ok, bad = [], []


def check(label, cond):
    (ok if cond else bad).append(label)


# ==========================
# 1. MAVJUD BO'LMAGAN YO'L - 404 LEKIN JSON
# ==========================

r = client.get("/api/mavjud-emas-shunday-route")

check("404 status", r.status_code == 404)
check("HTML emas, JSON", r.is_json)
check("xato matni bor", "error" in (r.get_json() or {}))


# ==========================
# 2. KUTILMAGAN ICHKI XATO - 500 LEKIN JSON, TRACEBACK OSHKOR EMAS
# ==========================

original = ws._authenticated_user

ws._authenticated_user = lambda: (_ for _ in ()).throw(RuntimeError("sinov xatosi"))

r = client.get("/api/whoami")

check("500 status", r.status_code == 500)
check("HTML emas, JSON", r.is_json)

body = r.get_json() or {}

check("xato matni bor", "error" in body)
check(
    "python traceback foydalanuvchiga chiqmadi",
    "RuntimeError" not in str(body) and "Traceback" not in str(body)
)

ws._authenticated_user = original


# ==========================
# 3. ODATDAGI RUXSAT XATOSI HALI HAM O'ZGARMAGAN (401)
# ==========================

r = client.get("/api/whoami")

check("ruxsatsiz so'rov hali ham 401", r.status_code == 401)


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
