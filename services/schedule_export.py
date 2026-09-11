# -*- coding: utf-8 -*-
"""
O'qituvchi jadval variantlarini (`schedule_planner.generate_variants`
natijasini) Excel faylga yozish.

Bazaga hech narsa yozilmaydi - fayl faqat ko'rsatish va qayta yuklash
uchun. O'qituvchi variantlardan birini tanlaydi, kerak bo'lsa
katakchani qo'lda tuzatadi, so'ng faylni «📥 Jadvalni Excel'dan
yuklash» oqimiga (`handlers/schedule_excel.py`,
`services/schedule_import.py`) qayta yuboradi - o'sha parser bu
faylni tushunadigan qilib yozamiz: "O'qituvchisi:" qatori, F.I.O/Sinfi
va 6 ta kun ustuni, fan bloki sarlavhalari, guruh sarlavhalari.

Nega rasmiy shtamp shablon emas: parser shtampga qaramaydi - faqat
kalit so'zlarni qidiradi. Muhimi - moslik, tashqi ko'rinish emas.
"""

import re

import openpyxl
from openpyxl.styles import Font
from openpyxl.utils import get_column_letter


DAY_COLUMNS = {
    "Dushanba": 4,
    "Seshanba": 5,
    "Chorshanba": 6,
    "Payshanba": 7,
    "Juma": 8,
    "Shanba": 9,
}


def variant_filename(teacher, index):
    """O'qituvchi ismidan fayl tizimiga yaroqli nom yasaydi."""

    safe_name = re.sub(r'[\\/:*?"<>|]', "_", teacher).replace(" ", "_")

    return safe_name + "_variant_" + str(index) + ".xlsx"


def _group_by_subject(lessons):
    """
    Darslarni fan bo'yicha, ichida `who` bo'yicha guruhlaydi - ikkalasi
    ham birinchi uchragan tartibda (dict Python 3.7+ da tartibni saqlaydi).
    """

    by_subject = {}

    for lesson in lessons:

        subject = lesson.get("subject") or "Noma'lum fan"
        who = lesson.get("who") or "Noma'lum"

        by_subject.setdefault(subject, {})

        entry = by_subject[subject].setdefault(who, {
            "is_group": lesson.get("is_group", False),
            "class_name": lesson.get("class_name") or "",
            "members": lesson.get("members"),
            "times": {},
        })

        day = lesson.get("day")

        if day and lesson.get("start") and lesson.get("end"):

            entry["times"][day] = "{}-{} ({})".format(
                lesson["start"], lesson["end"], lesson.get("room") or "?"
            )

    return by_subject


def _write_times(ws, row, times):

    for day, time_text in times.items():

        column = DAY_COLUMNS.get(day)

        if column:
            ws.cell(row=row, column=column, value=time_text)


def _write_sheet(ws, teacher, variant):

    ws["A1"] = "O'qituvchisi " + teacher

    headers = ["F.I.O", "Sinfi"] + list(DAY_COLUMNS)

    for column, text in enumerate(headers, start=2):

        cell = ws.cell(row=4, column=column, value=text)
        cell.font = Font(bold=True)

    ws.column_dimensions["B"].width = 28
    ws.column_dimensions["C"].width = 8

    for column in range(4, 4 + len(DAY_COLUMNS)):
        ws.column_dimensions[get_column_letter(column)].width = 16

    by_subject = _group_by_subject(variant.get("lessons") or [])

    row = 5

    for subject, who_map in by_subject.items():

        header_cell = ws.cell(row=row, column=2, value=subject)
        header_cell.font = Font(bold=True)

        row += 1

        for who, data in who_map.items():

            ws.cell(row=row, column=2, value=who)

            members = data["members"] if data["is_group"] else None

            if not members:

                if not data["is_group"] and data["class_name"]:
                    ws.cell(row=row, column=3, value=data["class_name"])

                _write_times(ws, row, data["times"])

                row += 1

                continue

            # Guruh - a'zolar alohida qatorda, vaqt faqat birinchisida
            # (aks holda parser bir darsni har a'zoga alohida hisoblab
            # qo'yadi - guruh darsi umumiy, a'zolarga bo'linmaydi)

            row += 1

            for index, (member_name, member_class) in enumerate(members):

                ws.cell(row=row, column=2, value=member_name)

                if member_class:
                    ws.cell(row=row, column=3, value=member_class)

                if index == 0:
                    _write_times(ws, row, data["times"])

                row += 1

        row += 1

    unplaced = variant.get("unplaced") or []

    if not variant.get("complete", True) and unplaced:

        row += 1

        warn_cell = ws.cell(row=row, column=2, value="❓ Joylashtirilmadi:")
        warn_cell.font = Font(bold=True, color="FF0000")

        row += 1

        for lesson in unplaced:

            text = "{} ({})".format(
                lesson.get("who") or "?", lesson.get("subject") or "?"
            )

            cell = ws.cell(row=row, column=2, value=text)
            cell.font = Font(color="FF0000")

            row += 1


def export_variant_to_excel(teacher, variant, out_path, index=1):
    """
    BITTA variantni bitta varaqli faylga yozadi. Bazaga tegilmaydi.

    Nega bitta varaq: import oqimi (`services/schedule_import.py`)
    faylning faqat BIRINCHI varag'ini o'qiydi - o'qituvchi bitta
    chorak jadvalini bitta faylda yuboradi degan qoidaga ko'ra.
    Ilgari hamma variant bitta faylning alohida varaqlarida
    yozilardi va o'qituvchi 2-variantni tanlab qayta yuborsa,
    bot jimgina 1-variantni olardi.

    Shuning uchun har bir variant alohida fayl bo'lib boradi -
    o'qituvchi yoqqanini qayta yuboradi, tanlash esa fayl
    tanlashning o'ziga aylanadi.
    """

    workbook = openpyxl.Workbook()

    ws = workbook.active

    title = "Variant " + str(index)

    if not variant.get("complete", True):
        title += " (to'liq emas)"

    ws.title = title

    _write_sheet(ws, teacher, variant)

    workbook.save(out_path)
