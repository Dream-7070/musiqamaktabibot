import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import database as db

# O`z ajratilgan bazasi - haqiqiy school.db ga tegmaydi
os.makedirs(os.path.join(os.path.dirname(os.path.abspath(__file__)), "_tmp"), exist_ok=True)
db.DB_NAME = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          "_tmp", "concurrent.db")
db.create_tables()
db.migrate_schema()

tag = sys.argv[1]
errors = 0
ok = 0

for i in range(40):
    try:
        sid = db.create_slot("ZZTest " + tag, "Solfedjio", "Dushanba", "0" + str(i % 9) + ":00", "R" + tag)
        db.add_student_to_slot(sid, "Bola" + str(i), "ZZTest " + tag)
        db.get_teacher_slots("ZZTest " + tag)
        ok += 1
    except Exception as e:
        errors += 1
        print(tag, "XATO:", e)

print(tag, "-> muvaffaqiyatli:", ok, "| xato:", errors)
