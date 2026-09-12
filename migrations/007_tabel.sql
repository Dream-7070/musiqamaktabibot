-- ==========================
-- 007 - oylik tabel
-- ==========================
--
-- Tabel to'ldirish kun-baku'n emas, ISTISNO bo'yicha ishlaydi.
-- Sababi: 16 xodim x 30 kun = oyiga 480 katakcha, va maktabning
-- haqiqiy faylida ularning deyarli hammasi "+" (2026 varaqlarida
-- 3099 ta "+" bor). Shuning uchun:
--
--   - hamma kun sukut bo'yicha "+" (kelgan) hisoblanadi
--   - dam kunlari alohida jadvalda (yakshanba va bayramlar)
--   - faqat istisnolar (K, M, O, X, Y) yoziladi
--
-- Natijada mudir oyiga 480 emas, 5-10 marta bosadi.

-- Oy holati. `confirmed_at` - mudir dam kunlarini tasdiqlagan
-- vaqt: bot yakshanba va bayramlarni o'zi hisoblab beradi, lekin
-- ko'chma bayramlar (Ramazon, Qurbon hayiti) har yili siljiydi,
-- shuning uchun oxirgi so'z mudirda qoladi.

CREATE TABLE IF NOT EXISTS tabel_month(

    id            INTEGER PRIMARY KEY AUTOINCREMENT,

    year          INTEGER,

    month         INTEGER,

    confirmed_at  TEXT,

    UNIQUE(year, month)

);


-- Dam kunlari. Tasdiqlashda yakshanba va bayramlar shu yerga
-- yoziladi; mudir keyin qo'shimcha kun qo'shishi yoki olib
-- tashlashi mumkin (masalan ish shanbasi).

CREATE TABLE IF NOT EXISTS tabel_rest_days(

    id     INTEGER PRIMARY KEY AUTOINCREMENT,

    year   INTEGER,

    month  INTEGER,

    day    INTEGER,

    UNIQUE(year, month, day)

);


-- Istisnolar. "+" va "D" bu yerda SAQLANMAYDI - ular hisoblanadi.
--
--   K - kasallik varaqasi
--   M - mehnat ta'tili
--   O - o'z hisobidan ta'til
--   X - xizmat safari
--   Y - sababsiz kelmagan

CREATE TABLE IF NOT EXISTS tabel_marks(

    id        INTEGER PRIMARY KEY AUTOINCREMENT,

    staff_id  INTEGER,

    year      INTEGER,

    month     INTEGER,

    day       INTEGER,

    mark      TEXT,

    UNIQUE(staff_id, year, month, day)

);


CREATE INDEX IF NOT EXISTS idx_tabel_marks_oy
ON tabel_marks(year, month);
