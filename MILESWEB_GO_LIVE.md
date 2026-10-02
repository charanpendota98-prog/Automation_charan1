# 🚀 studentup.in — MilesWeb (cPanel) lo ZIP upload chesi LIVE (v175)

Ee doc = okka page lo motham. **Moodu zips** — ekkadiki upload cheyyali anedi kinda table lo.
Anni zips `milesweb-kit/` folder lo unnayi (`python3 tools/build_milesweb_kit.py` tho malli build cheyyachu).

| # | Zip | Ekkadiki | Enti chestundi |
|---|---|---|---|
| 1 | `studentup-theme-1.9.31.zip` | WordPress → **Appearance → Themes → Add New → Upload Theme** | Mee site design + job card + Apply bar + schema + ads slots (theme activate ayinappude categories/menus/policy pages auto-create) |
| 2 | `studentup-seo-bridge-1.1.0.zip` | WordPress → **Plugins → Add New → Upload Plugin** | Rank Math fields ni REST tho verify chese bridge (theme lo already undi — veru theme vadithe matrame kavali) |
| 3 | `studentup-static-site.zip` | cPanel → **File Manager → `public_html/`** | Static preview site (WordPress path vadakapothe matrame) |
| 4 | `studentup-bot-cron.zip` | cPanel → **File Manager → `~/bot/`** | Auto-blogger bot (cron jobs tho: drafts + approvals + guardian) |

> **Okate path select cheyandi:** WordPress + theme (⭐ recommended) **leda** static site.
> Rendu kalipi `public_html` lo pettakandi (WordPress `index.php` ne serve avvali).
> Bot ni **MilesWeb lo okka chota matrame** schedule cheyandi (Oracle + MilesWeb rendu unte **duplicate posts**).

---

## 0) Modata verify (30 seconds) — zip sha256

```bash
sha256sum studentup-theme-1.9.31.zip      # leda: sha256sum -c SHA256SUMS.txt
```
`milesweb-kit/SHA256SUMS.txt` lo unna value tho match avvali. Theme zip build **fully
reproducible** (POT date kuda fixed) — so ee sha256 prathi machine lo same.

---

## 1) WordPress + theme (10 nimishalu) ⭐

1. cPanel → **WordPress Toolkit / Softaculous** → `studentup.in` ki WordPress install.
2. cPanel → **SSL/TLS Status** → Let's Encrypt **ON** (free).
3. `https://studentup.in/wp-admin` login → **Users → Profile → Application Passwords**
   → name "bot" → **Add New** → copy chesi `.env` lo `WP_APP_PASSWORD=` ki pettandi
   (idi password kaadu — separate app password, eppudaina revoke cheyyachu).
4. **Appearance → Themes → Add New → Upload Theme** → `studentup-theme-1.9.31.zip`
   → **Install Now** → **Activate**.
   Activate ayina ventane theme **one-click setup** run avutundi:
   categories (TS/AP/Central/Private/Software/Walk-in/…), policy pages
   (About/Contact/Privacy/Terms/Disclaimer/Editorial), menus (header + footer),
   permalink `/%postname%/`, timezone Asia/Kolkata, posts-per-page.
   *(Unna categories/pages ni touch cheyyadu — missing vi matrame add chestundi.)*
5. **Rank Math** plugin install chesi activate cheyyandi (SEO fields).
   Theme lo `inc/seo-bridge.php` already load avutundi → veru plugin **kavasaram ledu**.
   Veru theme vaadutunna appude `studentup-seo-bridge-1.1.0.zip` install cheyyandi.
6. **Appearance → StudentUp** → mee WhatsApp/Telegram/Instagram/YouTube links,
   homepage sections toggles pettandi. AdSense ippudu **OFF** unchandi
   (approval tarvata `ADSENSE_APPROVED=1`).
7. Phone lo site open chesi check: hero · hot jobs · quiz ring · bottom nav ·
   oka job post lo **Apply online** bar.

---

