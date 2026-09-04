# ==========================
# handlers/admin_permissions.py
# O'QITUVCHI HUQUQLARI, O'ZGARISHLAR TARIXI, ARXIV
# ==========================
#
# HUQUQLAR
#   Hamma o'qituvchi hamma ishni qila olmaydi. Solfedjio yoki
#   san'at tarixi o'qituvchisining o'z o'quvchisi yo'q - u faqat
#   boshqalarning o'quvchilariga guruhli dars beradi. Jo'rnavoz
#   esa o'zi dars jadvali tuzmaydi.
#
#   Admin tur tanlaydi (tayyor shablon), kerak bo'lsa keyin
#   bitta huquqni alohida yoqib/o'chirib qo'yadi - masalan
#   pianinochi ham mutaxassislik o'qituvchisi, ham jo'rnavoz.
#
# TARIX
#   17 (kelajakda 58) kishi bitta bazani tahrirlaydi. To'lov
#   summasi o'zgarsa yoki o'quvchi yo'qolsa - kim qilganini
#   bilish kerak.
#
# ARXIV
#   Maktabdan ketgan o'quvchi o'chirilmaydi. O'chirilsa to'lov
#   tarixi ham yo'qolib, o'tgan oylarning hisoboti buzilardi.
#
# ==========================


from telebot import types

from config import ADMIN_IDS

from database import (
    TEACHER_TYPES,
    PERMISSION_LABELS,
    set_teacher_type,
    toggle_teacher_permission,
    get_teacher_permissions,
    get_teachers_without_type,
    search_teachers_by_name,
    get_audit_log,
    get_archived_students,
    restore_student,
    log_action
)


# chat_id -> vaqtinchalik holat
ctx = {}


