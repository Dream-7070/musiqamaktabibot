# ==========================
# webapp/auth.py
# TELEGRAM WEB APP - INITDATA TEKSHIRUVI
# ==========================
#
# Mini App Telegram ichida ochilganda, frontend'ga
# "initData" degan imzolangan matn beriladi. Bu matn
# foydalanuvchi ID'sini o'z ichiga oladi, lekin uni
# ISHONCH bilan ishlatishdan oldin TEKSHIRISH SHART -
# aks holda birov o'zini boshqa odam qilib ko'rsatishi
# mumkin.
#
# Tekshirish rasmiy Telegram hujjatidagi algoritm bo'yicha:
# https://core.telegram.org/bots/webapps#validating-data-received-via-the-web-app
#
# ==========================


import hashlib
import hmac
import json
import time
from urllib.parse import parse_qsl


# initData necha soniyagacha "yangi" hisoblanadi
# (undan eski bo'lsa, qayta ochilgan eski havola bo'lishi mumkin)

MAX_AGE_SECONDS = 24 * 3600


def validate_init_data(init_data, bot_token):
    """
    initData ni tekshiradi.

    Muvaffaqiyatli bo'lsa: (True, user_dict)
    Muvaffaqiyatsiz bo'lsa: (False, xato_matni)
    """

    if not init_data:
        return False, "initData bo'sh"

    try:
        pairs = dict(parse_qsl(init_data, strict_parsing=True))

    except ValueError:
        return False, "initData formati noto'g'ri"

    received_hash = pairs.pop("hash", None)

    if not received_hash:
        return False, "hash topilmadi"

    data_check_string = "\n".join(
        f"{key}={value}"
        for key, value in sorted(pairs.items())
    )

    secret_key = hmac.new(
        b"WebAppData",
        bot_token.encode(),
        hashlib.sha256
    ).digest()

    computed_hash = hmac.new(
        secret_key,
        data_check_string.encode(),
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(computed_hash, received_hash):
        return False, "imzo mos emas"

    auth_date = int(pairs.get("auth_date", 0))

    if time.time() - auth_date > MAX_AGE_SECONDS:
        return False, "initData eskirgan, Mini App'ni qayta oching"

    user_raw = pairs.get("user")

    if not user_raw:
        return False, "foydalanuvchi ma'lumoti topilmadi"

    try:
        user = json.loads(user_raw)

    except ValueError:
        return False, "foydalanuvchi ma'lumoti buzilgan"

    return True, user
