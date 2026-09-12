# -*- coding: utf-8 -*-
"""
O'qituvchi uchun bir nechta to'qnashuvsiz haftalik jadval varianti taklif qilish.

Bu modul bazaga HECH NARSA YOZMAYDI - faqat `db/schedule.py` dagi mavjud
tekshiruv funksiyalarini (o'qituvchi/o'quvchi/xona bandligi) ishlatib,
darslarni kun-vaqt-xonaga joylashtirishga urinadi va bir nechta muqobil
variant qaytaradi. Tanlangan variantni bazaga yozish (`create_slot`)
chaqiruvchi tomonda, keyingi bosqichda bajariladi.

Nega bu yerda: admin/o'qituvchi har bir darsni qo'lda joy-joyiga qo'yish
o'rniga, faqat kim tushlikgacha/tushlikdan keyin ekanini va qaysi kunlar/
xonalar bo'shligini aytadi - qolganini shu modul hisoblaydi.
"""

from database import (
    DAYS_OF_WEEK,
    LUNCH_START, LUNCH_END,
    available_lesson_times,
    find_teacher_conflict,
    find_student_conflict,
    get_room_availability,
)


def _parse_time_to_minutes(time_str):
    """"08:20" -> 500"""

    hour, minute = time_str.split(":")

    return int(hour) * 60 + int(minute)


def _get_candidate_slots(lesson, allowed_days, preferred_rooms):
    """
    Bitta dars uchun mumkin bo'lgan (kun, vaqt, xona) nomzodlari.

    Tushlikkacha/tushlikdan keyin cheklovi shu yerda filtrlanadi.
    Afzal xonalar ustuvor - lekin ular band bo'lsa, qolgan bo'sh
    xonalar ham nomzod bo'lib qoladi.
    """

    candidates = []

    duration = lesson.get("duration_minutes", 45)
    shift = lesson.get("shift")

    for day in allowed_days:

        if day not in DAYS_OF_WEEK:
            continue

        for start_str, end_str in available_lesson_times(duration):

            start_min = _parse_time_to_minutes(start_str)
            end_min = _parse_time_to_minutes(end_str)

            if shift == "tushlikgacha" and end_min > LUNCH_START:
                continue

            if shift == "tushlikdan_keyin" and start_min < LUNCH_END:
                continue

            rooms_info = get_room_availability(day, start_str, duration)

            free_rooms = [r["room"] for r in rooms_info if not r["busy"]]

            if not free_rooms:
                continue

            chosen_rooms = (
                [room for room in preferred_rooms if room in free_rooms]
                if preferred_rooms else []
            )

            if not chosen_rooms:
                chosen_rooms = free_rooms

            for room in chosen_rooms:

                candidates.append({
                    "day": day,
                    "start": start_str,
                    "end": end_str,
                    "room": room,
                    "duration_minutes": duration,
                })

    return candidates


def _conflicts_within_variant(variant_lessons, candidate, lesson):
    """
    Shu variant ichida allaqachon joylashtirilgan darslar bilan
    to'qnashadimi: bir xil o'quvchi/guruh vaqti ustma-ust tushsa,
    yoki bir xil kun+vaqt+xona ikkinchi marta band qilinsa.
    """

    c_start = _parse_time_to_minutes(candidate["start"])
    c_end = _parse_time_to_minutes(candidate["end"])

    for placed in variant_lessons:

        if placed["day"] != candidate["day"]:
            continue

        p_start = _parse_time_to_minutes(placed["start"])
        p_end = _parse_time_to_minutes(placed["end"])

        overlaps = c_start < p_end and p_start < c_end

        if not overlaps:
            continue

        if placed["who"] == lesson["who"]:
            return True

        if placed["room"] == candidate["room"]:
            return True

    return False


