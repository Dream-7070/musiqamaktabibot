# -*- coding: utf-8 -*-
"""
2026 o'quv rejasi PDF -> data/curriculum.py

PDF matnini oddiy chiqarganda ustunlar yo'qoladi va "1 1 1 1"
qaysi sinflarga tegishli ekani bilinmaydi. Shuning uchun pypdf
layout rejimi ishlatiladi: har bir raqamning satrdagi o'rni
sarlavhadagi sinf raqamining o'rniga solishtiriladi.

Har bir satr o'zining "Umumiy soatlar" ustuni bilan tekshiriladi:
    haftalik soatlar yig'indisi x 34 hafta = umumiy soat
"""

import io
import re
import json

import pypdf


PDF = "D:/Claude Projects/19 bmsm/2026 O\u2018QUV REJA LOYIHA .pdf"

WEEKS = 34

# 0,5 va 0.5 - reja ikkalasini ham ishlatadi
NUM = re.compile(r"(?<!\d)\d{1,4}(?:[.,]\d)?(?!\d)")

HEAD = re.compile(
    r"([^.\d]{4,110}?)\s*[–—-]?\s*"
    r"mutaxassisli(?:gi|klari|ki|k)\s+bo[‘'`]yicha\s+"
    r"ta[’']lim muddati\s*(\d+)\s*yil"
)


def to_float(value):
    return float(value.replace(",", "."))


def clean_name(value):

    name = re.split(
        r"o[‘'`]quv reja\s+|mutaxassisli\w*\s+bo[‘'`]yicha\s*",
        value.strip(" –—-:")
    )[-1]

    name = re.sub(r"^(?:[IVX]+\.\s*)?Ta[’']lim yo[‘'`]nalishi:\s*", "", name)

    return re.sub(r"\s+", " ", name).strip(" –—-:")


# "Ritmika / parter" qatorida ikki fan birlashtirilgan:
# "1/0,5" = 1 soat + 0,5 soat. Yig'indi sifatida olamiz va
# ustun joylashuvi buzilmasligi uchun bo'sh joy bilan to'ldiramiz.

COMBINED = re.compile(r"(?<!\d)(\d{1,2}(?:[.,]\d)?)/(\d{1,2}(?:[.,]\d)?)(?!\d)")


def merge_pairs(line):

    def replace(match):
        total = to_float(match.group(1)) + to_float(match.group(2))
        text = ("%g" % total).replace(".", ",")
        return text.ljust(len(match.group(0)))

    return COMBINED.sub(replace, line)


reader = pypdf.PdfReader(PDF)

lines = []

for page in reader.pages:
    for line in page.extract_text(extraction_mode="layout").split("\n"):
        if line.strip():
            lines.append(merge_pairs(line))


curriculum = {}

name = years = None
columns = None
previous_text = ""

checked = failed = 0
problems = []

