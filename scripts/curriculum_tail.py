

# ==========================
# NAZARIYA BO'LIMI
# ==========================
#
# Nazariya o'qituvchilarining o'z o'quvchisi bo'lmaydi. Ular
# barcha bo'limlarning o'quvchilariga umumiy nazariy fanlarni
# o'tishadi - solfedjio, musiqa adabiyoti va boshqalar.
#
# Shuning uchun ularning fanlar ro'yxati bitta mutaxassislikdan
# emas, quyidagi ro'yxatdan olinadi. Soat esa o'quvchining
# yo'nalishiga qarab farq qilishi mumkin (masalan solfedjio
# 5-sinfda Fortepianoda 1,5 soat, Xalq cholg'usida 2 soat) -
# bunday holda bot ikkala variantni ham ko'rsatadi.
#
# San'at tarixi fanlari bu ro'yxatga kirmaydi: ular o'z
# bo'limlarida (Tasviriy, Xoreografiya, Teatr) o'tiladi.
# ==========================


THEORY_DEPARTMENT = "Nazariya"


THEORY_SUBJECTS = [
    "Solfedjio",
    "Maqom alifbosi",
    "Maqom asoslari",
    "Musiqa savodi va musiqa tinglash",
    "Xorij musiqa adabiyoti",
    "O‘zbek musiqa adabiyoti",
    "Xorij va o‘zbek musiqa adabiyoti",
    "Estrada tarixi",
    "Xalq ijodiyoti tarixi",
    "Baxshi, jirov va oqinlar san’at tarixi",
]


# ==========================
# QIDIRUV FUNKSIYALARI
# ==========================


def _specialties_for(department):
    """
    Bo'limdagi mutaxassisliklar.

    Nazariya bo'limi hech qaysi bitta mutaxassislikka tegishli
    emas - u barcha yo'nalishlarga dars beradi.
    """

    if department == THEORY_DEPARTMENT:
        return sorted(CURRICULUM)

    return DEPARTMENT_SPECIALTIES.get(department, [])


def department_subjects(department):
    """
    Bo'limdagi barcha fanlar: [(fan, {sinf: soat}), ...]

    Bo'limda bir nechta mutaxassislik bo'lsa, fanlar birlashtiriladi.
    Bir xil fan turli mutaxassislikda turli soat olsa - o'rtachasi
    olinadi (aniq qiymat sinf bilan birga planned_hours dan topiladi).
    """

    merged = {}

    for specialty in _specialties_for(department):

        for subject, hours in CURRICULUM[specialty]["subjects"].items():

            if department == THEORY_DEPARTMENT and subject not in THEORY_SUBJECTS:
                continue

            target = merged.setdefault(subject, {})

            for class_name, value in hours.items():
                target.setdefault(class_name, []).append(value)

    result = []

    for subject in sorted(merged):

        hours = {
            class_name: sorted(values)[len(values) // 2]
            for class_name, values in merged[subject].items()
        }

        result.append((subject, hours))

    return result


def department_years(department):
    """Bo'limdagi ta'lim muddati (eng uzuni)."""

    years = [
        CURRICULUM[s]["years"]
        for s in _specialties_for(department)
        if s in CURRICULUM
    ]

    return max(years) if years else 7


def planned_hours(department, subject, class_name):
    """
    Reja bo'yicha haftalik soat.

    Bo'limdagi mutaxassisliklar turli qiymat bersa - hammasi
    qaytariladi, o'qituvchi tanlaydi. Reja jim tursa - bo'sh ro'yxat.
    """

    values = []

    for specialty in _specialties_for(department):

        hours = CURRICULUM[specialty]["subjects"].get(subject, {})

        value = hours.get(str(class_name))

        if value is not None and value not in values:
            values.append(value)

    return sorted(values)


def weekly_norm(specialty, class_name):
    """Bitta o'quvchining shu sinfdagi haftalik jami soati."""

    subjects = CURRICULUM.get(specialty, {}).get("subjects", {})

    return sum(
        hours.get(str(class_name), 0) for hours in subjects.values()
    )
