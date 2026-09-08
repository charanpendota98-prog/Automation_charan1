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

## 🔧 Round 3: 20+ Chinna Mistakes Fix + Features (v3)

**Bugs fix chesayi:**
1. **Search double-encoding bug** — DDG query `%2520` la pampindi → ippudu clean
2. **Dry-run dedupe pollution** — test posts DB lo block cheyyevi → fix
3. **Disk full risk** — upload ayyaka local images delete (`KEEP_IMAGES=0`)
4. **systemd timeout** — research mode long runs kosam 600s → 1200s
5. **Midnight race** — schedule check lo time double-read fix
6. **Old DB upgrade** — new columns automatic add (DB delete avvakkarledu)
7. **Meta DB growth** — 7+ rojula purana keys automatic cleanup

**Kotha features:**
8. **Auto-categorization** — URL mode lo Telugu+English keywords tho category automatic (SSC job → Govt Jobs, scholarship → Scholarships...)
9. **Scheduler Watchdog** — bot 26 hours run avvakapote Telegram ki ⚠️ alert (roju okke sari, false spam ledu)
10. **Quality trend tracking** — avg QA score + avg originality % — `/stats` lo mariyu `--status` lo kanipistundi
11. **Title hygiene** — 85+ chars title → seo_title automatic swap (Rank Math penalty avoid)
12. **Tag hygiene** — duplicates remove, 32 char cap, max 8
13. **Meta description fallback** — short aite quick_answer/first para nunchi auto-build
14. **`--process-queue N`** — queue lo N URLs okka command lo bulk process
15. **`--url --category X`** — URL mode lo category force cheyochu
16. **Search fallback endpoint** — DDG block aite lite.duckduckgo.com automatic try
17. **Image palette variety** — kotha image prathi sari different colors (repeat ledu)
18. **WhatsApp daily digest** — roju summary WhatsApp ki kuda
19. **`/pending` draft count** — "12 drafts unnayi — latest 5 isthunnanu"
20. **sources_queue.txt auto-create** — setup script ne file ready chestundi
21. **Image disk cleanup** — valla footage megabytes save
22. **`.env` docs** — ani kotha keys documented

## 🔄 Content Refresh: Published Post ni Improve cheyadam (v4)

Oka post already publish ayyaka, **kotha information dorikithe** danini same post lo add chesi better ga cheyochu — **URL maradu** (Google lo freshness boost, SEO juice safe!):

### Method 1: Telegram (easiest)
- Prathi draft/post message lo **🔄️ Improve + Research** button — one tap lo:
  bot internet lo kotha info search chesi → merge chesi → same post update
- Leda command: `/update POST_ID` (manual ga kotha source isthe: `/update 123 https://site.com/new-info`)

### Method 2: Command line
```bash
# Auto research (post title meeda web search):
.venv/bin/python run.py --update 1234

# Specific kotha source URL tho:
.venv/bin/python run.py --update 1234 --add-source "https://site.com/new-notification"
```
(`POST_ID` — WordPress editor URL lo `post=1234` ga kanipistundi)

### Update flow lo em avtundi?
1. Existing post content teesi → auto web research / mi source URL fetch
2. Gemini: **kotha facts matrame add** chestundi (old info remove cheyadu, title/URL same)
3. Fresh SEO re-enhance (kotha TOC, Quick Answer, Last Updated date, schema — duplicates levu)
4. Rank Math meta refresh + IndexNow ping + Telegram ki "🔄 POST UPDATED" message
   (kotha info em add ayyindo "update notes" lo kanipistundi!)

> SEO Tip: Google "content freshness" ni premistundi — 2-3 months old top posts ni monthly once refresh cheyandi. Rankings long-term lo stable ga untayi.

## 📰 Trending Stories (Listicles) + Daily Auto-Refresh + Ads (v5)

