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
python run.py --adsense-ready            # v94: AdSense approval READINESS gate
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

**1. ANNI KEYWORDS (12,344) — Keyword Universe**
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
Repo lo ready sample: `docs/design-archive/dominance-plan-90-days.md`.

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

## 🎓 v39 — College Exam Portal (retired in v74)

> **v74 note:** live exam avasaram ledu (owner decision) → exam portal motham
> teesesam (`exam_portal/` · `--exam-*` flags · `/exam` `/poll` `/lead` APIs ·
> portal deploy units). History kosam: `docs/design-archive/v39.html`.
> Daily quiz/question ippudu **server lekunda** (browser JS) pani chestayi;
> approvals `--approval-poll` cron tho vastayi (details kindha v74 section).

Related commands (migilina versions — v39 test poyindi):

```bash
python run.py --ad-advisor              # v57: eppudu e ad-network ki apply cheyyali
python run.py --ad-advisor --traffic-csv ga4.csv   # GA4 export → advisor (logs/traffic.json)
python run.py --breaking-feed           # v59: radar → site బ్రేకింగ్ న్యూస్ feed (ticker+section)
python run.py --breaking-from file.json # v59: feed ni JSON nunchi (offline/approved list)
python tools/parity_audit.py            # v69: PARITY AUDIT (CLI · modules · preview · docs · counts)
python tools/code_audit.py              # v68: CODE AUDIT — bot + theme bugs (E1–E12 · W1–W7)
python run.py --index-key-gen           # v68: IndexNow key (theme /<key>.key serve chestundi)
python run.py --index-status            # v68: instant indexing status (key · SA · signing)
python run.py --index-now URL           # v68: IndexNow + Google Indexing (JobPosting) submit
```

```
# v69: migilina advanced flags (anni docs lo — parity audit enforce chestundi)
python run.py --ads-demo                 # advanced control
python run.py --deep                     # advanced control
python run.py --deep-research            # advanced control
python run.py --approval-poll            # v74: Telegram approvals cron mode (*/5 min)
python run.py --tg-test                  # v91: Telegram connectivity ping
python run.py --tg-broadcast "MESSAGE"   # v91: channel announcement (auto-split)
python run.py --tg-alert "code|MESSAGE"  # v91: site notify queue push (v90 banner)
python run.py --tg-severity critical     # v91: --tg-alert severity level
python run.py --rebuild-hubs             # advanced control
python run.py --research-limit           # advanced control
python run.py --top-post-category        # advanced control
python run.py --traffic-sessions         # advanced control
python run.py --traffic-views            # advanced control
```

### v94 — ADSENSE READINESS + GOOGLE DISCOVER + CWV (theme 1.9.5)

**Mee brief:** "posts publish cheste ads approval ki problem leda? google lo mana
post suggest avvali ante em em miss avutunnam? chala miss avutunnam — anni fix cheyu".

End-to-end audit (repo + Google requirements) chesi **6 nijamaina gaps** kanukkunni fix chesam:

**GAP-1 ARTICLE SCHEMA LO `image` LEDU (pedda fix):** Google Article structured
data ki `image` **required property**. Bot schema lo adi ledu → Article rich result +
Discover large card eligibility thaggutundi. Ippudu `schema_jsonld` `image`
(ImageObject + 1200×675 dimensions) emit chestundi; featured image upload tarvata
`attach_schema_image()` tho **idempotent** ga attach avutundi (schema upload ki mundu
generate avutundi anduke — adi nijamaina wiring problem).

**GAP-2 DISCOVER LARGE-CARD IMAGE:** Discover pedda card ki **1200px+** image kavali;
theme 640×360 mattrame register chesindi. Fix: `studentup-discover` (1200×675) +
`og:image:width/height/alt` + Rank Math/Yoast filter (**duplicate tag lekunda** —
vaati OG image ni 1200px version ki upgrade chestundi mattrame).

**GAP-3 PRIVACY DISCLOSURE:** AdSense rule — "third-party vendors, including Google,
use cookies … opt out at Ads Settings" ane specific disclosure undali. Adi ledu.
Fix: privacy policy lo dedicated section (+ aboutads.info opt-out link + CMP line).

**GAP-4 POLICY PAGES FOOTER REACH:** AdSense reviewers + readers ki prathi page nunchi
policy pages kanipinchali. Fix: footer lo 5 links (publish ayyithe mattrame — 404 ledu).

**GAP-5 PRE-APPLICATION AUDIT LEDU:** "apply cheyyala?" ki okka chota jawabu ledu.
Fix: **`python run.py --adsense-ready`** — 8 groups · 29 mandatory checks ·
score + blockers + fix lines + JSON artifact.

**GAP-6 CLS/INP:** content images ki `width/height` ledu (layout shift) + mobile taps ki
~300ms delay. Fix: image dims filter + `touch-action: manipulation`.

**Proof:** `--test-all` **74/74** (v94_test.py kotha: 13 checks) · jsdom **164/164** ·
saved-engine **53/53** · readiness **100/100** · php-lint **38/38** · theme **1.9.5**.
AdSense readiness score: **97%** (1 blocker = posts volume — live publishing tho mattrame).

**Honest limit:** AdSense approval · Discover inclusion · ranking · traffic · revenue
**Google + mee account + time** batti untayi. Ee tooling technical/content requirements
ni ready cheyyagaladu — approval ni guarantee cheyyaledu. "Google lo suggest avvadam"
ante autocomplete/Discover placement — adi **Google algorithm**, daaniki code tho force
cheyyaleamu; cheyyagaligedi eligibility + quality signals mattrame.

### v107 — DIRECT GSC API + RANKING-DROP ALERTS

CSV export optional ga continue avutundi. Service account Search Console
property access configure chesthe direct sync:

```bash
python run.py --gsc-sync --gsc-days 28
```

Real page-level clicks, impressions, CTR and position fetch chesi v102 refresh
priority store update chestundi. Previous sync tho compare chesi 100+ impression
pages lo position 3+ drop or CTR 3-point drop alert chestundi. Low-impression
noise ignore chestundi. Credentials lekunte fake success kaadu; clear setup
message and CSV fallback istundi.

**Proof:** `--test-all` **87/87**; API row conversion, alert thresholds,
noise suppression, missing-credential safety and CLI wiring tested.

### v106 — SEARCH-INTENT + CONTENT CANNIBALIZATION AUDIT

Same intent kosam multiple pages compete chesthe ranking signals split avvachu.
Ippudu local published posts ni intent map lo classify chesi, similar pages
pair ni flag chestundi:

```bash
python run.py --cannibalization-audit
```

Recommendations only: `merge_or_301`, `choose_pillar_and_canonical`, or keep
separate intents with internal links. Automatic destructive merge/redirect
cheyyadu. Notification, apply, eligibility, syllabus, hall-ticket, result,
scholarship and current-affairs intents separate ga map chestundi.

**Proof:** `--test-all` **86/86**; duplicate intent, separate intent,
non-destructive recommendation and CLI wiring tested.

### v105 — UPDATE BACKUP + ONE-CLICK ROLLBACK

Old post refresh safe ga undadaniki WordPress revisions meeda matrame depend
avvakunda, prathi remote update mundu exact local backup create avutundi:

- old title/content/meta/date;
- new candidate HTML/meta;
- unified diff;
- editorial provenance ledger;
- timestamp and rollback-ready record.

Backup create fail ayithe remote WordPress PUT **refuse** avutundi. Wrong update
ayithe:

```text
python run.py --rollback-post POST_ID
# or exact file:
python run.py --rollback-post POST_ID --rollback-backup output/update_backups/file.json
```

Rollback explicit ga old state restore chestundi. Silent destructive update kaadu.
**Proof:** `--test-all` **85/85**; exact backup, candidate diff, rollback restore,
backup-failure refusal and CLI wiring tested.

### v104 — EDITORIAL VALUE + CLAIM PROVENANCE (expert quality layer)

No-copy wording alone saripodu. Source article ni paraphrase chesi low-value
page publish cheyyakoodadu. v104 prathi article ki internal evidence ledger
create chestundi:

- source URL, domain, tier and checked date;
- factual number/date claim context;
- claim ki support chestunna source IDs;
- unsupported claims human review flags;
- official links, action steps, local context, headings and table/list signals;
- practical editorial value score (word count ni reward cheyyadu).

Live publish lo provenance/value flags unte block; draft workflow lo flags human
review kosam preserve. Idi fake E-E-A-T badge kaadu — actual evidence ledger.
Source facts + independent explanation + Telangana/AP student usefulness add ayithe
matrame strong article candidate.

**Proof:** `--test-all` **84/84**; unsupported vacancy/date claims, no-source
authority, source tiers, practical signals and live gate tested.

### v103 — REAL-TIME MULTI-SOURCE ORIGINALITY CHECK (no-copy safety)

Local source comparison strong ga undi, kaani manam fetch cheyyani unknown web
page nunchi phrase copy ayithe local donors detect cheyyaleru. Ippudu final
article ki extra live layer add chesanu:

- article nunchi distinctive 9–24 word sentences select;
- exact quoted phrase ni live search chestundi;
- returned external pages fetch chesi phrase nijamga unda verify chestundi;
- exact match dorikithe **publish block** — `SKIP-LIVE-EXACT-OVERLAP`;
- own site URLs exclude chestundi;
- Google Custom Search API key + CX unte actual Google CSE result engine;
- credentials lekunte fallback engine honest ga report avutundi — fake “Google
  checked” claim ledu;
- `ORIG_LIVE_REQUIRED=1` tho live search unavailable ayithe kuda publish block
  cheyyachu; default 0 keeps infrastructure outages from stopping drafts.

Configuration: `ORIG_LIVE_CHECK=1`, `ORIG_LIVE_PHRASES=3`, optional
`GOOGLE_CSE_API_KEY` and `GOOGLE_CSE_ID`. Idi AI detector kaadu, legal copyright
verdict kaadu; exact web evidence checker. Local donor overlap, source rewrite
distance, near-duplicate, hard originality floor and now live phrase evidence
— five-layer protection.

**Proof:** `--test-all` **83/83**; v103 tests live match blocking, own-domain
exclusion, engine transparency, pipeline wiring and configuration.

### v102 — GSC-EVIDENCE REFRESH PRIORITY (advanced growth engine)

Oldest-first refresh kaadu. Ippudu real Search Console **Pages export** batti
high-value old posts first select avutayi:

- impressions unnayi, position 4–20 lo unnayi, CTR weak ga undi → high priority;
- URL matching exact ga jarugutundi (host/path normalise, query/fragment remove);
- query-only CSV ni reject chestundi — URL teliyakunda wrong post ni guess cheyyamu;
- scores SQLite state lo save avutayi, daily auto-refresh next matching post ni
  pick chestundi;
- GSC data lekapothe old safe priority (never-refreshed/oldest) continue;
- final update mundu freshness, originality, QA and post gates unchanged.

Run:

```text
python run.py --gsc-refresh search-console-pages.csv
```

Search Console: Performance → Pages → Export CSV. `--gsc` query export
opportunities kosam separate ga continue avutundi. GSC score ranking
**prediction kaadu**; content/title experiment priority matrame. Wrong URL
mapping or missing evidence unte automation guess cheyyadu.

**Proof:** `--test-all` **82/82**; v102 tests URL matching, score ordering,
query-export rejection, SQLite persistence, unmatched-page safety and CLI wiring.

### v101 — DECEPTIVE-FRESHNESS GUARD (highest-risk Google protection)

**Nenu top-expert level lo decide chesina next step:** NotebookLM integration
kanna, GSC automation kanna mundu **site ni Google spam-risk nunchi protect
cheyyadam** priority. Audit lo oka dangerous gap dorikindi.

**Critical gap:** daily `auto_refresh()` old posts ni refresh chestundi. Kaani
old vs new content nijamga entha marindo check cheyyakunda `dateModified` ni
eppudu today ki bump chestundi. LLM same content ni cosmetic ga rewrite chesina
kuda Google ki kotha update laga kanipistundi — roju automatic ga. Google
August 2026 spam update exactly **"dateModified bumped with no real change"**
(deceptive freshness) ni target chesindi; scheduled job pattern ayithe risk
inka ekkuva.

**Fix:** `autoblog/freshness.py` lo shingle-level content comparison + new
numbers/dates/facts audit add chesanu:

- identical / almost-identical refresh → **WP write kuda skip**;
- 2%–8% cosmetic/text-only change → **full WP write skip** (WordPress internal
  `modified` timestamp kuda marchakudadu);
- real change or new vacancy/date/fee facts → publish + `dateModified` bump
  allowed;
- defaults: 2% kanna takkuva change = skip; 8% kanna ekkuva change = genuine
  freshness signal. `.env` tho tune cheyyachu;
- `python run.py --freshness-audit` owner-readable status/report;
- failure-safe wiring: guard infrastructure fail ayina refresh aagadu, log avutundi.

Idi refresh ni aapadam kaadu — **fake freshness ni aapadam**. Google ki
"updated" ani cheppe right ippudu content change tho earn cheyyali.

