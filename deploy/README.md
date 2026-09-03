# VPS ga chiqarish

Bot va Mini App **bitta serverda birga** ishlaydi — ularni ajratib
bo'lmaydi, chunki ikkalasi ham bir xil `school.db` bazasi bilan
ishlaydi.

Domen: **app.cybermate.uz**

---

## 1. Lokal kompyuterda: botni to'xtating

Telegram bitta tokenga faqat **bitta** ulanishga ruxsat beradi.
VPS da ishga tushirishdan oldin Windows'dagi botni yoping,
aks holda "409 Conflict" xatosi chiqadi.

---

## 2. Fayllarni VPS ga ko'chirish

Windows'da (PowerShell yoki Git Bash), loyiha papkasidan:

```bash
scp -r config.py database.py main.py state.py requirements.txt \
       data handlers services webapp scripts deploy \
       school.db token.json credentials.json \
       root@SERVER_IP:/opt/school_bot/
```

`uploads/` **kerak emas** — barcha fayllar Google Drive'da.

Muhim: `school.db`, `token.json`, `credentials.json` git'da yo'q
(`.gitignore` da), shuning uchun ular qo'lda ko'chiriladi.

---

## 3. VPS da o'rnatish

```bash
ssh root@SERVER_IP
cd /opt/school_bot
sudo bash deploy/setup_vps.sh
```

Skript quyidagilarni bajaradi:

1. python3, venv, nginx, certbot o'rnatadi
2. `botuser` foydalanuvchisini yaratadi
3. Python kutubxonalarini o'rnatadi
4. Maxfiy fayllarga `chmod 600` qo'yadi
5. `school-bot` va `school-webapp` systemd xizmatlarini yoqadi
6. nginx'ni sozlaydi (faqat app.cybermate.uz uchun alohida blok)
7. Let's Encrypt SSL sertifikatini oladi

---

## 4. Mini App manzilini yoqish

VPS dagi `config.py` da:

```python
WEBAPP_URL = "https://app.cybermate.uz"
```

So'ng botni qayta ishga tushiring:

```bash
sudo systemctl restart school-bot
```

Shundan keyin "📱 Mini App" tugmasi ota-ona, o'qituvchi va
admin menyularida paydo bo'ladi.

---

## Tekshirish

```bash
sudo systemctl status school-bot
sudo systemctl status school-webapp
curl -I https://app.cybermate.uz
```

Loglar:

```bash
sudo journalctl -u school-bot -f
sudo journalctl -u school-webapp -f
```

---

## Keyingi yangilanishlar

Lokal kompyuterdan:

```bash
scp -r handlers services webapp main.py database.py \
       root@SERVER_IP:/opt/school_bot/
```

VPS da:

```bash
sudo systemctl restart school-bot school-webapp
```

---

## Eslatmalar

- **Zaxira**: bot har 6 soatda `school.db` nusxasini Google Drive'ning
  `Maktab arxivi/Zaxira/` papkasiga yuklaydi. Oxirgi 30 nusxa saqlanadi.
- **Token muddati**: OAuth ilova "In production" holatida bo'lsa —
  muddatsiz. "Testing" holatida — 7 kunda eskiradi.
- **SSL yangilanishi**: certbot avtomatik yangilaydi (systemd timer).
- `token.json` va `credentials.json` ni hech qachon git'ga qo'shmang.
