# 🚀 DEPLOY — StudentUp bot + College Exam Portal (honest, step-by-step)

Ee file lo **3 deployment paths** unnayi. Mee situation chusi okati select cheyandi:

| Path | Evariki | Time | Enti deploy avutundi |
|---|---|---|---|
| **A. VPS + systemd + Caddy** (recommended) | Server unna college / mee own VPS (₹300–600/నెల) | ~10 min | Exam portal (**HTTPS** tho) + hourly bot + backups |
| **B. Docker compose** | Docker telisinavallu / kotha VM | ~5 min | Exam portal (okka command), volume lo data |
| **C. PaaS (Render/Railway/Fly)** | Server maintenance vaddu anukunevallu | ~10 min | Exam portal (managed HTTPS), free/cheap tier ok |

**Modata (anni paths ki):** ee command run cheyandi — enti miss undo cheptundi.

```bash
python run.py --deploy-check
```

Output lo `❌ fail` unte adi fix cheyandi; `⚠️ warn` unnavi optional/manual (ex: WP creds).

---

## Path A — VPS (Ubuntu 22.04/24.04) ⭐ recommended

Kolukovalsina server: 1 vCPU / 1 GB RAM chalu (exam portal stdlib + sqlite; 200–500 students
ki comfortable). Domain okati (ex: `exams.college.edu`) + DNS A record server IP ki.

```bash
# 1) Server SSH lo (root/sudo)
sudo apt update && sudo apt install -y git
git clone https://github.com/charanpendota98-prog/Automation_charan1.git /opt/studentup-src

# 2) One-command install (python+deps+user+systemd+Caddy+check)
sudo DOMAIN=exams.college.edu REPO_URL=https://github.com/charanpendota98-prog/Automation_charan1.git \
     bash /opt/studentup-src/deploy/install-vps.sh

# 3) Verify
sudo systemctl status exam-portal --no-pager
curl -s localhost:8080/healthz          # {"ok": true, ...}
sudo cat /opt/studentup/exam_portal_admin_key.txt     # admin key (save cheyandi!)
```

Browser lo: `https://exams.college.edu/admin` → admin key → **+ New exam** → questions paste →
roster → **START**. Students ki `https://exams.college.edu/exam/<CODE>` link pampandi
(roll number tho join avutaru — password ledu).

**Firewall:** `sudo ufw allow 80,443/tcp` — **8080 ni bayata open cheyyakandi** (Caddy
localhost nunchi proxy chestundi).

**Caddy badulu nginx** vadali ante: `sudo cp deploy/nginx-exam.conf /etc/nginx/sites-available/exam-portal`
(then `certbot --nginx -d exams.college.edu`).

**Automation (bot) 24/7:** installer `studentup-bot.timer` ni enable chestundi (hourly).
WordPress creds `.env` lo pettandi:

```bash
sudo -u studentup nano /opt/studentup/.env     # WP_SITE / WP_USERNAME / WP_APP_PASSWORD / TELEGRAM_*
sudo systemctl start studentup-bot             # okka manual test run
sudo journalctl -u studentup-bot -n 80         # result chudandi
```

**Backups (must):**

```bash
sudo crontab -e
# 15 2 * * * /opt/studentup/deploy/backup.sh >> /var/log/studentup/backup.log 2>&1
```

Restore: `systemctl stop exam-portal && cp /var/backups/studentup/exam_portal-<stamp>.db /opt/studentup/exam_portal.db && systemctl start exam-portal`.

**Update (kotha version):**

```bash
cd /opt/studentup && sudo -u studentup git pull
sudo -u studentup .venv/bin/pip install -q -r requirements.txt
sudo systemctl restart exam-portal
```

---

## Path B — Docker (okka command)

```bash
git clone https://github.com/charanpendota98-prog/Automation_charan1.git && cd Automation_charan1
echo "EXAM_PORTAL_ADMIN_KEY=$(openssl rand -hex 16)" > .env
echo "EXAM_PUBLIC_URL=https://exams.college.edu" >> .env

docker compose -f deploy/docker-compose.yml up -d --build
docker compose -f deploy/docker-compose.yml logs -f
curl -s localhost:8080/healthz
```