**Proof:** `--test-all` **81/81**; v101 lo identical skip, cosmetic no-bump,
real new-fact bump, configurable thresholds, removed/new facts evidence,
pipeline wiring, CLI/config/docs assertions unnayi.

**Priority decision:** originality gate already strong ga undi; GSC import
already available (`--gsc CSV`). NotebookLM ki official API/source boundary
clear ga ledu, kabatti credentials/source provenance lekunda fake integration
add cheyyadam kanna, first Google spam-risk ni close cheyyadam expert decision.

### v100 — AUTOMATION WIRING + 3 REAL BUG FIXES (audit release)

**Mee brief:** "inka best ga em cheyyalo cheyu — anni fix cheyu".

Ee release lo **kotha feature kanna**, naa sonta v96–v99 code ni **audit**
chesi nijamaina bugs pattukunnanu. Ivi user ki kanipinchanavi, kaani silent
ga nashtam chesevi.

**GAP-1 🐞 AUTOMATION LEDU (pedda miss):** district hubs (v96) + link graph
(v99) — rendu **CLI-only**. Ante meeru **prathi vaaram gurtu pettukoni**
manual ga run cheyyali. Adi **jaragadu** (nijam cheptunna). Result: orphan
posts perigipotayi, district pages stale avutayi — nenu build chesina rendu
tools **waste**. Ippudu rendu **weekly cron slot lopala** (exam hub rebuild
jarige chotane) automatic ga run avutayi. Prathi okkati **try/except** —
okati fail aina **daily posting aagadu**. `DISTRICT_HUBS_AUTO=0` /
`LINK_GRAPH_AUTO=0` tho off cheyyochu.

**GAP-2 🐞 RELATIVE LINKS RESOLVE AVVATLEDU (naa v99 code lo bug):**
`/tspsc-group-2/` lanti **site-relative** link graph lo match avvadu —
"studentup.in/..." ga kaakunda "/tspsc-group-2" ga migilipoyedi. Result:
nijamga inbound links **unna** posts kuda **orphans ga report** ayyevi
(false positive) → anavasaram ga extra links add ayyevi (over-linking).
WordPress themes chala chota relative links emit chestayi kabatti idi
real-world lo **chala common**. Ippudu site-relative + protocol-relative
(`//host/path`) rendu resolve avutayi.

**GAP-3 🐞 `javascript:` URL href lo velthundi (XSS vector):** `seo._esc()`
**text** ni escape chestundi — kaani URL **scheme** ni validate cheyyadu.
So district hub table lo, link-graph insert lo
`href="javascript:alert(1)"` appatike emit ayyedi. WordPress sanitiser
save cheyyochu, kaani **manam emit chese HTML** lo ne adi undakudadu
(defence in depth). Fix: **`seo.safe_url()`** — scheme allowlist +
obfuscation guard (`java\tscript:`, `JaVaScRiPt:`, `data:`, `vbscript:`
anni block) + attribute-breakout quote escape.

**GAP-4 HUB PAGES INSTANT INDEXING KI POVATLEDU:** posts publish ayyaka
IndexNow ki submit avutayi (`_after_publish_push`), kaani **hub + district
pages** organic crawl kosam wait chesevi — konni rojulu. Ippudu avi kuda
submit avutayi (apply mode lo matrame, best-effort — IndexNow fail aina
rebuild aagadu).

**Proof:** `--test-all` **80/80** (v100_test.py kotha: 12 checks) — relative
link resolution, XSS scheme blocking (obfuscation included), weekly wiring,
IndexNow failure safety, mariyu v99 guards intact — anni asserted.

**Honest limit:** ivi **correctness + reliability** fixes. Ee release traffic
ni perchadu — kaani nenu build chesina tools **nijamga run avutayi** ani,
mariyu avi **tappu data meeda pani cheyyavu** ani guarantee chestundi. Adi
foundation; daani meeda ne migatavi pani chestayi.

### v99 — INTERNAL LINK GRAPH + FAQ/AI SCHEMA (orphan posts fix)

**Mee brief:** "anni build cheyu — Web Stories, link graph, FAQ schema".

Moodu adiganu. Research chesi cross-check chesaka **rendu build chesanu,
okati deliberately build cheyyaledu** — enduko kinda nijam ga cheptunna.

**GAP-1 🚨 ORPHAN POSTS (idi pedda, silent gap):** `seo.enhance()` prathi
**kotha** post lo internal links pedutundi — kaani adi **okka direction**:
kotha → purana. **Purana post ni evaru link cheyyaru** (adi publish
ayinappudu daani tarvata vachhe posts inka lev). Result: site lo
**inbound internal link ZERO** unna posts — Googlebot vaatini sitemap meeda
matrame depend ayyi crawl chestundi → crawl priority takkuva, ranking weak,
konnisarlu index kuda kaavu. **Idi Rank Math lo kanipinchadu** (adi single
page ni matrame chustundi) — idi **site-level graph** problem, anduke ippati
varaku miss ayindi.

**FIX — `autoblog/link_graph.py`:** live posts content nunchi **nijamaina**
link graph build chestundi (guess kaadu — actual `<a href>` parse), orphans /
weak / dead-ends diagnose chesi, prathi orphan ki **relevant** donor posts
(shared keywords + same category) kanukkoni vaati paragraph lopala
**contextual link** insert chestundi.

```
python run.py --link-graph                      # report matrame (edi marchadu)
python run.py --link-graph --link-graph-apply   # live posts lo apply
```

**Safety (idi LIVE content ni touch chestundi — anduke strict):** `--apply`
lekapothe **edi marchadu** · donor ki **max 1** kotha link per run · already
link unte skip (duplicate raadu) · nested `<a>` create cheyyadu · headings /
quick-answer / CTA / ad blocks lopala insert cheyyadu · self-link eppudu
cheyyadu · donor ki already 12 links unte skip (over-linking = spam signal) ·
anchor **natural title** nunchi (exact-match keyword stuffing kaadu) ·
**idempotent** (malli run cheste duplicate links raavu).

**GAP-2 FAQ SCHEMA — repo lo tappu assumption undedi.** Code lo
*"Google retired FAQPage in 2026"* ani FAQ schema motham skip chesaru.
Research chesi cross-check chesanu — **sagam nijam**: Google FAQ **rich
result** (SERP accordion) ni **7 May 2026** nunchi teesesindi, adi nijam.
**KAANI** Google schema ni content understanding ki inka parse chestundi,
mariyu **Bing Copilot · Perplexity · AI Overviews** lanti **AI retrieval**
systems daanni **actively** vadutunnayi — adi kotha traffic surface.
Google ye cheppindi: *"unused structured data does not cause problems for
Search"*. Kabatti FAQPage ni **tirigi** emit chestunnam — kaani **nijamaina,
visible Q&A 2+ unnappudu MATRAME** (thin/fake FAQ = manual action risk,
adi eppudu cheyyamu). Thin answers, duplicate questions, khali questions
automatic ga drop avutayi; `FAQ_SCHEMA_ENABLED=0` tho off cheyyochu.

**WEB STORIES — deliberately BUILD CHEYYALEDU (idi mee kosam save chesina
time).** Meeru adigaru, kaani research chesaka build cheyyakoodadu ani
తేలింది: Google **2024 lo** Web Stories ni Google Images nunchi **teesesindi**,
Discover **carousel** ni kuda **teesesindi**. Ippudu avi Discover lo **single
card** ga matrame kanipistayi, adi kuda "most likely US, India, Brazil"
ane weak language tho. Industry experts idi **"the demise of Web Stories"**
ani 2024 lo ne cheppparu. Ante: AMP-based separate content format, separate
templates, separate maintenance — **declining surface** kosam. Ade effort ni
link graph (durable crawl equity) + AI schema (growing surface) meeda pettadam
**chala better ROI**. Meeru "still kavali" ante cheppandi, build chestanu —
kaani honest recommendation **vaddu**.

**Proof:** `--test-all` **80/80** (v99_test.py: 14 checks) · orphan
detection, dry-run safety, idempotency, blocked-zone protection, FAQ thin/dupe
rejection — anni asserted.

**Honest limit:** internal links **crawl + equity** ni improve chestayi —
ranking ni **guarantee cheyyavu**. Orphan fix ante "rank avutundi" ani kaadu;
"Google ki ee page kanipistundi, daaniki site lopala context undi" ani.

### v98 — VIRAL SHARE ENGINE (free reach lever · theme 1.9.8)

**Mee brief:** "fully viral avvali · neatga undali · free ga inka best ga em
chesthavo adi cheyu".

**NIJAMAINA GAP:** share buttons **post chivara MATRAME** unnayi. Mobile lo
60–70% readers akkadi varaku scroll **cheyyaru** → vaallaki share option
**eppudu kanipinchadu**. Share = **free reach** (okka share → WhatsApp group lo
200 mandi). Idi manam ivvagalige **biggest free viral lever**, adi miss ayyindi.

**FIX — 3 parts (anni free, service/API avasaram ledu):**

**1. IN-CONTENT SHARE BAR:** modati H2 **+ aa tarvata modati paragraph**
tarvata compact share row (heading ki venakane buttons awkward ga untayi
anduke para tarvata). Reader "idi naaku kavalsinde" ani decide chese exact
point adi. Idempotent · `is_singular` + `in_the_loop` + `is_main_query` guards ·
H2 lekapothe content chivara (content eppudu maayam avvadu).

**2. RICH SHARE TEXT (bare URL kaadu):** WhatsApp ki వెళ్ళే text lo **title +
last date** untundi — *"TSPSC Group 2 Notification 2026 — Last date in 3 day(s)"*.
Group lo idi chusi tap chese rate, bare link kanna chala ekkuva.
**Fake urgency LEDU:** deadline meta lekapothe khali; deadline **dhatipoyinది
aithe** urgency line **raadu** (misleading = trust loss).

**3. NATIVE SHARE SHEET:** mobile lo `navigator.share` support unte reader tana
**own apps** (WhatsApp, Instagram, SMS, Gmail) ki **1 tap** lo pampochu — highest
conversion share path. **Feature-detect:** support lekapothe button
**hidden ye** untundi (broken button eppudu kanipinchadu; desktop lo normal
WA/TG links panichestayi). **Tracking/pixel LEDU** — privacy-safe.

Owner toggle: **StudentUp → Settings → "In-content share bar"** (default ON).

**Proof:** `--test-all` **79/79** (v98_test.py: 10 checks) · php-lint
**40/40** · theme **1.9.8** · zip 50 files · escaping + noopener/nofollow
asserted · no unescaped echo.

**Honest limit:** idi **organic sharing ni sulabham chestundi** — share
avutunda ledha ante mee **content quality** batti untundi. Fake/auto sharing,
bot clicks **eppudu cheyyamu** (adi AdSense invalid traffic + platform ban).
"Fully viral" ni code guarantee cheyyaledu; reach ki unna friction ni maatrame
teesesamu.

### v97 — REAL-TIME KEYWORD VERIFICATION (dummy keyword list kaadu)

**Mee brief:** "real time lo keyword verify cheyali — dummy/static keyword list vaddu".

**NIJAMAINA PROBLEM:** ippati varaku `focus_keyword` ni **LLM invent** chesedi
(leda title nunchi derive avutundi). Adi nijamga **evaraina search chese phrase
aa** ani check chese code **ekkada ledu**. Result: *"TSPSC Group 2 Notification
Complete Details Telugu"* lanti keyword — chudadaniki bagunnadi, kaani daaniki
**search demand ZERO**. Aa post ki Rank Math 100 vachina Google lo traffic
raadu, endukante **aa phrase ni evaru type cheyyaru**. Idi silent ga prathi
post ni debba tinipistundi.

**FIX — Google Autocomplete = LIVE demand proof.** Suggest lo oka phrase
kanipistundi ante, aa phrase ni users **nijamga type chestunnaru** (Google aa
list ni real queries nunchi build chestundi). Kabatti prathi post publish
avvadaniki mundu:

