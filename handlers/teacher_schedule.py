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


from datetime import datetime

from telebot import types

from services.group_capacity import notify_if_overcapacity

from data.curriculum import (
    department_subjects,
    department_years,
    planned_hours,
    MIN_SPLITTABLE_HOURS
)

from database import (
    is_cancel_text,
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
    slot_allows_concertmaster,
    remove_concertmaster,
    get_slot_concertmasters,
    get_concertmaster_slots,
    get_teacher_chat_id,
    normalize_time,
    ACADEMIC_HOURS,
    hours_label,
    hours_to_minutes,
    available_lesson_times,
    DEFAULT_DURATION,
    scheduled_hours,
    get_department_for_teacher,
    find_room_conflict,
    get_room_availability,
    update_slot_schedule,
    get_teacher_last_pick,
    get_slot_class,
    get_slot_duration,
    LESSON_MINUTES,
    find_teacher_conflict,
    find_student_conflict,
    can,
    log_action
)


# chat_id -> vaqtinchalik holat (yangi slot yaratish, qidiruv natijalari)
ctx = {}


def _type_icon(lesson_type):

    return "👥" if lesson_type == "guruh" else "👤"


def register_teacher_schedule(bot, selected_teachers):


    # ==========================
    # BUGUNGI DARSLAR
    # ==========================
    #
    # Kunlik eng ko'p kerak bo'ladigan ma'lumot: bugun nechada,
    # qaysi xonada, kim bilan. Butun jadvalni ochib kunni
    # qidirib o'tirmaslik uchun alohida tugma.

    @bot.message_handler(
        func=lambda m: m.text == "📅 Bugungi darslarim"
    )
    def today_lessons(message):

        chat_id = message.chat.id

        teacher = selected_teachers.get(chat_id)

        if not teacher:

            bot.send_message(chat_id, "❌ Avval o'qituvchini tanlang.")

            return

        now = datetime.now()

        weekday = now.weekday()

        # DAYS_OF_WEEK da 6 kun bor - yakshanba ro'yxatdan tashqari

        if weekday >= len(DAYS_OF_WEEK):

            bot.send_message(
                chat_id,
                "😴 Bugun yakshanba - dars yo'q.\n\n"
                "Butun haftani ko'rish uchun «🗓 Dars jadvali»."
            )

            return

        today = DAYS_OF_WEEK[weekday]

        mine = [
            (time, subject, room, slot_id, None)
            for slot_id, subject, day, time, room in get_teacher_slots(teacher)
            if day == today
        ]

        # jo'rnavozlik - darsning egasi boshqa o'qituvchi, lekin
        # bu odam ham o'sha vaqtda o'sha xonada bo'ladi

        for row in get_concertmaster_slots(teacher):

            slot_id, owner, subject, day, time, room = row[:6]

            if day == today:
                mine.append((time, subject, room, slot_id, owner))

        if not mine:

            bot.send_message(
                chat_id,
                "🎉 " + today + " kuni darsingiz yo'q."
            )

            return

        mine.sort(key=lambda row: row[0])

        now_minutes = now.hour * 60 + now.minute

        out = [
            "📅 " + today + " · " + str(len(mine)) + " ta dars"
        ]

        for time, subject, room, slot_id, owner in mine:

            students = [s for _, s, _ in get_slot_students(slot_id)]

            duration = get_slot_duration(slot_id)

            try:
                hh, mm = time.split(":")
                start = int(hh) * 60 + int(mm)

            except (ValueError, AttributeError):
                start = None

            mark = ""

            if start is not None:

                if start <= now_minutes <= start + duration:
                    mark = " 🟢 hozir"

                elif start > now_minutes:
                    mark = " ⏰ " + str(start - now_minutes) + " daqiqadan keyin"

                else:
                    mark = " ✅"

            out.append(
                "🕒 " + time + mark + "\n"
                "📚 " + subject
                + ("\n🎹 jo'rnavoz: " + owner if owner else "")
                + "\n🚪 " + room + "-xona"
                + "\n🧑 "
                + (", ".join(students) if students else "o'quvchi biriktirilmagan")
            )

        bot.send_message(chat_id, "\n\n".join(out))


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


        # jo'rnavoz o'zi dars jadvali tuzmaydi - u boshqalarning
        # darslariga biriktiriladi

        if not can(teacher, "can_manage_schedule"):

            # na jadval, na jo'rnavozlik huquqi bo'lmasa - bo'lim yopiq

            if not can(teacher, "can_be_concertmaster"):

                bot.send_message(
                    message.chat.id,
                    "❌ Sizda dars jadvali bilan ishlash huquqi yo'q."
                )

                return

            _show_cm_menu(message.chat.id, teacher)

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

        # jo'rnavozlik huquqi yo'q o'qituvchiga bu tugma umuman
        # ko'rinmasin

        if can(teacher, "can_be_concertmaster"):

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

        if is_cancel_text(message.text):
            ctx.pop(chat_id, None)
            bot.send_message(chat_id, "❌ Bekor qilindi.")
            return


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

        if is_cancel_text(message.text):
            ctx.pop(chat_id, None)
            bot.send_message(chat_id, "❌ Bekor qilindi.")
            return


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

        department = get_department_for_teacher(teacher)


        # Fanlar ro'yxati 2026 o'quv rejasidan, o'qituvchining
        # bo'limi bo'yicha olinadi - Tasviriy san'at o'qituvchisiga
        # solfedjio yoki maqom alifbosi ko'rsatilmaydi.
        #
        # Bundan tashqari o'zi qo'shgan fanlar ham chiqadi.

        plan = [name for name, _ in department_subjects(department)]

        own = [row[1] for row in get_own_subjects(teacher)]

        names = plan + [n for n in own if n not in plan]

        if not names:
            names = [row[1] for row in get_subjects_for_teacher(teacher)]

        ctx[chat_id] = {"names": names, "department": department}

        markup = types.InlineKeyboardMarkup()


        # Ko'p oqituvchi bir xil fan/sinfni haftada bir necha marta
        # takrorlaydi - fan va sinfni qayta so'ramasdan, to'g'ridan-
        # to'g'ri kun/vaqt/xonaga o'tkazamiz.

        last_pick = get_teacher_last_pick(teacher)

        if last_pick and last_pick[0] in names:

            last_subject, last_class = last_pick

            markup.add(
                types.InlineKeyboardButton(
                    "🔁 Oxirgisidek: " + last_subject
                    + (" · " + last_class + "-sinf" if last_class else "")
                    + " (tez)",
                    callback_data="tsch:quick"
                )
            )

        for index, name in enumerate(names):

            mark = "" if name in plan else "➕ "

            markup.add(
                types.InlineKeyboardButton(
                    mark + name,
                    callback_data="tsch:subj:" + str(index)
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
            "📚 Fanni tanlang:\n\n"
            "Ro'yxat " + (department or "bo'limingiz")
            + " uchun o'quv rejasidan olingan.",
            reply_markup=markup
        )


    @bot.callback_query_handler(
        func=lambda c: c.data == "tsch:quick"
    )
    def new_slot_quick(call):
        """Fan va sinfni oxirgi darsdan olib, to'g'ridan-to'g'ri kunga o'tadi."""

        chat_id = call.message.chat.id

        teacher = selected_teachers.get(chat_id)

        data = ctx.get(chat_id)

        if not teacher or not data:

            bot.answer_callback_query(call.id, "Xatolik, qaytadan boshlang")

            return

        last_pick = get_teacher_last_pick(teacher)

        if not last_pick:

            bot.answer_callback_query(call.id, "Topilmadi")

            return

        data["subject"], data["class"] = last_pick

        bot.answer_callback_query(call.id)

        _ask_day(
            chat_id,
            "📅 " + data["subject"]
            + (" · " + data["class"] + "-sinf" if data["class"] else "")
            + " — qaysi kun?"
        )


    @bot.callback_query_handler(
        func=lambda c: c.data.startswith("tsch:editask:")
    )
    def edit_slot_start(call):
        """
        Kun/vaqt/xonani tahrirlashni boshlaydi - fan, sinf va
        davomiylik o'zgarmaydi, o'quvchilar va jo'rnavozlar
        tegilmaydi. Darsni o'chirib qayta yaratish shart emas.
        """

        chat_id = call.message.chat.id

        teacher = selected_teachers.get(chat_id)

        slot_id = int(call.data.split(":", 2)[2])

        slot = get_slot(slot_id)

        if not slot or not teacher or slot[1] != teacher:

            bot.answer_callback_query(call.id, "Topilmadi")

            return

        _, _, subject, day, time, room = slot

        duration = get_slot_duration(slot_id) or DEFAULT_DURATION

        ctx[chat_id] = {
            "subject": subject,
            "class": get_slot_class(slot_id),
            "department": get_department_for_teacher(teacher),
            "duration": duration,
            "hours": duration / LESSON_MINUTES,
            "edit_slot_id": slot_id,
        }

        bot.answer_callback_query(call.id)

        _ask_day(
            chat_id,
            "✏️ " + subject + "\n"
            "Hozir: " + day + " " + time + " · 🚪 " + room + "\n\n"
            "📅 Yangi kun?"
        )


    @bot.callback_query_handler(
        func=lambda c: c.data.startswith("tsch:subj:")
    )
    def new_slot_class(call):

        chat_id = call.message.chat.id

        data = ctx.get(chat_id)

        if not data or "names" not in data:

            bot.answer_callback_query(call.id, "Xatolik, qaytadan boshlang")

            return

        index = int(call.data.split(":", 2)[2])

        if index >= len(data["names"]):

            bot.answer_callback_query(call.id, "Fan topilmadi")

            return

        data["subject"] = data["names"][index]

        bot.answer_callback_query(call.id)


        # Sinf so'raladi, chunki rejadagi soat sinfga bog'liq:
        # masalan mutaxassislik 1-6 sinfda 2 soat, 7-sinfda 3 soat.

        years = department_years(data["department"])

        markup = types.InlineKeyboardMarkup()

        row = []

        for number in range(1, years + 1):

            row.append(
                types.InlineKeyboardButton(
                    str(number) + "-sinf",
                    callback_data="tsch:cls:" + str(number)
                )
            )

            if len(row) == 4:
                markup.row(*row)
                row = []

        if row:
            markup.row(*row)

        bot.send_message(
            chat_id,
            "🏫 " + data["subject"] + " — qaysi sinf uchun?",
            reply_markup=markup
        )


    @bot.callback_query_handler(
        func=lambda c: c.data.startswith("tsch:cls:")
    )
    def new_slot_day(call):

        chat_id = call.message.chat.id

        data = ctx.get(chat_id)

        if not data or "subject" not in data:

            bot.answer_callback_query(call.id, "Xatolik, qaytadan boshlang")

            return

        data["class"] = call.data.split(":", 2)[2]

        bot.answer_callback_query(call.id)

        _ask_day(chat_id)


    def _ask_day(chat_id, text="📅 Qaysi kun?"):
        """Kun tugmalari - yangi dars qo'shishda ham, tahrirlashda ham."""

        markup = types.InlineKeyboardMarkup()

        for day_index, day in enumerate(DAYS_OF_WEEK):

            markup.add(
                types.InlineKeyboardButton(
                    day,
                    callback_data="tsch:day:" + str(day_index)
                )
            )

        bot.send_message(chat_id, text, reply_markup=markup)


    @bot.callback_query_handler(
        func=lambda c: c.data.startswith("tsch:day:")
    )
    def new_slot_time(call):

        chat_id = call.message.chat.id

        data = ctx.get(chat_id)

        teacher = selected_teachers.get(chat_id)

        if not data or not teacher:

            bot.answer_callback_query(call.id, "Xatolik, qaytadan boshlang")

            return

        index = int(call.data.split(":", 2)[2])

        data["day"] = DAYS_OF_WEEK[index]

        bot.answer_callback_query(call.id)


        # Tahrirlashda davomiylik o'zgarmaydi - reja bo'yicha
        # qancha soat qolgani qayta hisoblanmaydi, faqat kun/vaqt/
        # xona o'zgaradi.

        if data.get("edit_slot_id"):

            _ask_time(chat_id, teacher, data, exclude_slot_id=data["edit_slot_id"])

            return

        _ask_duration(chat_id)


    # ==========================
    # DARS DAVOMIYLIGI
    # ==========================
    #
    # 2026 o'quv rejasi fanlarga haftalik akademik soat beradi:
    # 0,5 / 1 / 1,5 / 2 / 3 / 4. Bitta dars shu soatlarning
    # biriga teng bo'ladi - masalan 2 soatlik fanni haftada
    # bir marta 90 daqiqa yoki ikki marta 45 daqiqadan o'tish
    # mumkin (reja 6.5-bandi ikkalasiga ham ruxsat beradi).

    def _ask_duration(chat_id):
        """
        Reja fanga qancha soat berganini topib, shu darsga
        qancha qo'yilishini so'raydi.

        0,5 / 1 / 1,5 soatlik fanlar bo'linmaydi - bitta dars
        bo'lib o'tiladi, shuning uchun tanlov ham so'ralmaydi.

        2 soatdan boshlab kunlarga bo'lish mumkin (reja 6.5-bandi),
        shuning uchun "shu darsga nechta soat" deb so'raladi va
        rejagacha qancha qolgani ko'rsatiladi.
        """

        data = ctx.get(chat_id, {})

        teacher = selected_teachers.get(chat_id)

        subject = data.get("subject", "")

        class_name = data.get("class", "")

        planned = planned_hours(data.get("department"), subject, class_name)

        done = scheduled_hours(teacher, subject, class_name) if teacher else 0


        # reja jim tursa yoki bir nechta qiymat bersa - hammasini
        # ko'rsatamiz, o'qituvchi tanlaydi

        if not planned:

            _show_hour_buttons(
                chat_id, ACADEMIC_HOURS,
                "⏱ Dars qancha davom etadi?\n\n"
                "📗 Reja bu fan uchun " + class_name
                + "-sinfda soat ko'rsatmagan."
            )

            return

        if len(planned) > 1:

            _show_hour_buttons(
                chat_id, planned,
                "⏱ Dars qancha davom etadi?\n\n"
                "📗 Reja bo'yicha bo'limingizda bu fan "
                + " yoki ".join(_hours_text(h) for h in planned)
                + " bo'lishi mumkin."
            )

            return

        norm = planned[0]

        remaining = norm - done


        # bo'linmaydigan fan - to'g'ridan-to'g'ri o'tamiz

        if norm < MIN_SPLITTABLE_HOURS:

            data["hours"] = norm
            data["duration"] = hours_to_minutes(norm)

            bot.send_message(
                chat_id,
                "📗 Reja: " + subject + " · " + class_name + "-sinf → "
                + hours_label(norm) + "\n"
                "Bu fan kunlarga bo'linmaydi."
            )

            _ask_time(chat_id, teacher, data)

            return


        # 2 soat va undan yuqori - bo'lish mumkin

        if remaining <= 0:

            text = (
                "📗 Reja: " + subject + " · " + class_name + "-sinf → "
                + _hours_text(norm) + "\n"
                "⚠️ Siz allaqachon " + _hours_text(done) + " qo'ygansiz.\n\n"
                "Yana qo'shsangiz reja normasidan oshadi."
            )

            choices = [h for h in ACADEMIC_HOURS if h >= 1]

        else:

            text = (
                "📗 Reja: " + subject + " · " + class_name + "-sinf → "
                + _hours_text(norm) + "\n"
            )

            if done:
                text += "Qo'yilgan: " + _hours_text(done) + "\n"

            text += (
                "Qolgan: " + _hours_text(remaining) + "\n\n"
                "⏱ Shu darsga nechta soat?\n"
                "Bir kunda hammasini yoki bir necha kunga bo'lib "
                "qo'yishingiz mumkin."
            )

            choices = [h for h in ACADEMIC_HOURS
                       if h >= 1 and h <= remaining]

            if not choices:
                choices = [h for h in ACADEMIC_HOURS if h >= 1]

        _show_hour_buttons(chat_id, choices, text)


    def _hours_text(hours):
        return ("%g" % float(hours)).replace(".", ",") + " soat"


    def _show_hour_buttons(chat_id, choices, text):

        ctx.setdefault(chat_id, {})["choices"] = list(choices)

        markup = types.InlineKeyboardMarkup()

        for index, hours in enumerate(choices):

            markup.add(
                types.InlineKeyboardButton(
                    hours_label(hours),
                    callback_data="tsch:dur:" + str(index)
                )
            )

        bot.send_message(chat_id, text, reply_markup=markup)


    @bot.callback_query_handler(
        func=lambda c: c.data.startswith("tsch:dur:")
    )
    def new_slot_duration(call):

        chat_id = call.message.chat.id

        data = ctx.get(chat_id)

        teacher = selected_teachers.get(chat_id)

        if not data or "day" not in data or not teacher:

            bot.answer_callback_query(call.id, "Xatolik, qaytadan boshlang")

            return

        choices = data.get("choices") or ACADEMIC_HOURS

        index = int(call.data.split(":", 2)[2])

        if index >= len(choices):

            bot.answer_callback_query(call.id, "Topilmadi")

            return

        hours = choices[index]

        data["hours"] = hours
        data["duration"] = hours_to_minutes(hours)

        bot.answer_callback_query(call.id)

        _ask_time(chat_id, teacher, data)


    # ==========================
    # DARS VAQTI
    # ==========================
    #
    # Vaqt qo'lda yozilmaydi. Maktab kuni 08:00-17:05,
    # 12:05-13:00 tushlik, darslar orasida 5 daqiqa tanaffus -
    # shundan aniq 10 ta vaqt kelib chiqadi. Tanlangan
    # davomiylik tushlikka yoki kun oxiriga urilib qolsa,
    # o'sha vaqt tugmada umuman ko'rsatilmaydi.
    #
    # O'qituvchining o'zi band bo'lgan vaqtlar ham chiqarilmaydi.

    def _ask_time(chat_id, teacher, data, exclude_slot_id=None):

        slots = available_lesson_times(data["duration"])

        free = []

        for start, end in slots:

            if find_teacher_conflict(
                teacher, data["day"], start, data["duration"],
                exclude_slot_id=exclude_slot_id
            ):
                continue

            free.append((start, end))

        if not free:

            bot.send_message(
                chat_id,
                "⚠️ " + data["day"] + " kuni "
                + hours_label(data["hours"]) + " dars uchun bo'sh vaqt yo'q.\n\n"
                "Boshqa kun yoki qisqaroq dars tanlang."
            )

            _show_slot_list(chat_id, teacher)

            return

        data["times"] = free

        markup = types.InlineKeyboardMarkup()

        row = []

        for index, (start, end) in enumerate(free):

            row.append(
                types.InlineKeyboardButton(
                    start + "-" + end,
                    callback_data="tsch:time:" + str(index)
                )
            )

            if len(row) == 2:
                markup.row(*row)
                row = []

        if row:
            markup.row(*row)

        bot.send_message(
            chat_id,
            "🕐 " + data["day"] + " kuni qaysi vaqtda?\n\n"
            "Faqat bo'sh va rejaga mos vaqtlar ko'rsatilgan.",
            reply_markup=markup
        )


    @bot.callback_query_handler(
        func=lambda c: c.data.startswith("tsch:time:")
    )
    def new_slot_pick_time(call):

        chat_id = call.message.chat.id

        data = ctx.get(chat_id)

        if not data or "times" not in data:

            bot.answer_callback_query(call.id, "Xatolik, qaytadan boshlang")

            return

        index = int(call.data.split(":", 2)[2])

        if index >= len(data["times"]):

            bot.answer_callback_query(call.id, "Topilmadi")

            return

        data["time"] = data["times"][index][0]

        bot.answer_callback_query(call.id)

        ask_room(chat_id, data)


    def ask_room(chat_id, data):
        """Xonalarni bandlik holati bilan tugma qilib chiqaradi."""

        duration = data.get("duration", DEFAULT_DURATION)

        rooms = get_room_availability(
            data["day"], data["time"], duration,
            exclude_slot_id=data.get("edit_slot_id")
        )

        # tugma bosilganda indeks bo'yicha topamiz - callback_data
        # 64 baytdan oshmasligi kerak, xona nomini yubormaymiz
        data["rooms"] = rooms

        markup = types.InlineKeyboardMarkup(row_width=3)

        # Oddiy xonalar qatorda 3 tadan, nomli xonalar ("1/23 Zal")
        # esa alohida qatorda - nomi kesilib qolmasin.

        row = []

        for i, r in enumerate(rooms):

            lock = "🔒 " if r["busy"] else ""

            if r["name"]:

                if row:
                    markup.row(*row)
                    row = []

                markup.row(types.InlineKeyboardButton(
                    lock + r["label"],
                    callback_data="tsch:room:" + str(i)
                ))

                continue

            row.append(types.InlineKeyboardButton(
                lock + r["room"],
                callback_data="tsch:room:" + str(i)
            ))

            if len(row) == 3:
                markup.row(*row)
                row = []

        if row:
            markup.row(*row)

        busy = [r for r in rooms if r["busy"]]

        text = (
            "🚪 " + data["day"] + " kuni " + data["time"]
            + " da qaysi xonada?\n\n"
        )

        if busy:

            text += "🔒 Band xonalar:\n"

            for r in busy:
                text += (
                    "• " + r["label"] + " - " + r["teacher"]
                    + " (" + r["subject"] + ")\n"
                )

        else:
            text += "Bu vaqtda barcha xonalar bo'sh."

        bot.send_message(chat_id, text, reply_markup=markup)


    @bot.callback_query_handler(
        func=lambda c: c.data.startswith("tsch:room:")
    )
    def new_slot_pick_room(call):

        chat_id = call.message.chat.id

        data = ctx.get(chat_id)

        if not data or "rooms" not in data:

            bot.answer_callback_query(call.id, "Xatolik, qaytadan boshlang")

            return

        index = int(call.data.split(":", 2)[2])

        if index >= len(data["rooms"]):

            bot.answer_callback_query(call.id, "Topilmadi")

            return

        chosen = data["rooms"][index]

        # Band xonaga bosilsa - kim bandligini aytamiz va shu yerda
        # jo'rnavozlikni taklif qilamiz. Ro'yxat yopilmaydi, o'qituvchi
        # boshqa xonani bosishi mumkin.

        if chosen["busy"]:

            bot.answer_callback_query(call.id, chosen["room"] + " band")

            # jo'rnavozlik huquqi yo'q o'qituvchiga taklif qilmaymiz

            teacher = selected_teachers.get(chat_id)

            may_cm = bool(teacher) and can(teacher, "can_be_concertmaster")

            markup = None

            if may_cm:

                markup = types.InlineKeyboardMarkup()

                markup.add(
                    types.InlineKeyboardButton(
                        "🎹 Shu darsga jo'rnavoz bo'lish",
                        callback_data="tcm:s:" + str(chosen["slot_id"])
                    )
                )

            bot.send_message(
                chat_id,
                "⚠️ " + chosen["label"] + " " + data["day"]
                + " kuni " + chosen["time"] + " da band:\n\n"
                + "📚 " + chosen["subject"] + "\n"
                + "👨‍🏫 " + chosen["teacher"] + "\n\n"
                "Bitta xonani bir vaqtda ikki dars egallay olmaydi.\n"
                + (
                    "Yuqoridagi ro'yxatdan bo'sh xonani tanlang yoki "
                    "shu darsda jo'rnavozlik qiling."
                    if may_cm else
                    "Yuqoridagi ro'yxatdan bo'sh xonani tanlang."
                ),
                reply_markup=markup
            )

            return

        bot.answer_callback_query(call.id)

        new_slot_save(chat_id, chosen["room"])


    def new_slot_save(chat_id, room):

        data = ctx.get(chat_id)

        teacher = selected_teachers.get(chat_id)

        if not data or "time" not in data or not teacher:

            bot.send_message(chat_id, "❌ Xatolik yuz berdi. Qaytadan boshlang.")

            return

        duration = data.get("duration", DEFAULT_DURATION)

        edit_slot_id = data.get("edit_slot_id")


        # xonani bir vaqtda bitta dars egallaydi. Boshqa o'qituvchi
        # shu xonada shu vaqtda dars o'tayotgan bo'lsa - yangi dars
        # ochilmaydi, o'sha darsga jo'rnavoz bo'lib qo'shiladi.
        # Tahrirlanayotgan darsning o'zi hisobga olinmaydi.

        taken = find_room_conflict(
            data["day"], data["time"], room, duration,
            exclude_slot_id=edit_slot_id
        )

        if taken:

            slot_id, owner, subject, slot_time, _ = taken

            teacher = selected_teachers.get(chat_id)

            may_cm = bool(teacher) and can(teacher, "can_be_concertmaster")

            markup = types.InlineKeyboardMarkup()

            if may_cm:

                markup.add(
                    types.InlineKeyboardButton(
                        "🎹 Shu darsga jo'rnavoz bo'lish",
                        callback_data="tcm:s:" + str(slot_id)
                    )
                )

            markup.add(
                types.InlineKeyboardButton(
                    "🕐 Boshqa vaqt tanlash",
                    callback_data=(
                        "tsch:editask:" + str(edit_slot_id)
                        if edit_slot_id else "tsch:new"
                    )
                )
            )

            bot.send_message(
                chat_id,
                "⚠️ " + room + "-xona " + data["day"] + " kuni "
                + slot_time + " da band:\n\n"
                + "📚 " + subject + "\n"
                + "👨‍🏫 " + owner + "\n\n"
                "Bitta xonani bir vaqtda ikki dars egallay olmaydi.\n"
                + (
                    "Agar shu darsda jo'rnavozlik qilmoqchi bo'lsangiz - "
                    "quyidagi tugmani bosing."
                    if may_cm else
                    "Boshqa vaqt yoki xona tanlang."
                ),
                reply_markup=markup
            )

            ctx.pop(chat_id, None)

            return


        # Tahrirlash: kun/vaqt/xona yangilanadi, o'quvchilar va
        # jo'rnavozlar tegilmaydi - shu ularni yo'qotmaslik uchun
        # butun bu tahrirlash imkoniyati yaratildi.

        if edit_slot_id:

            update_slot_schedule(
                edit_slot_id, data["day"], data["time"], room, duration
            )

            log_action(
                teacher, "dars vaqtini tahrirladi", data["subject"],
                data["day"] + " " + data["time"] + ", xona " + room
            )

            bot.send_message(
                chat_id,
                "✅ Yangilandi: " + data["day"] + " " + data["time"]
                + " - " + data["subject"] + "\n"
                "🚪 Xona " + room + "\n\n"
                "O'quvchilar joyida qoldi."
            )

            ctx.pop(chat_id, None)

            _show_slot_detail(chat_id, edit_slot_id)

            return

        slot_id = create_slot(
            teacher,
            data["subject"],
            data["day"],
            data["time"],
            room,
            duration,
            data.get("class")
        )

        bot.send_message(
            chat_id,
            "✅ Qo'shildi: " + data["day"] + " " + data["time"]
            + " - " + data["subject"] + "\n"
            + "⏱ " + hours_label(data.get("hours", 1)) + "\n"
            + "🚪 Xona " + room
        )


        # Reja bo'yicha soat to'lmagan bo'lsa - qolgan bo'lakni
        # darrov shu yerda joylashtiramiz. O'qituvchi jadvalga
        # qaytib, fandan va sinfdan qaytadan boshlamasin.

        planned = planned_hours(
            data.get("department"), data["subject"], data.get("class")
        )

        if len(planned) == 1:

            remaining = planned[0] - scheduled_hours(
                teacher, data["subject"], data.get("class")
            )

            if remaining > 0:

                # fan, sinf va bo'lim saqlanib qoladi -
                # faqat kun qaytadan so'raladi

                ctx[chat_id] = {
                    "subject": data["subject"],
                    "class": data.get("class"),
                    "department": data.get("department"),
                    "names": data.get("names", []),
                }

                markup = types.InlineKeyboardMarkup()

                for day_index, day in enumerate(DAYS_OF_WEEK):

                    markup.add(
                        types.InlineKeyboardButton(
                            day,
                            callback_data="tsch:day:" + str(day_index)
                        )
                    )

                markup.add(
                    types.InlineKeyboardButton(
                        "⏸ Keyinroq qo'yaman",
                        callback_data="tsch:view:" + str(slot_id)
                    )
                )

                bot.send_message(
                    chat_id,
                    "📗 " + data["subject"] + " · " + str(data.get("class"))
                    + "-sinf uchun rejada yana "
                    + _hours_text(remaining) + " qoldi.\n\n"
                    "📅 Qolgan qismini qaysi kunga qo'yamiz?",
                    reply_markup=markup
                )

                return

        ctx.pop(chat_id, None)

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

        markup.add(
            types.InlineKeyboardButton(
                "✏️ Kun/vaqt/xonani tahrirlash",
                callback_data="tsch:editask:" + str(slot_id)
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
                callback_data=(
                    "tsch:delslotask:" + str(slot_id)
                    if students else
                    "tsch:delslot:" + str(slot_id)
                )
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
        func=lambda c: c.data.startswith("tsch:delslotask:")
    )
    def delete_slot_ask(call):

        slot_id = int(call.data.split(":", 2)[2])

        slot = get_slot(slot_id)

        if not slot:

            bot.answer_callback_query(call.id, "Topilmadi")

            return

        count = len(get_slot_students(slot_id))

        bot.answer_callback_query(call.id)

        markup = types.InlineKeyboardMarkup()

        markup.add(
            types.InlineKeyboardButton(
                "🗑 Ha, o'quvchilar bilan birga o'chirilsin",
                callback_data="tsch:delslot:" + str(slot_id)
            )
        )

        markup.add(
            types.InlineKeyboardButton(
                "⬅️ Yo'q, ortga",
                callback_data="tsch:view:" + str(slot_id)
            )
        )

        bot.send_message(
            call.message.chat.id,
            "⚠️ Bu vaqtda " + str(count) + " ta o'quvchi bor.\n\n"
            "O'chirilsa ular ro'yxatdan chiqadi - qayta qo'shish "
            "kerak bo'ladi. Rostdan ham butunlay o'chirilsinmi?",
            reply_markup=markup
        )


    @bot.callback_query_handler(
        func=lambda c: c.data.startswith("tsch:delslot:")
    )
    def delete_slot_handler(call):

        slot_id = int(call.data.split(":", 2)[2])

        slot = get_slot(slot_id)

        delete_slot(slot_id)

        if slot:

            log_action(
                slot[1], "dars vaqtini o'chirdi", slot[2],
                slot[3] + " " + slot[4] + ", xona " + slot[5]
            )

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

        if can(teacher, "can_be_concertmaster"):

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

        if teacher and not can(teacher, "can_be_concertmaster"):

            bot.answer_callback_query(
                call.id, "Sizda jo'rnavozlik huquqi yo'q", show_alert=True
            )

            return

        bot.answer_callback_query(call.id)

        if teacher:
            _show_cm_menu(call.message.chat.id, teacher)


    @bot.callback_query_handler(
        func=lambda c: c.data == "tcm:add"
    )
    def cm_add_start(call):

        teacher = selected_teachers.get(call.message.chat.id)

        if teacher and not can(teacher, "can_be_concertmaster"):

            bot.answer_callback_query(
                call.id, "Sizda jo'rnavozlik huquqi yo'q", show_alert=True
            )

            return

        bot.answer_callback_query(call.id)

        sent = bot.send_message(
            call.message.chat.id,
            "🔍 Dars egasi - o'qituvchining ism-familiyasini yozing:"
        )

        bot.register_next_step_handler(sent, cm_search_teacher)


    def cm_search_teacher(message):

        chat_id = message.chat.id

        if is_cancel_text(message.text):
            ctx.pop(chat_id, None)
            bot.send_message(chat_id, "❌ Bekor qilindi.")
            return


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

        # Rejada jo'rnavoz soati ajratilmagan fanlar
        # ro'yxatga umuman kirmaydi - bosib bo'lmaydigan
        # tugmani ko'rsatib turishdan foyda yo'q.

        from data.curriculum import subject_has_concertmaster

        department = get_department_for_teacher(owner)

        slots = [
            row for row in get_teacher_slots(owner)
            if subject_has_concertmaster(department, row[1])
        ]

        bot.answer_callback_query(call.id)

        if not slots:

            bot.send_message(
                chat_id,
                "❌ " + owner + " darslari orasida jo'rnavoz\n"
                "biriktirsa bo'ladiganlari yo'q."
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

        if not can(teacher, "can_be_concertmaster"):

            bot.answer_callback_query(
                call.id, "Sizda jo'rnavozlik huquqi yo'q", show_alert=True
            )

            return


        # jo'rnavoz ham bir vaqtda ikki darsda bo'la olmaydi

        busy = find_teacher_conflict(
            teacher, slot[3], slot[4], exclude_slot_id=slot_id
        )

        if busy:

            bot.answer_callback_query(call.id, "⚠️ Siz band")

            bot.send_message(
                chat_id,
                "⚠️ Siz " + slot[3] + " kuni " + slot[4]
                + " da band ekansiz:\n\n"
                + "📚 " + busy[2] + " (" + busy[1] + ")\n"
                + "🚪 Xona " + busy[4]
            )

            return

        # Reja jo'rnavoz soatini faqat sanalgan fanlarga
        # ajratadi - solfedjio yoki rang tasvir darsiga
        # jo'rnavoz qo'yilmaydi.

        allowed, subject = slot_allows_concertmaster(slot_id)

        if not allowed:

            bot.answer_callback_query(call.id, "⚠️ Bu fanga jo'rnavoz qo'yilmaydi")

            bot.send_message(
                chat_id,
                "⚠️ «" + str(subject) + "» fani uchun o'quv rejasida\n"
                "jo'rnavoz soati ajratilmagan.\n\n"
                "Jo'rnavoz mutaxassislik, akkompanement, jamoa\n"
                "ijrochiligi, raqs fanlari va tanlangan fanga\n"
                "biriktiriladi."
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

        if is_cancel_text(message.text):
            ctx.pop(chat_id, None)
            bot.send_message(chat_id, "❌ Bekor qilindi.")
            return


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
            "Topilgan o'quvchilar:\n\n"
            "Kerakli o'quvchi yo'qmi? Boshqa nom yozing - "
            "qidiruv davom etadi.",
            reply_markup=markup
        )


        # Natija chiqqandan keyin ham TINGLASHDA qolamiz.
        #
        # Ilgari bu yerda kutish tugardi: xodim noto'g'ri natija
        # ko'rsa, faqat tugmalardan birini bosishi mumkin edi -
        # yangi nom yozsa bot javob bermasdi. Endi yozilgan har
        # qanday yangi nom qayta qidiriladi.
        #
        # Tanlov qilingach (add_student_pick) bu kutish
        # bekor qilinadi - aks holda keyingi begona xabar
        # qidiruv so'rovi sifatida tushunilardi.

        bot.register_next_step_handler(message, add_student_search)


    @bot.callback_query_handler(
        func=lambda c: c.data.startswith("tsch:pick:")
    )
    def add_student_pick(call):

        chat_id = call.message.chat.id

        data = ctx.get(chat_id)

        if not data or "results" not in data or "slot_id" not in data:

            bot.answer_callback_query(call.id, "Xatolik, qaytadan boshlang")

            return

        # qidiruv kutishini to'xtatamiz - tanlov qilindi
        bot.clear_step_handler_by_chat_id(chat_id)

        index = int(call.data.split(":", 2)[2])

        results = data["results"]

        if index >= len(results):

            bot.answer_callback_query(call.id, "Topilmadi")

            return

        student_teacher, student = results[index]

        slot_id = data["slot_id"]

        slot = get_slot(slot_id)


        # o'quvchi bir vaqtda ikki xil darsda bo'la olmaydi.
        # Shu darsning o'zi hisobga olinmaydi - bitta darsda
        # bir nechta o'qituvchi bo'lishi mumkin.

        busy = find_student_conflict(
            student, student_teacher,
            slot[3], slot[4],
            exclude_slot_id=slot_id
        ) if slot else None

        if busy:

            bot.answer_callback_query(call.id, "⚠️ O'quvchi band")

            bot.send_message(
                chat_id,
                "⚠️ " + student + " " + slot[3] + " kuni "
                + slot[4] + " da boshqa darsda:\n\n"
                + "📚 " + busy[2] + "\n"
                + "👨‍🏫 " + busy[1] + "\n"
                + "🚪 Xona " + busy[4] + "\n\n"
                "Bitta o'quvchi bir vaqtda ikki darsda bo'la olmaydi."
            )

            ctx.pop(chat_id, None)

            _show_slot_detail(chat_id, slot_id)

            return

        added = add_student_to_slot(slot_id, student, student_teacher)

        bot.answer_callback_query(
            call.id,
            "✅ Qo'shildi" if added else "Allaqachon qo'shilgan"
        )

        if added:
            notify_if_overcapacity(bot.send_message, slot_id)

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