### Trending Stories — Adda247 style "Top 10" posts
- **Top 10 Central Government Jobs**, **Top 7 Scholarships**, **Top 5 Railway Jobs**, **Top 10 Work From Home**... 16 rotating ideas
- Roju **LISTICLES_PER_DAY=2** stories automatic (scheduled slots lo) — trending traffic ki best
- **ItemList JSON-LD schema** automatic (4th schema!) — Google lo list rich results eligibility
- Manual: `.venv/bin/python run.py --listicle "Top 10 Bank Jobs"` (topic ivvakkarledu — bot idea pick chestundi)

### Daily Auto-Refresh (Google freshness signal)
- Prathi roju **AUTO_REFRESH_HOUR** (default 21:00) lo **purana published posts** (14+ days) ni select chesi
  kotha web research tho **refresh** chestundi (never-refreshed posts ki priority)
- Rankings long-term lo stable — top websites idi exact ga chestayi
- Manual: `.venv/bin/python run.py --auto-refresh 3`

### In-Content Ads (ADSENSE-SAFE positions)
- `AD_SHORTCODE=[quads id=1]` set cheste — bot 3 policy-safe positions lo ads insert chestundi:
  intro tarvata, mid-article, FAQ mundu (Max 3 — accidental-click policy safe)

### ⚠️ AdSense Safety — MEERU adigina "click → new page → back → new ads" pattern GURTHU PETTANDI:
Ee pattern (**forced navigation for ad impressions**, **back-navigation ad refresh**) —
**Google AdSense policy violation**. Ban risk perigite mottam revenue pothundi.
SAFE alternatives (bot already implement chesindi):
1. ✅ In-content ads (3 safe positions) — impressions perakuthayi, policy safe
2. ✅ Listicles + Related articles + internal links — **legit pageviews peruguthayi**
   (user natural ga inko post open chestadu = kotha page = kotha ads — idi 100% allowed)
3. ✅ Daily refresh — repeat visitors ki fresh content (fresh ads automatic ga vastayi new page lo)
4. ✅ Reading time + TOC + Quick Answer — dwell time perigindi = scroll depth = viewability perugutundi
5. ✅ Site-side (dashboard cheyandi): AdSense **Auto Ads** ON cheyandi, **anchor ads** (mobile sticky)
   allow cheyandi, **Web Stories plugin** install cheyandi (stories format lo kotha ad inventory)
6. ❌ Cheyakudadu: own ads click, "click here" arrows deggara ads, timer-based ad refresh,
   back-button ad refresh, thin pages only-for-ads

## 💰 Smart Revenue Maximization (v6) — 100% Policy-Safe

### Bot automatic chestundi (already built):
| Technique | Em chestundi | Revenue impact |
|---|---|---|
| **High-CPC targeting** | `HIGH_CPC_SHARE=30` — 30% daily posts high-CPC themes (education loans, bank jobs salary, IT courses, insurance jobs) | CPC 2-5x ekkuva topics |
| **Seasonal calendar** | Month prakaram topics (Mar-May results, Jun-Jul admissions, exam season) | Traffic 3-10x seasonal spikes |
| **Channel CTA block** | Prathi post end lo "Join Telegram" CTA | Repeat visitors = free pageviews lifetime |
| **Affiliate section** | Relevant posts lo `AFFILIATE_LINKS` (rel=sponsored + disclosure) | AdSense revenue + affiliate income |
| **Long content** | 2200-3000 words | More ad slots per page |
| **Dwell time** | Quick Answer, TOC, Reading badge | Viewability-based CPC perugutundi |

### Meeru site lo cheyali (WordPress dashboard — 30 nimishalu):
1. **AdSense Auto Ads ON** — Google automatic optimal placements chestundi
2. **Anchor ads allow cheyandi** (mobile sticky) — AdSense > Ads > By ad unit
3. **Ezoic / Monumetric apply** — 10,000+ monthly pageviews ayite; AdSense RPM 50-150% perugutundi (mediation automatic)
4. **Google News Publisher submit** — 30+ quality posts unnaka; news sites ki massive Discover traffic
5. **Google Search Console submit** — sitemap add cheyandi (yoast/rankmath auto sitemap)
6. **WP-Optimize / LiteSpeed cache** — page speed = Core Web Vitals = higher ad viewability + rankings

