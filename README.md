# studentup.in Auto-Blogger 🤖

24/7 automatic blog posting system for **studentup.in** (WordPress) — runs on your Oracle Cloud instance.

- **AI content:** Google Gemini (free tier) generates Telugu + English mix articles
- **URL → 100% Original:** vere site article URL ivvandi → facts teesi **complete ga original ga rewrite** (no copy) + **extra advanced info** add chesi post
- **Multi-source research:** internet lo same topic articles search chesi, source-backed context ni fact-check flow tho use chestundi; competitor copy/word-count race kaadu
- **SEO + QA:** focus/secondary keywords, useful Quick Answer, TOC, internal/external links, visible FAQs, Article/Breadcrumb/eligible JobPosting schema, meta tags — Google result guarantee kaadu
- **Review flow:** posts **DRAFT** lo vastayi → **Telegram ki message** (✅ Publish / 🗑️ Delete buttons) → **one tap lo approve**
- **Categories:** Scholarships, Govt Jobs, Education News, Exam Updates, Admissions, Results, Internships, Study Tips
- **Auto-publish:** WordPress REST API — post + category + tags + featured image + SEO meta
- **Schedule:** default 3–5 draft slots/day, spread across 6 AM – 10 PM IST; human review decides what goes live
- **No duplicates:** SQLite state tracks every posted title + source URL
- **WhatsApp alerts** too (optional)

## 📡 v15–v17.1: Breaking News Radar + 105 Official Sources + Keyword Dominance
- **District Radar:** TS 33 + AP 26 districts Google News (Telugu) — breaking
  news **6 గంటలకోసారి** scan (4×/day). Education-relevant matrame → auto draft.
- **Official Sources Grid (v16.1):** 105 sources — SSC/UPSC/RRB/IBPS/SBI/LIC/RBI,
  TSPSC/APPSC/TGRTC/APSRTC/Police/DSC/DISCOMs, NEET/AIIMS/Kaloji/NTR (medical),
  NSP/YASASVI/ePASS/Jnanabhumi (scholarships), TCS/Infosys/Cognizant/Zoho+ (software),
  walk-ins 5 cities, internships. **17 daily hot-list** prathi run lo; bavita rotation.
- **Channel/Website Watch:** `WATCH_SOURCES=` lo Telegram channels (t.me/s/...) +
  RSS/websites — vaalli edu-relevant posts mana queue → fresh original articles.
- **Keyword Dominance (v17):** 66 exams × 14 intents = **980 exact search keywords**
  + Google Autocomplete harvester (free) + daily gap analyse vs live posts —
  "SSC 2026" lanti queries ki maname target post rasi publish chestam.
- **People-first prompts:** NO-COPY hard rule + source provenance + useful reader answers; no Google #1, CPC or ad-attraction promise.
- **Pro thumbnails (v15/v16):** left-scrim / bottom-band / right-panel 3 layouts
  rotation — mana own rendering, copy look ledu (monetization-safe).
- **Viral + Tips engine (v16/v17):** "SSC lo 10 books", "SBI 5 topics" style
  20 viral ideas + 16 student tips pools, daily rotation shares.
- **Tag hygiene (v15):** "Studentup.in"/"News" junk tags create avvu; specific
  tags matrame. `run.py --sources` / `--keywords` / `--radar` commands add.
- **v17.1 truncation fix:** 32k output tokens (2.5 thinking OFF) + MAX_TOKENS
  detect + LENGTH OVERRIDE crisp retry — Telugu JSON "Unterminated string" bug ledu.

---

## 🎯 v18–v19: Honest RankMath Gate + Multi-Key + Google Playbook Adoption
- **v18 — Rank Math STRICT gate:** real panel checks (capped /100 — no inflation),
  auto-refine round when < 90, TOC/list truncation, mobile clamp CSS, crop-safe
  thumbnails, multi-key Gemini rotation (429-proof: `GEMINI_API_KEYS=k2,k3` +
  per-key RPD cap + dead-key day cooldown), near-copy HARD FLOOR (skip < 72%).
- **v19 — top-site playbook adoption:**
  - **Google Jobs:** `JobPosting` JSON-LD auto-emitted on notification posts —
    ONLY when org + real future deadline + substantial description exist
    (expired/fake → silently off; `directApply:false` honest).
  - **Deadline countdown:** "Last date to apply — N days left 🔥" badge (auto
    from `recruitment.apply_end`; expired → red CLOSED box). Model fills dates
    ONLY from the notice — GUESS strictly banned in rules.
  - **Scaled-content protection:** every publish fingerprints 3-word shingles;
    a new near-duplicate (swapped name/date, ≥62% overlap) is REFUSED
    (`DUP_JACCARD_SKIP`). Combined with the no-copy floor → AdSense rule #1.
  - **E-E-A-T:** visible corrections policy + report-by-email line in every
    post; `--ensure-adsense` creates Corrections page + reports the content
    inventory. It does not claim a fixed post count or Google approval rule.
  - **Colloquial H2s:** student-query style ("Apply ela cheyali?", "Fee emiti?")
    + value-add rules (never mirror the notice — add explanation/links/action).

## 🧠 v21: Fact Guard + Voice + Owned Distribution (advanced layer)
- **Fact guard (FACT_STRICT=1 default):** article lo unna prathi date / vacancy
  count source texts lo verify avutundi. Fabricated "last date" auto-flag →
  refine round lo correct/remove; still unresolved ante Telegram lo ⚠️ Fact
  flags count (publish mundu human check). Fake data = Google News/AdSense ki
  #1 risk — ippudu machine ga catch avutundi.
- **Related Questions block:** article own H2 sections nunchi max 3 honest questions/answers — useful for readers, without claiming a rich-result placement.
- **Structured-data hygiene:** visible FAQs remain in HTML, but deprecated FAQPage and unsupported speakable markup are not emitted.
- **Public Telegram channel auto-broadcast:** TELEGRAM_CHANNEL_CHAT_ID set
  cheste prathi PUBLISHED post channel ki automatic (drafts/mocks eppudu
  pampabadu) — owned distribution stream, Google-dependency lekapote growth.
- **GSC data loop:** `run.py --gsc export.csv` ippudu top striking-distance
  query tokens ni state lo save chesi, radar/topic QUEUE ni re-sort chesthundi
  — meeru provide chechina real Google data bot priorities ni drive chesthundi
  (radar sweep lo kuda auto-apply).

## 🔧 v22: Bot = FULL Website Admin (post kaadu — site settings entire)
`run.py --setup` (preview: `--setup --dry-run`) — WordPress ni mee application
password admin tho connect chesi ee items audit + auto-fix chesthundhi:
- ⛔ **Blockers**: `robots.txt Disallow:/` (blog_public off!), `?p=` plain
  permalinks — ee rendhi unte SEO/AdSense ey padipoye; setup pakkaga chupisthundi
- 🔧 **Auto-fixes**: SEO tagline, timezone Asia/Kolkata, comments/pings OFF
  (global + prathi new post lo), posts_per_page, **footer legal menu**
  (Privacy/About/Contact/Corrections/Editorial — links page lekapote AdSense
  reject), **category Telugu SEO descriptions** (empty taaghata — existing
  touch cheyyadu), site icon (SITE_LOGO_URL untelo auto favicon)
- ⚠️ **Checks/Warns**: Rank Math sitemap live aa, Rank Math REST undaa,
  sample permalink format — manual ki miginavay notifications isthundhi
