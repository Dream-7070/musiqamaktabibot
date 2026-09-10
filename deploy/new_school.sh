#!/usr/bin/env bash
# ==========================
# new_school.sh - YANGI MAKTAB QO'SHISH
# ==========================
#
#   ./new_school.sh <slug> "<Maktab to'liq nomi>" <BOT_TOKEN> <ADMIN_IDS>
#
# Misol:
#   ./new_school.sh 5mmm "5-son bolalar musiqa maktabi" 123:ABC 566206701,111
#
# Nima qiladi: kodni ko'chiradi, venv quradi, .env yozadi,
# port ajratadi, nginx jadvaliga qo'shadi va servislarni
# ishga tushiradi. Sxema migratsiyalari bot ishga tushganda
# o'zi qo'llanadi (db/migrations.py).
# ==========================

set -euo pipefail


CODE_DIR="/opt/school_bot"
SCHOOLS_DIR="/opt/schools"
PORTS_MAP="/etc/nginx/school-ports.map"
BASE_DOMAIN="cybermate.uz"
RUN_USER="botuser"
FIRST_PORT=8000


xato() {
    echo "XATO: $*" >&2
    exit 1
}


if [ "$#" -ne 4 ]; then
    echo "Foydalanish: $0 <slug> \"<Maktab to'liq nomi>\" <BOT_TOKEN> <ADMIN_IDS>"
    echo "Misol:       $0 5mmm \"5-son bolalar musiqa maktabi\" 123:ABC 566206701,111"
    exit 1
fi

SLUG="$1"
SCHOOL_NAME="$2"
BOT_TOKEN="$3"
ADMIN_IDS="$4"


# ==========================
# TEKSHIRUVLAR
# ==========================

[ "$(id -u)" -eq 0 ] || xato "skript root (sudo) bilan ishga tushirilishi kerak."

[[ "$SLUG" =~ ^[a-z0-9][a-z0-9_-]*$ ]] \
    || xato "slug noto'g'ri: '$SLUG'. Faqat kichik lotin harflari, raqam, - va _."

[[ "$BOT_TOKEN" =~ ^[0-9]+:[A-Za-z0-9_-]+$ ]] \
    || xato "BOT_TOKEN formati noto'g'ri. Namuna: 123456789:AA..."

[[ "$ADMIN_IDS" =~ ^[0-9]+(,[0-9]+)*$ ]] \
    || xato "ADMIN_IDS faqat vergul bilan ajratilgan raqamlar bo'lishi kerak."

[ -n "$SCHOOL_NAME" ] || xato "maktab nomi bo'sh."

TARGET_DIR="$SCHOOLS_DIR/$SLUG"
DOMAIN="${SLUG}.${BASE_DOMAIN}"

[ ! -e "$TARGET_DIR" ] || xato "$TARGET_DIR allaqachon mavjud."

[ -d "$CODE_DIR" ] || xato "kod papkasi topilmadi: $CODE_DIR"

[ -f "$CODE_DIR/requirements.txt" ] || xato "$CODE_DIR ichida requirements.txt yo'q."

# chown ishlashi uchun foydalanuvchi bo'lishi shart - aks holda
# skript yarim yo'lda to'xtab, papka egasiz qolardi.
id -u "$RUN_USER" >/dev/null 2>&1 \
    || xato "$RUN_USER foydalanuvchisi yo'q. Avval: useradd -r -s /usr/sbin/nologin $RUN_USER"

# systemd shablonlari o'rnatilganmi
for unit in "school-bot@.service" "school-webapp@.service"; do
    systemctl cat "$unit" >/dev/null 2>&1 \
        || xato "$unit o'rnatilmagan. deploy/ dagi shablonni /etc/systemd/system/ ga ko'chiring."
done

# nuqtalarni ekranlaymiz - aks holda regexda istalgan belgiga mos kelardi
DOMAIN_RE="${DOMAIN//./\\.}"

