# ==========================
# handlers/admin_staff.py
# ADMIN - XODIMLARNI BOSHQARISH
# ==========================
#
# Buxgalter, direktor va yordamchi rollari o'z-o'zidan
# olinmaydi - ularni faqat admin beradi.
#
# Xodim avval botga /start bosishi kerak (shunda uning
# Telegram ID si paydo bo'ladi), so'ng admin shu ID ni
# kiritib rol biriktiradi.
#
# ==========================


from telebot import types

from config import ADMIN_IDS

from database import (
    STAFF_ROLES,
    add_staff_directly,
    list_staff,
    remove_staff
)


pending = {}


def register_admin_staff(bot):


    @bot.message_handler(
        func=lambda m:
        m.text == "👥 Xodimlar"
        and m.chat.id in ADMIN_IDS
    )
    def staff_menu(message):

        _show_staff_list(message.chat.id)


    def _show_staff_list(chat_id):

        rows = list_staff()

        markup = types.InlineKeyboardMarkup()

        text = "👥 Xodimlar\n\n"

        if rows:

            for staff_id, telegram_id, role, full_name, status in rows:

                label = STAFF_ROLES.get(role, role)

                text += (
                    label + "\n"
                    + (full_name or "ismsiz")
                    + " · 🆔 " + str(telegram_id)
                    + ("" if status == "approved" else " (" + status + ")")
                    + "\n\n"
                )

                markup.add(
                    types.InlineKeyboardButton(
                        "🗑 " + (full_name or str(telegram_id))[:30],
                        callback_data="staff:del:" + str(staff_id)
                    )
                )

        else:

            text += "Hali xodim qo'shilmagan.\n\n"

        text += (
            "➕ Yangi xodim qo'shish uchun avval u botga "
            "/start bossin, so'ng uning Telegram ID sini kiriting."
        )

        markup.add(
            types.InlineKeyboardButton(
                "➕ Xodim qo'shish",
                callback_data="staff:add"
            )
        )

        bot.send_message(chat_id, text, reply_markup=markup)


    # ==========================
    # QO'SHISH
    # ==========================

    @bot.callback_query_handler(
        func=lambda c: c.data == "staff:add"
        and c.message.chat.id in ADMIN_IDS
    )
    def staff_add_role(call):

        markup = types.InlineKeyboardMarkup()

        for key, label in STAFF_ROLES.items():

            markup.add(
                types.InlineKeyboardButton(
                    label,
                    callback_data="staff:role:" + key
                )
            )

        bot.answer_callback_query(call.id)

        bot.send_message(
            call.message.chat.id,
            "Qaysi rol?",
            reply_markup=markup
        )


    @bot.callback_query_handler(
        func=lambda c: c.data.startswith("staff:role:")
        and c.message.chat.id in ADMIN_IDS
    )
    def staff_ask_id(call):

        chat_id = call.message.chat.id

        role = call.data.split(":", 2)[2]

        if role not in STAFF_ROLES:

            bot.answer_callback_query(call.id, "Noto'g'ri rol")

            return

        pending[chat_id] = {"role": role}

        bot.answer_callback_query(call.id)

        sent = bot.send_message(
            chat_id,
            "🆔 " + STAFF_ROLES[role] + " uchun Telegram ID ni kiriting:\n\n"
            "(Xodim botga /start bosgan bo'lishi kerak. "
            "ID ni bilmasa, u @userinfobot ga yozib olishi mumkin.)"
        )

        bot.register_next_step_handler(sent, staff_receive_id)


    def staff_receive_id(message):

        chat_id = message.chat.id

        data = pending.get(chat_id)

        if not data:

            bot.send_message(chat_id, "❌ Xatolik. Qaytadan boshlang.")

            return

        digits = "".join(ch for ch in (message.text or "") if ch.isdigit())

        if not digits:

            sent = bot.send_message(
                chat_id,
                "❌ Bu raqamga o'xshamaydi. Telegram ID ni qaytadan kiriting:"
            )

            bot.register_next_step_handler(sent, staff_receive_id)

            return

        data["telegram_id"] = int(digits)

        sent = bot.send_message(
            chat_id,
            "👤 Xodimning ism-familiyasini yozing:"
        )

        bot.register_next_step_handler(sent, staff_save)


    def staff_save(message):

        chat_id = message.chat.id

        data = pending.pop(chat_id, None)

        if not data or "telegram_id" not in data:

            bot.send_message(chat_id, "❌ Xatolik. Qaytadan boshlang.")

            return

        full_name = (message.text or "").strip() or "Ismsiz"

        add_staff_directly(data["telegram_id"], data["role"], full_name)

        label = STAFF_ROLES.get(data["role"], data["role"])

        bot.send_message(
            chat_id,
            "✅ Qo'shildi: " + full_name + " — " + label
        )

        # xodimning o'ziga xabar

        try:

            bot.send_message(
                data["telegram_id"],
                "✅ Sizga " + label + " roli berildi.\n"
                "Botni ishlatish uchun /start bosing."
            )

        except Exception:

            bot.send_message(
                chat_id,
                "⚠️ Xodimga xabar yetmadi — u hali botga /start "
                "bosmagan bo'lishi mumkin. Rol baribir saqlandi."
            )

        _show_staff_list(chat_id)


    # ==========================
    # O'CHIRISH
    # ==========================

    @bot.callback_query_handler(
        func=lambda c: c.data.startswith("staff:del:")
        and c.message.chat.id in ADMIN_IDS
    )
    def staff_delete(call):

        staff_id = int(call.data.split(":", 2)[2])

        row = remove_staff(staff_id)

        if not row:

            bot.answer_callback_query(call.id, "Topilmadi")

            return

        telegram_id, role, full_name = row

        bot.answer_callback_query(call.id, "🗑 O'chirildi")

        bot.edit_message_text(
            "🗑 O'chirildi: " + (full_name or str(telegram_id))
            + " — " + STAFF_ROLES.get(role, role),
            call.message.chat.id,
            call.message.message_id
        )
