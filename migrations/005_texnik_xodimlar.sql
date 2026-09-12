-- ==========================
-- 005 - texnik xodimlar va ularning hujjatlari
-- ==========================
--
-- Maktabda o'qituvchilardan tashqari texnik xodimlar bor: farrosh,
-- qorovul, elektrik, duradgor, santexnik... Ular xo'jalik mudiri
-- (ХИБДЎ - xo'jalik ishlari bo'yicha direktor o'rinbosari) qo'l
-- ostida ishlaydi va oylik tabel shular bo'yicha to'ldiriladi.
--
-- MUHIM: texnik xodim botdan FOYDALANMAYDI. Uning yozuvini va
-- hujjatlarini mudir yuritadi - xuddi o'qituvchi o'quvchining
-- hujjatlarini yuritganidek. Shuning uchun ular `staff` jadvaliga
-- yozilmaydi: u yerda bot foydalanuvchilari turadi (telegram_id
-- bilan), bu esa butunlay boshqa narsa.

-- Lavozimlar. Mudir yangisini qo'sha oladi, shuning uchun kodda
-- emas - bazada. `tungi_navbat` - qorovullarga oyiga qo'shiladigan
-- belgilangan summa (tabelda alohida qator bo'lib turadi).

CREATE TABLE IF NOT EXISTS tech_positions(

    id            INTEGER PRIMARY KEY AUTOINCREMENT,

    name          TEXT UNIQUE,

    tungi_navbat  INTEGER DEFAULT 0,

    created_at    TEXT DEFAULT (datetime('now','localtime'))

);


-- Xodimning o'zi. `tabel_raqami` va `stavka` tabeldan keladi:
-- 2026 varaqlarida har xodimning tabel raqami (15, 68, 5...) va
-- stavka miqdori (5178562) alohida ustunda turadi.

CREATE TABLE IF NOT EXISTS tech_staff(

    id            INTEGER PRIMARY KEY AUTOINCREMENT,

    full_name     TEXT,

    position      TEXT,

    tabel_raqami  TEXT,

    stavka        INTEGER DEFAULT 0,

    status        TEXT DEFAULT 'ishlayapti',

    created_at    TEXT DEFAULT (datetime('now','localtime'))

);


CREATE INDEX IF NOT EXISTS idx_tech_staff_status
ON tech_staff(status);


-- Hujjatlar. Tuzilishi o'qituvchi hujjatlari (`documents`) bilan
-- bir xil - Drive'ga yuklanadi, bazada faqat havola va o'lcham
-- qoladi. Farqi: buni xodimning o'zi emas, mudir yuklaydi.

CREATE TABLE IF NOT EXISTS tech_staff_documents(

    id             INTEGER PRIMARY KEY AUTOINCREMENT,

    staff_id       INTEGER,

    document_type  TEXT,

    file_id        TEXT,

    drive_file_id  TEXT,

    drive_link     TEXT,

    file_name      TEXT,

    file_size      INTEGER,

    uploaded_at    TEXT

);


CREATE INDEX IF NOT EXISTS idx_tech_docs_staff
ON tech_staff_documents(staff_id);


-- Boshlang'ich lavozimlar ro'yxati - tabeldagi 2026 varaqlaridan
-- olindi. Bu faqat urug': mudir keyin o'zi qo'shadi/o'zgartiradi.

INSERT OR IGNORE INTO tech_positions (name) VALUES
    ('Farrosh'),
    ('Qorovul'),
    ('Elektrik'),
    ('Duradgor'),
    ('Santexnik'),
    ('Xovlibon'),
    ('O''t yoquvchi'),
    ('Ovoz operatori'),
    ('Liboschi');
