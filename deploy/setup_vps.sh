#!/usr/bin/env bash
# ==========================
# deploy/setup_vps.sh
# VPS DA BIR MARTALIK O'RNATISH
# ==========================
#
# VPS da root (yoki sudo) bilan ishga tushiring:
#
#   sudo bash deploy/setup_vps.sh
#
# Skript qayta-qayta ishga tushirilsa ham xavfsiz -
# mavjud narsalarni buzmaydi.
#
# ==========================

set -euo pipefail

APP_DIR=/opt/school_bot
APP_USER=botuser
DOMAIN=app.cybermate.uz

echo "==> 1/7  Kerakli paketlar"

apt-get update -qq
apt-get install -y -qq python3 python3-venv python3-pip nginx certbot python3-certbot-nginx


echo "==> 2/7  Foydalanuvchi va papka"

if ! id -u "$APP_USER" >/dev/null 2>&1; then
    useradd -r -m -d "$APP_DIR" -s /usr/sbin/nologin "$APP_USER"
    echo "    $APP_USER yaratildi"
else
    echo "    $APP_USER allaqachon bor"
fi

mkdir -p "$APP_DIR"


echo "==> 3/7  Python muhiti"

if [ ! -d "$APP_DIR/venv" ]; then
    python3 -m venv "$APP_DIR/venv"
fi

"$APP_DIR/venv/bin/pip" install -q --upgrade pip
"$APP_DIR/venv/bin/pip" install -q -r "$APP_DIR/requirements.txt"

echo "    kutubxonalar o'rnatildi"


echo "==> 4/7  Fayl egaligi"

chown -R "$APP_USER:$APP_USER" "$APP_DIR"

# Maxfiy fayllarni faqat botuser o'qiy olsin.
#
# Ilgari ro'yxatda config.py turardi - sozlamalar o'sha faylda
# edi. Endi ular .env da (config.py faqat o'qib oladi), shuning
# uchun himoya .env ga ko'chdi. service_account.json ham shu
# ro'yxatda: u Google kaliti, tokendan kam maxfiy emas.
for f in .env token.json credentials.json service_account.json school.db; do
    [ -f "$APP_DIR/$f" ] && chmod 600 "$APP_DIR/$f" || true
done


echo "==> 5/7  systemd xizmatlari"

# Ikkala birlik ham EnvironmentFile=.env ga tayanadi (webapp
# porti ham shundan olinadi), shuning uchun fayl bo'lmasa
# servis ko'tarilmaydi. Sababini oldindan aytib to'xtaymiz -
# aks holda journalctl da tushunarsiz xato chiqadi.
if [ ! -f "$APP_DIR/.env" ]; then
    echo "XATO: $APP_DIR/.env topilmadi." >&2
    echo "      cp $APP_DIR/.env.example $APP_DIR/.env" >&2
    echo "      so'ng BOT_TOKEN, ADMIN_IDS va WEBAPP_PORT ni to'ldiring." >&2
    exit 1
fi

cp "$APP_DIR/deploy/school-bot.service"    /etc/systemd/system/
cp "$APP_DIR/deploy/school-webapp.service" /etc/systemd/system/

systemctl daemon-reload
systemctl enable school-bot school-webapp
systemctl restart school-bot school-webapp

echo "    school-bot va school-webapp ishga tushdi"


echo "==> 6/7  nginx"

cp "$APP_DIR/deploy/nginx-app.conf" "/etc/nginx/sites-available/$DOMAIN"

ln -sf "/etc/nginx/sites-available/$DOMAIN" "/etc/nginx/sites-enabled/$DOMAIN"

nginx -t
systemctl reload nginx

echo "    nginx sozlandi"


echo "==> 7/7  SSL sertifikat (Let's Encrypt)"

if [ ! -d "/etc/letsencrypt/live/$DOMAIN" ]; then
    certbot --nginx -d "$DOMAIN" --non-interactive --agree-tos --register-unsafely-without-email --redirect
else
    echo "    sertifikat allaqachon bor"
fi


echo
echo "======================================"
echo "✅ Tayyor"
echo
echo "Tekshirish:"
echo "  systemctl status school-bot"
echo "  systemctl status school-webapp"
echo "  curl -I https://$DOMAIN"
echo
echo "Loglar:"
echo "  journalctl -u school-bot -f"
echo "  journalctl -u school-webapp -f"
echo "======================================"
