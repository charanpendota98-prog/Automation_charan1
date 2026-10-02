# 🚀 studentup.in — MilesWeb (cPanel) lo ZIP upload chesi LIVE (v186 · FINAL)

## ⚡ TL;DR — 40 nimushalalo live (ee 7 steps chaalu)

| # | Pani | Ekkada | Detail section |
|---|---|---|---|
| 1 | Kit download + sha verify | mee laptop | [§0](#0-modata-verify-30-seconds--zip-sha256) |
| 2 | Domain + **SSL ON** | cPanel → SSL/TLS Status | §1 (1-2) |
| 3 | WordPress install | cPanel → Softaculous | §1 (1) |
| 4 | **Theme zip upload → Activate** | WP Admin → Appearance → Themes | §1 (4) |
| 5 | **Bot zip → `~/bot`** + `.env` + `--deploy-check` | cPanel File Manager + Terminal | §2 |
| 6 | **Cron 4 lines** (core) | cPanel → Cron Jobs | §2 (4) |
| 7 | `--live-audit` → em fix kavalo chudu | Terminal | §3e |

```bash
# 1) sha verify (kit folder lo)
sha256sum -c SHA256SUMS.txt                 # 4 zips · anni OK ravali

# 5) bot setup (cPanel Terminal)
cd ~/bot && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
cp .env.example .env && nano .env            # WP_SITE · WP_USERNAME · WP_APP_PASSWORD ·
                                             # GEMINI key · TELEGRAM token+chat id
.venv/bin/python run.py --deploy-check       # 0 fail ravali
.venv/bin/python run.py --check-wp           # WordPress login test ✅

# 7) site live ayyaka — 16 checks
.venv/bin/python run.py --live-audit --live-url https://studentup.in --live-notify
```

**Tarvata roju rhythm:** bot `0 * * * *` cron → WP lo **DRAFT** → Telegram **✅ Publish** tap →
post live → `--forward-list` (WhatsApp groups ki) → weekly `--calendar` / `--revenue-loop` / `--rank-trend`.

Mee accounts lo onetime: Gemini key · Telegram bot · Search Console (+sitemap submit) · GA4 ·
IndexNow → push keys → (posts 20 ayaka) AdSense. Anni kinda checklist lo unnayi.

---

Ee doc = okka page lo motham. **Naalugu zips** — ekkadiki upload cheyyali anedi kinda table lo.
WordPress path + static path lo **okati matrame** select cheyyandi (⭐ WordPress recommended).
Anni zips `milesweb-kit/` folder lo unnayi (`python3 tools/build_milesweb_kit.py` tho malli build cheyyachu).

| # | Zip | Ekkadiki | Enti chestundi |
|---|---|---|---|
| 1 | `studentup-theme-1.9.35.zip` | WordPress → **Appearance → Themes → Add New → Upload Theme** | Mee site design + job card + Apply bar + schema + ads slots (theme activate ayinappude categories/menus/policy pages auto-create) |
| 2 | `studentup-seo-bridge-1.1.0.zip` | WordPress → **Plugins → Add New → Upload Plugin** | Rank Math fields ni REST tho verify chese bridge (theme lo already undi — veru theme vadithe matrame kavali) |
| 3 | `studentup-static-site.zip` | cPanel → **File Manager → `public_html/`** | Static site (23 files · PWA + ads.txt + sitemap tho) — WordPress path vadakapothe matrame |
| 4 | `studentup-bot-cron.zip` | cPanel → **File Manager → `~/bot/`** | Auto-blogger bot (cron: research → draft → Telegram approval → publish; guardian + growth loops) |

> **Okate path select cheyandi:** WordPress + theme (⭐ recommended) **leda** static site.
> Rendu kalipi `public_html` lo pettakandi (WordPress `index.php` ne serve avvali).
> Bot ni **MilesWeb lo okka chota matrame** schedule cheyandi (Oracle + MilesWeb rendu unte **duplicate posts**).

---

## 0) Modata verify (30 seconds) — zip sha256

```bash
sha256sum studentup-theme-1.9.35.zip      # leda: sha256sum -c SHA256SUMS.txt
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
4. **Appearance → Themes → Add New → Upload Theme** → `studentup-theme-1.9.35.zip`
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
# 6:30 AM — daily morning list (Telegram + WhatsApp automatic + click-to-forward):
30 6 * * * cd ~/bot && .venv/bin/python run.py --forward-morning >> ~/bot/log/morning.log 2>&1
0 3 * * 0      cd /home/<user>/bot && /home/<user>/bot/.venv/bin/python run.py --site-audit >> log/audit.log 2>&1
# v181 growth loops (optional — rendu in-bot daily hook tho automatic ga kuda jarugutayi):
30 8 * * *     cd /home/<user>/bot && /home/<user>/bot/.venv/bin/python run.py --search-demand --notify >> log/demand.log 2>&1
0 9 * * 1      cd /home/<user>/bot && /home/<user>/bot/.venv/bin/python run.py --rank-trend --csv private/Pages.csv --notify >> log/rank.log 2>&1
15 9 * * *     cd /home/<user>/bot && /home/<user>/bot/.venv/bin/python run.py --sponsor-crm --notify >> log/sponsor.log 2>&1
# v182 strategic loops (weekly):
45 8 * * 1     cd /home/<user>/bot && /home/<user>/bot/.venv/bin/python run.py --revenue-loop private/adsense-pages.csv --revenue-notify >> log/revenue.log 2>&1
0 9 * * 1      cd /home/<user>/bot && /home/<user>/bot/.venv/bin/python run.py --calendar --calendar-apply --calendar-notify >> log/calendar.log 2>&1
30 9 * * 1     cd /home/<user>/bot && /home/<user>/bot/.venv/bin/python run.py --backlink --backlink-notify >> log/backlink.log 2>&1
# v183 daily forward list (WhatsApp):
35 8 * * *     cd /home/<user>/bot && /home/<user>/bot/.venv/bin/python run.py --forward-list >> log/forward.log 2>&1
# v186 live site audit (weekly, Monday 10:00):
0 10 * * 1     cd /home/<user>/bot && /home/<user>/bot/.venv/bin/python run.py --live-audit --live-notify >> log/live-audit.log 2>&1
```
   (MilesWeb lo **unlimited cron jobs** unnayi; shared hosting lo daemon run avvadu —
   anduke bot antha cron-only ga design ayyindi.)
5. Flow: cron → bot research + draft → **WordPress lo DRAFT** → Telegram lo
   **✅ Publish / 🗑️ Delete** buttons → meeru tap chesthe ~5 nimishalaki post live
   (cron rhythm). **Emi mee approval lekunda publish avvadu.**

---

## 2b) App install (PWA) + Push notifications — reader ni tirigi techhe 2 levers 📱🔔

**Idi theme lo already build ayindi** — meeru cheyyalsindi config matrame:

**(a) App install (PWA) — "Download app" banner**
- Theme options: **Appearance → StudentUp → PWA = ON** (default ON).
- `inc/pwa.php` `manifest.webmanifest` + service worker + install prompt ni serve chestundi.
- Reader phone lo Chrome → site open → "Install app" / "Add to Home screen" prompt (own icon, fullscreen, offline shell).
- Static site path lo kuda `preview/manifest.webmanifest` + `sw.js` ready.

**(b) Push notifications (real Web Push · VAPID)**
```bash
cd ~/bot
.venv/bin/pip install pywebpush py-vapid        # one-time (lopaley unte skip)
.venv/bin/python run.py --push-keys             # VAPID keypair → push_keys.json (gitignored)
```
- Tarvata WP Admin → **Appearance → StudentUp** → *Push public key* field lo `push_keys.json` lo unna **public** key paste cheyyandi → Save.
- Reader ki prompt **2nd pageview / oka click tarvata** vastundi (Chrome abusive-permission penalty avoid; "No thanks" ante 30 rojulu malli adagadu).
- Pampadaniki:
```bash
.venv/bin/python run.py --push-send "Title|https://studentup.in/post-url|Short body"
.venv/bin/python run.py --push-send "..." --dry-run      # mundu chudu
```
- Subscriptions **sonta DB table** lo (`studentup_push_subs`) — `wp_options` kaadu (vela rows unna site slow avvadu).
- `410/404` vachina subscriptions automatic ga "expired" ga clean avutayi.
- **Best practice:** roju 1 push ekkuva vadakandi (breaking/result alert laantivi matrame) — spam chesthe unsubscribes vastayi.

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

## 3c) v182 — Plan · Money · Authority (moodu strategic loops)

| Loop | Command | Enti chestundi |
|---|---|---|
| 🗓 **Calendar** | `run.py --calendar --calendar-apply --calendar-notify` | 90-day plan: demand (readers) + decay (GSC) + trends + keyword-matrix gaps + ₹-RPM signals ni kalipi **pillar/cluster balance tho** slots. `--calendar-apply` top topics ni pipeline queue loki (so bot aa order lo rasi) |
| 💰 **Revenue loop** | `run.py --revenue-loop adsense-pages.csv --revenue-notify` | AdSense Pages CSV → **category RPM**, **money pages** (protect), **revenue leaks** (views unnayi RPM takkuva → slots/interlinks fix), **high-RPM topics** → calendar ki priority isthundi |
| 🔗 **Backlink/authority** | `run.py --backlink --backlink-assets --backlink-targets --backlink-notify` | White-hat link building: link-worthy assets (trackers/data/tools), outreach targets (colleges/libraries/news desks/YouTubers/communities) + stages/follow-ups/forecast + ready messages. **No paid links, no PBN, no blasts.** |

```bash
# weekly rhythm (cron lo pettachu)
python run.py --revenue-loop private/adsense-pages.csv --revenue-notify   # ad data → strategy
python run.py --calendar --calendar-apply --calendar-notify               # plan → queue
python run.py --backlink --backlink-notify --backlink-templates           # 3 outreach/day
```

> v182 flags: `--calendar` · `--calendar-days` · `--calendar-per-day` · `--calendar-apply` · `--calendar-limit` · `--calendar-no-universe` · `--calendar-notify` · `--revenue-loop` · `--revenue-notify` · `--revenue-min-views` · `--backlink` · `--backlink-assets` · `--backlink-targets` · `--backlink-add` · `--backlink-update` · `--backlink-notify` · `--backlink-templates`

Honest: calendar = plan (generation + approval gates appude) · revenue loop =
strategy input (ad code ni touch cheyyadu) · backlink = manual outreach
(meeru messages pampali; links/time guarantee ledu).

---

## 3d) v183 — Daily forward list (WhatsApp groups ki) 📲

Idi mee **#1 free traffic lever**: roju oka ready list → meeru WhatsApp groups /
status ki forward cheyyadam. Roju 08:35 ki cron tho build avutundi:

```bash
cd ~/bot
.venv/bin/python run.py --forward-list                  # print + save
.venv/bin/python run.py --forward-list --forward-send   # optional: Telegram/WhatsApp ki kuda
```

- Files: `~/bot/output/forward-list-YYYY-MM-DD.txt` + `~/bot/output/forward-list.txt`
  (cPanel File Manager → bot/output → Download → copy → groups lo paste).
- Sections: TS · AP · Central · Walk-in · **Outsourcing** · Job Melas · Software ·
  Private · Scholarships · Results · Hall Tickets · Current Affairs + 🆕 *IVVALTI* block.
- **Plain text** (WhatsApp HTML render cheyyadu) · links mee site vi (real permalinks).
- **v184 hygiene (site board + list rendu okate):** last date ayyipoyinavi out ·
  deadline lekunda **120+ rojula puratana** out · **same recruitment ki kotha post
  vaste puratana di out** (supersede). Kotha items ki 🆕 · close avutunna vaatiki ⏰.
- **Daily change report:** `output/forward-list-state.json` → roju *"🆕 4 kotha ·
  ❌ 3 out"*; CLI lo **enduku poyindi** (last date ayyindi / stale / kotha version)
  kanipistundi. Stale window marchali ante `.env` lo `OPPORTUNITY_STALE_DAYS=120`
  (0 = off) — theme board kuda `studentup_opportunity_stale_days` filter tho same.

v183 flags: `--forward-list` · `--forward-format` · `--forward-per-section` · `--forward-send` · `--forward-no-save`

## 3e) v186 — Live site audit (deploy ayyaka okkasari + weekly) 🌐

Site live ayyaka **modati pani** idi — 16 checks real HTTP tho:

```bash
cd ~/bot
.venv/bin/python run.py --live-audit --live-url https://studentup.in --live-notify
```

- ✅ pass aithe: SSL/redirects · robots+sitemap · ads.txt · security headers ·
  compression · homepage SEO/schema · PWA manifest+SW · sample posts · 404 · caching
  — anni correct.
- ❌ fail/warn vasthe: report lo **exact fix** untundi (`output/live-audit.md`) —
  e.g. "site-wide Disallow: /", "soft-404", "no H1", "no gzip", "thin content".
- Weekly cron lo kuda pettachu (kindha line) — hosting config marithe telustundi.

v186 flags: `--live-audit` · `--live-url` · `--live-posts` · `--live-timeout` · `--live-notify` · `--live-strict`

## 3f) v187 — Multi-link intake (list → separate drafts) 🔗

Mee daggara list unte (WhatsApp/notes lo ila):

```
1. **ECIL (310 ITI Trade Apprentice Posts)**
   - [https://www.ecil.co.in](https://www.ecil.co.in)
2. **SSC CGL 2026 (1000+ posts)**
   - [https://ssc.gov.in](https://ssc.gov.in)
```

Aa list ni `~/bot/links.txt` lo paste chesi:

```bash
cd ~/bot
.venv/bin/python run.py --links-file links.txt --links-dry-run   # modata plan chudu
.venv/bin/python run.py --links-file links.txt --links-notify     # prathi link → veru draft
```

- Prathi draft WordPress lo **DRAFT** ga vastundi → Telegram ✅ approve cheyyandi.
- Run ki max 10 links (`LINK_INTAKE_MAX`) — roju 2-3 lists chaalu.
- Report: `~/bot/output/link-intake.json` (created/refreshed/failed).
- WhatsApp list ipudu **Telugu lo** hook headlines (`*SSC CHSL 2026 ఉద్యోగాలు*`), **software English**,
  prathi item kinda mee site link. Per-item last-date line ledu; expiry lopala bot ne list nunchi teesestundi.

v187 flags: `--links-file` · `--links` · `--links-limit` · `--links-dry-run` · `--links-notify`

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
python run.py --calendar        # v182: 90-day editorial calendar (plan + files)
python run.py --revenue-loop adsense-pages.csv   # v182: ₹ strategy (RPM/leaks)
python run.py --backlink        # v182: authority/backlink plan (white-hat)
```
CI/local lo anni suites: `python run.py --test-all` (**132/132**) ·
jsdom runtime: `node tests/runtime/jsdom_runtime_test.js` (**177/177**) ·
PHP lint: `node tools/php_lint.js` (**86/86**) ·
CWV/a11y static audit: `python3 tools/cwv_audit.py` (10 pages · 0/0).

---

## 4b) Emem already build ayindi — proof tho (laptop · phone · app · ads · clicks · backlinks)

| Meeru adigindi | Ekkada implement ayindi | Proof / command |
|---|---|---|
| 🌐 **Advanced UI + frontend** | `wordpress-theme/studentup/` (113 files, v1.9.35): hero · job cards · quiz ring · bottom nav · dark mode · skeleton · critical CSS · minified assets | theme audit 0/0 · jsdom 177/177 · php-lint 86/86 |
| 💻 **Laptop lo neat** | responsive grid + 51 `@media` rules · desktop mega menu · keyboard nav (`studentup-cmdk.js`) · wide layouts | `python3 tools/cwv_audit.py` (10 pages) · jsdom |
| 📱 **Phone lo neat** | mobile bottom nav · tap targets · `viewport-fit=cover` · iOS zoom fix · sticky Apply bar | jsdom 177/177 · cwv_audit |
| ⬇️ **App download** | `inc/pwa.php` + `manifest.webmanifest` + `sw.js` + install prompt banner (§2b) | theme option PWA=ON |
| 🔔 **Push notifications** | `inc/webpush.php` (VAPID, own table) + bot `autoblog/webpush.py` + `--push-keys` / `--push-send` (§2b) | `--push-keys` → keys file |
| 💰 **Ads highest (RPM)** | `inc/ads.php` (slots) + `inc/slotlab.php` (A/B variant) + `inc/ads-txt.php` + `--revenue-loop` (category RPM · leaks · money pages) + `AD_NETWORKS_APPLICATION_KIT.md` | `--adsense-ready` (97%, blocker: posts) |
| 🖱️ **Highest clicks (CTR)** | `autoblog/ctr_boost.py` (`--ctr-boost`): GSC lo impressions unnayi kaani CTR takkuva unna queries → title/meta rewrite; title formulas + schema rich results | `python run.py --ctr-boost queries.csv` |
| 🔄 **Post updates (freshness)** | `autoblog/rank_trend.py` + `--rank-trend --csv Pages.csv` → decay score → refresh queue; calendar roju 1 refresh slot | `python run.py --rank-trend` |
| 🔗 **Backlinks (authority)** | `autoblog/backlink_engine.py`: 6 link-worthy assets + 10 target types + pipeline/forecast + Telugu templates (white-hat only) | `python run.py --backlink --backlink-assets` |
| 🤖 **Backend advanced** | 130 test suites · guardian 15 checks · readiness 100/100 · state.db dedupe · fact-guard · no-copy · human approval gate | `--test-all` · `--guardian` · `--readiness` |

---

## 5) Nijam (honest) — edi code cheyyagaladu, edi meeru cheyyali

**Code + repo ready (verified):** theme zip (**113 files** · 1016 KB · sha256 reproducible) ·
SEO bridge · static site (23 files) · cron bot (303 files) · guardian **14/15 OK**
(1 owner-pending) · readiness **100/100** · `--deploy-check` **0 fail** ·
php-lint **86/86** · `--test-all` **132/132** · code/parity/theme audit **0/0**.

**Mee accounts lo matrame jarugutundi (code valla kaadu):**
- [ ] Domain `studentup.in` + hosting + SSL
- [ ] WordPress install + **Application Password**
- [ ] **Gemini/AI key** (`aistudio.google.com` — free tier) → `.env`
- [ ] **Telegram bot token + chat id** (@BotFather → @userinfobot) → `.env`
- [ ] Google **Search Console** verify + `sitemap.xml` submit · **GA4** property
- [ ] **AdSense** apply → approve ayyaka `ADSENSE_CLIENT_ID` + `ADSENSE_APPROVED=1`
      → `python3 tools/build_policy_pages.py` (ads.txt live avutundi) + CMP ON
      ⚠️ Apply cheyyadaniki **≥20 published posts** kavali (ippudu 0) — bot roju
      drafts istundi, meeru Telegram lo approve chesthe avi publish avutayi
- [ ] **Push notifications**: `--push-keys` → public key ni theme options lo paste (§2b)
- [ ] **PWA/App**: theme option PWA=ON (default) — extra pani ledu
- [ ] (Recommended) **IndexNow** key → `.env` (`--index-status` tho verify) · **GA4** property
- [ ] (Optional) Oracle Always Free VM — 24×7 daemon + watchdog kosam
      (`DEPLOY_ORACLE_CLOUD.md`) — **MilesWeb cron tho kalipi vadakandi** (duplicates)

⚠️ Ee repo Google ranking / AdSense approval / revenue ki **guarantee ivvadu** —
gates mistakes ni taggistayi; final numbers mee GSC/AdSense accounts lo vastayi.

---

*Last updated: v186 · kit builder: `python3 tools/build_milesweb_kit.py` ·
detail docs: `DEPLOY_MILESWEB.md` · `GO_LIVE_CHECKLIST.md` · `docs/MILESWEB_SETUP_TELUGU.md`*