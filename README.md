# studentup.in Auto-Blogger 🤖

24/7 automatic blog posting system for **studentup.in** (WordPress) — runs on your Oracle Cloud instance.

- **AI content:** Google Gemini (free tier) generates Telugu + English mix articles
- **URL → 100% Original:** vere site article URL ivvandi → facts teesi **complete ga original ga rewrite** (no copy) + **extra advanced info** add chesi post
- **Multi-source research:** internet lo same topic articles **search chesi merge** chestundi (MERGE & BEAT strategy — competitors kante complete article)
- **SEO + Rank Math 100%:** focus + secondary keywords, Quick Answer (featured snippet), TOC, internal/external links, FAQ/Article schema, meta tags — anni automatic
- **Review flow:** posts **DRAFT** lo vastayi → **Telegram ki message** (✅ Publish / 🗑️ Delete buttons) → **one tap lo approve**
- **Categories:** Scholarships, Govt Jobs, Education News, Exam Updates, Admissions, Results, Internships, Study Tips
- **Auto-publish:** WordPress REST API — post + category + tags + featured image + SEO meta
- **Schedule:** 10–15 posts/day, spread across 6 AM – 10 PM IST, hourly runs via systemd/cron
- **No duplicates:** SQLite state tracks every posted title + source URL
- **WhatsApp alerts** too (optional)

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

### Step 3: Telegram bot create cheyali (review buttons kosam — 3 nimishalu)

1. Telegram lo **@BotFather** open cheyandi
2. `/newbot` ani pampandi → peru ivvandi (example: `studentup_review_bot`)
3. BotFather **token** istundi (`123456:ABC-DEF...` format) — copy cheyandi
4. (WhatsApp kuda kavali ante: `https://callmebot.com` — WhatsApp lo `+34 644 66 32 62` ki
   "I allow call mebot to send me messages" ani pampi, vachhina apikey ni URL ga save cheyandi)

### Step 4: Oracle Cloud instance lo deploy cheyali

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

### Step 5: Test cheyandi

```bash
# WordPress connection correct aa?
.venv/bin/python run.py --check-wp

# Notification test (Telegram ki message vastunda chudandi):
.venv/bin/python run.py --notify-test

# Oka real test post (DRAFT lo vastundi):
.venv/bin/python run.py --force
```

Draft create ayyaka **Telegram ki message vastundi** — ✅ Publish button click cheyte post live avtundi!

**Mundhu cheyali:** setup chesina tarvata, mi kotha Telegram bot chat loki velli **`/start`** ani pampandi — bot automatic ga register aytundi. (Approval bot setup_oracle.sh dwara 24/7 run avtundi.)

## Review workflow (idi important!)

```
┌─────────────┐    ┌──────────────┐    ┌─────────────────┐    ┌──────────┐
│ Bot article │───▶│  WordPress   │───▶│  Telegram msg   │───▶│  LIVE!   │
│  generate   │    │ DRAFT lo save│    │ ✅ Publish btn  │    │ (1 tap)  │
└─────────────┘    └──────────────┘    └─────────────────┘    └──────────┘
```

- Prathi post **draft** loney save avtundi — site lo kanipinchadu
- Telegram ki message: title, category, tags, summary + buttons
- **✅ Publish** → post live · **🗑️ Delete** → trash · **✏️ Edit in WordPress** → manual edit
- Bot commands: `/pending` (review avasaram leni drafts), `/stats` (poster stats)
- Direct ga publish avvali ante (review ledu) → `.env` lo `DEFAULT_POST_STATUS=publish`

---

## 🔥 Advanced Mode: URL → 100% Original Article (No Copy)

Vere valla site article ni **copy cheyakunda** daani nunchi mana own original article raayadam — 3 methods:

### Method 1: Telegram lo URL paste cheyandi (easiest!)
1. Mi bot chat loki vere site article URL ni paste cheyandi
2. Bot: source nunchi **facts** teesi → **100% original** Telugu article (2200-3000 words) → **extra advanced sections** (documents, mistakes, tips, tables, FAQ) add chesi → **SEO optimize** chesi → **DRAFT** create chestundi
3. ✅ Publish button press cheyandi — done!

### Method 2: Command line
```bash
.venv/bin/python run.py --url "https://example.com/news/article-link"
```

