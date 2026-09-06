# studentup.in Auto-Blogger 🤖

24/7 automatic blog posting system for **studentup.in** (WordPress) — runs on your Oracle Cloud instance.

- **AI content:** Google Gemini (free tier) generates Telugu + English mix articles
- **Categories:** Scholarships, Govt Jobs, Education News, Exam Updates, Admissions, Results, Internships, Study Tips
- **Auto-publish:** WordPress REST API — post + category + tags + featured image + SEO meta
- **Schedule:** 10–15 posts/day, spread across 6 AM – 10 PM IST, hourly runs via systemd/cron
- **No duplicates:** SQLite state tracks every posted title

---

## Setup Guide (Telugu)

### Step 1: Gemini API key (FREE) teyali

1. `https://aistudio.google.com` open cheyandi (Google account tho login)
2. **"Get API key"** → **"Create API key"** click cheyandi
3. Key copy chesi save cheyandi (`AIza...` tho start avtundi)

### Step 2: WordPress Application Password create cheyali

1. `https://studentup.in/wp-admin` lo login cheyandi
2. Left menu lo **Users → Profile** click cheyandi
3. Page scroll chesi bottom daggara **"Application Passwords"** section kanipistundi
4. **"New Application Password"** box lo peru ivvandi — example: `autoblog`
5. **"Add New Application Password"** button click cheyandi
6. Screen meedha oka password vastundi — **`xxxx xxxx xxxx xxxx xxxx xxxx`** format lo (spaces tho)
7. Danini **immediately copy cheyandi** — malli chudalem! Notepad lo save cheyandi

> Note: Application Password = bot ki ichina permission. Mi real WordPress password e kadu — anytime revoke cheseyochu (delete button tho). Safe method idhi.

> **Ila block ayyinda?** Application Password section kanipisthe: `install-plugins` capability ledu ante, mi account full admin kadu anni — admin account tho cheyandi. Ekkuva security plugins (Wordfence lanti) unnayi ante REST block cheyyochu — plugin settings lo REST API allow cheyandi.

### Step 3: Oracle Cloud instance lo deploy cheyali

SSH chesi instance loki velli:

```bash
# Option A: git tho (recommended)
git clone https://github.com/charanpendota98-prog/Automation_charan1.git studentup-autoblog
cd studentup-autoblog

# Option B: file upload
# local nunchi: scp -r . ubuntu@YOUR_ORACLE_IP:~/studentup-autoblog
```

Tarvata **okka command** — setup script antha automatic ga chestundi:

```bash
bash setup_oracle.sh
```

Idhi cheyindi:
1. Python + fonts + system packages install
2. Python virtual environment (`.venv`) create
3. `.env` config file — mi values adugutundi (WP username, Application Password, Gemini key)
4. WordPress connection test
5. **Hourly scheduler** install (systemd timer — 24/7 automatic)

### Step 4: Test cheyandi

```bash
# WordPress connection correct aa?
.venv/bin/python run.py --check-wp

# Oka real test post publish cheyali ante:
.venv/bin/python run.py --force

# WordPress lo check cheyandi — post vacchinda!
```

Post కనిపించిందా? **అయిపోయింది! Bot 24/7 automatic ga post chestundi.** 🎉

---

## Daily working style

- Prathi గంట (hourly) scheduler bot ni run chestundi
- Bot roju morning 6 AM lo aa roju plan chestundi — 10–15 random hours pick chestundi (6 AM–10 PM madhya)
- Current hour plan lo undo → new article generate chesi publish chestundi
- Duplicate titles, category balance — antha automatic ga manage avtundi

## Useful commands

```bash
.venv/bin/python run.py --status    # inka entha posts ayyayi, plan emito
.venv/bin/python run.py --force     # ippude oka post publish cheyali ante
.venv/bin/python run.py --dry-run   # WordPress touch avvakunda local test
.venv/bin/python run.py --dry-run --mock   # offline test (API key kavali kadu)

# Scheduler control (systemd):
sudo systemctl stop studentup-autoblog.timer    # bot ni stop cheyali ante
sudo systemctl start studentup-autoblog.timer   # malli start
systemctl list-timers studentup-autoblog.*     # next run eppudo

# Log file:
tail -f log/autoblog.log
```

## Configuration (`.env`)

| Variable | Default | Description |
|---|---|---|
| `WP_SITE` | `https://studentup.in` | Site URL |
| `WP_USERNAME` | — | WordPress admin username |
| `WP_APP_PASSWORD` | — | Application Password (Step 2) |
| `GEMINI_API_KEY` | — | Gemini API key (Step 1) |
| `DEFAULT_POST_STATUS` | `publish` | `draft` pette review kosam wait chestundi |
| `DAILY_MIN` / `DAILY_MAX` | `10` / `15` | Posts per day range |
| `ACTIVE_HOUR_START` / `ACTIVE_HOUR_END` | `6` / `22` | Posting window (24h IST) |
| `CATEGORIES` | 8 categories | Site sections |
| `IMAGE_ENABLED` | `1` | Featured image generation on/off |

Marpali te: `.env` edit chesi scheduler ni restart cheyandi: `sudo systemctl restart studentup-autoblog.timer`

## Troubleshooting

**401 / authentication failed**
- `.env` lo username + Application Password exact ga unnaya? Password lo spaces kavali (`xxxx xxxx` format lo ne paste cheyandi)
- Site lo SSL active aa? `WP_SITE` `https://` tho start avvali
- LiteSpeed/NGINX servers kosam: `Authorization` header block avtundi ante — `.htaccess` lo idi add cheyandi:
  ```apache
  RewriteEngine On
  RewriteRule ^index\.php$ - [E=HTTP_AUTHORIZATION:%{HTTP:Authorization}]
  ```

**Gemini 429 (rate limit)**
- Free tier daily limits. Bot automatic ga retry chestundi. Ekkuva posts kavali ante `GEMINI_MODEL=gemini-2.5-flash` tho untundi — chala efficient.

**Posts publish avtunnayi kani review cheyali**
- `.env` lo `DEFAULT_POST_STATUS=draft` pettandi — posts WordPress drafts lo vastayi, miru approve cheyandi.

**Bot status em cheyalo teleefda?**
- `.venv/bin/python run.py --status` run cheyandi.

## Important notes

- AI-generated content — **occasionally review cheyandi**. Bot fake deadlines/vacancy numbers rasanivvakunda strict rules pettanu, kani manam verify cheyadam better.
- Google lo duplicate content penalty radanuke prathi article fresh ga unique topic meeda generate avtundi + duplicate title check untundi.
- State antha `state.db` lo — adi delete cheyakudadu (delete cheste duplicate posts possibility).

## Project structure

```
├── run.py                  # CLI entry point
├── setup_oracle.sh         # One-command Oracle Cloud installer
├── requirements.txt        # requests + pillow
├── .env.example            # Config template
├── autoblog/
│   ├── config.py           # Settings loader
│   ├── main.py             # Orchestrator + schedule logic
│   ├── gemini_client.py    # Gemini REST client + Telugu prompt
│   ├── wordpress_client.py # WP REST publish (post/media/terms)
│   ├── topic_engine.py     # Category rotation + mock generator
│   ├── image_gen.py        # Featured image (PIL, no API)
│   └── state.py            # SQLite state (dedupe, plan, counts)
└── tests/fake_wp_test.py   # WP client end-to-end test
```
