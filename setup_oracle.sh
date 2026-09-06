#!/usr/bin/env bash
# =====================================================================
# studentup.in Auto-Blogger — Oracle Cloud (Ubuntu / Oracle Linux) setup
# Ikkada run cheyandi:  bash setup_oracle.sh
# IIDI OKKA COMMAND lo: python, venv, .env, systemd timer antha set avtundi
# =====================================================================
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

echo "==============================================="
echo " studentup.in Auto-Blogger Setup"
echo " Project dir: $PROJECT_DIR"
echo "==============================================="

# ---------- 1) OS detect & system packages ----------
if command -v apt-get >/dev/null 2>&1; then
    echo "[1/6] Ubuntu/Debian detected — installing packages..."
    sudo apt-get update -y
    sudo apt-get install -y python3 python3-venv python3-pip \
        fonts-dejavu-core tzdata curl
elif command -v dnf >/dev/null 2>&1; then
    echo "[1/6] Oracle Linux/RHEL detected — installing packages..."
    sudo dnf install -y python3 python3-pip dejavu-sans-fonts tzdata curl
else
    echo "Unknown OS — python3 + pip manually install cheyandi."
    exit 1
fi

# ---------- 2) Python venv + dependencies ----------
echo "[2/6] Python virtual environment create chesthunnanu..."
if [ ! -d .venv ]; then
    python3 -m venv .venv
fi
.venv/bin/pip install --quiet --upgrade pip
.venv/bin/pip install --quiet -r requirements.txt

# ---------- 3) .env file ----------
echo "[3/6] Configuration (.env)..."
if [ ! -f .env ]; then
    read -rp "WordPress site URL [https://studentup.in]: " WP_SITE
    WP_SITE=${WP_SITE:-https://studentup.in}
    read -rp "WordPress username (admin login name): " WP_USERNAME
    read -rp "WordPress Application Password: " WP_APP_PASSWORD
    read -rp "Gemini API key (aistudio.google.com): " GEMINI_API_KEY
    read -rp "Telegram bot token (@BotFather /newbot — Enter to skip): " TELEGRAM_BOT_TOKEN
    read -rp "WhatsApp CallMeBot URL (optional — Enter to skip): " WHATSAPP_CALLMEBOT_URL

    cat > .env <<EOF
WP_SITE=${WP_SITE}
WP_USERNAME=${WP_USERNAME}
WP_APP_PASSWORD=${WP_APP_PASSWORD}
DEFAULT_POST_STATUS=draft
GEMINI_API_KEY=${GEMINI_API_KEY}
GEMINI_MODEL=gemini-2.5-flash
GEMINI_FALLBACK_MODELS=gemini-2.0-flash,gemini-1.5-flash
DAILY_MIN=10
DAILY_MAX=15
ACTIVE_HOUR_START=6
ACTIVE_HOUR_END=22
TIMEZONE=Asia/Kolkata
IMAGE_ENABLED=1
SITE_BRAND=studentup.in
TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
TELEGRAM_CHAT_ID=
WHATSAPP_CALLMEBOT_URL=${WHATSAPP_CALLMEBOT_URL}
EOF
    chmod 600 .env
    echo "     .env file created."
else
    echo "     .env already untundi — skip."
fi

mkdir -p log output

# ---------- 4) WordPress connection test ----------
echo "[4/6] WordPress connection test..."
if .venv/bin/python run.py --check-wp; then
    echo "     WordPress OK!"
else
    echo "     !! WordPress connect avvaledu — .env values check cheyandi."
    echo "     (Bot schedule automatic ga start avtundi kani posts publish avvavu,"
    echo "      credentials correct cheyi.)"
fi

# ---------- 5) systemd timer (or cron fallback) ----------
RUN_USER="${SUDO_USER:-$(id -un)}"
echo "[5/6] Scheduler install chesthunnanu (user: ${RUN_USER})..."
if command -v systemctl >/dev/null 2>&1 && [ -d /run/systemd/system ]; then
    sudo tee /etc/systemd/system/studentup-autoblog.service >/dev/null <<EOF
[Unit]
Description=studentup.in auto blog poster
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
User=${RUN_USER}
WorkingDirectory=${PROJECT_DIR}
ExecStart=${PROJECT_DIR}/.venv/bin/python ${PROJECT_DIR}/run.py
TimeoutStartSec=600
EOF
    sudo tee /etc/systemd/system/studentup-autoblog.timer >/dev/null <<EOF
[Unit]
Description=Run studentup autoblog every hour

[Timer]
OnCalendar=*-*-* *:00:00
RandomizedDelaySec=600
Persistent=true

[Install]
WantedBy=timers.target
EOF
    sudo systemctl daemon-reload
    sudo systemctl enable --now studentup-autoblog.timer

    # approval bot service (Telegram review buttons) — token untey matrame
    if grep -q "^TELEGRAM_BOT_TOKEN=..*" .env; then
        sudo tee /etc/systemd/system/studentup-approval.service >/dev/null <<EOF
[Unit]
Description=studentup.in Telegram approval bot
After=network-online.target
Wants=network-online.target

[Service]
User=${RUN_USER}
WorkingDirectory=${PROJECT_DIR}
ExecStart=${PROJECT_DIR}/.venv/bin/python -m autoblog.approval_bot
Restart=always
RestartSec=15

[Install]
WantedBy=multi-user.target
EOF
        sudo systemctl daemon-reload
        sudo systemctl enable --now studentup-approval.service
        echo "     systemd timer + Telegram approval bot install ayyayi."
    else
        echo "     systemd timer install ayyindi (Telegram token ledu — approval bot skip)."
    fi
else
    CRON_LINE="0 * * * * cd ${PROJECT_DIR} && ${PROJECT_DIR}/.venv/bin/python run.py >> ${PROJECT_DIR}/log/cron.log 2>&1"
    (crontab -l 2>/dev/null | grep -v "studentup" ; echo "$CRON_LINE") | crontab -
    echo "     cron job install ayyindi — hourly run avtundi."
fi

# ---------- 6) done ----------
echo "[6/6] SETUP COMPLETE! 🎉"
echo ""
if grep -q "^TELEGRAM_BOT_TOKEN=..*" .env 2>/dev/null; then
    echo " IMPORTANT (Telegram approval flow):"
    echo "   1. Phone lo Telegram open cheyandi — mi kotha bot search cheyandi"
    echo "   2. Bot chat loki velli /start ani pampandi"
    echo "      -> Bot automatic ga register aytundi, ippudu prathi draft ki"
    echo "         ✅ Publish / 🗑️ Delete buttons tho message vastundi!"
fi
echo " Useful commands:"
 echo "   Test post immediate ga (draft lo):            .venv/bin/python run.py --force"
 echo "   Offline test (WordPress touch avvakunda):     .venv/bin/python run.py --dry-run --mock"
 echo "   Status chudatam:                              .venv/bin/python run.py --status"
 echo "   Notification test:                            .venv/bin/python run.py --notify-test"
 echo "   Scheduler stop:            sudo systemctl stop studentup-autoblog.timer"
 echo "   Scheduler start:           sudo systemctl start studentup-autoblog.timer"
echo ""
echo " Log file: ${PROJECT_DIR}/log/autoblog.log"
