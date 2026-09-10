# -*- coding: utf-8 -*-
"""
Bir martalik tozalash: o'chirilgan darslardan qolgan yetim yozuvlar.

Ilgari `delete_slot` `slot_concertmasters` jadvalini tozalamasdi -
dars o'chsa ham jo'rnavoz yozuvi bazada qolib ketardi. Kod
tuzatildi, lekin jonli bazadagi eski yetimlar o'z-o'zidan
yo'qolmaydi. Shu skript ularni bir marta tozalaydi.

    python scripts/cleanup_orphans.py            # faqat sanaydi
    python scripts/cleanup_orphans.py --apply    # o'chiradi

Serverda ishga tushirishdan oldin zaxira oling
(`services/backup.py` avtomatik zaxirasi bor).
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import database as db


ORPHAN_QUERIES = [
    (
        "slot_concertmasters",
        """
        DELETE FROM slot_concertmasters
        WHERE slot_id NOT IN (SELECT id FROM schedule_slots)
        """,
        """
        SELECT COUNT(*) FROM slot_concertmasters
        WHERE slot_id NOT IN (SELECT id FROM schedule_slots)
        """
    ),
    (
        "schedule_slot_students",
        """
        DELETE FROM schedule_slot_students
        WHERE slot_id NOT IN (SELECT id FROM schedule_slots)
        """,
        """
        SELECT COUNT(*) FROM schedule_slot_students
        WHERE slot_id NOT IN (SELECT id FROM schedule_slots)
        """
    ),
]


def main():

    apply = "--apply" in sys.argv

    conn = db.connect()

    total = 0

    for table, delete_sql, count_sql in ORPHAN_QUERIES:

        count = conn.execute(count_sql).fetchone()[0]

        total += count

        print(table + ": " + str(count) + " ta yetim qator")

        if count and apply:

            conn.execute(delete_sql)

    if apply:

        conn.commit()

    conn.close()

    print()

    if not total:
        print("Baza toza - tozalash kerak emas.")

    elif apply:
        print(str(total) + " ta qator o'chirildi.")

    else:
        print("O'chirish uchun: python scripts/cleanup_orphans.py --apply")

    return 0


if __name__ == "__main__":
    sys.exit(main())