1. **VERIFY** — keyword prefix (modati 3 words) ni Suggest ki pampi, mana
   keyword (leda close variant) return avutunda ani chustam. Suggest lo
   **position = demand proxy** (#1 = highest).
2. **DETECT** — "complete details / full guide / everything you need" lanti
   **invented fluff** ni catch chestam (humans ila search cheyyaru).
3. **REPLACE** — verify fail ayithe, ade topic ki **Suggest lo nijamga unna**
   best phrase tho focus keyword ni replace chestam. **Topic drift guard:**
   "ts police" post ki eppudu "ap police" keyword raadu; fluff unna
   suggestions + 8-words kanna podugu phrases reject avutayi.

**Fail-open (important):** network ledu ⇒ verdict **`unknown`** — post
**block avvadu**, keyword **marchadu**, mariyu fake "verified" stamp
**eppudu veyyadu**. Cache (TTL 3600s) + 2 Google endpoints fallback.

```
python run.py --verify-keyword "tspsc group 2 notification"   # single check
python run.py --keyword-audit                                 # live posts bulk audit
```

**Proof:** `--test-all` **78/78** (v97_test.py: 12 checks, anni
offline-safe — fetcher inject chestam).

**Honest limit (idi telusukondi):** Autocomplete **exact monthly search
volume ivvadu**. Nijamaina volume numbers kavali ante paid API (DataForSEO /
Keywords Everywhere / Ahrefs) kavali — adi kavalante cheppandi, adapter
raastanu. Idi *demand undi / ledu* ane **binary + ordinal** signal mattrame.
Aina, invent chesina keyword kanna idi **chala better**. Suggest lo undadam
ante "rank avutam" ani kaadu — demand undi ani mattrame.

### v96 — COVERAGE MISS-ZERO + SESSION DEPTH + 3 REAL BUG FIXES (theme 1.9.7)

**Mee brief:** "ts and ap students ki em em posts vasthunnai … anni … job melas ·
every district pages jobs · university results · daily current affairs …
telegram and whatsapp buttons neatga madhyalo … ads refresh ayyevidam ga plan —
automation kadu, vere page ki vachi malli mundu page vachelaga … thumbnails
neatga and daniki name … chala miss chesam, chinna chinnavi kuda miss cheyoddu".

Deep coverage audit + code audit chesi **7 gaps** (andulo **3 nijamaina bugs**) fix chesam:

**GAP-1 COVERAGE MISS (job melas · district jobs · university results):** radar 59
districts ni scan chestundi, kaani grid lo job-mela, district-level recruitment,
university results (JNTUH/JNTUK/OU/AU/SVU…), dedicated hall-ticket axis mariyu
daily current affairs **queries ledu** — aa intents ki mana posts generate avvavu.
Fix: **180 sources** (37 kotha) + **221 entities → 12,344 keywords** (18 kotha
entities). Counts guardian + readiness lo lock ayyayi (stale docs = test fail).

**GAP-2 MID-ARTICLE JOIN BUTTONS (bot posts):** WhatsApp/Telegram CTA post
**chivara** mattrame undedi — chala mandi akkadi varaku scroll cheyyaru. Fix:
`monetize.join_strip_block()` + `insert_join_strip()` — modati **content** H2
tarvata (quick-answer skip), idempotent, links levakapote khali (fake buttons
raavu), number typo-safe (`9182739312` · `+91 …` · invite link · junk → None).
Theme `.su-join-inline` tho duplicate raakunda `cta.php` lo dedupe guard.

**GAP-3 "ADS REFRESH" — POLICY-SAFE ga (chala important):** timer/JS tho ad ni
auto-refresh cheyyadam = AdSense **invalid traffic** → account ban risk. Anduke
timer vaddu. Badhulu ga theme `inc/upnext.php`: article chivara **Up Next** (ade
category 3 posts) + mobile **sticky next-article bar** (55% scroll tarvata,
dismiss memory tho). Reader tap = **nijamaina kotha pageview = legit kotha ad
request**. Suite lo `setInterval/reload/redirect` ledu ani verify avutundi.

**GAP-4 THUMBNAIL NAME:** featured image eppudu `{slug}.webp` ga upload ayyedi.
Fix: `seo.image_filename()` — `focus-keyword-year-category.webp` (ascii-only,
stopwords/duplicate tokens ledu, 70-char cap, Telugu-only keyword ki fallback)
+ `seo.image_alt()` helper.

**GAP-5 🐞 REAL BUG — webp ni `image/jpeg` ga upload:** v81 lo webp default
ayyaka kuda `upload_media()` MIME ni hardcode chesindi. WordPress
`wp_check_filetype_and_ext()` mismatch valla konni hosts upload **reject**
chestayi → featured image ledu → Article schema/Discover image ledu. Fix:
extension → real MIME map + `Content-Disposition` lo kuda kotha SEO name.

**GAP-6 🐞 REAL BUG — refresh lo monetize blocks POYEVI:** `update_post()` lo
`monetize.append_blocks()` call **ledu**. So auto-refresh ayina prathi post nunchi
Telegram CTA + affiliate + join strip **delete** ayyevi (refresh ekkuva ayina
koddi CTA-less posts perigevi). Fix: update path lo monetize + ad_manager
wiring — QA/pin-gate ki **mundu** (score nijamaina final HTML meeda).

**GAP-7 DISTRICT PAGES LEVU:** 59 districts scan avutayi kaani landing page
okkati kuda ledu — "Karimnagar jobs", "Guntur job mela" lanti low-competition
local queries motham miss. Fix: `autoblog/district_hubs.py` + CLI
(`--district-hubs [--district-hubs-apply] [--district-hubs-state TS|AP]`):
prathi district ki posts table + job-mela section + nearby-district cross-links.
**Thin-page guard:** `DISTRICT_HUB_MIN_POSTS` (default 3) kanna takkuva posts
unte page **create avvadu** — khali shelves = Google scaled-content + AdSense
low-value risk.

**Proof:** `--test-all` **77/77** (v96_test.py: 17 checks) · php-lint
**39/39** · theme **1.9.7** · zip 49 files.

**Honest limit:** ee release **coverage + signals + session depth** ni
penchindi. Google ranking, "top 0.01%", Discover placement, AdSense approval,
views/clicks — avi **Google algorithm + mee content + time** batti untayi; code
vaatini guarantee cheyyaledu. Ad refresh ni policy-safe navigation tho
mattrame penchamu — auto-refresh **deliberately** implement cheyyaledu.

### v95 — SEO 100 PIN-TO-PIN + TERMS + IN-BODY SIGNALS (theme 1.9.6)

**Mee brief:** "fix" — remaining audit gaps (Rank Math/SEO 100 · contextual linking ·
policy completeness) okati okati ga close cheyyadam.

**GAP-1 CONTENT LOPALA IMAGE LEDU (pedda fix):** featured image mattrame undi,
article HTML lo `<img>` **ledu** → Rank Math "Focus Keyword in Image Alt" test fail,
Discover/rich-result ki in-article image support takkuva, engagement takkuva.
Ippudu `seo.attach_inline_image()` (featured image ni content lopala reuse):
`width/height` tho **CLS 0** · `loading="lazy"` + `decoding="async"` (LCP ni touch
cheyyadu) · figcaption · 2nd H2 tarvata (Discover top-of-article) · **idempotent**
(`<img>` unte no-op).

**GAP-2 IN-BODY CONTEXTUAL LINKS:** `su-related` section links mattrame unnayi
(footer-style, weak internal-link signal). Ippudu `seo.contextual_links()` —
paragraph **lopala** natural anchor: modati occurrence mattrame · `<a>` unna paragraph
skip (nested link ledu) · headings/tag attributes touch cheyyadu · idempotent ·
`CONTEXTUAL_LINKS_MAX` (default 3). CSS: `.su-ctx`.

**GAP-3 RANK MATH PARITY:** `slug-length` (URL ≤75 chars — `rm100._trim_slug`
guarantee) + `kw-in-img-alt` (image unte **mattrame** add avutundi → gate fair,
image lekunda score padipodu). Pin gate: **68/68 checks** (kotha `content_image`).

**GAP-4 TERMS PAGE:** AdSense/Google policy completeness ki **Terms of service** page
kavali (usage rules · copyright + correction route · ad disclosure · third-party links ·
"as is" information · liability limits · governing law India/Telangana · contact).
`tools/build_policy_pages.py` lo TERMS + nav + sitemap; footer lo 6వ policy link.

**Proof:** `--test-all` **76/76** (v95_test.py: 13 checks) · jsdom **164/164** ·
saved-engine **53/53** · pin gate **100/100 · 68/68** · readiness **100/100** ·
php-lint **38/38** · theme **1.9.6**.

**Honest limit:** "Google lo suggest avvali" anedi Google **algorithm** — code tho force
cheyyaleamu. Ee v95 chesindi: Rank Math/SEO checks pin-to-pin, in-body images, real
contextual internal links, policy completeness, terms page — ivanni Google ki *signals*
mattrame; ranking/traffic/approval/revenue Google + mee content + time batti untayi.

### v93 — TOP-WEBSITE UI PASS (theme 1.9.4: menu · icons · collisions)

**Mee brief:** "top website ui avvali and menu clear and neatga cheyu, icons
correctga vundali (whatsapp instagram telegram youtube), chala mistakes unnayi".

Deep audit (icons ni **render chesi** chusanu — grep kaadu) tho 4 nijamaina
mistakes dorikayi + anni fix:

**BUG-1 MENU CLUTTER (pedda fix):** fallback menu Home + 9 categories ni **flat ga**
render chesindi — prathi item ki description line tho → header lo 10 items, 2 lines
each, overflow. Approved preview design lo menu **grouped dropdowns** (Home · Jobs ▾ ·
Hall Tickets · Results · Current Affairs · Exams ▾ · More ▾). Ippudu theme kuda ade
istundi: `menu-item-has-children` + `ul.sub-menu` markup (anduke dropdown CSS pani
chestundi), caret, orange hover underline, keyboard focus ring, dark mode, and
"More" dropdown screen nunchi bayataki velladu. **Missing categories automatic ga
skip** (empty link ledu) + page links (Saved/Contact/About/Quiz) **publish ayyithe
mattrame** — menu lo 404 eppudu ledu.

**BUG-2 TELEGRAM LINK:** `studentup_social_links()['telegram']` v91 lo add chesina
**private-channel override** ni ignore chesindi → private invite unte footer rail +
mobile panel + footer link **tappu username** ki velledi. Ippudu resolver okkate source.

**BUG-3 FIXED-BAR COLLISION (mobile):** `.su-stickyad` (bottom:0 · z95) `.su-social`
row (bottom:10px · z45) ni full ga cover chesindi; footer bottom 24px valla
`.installbtn` footer text ni cover chesindi; saved rail/panel/toast kuda todukkunnayi.
Ippudu `su-has-stickyad` body class + footer safe space → overlap zero.

**BUG-4 CSS HYGIENE:** `.su-ad-lazy::after` lo `display` rendu saarlu (block → grid) — teesesa.

**Icons audit:** 8 icons (whatsapp · telegram · instagram · youtube · x · call ·
email · link) ni SVG path data nunchi **nijamga render chesi** verify chesanu —
anni correct + complete (`Z` closed paths) + brand gradients
(`#2bd46b` · `#37aee2` · `#f09433` · `#ff4e45`). Icon ↔ link mismatch audit: **0**.

**UI polish:** 64px header row · brand text · hero/section rhythm · subtle card
hover lift (reduced-motion safe) · footer safe space · toast reposition.

**Proof:** `--test-all` **73/73** (v93_test.py kotha: 12 checks) · jsdom
**164/164** · saved-engine **53/53** · readiness **100/100** · php-lint **37/37** ·
theme **1.9.4**.

### v92 — SAVED / READER RETENTION (theme 1.9.3)

**Mee brief:** "more and more advanced, fully deep" — deep audit chesi okka
nijamaina reader-facing gap kanukkunamu: **job notification ni save cheyyadaniki
daari ledu**. Student oka notification chusi "tarvata apply cheddam" anukuntadu,
kaani save cheyyaleru → tirigi ravatam thaggutundi.

**v92 — Saved (theme 1.9.3):** theme `inc/saved.php` +
`assets/js/studentup-saved.js`:
* 🔖 **Save/un-save** — prathi job card lo + single post lo (aria-pressed,
  keyboard + screen-reader ready). Toggle state buttons anni sync avutayi.
* **Saved rail + drawer** — count badge tho; panel lo saved list + ᳚Recently
  read᳛ (reading history) block. Escape / outside-click tho close.
* **`[studentup_saved]` shortcode** — /saved/ page create chesi paste cheyandi
  (menu lo link pettachu). Page template avasaram ledu.
* **localStorage mattrame** — DB table ledu · cookie ledu · server round-trip
  ledu (privacy-policy + AdSense ki clean, server load zero).
* **Graceful degradation** — private mode lo localStorage block aithe soft note
  + saving off; page eppudu break avvadu (PART-45 rule).
* Options: StudentUp → Content → "Saved / bookmarks" (default ON) +
  "Saved posts limit" (5–200, default 60; FIFO drop).
* **XSS-safe render** — items anni `textContent` tho (innerHTML ledu).

**Real behaviour test:** `tests/runtime/saved_runtime_test.js` (jsdom) —
**53 checks**: save/un-save, persistence, count badge, panel order, remove,
clear + cancel, XSS payload, /saved/ grid, reading history, FIFO cap,
blocked-storage fallback.

**Proof:** `--test-all` **72/72** (v92_test.py kotha: 11 checks) · jsdom
**164/164** · saved-engine **53/53** · readiness **100/100** ·
php-lint **37/37** · theme **1.9.3**.

### v91 — TELEGRAM TOOLS (theme 1.9.2) + v90 — NOTIFICATIONS (theme 1.9.1)

**Mee brief:** alerts ki standard surface ledu (logs lo matrame) · owner ki
manual Telegram toolbox kavali (connectivity test · PRIVATE channel
announcements · site alert push) · readers ki channel reach (private invite
support + join chip).

**v90 — Notifications (theme 1.9.1):** theme `inc/notify.php` — alert queue
(option-backed · code-wise dedupe · cap 20 · severities `info · warn ·
critical` whitelist) → **admin notices** (per-user dismiss, AJAX nonce) +
**CRITICAL public banner** (option gate `notify_banner`, localStorage
dismiss) + REST `/wp-json/studentup/v1/notify` (GET/POST/DELETE,
`manage_options` only). Prathi callback try/catch — PART-45 rule: notify
eppudu page/cron break cheyyadu.

**v91 — Telegram tools (theme 1.9.2):** bot `autoblog/telegram_tools.py` +
theme `inc/telegram.php`:
* `python run.py --tg-test` — bot ↔ owner chat ping + `getMe` identity
* `python run.py --tg-broadcast "MESSAGE"` — channel announcement; long text
  paragraph-wise **auto-split** (truncate kaadu — full text `(i/n)` parts);
  private `-100…` channel ids supported
* `python run.py --tg-alert "code|MESSAGE" [--tg-severity info|warn|critical]`
  — v90 notify queue ki REST push (critical → public banner)
* Theme: `studentup_tg_channel_url()` (private invite override option
  `telegram_channel_url`) + footer **join chip** (Telugu CTA) +
  `t.me/share/url` share helper. creds lekapote clear message + exit 0
  (cron-safe).

**Proof:** `--test-all` **71/71** (v90_test.py kotha: 8 checks ·
v91_test.py kotha: 10 checks) · jsdom **164/164** · readiness **100/100** ·
php-lint **36/36** · theme **1.9.2**.

### v89 — PREMIUM HOMEPAGE (theme 1.9.0: Central fix + live search + ticker + brand icons)

**Mee brief (screenshots pampincharu):** TS/AP Govt Jobs site lo asalu
kanipinchaledu · Central jobs section ledu · WhatsApp/Telegram/Instagram/
YouTube icons tappu ga vunnayi · "Read more" click pani cheyyatledu ·
search type cheste results load kavatledu · qualification dropdown plain ·
latest jobs scrolling ledu · Internet Center block Telugu lo neat ga kavali ·
laptop layout messy.

**Root cause:** live site categories `ts-govt-jobs` / `ap-govt-jobs` /
`central-govt-jobs` — kaani theme `ts-jobs` / `ap-jobs` ni direct
`get_category_by_slug()` tho vethikedi. Mismatch → **prathi section silent-ga
mayam** (cards · menu · mobile panel · chips · footer).

**Fixes (10):** alias resolver (`studentup_used_term()` + reverse
`studentup_theme_cat()` — card `data-cat` eppudu theme slug, chips filter
correct ga match) · **Central Govt Jobs** theme+bot+preview+guardian sync
(TS · AP · Central top-3, hot) · **Latest Jobs scrolling ticker** (own posts,
10-min cache, click → aa post open, hover pause) · **live search** (REST
dropdown, debounce, ↑↓ Enter Esc) · **brand SVG icons** (emoji 💬✈️📸▶️
poyayi — Simple-Icons paths, rail/mpanel/share/author) · card **"Read more"**
real permalink link (dead `<b>` kadu) · **విద్యార్థుల ఇంటర్నెట్ సెంటర్**
Telugu block + perks row (Application PDF · పూర్తి Guidance · Preparation
Group) + brand WhatsApp button · **animated quadd dropdown** (native select
no-JS safe) + **SSC · 10th** wording + SSC GD/MTS/CHSL keywords · laptop
**3×3 strip + 3-col grid + menu scroll/no-wrap + current-page pill**.

**Proof:** `--test-all` **69/69** (v89_test.py kotha: 10 checks) ·
jsdom **164/164** · readiness **100/100** · theme-audit **0/0** · theme **1.9.0**.

### v87 — FIX-ALL ROUND (update e2e + quiz + banners → 7 real fixes)

**Mee brief:** "fix all". Update flow e2e probe + quiz/banner visual audit
(real renders chusi!) — dorikina real bugs anni fix.

**Real fixes (7):** update rm100 `KeyError: 'after'` (v84 feature DEAD —
optimize returns `score`!) · update official-links gap (create parity) ·
quiz `--quiz-level 9` crash → clamp + questions 500 → 30 + dup-guard
pre-generate (LLM waste) · **Telugu banner tofu boxes** → transliteration
(PIL shaping ledu — deterministic Latin) · long-token canvas overflow →
hard-break · 3-line footer overlap → auto-shrink fit · empty focus_keyword
→ title-derived fallback · auto-refresh owner summary (cron silent fix).

**Proof:** `--test-all` **68/68** (v87_test.py kotha: 7 checks) ·
jsdom **164/164** · readiness **100/100** · theme-audit **0/0** · theme **1.7.2**.

### v86 — PROFESSIONAL POST AUDIT (final post e2e → 6 real fixes)

**Mee brief:** "oka professional post avvali — inka emaina bugs unte
advanced ga audit chesi fix cheyu". Full pipeline ni local source tho
end-to-end run chesi FINAL post HTML line-by-line audit.

**Real fixes (6):** duplicate related/read-also merge (same links tho rendu
sections!) + short titles · news-source "అధికారిక లింక్స్" mislabel —
gov/edu domains matrame (`is_official_domain` gate) · Telugu TOC anchors →
ASCII (`section-N` fallback, link↔id match) · DOUBLE breadcrumbs (theme +
content) — engine block remove, JSON-LD intact · pin-gate error-dict silent
success — source + update paths rendu ki honest ⛔ message.

**Proof:** `--test-all` **67/67** (v86_test.py kotha: 6 checks, e2e tho) ·
jsdom **164/164** · readiness **100/100** · theme-audit **0/0** · theme **1.7.2**.

### v85 — AUTO-BLOG PREP DEEP AUDIT (any URL + any length → 9 real fixes)

**Mee brief:** "inka audit cheyu — auto-blog prep lo chala bugs; prompt
correct/advanced, Telegram URL→post eme URL + entha lengthy ayina success,
100% RankMath/SEO/keywords". Fetch→prompt→parse→refine→bot full path audit.

**Real fixes (9):** source `<table>`+headings drop (vacancy/fee facts LLM
invent chesedi!) + 6000→18000 chars · **JSON schema contract** (content_html
key e prompt lo ledu — Empty-field fail loops!) · _parse_json repair
(trailing commas/control chars) + key aliases (content/html/body→content_html)
+ faq shapes · JS-site **JSON-LD fallback** (articleBody recover) · refine
context 20000 + **anti-truncation guard** (<70% = reject) · slug ASCII-only
(Telugu %E0.. slugs vaddu) · mid-text URL extract · bot sync-freeze fix
(pipeline thread + honest error message) · v84 test registration miss.

**Proof:** `--test-all` **66/66** (v85_test.py kotha: 9 checks) · jsdom
**164/164** · readiness **100/100** · theme-audit **0/0** · theme **1.7.2**.

### v84 — FULL BUG HUNT (money + ads + approvals → 11 real fixes)

**Mee brief:** "inka chala bugs undochu — anni fix cheyali, lekapothe amount/
ads/approvals pothayi". Systematic hunt (theme XSS · ad slots 6/6 · expiry ·
cron race · gate holes · TOC · update flow) — prathi doubt real-run tho verify.

