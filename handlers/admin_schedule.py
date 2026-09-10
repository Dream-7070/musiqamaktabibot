# ==========================
# handlers/admin_schedule.py
# ADMIN/DIREKTOR - DARS JADVALLARINI KO'RISH
# ==========================
#
# Bo'lim -> O'qituvchi -> uning barcha vaqt katakchalari
# (kun, soat, fan, xona, o'quvchilar).
#
# Admin bu yerdan istalgan o'qituvchiga **istalgan vaqtga** dars
# qo'yishi ham mumkin - o'qituvchining o'z oynasidagi tayyor
# vaqt katakchalari bilan cheklanmaydi (masalan 07:15 kabi
# jadvaldan tashqari vaqt). Bu maxsus holatlar uchun - odatiy
# dars vaqtini o'qituvchining o'zi qo'yadi.
#
# ==========================


from telebot import types

from config import ADMIN_IDS

from data.curriculum import department_subjects, specialties_for

from handlers.students import class_markup

from database import (
    plan_subject_names,
    is_cancel_text,
    get_departments,
    get_teachers_by_department,
    get_teacher_by_id,
    get_teacher_slots,
    get_slot,
    get_slot_students,
    get_department_for_teacher,
    get_own_subjects,
    get_subjects_for_teacher,
    add_subject,
    LESSON_TYPES,
    get_teacher_specialties,
    toggle_teacher_specialty,
    teacher_specialty_label,
    get_room_availability,
    create_slot,
    normalize_time,
    ACADEMIC_HOURS,
    hours_label,
    hours_to_minutes,
    DAYS_OF_WEEK,
    DEFAULT_DURATION,
    find_teacher_conflict,
    log_action
)


# chat_id -> vaqtinchalik holat (admin yangi dars qo'shayotganda)
admin_slot_ctx = {}


