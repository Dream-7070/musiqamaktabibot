# ==========================
# services/group_capacity.py
# GURUH HAJMI - ADMINGA BILDIRISHNOMA
# ==========================
#
# Guruh darsiga meʼyordan ko'p o'quvchi qo'shilsa - TO'SILMAYDI,
# faqat adminga xabar boradi (o'qituvchi ishini davom ettiraveradi).
#
# Meʼyordan kam bo'lsa - kunlik eslatma orqali (services/daily_reminders.py
# ichidan chaqiriladi, bu yerda emas).
#
# Bot ham, Mini App (webapp) ham shu funksiyani chaqiradi - ikkalasi
# ham o'z `send_message` funksiyasini beradi (telebot instansiyasi
# bog'lab qo'yilgan usul).
#
# ==========================


from config import ADMIN_IDS

from database import get_slot_group_status, get_slot


def notify_if_overcapacity(send_message, slot_id):
    """
    Dars meʼyordan ortiq bo'lsa - har bir adminga xabar yuboradi.

    `send_message(chat_id, text)` - chaqiruvchi tomonidan beriladi,
    chunki bot instansiyasi bot va webapp'da har xil.
    """

    status = get_slot_group_status(slot_id)

    if not status or status["status"] != "ortiq":
        return

    slot = get_slot(slot_id)

    if not slot:
        return

    _, teacher, subject, day, time, room = slot

    text = (
        "⚠️ Guruh meʼyordan ortiq\n\n"
        "📚 " + subject + " · " + teacher + "\n"
        "🗓 " + day + " " + time + " · 🚪 " + room + "\n\n"
        + str(status["count"]) + " ta o'quvchi (meʼyor: "
        + str(status["min"]) + "-" + str(status["max"]) + " nafar).\n\n"
        "Dars to'silmadi - bu faqat ogohlantirish."
    )

    for admin_id in ADMIN_IDS:

        try:
            send_message(admin_id, text)
        except Exception:
            # admin botni bloklagan yoki hali /start bosmagan bo'lishi mumkin
            pass