if [ -f "$PORTS_MAP" ] && grep -qE "^[[:space:]]*${DOMAIN_RE}[[:space:]]" "$PORTS_MAP"; then
    xato "$DOMAIN allaqachon $PORTS_MAP ichida bor."
fi


# ==========================
# 1/7 PORT AJRATISH
# ==========================
#
# Eng katta band port + 1. Undan keyin haqiqatan ham hech kim
# tinglamayotganiga ishonch hosil qilamiz - jadvalda yo'q,
# lekin boshqa dastur egallab turgan port bo'lishi mumkin.

echo "[1/7] port ajratilmoqda..."

[ -f "$PORTS_MAP" ] || : > "$PORTS_MAP"

MAX_PORT=0

while read -r _ port_str _rest; do

    port="${port_str%;}"

    if [[ "$port" =~ ^[0-9]+$ ]] && [ "$port" -gt "$MAX_PORT" ]; then
        MAX_PORT="$port"
    fi

done < "$PORTS_MAP"

if [ "$MAX_PORT" -lt "$FIRST_PORT" ]; then
    NEW_PORT="$FIRST_PORT"
else
    NEW_PORT=$((MAX_PORT + 1))
fi

while ss -ltn 2>/dev/null | grep -q ":${NEW_PORT}[[:space:]]"; do
    NEW_PORT=$((NEW_PORT + 1))
done

echo "      port: $NEW_PORT"


# ==========================
# 2/7 KODNI KO'CHIRISH
# ==========================

echo "[2/7] kod $TARGET_DIR ga ko'chirilmoqda..."

mkdir -p "$SCHOOLS_DIR"

if command -v rsync >/dev/null 2>&1; then

    rsync -a \
        --exclude '.git' \
        --exclude 'venv' \
        --exclude '__pycache__' \
        --exclude '*.db' \
        --exclude '*.db-wal' \
        --exclude '*.db-journal' \
        --exclude '.env' \
        --exclude 'token.json' \
        --exclude 'credentials.json' \
        --exclude 'tests/_tmp' \
        "$CODE_DIR/" "$TARGET_DIR/"

