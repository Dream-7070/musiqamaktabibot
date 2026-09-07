# ==========================
# data/curriculum.py
# 2026-YIL TAYANCH O'QUV REJASI
# ==========================
#
# O'zbekiston Respublikasi Madaniyat vazirligi tasdiqlagan
# "Bolalar musiqa va san'at maktablarining tayanch o'quv
# rejalari" hujjatidan avtomatik ajratilgan.
#
# Tuzilishi:
#   CURRICULUM[mutaxassislik] = {
#       "years":    ta'lim muddati (5 yoki 7 yil),
#       "subjects": {fan: {sinf: haftalik akademik soat}}
#   }
#
# Har bir satr rejaning "Umumiy soatlar" ustuni bilan
# tekshirilgan: haftalik yig'indi x 34 hafta. 305 satrdan
# 303 tasi mos keldi; qolgan 2 tasi Askiya san'atida -
# u yerda rejaning o'zida qarama-qarshilik bor.
#
# Bu fayl QO'LDA TAHRIRLANMAYDI:
#     python scripts/build_curriculum.py
# ==========================


# bir o'quv yilidagi hafta soni

WEEKS_PER_YEAR = 34


# Bir dars nechta akademik soatgacha bo'linmasdan o'tiladi.
#
# 0,5 / 1 / 1,5 soatlik fanlar bo'linmaydi - bitta dars
# bo'lib o'tiladi. 2 soatdan boshlab esa haftaning turli
# kunlariga bo'lish mumkin (reja 6.5-bandi).

MIN_SPLITTABLE_HOURS = 2


