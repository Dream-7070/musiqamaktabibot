# -*- coding: utf-8 -*-
"""
database.py (5100+ satr) ni db/ paketiga ajratadi.

Tamoyil: `database.py` FASAD bo'lib qoladi - u db/ dagi hamma narsani
qayta eksport qiladi. Shuning uchun loyihadagi barcha
`from database import X` qatorlari o'zgarishsiz ishlayveradi.

Modullararo bog'liqliklar avtomatik hisoblanadi: har bir modul
qaysi nomlarni boshqa moduldan olishi kerakligi AST orqali
aniqlanadi va kerakli import qatorlari o'z-o'zidan qo'shiladi.

Bir martalik skript - ishlatilgandan keyin saqlanadi, chunki
ajratish qanday qilinganini ko'rsatadi.
"""

import ast
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SOURCE = os.path.join(ROOT, "database.py")

OUT_DIR = os.path.join(ROOT, "db")


# bo'lim nomi -> qaysi modulga tushadi
LAYOUT = {
    "core": [
        "DATABASE",
        "MENYU MATNLARI (bekor qilishni aniqlash uchun)",
        "CONNECT",
        "CREATE TABLES",
        "SOZLAMALAR (kalit-qiymat)",
    ],
    "teachers": [
        "TEACHERS",
        "O'QITUVCHI RO'YXATI (bo'lim / ism)",
        "AKKAUNT SO'ROVI (tasdiqlash oqimi)",
        "O'QITUVCHINI ISM BO'YICHA QIDIRISH",
        "O'QITUVCHI TURLARI VA HUQUQLARI",
    ],
    "students": [
        "STUDENTS",
        "O'QUVCHI OYLIK BADAL",
        "TUG'ILGANLIK GUVOHNOMASI TAKRORI",
        "BADAL SUMMALARI",
        "O'QUVCHI MA'LUMOTINI TAHRIRLASH",
        "O'QUVCHI ARXIVI",
        "SINFLAR",
    ],
    "documents": [
        "STUDENT DOCUMENTS",
        "GOOGLE DRIVE MIGRATSIYASI",
        "DRIVE HUJJATLARI - O'QITUVCHI",
        "DRIVE HUJJATLARI - O'QUVCHI",
        "MIGRATSIYA UCHUN YORDAMCHI",
        "MAJBURIY HUJJATLAR",
    ],
    "parents": [
        "PARENTS",
        "PARENT DOCUMENT ACCESS",
        "OTA-ONA - ITV (METRIKA) ORQALI TOPISH",
        "OTA-ONA ALOQASI",
    ],
    "payments": [
        "PAYMENTS",
        "TO'LOV KVITANSIYALARI",
    ],
    "staff": [
        "XODIMLAR (BUXGALTER)",
        "XODIMLARNI ADMIN QO'SHADI",
    ],
    "schedule": [
        "DARS JADVALI",
        "JADVAL TO'QNASHUVLARI",
        "JO'RNAVOZLAR (konsertmeysterlar)",
        "DARS VAQTLARI",
    ],
    "subjects": [
        "FANLAR",
    ],
    "audit": [
        "O'ZGARISHLAR TARIXI",
    ],
    "miniapp": [
        "MINI APP UCHUN QO'SHIMCHA",
        "MINI APP - QO'SHIMCHA (admin/o'qituvchi ekranlari)",
    ],
}

# modullar shu tartibda import qilinadi (fasadda) - core birinchi
ORDER = ["core", "teachers", "students", "documents", "parents",
         "payments", "staff", "subjects", "schedule", "audit", "miniapp"]


def find_sections(lines):
    """[(boshlanish_indeksi, tugash_indeksi, nom), ...]"""

    heads = []

    for i in range(len(lines) - 2):
        if (re.match(r'^# ={10,}\s*$', lines[i])
                and lines[i + 1].startswith("# ")
                and re.match(r'^# ={10,}\s*$', lines[i + 2])):
            heads.append((i, lines[i + 1][2:].strip()))

    out = []

    for idx, (start, name) in enumerate(heads):
        end = heads[idx + 1][0] if idx + 1 < len(heads) else len(lines)
        out.append((start, end, name))

    return out


def top_level_names(source):
    """Modulda e'lon qilingan barcha nomlar (funksiya, sinf, konstanta)."""

    names = set()

    try:
        tree = ast.parse(source)
    except SyntaxError:
        return names

    for node in tree.body:

        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name)

        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    names.add(target.id)

    return names


def referenced_names(source):
    """Modulda ishlatilgan barcha nomlar."""

    used = set()

    try:
        tree = ast.parse(source)
    except SyntaxError:
        return used

    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            used.add(node.id)

    return used


