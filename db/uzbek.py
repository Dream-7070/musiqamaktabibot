# -*- coding: utf-8 -*-
# ==========================
# db/uzbek.py
# O'ZBEKCHA YOZUV FARQLARI
# ==========================
#
# Maktab ro'yxatlarida bir ism bir necha xil yoziladi:
#
#   Maxmudov Bexruz Ma'sudjon ugli
#   Mahmudov Behruz Masudjon o'g'li
#
# Oddiy `LIKE '%behruz%'` bunday yozuvni TOPMAYDI - xodim
# qidiradi, hech narsa chiqmaydi va o'quvchi "yo'q" deb
# o'ylanadi. Aynan shu voqea bo'lgan.
#
# Bu modul taqqoslash uchun "kanonik" ko'rinish yasaydi:
#   x=h, o'=u, g'=g, apostroflar olib tashlanadi.
#
# DIQQAT: natija FAQAT solishtirish uchun - foydalanuvchiga
# hech qachon ko'rsatilmaydi.
#
# Bu modul db/ paketining boshqa modullarini import QILMAYDI
# (faqat `re`), shuning uchun uni to'g'ridan-to'g'ri
# `from db.uzbek import ...` deb chaqirish xavfsiz. Fasadga
# (database.py) ATAYLAB qo'shilmagan: `normalize`, `matches`
# kabi umumiy nomlar butun loyiha nomlari bilan chalkashardi.
#
# ==========================


import re


# ==========================
# NORMALLASHTIRISH
# ==========================

def normalize(text):
    """
    Matnni taqqoslash uchun standart ko'rinishga keltiruvchi funksiya.
    Bu natija foydalanuvchiga ko'rsatilmaydi, faqat qidiruv uchun ishlatiladi.
    """
    # 1. Agar qiymat None bo'lsa, bo'sh satr qaytaramiz
    if text is None:
        return ""


    # Satrga o'g'iramiz va kichik harflarga o'tkazamiz
    text = str(text).casefold()


    # 2. Barcha turdagi apostrofga o'xshash belgilarni yagona ASCII "'" belgisiga o'tkazamiz
    text = re.sub(r"[‘’ʻʼ`´′]", "'", text)


    # 3. Qo'shaloq harflarni qisqartirish (o' -> u, g' -> g).
    # Bu qadam apostroflarni olib tashlashdan oldin bajarilishi shart,
    # chunki apostroflar olib tashlangandan so'ng "o'" bilan oddiy "o" ni farqlab bo'lmaydi.
    text = text.replace("o'", "u").replace("g'", "g")


    # 4. Qolgan barcha apostroflarni olib tashlaymiz
    text = text.replace("'", "")


    # 5. Yakka harflarni almashtirish.
    # 'ch' va 'sh' harflari 'c' -> 's' qoidasiga tushib qolmasligi uchun oldin ularni 
    # maxsus belgilarga o'tkazamiz, so'ngra x -> h, c -> s qilamiz va yana o'z holiga qaytaramiz.
    text = text.replace("ch", "\x01").replace("sh", "\x02")
    text = text.replace("x", "h").replace("c", "s")
    text = text.replace("\x01", "ch").replace("\x02", "sh")


    # 6. Bo'shliqlarni bitta joyga qisqartiramiz va chetlarini tozalaymiz
    text = re.sub(r"\s+", " ", text).strip()


    # 7. Ikki marta ketma-ket kelgan harflarni bittaga qisqartiramiz. 
    # Bu eng oxirgi qadam bo'lishi shart.
    text = re.sub(r"(.)\1+", r"\1", text)


    return text


# ==========================
# QIDIRUV VA TAQQOSLASH
# ==========================

def matches(query, value):
    """
    So'rov matni qidirilayotgan qiymat ichida mavjudligini tekshiradi.
    """
    norm_query = normalize(query)


    # Bo'sh so'rovlar har doim False qaytaradi
    if not norm_query:
        return False


    norm_value = normalize(value)


    return norm_query in norm_value


def filter_matches(query, rows, key=None):
    """
    Ro'yxatdan faqat mos keladigan qatorlarni ajratib oladi, asl tartibni saqlab qoladi.
    """
    result = []


    for row in rows:
        text = key(row) if key is not None else row


        if matches(query, text):
            result.append(row)


    return result


def sort_key(query, value):
    """
    Natijalarni tartiblash uchun kalit (tuple) qaytaradi.
    Oldin boshidan mos kelganlar, keyin mos kelgan joylashuvi, so'ngra matnning o'zi.
    """
    norm_query = normalize(query)


    norm_value = normalize(value)


    if not norm_query:
        return (1, 999999, norm_value)


    starts_with = 0 if norm_value.startswith(norm_query) else 1


    index = norm_value.find(norm_query)


    if index == -1:
        index = 999999


    return (starts_with, index, norm_value)


# ==========================
# TESTLAR
# ==========================

if __name__ == "__main__":
    assert matches("behruz", "Maxmudov Bexruz Ma'sudjon ugli") is True, "behruz mos kelmadi"
    assert matches("mahmudov", "Maxmudov Bexruz") is True, "mahmudov mos kelmadi"
    assert matches("o'g'li", "ugli") is True, "o'g'li mos kelmadi"
    assert matches("notani varaqdan o'qish", "notani varaqdan uqish") is True, "o'qish mos kelmadi"
    assert matches("solfedjio", "Mutaxassislik") is False, "Solfedjio mos kelmasligi kerak"
    assert matches("", "har qanday") is False, "Bo'sh so'rov mos kelmasligi kerak"


    print("uzbek.py: hammasi joyida")