def register_admin_schedule(bot):


    @bot.message_handler(
        func=lambda m:
        m.text == "🗓 Dars jadvallari"
        and m.chat.id in ADMIN_IDS
    )
    def schedule_start(message):

        markup = types.InlineKeyboardMarkup()

        for index, dept in enumerate(get_departments()):

            markup.add(
                types.InlineKeyboardButton(
                    dept,
                    callback_data="adsch:dept:" + str(index)
                )
            )

        bot.send_message(
            message.chat.id,
            "🔍 Qaysi bo'lim?",
            reply_markup=markup
        )


    @bot.callback_query_handler(
        func=lambda c: c.data.startswith("adsch:")
        and c.message.chat.id in ADMIN_IDS
    )
    def dispatch(call):

        chat_id = call.message.chat.id

        message_id = call.message.message_id

        parts = call.data.split(":")

        step = parts[1]

        bot.answer_callback_query(call.id)


        if step == "dept":

            dept_index = int(parts[2])

            departments = get_departments()

            if dept_index >= len(departments):
                return

            dept = departments[dept_index]

            markup = types.InlineKeyboardMarkup()

            for teacher_id, name, status in get_teachers_by_department(dept):

                markup.add(
                    types.InlineKeyboardButton(
                        name,
                        callback_data="adsch:teacher:" + str(teacher_id) + ":" + str(dept_index)
                    )
                )

            markup.add(
                types.InlineKeyboardButton(
                    "⬅️ Bo'limlar",
                    callback_data="adsch:deptlist"
                )
            )

            bot.edit_message_text(
                "📂 " + dept + "\n\nO'qituvchini tanlang:",
                chat_id, message_id,
                reply_markup=markup
            )


        elif step == "deptlist":

            markup = types.InlineKeyboardMarkup()

            for index, dept in enumerate(get_departments()):

                markup.add(
                    types.InlineKeyboardButton(
                        dept,
                        callback_data="adsch:dept:" + str(index)
                    )
                )

            bot.edit_message_text(
                "🔍 Qaysi bo'lim?",
                chat_id, message_id,
                reply_markup=markup
            )


        elif step == "teacher":

            teacher_id, dept_index = parts[2], parts[3]

            row = get_teacher_by_id(int(teacher_id))

            if not row:
                return

            name = row[1]

            slots = get_teacher_slots(name)

            markup = types.InlineKeyboardMarkup()

            for slot_id, subject, day, time, room in slots:

                count = len(get_slot_students(slot_id))

                label = day + " " + time + " - " + subject + " (" + str(count) + " ta)"

                markup.add(
                    types.InlineKeyboardButton(
                        label,
                        callback_data="adsch:slot:" + str(slot_id) + ":" + teacher_id + ":" + dept_index
                    )
                )

            markup.add(
                types.InlineKeyboardButton(
                    "➕ Yangi dars qo'shish (istalgan vaqt)",
                    callback_data="adsl:new:" + teacher_id + ":" + dept_index
                )
            )

            # Fan qo'shish endi FAQAT adminda. O'qituvchi o'ziga fan
            # qo'sha olmaydi - u chalkashlik keltirardi (bitta fan
            # bir necha xil yozilib ketardi). Reja yetmagan hollarda
            # admin shu yerdan qo'shadi.

            markup.add(
                types.InlineKeyboardButton(
                    "📚 Fan qo'shish (rejada yo'q fan)",
                    callback_data="adsubj:new:" + teacher_id + ":" + dept_index
                )
            )

            # Yo'nalish tugmasi faqat KERAK bo'lganda - bo'limda
            # bitta yo'nalish bo'lsa tanlashning ma'nosi yo'q va
            # menyuni ortiqcha to'ldiradi.

            if len(specialties_for(get_department_for_teacher(name))) > 1:

                markup.add(
                    types.InlineKeyboardButton(
                        "🎯 Yo'nalish: " + teacher_specialty_label(name),
                        callback_data="adyon:new:" + teacher_id + ":" + dept_index
                    )
                )

            markup.add(
                types.InlineKeyboardButton(
                    "⬅️ Orqaga",
                    callback_data="adsch:dept:" + dept_index
                )
            )

            text = (
                "👨‍🏫 " + name + " - dars jadvali:"
                if slots else
                "👨‍🏫 " + name + "\n\nHali dars vaqti kiritilmagan."
            )

            bot.edit_message_text(text, chat_id, message_id, reply_markup=markup)


        elif step == "slot":

            slot_id, teacher_id, dept_index = parts[2], parts[3], parts[4]

            slot = get_slot(int(slot_id))

            if not slot:
                return

            _, teacher, subject, day, time, room = slot

            students = get_slot_students(int(slot_id))

            text = (
                "🗓 " + day + " " + time + "\n"
                "📚 " + subject + "\n"
                "🚪 Xona: " + room + "\n\n"
            )

            if students:

                text += "👨‍🎓 O'quvchilar:\n"

                for _, student, student_teacher in students:
                    text += "- " + student + " (" + student_teacher + ")\n"

            else:

                text += "👨‍🎓 O'quvchi yo'q."

            markup = types.InlineKeyboardMarkup()

            markup.add(
                types.InlineKeyboardButton(
                    "⬅️ Orqaga",
                    callback_data="adsch:teacher:" + teacher_id + ":" + dept_index
                )
            )

            bot.edit_message_text(text, chat_id, message_id, reply_markup=markup)


    # ==========================
    # ADMIN - O'QITUVCHIGA YO'NALISH BELGILASH
    # ==========================
    #
    # Bo'limda bir nechta yo'nalish bo'lishi mumkin. "Amaliy
    # san'at"da 13 ta bor, shuning uchun o'sha bo'lim o'qituvchisiga
    # dars qo'shayotganda 34 ta fan chiqardi - ko'pchiligi boshqa
    # kasbniki. Aynan shundan noto'g'ri fan tanlangan.
    #
    # Yo'nalish belgilangach, fan ro'yxati faqat o'sha yo'nalish
    # fanlaridan iborat bo'ladi (db/specialties.py).
    #
    # Bitta o'qituvchi BIR NECHTA yo'nalishda bo'lishi mumkin -
    # masalan bitta usta ham naqqoshlik, ham kashtachilik o'qitadi.
    # Shuning uchun ro'yxat "belgilash" emas, "yoqish/o'chirish".

    def _show_specialties(chat_id, teacher, teacher_id, dept_index, message_id=None):

        department = get_department_for_teacher(teacher)

        available = specialties_for(department)

        chosen = get_teacher_specialties(teacher)

        markup = types.InlineKeyboardMarkup()

        for index, name in enumerate(available):

            belgi = "✅ " if name in chosen else "▫️ "

            markup.add(
                types.InlineKeyboardButton(
                    belgi + name,
                    callback_data="adyon:tog:" + str(index)
                )
            )

        markup.add(
            types.InlineKeyboardButton(
                "⬅️ O'qituvchiga qaytish",
                callback_data="adsch:teacher:" + teacher_id + ":" + dept_index
            )
        )

        admin_slot_ctx[chat_id] = {
            "yon_teacher": teacher,
            "yon_teacher_id": teacher_id,
            "yon_dept_index": dept_index,
            "yon_list": available
        }

        # Nechta fan ko'rinishini darhol ko'rsatamiz - admin
        # tanlovining natijasini o'sha zahoti tushunsin.

        fanlar = len(plan_subject_names(teacher))

        text = (
            "🎯 " + teacher + "\n"
            "📂 Bo'lim: " + str(department) + "\n\n"
        )

        if len(available) <= 1:

            text += (
                "Bu bo'limda bitta yo'nalish bor - alohida "
                "belgilash shart emas.\n\n"
            )

        else:

            text += (
                "O'qituvchi o'qitadigan yo'nalishlarni belgilang. "
                "Bir nechtasini tanlash mumkin.\n\n"
            )

        if chosen:
            text += "Hozir: " + ", ".join(chosen) + "\n"
        else:
            text += "Hozir: belgilanmagan (butun bo'lim fanlari)\n"

        text += "📚 Dars qo'shishda ko'rinadigan fanlar: " + str(fanlar) + " ta"

        if message_id:

            try:
                bot.edit_message_text(
                    text, chat_id, message_id, reply_markup=markup
                )

                return

            except Exception:
                # xabar o'zgarmagan bo'lsa Telegram xato beradi -
                # bunday holatda yangisini yuboramiz
                pass

        bot.send_message(chat_id, text, reply_markup=markup)


    @bot.callback_query_handler(
        func=lambda c: c.data.startswith("adyon:new:")
        and c.message.chat.id in ADMIN_IDS
    )
    def admin_specialties_open(call):

        chat_id = call.message.chat.id

        _, _, teacher_id, dept_index = call.data.split(":")

        row = get_teacher_by_id(int(teacher_id))

        if not row:

            bot.answer_callback_query(call.id, "O'qituvchi topilmadi")

            return

        bot.answer_callback_query(call.id)

        _show_specialties(chat_id, row[1], teacher_id, dept_index)


    @bot.callback_query_handler(
        func=lambda c: c.data.startswith("adyon:tog:")
        and c.message.chat.id in ADMIN_IDS
    )
    def admin_specialty_toggle(call):

        chat_id = call.message.chat.id

        data = admin_slot_ctx.get(chat_id)

        if not data or "yon_list" not in data:

            bot.answer_callback_query(call.id, "Xatolik, qaytadan boshlang")

            return

        index = int(call.data.split(":", 2)[2])

        available = data["yon_list"]

        if index >= len(available):

            bot.answer_callback_query(call.id, "Topilmadi")

            return

        teacher = data["yon_teacher"]

        name = available[index]

        yoqildi = toggle_teacher_specialty(teacher, name)

        bot.answer_callback_query(
            call.id,
            ("✅ " if yoqildi else "▫️ ") + name
        )

        log_action(
            "admin",
            "yo'nalish " + ("yoqdi" if yoqildi else "o'chirdi"),
            teacher,
            name,
            actor_role="admin"
        )

        _show_specialties(
            chat_id, teacher,
            data["yon_teacher_id"], data["yon_dept_index"],
            message_id=call.message.message_id
        )


    # ==========================
    # ADMIN - O'QITUVCHIGA FAN QO'SHISH
    # ==========================
    #
    # Ilgari o'qituvchi o'ziga fan qo'sha olardi. Amalda bu juda
    # ko'p chalkashlik keltirdi: bitta fan bir necha xil yozilib
    # ketdi ("Notani varoqdan uqish" <- "Notani varaqdan o'qish"),
    # natijada jadval o'quv rejasi bilan mos kelmay qoldi.
    #
    # Endi o'qituvchi faqat TANLAYDI, qo'shish esa shu yerda -
    # adminda. Reja bo'lmagan yo'nalishlar (masalan amaliy san'at
    # to'garaklari) uchun kerak bo'ladi.

    @bot.callback_query_handler(
        func=lambda c: c.data.startswith("adsubj:new:")
        and c.message.chat.id in ADMIN_IDS
    )
    def admin_new_subject(call):

        chat_id = call.message.chat.id

        _, _, teacher_id, dept_index = call.data.split(":")

        row = get_teacher_by_id(int(teacher_id))

        if not row:

            bot.answer_callback_query(call.id, "O'qituvchi topilmadi")

            return

        teacher = row[1]

        department = get_department_for_teacher(teacher)

        plan = [name for name, _ in department_subjects(department)]

        admin_slot_ctx[chat_id] = {
            "subj_teacher": teacher,
            "subj_teacher_id": teacher_id,
            "subj_dept_index": dept_index
        }

        bot.answer_callback_query(call.id)

        # Rejada nima borligini ko'rsatamiz - admin bexosdan
        # rejadagi fanni qaytadan yozib qo'ymasin.

        text = "📚 " + teacher + " uchun yangi fan.\n\n"

        if plan:

            text += (
                "Rejada allaqachon bor (qayta yozish shart emas):\n"
                + "\n".join("  • " + p for p in plan) + "\n\n"
            )

        text += "Yangi fan nomini yozing:"

        sent = bot.send_message(chat_id, text)

        bot.register_next_step_handler(sent, admin_subject_type)


    def admin_subject_type(message):

        chat_id = message.chat.id

        if is_cancel_text(message.text):

            admin_slot_ctx.pop(chat_id, None)

            bot.send_message(chat_id, "❌ Bekor qilindi.")

            return

        data = admin_slot_ctx.get(chat_id)

        if not data or "subj_teacher" not in data:

            bot.send_message(chat_id, "❌ Xatolik. Qaytadan boshlang.")

            return

        name = (message.text or "").strip()

        if len(name) < 2:

            bot.send_message(chat_id, "❌ Fan nomi juda qisqa. Qaytadan boshlang.")

            admin_slot_ctx.pop(chat_id, None)

            return

        data["subj_name"] = name

        markup = types.InlineKeyboardMarkup()

        for key, label in LESSON_TYPES.items():

            markup.add(
                types.InlineKeyboardButton(
                    label,
                    callback_data="adsubj:type:" + key
                )
            )

        bot.send_message(
            chat_id,
            "«" + name + "» qanday o'tiladi?",
            reply_markup=markup
        )


    @bot.callback_query_handler(
        func=lambda c: c.data.startswith("adsubj:type:")
        and c.message.chat.id in ADMIN_IDS
    )
    def admin_subject_save(call):

        chat_id = call.message.chat.id

        data = admin_slot_ctx.get(chat_id)

        if not data or "subj_name" not in data:

            bot.answer_callback_query(call.id, "Xatolik, qaytadan boshlang")

            return

        lesson_type = call.data.split(":", 2)[2]

        if lesson_type not in LESSON_TYPES:

            bot.answer_callback_query(call.id, "Noto'g'ri tur")

            return

        teacher = data["subj_teacher"]
        name = data["subj_name"]

        added = add_subject(teacher, name, lesson_type)

        if added:

            bot.answer_callback_query(call.id, "✅ Qo'shildi")

            log_action(
                "admin",
                "fan qo'shdi",
                teacher,
                name + " (" + lesson_type + ")",
                actor_role="admin"
            )

            bot.send_message(
                chat_id,
                "✅ Fan qo'shildi: " + name + "\n"
                + LESSON_TYPES[lesson_type] + "\n"
                + "👨‍🏫 " + teacher + "\n\n"
                "Endi bu fan o'qituvchining dars qo'shish ro'yxatida chiqadi."
            )

        else:

            bot.answer_callback_query(call.id, "Bunday fan allaqachon bor")

            bot.send_message(
                chat_id,
                "ℹ️ «" + name + "» allaqachon mavjud - qayta qo'shilmadi."
            )

        admin_slot_ctx.pop(chat_id, None)


    # ==========================
    # ADMIN - ISTALGAN VAQTGA DARS QO'SHISH
    # ==========================
    #
    # O'qituvchining o'z oynasidagi tayyor vaqt katakchalari bilan
    # cheklanmaydi - istalgan vaqt (masalan 07:15) kiritiladi.
    # Xona va o'qituvchi to'qnashuvi baribir tekshiriladi.

    @bot.callback_query_handler(
        func=lambda c: c.data.startswith("adsl:new:")
        and c.message.chat.id in ADMIN_IDS
    )
    def new_static_slot(call):

        chat_id = call.message.chat.id

        _, _, teacher_id, dept_index = call.data.split(":")

        row = get_teacher_by_id(int(teacher_id))

        if not row:

            bot.answer_callback_query(call.id, "O'qituvchi topilmadi")

            return

        teacher = row[1]

        # Fan ro'yxati YAGONA manbadan - db/specialties.py.
        # Ilgari bu ro'yxat uch joyda alohida qurilardi (bot,
        # admin paneli, Mini App) va ular bir-biridan farq qilib
        # ketgan edi. Endi hammasi shu funksiyani chaqiradi.
        #
        # O'qituvchiga yo'nalish belgilangan bo'lsa - faqat o'sha
        # yo'nalish fanlari, aks holda butun bo'lim fanlari.

        names = plan_subject_names(teacher)

        if not names:
            names = [r[1] for r in get_subjects_for_teacher(teacher)]

        admin_slot_ctx[chat_id] = {
            "teacher": teacher,
            "teacher_id": teacher_id,
            "dept_index": dept_index,
            "names": names
        }

        bot.answer_callback_query(call.id)

        markup = types.InlineKeyboardMarkup()

        for index, name in enumerate(names):

            markup.add(
                types.InlineKeyboardButton(
                    name,
                    callback_data="adsl:subj:" + str(index)
                )
            )

        bot.send_message(
            chat_id,
            "📚 " + teacher + " uchun fanni tanlang:",
            reply_markup=markup
        )


    @bot.callback_query_handler(
        func=lambda c: c.data.startswith("adsl:subj:")
        and c.message.chat.id in ADMIN_IDS
    )
    def static_slot_subject(call):

        chat_id = call.message.chat.id

        data = admin_slot_ctx.get(chat_id)

        if not data:

            bot.answer_callback_query(call.id, "Qaytadan boshlang")

            return

        index = int(call.data.split(":")[2])

        if index >= len(data["names"]):

            bot.answer_callback_query(call.id, "Topilmadi")

            return

        data["subject"] = data["names"][index]

        bot.answer_callback_query(call.id)

        bot.send_message(
            chat_id, "📐 Qaysi sinf uchun?",
            reply_markup=class_markup("adsl:class")
        )


    @bot.callback_query_handler(
        func=lambda c: c.data.startswith("adsl:class:")
        and c.message.chat.id in ADMIN_IDS
    )
    def static_slot_class(call):

        chat_id = call.message.chat.id

        data = admin_slot_ctx.get(chat_id)

        if not data or "subject" not in data:

            bot.answer_callback_query(call.id, "Qaytadan boshlang")

            return

        data["class"] = call.data.split(":", 2)[2]

        bot.answer_callback_query(call.id)

        markup = types.InlineKeyboardMarkup(row_width=2)

        markup.add(*[
            types.InlineKeyboardButton(day, callback_data="adsl:day:" + day)
            for day in DAYS_OF_WEEK
        ])

        bot.send_message(chat_id, "🗓 Hafta kuni?", reply_markup=markup)


    @bot.callback_query_handler(
        func=lambda c: c.data.startswith("adsl:day:")
        and c.message.chat.id in ADMIN_IDS
    )
    def static_slot_day(call):

        chat_id = call.message.chat.id

        data = admin_slot_ctx.get(chat_id)

        if not data or "class" not in data:

            bot.answer_callback_query(call.id, "Qaytadan boshlang")

            return

        data["day"] = call.data.split(":", 2)[2]

        bot.answer_callback_query(call.id)

        sent = bot.send_message(
            chat_id,
            "🕐 Soatni yozing (masalan: 07:15 yoki 7:15):\n\n"
            "Odatiy jadval katakchalari bilan cheklanmaydi - "
            "istalgan vaqtni kiritishingiz mumkin."
        )

        bot.register_next_step_handler(sent, static_slot_time)


    def static_slot_time(message):

        chat_id = message.chat.id

        if is_cancel_text(message.text):
            admin_slot_ctx.pop(chat_id, None)
            bot.send_message(chat_id, "❌ Bekor qilindi.")
            return

        data = admin_slot_ctx.get(chat_id)

        if not data or "day" not in data:
            return

        time = normalize_time(message.text)

        if not time:

            sent = bot.send_message(
                chat_id,
                "❌ Tushunarsiz vaqt. Masalan: 07:15\n\nQaytadan yozing:"
            )

            bot.register_next_step_handler(sent, static_slot_time)

            return

        data["time"] = time

        markup = types.InlineKeyboardMarkup()

        for index, hours in enumerate(ACADEMIC_HOURS):

            markup.add(
                types.InlineKeyboardButton(
                    hours_label(hours),
                    callback_data="adsl:dur:" + str(index)
                )
            )

        bot.send_message(chat_id, "⏱ Dars davomiyligi?", reply_markup=markup)


    @bot.callback_query_handler(
        func=lambda c: c.data.startswith("adsl:dur:")
        and c.message.chat.id in ADMIN_IDS
    )
    def static_slot_duration(call):

        chat_id = call.message.chat.id

        data = admin_slot_ctx.get(chat_id)

        if not data or "time" not in data:

            bot.answer_callback_query(call.id, "Qaytadan boshlang")

            return

        index = int(call.data.split(":")[2])

        if index >= len(ACADEMIC_HOURS):

            bot.answer_callback_query(call.id, "Topilmadi")

            return

        data["hours"] = ACADEMIC_HOURS[index]

        duration = hours_to_minutes(data["hours"])

        data["duration"] = duration

        teacher_busy = find_teacher_conflict(
            data["teacher"], data["day"], data["time"], duration
        )

        if teacher_busy:

            bot.answer_callback_query(call.id, "⚠️ O'qituvchi band")

            bot.send_message(
                chat_id,
                "⚠️ " + data["teacher"] + " " + data["day"] + " kuni "
                + data["time"] + " da band:\n\n"
                "📚 " + teacher_busy[2] + " (xona " + teacher_busy[4] + ")\n\n"
                "Boshqa vaqt tanlang."
            )

            admin_slot_ctx.pop(chat_id, None)

            return

        bot.answer_callback_query(call.id)

        rooms = get_room_availability(data["day"], data["time"], duration)

        data["rooms"] = rooms

        markup = types.InlineKeyboardMarkup(row_width=3)

        row = []

        for i, r in enumerate(rooms):

            lock = "🔒 " if r["busy"] else ""

            if r["name"]:

                if row:
                    markup.row(*row)
                    row = []

                markup.row(types.InlineKeyboardButton(
                    lock + r["label"], callback_data="adsl:room:" + str(i)
                ))

                continue

            row.append(types.InlineKeyboardButton(
                lock + r["room"], callback_data="adsl:room:" + str(i)
            ))

            if len(row) == 3:
                markup.row(*row)
                row = []

        if row:
            markup.row(*row)

        bot.send_message(
            chat_id,
            "🚪 " + data["day"] + " kuni " + data["time"] + " da qaysi xonada?",
            reply_markup=markup
        )


    @bot.callback_query_handler(
        func=lambda c: c.data.startswith("adsl:room:")
        and c.message.chat.id in ADMIN_IDS
    )
    def static_slot_room(call):

        chat_id = call.message.chat.id

        data = admin_slot_ctx.get(chat_id)

        if not data or "rooms" not in data:

            bot.answer_callback_query(call.id, "Qaytadan boshlang")

            return

        index = int(call.data.split(":")[2])

        if index >= len(data["rooms"]):

            bot.answer_callback_query(call.id, "Topilmadi")

            return

        chosen = data["rooms"][index]

        if chosen["busy"]:

            bot.answer_callback_query(call.id, chosen["room"] + " band")

            bot.send_message(
                chat_id,
                "⚠️ " + chosen["label"] + " " + data["day"] + " kuni "
                + chosen["time"] + " da band:\n\n"
                "📚 " + chosen["subject"] + " · 👨‍🏫 " + chosen["teacher"] + "\n\n"
                "Boshqa xona tanlang."
            )

            return

        bot.answer_callback_query(call.id)

        slot_id = create_slot(
            data["teacher"], data["subject"], data["day"], data["time"],
            chosen["room"], data.get("duration", DEFAULT_DURATION),
            data.get("class")
        )

        log_action(
            str(chat_id), "admin dars qo'shdi (statik vaqt)",
            data["teacher"], data["subject"] + " " + data["day"] + " "
            + data["time"] + ", xona " + chosen["room"],
            actor_role="admin"
        )

        bot.send_message(
            chat_id,
            "✅ Qo'shildi: " + data["teacher"] + "\n"
            + data["day"] + " " + data["time"] + " - " + data["subject"] + "\n"
            "🚪 Xona " + chosen["room"]
        )

        teacher_id = data.get("teacher_id", "0")
        dept_index = data.get("dept_index", "0")

        admin_slot_ctx.pop(chat_id, None)

        markup2 = types.InlineKeyboardMarkup()

        markup2.add(
            types.InlineKeyboardButton(
                "⬅️ " + data["teacher"] + "ning jadvaliga qaytish",
                callback_data="adsch:teacher:" + teacher_id + ":" + dept_index
            )
        )

        bot.send_message(chat_id, "Davom etasizmi?", reply_markup=markup2)
