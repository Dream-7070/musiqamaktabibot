# -*- coding: utf-8 -*-
"""Admin "ko'rish rejimi": tanlangan o'qituvchi bot va Mini App'da bir xil."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import database as db

os.makedirs(os.path.join(os.path.dirname(os.path.abspath(__file__)), "_tmp"), exist_ok=True)
DB = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                  "_tmp", "test_view_as.db")

if os.path.exists(DB):
    os.remove(DB)

db.DB_NAME = DB
db.create_tables()
db.migrate_schema()

db.add_teacher("Karimov Aziz", "Fortepiano")
db.add_teacher("Aliyev Bobur", "Fortepiano")

import webapp.server as ws

client = ws.app.test_client()

ok, bad = [], []


def check(label, cond):
    (ok if cond else bad).append(label)


# ==========================
# SOXTA AUTENTIFIKATSIYA
# ==========================

CURRENT = {"id": 111}

ws._authenticated_user = lambda: CURRENT

ws.ADMIN_IDS = [999]

ws.find_teacher_binding = lambda uid: (
    ("Karimov Aziz", "Fortepiano") if uid == 111 else None
)

ADMIN = 999


def as_teacher():
    CURRENT["id"] = 111


def as_admin():
    CURRENT["id"] = ADMIN


def as_stranger():
    CURRENT["id"] = 555


# ==========================
# 1. BAZA QATLAMI
# ==========================

check("boshida rejim yo'q", db.get_view_as(ADMIN) is None)

db.set_view_as(ADMIN, "Aliyev Bobur")

check("rejim saqlandi", db.get_view_as(ADMIN) == "Aliyev Bobur")
check("boshqa adminga tegmadi", db.get_view_as(1234) is None)

db.set_view_as(ADMIN, "Karimov Aziz")

check("boshqa o'qituvchiga almashdi", db.get_view_as(ADMIN) == "Karimov Aziz")
check("ro'yxatda bitta yozuv", len(db.get_all_view_as()) == 1)

db.clear_view_as(ADMIN)

check("rejim o'chdi", db.get_view_as(ADMIN) is None)

# o'chirilgan o'qituvchi - rejim o'z-o'zidan bekor bo'ladi

db.set_view_as(ADMIN, "Yo'q Odam")

check("yo'q o'qituvchi rejimi bekor bo'ldi", db.get_view_as(ADMIN) is None)
check("yozuv ham tozalandi", db.get_all_view_as() == [])


# ==========================
# 2. REJIMSIZ - ADMIN O'Z PANELINI KO'RADI
# ==========================

as_admin()

who = client.get("/api/whoami").get_json()

check("admin panel ko'rindi", who["role"] == "admin")

check("admin o'qituvchi API'siga kira olmaydi",
      client.get("/api/teacher/me").status_code == 403)


# ==========================
# 3. REJIMNI YOQISH (Mini App orqali)
# ==========================

teachers = client.get(
    "/api/admin/teachers?dept=" + "Fortepiano"
).get_json()["teachers"]

bobur_id = [t["id"] for t in teachers if t["name"] == "Aliyev Bobur"][0]

r = client.post("/api/admin/view-as", json={"teacher_id": bobur_id})

check("rejim yoqildi", r.status_code == 200)
check("kim tanlangani qaytdi", r.get_json()["teacher"] == "Aliyev Bobur")
check("bazaga yozildi (bot ham ko'radi)",
      db.get_view_as(ADMIN) == "Aliyev Bobur")

r = client.post("/api/admin/view-as", json={"teacher_id": 99999})

check("yo'q o'qituvchi rad etildi", r.status_code == 404)


# ==========================
# 4. REJIMDA - ADMIN O'QITUVCHIDEK KO'RINADI
# ==========================

who = client.get("/api/whoami").get_json()

check("roli o'qituvchi bo'ldi", who["role"] == "teacher")
check("tanlangan o'qituvchi", who["teacher"] == "Aliyev Bobur")
check("rejim ekani aytildi", who["viewing_as"] == "Aliyev Bobur")
check("bo'limi ham keldi", who["department"] == "Fortepiano")

me = client.get("/api/teacher/me")

check("o'qituvchi API ochildi", me.status_code == 200)
check("uning ma'lumoti keldi", me.get_json()["teacher"] == "Aliyev Bobur")

# tanlangan o'qituvchining jadvali ko'rinadi, o'zganiki emas

db.create_slot("Aliyev Bobur", "Ansambl", "Dushanba", "08:00", "2/4", 45)
db.create_slot("Karimov Aziz", "Solfedjio", "Seshanba", "09:00", "2/9", 45)

slots = client.get("/api/teacher/slots").get_json()["slots"]

check("faqat o'sha o'qituvchining darsi", len(slots) == 1)
check("dars aynan uniki", slots[0]["subject"] == "Ansambl")


# ==========================
# 5. REJIM FAQAT ADMINGA TEGISHLI
# ==========================

as_teacher()

who = client.get("/api/whoami").get_json()

check("o'qituvchi o'zini ko'radi", who["teacher"] == "Karimov Aziz")
check("unda rejim yo'q", not who.get("viewing_as"))

check("o'qituvchi rejim yoqa olmaydi",
      client.post("/api/admin/view-as",
                  json={"teacher_id": bobur_id}).status_code == 401)

as_stranger()

check("begona o'qituvchi API'siga kira olmaydi",
      client.get("/api/teacher/me").status_code == 403)


# ==========================
# 6. REJIMDAN CHIQISH
# ==========================

as_admin()

r = client.delete("/api/admin/view-as")

check("rejim o'chirildi", r.status_code == 200)
check("bazada ham qolmadi", db.get_view_as(ADMIN) is None)

who = client.get("/api/whoami").get_json()

check("admin paneliga qaytdi", who["role"] == "admin")


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
