#!/usr/bin/env bash
# StudentUp backup — bot state DBs (sqlite, WAL-safe) + config + output.
# Cron: 15 2 * * *  /opt/studentup/deploy/backup.sh >> /var/log/studentup/backup.log 2>&1
set -euo pipefail

APP_DIR="${APP_DIR:-/opt/studentup}"
DEST="${DEST:-/var/backups/studentup}"
KEEP_DAYS="${KEEP_DAYS:-14}"
STAMP="$(date +%Y%m%d-%H%M)"
mkdir -p "$DEST"

# 1) sqlite ni online-safe backup (WAL tho kuda correct — cp chesthe corrupt avvachu)
for db in state.db service_center.db; do
  if [ -f "$APP_DIR/$db" ]; then
    python3 - "$APP_DIR/$db" "$DEST/${db%.db}-$STAMP.db" <<'PY'
import sqlite3, sys
src, dst = sys.argv[1], sys.argv[2]
with sqlite3.connect(src) as s, sqlite3.connect(dst) as d:
    s.backup(d)
print(f"sqlite backup ok → {dst}")
PY
  fi
done

# 2) config + design kit (secrets: chmod 600)
tar -czf "$DEST/studentup-config-$STAMP.tar.gz" -C "$APP_DIR" \
    --ignore-failed-read .env state.db design_kit.json 2>/dev/null || true
chmod 600 "$DEST"/studentup-config-*.tar.gz "$DEST"/*.db 2>/dev/null || true

# 3) output/ (posts, reports, audit JSON) — pedda unte weekly matrame
if [ "$(date +%u)" = "7" ] && [ -d "$APP_DIR/output" ]; then
  tar -czf "$DEST/studentup-output-$STAMP.tar.gz" -C "$APP_DIR" output || true
fi

# 4) rotation
find "$DEST" -type f -mtime "+$KEEP_DAYS" -delete
echo "[$(date -Is)] backup done → $DEST (kept ${KEEP_DAYS}d)"
echo "Restore: cp $DEST/state-<stamp>.db $APP_DIR/state.db (bot timer aapi, restore chesi, malli start cheyandi)"
