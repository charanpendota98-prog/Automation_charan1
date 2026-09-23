# 📋 MANUAL ADVANCED CHECKLIST — "Nenu manual ga em em cheyali"
### Website advanced ga run avvali · Posts ANI-PERFECT · Mistakes leku · Deep analyse + NotebookLM

**Ee file = mee haath tho cheyyalsina ANNI — exact order, exact commands.**
Bot automatic ga chesthunna varam rework cheyakapovadu — idi mee 15-min/day ritual matrame.

---

## PART 0 — ONE-TIME SETUP (Day 1 · ~90 min)

> 🏗 **Modata architecture clear chesukondi:** WordPress = website (MilesWeb) · Bot =
> engine (Oracle leda MilesWeb cron). Rendu kalipi okate system — link = **WordPress REST API**.
> Diagram + 3 combos: **GO_LIVE_CHECKLIST.md → section A0**. ⛔ Bot ni rendu chotla schedule
> cheyyakandi (duplicate posts).


| # | Action | Where | Command / Step |
|---|---|---|---|
| 1 | Gemini keys (2-3 free) | aistudio.google.com | `.env` → `GEMINI_API_KEYS=k2,k3` |
| 2 | WP Application Password | wp-admin → Users | `.env` → `WP_USERNAME` + `WP_APP_PASSWORD` |
| 3 | Telegram bot | @BotFather | `.env` → `TELEGRAM_BOT_TOKEN` + `/start` chat id |
| 4 | Logo 512×512 | — | `.env` → `SITE_LOGO_URL=https://studentup.in/logo.png` |
| 5 | Bot install (server SSH) | server | `sudo apt install git && git clone ... /opt/studentup-src && sudo DOMAIN=studentup.in bash /opt/studentup-src/deploy/install-vps.sh` (DEPLOY.md Path A) |
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

*Last updated: v81 (2026-09-19) — ULTIMATE SPEC GAP CLOSE (qual-noindex · rich tags · mobile tables · webp · orphans · health widget · search-track · HSTS): 63/63 suites · 164/164 runtime · readiness 100/100 · code audit 0/0 · parity 0/0 · theme audit 0/0 · theme v1.7.2*

## PART 26 — v67: DEEP AUDIT (expert/BA) + TOP-THEME HARDENING + 6/6 REVENUE SLOTS

```
DEEP AUDIT PASS 2 (tools/theme_audit_deep.py):
  · templates  : required files (index/functions/style/header/footer/single/page/archive/
                 search/404/theme.json/screenshot) · recommended (comments/sidebar/POT/readme)
                 · style.css header fields · theme.json v2 + layout settings
  · security   : ABSPATH guard prathi file lo · eval/base64/shell_exec/system/extract/unserialize
                 · file_get_contents(remote) → wp_remote_get · admin nonce (Settings API ok)
                 · REST permission_callback · register_setting sanitize_callback
  · escaping   : `echo $var` lines ki esc_*/int/kses wrap unda
  · perf       : script footer load · preconnect hosts · @import · style.css <120 KB
  · a11y       : skip-link · focus-visible · nav aria-label · button type · sr-only CSS ·
                 lang (language_attributes ok)
  · SEO        : multi-H1 templates · thin-page noindex (search/404) · canonical/og notes
  · ads/policy : 6 positions (leaderboard · in-article · in-feed · sidebar · below-content ·
                 anchor) · .su-ad spacing/margin CSS · AdSense code · ad-refresh code ledu
  · standards  : inc/*.php anni functions.php lo require (dead module pattukuntundi) ·
                 title-tag/post-thumbnails/nav menus supports · html5/responsive-embeds
  · i18n       : POT file + load_theme_textdomain · KPI row (ad positions · css KB · php files)

AUDIT TOOL BUG FIX (v67):
  comment stripper line-wise `//` cut cheyyadam valla `https://...` URLs comments la
  theesesaru → audit ki code kanipinchaledu. Ippudu **string-aware** stripper (quote state)
  → URLs safe, comments mattrame cut. Regression test v67_test lo undi.

THEME HARDENING (top-most level):
  inc/security.php NEW : security headers · XML-RPC off · ?author=N block · attachment →
                         parent redirect · comment link-flood guard · DISALLOW_FILE_EDIT
  comments.php NEW     : clean comments (Telugu labels, spam-safe, pagination)
  sidebar.php NEW      : widget area + STICKY ad (widgets lekapote render avvadu)
  readme.txt NEW       : WP standard readme + changelog
  languages/*.pot      : auto-generated (tools/build_pot.py → build lo regenerate)
  ads.php              : +below-content slot (280) · sidebar sticky class
  perf.php             : preconnect (pagead2 · doubleclick · GTM · GA) + wp_robots noindex
                         (search/404) + content-visibility body class (`su-cv`)
  style.css            : focus-visible · skip-link focus · ad spacing · sidebar widgets ·
                         comments · content-visibility (gated) · reduced-motion
  options.php          : +adsense_slot_below_content · comments_on · security_hardening ·
                         content_visibility (anni read avutunnayi — dead field ledu)

REVENUE (6/6 slots · privacy-safe):
  leaderboard (front) · in-article (content 3rd para, the_content filter) · in-feed (grids) ·
  sidebar sticky (archive/search + widgets) · below-content (single, article tarvata) ·
  anchor/sticky-bottom (mobile) — anni density cap + lazy + reserved height + consent tho.

TESTS            : tests/v67_test.py = 11 checks · run.py --test-all 53/53 ·
                   jsdom 138/138 · readiness 100/100 (27/27) · theme audit 0/0 ·
                   code audit 0/0 · parity 0/0 · php-lint 29/29 · zip 37 files ·
                   BA matrix docs/BA_REQUIREMENTS_MATRIX.md
```

---

## PART 25 — v66: THEME AUDIT + ADS REVENUE ENGINE + SEMANTIC CHECKS

```
THEME AUDIT (tools/theme_audit.py) — "theme lo mistakes" ni vetike static scanner:
  · undefined studentup_* function calls (WP core allowlist tho) → white-screen prevent
  · options read ayyi admin page lo declare avvakapovadam (read vs declared)
  · XSS patterns (`echo $var`, `$_GET` echo)
  · critical hooks: wp_head · wp_body_open · body_class · language_attributes ·
    wp_footer · `<main id="main">` · breadcrumbs · author box
  · ads readiness (adsbygoogle · reserved height · lazy · gating) · ads.txt · consent
  · exit 1 on errors → tools/build_wp_theme.py LO hard gate + guardian + readiness
  · run: .venv/bin/python tools/theme_audit.py --verbose   (24 files · 63 functions ·
    31 options) — --verbose lo info rows: dynamic prefix reads · dead admin fields ·
    unused functions (aa row lu errors kaavu, kaani user confusion pattukuntayi)

AD REVENUE ENGINE (theme — "highest ads ki miss avthunna" fix):
  · inc/consent.php      : Consent Mode v2 head lo (priority 1) — ad_storage/ad_user_data/
                           ad_personalization/analytics_storage default denied [EEA,GB,CH]
                           + granted fallback + ads_data_redaction + region sanitize (A-Z0-9)
                           + CMP snippet option (priority 2) → EEA/UK ads block avvavu
  · inc/ads-txt.php      : /ads.txt serve (template_redirect) — AdSense client nunchi
                           `google.com, pub-XXXX, DIRECT, f08c47fec0942fa0` auto line
                           → direct ad demand + reseller path open (noindex header)
  · inc/ads.php REWRITE  : AdSense-first render (client + slot unte unit) → house fallback
                           · kotha IN-ARTICLE ad: the_content filter (priority 20) — content
                             3rd paragraph tarvata okka unit (highest CTR) · density cap ·
                             lazy · idempotency marker su-ad-anchor-mid (double render ledu) ·
                             <3 paragraphs unte skip (thin content)
                           · page gating (admin/feed/404/search/attachment/policy out)
                           · density cap max_ads (default 4) · reserved min-height (CLS 0)
                           · lazy ads (leaderboard/anchor tappa) · ads_enabled master switch
  · inc/perf.php         : LCP preload + fetchpriority=high (single) · img decoding=async
                           · lazy-ads IntersectionObserver (rootMargin 300px, viewability)
  · inc/news-sitemap.php : /news-sitemap.xml (48h posts + news:publication/image) +
                           robots.txt lo news sitemap line (Google News/Discover eligibility)
  · options.php +12      : ads_enabled · adsense_slot_mid · adsense_slot_in_feed · ads_txt ·
                           max_ads · lazy_ads · ads_on_policy · consent_mode ·
                           consent_regions · consent_cmp_id · news_sitemap · deadline_json
  · style.css            : takeaways/entities/dark-mode/consent-note/ad-reserved blocks

SEMANTIC CHECKS (bot side — "blog rasthunnapudu inka chala check cheyali"):
  · post_gate lo kotha SEMANTIC group (7 checks): entity coverage (3+) · ముఖ్యాంశాలు box ·
    question-form headings 2+ · సంబంధిత అంశాలు cluster block · avg sentence ≤24 words ·
    current year · quick answer
  · DEEPER batch (12 checks — "inka chala check cheyali"): heading hierarchy (H1 ledu ·
    level-skip ledu) · heading ≤70 ch · markdown/escape leftovers ledu · list items ≤12 words ·
    table ≤5 columns (mobile) · job-guarantee/clickbait claims ledu (trust+policy) ·
    focus-keyword cannibalization ledu · slug ≤60 ch · meta lo CTA+number (CTR) ·
    secondary keywords body lo · content img width/height (CLS) · descriptive anchors ·
    FAQ answers 12+ words → **gate ippudu 67 checks**
  · gate fails → LLM refine hints ga (CONTENT/SEMANTIC/SEO) — writing loop lo ne fix
    (publish-time lo block kaadu; pin gate lo mattrame block)
  · rm100 fixers: fix_takeaways (ముఖ్యాంశాలు box) + fix_entities (సంబంధిత అంశాలు, internal
    search links) — content nunchi mattrame, invent cheyyadu
  · rm100.fix_faq BUG FIX: puratana guard (`<h3` 3+ unte skip) valla FAQ asalu rakapovadam
    → ippudu FAQ questions nijam ga content lo unnaya ani check chestundi (regression test)
  · trends queue match check: article keyword + trending queue overlap

TESTS            : tests/v66_test.py = 12 checks (audit detection ability tho!) ·
                   run.py --test-all 52/52 · readiness 100/100 (26/26 system checks) ·
                   pin gate 67 checks · zip 29 files 616 KB
```

---

## PART 24 — v65: PIN-TO-PIN GATE + GOOGLE VISIBILITY (Trends/Suggest)

```
PIN-TO-PIN GATE (autoblog/post_gate.py) — publish ki mundu 47 checks:
  CONTENT        : depth 1500+ · density · kw first para/body · FAQ · facts table ·
                   TOC links = heading ids · dev/demo text ledu (critical) ·
                   paragraphs · transitions · Telugu share · list items · dup H2
  SEO            : title 40-62 · kw modatlo (critical) · number · power word ·
                   meta 110-156 (critical) · slug tokens · Rank Math 100 (critical)
  SCHEMA         : Article (critical) · Breadcrumb · JobPosting (recruitment unte) ·
                   ItemList · publisher @id
  MEDIA          : featured image · ≥1200px (Discover) · alt lo kw · hotlink ledu
  LINKS          : internal 3+ · external authority (gov/edu) · ad links rel=sponsored
  ADSENSE        : slot present · house ratio ≤1/600 words · ads.txt
  FRESHNESS      : date ≤ today · deadline past kaadu (critical when set)
  GOOGLE READY   : inLanguage te · author · publisher · demand signal ·
                   near-duplicate ledu (critical) · unverified facts ledu (critical)
  BLOCK          : critical fail unte publish aaputundi (PIN_GATE_BLOCK=0 tho off)
  CERTIFICATE    : output/certificates/<date>-<slug>.md + .json (prathi post ki proof)
GOOGLE VISIBILITY (autoblog/trends.py):
  · Google Trends daily RSS (IN) — ET parser + regex fallback (unbad prefix feeds)
  · Google Suggest (autocomplete) — seeds: 17 pillars nunchi
  · Niche filter (TS/AP students) + demand score (0-100)
  · Topic queue: output/trend_queue.json (dedupe 3 rojulu · consume/next_topics)
  · radar_run lo 4x/day automatic (network lekapote silent skip)
  · CLI: python run.py --trends --trends-queue
BRAND GRAPH      : Article JSON-LD → author.worksFor #org · isPartOf #website ·
                   publisher @id → theme Organization schema tho okate entity graph
V65 BUG FIX      : seo.jobposting_obj — salary keys lekapote KeyError (publish crash)
                   → safe int() + regression test
TESTS            : tests/v65_test.py = 13 checks · run.py --test-all 51/51 ·
                   readiness 100/100 (25/25 system checks) · --pin-check 100/100
```

---

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
TESTS           : tests/v64_test.py = 12 checks · run.py --test-all 51/51 ·
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
TESTS    : tests/v63_test.py = 7 checks · run.py --test-all 51/51
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
TESTS    : tests/v62_test.py = 11 checks · run.py --test-all 51/51
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
          5) python run.py --push-theme-data   → breaking/house/indexnow push
BOT LINK: POST /wp-json/studentup/v1/theme-data (WP_SITE + WP_USERNAME +
          WP_APP_PASSWORD, edit_posts chaalu) — roju breaking feed tarvata auto push
OPTIONS : studentup_breaking_json · studentup_house_ads · studentup_adsense_client ·
          studentup_indexnow_key (v74: proof/deadline/exam_url options poyayi)
FILES   : front-page (home order) · header (menu+టికర్) · footer (socials+links) ·
          single (article+ads+share+related) · archive/search/page/404 ·
          inc/breaking (feed + REST) · inc/ads (AdSense + house, SPONSORED label) ·
          inc/template (cards · proof tiles · countdown · breadcrumbs)
SPEED   : external JS library ledu (1 CSS + 1 JS) · lazy images · CLS-safe ad slots
NIJAM   : theme = mee design; WP plugins (Rank Math · AdSense) vaalla pani vaalle chestayi.
TESTS   : tests/v61_test.py = 14 checks · run.py --test-all 56/56 · jsdom 164/164
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
           (17 · 203 · 12,344 · 143) · menu wiring · storage · theme zip · .env readiness
SEVERITY : ❌ = system break (fix cheyyali) · ⚠️ = mee pani pending (creds)
           exit code: hard fail unte 1, warn-only unte 0
STATUS   : logs/guardian.json — chivari 14 runs history (gitignored)
NIJAM    : read-only audit — fix cheyyadu, cheptundi matrame. Fixes tests +
           builder nunchi vasthai (tiles bump, builder rerun, prune…)
TESTS    : tests/v60_test.py = 10 checks · run.py --test-all 51/51
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
HONESTY  : feed lo radar (Google News తెలుగు + 180 official sources) verified items
           matrame · item lekapote site "కొత్త verified బ్రేకింగ్ అప్డేట్‌లు లేవు" +
           "రాడార్ ప్రతి 6 గంటలకు చెక్ చేస్తుంది" ani cheptundi — fake/clickbait ledu
TESTS    : tests/v59_test.py = 12 checks · run.py --test-all 45/45 · jsdom 138/138
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
           tiles: 17 content categories · 180 official sources · 12,344 keywords
KEYWORDS : top_post ENTITIES 188 → 203 (+15 abroad: Gulf/eMigrate/IELTS/PTE/Canada…)
           universe 10,682 → 12,344 (510 abroad keywords) · exam-mechanics intents skip
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
LEADS  : v74 — server/store ledu: contact ఫారం details WhatsApp message ga ready ayyi
         owner number ki open avutundi (validation + honeypot same, DB ledu)
         pipeline ippudu mee WhatsApp chat label/star (కొత్త → సంప్రదించాం → అమ్మాం)
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
House ads      : ads/house.json (StudentUp sevalu · quiz · services) — sponsor lekapote slot fill
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
su-watchdog.timer (2 min)     → website (HTTP+keyword) + bot freshness + disk/TLS check
                              → fail 3x ayite Telegram alert (auto-restart: bot timers ke)
tools/prune_media.py          → disk clean · backup.sh → nightly data backup
website graceful degrade      → static question/quiz (server ledu → down avvadu)
external: UptimeRobot → https://studentup.in/ (VM motham down aithe kuda alert)
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
Website (WordPress)            → public_html          (పని చేస్తుంది ✔)
Bot (Python)                   → ~/bot venv + cron (hourly run.py + */5 --approval-poll)
Live exam / WSGI               → v74 lo teesesam ✔ (cron-only — Setup Python App vaddu)
Storage                        → python tools/prune_media.py [--apply]
```
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

**Daily question (v74: website → server lekunda, browser JS):**
```
7-question bank → IST date tho rojuki okati rotate (day.toordinal() % bank)
Vote → localStorage 1 vote/day · correct answer + explanation instant reveal
```
- Question marchali ante bank file lo edit — server/API ledu kabatti down avvadu.
- Fake vote counts levu — honest by design (counts levu, answers untayi).

**Sponsor ads (owner control — WP Admin):**
```
WP Admin → StudentUp → Ads → add / edit / delete
Save → ads/inventory.json (bot next post lo SPONSORED + rel=sponsored tho use chestundi)
```
- Validation: id/title/link(http-only)/type/layout/dates — javascript: & data: URLs block.
- Atomic write (.tmp + os.replace) — version/policy never overwritten.
- 5 ad types: college_banner · coaching · shop · service · sponsorship.

**Public site:** fully Telugu script (no Romanized mixing), trust section with live verified numbers, dev-facing demo text removed, daily question widget (v74: server lekunda), mobile-clean CSS.


---

## PART 27 — v68: CODE-LEVEL BUG HUNT (bot + theme) + INSTANT INDEXING

```
AUDIT TOOL (kotha): tools/code_audit.py  — "errors 0 · warnings 0" = nijamaina bug ledu
  E1  config.<attr> undefined            → AttributeError (research path crash) — FIXED
  E2  sibling module attr typo           → AttributeError
  E3  bare `except:`                     → KeyboardInterrupt/SystemExit swallow
  E4  mutable default arg                → state leak between calls
  E5  duplicate dict literal key         → SILENT data loss (portal server.py 'name' — file v74 lo retire)
  E6  wp.<method>() lekapovadam           → publish crash
  E7-E8  AdSense markup rules             → in-article invalid format = RPM miss
  E9  .env.example drift                 → owner ki teliyani setting (20 keys add chesam)
  E10 PHP printf placeholder ↔ args      → PHP warning + wrong output (detection proof test)
  E11 Python `%` format arg count        → TypeError
  E12 bot push key ↔ theme option typo    → site lo update kanipinchadu
  W1  `except Exception: pass`           → 34 blocks (14 bot-critical + 20 modules) → log avutayi
  W2  os.environ[...]  W3 json.loads try lekunda  W4 write_text encoding ledu (Telugu mojibake)
  W5  network/subprocess timeout ledu (hang)  W6 AdSense unit rules  W7 news sitemap specs

