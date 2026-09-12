# -*- coding: utf-8 -*-
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import database as db

os.makedirs(os.path.join(os.path.dirname(os.path.abspath(__file__)), "_tmp"), exist_ok=True)
DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_tmp", "test_schedule_planner_group.db")

if os.path.exists(DB):
    os.remove(DB)

db.DB_NAME = DB
db.create_tables()
if hasattr(db, 'migrate_schema'):
    db.migrate_schema()
else:
    import db.schema
    if hasattr(db.schema, 'migrate_schema'):
        db.schema.migrate_schema()

# Add some rooms just in case, though test_schedule_planner doesn't seem to
try:
    conn = db.get_db_connection()
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO rooms (name) VALUES ('Xona1'), ('Xona2')")
    conn.commit()
    conn.close()
except:
    pass

from services.schedule_planner import generate_variants
from database import DAYS_OF_WEEK

ok, bad = [], []

def check(label, cond):
    (ok if cond else bad).append(label)

def time_to_min(t):
    h, m = t.split(":")
    return int(h) * 60 + int(m)

def overlap(l1, l2):
    if l1["day"] != l2["day"]: return False
    start1 = time_to_min(l1["start"])
    end1 = time_to_min(l1["end"])
    start2 = time_to_min(l2["start"])
    end2 = time_to_min(l2["end"])
    return start1 < end2 and start2 < end1

# 1. Guruh a'zosi yakka darsi bilan to'qnashmasin
lessons_1 = [
    {"who": "Aliyev Ali", "duration_minutes": 45, "is_group": False, "members": None},
    {"who": "Guruh 1", "duration_minutes": 45, "is_group": True, "members": [("Aliyev Ali", "1")]}
]
v1 = generate_variants("Teacher1", lessons_1, ["Juma"], ["Xona1"])
if v1 and len(v1[0]["lessons"]) == 2:
    l1 = v1[0]["lessons"][0]
    l2 = v1[0]["lessons"][1]
    check("1. Guruh va yakka dars ustma-ust tushmasin", not overlap(l1, l2))
else:
    check("1. Guruh va yakka dars ustma-ust tushmasin", False)

# 2. Umumiy a'zosi bor ikki guruh bir vaqtga tushmasin
lessons_2 = [
    {"who": "Guruh A", "duration_minutes": 45, "is_group": True, "members": [("Aliyev Ali", "1"), ("B", "1")]},
    {"who": "Guruh B", "duration_minutes": 45, "is_group": True, "members": [("Aliyev Ali", "1"), ("C", "1")]}
]
v2 = generate_variants("Teacher2", lessons_2, ["Dushanba"], ["Xona1", "Xona2"])
if v2 and len(v2[0]["lessons"]) == 2:
    l1 = v2[0]["lessons"][0]
    l2 = v2[0]["lessons"][1]
    check("2. Umumiy a'zosi bor 2 guruh ustma-ust tushmasin", not overlap(l1, l2))
else:
    check("2. Umumiy a'zosi bor 2 guruh ustma-ust tushmasin", False)


# 3. Umumiy a'zosi YO'Q ikki guruh bir vaqtda bo'la oladi
lessons_3 = [
    {"who": "Guruh X", "duration_minutes": 45, "is_group": True, "members": [("A", "1")]},
    {"who": "Guruh Y", "duration_minutes": 45, "is_group": True, "members": [("B", "1")]}
]
# To force them to be at the same time, we need to pass rooms
v3 = generate_variants("Teacher3", lessons_3, ["Dushanba"], ["Xona1", "Xona2"])
if v3 and len(v3[0]["lessons"]) == 2:
    # Just need to check they are both placed successfully.
    # Actually, they might be placed one after another, but they shouldn't conflict.
    check("3. Umumiy a'zosi yo'q guruhlar joylashtiriladi", len(v3[0]["unplaced"]) == 0)
else:
    check("3. Umumiy a'zosi yo'q guruhlar joylashtiriladi", False)


print()
for line in ok:
    print("  OK   " + line)

for line in bad:
    print("  XATO " + line)

print()
print(str(len(ok)) + " ta o'tdi, " + str(len(bad)) + " ta xato")

sys.exit(1 if bad else 0)
