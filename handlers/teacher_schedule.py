# ==========================
# handlers/teacher_schedule.py
# O'QITUVCHI - DARS JADVALI (vaqt katakchalari)
# ==========================
#
# Har bir o'qituvchi o'z haftalik vaqt katakchalarini
# (kun+soat+fan+xona) tuzadi va shu katakchaga o'quvchi
# qo'shadi - hatto ular boshqa o'qituvchining o'quvchisi
# bo'lsa ham (butun maktab bo'yicha qidirib topiladi).
#
# ==========================


from telebot import types

from database import (
    DAYS_OF_WEEK,
    SUBJECTS,
    create_slot,
    get_teacher_slots,
    get_slot,
    delete_slot,
    get_slot_students,
    add_student_to_slot,
    remove_slot_student,
    search_students
)


# chat_id -> vaqtinchalik holat (yangi slot yaratish, qidiruv natijalari)
ctx = {}


def register_teacher_schedule(bot, selected_teachers):


    # ==========================
    # KIRISH - VAQTLAR RO'YXATI
    # ==========================

    @bot.message_handler(
        func=lambda m: m.text == "🗓 Dars jadvali"
    )
    def schedule_start(message):

        teacher = selected_teachers.get(message.chat.id)

        if not teacher:

            bot.send_message(
                message.chat.id,
                "❌ Avval o'qituvchini tanlang."
            )

            return

        _show_slot_list(message.chat.id, teacher)


    def _show_slot_list(chat_id, teacher):

        slots = get_teacher_slots(teacher)

        markup = types.InlineKeyboardMarkup()

        for slot_id, subject, day, time, room in slots:

            count = len(get_slot_students(slot_id))

            label = day + " " + time + " - " + subject + " (" + str(count) + " ta)"

            markup.add(
                types.InlineKeyboardButton(
                    label,
                    callback_data="tsch:view:" + str(slot_id)
                )
            )

        markup.add(
            types.InlineKeyboardButton(
                "➕ Yangi vaqt qo'shish",
                callback_data="tsch:new"
            )
        )

        text = (
            "🗓 " + teacher + " - dars jadvali:"
            if slots else
            "🗓 Hali dars vaqti kiritilmagan."
        )

        bot.send_message(chat_id, text, reply_markup=markup)


    @bot.callback_query_handler(
        func=lambda c: c.data == "tsch:list"
    )
    def back_to_list(call):

        teacher = selected_teachers.get(call.message.chat.id)

        bot.answer_callback_query(call.id)

        if teacher:
            _show_slot_list(call.message.chat.id, teacher)


    # ==========================
    # YANGI VAQT QO'SHISH
    # ==========================

    @bot.callback_query_handler(
        func=lambda c: c.data == "tsch:new"
    )
    def new_slot_subject(call):

        markup = types.InlineKeyboardMarkup()

        for index, subject in enumerate(SUBJECTS):

            markup.add(
                types.InlineKeyboardButton(
                    subject,
                    callback_data="tsch:subj:" + str(index)
                )
            )

        bot.answer_callback_query(call.id)

        bot.send_message(
            call.message.chat.id,
            "📚 Fanni tanlang:",
            reply_markup=markup
        )


    @bot.callback_query_handler(
        func=lambda c: c.data.startswith("tsch:subj:")
    )
    def new_slot_day(call):

        chat_id = call.message.chat.id

        index = int(call.data.split(":", 2)[2])

        ctx[chat_id] = {"subject": SUBJECTS[index]}

        markup = types.InlineKeyboardMarkup()

        for day_index, day in enumerate(DAYS_OF_WEEK):

            markup.add(
                types.InlineKeyboardButton(
                    day,
                    callback_data="tsch:day:" + str(day_index)
                )
            )

        bot.answer_callback_query(call.id)

        bot.send_message(chat_id, "📅 Qaysi kun?", reply_markup=markup)


    @bot.callback_query_handler(
        func=lambda c: c.data.startswith("tsch:day:")
    )
    def new_slot_time(call):

        chat_id = call.message.chat.id

        if chat_id not in ctx:

            bot.answer_callback_query(call.id, "Xatolik, qaytadan boshlang")

            return

        index = int(call.data.split(":", 2)[2])

        ctx[chat_id]["day"] = DAYS_OF_WEEK[index]

        bot.answer_callback_query(call.id)

        sent = bot.send_message(
            chat_id,
            "🕐 Soat nechida? (masalan: 15:00)"
        )

        bot.register_next_step_handler(sent, new_slot_room)


    def new_slot_room(message):

        chat_id = message.chat.id

        data = ctx.get(chat_id)

        if not data or "day" not in data:

            bot.send_message(chat_id, "❌ Xatolik yuz berdi. Qaytadan boshlang.")

            return

        data["time"] = message.text.strip()

        sent = bot.send_message(
            chat_id,
            "🚪 Xona raqami? (masalan: 12)"
        )

        bot.register_next_step_handler(sent, new_slot_save)


    def new_slot_save(message):

        chat_id = message.chat.id

        data = ctx.get(chat_id)

        teacher = selected_teachers.get(chat_id)

        if not data or "time" not in data or not teacher:

            bot.send_message(chat_id, "❌ Xatolik yuz berdi. Qaytadan boshlang.")

            return

        room = message.text.strip()

        slot_id = create_slot(
            teacher,
            data["subject"],
            data["day"],
            data["time"],
            room
        )

        ctx.pop(chat_id, None)

        bot.send_message(
            chat_id,
            "✅ Qo'shildi: " + data["day"] + " " + data["time"]
            + " - " + data["subject"] + " (xona " + room + ")"
        )

        _show_slot_detail(chat_id, slot_id)


    # ==========================
    # VAQT KATAKCHASI TAFSILOTI
    # ==========================

    def _show_slot_detail(chat_id, slot_id):

        slot = get_slot(slot_id)

        if not slot:

            bot.send_message(chat_id, "❌ Topilmadi.")

            return

        _, teacher, subject, day, time, room = slot

        students = get_slot_students(slot_id)

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

            text += "👨‍🎓 Hali o'quvchi qo'shilmagan."

        markup = types.InlineKeyboardMarkup()

        markup.add(
            types.InlineKeyboardButton(
                "➕ O'quvchi qo'shish",
                callback_data="tsch:addstud:" + str(slot_id)
            )
        )

        for row_id, student, student_teacher in students:

            markup.add(
                types.InlineKeyboardButton(
                    "🗑 " + student[:35],
                    callback_data="tsch:delstud:" + str(row_id) + ":" + str(slot_id)
                )
            )

        markup.add(
            types.InlineKeyboardButton(
                "🗑 Bu vaqtni butunlay o'chirish",
                callback_data="tsch:delslot:" + str(slot_id)
            )
        )

        markup.add(
            types.InlineKeyboardButton(
                "⬅️ Ro'yxatga qaytish",
                callback_data="tsch:list"
            )
        )

        bot.send_message(chat_id, text, reply_markup=markup)


    @bot.callback_query_handler(
        func=lambda c: c.data.startswith("tsch:view:")
    )
    def view_slot(call):

        slot_id = int(call.data.split(":", 2)[2])

        bot.answer_callback_query(call.id)

        _show_slot_detail(call.message.chat.id, slot_id)


    @bot.callback_query_handler(
        func=lambda c: c.data.startswith("tsch:delslot:")
    )
    def delete_slot_handler(call):

        slot_id = int(call.data.split(":", 2)[2])

        delete_slot(slot_id)

        bot.answer_callback_query(call.id, "🗑 O'chirildi")

        teacher = selected_teachers.get(call.message.chat.id)

        if teacher:
            _show_slot_list(call.message.chat.id, teacher)


    # ==========================
    # O'QUVCHI QO'SHISH (butun maktab bo'yicha qidiruv)
    # ==========================

    @bot.callback_query_handler(
        func=lambda c: c.data.startswith("tsch:addstud:")
    )
    def add_student_start(call):

        chat_id = call.message.chat.id

        slot_id = int(call.data.split(":", 2)[2])

        ctx[chat_id] = {"slot_id": slot_id}

        bot.answer_callback_query(call.id)

        sent = bot.send_message(
            chat_id,
            "🔍 O'quvchi ism-familiyasini (yoki bir qismini) yozing:"
        )

        bot.register_next_step_handler(sent, add_student_search)


    def add_student_search(message):

        chat_id = message.chat.id

        data = ctx.get(chat_id)

        if not data or "slot_id" not in data:

            bot.send_message(chat_id, "❌ Xatolik yuz berdi. Qaytadan boshlang.")

            return

        query = message.text.strip()

        results = search_students(query)

        if not results:

            bot.send_message(
                chat_id,
                "❌ Topilmadi. Qaytadan qidiring:"
            )

            bot.register_next_step_handler(message, add_student_search)

            return

        data["results"] = results

        markup = types.InlineKeyboardMarkup()

        for index, (teacher, student) in enumerate(results):

            markup.add(
                types.InlineKeyboardButton(
                    student + " (" + teacher + ")",
                    callback_data="tsch:pick:" + str(index)
                )
            )

        bot.send_message(
            chat_id,
            "Topilgan o'quvchilar:",
            reply_markup=markup
        )


    @bot.callback_query_handler(
        func=lambda c: c.data.startswith("tsch:pick:")
    )
    def add_student_pick(call):

        chat_id = call.message.chat.id

        data = ctx.get(chat_id)

        if not data or "results" not in data or "slot_id" not in data:

            bot.answer_callback_query(call.id, "Xatolik, qaytadan boshlang")

            return

        index = int(call.data.split(":", 2)[2])

        results = data["results"]

        if index >= len(results):

            bot.answer_callback_query(call.id, "Topilmadi")

            return

        student_teacher, student = results[index]

        added = add_student_to_slot(data["slot_id"], student, student_teacher)

        bot.answer_callback_query(
            call.id,
            "✅ Qo'shildi" if added else "Allaqachon qo'shilgan"
        )

        slot_id = data["slot_id"]

        ctx.pop(chat_id, None)

        _show_slot_detail(chat_id, slot_id)


    @bot.callback_query_handler(
        func=lambda c: c.data.startswith("tsch:delstud:")
    )
    def remove_student(call):

        _, _, row_id, slot_id = call.data.split(":")

        remove_slot_student(int(row_id))

        bot.answer_callback_query(call.id, "🗑 O'chirildi")

        _show_slot_detail(call.message.chat.id, int(slot_id))