FIXED BUGS (nijamaina impact):
  1) config.GEMINI_API_BASE ledu → deep-research path **AttributeError** (crash)  → define chesam
  2) 34 × `except Exception: pass` → failures **kanipinchalevu** ("anni aapthunnayi") → prathi okkati
     ippudu `log.debug/warning` tho reason cheptundi
  3) AdSense in-article unit: `data-ad-format="in-article"` (**INVALID**) velledi →
     ippudu `data-ad-format="fluid" data-ad-layout="in-article"` (correct spec) + in-feed kuda
  4) news sitemap lo `<lastmod>` ledu → Google News reject → ippudu loc tarvata lastmod
  5) portal server.py duplicate 'name' key → okati silent ga poyindi → clean (file v74 lo retire)
  6) IndexNow: key file ni **manual ga cPanel lo pettali** (lekapote submit fail) →
     ippudu theme `/<key>.key` ne serve chestundi (admin option, end-to-end automatic)
  7) .env.example lo 20 keys ledu (socials · contact · instant indexing · overrides)

KOTHA (trending ki): instant indexing
  · `python run.py --index-key-gen`  → kotha IndexNow key (hex) + .env line
  · `python run.py --index-status`   → SA / key file / openssl status
  · `python run.py --index-now URL`  → manual submit (IndexNow + Google Indexing)
  · publish appudu automatic: IndexNow (Bing/Yandex) + Google Indexing API (JobPosting pages,
    Google officially support chese use case — Search Console lo SA ni Owner ga add cheyandi)
  · RS256 signing: `cryptography` leda `openssl` CLI (dependency ledu; test real signature verify)

PROOF: tests/v68_test.py 19 checks (audit clean · bug locks · detection ability fixtures ·
  CLI smoke battery 10 commands · real RSA-2048 sign→verify) · run.py --test-all 55/55 ·
  readiness 100/100 (28/28) · theme audit 0/0 · code audit 0/0 · parity 0/0 · php-lint 29/29 · zip 37 files
HONEST: instant indexing = notification, **ranking guarantee kaadu** (Google decide chestundi).
```


---

## PART 28 — v69: THEME STANDARDS PASS 3 + PARITY AUDIT (pin-to-pin)

```
NIJAMAINA BUG (fix): style.css `Version: 1.0.0` vs `STUDENTUP_VERSION 1.3.0`
  → WordPress theme version style.css nunchi chaduvutundi (theme screen · child theme ·
    cache-busting) → ippudu 1.5.0 rendu chota + build gate check (audit ERROR).

THEME TOP-LEVEL STANDARDS (ippudu unnai, audit lo lock):
  · editor-styles + wp-block-styles + assets/css/editor.css  (block editor parity)
  · post_class() article loops lo (plugin/CSS compatibility)
  · aria-current="page" nav filter (a11y)
  · no_found_rows custom WP_Query lo → 2 extra SQL queries taggayi (shared hosting perf)
  · readme.txt Stable tag 1.5.0 + changelog · version parity · admin nonce checks
  · author.php (E-E-A-T: avatar · bio · article count · profile + editorial-policy links)

