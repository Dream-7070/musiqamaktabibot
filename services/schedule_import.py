# -*- coding: utf-8 -*-
"""
O'qituvchining Excel dars jadvalini o'qish.

O'qituvchilar maktabning yagona shablonida ishlaydi: satrlar -
o'quvchilar, ustunlar - haftaning 6 kuni, oraliqdagi sariq
satrlar - fan bloklari.

Shablon bitta bo'lsa ham, yillar davomida u siljib ketgan:
bir faylda sarlavha 4-satrda, boshqasida 5-satrda; biri kirill,
biri lotin. Shuning uchun bu modul satr raqamlariga TAYANMAYDI -
u kalit so'zlarni ("Dushanba", "N.V.O", "1-guruh") qidirib,
jadvalning tuzilishini o'zi topadi.

Modul Telegram'ni bilmaydi - faqat fayldan ma'lumot ajratadi.
Natijani handler ko'rsatadi va o'qituvchi tasdiqlaydi.
"""

import difflib
import re

import openpyxl


# ==========================
# LUG'ATLAR
# ==========================


DAYS_OF_WEEK = [
    "Dushanba",
    "Seshanba",
    "Chorshanba",
    "Payshanba",
    "Juma",
    "Shanba"
]


# kirill va lotin yozuvi - ikkalasi ham uchraydi

DAY_ALIASES = {
    "dushanba": "Dushanba",
    "душанба": "Dushanba",
    "seshanba": "Seshanba",
    "сешанба": "Seshanba",
    "chorshanba": "Chorshanba",
    "чоршанба": "Chorshanba",
    "payshanba": "Payshanba",
    "пайшанба": "Payshanba",
    "juma": "Juma",
    "жума": "Juma",
    "shanba": "Shanba",
    "шанба": "Shanba",
}


# Blok sarlavhalari - yakka shablonda fan shu yerdan olinadi.
# Kalit normallashtirilgan holda (nuqtasiz, kichik harf).

BLOCK_SUBJECTS = {
    "mutaxassislik": "Mutaxassislik",
    "nvo": "Notani varaqdan o'qish",
    "notani varaqdan o'qish": "Notani varaqdan o'qish",
    "yakka ansambl": "Ansambl",
    "ansambl": "Ansambl",
    "jamoaviy ansambl": "Jamoa ijrochiligi",
    "jamoa ijrochiligi": "Jamoa ijrochiligi",
    "tanlangan fan": "Tanlangan fan",
    "jo'rnavozlik": "Jo'rnavozlik",
    "solfedjio": "Solfedjio",
    "umumiy fortepiano": "Umumiy fortepiano",
}


# Katak ichidagi qisqartmalar - guruh shablonida fan shu yerda.
# Uzunroq kalit oldin tekshiriladi ("kom a" dan oldin "kom" emas).

CELL_SUBJECTS = {
    "mut": "Mutaxassislik",
    "rang t": "Rangtasvir",
    "rangtasvir": "Rangtasvir",
    "chiz t": "Chizmatasvir",
    "chizmatasvir": "Chizmatasvir",
    "kom a": "Kompozitsiya (amaliy)",
    "kom d": "Kompozitsiya (dastgohli)",
    "kom": "Kompozitsiya",
    "kompozitsiya": "Kompozitsiya",
    "xaykal": "Xaykaltaroshlik",
    "xaykaltaroshlik": "Xaykaltaroshlik",
    "badiiy kashtachilik": "Badiiy kashtachilik",
    "kashta tikish": "Kashta tikish texnologiyasi",
}


# nechta akademik soatga to'g'ri kelishini tekshirish uchun.
# 1 soat = 45 daqiqa, yarim soat = 25 daqiqa (reja 6.5-bandi).

HOUR_MINUTES = {
    0.5: 25,
    1.0: 45,
    1.5: 65,
    2.0: 90,
    3.0: 135,
    4.0: 180,
}


