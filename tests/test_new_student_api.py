# -*- coding: utf-8 -*-
"""Mini App'da o'quvchi qo'shish: bitta so'rov, botdagi qoidalar bilan bir xil."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import database as db

HERE = os.path.dirname(os.path.abspath(__file__))

os.makedirs(os.path.join(HERE, "_tmp"), exist_ok=True)
DB = os.path.join(HERE, "_tmp", "test_new_student_api.db")

if os.path.exists(DB):
    os.remove(DB)

db.DB_NAME = DB
db.create_tables()
db.migrate_schema()

db.add_teacher("Karimov Aziz", "Fortepiano")
db.add_teacher("Sobirova Nilufar", "Doira")

import webapp.server as ws

client = ws.app.test_client()

ok, bad = [], []


def check(label, cond):
    (ok if cond else bad).append(label)


CURRENT = {"id": 111}

ws._authenticated_user = lambda: CURRENT
ws.ADMIN_IDS = [999]
ws.find_teacher_binding = lambda uid: (
    ("Karimov Aziz", "Fortepiano") if uid == 111
    else ("Sobirova Nilufar", "Doira") if uid == 222
    else None
)


def post(**kwargs):
    return client.post("/api/teacher/students", json=kwargs)


BASE = {
    "student": "Aliyev Ali",
    "birth_date": "2015-03-21",
    "metrika": "AA1234567",
    "class_name": "3",
    "monthly_fee": 0
}


# ==========================
# 1. FORMA MA'LUMOTNOMASI
# ==========================

r = client.get("/api/teacher/student_form")

check("forma ma'lumotnomasi keldi", r.status_code == 200)

form = r.get_json()

check("sinflar ro'yxati bor", "1" in form["classes"] and "7" in form["classes"])
check("badal variantlari bor", len(form["fees"]) > 1)
check("imtiyoz belgisi bor", form["privileged_fee"] in form["fees"])


# ==========================
# 2. BITTA SO'ROV BILAN QO'SHILADI
# ==========================

fee = [f for f in form["fees"] if f > 0][0]

data = dict(BASE, monthly_fee=fee)

r = post(**data)

check("o'quvchi qo'shildi", r.status_code == 200)
check("ismi qaytdi", r.get_json()["student"] == "Aliyev Ali")
check("bazada bor", "Aliyev Ali" in db.get_students("Karimov Aziz"))
check("badal saqlandi", db.get_student_fee("Karimov Aziz", "Aliyev Ali") == fee)


# ==========================
# 3. VALIDATSIYA
# ==========================

check("qisqa ism rad etildi",
      post(**dict(data, student="Al", metrika="BB2")).status_code == 400)

check("noto'g'ri sana rad etildi",
      post(**dict(data, birth_date="kecha", metrika="BB7654321")).status_code == 400)

check("qisqa guvohnoma rad etildi",
      post(**dict(data, metrika="12")).status_code == 400)

check("yo'q sinf rad etildi",
      post(**dict(data, class_name="99", metrika="BB7654321")).status_code == 400)

check("yo'q badal rad etildi",
      post(**dict(data, monthly_fee=12345, metrika="BB7654321")).status_code == 400)

check("KK.OO.YYYY sanasi qabul qilinadi",
      post(**dict(data, student="Sanaev Sana",
                  birth_date="21.03.2015",
                  metrika="CC7654321")).status_code == 200)


# ==========================
# 4. SHU O'QITUVCHIDA TAKROR - XATO
# ==========================

r = post(**dict(data, student="Boshqa Bola"))

check("takror guvohnoma to'sildi", r.status_code == 409)
check("kim ekani aytildi", "Aliyev Ali" in r.get_json()["error"])


# ==========================
# 5. BOSHQA O'QITUVCHIDA BOR - TASDIQ SO'RALADI
# ==========================

CURRENT["id"] = 222  # Sobirova Nilufar

r = post(**dict(BASE, student="Aliyev Ali", monthly_fee=fee))

check("tasdiq so'raldi", r.status_code == 409)

body = r.get_json()

check("tasdiq belgisi bor", body.get("needs_confirm") is True)
check("boshqa o'qituvchidagi sinfi ma'lumot uchun keldi",
      body["other_class"] == "3")


# ==========================
# 6. TASDIQLANGACH: ISM/SANA KO'CHIRILADI, SINF ESA YO'Q
# ==========================
# Sinf mutaxassislikka bog'liq: fortepianoda 3-sinf bola
# doirani endi boshlayotgan bo'lsa - u yerda 1-sinf.
#

r = post(**dict(
    BASE,
    student="Aliyev Ali",
    monthly_fee=fee,
    birth_date="2000-01-01",   # ataylab noto'g'ri
    class_name="1",            # bu yerda boshqa sinf - saqlanishi kerak
    same_child=True
))

check("ikkinchi mutaxassislikka qo'shildi", r.status_code == 200)
check("ikkinchi o'qituvchida ham bor",
      "Aliyev Ali" in db.get_students("Sobirova Nilufar"))

info = db.get_student_info("Aliyev Ali", "Sobirova Nilufar")

check("tug'ilgan sana asl holida", info[3] == "2015-03-21")
check("sinfi o'zi tanlagancha qoldi (ko'chirilmadi)", str(info[5]) == "1")
check("badal esa o'ziniki", db.get_student_fee("Sobirova Nilufar", "Aliyev Ali") == fee)


# ==========================
# 7. RUXSAT
# ==========================

CURRENT["id"] = 555

check("begona qo'sha olmaydi", post(**BASE).status_code == 403)
check("begona formani ko'rmaydi",
      client.get("/api/teacher/student_form").status_code == 403)


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