PARITY AUDIT (kotha tool: tools/parity_audit.py) — "emi miss avvakoodadu":
  P1 CLI ↔ docs          : run.py flags 92/92 README/MANUAL/GO_LIVE lo (7 miss → fix)
  P2 modules             : autoblog 43 modules · dead 0 (import ledu ante engine pani cheyyadu)
  P3 preview links       : preview/**/*.html local links anni nijamaina files ki
  P4 preview meta        : deploy ayyina pages lo title/description/canonical/robots/og
  P5 index files         : robots.txt → sitemap · sitemap URLs ↔ files · ads.txt · favicon
  P6 tools               : tools/*.py prathi script doc leda test lo reference
  P7 placeholders        : TODO/FIXME/lorem ledu (shipped surfaces — comments tho pattu)
  P8 counts              : suites ↔ preview tile ↔ jsdom ↔ README

AUTOMATIC (v60 rule): guardian lo code_audit + parity_audit checks (13/15 = 2 warn-only) ·
  readiness lo +1 check → 100/100 (28/28)

PROOF: tests/v69_test.py 18 checks (parity detection fixture to) · --test-all 55/55 ·
  jsdom 138/138 · code audit 0/0 · parity 0/0 · theme audit 0/0 · php-lint 29/29 ·
  zip 37 files 629 KB · theme v1.5.0

## PART 29 — v70: PUBLIC SURFACE CLEANUP (proof/developer text ledu) + 100% verification

**Enduku:** mee directive — "100% ధృవీకరించి, తర్వాతే ప్రచురణ … i dont want these all things
no use so remove". Verification-proof block (tiles · gates · honest note) site meeda
kanipisthe visitor ki adi **developer text** — anduku anni public surfaces nunchi teesesaru.

EMI TEESESARU (public surfaces):
  preview/index.html : trust/qgate section (2863 chars) + qtile/vsteps CSS · mobile panel links
                       → pages/editorial-policy.html · pages/contact.html · pages/privacy.html
  theme (studentup)  : front-page hero-proof tiles · studentup_proof_tiles() · option proof_json ·
                       breaking.php REST param 'proof' · hero-proof CSS · README-THEME proof row
  policy pages       : builder notes lo developer text remove (disclaimer · advertise)
  preview root       : v38/v39/v41/legacy-concept/ads-preview/top-post-blueprint.html +
                       dominance-plan-90-days.md → docs/design-archive/  (website meeda serve avvadu)

EMI MIGILINDI (visitor-facing — user cheppinattu): per-post trust note (sources + last updated) ·
  corrections email links · content.

ENFORCEMENT (silent ga malli ravakoodadu):
  guardian  counts_sync  : suites count ↔ README + public surfaces lo developer text ledu
  readiness c_counts_sync: iddari madhya (28 checks lo okati)
  parity P8              : docs claims + public-surface developer-text ban
  jsdom                  : 2 clean-checks (preview lo dev strings ledu)
  v58/v60/v68/v69 tests  : reworked — public-clean assertions

NIJAMAINA BUG (ee cleanup lo pattukunnadi + fix):
  autoblog/wp_theme_sync.py build_payload() nunchi 'options' + 'deadline' blocks + 'return out'
  poyayi (proof block tho pattu) → daily hook khali payload pampedi (options/deadline/indexnow
  sync aagipoyedi). Ippudu restore + 'proof_json' mapping remove.

PROOF (v70): tests/v70 lock — --test-all 55/55 · jsdom 138/138 · readiness 100/100 (28/28) ·
  guardian 14/15 (1 warn-only env) · code audit 0/0 · parity 0/0 · theme audit 0/0 · php-lint 29/29 ·
  zip 37 files 628 KB · theme v1.5.0 · proof doc: output/v70-proof-2026-09-18.md

## PART 30 — v71: STUDENTS INTERNET CENTER + CLEAN MONETISATION (English-first)

**Your brief:** neat English where a premium site needs it, Telugu only where it helps; explain the
application-help service properly; keep rates off the website (deal personally); replace the
newsletter form with WhatsApp/Telegram join; smaller mobile icons; floating rail that comes and
goes every 2 minutes so it never covers the article text.

WHAT CHANGED
  Homepage   : "Students Internet Center (TS & AP)" card — call → WhatsApp documents → PDF back,
               plus a green WhatsApp CTA box (opens your WhatsApp), call + email fallback.
               Sidebar "Advertise" rate-card card deleted.
               Newsletter form deleted → "Join on WhatsApp/Telegram" block (2 buttons + honest note).
  Partner page (pages/advertise.html): premium English page — placements, policy, house-ads note,
               "rates & availability shared personally". No prices, no table, no booking flow.
  Rate card  : autoblog/rate_card.py (5 slots ₹1,000–₹4,000 + full package ₹8,000 + 3 premium
               services). `python run.py --rate-card` prints the WhatsApp-ready card.
  Lead engine: form moved to pages/contact.html (v74: /lead API poyindi — WhatsApp-compose,
               honeypot + phone validation same,
               English labels). Homepage keeps the lead engine via the join block links.
  Social rail: shows 9 s → slides away → returns every 2 minutes; ✕ = hide now (2 min later back),
               ‹ = show now; Escape hides; hover/focus holds it open; reduced-motion respected.
  Mobile     : social chips 34 px (31 px < 400 px), tighter mobile-nav icons, full-width join CTA.
  Theme      : v1.6.0 — inc/cta.php (Internet Center + join on every page), inc/editor.php +
               assets/css/editor.css (block-editor parity), style.css ↔ STUDENTUP_VERSION ↔
               readme.txt Stable tag kept identical by the audit.

AUTOMATIC (v60 rule): guardian `counts_sync` · readiness `c_counts_sync` · parity **P8** (suites +
jsdom count from the jsdom `EXPECTED_CHECKS` constant) · jsdom drift guard · theme audit pass 3.

PROOF (v71): --test-all 55/55 · jsdom 138/138 · readiness 100/100 (28/28) · guardian 14/15
  (1 warn-only owner env) · code audit 0/0 · parity 0/0 · theme audit 0/0 · php-lint 31/31 ·
  zip 39 files 633 KB · theme v1.6.0 · proof doc: output/v71-proof-2026-09-18.md

```

## PART 31 — v72: QUALIFICATION FILTER · HEADER SEARCH · PWA INSTALL · CLEAN COPY

**Your brief:** బ్రేకింగ్ న్యూస్ అవసరం లేదు (teeseyandi) · internal metrics (keywords/sources/districts)
public ga vaddu · విద్యార్హత ప్రకారం ఉద్యోగాలు automatic ga filter avvali (10th · 10+2 · ITI ·
Diploma · Degree · PG · B.Tech) — WordPress lo kuda, manual tagging lekunda · menu pakkana neat
search · mobile lo app-laga install · colorful premium look, text/background contrast break avvakoodadu.

WHAT CHANGED
  Site copy  : బ్రేకింగ్ టికర్ + section + nav/mobile links + JS + CSS — public sitenunchi poyayi.
               Hero proof-stats (12,344 keywords · 180 sources · 59 districts) mariyu topbar/footer
               district lines teesesaam. "నమూనా/DEMO" maatalu public pages/theme nunchi clean.
  Filters    : Homepage `.qrow` chips — అన్నీ · 10వ తరగతి · ఇంటర్ (10+2) · ఐటీఐ · డిప్లొమా · డిగ్రీ ·
               పీజీ · బీటెక్ · ⏳ 7 రోజుల్లో ముగిసేవి. `applyFilter()` qual + search + category ni
               kalipi pani chestundi, `#qcount` lo "N అవకాశాలు" chupistundi. `data-last` nunchi
               "⏳ N రోజుల్లో ముగుస్తుంది" badge; గడువు ముగిసినవి `.expired` (default ga hide).
  WordPress  : `inc/qual-filter.php` — post save lo title+content nunchi auto tag (`studentup_qual`),
               bot REST meta (priority), purana posts ki admin batch + `wp studentup-qual-backfill`,
               front-end `?qual=degree` server-side `WP_Query` filter, chips lo counts (15 min cache).
               Menu pakkana 🔍 search panel (Enter / `/` shortcut, mobile menu lo link).
  PWA        : `manifest.webmanifest` + `sw.js` (offline page + repeat-visit speed) +
               "⬇️ యాప్గా ఇన్స్టాల్ చేయండి" button (Android `beforeinstallprompt`, iPhone Share hint).
               Theme: `inc/pwa.php` SW ni `?studentup_sw=1` tho serve chestundi (`Service-Worker-Allowed: /`)
               — kotha rewrite rules/server config avasaram ledu.
  Bot        : `autoblog/qual.py` (slug/keyword parity with theme) — pipeline meta lo `studentup_qual` +
               `studentup_last_date` add chestundi, `verify_meta` lo land ayyaya ani check chestundi.
  Theme      : v1.7.0 — qual-filter · studentup-pwa.js · header search · closing badges · options
               (breaking_enabled default OFF · qual_filter · install_prompt) · contrast/overflow rules.

HOW IT STAYS AUTOMATIC
  Every new post   : save_post → auto tag (bot value unte adi priority) → chips lo ventane kanipistundi.
  Every old post   : admin page load (20/batch) · `wp studentup-qual-backfill --limit=500`.
  Every publish    : bot meta + verify + Telegram WAR (tag land avvakapote telustundi).
  Every change     : guardian `first_look_ui` (search/అర్హత/install + copy clean) · readiness
                     `c_first_look` · parity P8 (jsdom count) · jsdom drift guard · v72 suite (20 checks).

VERIFY
```
python run.py --test-all                     # 56/56 suites
node tests/runtime/jsdom_runtime_test.js     # 164/164 browser checks
python run.py --readiness                    # 100/100 · python run.py --guardian
python tools/parity_audit.py                 # PIN-TO-PIN · python tools/code_audit.py
node tools/php_lint.js                       # 32/32 PHP files · python tools/build_wp_theme.py
```
**Note:** themeలో ఏ మార్పు చేసినా `--test-all` కి **ముందు** `python tools/build_wp_theme.py`
(zip fresh kaavali) — theme audit/zip checks adi enforce chestayi.

OWNER STEPS (v72)
1. WordPress lo theme 1.7.1 activate chesi, *StudentUp → కంటెంట్* lo chips + అర్హత sections chudandi
   (PART 32 lo v72.1 detail undi).
2. Purana posts ki okasari `wp studentup-qual-backfill --limit=500` (leda admin page open cheyandi).
3. బ్రేకింగ్ న్యూస్ kavali ante — *StudentUp → కంటెంట్ → బ్రేకింగ్ న్యూస్ సెక్షన్ ON* (default OFF).
4. Phones lo "యాప్గా ఇన్స్టాల్" button test cheyandi (Android Chrome + iPhone Safari).

PROOF (v72.1): --test-all 57/57 · jsdom 162/162 · readiness 100/100 (28/28) · guardian 14/15
  (1 warn-only owner env) · code audit 0/0 · parity 0/0 · theme audit 0/0 · php-lint 32/32 ·
  zip 41 files 642 KB · theme v1.7.1 · proof doc: output/v73-proof-2026-09-18.md

No guarantee: rankings, traffic, AdSense approval and revenue depend on Google + your accounts +
time. Everything measured in this pass is code-level (tests · audits · readiness), nothing more.

```

## PART 32 — v72.1: అర్హత SECTIONS · ALWAYS-VISIBLE APP DOWNLOAD · CLEAN PUBLIC COPY

**Mee follow-up brief:** "ప్రత్యక్ష పరీక్ష" wording/CTA avasaram ledu → remove · coverage topbar line
(33/26 జిల్లాలు) remove · 7-విషయాల demo article motham remove · hero stats manaki mattrame ·
"ABC/ట్యూషన్/స్టేషనరీ" demo ads → nijamaina "మీ ప్రకటన ఇక్కడ" slots · hero countdown fake date
vaddu · App డౌన్‌లోడ్ button prathi visit lo (mobile first) · **అర్హత ప్రకారం ఉద్యోగాలు విభాగాలుగా,
manual tagging lekunda automatic** · text/background clash ledu, mobile lo fast + neat.

WHAT CHANGED (site)
  Copy clean : coverage topbar (33/26 జిల్లాలు line + policy links strip) motham teesesaam ·
               hero hero-proof stats · "ప్రత్యక్ష పరీక్ష" → "ఆన్‌లైన్ పరీక్షలు" ·
               7-విషయాల demo article (QUICK ANSWER + checklist + share buttons) remove.
  Ads        : fake advertisers (ABC అకాడమీ/కళాశాల · ట్యూషన్ · స్టేషనరీ + example.com links)
               → house "స్లాట్ ఖాళీ · మీ ప్రకటన ఇక్కడ" creatives (SPONSORED label + Partner page CTA).
  Countdown  : hardcoded sample date → `preview/data/deadline.json` (bot `--push-theme-data` rasi
               pettedi). File lekapote honest line ("తుది తేదీలు ప్రతి పోస్ట్‌లో…") chupistundi.
  App        : "⬇️ App డౌన్‌లోడ్ [FREE]" button **prathi visit lo** (mobile-first) + device-wise
               install sheet (Android Chrome prompt · iPhone Share · Computer icon).
  Sections   : "అర్హత ప్రకారం చూడండి" — 10th · 10+2 · ITI · డిప్లొమా · డిగ్రీ · పీజీ · బీటెక్ ·
               ⏳ 7 రోజుల్లో ముగిసేవి. Groups **grid cards nunchi JS automatic ga** build avutayi
               (జీరో extra DB queries) — కొత్త పోస్ట్ వచ్చిన ప్రతిసారీ అదే క్షణం అప్డేట్.
  Filter     : chips క్లిక్ → reload lekunda category tho kalisi filter (`?qual=` URL sync tho) ·
               గడువు ముగిసినవి దాచి note chupistundi.

WORDPRESS (theme v1.7.1)
  `inc/qual-filter.php`  : `studentup_qual_directory()` (wp_footer) · `studentup_hidden_note()` ·
                           admin dashboard widget (అర్హత-wise counts + tag-leni posts) ·
                           chips ki `data-qual` (JS combined filter).
  `assets/js/studentup.js`: combined category × అర్హత filter + expired hide + grouping builder.
  `assets/js/studentup-pwa.js`: always-visible button + device-wise sheet + SW register.
  `inc/template.php`     : card ki `data-last` (closing filter) — bot `studentup_last_date` nunchi.
  `footer.php`           : Download App button + install sheet (options tho on/off) — **v73: English copy**.
  Version parity: style.css ↔ STUDENTUP_VERSION ↔ readme.txt = **1.7.1**.

BOT
  `wp_theme_sync.write_preview_deadline()` — **v73 lo teesesaamu** (hero block poyindi, dead code vaddhu).

VERIFY (v72.1)
```
python run.py --test-all                     # 56/56 suites
node tests/runtime/jsdom_runtime_test.js     # 164/164 browser checks
python tests/v72_test.py                     # 27 checks (v72 + v72.1)
python run.py --readiness                    # 100/100 · python run.py --guardian
python tools/parity_audit.py                 # PIN-TO-PIN · python tools/code_audit.py # 0/0
node tools/php_lint.js                       # 32/32 · python tools/build_wp_theme.py
```

No guarantee: rankings/traffic/AdSense/revenue Google + mee accounts + time batti — ee pass lo unna vi
code-level measurements matrame.

---

## PART 33 — v73: ENGLISH UI PASS + HERO BLOCK REMOVAL

**Mee brief (2026-09-18):** "antha ilaga telugu lo kkadu english lo cheyu" · hero block
(eyebrow · h1 · lede · CTA · live countdown card · అర్హత/మూలం tiles) **idi avasram ledu** → remove.
Scope (mee choice): UI/labels/headings English; Telugu mattrame job/article content lo.

PREVIEW (`preview/`)
```
index.html   : hero → `.hero-slim` (English h1 + one honest line) · countdown card + JS teesesaam
               (`#cd-live`/`#cd-none`/`#cd-box`/`data-deadline`/`data/deadline.json` = 0) · `lang="en"` ·
               og:locale en_IN · ld inLanguage en-IN · UI text/attrs/JS strings antha English ·
               Telugu migilindi = job/article cards + quiz bank (content — mee scope)
pages/*.html : about · contact · advertise · privacy · disclaimer · editorial-policy → 0 Telugu
               (English bodies, English footer, SPONSORED asides English)
sw.js        : VERSION `su-v73-1` · offline page English
manifest     : shortcuts English (Jobs · Jobs by qualification · Results · Daily Quiz)
```

THEME (`wordpress-theme/studentup/`, version 1.7.1 — copy/UI pass)
```
front-page.php        : hero card + countdown + deadline teesesaam → `.hero-slim` English
inc/template.php      : studentup_deadline() / studentup_set_deadline() poyayi (dead code)
functions.php         : menu labels · most-used tiles · i18n strings English · 'deadline' localize poyindi
header.php / footer.php / index.php / single.php / 404.php / search.php / searchform.php / author.php /
archive.php / comments.php / inc/*.php / assets/js/*.js : public copy antha English
inc/qual-filter.php   : chips/labels/notes/subs English · `studentup_qual_keywords()` mattrame Telugu
                        (posts Telugu headline nunchi auto-tag cheyyadaniki — REQUIRED)
style.css             : `.hero-slim` CSS (old hero/hcard CSS poyindi) · header Description English
Version parity        : style.css ↔ STUDENTUP_VERSION ↔ readme.txt = 1.7.1 (version bump ledu — UI pass)
```

BOT (`autoblog/`)
```
breaking.py          : MOST_USED labels/hints English (site/bot parity intact)
wp_theme_sync.py     : write_preview_deadline() teesesaam · payload nunchi 'deadline' poyindi
main.py              : --push-theme-data nunchi preview deadline step poyindi
config.py / .env.example : POST_DEADLINE_TITLE / POST_DEADLINE_ISO poyayi
```

VERIFY (v73)
```
python run.py --test-all                     # 56/56 suites (v73_test.py kotha: 9 checks)
node tests/runtime/jsdom_runtime_test.js     # 164/164 browser checks (English UI + countdown removal)
python run.py --readiness                    # 100/100 · python run.py --guardian
python tools/parity_audit.py                 # PIN-TO-PIN · python tools/code_audit.py # 0/0
node tools/php_lint.js                       # 32/32 · python tools/build_wp_theme.py (zip rebuild LAST)
```

TESTS REBASE (v73 lo maree pins update chesam — UI ni tirigi pettaledu):
`tests/v59_test.py` (menu/ticker wording) · `tests/v61_test.py` (labels + countdown JS) ·
`tests/v67_test.py` (search empty state) · `tests/v72_test.py` (countdown → no-countdown check) ·
`tests/runtime/jsdom_runtime_test.js` (English chrome + hero + 162 checks) ·
`autoblog/readiness.py` (`lang="en"` + og:locale · first-look labels) · `autoblog/guardian.py`
(first-look needles + hero order).

No guarantee: rankings/traffic/AdSense/revenue Google + mee accounts + time batti — ee pass lo unna vi
code-level measurements matrame.

## PART 34 — v75: CONTACT FINAL (+91 ledu) + PUBLISH SAFETY + DUMMY PURGE

**Mee brief (2026-09-19):** "+91 avasaram ledu" · "more and more advanced" ·
website fully finalise · all bugs fix · anni advanced implement.

CONTACT (owner number 9182739312 — verified)
```
tel: links      : tel:9182739312 (preview index/contact · policy builder PHONE · theme CTA)
visible text    : "Call 9182739312" (+91 ekkada kanipinchadu)
wa.me links     : wa.me/919182739312 (country code MANDATORY — lekunte button work avvadu)
theme helpers   : studentup_wa_number() (10-digit/+91/0 → wa.me digits) ·
                  studentup_call_number() (display/tel kosam 10-digit) · defaults 10-digit
header fallback : hardcoded wa.me full number (template safety-net, pani chestundi)
```

SAFETY (thin stubs live ki vellavu)
```
main.run()      : mock=True + dry_run=False → auto dry-run ON (log warning)
top_post_run()  : publish + mock → auto dry-run ON
offline harness : mock + FakeWP tests (listicle/research/seo_pipeline) alage work (CLI-level guard,
                  pipeline-level kaadu — anduke test pattern break avvaledu)
```

DUMMY PURGE (live surfaces 0 fake content)
```
ads/inventory.json : demo ads active:false (FORMAT SAMPLES — posts loki ravu, demo page lo preview untundi)
ads/house.json     : house-live-exam (dead #exam) → house-jobs (#jobs, real anchor)
wp_theme_sync      : inactive + link-leni house ads live theme ki push avvavu
guardian           : ads count honest ("live/total ads active")
```

BUG HUNT (pyflakes + review)
```
readiness.py    : THEME_PATH undefined dead branch teesesam
ad_network_plan : uplift import shadow teesesam (local def canonical)
ad_manager      : dead `house` var · rm100: dead `tests = analyze()` line
v59_test        : fixed-date time-bomb → dynamic pub dates (sort deterministic, eppudu green)
4 suites        : .venv/bin/python hardcode → sys.executable (fresh clone + CI safe)
package-lock    : php-parser entry add (lock stale undindi)
```

VERIFY (v75)
```
python run.py --test-all                     # 57/57 suites (v75_test.py kotha: 10 checks)
node tests/runtime/jsdom_runtime_test.js     # 164/164 browser checks
python run.py --readiness                    # 100/100 · python run.py --guardian # 14/15 (creds pending)
node tools/php_lint.js                       # 32/32 · python tools/build_wp_theme.py (zip rebuild LAST)
python run.py --mock --force                 # auto dry-run ON + DRY-RUN saved (publish ledu)
```

No guarantee: rankings/traffic/AdSense/revenue Google + mee accounts + time batti — ee pass lo unna vi
code-level measurements matrame.

## PART 35 — v76: QUALIFICATION DROPDOWN (chips → select) + UI DE-JUNK

**Mee brief (2026-09-19):** "10th jobs ilaga filters best ga undali dropdown lo" ·
"live exam avasaram ledu" · "UI inkbest + sodi lekunda" · "more easy + advanced".

PREVIEW (`preview/index.html`)
```
qrow chips (9 buttons) → select#qualsel + label.quallabel + span#qcount (same ids)
options : all · 10th (label "10th Pass") · inter · iti · diploma · degree · pg · btech · closing
JS      : change → activeQual + history ?qual= sync + applyFilter (v72 engine same)
counts  : option labels ki grid nunchi live counts ("10th Pass (3)") — values same
deep-link: ?qual=degree tho page open → pre-filtered (shareable links)
CSS     : .qualsel + .quallabel (native arrow · dark mode) · .qchip/.soonchip teesesam
sodi    : in-feed ad "Your brand" duplication fix (okasari)
```

THEME (`wordpress-theme/studentup/` — parity)
```
qual_bar()  : chips → <form GET> + select#qualsel + noscript Filter button
              (no-JS kuda pani chestundi; counts server-side; closing option KOTHA)
studentup.js: qchip clicks → qualsel change (reload-lekunda filter + history sync same)
bug fix     : ?qual= tho page load ayithe JS activeQual select value nunchi init
              (mundu category click qual filter ni reset chesedi — server/JS sync)
style.css   : .qualsel rules (preview tho same look) · .qchip rules teesesam
qualtags    : card qual tags wrapper rename (qchips → qualtags, confusion ledu)
```

PINS MOVED (chips → dropdown, logic same)
```
v72_test  : option order + label + JS needles (TESTS REBASE pattern)
v59_test  : qualsel + value="10th" + qcount
readiness : c_first_look qualsel needles (preview + theme)
guardian  : UI_BLOCKS qualsel needle
jsdom     : qual block select mechanics (setQual helper) — ok() count SAME (164/164)
v75_test  : suites 57 → 58
```

LIVE-EXAM (user doubt — verified + locked)
```
grep live[ _-]*exam (preview · theme · ads · manifest) = 0 · #exam = 0
quiz = practice questions matrame (6 Q · instant answers · browser score) — exam conduct kaadu
manifest shortcuts = Jobs · Qualification · Results · Quiz (exam ledu)
```

VERIFY (v76)
```
python run.py --test-all                     # 58/58 suites (v76_test.py kotha: 10 checks)
node tests/runtime/jsdom_runtime_test.js     # 164/164 browser checks (dropdown mechanics)
node tools/php_lint.js                       # 32/32 · python tools/build_wp_theme.py (zip rebuild LAST)
python run.py --readiness                    # 100/100 · python run.py --guardian
```

No guarantee: rankings/traffic/AdSense/revenue Google + mee accounts + time batti — ee pass lo unna vi
code-level measurements matrame.

## PART 36 — v77: ORIGINAL CONTENT ENGINE + HIGH-ADS READINESS

**Mee brief (2026-09-19):** fully advanced · high ads · ads auto na? · reach
tavata vere networks apply · URL → related content gather · 100% RankMath/SEO
real · no copy fresh · Telegram update = fresh re-trend · page-to-page fresh ads.

GATHER (URL isthe related antha)
```
sources.py  : SourceArticle.outbound (content-area links, boilerplate out)
              rank_outbound: official-hosts(3) > gov/edu(2) > org(1) > rest;
              same-site last; social out; cap 25
research.py : official outbound FIRST (4 varaku) → tarvata web search extras
              (MERGE & BEAT same; max_extra cap same)
```

ORIGINALITY (REAL numbers — "dummy" doubt close)
```
validator.rewrite_distance(html, source_texts):
  donor-vs-final 3-word shingle containment → {overlap, fresh, verdict}
  fresh ≥0.70 · rewrite ≥0.40 · copy-risk kindha · short (<60 shingles) skip
pipeline.publish_article: _originality compute + log (prathi post)
pipeline.update_post    : _originality compute + log (prathi update)
near_duplicate (own corpus) alage undi — rendu kalisi double-proof
```

UPDATE = RE-TREND (chain verify + 1 fix)
```
upd: button → approval_bot.run_update → update_post → date_modified schema +
"Last Updated" badge + RankMath re-meta + IndexNow ping + Telegram confirm
FIX: news-sitemap date_query publish OR modified 48h (mundu updated old posts
re-enter ayyevi kaavu — trending miss; ippudu avtayi)
```

ADS SMART (high + fresh + auto)
```
theme rotate_house: day → hour-base (24 chances) + slot offset + static $shown
  no-repeat (oke page lo vere ads; next hour kotha) — house/sponsor kevalam
AdSense: auto-refresh LEKUNDE (policy) — test locks (setInterval = social only)
auto proof: auto-head (option + ca-pub regex) · in-article filter ON ·
  density cap · consent gate · house fallback — manual placing ZERO
networks: AD_NETWORKS_APPLICATION_KIT.md (review + order + checklist + flips)
```

PINS: v61 rotation formula rebase (hour) · v75/v76 counts 59 · jsdom untouched 164.

VERIFY (v77)
```
python run.py --test-all                     # 59/59 suites (v77_test.py kotha: 10 checks)
node tools/php_lint.js                       # 32/32 · python tools/build_wp_theme.py (zip LAST)
python run.py --readiness                    # 100/100 · python run.py --guardian
```

No guarantee: rankings/traffic/approval/revenue Google + accounts + time —
v77 = copy-proof + deepest gather + fastest re-index path (code-side max).

## PART 37 — v78: TOP-BLOG PERFECTION PASS (real-probe → fix → re-probe)

**Mee brief (2026-09-19):** anni points real check · dummy/sample vaddu ·
retry-best loop · correct data + many sources + NotebookLM · neat blogs
(text peddga vaddu) · colors/tables/tags/categories perfect · 100% top blog.

METHOD (edo final kaadu): REAL probe publish (thin input, no FAQ, 1 tag) →
gaps measure → code fix → RE-PROBE same input → numbers prove:
tables 0→1 · FAQ 0→6 · tags 3→4+ · ORIG None→98.8 · RM 88→96 ·
TOP 84→90 🏆 · GATE 86→92.

FALLBACKS (LLM marchipoina kuda perfect — invent cheyyavu)
```
rm100.extract_facts(html): Telugu+English regex → last_date/exam_date/
  vacancies/fee/age/qualification/salary (content phrases only)
fix_table: fields <3 → facts merge (8 rows cap) → <3 = honest skip
fix_faq:   pairs <3 → facts templates (6 cap) + <div class="su-faq">;
  already-in-content guard same; <3 = honest skip
suggest_tags: existing + focus + secondary[:4] + category + title
  acronyms (TSPSC/[A-Z]{2,}) + Group-N → hygiene junk-block/dedupe/cap8
```

UNIFORM + DEPTH + NEAT
```
pipeline: _source_texts <= _deep_sources (no _source_texts unte) → _orig
  live gate publish + rewrite paths ki (None bug fix)
config: RESEARCH_MAX_SOURCES 3→5 (+ v77 outbound = deepest gather)
fix_paragraph_len: split 120→100w, chunks 90→~70w (sentence boundary only)
theme style.css: .su-lede · .su-faq h3 cards (+p answers) · dark variants ·
  su-facts zebra — mundu lede/faq styles LEVU (live ugly root-cause)
```

VERIFIED REAL (no dummy): NotebookLM brief merge + hard-reject validation;
17 category rules auto-detect; writer prompt = table/1500-2200w/tags/faq adugutundi;
rm100 rich-content → 81 + honest remainder (length/density = content job).

VERIFY (v78)
```
python run.py --test-all                     # 60/60 suites (v78_test.py kotha: 10 checks)
node tools/php_lint.js                       # 32/32 · python tools/build_wp_theme.py (zip LAST)
python run.py --readiness                    # 100/100 · python run.py --guardian
```

Loop rule (standing): best vache varaku probe→fix→reprobe; final-cheyatam kaadu.

## PART 38 — v79: AUTHOR + MID-ARTICLE JOIN + MISS-AUDIT CLOSE

**Mee brief (2026-09-19):** author unte best kada? mid-blog TG/WA join?
inka em miss? — audit → fix → verify.

AUTHOR (E-E-A-T upgrade, v64 pins hold)
```
inc/author-box.php: avatar custom_logo(64) → site-icon → 📝 fallback;
  Person schema (name + jobTitle Education Editor) inside Organization;
  🔍 Reviewed: <modified-date>; TG/WA follow (studentup_social_links);
  corrections email + editorial policy same
```

MID-ARTICLE JOIN (reuse — duplicate kaadu)
```
inc/cta.php: studentup_cta_join_inline() — compact strip, div/span/a ONLY
  (no <p> → ad explode-after-3rd-para intact; no <h2> → TOC clean);
  same social options (owner changes once).
  studentup_inject_join_cta @ the_content prio 12 (ad = 20): singular+
  loop+main+!feed guards · join_cta_inline opt (default 1) · once-guard ·
  2nd </p> tarvata. option: content section lo 'join_cta_inline' check.
```

MISS-AUDIT CLOSE (single.php)
```
the_tags (🏷 su-tags div, has_tag guard) + post-nav (prev/next) — rendu
mundhu LEVU. Surface 13/13: progress·crumbs·read-time·mid-ad·share·
trust·author·tags·prev/next·comments·related·last-date·qual.
FAQPage schema = deliberate skip (Google retired 2026 — seo.py note).
CSS: .su-join-inline(+dark) · .su-author-avatar img · .su-tags · .post-nav(+dark).
```

VERIFY (v79)
```
python run.py --test-all                     # 61/61 suites (v79_test.py kotha: 10 checks)
node tools/php_lint.js                       # 32/32 · python tools/build_wp_theme.py (zip LAST)
python run.py --readiness                    # 100/100 · python run.py --guardian
```

## PART 39 — v80: MASTER PROMPT GAP CLOSE (50-phase audit)

**Mee brief (2026-09-19):** 50-phase master prompt + 5 additions verify —
em miss ayyama? Method: phase-by-phase grep-proof audit.

COVERED (verify chesamu — kotha code avasaram ledu)
```
P1 info-arch: WP cats + 17 bot rules + hubs · P2 URLs: WP permalinks +
  bot slug hygiene · P3/P4/P22/P43 DB+admin+API: WP CORE (custom kaadu —
  master prompt custom-stack assume chesindi) · P5 on-page: RankMath+WP
  (+v80 fallback) · P6 H1: single/home ✓ (archive/search v80 fix) ·
P7 content model: prompt sections + v78 fallbacks, no-fabrication guards ·
P8/P37 linking: related/crumbs/prev-next/contextual/hubs · P9 crumbs+schema ·
P10 sitemap WP+news · P11 robots WP+news · P12 canonical WP ·
P13/P15 search/404 noindex perf.php ✓ · P14 schema Article/Breadcrumb/
  JobPosting-eligible · P16 archive base (v80 enrich) · P17 images alt+lazy ·
P18/P19/P20 CWV/mobile/perf: CLS-reserve/content-vis/lazy · P21/P22 security
  headers+WP · P23 legal 6 · P26 badge+closing (v80 notice) · P27 quiz
  practice+key (obfuscation=theater, honest skip) · P30 a11y skip/focus ·
P31 share/OG · P32 audit engines · P33 61 suites · P34 live gates ·
P38 dup-guards · P39 dates · P40 E-E-A-T · P41/42 ads/rel · P44 bot logs ·
P46 GO_LIVE · P48/P49/P50 guardian+readiness (deploy-time verify).
AI pipeline = Official→verify→extract→human-review(Telegram)→
  draft→fact→SEO-gate→publish ✓ (addition #3 exact match).
```

V80 FIXES (7 real gaps)
```
P29  inc/redirects.php: redirects_json map · 404-only · resolve-chain
     direct (5 hops) · loop/relative-only · wp_safe_redirect 301
P6/16 archive+search h2→h1 (+CSS 3 spots) · studentup_subcat_chips()
     (child+counts, hide_empty, 12 cap) · .su-subcats CSS+dark
P28  404: popular 6 cats + latest 5 + reset postdata · CSS
P24/25 ga4_id (G- regex) + gsc_verify options · consent-aware GA4
     (prio 3, anonymize_ip) · JS outbound/apply_click (gtag-gated)
P26  studentup_expired_notice() + single guarded call · .su-expired CSS
P5   seo-fallback: RankMath absent → description+OG (bot meta reuse)
P47  tools/check_links.py + run.py --check-links (dead+redir report)
```

OWNER/HOSTING (code kaadu): GSC submit · GA4 ID · backups+restore-test ·
CDN · live GSC/GA4 monitoring · crawl post-deploy.

VERIFY (v80)
```
python run.py --test-all                     # 62/62 suites (v80_test.py kotha: 12 checks)
python run.py --check-links <post-URL>       # dead outbound report
node tools/php_lint.js                       # 33/33 · python tools/build_wp_theme.py (zip LAST)
python run.py --readiness                    # 100/100 · python run.py --guardian
```

## PART 40 — v81: ULTIMATE SPEC GAP CLOSE (99-section audit)

**Mee brief (2026-09-19):** Ultimate master spec — audit→plan→implement→
test→verify. v80-covered skip; kotha/expand areas (blog-advanced · job
entity · exam chain · mock tests · images · orphans · dashboards ·
filters · i18n · CSP · observability) verify.

COVERED (proof, no code): TOC smooth+dup-ids · JobPosting future-only+
org-guard (expired=past validThrough → Google drops ✓) · quiz analysis
chips+review · menus nav/footer · PWA offline page · RSS WP · images
slug-name+alt+srcset(WP) · revisions/scheduled WP · alerts=TG/WA ·
secrets=.env gitignored · scorecard=readiness report.

V81 FIXES (8)
```
§72 perf.php: $_GET['qual'] → noindex+follow (v67 pins hold)
§2  validator ALLOWED_TAGS += blockquote/pre/code (iframe/video/script
    OUT — WP auto-embed plain URLs) · gemini prompt 3 tag-lists sync
§7  style.css: .article-content table block+scroll-x · pre/code (+dark)
§22 image_gen: .webp→WEBP q82 · .jpg→JPEG (compat) · pipeline slug.webp
§32/60 tools/check_links --orphans SITEMAP (limit 200, inbound-0 report)
    + run.py --orphans wiring
§65 inc/health.php dashboard widget: published/drafts/expiring-7d/
    expired/redirects (counts-only queries) + functions require
§37 studentup.js: form[name=s] submit → gtag search event (gated)
§76 hsts_enforce opt (default 0) + is_ssl guard · CSP skip documented
```

NOT IMPLEMENTED (honest §95): mock-test series (accounts/infra roadmap) ·
server page-cache (hosting) · CSP (AdSense/GA4 break risk) · GSC-data
dashboard (OAuth/API post-launch) · Lighthouse run (needs deploy URL).

VERIFY (v81)
```
python run.py --test-all                     # 63/63 suites (v81_test.py kotha: 10 checks)
python run.py --orphans <sitemap.xml>        # orphan pages report
node tools/php_lint.js                       # 34/34 · python tools/build_wp_theme.py (zip LAST)
python run.py --readiness                    # 100/100 · python run.py --guardian
```

## PART 41 — v82: SELF-AUDIT REGRESSIONS (proactive hunt)

**Mee brief (2026-09-19):** "chala miss chesava" — v81 tarvata nenu mundhe
deep self-audit (real runs: update_post · guardian · mock E2E · --doctor ·
deps · idempotency · house chain · approval auth). Assumptions tho "gap"
declare cheyakunda prathi doubt ni code-run tho verify.

V82 FIXES (6 + cleanup)
```
rm100 chain reorder: h2/table/faq MUNDU → toc TARVATA (single-pass
  structure complete; optimize() 3-pass converge, no-dupes verified)
inc/ads.php: leaderboard → top_leaderboard slot mapping (AdSense unit
  never loaded — REAL revenue bug) + house 'description' key accept
crontab.example: mkdir -p log step + cron.log monthly rotation line
approval_bot: callbacks fail-closed (owner lekapote deny) + auto-claim
  loud warning + TELEGRAM_CHAT_ID lock reminder
pyflakes: 57 dead imports/vars cleanup (32 code + 25 tests) · f-strings
re-export REGRESSION: tools/ad_network_plan.NETWORKS (v56 pin)
```

VERIFY (v82)
```
python run.py --test-all                     # 64/64 suites (v82_test.py kotha: 9 checks)
node tests/runtime/jsdom_runtime_test.js     # 164/164 browser checks
python tools/build_wp_theme.py               # zip LAST (ads.php changes!)
python run.py --readiness                    # 100/100
python -m pyflakes autoblog tools tests      # 0 findings
```

## PART 42 — v84: FULL BUG HUNT (money + ads + approvals)

**Mee brief (2026-09-19):** "inka chala bugs undochu — anni fix cheyali".
Systematic hunt areas: theme XSS · 6 ad slots mapping · expiry/validThrough ·
cron race · gate false-pass · TOC duplication · update flow · SQLite lock ·
TG limits · archive SEO. Prathi doubt real-run tho verify (assumption tho
"gap" declare cheyaledu).

V84 FIXES (11)
```
validator.strip_tags: <script>/<style> blocks drop (JSON-LD +106 words
  gate words-check false-pass HOLE — 1400-word thin publish ayyedi!)
validator.ist_today + seo/post_gate: IST-explicit deadlines (server UTC
  00:00-05:30 window lo expired jobs 'valid' ayyevi)
inc/options.php + ads.php + pwa.php: AdSense APPROVAL GATE —
  adsense_approved OFF unte code render kaadu (house ads only)
main.py run(): hour-slot claim post:DATE:HOUR (overlap double-post race)
main.py --orphans: no-URL → WP sitemap default · check_links: DEAD-url
  report (404 pages) · crontab: weekly orphans scan
state.py _connect: timeout=30 + WAL (hourly + */5 overlap lock fix)
notifier.send_telegram: 4000-char truncate (4096 reject = alert loss)
perf.php robots: is_date() noindex,follow · seo-bridge: Yoast/AIOSEO
  stand-down (double-meta)