- **Idempotent**: ralli run cheste zero writes; okka safe REST endpoints matrame
  (delete/overwrite emi ledu). Full test coverage: `tests/site_setup_test.py`

## 🎨 v24 — Crop-proof thumbnails + site-wide Design Kit (`--polish`)

Screenshots se nerugu: theme cards image ni **center 56% width** (mobile square!) varaku crop chestundi —
kaani thumbnails text anni **center safe band [0.19w–0.81w]** lo ki move ayipoyayi (3 layouts: bottom band /
center card / top pill — pixel-test tho verify). Inka:

- `run.py --polish` → **site-wide Design Kit**: brand navy `#12356B` + orange `#E8842B`, Noto Sans Telugu+Inter,
  bordered h2, zebra rounded tables, 14px rounded images, single-post featured image `max-height:420px + cover`,
  pill Read-More buttons, mobile 15.5px/1.8 body — homepage ni kuda spellbind chestundi (footer text-widget
  global `<style>` via core Widgets REST — theme files emi touch cheyydu, idempotent refresh).
- `--setup` apply lo kit **automatic ga** install avutundi.
- Footer lo kanipinchina raw `{StudentUp.in}` token → widget lo unte **auto-fix**; Customizer lo unte CLI
  instruction print avutundi.
- **v25**: home/archive cards kortha CSS (rounded border + hover lift + 16:9 thumb crop + widget
  headings brand style); `--setup` lo footer menu **duplicate items auto-removal** (`_menu_dedupe`);
  kit CSS maATkade poTE widget update skip (`up to date`) — widget ni manual ga edit chesina
  sidecar (`design_kit.json`) id gurthupettukuni **duplicate widget create avvadu**.
- WP connect kaNIPITE → kit CSS ni *Additional CSS* ki paste cheyyadaniki ready ga print chestundi.

> ℹ️ Ee site fixes run.py `--setup` / `--polish` commands dwara idempotent ga apply avutayi.
> Production lo apply mundu `--dry-run` report chusi, blockers clear ayyaka matrame run cheyandi.

## 🎯 v26 — Daily Quiz Engine (exam-style, top-level interactive)

RojU automatic ga **okka exam-style quiz post** publish avutundi — Adda247/Adda
level interactivity, mana design kit palette lo:

- **Exam Mode**: total timer (question ki 60s default), question palette
  (answered/flagged/current), flag-for-review, confirm-before-submit,
  **negative marking (+1 / −0.25)**, timeout aite auto-submit.
- **Practice Mode**: option click chesinappude right/wrong + Telugu explanation.
- **Results**: score, accuracy %, grade (Topper/Excellent/Good...), 🔥 daily
  streak (localStorage), per-question review (mee answer vs correct +
  explanation), WhatsApp share button.
- **Bilingual**: prathi question English + Telugu script (`qt`), explanations
  Telugu-mix. Telugu lo topic cheppina work avutundi.
- **Difficulty ramp (auto)**: Mon L1 Basics → Tue L2 → Wed L3 → Thu L2 →
  Fri L3 → Sat L4 → **Sun = 20-question Weekly Mega Mock (L4)**.
  `QUIZ_LEVEL=1-4` tho fix cheyochu.
- **SEO**: post lo static Answer Key + explanations (no-JS users + Google),
  `Quiz` JSON-LD schema, dedicated **Daily Quiz** category (Telugu SEO copy).

**Architecture** (post content sanitizer ni bypass cheyyakunda safe):
quiz block = `<div class="su-quiz" data-quiz="...">` (escaped JSON only);
actual exam UI (CSS+JS) **site-wide footer text widget** ga install avutundi —
design kit (`--polish`) same mechanism, marker `suquiz26`, idempotent.
`--setup` apply lo automatic ga install; leda `run.py --quiz-kit` manual.

**Usage:**
```bash
python run.py --quiz                       # today's auto-rotation quiz (publish)
python run.py --quiz --mock --dry-run      # offline preview (no keys/WP needed)
python run.py --quiz-topic "స్కాలర్‌షిప్‌ల మీద క్విజ్" --quiz-level 3
python run.py --quiz-questions 15 --quiz   # custom length
python run.py --quiz-kit                   # update site-wide exam UI widget
```
Hourly cron lo `QUIZ_HOUR` (default 8 AM) tarvata first run lo quiz post
vastundi; aa roju already ayyunte skip (idempotent). Config: `QUIZ_ENABLED`,
`QUIZ_QUESTIONS`, `QUIZ_SUNDAY_QUESTIONS`, `QUIZ_TIME_PER_Q`,
`QUIZ_NEGATIVE_MARK`, `QUIZ_CATEGORY` (.env).

## 🧰 v28 — Plugins, AdSense kit & honest theme audit

v28 `--setup` ni **site admin** ga extend chestundi. REST capability lekapothe
failure ni hide cheyyadu; report lo WARN chupistundi.

- **Allow-listed plugin stack:** `Rank Math`, `Redirection`, `UpdraftPlus`,
  `WP Super Cache` — missing aite WordPress.org slug tho install, inactive aite
  activate. `AUTO_INSTALL_PLUGINS` lo unknown slugs ignore avutayi; delete,
  deactivate, arbitrary ZIP/URL install eppudu cheyyadu.
- **Theme audit:** active theme ni read-only ga detect chestundi. GeneratePress,
  Astra, Kadence, Blocksy lightweight families lo unte OK; leka recommend
  chestundi. Theme switch ni REST dwara automate cheyyadu — widgets/menus break
  avvakunda Appearance → Themes lo manual decision mee control lo untundi.
- **AdSense Auto Ads loader:** `.env` lo valid `ADSENSE_CLIENT_ID=ca-pub-...`
  pettinappudu okka footer text widget lo Google loader install/refresh avutundi.
  Empty/invalid id aite **script emit kaadu**. Ad units, forced clicks,
  navigation tricks levu; AdSense approval, consent/CMP, ads.txt Google-side
  manual requirements gaane untayi.
- **Idempotent widget writes:** marker-based lookup + sidecar id valla repeated
  `--setup` duplicate widgets create cheyyadu. Block theme/widget REST unavailable
  aite manual Site Kit/Additional HTML route instructions report lo vastayi.
- **Dry-run safety:** `--setup --dry-run`, `--plugins --dry-run`,
  `--adsense-kit --dry-run` REST reads/plans matrame; menu/plugin/widget writes
  jaragavu.

```bash
python run.py --setup --dry-run       # full audit + v28 plan
python run.py --plugins --dry-run     # plugin plan only
python run.py --plugins               # install/activate reviewed stack
python run.py --theme-audit           # read-only theme check
python run.py --adsense-kit --dry-run # validate client id, no widget write
python run.py --adsense-kit           # install/update Auto Ads loader
```

**Honest limitation:** `ADSENSE_CLIENT_ID` set cheyyadam revenue/approval
 guarantee kaadu. AdSense approve ayyaka publisher id tho ads.txt line ni
`https://studentup.in/ads.txt` lo host cheyyali, consent requirements verify
cheyyali, and Auto Ads placements ni manually review cheyyali. `--revenue-check`
ippudu ee gaps ni separate ga report chestundi.

## ✨ v29 — Advanced post experience + theme UI layer

v29 is not a new heavy theme or page-builder lock-in. Existing WordPress theme
meeda progressive enhancement ga install avutundi, so theme change ayina posts
break avvakunda:

- **Article UI:** visible breadcrumbs, reading badge, structured “At a Glance”
  facts card for source-backed notification fields, quick-answer card, styled
  TOC, deadline card, trust box, official links, and related-article sections.
- **Reader tools:** reading-progress bar, skip-to-content accessibility link,
  responsive horizontally-scrollable tables, WhatsApp share + copy-link buttons,
  dark/light mode with local preference, scroll-to-top, reduced-motion support.
- **Theme-safe responsive layer:** mobile cards, dark palette, focus states,
  accessible labels, touch-friendly controls, and no jQuery/external UI library.
  It is one idempotent UI widget marker (`sukit24` compatibility marker) and
  does not overwrite theme files or existing widgets.
- **Truth guard:** facts card shows only structured values already present in
  the model/source response; the code never invents vacancy counts, dates,
  salary, or locations.

`--setup` / `--polish` refreshes the UI layer. If the active theme has no
widget REST area, the command reports a manual fallback instead of pretending
that the UI was installed.

## 🛡️ v30 — Production safety + revenue audit

`--production-audit` is the final pre-live gate. It checks HTTPS, WP/Gemini
credentials, fact/originality guards, human-review mode, AdSense id format,
CMP/consent configuration, ad-slot cap and CLS protection. With a real WP
connection it also checks robots visibility, sitemap, policy pages, plugin
activation, active theme and `ads.txt` publisher line.

```bash
python run.py --production-audit
```

The audit intentionally distinguishes **PASS / WARN / FAIL / INFO**. A CMP
name in `.env` is not accepted as proof that consent works; Google-certified
CMP setup and an actual browser verification are still required. Likewise,
`ADSENSE_CLIENT_ID` only enables the loader after approval—it cannot guarantee
AdSense approval, RPM, CPC, rankings, or income. No code can honestly promise
that Google accepts every page or that revenue is “highest”.

Revenue safety rules remain enforced: no self-click prompts, no forced
navigation, sponsored/affiliate links are disclosed and sanitized, ads are
capped with reserved space, and draft + fact/originality review is the default.

## 📞 v31 — Student Internet Center service platform

The site can now become a real local assistance business, not only a blog.
`--service-center` publishes a transparent service page for:

- online applications, jobs and recruitment guidance;
- scholarships and welfare schemes;
- resume/CV and cover letters;
- admissions and exam registrations;
- hall-ticket/results plus print/scan/PDF help.

The page supports configured phone, WhatsApp enquiry, and a private upload-link
CTA. It explains the workflow: enquiry → eligibility check → secure documents →
fee confirmation → client verifies form → submission → receipt/materials/status.
It also clearly says there is no government/selection guarantee, no hidden fee,
and clients must never share OTP, UPI PIN, passwords or bank credentials.

```bash
python run.py --service-center --dry-run  # local preview: output/service-center.html
python run.py --service-center             # create/update only if managed copy is unchanged
python run.py --service-center --force     # explicit overwrite after taking a backup
```

Normal posts, pages, menus, categories and media remain editable from the
WordPress dashboard. The service page is marked as managed and preserves a
manual WP edit automatically; only the explicit `--force` flag can replace it.

For the staff workflow, `autoblog/service_center.py` stores only consented case
metadata, status events and private-storage document references. It does not
accept or store document bytes. Case ids, status changes, retention purge and
terminal-case protection are included. Put uploads in a private, access-
controlled portal; do not commit documents, and set `SERVICE_RETENTION_DAYS`.
WhatsApp may be convenient but is not a substitute for a secure upload process.

## 🧪 v32 — Existing-post deep audit before editing

Existing posts are **not blindly rewritten**. `--content-audit` pulls published
posts directly from WordPress (not only local `state.db`) and reports title
length, word depth, section structure, summary table, Quick Answer, FAQ,
internal/external links, image alt text, quality score and a safe action:
`priority-refresh`, `editorial-refresh`, `small-fix` or `keep`.

```bash
python run.py --content-audit --content-limit 500
```

The audit is read-only and never changes a title, slug or URL. After source and
fact review, the existing controlled `--auto-refresh N` flow can be used. This
separation prevents a low-quality bulk AI rewrite from damaging already-ranking
pages.

## 🔎 v33 — Google-facing public checks

Run a public page audit with PageSpeed Insights and HTML checks:

```bash
python run.py --google-audit https://studentup.in/
```

It reports HTTPS, HTTP response, title, meta description, canonical, H1,
viewport, JSON-LD, image alt text, and PageSpeed mobile/desktop scores plus
LCP/CLS/INP when the PSI endpoint responds. It does **not** pretend to be
Search Console or AdSense account access. For real query CTR/impressions,
export Search Console data and use the existing `--gsc report.csv` flow; for
AdSense approval, CMP, invalid traffic and ads.txt, use the owner account and
production audit.

## 🔒 v34 — Ad pre-approval hard gate

Until Google AdSense approval, `ADSENSE_APPROVED=0` guarantees that the
pipeline emits no Auto Ads loader and no in-content ad shortcode spaces. This
keeps the pre-approval site focused on original content, UX and service leads.
After approval, enable it deliberately only after checking CMP/consent, ads.txt
and the AdSense dashboard.

## 🧠 v35 — Deep quality and policy gap fixes

The production path is now quality-first instead of volume-first:

- default schedule is 3–5 draft slots/day, not a scaled live-content firehose
- direct live publishing is blocked without a named `EDITORIAL_REVIEWER`, below `PUBLISH_QA_MIN_SCORE=80`, or below the originality floor
- research prompts explicitly reject ranking/ad/word-count manipulation and resolve source conflicts visibly
- bylines no longer claim a human editorial review unless `EDITORIAL_REVIEWER` is configured after real review
- deprecated FAQPage and unsupported speakable JSON-LD are not emitted; visible FAQs remain for readers
- canonical matching, noindex, HTML language, Open Graph and JSON-LD parse checks are in the public audit
- sponsored partner HTML is rejected unless its link includes `rel="sponsored"`