### Method 3: Queue file (bulk)
`sources_queue.txt` file lo URLs okka line okati paste cheyandi:
```
https://somesite.com/ssc-notification-article
https://othersite.com/scholarship-news
```
Scheduler prathi hour lo queue lo unna URL ni priority ga process chesi original post chestundi. Process ayyina URL automatic ga remove avtundi + gurthu pettukundi (malli duplicate cheyadu).

### Ee mode lo em avtundi?
| Step | Em chestundi |
|---|---|
| 1. Fetch | Source article read chesi text extract (ads/menu junk vadiyesi) |
| 2. **Research** | **Internet lo aa same topic meeda inko articles search** (DuckDuckGo — API key ledu) — top competitor sources fetch |
| 3. **Merge & Beat** | Anni sources facts **merge** — mi URL lo **miss ayyina info kuda add** (fee, salary, selection stages, documents) |
| 4. Rewrite | Complete ga fresh structure + fresh wording lo Telugu article (2200-3000 words), no copy |
| 5. Enhance | Extra sections: documents list, common mistakes, pro tips, comparison table, key dates |
| 6. SEO | Quick Answer + focus/secondary keywords + TOC + internal/external links + FAQ/Article schema + Rank Math meta |
| 7. Draft | WordPress draft + Telegram review buttons |

> Idhe **"MERGE & BEAT" strategy** — internet lo already unna articles kante MII article ekkuva complete. Same topic search lo mii post top lo randaniki idhe main Google trick. DuckDuckGo fail aite bot primary source tho graceful ga continue chestundi.

## 🛡️ QA & Safety Layer (kothena — 100x level)

Prathi post lo **publish mundhe** automatic checks:

| Check | Em chestundi |
|---|---|
| **Originality Proof** | Final article vs sources — 5-gram shingle analysis tho **measurable no-copy %**. 70% kante takkuva aite article **automatic regenerate**! Telegram message lo "Originality: 94%" ani kanipistundi |
| **QA Score /100** | Rank Math-style 15 checks — keyword placement, density, word count, FAQ, table, meta length, tags... Telegram lo score kanipistundi |
| **HTML Sanitizer** | Gemini script/div/markdown waste ichina automatic strip — only clean SEO tags |
| **Keyword Intelligence** | Google lo already top-lo unna competitor titles ni kuda analyze chesi **vatikante strong title/keywords** generate |
| **Boilerplate Footprint Fix** | Intro paragraphs & headings prathi post lo **rotate avtayi** — Google duplicate-pattern spam signal risk zero |
| **E-E-A-T Trust Box** | "About This Article" — editorial review + sources + date (Google trust signals) |
| **Reading Time Badge** | ⏱️ words + minutes — UX + dwell time signal |
| **Smart Source Fetch** | Site block cheste Googlebot UA tho retry + Telugu encoding auto-fix |

## 🚀 Traffic & Indexing Boosters

- **IndexNow** (optional): publish ayyaka Bing/Yandex ki instant ping — `INDEXNOW_KEY` set cheyandi (key file site root lo host cheyali)
- **Telegram Channel auto-post** (optional): publish ayyaka mi channel lo automatic post — instant traffic + social signals (`TELEGRAM_CHANNEL_CHAT_ID`)
- **Daily Digest**: roji chivari lo Telegram ki summary (enta posts, em pending)

## 🎯 SEO / Rank Math 100% Score — Top 0.001% Level Tricks

Prathi post lo automatic ga:
- ✅ **Focus keyword** — title lo, first paragraph lo, 2+ headings lo, meta description lo (~1% density)
- ✅ **Secondary keywords** — 3-5 related search phrases kuda Rank Math lo set (multi-keyword tracking)
- ✅ **SEO title** — keyword start lo + year + power word + number (60 chars lopala)
- ✅ **Quick Answer block** — article top lo 40-60 word direct answer (**featured snippet bait** — Google position 0 kosam main trick!) + "Last Updated" fresh date
- ✅ **Table of Contents** — automatic TOC + anchor links (Rank Math readability)
- ✅ **Internal links** — mi site recent posts ki "Related Articles" links (same category priority)
- ✅ **External links** — official portals (ssc.gov.in lanti vi) nofollow links tho
- ✅ **FAQ + Article + Breadcrumb JSON-LD schema** — Google rich results eligibility — `te` language tag tho
- ✅ **Social OG/Twitter meta** — Facebook/WhatsApp/Twitter preview titles (CTR boost)
- ✅ **Image alt text** — focus keyword tho alt text
- ✅ **Rank Math meta** — `rank_math_focus_keyword` (primary + secondary), `rank_math_description`, `rank_math_title` direct REST API dwara
- ✅ **Content length** — 2200-3000 words, short paragraphs, transition words (readability full)
- ✅ **Meta description** — 140-160 chars keyword tho
- ✅ **Tables + lists** — snippet-eligible formats