for index, line in enumerate(lines):

    window = re.sub(r"\s+", " ", " ".join(lines[max(0, index - 8):index + 1]))

    found = list(HEAD.finditer(window))

    if found:
        name = clean_name(found[-1].group(1))
        years = int(found[-1].group(2))

    tokens = [(m.start(), m.group()) for m in NUM.finditer(line)]

    values = [t[1] for t in tokens]

    # sinf sarlavhasi: "1 2 3 4 5 6 7"
    if len(values) >= 4 and values == [str(i + 1) for i in range(len(values))]:
        columns = tokens
        continue

    if columns is None:
        if line.strip():
            previous_text = line.strip()
        continue

    if line.strip().startswith("Haftalik jami"):
        columns = None
        continue

    if not re.match(r"\s*\d{1,2}\.\s", line):
        if line.strip():
            previous_text = line.strip()
        continue

    # fan nomi ikki-uch qatorga bo'linib ketgan bo'lishi mumkin:
    #   "Jamoa ijrochiligi (maqom"
    #   "10.  ansambli, folklor ansambli va   2  3  3 ..."
    #   "boshqalar)"
    # oldingi va keyingi qatorlarda raqam bo'lmasa - ular nomning
    # davomi hisoblanadi

    suffix = ""

    if index + 1 < len(lines):

        nxt = lines[index + 1]

        text = nxt.strip()

        # keyingi qator nomning davomi bo'lishi uchun: yo qavs
        # ochiq qolgan, yo kichik harf bilan boshlangan. Aks holda
        # bu keyingi fanning nomi bo'lib chiqadi.

        if (text and not NUM.search(nxt)
                and not re.match(r"\s*\d{1,2}\.\s", nxt)
                and len(text) < 60):

            head = re.match(r"\s*\d{1,2}\.\s+(.+?)\s{2,}\S", line)
            head = head.group(1) if head else ""

            if head.count("(") > head.count(")") or text[:1].islower():
                suffix = text

    cells = tokens[1:]              # birinchisi - tartib raqami

    if len(cells) < 2:
        continue

    total = cells[-1][1]

    if not total.isdigit():
        continue

    hours = {}

    for position, value in cells[:-1]:

        nearest = min(columns, key=lambda c: abs(c[0] - position))

        hours[nearest[1]] = to_float(value)

    # fan nomi
    subject = re.match(r"\s*\d{1,2}\.\s+(.+?)\s{2,}\S", line)
    subject = re.sub(r"\s+", " ", subject.group(1)).strip(" *") if subject else ""

    # nom oldingi qatordan boshlangan bo'lsa
    if previous_text and (
        subject[:1].islower()
        or subject.startswith("(")
        or previous_text.endswith(("(", "va", "bilan"))
    ):
        header_words = ("T/r", "Fanlarning", "Sinflar", "soatlar")

        if not re.match(r"\s*\d{1,2}\.\s", previous_text)                 and not NUM.search(previous_text)                 and not any(w in previous_text for w in header_words):
            subject = re.sub(r"\s+", " ", previous_text + " " + subject)

    if suffix:
        subject = re.sub(r"\s+", " ", subject + " " + suffix)

    subject = subject.strip(" *")

    if not subject or not name:
        continue

    checked += 1

    if abs(sum(hours.values()) * WEEKS - int(total)) > 0.5:
        failed += 1
        problems.append((name, subject, sum(hours.values()) * WEEKS, total))

    entry = curriculum.setdefault(name, {"years": years, "subjects": {}})
    entry["subjects"][subject] = hours


# Nomi uch qatorga bo'linib ketgan bir nechta fan avtomatik
# yig'ilmaydi (tartib raqami nomning o'rtasidagi qatorda turadi).
# Ular qo'lda to'g'rilanadi. Rejadagi "ijrichiligi" imlo xatosi
# ham shu yerda tuzatiladi.

NAME_FIXES = {
    "Jamoa ijrichiligi ansambli)":
        "Jamoa ijrochiligi (xor, orkestor, cholg‘u ansambli)",
    "Jamoa ijrochiligi ansambli)":
        "Jamoa ijrochiligi (xor, vokal ansambli)",
    "Jamoa ijrochiligi xonanda aralashgan xolda)":
        "Jamoa ijrochiligi (cholg‘u va xonanda aralashgan holda)",
    "Jamoa ijrochiligi ansambli va boshqalar )":
        "Jamoa ijrochiligi (maqom ansambli, folklor ansambli va boshqalar)",
    "o‘zbek musiqa adabiyoti":
        "O‘zbek musiqa adabiyoti",
    "Mutaxassislik a) xonandalik":
        "Mutaxassislik (a - xonandalik, b - cholg‘u ijrochiligi)",
}

def tidy(name):
    """Nomdagi ko'chirish nuqsonlari va rejadagi imlo xatolari."""

    name = re.sub(r"\s{2,}", " ", name).strip()

    # qavs oldidagi ortiqcha vergul: "(... o'ymakorligi,)"
    name = re.sub(r"[,;]\s*\)", ")", name)

    name = name.rstrip(",; ")

    # rejadagi imlo xatolari
    name = name.replace("ijrichiligi", "ijrochiligi")
    name = name.replace("Pesrpektiva", "Perspektiva")

    return name


for data in curriculum.values():

    for old_name in list(data["subjects"]):

        new_name = tidy(old_name)

        if new_name != old_name:
            data["subjects"][new_name] = data["subjects"].pop(old_name)


for data in curriculum.values():

    for wrong, right in NAME_FIXES.items():

        if wrong in data["subjects"]:
            data["subjects"][right] = data["subjects"].pop(wrong)


print("mutaxassislik:", len(curriculum))
print("fan satri:", checked, "| umumiy soat bilan mos kelmagan:", failed)
print()

for name_, subject, mine, total in problems:
    print("  ", name_[:24].ljust(26), subject[:32].ljust(34),
          "hisob", mine, "| rejada", total)

io.open("curriculum.json", "w", encoding="utf-8").write(
    json.dumps(curriculum, ensure_ascii=False, indent=1)
)

print()
print("curriculum.json yozildi")
