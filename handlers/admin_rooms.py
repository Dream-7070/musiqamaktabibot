# ==========================
# handlers/admin_rooms.py
# ADMIN - DARS XONALARI
# ==========================
#
# Xonalar ro'yxati bazada (`rooms` jadvali) saqlanadi va
# o'qituvchi dars qo'yayotganda shu ro'yxatdan tanlaydi.
# Bu yerda admin yangi xona qo'shadi yoki keraksizini
# o'chiradi.
#
# Xonada dars bo'lsa - o'chirilmaydi, aks holda jadval
# ma'nosini yo'qotadi.
#
# ==========================


from telebot import types

from config import ADMIN_IDS

from database import (
    get_rooms,
    add_room,
    delete_room,
    log_action
)


# chat_id -> nima kutilyapti ("code" yoki {"code": ...})
pending = {}


def register_admin_rooms(bot):


    def show_rooms(chat_id):

        rooms = get_rooms()

        markup = types.InlineKeyboardMarkup()

        markup.add(
            types.InlineKeyboardButton(
                "➕ Yangi xona qo'shish",
                callback_data="arm:new"
            )
        )

        for room in rooms:

            markup.add(
                types.InlineKeyboardButton(
                    "🗑 " + room["label"],
                    callback_data="arm:del:" + str(room["id"])
                )
            )

        text = (
            "🚪 Dars xonalari - " + str(len(rooms)) + " ta\n\n"
            "O'qituvchi dars qo'yayotganda shu ro'yxatdan tanlaydi.\n"
            "O'chirish uchun xona ustiga bosing."
        )

        bot.send_message(chat_id, text, reply_markup=markup)


    @bot.message_handler(
        func=lambda m:
        m.text == "🚪 Xonalar"
        and m.chat.id in ADMIN_IDS
    )
    def rooms_menu(message):

        show_rooms(message.chat.id)


    # ==========================
    # YANGI XONA
    # ==========================

    @bot.callback_query_handler(
        func=lambda c: c.data == "arm:new"
    )
    def new_room(call):

        chat_id = call.message.chat.id

        if chat_id not in ADMIN_IDS:

            bot.answer_callback_query(call.id, "Ruxsat yo'q")

            return

        bot.answer_callback_query(call.id)

        pending[chat_id] = "code"

        sent = bot.send_message(
            chat_id,
            "🚪 Yangi xona raqamini yozing.\n\n"
            "Masalan: 2/20\n\n"
            "Agar xonaning nomi bo'lsa - raqamdan keyin yozing:\n"
            "2/20 Zal"
        )

        bot.register_next_step_handler(sent, save_room)


    def save_room(message):

        chat_id = message.chat.id

        if pending.pop(chat_id, None) != "code":
            return

        raw = (message.text or "").strip()

        if not raw:

            bot.send_message(chat_id, "❌ Bo'sh yuborildi. Qaytadan urinib ko'ring.")

            return


        # birinchi so'z - raqam, qolgani - nomi

        parts = raw.split(None, 1)

        code = parts[0]
        name = parts[1].strip() if len(parts) > 1 else ""

        ok, result = add_room(code, name)

        if not ok:

            bot.send_message(chat_id, "❌ " + result)

            show_rooms(chat_id)

            return

        log_action(
            str(chat_id), "xona qo'shdi",
            result["label"], "", actor_role="admin"
        )

        bot.send_message(chat_id, "✅ Qo'shildi: " + result["label"])

        show_rooms(chat_id)


    # ==========================
    # O'CHIRISH
    # ==========================

    @bot.callback_query_handler(
        func=lambda c: c.data.startswith("arm:del:")
    )
    def ask_delete(call):

        chat_id = call.message.chat.id

        if chat_id not in ADMIN_IDS:

            bot.answer_callback_query(call.id, "Ruxsat yo'q")

            return

        room_id = int(call.data.split(":")[2])

        rooms = {r["id"]: r for r in get_rooms()}

        room = rooms.get(room_id)

        if not room:

            bot.answer_callback_query(call.id, "Xona topilmadi")

            return

        bot.answer_callback_query(call.id)

        markup = types.InlineKeyboardMarkup()

        markup.add(
            types.InlineKeyboardButton(
                "🗑 Ha, o'chirilsin",
                callback_data="arm:delok:" + str(room_id)
            )
        )

        markup.add(
            types.InlineKeyboardButton(
                "⬅️ Yo'q",
                callback_data="arm:list"
            )
        )

        bot.send_message(
            chat_id,
            "🗑 " + room["label"] + " o'chirilsinmi?",
            reply_markup=markup
        )


    @bot.callback_query_handler(
        func=lambda c: c.data.startswith("arm:delok:")
    )
    def do_delete(call):

        chat_id = call.message.chat.id

        if chat_id not in ADMIN_IDS:

            bot.answer_callback_query(call.id, "Ruxsat yo'q")

            return

        room_id = int(call.data.split(":")[2])

        ok, result = delete_room(room_id)

        bot.answer_callback_query(call.id)

        if not ok:

            bot.send_message(chat_id, "❌ " + result)

            show_rooms(chat_id)

            return

        log_action(
            str(chat_id), "xonani o'chirdi",
            result["label"], "", actor_role="admin"
        )

        bot.send_message(chat_id, "🗑 O'chirildi: " + result["label"])

        show_rooms(chat_id)


    @bot.callback_query_handler(
        func=lambda c: c.data == "arm:list"
    )
    def back_to_rooms(call):

        bot.answer_callback_query(call.id)

        show_rooms(call.message.chat.id)
