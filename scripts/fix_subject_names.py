# -*- coding: utf-8 -*-
"""
Bir martalik tuzatish: o'qituvchilar xato yozib qo'shgan fan nomlari.

Mini App ilgari o'qituvchiga 2026-rejadagi fanlarni ko'rsatmasdi -
faqat umumiy 8 ta nomni. Shuning uchun o'qituvchilar kerakli fanni
o'zlari yozib qo'shgan va ko'pincha boshqacha yozilgan:

    "notani varaqdan uqish"  o'rniga  "Notani varaqdan o'qish"

Bu fanlarga haqiqiy darslar biriktirilgan, shuning uchun ularni
shunchaki o'chirib bo'lmaydi. Skript ularni topadi va nomini
rejadagi to'g'ri nomga keltiradi (darslari bilan birga).

Ishlatish:

    python scripts/fix_subject_names.py              # faqat ko'rsatadi
    python scripts/fix_subject_names.py --apply      # o'zgartiradi
    python scripts/fix_subject_names.py --db nusxa.db  # boshqa bazada sinash

DIQQAT: --apply dan oldin zaxira oling. services/backup.py har 6
soatda avtomatik nusxa saqlaydi, lekin oxirgi o'zgarishlar undan
keyin bo'lgan bo'lishi mumkin. Avval --db bilan nusxada sinab
ko'rish eng xavfsiz yo'l.
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import database as db

from data.curriculum import department_subjects

from db.uzbek import normalize


# ==========================
# TAHLIL
# ==========================


def collect():
    """
    Bazani tekshiradi va uchta ro'yxat qaytaradi:

      tuzatiladi  - {o'qituvchi: [(subject_id, xato_nom, togri_nom, darslar), ...]}
      tegilmaydi  - [(o'qituvchi, nom), ...]  rejada yo'q, shaxsiy fanlar
      tekshirilmadi - [o'qituvchi, ...]       bo'limi belgilanmagan
    """

    conn = db.connect()
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM teachers ORDER BY name")

    teachers = [row[0] for row in cursor.fetchall()]

    conn.close()

    tuzatiladi = {}
    tegilmaydi = []
    tekshirilmadi = []

    for teacher in teachers:

        department = db.get_department_for_teacher(teacher)

        if not department:
            # Bo'limsiz o'qituvchining rejasi yo'q - solishtirish
            # uchun manba topilmaydi, shuning uchun tegilmaydi.
            tekshirilmadi.append(teacher)
            continue

        plan = [name for name, _ in department_subjects(department)]

        for subject_id, name, _lesson_type in db.get_own_subjects(teacher):

            mos = [p for p in plan if normalize(p) == normalize(name)]

            if not mos:
                # Rejada umuman yo'q - o'qituvchining haqiqiy
                # shaxsiy fani. Tegmaymiz.
                tegilmaydi.append((teacher, name))
                continue

            if len(mos) > 1:
                # Ikki xil reja fani bir xil "kanonik" shaklga
                # tushdi - qaysi biri kerakligini bilib bo'lmaydi,
                # avtomatik tuzatish xavfli.
                print(
                    "  OGOHLANTIRISH: " + teacher + " - '" + name
                    + "' bir nechta reja faniga mos keldi ("
                    + ", ".join(mos) + "). Qo'lda hal qiling."
                )
                continue

            togri = mos[0]

            if togri == name:
                # Yozilishi allaqachon to'g'ri
                continue

            tuzatiladi.setdefault(teacher, []).append(
                (subject_id, name, togri,
                 db.count_slots_using_subject(teacher, name))
            )

    return tuzatiladi, tegilmaydi, tekshirilmadi


# ==========================
# HISOBOT
# ==========================


def report(tuzatiladi, tegilmaydi, tekshirilmadi):

    if tuzatiladi:

        print("TUZATILADIGAN FANLAR:")
        print()

        fanlar = 0
        darslar = 0

        for teacher in sorted(tuzatiladi):

            department = db.get_department_for_teacher(teacher)

            print("  " + teacher + "  (" + str(department) + ")")

            for _subject_id, name, togri, count in tuzatiladi[teacher]:

                fanlar += 1
                darslar += count

                print(
                    '     "' + name + '"  ->  "' + togri + '"'
                    + "      darslar: " + str(count)
                )

            print()

        print(
            "JAMI: " + str(len(tuzatiladi)) + " ta o'qituvchi, "
            + str(fanlar) + " ta fan, " + str(darslar) + " ta dars."
        )

    else:
        print("Tuzatish kerak bo'lgan fan nomi topilmadi.")

    print()

    if tegilmaydi:

        print("O'ZGARISHSIZ QOLADI (rejada yo'q, shaxsiy fanlar):")

        for teacher, name in tegilmaydi:
            print("  " + teacher + ": " + name)

        print()

    if tekshirilmadi:

        print("TEKSHIRIB BO'LMADI (bo'limi belgilanmagan o'qituvchilar):")

        for teacher in tekshirilmadi:
            print("  " + teacher)

        print()


# ==========================
# QO'LLASH
# ==========================


def apply_changes(tuzatiladi):
    """Har bir fanni alohida tuzatadi. Bittasi yiqilsa qolganlari davom etadi."""

    ok_count = 0
    xato_count = 0

    for teacher in sorted(tuzatiladi):

        for subject_id, name, togri, _count in tuzatiladi[teacher]:

            # 1) Oddiy holat: rejadagi nom `subjects` jadvalida yo'q.
            #    rename_subject darslarni ham o'zi ko'chiradi.

            ok, info = db.rename_subject(subject_id, teacher, togri)

            if ok:
                print("  [NOMI O'ZGARDI] " + teacher + ": '" + name
                      + "' -> '" + togri + "'")
                ok_count += 1
                continue

            # 2) To'g'ri nomli fan ALLAQACHON bor (umumiy yoki
            #    o'ziniki). Unda nom o'zgartirib bo'lmaydi -
            #    darslarni o'shanga ko'chirib, dublikatni o'chiramiz.

            if "allaqachon" in str(info).lower():

                conn = db.connect()
                cursor = conn.cursor()

                try:
                    cursor.execute(
                        "UPDATE schedule_slots SET subject=? "
                        "WHERE teacher=? AND subject=?",
                        (togri, teacher, name)
                    )

                    moved = cursor.rowcount

                    cursor.execute(
                        "DELETE FROM subjects WHERE id=? AND teacher=?",
                        (subject_id, teacher)
                    )

                    conn.commit()

                    print("  [BIRLASHTIRILDI] " + teacher + ": '" + name
                          + "' -> mavjud '" + togri + "' ga, "
                          + str(moved) + " ta dars ko'chdi")

                    ok_count += 1

                except Exception as err:

                    conn.rollback()

                    print("  [XATO] " + teacher + ": '" + name + "' - " + str(err))

                    xato_count += 1

                finally:
                    conn.close()

                continue

            # 3) Boshqa sabab

            print("  [XATO] " + teacher + ": '" + name + "' - " + str(info))

            xato_count += 1

    print()
    print("Tuzatildi: " + str(ok_count) + " ta, xato: " + str(xato_count) + " ta.")


# ==========================
# ASOSIY
# ==========================


def main():

    parser = argparse.ArgumentParser(
        description="Xato yozilgan fan nomlarini rejadagi nomga keltiradi"
    )

    parser.add_argument(
        "--apply", action="store_true",
        help="o'zgarishlarni bazaga yozadi (busiz faqat ko'rsatadi)"
    )

    parser.add_argument(
        "--db", metavar="YO'L",
        help="boshqa baza fayli - avval nusxada sinab ko'rish uchun"
    )

    args = parser.parse_args()

    if args.db:
        db.DB_NAME = args.db

    print("Baza: " + str(db.DB_NAME))
    print("-" * 60)

    tuzatiladi, tegilmaydi, tekshirilmadi = collect()

    report(tuzatiladi, tegilmaydi, tekshirilmadi)

    if not tuzatiladi:
        return

    print("-" * 60)

    if not args.apply:
        print("Hech narsa o'zgartirilmadi (sinov rejimi).")
        print()
        print("O'zgartirish uchun:")
        print("    python scripts/fix_subject_names.py --apply")
        print()
        print("Avval nusxada sinab ko'rish uchun:")
        print("    python scripts/fix_subject_names.py --db nusxa.db --apply")
        return

    print("O'ZGARISHLAR QO'LLANMOQDA...")
    print()

    apply_changes(tuzatiladi)


if __name__ == "__main__":
    main()