seo.add_table_of_contents: idempotent guard (rm100+enhance DOUBLE TOC —
  live posts lo 2 boxes vachevi! user-visible bug)
pipeline.update_post: rm100.optimize re-run (rewrite degrade fix +
  rank_math_seo_score fresh)
```

ALSO (v83, no suite bump): rm100 TRUE-100 — takeaways/TOC self-fail fix
(57→100 proven) · content-length message 1500 align · v82_test 9th check.

VERIFY (v84)
```
python run.py --test-all                     # 65/65 suites (v84_test.py kotha: 13 checks)
node tests/runtime/jsdom_runtime_test.js     # 164/164 browser checks
python tools/build_wp_theme.py               # zip LAST (ads/options/pwa/perf/bridge changes!)
python run.py --readiness                    # 100/100
python -m pyflakes autoblog tools tests run.py  # 0 findings
```

## PART 43 — v85: AUTO-BLOG PREP DEEP AUDIT (any URL + any length)

**Brief:** Telegram-bot URL→post eme URL + entha lengthy ayina success;
prompts correct/advanced; 100% RankMath/SEO/keywords. Fetch→prompt→parse→
refine→bot full-path real-run audit (local HTTP fixtures + monkeypatch).

**Fixes (9):**
1. `sources.py` — `<table>` rows `TABLE:` lines + h2/h3 `[H]` + cap 18000
   (vacancy/fee/age facts drop = hallucination cause)
2. `gemini_client.py` — `JSON_SCHEMA_CONTRACT` (10 required keys, recruitment
   object, empty-string-NOT-ok) both generate paths ki wire
3. `gemini_client.py` — `_parse_json` repair (trailing commas/control chars)
   + `_normalize_keys` aliases + faq `{q,a}`/`[q,a]` unify
4. `sources.py` — JS-empty pages ki JSON-LD `articleBody` fallback
   (decompose MUNDU capture); non-HTML/404 honest ValueError
5. `refine_article` context 20000 + `_rankmath_gate` anti-truncation
   (<70% length = reject, original keep)
6. `rm100.fix_slug` ASCII-only (pure-Telugu keyword = untouched)
7. `approval_bot.on_message` — mid-text URL extract (`https?://\S+`)
8. `approval_bot` — pipeline daemon thread (polling freeze fix) +
   honest exception message user ki
