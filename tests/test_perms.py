# -*- coding: utf-8 -*-
"""Huquqlar, o'zgarishlar tarixi, arxiv, ota-ona eslatmasi."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import database as db

os.makedirs(os.path.join(os.path.dirname(os.path.abspath(__file__)), "_tmp"), exist_ok=True)
DB = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                  "_tmp", "test_perms.db")

if os.path.exists(DB):
    os.remove(DB)

db.DB_NAME = DB
db.create_tables()
db.migrate_schema()

ok, bad = [], []


def check(label, cond):
    (ok if cond else bad).append(label)


db.add_teacher("Karimov A.", "Fortepiano")
db.add_teacher("Berdiqulov I.", "Nazariy")
db.add_teacher("Ismoilova N.", "Fortepiano")


# ==========================
# 1. HUQUQLAR
# ==========================

p = db.get_teacher_permissions("Karimov A.")
check("belgilanmagan o'qituvchida hamma huquq ochiq",
      p["can_add_students"] and p["can_manage_schedule"]
      and p["can_be_concertmaster"] and p["type"] is None)

db.set_teacher_type("Karimov A.", "mutaxassislik")
p = db.get_teacher_permissions("Karimov A.")
check("mutaxassislik: hammasi ochiq",
      p["can_add_students"] and p["can_manage_schedule"] and p["can_be_concertmaster"])

db.set_teacher_type("Berdiqulov I.", "umumiy")
p = db.get_teacher_permissions("Berdiqulov I.")
check("umumiy fan: o'quvchi qo'sha olmaydi",
      not p["can_add_students"])
check("umumiy fan: jadval tuza oladi",
      p["can_manage_schedule"])
check("umumiy fan: jo'rnavozlik qila olmaydi",
      not p["can_be_concertmaster"])

db.set_teacher_type("Ismoilova N.", "jornavoz")
p = db.get_teacher_permissions("Ismoilova N.")
check("jo'rnavoz: faqat jo'rnavozlik",
      not p["can_add_students"] and not p["can_manage_schedule"]
      and p["can_be_concertmaster"])

check("can() yordamchisi", db.can("Berdiqulov I.", "can_add_students") is False)

# alohida huquqni yoqish (pianinochi ham mutaxassis, ham jo'rnavoz)
db.toggle_teacher_permission("Berdiqulov I.", "can_be_concertmaster")
check("alohida huquq yoqildi",
      db.can("Berdiqulov I.", "can_be_concertmaster") is True)
check("turi saqlanib qoldi",
      db.get_teacher_permissions("Berdiqulov I.")["type"] == "umumiy")

check("noto'g'ri tur rad etiladi", db.set_teacher_type("Karimov A.", "yoq") is False)
check("noto'g'ri huquq rad etiladi",
      db.toggle_teacher_permission("Karimov A.", "can_fly") is None)

db.add_teacher("Yangi O.", "Torli")
c = db.connect()
c.execute("UPDATE teachers SET status='approved' WHERE name IN ('Yangi O.','Karimov A.')")
c.commit()
c.close()
without = [n for n, _ in db.get_teachers_without_type()]
check("turi belgilanmaganlar ro'yxati: " + str(without),
      without == ["Yangi O."])


# ==========================
# 2. O'ZGARISHLAR TARIXI
# ==========================

db.log_action("Karimov A.", "o'quvchi qo'shdi", "Ali Valiyev", "badal: 123 600 so'm")
db.log_action("Karimov A.", "oylik badalni o'zgartirdi", "Ali Valiyev", "82 400 so'm")
db.log_action("566206701", "huquqni o'zgartirdi", "Berdiqulov I.",
              "jo'rnavozlik: ha", actor_role="admin")

rows = db.get_audit_log()
check("3 ta yozuv, yangisi birinchi: " + str(len(rows)),
      len(rows) == 3 and rows[0][3] == "huquqni o'zgartirdi")

check("o'quvchi ismi bo'yicha qidiruv",
      len(db.get_audit_log(query="Ali Valiyev")) == 2)

check("o'qituvchi ismi bo'yicha qidiruv",
      len(db.get_audit_log(query="Karimov")) == 2)

check("yozuvda rol bor", rows[0][2] == "admin")


# ==========================
# 3. ARXIV
# ==========================

db.add_student("Karimov A.", "Ali Valiyev", "2015-01-01", "I-TV 1111111", "3", 123600)
db.add_student("Karimov A.", "Zebo Karimova", "2015-02-02", "I-TV 2222222", "3", 82400)

check("boshida 2 ta o'quvchi", len(db.get_students("Karimov A.")) == 2)

slot = db.create_slot("Karimov A.", "Mutaxassislik", "Dushanba", "15:00", "12")
db.add_student_to_slot(slot, "Zebo Karimova", "Karimov A.")

check("arxivga olindi",
      db.archive_student("Karimov A.", "Zebo Karimova", "maktabdan ketdi"))

check("ro'yxatdan yo'qoldi",
      db.get_students("Karimov A.") == ["Ali Valiyev"])

check("qidiruvda chiqmaydi",
      db.search_students("Zebo") == [])

check("qarzdorlar ro'yxatida yo'q",
      "Zebo Karimova" not in
      [s for s, _ in db.get_unpaid_students("Karimov A.", "2026-09")])

check("direktor hisobotida yo'q",
      "Zebo Karimova" not in [r[2] for r in db.get_monthly_debt_rows("2026-09")])

check("ota-ona ITV orqali ulay olmaydi",
      db.find_students_by_metrika("I-TV 2222222") == [])

check("is_archived to'g'ri",
      db.is_archived("Karimov A.", "Zebo Karimova")
      and not db.is_archived("Karimov A.", "Ali Valiyev"))

arch = db.get_archived_students()
check("arxiv ro'yxatida sabab bilan: " + str(arch),
      len(arch) == 1 and arch[0][3] == "maktabdan ketdi")

check("to'lov tarixi uchun yozuv saqlanib qoldi",
      db.get_student_info("Zebo Karimova", "Karimov A.") is not None)

check("arxivdan qaytarildi",
      db.restore_student("Karimov A.", "Zebo Karimova"))

check("yana ro'yxatda",
      len(db.get_students("Karimov A.")) == 2)

check("arxiv bo'shadi", db.get_archived_students() == [])


# ==========================
# 4. OTA-ONA ALOQASI
# ==========================

db.add_parent(999001, "Valiyev Otabek", "+998901234567")
parent = db.get_parent(999001)
db.link_parent_student(parent[0], "Karimov A.", "Ali Valiyev")

parents = db.get_parents_of_student("Karimov A.", "Ali Valiyev")
check("ota-ona topildi: " + str(parents),
      len(parents) == 1 and parents[0][0] == 999001)

check("ulanmagan o'quvchining ota-onasi yo'q",
      db.get_parents_of_student("Karimov A.", "Zebo Karimova") == [])

from services.reminders import _month_name, _money
check("oy nomi: " + _month_name("2026-09"),
      _month_name("2026-09") == "2026-yil sentabr")
check("summa: " + _money(123600), _money(123600) == "123 600")

# imtiyozli o'quvchi eslatmaga tushmasligi kerak
db.update_student_field("Karimov A.", "Ali Valiyev", "monthly_fee", db.FEE_PRIVILEGED)
check("imtiyozli ota-onasiga eslatma ketmaydi",
      "Ali Valiyev" not in
      [s for s, _ in db.get_unpaid_students("Karimov A.", "2026-09")])


# ==========================
print()
for line in ok:
    print("  OK   " + line)
for line in bad:
    print("  XATO " + line)
print()
print(str(len(ok)) + " ta o'tdi, " + str(len(bad)) + " ta xato")

sys.exit(1 if bad else 0)
