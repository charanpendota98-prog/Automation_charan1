#!/usr/bin/env bash
# StudentUp — one-command VPS install (Ubuntu 22.04/24.04, Debian 12).
#
#   sudo bash deploy/install-vps.sh                    # interactive
#   sudo DOMAIN=exams.college.edu bash deploy/install-vps.sh
#
# Enti chestundi (idempotent — malli run chesina safe):
#   1. python3 + venv + git + caddy install (apt)
#   2. /opt/studentup ki ee repo copy/clone + .venv + deps
#   3. studentup user, log dir, systemd units (exam portal + hourly bot timer)
#   4. Caddy reverse proxy (HTTPS automatic) + firewall hints
#   5. deploy-check run — nijamga ready-a ani proof
#
# Emi cheyyadu: WordPress ni touch cheyyadu; mee secrets ni bayata pampadu.

set -euo pipefail

APP_DIR="${APP_DIR:-/opt/studentup}"
APP_USER="${APP_USER:-studentup}"
DOMAIN="${DOMAIN:-}"
REPO_URL="${REPO_URL:-}"
PORT="${PORT:-8080}"
SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

say()  { printf "\n\033[1;34m▶ %s\033[0m\n" "$*"; }
ok()   { printf "  \033[1;32m✔\033[0m %s\n" "$*"; }
warn() { printf "  \033[1;33m⚠\033[0m %s\n" "$*"; }
die()  { printf "  \033[1;31m✘\033[0m %s\n" "$*" >&2; exit 1; }

[ "$(id -u)" = "0" ] || die "sudo tho run cheyandi: sudo bash deploy/install-vps.sh"

say "1/6 System packages (python3, venv, git, caddy)"
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq python3 python3-venv python3-pip git curl ca-certificates >/dev/null
if ! command -v caddy >/dev/null 2>&1; then
  apt-get install -y -qq debian-keyring debian-archive-keyring apt-transport-https >/dev/null || true
  curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' \
    | gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg 2>/dev/null || warn "Caddy key skip"
  curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' \
    > /etc/apt/sources.list.d/caddy-stable.list 2>/dev/null || warn "Caddy repo skip (system caddy try avutundi)"
  apt-get update -qq && apt-get install -y -qq caddy >/dev/null 2>&1 || warn "Caddy install skip — nginx path vadandi (deploy/nginx-exam.conf)"
fi
ok "packages ready"

say "2/6 App code → $APP_DIR"
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

say "3/6 Python venv + deps"
sudo -u "$APP_USER" python3 -m venv "$APP_DIR/.venv"
sudo -u "$APP_USER" "$APP_DIR/.venv/bin/pip" install -q --upgrade pip
sudo -u "$APP_USER" "$APP_DIR/.venv/bin/pip" install -q -r "$APP_DIR/requirements.txt"
ok "deps installed"

say "4/6 .env + admin key"
if [ ! -f "$APP_DIR/.env" ]; then
  cp "$APP_DIR/.env.example" "$APP_DIR/.env"
  KEY="$(openssl rand -hex 16 2>/dev/null || python3 -c 'import secrets;print(secrets.token_hex(16))')"
  {
    echo ""
    echo "# --- v39 exam portal (install script auto) ---"
    echo "EXAM_PORTAL_ADMIN_KEY=$KEY"
    [ -n "$DOMAIN" ] && echo "EXAM_PUBLIC_URL=https://$DOMAIN"
  } >> "$APP_DIR/.env"
  chown "$APP_USER:$APP_USER" "$APP_DIR/.env"
  chmod 600 "$APP_DIR/.env"
  ok "kotha .env + admin key generate ayyindi (chmod 600)"
else
  ok ".env already undi — touch cheyyaledu"
fi

say "5/6 systemd units + Caddy"
cp "$APP_DIR/deploy/exam-portal.service" /etc/systemd/system/exam-portal.service
cp "$APP_DIR/deploy/studentup-bot.service" /etc/systemd/system/studentup-bot.service
cp "$APP_DIR/deploy/studentup-bot.timer" /etc/systemd/system/studentup-bot.timer
sed -i "s#/opt/studentup#$APP_DIR#g" /etc/systemd/system/exam-portal.service \
        /etc/systemd/system/studentup-bot.service
sed -i "s#User=studentup#User=$APP_USER#g;s#Group=studentup#Group=$APP_USER#g" \
        /etc/systemd/system/exam-portal.service /etc/systemd/system/studentup-bot.service
if [ "$PORT" != "8080" ]; then
  sed -i "s#--exam-port 8080#--exam-port $PORT#" /etc/systemd/system/exam-portal.service
fi
systemctl daemon-reload
systemctl enable --now exam-portal.service
systemctl enable --now studentup-bot.timer
ok "exam-portal active + bot timer enabled"

if command -v caddy >/dev/null 2>&1 && [ -n "$DOMAIN" ]; then
  cp "$APP_DIR/deploy/Caddyfile" /etc/caddy/Caddyfile
  sed -i "s#exams.college.edu#$DOMAIN#g" /etc/caddy/Caddyfile
  sed -i "s#127.0.0.1:8080#127.0.0.1:$PORT#g" /etc/caddy/Caddyfile
  systemctl reload caddy 2>/dev/null || systemctl restart caddy
  ok "Caddy HTTPS → https://$DOMAIN (certificate automatic ga vastundi)"
else
  warn "DOMAIN ivvakapote Caddy configure cheyyaledu → DOMAIN=mee.domain sudo bash $0"
fi

say "6/6 Deploy check (nijamga pani chestunda?)"
cd "$APP_DIR"
sudo -u "$APP_USER" "$APP_DIR/.venv/bin/python" run.py --deploy-check --deploy-port "$PORT" || true

cat <<EOT

────────────────────────────────────────────────────────────
✅ Install done. Next steps:
   1. Admin key chudandi:      sudo cat $APP_DIR/exam_portal_admin_key.txt   (leda .env lo EXAM_PORTAL_ADMIN_KEY)
   2. Portal open cheyandi:    http(s)://$DOMAIN/admin   (leda http://SERVER-IP:$PORT — firewall tho)
   3. WordPress bot:           sudo systemctl start studentup-bot    # manual test
                               sudo journalctl -u studentup-bot -n 50
   4. Backups (cron):          sudo crontab -e →  15 2 * * * $APP_DIR/deploy/backup.sh >> /var/log/studentup/backup.log 2>&1
   5. Update (kotha version):  cd $APP_DIR && sudo -u $APP_USER git pull && sudo systemctl restart exam-portal
   6. Firewall:                sudo ufw allow 80,443/tcp  (8080 ni bayata open cheyyakandi!)

⚠️  Admin key ni evariki share cheyyakandi. Student link + per-exam manage link matrame pampandi.
EOT
