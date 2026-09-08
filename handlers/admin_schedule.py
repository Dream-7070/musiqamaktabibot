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

from data.curriculum import department_subjects

from handlers.students import class_markup

from database import (
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

        department = get_department_for_teacher(teacher)

        plan = [name for name, _ in department_subjects(department)]

        own = [r[1] for r in get_own_subjects(teacher)]

        names = plan + [n for n in own if n not in plan]

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
