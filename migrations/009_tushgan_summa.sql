-- ==========================
-- 009 - hisobga tushgan summa
-- ==========================
--
-- `payments.amount` - o'qituvchi kvitansiyada ko'rsatgan summa.
-- `received_amount` - buxgalter bank ko'chirmasiga qarab
-- belgilagan, hisobga HAQIQATAN tushgan summa. Ikkisi farq qiladi:
-- bank komissiya ushlaydi, to'lov qisman bo'lishi ham mumkin.
--
-- Ustunning o'zi `db/documents.py` dagi PAYMENT_RECEIPT_COLUMNS
-- ro'yxatiga qo'shilgan va `_add_missing_columns` uni har ishga
-- tushishda tekshiradi - shuning uchun bu yerda ALTER TABLE yo'q
-- (SQLite'da takroriy ADD COLUMN xato beradi, migratsiya esa
-- idempotent bo'lishi shart).

SELECT 1;
