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
#   MUTAXASSISLIK -> {
#       "years":    ta'lim muddati (5 yoki 7 yil),
#       "subjects": {fan: {sinf: haftalik soat}}
#   }
#
# Har bir satr rejaning "Umumiy soatlar" ustuni bilan
# tekshirilgan: haftalik soatlar yig'indisi x 34 hafta.
# 305 satrdan 303 tasi mos keldi; mos kelmagan 2 tasi
# Askiya san'ati bo'limida - u yerda rejaning o'zida
# qarama-qarshilik bor.
#
# Bu fayl QO'LDA TAHRIRLANMAYDI - reja yangilansa
# scripts/build_curriculum.py qayta yuritiladi.
# ==========================


# bir o'quv yilidagi hafta soni

WEEKS_PER_YEAR = 34


CURRICULUM = {

    "Akademik xonandalik": {
        "years": 5,
        "subjects": {
            "Aktyorlik mahorati": {"2": 0.5, "3": 0.5, "4": 0.5, "5": 0.5},
            "Jamoa ijrochiligi": {"1": 2, "2": 3, "3": 3, "4": 3, "5": 3},
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
            "Maqom alifbosi": {"1": 1},
            "Maqom asoslari": {"2": 1, "3": 1, "4": 1, "5": 1},
            "Mutaxassislik": {"1": 2, "2": 2, "3": 2, "4": 2, "5": 3},
            "Notani varaqdan o‘qish": {"2": 1, "3": 1, "4": 1, "5": 1},
            "Solfedjio": {"1": 1.5, "2": 1.5, "3": 1.5, "4": 1.5, "5": 2},
            "Tanlangan fan": {"2": 0.5, "3": 0.5, "4": 0.5, "5": 0.5},
            "Umumiy fortepiano": {"1": 0.5, "2": 1, "3": 1, "4": 1, "5": 1},
            "Xorij musiqa adabiyoti": {"2": 1, "3": 1},
            "ansambli, folklor ansambli va": {"1": 2, "2": 3, "3": 3, "4": 3, "5": 3},
            "o‘zbek musiqa adabiyoti": {"4": 1, "5": 1},
        }
    },

    "An’anaviy xonandalik": {
        "years": 5,
        "subjects": {
            "Maqom alifbosi": {"1": 1},
            "Maqom asoslari": {"2": 1, "3": 1, "4": 1, "5": 1},
            "Mutaxassislik": {"1": 2, "2": 2, "3": 2, "4": 2, "5": 3},
            "Ovozni yo‘lga qo‘yish": {"1": 1, "2": 1, "3": 1, "4": 1, "5": 1},
            "O‘zbek musiqa adabiyoti": {"4": 1, "5": 1},
            "Solfedjio": {"1": 1.5, "2": 1.5, "3": 1.5, "4": 1.5, "5": 2},
            "Tanlangan fan": {"2": 0.5, "3": 0.5, "4": 0.5, "5": 0.5},
            "Umumiy fortepiano": {"1": 0.5, "2": 1, "3": 1, "4": 1, "5": 1},
            "Xorij musiqa adabiyoti": {"2": 1, "3": 1},
            "ansambli, folklor ansambli va": {"1": 2, "2": 3, "3": 3, "4": 3, "5": 3},
        }
    },

    "Arxitektura dizayni": {
        "years": 5,
        "subjects": {
            "Arxitektura grafikasi va maket": {"1": 1, "2": 1, "3": 1, "4": 1, "5": 1},
            "Chizmatasvir": {"1": 2, "2": 2, "3": 2, "4": 2, "5": 2},
            "Kompozitsiya": {"1": 2, "2": 2, "3": 2, "4": 2, "5": 2},
            "Mutaxassislik (arxitektura": {"1": 2, "2": 2, "3": 3, "4": 4, "5": 4},
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
            "Mutaxassislik": {"1": 2, "2": 2, "3": 2, "4": 2, "5": 3},
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
            "Mutaxassislik (badiiy ganch": {"1": 2, "2": 2, "3": 3, "4": 4, "5": 4},
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
            "Mutaxassislik (badiiy": {"1": 2, "2": 2, "3": 3, "4": 4, "5": 4},
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
            "Mutaxassislik (badiiy": {"1": 2, "2": 2, "3": 3, "4": 4, "5": 4},
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
            "Mutaxassislik (badiiy": {"1": 2, "2": 2, "3": 3, "4": 4, "5": 4},
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
            "Mutaxassislik (badiiy yog‘och": {"1": 2, "2": 2, "3": 3, "4": 4, "5": 4},
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
            "Baxshi, jirov va oqinlar san’at": {"4": 1, "5": 1},
            "Jamoa ijrochiligi": {"1": 1, "2": 2, "3": 2, "4": 2, "5": 2},
            "Maqom alifbosi": {"1": 1},
            "Mutaxassislik a) xonandalik": {"1": 1, "2": 1, "3": 1, "4": 1, "5": 2},
            "Ovozni yo‘lga qo‘yish": {"1": 1, "2": 1, "3": 1, "4": 1, "5": 1},
            "Solfedjio": {"1": 1.5, "2": 1.5, "3": 1.5, "4": 1.5, "5": 2},
            "Tanlangan fan": {"2": 0.5, "3": 0.5, "4": 0.5, "5": 0.5},
            "Umumiy fortepiano": {"1": 0.5, "2": 1, "3": 1, "4": 1, "5": 1},
            "Xorij va o‘zbek musiqa adabiyoti": {"2": 1, "3": 1},
            "va dostonlar ijrochiligi, nutq": {"1": 0.5, "2": 1, "3": 1, "4": 1, "5": 1},
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
            "Mutaxassislik (dastgohli": {"1": 2, "2": 2, "3": 3, "4": 4, "5": 4},
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
            "Xorij va o‘zbek musiqa": {"2": 1, "3": 1},
        }
    },

    "Estrada cholg‘ulari ijrochiligi – fortepiano, torli cholg‘ular": {
        "years": 7,
        "subjects": {
            "Akkompanement": {"5": 1, "6": 1, "7": 1},
            "Ansambl": {"3": 0.5, "4": 0.5, "5": 0.5, "6": 0.5, "7": 0.5},
            "Estrada tarixi": {"6": 1, "7": 1},
            "Jamoa ijrochiligi": {"1": 2, "2": 3, "3": 3, "4": 3, "5": 3, "6": 3, "7": 3},
            "Maqom alifbosi": {"3": 1},
            "Mutaxassislik": {"1": 2, "2": 2, "3": 2, "4": 2, "5": 2, "6": 2, "7": 3},
            "Notani varaqdan o‘qish": {"2": 1, "3": 1, "4": 1, "5": 1},
            "Solfedjio": {"1": 1.5, "2": 1.5, "3": 1.5, "4": 1.5, "5": 1.5, "6": 1.5, "7": 2},
            "Tanlangan fan": {"2": 0.5, "3": 0.5, "4": 0.5, "5": 0.5, "6": 0.5, "7": 0.5},
            "Umumiy fortepiano (torli": {"1": 0.5, "2": 1, "3": 1, "4": 1, "5": 1, "6": 1, "7": 1},
            "Xorij va o‘zbek musiqa": {"4": 1, "5": 1},
        }
    },

    "Estrada raqs ijrochiligi": {
        "years": 5,
        "subjects": {
            "Klassik raqs": {"1": 2, "2": 2, "3": 2, "4": 2, "5": 2},
            "Musiqa savodi va musiqa": {"2": 1, "3": 1, "4": 1, "5": 1},
            "Mutaxassislik (estrada raqs": {"1": 2, "2": 2, "3": 3, "4": 4, "5": 4},
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
            "Jamoa ijrochiligi": {"1": 2, "2": 3, "3": 3, "4": 3, "5": 3},
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
            "Mutaxassislik (floristika": {"1": 2, "2": 2, "3": 3, "4": 4, "5": 4},
            "Rangtasvir": {"1": 1, "2": 1, "3": 1, "4": 1, "5": 1},
            "Tanlangan fan": {"2": 0.5, "3": 0.5, "4": 0.5, "5": 0.5},
            "Tasviriy va amaliy san’at tarixi": {"2": 1, "3": 1, "4": 1, "5": 1},
        }
    },

    "Folklor ijrochilik san’ati": {
        "years": 5,
        "subjects": {
            "Folklor cholg‘ular ijrochiligi": {"4": 1, "5": 1},
            "Jamoa ijrochiligi": {"1": 2, "2": 3, "3": 3, "4": 3, "5": 3},
            "Maqom alifbosi": {"1": 1},
            "Mutaxassislik (xalq qo‘shiqlari": {"1": 2, "2": 2, "3": 2, "4": 2, "5": 3},
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
            "Musiqa savodi va musiqa": {"2": 1, "3": 1, "4": 1, "5": 1},
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
            "Mutaxassislik (kompyuter": {"1": 2, "2": 2, "3": 3, "4": 4, "5": 4},
            "Rangtasvir": {"1": 1, "2": 1, "3": 1, "4": 1, "5": 1},
            "Raqamli tasvir asoslari (Digital": {"1": 1, "2": 1, "3": 1, "4": 1, "5": 1},
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
            "Mutaxassislik (qo‘g‘irchoq": {"1": 2, "2": 2, "3": 2, "4": 3, "5": 3},
            "Qo‘g‘irchoq liboslari bilan": {"2": 1, "3": 1, "4": 1, "5": 1},
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
            "Jamoa ijrichiligi": {"1": 2, "2": 3, "3": 3, "4": 3, "5": 3, "6": 3, "7": 3},
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

    "Xalq raqsi ijrochiligi": {
        "years": 5,
        "subjects": {
            "Klassik raqs": {"1": 2, "2": 2, "3": 2, "4": 2, "5": 2},
            "Musiqa savodi va musiqa": {"2": 1, "3": 1, "4": 1, "5": 1},
            "Mutaxassislik (xalq raqsi": {"1": 2, "2": 2, "3": 3, "4": 4, "5": 4},
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
            "Mutaxassislik (xattotlik va": {"1": 2, "2": 2, "3": 3, "4": 4, "5": 4},
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
