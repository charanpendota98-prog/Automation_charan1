# 📋 MANUAL ADVANCED CHECKLIST — "Nenu manual ga em em cheyali"
### Website advanced ga run avvali · Posts ANI-PERFECT · Mistakes leku · Deep analyse + NotebookLM

**Ee file = mee haath tho cheyyalsina ANNI — exact order, exact commands.**
Bot automatic ga chesthunna varam rework cheyakapovadu — idi mee 15-min/day ritual matrame.

---

## PART 0 — ONE-TIME SETUP (Day 1 · ~90 min)

> 🏗 **Modata architecture clear chesukondi:** WordPress = website (MilesWeb) · Bot + portal =
> engine (Oracle leda MilesWeb cron). Rendu kalipi okate system — link = **WordPress REST API**.
> Diagram + 3 combos: **GO_LIVE_CHECKLIST.md → section A0**. ⛔ Bot ni rendu chotla schedule
> cheyyakandi (duplicate posts).


| # | Action | Where | Command / Step |
|---|---|---|---|
| 1 | Gemini keys (2-3 free) | aistudio.google.com | `.env` → `GEMINI_API_KEYS=k2,k3` |
| 2 | WP Application Password | wp-admin → Users | `.env` → `WP_USERNAME` + `WP_APP_PASSWORD` |
| 3 | Telegram bot | @BotFather | `.env` → `TELEGRAM_BOT_TOKEN` + `/start` chat id |
| 4 | Logo 512×512 | — | `.env` → `SITE_LOGO_URL=https://studentup.in/logo.png` |
| 5 | Bot install (server SSH) | server | `sudo apt install git && git clone ... /opt/studentup-src && sudo DOMAIN=exams.college.edu bash /opt/studentup-src/deploy/install-vps.sh` (DEPLOY.md Path A) |
| 6 | Bot auto-setup | server | `python run.py --setup && python run.py --polish && python run.py --plugins` |
| 7 | **WP 60-min customization** | wp-admin | `WP_ADVANCED_CUSTOMIZATION.md` Part 1-8 follow (theme, WP Code packs, Rank Math Local SEO location!, Cloudflare, Wordfence 2FA) |
| 8 | AdSense apply | adsense.google.com | Policy pages bot create chesthundi (`--ensure-adsense`); approval ayyaka `.env` lo `ADSENSE_APPROVED=1` + client id |

**Verify:** `python run.py --doctor` → 0 problems · `python run.py --deploy-check` → 0 fail

---

## PART 1 — PERFECT POST WORKFLOW (prathi post · 10–15 min)
### "Posts ani perfect ga, mistakes leku" — 4 steps

### Step A — DEEP RESEARCH (5 min)
```bash
python run.py --deep-research "TSPSC Group 2 2027 notification" \
    --research-year 2027 --research-limit 5
```
**Output lo ee varam cheyandi (1 min):**
| Report item | Meeku chadali? |
|---|---|
| `CONFIDENCE: 85/100` | 75+ = strong · 50–74 = verify more · <50 = official source add cheyandi |
| `⛔ Conflicts` | Sources **mattudu** (2 last dates!) → official site open chesi **correct date note cheyandi** |
| `❓ Gaps` | Sources lo ledu (fee/eligibility/official link) → official notification lo confirm cheyandi |
| `Sources [T1]/[T2]` | T1 (official) unte strong; T2 matrame unte official link add cheyandi |

Report: `output/deep/<topic>-<date>.md` + `.json` (browser/Excel lo open avtundi)

