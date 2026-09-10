-- ==========================
-- 002 - maktab sozlamalari
-- ==========================
--
-- `settings` jadvali ilgari kerak bo'lganda "yo'lda" yaratilardi
-- (db/core.py dagi _ensure_settings_table). Endi maktab nomi va
-- slugi ham shu yerda saqlanadi, ya'ni jadval botning ASOSIY
-- qismiga aylandi - shuning uchun uni migratsiya bilan qat'iy
-- yaratamiz.
--
-- Qiymatlarning o'zi bu yerda urug'lanmaydi: ular har maktabda
-- boshqacha va .env dan keladi (db/school.py -> ensure_school_identity).

CREATE TABLE IF NOT EXISTS settings(
    key   TEXT PRIMARY KEY,
    value TEXT
);
