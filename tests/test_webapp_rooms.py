# -*- coding: utf-8 -*-
"""Mini App xona endpointlari: o'qituvchi ko'radi, admin boshqaradi."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import database as db

os.makedirs(os.path.join(os.path.dirname(os.path.abspath(__file__)), "_tmp"), exist_ok=True)
DB = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                  "_tmp", "test_webapp_rooms.db")

if os.path.exists(DB):
    os.remove(DB)

db.DB_NAME = DB
db.create_tables()
db.migrate_schema()

db.add_teacher("Karimov Aziz", "Fortepiano")
db.add_teacher("Aliyev Bobur", "Fortepiano")

import webapp.server as ws

# server o'z modulida DB_NAME ni database'dan oladi, shuning uchun
# alohida sozlash shart emas - db.DB_NAME allaqachon o'zgargan

client = ws.app.test_client()

ok, bad = [], []


def check(label, cond):
    (ok if cond else bad).append(label)


# ==========================
# SOXTA AUTENTIFIKATSIYA
# ==========================
#
# initData HMAC ni sinovda qurib bo'lmaydi - shuning uchun
# foydalanuvchini aniqlaydigan funksiyani almashtiramiz.

CURRENT = {"id": 111}

ws._authenticated_user = lambda: CURRENT

# admin - ADMIN_IDS orqali tekshiriladi
ws.ADMIN_IDS = [999]

# o'qituvchi - ismi orqali topiladi
ws.find_teacher_binding = lambda uid: (
    ("Karimov Aziz", "Fortepiano") if uid == 111 else None
)


def as_teacher():
    CURRENT["id"] = 111


def as_admin():
    CURRENT["id"] = 999


def as_stranger():
    CURRENT["id"] = 555


# ==========================
# 1. O'QITUVCHI XONALARNI KO'RADI
# ==========================

as_teacher()

r = client.get("/api/teacher/rooms?day=Dushanba&time=08:00&hours=1")

check("o'qituvchiga ro'yxat berildi", r.status_code == 200)

rooms = r.get_json()["rooms"]

check("31 ta xona qaytdi", len(rooms) == 31)
check("hech biri band emas", not any(x["busy"] for x in rooms))
check("nomli xona label bilan keldi",
      any(x["label"] == "1/23 - Zal" for x in rooms))


# ==========================
# 2. BAND XONA - KIM BANDLIGI
# ==========================

db.create_slot("Aliyev Bobur", "Ansambl", "Dushanba", "08:00", "2/4", 45)

rooms = client.get(
    "/api/teacher/rooms?day=Dushanba&time=08:00&hours=1"
).get_json()["rooms"]

busy = [x for x in rooms if x["busy"]]

check("bitta xona band ko'rindi", len(busy) == 1)
check("2/4 band", busy[0]["room"] == "2/4")
check("kim band qilgani keldi", busy[0]["teacher"] == "Aliyev Bobur")
check("fani ham keldi", busy[0]["subject"] == "Ansambl")


# ==========================
# 3. BAND XONAGA DARS QO'YIB BO'LMAYDI
# ==========================

r = client.post("/api/teacher/slots", json={
    "subject": "Ansambl", "day": "Dushanba",
    "time": "08:00", "hours": 1, "room": "2/4"
})

check("band xona rad etildi", r.status_code == 409)
check("xato matnida o'qituvchi ismi bor",
      "Aliyev Bobur" in r.get_json().get("error", ""))


# ==========================
# 4. RO'YXATDA YO'Q XONA RAD ETILADI
# ==========================

r = client.post("/api/teacher/slots", json={
    "subject": "Ansambl", "day": "Dushanba",
    "time": "09:00", "hours": 1, "room": "9/99"
})

check("noma'lum xona rad etildi", r.status_code == 400)
check("sababi tushunarli",
      "xona yo'q" in r.get_json().get("error", "").lower())


# ==========================
# 5. ADMIN XONA QO'SHADI
# ==========================

as_admin()

r = client.post("/api/admin/rooms", json={"code": "2/20", "name": "Repetitsiya"})

check("admin xona qo'shdi", r.status_code == 200)
check("label qaytdi", r.get_json()["room"]["label"] == "2/20 - Repetitsiya")

listed = client.get("/api/admin/rooms").get_json()["rooms"]

check("ro'yxatda ko'rindi", any(x["code"] == "2/20" for x in listed))
check("endi 32 ta", len(listed) == 32)

r = client.post("/api/admin/rooms", json={"code": "2/20"})

check("takror qo'shilmadi", r.status_code == 400)

r = client.post("/api/admin/rooms", json={"code": ""})

check("bo'sh raqam rad etildi", r.status_code == 400)


# ==========================
# 6. O'CHIRISH
# ==========================

new_id = [x for x in listed if x["code"] == "2/20"][0]["id"]

r = client.delete("/api/admin/rooms/" + str(new_id))

check("bo'sh xona o'chdi", r.status_code == 200)
check("yana 31 ta",
      len(client.get("/api/admin/rooms").get_json()["rooms"]) == 31)

busy_id = [
    x for x in client.get("/api/admin/rooms").get_json()["rooms"]
    if x["code"] == "2/4"
][0]["id"]

r = client.delete("/api/admin/rooms/" + str(busy_id))

check("dars bor xona o'chmadi", r.status_code == 400)
check("sababi aytildi", "dars" in r.get_json().get("error", ""))


# ==========================
# 7. RUXSAT
# ==========================

as_teacher()

check("o'qituvchi admin ro'yxatini ko'rmaydi",
      client.get("/api/admin/rooms").status_code == 401)

check("o'qituvchi xona qo'sha olmaydi",
      client.post("/api/admin/rooms",
                  json={"code": "5/5"}).status_code == 401)

as_stranger()

check("begona xonalarni ko'rmaydi",
      client.get("/api/teacher/rooms?day=Dushanba&time=08:00&hours=1"
                 ).status_code == 403)


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