def main():

    text = io.open(SOURCE, encoding="utf-8").read()
    lines = text.split("\n")

    sections = find_sections(lines)

    by_name = {name: (s, e) for s, e, name in sections}

    # tekshirув: LAYOUT dagi hamma bo'lim mavjudmi
    missing = []
    for mod, names in LAYOUT.items():
        for n in names:
            if n not in by_name:
                missing.append(n)

    if missing:
        print("XATO - bu bo'limlar topilmadi:")
        for n in missing:
            print("   ", repr(n))
        return 1

    placed = {n for names in LAYOUT.values() for n in names}
    unplaced = [n for _, _, n in sections if n not in placed]

    if unplaced:
        print("XATO - bu bo'limlar hech qaysi modulga tushmadi:")
        for n in unplaced:
            print("   ", repr(n))
        return 1

    # 1-bosqich: har bir modul matnini yig'amiz
    chunks = {}

    for mod in ORDER:
        parts = []
        for name in LAYOUT[mod]:
            s, e = by_name[name]
            parts.append("\n".join(lines[s:e]).rstrip() + "\n")
        chunks[mod] = "\n\n".join(parts)

    # 2-bosqich: har bir modul qaysi nomlarni e'lon qiladi
    declared = {mod: top_level_names(chunks[mod]) for mod in ORDER}

    owner = {}
    for mod in ORDER:
        for n in declared[mod]:
            owner.setdefault(n, mod)

    # 3-bosqich: modullararo bog'liqliklarni hisoblaymiz
    STDLIB_OK = {"sqlite3", "datetime", "os", "re", "json", "time"}

    imports_for = {}

    for mod in ORDER:
        used = referenced_names(chunks[mod])
        own = declared[mod]

        needed = {}

        for n in sorted(used):
            if n in own or n in STDLIB_OK:
                continue
            src = owner.get(n)
            if src and src != mod:
                needed.setdefault(src, []).append(n)

        imports_for[mod] = needed

    # 4-bosqich: fayllarni yozamiz
    if not os.path.isdir(OUT_DIR):
        os.makedirs(OUT_DIR)

    header_tpl = (
        "# -*- coding: utf-8 -*-\n"
        "# ==========================\n"
        "# db/%s.py\n"
        "# ==========================\n"
        "#\n"
        "# Bu fayl ilgari database.py ning bir qismi edi (5100+ satr).\n"
        "# database.py hozir FASAD - u shu paketdagi hamma narsani\n"
        "# qayta eksport qiladi, shuning uchun `from database import X`\n"
        "# hamma joyda o'zgarishsiz ishlayveradi.\n"
        "#\n"
        "# ==========================\n\n\n"
        "import sqlite3\n\n"
        "from datetime import datetime\n"
    )

    for mod in ORDER:

        body = header_tpl % mod

        # Modullararo import ATAYLAB yozilmaydi.
        #
        # Sabab: bo'limlar orasida halqali bog'liqliklar bor
        # (students <-> parents <-> documents, core <-> schedule).
        # Oddiy importda bu "circular import" xatosini beradi.
        #
        # Yechim: database.py (fasad) hamma modulni yuklab bo'lgach,
        # yetishmayotgan nomlarni har bir modulning globals() iga
        # o'zi joylashtiradi. Bu xavfsiz, chunki hech bir modul
        # import PAYTIDA begona nomni ishlatmaydi - faqat funksiya
        # ichida, ya'ni chaqirilganda, o'shanda globals() to'la.

        needed = imports_for[mod]

        if needed:
            body += "\n# Bu modul quyidagi modullardagi nomlarni ishlatadi\n"
            body += "# (database.py fasadi ularni yuklashda joylashtiradi):\n"
            for src in ORDER:
                if src in needed:
                    body += "#   db.%s: %s\n" % (
                        src, ", ".join(sorted(set(needed[src]))))

        body += "\n\n" + chunks[mod].lstrip("\n")

        path = os.path.join(OUT_DIR, mod + ".py")
        io.open(path, "w", encoding="utf-8", newline="\n").write(body)

        print("yozildi: db/%s.py  (%d satr, %d ta nom)"
              % (mod, body.count("\n"), len(declared[mod])))

    # __init__.py
    init = (
        "# -*- coding: utf-8 -*-\n"
        "# db/ - ilgari bitta database.py bo'lgan kod.\n"
        "# Tashqi kod uchun kirish nuqtasi hamon database.py (fasad).\n"
    )
    io.open(os.path.join(OUT_DIR, "__init__.py"), "w",
            encoding="utf-8", newline="\n").write(init)

    # bog'liqlik xaritasini ko'rsatamiz
    print()
    print("modullararo bog'liqliklar:")
    for mod in ORDER:
        deps = sorted(imports_for[mod].keys())
        print("   %-10s -> %s" % (mod, ", ".join(deps) if deps else "-"))

    return 0


if __name__ == "__main__":
    sys.exit(main())