9. `tests/v84_test.py` — `test_first_para_skips_ads` registration miss fix

**Lesson:** same-file parallel edits race (last-write-wins) — sequential only.

VERIFY (v85)
```
python tests/v85_test.py                     # 9/9 checks
python run.py --test-all                     # 66/66 suites
node tests/runtime/jsdom_runtime_test.js     # 164/164 browser checks
python run.py --readiness                    # 100/100
python -m pyflakes autoblog tools tests run.py  # 0 findings
```

## PART 44 — v86: PROFESSIONAL POST AUDIT (final post end-to-end)

**Brief:** oka professional post avvali — full pipeline local source tho
end-to-end run chesi FINAL WP payload audit (structure/tags/anchors/
provenance/featured/excerpt/slug).

**Fixes (6):**
1. `seo.py` — read-also duplicate delete; `su-related` single block +
   `_short_title` + "వీటిని కూడా చదవండి" rotation (4 headings)
2. `pipeline._append_official_sources` — gov/edu matrame official-links;
   news sources skip (su-source + trust-box cover); dedupe
3. `sources.is_official_domain` — hosts + full URLs (pipeline gate)
4. `rm100._anchor_id` — ASCII-only (pure-Telugu → section-N); seo side
   already ASCII (probe: rm100 TOC ne live path)
5. `seo.enhance` — visible breadcrumb remove (theme `.crumbs` duplicate);
   BreadcrumbList JSON-LD intact
6. `approval_bot` — pin-gate error dict → honest ⛔ (source + update paths;
   "ayyindi ✔" false-success hole closed)

**False alarms (verify chesi vadilesina):** post lo "raw CSS" — `<style>`
intact (text-view artifact); in-content images — feature, not bug (skip).

VERIFY (v86)
```
python tests/v86_test.py                     # 6/6 checks (e2e FakeWP/Src/TG)
python run.py --test-all                     # 67/67 suites
node tests/runtime/jsdom_runtime_test.js     # 164/164 browser checks
python run.py --readiness                    # 100/100
python -m pyflakes autoblog tools tests run.py  # 0 findings
```

## PART 45 — v87: FIX-ALL ROUND (update e2e + quiz + banners)

**Brief:** "fix all" — update flow e2e probe + quiz/banner visual audit.

**Fixes (7):**
1. `pipeline.update_post` — `_ures["after"]` → `["score"]` (×2: dict + log
   line). `optimize()` returns "score"; v84 update-rm100 KeyError tho ALWAYS
   skip ayyedi. (apply-vs-optimize key audit: migathavi anni correct)
2. `update_post` — `_source_urls` + `_append_official_sources` (create parity);
   helper None-safe (`article.get(...) or []`)
3. `create_quiz` — manual level clamp 1-4 (KeyError crash fix), questions
   clamp 1-30 (LLM truncate/cost), dup-guard generate MUNDU (title pre-compute)
4. `image_gen.telugu_to_latin` — Telugu banner tofu boxes (□□□) fix. PIL ku
   Indic shaping ledu (no raqm local + server) → deterministic Latin
   (conjuncts/virama/matras/digits). Banner + pill label rendu.
5. `image_gen` — `_split_word` hard-break (long-token canvas overflow) +
   `_fit_banner` auto-shrink (bottom 3-line → footer overlap fix)
6. `_hygiene` — empty focus_keyword → title-derived (41-score drafts + rm100
   kw-skip fix). Validator empty-kw ni honest-41 ga handle chestundi (verified)
7. `auto_refresh` — owner TG summary (cron silent fix; notify never breaks cron)

**Visual proof:** /tmp/v87_img renders (before: tofu + overlap + overflow;
after: clean Latin + fit). Probe artifacts noted: FakeWP routing
(`?context=edit` endswith), dates/title/related anni real-run lo verify.

VERIFY (v87)
```
python tests/v87_test.py                     # 7/7 checks
python run.py --test-all                     # 68/68 suites
node tests/runtime/jsdom_runtime_test.js     # 164/164 browser checks
python run.py --readiness                    # 100/100
python -m pyflakes autoblog tools tests run.py  # 0 findings
```

## PART 46 — v89: PREMIUM HOMEPAGE (theme 1.9.0)

**Brief (screenshots):** TS/AP Govt Jobs asalu kanipinchaledu · Central ledu ·
icons tappu · read-more dead · search live kadu · dropdown plain · scrolling
ledu · Internet Center Telugu lo kavali · laptop messy.

**Root cause:** live categories `ts-govt-jobs`/`ap-govt-jobs`/`central-govt-jobs`;
theme `ts-jobs`/`ap-jobs` ni direct search chesedi → silent miss prathi chota.

**Fixes:**
1. Alias resolver `studentup_used_term()` (theme slug → live candidates) +
   reverse `studentup_theme_cat()` (live slug → chip slug). Call-sites:
   front-page cards · header mobile panel · footer categories · menu fallback.
   Card `data-cat` eppudu theme slug → live chip filter match.
2. Central Govt Jobs — most_used TS·AP·Central top-3 (theme + bot breaking.py
   + preview + jsdom + guardian 9-tile pin anni sync).
3. Latest Jobs ticker `studentup_latest_ticker()` — homepage only, own posts
   (`su_latest_ticker` transient 10 min, save_post flush), link = post
   permalink same-tab, hover pause, reduced-motion off. Option:
   StudentUp → Content → Latest jobs scrolling ticker.
4. Live search `#qtop` — WP REST `/wp/v2/search?per_page=7`, 220 ms debounce +
   AbortController, ↑↓/Enter/Esc keyboard, combobox ARIA, click → exact post.
5. Brand SVG icons `studentup_social_icon()` (Simple-Icons CC0 paths) — rail
   (`su-rail-*`), mobile menu (`su-msoc-*`), single share (`su-share-*`),
   author box, join blocks. Chrome emojis 💬✈️📸▶️ removed.
6. Card "Read more" — real `<a class="su-readmore">` permalink (was dead `<b>`).
7. విద్యార్థుల ఇంటర్నెట్ సెంటర్ (Students Internet Center · TS & AP) —
   Telugu lead + perks row (Application PDF · పూర్తి Guidance · Preparation
   Group) + brand WhatsApp button + tel:+91 Call.
8. Animated qualification dropdown (`.quadd` custom UI; native select sr-only
   tho no-JS/SEO safe) + `SSC · 10th` wording + SSC GD/MTS (10th) + SSC CHSL
   (10+2) keyword mapping.
9. Laptop layout: used-strip 3×3 + news grid 3-col (≥981 px) + menu no-wrap
   scroll + current-page pill + animated submenu caret.
10. Menu/mpanel/chips top: TS Govt Jobs · AP Govt Jobs · Central Govt Jobs.

VERIFY (v89)
```
python tests/v89_test.py                     # 10/10 checks
python run.py --test-all                     # 69/69 suites
node tests/runtime/jsdom_runtime_test.js     # 164/164 browser checks
python run.py --readiness                    # 100/100
python -m pyflakes autoblog tools tests run.py  # 0 findings
```

* AdSense-safe: kotha UI anni ads.php slots ni block cheyyadu; house ads same;
  AdSense toggle OFF aithe public pages lo e ad code render avvadu (v84 gate
  unchanged).
* Deploy: theme zip rebuild (`python tools/build_wp_theme.py`) → WP Admin →
  Appearance → Themes → Add New → Upload → **Replace current** (1.9.0).

## PART 47 — v90: NOTIFICATIONS (theme 1.9.1)

**Brief:** bot/site alerts ki okka STANDARD surface ledu — guardian "feed
stale" antundi log lo matrame; owner dashboard chudakapote alert reach kaadu;
readers ki critical info (result released / site maintenance) banner ga
chupinchadaniki mechanism ledu.

**Root cause:** theme lo alert plumbing ledu; notifier.py = Telegram-only
(owner chat), site-side surface kaadu.

**Fixes (inc/notify.php — theme 1.9.1):**
1. Alert queue = WP option `studentup_notify_queue` — code-wise DEDUPE (same
   code push chesthe update, duplicates ledu) · FIFO cap 20 · messages
   300-char strip + sanitize.
2. Severities whitelist `info · warn · critical` — vere emi ichina `info` ki
   fallback (safe default).
3. Admin notices — severity classes (error/warning/info) + dismiss **per-user**
   meta (`studentup_notify_dismissed`, cap 50) — okari dismiss inkariki
   apply kaadu. AJAX `su_notify_dismiss` nonce-gated.
4. Public banner — **CRITICAL matrame** + option gate (`notify_banner`,
   default ON) · `wp_body_open()` tarvata render · reader ✕ = localStorage
   (`suNotifyHidden_<code>`) — server round-trip ledu. info/warn = admin-only.
5. REST `/wp-json/studentup/v1/notify` — GET (list) · POST (push) · DELETE
   (clear; `__all__` supported) — anni `manage_options` permission (bot
   application password). Body: `{code, message, severity}`.
6. Crash-proofing (PART-45 "notify never breaks cron" extension): prathi
   callback try/catch · corrupt option ayina khali queue return · banner
   fail ayina page render continue.

VERIFY (v90)
```
python tests/v90_test.py                     # 8/8 checks
python run.py --test-all                     # 71/71 suites
node tests/runtime/jsdom_runtime_test.js     # 164/164 browser checks
node tools/php_lint.js                       # 36/36 files OK
python run.py --readiness                    # 100/100
```

* AdSense-safe: banner chrome lo render — ad slots (`su-ad`/sticky/rail)
  block kaadu; banner OFF aithe markup eh ledu.
* Bot bridge: `python run.py --tg-alert "code|msg" --tg-severity critical`
  (v91 tools) → REST push → critical aithe public banner.
* Deploy: theme zip rebuild (`python tools/build_wp_theme.py`) → WP Admin →
  Appearance → Themes → Add New → Upload → **Replace current** (1.9.1).

## PART 48 — v91: TELEGRAM TOOLS (theme 1.9.2)

**Brief:** owner ki manual Telegram toolbox kavali — bot connectivity test,
PRIVATE channel ki announcement, site alert push. Readers ki channel reach:
private invite link support + footer join chip.

