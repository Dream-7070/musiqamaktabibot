# ==========================
# handlers/admin_schedule.py
# ADMIN/DIREKTOR - DARS JADVALLARINI KO'RISH
# ==========================
#
# Bo'lim -> O'qituvchi -> uning barcha vaqt katakchalari
# (kun, soat, fan, xona, o'quvchilar). Faqat ko'rish uchun.
#
# ==========================


from telebot import types

from config import ADMIN_IDS

from database import (
    get_departments,
    get_teachers_by_department,
    get_teacher_by_id,
    get_teacher_slots,
    get_slot,
    get_slot_students
)


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
