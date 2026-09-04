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
# FANLAR
#   Umumiy fanlardan tashqari o'qituvchi o'ziga fan qo'sha
#   oladi - masalan Tasviriy san'atda "Rang tasvir" va
#   "Qalam tasvir". Fan qo'shilayotganda yakka tartibdagi
#   yoki guruhli mashg'ulot ekani tanlanadi.
#
# JO'RNAVOZLAR
#   Bitta darsga bir nechta jo'rnavoz biriktirilishi mumkin.
#   Jo'rnavozning o'zi «🎹 Jo'rnavozligim» orqali o'qituvchini
#   qidirib, uning dars vaqtiga biriktiriladi. Dars egasiga
#   xabar boradi va u keraksiz biriktirmani olib tashlay oladi.
#
# ==========================


from telebot import types

from database import (
    DAYS_OF_WEEK,
    LESSON_TYPES,
    create_slot,
    get_teacher_slots,
    get_slot,
    delete_slot,
    get_slot_students,
    add_student_to_slot,
    remove_slot_student,
    search_students,
    search_teachers_by_name,
    get_subjects_for_teacher,
    get_own_subjects,
    get_subject,
    get_subject_type,
    add_subject,
    delete_subject,
    rename_subject,
    set_subject_type,
    count_slots_using_subject,
    add_concertmaster,
    remove_concertmaster,
    get_slot_concertmasters,
    get_concertmaster_slots,
    get_teacher_chat_id
)


# chat_id -> vaqtinchalik holat (yangi slot yaratish, qidiruv natijalari)
ctx = {}