**Fixes (bot: autoblog/telegram_tools.py · theme: inc/telegram.php):**
1. CLI (main.py wiring):
   * `python run.py --tg-test` — bot ↔ owner chat ping + `getMe` identity.
   * `python run.py --tg-broadcast "MESSAGE"` — channel ki manual
     announcement. Long text **paragraph boundaries lo auto-SPLIT**
     (truncate kaadu — v84 truncate reports ki matrame; broadcasts ki full
     text `(i/n)` parts ga vellutundi). Private `-100…` channel ids supported
     (bot channel lo admin ga undali).
   * `python run.py --tg-alert "code|MESSAGE" [--tg-severity critical]` —
     v90 notify queue ki REST push (bridge).
2. Cron-safe: creds lekapote clear message + **exit 0** (PART-45 rule —
   notify/tools valla cron break kaadu) · network errors handled.
3. Theme `inc/telegram.php` (1.9.2):
   * `studentup_tg_channel_url()` — option override `telegram_channel_url`
     (PRIVATE invite `https://t.me/+…` regex-validated) → lekapote
     `social_telegram` username → `t.me/<user>`.
   * `studentup_tg_join_block($context)` — footer join chip (Telugu CTA
     "Telegram లో జాయిన్ అవ్వండి" + brand SVG icon).
   * `studentup_tg_share_url()` — `t.me/share/url?url=…&text=…` helper
     (single.php share row pattern).
4. Options: StudentUp → Socials → **Telegram channel URL override** (khali
   unte username link). `.env.example` lo `-1001234567890` private id hint.
5. Version bump 1.9.0 → **1.9.2** (functions.php · style.css · readme.txt
   Stable tag · changelog 1.9.1 + 1.9.2 entries) · suites 69 → **71**
   (v75–v81 pins updated).

VERIFY (v91)
```
python tests/v91_test.py                     # 10/10 checks
python tests/v90_test.py                     # 8/8 checks (bridge intact)
python run.py --test-all                     # 71/71 suites
node tests/runtime/jsdom_runtime_test.js     # 164/164 browser checks
node tools/php_lint.js                       # 36/36 files OK
python run.py --readiness                    # 100/100
python -m pyflakes autoblog tools tests run.py  # 0 findings
python tools/parity_audit.py                 # 0 errors
```

* Channel setup: `.env` lo `TELEGRAM_CHANNEL_CHAT_ID=-100…` (private) leda
  public channel id · bot ni channel lo **admin** ga add cheyandi ·
  `TELEGRAM_CHANNEL_URL` = invite link (auto-post footer lo kanipistundi).
* Deploy: theme zip rebuild (`python tools/build_wp_theme.py`) → WP Admin →
  Appearance → Themes → Add New → Upload → **Replace current** (1.9.2).

## PART 49 — v92: SAVED / READER RETENTION (theme 1.9.3)

**Mee brief:** "fully advanced best ga build cheyyu more and more advanced fully deep gaa".
Deep audit chesi (bookmark grep = 0 hits) okka **nijamaina** reader-facing gap fix chesam.

ENTI CHESAMU (v92)
```
wordpress-theme/studentup/inc/saved.php              # module (gates · button · panel · shortcode)
wordpress-theme/studentup/assets/js/studentup-saved.js  # engine (localStorage · toggle · render)
tests/runtime/saved_runtime_test.js                  # REAL behaviour test (jsdom · 53 checks)
tests/v92_test.py                                    # 11 checks (source + wiring + parity + zip)
```

* 🔖 **Save/un-save** — prathi card + single post lo. `aria-pressed` sync ·
  keyboard + screen-reader ready · label "Save" ↔ "Saved".
* **Saved rail + drawer** — count badge tho; saved list + Recently-read block;
  Escape / outside-click close.
* **`[studentup_saved]` shortcode** → /saved/ page (menu lo link pettachu).
* **localStorage mattrame** — DB ledu · cookie ledu · server round-trip ledu
  (privacy + AdSense clean · server load zero).
* **Private mode safe** — storage block aithe soft note + saving OFF; page break ledu.
* Options: Content tab → "Saved / bookmarks" (default ON) · "Saved posts limit"
  (5–200, default 60, FIFO drop).

VERIFY (v92)
```
python tests/v92_test.py                     # 11/11 checks
node tests/runtime/saved_runtime_test.js     # 53/53 real behaviour checks
python run.py --test-all                     # 72/72 suites
node tests/runtime/jsdom_runtime_test.js     # 164/164 browser checks
node tools/php_lint.js                       # 37/37 files OK
python run.py --readiness                    # 100/100
python tools/theme_audit.py                  # 0 errors
python tools/theme_audit_deep.py             # 0 errors · 0 warnings
```

* Deploy: theme zip rebuild (`python tools/build_wp_theme.py`, 47 files) →
  WP Admin → Appearance → Themes → Add New → Upload → **Replace current** (1.9.3).

## PART 50 — v93: TOP-WEBSITE UI PASS (theme 1.9.4)

**Mee brief:** "top website ui avvali · menu clear and neatga cheyu · icons
correctga vundali (whatsapp instagram telegram youtube) · chala mistakes unnayi".

ENTI ANUKUNNAMU (deep audit method)
```
1. icons ni grep cheyyaledu — SVG path data nunchi **render chesi** chusanu
   (svgpathtools + matplotlib) → 8/8 correct ani confirm ayyindi
2. icon <-> link mismatch audit (255 anchors)        → 0 mismatch
3. duplicate ID / broken link audit (preview)        → 0
4. CSS duplicate-property audit (theme + preview)    → 1 mistake dorikindi
5. theme vs preview CSS drift (131 shared selectors) → menu structure drift dorikindi
6. fixed-bar collision audit (mobile)                → 3 overlap dorikindi
7. heading order · button type · target=_blank rel   → 0 issue
```

FIX AYYINA 4 BUGS
```
BUG-1 menu: flat 10-item row → grouped dropdowns (Jobs ▾ / More ▾) + polish
BUG-2 telegram link: private-channel override rail/panel/footer ki apply avvatledu
BUG-3 fixed bars: sticky ad social icons ni cover · installbtn footer ni cover
BUG-4 css: .su-ad-lazy::after lo duplicate `display`
```

MENU STRUCTURE (ippudu — approved design parity)
```
Home · Jobs ▾ · Hall Tickets · Results · Current Affairs · More ▾
Jobs ▾ : TS · AP · Central · Private · Walk-in · Software   (unna vi mattrame)
More ▾ : Saved posts · Contact · About · Daily Quiz (publish ayyithe) ·
         Jobs by qualification · Telegram channel · All categories
```

VERIFY (v93)
```
python tests/v93_test.py                     # 12/12 checks (menu · icons · collisions)
python run.py --test-all                     # 73/73 suites
node tests/runtime/jsdom_runtime_test.js     # 164/164 browser checks
node tests/runtime/saved_runtime_test.js     # 53/53 saved engine
node tools/php_lint.js                       # 37/37 files OK
python run.py --readiness                    # 100/100
python tools/theme_audit.py                  # 0 errors
python tools/theme_audit_deep.py             # 0 errors · 0 warnings
```

* Deploy: `python tools/build_wp_theme.py` → WP Admin → Appearance → Themes →
  Add New → Upload → **Replace current** (1.9.4).

## PART 51 — v94: ADSENSE READINESS + DISCOVER + CWV (theme 1.9.5)

**Mee brief:** "posts publish cheste ads approval ki problem leda? google suggest
avvali ante em miss avutunnam? anni fix cheyu".

ENTI CHESAMU
```
autoblog/adsense_ready.py             # NEW: pre-application audit (8 groups · 29 checks)
wordpress-theme/studentup/inc/discover.php  # NEW: 1200px Discover image + og dims + CLS/INP
autoblog/seo.py                       # schema_jsonld(image) + attach_schema_image()
autoblog/wordpress_client.py          # upload ayna media source_url capture
autoblog/pipeline.py                  # upload tarvata schema image attach
tools/build_policy_pages.py           # privacy: third-party vendors + opt-out disclosure
wordpress-theme/studentup/footer.php  # 5 policy links (404-safe)
tests/v94_test.py                     # 13 checks
```

NEW COMMAND (meeru adigina prashnaki jawabu)
```
python run.py --adsense-ready
# Score: 97% (28/29 mandatory) · 1 blocker = posts volume (0 posts)
# blocker/warning prathi daniki fix line + JSON artifact output/adsense-ready.json
```

FIX AYYINA 6 GAPS
```
GAP-1 Article schema lo `image` ledu (Google ki REQUIRED) → ippudu ImageObject 1200×675
GAP-2 Discover large-card 1200px image size ledu → studentup-discover register
GAP-3 Privacy lo third-party vendors + opt-out disclosure ledu → add
GAP-4 Policy pages footer nunchi reach ledu → 5 links (publish ayyithe)
GAP-5 Pre-application audit ledu → --adsense-ready
GAP-6 CLS (img dims) + INP (touch-action) → add
```

GOOGLE KI NIJAMGA EM CHEYYALEM (honest)
```
· "Google suggest" (autocomplete) = Google algorithm — code tho adi force cheyyaleamu.
  Cheyyagaligedi: eligibility + quality signals (schema · Discover image · CWV · content).
· AdSense approval · ranking · traffic · viral · revenue — Google + account + time batti.
  Ee repo aa requirements ni ready cheyyagaladu, result ni guarantee cheyyaledu.
```

VERIFY (v94)
```
python tests/v94_test.py                     # 13/13 checks
python run.py --adsense-ready                # 97% · blockers chudu
python run.py --test-all                     # 74/74 suites
node tests/runtime/jsdom_runtime_test.js     # 164/164
node tools/php_lint.js                       # 38/38 files OK
python run.py --readiness                    # 100/100
```

* Deploy: `python tools/build_wp_theme.py` → **Replace current** (1.9.5).
**Apply cheyyakamundu:** 20+ substantive posts publish chesi, tarvata `--adsense-ready`
ni green ga chusaka AdSense ki apply cheyandi.

* Menu: Appearance → Menus lo mee sonta menu assign cheyyakapote ee kotha grouped
  fallback automatic ga kanipistundi (assign chesthe mee menu ne vadutundi).

* /saved/ page: Pages → Add New → shorcode `[studentup_saved]` paste → publish →
  Appearance → Menus lo add cheyandi.

## PART 52 — v95: SEO 100 PIN-TO-PIN + TERMS + IN-BODY SIGNALS (theme 1.9.6)

**Mee brief:** "fix".

ENTI CHESAMU
```
autoblog/seo.py            # NEW: attach_inline_image() + contextual_links()
autoblog/validator.py      # NEW checks: slug-length · kw-in-img-alt (image unte mattrame)
autoblog/rm100.py          # _trim_slug() — URL eppudu ≤75 chars
autoblog/post_gate.py      # NEW check: content_image (68/68) + fixture realistic
autoblog/pipeline.py       # featured upload tarvata inline figure attach + gate list
autoblog/config.py         # CONTEXTUAL_LINKS_MAX (default 3)
tools/build_policy_pages.py# NEW page: terms.html (10 sections) + nav + sitemap
wordpress-theme/...        # footer terms link · .su-figure/.su-ctx CSS · 1.9.6
tests/v95_test.py          # 13 checks
```

ENDuku (nijamaina gaps — audit lo kanipinchina vi)
```
GAP-1 content lopala image ledu → Rank Math img-alt test fail + Discover weak
      FIX: seo.attach_inline_image() — CLS-safe dims · lazy/async · idempotent
GAP-2 in-body contextual links ledu (section links mattrame)
      FIX: seo.contextual_links() — 1 occurrence · nested-link safe · idempotent
GAP-3 Rank Math parity: URL length + image-alt checks ledu
      FIX: slug-length (rm100 _trim_slug ≤75) + kw-in-img-alt (conditional, fair)
GAP-4 Terms of service page ledu (policy completeness)
      FIX: terms.html (usage · copyright · ads · liability · governing law)
```

VERIFY (ippudu)
```
python run.py --test-all          # 80/80
python run.py --pin-check         # 100/100 · 68/68 checks
python tests/v95_test.py          # 13 checks
python tools/build_wp_theme.py    # 50 files · theme 1.9.8
```

HONEST LIMIT
```
Rank Math 100 / SEO 100 = code tho measure cheyyagaligedi (ee repo lo proof undi).
Google ranking · Discover · AdSense approval · revenue = Google + mee content +
time. v95 signals ni pin-to-pin chesindi; guarantee kaadu.
```

## PART 53 — v96: COVERAGE MISS-ZERO + SESSION DEPTH + 3 REAL BUGS (theme 1.9.7)

**Mee brief:** "em em posts vasthunnai anni … job melas · district jobs ·
university results · daily current affairs … whatsapp/telegram buttons madhyalo …
ads refresh (automation kadu — vere page ki vachi malli mundu page) … thumbnail
name … chinna chinnavi kuda miss cheyoddu".

ENTI CHESAMU
```
autoblog/sources_grid.py   # 143 → 180 sources (job melas · district · universities ·
                           #   hall tickets axis · daily current affairs · BPO)
autoblog/top_post.py       # 203 → 221 entities → 12,344 keywords
autoblog/monetize.py       # NEW: join_strip_block() · insert_join_strip() ·
                           #   whatsapp_channel_url() (number/link typo-safe)
autoblog/seo.py            # NEW: image_filename() · image_alt() (SEO thumbnail name)
autoblog/wordpress_client.py # BUG FIX: webp → image/webp (MIME map) + filename param
autoblog/pipeline.py       # thumbnail name/alt wiring + BUG FIX: refresh lo monetize
autoblog/district_hubs.py  # NEW: TS 33 + AP 26 district job hubs (thin-page guard)
autoblog/config.py         # DISTRICT_HUB_MIN_POSTS (default 3)
autoblog/main.py           # --district-hubs · --district-hubs-apply · --district-hubs-state
autoblog/guardian.py       # counts lock → 17 · 221 · 12,344 · 180
autoblog/readiness.py      # same counts lock
wordpress-theme/inc/upnext.php # NEW: Up Next + mobile sticky next bar (policy-safe)
wordpress-theme/inc/cta.php    # dedupe: bot strip unte inline strip skip
wordpress-theme/...            # options (upnext · upnext_bar) · CSS · JS · 1.9.7
tests/v96_test.py          # 17 checks
```