CURRICULUM = {

    "Akademik xonandalik": {
        "years": 5,
        "subjects": {
            "Aktyorlik mahorati": {"2": 0.5, "3": 0.5, "4": 0.5, "5": 0.5},
            "Jamoa ijrochiligi (xor, vokal ansambli)": {"1": 2, "2": 3, "3": 3, "4": 3, "5": 3},
            "Maqom alifbosi": {"1": 1},
            "Mutaxassislik": {"1": 2, "2": 2, "3": 2, "4": 2, "5": 3},
            "Ovozni yo‘lga qo‘yish": {"1": 1, "2": 1, "3": 1, "4": 1, "5": 1},
            "O‘zbek musiqa adabiyoti": {"4": 1, "5": 1},
            "Solfedjio": {"1": 1.5, "2": 1.5, "3": 1.5, "4": 1.5, "5": 2},
            "Tanlangan fan": {"2": 0.5, "3": 0.5, "4": 0.5, "5": 0.5},
            "Umumiy fortepiano": {"1": 0.5, "2": 1, "3": 1, "4": 1, "5": 1},
            "Xorij musiqa adabiyoti": {"2": 1, "3": 1},
        }
    },

    "An’anaviy cholg‘ular ijrochiligi": {
        "years": 5,
        "subjects": {
            "Jamoa ijrochiligi (maqom ansambli, folklor ansambli va boshqalar)": {"1": 2, "2": 3, "3": 3, "4": 3, "5": 3},
            "Maqom alifbosi": {"1": 1},
            "Maqom asoslari": {"2": 1, "3": 1, "4": 1, "5": 1},
            "Mutaxassislik": {"1": 2, "2": 2, "3": 2, "4": 2, "5": 3},
            "Notani varaqdan o‘qish": {"2": 1, "3": 1, "4": 1, "5": 1},
            "O‘zbek musiqa adabiyoti": {"4": 1, "5": 1},
            "Solfedjio": {"1": 1.5, "2": 1.5, "3": 1.5, "4": 1.5, "5": 2},
            "Tanlangan fan": {"2": 0.5, "3": 0.5, "4": 0.5, "5": 0.5},
            "Umumiy fortepiano": {"1": 0.5, "2": 1, "3": 1, "4": 1, "5": 1},
            "Xorij musiqa adabiyoti": {"2": 1, "3": 1},
        }
    },

    "An’anaviy xonandalik": {
        "years": 5,
        "subjects": {
            "Jamoa ijrochiligi (maqom ansambli, folklor ansambli va boshqalar)": {"1": 2, "2": 3, "3": 3, "4": 3, "5": 3},
            "Maqom alifbosi": {"1": 1},
            "Maqom asoslari": {"2": 1, "3": 1, "4": 1, "5": 1},
            "Mutaxassislik": {"1": 2, "2": 2, "3": 2, "4": 2, "5": 3},
            "Ovozni yo‘lga qo‘yish": {"1": 1, "2": 1, "3": 1, "4": 1, "5": 1},
            "O‘zbek musiqa adabiyoti": {"4": 1, "5": 1},
            "Solfedjio": {"1": 1.5, "2": 1.5, "3": 1.5, "4": 1.5, "5": 2},
            "Tanlangan fan": {"2": 0.5, "3": 0.5, "4": 0.5, "5": 0.5},
            "Umumiy fortepiano": {"1": 0.5, "2": 1, "3": 1, "4": 1, "5": 1},
            "Xorij musiqa adabiyoti": {"2": 1, "3": 1},
        }
    },

    "Arxitektura dizayni": {
        "years": 5,
        "subjects": {
            "Arxitektura grafikasi va maket texnologiyasi": {"1": 1, "2": 1, "3": 1, "4": 1, "5": 1},
            "Chizmatasvir": {"1": 2, "2": 2, "3": 2, "4": 2, "5": 2},
            "Kompozitsiya": {"1": 2, "2": 2, "3": 2, "4": 2, "5": 2},
            "Mutaxassislik (arxitektura dizayni)": {"1": 2, "2": 2, "3": 3, "4": 4, "5": 4},
            "Pesrpektiva": {"1": 1, "2": 1, "3": 1, "4": 1, "5": 1},
            "Rangtasvir": {"1": 1, "2": 1, "3": 1, "4": 1, "5": 1},
            "Tanlangan fan": {"2": 0.5, "3": 0.5, "4": 0.5, "5": 0.5},
            "Tasviriy va amaliy san’at tarixi": {"2": 1, "3": 1, "4": 1, "5": 1},
        }
    },

    "Askiya san’ati": {
        "years": 5,
        "subjects": {
            "Askiya san’ati tarixi": {"4": 1, "5": 1},
            "Badihagoylik san’ati": {"2": 1, "3": 1, "4": 1, "5": 1},
            "Hajviy asarlarni sahnalashtirish": {"1": 1, "2": 2, "3": 2, "4": 2, "5": 2},
            "Mutaxassislik (Aktyorlik mahorati (xalqona shakl))": {"1": 2, "2": 2, "3": 2, "4": 2, "5": 3},
            "O‘zbek xalq tomosha san’ati": {"2": 1, "3": 1},
            "Ritmika va plastika": {"1": 1, "2": 1, "3": 1, "4": 1, "5": 1},
            "Sahna nutqi": {"1": 1, "2": 1, "3": 1, "4": 1, "5": 1},
            "Sahna xarakati": {"1": 1, "2": 1, "3": 1, "4": 1, "5": 1},
            "Tanlangan fan": {"2": 0.5, "3": 0.5, "4": 0.5, "5": 0.5},
        }
    },

    "Badiiy ganch o‘ymakorligi": {
        "years": 5,
        "subjects": {
            "Ashyolarga badiiy ishlov berish": {"1": 1, "2": 1, "3": 1, "4": 1, "5": 1},
            "Chizmatasvir": {"1": 2, "2": 2, "3": 2, "4": 2, "5": 2},
            "Kompozitsiya": {"1": 2, "2": 2, "3": 2, "4": 2, "5": 2},
            "Mutaxassislik (badiiy ganch o‘ymakorligi)": {"1": 2, "2": 2, "3": 3, "4": 4, "5": 4},
            "Rangtasvir": {"1": 2, "2": 2, "3": 2, "4": 2, "5": 2},
            "Tanlangan fan": {"2": 0.5, "3": 0.5, "4": 0.5, "5": 0.5},
            "Tasviriy va amaliy san’at tarixi": {"2": 1, "3": 1, "4": 1, "5": 1},
        }
    },

    "Badiiy kashtachilik": {
        "years": 5,
        "subjects": {
            "Chizmatasvir": {"1": 2, "2": 2, "3": 2, "4": 2, "5": 2},
            "Kashta tikish texnologiyasi": {"1": 1, "2": 1, "3": 1, "4": 1, "5": 1},
            "Kompozitsiya": {"1": 2, "2": 2, "3": 2, "4": 2, "5": 2},
            "Mutaxassislik (badiiy kashtachilik)": {"1": 2, "2": 2, "3": 3, "4": 4, "5": 4},
            "Rangtasvir": {"1": 2, "2": 2, "3": 2, "4": 2, "5": 2},
            "Tanlangan fan": {"2": 0.5, "3": 0.5, "4": 0.5, "5": 0.5},
            "Tasviriy va amaliy san’at tarixi": {"2": 1, "3": 1, "4": 1, "5": 1},
        }
    },

    "Badiiy kulolchilik": {
        "years": 5,
        "subjects": {
            "Ashyolarga badiiy ishlov berish": {"1": 1, "2": 1, "3": 1, "4": 1, "5": 1},
            "Chizmatasvir": {"1": 2, "2": 2, "3": 2, "4": 2, "5": 2},
            "Kompozitsiya": {"1": 2, "2": 2, "3": 2, "4": 2, "5": 2},
            "Mutaxassislik (badiiy kulolchilik)": {"1": 2, "2": 2, "3": 3, "4": 4, "5": 4},
            "Rangtasvir": {"1": 2, "2": 2, "3": 2, "4": 2, "5": 2},
            "Tanlangan fan": {"2": 0.5, "3": 0.5, "4": 0.5, "5": 0.5},
            "Tasviriy va amaliy san’at tarixi": {"2": 1, "3": 1, "4": 1, "5": 1},
        }
    },

    "Badiiy misgarlik": {
        "years": 5,
        "subjects": {
            "Ashyolarga badiiy ishlov berish": {"1": 1, "2": 1, "3": 1, "4": 1, "5": 1},
            "Chizmatasvir": {"1": 2, "2": 2, "3": 2, "4": 2, "5": 2},
            "Kompozitsiya": {"1": 2, "2": 2, "3": 2, "4": 2, "5": 2},
            "Mutaxassislik (badiiy misgarlik)": {"1": 2, "2": 2, "3": 3, "4": 4, "5": 4},
            "Rangtasvir": {"1": 2, "2": 2, "3": 2, "4": 2, "5": 2},
            "Tanlangan fan": {"2": 0.5, "3": 0.5, "4": 0.5, "5": 0.5},
            "Tasviriy va amaliy san’at tarixi": {"2": 1, "3": 1, "4": 1, "5": 1},
        }
    },

    "Badiiy naqqoshlik": {
        "years": 5,
        "subjects": {
            "Ashyolarga badiiy ishlov berish": {"1": 1, "2": 1, "3": 1, "4": 1, "5": 1},
            "Chizmatasvir": {"1": 2, "2": 2, "3": 2, "4": 2, "5": 2},
            "Kompozitsiya": {"1": 2, "2": 2, "3": 2, "4": 2, "5": 2},
            "Mutaxassislik (badiiy naqqoshlik)": {"1": 2, "2": 2, "3": 3, "4": 4, "5": 4},
            "Rangtasvir": {"1": 2, "2": 2, "3": 2, "4": 2, "5": 2},
            "Tanlangan fan": {"2": 0.5, "3": 0.5, "4": 0.5, "5": 0.5},
            "Tasviriy va amaliy san’at tarixi": {"2": 1, "3": 1, "4": 1, "5": 1},
        }
    },

    "Badiiy yog‘och o‘ymakorligi": {
        "years": 5,
        "subjects": {
            "Ashyolarga badiiy ishlov berish": {"1": 1, "2": 1, "3": 1, "4": 1, "5": 1},
            "Chizmatasvir": {"1": 2, "2": 2, "3": 2, "4": 2, "5": 2},
            "Kompozitsiya": {"1": 2, "2": 2, "3": 2, "4": 2, "5": 2},
            "Mutaxassislik (badiiy yog‘och o‘ymakorligi,)": {"1": 2, "2": 2, "3": 3, "4": 4, "5": 4},
            "Rangtasvir": {"1": 2, "2": 2, "3": 2, "4": 2, "5": 2},
            "Tanlangan fan": {"2": 0.5, "3": 0.5, "4": 0.5, "5": 0.5},
            "Tasviriy va amaliy san’at tarixi": {"2": 1, "3": 1, "4": 1, "5": 1},
        }
    },

    "Badiiy zardo‘zlik": {
        "years": 5,
        "subjects": {
            "Chizmatasvir": {"1": 2, "2": 2, "3": 2, "4": 2, "5": 2},
            "Kompozitsiya": {"1": 2, "2": 2, "3": 2, "4": 2, "5": 2},
            "Mutaxassislik (badiiy zardo‘zlik)": {"1": 2, "2": 2, "3": 3, "4": 4, "5": 4},
            "Rangtasvir": {"1": 2, "2": 2, "3": 2, "4": 2, "5": 2},
            "Tanlangan fan": {"2": 0.5, "3": 0.5, "4": 0.5, "5": 0.5},
            "Tasviriy va amaliy san’at tarixi": {"2": 1, "3": 1, "4": 1, "5": 1},
            "Zardo‘z tikish texnologiyasi": {"1": 1, "2": 1, "3": 1, "4": 1, "5": 1},
        }
    },

    "Badiiy zargarlik": {
        "years": 5,
        "subjects": {
            "Ashyolarga badiiy ishlov berish": {"1": 1, "2": 1, "3": 1, "4": 1, "5": 1},
            "Chizmatasvir": {"1": 2, "2": 2, "3": 2, "4": 2, "5": 2},
            "Kompozitsiya": {"1": 2, "2": 2, "3": 2, "4": 2, "5": 2},
            "Mutaxassislik (badiiy zargarlik)": {"1": 2, "2": 2, "3": 3, "4": 4, "5": 4},
            "Rangtasvir": {"1": 2, "2": 2, "3": 2, "4": 2, "5": 2},
            "Tanlangan fan": {"2": 0.5, "3": 0.5, "4": 0.5, "5": 0.5},
            "Tasviriy va amaliy san’at tarixi": {"2": 1, "3": 1, "4": 1, "5": 1},
        }
    },

    "Baxshichilik ijrochiligi": {
        "years": 5,
        "subjects": {
            "Badixago‘ylik (improvizatsiya) va dostonlar ijrochiligi, nutq madaniyati": {"1": 0.5, "2": 1, "3": 1, "4": 1, "5": 1},
            "Baxshi, jirov va oqinlar san’at tarixi": {"4": 1, "5": 1},
            "Jamoa ijrochiligi (cholg‘u va xonanda aralashgan holda)": {"1": 1, "2": 2, "3": 2, "4": 2, "5": 2},
            "Maqom alifbosi": {"1": 1},
            "Mutaxassislik (a - xonandalik, b - cholg‘u ijrochiligi)": {"1": 1, "2": 1, "3": 1, "4": 1, "5": 2},
            "Ovozni yo‘lga qo‘yish": {"1": 1, "2": 1, "3": 1, "4": 1, "5": 1},
            "Solfedjio": {"1": 1.5, "2": 1.5, "3": 1.5, "4": 1.5, "5": 2},
            "Tanlangan fan": {"2": 0.5, "3": 0.5, "4": 0.5, "5": 0.5},
            "Umumiy fortepiano": {"1": 0.5, "2": 1, "3": 1, "4": 1, "5": 1},
            "Xorij va o‘zbek musiqa adabiyoti": {"2": 1, "3": 1},
        }
    },

    "Damli va zarbli cholg‘ular ijrochiligi": {
        "years": 5,
        "subjects": {
            "Ansambl": {"2": 0.5, "3": 0.5, "4": 0.5, "5": 0.5},
            "Jamoa ijrochiligi": {"1": 2, "2": 3, "3": 3, "4": 3, "5": 3},
            "Maqom alifbosi": {"1": 1},
            "Mutaxassislik": {"1": 2, "2": 2, "3": 2, "4": 2, "5": 3},
            "Notani varaqdan o‘qish": {"2": 1, "3": 1, "4": 1, "5": 1},
            "O‘zbek musiqa adabiyoti": {"4": 1, "5": 1},
            "Solfedjio": {"1": 1.5, "2": 1.5, "3": 1.5, "4": 1.5, "5": 2},
            "Tanlangan fan": {"2": 0.5, "3": 0.5, "4": 0.5, "5": 0.5},
            "Umumiy fortepiano": {"1": 0.5, "2": 1, "3": 1, "4": 1, "5": 1},
            "Xorij musiqa adabiyoti": {"2": 1, "3": 1},
        }
    },

    "Dastgohli rangtasvir": {
        "years": 5,
        "subjects": {
            "Ashyolar bilan ishlash": {"1": 1, "2": 1, "3": 1, "4": 1, "5": 1},
            "Chizmatasvir": {"1": 2, "2": 2, "3": 2, "4": 2, "5": 2},
            "Kompozitsiya (amaliy)": {"1": 1, "2": 1, "3": 1, "4": 1, "5": 1},
            "Kompozitsiya (dastgohli)": {"1": 1, "2": 1, "3": 1, "4": 1, "5": 1},
            "Kompyuter grafikasi": {"1": 1, "2": 1, "3": 1, "4": 1, "5": 1},
            "Lepka": {"1": 1, "2": 1, "3": 1, "4": 1, "5": 1},
            "Mutaxassislik (dastgohli rangtasvir)": {"1": 2, "2": 2, "3": 3, "4": 4, "5": 4},
            "Tanlangan fan": {"2": 0.5, "3": 0.5, "4": 0.5, "5": 0.5},
            "Tasviriy va amaliy san’at tarixi": {"2": 1, "3": 1, "4": 1, "5": 1},
        }
    },

    "Estrada cholg‘ulari ijrochiligi – damli va zarbli cholg‘ular, gitara, bas gitara": {
        "years": 5,
        "subjects": {
            "Ansambl": {"2": 0.5, "3": 0.5, "4": 0.5, "5": 0.5},
            "Estrada tarixi": {"4": 1, "5": 1},
            "Maqom alifbosi": {"1": 1},
            "Mutaxassislik": {"1": 2, "2": 2, "3": 2, "4": 2, "5": 3},
            "Notani varaqdan o‘qish": {"2": 1, "3": 1, "4": 1, "5": 1},
            "Solfedjio": {"1": 1.5, "2": 1.5, "3": 1.5, "4": 1.5, "5": 2},
            "Tanlangan fan": {"2": 0.5, "3": 0.5, "4": 0.5, "5": 0.5},
            "Umumiy fortepiano": {"1": 0.5, "2": 1, "3": 1, "4": 1, "5": 1},
            "Xorij va o‘zbek musiqa adabiyoti": {"2": 1, "3": 1},
        }
    },

    "Estrada cholg‘ulari ijrochiligi – fortepiano, torli cholg‘ular": {
        "years": 7,
        "subjects": {
            "Akkompanement": {"5": 1, "6": 1, "7": 1},
            "Ansambl": {"3": 0.5, "4": 0.5, "5": 0.5, "6": 0.5, "7": 0.5},
            "Estrada tarixi": {"6": 1, "7": 1},
            "Jamoa ijrochiligi (xor, orkestor, vokal va cholg‘u ansambl turlari,)": {"1": 2, "2": 3, "3": 3, "4": 3, "5": 3, "6": 3, "7": 3},
            "Maqom alifbosi": {"3": 1},
            "Mutaxassislik": {"1": 2, "2": 2, "3": 2, "4": 2, "5": 2, "6": 2, "7": 3},
            "Notani varaqdan o‘qish": {"2": 1, "3": 1, "4": 1, "5": 1},
            "Solfedjio": {"1": 1.5, "2": 1.5, "3": 1.5, "4": 1.5, "5": 1.5, "6": 1.5, "7": 2},
            "Tanlangan fan": {"2": 0.5, "3": 0.5, "4": 0.5, "5": 0.5, "6": 0.5, "7": 0.5},
            "Umumiy fortepiano (torli cholg‘ular uchun)": {"1": 0.5, "2": 1, "3": 1, "4": 1, "5": 1, "6": 1, "7": 1},
            "Xorij va o‘zbek musiqa adabiyoti": {"4": 1, "5": 1},
        }
    },

    "Estrada raqs ijrochiligi": {
        "years": 5,
        "subjects": {
            "Klassik raqs": {"1": 2, "2": 2, "3": 2, "4": 2, "5": 2},
            "Musiqa savodi va musiqa tinglash": {"2": 1, "3": 1, "4": 1, "5": 1},
            "Mutaxassislik (estrada raqs ijrochiligi)": {"1": 2, "2": 2, "3": 3, "4": 4, "5": 4},
            "O‘zbek raqs": {"1": 2, "2": 2, "3": 3, "4": 4, "5": 4},
            "Raqs san’ati tarixi": {"4": 1, "5": 1},
            "Ritmika / parter": {"1": 1.5, "2": 1.5, "3": 0.5, "4": 0.5, "5": 0.5},
            "Tanlangan fan": {"2": 1, "3": 1, "4": 1, "5": 1},
            "Xalq sahna raqsi": {"4": 1, "5": 1},
        }
    },

    "Estrada xonandaligi": {
        "years": 5,
        "subjects": {
            "Aktyorlik mahorati": {"2": 0.5, "3": 0.5, "4": 0.5, "5": 0.5},
            "Jamoa ijrochiligi (xor, vokal ansambli)": {"1": 2, "2": 3, "3": 3, "4": 3, "5": 3},
            "Maqom alifbosi": {"1": 1},
            "Mutaxassislik": {"1": 2, "2": 2, "3": 2, "4": 2, "5": 3},
            "Ovozni yo‘lga qo‘yish": {"1": 1, "2": 1, "3": 1, "4": 1, "5": 1},
            "O‘zbek musiqa adabiyoti": {"4": 1, "5": 1},
            "Solfedjio": {"1": 1.5, "2": 1.5, "3": 1.5, "4": 1.5, "5": 2},
            "Tanlangan fan": {"2": 0.5, "3": 0.5, "4": 0.5, "5": 0.5},
            "Umumiy fortepiano": {"1": 0.5, "2": 1, "3": 1, "4": 1, "5": 1},
            "Xorij musiqa adabiyoti": {"2": 1, "3": 1},
        }
    },

    "Floristika dizayni": {
        "years": 5,
        "subjects": {
            "Ashyolar bilan ishlash": {"1": 1, "2": 1, "3": 1, "4": 1, "5": 1},
            "Chizmatasvir": {"1": 2, "2": 2, "3": 2, "4": 2, "5": 2},
            "Kompozitsiya": {"1": 2, "2": 2, "3": 2, "4": 2, "5": 2},
            "Lepka": {"1": 1, "2": 1, "3": 1, "4": 1, "5": 1},
            "Mutaxassislik (floristika dizayni)": {"1": 2, "2": 2, "3": 3, "4": 4, "5": 4},
            "Rangtasvir": {"1": 1, "2": 1, "3": 1, "4": 1, "5": 1},
            "Tanlangan fan": {"2": 0.5, "3": 0.5, "4": 0.5, "5": 0.5},
            "Tasviriy va amaliy san’at tarixi": {"2": 1, "3": 1, "4": 1, "5": 1},
        }
    },

    "Folklor ijrochilik san’ati": {
        "years": 5,
        "subjects": {
            "Folklor cholg‘ular ijrochiligi": {"4": 1, "5": 1},
            "Jamoa ijrochiligi (maqom ansambli, folklor ansambli va boshqalar)": {"1": 2, "2": 3, "3": 3, "4": 3, "5": 3},
            "Maqom alifbosi": {"1": 1},
            "Mutaxassislik (xalq qo‘shiqlari ijrosi)": {"1": 2, "2": 2, "3": 2, "4": 2, "5": 3},
            "Ovozni yo‘lga qo‘yish": {"1": 1, "2": 1, "3": 1, "4": 1, "5": 1},
            "O‘zbek xalq raqslari": {"1": 0.5, "2": 1, "3": 1, "4": 1, "5": 1},
            "Solfedjio": {"1": 1.5, "2": 1.5, "3": 1.5, "4": 1.5, "5": 2},
            "Tanlangan fan": {"2": 0.5, "3": 0.5, "4": 0.5, "5": 0.5},
            "Xalq ijodiyoti tarixi": {"4": 1, "5": 1},
            "Xorij va o‘zbek musiqa adabiyoti": {"2": 1, "3": 1},
        }
    },

    "Fortepiano ijrochiligi": {
        "years": 7,
        "subjects": {
            "Akkompanement": {"5": 1, "6": 1, "7": 1},
            "Ansambl": {"3": 0.5, "4": 0.5, "5": 0.5, "6": 0.5, "7": 0.5},
            "Jamoa ijrochiligi": {"1": 2, "2": 3, "3": 3, "4": 3, "5": 3, "6": 3, "7": 3},
            "Maqom alifbosi": {"3": 1},
            "Mutaxassislik": {"1": 2, "2": 2, "3": 2, "4": 2, "5": 2, "6": 2, "7": 3},
            "Notani varaqdan o‘qish": {"2": 1, "3": 1, "4": 1, "5": 1},
            "O‘zbek musiqa adabiyoti": {"6": 1, "7": 1},
            "Solfedjio": {"1": 1.5, "2": 1.5, "3": 1.5, "4": 1.5, "5": 1.5, "6": 1.5, "7": 2},
            "Tanlangan fan": {"2": 0.5, "3": 0.5, "4": 0.5, "5": 0.5, "6": 0.5, "7": 0.5},
            "Xorij musiqa adabiyoti": {"4": 1, "5": 1},
        }
    },

    "Grafika": {
        "years": 5,
        "subjects": {
            "Ashyolar bilan ishlash": {"1": 1, "2": 1, "3": 1, "4": 1, "5": 1},
            "Chizmatasvir": {"1": 2, "2": 2, "3": 2, "4": 2, "5": 2},
            "Kompozitsiya (amaliy)": {"1": 1, "2": 1, "3": 1, "4": 1, "5": 1},
            "Kompozitsiya (dastgohli)": {"1": 1, "2": 1, "3": 1, "4": 1, "5": 1},
            "Mutaxassislik (grafika)": {"1": 2, "2": 2, "3": 3, "4": 4, "5": 4},
            "Rang tasvir": {"1": 1, "2": 1, "3": 1, "4": 1, "5": 1},
            "Shrift": {"1": 1, "2": 1, "3": 1, "4": 1, "5": 1},
            "Tanlangan fan": {"2": 0.5, "3": 0.5, "4": 0.5, "5": 0.5},
            "Tasviriy va amaliy san’at tarixi": {"2": 1, "3": 1, "4": 1, "5": 1},
        }
    },

    "Klassik raqs ijrochiligi": {
        "years": 5,
        "subjects": {
            "Musiqa savodi va musiqa tinglash": {"2": 1, "3": 1, "4": 1, "5": 1},
            "Mutaxassislik (klassik raqs)": {"1": 2, "2": 2, "3": 3, "4": 4, "5": 4},
            "O‘zbek raqs": {"1": 2, "2": 2, "3": 3, "4": 4, "5": 4},
            "Raqs san’ati tarixi": {"4": 1, "5": 1},
            "Ritmika / parter": {"1": 2, "2": 2, "3": 2, "4": 0.5, "5": 0.5},
            "Tanlangan fan": {"2": 1, "3": 1, "4": 1, "5": 1},
            "Tarixiy-maishiy raqs": {"2": 1, "3": 1},
            "Xalq sahna raqsi": {"2": 1, "3": 1, "4": 1, "5": 1},
            "Zamonaviy raqs": {"4": 1, "5": 1},
        }
    },

    "Kompyuter grafikasi dizayni": {
        "years": 5,
        "subjects": {
            "Chizmatasvir": {"1": 2, "2": 2, "3": 2, "4": 2, "5": 2},
            "Kompozitsiya": {"1": 2, "2": 2, "3": 2, "4": 2, "5": 2},
            "Mutaxassislik (kompyuter grafikasi dizayni)": {"1": 2, "2": 2, "3": 3, "4": 4, "5": 4},
            "Rangtasvir": {"1": 1, "2": 1, "3": 1, "4": 1, "5": 1},
            "Raqamli tasvir asoslari (Digital Drawing)": {"1": 1, "2": 1, "3": 1, "4": 1, "5": 1},
            "Shrift": {"1": 1, "2": 1, "3": 1, "4": 1, "5": 1},
            "Tanlangan fan": {"2": 0.5, "3": 0.5, "4": 0.5, "5": 0.5},
            "Tasviriy va amaliy san’at tarixi": {"2": 1, "3": 1, "4": 1, "5": 1},
        }
    },

    "Liboslar dizayni": {
        "years": 5,
        "subjects": {
            "Chizmatasvir": {"1": 2, "2": 2, "3": 2, "4": 2, "5": 2},
            "Kompozitsiya": {"1": 2, "2": 2, "3": 2, "4": 2, "5": 2},
            "Modellashtirish va eskiz": {"1": 1, "2": 1, "3": 1, "4": 1, "5": 1},
            "Mutaxassislik (liboslar dizayni)": {"1": 2, "2": 2, "3": 3, "4": 4, "5": 4},
            "Rangtasvir": {"1": 1, "2": 1, "3": 1, "4": 1, "5": 1},
            "Tanlangan fan": {"2": 0.5, "3": 0.5, "4": 0.5, "5": 0.5},
            "Tasviriy va amaliy san’at tarixi": {"2": 1, "3": 1, "4": 1, "5": 1},
            "Tikish texnikasi va bichish": {"1": 1, "2": 1, "3": 1, "4": 1, "5": 1},
        }
    },

    "Qo‘g‘irchoq teatr aktyorligi": {
        "years": 5,
        "subjects": {
            "Grim va sahna liboslari": {"2": 1, "3": 1, "4": 1, "5": 1},
            "Mutaxassislik": {"1": 2, "2": 2, "3": 3, "4": 3, "5": 4},
            "Ritmika va raqs": {"1": 1, "2": 1, "3": 1, "4": 1, "5": 1},
            "Sahna harakati": {"1": 1, "2": 1, "3": 1, "4": 1, "5": 1},
            "Sahna madaniyati": {"1": 1, "2": 1, "3": 1, "4": 1, "5": 1},
            "Sahna nutqi": {"1": 0.5, "2": 1, "3": 1, "4": 1, "5": 1},
            "Tanlangan fan": {"2": 0.5, "3": 0.5, "4": 0.5, "5": 0.5},
            "Teatr san’ati tarixi": {"2": 1, "3": 1, "4": 1, "5": 1},
            "Vokal": {"1": 1, "2": 1, "3": 1, "4": 1, "5": 1},
        }
    },

    "Qo‘g‘irchoq yasash texnologiyasi": {
        "years": 5,
        "subjects": {
            "Ashyolar bilan ishlash": {"1": 1, "2": 1, "3": 1, "4": 1, "5": 1},
            "Chizmatasvir": {"1": 2, "2": 2, "3": 2, "4": 2, "5": 3},
            "Kompozitsiya": {"2": 1, "3": 1, "4": 1, "5": 1},
            "Maketlashtirish": {"2": 1, "3": 1, "4": 1, "5": 1},
            "Mutaxassislik (qo‘g‘irchoq yasash texnologiyasi)": {"1": 2, "2": 2, "3": 2, "4": 3, "5": 3},
            "Qo‘g‘irchoq liboslari bilan ishlash": {"2": 1, "3": 1, "4": 1, "5": 1},
            "Rangtasvir": {"1": 2, "2": 2, "3": 2, "4": 2, "5": 2},
            "Sahna buyumlari yasash": {"2": 1, "3": 1, "4": 1, "5": 1},
            "Tanlangan fan": {"2": 0.5, "3": 0.5, "4": 0.5, "5": 0.5},
        }
    },

    "Teatr va kino aktyorligi": {
        "years": 5,
        "subjects": {
            "Grim va sahna liboslari": {"2": 1, "3": 1, "4": 1, "5": 1},
            "Mutaxassislik": {"1": 2, "2": 2, "3": 3, "4": 3, "5": 4},
            "Ritmika va raqs": {"1": 1, "2": 1, "3": 1, "4": 1, "5": 1},
            "Sahna harakati": {"1": 1, "2": 1, "3": 1, "4": 1, "5": 1},
            "Sahna madaniyati": {"1": 1, "2": 1, "3": 1, "4": 1, "5": 1},
            "Sahna nutqi": {"1": 0.5, "2": 1, "3": 1, "4": 1, "5": 1},
            "Tanlangan fan": {"2": 0.5, "3": 0.5, "4": 0.5, "5": 0.5},
            "Teatr san’ati tarixi": {"2": 1, "3": 1, "4": 1, "5": 1},
            "Vokal": {"1": 1, "2": 1, "3": 1, "4": 1, "5": 1},
        }
    },

    "Torli cholg‘ular ijrochiligi": {
        "years": 7,
        "subjects": {
            "Ansambl": {"3": 0.5, "4": 0.5, "5": 0.5, "6": 0.5, "7": 0.5},
            "Jamoa ijrichiligi (xor, orkestor, cholg‘u ansambli)": {"1": 2, "2": 3, "3": 3, "4": 3, "5": 3, "6": 3, "7": 3},
            "Maqom alifbosi": {"3": 1},
            "Mutaxassislik": {"1": 2, "2": 2, "3": 2, "4": 2, "5": 2, "6": 2, "7": 3},
            "Notani varaqdan o‘qish": {"2": 1, "3": 1, "4": 1, "5": 1},
            "O‘zbek musiqa adabiyoti": {"6": 1, "7": 1},
            "Solfedjio": {"1": 1.5, "2": 1.5, "3": 1.5, "4": 1.5, "5": 1.5, "6": 1.5, "7": 2},
            "Tanlangan fan": {"2": 0.5, "3": 0.5, "4": 0.5, "5": 0.5, "6": 0.5, "7": 0.5},
            "Umumiy fortepiano": {"1": 0.5, "2": 1, "3": 1, "4": 1, "5": 1, "6": 1, "7": 1},
            "Xorij musiqa adabiyoti": {"4": 1, "5": 1},
        }
    },

    "Xalq cholg‘ulari ijrochiligi": {
        "years": 5,
        "subjects": {
            "Ansambl": {"2": 0.5, "3": 0.5, "4": 0.5, "5": 0.5},
            "Jamoa ijrochiligi (xor, orkestor, cholg‘u ansambl turlari)": {"1": 2, "2": 3, "3": 3, "4": 3, "5": 3},
            "Maqom alifbosi": {"1": 1},
            "Mutaxassislik": {"1": 2, "2": 2, "3": 2, "4": 2, "5": 3},
            "Notani varaqdan o‘qish": {"2": 1, "3": 1, "4": 1, "5": 1},
            "O‘zbek musiqa adabiyoti": {"4": 1, "5": 1},
            "Solfedjio": {"1": 1.5, "2": 1.5, "3": 1.5, "4": 1.5, "5": 2},
            "Tanlangan fan": {"2": 0.5, "3": 0.5, "4": 0.5, "5": 0.5},
            "Umumiy fortepiano": {"1": 0.5, "2": 1, "3": 1, "4": 1, "5": 1},
            "Xorij musiqa adabiyoti": {"2": 1, "3": 1},
        }
    },

    "Xalq raqsi ijrochiligi": {
        "years": 5,
        "subjects": {
            "Klassik raqs": {"1": 2, "2": 2, "3": 2, "4": 2, "5": 2},
            "Musiqa savodi va musiqa tinglash": {"2": 1, "3": 1, "4": 1, "5": 1},
            "Mutaxassislik (xalq raqsi ijrochiligi)": {"1": 2, "2": 2, "3": 3, "4": 4, "5": 4},
            "O‘zbek raqs": {"1": 2, "2": 2, "3": 3, "4": 4, "5": 4},
            "Raqs san’ati tarixi": {"4": 1, "5": 1},
            "Ritmika / parter": {"1": 1.5, "2": 1.5, "3": 0.5, "4": 0.5, "5": 0.5},
            "Tanlangan fan": {"2": 1, "3": 1, "4": 1, "5": 1},
            "Zamonaviy raqs": {"4": 1, "5": 1},
        }
    },

    "Xattotlik va miniatyura": {
        "years": 5,
        "subjects": {
            "Ashyolar bilan ishlash": {"1": 1, "2": 1, "3": 1, "4": 1, "5": 1},
            "Chizmatasvir": {"1": 2, "2": 2, "3": 2, "4": 2, "5": 2},
            "Kompozitsiya (dastgohli)": {"1": 1, "2": 1, "3": 1, "4": 1, "5": 1},
            "Kompyuter grafikasi": {"1": 1, "2": 1, "3": 1, "4": 1, "5": 1},
            "Lepka": {"1": 1, "2": 1, "3": 1, "4": 1, "5": 1},
            "Mutaxassislik (xattotlik va miniatyura)": {"1": 2, "2": 2, "3": 3, "4": 4, "5": 4},
            "Rang tasvir": {"1": 1, "2": 1, "3": 1, "4": 1, "5": 1},
            "Tanlangan fan": {"2": 0.5, "3": 0.5, "4": 0.5, "5": 0.5},
            "Tasviriy va amaliy san’at tarixi": {"2": 1, "3": 1, "4": 1, "5": 1},
        }
    },

    "Xaykaltaroshlik": {
        "years": 5,
        "subjects": {
            "Ashyoshunoslik": {"1": 1, "2": 1, "3": 1, "4": 1, "5": 1},
            "Chizmatasvir": {"1": 2, "2": 2, "3": 2, "4": 2, "5": 2},
            "Kompozitsiya (amaliy)": {"1": 1, "2": 1, "3": 1, "4": 1, "5": 1},
            "Kompozitsiya (dastgohli)": {"1": 1, "2": 1, "3": 1, "4": 1, "5": 1},
            "Kompyuter grafikasi": {"1": 1, "2": 1, "3": 1, "4": 1, "5": 1},
            "Mutaxassislik (xaykaltaroshlik)": {"1": 2, "2": 2, "3": 3, "4": 4, "5": 4},
            "Rang tasvir": {"1": 1, "2": 1, "3": 1, "4": 1, "5": 1},
            "Tanlangan fan": {"2": 0.5, "3": 0.5, "4": 0.5, "5": 0.5},
            "Tasviriy va amaliy san’at tarixi": {"2": 1, "3": 1, "4": 1, "5": 1},
        }
    },
}