### Revenue realistic ga ela perugutundi (honest math):
- AdSense Telugu education traffic: ~$0.5-2 RPM (1000 pageviews = $0.5-2)
- TARGET: 6 months lo 50,000 pageviews/month = $25-100/month
- 12-18 months lo 200,000+ pageviews = $100-400/month
- KEY: consistency (bot 24/7), quality (QA layer), freshness (auto-refresh) — already built!
- Affiliate + Ezoic add ayite same traffic lo 2-3x revenue

## 💸 v7: Ad Revenue Maximizer (viewability + relevance + money pages)

**Bot-side (automatic):**
- **Viewability-optimized ad slots**: after 2nd para (above-fold), after tables (natural pause), mid-article, before FAQ — users actually SEE these ads → viewable impressions perugutayi → CPC perugutundi
- **CLS-safe wrapper**: `min-height:280px` tho ad space reserve — layout shift radu → Core Web Vitals green + ad viewability better
- **`MAX_AD_SLOTS`** (default 3, long articles ki 4-5 set cheyochu — news site standard, policy safe)
- **Money-page internal linking**: traffic posts (results/admit cards) nunchi high-CPC posts (salary/loan/bank lists) ki automatic link priority — high-CPC pageviews ekkuva avtayi
- **Commercial depth prompts**: fee/salary/stipend/loan/comparison angles articles lo — relevant high-value ads attract avtayi
- **`--revenue-check` command**: bot-side + site-side setup audit — em missing o okka command lo

```bash
.venv/bin/python run.py --revenue-check
```

**Honest note:** ad CLICKS ni artificially peragalera — adi policy violation (ban). Nenu build chesindi: viewability (ads kanipistayi), relevance (value ads match), slots (eka page ki ekkuva legit slots), money pages (high-CPC views). Idi real revenue growth formula.

## ⚖️ v13: Category Priority Weighting (revenue strategy default)

`CATEGORY_PRIORITY` env (default `Govt Jobs:4,Results:3,Internships:2,Education News:2`) —
topic engine lo ee categories ki extra tickets. Strategy:
**Govt Jobs** = high-CPC ads (salary/bank content), **Results** = high search
volume (telugu students). Least-used balance + seasonal boosts untouched —
idi extra layer matrame. Marali ante `.env` lo value marchandi, code touch
avvakkarledu.

## 🧪 v12: 1000x Stress Audit + Search Console Opportunities

**1000x audit** (fuzz suite `tests/stress_test.py` — 3,800+ calls):
- optimize_slug 300× random inputs, ad-inserter 200×, JSON-LD validity 100×,
  validator 200×, XSS battery, pickers 1000×, full mock pipeline 5×
- **2 real bugs FOUND + FIXED**:
  1. `sanitize_html` XSS gap — event-handler attributes (`onclick`,
     `onerror`...) + `javascript:`/`vbscript:`/`data:` URLs strip chesanu
     (URL-research mode lo external content risk — postublish XSS zero)
  2. `optimize_slug` raw-input leak — spaces/quotes slug lo vachi
     potential URL break — defensive sanitize add chesanu

**`--gsc` — Search Console opportunities (top real revenue trick):**

```bash
# Search Console > Performance > Queries > Export CSV
.venv/bin/python run.py --gsc queries.csv
```

Striking-distance queries (impressions 100+, rank 4–20, low CTR) list
chestundi + action plan — **veeti posts improve cheyadam = fastest proven
traffic gain** (page-1 lo already unna queries — ippudu CTR matrame
peragali). Idi guess-work kadu, me own Google data.

## 🩺 v11: `--doctor` — Deployment Health Check + flaky test fix

Oracle server lo deploy chesaka bot start cheyandi mundu okka command:

```bash
.venv/bin/python run.py --doctor
```

Anni dependencies live ga verify chestundi:
- **Gemini API** — key valid aa? models endpoint live test
- **WordPress REST** — auth + categories count
- **Telegram bot** — getMe token validation (intrusive kadu)
- **IndexNow** — key format
- **Storage** — state DB + output dir writable
- **Disk** — free space (images perugutayi kada)
- Plan summary (posts/day, listicles, refresh, trends, ads)