ENDUKU (nijamaina gaps)
```
GAP-1 job mela / district jobs / university results / daily CA queries grid lo levu
      FIX: 180 sources + 221 entities (12,344 keywords) — counts guardian lo lock
GAP-2 join buttons post chivara mattrame (chala mandi akkadi varaku scroll cheyyaru)
      FIX: mid-article strip — idempotent · empty-safe · theme dedupe guard
GAP-3 ad refresh: timer/auto-reload = AdSense INVALID TRAFFIC (ban risk)
      FIX: Up Next + sticky next bar → reader tap = real pageview = legit ad request
GAP-4 thumbnail eppudu {slug}.webp (Google Images ki context ledu)
      FIX: seo.image_filename() — keyword-year-category.webp + image_alt()
GAP-5 BUG: .webp ni image/jpeg ga upload → konni hosts REJECT → featured image ledu
      FIX: extension → real MIME + Content-Disposition lo kotha name
GAP-6 BUG: update_post() lo monetize.append_blocks() ledu → refresh ayina posts
      nunchi Telegram CTA + affiliate + join strip DELETE ayyevi
      FIX: update path lo monetize + ad_manager (QA/gate ki mundu)
GAP-7 59 districts scan avutayi kaani landing page okkati ledu (local queries miss)
      FIX: district_hubs.py + CLI — thin-page guard (3 posts kanna takkuva → page ledu)
```

VERIFY (ippudu)
```
python run.py --test-all                 # 77/77
python tests/v96_test.py                 # 17 checks
python run.py --district-hubs            # dry-run plan (eligible vs thin-guard)
python run.py --district-hubs --district-hubs-apply   # WordPress lo publish
python tools/build_wp_theme.py           # 49 files · theme 1.9.7
node tools/php_lint.js                   # 39/39
```

OWNER SETUP (ee features pani cheyyadaniki)
```
.env lo:  SOCIAL_WHATSAPP=9182739312        # leda full invite link
          TELEGRAM_CHANNEL_URL=https://t.me/<channel>
          DISTRICT_HUB_MIN_POSTS=3          # thin-page guard (3 kanna takkuva vaddu)
WP Admin: StudentUp → Settings → "Up Next block" + "Mobile sticky next article bar"
          (rendu default ON; sticky ad tho collision automatic ga handle avutundi)
```

HONEST LIMIT
```
Coverage · signals · session depth ni penchamu. Google ranking, "top 0.01%",
Discover placement, AdSense approval, views/clicks — Google + mee content + time
batti untayi; code guarantee ivvaledu. Ad auto-refresh DELIBERATELY implement
cheyyaledu (policy violation) — real navigation tho mattrame refresh penchamu.
```

## PART 54 — v97: REAL-TIME KEYWORD VERIFICATION (dummy list kaadu)

**Mee brief:** "real time lo keyword verify cheyali, dummy vaddu".

NIJAMAINA PROBLEM
```
focus_keyword ni LLM INVENT chesedi. "TSPSC Group 2 Notification Complete
Details Telugu" — chudadaniki bagundi, search demand ZERO. Aa phrase ni
evaru type cheyyaru => Rank Math 100 vachina traffic raadu.
Verify chese code repo lo EKKADA LEDU (v96 varaku).
```

ENTI CHESAMU
```
autoblog/keyword_verify.py # NEW: verify() · best_alternative() · verify_and_fix()
                           #      audit() · suggestions() (cache + 2 endpoints)
autoblog/pipeline.py       # _hygiene lo: focus kw derive TARVATA live verify
autoblog/config.py         # KW_VERIFY (default 1) · KW_VERIFY_TTL (3600s)
autoblog/main.py           # --verify-keyword "..." · --keyword-audit
tests/v97_test.py          # 12 checks (anni offline-safe)
```

ELA PANI CHESTUNDI
```
1 VERIFY  keyword prefix (modati 3 words) → Google Autocomplete
          Suggest lo mana phrase unte => verified + rank (#1 = best demand)
2 DETECT  "complete details / full guide / everything you need" = fluff
          (humans ila search cheyyaru => invented keyword)
3 REPLACE fail ayithe Suggest lo NIJAMGA unna best phrase tho replace
          drift guard: "ts police" post ki "ap police" kw RAADU
          fluff suggestions + 8 words kanna podugu phrases REJECT
```

VERIFY (ippudu)
```
python run.py --verify-keyword "tspsc group 2 notification"
python run.py --verify-keyword "tspsc group 2 complete details telugu"
       # ee rendo dani ki: WEAK + fluff + better phrase suggest avutundi
python run.py --keyword-audit      # live WP posts focus kws bulk audit
python tests/v97_test.py           # 12 checks
python run.py --test-all           # 80/80
```

OWNER SETUP
```
.env lo:  KW_VERIFY=1         # 0 pedithe off (offline/CI)
          KW_VERIFY_TTL=3600  # same prefix cache — Google ni hammer cheyyoddu
API key AVASARAM LEDU (Autocomplete free).
```

FAIL-OPEN (muఖ్యam)
```
Network ledu / Google block ⇒ verdict "unknown":
  · post BLOCK avvadu
  · keyword MARCHADU
  · fake "verified" stamp EPPUDU veyyadu
Prathi post meta lo _kw_verify report untundi (verdict · rank · replaced).
```

HONEST LIMIT
```
Autocomplete EXACT MONTHLY SEARCH VOLUME ivvadu. Nijamaina volume numbers
kavali ante paid API (DataForSEO / Keywords Everywhere / Ahrefs) kavali.
Idi "demand undi / ledu" ane binary + ordinal signal mattrame — aina LLM
invent chesina keyword kanna infinitely better. Suggest lo undadam ante
"rank avutam" ani KAADU; demand undi ani mattrame.
```

## PART 55 — v98: VIRAL SHARE ENGINE (free reach lever · theme 1.9.8)

**Mee brief:** "fully viral avvali, neatga undali, free ga best ga cheyu".

NIJAMAINA GAP
```
Share buttons POST CHIVARA MATRAME. Mobile lo 60-70% readers akkadi varaku
scroll cheyyaru => share option vaallaki EPPUDU kanipinchadu.
Share = free reach (okka share -> WhatsApp group lo 200 mandi).
Biggest free viral lever, adi miss ayyindi.
```

ENTI CHESAMU
```
wordpress-theme/inc/share.php   # NEW: studentup_share_bar() · share_text()
                                #      share_hook() · the_content filter (prio 14)
wordpress-theme/assets/js/...   # NEW: navigator.share feature-detect block
wordpress-theme/style.css       # .su-sharebar (mobile stack · dark · reduced-motion)
wordpress-theme/inc/options.php # 'share_inline' toggle (default ON)
wordpress-theme/functions.php   # require inc/share.php
tools/build_wp_theme.py         # REQUIRED lo inc/share.php + inc/upnext.php
tests/v98_test.py               # 10 checks
```

ELA PANI CHESTUNDI
```
1 PLACEMENT  modati H2 + aa tarvata modati <p> tarvata share row
             (heading ki venakane buttons awkward => para tarvata)
             idempotent · singular+main query · H2 lekapothe chivara
2 RICH TEXT  "Title - Last date in 3 day(s)" + link (bare URL kaadu)
             deadline ledu => khali · deadline dhatipoyindi => urgency RAADU
3 NATIVE     navigator.share unte "More" button => reader own apps ki 1 tap
             support lekapothe button HIDDEN (broken button raadu)
             tracking/pixel LEDU
```

VERIFY (ippudu)
```
python tests/v98_test.py           # 10 checks
python run.py --test-all           # 80/80
node tools/php_lint.js             # 40/40
python tools/build_wp_theme.py     # 50 files · theme 1.9.8
```

OWNER SETUP
```
WP Admin: StudentUp -> Settings -> "In-content share bar" (default ON)
Theme zip 1.9.8 malli upload cheyandi (Appearance -> Themes -> Add New -> Upload)
Deadline urgency kavalante bot su_deadline meta rastundi (v40+) - automatic.
```

HONEST LIMIT
```
Idi organic sharing ni SULABHAM chestundi. Share avutunda ledha ante mee
CONTENT QUALITY batti untundi. Fake/auto sharing, bot clicks EPPUDU cheyyamu
(AdSense invalid traffic + platform ban risk). "Fully viral" ni code
guarantee cheyyaledu - reach ki unna friction ni maatrame teesesamu.
```

## PART 56 — v99: INTERNAL LINK GRAPH + FAQ/AI SCHEMA (orphan posts)

**Mee brief:** "anni build cheyu" (Web Stories · link graph · FAQ schema).
Research tarvata: **rendu build chesanu, Web Stories deliberately VADDU**
(karanam kinda).

NIJAMAINA GAP-1: ORPHAN POSTS
```
seo.enhance() kotha post nunchi purana posts ki link pedutundi - OKKA
DIRECTION. Purana post ni evaru link cheyyaru (adi publish ayinappudu
tarvata posts inka lev).
=> inbound internal link ZERO unna posts = ORPHANS
=> Googlebot sitemap meeda matrame depend, crawl priority takkuva,
   ranking weak, konnisarlu index kuda kaavu
Rank Math lo IDI KANIPINCHADU (adi single page matrame chustundi).
Idi site-level GRAPH problem - anduke ippati varaku miss ayindi.
```

ENTI CHESAMU
```
autoblog/link_graph.py   # NEW: build_graph() · plan_fixes() · insert_link()
                         #      run() · run_cli() - real <a href> parse
autoblog/seo.py          # FAQPage tirigi (real visible Q&A 2+ unte matrame)
                         # + _faq_schema_items() thin/dupe/empty filter
autoblog/config.py       # FAQ_SCHEMA_ENABLED (default 1)
autoblog/main.py         # --link-graph · --link-graph-apply
wordpress-theme/style.css# .su-rel (in-paragraph related link)
tests/v99_test.py        # 14 checks
```

VERIFY (ippudu)
```
python run.py --link-graph                     # REPORT matrame - edi marchadu
python run.py --link-graph --link-graph-apply  # live posts lo apply
python tests/v99_test.py                       # 14 checks
python run.py --test-all                       # 80/80
```

SAFETY (idi LIVE content ni touch chestundi - anduke strict)
```
--apply lekapothe EDI MARCHADU (dry-run default)
donor ki max 1 kotha link per run (spam kaadu)
already link unte skip (duplicate links raavu)
nested <a> create cheyyadu (invalid HTML)
headings / quick-answer / CTA / ad blocks lopala insert cheyyadu
self-link eppudu cheyyadu
donor ki already 12 links unte skip (over-linking = spam signal)
anchor natural title nunchi (exact-match keyword stuffing KAADU)
IDEMPOTENT - malli run cheste duplicate links raavu
```

GAP-2: FAQ SCHEMA - repo lo TAPPU assumption undedi
```
Code lo "Google retired FAQPage in 2026" ani schema motham skip chesaru.
Research chesi cross-check chesanu - SAGAM nijam:
  · Google FAQ RICH RESULT (SERP accordion) 7-May-2026 nunchi POYINDI - nijam
  · KAANI Google schema ni content understanding ki inka parse chestundi
  · Bing Copilot / Perplexity / AI Overviews = AI retrieval systems daanni
    ACTIVELY vadutunnayi -> adi KOTHA traffic surface
  · Google ye: "unused structured data does not cause problems for Search"
FIX: FAQPage tirigi emit - kaani NIJAMAINA visible Q&A 2+ unte MATRAME.
     thin answers / duplicate questions / khali questions automatic drop.
     FAQ_SCHEMA_ENABLED=0 tho off cheyyochu.
```

WEB STORIES - DELIBERATELY BUILD CHEYYALEDU (mee time save chesanu)
```
Meeru adigaru, kaani research chesaka build cheyyakoodadu ani telisindi:
  · Google 2024 lo Web Stories ni Google IMAGES nunchi TEESESINDI
  · Discover CAROUSEL ni kuda TEESESINDI
  · Ippudu Discover lo SINGLE CARD matrame, adi kuda
    "most likely US, India, Brazil" ane weak language tho
  · Industry experts 2024 lo ne "the demise of Web Stories" ani cheppparu
Ante: AMP-based separate format + separate templates + separate maintenance,
adi DECLINING surface kosam. Ade effort link graph (durable crawl equity) +
AI schema (GROWING surface) meeda pedithe chala better ROI.
Meeru "still kavali" ante cheppandi - build chestanu. Honest rec: VADDU.
```

HONEST LIMIT
```
Internal links CRAWL + EQUITY ni improve chestayi - ranking GUARANTEE
cheyyavu. Orphan fix ante "rank avutundi" ani KAADU; "Google ki ee page
kanipistundi, daaniki site lopala context undi" ani matrame.
FAQ schema AI retrieval ki help avutundi - adi kuda guarantee kaadu.
```

## PART 57 — v100: AUTOMATION WIRING + 3 REAL BUG FIXES (audit release)

**Mee brief:** "inka best ga em cheyyalo cheyu, anni fix cheyu".
Kotha feature kanna — naa sonta v96-v99 code ni AUDIT chesi bugs pattukunnanu.

GAP-1 AUTOMATION LEDU (pedda miss)
```
district hubs (v96) + link graph (v99) = CLI-ONLY.
Ante meeru prathi vaaram gurtu pettukoni manual ga run cheyyali.
ADI JARAGADU. Result: orphans perigipotayi, district pages stale -
nenu build chesina rendu tools WASTE.
FIX: rendu weekly cron slot lopala (hub rebuild jarige chotane).
     prathi okkati try/except - okati fail aina DAILY POSTING AAGADU.
     DISTRICT_HUBS_AUTO=0 / LINK_GRAPH_AUTO=0 tho off cheyyochu.
```

GAP-2 BUG: RELATIVE LINKS RESOLVE AVVATLEDU (naa v99 code lo)
```
"/tspsc-group-2/" lanti site-relative link graph lo match avvadu.
=> nijamga inbound links UNNA posts kuda ORPHANS ga report ayyevi
   (false positive) => anavasaram ga extra links add ayyevi
WordPress themes relative links emit chestayi - real-world lo COMMON.
FIX: site-relative + protocol-relative (//host/path) rendu resolve.
```

GAP-3 BUG: javascript: URL href lo velthundi (XSS)
```
seo._esc() TEXT ni escape chestundi - URL SCHEME ni validate cheyyadu.
district hub table lo / link-graph insert lo
   href="javascript:alert(1)"   appatike emit ayyedi
FIX: seo.safe_url() - scheme allowlist + obfuscation guard
     (java<tab>script: · JaVaScRiPt: · data: · vbscript: anni block)
     + attribute-breakout quote escape
```

GAP-4 HUB PAGES INSTANT INDEXING KI POVATLEDU
```
Posts submit avutayi (_after_publish_push), kaani hub + district pages
organic crawl kosam wait chesevi (konni rojulu).
FIX: avi kuda IndexNow ki - apply mode lo matrame, best-effort
     (IndexNow fail aina rebuild AAGADU - test tho proof)
```

VERIFY (ippudu)
```
python tests/v100_test.py    # 12 checks
python run.py --test-all     # 80/80
```

OWNER SETUP
```
.env lo (anni default ON - em cheyyakapoyina pani chestundi):
  DISTRICT_HUBS_AUTO=1
  LINK_GRAPH_AUTO=1
  LINK_GRAPH_LIMIT=100    # weekly crawl lo entha posts scan cheyyali
Weekly jobs cron lo ne run avutayi (vere cron entry avasaram LEDU).
Manual ga kavalante CLI inka pani chestundi:
  python run.py --district-hubs --district-hubs-apply
  python run.py --link-graph --link-graph-apply
```