### Step B — NOTEBOOKLM DEEP LOOP (5–10 min) — "deep ga sources nunchi"
```bash
# 1) Evidence bundle + 5-pass prompt generate
python run.py --research-brief "TSPSC Group 2 2027 notification" --research-year 2027
# 2) Extended deep prompt (passes 6–8: year-over-year, ELI-12, gap priority)
python run.py --deep-research "TSPSC Group 2 2027 notification" --research-year 2027 --deep
```
**Mee haath tho (NotebookLM lo — 5 min):**
1. [notebooklm.google.com](https://notebooklm.google.com) open → **Import** → bundle file paste/upload
2. Prompt file content paste cheyandi (5 passes; `--deep` undi ante passes 6-8 kuda)
3. NotebookLM output lo: **Claim ledger + Conflict audit + Gap list** kanipisthundi
4. Output copy cheyandi → `brief.txt` file lo save cheyandi

**Re-run (merge + verify):**
```bash
python run.py --deep-research "TSPSC Group 2 2027 notification" \
    --research-year 2027 --notebooklm-brief brief.txt
```
→ Bot **validate chesthundi**: citations (S1, S2…) unnaa? 400+ words? Conflict audit undaa? Target year stated aa? → `NotebookLM cross-check: N cited claims` report lo vasthundi. **Uncited summary = block** (silent AI summary content lo ramigadu).

### Step C — POST GENERATE (bot auto · 3 min wait + 3 min review)
```bash
python run.py --url https://tspsc.gov.in/<official-notice-url> --notebooklm-brief brief.txt
```
**Bot automatic ga chesthundi:**
- Official source fetch + 2-3 extra sources (research)
- 100% original rewrite (Telugu-English)
- **🔬 In-Depth Analysis section auto-add** — verified facts table (✅/🏛/⚠️ status + source), ⛔ conflict box, ❓ gap box, confidence badge
- Quick Answer + TOC + FAQ + internal links + schema (JobPosting if eligible)
- Fact Guard (dates/counts source cross-check) + Originality floor 72% + QA gate 80/100
- **Perfect gates:** 2 different last dates? → BLOCK · conflicts? → BLOCK (live) · stale years? → BLOCK
- Ad slots (v43) + monetize blocks
- → **DRAFT lo WordPress** + Telegram ✅/🗑️ buttons

**Mee review (WordPress draft lo — 3 min):**
1. **Deep Analysis table** chudandi — ⛔/❓ unna varam official site tho fix
2. **Prathi date** official notification tho compare (5 sec/date)
3. Telugu readability — 2 lines parugu
4. Telegram lo **✅ Publish** (matrame approve)

### Step D — AFTER PUBLISH (2 min)
- Rank Math → GSC: index status check (auto)
- Telegram channel auto-post (configured unte)
- Deadline post unte: countdown badge verify

---

## PART 2 — WEEKLY LOOP (15 min/week)

| Day | Action | Command |
|---|---|---|
| Monday | GSC queries → queue priority | GSC → Performance → Export CSV → `python run.py --gsc file.csv` |
| Wednesday | Site health | `python run.py --site-audit` (findings chudandi) |
| Friday | Content quality + ads | `python run.py --content-audit` · GA4 → campaign `studentup.in` → ad CTR (< 0.3% → creative rotate) |

**Monthly:** `python run.py --rebuild-hubs` (authority hubs refresh) · UpdraftPlus backup verify

---

## PART 3 — ZERO-MISTAKE RULES (10 rules — bot enforces + mee verify)

| # | Rule | Bot enforcement | Mee verify |
|---|---|---|---|
| 1 | **One canonical date** per fact | 2 last-dates → LIVE BLOCK | Draft lo dates compare |
| 2 | **Conflicts never auto-picked** | ⛔ → LIVE BLOCK + visible box | Official site open chesi correct cheyandi |
| 3 | **No stale years** | Stale gate → LIVE BLOCK | Fresh source use cheyandi |
| 4 | **Every number source-backed** | Fact Guard flags | Big numbers (vacancies/fees) double-check |
| 5 | **NotebookLM briefs need citations** | Validator (400+ words, S-IDs, conflict audit) | Citations 2-3 open chesite verify |
| 6 | **Target-year lock** | `--research-year` → year-relevance tags | 2027 post ki 2026 numbers carry avvadu |
| 7 | **Draft-first + human approval** | DEFAULT_POST_STATUS=draft | Telegram ✅ matrame — rush lo publish kavali ledu |
| 8 | **Official link mandatory** | Gap check → visible ❓ box | `.gov.in` link article lo unnaa |
| 9 | **Corrections workflow** | Byline + report email in every post | Corrections report 24h lo fix |
| 10 | **Ad safety** | Sponsored label + rel + no-link-adjacency | Ad links click cheyandi (1 per month) |

---

## PART 4 — "LIVE-PUBLISH BLOCKED" vasthe? (panic ledu)

Message lo reason undi — exact ga fix cheyandi:

| Block reason | Fix |
|---|---|
| `DEEP GATE: source conflict on 'last-date-apply' (15/10 vs 20/10)` | Official site open chesi correct date note → article draft lo edit → re-publish |
| `DEEP GATE: article lo 2 different 'last date' values` | Article lo okka date matrame — vippudu delete cheyandi |
| `DEEP GATE: stale dates — current year dates levu` | Fresh official source ivvandi (2026/2027 date unna) |
| `FACT GUARD: unverified data` | Telegram message lo flagged items chudandi — official verify |
| `QA score < 80` | `run.py --score-post <file>` → fixes list → edit |
| `originality < 72%` | Kotha source add cheyandi / rewrite — copy kavali ledu |
| `EDITORIAL_REVIEWER empty` | `.env` lo `EDITORIAL_REVIEWER="Mee Name"` pettandi |

**Rule:** Block = bot mee ke save chesthundi. Override cheyaku (DEEP_GATE_STRICT=0 emergency kaani permanent kaadu).

---

## PART 5 — DAILY 10-MIN (rozu ritual)

```
0-2 min  : Telegram drafts chudandi (⚠️ flags unna mattam deep ga)
2-5 min  : 1 deep-research run (queue lo unna top topic ki)
5-8 min  : NotebookLM brief (2-3 topics varam ki okka deep loop chalu)
8-10 min : Approve 2-3 drafts (✅)
```

**Varam lo:** 10-15 perfect posts + 1 GSC cycle + 1 ad CTR check = "top website" flywheel 🔄

---

## ⚠️ Honest note
Perfect = **machine gates + human 5-min verify**. Gates mistakes ramigadu (conflicts/stale/dates/originality), kaani official numbers mee mata tho final check — AdSense/Google/reputation thartham lo idi matrame safety.

*Last updated: v64 (2026-09-18) — RANK MATH 100 engine (rm100) + theme 100x (options/TOC/schema/E-E-A-T/PWA) + PHP syntax gate: 12 checks · 50/50 suites · 122/122 runtime · readiness 100/100 (23/23)*

## PART 23 — v64: RANK MATH 100 + THEME 100x (options/TOC/schema/E-E-A-T/PWA)

```
RANK MATH 100 ENGINE (autoblog/rm100.py — deterministic, LLM ledu)
  title      : focus keyword MODATLO + year (kw tarvata) + power word + 40-62 chars
  meta       : kw + 110-156 chars
  slug       : keyword tokens (URL test)
  lede/TOC   : first paragraph lo kw · H2/H3 anchor ids + "విషయ సూచిక" jump links
  H2s        : 2+ H2 headings lo keyword
  density    : exact keyword 7-15 sarlu (0.4-0.8% — natural Telugu vakyalu)
  table/FAQ  : unna facts thone summary table · faq 3+ unte FAQ section
  links      : external (source url mattrame) + internal (site hub) — invent ledu
  transitions: Telugu connectives 30% sentences ki (checker laage kolichi)
  paragraphs : 120+ word paragraphs chunks ga split (text poadu)
  PROOF      : python run.py --rm100 → 33/100 → 100/100 (21 tests ✅)
GATE (pipeline) : rm100 → LLM refine (RM_REFINE_ROUNDS=2, RM_TARGET=100) → rm100 malli
                  → final score WP meta 'rank_math_seo_score' + Telegram
WEBSITE OPTIONS : WP Admin → StudentUp (tabs: Ads · Socials · Content · Advanced)
                  REST /wp-json/studentup/v1/options (GET public · POST manage_options)
                  bot --push-theme-data lo 'options' block (socials/adsense/flags)
THEME 100x      : inc/options.php (admin+REST) · inc/toc.php (auto TOC) ·
                  inc/schema.php (Organization/WebSite/SearchAction/Breadcrumb) ·
                  inc/author-box.php (E-E-A-T + last updated) · inc/pwa.php
                  (manifest + theme-color + preconnect + AdSense auto ads)
                  sticky bottom ad · copy link · reading progress · facts table style
PHP LINT GATE   : tools/php_lint.js (node php-parser · PHP 8 grammar) —
                  build_wp_theme.py lo hard gate (syntax tappu → zip ledu)
V64 BUG FIXES   : (1) 10 templates lo `?>` miss → white screen (site break!) — fix +
                  regex guard test · (2) TOC id/link mismatch (-2 suffix) — fix +
                  link⊆ids test · (3) paragraph split text loss — fix + words>=before test
TESTS           : tests/v64_test.py = 12 checks · run.py --test-all 50/50 ·
                  readiness 100/100 (23/23 system checks)
```

---

## PART 22 — v63: MISTAKE-FREE SEO (Rank Math REST bridge + meta verification)

```
PROBLEM  : WordPress REST default ga custom meta accept cheyyadu → bot rank_math_*
           fields pampiste 400 → bot meta lekunda post pettēdi → SEO fields khali
           (silent mistake — ee roju pattukunna gap)
FIX 1    : theme inc/seo-bridge.php — 10 keys REST ki register (show_in_rest +
           edit_post auth). Theme activate unte bot meta writes land avutayi.
FIX 2    : WordPressClient.verify_meta() — publish/update tarvata check:
           focus keyword/title/description land ayyaya? Ledu ante Telegram ⚠️ WAR +
           log + result lo seo_meta_missing (fix pointer: seo-bridge)
FIX 3    : UPDATE path lo kuda verify (purana posts refresh lo kuda same check)
POST EDIT: bot existing posts ni edit chestundi —
           · python run.py --update <id> [--update-source URL]  (manual)
           · auto_refresh (roju purana posts kotha research tho refresh)
           · URL/slug same untundi (SEO safe) · meta verify same
SEAL     : GET /wp-json/studentup/v1/theme-info → theme/version/seo_bridge/rankmath/
           adsense/posts (deploy tarvata okka call tho verify)
GSC/GA4  : GO_LIVE step 2a — GSC verify + sitemap submit + GA4 property (owner pani)
CMP      : GO_LIVE step 2c — AdSense → Privacy & messaging → Google-certified CMP ON
           (EEA/UK ads ki Google rule)
TESTS    : tests/v63_test.py = 7 checks · run.py --test-all 50/50
```

---

## PART 21 — v62: TOP WEBSITE READINESS ("asalu 100% advanced ga unda?")

```
RUN      : python run.py --readiness
OUTPUT   : score/100 + sections (CONTENT ENGINE · SEO · ADS & MONEY · AUTOMATION ·
           REAL SITE · OWNER PENDING) — prathi line lo verifiable number
ARTIFACTS: logs/readiness.json · output/readiness-<date>.md (markdown report)
EE REPO  : 100/100 system checks · 6 owner-pending (domain · WP+theme · Gemini ·
           Telegram · AdSense · Oracle VM)
NIJAM    : ee score = code side enta ready undo matrame. Google ranking, traffic,
           AdSense approval, revenue — Google + mee accounts + time. Ee report aa
           vatiki guarantee ivvadu (adi report lo kuda rasi undi).
EVIDENCE : blueprint 100/100 (TOP POST 🏆) · gates QA 80+/orig 72%+/deep ON ·
           radar 4x/day · 59 districts · Rank Math LIVE fields · slots 3/3 ·
           hooks 6/6 · theme zip fresh
TESTS    : tests/v62_test.py = 11 checks · run.py --test-all 50/50
```

---

## PART 20 — v61: REAL WEBSITE (WordPress + StudentUp theme) — "asalu site ela untundi?"

```
ANSWER  : Mee real website = **WordPress (MilesWeb)** + **mana custom theme** ee repo lo.
          preview/index.html lo chusina design NE live site ga untundi (టికర్ ·
          "విద్యార్థులు ఎక్కువగా వెతికేవి" · కార్డులు · ad slots · dark mode) —
          kaani DYNAMIC: bot post rasthe aa card + category count + breaking item
          automatic ga site lo kanipistayi.
THEME   : wordpress-theme/studentup/  →  zip: wordpress-theme/studentup-theme.zip (~29 KB)
INSTALL : 1) python tools/build_wp_theme.py
          2) WP Admin → Appearance → Themes → Add New → Upload Theme → zip upload → Activate
          3) Appearance → Menus → primary/mobile/footer assign (lekapote default
             Telugu menu vastundi)
          4) Settings → Reading → "Your latest posts" (front-page.php design home)
          5) python run.py --push-theme-data   → breaking/proof/deadline/house ads push
BOT LINK: POST /wp-json/studentup/v1/theme-data (WP_SITE + WP_USERNAME +
          WP_APP_PASSWORD, edit_posts chaalu) — roju breaking feed tarvata auto push
OPTIONS : studentup_breaking_json · studentup_proof_json · studentup_deadline_json ·
          studentup_house_ads · studentup_adsense_client · studentup_exam_url
FILES   : front-page (home order) · header (menu+టికర్) · footer (socials+links) ·
          single (article+ads+share+related) · archive/search/page/404 ·
          inc/breaking (feed + REST) · inc/ads (AdSense + house, SPONSORED label) ·
          inc/template (cards · proof tiles · countdown · breadcrumbs)
SPEED   : external JS library ledu (1 CSS + 1 JS) · lazy images · CLS-safe ad slots
NIJAM   : theme = mee design; WP plugins (Rank Math · AdSense) vaalla pani vaalle chestayi.
TESTS   : tests/v61_test.py = 14 checks · run.py --test-all 50/50
```

---

## PART 19 — v60: SITE GUARDIAN (eppatiki advanced ga — roju automatic check)

```
WHY      : "advanced ga untu undali" = manual gurthupettukovadam kaadu. Roju okkasari
           bot motham system ni chusi, edaina padipoyindi/desync ayithe Telegram lo
           cheptundi — silent regressions roju teliyali.
RUN      : python run.py --guardian            (ippude check)
           python run.py --guardian-notify     (report Telegram ki kuda)
BOT HOOK : roju GUARDIAN_HOUR (default 20 IST) tarvata okkasari automatic
           (state meta tho once/day — rerun ayina double report ledu)
CHECKS   : 12 — site files · first-look UI blocks (ticker/used/breaking/feed fetch/
           nav) · tiles ↔ tests/jsdom sync · robots+sitemap · ads.txt status ·
           breaking feed freshness · ad inventory validity · keyword/pillar lock
           (17 · 203 · 11,192 · 143) · menu wiring · storage · theme zip · .env readiness
SEVERITY : ❌ = system break (fix cheyyali) · ⚠️ = mee pani pending (creds)
           exit code: hard fail unte 1, warn-only unte 0
STATUS   : logs/guardian.json — chivari 14 runs history (gitignored)
NIJAM    : read-only audit — fix cheyyadu, cheptundi matrame. Fixes tests +
           builder nunchi vasthai (tiles bump, builder rerun, prune…)
TESTS    : tests/v60_test.py = 10 checks · run.py --test-all 50/50
```

---
## PART 18 — v59: FIRST LOOK (బ్రేకింగ్ న్యూస్ + విద్యార్థులు ఎక్కువగా వెతికేవి + పర్ఫెక్ట్ మెనూ)

```
WHY      : student site open cheyagane (3 sec lo) rendu kanipinchali —
           (a) ippude em jarigindi (బ్రేకింగ్), (b) naaku panikocchede (TS/AP jobs …)
ORDER    : టికర్ (breaing) → "విద్యార్థులు ఎక్కువగా వెతికేవి" 8 tiles → ప్రకటన (high
           visibility) → hero (countdown) → main (బ్రేకింగ్ section + grid)
TICKER   : verified feed nunchi; 18 గంటల rolling window (sweep lo kotha item
           lekuna chivari headlines nilabadtayi, paatavi expire) · feed khali aithe
           ticker HIDE (fake news ledu)
MOST-USED: టీఎస్ ప్రభుత్వ ఉద్యోగాలు · ఏపీ ప్రభుత్వ ఉద్యోగాలు · హాల్ టికెట్లు ·
           ఫలితాలు · వాక్-ఇన్ · సాఫ్ట్‌వేర్ · ప్రైవేట్ · ప్రస్తుతాంశాలు
           (ordinate bot nunchi vasthundi: autoblog/breaking.MOST_USED — okate source)
           prathi tile ki LIVE count ("ఎన్ని అప్డేట్‌లు") + one-tap filter
MENU     : హోమ్ · ఉద్యోగాలు▾ (TS · AP · కేంద్ర · ప్రైవేట్ · వాక్-ఇన్ · సాఫ్ట్‌వేర్ ·
           అవుట్‌సోర్సింగ్ · పార్ట్-టైమ్ · విదేశీ) · హాల్ టికెట్లు · ఫలితాలు ·
           బ్రేకింగ్ న్యూస్ (red dot) · స్కాలర్‌షిప్‌లు · ప్రస్తుతాంశాలు · పరీక్షలు▾ ·
           మరికొన్ని▾ — mobile panel kuda ade order
GRID     : TS/AP ప్రభుత్వ ఉద్యోగాలు modati cards (student-vadana order)
BOT      : python run.py --breaking-feed              (radar → feed + Telegram flow alage)
           python run.py --breaking-from file.json    (offline/approved list)
           radar run lo auto hook: news_radar sweep → breaking.publish()
HONESTY  : feed lo radar (Google News తెలుగు + 143 official sources) verified items
           matrame · item lekapote site "కొత్త verified బ్రేకింగ్ అప్డేట్‌లు లేవు" +
           "రాడార్ ప్రతి 6 గంటలకు చెక్ చేస్తుంది" ani cheptundi — fake/clickbait ledu
TESTS    : tests/v59_test.py = 12 checks · run.py --test-all 45/45 · jsdom 122/122
```

---

## PART 17 — v58: విదేశీ ఉద్యోగాలు (Abroad Jobs) — Tier-1 revenue unlock

```
PILLAR   : Abroad Jobs (17వది) — Gulf/abroad jobs · visa · IELTS/PTE · study abroad · NRI
WHY      : Tier-1 (US/UK/Gulf) ట్రాఫిక్ + high-CPC (visa, IELTS, education loan,
           consultancy) → AdSense RPM 3–5x + Raptive/Mediavine eligibility ki daari
CODE     : config CATEGORIES + priority 4 · pipeline rule (LIST MODATI — "గల్ఫ్
           ఉద్యోగాలు" → Abroad, Central kaadu) · Gemini CATEGORY_SEEDS ·
           14 sources (eMigrate/MEA/IELTS/Study abroad/Canada/UK…), 4 daily
SITE     : nav dropdown + chip "విదేశీ ఉద్యోగాలు" + mobile link + #grid card
           tiles: 17 content categories · 143 official sources · 11,192 keywords
KEYWORDS : top_post ENTITIES 188 → 203 (+15 abroad: Gulf/eMigrate/IELTS/PTE/Canada…)
           universe 10,682 → 11,192 (510 abroad keywords) · exam-mechanics intents skip
TOP_POST : LIVE_CATEGORIES lo 17 pillars (mundu 12 matrame — 5 pillars
           "Online Education" ki map ayyevi!) + abroad intent filter
ADVISOR  : Tier-1 gap unte — 'విదేశీ ఉద్యోగాలు (Abroad Jobs)' pillar posts cheyyamani cheptundi
CLASSIFY : "Dubai jobs", "IELTS exam date", "గల్ఫ్ ఉద్యోగాలు", "Canada work visa" → Abroad Jobs
AUDIT    : review lo pattina rendu issues fix —
           (1) robots.txt ippudu internal artifacts anni block chestundi (keyword CSV,
               dominance-plan, blueprint, v38/39/41, ads-preview, legacy-concept) +
               builder (build_policy_pages.py) nunchi auto-generate avutundi
           (2) keyword-universe-top200.csv ippudu engine nunchi generate (stale kaadu:
               10 Abroad rows top-200 lo) — test fail ayithe CSV stale ani artham
TESTS    : tests/v58_test.py = 12 checks · run.py --test-all 44/44 · jsdom 109/109
```

---

## PART 16 — v57: AD ADVISOR (eppudu e network ki apply cheyyali — AUTOMATIC)

```
CLI      : python run.py --ad-advisor [--traffic-csv ga4.csv] [--traffic-views 25k --tier1 0.5]
Traffic  : logs/traffic.json (GA4 CSV import leda manual) → .env (AD_MONTHLY_VIEWS) → CLI
Bot hook : roju ADVISOR_HOUR (default 10) tarvata okkasari — notify=True
Alerts   : kotha network threshold cross ayyaka Telegram (milestone ki okkasari)
           ADSENSE_APPROVED=1 ayyaka checklist alert (ads.txt status tho)
Next     : eligible lo best per-view value; leda next threshold dooram (views/sessions/Tier-1)
Publisher: AdSense ca-pub-… id MAREADU · Ezoic ade account vaadutundi · Raptive/Mediavine
           exclusive — vaalla tags, AdSense line ads.txt nunchi thiyyali (account migilipotundi)
State    : logs/ad_advisor_state.json (gitignored) · runtime data logs/ lo
```

---

## PART 15 — v56: AD NETWORKS (50k tarvata enti? 2x avutaya?)

```
tool     : tools/ad_network_plan.py --views 50k --tier1 0.30   (--json kuda)
threshold: Raptive 25k pageviews + ~50% Tier-1 · Mediavine 50k SESSIONS (≈65-80k PV)
           + Tier-1 majority · Monumetric 10k PV · Adversal/Revcontent 50k PV ·
           Ezoic no strict minimum (AdSense good standing) · AdSense no minimum
nijam    : header bidding add → +30-70% (automatic 2x KAADU) · Raptive/Mediavine 2-4x
           kaani EXCLUSIVE (AdSense replace) + Tier-1 share kavali
ads.txt  : ads/ads_txt_extra.txt lo partner lines paste cheyyandi → builder auto add
           (comments skip; placeholder state intact while unapproved)
order    : AdSense → direct sponsors (4-5x, ippude) → Ezoic → Monumetric → Raptive → Mediavine
```

---

## PART 14 — v55: ADS-ONLY REVENUE (ads.txt + ladder)

```
ads.txt  : preview/ads.txt — builder (tools/build_policy_pages.py) generate chestundi
           placeholder (honest) → ADSENSE_CLIENT_ID set ayyaka live line automatic
           google.com, pub-XXXXXXXX, DIRECT, f08c47fec0942fa0
           robots.txt: /ads.txt open + Mediapartners-Google allow (verify chesadu)
status   : autoblog/adsense_kit.ads_txt_status() → live | placeholder | warn | missing
ladder   : python tools/revenue_estimate.py --views 100000 --ads-only
           ads-only = AdSense + sponsor slots (leads/premium lekunda)
           1L views → ₹5,000–₹23,100 · 10L views → ₹46,000–₹1,82,400
nijam    : ads revenue = views × RPM — views perugakunda ceiling peragadu
```

---

## PART 13 — v54: HIGHEST REVENUE ENGINE (adi asalu pani)

```
LEADS  : exam_portal/leads table + POST /lead (CORS) → website "ఉచిత సమాచారం" ఫారం
         dedupe 24h · IP throttle 5/hour · honeypot spam trap · admin auth
         admin console: 📞 లీడ్లు panel (status: కొత్త → సంప్రదించాం → అమ్మాం → స్పామ్) + CSV
PREMIUM: advertise page lo 3 కొత్త products — స్పాన్సర్డ్ ఆర్టికల్ ₹8,000–₹15,000 ·
         లీడ్లు ₹150–₹400/లీడ్ (కనీసం 50) · బ్రాడ్కాస్ట్ ₹1,500
TIERS  : tools/revenue_estimate.py → 1) BASELINE (AdSense) 2) STANDARD (+ slots)
         3) ADVANCED (+ లీడ్లు/ఆర్టికల్స్/బ్రాడ్కాస్ట్/అఫిలియేట్) — 10k views: ₹16,050–₹64,350
SALES  : SALES_KIT_ADVERTISERS.md — WhatsApp/email టెంప్లేట్లు, objection handling, 90-day plan
దినచర్య: రోజూ 2 అమ్మకాల మెసేజ్లు + 1 షేర్ (15 నిమిషాలు) — ide revenue ni penchutundi
```

---

## PART 12 — v53: REVENUE CALCULATOR + GO-LIVE

```
Tool      : tools/revenue_estimate.py  (--views 10k / 50k / 1l / 1m / --json)
Source    : rate card LIVE ga preview/pages/advertise.html nunchi (okate chota prices)
10k views : ₹400–₹4,200/నెల   · 1L views: ₹5,000–₹23,100 · 3L: ₹15,000–₹61,200
Honesty   : RPM bands ₹40–₹250/1000 (Indian jobs/education 2026 benchmarks) ·
            house ads ₹0 · no-guarantee line output lo untundi
Deploy    : GO_LIVE_CHECKLIST.md — 5 owner panulu (domain/WP/Gemini/Telegram/Oracle) →
            .env → production-audit 0 blockers → MilesWeb + Oracle VM → UptimeRobot
```

---

## PART 11 — v52: PRIVATE ADS + MANA SONTA ADS (house)

```
Advertise page : preview/pages/advertise.html  (rate card ₹1,000–₹8,000/నెల, 3-step booking)
Private ad     : advertiser email/Telegram → admin "📢 ప్రకటనలు" → SPONSORED label tho live
House ads      : ads/house.json (StudentUp sevalu · quiz · exam) — sponsor lekapote slot fill
                 SPONSORED label veyyamu ("StudentUp · మా సేవ") · HOUSE_AD_ENABLED=0 tho off
Gaps           : paid sponsor unte ade mundu; house ad rotation lo turn teesukuntundi
Revenue plan   : AD_REVENUE_PLAYBOOK.md — 4 lines, levers, cheyyakudadu list
```
Rate card: leaderboard ₹4,000 · mid-article ₹3,500 · in-feed ₹3,000 · sidebar ₹2,000 ·
policy ₹1,000 · **full package ₹8,000/నెల**.

---

## PART 10 — v51: CATEGORY MENU + CRASH-PROOF DEPLOY

**Menu (owner list):** ఉద్యోగాలు dropdown = టీఎస్ · ఏపీ · కేంద్ర · వాక్-ఇన్ · సాఫ్ట్‌వేర్ ·
ప్రైవేట్ · అవుట్‌సోర్సింగ్ · పార్ట్-టైమ్ · **పరీక్షలు dropdown** = హాల్ టికెట్లు · ఫలితాలు ·
రానున్న పరీక్షలు · పరీక్షా చిట్కాలు. Mobile panel lo kuda ade 12 categories.
Grid lo **15 filter chips** (state + category + search kalipi pani chestayi); shareable links: `#cat-walkin`.

**Crash-proof (Oracle/VPS):**
```
systemd Restart=always        → process chachina 3 sec lo malli start
su-watchdog.timer (2 min)     → /healthz fail 3x → auto-restart + Telegram alert
                              → disk / memory / load / TLS expiry alerts too
tools/prune_media.py          → disk clean · backup.sh → nightly DB backup
website graceful degrade      → poll down aithe note chupistundi, page crash ledu
external: UptimeRobot → /healthz (VM motham down aithe kuda alert)
```
Ekkada emi run cheyyali + Oracle free-tier nijamaina limits (2 OCPU/12 GB new free
tenancies, PAYG ki 4/24, idle reclaim risk): **DEPLOY_ORACLE_CLOUD.md**.

---

## PART 9 — v50: ANNI CATEGORIES + MANUAL GATE + DAILY REFRESH

Full plan: **CONTENT_PLAN_DAILY.md**

```
16 pillars : TS/AP/Central jobs · Outsourcing · Walk-in · Private · Software ·
             Part-time · Scholarships · Upcoming Exams · Current Affairs ·
             Exam Tips · Hall Tickets · Results · Internships · Online Education
129 sources: 4x/day check (daily hot-list + rotation), prathi pillar ki watch
Category   : kotha pillar WordPress lo lenappudu bot ne create chestundi
             (wp.get_or_create_term) — manual work ledu
Manual gate: DEFAULT_POST_STATUS=draft + Telegram ✅ + QA 80 +
             originality 72% + deep conflict BLOCK
Refresh    : --auto-refresh 2 (roju) · --update <id> (manual) · refreshed_at track
SEO        : Rank Math fields (focus keyword/title/desc/social/robots) +
             canonical + OG + JSON-LD + quick-answer card + IndexNow ping
```
Rate cheyyalsina command: `python run.py --test-only v50_test`

---

## PART 8 — v49: MILESWEB / cPanel LO RUN CHEYYADAM

Full guide: **DEPLOY_MILESWEB.md**

```
Website (static or WordPress)  → public_html          (పని చేస్తుంది ✔)
Bot (Python)                   → cPanel Python App + cron (5 cronjobs base plan)
Exam portal (poll/admin/exam)  → passenger_wsgi.py  (MilesWeb "Setup Python App")
Storage                        → python tools/prune_media.py [--apply]
```
- Portal ni WSGI ga run cheyyadam valla same features: `/exam`, `/admin`, `/poll/today`,
  `/poll/vote`, ads API — `tests/v49_wsgi_test.py` lo 8 checks.
- GitHub Actions cron **optional** (free) kaani: default branch lo ne fire avutundi,
  15–45 నిమిషాలు delay avvochu, private repo free plan ki 2,000 min/month limit.
  Predictable kaavali ante MilesWeb cron better.
- Storage: site 276 KB · DB ~96 KB · 1 పోస్ట్/రోజు ≈ 6 MB/నెల → base plan 50 GB ki
  ఎన్నేళ్లైనా సరిపోతుంది. Inodes (file count) important — prune tool vaadandi.

---

## PART 7 — v48: POLICY PAGES + ADS NEVER-MISS

**Real pages (AdSense review & trust ki kavali):**
```
preview/pages/about.html · contact.html · privacy.html · disclaimer.html · editorial-policy.html
```
- Footer + topbar + dropdown links ivi — dead `#trust` anchor lu poyayi.
- Prathi page Telugu, mobile-clean, canonical + OG + JSON-LD + okka SPONSORED slot.
- Mallee build cheyyali ante: `.venv/bin/python tools/build_policy_pages.py`

**SEO files:** `preview/robots.txt` (Mediapartners-Google allow, /admin disallow) · `preview/sitemap.xml` (anni URLs real files) · `preview/favicon.svg`.

**Ads guarantee (daily posts lo ad miss avvadu):**
- Category match lekapoyina, active ad unte **fallback rotation** tho ad vestundi.
- `ads/rotation.json` lo "last shown" date — **andariki turn vastundi** (real partner ad demo placeholder ni outrank chestundi).
- Strict ga kavali ante `.env` lo: `AD_FALLBACK_ALWAYS=0` (category match unte matrame ad).
- Cap: policy (`max_personal_ads_per_post`) + env hard cap `MAX_PERSONAL_AD_SLOTS` (AdSense approve ayyaka auto 1).
- Dry run okkate chudali ante: `python run.py --ads` (rotation ni touch cheyyadu).

---

## PART 6 — v47: DAILY POLL + ADMIN ADS + TELUGU SITE

**Daily poll (website → exam portal):**
```
Admin console → (kotha exam create cheyyakunda) question bank lo questions add cheyandi
Website "ఈరోజు పోల్" → /poll/today (rotates daily: day.toordinal() % bank)
Vote → 1 IP = 1 vote/day · % bars + correct answer + explanation
```
- Bank peddaga aithe rojuki kotha prashna — exams laage questions update avutune untayi.
- Endpoint offline unte website "⚠️ పోల్ అందుబాటులో లేదు" ani clean ga chupistundi (broken UI ledu).

**Admin ads (owner control):**
```
Admin login → "📢 ప్రకటనలు" card → add / edit / delete
Save → ads/inventory.json (bot next post lo SPONSORED + rel=sponsored tho use chestundi)
```
- Validation: id/title/link(http-only)/type/layout/dates — javascript: & data: URLs block.
- Atomic write (.tmp + os.replace) — version/policy never overwritten.
- 5 ad types: college_banner · coaching · shop · service · sponsorship.

**Public site:** fully Telugu script (no Romanized mixing), trust section with live verified numbers, dev-facing demo text removed, daily poll widget, mobile-clean CSS.