## 2) Bot on MilesWeb cron (15 nimishalu, one-time)

1. cPanel → **File Manager** → home folder lo `bot` folder create cheyyandi.
2. `studentup-bot-cron.zip` upload → **Extract** (files anni `~/bot/` lo undali —
   leda `~/bot/studentup-bot-cron/` lo extract aithe aa files ni `~/bot/` ki move cheyyandi).
3. cPanel → **Terminal** (leda SSH):
```bash
cd ~/bot
python3 --version                      # 3.10+ undali (thakkuva unte hosting support ni adagandi)
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env
nano .env                              # WP_SITE · WP_USERNAME · WP_APP_PASSWORD ·
                                       # AI key (Gemini) · TELEGRAM_BOT_TOKEN · TELEGRAM_CHAT_ID
mkdir -p log
.venv/bin/python run.py --deploy-check # anni green ravali (0 fail)
.venv/bin/python run.py --check-wp     # WordPress login test
.venv/bin/python run.py --site-setup --dry-run   # WP settings audit (writes ledu)
.venv/bin/python run.py --tg-test      # Telegram ping (optional)
```
4. cPanel → **Cron Jobs** → kindha 4 lines add cheyyandi
   (`<user>` ni mee cPanel username tho marchandi):
```
0 * * * *      cd /home/<user>/bot && /home/<user>/bot/.venv/bin/python run.py >> log/cron.log 2>&1
*/5 * * * *    cd /home/<user>/bot && /home/<user>/bot/.venv/bin/python run.py --approval-poll >> log/approval.log 2>&1
0 7 * * *      cd /home/<user>/bot && /home/<user>/bot/.venv/bin/python run.py --guardian >> log/guardian.log 2>&1
0 3 * * 0      cd /home/<user>/bot && /home/<user>/bot/.venv/bin/python run.py --site-audit >> log/audit.log 2>&1
```
   (MilesWeb lo **unlimited cron jobs** unnayi; shared hosting lo daemon run avvadu —
   anduke bot antha cron-only ga design ayyindi.)
5. Flow: cron → bot research + draft → **WordPress lo DRAFT** → Telegram lo
   **✅ Publish / 🗑️ Delete** buttons → meeru tap chesthe ~5 nimishalaki post live
   (cron rhythm). **Emi mee approval lekunda publish avvadu.**

---

## 3) Static site path (WordPress vadakapothe)

1. cPanel → File Manager → `public_html/`.
2. `studentup-static-site.zip` upload → **Extract** (zip root lo ne files unnayi —
   `index.html`, `pages/`, `robots.txt`, `sitemap.xml`, `ads.txt`,
   `manifest.webmanifest`, `sw.js`, `data/`).
3. `https://studentup.in` open → design kanipistundi. PWA install kuda work avutundi.
   > Bot posts WordPress lo untayi — static site lo kanipinchavu. Dynamic blog kavalante
   > WordPress + theme path (section 1) select cheyyandi.

---

## 3b) Growth loops (v181) — visitors → content → rankings → revenue

Ee loops mee site ni "post machine" nunchi **business** ga marchutayi (cron lo automatic):

| Loop | Command | Enti chestundi |
|---|---|---|
| 🔎 **Search demand** | `run.py --search-demand --notify` | Students site lo em search chestunnaro (theme `inc/searchlog.php`, anonymous) chusi **content gaps → queue** (`output/search-demand-queue.json`). Meere review chesi topics rasi — auto-publish ledu. |
| 📉 **Rank trend** | `run.py --rank-trend --csv Pages.csv --notify` | GSC CSV ni **time-series** ga save chesi (roju/weekly) rising/decaying pages chupistundi; **traffic padutunna pages → refresh queue** (`output/refresh-queue.json`) + mee `--update` pipeline priority update. |
| 🤝 **Sponsor pipeline** | `run.py --sponsor-crm --notify` | Direct sales (highest revenue): roju **2 outreach targets** + overdue follow-ups + pipeline ₹/expected forecast + ready Telugu message templates. |

