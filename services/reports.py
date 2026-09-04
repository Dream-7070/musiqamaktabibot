# ==========================
# services/reports.py
# DIREKTOR UCHUN OYLIK QARZDORLIK HISOBOTI (Excel)
# ==========================


import io

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment


HEADER_FILL = PatternFill(
    start_color="305496",
    end_color="305496",
    fill_type="solid"
)

HEADER_FONT = Font(color="FFFFFF", bold=True)

DEBT_FILL = PatternFill(
    start_color="FCE4E4",
    end_color="FCE4E4",
    fill_type="solid"
)


def _style_header(ws, row=1):

    for cell in ws[row]:

        cell.font = HEADER_FONT
        cell.fill = HEADER_FILL
        cell.alignment = Alignment(horizontal="center", vertical="center")


def _autosize(ws):

    for col in ws.columns:

        length = max(
            (len(str(cell.value)) for cell in col if cell.value is not None),
            default=8
        )

        ws.column_dimensions[col[0].column_letter].width = min(length + 3, 45)


def build_debt_report(month, rows):
    """
    rows: [(teacher, department, student, fee, paid_bool, privileged_bool), ...]
    Qaytaradi: (BytesIO, fayl_nomi)
    """

    wb = Workbook()


    # ==========================
    # 1-BET: XULOSA (o'qituvchi bo'yicha)
    # ==========================

    ws1 = wb.active
    ws1.title = "Xulosa"

    ws1.append([
        "O'qituvchi", "Bo'lim", "Jami o'quvchi", "Imtiyozli",
        "Qarzdor soni", "Jami qarz (so'm)"
    ])

    _style_header(ws1)


    summary = {}

    for teacher, dept, student, fee, paid, privileged in rows:

        entry = summary.setdefault(
            teacher,
            {"dept": dept, "total": 0, "free": 0, "unpaid": 0, "debt": 0}
        )

        entry["total"] += 1

        if privileged:
            entry["free"] += 1

        elif not paid:
            entry["unpaid"] += 1
            entry["debt"] += fee


    for teacher, data in sorted(
        summary.items(),
        key=lambda x: x[1]["debt"],
        reverse=True
    ):

        row_index = ws1.max_row + 1

        ws1.append([
            teacher,
            data["dept"],
            data["total"],
            data["free"],
            data["unpaid"],
            data["debt"]
        ])

        if data["debt"] > 0:

            for cell in ws1[row_index]:
                cell.fill = DEBT_FILL


    total_debt = sum(d["debt"] for d in summary.values())
    total_unpaid = sum(d["unpaid"] for d in summary.values())

    ws1.append([])
    total_free = sum(d["free"] for d in summary.values())

    ws1.append(["JAMI", "", "", total_free, total_unpaid, total_debt])

    for cell in ws1[ws1.max_row]:
        cell.font = Font(bold=True)

    _autosize(ws1)


    # ==========================
    # 2-BET: BATAFSIL (o'quvchi bo'yicha)
    # ==========================

    ws2 = wb.create_sheet("Batafsil")

    ws2.append([
        "O'qituvchi", "Bo'lim", "O'quvchi",
        "Oylik badal", "Holat"
    ])

    _style_header(ws2)

    for teacher, dept, student, fee, paid, privileged in rows:

        row_index = ws2.max_row + 1

        if privileged:
            status = "🎖 Imtiyozli"

        elif paid:
            status = "✅ To'langan"

        else:
            status = "❌ Qarzdor"

        ws2.append([
            teacher,
            dept,
            student,
            "-" if privileged else fee,
            status
        ])

        if not paid:

            for cell in ws2[row_index]:
                cell.fill = DEBT_FILL

    _autosize(ws2)


    buffer = io.BytesIO()

    wb.save(buffer)

    buffer.seek(0)

    filename = "hisobot_" + month + ".xlsx"

    return buffer, filename