def _try_build_variant(teacher, lessons, allowed_days, preferred_rooms, offset):
    """
    Barcha darslarni bittalab joylashtirishga urinadi.

    `offset` - har chaqiriqda nomzodlar ro'yxatini boshqa nuqtadan
    boshlab aylantiradi, shu bilan bir xil kirish ma'lumotidan turli
    (lekin barqaror, tasodifsiz) variantlar hosil bo'ladi.
    """

    variant_lessons = []
    unplaced = []

    kun_yuki = {}
    kun_egalari = {}
    allowed_days_list = list(allowed_days)

    for index, lesson in enumerate(lessons):

        candidates = _get_candidate_slots(lesson, allowed_days, preferred_rooms)

        # Nomzodlar kun bo'yicha ketma-ket tuzilgan: avval butun
        # Dushanba, keyin Seshanba... Ro'yxatdan shunchaki birinchi
        # mosini olsak, Dushanba to'lmaguncha hamma dars o'sha kunga
        # tiqiladi - aynan shu xato bo'lgan edi. Shuning uchun har
        # darsdan oldin nomzodlarni qayta saralaymiz.

        if candidates:

            shift_amt = (offset + index) % len(allowed_days_list)
            rotated_days = allowed_days_list[shift_amt:] + allowed_days_list[:shift_amt]
            day_order = {day: i for i, day in enumerate(rotated_days)}

            def candidate_sort_key(c):

                day = c["day"]

                # 1) bolaning o'sha kunda darsi bo'lsa - oxirgi o'ringa
                #    (haftalik darslari har xil kunga tarqalsin)
                # 2) kam yuklangan kun oldinga
                # 3) kunlar aylantirilgan tartibda - shu variantlarni
                #    bir-biridan farqli qiladi

                return (
                    1 if lesson["who"] in kun_egalari.get(day, set()) else 0,
                    kun_yuki.get(day, 0),
                    day_order.get(day, 999)
                )

            # sort barqaror - teng kunlar ichida vaqt va xona tartibi saqlanadi

            candidates.sort(key=candidate_sort_key)

        placed = False

        for candidate in candidates:

            if _conflicts_within_variant(variant_lessons, candidate, lesson):
                continue

            if find_teacher_conflict(
                teacher, candidate["day"], candidate["start"],
                candidate["duration_minutes"]
            ):
                continue

            student_teacher = lesson.get("student_teacher")

            if student_teacher and find_student_conflict(
                lesson["who"], student_teacher, candidate["day"],
                candidate["start"], candidate["duration_minutes"]
            ):
                continue

            variant_lessons.append({
                "who": lesson["who"],
                "subject": lesson.get("subject"),
                "class_name": lesson.get("class_name"),
                "is_group": lesson.get("is_group", False),
                "members": lesson.get("members"),
                "day": candidate["day"],
                "start": candidate["start"],
                "end": candidate["end"],
                "room": candidate["room"],
            })

            c_day = candidate["day"]
            kun_yuki[c_day] = kun_yuki.get(c_day, 0) + 1
            if c_day not in kun_egalari:
                kun_egalari[c_day] = set()
            kun_egalari[c_day].add(lesson["who"])

            placed = True

            break

        if not placed:
            unplaced.append(lesson)

    return {
        "complete": not unplaced,
        "lessons": variant_lessons,
        "unplaced": unplaced,
    }


def generate_variants(teacher, lessons, allowed_days, preferred_rooms=None,
                       max_variants=3):
    """
    `lessons` uchun eng ko'pi bilan `max_variants` ta to'qnashuvsiz
    haftalik variant qaytaradi (qarang: modul docstring'i).

    Cheklovi ko'proq darslar (shift belgilanganlar) avval joylashtiriladi -
    ular uchun bo'sh joy kamroq, keyinroq qolsa topish qiyinlashadi.
    """

    sorted_lessons = sorted(lessons, key=lambda item: 0 if item.get("shift") else 1)

    variants = []
    best_incomplete = None

    max_attempts = max_variants * 5

    for offset in range(max_attempts):

        variant = _try_build_variant(
            teacher, sorted_lessons, allowed_days, preferred_rooms, offset
        )

        if any(existing["lessons"] == variant["lessons"] for existing in variants):
            continue

        if variant["complete"]:
            variants.append(variant)
        elif (best_incomplete is None
              or len(variant["lessons"]) > len(best_incomplete["lessons"])):
            best_incomplete = variant

        if len(variants) >= max_variants:
            break

    if not variants and best_incomplete:
        variants.append(best_incomplete)

    return variants
