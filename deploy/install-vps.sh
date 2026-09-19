#!/usr/bin/env bash
# StudentUp — one-command VPS install (Ubuntu 22.04/24.04, Debian 12).
#
#   sudo bash deploy/install-vps.sh                    # interactive
#   sudo DOMAIN=studentup.in bash deploy/install-vps.sh
#
# Enti chestundi (idempotent — malli run chesina safe):
#   1. python3 + venv + git install (apt)
#   2. /opt/studentup ki ee repo copy/clone + .venv + deps
#   3. studentup user, log dir, systemd units (hourly bot timer + watchdog timer)
#   4. deploy-check run — nijamga ready-a ani proof
#
# v74: portal ledu → bot cron/timer-only; website = WordPress (vere host)
# leda Caddy static (deploy/Caddyfile) — ee script bot matrame setup chestundi.
# Emi cheyyadu: WordPress ni touch cheyyadu; mee secrets ni bayata pampadu.

set -euo pipefail

APP_DIR="${APP_DIR:-/opt/studentup}"
APP_USER="${APP_USER:-studentup}"
DOMAIN="${DOMAIN:-}"
REPO_URL="${REPO_URL:-}"
SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

say()  { printf "\n\033[1;34m▶ %s\033[0m\n" "$*"; }
ok()   { printf "  \033[1;32m✔\033[0m %s\n" "$*"; }
warn() { printf "  \033[1;33m⚠\033[0m %s\n" "$*" ; }
die()  { printf "  \033[1;31m✘\033[0m %s\n" "$*" >&2; exit 1; }

[ "$(id -u)" = "0" ] || die "sudo tho run cheyandi: sudo bash deploy/install-vps.sh"

say "1/5 System packages (python3, venv, git)"
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq python3 python3-venv python3-pip git curl ca-certificates >/dev/null
ok "packages ready"

say "2/5 App code → $APP_DIR"
mkdir -p "$APP_DIR" /var/log/studentup /var/backups/studentup
if [ ! -d "$APP_DIR/.git" ] && [ -n "$REPO_URL" ]; then
  git clone --depth 1 "$REPO_URL" "$APP_DIR"
else
  # ee script repo lo nunchi run ayindi → current code copy chesam (rsync ledu ante cp)
  if command -v rsync >/dev/null 2>&1; then
    rsync -a --exclude '.git' --exclude '.venv' --exclude '__pycache__' \
          --exclude 'output' --exclude '*.db*' "$SRC_DIR/" "$APP_DIR/"
  else
    (cd "$SRC_DIR" && tar --exclude='.git' --exclude='.venv' --exclude='__pycache__' \
        --exclude='output' -cf - .) | (cd "$APP_DIR" && tar -xf -)
  fi
fi
id -u "$APP_USER" >/dev/null 2>&1 || useradd --system --create-home --shell /bin/bash "$APP_USER"
chown -R "$APP_USER:$APP_USER" "$APP_DIR" /var/log/studentup /var/backups/studentup
ok "code + user ($APP_USER) ready"

say "3/5 Python venv + deps"
sudo -u "$APP_USER" python3 -m venv "$APP_DIR/.venv"
sudo -u "$APP_USER" "$APP_DIR/.venv/bin/pip" install -q --upgrade pip
sudo -u "$APP_USER" "$APP_DIR/.venv/bin/pip" install -q -r "$APP_DIR/requirements.txt"
ok "deps installed"

say "4/5 .env"
if [ ! -f "$APP_DIR/.env" ]; then
  cp "$APP_DIR/.env.example" "$APP_DIR/.env"
  chown "$APP_USER:$APP_USER" "$APP_DIR/.env"
  chmod 600 "$APP_DIR/.env"
  ok "kotha .env create ayyindi (chmod 600) — WP_URL/WP_APP_PASSWORD/GEMINI key pettandi"
else
  ok ".env already undi — touch cheyyaledu"
fi

say "5/5 systemd units (bot timer + watchdog timer)"
cp "$APP_DIR/deploy/studentup-bot.service" /etc/systemd/system/studentup-bot.service
cp "$APP_DIR/deploy/studentup-bot.timer" /etc/systemd/system/studentup-bot.timer
cp "$APP_DIR/deploy/systemd/su-watchdog.service" /etc/systemd/system/su-watchdog.service
cp "$APP_DIR/deploy/systemd/su-watchdog.timer" /etc/systemd/system/su-watchdog.timer
sed -i "s#/opt/studentup#$APP_DIR#g" /etc/systemd/system/studentup-bot.service \
        /etc/systemd/system/su-watchdog.service
sed -i "s#User=studentup#User=$APP_USER#g;s#Group=studentup#Group=$APP_USER#g" \
        /etc/systemd/system/studentup-bot.service
if [ -n "$DOMAIN" ]; then
  sed -i "s#^Environment=SITE_URL=.*#Environment=SITE_URL=https://$DOMAIN/#" \
        /etc/systemd/system/su-watchdog.service
  grep -q "^Environment=DOMAIN=" /etc/systemd/system/su-watchdog.service \
    || echo "Environment=DOMAIN=$DOMAIN" >> /etc/systemd/system/su-watchdog.service
fi
systemctl daemon-reload
systemctl enable --now studentup-bot.timer
systemctl enable --now su-watchdog.timer
ok "bot timer + watchdog timer enabled"

say "Deploy check (nijamga pani chestunda?)"
cd "$APP_DIR"
sudo -u "$APP_USER" "$APP_DIR/.venv/bin/python" run.py --deploy-check || true

cat <<EOT

────────────────────────────────────────────────────────────
✅ Install done. Next steps:
   1. Bot secrets:            sudo -u $APP_USER nano $APP_DIR/.env   (WP_URL, WP_USERNAME,
                               WP_APP_PASSWORD, GEMINI_API_KEY, TELEGRAM_BOT_TOKEN)
   2. Manual test:             sudo systemctl start studentup-bot
                               sudo journalctl -u studentup-bot -n 50
   3. Approvals (Telegram ✅/🗑️): VPS daemon leda cron */5 → run.py --approval-poll
   4. Backups (cron):          sudo crontab -e →  15 2 * * * $APP_DIR/deploy/backup.sh >> /var/log/studentup/backup.log 2>&1
   5. Update (kotha version):  cd $APP_DIR && sudo -u $APP_USER git pull
   6. Static site (optional):  deploy/Caddyfile → /etc/caddy/Caddyfile (DOMAIN marchandi)

⚠️  .env ni evariki share cheyyakandi (App Password + API keys untayi).
EOT
