#!/usr/bin/env bash
# ============================================================================
# STUDENTUP AUTOBLOG — ONE-COMMAND DEPLOY
# Usage (Oracle server lo):  bash deploy.sh
# Idi chesevi: latest code + venv + .env interactive + doctor + dry-run + 24/7 service
# ============================================================================
set -uo pipefail
cd "$(dirname "$0")"

BRANCH="arena/01a07838-automation-charan1"

say() { echo -e "\n==================== $1 ===================="; }

say "1/6 LATEST CODE"
git fetch origin
git checkout "$BRANCH" 2>/dev/null || echo "  (already on branch / checkout note)"
git pull origin "$BRANCH" 2>/dev/null || echo "  (pull skip — local/offline, continue)"

say "2/6 PYTHON + DEPENDENCIES"
if [ ! -d .venv ]; then
    python3 -m venv .venv || { echo "❌ python3-venv install avvali: sudo apt install python3-venv"; exit 1; }
fi
.venv/bin/pip install -q -r requirements.txt && echo "  venv OK"

say "3/6 .ENV SETUP (keys ivvandi — idi server lo ne safe)"
if [ ! -f .env ]; then touch .env; fi

ask() {  # ask <ENV_KEY> <label> <hint>
    if ! grep -q "^$1=" .env 2>/dev/null; then
        read -r -p "  $2${3:+  [$3]}: " val
        echo "$1=$val" >> .env
    else
        echo "  $1 already set ✔"
    fi
}

ask GEMINI_API_KEY       "Gemini API key (aistudio.google.com -> Get API key, FREE)"
ask WP_SITE              "WordPress site URL" "https://studentup.in"
ask WP_USERNAME          "WordPress username" "charanpendota"
ask WP_APP_PASSWORD      "WordPress APPLICATION password (wp-admin > Users > Profile > Application Passwords > Add New)"
ask TELEGRAM_BOT_TOKEN   "Telegram bot token" "@BotFather ichhina token"
ask TELEGRAM_CHAT_ID     "Telegram chat ID" "123456789 (telegram bot start chesina chat id)"

# optional revenue defaults (water lo levu ante ignore)
grep -q "^AD_SHORTCODE="        .env || echo "AD_SHORTCODE=[adinsert block=1]" >> .env
grep -q "^TELEGRAM_CHANNEL_URL=" .env || echo "TELEGRAM_CHANNEL_URL=" >> .env
grep -q "^MAX_AD_SLOTS="        .env || echo "MAX_AD_SLOTS=3" >> .env
echo "  .env ready (tariku marali ante: nano .env)"

say "4/6 HEALTH CHECK (doctor)"
if ! .venv/bin/python run.py --doctor; then
    echo "❌ doctor FAIL — paina errors chudu, .env correct chesi malli: bash deploy.sh"
    exit 1
fi

say "5/6 TEST ARTICLE (dry-run — publish avvadu)"
read -r -p "  Test article generate cheyala? (y/n): " yn
if [ "${yn:-n}" = "y" ] || [ "${yn:-n}" = "Y" ]; then
    .venv/bin/python run.py --dry-run --force || true
fi

say "6/6 24/7 SERVICE START"
read -r -p "  Bot ni 24/7 service ga install + start cheyala? (y/n): " yn2
if [ "${yn2:-n}" = "y" ] || [ "${yn2:-n}" = "Y" ]; then
    bash setup_oracle.sh
    systemctl --user status autoblog --no-pager 2>/dev/null | head -5 || true
fi

say "DEPLOY COMPLETE 🚀"
echo "  Live logs:   journalctl --user -u autoblog -f"
echo "  Status:      .venv/bin/python run.py --status"
echo "  Health:      .venv/bin/python run.py --doctor"
echo "  Manual post: .venv/bin/python run.py --force"