**Real fixes (10):** strip_tags script/style drop (schema JSON +106 words →
gate false-pass HOLE!) · IST-explicit deadlines (UTC server bug) · AdSense
APPROVAL GATE (approved switch OFF unte code render kaadu — blank-box risk
zero) + pwa shared gate · hour-slot claim (double-post race) · --orphans
default sitemap + DEAD-url report + weekly cron · SQLite WAL+timeout · TG 4000
truncate · date-archive noindex + Yoast/AIOSEO stand-down · **DOUBLE TOC fix**
(rm100+enhance rendu — live posts lo 2 boxes!) · update_post rm100 re-run.

**Proof:** `--test-all` **65/65** (v84_test.py kotha: 13 checks) · jsdom
**164/164** · readiness **100/100** · theme-audit **0/0** · theme **1.7.2**.

### v83 — rm100 TRUE-100 (self-contradiction fix)

Engine-generated takeaways/TOC `<li>` ne engine check fail chesedi →
100 unreachable. Fix: check nunchi engine boxes exclude + content-length
message 1500 align. Proof live: 57→**100/100** (`reached100: True`).
v82_test.py 9th check (64/64 intact — suite file kotha kaadu).

### v82 — SELF-AUDIT REGRESSIONS (proactive hunt → 6 real fixes pin)

**Mee brief:** v81 tarvata "chala miss chesava" — nenu mundhe deep self-audit
run chesanu (real runs, no assumptions). Dhorikindi:

**Real fixes:** rm100 single-pass structure (TOC/table/FAQ — mundu thin
content lo 2nd pass varaku TOC skip) · leaderboard slot mismatch (option key
`top_leaderboard` vs code `leaderboard` — AdSense unit never loaded!) · house
ad `description` key accept (cards text lekunda vachayi) · crontab mkdir +
cron.log rotation · approval callbacks fail-closed + auto-claim loud warning ·
57 pyflakes cleanup (dead imports/vars).

**My-own-bug caught:** cleanup lo `NETWORKS` re-export thesesanu → v56 fail →
restore + regression pin (v82_test.py).

**Proof:** `--test-all` **64/64** (v82_test.py kotha: 9 checks) · jsdom
**164/164** · readiness **100/100** · theme-audit **0/0** · theme **1.7.2**.

### v81 — ULTIMATE SPEC GAP CLOSE (99 sections verify → 8 real gaps fix)

**Mee brief:** 99-section Ultimate Spec — FIRST AUDIT → PLAN → IMPLEMENT →
TEST → VERIFY. v80 overlap skip chesi kotha areas verify chesamu:

**Already covered (proof):** TOC smooth+dup-safe ✓ · JobPosting
future-validThrough-only ✓ · quiz analysis (✔/✘/skip/%/streak/review) ✓ ·
nav/footer menus ✓ · PWA offline ✓ · RSS (WP) · images slug-named+alt ✓ ·
revisions/scheduled (WP) · email→TG/WA channels ✓ · env secrets ✓.

**v81 lo fix chesina 8 NIJAMAINA gaps:**

| # | Section | Gap → Fix |
| 1 | §72 | `?qual=` filter URLs indexable → noindex,follow (category canonical only) |
| 2 | §2 | Sanitizer strips blockquote/pre/code → keep (callouts + code); iframe/video/script OUT (XSS) + prompt 3 spots |
| 3 | §7 | Mobile tables overflow → block+scroll-x CSS + pre/code styles + dark |
| 4 | §22 | JPEG only → **WebP emit** (smaller, PIL-verified) + .jpg compat |
| 5 | §32/§60 | Orphan detection ledu → `--orphans` sitemap crawl (inbound-0 report) |
| 6 | §65 | Admin health widget → published/drafts/expiring/expired/redirects |
| 7 | §37 | Search tracking ledu → GA4 `search` event (gtag-gated) |
| 8 | §76 | HSTS option (default OFF + is_ssl guard); CSP deliberate skip (AdSense risk) |

**Honest NOT IMPLEMENTED (spec §95 format):** mock-test series (needs
accounts/infra — roadmap; daily quiz + analysis live) · server page-cache
(hosting) · CSP header (break risk) · GSC-data dashboard (needs OAuth/API).

**Proof:** `--test-all` **63/63** (v81_test.py kotha: 10 checks) · jsdom
**164/164** · readiness **100/100** · php-lint **34/34** · theme **1.7.2**.

### v80 — MASTER PROMPT GAP CLOSE (50 phases verify → 7 real gaps fix)

**Mee brief:** 50-phase Production Master Prompt + 5 mandatory additions —
"verify, em miss ayyama?" Phase-by-phase repo verify chesamu:

**Already covered (proof):** on-page engine (RankMath+WP) · H1 single/home ·
job content model (prompt sections + v78 fallbacks) · AI pipeline
Official→verify→human-review→draft→fact→SEO-gate→publish ✓ · internal
linking (related/crumbs/prev-next/contextual) · sitemap (WP+news) ·
robots (WP+news) · canonical (WP) · search/404 noindex (perf.php) ·
schema (Article/Breadcrumb/JobPosting-eligible; FAQPage retired-skip honest) ·
category filters · image alt (bot) · CWV (lazy/CLS-reserved/content-vis) ·
mobile-first CSS · security headers · legal 6 pages · expiry badge+closing ·
404+search exist · a11y (skip-link/focus) · audit engines (post_gate/
guardian/readiness/theme-audit) · quality gates (live blocks) · freshness
dates · E-E-A-T author · ads policy-safe · logging (bot) · deploy checklist.

**v80 lo fix chesina 7 NIJAMAINA gaps:**

| # | Phase | Gap → Fix |
| 1 | P29 | Redirect manager LEDU → `inc/redirects.php`: JSON map, 404-only 301, chain-resolve direct, loop/open-redirect safe |
| 2 | P6/P16 | Archive/search H1 LEDU (h2) → H1 + CSS; category landing thin → subcat chips (child+counts) |
| 3 | P28 | 404 thin → popular categories + latest 5 (recovery) |
| 4 | P24/25 | GA4/GSC wiring LEDU → options + consent-aware GA4 load + verification meta + outbound/apply click events |
| 5 | P26 | Expired notice LEDU (badge only) → single expired box + category link (URL stable) |
| 6 | P5 | RankMath-absent fallback LEDU → description + OG (bot meta reuse) |
| 7 | P47 | Link-liveness tool LEDU → `tools/check_links.py` + `run.py --check-links` |

