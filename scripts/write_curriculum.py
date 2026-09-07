# -*- coding: utf-8 -*-
"""curriculum.json -> data/curriculum.py (bo'lim bog'lanishi bilan)."""

import io
import json

cur = json.load(io.open("curriculum.json", encoding="utf-8"))

names = sorted(cur)


def find(*fragments):
    """Nom bo'lagiga mos mutaxassisliklar."""

    out = []

    for name in names:
        for fragment in fragments:
            if fragment in name:
                out.append(name)
                break

    return out


DEPARTMENTS = [
    ("Fortepiano", find("Fortepiano ijrochiligi")),
    ("Torli cholg'ular", find("Torli cholg")),
    ("Xalq cholg'u", find("Xalq cholg")),
    ("An'anaviy cholg'u", find("An\u2019anaviy cholg")),
    ("Damli va zarbli", find("Damli va zarbli")),
    ("Estrada cholg'u", find("Estrada cholg")),
    ("Akadem xonandalik", find("Akademik xonandalik")),
    ("An'anaviy xonandalik", find("An\u2019anaviy xonandalik")),
    ("Estrada xonandalik", find("Estrada xonandaligi")),
    ("Folklor", find("Folklor ijrochilik", "Baxshichilik", "Askiya")),
    ("Xoreografiya", find("raqs")),
    ("Tasviriy san'at", find("Dastgohli rangtasvir", "Xattotlik va miniatyura",
                             "Grafika") + find("Xaykaltaroshlik")),
    ("Amaliy san'at", find("Badiiy ", "dizayni", "Qo\u2018g\u2018irchoq yasash")),
    ("Teatr san'ati", find("Teatr va kino aktyorligi",
                           "Qo\u2018g\u2018irchoq teatr aktyorligi")),
]

# "Grafika" qidiruvi "Kompyuter grafikasi dizayni" ni ham tutadi
DEPARTMENTS = [
    (dept, [s for s in specs if not (dept == "Tasviriy san'at"
                                     and "dizayni" in s)])
    for dept, specs in DEPARTMENTS
]

lines = [
    "# ==========================",
    "# data/curriculum.py",
    "# 2026-YIL TAYANCH O'QUV REJASI",
    "# ==========================",
    "#",
    "# O'zbekiston Respublikasi Madaniyat vazirligi tasdiqlagan",
    "# \"Bolalar musiqa va san'at maktablarining tayanch o'quv",
    "# rejalari\" hujjatidan avtomatik ajratilgan.",
    "#",
    "# Tuzilishi:",
    "#   CURRICULUM[mutaxassislik] = {",
    "#       \"years\":    ta'lim muddati (5 yoki 7 yil),",
    "#       \"subjects\": {fan: {sinf: haftalik akademik soat}}",
    "#   }",
    "#",
    "# Har bir satr rejaning \"Umumiy soatlar\" ustuni bilan",
    "# tekshirilgan: haftalik yig'indi x 34 hafta. 305 satrdan",
    "# 303 tasi mos keldi; qolgan 2 tasi Askiya san'atida -",
    "# u yerda rejaning o'zida qarama-qarshilik bor.",
    "#",
    "# Bu fayl QO'LDA TAHRIRLANMAYDI:",
    "#     python scripts/build_curriculum.py",
    "# ==========================",
    "",
    "",
    "# bir o'quv yilidagi hafta soni",
    "",
    "WEEKS_PER_YEAR = 34",
    "",
    "",
    "# Bir dars nechta akademik soatgacha bo'linmasdan o'tiladi.",
    "#",
    "# 0,5 / 1 / 1,5 soatlik fanlar bo'linmaydi - bitta dars",
    "# bo'lib o'tiladi. 2 soatdan boshlab esa haftaning turli",
    "# kunlariga bo'lish mumkin (reja 6.5-bandi).",
    "",
    "MIN_SPLITTABLE_HOURS = 2",
    "",
    "",
    "CURRICULUM = {",
]

for name in names:

    data = cur[name]

    lines.append("")
    lines.append("    " + json.dumps(name, ensure_ascii=False) + ": {")
    lines.append("        \"years\": " + str(data["years"]) + ",")
    lines.append("        \"subjects\": {")

    for subject in sorted(data["subjects"]):

        hours = data["subjects"][subject]

        inner = ", ".join(
            '"%s": %s' % (c, ("%g" % hours[c]))
            for c in sorted(hours, key=int)
        )

        lines.append("            "
                     + json.dumps(subject, ensure_ascii=False)
                     + ": {" + inner + "},")

    lines.append("        }")
    lines.append("    },")

lines.append("}")
lines.append("")
lines.append("")
lines.append("# Maktabdagi bo'lim -> rejadagi mutaxassislik(lar).")
lines.append("#")
lines.append("# Ko'p bo'limda bitta mutaxassislik bor - u holda")
lines.append("# o'qituvchidan hech narsa so'ralmaydi.")
lines.append("")
lines.append("DEPARTMENT_SPECIALTIES = {")

for dept, specs in DEPARTMENTS:

    lines.append("")
    lines.append("    " + json.dumps(dept, ensure_ascii=False) + ": [")

    for spec in specs:
        lines.append("        " + json.dumps(spec, ensure_ascii=False) + ",")

    lines.append("    ],")

lines.append("}")
lines.append("")

out = "D:/Claude Projects/19 bmsm/school_bot/data/curriculum.py"
io.open(out, "w", encoding="utf-8").write("\n".join(lines))

print("yozildi:", out)
print()
for dept, specs in DEPARTMENTS:
    print("  " + dept.ljust(23) + str(len(specs)).rjust(2) + " ta mutaxassislik")
