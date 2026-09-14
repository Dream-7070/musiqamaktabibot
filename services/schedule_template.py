# -*- coding: utf-8 -*-
# ==========================
# services/schedule_template.py
# YAKKA DARSLAR JADVALI - EXCEL SHABLONI
# ==========================
#
# Har qator - bitta dars: o'quvchi, sinf, fan, kun, vaqt, xona.
# Eski shablonda kunlar ustun bo'lib turardi, fan blok
# sarlavhasidan, xona esa umuman yozilmasdi - bot taxmin qilardi
# yoki so'rardi. Bu shablonda taxmin qilinadigan narsa yo'q.
#
# Fan, kun, sinf va xona ro'yxatdan tanlanadi (Excel ochiladigan
# ro'yxati) - qo'lda yozilganda imlo xatosi chiqardi.
# ==========================


from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.worksheet.datavalidation import DataValidation


DAYS = ["Dushanba", "Seshanba", "Chorshanba", "Payshanba", "Juma", "Shanba"]

CLASSES = ["1", "2", "3", "4", "5", "6", "7"]

HEADERS = [
    ("№", 5),
    ("O'quvchining F.I.SH", 30),
    ("Sinfi", 7),
    ("Fan", 30),
    ("Kun", 13),
    ("Dars soati", 14),
    ("Xona", 9),
]

HEADER_ROW = 4

DATA_ROWS = 300


def build_template(path, rooms, subjects, teacher=""):
    """Shablonni `path` ga yozadi. rooms, subjects - ro'yxat."""

    wb = Workbook()

    ws = wb.active
    ws.title = "Jadval"

    ws["A1"] = "O'qituvchi: " + (teacher or "______________________")
    ws["A1"].font = Font(bold=True, size=12)

    ws["A2"] = "Yakka darslar jadvali"
    ws["A2"].font = Font(bold=True, size=14)

    chiziq = Side(style="thin")
    ramka = Border(left=chiziq, right=chiziq, top=chiziq, bottom=chiziq)
    kulrang = PatternFill("solid", fgColor="D9D9D9")

    for col, (nom, eni) in enumerate(HEADERS, start=1):

        cell = ws.cell(HEADER_ROW, col, nom)
        cell.font = Font(bold=True)
        cell.fill = kulrang
        cell.border = ramka
        cell.alignment = Alignment(horizontal="center", vertical="center",
                                   wrap_text=True)

        ws.column_dimensions[cell.column_letter].width = eni

    first = HEADER_ROW + 1
    last = HEADER_ROW + DATA_ROWS

    for row in range(first, last + 1):
        for col in range(1, len(HEADERS) + 1):
            ws.cell(row, col).border = ramka

    ws.freeze_panes = ws.cell(first, 1)

    # --- ro'yxatlar: alohida yashirin varaqda ---
    #
    # Fanlar 90 dan ortiq - Excel'da ro'yxatni to'g'ridan-to'g'ri
    # yozish 255 belgi bilan cheklangan, shuning uchun katakchalar
    # diapazoniga havola qilinadi.

    ls = wb.create_sheet("Ro'yxatlar")

    for i, nom in enumerate(subjects, start=1):
        ls.cell(i, 1, nom)

    for i, nom in enumerate(rooms, start=1):
        ls.cell(i, 2, str(nom))

    ls.sheet_state = "hidden"

    def _royxat(formula, ustun):

        dv = DataValidation(type="list", formula1=formula, allow_blank=True)
        dv.error = "Ro'yxatdan tanlang"
        dv.errorTitle = "Noto'g'ri qiymat"
        ws.add_data_validation(dv)
        dv.add(ustun + str(first) + ":" + ustun + str(last))

    _royxat('"' + ",".join(CLASSES) + '"', "C")
    _royxat("'Ro''yxatlar'!$A$1:$A$" + str(max(len(subjects), 1)), "D")
    _royxat('"' + ",".join(DAYS) + '"', "E")
    _royxat("'Ro''yxatlar'!$B$1:$B$" + str(max(len(rooms), 1)), "G")

    # --- yo'riqnoma ---

    yo = wb.create_sheet("Yo'riqnoma")

    matn = [
        "QANDAY TO'LDIRILADI",
        "",
        "1. Har qator - BITTA dars.",
        "   Bolaning haftada 3 ta darsi bo'lsa - 3 ta qator yoziladi.",
        "",
        "2. Fan, Kun, Sinfi va Xona - ro'yxatdan tanlanadi (katakchani bosing).",
        "",
        "3. Dars soati - boshlanish va tugash vaqti: 9:40-10:25",
        "",
        "4. Ism-familiya botdagi o'quvchilar ro'yxatidagi bilan bir xil bo'lsin.",
        "   Botda yo'q o'quvchining darsi yuklanmaydi - avval uni qo'shing.",
        "",
        "5. Jo'rnavozlik darslarini yozmang - ular mutaxassislik",
        "   o'qituvchisining jadvaliga bog'lanadi.",
        "",
        "NAMUNA:",
        "",
    ]

    for i, qator in enumerate(matn, start=1):
        yo.cell(i, 1, qator)

    yo["A1"].font = Font(bold=True, size=13)

    namuna_boshi = len(matn) + 1

    for col, (nom, eni) in enumerate(HEADERS, start=1):
        cell = yo.cell(namuna_boshi, col, nom)
        cell.font = Font(bold=True)
        cell.fill = kulrang
        yo.column_dimensions[cell.column_letter].width = eni

    namunalar = [
        (1, "Turg'inboyev Kamron", "5", "Mutaxassislik", "Dushanba", "9:40-10:50", "2/8"),
        (2, "Turg'inboyev Kamron", "5", "Mutaxassislik", "Chorshanba", "8:50-10:00", "2/8"),
        (3, "Alisherov Zafar", "3", "Notani varaqdan o'qish", "Chorshanba", "10:05-10:50", "2/8"),
    ]

    for i, qator in enumerate(namunalar, start=namuna_boshi + 1):
        for col, qiymat in enumerate(qator, start=1):
            yo.cell(i, col, qiymat)

    wb.save(path)

    return path