def _type_icon(lesson_type):

    return "👥" if lesson_type == "guruh" else "👤"


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

            label = (
                day + " " + time + " - " + subject
                + " (" + str(count) + " ta)"
            )

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

        markup.add(
            types.InlineKeyboardButton(
                "📚 Fanlarim",
                callback_data="tsch:subjects"
            )
        )

        markup.add(
            types.InlineKeyboardButton(
                "🎹 Jo'rnavozligim",
                callback_data="tcm:menu"
            )
        )

        text = (
            "🗓 " + teacher + " - dars jadvali:"
            if slots else
            "🗓 Hali dars vaqti kiritilmagan."
        )


        # boshqa o'qituvchilarning darslarida jo'rnavoz bo'lsa -
        # ular ham shu yerda ko'rinib tursin

        cm_slots = get_concertmaster_slots(teacher)

        if cm_slots:

            text += "\n\n🎹 Jo'rnavoz sifatida:\n"

            for _, owner, subject, day, time, room in cm_slots:

                text += (
                    "• " + day + " " + time + " - " + subject
                    + " (" + owner + ", xona " + room + ")\n"
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
    # FANLARIM
    # ==========================

    def _show_subjects(chat_id, teacher):

        own = get_own_subjects(teacher)

        markup = types.InlineKeyboardMarkup()

        for subject_id, name, lesson_type in own:

            markup.add(
                types.InlineKeyboardButton(
                    _type_icon(lesson_type) + " " + name,
                    callback_data="tsch:sv:" + str(subject_id)
                )
            )

        markup.add(
            types.InlineKeyboardButton(
                "➕ Yangi fan qo'shish",
                callback_data="tsch:newsubj"
            )
        )

        markup.add(
            types.InlineKeyboardButton(
                "⬅️ Jadvalga qaytish",
                callback_data="tsch:list"
            )
        )

        if own:

            text = (
                "📚 O'zingiz qo'shgan fanlar:\n\n"
                "👤 - yakka tartibdagi, 👥 - guruhli mashg'ulot\n\n"
                "Tahrirlash yoki o'chirish uchun fan ustiga bosing."
            )

        else:

            text = (
                "📚 Siz hali o'zingizga fan qo'shmagansiz.\n\n"
                "Umumiy fanlar (Mutaxassislik, Solfedjio va h.k.) "
                "baribir mavjud. Bu yerga faqat o'z yo'nalishingizdagi "
                "fanlarni qo'shasiz - masalan «Rang tasvir», «Qalam tasvir»."
            )

        bot.send_message(chat_id, text, reply_markup=markup)


    @bot.callback_query_handler(
        func=lambda c: c.data == "tsch:subjects"
    )
    def subjects_menu(call):

        teacher = selected_teachers.get(call.message.chat.id)

        bot.answer_callback_query(call.id)

        if teacher:
            _show_subjects(call.message.chat.id, teacher)


    # ==========================
    # BITTA FAN - TAHRIRLASH
    # ==========================

    def _show_subject_detail(chat_id, teacher, subject_id):

        row = get_subject(subject_id)

        if not row or row[1] != teacher:

            bot.send_message(chat_id, "❌ Fan topilmadi.")

            return

        _, _, name, lesson_type = row

        used = count_slots_using_subject(teacher, name)

        text = (
            "📚 " + name + "\n"
            + LESSON_TYPES[lesson_type] + " mashg'ulot\n\n"
        )

        if used:

            text += (
                "🗓 Bu fan bo'yicha " + str(used) + " ta dars vaqti tuzilgan.\n"
                "Nomini o'zgartirsangiz, ular ham yangilanadi."
            )

        else:

            text += "🗓 Bu fan bo'yicha hali dars vaqti tuzilmagan."

        other = "guruh" if lesson_type == "yakka" else "yakka"

        markup = types.InlineKeyboardMarkup()

        markup.add(
            types.InlineKeyboardButton(
                "✏️ Nomini o'zgartirish",
                callback_data="tsch:sren:" + str(subject_id)
            )
        )

        markup.add(
            types.InlineKeyboardButton(
                "🔄 " + LESSON_TYPES[other] + " qilish",
                callback_data="tsch:stog:" + str(subject_id)
            )
        )

        markup.add(
            types.InlineKeyboardButton(
                "🗑 Fanni o'chirish",
                callback_data="tsch:delsubj:" + str(subject_id)
            )
        )

        markup.add(
            types.InlineKeyboardButton(
                "⬅️ Fanlarga qaytish",
                callback_data="tsch:subjects"
            )
        )

        bot.send_message(chat_id, text, reply_markup=markup)


    @bot.callback_query_handler(
        func=lambda c: c.data.startswith("tsch:sv:")
    )
    def subject_detail(call):

        chat_id = call.message.chat.id

        teacher = selected_teachers.get(chat_id)

        bot.answer_callback_query(call.id)

        if teacher:

            _show_subject_detail(
                chat_id, teacher, int(call.data.split(":", 2)[2])
            )


    @bot.callback_query_handler(
        func=lambda c: c.data.startswith("tsch:stog:")
    )
    def subject_toggle_type(call):

        chat_id = call.message.chat.id

        teacher = selected_teachers.get(chat_id)

        subject_id = int(call.data.split(":", 2)[2])

        row = get_subject(subject_id)

        if not teacher or not row or row[1] != teacher:

            bot.answer_callback_query(call.id, "Fan topilmadi")

            return

        other = "guruh" if row[3] == "yakka" else "yakka"

        set_subject_type(subject_id, teacher, other)

        bot.answer_callback_query(call.id, "✅ O'zgartirildi")

        _show_subject_detail(chat_id, teacher, subject_id)


    @bot.callback_query_handler(
        func=lambda c: c.data.startswith("tsch:sren:")
    )
    def subject_rename_ask(call):

        chat_id = call.message.chat.id

        subject_id = int(call.data.split(":", 2)[2])

        row = get_subject(subject_id)

        if not row:

            bot.answer_callback_query(call.id, "Fan topilmadi")

            return

        ctx[chat_id] = {"rename_id": subject_id}

        bot.answer_callback_query(call.id)

        sent = bot.send_message(
            chat_id,
            "✏️ «" + row[2] + "» uchun yangi nom yozing:"
        )

        bot.register_next_step_handler(sent, subject_rename_save)


    def subject_rename_save(message):

        chat_id = message.chat.id

        data = ctx.pop(chat_id, None)

        teacher = selected_teachers.get(chat_id)

        if not data or "rename_id" not in data or not teacher:

            bot.send_message(chat_id, "❌ Xatolik. Qaytadan boshlang.")

            return

        ok, info = rename_subject(
            data["rename_id"], teacher, message.text
        )

        if ok:

            bot.send_message(
                chat_id,
                "✅ Nomi o'zgartirildi: " + info
                + " → " + message.text.strip()
            )

        else:

            bot.send_message(chat_id, "❌ " + info)

        _show_subject_detail(chat_id, teacher, data["rename_id"])


    @bot.callback_query_handler(
        func=lambda c: c.data == "tsch:newsubj"
    )
    def new_subject_name(call):

        bot.answer_callback_query(call.id)

        sent = bot.send_message(
            call.message.chat.id,
            "📚 Yangi fan nomini yozing:\n\nMasalan: Rang tasvir"
        )

        bot.register_next_step_handler(sent, new_subject_type)


    def new_subject_type(message):

        chat_id = message.chat.id

        name = (message.text or "").strip()

        if len(name) < 2:

            bot.send_message(chat_id, "❌ Fan nomi juda qisqa. Qaytadan boshlang.")

            return

        ctx[chat_id] = {"subject_name": name}

        markup = types.InlineKeyboardMarkup()

        for key, label in LESSON_TYPES.items():

            markup.add(
                types.InlineKeyboardButton(
                    label,
                    callback_data="tsch:stype:" + key
                )
            )

        bot.send_message(
            chat_id,
            "«" + name + "» qanday o'tiladi?",
            reply_markup=markup
        )


    @bot.callback_query_handler(
        func=lambda c: c.data.startswith("tsch:stype:")
    )
    def new_subject_save(call):

        chat_id = call.message.chat.id

        data = ctx.pop(chat_id, None)

        teacher = selected_teachers.get(chat_id)

        if not data or "subject_name" not in data or not teacher:

            bot.answer_callback_query(call.id, "Xatolik, qaytadan boshlang")

            return

        lesson_type = call.data.split(":", 2)[2]

        added = add_subject(teacher, data["subject_name"], lesson_type)

        if added:

            bot.answer_callback_query(call.id, "✅ Qo'shildi")

            bot.send_message(
                chat_id,
                "✅ Fan qo'shildi: " + data["subject_name"]
                + " (" + LESSON_TYPES[lesson_type] + ")"
            )

        else:

            bot.answer_callback_query(call.id, "Bunday fan allaqachon bor")

        _show_subjects(chat_id, teacher)


    @bot.callback_query_handler(
        func=lambda c: c.data.startswith("tsch:delsubj:")
    )
    def delete_subject_handler(call):

        chat_id = call.message.chat.id

        teacher = selected_teachers.get(chat_id)

        subject_id = int(call.data.split(":", 2)[2])

        if teacher and delete_subject(subject_id, teacher):

            bot.answer_callback_query(call.id, "🗑 O'chirildi")

        else:

            bot.answer_callback_query(call.id, "O'chirib bo'lmadi")

        if teacher:
            _show_subjects(chat_id, teacher)


    # ==========================
    # YANGI VAQT QO'SHISH
    # ==========================

    @bot.callback_query_handler(
        func=lambda c: c.data == "tsch:new"
    )
    def new_slot_subject(call):

        chat_id = call.message.chat.id

        teacher = selected_teachers.get(chat_id)

        if not teacher:

            bot.answer_callback_query(call.id, "Avval o'qituvchini tanlang")

            return

        markup = types.InlineKeyboardMarkup()

        for subject_id, name, lesson_type, is_own in get_subjects_for_teacher(teacher):

            markup.add(
                types.InlineKeyboardButton(
                    _type_icon(lesson_type) + " " + name,
                    callback_data="tsch:subj:" + str(subject_id)
                )
            )

        markup.add(
            types.InlineKeyboardButton(
                "➕ Yangi fan qo'shish",
                callback_data="tsch:newsubj"
            )
        )

        bot.answer_callback_query(call.id)

        bot.send_message(
            chat_id,
            "📚 Fanni tanlang:\n\n👤 - yakka tartibdagi, 👥 - guruhli",
            reply_markup=markup
        )


    @bot.callback_query_handler(
        func=lambda c: c.data.startswith("tsch:subj:")
    )
    def new_slot_day(call):

        chat_id = call.message.chat.id

        subject_id = int(call.data.split(":", 2)[2])

        row = get_subject(subject_id)

        if not row:

            bot.answer_callback_query(call.id, "Fan topilmadi")

            return

        ctx[chat_id] = {"subject": row[2], "lesson_type": row[3]}

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

        lesson_type = get_subject_type(teacher, subject)

        students = get_slot_students(slot_id)

        concertmasters = get_slot_concertmasters(slot_id)

        text = (
            "🗓 " + day + " " + time + "\n"
            "📚 " + subject + " — " + LESSON_TYPES[lesson_type] + "\n"
            "🚪 Xona: " + room + "\n\n"
        )

        if concertmasters:

            text += "🎹 Jo'rnavoz(lar):\n"

            for name in concertmasters:
                text += "- " + name + "\n"

            text += "\n"

        if students:

            text += "👨‍🎓 O'quvchilar:\n"

            for _, student, student_teacher in students:
                text += "- " + student + " (" + student_teacher + ")\n"

        else:

            text += "👨‍🎓 Hali o'quvchi qo'shilmagan."


        # yakka tartibdagi darsga bir nechta o'quvchi qo'shilgan bo'lsa
        # - bu xato bo'lishi mumkin, eslatib qo'yamiz

        if lesson_type == "yakka" and len(students) > 1:

            text += (
                "\n\n⚠️ Bu yakka tartibdagi dars, lekin "
                + str(len(students)) + " ta o'quvchi qo'shilgan."
            )

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

        for index, name in enumerate(concertmasters):

            markup.add(
                types.InlineKeyboardButton(
                    "🗑 🎹 " + name[:32],
                    callback_data="tsch:delcm:" + str(slot_id) + ":" + str(index)
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
    # JO'RNAVOZLIGIM
    # ==========================
    #
    # Jo'rnavozning O'ZI qaysi darsga jo'rnavozlik qilishini
    # tanlaydi: o'qituvchini qidiradi -> uning dars vaqtlarini
    # ko'radi -> keraklisiga biriktiriladi.
    #
    # Bitta darsda bir nechta jo'rnavoz bo'lishi mumkin.
    # Dars egasi esa o'z darsidan keraksiz biriktirmani
    # olib tashlay oladi (tsch:delcm).
    # ==========================

    def _show_cm_menu(chat_id, teacher):

        mine = get_concertmaster_slots(teacher)

        markup = types.InlineKeyboardMarkup()

        for slot_id, owner, subject, day, time, room in mine:

            markup.add(
                types.InlineKeyboardButton(
                    "🗑 " + day + " " + time + " - " + subject[:20]
                    + " (" + owner[:15] + ")",
                    callback_data="tcm:del:" + str(slot_id)
                )
            )

        markup.add(
            types.InlineKeyboardButton(
                "➕ Darsga biriktirilish",
                callback_data="tcm:add"
            )
        )

        markup.add(
            types.InlineKeyboardButton(
                "⬅️ Jadvalga qaytish",
                callback_data="tsch:list"
            )
        )

        if mine:

            text = (
                "🎹 Siz jo'rnavozlik qilayotgan darslar:\n\n"
                "Chiqish uchun dars ustiga bosing."
            )

        else:

            text = (
                "🎹 Siz hali hech qaysi darsga jo'rnavoz "
                "sifatida biriktirilmagansiz.\n\n"
                "«➕ Darsga biriktirilish» orqali o'qituvchini "
                "qidirib, uning dars vaqtini tanlaysiz."
            )

        bot.send_message(chat_id, text, reply_markup=markup)


    @bot.callback_query_handler(
        func=lambda c: c.data == "tcm:menu"
    )
    def cm_menu(call):

        teacher = selected_teachers.get(call.message.chat.id)

        bot.answer_callback_query(call.id)

        if teacher:
            _show_cm_menu(call.message.chat.id, teacher)


    @bot.callback_query_handler(
        func=lambda c: c.data == "tcm:add"
    )
    def cm_add_start(call):

        bot.answer_callback_query(call.id)

        sent = bot.send_message(
            call.message.chat.id,
            "🔍 Dars egasi - o'qituvchining ism-familiyasini yozing:"
        )

        bot.register_next_step_handler(sent, cm_search_teacher)


    def cm_search_teacher(message):

        chat_id = message.chat.id

        results = search_teachers_by_name(message.text.strip())

        if not results:

            bot.send_message(
                chat_id,
                "❌ Topilmadi. Kamida 3 ta harf yozing va qaytadan urinib ko'ring:"
            )

            bot.register_next_step_handler(message, cm_search_teacher)

            return

        ctx[chat_id] = {"cm_teachers": [row[1] for row in results]}

        markup = types.InlineKeyboardMarkup()

        for index, (_, name, department, _status) in enumerate(results):

            markup.add(
                types.InlineKeyboardButton(
                    name + " (" + department + ")",
                    callback_data="tcm:t:" + str(index)
                )
            )

        bot.send_message(
            chat_id,
            "Topilgan o'qituvchilar:",
            reply_markup=markup
        )


    @bot.callback_query_handler(
        func=lambda c: c.data.startswith("tcm:t:")
    )
    def cm_pick_teacher(call):

        chat_id = call.message.chat.id

        data = ctx.get(chat_id)

        if not data or "cm_teachers" not in data:

            bot.answer_callback_query(call.id, "Xatolik, qaytadan boshlang")

            return

        index = int(call.data.split(":", 2)[2])

        names = data["cm_teachers"]

        if index >= len(names):

            bot.answer_callback_query(call.id, "Topilmadi")

            return

        owner = names[index]

        slots = get_teacher_slots(owner)

        bot.answer_callback_query(call.id)

        if not slots:

            bot.send_message(
                chat_id,
                "❌ " + owner + " hali dars vaqti kiritmagan."
            )

            return

        me = selected_teachers.get(chat_id)

        markup = types.InlineKeyboardMarkup()

        for slot_id, subject, day, time, room in slots:

            already = me in get_slot_concertmasters(slot_id)

            markup.add(
                types.InlineKeyboardButton(
                    ("✅ " if already else "")
                    + day + " " + time + " - " + subject
                    + " (xona " + room + ")",
                    callback_data="tcm:s:" + str(slot_id)
                )
            )

        bot.send_message(
            chat_id,
            "🎹 " + owner + " darslari.\n\n"
            "Jo'rnavozlik qiladiganini tanlang:",
            reply_markup=markup
        )


    @bot.callback_query_handler(
        func=lambda c: c.data.startswith("tcm:s:")
    )
    def cm_attach(call):

        chat_id = call.message.chat.id

        teacher = selected_teachers.get(chat_id)

        slot_id = int(call.data.split(":", 2)[2])

        slot = get_slot(slot_id)

        if not teacher or not slot:

            bot.answer_callback_query(call.id, "Dars topilmadi")

            return

        if slot[1] == teacher:

            bot.answer_callback_query(
                call.id, "Bu o'z darsingiz"
            )

            return

        added = add_concertmaster(slot_id, teacher)

        bot.answer_callback_query(
            call.id,
            "✅ Biriktirildingiz" if added else "Allaqachon biriktirilgansiz"
        )

        if added:

            bot.send_message(
                chat_id,
                "🎹 Biriktirildingiz:\n"
                + slot[3] + " " + slot[4] + " - " + slot[2]
                + "\n👨‍🏫 " + slot[1] + ", xona " + slot[5]
            )


            # dars egasiga xabar - u kim qo'shilganini bilib tursin

            owner_chat = get_teacher_chat_id(slot[1])

            if owner_chat:

                try:

                    bot.send_message(
                        owner_chat,
                        "🎹 " + teacher + " sizning darsingizga "
                        "jo'rnavoz sifatida biriktirildi:\n"
                        + slot[3] + " " + slot[4] + " - " + slot[2]
                    )

                except Exception:
                    # o'qituvchi botni bloklagan bo'lishi mumkin
                    pass

        ctx.pop(chat_id, None)

        _show_cm_menu(chat_id, teacher)


    @bot.callback_query_handler(
        func=lambda c: c.data.startswith("tcm:del:")
    )
    def cm_detach(call):

        chat_id = call.message.chat.id

        teacher = selected_teachers.get(chat_id)

        slot_id = int(call.data.split(":", 2)[2])

        if teacher:

            remove_concertmaster(slot_id, teacher)

            bot.answer_callback_query(call.id, "🗑 Chiqarildi")

            _show_cm_menu(chat_id, teacher)

        else:

            bot.answer_callback_query(call.id, "Xatolik")


    @bot.callback_query_handler(
        func=lambda c: c.data.startswith("tsch:delcm:")
    )
    def remove_cm(call):

        _, _, slot_id, index = call.data.split(":")

        slot_id = int(slot_id)

        names = get_slot_concertmasters(slot_id)

        index = int(index)

        if index < len(names):

            remove_concertmaster(slot_id, names[index])

            bot.answer_callback_query(call.id, "🗑 O'chirildi")

        else:

            bot.answer_callback_query(call.id, "Topilmadi")

        _show_slot_detail(call.message.chat.id, slot_id)


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
