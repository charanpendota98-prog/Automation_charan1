#!/usr/bin/env bash
# Docker container lo bot loop — hourly --run + prathi 5 min --approval-poll.
# (cron-only bot ki systemd timer badulu container-friendly loop.)
set -euo pipefail

cd /app

# approval poll: background lo prathi 5 nimishalaki (Telegram ✅/🗑️ buttons)
(
  while true; do
    sleep 300
    python run.py --approval-poll >> /data/approval.log 2>&1 || true
  done
) &

# main loop: hourly scheduled run
while true; do
  python run.py >> /data/bot.log 2>&1 || true
  sleep 3600
done
