# 🚀 DEPLOY — StudentUp bot (honest, step-by-step)

Ee file lo **3 deployment paths** unnayi. Mee situation chusi okati select cheyandi:

| Path | Evariki | Time | Enti deploy avutundi |
|---|---|---|---|
| **A. VPS + systemd timers** (recommended) | Mee own VPS / Oracle Cloud VM (₹300–600/నెల leda free tier) | ~10 min | Hourly bot + watchdog + backups |
| **B. Docker compose** | Docker telisinavallu / kotha VM | ~5 min | Bot loop container (okka command), volume lo data |
| **C. Shared-hosting cron** (MilesWeb) | Server maintenance vaddu anukunevallu | ~15 min | Bot + approvals anni cron tho (details: `DEPLOY_MILESWEB.md`) |

v74 nunchi bot **cron-only** (live-exam server teesesam) — ports/servers levu,
24×7 daemon kuda optional (approvals cron tho vastayi).

**Modata (anni paths ki):** ee command run cheyandi — enti miss undo cheptundi.

```bash
python run.py --deploy-check
```

Output lo `❌ fail` unte adi fix cheyandi; `⚠️ warn` unnavi optional/manual (ex: WP creds).

---

## Path A — VPS (Ubuntu 22.04/24.04) ⭐ recommended

Kolukovalsina server: 1 vCPU / 1 GB RAM chalu (bot + sqlite; hourly runs ki
comfortable). Public website = WordPress (vere host) leda Caddy static (kindha).

```bash
# 1) Server SSH lo (root/sudo)
sudo apt update && sudo apt install -y git
git clone https://github.com/charanpendota98-prog/Automation_charan1.git /opt/studentup-src

# 2) One-command install (python+venv+deps+user+systemd timers+check)
sudo DOMAIN=studentup.in REPO_URL=https://github.com/charanpendota98-prog/Automation_charan1.git \
     bash /opt/studentup-src/deploy/install-vps.sh

# 3) Secrets pettandi + verify
sudo -u studentup nano /opt/studentup/.env     # WP_* / GEMINI_* / TELEGRAM_*
sudo systemctl start studentup-bot             # okka manual test run
sudo journalctl -u studentup-bot -n 80         # result chudandi
sudo systemctl status studentup-bot.timer su-watchdog.timer --no-pager
```

**Automation 24/7:** installer `studentup-bot.timer` (hourly) + `su-watchdog.timer`
(2 min: website + bot freshness + disk/TLS) enable chestundi.
Telegram approvals kosam: VPS daemon (`python -m autoblog.approval_bot` systemd lo)
**leda** cron line `*/5 * * * * ... run.py --approval-poll` (simple — ade chalu).

**Static site (optional):** `preview/` ni Caddy tho serve cheyali ante
`deploy/Caddyfile` ni `/etc/caddy/Caddyfile` ki copy chesi domain marchandi
(HTTPS automatic). WordPress vadithe ee step avasaram ledu.

**Backups (must):**

```bash
sudo crontab -e
# 15 2 * * * /opt/studentup/deploy/backup.sh >> /var/log/studentup/backup.log 2>&1
```

Restore: bot timer aapi → `cp /var/backups/studentup/state-<stamp>.db /opt/studentup/state.db` → timer malli start.

**Update (kotha version):**

```bash
cd /opt/studentup && sudo -u studentup git pull
sudo -u studentup .venv/bin/pip install -q -r requirements.txt
```

---

## Path B — Docker (okka command)

```bash
git clone https://github.com/charanpendota98-prog/Automation_charan1.git && cd Automation_charan1
cp .env.example .env   # WP_* / GEMINI_* / TELEGRAM_* pettandi

docker compose -f deploy/docker-compose.yml up -d --build
docker compose -f deploy/docker-compose.yml logs -f
```