else

    # rsync yo'q - nusxalab, keraksizlarini o'chiramiz.
    # __pycache__ ichma-ich joylashgani uchun find bilan.

    cp -a "$CODE_DIR" "$TARGET_DIR"

    rm -rf "$TARGET_DIR/.git" "$TARGET_DIR/venv" "$TARGET_DIR/tests/_tmp"
    rm -f  "$TARGET_DIR/.env" "$TARGET_DIR/token.json" "$TARGET_DIR/credentials.json"
    rm -f  "$TARGET_DIR"/*.db "$TARGET_DIR"/*.db-wal "$TARGET_DIR"/*.db-journal

    find "$TARGET_DIR" -name '__pycache__' -type d -prune -exec rm -rf {} +
fi


# ==========================
# 3/7 VENV
# ==========================

echo "[3/7] venv o'rnatilmoqda (biroz vaqt oladi)..."

python3 -m venv "$TARGET_DIR/venv"

"$TARGET_DIR/venv/bin/pip" install --upgrade pip -q

"$TARGET_DIR/venv/bin/pip" install -r "$TARGET_DIR/requirements.txt" -q


# ==========================
# 4/7 .env
# ==========================
#
# SCHOOL_NAME ichida bo'sh joy va apostrof bo'lishi mumkin -
# QO'SHTIRNOQSIZ yoziladi. systemd EnvironmentFile ham,
# python-dotenv ham aynan shuni kutadi.

echo "[4/7] .env yozilmoqda..."

cat > "$TARGET_DIR/.env" <<ENVEOF
SCHOOL_SLUG=$SLUG
SCHOOL_NAME=$SCHOOL_NAME
BOT_TOKEN=$BOT_TOKEN
ADMIN_IDS=$ADMIN_IDS
WEBAPP_URL=https://$DOMAIN
WEBAPP_PORT=$NEW_PORT
DB_PATH=school.db
GOOGLE_CREDENTIALS_FILE=credentials.json
GOOGLE_TOKEN_FILE=token.json
DRIVE_ROOT_FOLDER=Maktab arxivi
ENVEOF

chmod 600 "$TARGET_DIR/.env"


# ==========================
# 5/7 EGALIK
# ==========================

echo "[5/7] papka egasi $RUN_USER ga o'tkazilmoqda..."

chown -R "$RUN_USER:$RUN_USER" "$TARGET_DIR"


# ==========================
# 6/7 NGINX
# ==========================
#
# DIQQAT: fayl oxirida yangi qator bo'lmasa, yozuv oldingi
# maktab qatoriga YOPISHIB ketadi. Keyin xatolikda oxirgi
# qatorni o'chirish BOSHQA maktabni ham yo'q qilardi.
# Shuning uchun avval yangi qatorni kafolatlaymiz va
# to'liq zaxira nusxadan qaytaramiz.

echo "[6/7] nginx jadvaliga qo'shilmoqda..."

if [ -s "$PORTS_MAP" ] && [ -n "$(tail -c 1 "$PORTS_MAP")" ]; then
    printf '\n' >> "$PORTS_MAP"
fi

MAP_BACKUP="$(mktemp)"
cp "$PORTS_MAP" "$MAP_BACKUP"

printf '%s %s;\n' "$DOMAIN" "$NEW_PORT" >> "$PORTS_MAP"

if ! nginx -t >/dev/null 2>&1; then

    cp "$MAP_BACKUP" "$PORTS_MAP"
    rm -f "$MAP_BACKUP"

    echo "nginx -t xatosi:" >&2
    nginx -t >&2 || true

    xato "nginx sozlamasi qabul qilinmadi, o'zgarish qaytarildi."
fi

rm -f "$MAP_BACKUP"

systemctl reload nginx


# ==========================
# 7/7 SERVISLAR
# ==========================

echo "[7/7] servislar ishga tushirilmoqda..."

systemctl enable --now "school-bot@$SLUG" "school-webapp@$SLUG"

sleep 3

BOT_HOLAT="$(systemctl is-active "school-bot@$SLUG" || true)"
WEB_HOLAT="$(systemctl is-active "school-webapp@$SLUG" || true)"

if [ "$BOT_HOLAT" != "active" ] || [ "$WEB_HOLAT" != "active" ]; then

    echo ""
    echo "OGOHLANTIRISH: servis ko'tarilmadi (bot: $BOT_HOLAT, webapp: $WEB_HOLAT)."
    echo "Sababini ko'ring:"
    echo "    journalctl -u school-bot@$SLUG -n 50 --no-pager"
    echo "    journalctl -u school-webapp@$SLUG -n 50 --no-pager"
fi


# ==========================
# XULOSA
# ==========================

echo ""
echo "=================================================="
echo " MAKTAB QO'SHILDI"
echo "=================================================="
echo " slug   : $SLUG"
echo " nomi   : $SCHOOL_NAME"
echo " domen  : https://$DOMAIN"
echo " port   : $NEW_PORT"
echo " papka  : $TARGET_DIR"
echo "=================================================="
echo ""
echo "QO'LDA BAJARILADIGAN QADAMLAR:"
echo ""
echo " 1. Google Drive: maktabning credentials.json faylini"
echo "    $TARGET_DIR/ ichiga qo'ying, so'ng token.json ni hosil"
echo "    qilish uchun avtorizatsiyadan o'ting va servisni qayta"
echo "    ishga tushiring:"
echo "        systemctl restart school-bot@$SLUG"
echo ""
echo " 2. @BotFather -> /setmenubutton -> Mini App manzili:"
echo "        https://$DOMAIN"
echo ""
echo " 3. Adminlar botga /start yuborib tekshirsin."
echo ""
