#!/usr/bin/env bash
# su-watchdog.sh — v51 auto-heal for the StudentUp stack (VPS / Oracle Cloud).
#
# Eni chestundi:
#   1. Portal /healthz + website page ni check chestundi (curl, timeout tho)
#   2. 3 consecutive failures ayyaka service ni restart chestundi (systemd)
#   3. Disk / memory / TLS certificate expiry check (+ alerts)
#   4. Telegram alert (throttled — 30 min lo okkate, spam ledu)
#   5. State file tho crash history maintain chestundi (diagnosis kosam)
#
# Install (systemd timer 2 min ki okasari; deploy/systemd/su-watchdog.timer):
#   sudo cp deploy/su-watchdog.sh /opt/studentup/deploy/ && sudo chmod +x ...
#   sudo cp deploy/systemd/su-watchdog.{service,timer} /etc/systemd/system/
#   sudo systemctl daemon-reload && sudo systemctl enable --now su-watchdog.timer
#
# Manual run / test:
#   sudo WATCHDOG_DRY=1 bash deploy/su-watchdog.sh     # nothing is restarted
#
set -uo pipefail

APP_DIR="${APP_DIR:-/opt/studentup}"
STATE_DIR="${STATE_DIR:-/var/lib/studentup}"
LOG_FILE="${LOG_FILE:-/var/log/studentup/watchdog.log}"
PORTAL_URL="${PORTAL_URL:-http://127.0.0.1:8080/healthz}"
SITE_URL="${SITE_URL:-}"
SERVICES="${SERVICES:-exam-portal}"
FAIL_THRESHOLD="${FAIL_THRESHOLD:-3}"
ALERT_THROTTLE="${ALERT_THROTTLE:-1800}"     # seconds between identical alerts
DISK_MIN_MB="${DISK_MIN_MB:-512}"
MEM_MIN_MB="${MEM_MIN_MB:-96}"
CERT_WARN_DAYS="${CERT_WARN_DAYS:-14}"
DRY="${WATCHDOG_DRY:-0}"

mkdir -p "$STATE_DIR" "$(dirname "$LOG_FILE")" 2>/dev/null || true
STATE_FILE="$STATE_DIR/watchdog.state"

# .env nunchi Telegram details (unna)
if [ -z "${TELEGRAM_BOT_TOKEN:-}" ] && [ -f "$APP_DIR/.env" ]; then
  TELEGRAM_BOT_TOKEN="$(grep -E '^TELEGRAM_BOT_TOKEN=' "$APP_DIR/.env" 2>/dev/null | head -1 | cut -d= -f2- | tr -d '"'"'"' ' || true)"
  TELEGRAM_CHAT_ID="$(grep -E '^TELEGRAM_CHAT_ID=' "$APP_DIR/.env" 2>/dev/null | head -1 | cut -d= -f2- | tr -d '"'"'"' ' || true)"
fi
TELEGRAM_BOT_TOKEN="${TELEGRAM_BOT_TOKEN:-}"
TELEGRAM_CHAT_ID="${TELEGRAM_CHAT_ID:-}"

log() { printf '%s %s\n' "$(date '+%F %T')" "$*" | tee -a "$LOG_FILE" >/dev/null; echo "$(date '+%F %T') $*"; }

state_get() { [ -f "$STATE_FILE" ] && grep -E "^$1=" "$STATE_FILE" 2>/dev/null | tail -1 | cut -d= -f2- || true; }
state_set() {
  touch "$STATE_FILE" 2>/dev/null || true
  if grep -qE "^$1=" "$STATE_FILE" 2>/dev/null; then
    sed -i "s|^$1=.*|$1=$2|" "$STATE_FILE" 2>/dev/null || true
  else
    printf '%s=%s\n' "$1" "$2" >>"$STATE_FILE" || true
  fi
}

alert() {  # alert <key> <message>  (throttled per key)
  local key="$1" msg="$2" last now
  now="$(date +%s)"
  last="$(state_get "alert_$key")"
  if [ -n "$last" ] && [ $((now - last)) -lt "$ALERT_THROTTLE" ]; then
    log "ALERT (throttled) $key: $msg"
    return 0
  fi
  state_set "alert_$key" "$now"
  log "ALERT $key: $msg"
  if [ -n "$TELEGRAM_BOT_TOKEN" ] && [ -n "$TELEGRAM_CHAT_ID" ]; then
    curl -fsS --max-time 10 -X POST \
      "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
      -d "chat_id=${TELEGRAM_CHAT_ID}" \
      --data-urlencode "text=🛠 StudentUp watchdog: $msg" >/dev/null 2>&1 \
      && log "telegram alert sent ($key)" || log "telegram alert FAILED ($key)"
  else
    log "telegram not configured — alert only in log"
  fi
}