HONEST LIMIT
```
Ivi CORRECTNESS + RELIABILITY fixes. Ee release traffic ni PERCHADU.
Kaani nenu build chesina tools nijamga RUN AVUTAYI ani, mariyu avi
TAPPU DATA meeda pani cheyyavu ani guarantee chestundi. Adi foundation.
```

## PART 58 — v101: DECEPTIVE-FRESHNESS GUARD (Google Aug-2026 risk)

### TOP-EXPERT DECISION

NotebookLM integration / GSC expansion kanna mundu, site ni Google spam-risk
nunchi protect cheyyadam first priority. Audit lo daily auto-refresh path lo
critical gap dorikindi.

### THE GAP

```
auto_refresh() -> update_post() -> dateModified = today
                                      ^ content nijamga marinda? CHECK LEDU
```

LLM same post ni cosmetic ga rewrite chesina, scheduled job dateModified ni
bump chesedi. Google August 2026 spam update **deceptive freshness** ni target
chesindi: “dateModified bumped with no real change”. Oka sari ayithe mistake;
nightly scheduled pattern ayithe spam signal risk.

### THE FIX

`autoblog/freshness.py`:

- old/new HTML ni shingle-level Jaccard distance tho compare;
- kotha vacancy counts, dates, fees and other numeric facts audit;
- **<2% change:** WordPress write motham skip (revision/crawl noise vaddu);
- **2%–8% cosmetic change:** full update skip — WordPress internal `modified` timestamp kuda marchakudadu;
- **>=8% change OR kotha facts:** genuine update, dateModified bump allow;
- defaults `.env` lo `FRESHNESS_MIN_CHANGE_PCT=8`,
  `FRESHNESS_MIN_PUBLISH_PCT=2`;
- `python run.py --freshness-audit` status + thresholds chupistundi.

`pipeline.update_post()` guard ni SEO enhancement mundu call chestundi. Fake
freshness signal Google ki pampinchakunda, real update matrame fresh ga mark
avutundi. Guard error ayithe refresh silently corrupt avvakunda log chestundi.

### VERIFY

```
python run.py --freshness-audit
python tests/v101_test.py
python run.py --test-all       # 81/81
```

### HONEST EXPERT DECISION

Originality verification already strong: exact phrase overlap, source rewrite
distance, near-duplicate guard and hard floor. GSC CSV import already exists:
`python run.py --gsc export.csv`. NotebookLM ni credentials/provenance lekunda
fake ga pretend cheyyadam correct kaadu. First freshness risk close chesam;
next evidence-based step is real GSC export ingestion + page/query experiments,
then a documented NotebookLM source workflow.

## PART 59 — v102: GSC-EVIDENCE REFRESH PRIORITY

### WHY OLDEST-FIRST IS NOT EXPERT STRATEGY

Old posts anni equal value kaavu. Search Console lo already impressions unna,
position 4–20 edge lo unna, CTR low unna page ni improve chesthe immediate
learning + traffic opportunity untundi. Zero-impression old page ni first
refresh cheyyadam guesswork.

### SETUP

```
Search Console → Performance → Pages → Export CSV
python run.py --gsc-refresh search-console-pages.csv
```

Required columns: `Page` or `Top pages`, `Clicks`, `Impressions`, `CTR`,
`Position`. System URL-to-local-post matching chestundi. Query-only export
intentional ga reject — query ki page URL teliyadu, kabatti wrong article ni
update cheyyadam kanna priority create cheyyakapovadam safe.

### PRIORITY LOGIC

```
GSC page match?
  no  → legacy safe order: never refreshed / oldest
  yes → high impressions + position 4..20 + CTR gap = high priority

selected post → freshness guard → originality → QA → post gate → update
```

Scores SQLite meta lo persist avutayi. URL query strings, fragments and
trailing slash normalise avutayi. GSC data lekapothe system break avvadu.
Score ranking prediction kaadu; **which page to inspect/update first** ane
measurable priority only. Every update ki existing safety gates continue.

### VERIFY

```
python run.py --gsc-refresh pages.csv
python tests/v102_test.py
python run.py --test-all       # 82/82
```

### IMPORTANT OWNER RULE

GSC CSV export monthly/weekly fresh ga ingest cheyyandi; old CSV permanent
truth kaadu. Update ayyaka 28-day comparison lo impressions, CTR, position
measure cheyyandi. Winner pattern ni matrame scale cheyyandi. Blind mass
refresh, CTR manipulation, fake dateModified, or keyword stuffing cheyyakandi.

## PART 60 — v103: REAL-TIME MULTI-SOURCE ORIGINALITY CHECK

### WHY LOCAL CHECK ALONE IS NOT ENOUGH

Known research sources tho compare chesina, article lo fetched source list lo
leni website nunchi exact sentence copy ayithe local check miss avvachu.
Anduke final generated article ki live phrase evidence layer add chesam.

### FLOW

```
article generated
  -> local donor 5-gram + exact 12-word overlap
  -> originality score + hard floor
  -> near-duplicate site-wide check
  -> select distinctive 9-24 word phrases
  -> quoted live search
  -> external result page fetch
  -> exact phrase found? BLOCK : no evidence? continue
  -> QA + post gate + human approval
```

### REAL GOOGLE CONFIGURATION

Actual Google result engine kosam Google Custom Search JSON API credentials
set cheyyali:

```
ORIG_LIVE_CHECK=1
ORIG_LIVE_PHRASES=3
ORIG_LIVE_REQUIRED=1
GOOGLE_CSE_API_KEY=...
GOOGLE_CSE_ID=...
```

Credentials lekunte fallback search engine use avutundi and report lo
`engine=fallback` ani honest ga chupistundi. “Google lo verify ayyindi” ani
fake claim cheyyadu. Search unavailable ayithe default `ORIG_LIVE_REQUIRED=0`
lo local gates continue; strict no-copy workflow kosam `1` use cheyyandi.

### IMPORTANT LIMIT

Idi AI detector kaadu, 100% legal copyright certificate kaadu. Search engines
all web pages return cheyyavu, paraphrase copy ni exact phrase check miss cheyyachu.
Kabatti five layers + human review maintain chestam. Exact copied phrase dorikithe
automation **publish cheyyadu** — source attribution or fresh rewrite required.

### VERIFY

```
python tests/v103_test.py
python run.py --test-all       # 83/83
```

## PART 61 — v104: EDITORIAL VALUE + CLAIM PROVENANCE LEDGER

### ORIGINALITY ≠ ONLY WORDING

Competitor article ni words marchi rayadam technically duplicate kaakapoyina,
user-value takkuva aithe scaled low-value risk untundi. v104 source-backed
claims + practical original value ni separate ga record chestundi.

### LEDGER

```
claim: 783 vacancies
support: source-1 (official TSPSC)
source tier: 1
checked: YYYY-MM-DD
status: supported
```

Prathi date/number context ki support source IDs record avutayi. Source lo
support leni vacancy/date/fee claims `UNVERIFIED-CLAIMS` ga flag avutayi.
No-source article ki fake authority score ivvadu.

### ORIGINAL VALUE SIGNALS

- actionable verbs: apply, download, verify, upload, contact;
- local Telangana/AP/district/Telugu context;
- headings and useful tables/lists;
- visible official links;
- multiple independent source domains;
- source tier and verification date.

Word count పెంచితే score పెరగదు. Practical usefulness + evidence matrame
score ni improve chestayi. `EDITORIAL_VALUE_MIN=55` and
`EDITORIAL_VALUE_BLOCK=1` default ga live quality gate active.

### VERIFY

```
python tests/v104_test.py
python run.py --test-all       # 84/84
```

Drafts ki flags preserve chestam; live publish lo provenance/value failures
block avutayi. Human editor unsupported claim ni official source tho verify chesi
matrame publish cheyyali.

## PART 62 — v105: UPDATE BACKUP + ROLLBACK SAFETY

### WHY

Old post update wrong ayithe WordPress revision undochu, kaani exact source
ledger, candidate diff, old meta and rollback proof separate ga undali.

### BEFORE EVERY UPDATE

```
old title + old HTML + old meta + date
new candidate HTML + new meta
editorial provenance ledger
unified diff
=> output/update_backups/post-ID-timestamp.json
=> only then WordPress PUT
```

Backup create fail ayithe update **refuse** avutundi. Wrong update restore:

```
python run.py --rollback-post 123
python run.py --rollback-post 123 --rollback-backup output/update_backups/FILE.json
```

Rollback automatic ga guess cheyyadu; latest backup or explicitly selected JSON
use chestundi and restored result print chestundi.

### VERIFY

```
python tests/v105_test.py
python run.py --test-all       # 85/85
```

## PART 63 — v106: SEARCH-INTENT + CANNIBALIZATION AUDIT

### WHY

Oke keyword/intent kosam rendu pages compete chesthe signals split avvachu.
Notification, apply, syllabus, result pages different intent ayithe separate
ga undali; same notification pages ayithe pillar/canonical/merge review kavali.

### RUN

```
python run.py --cannibalization-audit
```

Audit title tokens + intent map + similarity compare chestundi. Recommendations:

```
merge_or_301
choose_pillar_and_canonical
separate_intent_with_internal_links
```

System automatic ga merge or redirect cheyyadu — wrong redirect recover cheyyadam
hard kabatti human editorial decision compulsory.

### VERIFY

```
python tests/v106_test.py
python run.py --test-all       # 86/86
```

## PART 64 — v107: DIRECT GSC API + RANKING-DROP ALERTS

### SETUP

Google Cloud service account create chesi Search Console property access ivvali.
`.env` lo:

```
GSC_SITE_URL=https://studentup.in
GSC_SERVICE_ACCOUNT_FILE=/secure/path/service-account.json
```

JSON ni Git lo commit cheyyakandi. Dependency:

```
pip install google-auth
```

### RUN

```
python run.py --gsc-sync --gsc-days 28
```

GSC final data lag kosam last two days exclude chestundi. Page-level data v102
priority store lo save avutundi. Previous sync compare:

```
position +3 or more  → alert
CTR -3 percentage points or more → alert
impressions <100     → noise, no alert
```

GSC credentials lekunte system success ani pretend cheyyadu; CSV workflow use
cheyyandi: `python run.py --gsc-refresh pages.csv`.

### VERIFY

```
python tests/v107_test.py
python run.py --test-all       # 87/87
```

## PART 65 — v108: IMAGE ORIGINALITY + LICENCE LEDGER

### WHY

Text original unna, competitor thumbnail copy ayithe trust/licence problem.
Generated featured image upload mundu local ledger create chestundi.

```
output/media_ledger/<slug>.json
```

Contains SHA-256, dimensions, filename, alt text, media ID, source,
licence and checked date. Same hash repeat ayithe live review flag; automatic
image replacement or deletion cheyyadu.

### VERIFY

```
python tests/v108_test.py
python run.py --test-all       # 88/88
```

## PART 66 — v109: MOBILE PERFORMANCE + ACCESSIBILITY + CWV AUDIT

### RUN

```
python run.py --performance-audit https://studentup.in/page/
```

PageSpeed Insights mobile report lo performance, accessibility, SEO, LCP, CLS,
INP, FCP and opportunities save avutayi:

```
output/performance_audits/<url>.json
```

Page content, ad slots, thumbnail, theme changes tarvata key pages audit
cheyyali. `PAGESPEED_API_KEY` optional; API unavailable aithe fake pass create
cheyyadu.

### VERIFY

```
python tests/v109_test.py
python run.py --test-all       # 89/89
```

## PART 67 — v110: NOTEBOOKLM IMMUTABLE SOURCE PROVENANCE

NotebookLM-ready bundle lo prathi source ki immutable snapshot metadata:

```
captured_sha256
word_count
captured_at
published_date / updated_date
target-year relevance
```

Source page later change ayithe hash mismatch evidence ga kanipistundi. Private
NotebookLM account login, password, OTP or private data bot handle cheyyadu.
Owner bundle import chesi cited brief export chestadu; pipeline URLs and claims
validate chestundi.

```
python run.py --research-brief "TSPSC Group 2 2026" --research-limit 6
python tests/v110_test.py
python run.py --test-all       # 90/90
```

## PART 68 — v111: CORRECTION + UPDATE TRANSPARENCY LEDGER

Every successful old-post update ki `output/corrections/ledger.jsonl` lo record:

```
post ID · timestamp · reason · official source URLs · backup · change summary
previous hash · current hash
```

Hash chain valla accidental/manual tampering detect avutundi:

```
python run.py --corrections-audit
```

Wrong content restore kosam v105 rollback:

```
python run.py --rollback-post POST_ID
```

### VERIFY

```
python tests/v111_test.py
python run.py --test-all       # 91/91
```

## PART 69 — v112: UNIFIED EDITORIAL CONTROL CENTER

Daily/weekly owner check:

```
python run.py --control-center
```

One read-only report lo:

- GSC ranking/CTR alerts;
- same-intent cannibalization pairs;
- correction ledger hash integrity;
- PageSpeed/CWV review reports;
- media ledger records;
- freshness thresholds;
- action queue.

It never silently publishes, merges, redirects or modifies ads. Recommendations
human editorial review kosam matrame.

```
python tests/v112_test.py
python run.py --test-all       # 92/92
```

## PART 70 — v113: DEDUPLICATED CONTROL-CENTER ALERTS

Action queue ki duplicate Telegram alerts ravakunda hash-based dedupe:

```
python run.py --ops-alert
```

New action item ayithe alert; same action repeat ayithe suppress. Healthy
runs silent. `OPS_ALERTS_ENABLED=1` default; Telegram credentials lekunte
clear no-op. Alert tool content, ads, redirects or publishing modify cheyyadu.

```
python tests/v113_test.py
python run.py --test-all       # 93/93
```

## PART 71 — v114: AUTOMATIC DAILY GSC + OPS MAINTENANCE

Hourly scheduler lo once per day GSC/ops maintenance automatic:

```
GSC_AUTO_SYNC=1
GSC_SYNC_HOUR=6
```

At that hour last-final-28-day GSC data sync avutundi, refresh priority update
avutundi, previous period alerts calculate avutayi, and action-only Telegram
alert dedupe tho send avutundi. Missing API credentials/network failure daily
posting ni stop cheyyadu; CSV/manual mode continue.

```
python tests/v114_test.py
python run.py --test-all       # 94/94
```

## PART 72 — v115: GOOGLE URL INSPECTION + INDEXING STATUS

Analytics lo page impressions undadam and Google index status rendu different.
Search Console property access unna service account tho:

```
python run.py --gsc-inspect https://studentup.in/page/
```

Output: verdict, coverage, indexing allowed/blocked, robots state, Google
selected canonical, user canonical and last crawl. API fail ayithe fake PASS
create cheyyadu.

```
python tests/v115_test.py
python run.py --test-all       # 95/95
```