**Owner/hosting-side (code kaadu — GO_LIVE lo):** GSC verify submit · GA4 ID
paste · backups · CDN · actual GSC/GA4 monitoring · restore test.
**WP-core-provided (custom build avasaram ledu):** DB/admin/CMS/API/auth —
master prompt custom-stack assume chesindi, manadi WP stack.

**Proof:** `--test-all` **62/62** (v80_test.py kotha: 12 checks) · jsdom
**164/164** · readiness **100/100** · theme **1.7.2**.

### v79 — AUTHOR + MID-ARTICLE JOIN + MISS-AUDIT CLOSE

**Mee brief:** author kuda unte best kada? Blogs madhyalo Telegram/WhatsApp
join isthava? Inka em miss avuthunnama? — audit chesamu, anni close chesamu:

| # | Audit finding | Fix |
| 1 | Author box basic (📝 emoji, Person schema ledu, reviewed-date ledu) | **Logo avatar** (custom_logo→site-icon→emoji) + **Person schema** (jobTitle Education Editor) + **Reviewed date** + TG/WA follow links |
| 2 | Join block footer lo matrame (mid-article LEDU) | **`su-join-inline` strip after 2nd para** — existing social options reuse (duplicate kaadu); div-only (ad position + TOC safe); priority 12 (ad 20 kanna mundhu); feed/off-guard |
| 3 | single.php lo **tags + prev/next LEVU** | `the_tags` + post-nav (miss-audit close) |
| 4 | CSS gaps | Join strip + author img + tags + nav styles + dark mode |
| 5 | FAQ schema? | Deliberate skip — Google FAQ rich-results 2026 lo retired (seo.py doc honest note) |

Single-post surface ippudu 13/13: progress · crumbs · read-time · mid-ad ·
share · trust · author · tags · prev/next · comments · related · last-date
badge · qual labels. Join links 100% option-driven (hardcode ledu — no dummy).

**Proof:** `--test-all` **61/61** (v79_test.py kotha: 10 checks) · jsdom
**164/164** · readiness **100/100** · php-lint **32/32** · theme **1.7.2**.

### v78 — TOP-BLOG PERFECTION PASS ("edo final kaadu — best vache varaku")

**Mee brief:** prathi point real check · dummy/sample vaddu · retry chesthu
undali · correct data + many sources + NotebookLM · text peddga kakunda neat ·
colors/tables/tags/categories anni perfect · 100% top blog, emi miss avvakunda.
Method: **REAL probe** (pipeline ni nijamga nadipe) → gaps list → fix → malli
probe — numbers kindha (same thin input, no FAQ, 1 tag):

| Metric | v77 probe | v78 probe |
|---|---|---|
| Tables | 0 | **1** (facts extract fallback) |
| FAQ | 0 | **6 Q/A + su-faq wrapper** |
| Tags | 3 passthrough | **4+ auto** (focus+secondary+category+acronyms) |
| Originality `_orig` | None | **98.8%** (deep-sources feed) |
| RankMath strict | 88 | **96** |
| TOP POST | 84 STRONG | **90 🏆 TOP POST** |
| PIN gate | 86 (59/66) | **92 (62/66)** |

| # | What changed | Detail |
| 1 | **`extract_facts`** | Telugu+English regex: last_date/exam_date/vacancies/fee/age/qualification/salary — content nunchi (invent kadu) |
| 2 | **Table guarantee** | LLM table marchipoina facts nunchi su-facts table (8 rows varaku); facts levu = honest skip |
| 3 | **FAQ guarantee** | faq<3 aite facts nunchi Q/A templates + `<div class="su-faq">` cards wrapper |
| 4 | **Auto-tags** | `suggest_tags` (focus+secondary+category+TSPSC-style acronyms) + hygiene junk-block; real flow lo 7-8 tags |
| 5 | **`_orig` uniform** | `_deep_sources` nunchi kuda score — live gate rendu paths ki (None bug fix) |
| 6 | **Many sources** | `RESEARCH_MAX_SOURCES` 3→**5** (+ v77 official-outbound = deepest gather) |
| 7 | **Neat text** | Para split 120→100, chunks ~90→~70 words (wall-of-text break, meaning safe) |
| 8 | **Theme CSS** | `.su-lede` + `.su-faq` cards + dark mode + table zebra (mundu levu — live ugly fix) |
| 9 | **Proof** | `--test-all` **60/60** (v78_test.py kotha: 10 checks) · jsdom **164/164** · readiness **100/100** · theme **1.7.2** |

Verify chesina REAL (no dummy): NotebookLM brief-file merge + validation
(`create_from_source --notebooklm-brief`, bad brief = hard reject); category
auto-detect 17 rules; prompt already asks table/1500-2200w/tags 5-8/faq 4-6.

### v77 — ORIGINAL CONTENT ENGINE + HIGH-ADS READINESS ("Google accept chestunda?")

**Mee brief:** fully advanced + high ads · ads auto vasthaya? · reach vachaka
vere networks ki apply · URL isthe related content antha gather · 100%
RankMath/SEO real checks · no copy fresh content · Telegram update = fresh
re-trending · page-to-page fresh ads. Doubt ki straight answer: scores anni
self-measured (honest note undi), kaani v77 lo **copy-detection REAL**
(donor-vs-final % — proof tho) + gather deeper + update re-entry + rotation.

| # | What changed | Detail |
| 1 | **Official outbound gather** | Source page lopala links extract → gov/edu first rank → research auto-follow (notification PDFs · portals · syllabi richest facts) |
| 2 | **Rewrite-distance (REAL %)** | `validator.rewrite_distance()` — donor sources vs final shingle overlap; `copy-risk`/`rewrite`/`fresh` verdicts; prathi publish + update lo `_originality` log |
| 3 | **Update = re-trending** | News sitemap publish **OR modified** 48h (updated posts malli enter) + modified schema + Last Updated badge + IndexNow + `upd:` Telegram chain (verify chesam) |
| 4 | **Smart ad rotation** | Theme hour-base (24 fresh chances/day) + slot offset (oke page lo vere ads) + no-repeat; AdSense auto-refresh ledu (policy) — proof test |
| 5 | **Networks kit** | `AD_NETWORKS_APPLICATION_KIT.md` — naa review: AdSense first → Ezoic second → Journey/Monumetric milestones + apply checklist (code flips ready) |
| 6 | **Ads = 100% auto (proof)** | Auto-head gated (option + ca-pub regex) · in-article auto ON · density cap · consent gate · house fallback — manual placing ZERO |
| 7 | **Proof** | `--test-all` **59/59** (v77_test.py kotha: 10 checks) · jsdom **164/164** · readiness **100/100** · php-lint **32/32** · theme **1.7.2** |

Honest (repeat): Google ranking/traffic/approval/revenue = Google + accounts +
time. v77 = copy-paste IMPOSSIBLE-proof + deepest gather + fastest re-index path.

### v76 — QUALIFICATION DROPDOWN (chips → select) + UI DE-JUNK

**Mee brief:** "10th jobs ilaga filters best ga undali dropdown lo" · live
exam avasaram ledu · UI inkbest + sodi lekunda · more easy + advanced.
Chips row (9 buttons clutter) → **single dropdown**: native mobile
control · **live counts** (`10th Pass (3)`) · **shareable `?qual=` links**.
Preview + WP theme rendu (parity) — filtering engine same (v72 intact).

| # | What changed | Detail |
| 1 | **Preview dropdown** | `select#qualsel` + label + `qcount`; JS counts grid nunchi auto; `?qual=` deep-link + history sync; no-JS kuda options kanipistayi |
| 2 | **Theme parity** | `qual_bar()` → form GET + select + noscript button; counts server-side; `closing` option kotha (server-side support mundhe undi); JS reload-lekunda filter + ?qual= state sync bug fix |
| 3 | **Live-exam final proof** | Product surfaces lo `live-exam` 0 (v74 removal hold — automated test); quiz = practice matrame (6 questions, exam conduct kaadu) |
| 4 | **UI sodi clean** | In-feed ad dup text fix ("Your brand" okasari); tel: 10-digit intact; poll/quiz distinct blocks |
| 5 | **Proof** | `--test-all` **58/58** (v76_test.py kotha: 10 checks) · jsdom **164/164** (same count, dropdown mechanics) · readiness **100/100** · php-lint **32/32** · theme **1.7.2** |

### v75 — CONTACT FINAL (+91 ledu) + PUBLISH SAFETY + DUMMY PURGE

**Mee brief:** "+91 avasaram ledu" · website fully final · more advanced ·
all bugs fix. Call links/display lo **10-digit number matrame**
(`9182739312`); wa.me buttons work avvali kabatti links lo country code
untundi (kanipinchadu). Theme auto-normalize chestundi — owner 10-digit /
+91 / 0 tho emichina anni chotla correct links.

| # | What changed | Detail |
| 1 | **Contact final** | `tel:` + visible text lo +91 ledu (preview · policy pages · theme CTA); wa.me/919182739312 buttons intact; `studentup_wa_number()` + `studentup_call_number()` normalizers + 10-digit defaults |
| 2 | **Mock publish block** | `--mock` ante auto dry-run (`main.run` + `top_post_run`) — thin test stubs WordPress ki eppudu vellavu |
| 3 | **Dummy purge** | Demo inventory ads `active:false` (fake ads live posts loki ravu) · dead `#exam` house ad → `#jobs` · theme sync inactive/dead-link promos filter |
| 4 | **Bug hunt** | `THEME_PATH` dead code · `uplift` import shadow · dead vars · guardian ads count honest (live/total) · v59 time-bomb + `.venv` hardcodes fix |
| 5 | **Proof** | `--test-all` **57/57** (v75_test.py kotha: 10 checks) · jsdom **164/164** · readiness **100/100** · guardian · parity **0/0** · code audit **0/0** · theme audit **0/0** · php-lint **32/32** · theme **1.7.2** |

### v74 — LIVE EXAM REMOVAL + CRON-ONLY BOT ("live exam avasaram ledu")

**Mee brief:** live exam portal **vaddu** · anni neat + perfect + advanced · MilesWeb
premium lo **pakka deploy** avvali. And that's what this is: portal motham teesesam,
bot ippudu cron-only (servers/ports levu) — shared hosting lo anni pani chestayi.

| # | What changed | Detail |
|---|---|---|
| 1 | **Portal deleted** | `exam_portal/` (4,864 lines) · `passenger_wsgi.py` · `wsgi_dev.py` · `--exam-*` flags · `EXAM_*` env · portal systemd units/proxy · `tests/v39` + `tests/v49` · `tools/ui_smoke.mjs` — anni poyayi |
| 2 | **Static daily question** | `/poll/today` + `/poll/vote` API badulu **7-question bank** (IST date rotation, localStorage vote, instant correct-answer reveal) — server ledu kabatti fake counts levu |
| 3 | **WhatsApp-compose lead form** | `/lead` API badulu contact form details ni **WhatsApp message ga** ready chesi owner ki open chestundi (validation + honeypot same, store ledu) |
| 4 | **Approvals via cron** | `run.py --approval-poll` — okka poll pass (Telegram ✅/🗑️ buttons cron lo kuda pani chestayi, ~5 min rhythm); VPS daemon optional ga migilindi |
| 5 | **Deploy simplified** | Bot timer + watchdog (website + bot-freshness + disk/TLS) + Docker loop + `crontab.example`; Caddyfile ippudu **static site** kosam (proxy ledu) |
| 6 | **Theme 1.7.2** | `exam_url` + `api_base` options · header exam buttons · dead `?studentup_exam=1` PWA shortcut poyayi; shortcuts = Jobs · Qualification · Results · Quiz |
| 7 | **Fresh-clone proof** | `php-parser` ippudu declared dep + CI lo node install (mundu fresh clone lo 8 suites fail ayyevi — env trap, ippudu ledu) |
| 8 | **Proof** | `--test-all` **56/56** · jsdom **164/164** · readiness **100/100** · guardian · parity **0/0** · code audit **0/0** · theme audit **0/0** · php-lint **32/32** · theme **1.7.2** |

MilesWeb answer (honest): WordPress site + bot cron + Telegram approvals + static
quiz/question — **anni MilesWeb premium shared lo run avutayi** (details:
`DEPLOY_MILESWEB.md`). Okkate tradeoff: approvals ~5 min late (cron rhythm).

### v73 — ENGLISH UI PASS + HERO BLOCK REMOVAL ("idi avasram ledu")

**Mee brief:** hero block (eyebrow · big Telugu h1 · lede · అవకాశాలు CTA · live-countdown card ·
అర్హత/మూలం tiles) **teeseyali** · site antha English lo (menus · buttons · chips · notes · footer ·
headings/labels) — Telugu mattrame job/article content lo.