```bash
# one-time: GSC export unte (Search Console → Performance → Pages → Export)
python run.py --rank-trend --csv Pages.csv --notify     # roju/weekly cron

# sponsor pipeline start
python run.py --sponsor-targets                          # evarini contact cheyyali
python run.py --sponsor-add "Sri Coaching|coaching|Hyderabad|98480xxxxx|8000"
python run.py --sponsor-crm --notify --sponsor-templates # roju plan + messages
```

**v181 flags (anni):** `--search-demand` · `--search-import` · `--search-notify` · `--rank-trend` · `--rank-csv` · `--rank-window` · `--rank-notify` · `--sponsor-crm` · `--sponsor-targets` · `--sponsor-add` · `--sponsor-update` · `--sponsor-notify` · `--sponsor-limit` · `--sponsor-templates`

Honest note: search demand = **queued ideas**, rank trend = **evidence** (GSC data
unte matrame), sponsor loop = **manual sales** (messages meeru pampali). Ee loops
rankings/revenue ni guarantee cheyyavu — kaani prathi roju **em cheyyali** anedi
chupistayi.

---

## 4) Notification / verification commands (server lo)

```bash
cd ~/bot
.venv/bin/python run.py --status          # ee roju plan + stats
.venv/bin/python run.py --force           # ippude okka draft (approval ki Telegram)
.venv/bin/python run.py --guardian        # 15 checks (site · UI · SEO · ads · feed · theme)
.venv/bin/python run.py --readiness       # 100/100 system score (owner items pending ga chupistundi)
.venv/bin/python run.py --deploy-check    # server setup green-a?
.venv/bin/python run.py --index-status    # IndexNow / Google indexing keys verify
python run.py --search-demand   # v181: readers' searches → content gaps (queue)
python run.py --rank-trend      # v181: GSC time-series → decay → refresh queue
python run.py --sponsor-crm     # v181: roju sponsor outreach + follow-ups + forecast
```
CI/local lo anni suites: `python run.py --test-all` (124/124) ·
jsdom runtime: `node tests/runtime/jsdom_runtime_test.js` (177/177) ·
PHP lint: `node tools/php_lint.js` (85/85).

---

## 5) Nijam (honest) — edi code cheyyagaladu, edi meeru cheyyali

**Code + repo ready (verified):** theme zip (112 files · sha256 reproducible) ·
SEO bridge · static site · cron bot · guardian 15 checks · readiness 100/100 ·
`--deploy-check` **0 fail** · php-lint 85/85 · code/parity audit 0 errors.

**Mee accounts lo matrame jarugutundi (code valla kaadu):**
- [ ] Domain `studentup.in` + hosting + SSL
- [ ] WordPress install + **Application Password**
- [ ] **Gemini/AI key** (`aistudio.google.com` — free tier) → `.env`
- [ ] **Telegram bot token + chat id** (@BotFather → @userinfobot) → `.env`
- [ ] Google **Search Console** verify + `sitemap.xml` submit · **GA4** property
- [ ] **AdSense** apply → approve ayyaka `ADSENSE_CLIENT_ID` + `ADSENSE_APPROVED=1`
      → `python3 tools/build_policy_pages.py` (ads.txt live avutundi) + CMP ON
- [ ] (Optional) Oracle Always Free VM — 24×7 daemon + watchdog kosam
      (`DEPLOY_ORACLE_CLOUD.md`) — **MilesWeb cron tho kalipi vadakandi** (duplicates)

⚠️ Ee repo Google ranking / AdSense approval / revenue ki **guarantee ivvadu** —
gates mistakes ni taggistayi; final numbers mee GSC/AdSense accounts lo vastayi.

---

*Last updated: v175 · kit builder: `python3 tools/build_milesweb_kit.py` ·
detail docs: `DEPLOY_MILESWEB.md` · `GO_LIVE_CHECKLIST.md` · `docs/MILESWEB_SETUP_TELUGU.md`*
