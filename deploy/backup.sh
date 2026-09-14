#!/usr/bin/env bash
# StudentUp backup — exam DB (sqlite, WAL-safe) + state + output + admin key.
# Cron: 15 2 * * *  /opt/studentup/deploy/backup.sh >> /var/log/studentup/backup.log 2>&1
set -euo pipefail

APP_DIR="${APP_DIR:-/opt/studentup}"
DEST="${DEST:-/var/backups/studentup}"
KEEP_DAYS="${KEEP_DAYS:-14}"
STAMP="$(date +%Y%m%d-%H%M)"
mkdir -p "$DEST"

# 1) sqlite ni online-safe backup (WAL tho kuda correct — cp chesthe corrupt avvachu)
if [ -f "$APP_DIR/exam_portal.db" ]; then
  python3 - "$APP_DIR/exam_portal.db" "$DEST/exam_portal-$STAMP.db" <<'PY'
import sqlite3, sys
src, dst = sys.argv[1], sys.argv[2]
with sqlite3.connect(src) as s, sqlite3.connect(dst) as d:
    s.backup(d)
print(f"sqlite backup ok → {dst}")
PY
fi

# 2) config + local state (secrets: chmod 600)
tar -czf "$DEST/studentup-config-$STAMP.tar.gz" -C "$APP_DIR" \
    --ignore-failed-read .env exam_portal_admin_key.txt state.db design_kit.json 2>/dev/null || true
chmod 600 "$DEST"/studentup-config-*.tar.gz "$DEST"/exam_portal-*.db 2>/dev/null || true

# 3) output/ (posts, reports, audit JSON) — pedda unte weekly matrame
if [ "$(date +%u)" = "7" ] && [ -d "$APP_DIR/output" ]; then
  tar -czf "$DEST/studentup-output-$STAMP.tar.gz" -C "$APP_DIR" output || true
fi

# 4) rotation
find "$DEST" -type f -mtime "+$KEEP_DAYS" -delete
echo "[$(date -Is)] backup done → $DEST (kept ${KEEP_DAYS}d)"
echo "Restore: systemctl stop exam-portal && cp $DEST/exam_portal-<stamp>.db $APP_DIR/exam_portal.db && systemctl start exam-portal"