| # | What changed | Detail |
|---|--------------|--------|
| 1 | **Hero block poyindi** | Countdown card, tiles, CTA, eyebrow — motham teesesaam. Badulu chinna English hero: h1 + one honest line ("Official-source updates for TS & AP students. Always confirm a deadline once in the official notification."). |
| 2 | **Countdown + deadline plumbing teesesaam** | Preview lo `#cd-live`/`#cd-none`/`data-deadline`/`data/deadline.json`, theme lo `studentup_deadline()`, bot lo `wp_theme_sync.write_preview_deadline()`, `.env` `POST_DEADLINE_*`, WP option `deadline_json` — anni poyayi (dead code ledu). Nijamaina deadlines ippudu post content + `studentup_last_date` badge lo. |
| 3 | **UI antha English** | Menu (Home · Jobs · Hall Tickets · Results · Scholarships · Current Affairs · Exams · More), search panel, chips (All · TS Jobs · … · Degree · ⏳ Closing in 7 days), qualification sections, ads labels, poll/quiz chrome, install sheet, footer, sw.js offline page, manifest shortcuts. |
| 4 | **6 policy pages English** | about · contact · advertise · privacy · disclaimer · editorial-policy — 0 Telugu chars, `lang="en"`, og:locale en_IN, ld+json inLanguage en-IN. |
| 5 | **WP theme English** | 27 files lo 5,284 Telugu chars → 0 (detection keywords block `studentup_qual_keywords()` mattrame Telugu ga undi — posts Telugu headline nunchi tag cheyyadaniki avasaram). Bot `MOST_USED` labels/hints kuda English (site/bot parity). |
| 6 | **Scope (mee choice)** | UI/labels/headings English; job/article content (post titles, summaries, quiz questions) Telugu — avi notifications nunchi vastayi. |
| 7 | **Proof** | `--test-all` **57/57** · jsdom **162/162** · readiness **100/100 (28/28)** · guardian **14/15** · parity **0/0** · code audit **0/0** · php-lint **32/32** · theme **1.7.1** (copy/UI pass — version same) |

**Language rule (ippudu):** website UI antha English; Telugu mattrame post/article content lo
(job titles, summaries, quiz questions). Internal reports/docs Telugu-English mix lo unnayi (owner kosam).

### v72.1 — అర్హత SECTIONS + ALWAYS-VISIBLE APP DOWNLOAD + CLEAN PUBLIC COPY

| # | Feature | Enti (mee brief → implementation) |
|---|---------|-----------------------------------|
| 0 | **Public copy clean** | Coverage topbar (33/26 జిల్లాలు line), hero proof stats, "ప్రత్యక్ష పరీక్ష" wording, 7-విషయాల demo article (share buttons tho) — anni public surfaces nunchi teesesaam. |
| 13 | **అర్హత ప్రకారం విభాగాలు** | "అర్హత ప్రకారం చూడండి": 10వ తరగతి · ఇంటర్ (10+2) · ఐటీఐ · డిప్లొమా · డిగ్రీ · పీజీ · బీటెక్ + "⏳ 7 రోజుల్లో ముగిసేవి". Groups grid cards nunchi **JS automatic** build avutayi (`buildQualSections`) — kotha post vasthe ade kshanam list lo vastundi, **manual tagging ledu**. |
| 14 | **Chips + విభాగాలు kalisi** | Category chip + అర్హత chip rendu kalisi filter (page reload ledu) · `?qual=` URL sync · గడువు ముగిసినవి దాచి `#su-hidden-note` note. |
| 15 | **App డౌన్‌లోడ్ (prathi visit)** | "⬇️ App డౌన్‌లోడ్ FREE" button prathi visit lo (mobile-first) · click tho device-wise sheet (Android Chrome prompt · iPhone Share · Computer icon) · `inc/pwa.php` manifest ki shortcuts (Jobs · అర్హత · ఆన్‌లైన్ పరీక్షలు). |
| 16 | **Countdown data-driven** (v73 lo teesesaamu) | Hero countdown hardcoded date ledu — `preview/data/deadline.json` (bot `--push-theme-data` rasi pettedi). **v73:** hero block tho paatu ee countdown + plumbing motham poyindi (post-level `studentup_last_date` badges mattrame migilayi). |
| 17 | **Ads nijamainaవి** | Demo advertisers (ABC academy/college/tuition/stationery) → house "స్లాట్ ఖాళీ · మీ ప్రకటన ఇక్కడ" creatives (SPONSORED + `rel=sponsored nofollow`), CTA → Partner page. |
| 18 | **Admin widget** | WP dashboard: "StudentUp · విద్యార్హత ప్రకారం ఉద్యోగాలు" — qualification-wise counts + tag-leni posts count. |
| 10 | **Theme v1.7.1** | `inc/qual-filter.php` (directory + notes + widget) · `assets/js/studentup.js` (combined filter + grouping) · `assets/js/studentup-pwa.js` (sheet) · version parity `style.css` ↔ `STUDENTUP_VERSION` ↔ `readme.txt` = **1.7.1**. |

### v72 — QUALIFICATION FILTER + HEADER SEARCH + PWA INSTALL + CLEAN COPY

**Mee brief:** బ్రేకింగ్ న్యూస్ అవసరం లేదు · internal metrics/radar/నమూనా maatalu public ga vaddu ·
విద్యార్హత ప్రకారం ఉద్యోగాలు **automatic** ga filter avvali (10th · 10+2 · ITI · Diploma · Degree ·
PG · B.Tech) — WordPress lo kuda, manual tagging lekunda · menu pakkana neat search · mobile lo
app-laga install (PWA) · colorful premium look, text/background contrast eppudu break avvakoodadu.

| # | What changed | Detail |
|---|---|---|
| 1 | **బ్రేకింగ్ న్యూస్ teesesaam** | Ticker + section + nav/mobile links + JS + CSS anni public sitenunchi poyayi. Bot radar feed (`autoblog/breaking.py`) intact — WP admin → *StudentUp → కంటెంట్ → బ్రేకింగ్ న్యూస్ సెక్షన్ ON* tho eppudaina tirigi on cheyyochu (**default OFF**). |
| 2 | **Internal metrics public lo levu** | Homepage proof-stats row (12,344 keywords · 180 sources · 59 districts) mariyu topbar/footer district lines teesesaam. Ee numbers ippudu internal reports/README lo mattrame. |
| 3 | **"నమూనా/DEMO" labels poyayi** | Public pages + theme copy nunchi demo/sample maatalu clean chesam (ads ki **SPONSORED** label intact — AdSense rule). |
| 4 | **విద్యార్హత ఫిల్టర్ (flagship)** | Job cards ki `data-qual`; chips: అన్నీ · 10వ తరగతి · ఇంటర్ (10+2) · ఐటీఐ · డిప్లొమా · డిగ్రీ · పీజీ · బీటెక్ · ⏳ 7 రోజుల్లో ముగిసేవి. Filter + search kalisi pani chestayi, count ("12 అవకాశాలు") chupistundi. |
| 5 | **Countdown + closing filter** | `data-last` unna cards ki "⏳ N రోజుల్లో ముగుస్తుంది" badge; గడువు ముగిసినవి default ga hide (`.expired`). |
| 6 | **Menu pakkana search** | 🔍 button → neat search panel (Enter/`/` shortcut); mobile menu lo "వెతకండి" link. WordPress lo idi `?s=` search ki connect (server-side). |
| 7 | **యాప్గా ఇన్స్టాల్ (PWA)** | `manifest.webmanifest` + `sw.js` (offline page, repeat visits fast) + "⬇️ యాప్గా ఇన్స్టాల్ చేయండి" button (Android `beforeinstallprompt`, iPhone Share hint). Theme lo `inc/pwa.php` + `assets/js/studentup-pwa.js` (`?studentup_sw=1` tho root-scope SW — kotha rewrite rules avasaram ledu). |
| 8 | **WordPress: automatic tagging** | `inc/qual-filter.php` — post save lo title+content nunchi అర్హత detect → `studentup_qual` meta; bot `autoblog/qual.py` kuda same tags REST tho pampistundi; purana posts ki admin/`wp studentup-qual-backfill` backfill; front-end `?qual=degree` server-side `WP_Query` filter (JS lekunda kuda pani chestundi). |
| 9 | **Contrast + neatness** | Brand gradient (text gradient safe-fallback tho), beige/blue chip tones, dark-mode overrides, `overflow-wrap` + flex-wrap rules — mobile lo text overlap ledu, contrast eppudu safe. |
| 10 | **Theme v1.7.0** | New: `inc/qual-filter.php` · `assets/js/studentup-pwa.js` · header search. Version parity: `style.css` ↔ `STUDENTUP_VERSION` ↔ `readme.txt` Stable tag. |
| 11 | **Slug parity (bot ↔ theme)** | Python `qual.QUALS` ↔ PHP `studentup_qual_terms()` — test ee rendu list ni compare chestundi, so filter chips eppudu match avutayi. |
| 12 | **Proof** (v72.1 tarvata) | `--test-all` **57/57** · jsdom **162/162** · readiness **100/100 (28/28)** · guardian **14/15** (1 warn-only owner env) · code audit **0/0** · parity **0/0** · theme audit **0/0** · php-lint **32/32** · zip **41 files 642 KB** |

**Language rule (v72.1 → v73 update):** v73 lo website UI **antha English** (menus · chips · buttons ·
notes · footer · policy pages); Telugu mattrame job/article content lo (post titles, summaries, quiz
questions). Internal metrics docs/reports lo mattrame.

### v71 — STUDENTS INTERNET CENTER + CLEAN MONETISATION (no public rate card)

**Your brief:** a premium, English-first site where needed; the application-help service explained
properly (call → WhatsApp documents → PDF back); no public rate card or booking flow (dealt
personally); WhatsApp/Telegram join instead of a newsletter form; smaller icons on mobile; and a
floating rail that appears, hides, and returns every 2 minutes so it never covers the text.

| # | What changed | Detail |
|---|---|---|
| 1 | **Students Internet Center (TS & AP)** | New card on the homepage + a section on every theme page: *call us → WhatsApp your documents → we apply and send the PDF*, lowest service charge. Wallet-friendly `wa.me` CTA box (opens your WhatsApp), `tel:` call button and email fallback. |
| 2 | **Public rate card removed** | The ₹4,000/₹3,500/₹3,000/₹2,000/₹8,000 table, the 3-step booking flow and the sidebar "Advertise" card are gone. `pages/advertise.html` is now a clean **Partner with us** page: placements, policy, house-ads note, and "rates & availability are shared personally". |
| 3 | **Rate card is internal now** | `autoblog/rate_card.py` is the single source of truth (5 slots + full package + 3 premium services). `tools/revenue_estimate.py` reads it; `--rate-card` prints the WhatsApp/Telegram-ready card for personal dealing. |
| 4 | **Newsletter form → join block** | The "free updates" form was replaced on the homepage by a **WhatsApp + Telegram join block**. The lead form itself moved to `pages/contact.html` (v74: `/lead` API poyindi — ippudu WhatsApp-compose form, honeypot + validation same), so the lead engine keeps working. |
| 5 | **Social rail with a 2-minute cycle** | Rail shows for 9 s, slides away, returns every 2 minutes. ✕ hides it instantly (returns after 2 min), ‹ pulls it back. Hover/focus keeps it, `Escape` closes it, reduced-motion respected. Same behaviour in the theme (`assets/js/studentup.js`). |
| 6 | **Mobile polish** | Social chips 34 px (31 px under 400 px), mobile-nav icon row tighter, join CTA full-width on phones — text stays readable. |
| 7 | **Theme v1.6.0** | New `inc/cta.php` (Internet Center + join blocks on every page) and `inc/editor.php` (block-editor parity with `assets/css/editor.css`). Version parity: `style.css` ↔ `STUDENTUP_VERSION` ↔ `readme.txt` Stable tag. |
| 8 | **Proof** | `--test-all` **55/55** · jsdom **138/138** (now merges the v70 removal suite with 12 core-product assertions; every suite has ≥1 behavioural check) · readiness **100/100 (28/28)** · guardian **14/15** (1 warn-only owner env) · code audit **0/0** · parity **0/0** · theme audit **0/0** · php-lint **31/31** · zip **39 files 633 KB** |

**Language rule (your call):** business/product copy is premium English; Telugu stays where it
helps the student (content, trust notes, the service line under the English steps).

### v70 — PUBLIC SURFACE CLEANUP (developer text/proof block remove) + 100% verification

**Mee maatalu: "100% ధృవీకరించి, తర్వాతే ప్రచురణ … i dont want these all things no use so remove".**
→ Site meeda kanipinche **verification-proof block** (stat tiles · ①–⑤ gates · honest note) mariyu
**developer/pipeline text** anni public surfaces nunchi teesesaru. Checks ippudu **internal ga**
(guardian + readiness + parity + tests) continue avutayi — kani **visitor ki kanipinchavu**.

