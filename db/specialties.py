# -*- coding: utf-8 -*-
# ==========================
# db/specialties.py
# O'QITUVCHI YO'NALISHLARI
# ==========================
# Nima uchun bu modul yaratilgan:
# Bo'limlarda ko'plab mutaxassisliklar bo'lishi mumkin. "Amaliy san'at"da 13 ta bor,
# shuning uchun u yerdagi o'qituvchiga dars yaratishda 34 ta fan taklif qilingan -
# ko'pchiligi boshqa kasblarga tegishli. Shu sababli noto'g'ri fanlar tanlangan.
# Endi o'qituvchi o'zi haqiqatan ham o'tadigan mutaxassisliklar bilan belgilanadi va
# fanlar ro'yxati faqat shular bilan cheklanadi. O'qituvchi bir nechta mutaxassislikka
# ega bo'lishi mumkin. Agar mutaxassislik hali belgilanmagan bo'lsa, xatti-harakat
# o'zgarmaydi (butun bo'lim) va hech kim to'sib qo'yilmaydi.
# ==========================

# Bu modul quyidagi modullardagi nomlarni ishlatadi
# (database.py fasadi ularni yuklashda joylashtiradi):
#   db.core: connect
#   db.students: get_department_for_teacher
#   db.subjects: get_own_subjects, get_subjects_for_teacher


def ensure_specialties_table():
    """
    Mutaxassisliklar jadvalini va uning indeksini yaratadi.
    Takror chaqirilganda xavfsiz (idempotent).
    """
    conn = connect()
    cur = conn.cursor()


    cur.execute("""
        CREATE TABLE IF NOT EXISTS teacher_specialties(
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            teacher   TEXT,
            specialty TEXT
        )
    """)


    cur.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_teacher_specialty
        ON teacher_specialties(teacher, specialty)
    """)


    conn.commit()
    conn.close()


def get_teacher_specialties(teacher):
    """
    O'qituvchining mutaxassisliklari ro'yxatini qaytaradi (tartiblangan holda).
    """
    if not teacher:
        return []


    conn = connect()
    cur = conn.cursor()


    cur.execute(
        "SELECT specialty FROM teacher_specialties WHERE teacher = ? ORDER BY specialty ASC",
        (teacher,)
    )
    rows = cur.fetchall()


    conn.close()


    return [row[0] for row in rows]


def set_teacher_specialties(teacher, names):
    """
    O'qituvchi uchun barcha mutaxassisliklarni bitta tranzaksiyada almashtiradi.
    Yangi o'rnatilgan mutaxassisliklar ro'yxatini tartiblangan holda qaytaradi.
    """
    if not teacher:
        return []


    clean_names = []
    for name in names:
        if name:
            val = str(name).strip()
            if val and val not in clean_names:
                clean_names.append(val)


    clean_names.sort()


    conn = connect()
    cur = conn.cursor()


    cur.execute("DELETE FROM teacher_specialties WHERE teacher = ?", (teacher,))


    for val in clean_names:
        cur.execute(
            "INSERT INTO teacher_specialties (teacher, specialty) VALUES (?, ?)",
            (teacher, val)
        )


    conn.commit()
    conn.close()


    return clean_names


def toggle_teacher_specialty(teacher, specialty):
    """
    Agar o'qituvchida bu mutaxassislik bo'lsa - uni o'chiradi va False qaytaradi.
    Aks holda qo'shadi va True qaytaradi.
    """
    if not teacher or not specialty:
        return False


    conn = connect()
    cur = conn.cursor()


    cur.execute(
        "SELECT id FROM teacher_specialties WHERE teacher = ? AND specialty = ?",
        (teacher, specialty)
    )
    row = cur.fetchone()


    if row:
        cur.execute("DELETE FROM teacher_specialties WHERE id = ?", (row[0],))
        conn.commit()
        conn.close()
        return False


    cur.execute(
        "INSERT OR IGNORE INTO teacher_specialties (teacher, specialty) VALUES (?, ?)",
        (teacher, specialty)
    )
    conn.commit()
    conn.close()


    return True


def plan_subject_names(teacher):
    """
    O'qituvchi qaysi fanlarni ishlata olishi mumkinligini belgilovchi yagona haqiqat manbai.
    """
    # Bot, admin panel va Mini App hammasi shu bitta funksiyani chaqirishi shart -
    # ro'yxat oldin uch xil joyda qayta qurilgan va ular bir-biridan farq qilib qolgan.
    if not teacher:
        return []


    from data.curriculum import department_subjects, specialty_subjects


    department = get_department_for_teacher(teacher)
    chosen = get_teacher_specialties(teacher)


    names = []


    if chosen:
        chosen_names = set()
        for s in chosen:
            subjects_list = specialty_subjects(s)
            for subj_info in subjects_list:
                chosen_names.add(subj_info[0])


        if chosen_names:
            names = sorted(list(chosen_names))
        else:
            dept_subjs = department_subjects(department) if department else []
            names = [item[0] for item in dept_subjs]


    else:
        dept_subjs = department_subjects(department) if department else []
        names = [item[0] for item in dept_subjs]


    own_subjects = get_own_subjects(teacher)
    for row in own_subjects:
        subj_name = row[1]
        if subj_name not in names:
            names.append(subj_name)


    if not names:
        fallback_list = get_subjects_for_teacher(teacher)
        names = [row[1] for row in fallback_list]


    return names


def teacher_specialty_label(teacher):
    """
    O'qituvchining mutaxassisliklarini kartada ko'rsatish uchun qisqa matn.
    """
    chosen = get_teacher_specialties(teacher)


    if not chosen:
        return "belgilanmagan"


    return ", ".join(chosen)