MIN_BREAK = 5


# ==========================
# MATN NORMALLASHTIRISH
# ==========================


APOSTROPHES = "‘’ʻʼ`´"


def normalize(text):
    """Qiyoslash uchun: kichik harf, bir xil apostrof, ortiqcha belgisiz."""

    if text is None:
        return ""

    text = str(text).strip().lower()

    for mark in APOSTROPHES:
        text = text.replace(mark, "'")

    # nuqta va ortiqcha bo'shliqlar qisqartmalarga xalaqit beradi:
    # "Kom.A." va "Kom. A" bir xil bo'lishi kerak

    text = text.replace(".", " ")

    text = re.sub(r"\s+", " ", text).strip()

    return text


# ==========================
# VAQTNI O'QISH
# ==========================


# 8:00-8:45 · 8;00 - 8:45 · 13.00–14.35 - hammasi uchraydi

TIME_RANGE = re.compile(
    r"(\d{1,2})\s*[:;.,]\s*(\d{2})"
    r"\s*[-–—]\s*"
    r"(\d{1,2})\s*[:;.,]\s*(\d{2})"
)


ROOM_IN_CELL = re.compile(r"\(([^)]*\d[^)]*)\)")


def to_minutes(hour, minute):
    return int(hour) * 60 + int(minute)