def register_admin_permissions(bot):


    def _is_admin(chat_id):
        return chat_id in ADMIN_IDS


    # ==========================
    # HUQUQLAR
    # ==========================

    @bot.message_handler(
        func=lambda m: m.text == "🔑 O'qituvchi huquqlari"
    )
    def permissions_start(message):

        if not _is_admin(message.chat.id):
            return

        pending = get_teachers_without_type()

        markup = types.InlineKeyboardMarkup()

        for name, department in pending[:20]:

            markup.add(
                types.InlineKeyboardButton(
                    "⚠️ " + name + " (" + department + ")",
                    callback_data="perm:v:" + name[:50]
                )
            )

        markup.add(
            types.InlineKeyboardButton(
                "🔍 O'qituvchini qidirish",
                callback_data="perm:search"
            )
        )

        if pending:

            text = (
                "🔑 O'qituvchi huquqlari\n\n"
                "⚠️ Quyidagi " + str(len(pending)) + " ta o'qituvchining "
                "turi hali belgilanmagan. Ular hozir barcha huquqqa ega.\n\n"
                "Turini belgilash uchun ism ustiga bosing."
            )

        else:

            text = (
                "🔑 O'qituvchi huquqlari\n\n"
                "✅ Barcha tasdiqlangan o'qituvchilarning turi belgilangan.\n\n"
                "O'zgartirish uchun qidiring."
            )

        bot.send_message(message.chat.id, text, reply_markup=markup)


    @bot.callback_query_handler(func=lambda c: c.data == "perm:search")
    def permissions_search(call):

        bot.answer_callback_query(call.id)

        sent = bot.send_message(
            call.message.chat.id,
            "🔍 O'qituvchi ism-familiyasini yozing:"
        )

        bot.register_next_step_handler(sent, permissions_search_result)


    def permissions_search_result(message):

        if not _is_admin(message.chat.id):
            return

        results = search_teachers_by_name(message.text.strip())

        if not results:

            sent = bot.send_message(
                message.chat.id,
                "❌ Topilmadi. Kamida 3 ta harf yozib, qaytadan urinib ko'ring:"
            )

            bot.register_next_step_handler(sent, permissions_search_result)

            return

        markup = types.InlineKeyboardMarkup()

        for _tid, name, department, _status in results:

            markup.add(
                types.InlineKeyboardButton(
                    name + " (" + department + ")",
                    callback_data="perm:v:" + name[:50]
                )
            )

        bot.send_message(
            message.chat.id,
            "Topilgan o'qituvchilar:",
            reply_markup=markup
        )


    def _show_permissions(chat_id, name):

        permissions = get_teacher_permissions(name)

        type_key = permissions["type"]

        markup = types.InlineKeyboardMarkup()


        # tayyor shablonlar

        for key, preset in TEACHER_TYPES.items():

            markup.add(
                types.InlineKeyboardButton(
                    ("✅ " if key == type_key else "") + preset["label"],
                    callback_data="perm:t:" + key + ":" + name[:40]
                )
            )


        # alohida huquqlar

        for key, label in PERMISSION_LABELS.items():

            markup.add(
                types.InlineKeyboardButton(
                    ("✅ " if permissions[key] else "🚫 ") + label,
                    callback_data="perm:x:" + key + ":" + name[:40]
                )
            )

        markup.add(
            types.InlineKeyboardButton(
                "⬅️ Ortga",
                callback_data="perm:back"
            )
        )

        current = (
            TEACHER_TYPES[type_key]["label"]
            if type_key in TEACHER_TYPES
            else "⚠️ belgilanmagan (barcha huquqlar ochiq)"
        )

        bot.send_message(
            chat_id,
            "👨‍🏫 " + name + "\n\n"
            "Turi: " + current + "\n\n"
            "Yuqoridagi turlardan birini tanlang, yoki pastdagi "
            "huquqlarni alohida yoqib/o'chiring.",
            reply_markup=markup
        )


    @bot.callback_query_handler(
        func=lambda c: c.data.startswith("perm:v:")
    )
    def view_permissions(call):

        if not _is_admin(call.message.chat.id):
            return

        bot.answer_callback_query(call.id)

        _show_permissions(call.message.chat.id, call.data.split(":", 2)[2])


    @bot.callback_query_handler(
        func=lambda c: c.data.startswith("perm:t:")
    )
    def apply_type(call):

        if not _is_admin(call.message.chat.id):
            return

        _, _, type_key, name = call.data.split(":", 3)

        if not set_teacher_type(name, type_key):

            bot.answer_callback_query(call.id, "Xatolik")

            return

        bot.answer_callback_query(call.id, "✅ Belgilandi")

        log_action(
            str(call.message.chat.id), "o'qituvchi turini belgiladi",
            name, TEACHER_TYPES[type_key]["label"], actor_role="admin"
        )

        _show_permissions(call.message.chat.id, name)


    @bot.callback_query_handler(
        func=lambda c: c.data.startswith("perm:x:")
    )
    def toggle_permission(call):

        if not _is_admin(call.message.chat.id):
            return

        _, _, key, name = call.data.split(":", 3)

        value = toggle_teacher_permission(name, key)

        if value is None:

            bot.answer_callback_query(call.id, "Xatolik")

            return

        bot.answer_callback_query(
            call.id, "✅ Yoqildi" if value else "🚫 O'chirildi"
        )

        log_action(
            str(call.message.chat.id), "huquqni o'zgartirdi", name,
            PERMISSION_LABELS[key] + ": " + ("ha" if value else "yo'q"),
            actor_role="admin"
        )

        _show_permissions(call.message.chat.id, name)


    @bot.callback_query_handler(func=lambda c: c.data == "perm:back")
    def permissions_back(call):

        bot.answer_callback_query(call.id)

        permissions_start(call.message)


    # ==========================
    # O'ZGARISHLAR TARIXI
    # ==========================

    @bot.message_handler(
        func=lambda m: m.text == "📜 O'zgarishlar tarixi"
    )
    def audit_start(message):

        if not _is_admin(message.chat.id):
            return

        _show_audit(message.chat.id)


    def _show_audit(chat_id, query=None):

        rows = get_audit_log(limit=30, query=query)

        if not rows:

            bot.send_message(
                chat_id,
                "📜 Hozircha yozuv yo'q."
                if not query else
                "📜 «" + query + "» bo'yicha hech narsa topilmadi."
            )

            return

        lines = []

        for at, actor, actor_role, action, target, details in rows:

            line = at + " · " + actor + "\n   " + action

            if target:
                line += ": " + target

            if details:
                line += "\n   " + details

            lines.append(line)

        markup = types.InlineKeyboardMarkup()

        markup.add(
            types.InlineKeyboardButton(
                "🔍 Qidirish (ism bo'yicha)",
                callback_data="audit:search"
            )
        )

        header = (
            "📜 Oxirgi o'zgarishlar:\n\n"
            if not query else
            "📜 «" + query + "» bo'yicha:\n\n"
        )

        bot.send_message(
            chat_id,
            header + "\n\n".join(lines),
            reply_markup=markup
        )


    @bot.callback_query_handler(func=lambda c: c.data == "audit:search")
    def audit_search(call):

        bot.answer_callback_query(call.id)

        sent = bot.send_message(
            call.message.chat.id,
            "🔍 O'qituvchi yoki o'quvchi ismini yozing:"
        )

        bot.register_next_step_handler(sent, audit_search_result)


    def audit_search_result(message):

        if not _is_admin(message.chat.id):
            return

        _show_audit(message.chat.id, (message.text or "").strip())


    # ==========================
    # ARXIV
    # ==========================

    @bot.message_handler(
        func=lambda m: m.text == "🗄 O'quvchilar arxivi"
    )
    def archive_start(message):

        if not _is_admin(message.chat.id):
            return

        rows = get_archived_students()

        if not rows:

            bot.send_message(
                message.chat.id,
                "🗄 Arxiv bo'sh.\n\n"
                "Maktabdan ketgan o'quvchini o'qituvchi «👨‍🎓 O'quvchilar "
                "ro'yxati» → o'quvchi → «🗄 Arxivga olish» orqali arxivlaydi.\n\n"
                "Arxivdagi o'quvchi ro'yxatlarda va hisobotlarda ko'rinmaydi, "
                "lekin to'lov tarixi saqlanib qoladi."
            )

            return

        markup = types.InlineKeyboardMarkup()

        for index, (teacher, student, at, reason) in enumerate(rows[:25]):

            ctx.setdefault(message.chat.id, {})[index] = (teacher, student)

            markup.add(
                types.InlineKeyboardButton(
                    "♻️ " + student[:30] + " (" + teacher[:15] + ")",
                    callback_data="arch:r:" + str(index)
                )
            )

        lines = [
            "👨‍🎓 " + student + "\n   " + teacher
            + "\n   " + (at or "?")
            + ((" · " + reason) if reason else "")
            for teacher, student, at, reason in rows[:25]
        ]

        bot.send_message(
            message.chat.id,
            "🗄 Arxivdagi o'quvchilar (" + str(len(rows)) + " ta):\n\n"
            + "\n\n".join(lines)
            + "\n\nQaytarish uchun ism ustiga bosing.",
            reply_markup=markup
        )


    @bot.callback_query_handler(
        func=lambda c: c.data.startswith("arch:r:")
    )
    def archive_restore(call):

        chat_id = call.message.chat.id

        if not _is_admin(chat_id):
            return

        index = int(call.data.split(":", 2)[2])

        pair = ctx.get(chat_id, {}).get(index)

        if not pair:

            bot.answer_callback_query(call.id, "Xatolik, qaytadan oching")

            return

        teacher, student = pair

        restore_student(teacher, student)

        bot.answer_callback_query(call.id, "♻️ Qaytarildi")

        log_action(
            str(chat_id), "o'quvchini arxivdan qaytardi",
            student, teacher, actor_role="admin"
        )

        bot.send_message(
            chat_id,
            "♻️ " + student + " arxivdan qaytarildi.\n"
            "Endi u yana " + teacher + " ro'yxatida ko'rinadi."
        )