# Maktabdagi bo'lim -> rejadagi mutaxassislik(lar).
#
# Ko'p bo'limda bitta mutaxassislik bor - u holda
# o'qituvchidan hech narsa so'ralmaydi.

DEPARTMENT_SPECIALTIES = {

    "Fortepiano": [
        "Fortepiano ijrochiligi",
    ],

    "Torli cholg'ular": [
        "Torli cholg‘ular ijrochiligi",
    ],

    "Xalq cholg'u": [
        "Xalq cholg‘ulari ijrochiligi",
    ],

    "An'anaviy cholg'u": [
        "An’anaviy cholg‘ular ijrochiligi",
    ],

    "Damli va zarbli": [
        "Damli va zarbli cholg‘ular ijrochiligi",
    ],

    "Estrada cholg'u": [
        "Estrada cholg‘ulari ijrochiligi – damli va zarbli cholg‘ular, gitara, bas gitara",
        "Estrada cholg‘ulari ijrochiligi – fortepiano, torli cholg‘ular",
    ],

    "Akadem xonandalik": [
        "Akademik xonandalik",
    ],

    "An'anaviy xonandalik": [
        "An’anaviy xonandalik",
    ],

    "Estrada xonandalik": [
        "Estrada xonandaligi",
    ],

    "Folklor": [
        "Askiya san’ati",
        "Baxshichilik ijrochiligi",
        "Folklor ijrochilik san’ati",
    ],

    "Xoreografiya": [
        "Estrada raqs ijrochiligi",
        "Klassik raqs ijrochiligi",
        "Xalq raqsi ijrochiligi",
    ],

    "Tasviriy san'at": [
        "Dastgohli rangtasvir",
        "Grafika",
        "Xattotlik va miniatyura",
        "Xaykaltaroshlik",
    ],

    "Amaliy san'at": [
        "Arxitektura dizayni",
        "Badiiy ganch o‘ymakorligi",
        "Badiiy kashtachilik",
        "Badiiy kulolchilik",
        "Badiiy misgarlik",
        "Badiiy naqqoshlik",
        "Badiiy yog‘och o‘ymakorligi",
        "Badiiy zardo‘zlik",
        "Badiiy zargarlik",
        "Floristika dizayni",
        "Kompyuter grafikasi dizayni",
        "Liboslar dizayni",
        "Qo‘g‘irchoq yasash texnologiyasi",
    ],

    "Teatr san'ati": [
        "Qo‘g‘irchoq teatr aktyorligi",
        "Teatr va kino aktyorligi",
    ],
}