| # | Emi chesaru | Detail |
|---|---|---|
| 1 | **On-site proof block remove** | `preview/index.html` nunchi trust/qgate section (headline · 7 stat tiles · ①–⑤ gates · honest note) + CSS teesesaru → mobile lo aa 3 links ippudu policy pages (`pages/editorial-policy.html` · `pages/contact.html` · `pages/privacy.html`) ki veltayi |
| 2 | **Theme proof remove** | front-page hero-proof tiles · `studentup_proof_tiles()` · theme option `proof_json` · `breaking.php` REST param `proof` · hero-proof CSS · README-THEME proof row — **anni gone** |
| 3 | **Policy pages clean** | `tools/build_policy_pages.py` notes (disclaimer/advertise) nunchi developer text remove → pages regenerate |
| 4 | **Dev archive** | `v38/v39/v41/legacy-concept/ads-preview/top-post-blueprint.html` + `dominance-plan-90-days.md` → **`docs/design-archive/`** (preview server ee folder ni serve cheyyadu — website meeda eppudu kanipinchadu · robots `Disallow: /_dev/` safety-net) |
| 5 | **Regression lock** | Guardian check `counts_sync` (suites ↔ README + public surfaces lo developer text ledu) · readiness `c_counts_sync` · parity **P8** (docs claims + public-text ban) · jsdom 2 clean-checks |
| 6 | **Nijamaina bug fix (v70 lo pattukunnadi)** | `wp_theme_sync.build_payload()` nunchi `options` + `deadline` blocks + `return out` accidentally poyayi → options/deadline/indexnow sync aagipoyedi. Ippudu restore (daily hook malli pani chestundi) |
| 7 | **Proof** | `--test-all` **55/55** · jsdom **138/138** · readiness **100/100 (28/28)** · guardian **14/15** (1 warn-only owner env) · code audit **0/0** · parity **0/0** · theme audit **0/0** · php-lint **29/29** |

**Rule ippati nunchi:** public page lo **developer/verification text undakoodadu** — proof antha
`output/` (proof docs) + Telegram + guardian status lo. Visitor ki: content · trust note ·
corrections email mattrame.

### v69 — THEME STANDARDS PASS 3 + PARITY AUDIT (emi miss avvakoodadu)

**Mee maatalu: "fix all bugs · advanced top-level website avvali · anni pin to pin · emi miss
avvakoodadu · everything must check and implement/fix".** → theme ni WordPress top-theme
standards ki mirror chesamu + kotha **parity audit** tho code ↔ docs ↔ preview ↔ counts
surfaces ni kalipesamu (edi ekkadaina miss aithey adi **fail** avutundi).

| # | Enti | Ela |
|---|---|---|
| 1 | **Nijamaina bug — version mismatch** | `style.css Version: 1.0.0` vs `STUDENTUP_VERSION 1.3.0` → WordPress ki telisedi **style.css** (theme screen · child themes · cache-busting) → ippudu **1.5.0** rendu chota + **build gate** lo check |
| 2 | **Block editor parity** (advanced theme standard) | `add_theme_support('editor-styles')` + `wp-block-styles` + kotha `assets/css/editor.css` (front-end tokens/typography/quote/table/heading accent editor lo same) |
| 3 | **WP standard markup + E-E-A-T author archive** | loops lo `post_class()` · nav lo `aria-current="page"` · kotha **`author.php`** (bio · prachurita vyasala count · profile link · editorial-policy link — Google ki "ee vyasam evaru rasinaru?" jawabu) |
| 4 | **Perf (shared hosting)** | custom `WP_Query` calls ki `no_found_rows` — page load ki **2 extra SQL queries** taggayi (front-page grid + related posts) |
| 5 | **Standards pass 3 audit** | version parity · editor styles · `post_class` · `no_found_rows` · admin nonce (`settings_fields`/`wp_nonce_field`) · `sanitize_callback` — anni permanent ga `tools/theme_audit_deep.py` lo (malli regress avvavu) |
| 6 | **Parity audit** (`tools/parity_audit.py` NEW) | **P1** CLI ↔ docs (92 flags) · **P2** dead modules (43 → 0) · **P3** preview links · **P4** preview meta (deployed pages) · **P5** robots↔sitemap↔ads.txt · **P6** tools references · **P7** placeholder text (TODO/FIXME/lorem) · **P8** count sync |
| 7 | **Dorikina misses → fix** | 7 CLI flags docs lo levu (ippudu 92/92 documented — README block) · 6 policy pages ki `robots` meta ledu (ippudu unnai) · parity audit itself reference avvaledu (ippudu README + readiness + guardian) |
| 8 | **Automatic ga run** (v60 rule) | `python run.py --guardian` lo **code_audit + parity_audit** checks (ippudu **14/15** — 1 warn-only owner env) · readiness lo kotha check → **100/100 (28/28)** |
| 9 | **Theme package** | version **1.5.0** · readme `Stable tag: 1.5.0` + changelog · zip **37 files 629 KB** (editor.css + **author.php**) |
| 10 | **Proof** | `tests/v69_test.py` **18 checks** · `--test-all` **55/55** · jsdom **138/138** · code audit **0/0** · parity audit **0/0** · theme audit **0/0** · php-lint **29/29** · POT **21 strings** · readiness **100/100 (28/28)** |

### v68 — CODE-LEVEL BUG HUNT (bot + theme) + INSTANT INDEXING (trending)

**Mee maatalu: "chala bugs unnayi — anni aapthunnayi (top website avvakunda · posts trending
avvakunda · ads rakunda · higher revenue apedvi)".** → kotha **code audit engine**
(`tools/code_audit.py`, rules E1–E12 · W1–W7) rasi bot + theme ni line-by-line check chesamu,
dorikina bugs **anni fix** chesamu — ippudu **0 errors · 0 warnings**.

| # | Enti | Ela |
|---|---|---|
| 1 | **Audit engine** (`tools/code_audit.py`) | undefined config attr · module attr typo · bare `except:` · mutable default · **duplicate dict key** · `wp.<method>` existence · AdSense markup rules · PHP `printf` placeholder↔args · Python `%` arg count · bot push key ↔ theme option typo · `.env` drift · silent-fail · encoding · timeout |
| 2 | **Nijamaina bug #1 — crash** | `config.GEMINI_API_BASE` config lo **ledu** → deep-research path lo **AttributeError** → ippudu defined (+ `.env` lo override) |
| 3 | **Nijamaina bug #2 — silent failures** | **34 × `except Exception: pass`** (14 bot-critical) → edi fail aina teliyadu → ippudu prathi okkati **reason tho log** avutundi (`debug`/`warning`) |
| 4 | **Nijamaina bug #3 — REVENUE** | in-article AdSense unit ki `data-ad-format="in-article"` (**invalid attribute**) velledi → Google generic display ga treat chesi **in-article RPM miss** → ippudu `data-ad-format="fluid" data-ad-layout="in-article"` (spec correct) + in-feed kuda |
| 5 | **Nijamaina bug #4 — Google News** | news sitemap lo **`<lastmod>` ledu** → News sitemap reject avvachu → ippudu loc tarvata lastmod (modified time) |
| 6 | **Nijamaina bug #5 — dalit data** | `server.py` lo **duplicate dict key** (`name` rendu sarlu) → okati silent ga poyedi → clean (file v74 lo retire ayyindi) |
| 7 | **Instant indexing (trending)** | `autoblog/indexing.py` (kotha): publish ayyaka **IndexNow** (Bing/Yandex) + **Google Indexing API** (JobPosting — Google support chese official use case; SA key + Search Console owner) · `--index-key-gen` · `--index-status` · `--index-now URL` · RS256 signing `cryptography` leda `openssl` |
| 8 | **IndexNow key file** (mundu manual) | puratana setup lo key file ni cPanel lo **manual ga** pettali (lekapote submit fail) → ippudu **theme ne serve chestundi** `/<key>.key` (admin option · `--push-theme-data` tho sync) |
| 9 | **Diagnosis + docs** | audit **build gate** lo (`build_wp_theme.py`) · readiness lo **2 kotha checks (27/27)** · `run.py --doctor` · GO_LIVE **PART B step 2f** (SA setup) · MANUAL PART 27 |
| 10 | **Proof** | `tests/v68_test.py` **19 checks** (bug locks + audit detection fixtures + **10-command CLI smoke** + real RSA-2048 sign→verify) · `--test-all` **55/55** · jsdom **138/138** · code audit **0/0** · theme audit **0/0** · php-lint **28/28** · readiness **100/100 (27/27)** · zip **35 files 625 KB** |

### v67 — DEEP AUDIT (expert/BA level) + TOP-THEME HARDENING + 6/6 REVENUE SLOTS

**Mee maatalu: "inka chala mistakes unnayi · deep audit cheyyi · expert level · BA level ·
anni fix cheyyi · theme top-most ga · highest revenue safe ga".** → guess kaadu — **audit
tool** rasi, adi cheppina mistakes **anni fix** chesamu (0 errors · 0 warnings ippudu).

| # | Enti | Ela |
|---|---|---|
| 1 | **Deep audit pass 2** (`tools/theme_audit_deep.py`) | templates · security/nonces · escaping · performance · a11y · SEO/noindex · ads/policy spacing · i18n · WordPress standards · **KPI row** (ad positions · css KB · php files) — anni **build gate + guardian + readiness** lo |
| 2 | **Audit detection ability** (test tho prove) | dead module (require ledu) · `eval()` · dead admin field · screenshot 1000×800 (WRONG size) — anni pattukuntunda ani `tests/v67_test.py` prove chestundi |
| 3 | **Audit tool bug kuda fix** | puratana comment-stripper `https://...` URLs ni comments la theeseyedi → **string-aware stripper** (URLs safe, comments cut) |
| 4 | **Security hardening** (`inc/security.php` NEW) | security headers (nosniff · SAMEORIGIN · Referrer-Policy · Permissions-Policy) · XML-RPC off · `?author=N` enumeration block · attachment → parent redirect · comment link-flood guard · `DISALLOW_FILE_EDIT` · admin toggle |
| 5 | **Top-most theme files** | `comments.php` (clean, Telugu labels, spam-safe) · `sidebar.php` (widgets + **sticky ad**) · `readme.txt` (WP standard + changelog) · `languages/studentup.pot` (**auto-generated** in build) · screenshot 1200×900 |
| 6 | **6/6 ad slots** (highest revenue) | leaderboard · **in-article** · in-feed · **sidebar-sticky** · **below-content (NEW)** · anchor/sticky-bottom · spacing policy CSS · density cap · house fallback |
| 7 | **Speed + a11y** | preconnect (adsense/doubleclick/GTM/GA) · LCP preload+fetchpriority · `content-visibility` toggle (`su-cv`) · `:focus-visible` · skip-link · button types · reduced-motion support |
| 8 | **Thin pages policy** | `wp_robots` → search results + 404 **noindex** (crawl budget + AdSense quality) · search page lo form + empty state |
| 9 | **BA artifacts** (business level) | `docs/BA_REQUIREMENTS_MATRIX.md` — requirement → implementation → test → evidence + **KPI dashboard** + **risk register** + owner-pending |
| 10 | **Proof** | `--test-all` **55/55** · jsdom **138/138** · theme audit **0/0** · code audit **0/0** · php-lint **28/28** · zip **35 files 625 KB** · readiness **100/100 (27/27)** |

### v66 — THEME AUDIT (mistake hunter) + ADS REVENUE ENGINE + WRITING-TIME SEMANTIC CHECKS

**Mee maatalu: "blog rasthunnapudu inka chala check cheyali" + "highest ads ravataniki
chala miss chesthunnam" + "theme lo kuda chala mistakes unnayi"** → moodintiki
**measure-cheyyi-fix** approach (v65 pin gate + v66 audit + 54-check gate).