Anni ✅ → `ALL SYSTEMS GO 🚀`. Edo fail aithe exact error chupistundi —
debug time save, deploy nunchi bot first-day failure risk zero.

Plus: listicle test flaky assertion fix (high-CPC pool ideas valid kada).

## 🔧 v10: Audit Fixes (bug fix + E-E-A-T + engagement)

- 🐛 **Visible-date bug fix** — refresh chesinappudu page meedha "Last Updated"
  badge ippudu **kotha date** chupistundi (v9 lo bug: old publish date
  chupinchindi — freshness look pothundi). Schema `datePublished` original
  preserve + visible badge + `dateModified` = today. Idi exact Google pattern.
- 👤 **E-E-A-T author schema** — Article JSON-LD lo `Person` author +
  `editor` + `worksFor` (Google E-E-A-T signal). Publisher logo
  (`SITE_LOGO_URL` set cheste `logo` kuda schema lo — rich results eligible).
- 📖 **"వీటిని కూడా చదవండి" block** — prathi article end lo 4 related posts
  (session time perugutundi + Google crawl depth + internal link juice).
- 🖼️ **Progressive JPEG** — featured images ippudu progressive render
  (mobile lo fast perceived load — CWV).

## 🔥 v9: Google-Native Traffic Pack (Discover + Trends + Freshness)

Google mida ee 3 tricks miss ayyayi — ippati varaku:

1. **Google Discover readiness** — Rank Math per-post robots
   `max-image-preview:large` (bot automatic ga pampistundi) + 1200x675
   featured images already. Discover = mobile lo lakala views (Adda247
   mukhyam ga Discover meede). Site-side kuda set cheyandi:
   Rank Math > Titles & Meta > Global Robots > Image Preview: **Large**.
2. **Google Trends daily RSS** — Google thana real-time trending searches
   free ga RSS lo istundi. Bot:
   - `run.py --trends` — India top-10 + education-relevant trends display
   - Scheduler: roju 1 post auto ga **trending education topic** meeda
     (USE_TRENDS=1). Trend ni mana education angle tho connect chestundi —
     "SSC GD Result" trend aithe aa roje SSC article!
   - Network fail → normal topic (safe fallback)
3. **Freshness dates (Google rule fix)** — refresh chesinappudu
   `datePublished` preserve + `dateModified` matrame update. Google
   guideline exact ga — mundu rendu overwrite ayyevi (freshness signal loss).

## ✍️ v8: "Article Write" Rank Math Tricks (write chesetappude score perugutundi)

Content **rastesetappudu ne** Rank Math checks pass avtaye — idhe real trick:

| Trick | Em chestundi | RM Check |
|---|---|---|
| **Slug optimizer** | Focus keyword English tokens slug lo pakka (`ssc-cgl-2026-...`) + stopwords strip (`how,the,and,in...` penalty radu) | Focus Keyword in URL ✔ |
| **Internal-link fallback** | Kotha site lo published posts lekapote **category archive links** automatic (site age lo ledu inka excuse) | Internal Links ✔ |
| **Title rules** | Keyword title FIRST HALF lo + number (year/vacancies) — prompt + validator rendu | Keyword in Title + Number ✔ |
| **Density window** | 1–2.5% sweet spot (stuffing radu, thin radu) | Keyword Density ✔ |
| **Short paragraphs** | 160+ words paragraphs validator catch chestundi + prompt lo 120 words rule | Readability ✔ |
| **WRITING_RULES** | Prathi Gemini prompt ki Rank Math rules append — AI ne RM-friendly ga rastundi | Anni ✔ |

`run.py --revenue-check` + Telegram QA score tho mee post Rank Math readiness venakala nunchi monitor avtundi.

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
.venv/bin/python run.py --process-queue 5                    # queue lo 5 URLs bulk process
.venv/bin/python run.py --listicle "Top 10 Bank Jobs 2026"    # trending story post
.venv/bin/python run.py --auto-refresh 3                      # 3 purana posts refresh
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