# ==========================
# NAZARIYA BO'LIMI
# ==========================
#
# Nazariya o'qituvchilarining o'z o'quvchisi bo'lmaydi. Ular
# barcha bo'limlarning o'quvchilariga umumiy nazariy fanlarni
# o'tishadi - solfedjio, musiqa adabiyoti va boshqalar.
#
# Shuning uchun ularning fanlar ro'yxati bitta mutaxassislikdan
# emas, quyidagi ro'yxatdan olinadi. Soat esa o'quvchining
# yo'nalishiga qarab farq qilishi mumkin (masalan solfedjio
# 5-sinfda Fortepianoda 1,5 soat, Xalq cholg'usida 2 soat) -
# bunday holda bot ikkala variantni ham ko'rsatadi.
#
# San'at tarixi fanlari bu ro'yxatga kirmaydi: ular o'z
# bo'limlarida (Tasviriy, Xoreografiya, Teatr) o'tiladi.
# ==========================


THEORY_DEPARTMENT = "Nazariya"


THEORY_SUBJECTS = [
    "Solfedjio",
    "Maqom alifbosi",
    "Maqom asoslari",
    "Musiqa savodi va musiqa tinglash",
    "Xorij musiqa adabiyoti",
    "O\u2018zbek musiqa adabiyoti",
    "Xorij va o\u2018zbek musiqa adabiyoti",
    "Estrada tarixi",
    "Xalq ijodiyoti tarixi",
    "Baxshi, jirov va oqinlar san\u2019at tarixi",
]