def format_time(total):
    return "{:d}:{:02d}".format(total // 60, total % 60)


CLOCK = re.compile(r"^\s*(\d{1,2})\s*[:;.,]\s*(\d{2})")


def parse_clock(text):
    """'08:00' -> 480. Tushunib bo'lmasa None."""

    if text is None:
        return None

    found = CLOCK.match(str(text))

    if not found:
        return None

    return to_minutes(found.group(1), found.group(2))


def known_subjects():
    """Tugmalarda ko'rsatish uchun barcha fan nomlari."""

    names = set(BLOCK_SUBJECTS.values()) | set(CELL_SUBJECTS.values())

    return sorted(names)


def alias_of(text):
    """Katakdagi matndan vaqtlarni olib tashlab, lug'at kalitini beradi."""

    cleaned = TIME_RANGE.sub(" ", str(text or ""))

    cleaned = ROOM_IN_CELL.sub(" ", cleaned)

    return normalize(cleaned)


def parse_cell(raw):
    """
    Bitta katakni tushunadi.

    Qaytaradi: (ranges, subject_hint, room_hint, leftover)
      ranges  - [(boshlanish_daqiqa, tugash_daqiqa), ...]
      subject - katakdagi qisqartmadan topilgan fan (bo'lmasa None)
      exact   - aniq topildimi (False - taxmin, so'rash kerak)
      room    - qavs ichidagi xona (bo'lmasa None)
      leftover- tushunilmagan matn (xato hisoboti uchun)
    """

    if raw is None:
        return [], None, True, None, ""

    text = str(raw).strip()

    if not text:
        return [], None, True, None, ""

    room = None

    found_room = ROOM_IN_CELL.search(text)

    if found_room:
        room = found_room.group(1).strip()
        text = ROOM_IN_CELL.sub(" ", text)

    ranges = []

    for match in TIME_RANGE.finditer(text):

        start = to_minutes(match.group(1), match.group(2))
        end = to_minutes(match.group(3), match.group(4))

        ranges.append((start, end))

    leftover = TIME_RANGE.sub(" ", text)

    leftover = re.sub(r"\s+", " ", leftover).strip()

    subject, exact = match_subject(leftover)

    if subject:
        leftover = ""

    return ranges, subject, exact, room, leftover


# Imlo xatosini kechirish chegarasi. 0.80 - "Jo'rnavoz;il" ni
# "Jo'rnavozlik" ga bog'lash uchun yetarli, lekin butunlay boshqa
# so'zni tortib olmaydigan darajada qattiq.

FUZZY_CUTOFF = 0.80


def _fuzzy(key, table):
    """Eng yaqin kalitni topadi: (fan, aniqlik) yoki (None, 0)."""

    close = difflib.get_close_matches(key, list(table), n=1,
                                      cutoff=FUZZY_CUTOFF)

    if not close:
        return None, 0.0

    score = difflib.SequenceMatcher(None, key, close[0]).ratio()

    return table[close[0]], score


def match_subject(text, aliases=None):
    """
    Katakdagi matndan fan qisqartmasini topadi.

    Qaytaradi: (fan, aniq_topildimi). Ikkinchi qiymat False bo'lsa -
    taxmin qilindi, o'qituvchidan so'rash kerak.
    """

    key = normalize(text)

    if not key:
        return None, True

    table = dict(CELL_SUBJECTS)

    if aliases:
        table.update({normalize(k): v for k, v in aliases.items()})

    # uzun kalitlar oldin - "kom a" "kom" dan ustun bo'lsin

    for alias in sorted(table, key=len, reverse=True):

        if key.startswith(alias):
            return table[alias], True

    guess, _ = _fuzzy(key, table)

    return guess, False


def match_block(text, aliases=None):
    """
    Satr fan bloki sarlavhasimi?

    Qaytaradi: (fan, aniq_topildimi).
    """

    key = normalize(text)

    if not key:
        return None, True

    table = dict(BLOCK_SUBJECTS)

    if aliases:
        table.update({normalize(k): v for k, v in aliases.items()})

    if key in table:
        return table[key], True

    # "N.V.O'" -> "n v o" -> nuqtalar olib tashlanganda "nvo"

    squeezed = key.replace(" ", "").replace("'", "")

    if squeezed in table:
        return table[squeezed], True

    guess, _ = _fuzzy(key, table)

    if guess is None:
        guess, _ = _fuzzy(squeezed, table)

    return guess, False


WORD = r"[A-ZА-ЯЎҚҒҲЁ][\w'’‘ʻ`-]+"

NAME_LIKE = re.compile(r"^" + WORD + r"(\s+" + WORD + r")+$", re.UNICODE)


def looks_like_name(text):
    """
    "Murodov Otabek" - ism. "Jo'rnavoz;il", "Yakka ansambl" - emas.

    Talab: ikki va undan ortiq so'z va HAR BIRI bosh harf bilan.
    Fan nomlarida ikkinchi so'z kichik harf bilan yoziladi, ism
    esa har doim ikki bosh harf - ajratish shunga tayanadi.

    Shubha tug'ilsa "ism emas" tomonga og'adi: u holda bot
    so'raydi, jimgina noto'g'ri qaror qabul qilmaydi.
    """

    return bool(NAME_LIKE.match(str(text).strip()))


GROUP_LABEL = re.compile(r"^\s*(\d+)\s*-\s*(guruh|gurux|гурух|гурух)", re.I)


def match_group(text):
    """"1-guruh" kabi sarlavhani topadi."""

    if text is None:
        return None

    found = GROUP_LABEL.match(str(text).strip())

    if not found:
        return None

    return found.group(1) + "-guruh"


# ==========================
# VARAQ TUZILISHINI TOPISH
# ==========================


def find_day_columns(ws):
    """
    Kun nomlari yozilgan satrni topadi va
    {ustun_raqami: "Dushanba"} qaytaradi.
    """

    for row in ws.iter_rows(min_row=1, max_row=min(ws.max_row, 20)):

        columns = {}

        for cell in row:

            day = DAY_ALIASES.get(normalize(cell.value))

            if day:
                columns[cell.column] = day

        # kamida uch kun topilsa - bu o'sha satr

        if len(columns) >= 3:
            return row[0].row, columns

    return None, {}


QUARTER = re.compile(r"(\d)\s*-?\s*(chorak|чорак)", re.I)


def find_quarter(ws):
    """
    Chorakni varaq ICHIDAN topadi: "1-chorak dars jadvali".

    Varaq nomiga qaralmaydi - u shablonning qismi emas.
    Excel varaqlari "Лист1", "Лист2" bo'lib qolishi mumkin va
    ichidagi matnga umuman aloqasi yo'q.
    """

    for row in ws.iter_rows(min_row=1, max_row=min(ws.max_row, 12)):

        for cell in row:

            if cell.value is None:
                continue

            found = QUARTER.search(str(cell.value))

            if found:
                return found.group(1)

    return None


TEACHER_LINE = re.compile(r"(o'qituvchisi|o‘qituvchisi|ўқитувчиси)\s*(.+)", re.I)


def find_teacher(ws):

    for row in ws.iter_rows(min_row=1, max_row=min(ws.max_row, 12)):

        for cell in row:

            if cell.value is None:
                continue

            found = TEACHER_LINE.search(str(cell.value))

            if found:
                return found.group(2).strip()

    return None


def merged_spans(ws):
    """
    Birlashtirilgan kataklarni xaritaga soladi.

    Guruh shablonida bitta vaqt katagi butun guruh satrlarini
    qamraydi - qaysi satrlarga tegishli ekanini bilish kerak.

    {(satr, ustun): (birinchi_satr, oxirgi_satr)}
    """

    spans = {}

    for area in ws.merged_cells.ranges:

        for row in range(area.min_row, area.max_row + 1):

            for column in range(area.min_col, area.max_col + 1):

                spans[(row, column)] = (area.min_row, area.max_row)

    return spans


def cell_value(ws, spans, row, column):
    """Birlashtirilgan katakning qiymati chap-yuqori katagida turadi."""

    value = ws.cell(row=row, column=column).value

    if value is not None:
        return value

    area = spans.get((row, column))

    if not area:
        return None

    return ws.cell(row=area[0], column=column).value


# ==========================
# VARAQNI O'QISH
# ==========================


def read_sheet(ws, sheet_name, aliases=None):
    """
    Bitta chorak varag'ini o'qiydi.

    aliases - o'qituvchi ilgari tushuntirib bergan nomlar
    ({"Jo'rnavoz;il": "Jo'rnavozlik"}). Bir marta so'ralib,
    bazada saqlanadi - keyingi safar so'ralmaydi.

    Qaytaradi: (lessons, groups, issues, questions, meta)
    """

    lessons = []

    groups = {}

    issues = []

    questions = []

    header_row, day_columns = find_day_columns(ws)

    meta = {
        "sheet": sheet_name,
        "quarter": find_quarter(ws),
        "teacher": find_teacher(ws),
        "layout": "yakka",
    }

    if not day_columns:

        issues.append({
            "level": "error",
            "sheet": sheet_name,
            "text": "Kun nomlari topilmadi - bu dars jadvali varag'i emasga o'xshaydi.",
        })

        return lessons, groups, issues, questions, meta

    spans = merged_spans(ws)

    first_column = min(day_columns) - 1        # sinf ustuni
    name_column = min(day_columns) - 2         # F.I.O ustuni

    subject = "Mutaxassislik"                  # birinchi blok odatda nomsiz

    # Fan qaysi yozuvdan olingani. Aniq tanilgan bo'lsa None -
    # o'qituvchidan so'ralmaydi. Taxmin yoki noma'lum bo'lsa shu
    # kalit orqali javob keyin darslarga qo'llanadi.

    subject_alias = None

    group = None

    student = None

    class_name = ""

    for row in range(header_row + 1, ws.max_row + 1):

        label = ws.cell(row=row, column=name_column).value

        text = str(label).strip() if label is not None else ""

        raw_class = ws.cell(row=row, column=first_column).value

        # --- avval satrdagi kataklarni yig'amiz: vaqt bor-yo'qligi
        #     satr sarlavhami yoki o'quvchimi degan savolga javob beradi

        cells = []

        for column, day in sorted(day_columns.items()):

            raw = cell_value(ws, spans, row, column)

            if raw is None or not str(raw).strip():
                continue

            area = spans.get((row, column))

            # guruh darsi bir marta yoziladi - birlashtirilgan
            # katakni faqat birinchi satrida hisobga olamiz

            if area and area[0] != row:
                continue

            cells.append((day, raw))

        has_time = any(parse_cell(raw)[0] for _, raw in cells)

        # --- guruh sarlavhasi

        group_name = match_group(text)

        if group_name:

            group = group_name
            groups.setdefault(group, [])
            meta["layout"] = "guruh"

            continue

        # --- fan bloki sarlavhasi
        #
        # Sarlavha satrida na sinf, na vaqt bo'ladi. Shu ikki
        # shart bilan uni o'quvchi satridan ajratamiz - aks holda
        # xato yozilgan sarlavha ("Jo'rnavoz;il") o'quvchi deb
        # o'qilib, keyingi darslar oldingi fanda qolib ketardi.

        looks_like_block = text and not has_time and not raw_class

        if looks_like_block:

            block, exact = match_block(text, aliases)

            if block and exact:

                subject = block
                subject_alias = None
                group = None

                continue

            if block and not exact:

                questions.append({
                    "kind": "block",
                    "sheet": sheet_name,
                    "row": row,
                    "text": text,
                    "guess": block,
                })

                subject = block
                subject_alias = normalize(text)
                group = None

                continue

            # Umuman tanilmadi. Ism ko'rinishida bo'lsa - darssiz
            # o'quvchi, aks holda noma'lum fan.

            if not looks_like_name(text):

                questions.append({
                    "kind": "block",
                    "sheet": sheet_name,
                    "row": row,
                    "text": text,
                    "guess": None,
                })

                subject = None
                subject_alias = normalize(text)
                group = None

                continue

        # --- o'quvchi satri
        #
        # Bo'sh yoki faqat raqamli satr - oldingi o'quvchining
        # davomi (bir o'quvchiga bir necha vaqt yozilgan holat).

        if text and not re.fullmatch(r"\d+", text):

            student = text

            class_name = str(raw_class).strip() if raw_class else ""

            if group:
                groups[group].append((student, class_name))

        elif student is None:
            continue

        for day, raw in cells:

            ranges, hint, hint_exact, room, leftover = parse_cell(raw)

            if leftover:

                issues.append({
                    "level": "warn",
                    "sheet": sheet_name,
                    "row": row,
                    "text": "Tushunilmadi: «" + str(raw).strip() + "»",
                })

            if not ranges:
                continue

            alias_key = None

            if hint and not hint_exact:

                alias_key = alias_of(raw)

                questions.append({
                    "kind": "cell",
                    "sheet": sheet_name,
                    "row": row,
                    "text": str(raw).strip(),
                    "guess": hint,
                })

            elif not hint:
                alias_key = subject_alias

            final_subject = hint or subject

            if final_subject is None:

                issues.append({
                    "level": "error",
                    "sheet": sheet_name,
                    "row": row,
                    "text": ("«" + str(raw).strip() + "» - qaysi fan ekani "
                             "aniqlanmadi."),
                })

            for start, end in ranges:

                lessons.append({
                    "sheet": sheet_name,
                    "quarter": meta["quarter"],
                    "day": day,
                    "start": start,
                    "end": end,
                    "minutes": end - start,
                    "subject": final_subject,

                    # guruh a'zolari turli sinflarda - guruh darsiga
                    # bitta sinf qo'yish noto'g'ri bo'lardi

                    "class": "" if group else class_name,
                    "who": group or student,
                    "is_group": bool(group),
                    "room": room,
                    "row": row,
                    "raw": str(raw).strip(),

                    # so'ralishi kerak bo'lgan nom (bo'lmasa None)

                    "alias_key": alias_key,
                })

    return lessons, groups, issues, questions, meta


# ==========================
# TEKSHIRUV
# ==========================


def check(lessons):
    """Fayl ichidagi mantiqiy xatolarni topadi."""

    issues = []

    for lesson in lessons:

        minutes = lesson["minutes"]

        if minutes <= 0:

            issues.append({
                "level": "error",
                "sheet": lesson["sheet"],
                "row": lesson["row"],
                "text": (lesson["day"] + " " + lesson["raw"]
                         + " - tugash vaqti boshlanishidan oldin."),
            })

            continue

        closest = min(HOUR_MINUTES.values(), key=lambda m: abs(m - minutes))

        if abs(closest - minutes) > 5:

            issues.append({
                "level": "warn",
                "sheet": lesson["sheet"],
                "row": lesson["row"],
                "text": (lesson["day"] + " " + lesson["raw"] + " = "
                         + str(minutes) + " daqiqa. Akademik soatga "
                         "to'g'ri kelmaydi (eng yaqini "
                         + str(closest) + " daqiqa)."),
            })

    # bir kunda ustma-ust tushgan darslar

    by_day = {}

    for lesson in lessons:
        by_day.setdefault((lesson["sheet"], lesson["day"]), []).append(lesson)

    for (sheet, day), items in by_day.items():

        items.sort(key=lambda item: item["start"])

        for earlier, later in zip(items, items[1:]):

            if later["start"] < earlier["end"]:

                issues.append({
                    "level": "error",
                    "sheet": sheet,
                    "text": (day + ": " + format_time(earlier["start"]) + "-"
                             + format_time(earlier["end"]) + " ("
                             + str(earlier["who"]) + ") va "
                             + format_time(later["start"]) + "-"
                             + format_time(later["end"]) + " ("
                             + str(later["who"]) + ") ustma-ust tushgan."),
                })

            elif 0 < later["start"] - earlier["end"] < MIN_BREAK:

                issues.append({
                    "level": "warn",
                    "sheet": sheet,
                    "text": (day + ": " + str(later["who"]) + " darsidan oldin "
                             + str(later["start"] - earlier["end"])
                             + " daqiqa tanaffus - 5 daqiqadan kam."),
                })

    return issues


# ==========================
# KIRISH NUQTASI
# ==========================


def read_workbook(path, aliases=None):
    """
    Faylning BIRINCHI varag'ini o'qiydi.

    O'qituvchi bitta chorak jadvalini bitta faylda yuboradi.
    Qolgan varaqlar (bo'lsa) e'tiborga olinmaydi: ular odatda
    o'tgan yilgi nusxalar bo'lib qoladi va qaysi biri kerakligini
    taxmin qilish - xato manbai.

    aliases - o'qituvchi ilgari tushuntirgan nomlar lug'ati.

    Qaytaradi: {"sheet": {...}, "issues": [...], "questions": [...]}

    questions - fan nomi tanilmagan yoki taxmin qilingan joylar.
    Handler ularni tugma bilan so'raydi, javob bazaga saqlanadi
    va keyingi faylda avtomatik qo'llanadi.
    """

    wb = openpyxl.load_workbook(path, data_only=True)

    ws = wb.worksheets[0]

    lessons, groups, issues, questions, meta = read_sheet(
        ws, ws.title, aliases)

    issues.extend(check(lessons))

    return {
        "sheet": {"meta": meta, "lessons": lessons, "groups": groups},
        "issues": issues,
        "questions": dedupe_questions(questions),
    }


def dedupe_questions(questions):
    """Bir xil nom bir necha varaqda uchraydi - bir marta so'raymiz."""

    unique = {}

    for question in questions:

        key = normalize(question["text"])

        if key in unique:
            unique[key]["count"] += 1
            continue

        question = dict(question)
        question["count"] = 1
        question["key"] = key

        unique[key] = question

    return list(unique.values())

# ==========================
# NIMA O'ZGARADI
# ==========================
#
# Import darslarni jimgina almashtirmaydi. Avval o'qituvchiga
# aynan nima o'zgarishini ko'rsatadi: nechtasi qo'shiladi,
# nechtasi o'chadi, nechtasi joyidan siljiydi.
#
# Sabab: o'qituvchi faylni tuzatib QAYTA yuborishi odatiy hol.
# Butun jadvalni o'chirib qayta yozish esa o'quvchilar va
# jo'rnavozlarni yo'qotardi (delete_slot kaskad o'chiradi).
# Shuning uchun faqat haqiqatan o'zgargan darslarga tegiladi.


def lesson_key(lesson):
    """Darsni aniqlovchi belgi: kim, qaysi fan, qaysi kun."""

    return (
        lesson["day"],
        lesson.get("subject") or "",
        str(lesson.get("class") or ""),
        str(lesson.get("who") or "").strip().lower(),
    )


def plan_changes(current, incoming):
    """
    Bazadagi darslar bilan fayldagilarni solishtiradi.

    current  - bazadagi darslar (lesson_key tushunadigan lug'atlar,
               "start" va "room" bilan)
    incoming - fayldan o'qilganlari

    Qaytaradi: {"add": [...], "remove": [...], "move": [...],
                "keep": [...]}

    move - kun/fan/o'quvchi bir xil, lekin vaqti yoki xonasi
    boshqa. Bunday dars o'chirilmaydi, faqat joyi tuzatiladi
    (update_slot_schedule) - o'quvchilari saqlanib qoladi.
    """

    pool = {}

    for lesson in current:
        pool.setdefault(lesson_key(lesson), []).append(lesson)

    add = []

    move = []

    keep = []

    for lesson in incoming:

        key = lesson_key(lesson)

        candidates = pool.get(key) or []

        # aynan o'sha vaqtdagisi bo'lsa - o'zgarish yo'q

        same = next(
            (item for item in candidates
             if item.get("start") == lesson.get("start")),
            None
        )

        if same is not None:

            candidates.remove(same)

            if (same.get("room") or "") != (lesson.get("room") or ""):
                move.append({"old": same, "new": lesson})
            else:
                keep.append(lesson)

            continue

        # vaqti boshqa, lekin o'sha kun-fan-o'quvchi: siljigan

        if candidates:

            old = candidates.pop(0)

            move.append({"old": old, "new": lesson})

            continue

        add.append(lesson)

    remove = [item for items in pool.values() for item in items]

    return {"add": add, "remove": remove, "move": move, "keep": keep}


def describe_changes(plan):
    """O'qituvchiga ko'rsatiladigan matn."""

    lines = []

    if plan["keep"]:
        lines.append("✅ " + str(len(plan["keep"]))
                     + " ta dars o'zgarishsiz qoladi")

    for lesson in plan["add"]:
        lines.append("➕ " + _one_line(lesson))

    for change in plan["move"]:

        old = change["old"]
        new = change["new"]

        detail = []

        if old.get("start") != new.get("start"):
            detail.append(format_time(old["start"]) + " → "
                          + format_time(new["start"]))

        if (old.get("room") or "") != (new.get("room") or ""):
            detail.append(str(old.get("room") or "-") + "-xona → "
                          + str(new.get("room") or "-") + "-xona")

        lines.append("🔀 " + _one_line(new, with_time=False)
                     + ": " + ", ".join(detail))

    for lesson in plan["remove"]:
        lines.append("➖ " + _one_line(lesson) + " - o'chadi")

    return lines


def _one_line(lesson, with_time=True):

    parts = [lesson["day"]]

    if with_time:
        parts.append(format_time(lesson["start"]) + "-"
                     + format_time(lesson["end"])
                     if lesson.get("end") else format_time(lesson["start"]))

    parts.append(lesson.get("subject") or "?")

    if lesson.get("class"):
        parts.append(str(lesson["class"]) + "-sinf")

    parts.append(str(lesson.get("who") or ""))

    return " · ".join(parts)

