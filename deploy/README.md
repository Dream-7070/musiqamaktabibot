# VPS ga chiqarish

## 1. Kerakli fayllarni ko'chirish

VPS ga quyidagilarni yuboring (`uploads/` KERAK EMAS - fayllar Drive'da):

```
config.py
database.py
main.py
state.py
requirements.txt
data/
handlers/
keyboards/
states/
services/
scripts/
school.db
token.json
credentials.json
deploy/
```

`scp` bilan (Windows'dan):

```bash
scp -r config.py database.py main.py state.py requirements.txt data handlers keyboards states services school.db token.json credentials.json user@VPS_IP:/opt/school_bot/
```

## 2. VPS da o'rnatish

```bash
sudo useradd -r -m -d /opt/school_bot -s /usr/sbin/nologin botuser
sudo chown -R botuser:botuser /opt/school_bot

cd /opt/school_bot
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
```

## 3. systemd bilan ishga tushirish

```bash
sudo cp deploy/school-bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now school-bot
```

Holatni tekshirish:

```bash
sudo systemctl status school-bot
sudo journalctl -u school-bot -f
```

## 4. Yangilash (kod o'zgarganda)

```bash
# lokal kompyuterdan
scp -r handlers services main.py database.py user@VPS_IP:/opt/school_bot/

# VPS da
sudo systemctl restart school-bot
```

## Eslatma

- `token.json` ni hech qachon git'ga qo'shmang (`.gitignore` da allaqachon bor).
- Token muddati: agar OAuth ilova "In production" holatida bo'lsa - muddatsiz.
  "Testing" holatida bo'lsa - 7 kunda eskiradi, shunda `scripts/get_token.py`
  ni qayta ishga tushirib, yangi `token.json` ni VPS ga ko'chiring.
- Bazani qo'lda zaxiralash: `python scripts/migrate_to_drive.py` faqat yangi
  fayllar uchun; `services/backup.py` esa `school.db` ni avtomatik zaxiralaydi.