check_url() { # check_url <url> → 0 ok, 1 fail
  curl -fsS --max-time 8 -o /dev/null "$1" 2>/dev/null
}

restart_service() { # restart_service <name>
  if [ "$DRY" = "1" ]; then
    log "DRY-RUN: would restart $1"
    return 0
  fi
  if command -v systemctl >/dev/null 2>&1; then
    systemctl restart "$1" 2>/dev/null && log "restarted $1" || log "restart FAILED for $1"
  else
    log "systemctl ledu — restart skip ($1)"
  fi
}

fail_file="$STATE_DIR/watchdog.fails"

# ---------------------------------------------------------------- 1) portal
if check_url "$PORTAL_URL"; then
  if [ "$(cat "$fail_file" 2>/dev/null || echo 0)" != "0" ]; then
    log "portal healthy again ($PORTAL_URL)"
  fi
  echo 0 >"$fail_file" 2>/dev/null || true
else
  fails=$(( $(cat "$fail_file" 2>/dev/null || echo 0) + 1 ))
  echo "$fails" >"$fail_file" 2>/dev/null || true
  log "portal check FAILED ($fails/$FAIL_THRESHOLD) — $PORTAL_URL"
  if [ "$fails" -ge "$FAIL_THRESHOLD" ]; then
    alert portal_down "portal $FAIL_THRESHOLD checks fail — auto-restarting ($PORTAL_URL)"
    for svc in $SERVICES; do restart_service "$svc"; done
    echo 0 >"$fail_file" 2>/dev/null || true
    sleep 5
    if check_url "$PORTAL_URL"; then
      log "portal recovered after restart ✔"
      alert portal_recovered "portal restarted and healthy again ✔"
    else
      alert portal_still_down "portal STILL down after restart — manual check kavali"
    fi
  fi
fi

# ---------------------------------------------------------------- 2) website
if [ -n "$SITE_URL" ]; then
  if ! check_url "$SITE_URL"; then
    alert site_down "website page fail: $SITE_URL"
  fi
fi

# ------------------------------------------------------------- 3) resources
avail_mb=$(df -Pm / 2>/dev/null | awk 'NR==2{print $4}')
if [ -n "${avail_mb:-}" ] && [ "$avail_mb" -lt "$DISK_MIN_MB" ]; then
  alert disk_low "disk space low: ${avail_mb} MB left (limit ${DISK_MIN_MB} MB) — tools/prune_media.py run cheyandi"
fi
if [ -r /proc/meminfo ]; then
  free_mb=$(awk '/MemAvailable/{printf "%d", $2/1024}' /proc/meminfo 2>/dev/null || echo "")
  if [ -n "${free_mb:-}" ] && [ "$free_mb" -lt "$MEM_MIN_MB" ]; then
    alert mem_low "memory low: ${free_mb} MB available (limit ${MEM_MIN_MB} MB)"
  fi
fi
load=$(awk '{print int($1)}' /proc/loadavg 2>/dev/null || echo 0)
cpus=$(nproc 2>/dev/null || echo 1)
if [ "${load:-0}" -gt $((cpus * 4)) ]; then
  alert load_high "load ${load} on ${cpus} CPU — slow/queue chances"
fi

# ------------------------------------------------------------------ 4) TLS
DOMAIN="${DOMAIN:-}"
if [ -n "$DOMAIN" ] && command -v openssl >/dev/null 2>&1; then
  end=$(echo | timeout 8 openssl s_client -servername "$DOMAIN" -connect "$DOMAIN:443" 2>/dev/null \
        | openssl x509 -noout -enddate 2>/dev/null | cut -d= -f2)
  if [ -n "$end" ]; then
    days=$(( ( $(date -d "$end" +%s 2>/dev/null || echo 0) - $(date +%s) ) / 86400 ))
    if [ "$days" -lt "$CERT_WARN_DAYS" ]; then
      alert cert_expiry "TLS certificate for $DOMAIN expires in ${days} days"
    fi
  fi
fi

log "watchdog run complete (dry=$DRY)"
exit 0    # eppudu 0 — timer ni fail cheyyakudadu