Container lo hourly `run.py` + prathi 5 min `--approval-poll` loop nadustundi.
Data `studentup-data` volume lo untundi (`/data/state.db`).
Update: `git pull && docker compose -f deploy/docker-compose.yml up -d --build`.
Health: container `state.db` freshness chustundi (3h kanna stale ayite unhealthy).

---

## Path C — Shared-hosting cron (MilesWeb)

Server maintenance vaddu ante: bot + approvals anni cPanel cron jobs ga —
**`DEPLOY_MILESWEB.md` follow cheyandi** (step-by-step: venv setup + 5 cron lines).
Tradeoff okkate: approval taps ~5 min late (cron rhythm).

---

## WordPress side (studentup.in bot)

Site already hosted kada — bot ni server lo run cheyyali:

```bash
# .env: WP_SITE / WP_USERNAME / WP_APP_PASSWORD (Application Password) + TELEGRAM_*
python run.py --status          # plan/stats
python run.py --force           # okka post ippude (draft lo vastundi by default)
python run.py --site-audit      # site health audit (read-only)
python run.py --test-all        # anni suites
```

Review flow (safe default): `DEFAULT_POST_STATUS=draft` → Telegram lo ✅ Publish / 🗑️ Delete
buttons (VPS daemon `python -m autoblog.approval_bot` leda cron `run.py --approval-poll`).
Live publish ki `EDITORIAL_REVIEWER` + QA/originality/top-post/v41 gates pass avvali.

---

## Security checklist (bot secrets)

- [ ] `.env` **chmod 600**, git lo commit avvadu (`.gitignore` lo undi)
- [ ] WordPress **Application Password** (main password eppudu vaddu) + admin 2FA on
- [ ] Telegram bot token / Gemini keys ni screenshots/logs lo share cheyyaledu
- [ ] Backups daily + **restore okka sari test** chesaru
- [ ] Server lo `sudo apt upgrade` (security patches) — monthly
- [ ] Old WP users/plugins audit (`run.py --site-audit`) — quarterly

## Monitoring

```bash
sudo systemctl status studentup-bot.timer su-watchdog.timer --no-pager
sudo journalctl -u studentup-bot -n 80        # bot runs
tail -f /var/log/studentup/watchdog.log       # watchdog alerts
python run.py --guardian                      # site/UI/SEO/ads/feed/storage check
python run.py --readiness                     # TOP WEBSITE readiness score
```

UptimeRobot (free) → `https://studentup.in/` 5-min ping — watchdog ki rendo kannu.

## Troubleshooting

| Problem | Fix |
|---|---|
| Bot run avvatledu | `journalctl -u studentup-bot -n 60` → venv/deps? `run.py --deploy-check` |
| Timer fire avvatledu | `systemctl status studentup-bot.timer` + `timedatectl` (server time) |
| WP publish fail | `--check-wp` → Application Password correct-a? RankMath REST on-a? |
| Telegram approval ravatledu | Bot token/chat id? cron `approval.log` chudandi; VPS aithe daemon status |
| Disk full | `tools/prune_media.py --days 30 --apply` + output/ cleanup |
| state.db lock/permission | `chown -R studentup:studentup /opt/studentup` + timer restart |

## Honest notes (repo policy)

- Google ranking / AdSense approval / RPM **guarantee ledu** — ee system quality, speed,
  uptime, zero-mistake flow ni **measure** chestundi, adi mee advantage.
- Job results/deadlines ni publish cheyyadaniki **mundu meeru verify** cheyandi
  (Telegram approval gate anduke undi).
- Free tiers heavy traffic ki risky; paid VPS/shared + backups + HTTPS = minimum professional setup.

## v72 — PWA files (preview site)

Static preview ni upload chesinappudu `manifest.webmanifest` + `sw.js` ni index.html pakkana
(root lo) pettandi — app-laga install + offline page ki avi kaavali. WordPress lo theme ne
serve chestundi (`?studentup_manifest=1` · `?studentup_sw=1`) — extra config ledu.
