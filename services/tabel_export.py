# -*- coding: utf-8 -*-
# ==========================
# services/tabel_export.py
# TABELNI EXCEL QILIB CHIQARISH
# ==========================
#
# Ustunlar va belgilar maktabning HAQIQIY tabel faylidan olingan
# (2026 varaqlari) - buxgalter ko'nikkan ko'rinish o'zgarmasin.
#
#   A  T/R
#   B  Tabel raqami
#   C  Xodimning familiyasi
#   D  Lavozimi
#   E  Stavka miqdori
#   F..AJ  1-31 kunlar
#   AK Ishlab berilgan kunlar
#   AL Ishlab berilgan soatlar
#   AM Mexnatga layoqatsizlik (K)
#   AN Mexnat ta'tili (M)
#   AO Ish haqi saqlanmagan (O)
#   AP Hizmat safari (X)
#   AQ Sababsiz ishda bo'lmagan (Y)
#   AR FMS
#   AT/AU  izoh (belgilar lug'ati)
# ==========================


from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, Side
from openpyxl.utils import get_column_letter

from database import (
    days_in_month,
    month_row,
    get_tech_staff,
    TABEL_MARKS,
)


OYLAR = [
    "Yanvar", "Fevral", "Mart", "Aprel", "May", "Iyun",
    "Iyul", "Avgust", "Sentyabr", "Oktyabr", "Noyabr", "Dekabr",
]


# Kunlar F ustunidan boshlanadi (6-ustun)
FIRST_DAY_COLUMN = 6

HEADER_ROW = 13
DAYS_ROW = 14
FIRST_DATA_ROW = 15


def tabel_filename(year, month):

    return "tabel_" + OYLAR[month - 1] + "_" + str(year) + ".xlsx"


def _yozuv(ws, row, column, value, bold=False, center=True):

    cell = ws.cell(row, column, value)

    if bold:
        cell.font = Font(bold=True)

    if center:
        cell.alignment = Alignment(horizontal="center", vertical="center")

    return cell


def export_tabel_to_excel(year, month, out_path, school_name=""):
    """
    Oylik tabelni faylga yozadi. Bazaga TEGILMAYDI.

    Faqat ishlayotgan xodimlar chiqadi - bo'shatilganlar o'tgan
    oylarda qoladi, lekin yangi tabelga tushmaydi.
    """

    wb = Workbook()
    ws = wb.active
    ws.title = OYLAR[month - 1] + " " + str(year)

    jami_kun = days_in_month(year, month)

    oxirgi_kun_ustuni = FIRST_DAY_COLUMN + jami_kun - 1

    # --- sarlavha ---

    ws.cell(1, 3, school_name or "Tabel")

    ws.cell(2, 3, OYLAR[month - 1] + " " + str(year) + " oyi uchun ish vaqti tabeli")

    # --- ustun sarlavhalari ---

    _yozuv(ws, HEADER_ROW, 1, "T/R", bold=True)
    _yozuv(ws, HEADER_ROW, 2, "Tabel raqami", bold=True)
    _yozuv(ws, HEADER_ROW, 3, "Xodimning familiyasi, ismi", bold=True)
    _yozuv(ws, HEADER_ROW, 4, "Lavozimi", bold=True)
    _yozuv(ws, HEADER_ROW, 5, "Stavka miqdori", bold=True)
    _yozuv(ws, HEADER_ROW, FIRST_DAY_COLUMN, "Kun sanalari", bold=True)

    yakun = [
        "Ishlab berilgan kunlar",
        "Ishlab berilgan soatlar",
        "Mexnatga layoqatsizlik",
        "Mexnat ta'tili",
        "Ish haqi saqlanmagan",
        "Hizmat safari",
        "Sababsiz ishda bo'lmagan",
        "FMS",
    ]

    for i, nom in enumerate(yakun):
        _yozuv(ws, HEADER_ROW, oxirgi_kun_ustuni + 1 + i, nom, bold=True)

    # --- kun raqamlari ---

    for day in range(1, jami_kun + 1):
        _yozuv(ws, DAYS_ROW, FIRST_DAY_COLUMN + day - 1, day, bold=True)

    # --- xodimlar ---

    row = FIRST_DATA_ROW

    for index, (staff_id, name, position, tabel_raqami, stavka, _status) in \
            enumerate(get_tech_staff(), start=1):

        data = month_row(staff_id, year, month)

        _yozuv(ws, row, 1, index)
        _yozuv(ws, row, 2, tabel_raqami or "")
        _yozuv(ws, row, 3, name, center=False)
        _yozuv(ws, row, 4, position, center=False)
        _yozuv(ws, row, 5, stavka or 0)

        for day in range(1, jami_kun + 1):
            _yozuv(ws, row, FIRST_DAY_COLUMN + day - 1, data["days"].get(day, ""))

        qiymatlar = [
            data["ishlangan"],
            data["soat"],
            data["K"],
            data["M"],
            data["O"],
            data["X"],
            data["Y"],
            0,
        ]

        for i, qiymat in enumerate(qiymatlar):
            _yozuv(ws, row, oxirgi_kun_ustuni + 1 + i, qiymat)

        row += 1

    # --- izoh: belgilar nimani anglatadi ---

    izoh_ustun = oxirgi_kun_ustuni + 10

    _yozuv(ws, HEADER_ROW, izoh_ustun, "Izoh", bold=True)

    _yozuv(ws, FIRST_DATA_ROW, izoh_ustun, "+", center=False)
    ws.cell(FIRST_DATA_ROW, izoh_ustun + 1, "kelgan kunlar")

    _yozuv(ws, FIRST_DATA_ROW + 1, izoh_ustun, "D", center=False)
    ws.cell(FIRST_DATA_ROW + 1, izoh_ustun + 1, "dam olish kuni")

    for i, (belgi, izoh) in enumerate(sorted(TABEL_MARKS.items()), start=2):

        _yozuv(ws, FIRST_DATA_ROW + i, izoh_ustun, belgi, center=False)
        ws.cell(FIRST_DATA_ROW + i, izoh_ustun + 1, izoh)

    # --- ko'rinish ---

    ws.column_dimensions["A"].width = 5
    ws.column_dimensions["B"].width = 8
    ws.column_dimensions["C"].width = 26
    ws.column_dimensions["D"].width = 18
    ws.column_dimensions["E"].width = 12

    for column in range(FIRST_DAY_COLUMN, oxirgi_kun_ustuni + 1):
        ws.column_dimensions[get_column_letter(column)].width = 4

    for i in range(len(yakun)):
        ws.column_dimensions[
            get_column_letter(oxirgi_kun_ustuni + 1 + i)
        ].width = 11

    ws.column_dimensions[get_column_letter(izoh_ustun)].width = 5
    ws.column_dimensions[get_column_letter(izoh_ustun + 1)].width = 24

    chiziq = Side(style="thin")
    ramka = Border(left=chiziq, right=chiziq, top=chiziq, bottom=chiziq)

    for r in range(HEADER_ROW, row):
        for c in range(1, oxirgi_kun_ustuni + len(yakun) + 1):
            ws.cell(r, c).border = ramka

    ws.freeze_panes = ws.cell(FIRST_DATA_ROW, FIRST_DAY_COLUMN)

    wb.save(out_path)

    return out_path
