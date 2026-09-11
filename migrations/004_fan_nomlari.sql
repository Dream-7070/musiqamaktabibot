-- ==========================
-- 004 - Excel'dagi fan nomlari
-- ==========================
--
-- O'qituvchi jadvalni Excel'da tuzadi va fan nomini o'z bilganicha
-- yozadi: "N.V.O", "Kom.A.", ba'zan xato bilan "Jo'rnavoz;il".
--
-- services/schedule_import.py aksariyatini o'zi tanidi, lekin
-- tanimaganini TAXMIN QILIB QO'YMAYDI - o'qituvchidan so'raydi.
-- Javob shu yerga yoziladi va keyingi safar so'ralmaydi.
--
-- Lug'at butun maktab uchun umumiy: bitta o'qituvchi tushuntirsa,
-- boshqasining faylida ham ishlaydi. Shuning uchun `alias` -
-- birlamchi kalit va `teacher` faqat kim qo'shganini eslatadi.
--
-- `alias` normallashtirilgan holda saqlanadi (kichik harf, bir xil
-- apostrof, nuqtasiz) - normalize() nima qaytarsa, o'sha.

CREATE TABLE IF NOT EXISTS subject_aliases(

    alias      TEXT PRIMARY KEY,

    subject    TEXT NOT NULL,

    teacher    TEXT,

    created_at TEXT DEFAULT (datetime('now','localtime'))
);