| # | Enti | Ela |
|---|---|---|
| 1 | **Theme mistake hunter** | `tools/theme_audit.py` — static scanner: **undefined `studentup_*` calls** (WP core allowlist) · options read ayyi admin page lo declare avvakapovadam · **dead admin field** (declared kaani eppudu read avvadu — `--verbose`) · XSS patterns (`echo $var`, `$_GET` echo) · hooks (wp_head · wp_body_open · body_class · language_attributes · wp_footer · `<main id="main">`) · breadcrumbs/author box · ads readiness (in-article · sticky · max_ads) · ads.txt · consent · **exit 1 on errors** → **build gate + guardian + readiness** |
| 2 | **Audit tho pattukunna nijamaina ads misses (anni fix)** | ① house ad **eppudu** render ayyedi (AdSense unna kuda) → AdSense-first render ② page-level gating ledu → 404/search/attachment/**policy pages** out ③ **density cap** ledu → `max_ads` (default 4) ④ **reserved height** ledu → CLS penalty → min-height ⑤ **lazy load** ledu → viewability low ⑥ **ads.txt** serve avvatledu → direct demand closed ⑦ **Consent Mode v2** ledu → EEA/UK ads block ⑧ **News sitemap** ledu → Discover/News eligibility miss ⑨ LCP preload ledu |
| 2b | **In-article ad (kotha, highest-CTR)** | `inc/ads.php` → `the_content` filter: content **3rd paragraph tarvata** okka AdSense in-article unit (lekapote house ad). Density cap + lazy + gating + idempotency marker (`su-ad-anchor-mid`) — double render ledu, thin posts (<3 paras) ki vaddu |
| 3 | **AdSense-first, house fallback** | `studentup_ad()` → client + slot unte **AdSense unit** (reserved `su-ad-reserved` + `su-ad-lazy`), lekapote house ad. Master switch `ads_enabled`, policy pages ki `ads_on_policy` (default OFF — AdSense safety) |
| 4 | **Consent Mode v2** (`inc/consent.php`) | head lo priority 1 — `ad_storage`/`ad_user_data`/`ad_personalization`/`analytics_storage` default **denied** [EEA,GB,CH] + rest of world granted + `ads_data_redaction` + `wait_for_update`; regions sanitize (A-Z0-9); CMP snippet option (priority 2) → **Google-certified CMP** tho kalisi EEA/UK revenue open |
| 5 | **ads.txt serving** (`inc/ads-txt.php`) | `/ads.txt` → `google.com, pub-XXXX, DIRECT, f08c47fec0942fa0` (AdSense client nunchi auto) + manual entries; `X-Robots-Tag: noindex` |
| 6 | **News sitemap + perf** | `/news-sitemap.xml` (48h posts · `news:language te` · images) + robots.txt line · `inc/perf.php` (LCP `preload`+`fetchpriority=high` · `decoding=async` · lazy-ads `IntersectionObserver` rootMargin 300px) |
| 7 | **Writing-time SEMANTIC + DEEPER checks** | **SEMANTIC group**: entity coverage 3+ · **ముఖ్యాంశాలు** box · **question-form headings** 2+ (PAA) · **సంబంధిత అంశాలు** cluster block · avg sentence ≤24 · current year · quick answer. **DEEPER batch**: heading hierarchy (H1 ledu/skip ledu) · markdown leftovers ledu · list ≤12 words · **table ≤5 cols (mobile)** · **job-guarantee/clickbait claims ledu** (trust+policy) · **keyword cannibalization ledu** · slug ≤60 · **meta lo CTA+number** · secondary keywords body lo · img width/height (CLS) · descriptive anchors · FAQ answers 12+ words → gate **67 checks** · fails → **LLM refine hints** (writing loop lo ne fix, publish block kaadu) |
| 8 | **rm100 fixers + FAQ bug** | `fix_takeaways` + `fix_entities` (content nunchi mattrame — invent ledu) · **nijamaina bug**: puratana FAQ guard (`<h3` 3+ unte skip) valla **FAQ section asalu rakapovadam** → ippudu questions nijam ga content lo unnaya ani check (regression test) |
| 9 | **+12 website options** | `ads_enabled` · `adsense_slot_mid` · `adsense_slot_in_feed` · `ads_txt` · `max_ads` · `lazy_ads` · `ads_on_policy` · `consent_mode` · `consent_regions` · `consent_cmp_id` · `news_sitemap` (anni WP Admin → StudentUp nunchi) · **v73:** `deadline_json` poyindi |
| 10 | **Proof** | `python run.py --test-all` → **55/55 suites** · jsdom **138/138** · `--readiness` **100/100 (27/27)** · pin gate **67/67** · code audit **0/0** · theme audit **0/0** · PHP lint **28/28** · zip **35 files (625 KB)** |

**v66 honest note:** Consent Mode v2 + ads.txt + gating + CLS + lazy = AdSense **policy-safe**
revenue foundations. Kaani **revenue numbers Google + traffic + country RPM batti** — idi
guarantee kaadu (v62 rule). Theme audit "0 errors" ante **static mistakes ledu**; ranking
ledu revenue ledu ani guarantee kaadu — avi traffic + time tho vastayi.

### v65 — PIN-TO-PIN GATE (47 checks + certificate) + GOOGLE VISIBILITY (Trends/Suggest)

**"Pin to pin check chesi rasetappudu real time ga anni perfect ga undala?"** → publish
ki mundu **47 checks** + prathi post ki **certificate file**; **trending/suggest** capture
tho topic demand.

| # | Enti | Ela |
|---|---|---|
| 1 | **Pin-to-pin gate** (`autoblog/post_gate.py`) | 47 checks · 8 groups: CONTENT · SEO · SCHEMA · MEDIA · LINKS · ADSENSE · FRESHNESS · GOOGLE READINESS. Score + certificate (`output/certificates/<date>-<slug>.md|.json`) |
| 2 | **Critical block** | title/meta/kw ledu · dev/demo text · Article schema ledu · unverified facts · past deadline · near-duplicate → **publish aaputundi** + Telegram (off: `PIN_GATE_BLOCK=0`) |
| 3 | **Real-time iterative** | `rm100.optimize()` — score → fix → score (2 passes) publish ki mundu; LLM refine tarvata malli |
| 4 | **Google Trends + Suggest** (`autoblog/trends.py`) | Trends RSS (IN) + autocomplete → TS/AP niche filter → **topic queue** + demand score. `--trends --trends-queue`; radar lo 4x/day automatic |
| 5 | **Brand/E-E-A-T graph** | Article JSON-LD lo `author.worksFor → #org`, `isPartOf → #website`, `publisher.@id` — theme Organization schema tho okate entity graph |
| 6 | **CLI proof** | `python run.py --pin-check` → 100/100 · 47/47 · 0 critical (offline) |

**v65 lo pattukunna bug:** `seo.jobposting_obj` — recruitment dict lo `salary_min`/`salary_max`
lekapote `KeyError` → publish path **crash**. Ippudu safe int conversion + regression test.

### v64 — RANK MATH 100 + THEME 100x (website options · TOC · schema · E-E-A-T · PWA)

**Mee requirement: "post ki Rank Math 100 vachela score high"** → deterministic engine
`autoblog/rm100.py` (LLM avasaram ledu) + theme 100x upgrades.

| # | Enti | Ela |
|---|---|---|
| 1 | **Rank Math 100 engine** | `rm100.apply()` — title (kw modatlo + year + power word + 40-62 ch) · meta 110-156 · slug tokens · lede lo kw · **auto TOC + anchor ids** · 2+ H2s lo kw · density 7-15 · facts table · FAQ · external+internal links · Telugu connectives 30% · paragraph split |
| 2 | **Proof command** | `python run.py --rm100` → imperfect draft **33/100 → 100/100** (21 on-page tests okkokaటి ✅) |
| 3 | **Gate + score** | pipeline: rm100 → LLM refine (`RM_REFINE_ROUNDS=2`, `RM_TARGET=100`) → rm100 malli → final score **WP meta `rank_math_seo_score`** + Telegram lo chupistundi |
| 4 | **Website options page** | WP Admin → **StudentUp** menu (tabs: Ads · Socials · Content · Advanced) + REST `/wp-json/studentup/v1/options` (bot sync) |
| 5 | **Theme 100x** | auto **TOC** · **JSON-LD schema** (Organization/WebSite/SearchAction/Breadcrumb) · **E-E-A-T author box** + last-updated · **PWA** manifest + theme-color + preconnect · sticky bottom ad · copy-link · reading progress |
| 6 | **PHP syntax gate** | `tools/php_lint.js` (**node php-parser · real PHP 8**) — build_wp_theme.py hard gate. Ee gate pettaka **site break chese 10 bugs** pattukunnamu (template files lo `?>` miss → white screen!) |

**v64 lo pattukunna nijamaina bugs (fix chesamu):**
1. 10 template files (single/front-page/header/footer/index/archive/search/404/page/searchform)
   lo ABSPATH guard tarvata `?>` ledu → **PHP fatal parse error → site white screen**.
2. TOC ids rendu sarlu generate ayyi `-2` suffix vachedi → **TOC links pani cheyyavu** (jump ledu).
3. Paragraph split long paragraphs ni chunks ga marchi **text ni thosesthundi** (content loss).
Ippudu moodintiki tests unnayi (white-screen regex guard · TOC link⊆ids · words before≥after).

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

**Ee command ee repo lo prastuta: 100/100 · 27/27 system checks · 10 owner-pending.**
Artifacts: `logs/readiness.json` + `output/readiness-<date>.md` (markdown report).

| Section | Enti verify avutundi (verifiable number) |
|---|---|
| CONTENT ENGINE | blueprint score 100/100 (TOP POST 🏆) · gates QA 80+ / originality 72%+ / deep-gate ON · 17 pillars · 221 entities · 12,344 kws · 180 sources · radar 4x/day · 59 districts |
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
Options: `studentup_breaking_json` · `studentup_proof_json` ·
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
| keyword_pillar_lock | 17 pillars · 221 entities · 12,344 kws · 180 sources | counts sync |
| menu_wiring | TS/AP/hall/results/walkin/software links + 8 used tiles | nav/mpanel |
| storage | disk free · state.db · output size | `tools/prune_media.py --apply` |
| env_readiness ⚠️ | Gemini/WP/Telegram creds (owner pani) | `.env` (GO_LIVE PART A) |

Severity: ❌ = system break · ⚠️ = owner-pending (creds) · status → `logs/guardian.json` (14-run history).
Guardian read-only — fix chestundi kaadu, cheptundi; fixes tests + builder nunchi.

### v59 — First Look: బ్రేకింగ్ న్యూస్ + "విద్యార్థులు ఎక్కువగా వెతికేవి" + పర్ఫెక్ట్ మెనూ

Student site open cheyagane modati 3 sekundullo kanipinche order:

| Position | Enti | Detail |
|---|---|---|
| 1 | 🔴 **బ్రేకింగ్ టికర్** | radar feed (Google News తెలుగు + 180 official sources) — verified items matrame; feed khali aithe ticker **hide** (fake news ledu) |
| 2 | **విద్యార్థులు ఎక్కువగా వెతికేవి** | 8 tiles: టీఎస్ · ఏపీ ప్రభుత్వ ఉద్యోగాలు · హాల్ టికెట్లు · ఫలితాలు · వాక్-ఇన్ · సాఫ్ట్‌వేర్ · ప్రైవేట్ · ప్రస్తుతాంశాలు — prathi tile ki **live count** + one-tap filter |
| 3 | ప్రకటన (leaderboard) | highest-visibility slot — content ki bhaadha lekunda |
| 4 | Hero + ముఖ్య గడువు countdown | trust tiles (45/45 · 11/11 · 138/138 · 12,344 · 17 cats · 180 sources) |
| 5 | బ్రేకింగ్ న్యూస్ section + తాజా అవకాశాలు grid | grid lo **TS/AP ప్రభుత్వ ఉద్యోగాలు modati cards** |

Menu (desktop + mobile same order): హోమ్ · ఉద్యోగాలు▾ (టీఎస్ · ఏపీ · కేంద్ర · ప్రైవేట్ ·
వాక్-ఇన్ · సాఫ్ట్‌వేర్ · అవుట్‌సోర్సింగ్ · పార్ట్-టైమ్ · విదేశీ) · **హాల్ టికెట్లు** ·
**ఫలితాలు** · **బ్రేకింగ్ న్యూస్** (live dot) · స్కాలర్‌షిప్‌లు · ప్రస్తుతాంశాలు · పరీక్షలు▾ · మరికొన్ని▾

Bot side: `autoblog/breaking.py` (feed build + tag classifier + honest empty note),
radar run lo auto hook, `MOST_USED` order okate source (bot + site + tests sync).
Evidence: tests/v59_test.py 12 checks · `run.py --test-all` 55/55 · jsdom 138/138.

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
python run.py --keyword-universe                     # 12,344 keywords + CSV
python run.py --top-post "TSPSC Group 2 2026 notification"
python run.py --top-post-plan --top-post-days 90     # domination calendar
python run.py --score-post file.html --score-keyword "ssc cgl 2026"
python run.py --top-post "NSP Scholarship last date" --publish-top-post
```

```bash
# v74 APPROVALS (cron mode — shared hosting friendly)
python run.py --approval-poll               # okka poll pass (cron: */5 * * * *)
python -m autoblog.approval_bot             # VPS daemon (24/7 long-polling)
```

```bash
# v41 SITE AUDIT + SAFE FIX
python run.py --site-audit                  # read-only audit (report files)
python run.py --site-audit-fix              # audit + fixes (dry-run default)
python run.py --site-audit-fix --site-audit-apply [--site-audit-trash]
python run.py --site-audit --site-audit-snapshot demo    # offline (network ledu)
python run.py --test-all                    # ANNI suites (30/30) okate command tho
python run.py --deploy-check                # deploy readiness (imports + artifacts + cron hint)
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
├── deploy/                 # bot timer · watchdog · Caddyfile (static) · Dockerfile · compose · backup.sh · install-vps.sh
├── autoblog/deploy_check.py # deploy readiness (imports + artifacts + cron hint)
├── autoblog/site_audit.py  # v41 deep audit + safe autofix + live publish gate
├── tools/
│   ├── revenue_estimate.py # v53 ad revenue calculator (--views 10k / 1l / --json)
│   └── ad_network_plan.py  # v56 network eligibility + uplift (--views 50k --tier1 0.3)
└── tests/                  # end-to-end tests (fake WP/Telegram/source servers)
```