Data `studentup-data` volume lo untundi (exam DB). Update: `git pull && docker compose -f deploy/docker-compose.yml up -d --build`.
HTTPS ki mundu Caddy/nginx/Cloudflare Tunnel pettandi (compose 127.0.0.1:8080 ki matrame bind avutundi).

---

## Path C — PaaS (Render / Railway / Fly.io)

1. GitHub repo ni PaaS lo connect cheyandi (repo already GitHub lo undi).
2. **Start command:** `python run.py --exam-portal --exam-host 0.0.0.0 --exam-port $PORT --exam-db /data/exam_portal.db`
3. **Environment:** `EXAM_PORTAL_ADMIN_KEY=<random>`, `EXAM_PUBLIC_URL=https://<app-url>`, optional Telegram/webhook.
4. **Persistent disk** attach cheyandi (`/data` ki) — leda exam DB restart ki poyidi (SQLite file).
5. Health check path: `/healthz`.
6. Free tier lo service idle aithe sleep avutundi — **exam day ki paid instance** leda VPS
   recommend (students mid-exam lo request fail avvakoodadu).

---

## WordPress side (studentup.in bot)

Site already hosted kada — bot ni server lo run cheyyali:

```bash
# .env: WP_SITE / WP_USERNAME / WP_APP_PASSWORD (Application Password) + TELEGRAM_*
python run.py --status          # plan/stats
python run.py --force           # okka post ippude (draft lo vastundi by default)
python run.py --site-audit      # site health audit (read-only)
python run.py --test-all        # anni suites (30/30)
```

Review flow (safe default): `DEFAULT_POST_STATUS=draft` → Telegram lo ✅ Publish / 🗑️ Delete
buttons (`python -m autoblog.approval_bot`, systemd lo 24/7 pettandi).
Live publish ki `EDITORIAL_REVIEWER` + QA/originality/top-post/v41 gates pass avvali.

---

## Security checklist (exam data)

- [ ] Admin key share cheyyaledu (per-exam **manage link** matrame share cheyandi: `/manage/<CODE>?key=...`)
- [ ] HTTPS mandatory (Caddy auto) — plain HTTP lo roll numbers/answers velaku
- [ ] Portal port (8080) bayata open ledu (ufw/firewall)
- [ ] `.env` + `exam_portal_admin_key.txt` **chmod 600**, git lo commit avvavu (`.gitignore` lo unnayi)
- [ ] Backups daily + **restore okka sari test** chesaru
- [ ] Server lo `sudo apt upgrade` (security patches) — monthly
- [ ] Exam ayyaka: results/CSV export + purge decide (student data retention policy mee college di)

## Monitoring

```bash
curl -s https://exams.college.edu/healthz        # uptime monitor (UptimeRobot free) ki
sudo journalctl -u exam-portal -f                # live logs
tail -f /var/log/studentup/exam-portal.log       # service log
python run.py --exam-portal-test-channels        # Telegram/webhook test ping
```

## Troubleshooting

| Problem | Fix |
|---|---|
| Portal start avvatledu | `journalctl -u exam-portal -n 60` → port busy aithe `--exam-port 8081` |
| HTTPS vastaledu | DNS A record correct-a? `sudo systemctl status caddy` (80/443 open-a?) |
| Students join avvatledu | `EXAM_PUBLIC_URL` set chesara? Firewall? Server time correct-a (`timedatectl`) |
| Exam DB lock/permission | `chown -R studentup:studentup /opt/studentup` + `systemctl restart exam-portal` |
| Bot post cheyyaledu | `journalctl -u studentup-bot -n 80` → WP creds/QA gate messages chudandi |

## Honest notes (repo policy)

- Google ranking / AdSense approval / RPM **guarantee ledu** — ee system quality, speed,
  uptime, zero-mistake flow ni **measure** chestundi, adi mee advantage.
- Exam results/deadlines ni publish cheyyadaniki **mundu meeru verify** cheyandi.
- Free tiers exam day ki risky; paid VPS/PaaS + backups + HTTPS = minimum professional setup.
