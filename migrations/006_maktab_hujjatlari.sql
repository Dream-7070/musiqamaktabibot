-- ==========================
-- 006 - maktabning umumiy hujjatlari
-- ==========================
--
-- Ish rejasi, kadastr, guvohnoma, INN, maktab pasporti, nizom...
-- Bular biror o'qituvchiga yoki o'quvchiga emas, MAKTABNING
-- o'ziga tegishli. Shuning uchun `documents` (o'qituvchi) yoki
-- `student_documents` ga sig'maydi - alohida jadval.
--
-- Kim yuklashi va ko'rishi mumkin: admin, direktor, yordamchi va
-- xo'jalik mudiri. Tekshiruv kod tomonda (handlers), chunki rol
-- `staff` jadvalidan o'qiladi.
--
-- Bitta turda bir nechta fayl bo'lishi mumkin (masalan ish rejasi
-- har yili yangilanadi) - eskisi o'chirilmaydi, tarix qoladi.

CREATE TABLE IF NOT EXISTS school_documents(

    id             INTEGER PRIMARY KEY AUTOINCREMENT,

    document_type  TEXT,

    file_id        TEXT,

    drive_file_id  TEXT,

    drive_link     TEXT,

    file_name      TEXT,

    file_size      INTEGER,

    uploaded_by    INTEGER,

    uploaded_at    TEXT

);


CREATE INDEX IF NOT EXISTS idx_school_docs_type
ON school_documents(document_type);
