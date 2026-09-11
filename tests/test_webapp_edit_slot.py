# -*- coding: utf-8 -*-
"""Mini App darsni tahrirlash endpointi sinovlari."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import database as db
from database import available_lesson_times, hours_to_minutes

times = [s for s, _ in available_lesson_times(hours_to_minutes(1))]
times_half = [s for s, _ in available_lesson_times(hours_to_minutes(0.5))]
t1, t2, t3, t4 = times[0], times[1], times[2], times[3]
th1 = times_half[3]

os.makedirs(os.path.join(os.path.dirname(os.path.abspath(__file__)), "_tmp"), exist_ok=True)
DB = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                  "_tmp", "test_webapp_edit_slot.db")

if os.path.exists(DB):
    os.remove(DB)

db.DB_NAME = DB
db.create_tables()
db.migrate_schema()

db.add_teacher("Karimov Aziz", "Torli cholg'ular")
db.add_teacher("Aliyev Bobur", "Fortepiano")

import webapp.server as ws

client = ws.app.test_client()

ok, bad = [], []

def check(label, cond):
    (ok if cond else bad).append(label)

CURRENT = {"id": 111}
ws._authenticated_user = lambda: CURRENT

ws.find_teacher_binding = lambda uid: (
    ("Karimov Aziz", "Torli cholg'ular") if uid == 111 else
    ("Aliyev Bobur", "Fortepiano") if uid == 222 else None
)

def as_aziz():
    CURRENT["id"] = 111

def as_bobur():
    CURRENT["id"] = 222

as_aziz()

# Aziz darsi - unga o'quvchi va jo'rnavoz biriktiriladi.
# Butun sinovning maqsadi: ko'chirishda ular yo'qolmasin.

slot_aziz = db.create_slot("Karimov Aziz", "Mutaxassislik", "Dushanba", t1, "1/5", 1)

db.add_student("Karimov Aziz", "Olimov Sardor", "2015-01-01", "12345", "1")
db.add_student_to_slot(slot_aziz, "Olimov Sardor", "Karimov Aziz")
db.add_concertmaster(slot_aziz, "Aliyev Bobur")

# Aziz ning ikkinchi darsi - o'z-o'ziga to'qnashuv uchun

slot_aziz_2 = db.create_slot("Karimov Aziz", "Mutaxassislik", "Dushanba", t2, "1/5", 1)

# Bobur darsi - xona bandligi va begona darsga tegish uchun

slot_bobur = db.create_slot("Aliyev Bobur", "Ansambl", "Dushanba", t3, "1/8", 1)

# 1. Asosiy maqsad: darsni ko'chirish
r = client.patch(f"/api/teacher/slots/{slot_aziz}", json={
    "day": "Seshanba", "time": t1, "room": "1/8", "hours": 1
})
check("Dars muvaffaqiyatli ko'chirildi", r.status_code == 200)

moved = db.get_slot(slot_aziz)
check("Kun/vaqt/xona bazada haqiqatan o'zgardi",
      moved[3] == "Seshanba" and moved[4] == t1 and moved[5] == "1/8")

students = db.get_slot_students(slot_aziz)
cms = db.get_slot_concertmasters(slot_aziz)
check("O'quvchi joyida qoldi", any(s[1] == "Olimov Sardor" for s in students))
check("Jo'rnavoz joyida qoldi", "Aliyev Bobur" in cms)

# 2. AYNI joyiga saqlash - dars o'zi bilan to'qnashmasligi kerak
r = client.patch(f"/api/teacher/slots/{slot_aziz}", json={
    "day": "Seshanba", "time": t1, "room": "1/8", "hours": 1
})
check("Ayni joyiga saqlash ruxsat etiladi (200)", r.status_code == 200)

# 3. Yakshanba
r = client.patch(f"/api/teacher/slots/{slot_aziz}", json={
    "day": "Yakshanba", "time": t3, "room": "1/5", "hours": 1
})
check("Yakshanba - 400", r.status_code == 400)

# 4. Tushlik vaqti (12:10)
r = client.patch(f"/api/teacher/slots/{slot_aziz}", json={
    "day": "Chorshanba", "time": "12:10", "room": "1/5", "hours": 1
})
check("Tushlik vaqtiga dars qo'yib bo'lmaydi - 400", r.status_code == 400)

# 5. Ro'yxatda yo'q xona
r = client.patch(f"/api/teacher/slots/{slot_aziz}", json={
    "day": "Chorshanba", "time": t4, "room": "99/99", "hours": 1
})
check("Noma'lum xona - 400", r.status_code == 400)

# 6. Noto'g'ri davomiylik
r = client.patch(f"/api/teacher/slots/{slot_aziz}", json={
    "day": "Chorshanba", "time": t4, "room": "1/5", "hours": 77
})
check("Noto'g'ri davomiylik (77) - 400", r.status_code == 400)

# 7. Eng qisqa davomiylik (0.5 soat)
r = client.patch(f"/api/teacher/slots/{slot_aziz}", json={
    "day": "Chorshanba", "time": th1, "room": "1/5", "hours": 0.5
})
check("Eng qisqa davomiylik (0.5) qabul qilinadi - 200", r.status_code == 200)

# 8. O'sha o'qituvchining boshqa darsi ustiga surish
r = client.patch(f"/api/teacher/slots/{slot_aziz}", json={
    "day": "Dushanba", "time": t2, "room": "1/8", "hours": 1
})
check("O'z darsining ustiga surish - 409", r.status_code == 409)

# 9. Boshqa o'qituvchi band qilgan xonaga ko'chirish
r = client.patch(f"/api/teacher/slots/{slot_aziz}", json={
    "day": "Dushanba", "time": t3, "room": "1/8", "hours": 1
})
check("Band qilingan xonaga surish - 409", r.status_code == 409)

# 10. BEGONA o'qituvchining darsini tahrirlash
r = client.patch(f"/api/teacher/slots/{slot_bobur}", json={
    "day": "Payshanba", "time": t3, "room": "1/5", "hours": 1
})
check("Boshqa o'qituvchi darsini tahrirlash - 404", r.status_code == 404)

# 11. Mavjud bo'lmagan slot id
r = client.patch(f"/api/teacher/slots/999999", json={
    "day": "Payshanba", "time": t3, "room": "1/5", "hours": 1
})
check("Mavjud bo'lmagan slot - 404", r.status_code == 404)

# 12. can_manage_schedule huquqi yo'q o'qituvchi
db.toggle_teacher_permission("Karimov Aziz", "can_manage_schedule")
r = client.patch(f"/api/teacher/slots/{slot_aziz}", json={
    "day": "Juma", "time": t1, "room": "1/5", "hours": 1
})
check("can_manage_schedule huquqisiz - 403", r.status_code == 403)
db.toggle_teacher_permission("Karimov Aziz", "can_manage_schedule")

print()
for line in ok:
    print("  OK   " + line)

for line in bad:
    print("  XATO " + line)

print()
print(str(len(ok)) + " ta o'tdi, " + str(len(bad)) + " ta xato")

sys.exit(1 if bad else 0)
