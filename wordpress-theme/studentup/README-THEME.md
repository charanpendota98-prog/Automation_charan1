# StudentUp WordPress Theme (v61) — "real website ఇలా ఉంటుంది"

**Idi enti:** `preview/index.html` lo chusina design (బ్రేకింగ్ టికర్ · "విద్యార్థులు ఎక్కువగా
వెతికేవి" · ఉద్యోగం కార్డులు · ad slots · dark mode) — **ide WordPress theme ga**.
WordPress lo install chesi activate chesthe, mee asalu site **ade design** tho, kaani
**dynamic** ga untundi: bot post rasthe automatic ga aa card, aa category count, aa
breaking item anni site lo kanipistayi.

## Install (5 నిమిషాలు)

1. `python tools/build_wp_theme.py` → `wordpress-theme/studentup-theme.zip` create avutundi
2. WP Admin → **Appearance → Themes → Add New → Upload Theme** → zip upload → **Activate**
3. **Appearance → Menus** → 'primary' (హెడర్) + 'mobile' + 'footer' menus create chesi assign cheyandi
   (assign cheyyakapote theme default Telugu menu — హోమ్ · టీఎస్ · ఏపీ · … · బ్రేకింగ్ — chupistundi)
4. **Settings → Reading** → "Your homepage displays" = **Your latest posts** leda static page (rendu pani chestayi —
   `front-page.php` unnappudu design home automatic)
5. Rank Math install (SEO) · AdSense approve ayyaka:

```
WP Admin → (bot nunchi) → python run.py --push-theme-data
```

## Theme options (bot automatic ga pettestundi — manual kuda cheyochu)

| Option | Enti | Example |
|---|---|---|
| `studentup_breaking_json` | బ్రేకింగ్ ఐటమ్స్ (radar feed) | `{"items":[{"title":"…","link":"…","tag":"results","time":"…"}]}` |
| `studentup_house_ads` | house/sponsor ads (day rotation) | `[{"title":"…","desc":"…","link":"https://…","cta":"…"}]` |
| `studentup_adsense_client` | AdSense client id | `ca-pub-1234567890123456` |

**Bot push (REST):** `POST /wp-json/studentup/v1/theme-data` — Application Password tho auth
(edit_posts). Idi lekapote: WP root lo `/data/breaking.json` file pettandi (theme 10 నిమిషాల
transient cache tho chadivi chupistundi).

## Em unnayi (files)

```
style.css            design tokens + anni components (Telugu fonts, dark mode, responsive)
front-page.php       home order: used-strip → ad → slim hero → (breaking OFF) → grid+chips
header.php           logo/menu/actions/mobile panel + టికర్
footer.php           footer + కుడి వైపు నిలువుగా socials
single.php           article + ads + share + related + trust note
index/archive/search/page/404/searchform.php
inc/breaking.php     feed (option → transient file → honest empty) + REST push
inc/ads.php          AdSense unit + house ads (SPONSORED label, rel=sponsored)
inc/template.php     cards, breadcrumbs (Rank Math compat), menu fallback
assets/js/studentup.js  dark mode, mobile panel, chips filter, qualification filter, live search
assets/js/studentup-saved.js  privacy-safe saved posts, deadlines and recently read items
assets/js/studentup-tools.js  compare drawer, calendar reminder export, print/PDF action
inc/student-tools.php        no-login student utilities; optional logged-in saved sync only
inc/opportunities.php         active board, expiry-safe sections, official links and student actions
theme.json           block editor colors/Typography (navy/blue/orange)
```

## Nijam (honest)

- Ivi **Preview design = production design**. Chinnavi matrame marutayi (WP nav_menu hook, real URLs).
- **Speed:** no jQuery, 1 CSS + 1 JS, lazy images — GeneratePress kante light (custom theme,
  add-ons ledu).
- **AdSense:** SPONSORED labels + rel=sponsored + ad units ki minimum height (CLS safe).
  Auto Ads ki `functions.php` lo em ledu — AdSense ki aa pani varasam (plugin leda site code).
- **Rank Math** unte breadcrumbs + meta aa plugin nunchi vasthayi (theme detect chestundi).
## v72 (theme 1.7.0) — qualification filter · search · install

| Feature | Where | Automatic? |
|---|---|---|
| విద్యార్హత ఫిల్టర్ (10th · 10+2 · ITI · Diploma · Degree · PG · B.Tech) | `inc/qual-filter.php` — home/archive `?qual=degree` | ✅ post save lo title/content nunchi tag; bot `studentup_qual` meta pampistundi; purana posts admin/CLI backfill |
| Menu pakkana search | `header.php` + `assets/js/studentup.js` | 🔍 button + `/` shortcut |
| యాప్గా ఇన్స్టాల్ (PWA) | `inc/pwa.php` + `assets/js/studentup-pwa.js` | service worker (`?studentup_sw=1`) + install prompt; Android/iPhone rendu |
| Closing-soon badge | `studentup_last_date` meta → "⏳ closing in N days" | ✅ bot `recruitment.apply_end` nunchi |
| Active opportunity finder | Browser-only title/category/deadline filters | ✅ no tracking or API request |
| Saved opportunities | localStorage for guests; same-site REST/user-meta sync for logged-in readers | ✅ opt-in; no email/ad identity collected |
| Compare + reminders | deadline-aware compare table and downloadable `.ics` calendar event | ✅ unknown dates never create reminders |
| Source trust/update metadata | `studentup_source_url`, qualification, updated date | ✅ same-source update + visible board context |
| Breaking section | `inc/breaking.php` | ⚙️ default **OFF** (`StudentUp → కంటెంట్ → breaking_enabled`) |

CLI: `wp studentup-qual-backfill --limit=500` (purana posts ki tags).

## v173–v178 (themes 1.9.24–1.9.29) — REAL-INSTALL AUDIT ERA

Anni changes **real WordPress 7.1.2 + SQLite install meeda verify chesi** ship chesamu
(fresh install → seed posts → curl audit → fix → re-verify cycle).

| Ver | Theme | Headline fixes (live-proof) |
|---|---|---|
| v173 | 1.9.24 | Hot-rail purathana meta keys (`su_last_date`) → real keys; days-left PHP warning; `paginate_links()` null fatal; Saved page auto-create; full emoji→SVG purge |
| v174 | 1.9.25 | Qualification word-boundary detection; board pills + pretty labels; SQLite/MySQL portable meta compares |
| v175 | 1.9.26 | Context-aware CTAs (Hall Ticket / Result / Apply); JobPosting schema gates (non-job cats, expired, signal checks); `#su-details` anchor; pretty quals; comma-tolerant vacancies; closing-week widget wrong meta key; `type=>DATE` meta_query SQLite break (5 spots) |
| v176 | 1.9.27 | Home `/page/N/` duplicate content + missing pagination (critical); news-sitemap HTTP 404 + ISO dates; JobPosting gate AND logic; health widget empty-meta false "Expired"; hot-rail signal gate + software boards; heading hierarchy; Compare page auto-create + version-stamped upgrade re-run; noindex (search + ?qual); og:image guarantee chain + shipped brand card |
| v177 | 1.9.28 | og/twitter cards for home + archives; twitter:card duplicate; archive canonicals; favicon fallback (svg + 32 + apple-touch); llms.txt tools + expired filter |
| v178 | 1.9.29 | **Alias-merged category archives** — menu links (`/category/ts-jobs/` etc.) empty ayye import/bot-slug sites lo group merge (0 → 10 cards); deterministic primary-term identity (H1/title/canonical); PWA manifest icons (install prompt fix); empty-archive noindex |
| v179 | 1.9.30 | Attachment pages → 301 parent post; RSS feed media:content images + official source + read-more CTA; docs |

**Invariant suite:** 124/124 python · jsdom 177 · workspace 22 · saved 53 · PHP lint 85/85 · theme audit 0/0 —
prathi release tarvata anni run chesi green ga ne commit.

## v172 (theme 1.9.23) — COMMAND CENTER: My Workspace (flagship)

**"1000x advanced" flagship feature** — student ki kavalsina ANNI okka page lo:

| # | Module | Em chestundi |
|---|---|---|
| 1 | **Profile** | Qualification · age · state okasari set cheyyandi (browser lo matrame — account ledu) |
| 2 | **Jobs matched for you** | Job meta (qual · age limits · state · deadline) ni profile tho instant match — eligible jobs deadline urgent-first order lo |
| 3 | **Application pipeline** | Saved → Applied → Interview → Result counts + list (saved panel apply-tracker tho same store — ekkuva sync lo untayi) |
| 4 | **Deadline radar** | Save chesina jobs lo closing-in-3-days RED · this-week AMBER · closing-soon BLUE |
| + | **Quick tools** | Age calc · fee calc · score calc · syllabus tracker · salary calc · jobs board |

**Kuda advanced (engineering):**
- Data server-side embedded (`studentup_smart_dataset` JSON attr) — REST wait ledu, **offline kuda pani chestundi**
- Assets workspace page lo matrame load (site-speed impact zero), JS deferred
- Critical CSS layer lo `.su-ws` prefix (workspace page first-paint instant)
- Admin toggle (StudentUp Options), firstrun automatic page creation (`My Workspace`)
- Entry points: mobile menu · ⌘K command palette · hero action chip

Setup: Theme activate chesina tarvata **StudentUp → First-run setup** run cheyyandi
(My Workspace page automatic create avutundi), leda epage lo `[studentup_workspace]`
shortcode pettandi. URL: `/workspace/`.

## v171 (theme 1.9.22) — PRO MODE: advanced · professional · very fast

Mee 3 requirements — "very useful, not silly", "advanced", "very fast":

1. **PROFESSIONAL (silly emojis pothayi)** — anni UI emojis (menu, search, dark,
   saved, home, jobs, scholar, alerts, calculators…) clean **inline SVG icons** ga
   replace chesamu (`inc/icons.php`). Prathi device lo same sharp professional
   look, dark mode automatic, zero extra HTTP requests. Article meta
   (date · category · eligibility) icons kuda SVG.
2. **VERY FAST (first paint)** — **Critical CSS layer**: above-fold styles (30 KB,
   `tools/build_critical_css.py` auto-build) `<head>` lo inline; full 154 KB CSS
   `media="print" + onload` swap tho **async** (+ `<noscript>` fallback). First
   paint ki external CSS wait ZERO — phone lo site open avvadam chala fast.
   File lekapothe theme automatic ga purathana blocking path ki velthundi (safe).
3. **ADVANCED + USEFUL — Application Status Tracker**: student job save chesina
   tarvata "apply chesa? interview ayyinda? result?" track cheyochu. Prathi saved
   job ki status chip — tap chesthe: **Saved → Applied → Interview → Result**.
   Saved panel + /saved/ page rendu chotla. localStorage matrame (privacy-safe:
   account ledu, server ki emi pampaledu).

Tech: `inc/icons.php` (SVG system) · `inc/critical-css.php` (inline+async) ·
`tools/build_critical_css.py` (build step, `build_wp_theme.py` automatic run) ·
`studentup-saved.js` (tracker). Re-upload: `python tools/build_wp_theme.py` →
zip → WP Admin → Appearance → Themes → Add New → Upload.

## v170 (theme 1.9.21) — PHONE MODE: fast · no side-scroll · no zoom

Mee phone lo 3 problems fix ayyayi:

1. **"Pakkaku velthundi" (side scroll) OFF** — `overflow-x:clip` hard guard (sticky header safe ga
   pani chestu untundi) + post content lo pedda URLs/tables leak ayite automatic wrap.
2. **"Zoom zoom-out avthundi" OFF** — pinch zoom (viewport meta + iOS gesture guard JS) +
   double-tap zoom (`touch-action:manipulation`) + iOS input-focus auto-zoom (16px inputs)
   — moortham ga block.
3. **"Phone lo slow" FIX** — hero blur orbs · quiz spin ring · pulse/wave infinite animations
   phone size lo OFF (GPU cool); header/bottom-nav/social-rail/apply-bar meeda costly
   `backdrop-filter` blur → solid colour; JS `defer` tho parallel download; reading-progress
   bar rAF-throttled (scroll jank taggindi). Desktop design deggara ekkuva
   marindhi cheyyaledu — anni changes `@media(max-width:980px)` lo unayi.

Re-upload: `python tools/build_wp_theme.py` → zip → WP Admin → Appearance → Themes → Add New → Upload.

## v168 (theme 1.9.20) — world-class interactive student suite

| Feature | Where | Automatic? |
|---|---|---|
| వయోపరిమితి కాలిక్యులేటర్ (Age & Eligibility) | `inc/agecalc.php` + `[studentup_age_calc]` | ✅ DOB & cutoff tho TSPSC/APPSC/Central reservation relaxation |
| దరఖాస్తు ఫీజు కాలిక్యులేటర్ (Fee Calculator) | `inc/feecalc.php` + `[studentup_fee_calc]` | ✅ SC/ST/PwD/Women fee exemptions breakdown |
| నెగెటివ్ మార్కింగ్ స్కోర్ కాలిక్యులేటర్ (Score Calc) | `inc/scorecalc.php` + `[studentup_score_calc]` | ✅ Net score + Accuracy rate % calculation |
| హాల్ టికెట్ పోర్టల్ హెల్పర్ (Admit Card Helper) | `inc/admitcard.php` + `[studentup_admit_card]` | ✅ Direct board hall ticket portals & login checklist |
| ఫ్రెషర్ బయోడేటా మేకర్ (Resume Builder) | `inc/resumemaker.php` + `[studentup_resume_maker]` | ✅ 1-click clean PDF bio-data generator |
| పరీక్ష సిలబస్ ట్రాకర్ (Syllabus Progress Tracker) | `inc/syllabustracker.php` + `[studentup_syllabus_tracker]` | ✅ Interactive study checklist with localStorage progress % |
| వాట్సాప్ 9:16 స్టేటస్ ఇమేజ్ జెనరేటర్ (Status Card) | `inc/statuscard.php` | ✅ 1-click 1080x1920 viral status graphic download |
| తెలుగు టెక్స్ట్-టు-స్పీచ్ రీడర్ (Audio Reader) | `inc/audioreader.php` | ✅ Native Web Speech API Telugu voice synthesizer |
| గూగుల్ FAQPage Rich Snippet Schema | `inc/faqschema.php` | ✅ SERP expandable FAQ rich snippet structured data |
| 1-Minute Key Highlights Box | `inc/quicksummary.php` | ✅ Axios/Verge style TL;DR takeaways card |
| రీడర్ టూల్‌బార్ (Font Resizer A-/A+) | `inc/readerbar.php` | ✅ Accessibility text scaling + reading time |
| కమ్యూనిటీ పల్స్ కార్డ్ (50k+ Community) | `inc/readerbar.php` | ✅ 1-click WhatsApp/Telegram channel conversion |