# ==========================
# QIDIRUV FUNKSIYALARI
# ==========================


def _specialties_for(department):
    """
    Bo'limdagi mutaxassisliklar.

    Nazariya bo'limi hech qaysi bitta mutaxassislikka tegishli
    emas - u barcha yo'nalishlarga dars beradi.
    """

    if department == THEORY_DEPARTMENT:
        return sorted(CURRICULUM)

    return DEPARTMENT_SPECIALTIES.get(department, [])


def department_subjects(department):
    """
    Bo'limdagi barcha fanlar: [(fan, {sinf: soat}), ...]

    Bo'limda bir nechta mutaxassislik bo'lsa, fanlar birlashtiriladi.
    Bir xil fan turli mutaxassislikda turli soat olsa - eng ko'p
    uchraydigani olinadi (aniq qiymat sinf bilan birga topiladi).
    """

    merged = {}

    for specialty in _specialties_for(department):

        for subject, hours in CURRICULUM[specialty]["subjects"].items():

            if department == THEORY_DEPARTMENT and subject not in THEORY_SUBJECTS:
                continue

            target = merged.setdefault(subject, {})

            for class_name, value in hours.items():
                target.setdefault(class_name, []).append(value)

    result = []

    for subject in sorted(merged):

        hours = {
            class_name: sorted(values)[len(values) // 2]
            for class_name, values in merged[subject].items()
        }

        result.append((subject, hours))

    return result


def department_years(department):
    """Bo'limdagi ta'lim muddati (eng uzuni)."""

    years = [
        CURRICULUM[s]["years"]
        for s in _specialties_for(department)
        if s in CURRICULUM
    ]

    return max(years) if years else 7


def planned_hours(department, subject, class_name):
    """
    Reja bo'yicha haftalik soat.

    Bo'limdagi mutaxassisliklar turli qiymat bersa - hammasi
    qaytariladi, o'qituvchi tanlaydi. Reja jim tursa - bo'sh ro'yxat.
    """

    values = []

    for specialty in _specialties_for(department):

        hours = CURRICULUM[specialty]["subjects"].get(subject, {})

        value = hours.get(str(class_name))

        if value is not None and value not in values:
            values.append(value)

    return sorted(values)


def weekly_norm(specialty, class_name):
    """Bitta o'quvchining shu sinfdagi haftalik jami soati."""

    subjects = CURRICULUM.get(specialty, {}).get("subjects", {})

    return sum(
        hours.get(str(class_name), 0) for hours in subjects.values()
    )
