# 🏆 StudentUp — MOTHAM SETUP GUIDE (v190)

> **Idi em doc:** mee site ni **world-class** ga nadapadaniki — **mee side cheyyalsina
> pani motham** (setup + daily rhythm + SEO + money + honest limits) — okate chota.
>
> **Nijam ga cheppali:** code/automation side **138 test suites + 8 audits** tho lock chesanu
> (nijaalu kinda "Verification" lo unnayi). Kani **Google ranking, traffic, AdSense approval,
> revenue** — avi Google + mee accounts + **time** batti untayi. Ee guide aa pani ni
> **systematic** ga cheyyadaniki, tappulu taggadaniki — guarantee icche doc kaadu.

---

## ⚡ TL;DR — 8 steps (2-3 hours, okkasari)

| # | Pani | Ekkada | Guide |
|---|---|---|---|
| 1 | Kit SHA verify | mee laptop | [B1](#b1-kit--sha-verify-5-nimishalu) |
| 2 | WordPress + **theme 1.9.37** upload → Activate | WP Admin | [B2](#b2-wordpress--theme-19.36-30-nimishalu) |
| 3 | **SEO bridge plugin** upload → Activate | WP Admin | [B3](#b3-plugins-15-nimishalu) |
| 4 | Bot → `~/bot` + `.env` keys (5 must) | cPanel | [B4](#b4-bot-setup-40-nimishalu) · [B5](#b5-env-keys--emi-pettali-exact-ga) |
| 5 | `--deploy-check` + `--check-wp` (0 fail) | Terminal | B4 |
| 6 | **Cron lines** (core 4 + daily + weekly) | cPanel | [B6](#b6-cron--mee-roju-anthaa-automatic) |
| 7 | SEO/analytics accounts (GSC · GA4 · IndexNow · push) | browsers | [B7](#b7-seo--analytics-setup-45-nimishalu) |
| 8 | AdSense path (≥20 posts tarvata) | AdSense | [B8](#b8-money--adsense-path) |

**Tarvata:** roju **Telegram ✅ tap** mattrame — migilinadi bot chestundi
([Part C](#part-c--daily-autopilot-247-em-jarugutundo)).

---

## PART A — Ippudu system lo emi undi (mee tool box)

| Engine | Em chestundi | Version |
|---|---|---|
| **Multi-link intake** | List lo **enni links ichina** → **prathi link ki veru draft** (source nunchi search + rewrite) | v187 |
| **Hook engine** | Prathi blog draft modata **"main enti"** lead (`su-hook`) + list hook headlines | v188 |
| **Daily list** | **Telugu** list (sections-wise, hook items, **mana blog links mattrame**) → expiry auto-out, kotha auto-in | v183–v187.2 |
| **Morning send** | 6:30 AM → Telegram + WhatsApp + `wa.me` click-to-forward | v189 |
| **`--daily` one command** | drafts → health → list → send (okka line cron) | v190 |
| **Board hygiene** | Expired out · stale sweep (120d) · same-recruitment supersede · daily diff | v184 |
| **Web quality** | 31-check deep theme matrix (perf · a11y · schema · PWA) | v185 |
| **Live audit** | 16 real-HTTP checks (SSL · robots · sitemap · schema · 404 · caching) | v186 |
| **Growth loops** | Search demand · rank decay · revenue loop · backlink engine · sponsor CRM · calendar | v181–v182 |
| **Guards** | Rank Math 100 gate · no-copy/originality gate · pin gate 100/100 (73 checks) · guardian | v18–v85 |

**Commands total:** **192 flags** (`python run.py --help`).

---

## PART B — FULL SETUP (okka sari cheyyali)

### B1) Kit + SHA verify (5 nimishalu)
```bash
# kit folder lo (milesweb-kit/)
sha256sum -c SHA256SUMS.txt          # 4 zips · anni "OK" ravali
```
| zip | sha256 (modati 16) | Ekkada |
|---|---|---|
| `studentup-theme-1.9.36.zip` | `eea8a787fa4095cc…` | WP → Appearance → Themes |
| `studentup-bot-cron.zip` | `d8b0cf611a0e2e89…` | cPanel → `~/bot/` |
| `studentup-seo-bridge-1.1.0.zip` | `2132fbe7d9653dfd…` | WP → Plugins |
| `studentup-static-site.zip` | `2430d8cc90065014…` | optional (static mirror) |

### B2) WordPress + theme 1.9.37 (30 nimishalu)
```
cPanel → Softaculous → WordPress install (domain)   # SSL already ACTIVE ✓
WP Admin → Appearance → Themes → Add New → Upload Theme → studentup-theme-1.9.36.zip
→ Activate
```
Activate cheyagane **automatic**: categories · menus · policy pages · schema · PWA shell · `.su-hook` styles.
**Tarvata:** WP → Settings → Permalinks → **Post name** → Save (okkasari).

### B3) Plugins (15 nimishalu)
```
WP Admin → Plugins → Add New → Upload Plugin → studentup-seo-bridge-1.1.0.zip → Activate
```
Idi **Rank Math fields** (focus keyword · SEO title · description · robots) ni bot nunchi
**verify + fill** chestundi — silent-fail ledu, publish ki mundu readback.

**Inka install cheyyali (WP lo):**
- **Rank Math SEO** (free) — Sitemap ON · Titles lo `%title% %sep% %sitename%`
- **AdSense** plugin — kani **apply tarvata mattrame** ([B8](#b8-money--adsense-path))
- Cache plugin **avaddu** (shared hosting lo bot traffic + cache = confusion) — theme already fast

### B4) Bot setup (40 nimishalu)
```bash
cd ~/bot
# (pata version unte: mv autoblog autoblog.bak  ← rollback safe)
# studentup-bot-cron.zip ni ikkada extract cheyandi (files ~/bot/ lo ne undali)
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env && nano .env      # ↓ B5 lo em pettalo chudu
.venv/bin/python run.py --deploy-check # ✅ 0 fail ravali
.venv/bin/python run.py --check-wp     # WordPress login ✅
```

### B5) `.env` keys — emi pettali (exact ga)
**TIER 1 — MUST (ivi lekapote bot pani cheyyadu):**
```ini
WP_SITE=https://studentup.in
WP_USERNAME=mee-wp-user
WP_APP_PASSWORD=xxxx xxxx xxxx xxxx      # WP → Users → Application Passwords
GEMINI_API_KEY=...                        # aistudio.google.com (free tier)
TELEGRAM_BOT_TOKEN=...                    # @BotFather
TELEGRAM_CHAT_ID=...                      # mee chat id (bot /start chesi chepthundi)
```
**TIER 2 — STRONGLY RECOMMENDED (SEO + money):**
```ini
GSC_SITE_URL=https://studentup.in/          # Search Console
GSC_SERVICE_ACCOUNT_FILE=private/gsc.json   # service account (or GSC_SERVICE_ACCOUNT_JSON)
INDEXNOW_KEY=...                            # run.py --index-key-gen (auto Bing/Yandex ping)
GOOGLE_CSE_API_KEY=... · GOOGLE_CSE_ID=...  # keyword verify (CSE)
PAGESPEED_API_KEY=...                       # performance audit
WHATSAPP_CALLMEBOT_URL=...                  # WhatsApp morning send (optional kaani best)
TELEGRAM_CHANNEL_CHAT_ID=...                # channel ki auto-post
```
**TIER 3 — OPTIONAL (backup providers → OKA provider fail aina bot aagadu):**
```ini
AI_FALLBACK_PROVIDERS=groq,openrouter,cerebras      # free tiers — chesukunte limit ledu
GROQ_API_KEY=... · OPENROUTER_API_KEY=... · CEREBRAS_API_KEY=...
ADSENSE_APPROVED=1        # approval tarvata (B8)
RADAR_ENABLED=1 · DAILY_MIN=6 · DAILY_MAX=20        # roju entha content
AUTOMATION_DRAFT_ONLY=1   # elappudu DRAFT — miru approve cheyyadam varaku publish ledu (safe)
```

### B6) Cron — mee roju antha automatic
```bash
crontab -e    # (MilesWeb lo: cPanel → Cron Jobs → lines paste)
```
```cron
# --- CORE (iva 4 pakka) ---
0 * * * *    cd ~/bot && .venv/bin/python run.py >> log/bot.log 2>&1
*/5 * * * *  cd ~/bot && .venv/bin/python run.py --approval-poll >> log/approve.log 2>&1
0 7 * * *    cd ~/bot && .venv/bin/python run.py --guardian >> log/guardian.log 2>&1
0 3 * * 0    cd ~/bot && .venv/bin/python run.py --site-audit >> log/audit.log 2>&1

# --- DAILY ROUTINE (6:30 AM: drafts → health → Telugu list → Telegram+WhatsApp) ---
30 6 * * *   cd ~/bot && .venv/bin/python run.py --daily >> log/daily.log 2>&1

# --- GROWTH LOOPS (weekly/daily) ---
30 8 * * *    cd ~/bot && .venv/bin/python run.py --search-demand --notify >> log/demand.log 2>&1
15 9 * * *    cd ~/bot && .venv/bin/python run.py --sponsor-crm --notify >> log/sponsor.log 2>&1
45 8 * * 1    cd ~/bot && .venv/bin/python run.py --revenue-loop private/adsense-pages.csv --revenue-notify >> log/revenue.log 2>&1
0 9 * * 1     cd ~/bot && .venv/bin/python run.py --calendar --calendar-apply --calendar-notify >> log/calendar.log 2>&1
30 9 * * 1    cd ~/bot && .venv/bin/python run.py --backlink --backlink-notify >> log/backlink.log 2>&1
0 10 * * 1    cd ~/bot && .venv/bin/python run.py --live-audit --live-notify >> log/live-audit.log 2>&1
45 3 * * 0    cd ~/bot && .venv/bin/python run.py --orphans >> log/links.log 2>&1
```
> `mkdir -p ~/bot/log` mundu cheyandi (lekapote cron output pothundi).
> Full list: `crontab.example` (comment tho vivaralu).

### B7) SEO + analytics setup (45 nimishalu)
1. **Search Console** (search.google.com/search-console) → property `https://studentup.in`
   → **sitemap submit**: `https://studentup.in/sitemap_index.xml`
2. **GA4** (analytics.google.com) → property → **Measurement ID** (`G-XXXXXXX`) →
   **WP Admin → StudentUp options → ga4_id** lo paste (consent-aware analytics auto).
3. **IndexNow**: `python run.py --index-key-gen` → key file site root lo →
   roju auto-ping (`--index-now` already pipeline lo).
4. **Push notifications**: `python run.py --push-keys` (VAPID keys generate) → WP options lo
   paste → site ki push subscribe bar (~1 nimisham). `--push-send` tho manual push kuda.
5. **Theme data push**: `python run.py --push-theme-data` (socials/contact/logo site ki).

### B8) Money — AdSense path
```
Ippati status:  --adsense-ready → 97% (28/29) · NOT READY
BLOCKER:        published posts ≥20 (ippudu 0 — miru Telegram ✅ tap cheyyali!)
```
1. **Roju 2–5 posts approve cheyandi** (Telegram ✅) → 20+ posts (7–10 rojulu)
2. `python run.py --adsense-ready` → **100% READY** vastundi
3. AdSense ki apply (adsense.google.com) → site verify → approval (days–weeks)
4. Approve ayyaka: `.env` lo `ADSENSE_APPROVED=1` + `ADSENSE_ENABLED=1` →
   `python run.py --ensure-adsense` → **ads.txt + Auto ads + slots** auto
5. **RPM report**: `python run.py --rpm-report` (roju/weekly) · `--revenue-check` · `--slot-lab`

> **Honest:** RPM (per-1000-views revenue) mee **traffic · niche · country · content type**
> batti untundi — industry lo chala wide range. Nenu number guarantee cheyyanu; levers
> (ad slots, high-CPC pages, sponsor deals, affiliates) ready ga unnayi — **measure cheyyandi**
> `--rpm-report` tho, mana gouging kaadu.

---

## PART C — Daily autopilot (24/7 em jarugutundo)

| Time | Em | Mee pani |
|---|---|---|
| **prathi hour** | Drafts prepare (sources search → rewrite → gates → WP **DRAFT**) → Telegram ki pampistundi | **✅ tap** (2–5 posts/roju) |
| **prathi 5 nimishalu** | Telegram approvals poll (✅ Publish / 🗑️ Delete) | — |
| **6:30 AM** | `--daily`: drafts → health → **Telugu list** → Telegram + WhatsApp + `wa.me` link | **WhatsApp group ki paste** (5 sec) |
| **7:00 AM** | Guardian health report | fail unte chudu |
| **roju** | Search-demand log (readers em adigaro) · sponsor CRM · push | — |
| **Monday 8:45/9:00/9:30** | Revenue loop · Calendar (auto-apply) · Backlink engine | 5 nimishalu chudu |
| **Monday 10:00** | Live audit (16 HTTP checks) | fail unte fix |
| **Sunday 3:00/3:45** | Site audit + media prune + orphan links | — |

**Mee roju pani: ~10 nimishalu** (Telegram taps + WhatsApp paste + evening oka look).

---

## PART D — SEO engine: "no copy + Rank Math 100" ela guarantee avutundi

| Gate | Em chestundi | Thaggakunda |
|---|---|---|
| **Source-backed** | Prathi article **nijamaina sources** nunchi (258 sources · 57 daily · official grid) | `SOURCE_*` gates |
| **No-copy / originality** | Rewrite + originality score (debate kaadu — **measure**) | `PUBLISH_ORIGINALITY_MIN` · `ORIG_LIVE_*` |
| **Fact check** | Numbers/dates source nunchi mattrame (fabricate ledu) | `FACT_STRICT` · reverification |
| **Rank Math** | Focus keyword · SEO title · desc · density · internal links → **100/100 gate** | `RM_TARGET=100` · bridge readback |
| **Pin gate** | 73 checks · critical 0 aithe ne publish | `--pin-check` |
| **Cannibalization** | Okate topic ki rendu posts raavu (audit + supersede) | `--cannibalization-audit` |
| **Keywords** | 12,344 keywords · 221 entities · 18 pillars · Trends/Suggest capture | `--keyword-audit` · `--score-keyword` |
| **Internal links** | Link graph + district hubs + contextual links | `--link-graph-apply` |
| **Schema** | Article · ItemList · JobPosting (**real org + future deadline unte mattrame**) | `SEO_SCHEMA_ENABLED` |
| **E-E-A-T** | Author team · trust box · source note · updated dates | `AUTHOR_TEAM` |

**Human review eppudu untundi** — bot **DRAFT** chestundi, miru ✅ cheyyaka publish avvadu
(`AUTOMATION_DRAFT_ONLY=1`). Adi feature, bug kaadu.

---

## PART E — Multiple links → separate drafts (mee favorite)

```bash
# Oka file lo entha links unna — prathi okkati VERU draft:
python run.py --links-file links.txt
python run.py --links "https://a.com/x, https://b.com/y"
python run.py --links-file links.txt --links-dry-run     # modata plan chudu
python run.py --links-file links.txt --links-notify      # Telegram summary
```
- Prathi link → **okka article** (aa source nunchi research + rewrite, hook lead tho).
- **Same link malli** isthe → **refresh** (duplicate post ledu).
- **Run ki max 10** (`LINK_INTAKE_MAX`) — roju 2–3 lists chaalu (spam pattern raadu).
- Report: `output/link-intake.json` (created/refreshed/failed — honest).
- Demo file: `output/link-intake-sample` leda oka `links.txt` create chesi try cheyandi.

---

## PART F — Google love (honest ga)

**Em chestunnam (correct direction):** sitemap + IndexNow ping · fresh content roju ·
News sitemap · schema rich results · fast theme (CWV-aware) · internal links · EEAT ·
no-copy original content · mobile-first + PWA.

**Nijam:** "First place guarantee" **evvaru ivvaleru** — Google official doc:
*"No one can guarantee a #1 ranking on Google."* Google engineer Maile Ohye: SEO ki
**4 nimishalu–1 year** padutundi. Ahrefs study: kotha pages lo **~1.74%** mattrame
year lopu top-10 ki vastayi (low-competition vi 1 month lo) — top-10 pages **~73% 3+ years
paatavi**. Ante: **roju posts + patience + quality** = rank. Bot aa pani chestundi; time
Google istundi — nenu kaadu, evvaru kaadu.

**Traffic build avvadaniki cheyyalsinavi (system chestundi):** roju 6–20 posts · WhatsApp
forwards · Telegram channel · push notifications · backlinks (weekly engine) · sponsor deals.

---

## PART G — Tappulu (mistakes) ledger — honest

| Risk | Guard | Mee side |
|---|---|---|
| Duplicate post | Same-source → refresh · supersede · cannibalization audit | — |
| Copy/paste content | Originality + ORIG_LIVE gates | — |
| Wrong facts/dates | Source-backed + reverification + FACT_STRICT | ✅ tap mundu chudu |
| Broken SEO | Rank Math 100 gate + bridge readback | — |
| **Publishing without review** | `AUTOMATION_DRAFT_ONLY=1` (default) | ✅ tap cheyyakapote publish ledu |
| Site down/broken | Guardian roju + live audit weekly | fail unte fix |
| **AdSense reject** | `--adsense-ready` 97% → **≥20 posts** taruvata apply | posts approve cheyyali |
| **ModSecurity currently OFF** | — (miru off chesaru) | site stable ayyaka **ON** cheyandi (security) |
| AI limit (free tier) | Fallback providers + multi-key rotation | keys add chesukovachu |
| Ranking/traffic slow | — | **time + consistency** (Google) |
| Zero revenue until ads/traffic | — | sponsors (`--sponsor-crm`) + affiliates (**earlier**) |

---

## PART H — Commands cheat sheet (192 lo mukhyamainavi)

```bash
# DAILY
run.py --daily                       # 6:30 AM one command (drafts→health→list→send)
run.py --forward-morning             # list + send mattrame
run.py --status                      # bot ippudu em chestundi

# DRAFTS
run.py --links-file links.txt        # prathi link ki veru draft
run.py --url https://source/x        # okka link nunchi draft
run.py --radar                       # breaking news sweep (districts + grid)
run.py --process-queue               # queue lo unnavi drafts ga

# HEALTH / VERIFY
run.py --deploy-check · --check-wp · --guardian · --site-audit
run.py --live-audit --live-url https://studentup.in --live-notify
run.py --readiness · --pin-check · --rm100

# SEO / KEYWORDS
run.py --keyword-audit · --score-keyword "ssc chsl" · --cannibalization-audit
run.py --gsc-sync · --gsc-refresh · --index-now · --index-status
run.py --link-graph-apply · --district-hubs-apply

# MONEY
run.py --adsense-ready · --ensure-adsense · --adsense-kit
run.py --rpm-report · --revenue-check · --revenue-loop · --slot-lab
run.py --rate-card · --sponsor-crm --notify · --backlink --notify

# GROWTH
run.py --calendar --calendar-apply · --rank-trend --csv Pages.csv
run.py --search-demand --notify · --trends · --breaking-feed

# SAFETY
run.py --rollback-post <id> · --rollback-backup · --corrections-audit
run.py --test-all                    # 138 suites (code health)
```

---

## PART I — Verification gauntlet (nijamaina numbers — 02 Oct 2026)

| Check | Command | Ippati result |
|---|---|---|
| Test suites | `run.py --test-all` | **141/141** ✔ |
| JS runtime | `node tests/runtime/jsdom_runtime_test.js` | **177/177** ✔ |
| PHP lint | `node tools/php_lint.js` | **94/94** ✔ |
| Theme deep audit | `python3 tools/theme_audit_deep.py` | **31 pass · 0 warn · 0 fail** |
| Parity (docs↔code) | `python3 tools/parity_audit.py` | **PIN-TO-PIN OK** |
| Code audit | `python3 tools/code_audit.py` | **0 errors · 0 warnings** |
| Deploy | `run.py --deploy-check` | **9 ok · 3 warn · 0 fail** (warn = optional keys) |
| Readiness | `run.py --readiness` | **100/100** (29/29 system · 10 owner-pending) |
| AdSense tech | `run.py --adsense-ready` | **97% (28/29)** — blocker: ≥20 posts |
| Kit integrity | `sha256sum -c milesweb-kit/SHA256SUMS.txt` | **4/4 OK** |

---

## PART J — Mee first-week checklist

| Roju | Pani |
|---|---|
| **1** | Steps B1–B6 (kit → theme → bot → cron) · `--deploy-check` 0 fail |
| **2** | B7 accounts (GSC sitemap · GA4 · IndexNow · push) · oka `links.txt` tho `--links-file` try cheyandi |
| **3–9** | Roju **2–5 posts ✅ approve** (Telegram) · 6:30 list ni WhatsApp group ki paste |
| **10** | `--adsense-ready` → 100%? → AdSense **apply** |
| **Tarvata** | Weekly cron loops chudu · `--rpm-report` measure · sponsors (rate card tho) |

---

*Last updated: v190 · ee guide code tho paatu update avutundi (`--test-all` lo docs pins lock unnayi).*