Google’s current AI-search guidance says the durable work is foundational SEO,
helpful non-commodity content, crawlability, internal links, page experience and
visible matching structured data — not special AEO/GEO hacks [Search Central](https://developers.google.com/search/docs/fundamentals/ai-optimization-guide).

## 📚 v36 — NotebookLM-ready source-grounded research

For a serious post, first create a focused evidence bundle instead of asking a
model to merge random web pages directly:

```bash
python run.py --research-brief "TSPSC Group 2 notification" --research-year 2027
# A year in the topic is also detected, but an explicit flag is safest:
python run.py --research-brief "TSPSC Group 2 2027 notification" \
  --research-year 2027
# or provide URLs already checked by the editor:
python run.py --research-brief "TSPSC Group 2 2027" \
  --research-urls checked_urls.txt --research-year 2027
```

When a target year is supplied, the bundle labels each source as target-year,
other-year/verify, or evergreen/verify-current. It records publication/update
metadata when the page exposes it and tells NotebookLM never to carry a 2026
(or older) deadline, fee, vacancy or eligibility rule into 2027 without an
explicit source statement. If a 2027 official notice is not available, the
brief must say that instead of inventing a projection. Use the same guard when
drafting from a checked brief:

```bash
python run.py --url "https://official.gov.in/notice" --target-year 2027 \
  --notebooklm-brief "checked-notebooklm-brief.md"
```

The command writes ignored local files under `output/research/`:

- `*-sources.md` — labelled public sources, URLs, extracted text and candidate fact sentences
- `*-notebooklm-prompt.md` — five-pass protocol: source map, fact ledger, conflict audit, gap analysis and cited article brief
- `*-manifest.json` — source inventory and bundle metadata

Import the sources file into the owner’s NotebookLM notebook, run the prompt,
open every citation, then save the cited brief. Feed that **saved, human-checked
brief** into the draft flow:

```bash
python run.py --url "https://official.gov.in/notice" \
  --notebooklm-brief "checked-notebooklm-brief.md"
```

NotebookLM is source-grounded and provides inline citations that link back to
supporting passages [Google’s NotebookLM update](https://blog.google/technology/ai/notebooklm-goes-global-support-for-websites-slides-fact-check/),
but it is not a replacement for human fact checking. This repository cannot log
into a private NotebookLM account or pretend that its answer was verified.

The final article must use Claim IDs from the brief, keep official sources
visible, flag disagreements, and be independently written. It must not stitch
source paragraphs together, copy headings/tables, or invent facts to fill gaps.
Never place private documents, passwords, OTPs, bank details or identity data in
the public research bundle.

## 🏆 v38 — Top Post Dominance Engine (anni keywords → top post)

"Top post" ippudu **plan → write → measure → harden → gate** — claim kaadu,
measurement. Kotha module: `autoblog/top_post.py` (offline, deterministic,
no API key needed for planning).

**1. ANNI KEYWORDS (11,192) — Keyword Universe**
188 entities (SSC/UPSC/RRB/banks/defence, TSPSC/APPSC/DSC/Police, scholarships,
entrances, universities, skills, internships) × **66 intents** (14 core +
52 long-tail: last date, eligibility, age limit, fee, documents, district wise,
PDF download, direct link, study plan, toppers strategy, mock test, FAQ,
YouTube channels, Telegram groups, photo-signature size, fee refund, exam day
checklist, seat matrix, renewal, income certificate…). Prathi keyword ki
cluster, funnel (TOFU/MOFU/BOFU), content type, priority score, proposed title:

```bash
python run.py --keyword-universe      # stats + export
# output/keywords/keyword_universe.csv  (Excel/Sheets lo open cheyochu)
```
Category hygiene built-in: scholarship/skill pages ki "negative marking / exam
centre" lanti meaningless combos generate avvavu. Demand/competition bands
**heuristic proxies matrame — Google volume data kaadu** (`--gsc` real data).

**2. TOP POST BLUEPRINT — okka keyword ki complete on-page pack**

```bash
python run.py --top-post "TSPSC Group 2 2026 notification"
```
- 3 title options (40-62 chars, keyword first 40% lo, power word) + meta (110-156
  chars keyword tho start) + slug + H1 + official site
- 6-11 H2 sections + H3 subtopics with target keywords + purpose (intent-aware
  families: notification / apply / result / hall ticket / cutoff / syllabus /
  salary / plan / books / **scholarship / admission / career**)
- Keyword family: secondary + question (PAA) + long-tail phrases
- Entities to cover, tables to build, snippet answer (first 40 words),
  visible FAQ plan, schema list, image banner + alt text, internal/external
  link plan, E-E-A-T checklist, 10 ranking levers, word target
- **Plan quality score** — 100/100 ki blueprints
- Files: `output/top-posts/<slug>.html` (styled page), `.md`, `.json`

**3. DOMINATION CALENDAR — 90-day publishing plan**

```bash
python run.py --top-post-plan --top-post-days 90 --top-post-per-day 2
```
Pillar (exam hub post) + support (long-tail wins) mix, cluster + intent
rotation, same-day lo veru clusters (footprint-safe). CSV/MD/JSON export.
Repo lo ready sample: `preview/dominance-plan-90-days.md`.

**4. TOP POST SCORE — 30+ checks, 0-100, grade**

```bash
python run.py --score-post output/top-posts/x.html --score-keyword "ssc cgl 2026"
```
Checks: keyword title/first-content-paragraph/2+ H2 lo, density band
(0.4-3% — **over-optimization penalty kuda**), secondary + long-tail + question
coverage, snippet block, structure (H2/H3/section split/paragraph length),
tables/lists (short list items), FAQ 4+, internal 2+ / official external link,
Article+Breadcrumb schema, image alt, byline + corrections + source-check date,
readability, entity coverage. Grades: `TOP POST 🏆 ≥90`, `STRONG 💪 ≥78`,
`OK 👌 ≥65`, `WEAK ⚠️`.

**5. HARDEN + GATE (publish path lo automatic)**
- Publish mundu **structural** hardening: focus keyword default, secondary
  keywords fill, meta 110-160 fix, slug keyword tokens, snippet answer
  (article own first paragraph nunchi), visible FAQ extraction (own H3 answers
  nunchi), **density cap** (3%+ repeat unte extras trim — spam signal safe).
  Kotha facts eppudu invent cheyyadu.
- `DEFAULT_POST_STATUS=publish` lo score < `TOP_POST_MIN_SCORE` (78) unte
  **live publish BLOCK** (`TOP_POST_STRICT=1`). Draft-first flow lo score
  log avutundi, block undadu.

**6. Blueprint → article (Gemini) + preview**
```bash
python run.py --top-post "NSP Scholarship last date" --publish-top-post
python run.py --top-post "SSC CGL 2026 apply online" --publish-top-post --mock --dry-run
# dry-run: output/top-posts/<slug>.draft.html (WordPress touch cheyadu)
```
Gemini prompt blueprint ni exact ga follow avutundi (structure, keyword family,
FAQ, density rule) — kaani **facts official source nunchi matrame**; teliyani
వివరాలు "అధికారిక నోటిఫికేషన్‌లో ధృవీకరించుకోండి" ani rayali, guess cheyyakudadu.

> ℹ️ Ranking, rich results, AdSense approval — ee plan **guarantee cheyyadu**.
> Blueprint + score manaki on-page discipline istundi; Google ni evaru
> "order" cheyyaleru.

## 🎓 v39 — College Exam Portal (online exams, zero-mistake flow)

College ki **okka command tho** online exam system: students link + **roll number**
matrame tho join avutaru (password ledu), admin **okka click tho START / CLOSE**
chestadu — andaru join ayyaka start, time ayyaka automatic close + auto-submit.
Kotha module: `exam_portal/` (Python stdlib + vanilla JS — no framework, no pip
installs, oka VM lo ne run avutundi).

**1. Start (college admin)**

```bash
python run.py --exam-portal-demo        # sample exam + students tho start (try cheyyadaniki)
python run.py --exam-portal             # empty portal — kotha exams create cheyyandi
python run.py --exam-portal --exam-port 9000 --exam-base-url https://exams.college.edu
python run.py --exam-portal-test-channels   # Telegram/webhook test ping
```

Boot lo admin key print avutundi (leda `EXAM_PORTAL_ADMIN_KEY` env). Console:
`/admin` (exam create → questions paste → roster → publish → START/CLOSE),
students ki share link: `/exam/<CODE>`.

**2. Zero-mistake flow — built-in protections (mistakes lekunda)**

| Risk | Protection |
|---|---|
| Questions tappu ga paste | `parse_questions` — 3 formats (blocks / CSV / JSON), prathi error line-wise report (silent skip ledu) |
| Answer key miss / question galat | Validation blockers: options <2, duplicate options, answer set kaledu, pass marks > total, negative ≥ marks, duration 0 |
| Live lo paper marchadam | Live/closed exam lo questions add/delete **block** (audit freeze) |
| Tappu question valla unfair marks | Admin **Drop** → aa question andariki count avvadu, scores automatic recalculate |
| Option shuffle valla tappu scoring | Scoring **text-anchored** — student chusina position ni original answer key ki map chestundi (v39 test 7b) |
| Duplicate attempt (okate roll, rendu devices) | Okka roll = okka device; same token tho resume allowed (answers eppudu poyipovu) |
| Time over — admin marchipoyadu | Background sweeper (5s): auto-close + auto-submit + "closing soon" ping |
| Andaru join ayyaka start marchipoyadu | `auto_start_all_joined` ON unte roster full → automatic START |
| START/CLOSE rendu sarlu click | Idempotent — rendu sarlu chesina okkate result, okkate end time |
| Student page accidental close / net cut | localStorage pending-answer queue + 10s heartbeat + token resume |
| Late join unfair advantage | Late joiners ki kuda **same end time** (grace minutes unte dani varaku matrame) |
| Mass copy / tab switch | Tab-switch count + audit log + live monitor (integrity signals) |

**3. Notifications — anni channels**

Telegram (`EXAM_TELEGRAM_BOT_TOKEN` + `EXAM_TELEGRAM_CHAT_ID`, leda repo
`TELEGRAM_*` fallback), webhook (`EXAM_WEBHOOK_URL`), in-app banner (students
screen lo live announcement), plus **copy-paste templates** (WhatsApp group,
SMS, notice board, email, JSON) — `/manage/<CODE>` → Share & Notify tab.
Channel fail aithe exam **eppudu block avvadu** (log lo record avutundi).

**4. Results, analysis, exports**

Immediate result + per-question review (option text tho), rank, pass/fail,
topper, average, question-wise analysis (which question everyone missed),
CSV exports: results / questions / analysis / audit log.

**5. Tests**

```bash
python tests/v39_exam_portal_test.py    # 14 sections: parse → validate → START/CLOSE →
                                        # scoring (shuffle-safe) → sweeper → notify →
                                        # HTTP end-to-end → demo → UI JS guards
node tools/ui_smoke.mjs                 # optional: real DOM (jsdom) full-flow smoke
python run.py --ad-advisor              # v57: eppudu e ad-network ki apply cheyyali
python run.py --ad-advisor --traffic-csv ga4.csv   # GA4 export → advisor (logs/traffic.json)
python run.py --breaking-feed           # v59: radar → site బ్రేకింగ్ న్యూస్ feed (ticker+section)
python run.py --breaking-from file.json # v59: feed ni JSON nunchi (offline/approved list)
```

### v63 — MISTAKE-FREE SEO: Rank Math REST bridge + meta verification + post edit

**Pattina nijamaina mistake:** WordPress REST default ga custom meta accept cheyyadu →
bot `rank_math_*` fields pampiste 400 → bot **meta lekunda** post pettēdi → SEO fields khali.
Ippudu moonu layers lo fix:

| Layer | Enti |
|---|---|
| `wordpress-theme/studentup/inc/seo-bridge.php` | 10 Rank Math keys ni REST ki register (show_in_rest + `edit_post` auth) → bot meta writes land avutayi |
| `WordPressClient.verify_meta()` | publish/update tarvata **verify** — field land avvaledu ante Telegram ⚠️ + log (silent fail ledu) |
| `pipeline` create + update | rendu chotla verify + `seo_meta_missing` result lo + fix pointer (seo-bridge) |

Post edit/refresh capability (mee "edit cheyyagalava?" prashna): `update_post()` REST edit
(URL/slug same — SEO safe) · `python run.py --update <id>` (manual) · `auto_refresh`
(roju purana posts ni fresh research tho update) · meta verify.

GET `/wp-json/studentup/v1/theme-info` → theme version + seo_bridge + rankmath + adsense seal.

### v62 — TOP WEBSITE READINESS (proof tho: enti ready, enti mee pani)

```bash
python run.py --readiness      # 18 system checks score/100 + 6 owner-pending items
```

**Ee command ee repo lo prastuta: 100/100 system checks · 8 owner-pending.**
Artifacts: `logs/readiness.json` + `output/readiness-<date>.md` (markdown report).

| Section | Enti verify avutundi (verifiable number) |
|---|---|
| CONTENT ENGINE | blueprint score 100/100 (TOP POST 🏆) · gates QA 80+ / originality 72%+ / deep-gate ON · 17 pillars · 203 entities · 11,192 kws · 143 sources · radar 4x/day · 59 districts |
| SEO | schema (Article · ItemList · JobPosting · BreadcrumbList) · head 6/6 (title/meta/canonical/OG/JSON-LD/lang) · robots+sitemap · Rank Math LIVE fields |
| ADS & MONEY | slots 3/3 high-CTR order · SPONSORED labels · rel=sponsored · ads.txt status · money engine 6/6 (rate card · house · calculator · network plan · advisor · leads) |
| AUTOMATION | daily hooks 6/6 (radar · auto-refresh · breaking · advisor · guardian · quiz) · draft-first approval · test tiles sync |
| REAL SITE | theme zip fresh · 14 PHP · REST bridge · first-look UX 4/4 |
| OWNER PENDING ⏳ | domain/hosting · WP+theme · Gemini · Telegram · **GSC+GA4** · **AdSense CMP** · AdSense · Oracle VM — prathi daniki fix line |

> ⚠️ Honest: ranking/traffic/AdSense approval/revenue — Google + mee accounts + time.
> Readiness score aa vatiki guarantee ivvadu; adi "code side 100% ready" ani matrame cheptundi.

### v61 — REAL WEBSITE: WordPress + StudentUp theme (design = preview design)

```bash
python tools/build_wp_theme.py      # wordpress-theme/studentup-theme.zip (~29 KB) — WP upload ready
python run.py --push-theme-data     # breaking · proof · deadline · house ads → WP theme (REST)
```

**Mee site ela untundi:** WordPress (MilesWeb) + `wordpress-theme/studentup/` — `preview/index.html`
lo unna **ade design**, kaani **dynamic**: bot post rasthe card + category count + breaking item
automatic ga site lo padutayi.

| Theme file | Enti (preview lo ekkado) |
|---|---|
| `front-page.php` | home order: used-strip → ప్రకటన → hero+countdown → బ్రేకింగ్ → grid+chips |
| `header.php` | logo · menu (TS/AP/… dropdown) · టికర్ · mobile panel |
| `single.php` | article + ads + WhatsApp/Telegram share + related + trust note |
| `inc/breaking.php` | feed (option → 10-min transient file → honest empty) + REST push endpoint |
| `inc/ads.php` | AdSense unit + house ads (SPONSORED · rel=sponsored · day rotation) |
| `inc/template.php` | cards · proof tiles (WP live numbers) · countdown · breadcrumbs (Rank Math) |
| `assets/js/studentup.js` | dark mode · mobile panel · chips filter · countdown (no library) |

Install (5 min): zip upload → Activate → Menus assign → `--push-theme-data`.
Options: `studentup_breaking_json` · `studentup_proof_json` · `studentup_deadline_json` ·
`studentup_house_ads` · `studentup_adsense_client` · `studentup_exam_url`.
Detail: `wordpress-theme/studentup/README-THEME.md`.

### v60 — SITE GUARDIAN: eppatiki advanced ga (roju automatic)

```bash
python run.py --guardian            # 12 checks: site/UI/SEO/ads/feed/storage/theme
python run.py --guardian-notify     # same + Telegram report (daily hook automatic @ 20 IST)
```

| Check | Enti chustundi | Fail ayithe fix |
|---|---|---|
| site_files | pages/robots/sitemap/ads.txt/feed | `python tools/build_policy_pages.py` |
| first_look_ui | ticker → most-used → hero blocks + feed fetch | v59 blocks restore |
| tiles_sync | site tiles ↔ tests/*.py count ↔ jsdom literal | tiles + jsdom okate change lo bump |
| robots_sitemap | sitemap line · /admin disallow · internal artifacts | builder rerun |
| ads_txt | live/placeholder status | builder + ADSENSE_CLIENT_ID |
| breaking_feed | freshness (GUARDIAN_FEED_MAX_AGE=26h) | `--breaking-feed` / radar cron |
| ads_inventory | ad link/title/id validity (inventory + house) | ads/*.json correct |
| keyword_pillar_lock | 17 pillars · 203 entities · 11,192 kws · 143 sources | counts sync |
| menu_wiring | TS/AP/hall/results/walkin/software links + 8 used tiles | nav/mpanel |
| storage | disk free · state.db · output size | `tools/prune_media.py --apply` |
| env_readiness ⚠️ | Gemini/WP/Telegram creds (owner pani) | `.env` (GO_LIVE PART A) |

Severity: ❌ = system break · ⚠️ = owner-pending (creds) · status → `logs/guardian.json` (14-run history).
Guardian read-only — fix chestundi kaadu, cheptundi; fixes tests + builder nunchi.

### v59 — First Look: బ్రేకింగ్ న్యూస్ + "విద్యార్థులు ఎక్కువగా వెతికేవి" + పర్ఫెక్ట్ మెనూ

Student site open cheyagane modati 3 sekundullo kanipinche order:

| Position | Enti | Detail |
|---|---|---|
| 1 | 🔴 **బ్రేకింగ్ టికర్** | radar feed (Google News తెలుగు + 143 official sources) — verified items matrame; feed khali aithe ticker **hide** (fake news ledu) |
| 2 | **విద్యార్థులు ఎక్కువగా వెతికేవి** | 8 tiles: టీఎస్ · ఏపీ ప్రభుత్వ ఉద్యోగాలు · హాల్ టికెట్లు · ఫలితాలు · వాక్-ఇన్ · సాఫ్ట్‌వేర్ · ప్రైవేట్ · ప్రస్తుతాంశాలు — prathi tile ki **live count** + one-tap filter |
| 3 | ప్రకటన (leaderboard) | highest-visibility slot — content ki bhaadha lekunda |
| 4 | Hero + ముఖ్య గడువు countdown | trust tiles (45/45 · 11/11 · 122/122 · 11,192 · 17 cats · 143 sources) |
| 5 | బ్రేకింగ్ న్యూస్ section + తాజా అవకాశాలు grid | grid lo **TS/AP ప్రభుత్వ ఉద్యోగాలు modati cards** |

Menu (desktop + mobile same order): హోమ్ · ఉద్యోగాలు▾ (టీఎస్ · ఏపీ · కేంద్ర · ప్రైవేట్ ·
వాక్-ఇన్ · సాఫ్ట్‌వేర్ · అవుట్‌సోర్సింగ్ · పార్ట్-టైమ్ · విదేశీ) · **హాల్ టికెట్లు** ·
**ఫలితాలు** · **బ్రేకింగ్ న్యూస్** (live dot) · స్కాలర్‌షిప్‌లు · ప్రస్తుతాంశాలు · పరీక్షలు▾ · మరికొన్ని▾

Bot side: `autoblog/breaking.py` (feed build + tag classifier + honest empty note),
radar run lo auto hook, `MOST_USED` order okate source (bot + site + tests sync).
Evidence: tests/v59_test.py 12 checks · `run.py --test-all` 49/49 · jsdom 122/122.

> ℹ️ Ee system exam conduct cheyyadaniki matrame — student data (roll, answers,
> scores) mee server lo untundi, bayata pampabadadu. Public internet lo pettali
> ante HTTPS reverse proxy (nginx/Caddy) vadandi; admin key ni evariki share
> cheyyakandi (per-exam manage link share cheyandi).

## 🧹 v41 — Site Audit + Safe Autofix (anni tappalu → okate scan lo)

Live site lo thin/junk content, tappu category, PII, raw shortcode, duplicate
TOC anchors, tag bloat, demo pages, UTC timezone — ivi manual ga vethakadam
kastam, malli malli vasthayi. v41 okka scan lo **anni** pattukuni, safe fixes ni
(dry-run default) apply chestundi + malli raakunda **publish gate** pettutundi.

```bash
# 1) Read-only audit — emi maradu
python run.py --site-audit

# 2) Audit + fixes (default DRY-RUN — emi apply avvadu, plan chupistundi)
python run.py --site-audit-fix

# 3) Fixes ni nijamga apply (safe set matrame)
python run.py --site-audit-fix --site-audit-apply

# 4) Junk/demo pages ni trash cheyyadaniki permission (reversible — trash, delete kaadu)
python run.py --site-audit-fix --site-audit-apply --site-audit-trash

# 5) Only konni fixers (comma list)
python run.py --site-audit-fix --site-audit-apply --site-audit-action strip_pii,strip_shortcode

# 6) Network ledu / CI / mee machine block ayithe → offline modes
python run.py --site-audit --site-audit-snapshot demo          # engine proof
python run.py --site-audit --site-audit-save output/audit/site-audit-snapshot.json  # site unna machine lo
python run.py --site-audit --site-audit-snapshot output/audit/site-audit-snapshot.json
```

**Enti pattukuntundi (post / page / tag / category / site — 20+ check classes)**

| Class | Example (live site lo pattukunna) | Auto-fix |
|---|---|---|
| Junk HTML fragment | `<title>…<header>…<footer>` dump, bot "100/100 SEO" text | → draft |
| Empty title/content | id 3452 (title ledu, content bot text) | → draft |
| Broken heading tags | closing `</h2>` > opening `<h2>` (sanitizer damage) | → draft |
| Missing featured image | 3 posts | manual (image generate → set) |
| Wrong category (Govt↔Private) | Optum (private MNC) → "Central Govt Jobs" | → `Private Jobs` |
| Wrong category (walk-in) | Walk-in drive → "Internships" | → `Walkin Jobs` |
| Uncategorized | 3 posts | → guessed category |
| PII phone | body lo `8977614045` | mask `89XXXXX45` |
| Unprocessed shortcode | `[adinsert block=1]` raw ×2 | strip |
| Duplicate TOC anchor | `#amp` ×3 (click tappu section ki) | unique `amp`, `amp-2`, `amp-3` |
| Off-topic entity | education site lo footballer article | manual (rewrite) |
| Stale dates | newest date 30+ days old (session over) | manual (refresh) |
| Mixed image format | `.jpg.webp`, `-768x432.jpg.webp` | manual (media pipeline) |
| Demo/theme pages live | `3029-2`, `image-gallery-block`, 9 pages | → trash (301 redirect) |
| Slug ↔ title mismatch | `/privacy-policy/` = "About us" | → slug fix |
| Duplicate contact page | `/contact/` + `/contact-us/` | → draft |
| Tag bloat | 200+ tags, ~85% count 0 | → purge zero-count |
| Truncated tag name | "TS Police SI Constable Preparati" | → "…Preparation" |
| Duplicate tags | Fresher / Freshers Jobs · Part Time / Part-time Jobs | **lossless merge** (posts reassign → drop tag delete) |
| Empty categories | 6 categories, posts ledu | manual (assign / noindex) |
| Timezone UTC | Indian audience ki tappu timestamps | → `Asia/Kolkata` |
| Local SEO without location | `locations.kml` live, business location ledu | manual (module off) |

**Safety rules (mistakes lekunda)**

- Default **dry-run** — `--site-audit-apply` ivvakapote okka write kuda jaragadu.
- Destructive ops (`draft` / `trash`) ki **`--site-audit-trash`** explicit permission.
- Junk content **delete avvadu** — draft/trash matrame (WordPress revisions tho reversible).
- PII report lo kuda raw ga chupinchadu (mask chesi) — privacy.
- Prathi fix audit log lo (`.json`) + `output/audit/site-audit-<stamp>.md`.

**Root-cause gate (malli raakunda)**

Ippati nunchi `DEFAULT_POST_STATUS=publish` unte, live publish ki mundu v35
(reviewer/QA/originality), v38 (top-post score) **+ v41 site gate** kuda run
avutundi — empty title/excerpt, featured image, junk HTML, unregistered
shortcode, duplicate anchor, U+2011/"today" template, stale date, PII phone,
Govt category lo private employer, off-topic entity → block. Drafts eppudu allow
(human review ki). Code: `autoblog/site_audit.py::article_gate()` +
`autoblog/pipeline.py` hook.

**CI + test runner (v41 tho vachindi)**

```bash
python run.py --test-all                 # ANNI suites okate command tho (30/30)
python run.py --test-all --test-only v41 # okka suite matrame
```

CI config: **`ci/github-actions-tests.yml`** — prathi push/PR ki 30 suites
(3 Python versions: 3.10/3.11/3.12) + offline site-audit demo job run avutundi.
⚠️ GitHub lo okka manual step: aa file ni **`.github/workflows/tests.yml`** ki copy
cheyandi (Arena agent GitHub App token ki `workflows` permission ledu — workflow
files direct ga push cheyyaleru; migilinavi anni automatic). Adi pettaka breaking
change silent ga merge avvadu.

```bash
python tests/v41_site_audit_test.py    # 15 sections: checks → fixers → gates → CLI →
                                       # network-fail → deploy pack (systemd/Docker/boot)
```


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
2. Bot: source nunchi **facts** teesi → **100% original** Telugu article (topic warrants it; no forced word count) → **useful sections** (documents, mistakes, tips, tables, visible FAQ) add chesi → **SEO/QA** chesi → **DRAFT** create chestundi
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
| 2. **Research** | **Internet lo same topic meeda sources search** (DuckDuckGo — API key ledu) — official/context sources fetch |
| 3. **Fact-backed context** | Source conflict flag chesi, only supported fee/salary/stages/documents add chestundi |
| 4. Rewrite | Complete ga fresh structure + fresh wording lo Telugu article; no copy and no forced length |
| 5. Enhance | Useful sections: documents list, common mistakes, pro tips, comparison table only when relevant |
| 6. SEO/QA | Quick Answer + focus/secondary keywords + TOC + internal/external links + visible FAQ + Article/Breadcrumb schema + Rank Math meta |
| 7. Draft | WordPress draft + Telegram review buttons |

> Goal: reader ki official-source-based, genuinely useful explanation. Google top position, CTR, approval or revenue ni code guarantee cheyyadu. DuckDuckGo fail aite bot primary source tho graceful ga continue chestundi.

## 🛡️ QA & Safety Layer (kothena — 100x level)

Prathi post lo **publish mundhe** automatic checks:

| Check | Em chestundi |
|---|---|
| **Originality Proof** | Final article vs sources — 5-gram shingle analysis tho **measurable no-copy %**. 70% kante takkuva aite article **automatic regenerate**! Telegram message lo "Originality: 94%" ani kanipistundi |
| **QA Score /100** | Rank Math-style 15 checks — keyword placement, density, word count, FAQ, table, meta length, tags... Telegram lo score kanipistundi |
| **HTML Sanitizer** | Gemini script/div/markdown waste ichina automatic strip — only clean SEO tags |
| **Keyword Intelligence** | Google lo already top-lo unna competitor titles ni kuda analyze chesi **vatikante strong title/keywords** generate |
| **Boilerplate Footprint Fix** | Intro paragraphs & headings prathi post lo **rotate avtayi** — Google duplicate-pattern spam signal risk zero |
| **Source context box** | "About This Article" — named author, source domains and source-check date; it does not falsely claim a human review |
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

### In-Content Ads — approval-gated
- Before approval, `ADSENSE_APPROVED=0` hard gate valla **ad spaces, shortcode ads and Auto Ads loader emi render avvavu**.
- Approval ayyaka matrame `ADSENSE_APPROVED=1` + valid `ADSENSE_CLIENT_ID` configure chesi, optional ga `AD_SHORTCODE` enable cheyali.
- Then only 3 reserved, policy-reviewed positions: intro tarvata, mid-article, FAQ mundu.

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

## 💼 Sustainable Revenue Plan — approval-first, data-driven

Until Google AdSense approval, `ADSENSE_APPROVED=0` hard gate valla **ad loader, ad spaces and ad shortcodes emi render avvavu**. Current growth levers:

| Lever | Safe implementation | What it can improve |
|---|---|---|
| Reader demand | Seasonal topics, official notifications, student questions | Relevant impressions and useful sessions |
| Search Console loop | High-impression/low-CTR and position 8–20 queries | Evidence-based title/content decisions |
| Owned audience | Optional Telegram CTA only when configured | Returning visitors, not artificial traffic |
| Service conversions | Student Internet Center CTA with configured contact details | Legitimate leads and service revenue |
| Affiliate links | Relevant links only, `rel=sponsored nofollow` + disclosure | Separate affiliate income, if actually relevant |
| Performance | Mobile HTML, image dimensions, caching and Core Web Vitals | Better experience and conversion potential |

These are opportunities, not CPC/RPM/revenue guarantees. Do not create pages only for high-CPC terms, force long articles, or insert commercial claims without verified reader value.

After approval, enable ads deliberately only after checking the AdSense Policy Center, authorized sites, `ads.txt`, CMP/consent and traffic sources. Google’s publisher guidance recommends understanding traffic segments, avoiding self-clicks and preventing artificial activity [Google traffic quality](https://www.google.com/ads/adtrafficquality/publishers/).

```bash
.venv/bin/python run.py --revenue-check
```

The command reports configuration gaps; it cannot approve an account or predict RPM.

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
- ✅ **Article + Breadcrumb JSON-LD schema** — visible FAQ remains useful HTML; deprecated FAQPage rich-result markup is intentionally not emitted — `te` language tag tho
- ✅ **Social OG/Twitter meta** — Facebook/WhatsApp/Twitter preview titles (CTR boost)
- ✅ **Image alt text** — focus keyword tho alt text
- ✅ **Rank Math meta** — `rank_math_focus_keyword` (primary + secondary), `rank_math_description`, `rank_math_title` direct REST API dwara
- ✅ **Content quality** — useful length for the topic, short paragraphs, transition words; no forced 2200-3000-word target
- ✅ **Meta description** — 140-160 chars keyword tho
- ✅ **Tables + lists** — snippet-eligible formats

> Tip: WordPress lo **Rank Math plugin active cheyandi** — bot automatic ga plugin meta fill chestundi, editor lo open chuste 90-100/100 score kanipistundi.

---

## Daily working style

- Prathi గంట (hourly) scheduler bot ni run chestundi
- Bot roju morning 6 AM lo aa roju plan chestundi — default 3–5 draft slots (6 AM–10 PM madhya); quality review first
- Current hour plan lo undo → new article generate chesi publish chestundi
- Duplicate titles, category balance — antha automatic ga manage avtundi

## Useful commands

```bash
# v38 TOP POST (blueprint → measure → publish)
python run.py --keyword-universe                     # 11,192 keywords + CSV
python run.py --top-post "TSPSC Group 2 2026 notification"
python run.py --top-post-plan --top-post-days 90     # domination calendar
python run.py --score-post file.html --score-keyword "ssc cgl 2026"
python run.py --top-post "NSP Scholarship last date" --publish-top-post
```

```bash
# v39 COLLEGE EXAM PORTAL (students + admin console)
python run.py --exam-portal-demo            # sample exam tho start (try cheyyandi)
python run.py --exam-portal                 # production portal (admin key print avutundi)
python run.py --exam-portal --exam-port 9000 --exam-base-url https://exams.college.edu
python run.py --exam-portal-test-channels   # Telegram/webhook notification test
python tests/v39_exam_portal_test.py        # 14-section suite
```

```bash
# v41 SITE AUDIT + SAFE FIX
python run.py --site-audit                  # read-only audit (report files)
python run.py --site-audit-fix              # audit + fixes (dry-run default)
python run.py --site-audit-fix --site-audit-apply [--site-audit-trash]
python run.py --site-audit --site-audit-snapshot demo    # offline (network ledu)
python run.py --test-all                    # ANNI suites (30/30) okate command tho
python run.py --deploy-check                # deploy readiness + exam portal boot proof
python tests/v41_site_audit_test.py         # 15-section suite
```

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
| `DAILY_MIN` / `DAILY_MAX` | `3` / `5` | Draft slots per day; human review decides live posts |
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
   - Site new aite quality-first ga **2-4 reviewed posts/day** chalu — approval kosam volume guarantee kaadu
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
├── wsgi_dev.py             # v54 dev WSGI runner (:8090) for poll + lead forms
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
│   ├── seo.py              # Quick Answer + TOC + links + Article/Breadcrumb schema
│   ├── notifier.py         # Telegram (buttons) + WhatsApp alerts
│   ├── approval_bot.py     # 24/7 Telegram bot (publish buttons + URL rewrite)
│   ├── topic_engine.py     # Category rotation + mock generator
│   ├── image_gen.py        # v15/v16 PRO thumbnails — 3 layouts auto-rotate
│   ├── news_radar.py       # v15: TS+AP district breaking news + channel watch
│   ├── sources_grid.py     # v16.1: 105 official sources auto-watch grid
│   ├── keyword_engine.py   # v17: 980-keyword matrix + autocomplete + gap analyse
│   ├── state.py            # SQLite state (dedupe, plan, sources)
│   ├── site_setup.py       # v22/v28 site audit, plugins, theme report
│   ├── adsense_kit.py      # v28 validated Auto Ads widget installer
│   ├── production_audit.py # v30 production safety/revenue gate
│   ├── service_center.py   # v31 service page + consented case metadata
│   ├── content_audit.py    # v32 existing-post quality audit
│   ├── google_audit.py     # v33 public HTML + PageSpeed checks
│   └── top_post.py         # v38 top-post engine: 10k keywords, blueprint,
│                           #      scorer, harden, gate, dominance calendar
├── ci/github-actions-tests.yml  # v41 CI — 30 suites × 3 py versions (copy to .github/workflows/)
├── DEPLOY.md               # deployment guide — VPS(systemd+Caddy) / Docker / PaaS
├── DEPLOY_MILESWEB.md      # v49 cPanel/MilesWeb guide (Python App, cron, storage)
├── DEPLOY_ORACLE_CLOUD.md  # v51 Oracle Always Free vs MilesWeb split + crash-proofing
├── CONTENT_PLAN_DAILY.md   # v58 daily plan: 17 pillars, rhythm, refresh, SEO gates
├── breaking (autoblog/breaking.py)      # v59 site బ్రేకింగ్ feed + most-used order
├── guardian (autoblog/guardian.py)      # v60 roju automatic system check + alert
├── readiness (autoblog/readiness.py)    # v62 top-website readiness score (proof tho)
├── wordpress-theme/studentup/           # v61 REAL site theme (preview design → WP)
├── wp_theme_sync (autoblog/)            # v61 bot data → WP theme (REST push)
├── GO_LIVE_CHECKLIST.md A0              # edi ekkada run avutundi (architecture + 3 combos)
├── preview/data/breaking.json           # v59 ticker/section feed (radar writes)
├── AD_REVENUE_PLAYBOOK.md  # v52 revenue lines, rate card, sponsor + house ad flows
├── ad_advisor (autoblog/ad_advisor.py) # v57 network advisor + automatic alerts
├── GO_LIVE_CHECKLIST.md    # v53 deploy order + owner actions + revenue table
├── SALES_KIT_ADVERTISERS.md # v54 advertiser outreach templates + 90-day plan
├── AD_NETWORKS_PLAN.md     # v56 network thresholds (2026), uplift reality, apply checklist
├── SALES_KIT_ADVERTISERS.md # v54 advertiser outreach templates + 90-day plan
├── deploy/                 # systemd units · Caddyfile · nginx · Dockerfile · compose · backup.sh · install-vps.sh
├── autoblog/deploy_check.py # deploy readiness (deps/env/disk/port + real /healthz boot)
├── autoblog/site_audit.py  # v41 deep audit + safe autofix + live publish gate
├── exam_portal/            # v39/v47 college exam portal (stdlib only)
│   ├── store.py            #      SQLite: exams/questions/roster/sessions/answers
│   │                       #      + v47 poll_votes (daily poll bank + dedup)
│   ├── engine.py           #      validate, START/CLOSE, scoring, sweeper, exports
│   ├── notify.py           #      Telegram/webhook/in-app + copy-paste templates
│   ├── ui.py               #      landing + admin console + manage + student app
│   │                       #      + v47 "ప్రకటనలు" ads manager card
│   ├── server.py           #      HTTP server + CLI (no framework)
│   │                       #      + v47 /poll/today · /poll/vote (CORS) and
│   │                       #      /api/admin/ads CRUD → ads/inventory.json
│   └── demo.py             #      sample exam seed (--exam-portal-demo)
├── tools/
│   ├── ui_smoke.mjs        # v39 optional jsdom full-flow UI smoke test
│   ├── revenue_estimate.py # v53 ad revenue calculator (--views 10k / 1l / --json)
│   └── ad_network_plan.py  # v56 network eligibility + uplift (--views 50k --tier1 0.3)
└── tests/                  # end-to-end tests (fake WP/Telegram/source servers)
```