> Tip: WordPress lo **Rank Math plugin active cheyandi** — bot automatic ga plugin meta fill chestundi, editor lo open chuste 90-100/100 score kanipistundi.

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
.venv/bin/python run.py --url "https://site.com/article"   # URL -> original rewrite post
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
| `DEFAULT_POST_STATUS` | `draft` | `draft` = Telegram review flow · `publish` = direct live |
| `TELEGRAM_BOT_TOKEN` | — | @BotFather token — buttons tho review messages |
| `TELEGRAM_CHAT_ID` | auto | `/start` cheythe bot automatic ga register avtundi |
| `WHATSAPP_CALLMEBOT_URL` | — | WhatsApp text alerts (callmebot.com free) |
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

## Monetization (AdSense) — automation problem istunda? 😟

**Short answer: review flow unte problem undadu.** Kani rules telusukovali:

1. **Google AI content ni ban cheyadu** — kani "low value content" ni reject chestundi. Idi matram important:
   - ✅ **Review flow** (mi bot default ga idi untundi!) — prathi post miree approve chestunnaru
   - ✅ Original content — Gemini prathi article fresh ga write chestundi (copy paste kadu)
   - ✅ Original images — bot eee images generate chestundi (Google Images nunchi visheshanga ledu, copyright ledu)
   - ❌ Fake deadlines/vacancy numbers — bot prompt lo strict ga ban chesanu
2. **AdSense approval kosari:**
   - Privacy Policy, About Us, Contact pages undali
   - 20-30 quality posts unnappudu apply cheyandi
   - Site new aite **mundu 5-8 posts/day chala** — approval tarvata 10-15 ki penchandi
   - ChinnA human-written posts kuda add cheyandi (menually raayandi)
3. **Google News/Discover lo rank avvali ante:** pure AI spam ga ledu — human review + original value undali. Mi draft-review flow idi guarantee chestundi.
4. **Telugu keyword SEO:** bot already Telugu+English mix lo rastundi — local search ki idi best.

**Bottom line:** Review lekunda site lo auto-publish cheyakandi — mee current setup (draft + approve) safe & sustainable. 📈

## Important notes

- AI-generated content — **occasionally review cheyandi**. Bot fake deadlines/vacancy numbers rasanivvakunda strict rules pettanu, kani manam verify cheyadam better.
- Google lo duplicate content penalty radanuke prathi article fresh ga unique topic meeda generate avtundi + duplicate title check untundi.
- State antha `state.db` lo — adi delete cheyakudadu (delete cheste duplicate posts possibility).

## Project structure

```
├── run.py                  # CLI entry point
├── setup_oracle.sh         # One-command Oracle Cloud installer
├── requirements.txt        # requests + pillow + beautifulsoup4
├── .env.example            # Config template
├── autoblog/
│   ├── config.py           # Settings loader
│   ├── main.py             # Orchestrator + schedule logic
│   ├── pipeline.py         # Shared publish flow (SEO+image+meta+notify)
│   ├── gemini_client.py    # Gemini REST client + Telugu prompts (auto + rewrite)
│   ├── wordpress_client.py # WP REST publish (post/media/terms/RankMath meta)
│   ├── sources.py          # URL fetch + text extraction + queue file
│   ├── research.py         # Web search (DuckDuckGo) + multi-source gathering
│   ├── seo.py              # Quick Answer + TOC + links + FAQ/Article JSON-LD schema
│   ├── notifier.py         # Telegram (buttons) + WhatsApp alerts
│   ├── approval_bot.py     # 24/7 Telegram bot (publish buttons + URL rewrite)
│   ├── topic_engine.py     # Category rotation + mock generator
│   ├── image_gen.py        # Featured image (PIL, no API)
│   └── state.py            # SQLite state (dedupe, plan, sources)
└── tests/                  # end-to-end tests (fake WP/Telegram/source servers)
```
