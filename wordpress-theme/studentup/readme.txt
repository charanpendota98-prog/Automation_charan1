=== StudentUp ===
Contributors: studentup
Requires at least: 6.0
Tested up to: 6.7
Stable tag: 1.9.33
Requires PHP: 7.4
Version: 1.9.26
License: GNU General Public License v2 or later
License URI: https://www.gnu.org/licenses/gpl-2.0.html
Tags: news, education, blog, custom-logo, custom-menu, featured-images, translation-ready, right-sidebar, block-styles, wide-blocks
Text Domain: studentup

== Description ==
StudentUp — Telangana & Andhra Pradesh students ki pure-Telugu education + jobs website theme.
Auto-blogging bot (Gemini) tho kalisi pani cheyyadam ki design chesindi.

Features (top-theme level):

* Fast: system fonts, 21 KB CSS, lazy ads, LCP preload, content-visibility
* SEO: Rank Math REST bridge, JSON-LD graph (Organization · WebSite · Article ·
  BreadcrumbList · FAQPage · JobPosting · ItemList), breadcrumbs, noindex thin pages
* Revenue: AdSense-first units (leaderboard · in-article · in-feed · sidebar +
  sticky · below-content · anchor/sticky-bottom), house-ad fallback, density cap,
  CLS-safe reserved height, viewability lazy load, ads.txt serving, Consent Mode v2
* Reader UX: dark mode, reading progress, TOC, copy-link, share bar, most-read tiles
  (TS/AP), breaking section (off by default), related posts, author box (E-E-A-T)
* Admin: StudentUp settings page (Ads · Socials · Content · Advanced) + REST options
* Security: security headers, XML-RPC off, author enumeration block, emoji cleanup,
  attachment redirect, comment link-flood guard, DISALLOW_FILE_EDIT

== Installation ==

1. WP Admin → Appearance → Themes → Add New → Upload Theme → `studentup-theme.zip`
2. Activate.
3. Settings → Permalinks → Save (once).
4. WP Admin → StudentUp → Ads: AdSense Client ID + slot IDs pettandi.
5. Menus: Appearance → Menus → `primary` location ki mee category list.

== Frequently Asked Questions ==

= Ads render avvatledu? =
StudentUp → Ads → "Ads ON (site)" check cheyandi + AdSense Client ID + slot IDs pettandi.
Without a client/slot, house ads (filled by the bot) render.

= Rank Math fields land avvatledu? =
The theme ships a REST bridge (`inc/seo-bridge.php`). Use an account with `manage_options`
user tho App Password ivvandi (Administrator role).

== Changelog ==

= 1.9.31 =

* SPEED (live-install measurement): home HTML lo 196 inline SVG icons = 65 KB duplicate paths (calendar 20×, wallet 17×, bookmark 15×…) — phone lo DOM parse slow + bytes waste. Ippudu **SVG sprite system**: okka hidden <symbol> sheet (wp_body_open lo, admin ki admin_footer fallback) + prathi icon <use href="#su-i-X"> reference. Home HTML ~30 KB lighter + DOM text nodes significant ga takkuva. Anni 48 icons same sharp look (fill currentColor — dark mode automatic).
* NEW VERIFICATION LAYER: live site pages ni real scripts tho jsdom lo run chesi JS runtime errors check (10 pages: home, paged, ?qual, category, single ×2, workspace, saved, compare, latest-jobs) — **ZERO JS errors**. Ippudu prathi release lo idi kuda standard.
* FIX: PWA manifest "Daily Quiz" shortcut EMPTY daily-quiz category ki pontundi (posts lekapote dead-end — live proof cards=0). Ippudu home #daily-quiz section (real quiz UI, category lekunda kuda render) ki point avutundi.

= 1.9.30 =

* ADVANCED (RSS): feed items nagna text ga levu — ippudu (a) media:content image prathi item ki (featured image lekapothe brand og-default.png — RSS readers lo visual card), (b) item content lo official source link (E-E-A-T), (c) "Read the full update" site CTA — subscribers site ki back vastaru.
* TOOLING (build-breaking guard): theme audit lo "redeclare fatal" check add — okka studentup_* function rendu files lo define ayyite PHP "Cannot redeclare" FATAL (site motham 500). Live incident nunchi nerpa: attachment-redirect function duplicate ayyaka syntax-lint + audit anni PASS ayyevi, kani site prathi page 500. Ippudu build ae fail avutundi (guard test: duplicate inject → errors 1 ⛔, clean → ✅).
* VERIFY: attachment → parent post 301 redirect (security.php lo v178 nunchi unna feature) redirect-following audit false-alarm valla "missing" anukunna — direct 301 check tho confirm (status 301 + Location header).
* DOCS: README-THEME.md lo v173–v178 full audit-era history table add (em fix ayyindo okka chotu).

= 1.9.29 =

* FIX (CRITICAL, live-install proof): category alias group merge — menu pradhana links (/category/ts-jobs/ · /category/central-jobs/ · /category/ap-jobs/ · /category/hall-ticket/) alias slug family lo posts unna sites lo EMPTY pages chupistunnayi (aa posts /category/ts-govt-jobs/ lanti sibling slugs lo unnayi — import leda alternate-slug bot valla). Ippudu archive query alias group ANNI terms cover chestundi: /category/ts-jobs/ → ts-jobs + ts-govt-jobs + telangana-govt-jobs + … Menu link eppadu empty kadu (live proof: 0 cards → 10 cards).
* FIX (PWA): manifest lo Site Icon set cheyyakapote icons LEdu (icons: [] — Chrome "Install app" prompt eppudu raadu) + description empty ayite nagna text. Ippudu: theme brand icons fallback (pwa-192.png + pwa-512.png + maskable) + brand description. Site Icon set cheste 192+512+maskable rendu combine.
* SEO: truly-empty term archives (alias merge tarvata kuda posts levu) ki noindex,follow — thin content index avvadam vaddu.

= 1.9.28 =

* FIX (live-install proof): HOME page WhatsApp/Telegram share card complete ga missing ayyindi — og:title · og:description · og:url · og:type · og:image · twitter:card anni levu (fallback SEO singular posts ki matrame). Ippudu home + category/date/author archives ki full card + brand image (og-default.png). "Just another WordPress site" default tagline unte brand fallback text.
* FIX: no-thumbnail posts lo twitter:card tag 2 sarlu print ayyedi (seo-bridge + ogimage rendu). Ippudu okate — twitter:image matrame ogimage nunchi.
* FIX: canonical tags home /page/N/ + category / date / author archives ki levu (WP core singular ki matrame). Ippudu self-canonical, pagination-aware (archive page 2 ki page-2 URL ye) — duplicate-content signals clean.
* NEW: favicon fallback — Customizer lo Site Icon set cheyyakapoina browser tab lo theme brand icon (gradient-S): favicon.svg + favicon-32.png + apple-touch-icon.png (iOS home screen). Site Icon set cheste owner icon ye vaadutundi (duplicate vaddu).
* FIX: llms.txt (AI assistants kosam) — (a) Student tools section add (latest-jobs board, compare, workspace, saved); (b) expired job posts "Recent public articles" lo recommend avvadam vaddu — board policy laaga hidden (expired filter).

= 1.9.27 =

* FIX (CRITICAL, live-install proof): home /page/2/, /page/3/ … anni SAME 12 posts chupistunevi (paged front page kuda front-page.php vaadutundi kani query lo 'paged' ledu → duplicate content penalty) + "Older updates" link eppudu render cheyyaledu — users ki 12 posts tarvata browse cheyadam impossible. Ippudu: real paged grid + numbered pagination (← Newer / 1 2 3 / Older →) + page 2+ lo lean archive (widgets page 1 lo matrame — duplicate widget content poochindi). Mobile-first pagination CSS kuda add (adedo category pages lo unstyled links ga unna).
* FIX: admin health widget — REST bot empty-string studentup_last_date save chesina posts false ga "Expired" count ayyevi ('' < today string compare TRUE). AND-relation non-empty guard.
* FIX: news-sitemap.xml HTTP 404 status lo serve ayyedi (XML body ostu untundi — Search Console reject). status_header(200) + ISO 8601 dates (lastmod / publication_date "2026-10-01 07:37:07" → "2026-10-01T07:37:07+00:00").
* FIX: JobPosting gate v175 lo OR ayipoyindi — apply_url LENI post (vac/salary unte) + numbers LENI placeholder post ki kuda schema vastevi. Ippudu: apply_url AND (numeric vacancies leda salary) — REAL jobs matrame Google Jobs lo.
* ADVANCED: JobPosting lo url (post permalink) + baseSalary add — "₹65,000 – ₹2,10,000" → INR 65000–210000/MONTH, "Rs. 3.6 LPA" → INR 360000/YEAR (lakh/LPA parser). Google Jobs salary facet + rich results.
* FIX: "Top 10 hot jobs today" rail — (a) job signal leni posts (last_date/salary/vacancies/apply_url anni leka poyina) #1 rank ayyevi; (b) software-jobs/walkin-jobs/internships boards eppudu rail lo raaledu. Signal gate + anni job boards cover.
* FIX: heading hierarchy (a11y + SEO) — h1 → h3 jump (Key Highlights box), h2 → h4 jump (mock-tests promo + footer widgets). Sequential ga correct chesamu + CSS updated.
* FIX: "Compare Jobs" tools link /#compare ki pontundi — aa anchor ekkada ledu (dead end). Ippudu firstrun /compare/ page auto-create chestundi ([studentup_compare] shortcode tho) + theme update mundu version stamp check chesi kotha pages purathana sites lo kuda automatic ga create avtayi (idempotent).
* SEO: search results + ?qual= filter views ki noindex,follow (internal search results + duplicate content protection — Google guidelines). Users ki pages normal ga work avutayi.
* ADVANCED: og:image GUARANTEE — chain: post thumbnail → generated card image (GD) → static brand card assets/og-default.png (1200×630, 60 KB, theme lo ship). GD/folder em lekapoina WhatsApp/Telegram/Google shares chala beautiful image tho vastayi (v175 lo nagna links!). og:image:alt + twitter:image kuda.

= 1.9.26 =
* v175 CONTEXT-AWARE CTAs + SCHEMA GATES — real WP audit nunchi:
* FIX: JobPosting JSON-LD ippudu REAL job posts ki matrame (hall-ticket/result/success-stories/current-affairs/admissions/quiz/tips categories skip + apply_url/vacancies/salary job-signal kavali + expired postings ki schema ledu — Google Jobs spam/quality guideline). Puratham hall ticket post (qual + last_date unna) ki kuda JobPosting attach ayedi.
* FIX: sticky apply bar CTA context-aware — hall-ticket post lo "Download Hall Ticket", result post lo "View Result", job post lo "Apply online" (puratham anni daanni "Apply online" ye).
* FIX: apply bar "Full details" ghost button anchor (#su-details) ekkada ledu — click emi cheyaledu. Ippudu article content id tho scroll chestundi.
* FIX: apply bar lo raw "degree,pg" → "Degree · PG"; FAQ answers lo kuda human labels + "05 Oct 2026" date format.
* NEW: FAQ section context-aware — hall ticket posts ki download FAQs (last date to download, credentials, official portal warning), result posts ki result FAQs (check kaka mundu em cheyali, link active till, next steps), job posts ki recruitment FAQs.
* FIX: totalJobOpenings "12,000" comma values kuda numeric ga parse.
* FIX (SQLite/Playground): meta_query 'type' => 'DATE' valla SQLite-backed sites lo CAST('Y-m-d' AS DATE) numeric ga maari — admin health widget anni posts "Expired" la chupinchindi (19/19) mariyu "Expiring" 0. Zero-padded ISO string compare (type ledu) MySQL + SQLite rendula portable. 5 queries fix (health ×2 · qual filter ×2 · closing week).
* FIX: "Closing this week" home widget (su-radar) puratham wrong meta key (su_last_date — eppudu save cheyyaledu) valla eppudu render cheyyaledu. Ippudu 7-days closing jobs deadline order lo vastayi (REAL install lo first render proof).

= 1.9.25 =
* v174 OPPORTUNITY BOARD RICHNESS — board cards ippudu salary + vacancies pills chupistayi (bot studentup_salary/studentup_vacancies meta nunchi) + qualification human labels ("degree,pg" → "Degree · PG").
* v174: keyfacts · quicksummary · jobs table · workspace why-text — anni raw meta keys badulu human-readable labels + "05 Oct 2026" date format (raw ISO kaadu).
* v174: hot rail date pill human format (d M) + closed post skip ayyaka rank numbers lo gap ledu.
* v174: miss ayyina 2300-23FF emoji range (⏳ ⏰ ⏹ ⏸ ▶) kuda SVG ayipoyindi — audio reader stop/pause buttons, qualification badges, expired notice, closing filter. Page UI lo emoji zero (canvas-generated share image thappa — adhi intentional design).
* v174 REAL FIX: qualification auto-tag lo substring match ("iti" → "writing", "pg" → "jpg" la false positives — Hello world! post ki "iti" tag attach ayindi real install lo). Ippudu ASCII keywords ki word-boundary match; Telugu ki fuzzy-safe strpos. `_topic_*` synonyms qual output lo leak ayye bug kuda fix.
* v174: workspace dataset jobs-only — studentup_* meta leni posts (default "Hello world!") matching lo participate avvavu.

= 1.9.24 =
* v173 REAL-INSTALL FIXES — WordPress 7.1.2 + PHP 8.3 real install mida proof chesina bugs:
* FIX: "Top hot jobs" rail wrong meta keys (su_last_date/su_salary → studentup_*) valla salary + deadline pills eppudu kanipinchaledu + PHP "Undefined $left" warning — ippudu real studentup_* meta tho salary pill, days-left pill, closed posts exclusion anni work.
* FIX: paginate_links() NULL → wp_kses_post(null) PHP 8.1+ FATAL (category/search/index/author single-page lo) — `?? ''` null-safe fix.
* FIX: firstrun ippudu /saved/ page kuda automatic create chestundi ([studentup_saved] tho) — saved panel link fresh install lo eppudu break avvadu.
* EMOJI PURGE: UI lo prathi emoji → professional inline SVG icons (23 kotha icon paths; keyfacts, hot rail, category menu/usedgrid/popular searches, footer tools, opportunities board, tools widgets, ⌘K palette, admin columns/health/notices) — cross-platform consistent look, font dependency ledu.
* Workspace JS runtime prove (jsdom 22/22): profile → qualification/age/state filtering, urgent-first deadlines, Closed chip, pipeline tiles, deadline radar colour classes.

= 1.9.23 =
* v172 COMMAND CENTER — "My Workspace" page ([studentup_workspace]): profile (qualification · age · state) set chesthe eligible jobs instant, application pipeline (Saved/Applied/Interview/Result tiles), deadline radar (urgent 3/7/14 days first) and quick tools — anni okka page lo. No account, browser-only, offline-capable.
* v172: firstrun automatic ga My Workspace page create chestundi; mobile menu + ⌘K palette + hero lo entry points.
* v172: workspace data server-side embedded (REST wait ledu) + JS deferred — speed impact zero.

= 1.9.22 =
* v171 PRO MODE — professional SVG icon system: anni UI emojis (☰ 🔍 ☾ 🔖 🏠 💼 🎓 🔔) clean inline SVG ga replace chesamu — prathi device lo same sharp look, zero extra requests.
* v171 VERY FAST — Critical CSS: above-fold styles (30 KB) head lo inline + full 154 KB CSS async (media=print + onload swap + noscript fallback) → first paint ki external CSS wait ledu.
* v171 ADVANCED — Application Status Tracker: prathi saved job ki status chip (Saved → Applied → Interview → Result, tap to cycle). localStorage privacy-safe.
* v171: article meta icons (date/category/eligibility) SVG; professional tone i18n cleanup.
* v170 PHONE MODE: pinch/double-tap zoom OFF, side-scroll hard guard, mobile speed (blur/infinite-anim OFF), JS defer, iOS input-focus zoom fix.

= 1.9.21 =
* v170: pinch/double-tap zoom fully OFF (viewport meta + iOS gesture guard + touch-action) — accidental zoom fix.
* v170: horizontal side-scroll hard guard (overflow-x clip + long-word wrap).
* v170: mobile speed — hero blur orbs, quiz spin ring, pulse/wave infinite animations OFF on phones; backdrop-filter blur replaced with solid colour on header/bottom-nav/social rail/apply bar.
* v170: iOS input auto-zoom fix (16px inputs), tap-highlight cleanup, JS deferred, reading-progress bar rAF-throttled.

= 1.9.20 =
* v134: Second in-article ad slot for long posts, anchor ad no longer stacks with the apply bar, preview update-count badges removed.

= 1.9.19 =
* v133: One-click first-run setup (categories, policy pages, header/mobile/footer menus, permalinks) + full job meta registered for REST publishing.

= 1.9.18 =
* v131: Sticky apply bar on job posts (deadline countdown + Apply online CTA) and JobPosting JSON-LD from job meta.

= 1.9.17 (2026-09-27, v130 render budget) =
* Below-the-fold homepage sections now use content-visibility with reserved intrinsic sizes, so long pages paint faster without any layout shift; the hero and first rail always render immediately for a clean LCP.
* Printing and search-engine crawling are unaffected — the markup is always present in the DOM.

= 1.9.16 (2026-09-27, v129 auto social cards + quick stories) =
* Automatic 1200x630 branded share card for posts without a featured image, rendered with GD, cached in uploads and served from a /studentup-card/<id>/ endpoint; when GD or a system font is unavailable the feature turns itself off instead of shipping a broken image.
* A real featured image always wins over the generated card, and og:image output is skipped when Rank Math or Yoast already provides it.
* Quick story cards: CSS-only full-screen swipe cards with progress bars, deadline, salary and vacancy chips plus prev/next controls, available on the homepage and via a [studentup_stories] shortcode.

= 1.9.15 (2026-09-27, v128 go-live score) =
* New Appearance → StudentUp Score page and dashboard widget: weighted, live checks for HTTPS, indexing, permalinks, content depth, the six policy pages, logo/site icon, menus, featured images, job data, social links, Search Console, GA4 and the AdSense publisher ID.
* Every check reads real site data and prints the exact fix step; nothing is hardcoded as passing.

= 1.9.14 (2026-09-27, v127 instant navigation + command palette) =
* Browser-native Speculation Rules prerender/prefetch with conservative exclusions (admin, login, nonce, external and nofollow links are never speculated).
* Cross-document View Transitions for app-like page changes; disabled automatically for reduced-motion readers.
* Command palette on Ctrl/Cmd + K: live REST search plus jumps to jobs, scholarships, results, quiz, AI match, salary calculator and calendar, fully keyboard navigable.
* "Picked for you" homepage rail built from the reader's own browsing history in localStorage, with a one-click clear button and no server-side profiling.

= 1.9.13 (2026-09-27, v126 editor job-data box + compare page) =
* New "StudentUp job data" editor box: last date, salary, vacancies, age range, qualification tags, apply URL and verified source date — strict validation means an invalid date or URL is dropped instead of stored.
* Posts list shows a job-data completeness column so missing card, eligibility and calendar data is obvious at a glance.
* Compare page template plus a `[studentup_compare]` shortcode: side-by-side salary, age, qualification, vacancies and last date from published posts only, with "—" wherever a detail is not yet confirmed.
* First hot-job card image now loads eagerly with high fetch priority for a faster LCP; the rest stay lazy.

= 1.9.12 (2026-09-27, v125 SEO + CTR finish) =
* Homepage ItemList JSON-LD built only from published posts — clearer Discover/rich-result signals with no invented ratings or salary markup.
* Urgency chips ("3d left" / "Last day") on hot job cards when a confirmed last date exists; undated posts stay silent.
* Extra high-viewability in-feed ad position after the AI job match block, still inside the existing per-page ad density cap.

= 1.9.11 (2026-09-27, v124 smart layer) =
* AI Job Match + Eligibility Checker: qualification, state and age filters return matching updates instantly in the browser, with an honest "age limit not published" state when the notification data is missing.
* In-hand salary calculator with an open formula (basic + DA + HRA + TA − deductions) and a clearly labelled estimate disclaimer.
* Job calendar listing the next confirmed last dates with days-left chips; undated posts are never given a guessed deadline.
* Trending Today strip under the hero and a state-first homepage switch (Telangana / Andhra Pradesh / All India) stored only in the reader's browser.
* Hot job cards now read the real `studentup_last_date` and `studentup_salary` meta instead of placeholder keys.

= 1.9.10 (2026-09-27, v123 premium homepage + real daily quiz) =
* Premium hero: brand line, live search bar and 🔥 Latest Govt Jobs · 🎓 Scholarships · 📢 Results · 🎫 Hall Tickets quick actions.
* TOP 10 hot jobs today — swipeable Netflix-style cards with last date, salary and apply link.
* Real Daily Quiz block: five date-rotated questions, instant scoring, explanation for each answer and a colourful rotating ring.
* Scholarships spotlight strip plus Scholarships and Daily Quiz in the header, mobile menu and bottom navigation.
* Instant alerts card — reader-approved browser notifications for new posts, with WhatsApp and Telegram fallbacks.
* Social rail is now pinned to the right edge, vertically centred, on phones as well as laptops; it no longer auto-hides.
* Category tiles drop the "N updates" badge so the title and hint text always stay readable.
* New homepage options group (hero, hot jobs, daily quiz, scholarships, alerts, bottom navigation) — every block can be switched off.

= 1.9.9 (2026-09-25, v120 student utility layer + v119 performance hardening) =
* Compare up to three posts locally without an account or reader profile.
* Export a confirmed ISO deadline as a local calendar `.ics` reminder; missing or invalid dates never create a guessed reminder.
* Add accessible Print / PDF actions, keyboard-safe dialogs, reduced-motion styling and dark-mode utility surfaces.
* Keep compare metadata in browser storage only; remind readers to confirm official notifications before acting.

* Featured 1200×675 image is rendered on article pages with eager LCP loading,
  async decoding, reserved aspect ratio and cache-busted theme assets.
* Conditional third-party resource hints: AdSense/GA4 connections are not opened
  before the corresponding feature is configured.
* Unused WordPress embed/block assets are removed on pages that do not need them.
* Caddy static preview serves gzip/zstd plus browser cache headers.
* Verified Success Stories share copy clearly describes the real journey and
  practical lessons without fake urgency or automated sharing.

= 1.9.8 (2026-09-22, v98 viral share engine: in-content share bar + native share sheet) =
* In-content share bar after the first H2 paragraph (WhatsApp/Telegram/copy).
* Rich share text with the real last date; no fake urgency when it has passed.
* Native share sheet on supported mobile browsers (feature-detected, no tracking).
* New option: In-content share bar (default ON).

= 1.9.7 (2026-09-22, v96 Up Next session depth + join-strip dedupe) =
* NEW: `inc/upnext.php` — article chivara "Up Next" (ade category 3 posts) +
  mobile sticky "next article" bar. Reader tap = NIJAMAINA kotha pageview →
  kotha ad request (AdSense policy-safe). Timer/auto-reload eppudu vaddu.
* NEW: `upnext` / `upnext_bar` theme options (rendu default ON).
* FIX: bot madhya-article join strip (`.su-join-strip`) content lo unte theme
  `.su-join-inline` ni render cheyyadu — okate page lo duplicate join box ledu.
* Sticky-ad collision handled (`body.su-has-stickyad .su-nextbar{bottom:78px}`).

= 1.9.6 (2026-09-22, v95 in-content image + contextual links + terms) =
* NEW: content lopala image (`.su-figure`) — rounded, caption styled, width/height
  tho CLS-safe, lazy + async decode (LCP ni touch cheyyadu).
* NEW: in-body contextual internal links (`.su-ctx`) — paragraph lopala, subtle.
* Footer policy row lo Terms of service link add (page publish aithe render).

= 1.9.5 (2026-09-22, v94 Discover + Core Web Vitals) =
* Google Discover large-card image: the theme now registers a 1200x675 size
  (`studentup-discover`) - Discover only shows the big card for images 1200px wide
  or more, and the bot already generates its featured images at exactly 1200x675.
* og:image now ships width, height and alt, so Discover and social unfurls pick
  the right image without re-measuring it. When Rank Math (or Yoast) is active the
  theme upgrades its OG image to the 1200px version through a filter instead of
  printing a second tag - no duplicates, ever.
* CLS: content images get width/height attributes so the browser reserves space
  before the image loads (layout shift stays at zero).
* INP: links and buttons get `touch-action: manipulation`, removing the ~300ms
  double-tap delay on phones - taps feel instant.
* Footer now links the policy pages (privacy, about, contact, disclaimer) so
  readers and AdSense reviewers can reach them from every page.

= 1.9.4 (2026-09-22, v93 top-website UI pass) =
* MENU (main fix): the default menu no longer dumps nine categories into a flat
  row with a description line under each one. It now mirrors the approved design:
  Home / Jobs (dropdown) / Hall Tickets / Results / Current Affairs / More
  (dropdown) - with caret, hover underline, keyboard focus rings, dark mode and a
  "More" dropdown that stays inside the screen. Categories that do not exist yet
  are skipped automatically, and page links (Saved, Contact, About, Quiz) only
  appear when that page is really published - so the menu can never show a 404.
* Telegram link fix: the private-channel invite override now also applies to the
  footer rail icon, the mobile panel row and the footer channel link. Before this,
  those three still pointed at the public username even when a private invite was
  set - the join link simply went to the wrong place.
* Fixed-bar collisions (mobile): the sticky bottom ad used to cover the social
  icons, the floating app button covered the footer, and the saved panel/toast
  sat underneath them. All fixed bars now shift when the sticky ad is on, and the
  footer reserves safe space.
* CSS hygiene: removed a duplicate `display` declaration on the ad placeholder.
* Polish: 64px header row, larger brand text, better hero/section rhythm, subtle
  card hover lift (reduced-motion safe).
* Saved is now reachable from the mobile menu (it closes the menu first).

= 1.9.3 (2026-09-22, v92 saved / reader retention) =
* inc/saved.php + assets/js/studentup-saved.js — reader bookmarks (🔖 save-for-later).
  Everything lives in localStorage: no database table, no cookie, no server round-trip
  (privacy-policy and AdSense clean, zero server load).
* Save button on every job card and on single posts (aria-pressed, keyboard + screen
  reader ready). A saved rail + slide-out drawer keeps the count visible, and a
  `[studentup_saved]` shortcode gives you a full /saved/ page (create it under Pages,
  paste the shortcode, and link it from the menu).
* Reading history: the drawer also lists "Recently read" so a reader can pick up where
  they left off — the strongest return-visit signal on a jobs/exam site.
* New options: StudentUp -> Content -> "Saved / bookmarks" (on by default) and
  "Saved posts limit" (5-200, default 60; oldest entries drop first).
* Graceful degradation: if localStorage is blocked (private mode) the note appears and
  saving turns itself off — the page never breaks.

= 1.9.2 (2026-09-20, v91 Telegram tools) =
* inc/telegram.php — Telegram channel URL resolver with private-channel invite
  override (`telegram_channel_url` option), footer join chip (Telugu CTA), and
  post share URL helper (t.me/share/url).
* New option: StudentUp → Socials → Telegram channel URL override (supports
  https://t.me/+… private invite links; empty = username t.me link).
* Footer: Telegram join chip in the footer-bottom row.

= 1.9.1 (2026-09-20, v90 notifications) =
* inc/notify.php — site-wide alert queue (option-backed, code-wise dedupe,
  cap 20): admin notices (per-user dismiss) + CRITICAL public banner
  (localStorage dismiss) + REST /studentup/v1/notify (GET/POST/DELETE,
  manage_options only). Severities: info · warn · critical.
* New option: StudentUp → Content → Critical alerts public banner (default ON).
* Header renders critical banners right after wp_body_open; studentup.js
  handles reader dismiss via localStorage.

= 1.9.0 (2026-09-19, v89 premium homepage) =
* TS · AP · Central category fix: alias resolver (`studentup_used_term()` +
  `studentup_theme_cat()`) maps theme slugs to live site slugs
  (`ts-jobs`→`ts-govt-jobs`, etc.) — cards, menu, mobile panel, chips and
  footer categories can never silently disappear again; cards' `data-cat`
  is always the theme slug so the live chip filter matches again
* New "Central Govt Jobs" entry in Most searched (TS · AP · Central top-3,
  hot highlighted) — bot `MOST_USED` + preview site synced (same source)
* Latest Jobs scrolling ticker on the homepage (own posts, no feed needed,
  10-min cache, click opens that exact post, hover=pause, reduced-motion off)
* Live search: while you type, results drop down from the WP REST search API
  (debounced, keyboard ↑↓ Enter Esc, click opens the exact post)
* Brand SVG icons (WhatsApp/Telegram/Instagram/YouTube/X) replace platform
  emojis — rail, mobile menu, share bar, join blocks, author box
* Students Internet Center rebranded to its Telugu brand name (TS & AP) with a
  perks row (Application PDF · full Guidance · Preparation Group) and a brand
  WhatsApp button
* Animated qualification dropdown (custom UI over the native select — no-JS
  still works) + SSC/10th wording and SSC GD/MTS/CHSL keyword mapping
* Card footer "Read more" is now a real permalink link (was dead bold text)
* Menu polish: current-page pill, animated submenus, no-wrap laptop scroll;
  3×3 used-strip and 3-column news grid on laptop

= 1.7.2 (2026-09-19, v74 portal removal) =
 * Removed the live exam portal: `exam_url` + `api_base` options, header exam buttons,
  and the dead `?studentup_exam=1` PWA shortcut (it never had a handler)
 * PWA shortcuts now mirror the site: Jobs · Jobs by qualification · Results · Daily Quiz

= 1.7.1 (2026-09-18, v72.1 + v73 copy pass) =
 * v73: English UI pass — chrome/labels/notes/footer English, Telugu only inside post content;
  slim hero replaces the old hero + countdown card (deadline plumbing removed)
 * "⬇️ Install app" web-app button on every visit (mobile first) + device-wise install sheet (no APK claim)
  (Android Chrome prompt · iPhone Share · Computer icon)
 * Qualification chips combine with the category filter in JS (no page reload) + `?qual=` URL sync
 * Expired jobs are hidden from the grid with a note (`#su-hidden-note`)
 * Admin dashboard widget: qualification-wise post counts + posts missing tags
* Public copy clean: coverage line/topbar, demo ads → our partner slot creatives,
  v73: hero is a slim English header — the hero countdown card was removed (no fake timer);
  real deadlines live in post content + the closing-soon badge

= 1.7.0 (2026-09-18, v72) =
* Qualification-wise filter: 10th · 10+2 · ITI · Diploma · Degree · PG · B.Tech chips
  (server-side `?qual=` WP_Query filter) + automatic `studentup_qual` tagging
  (save_post detect · bot REST meta · admin/CLI backfill)
* Header search next to the menu (🔍 panel + `/` shortcut), mobile panel search link
 * PWA: service worker (offline page + repeat-visit speed) + "Install as app" prompt
  (Android/Chrome `beforeinstallprompt`, iPhone Share hint)
 * Closing-soon badges (⏳ closing in 7 days) from `studentup_last_date`
* Breaking-news section default OFF (`breaking_enabled` option) — copy clean-up:
   internal metrics, radar/6-hour notes and "sample/DEMO" labels removed
* New options: breaking_enabled · qual_filter · install_prompt

= 1.6.0 =
* Students Internet Center CTA (call + WhatsApp documents -> application PDF) on every page.
* WhatsApp + Telegram join block replaces the old newsletter form.
* Social rail auto-hides after 9 seconds and returns every 2 minutes, with an instant pull tab (‹).
* Smaller social icons on mobile + block editor parity (assets/css/editor.css).

= 1.5.0 =
* Author archive template (`author.php`) — E-E-A-T: bio · published article count · profile/website link · editorial-policy link
* Author archive CSS block (mobile-first, tokens tho)
* Version parity: style.css ↔ STUDENTUP_VERSION ↔ readme Stable tag (audit ERROR unte)


= 1.4.0 =
* Theme standards pass 3: style.css version ↔ STUDENTUP_VERSION sync (build gate)
* Block editor parity: editor-styles + wp-block-styles + assets/css/editor.css
* `post_class()` on article loops (plugin/CSS compatibility) · `aria-current="page"` nav filter
* Performance: custom WP_Query calls ki no_found_rows (extra SQL query teesesaam)
* IndexNow key-file serving (/<key>.key) — instant indexing automatic


= 1.9.33 (2026-10-02, v183) =
* Board lo kotha section: **Outsourcing & Contract Jobs** (inc/opportunities.php).
  Outsourcing / contract-basis / guest-faculty posts ikkade kanipistayi —
  puratana lo ivi e section lo lekunda board nunchi poyevi (pipeline lo category
  'Outsourcing Jobs' unna kuda). Legacy repair fallback kuda add chesaamu
  (outsourcing / contract-basis / guest-faculty keywords).
* Bot daily list (`--forward-list`) kuda ide section + WhatsApp plain-text
  format tho align ayindi — site board · WhatsApp forward list rendu okate.

= 1.9.32 (2026-10-02, v181) =
* On-site search demand log (inc/searchlog.php): reader searches — live-search
  palette (“wp/v2/search”) + “?s=” pages — anonymous count + zero-result flag.
  Strict privacy: term/count/zero matrame; IP/user eppudu store avvadu (throttle
  transient 60s). Bot + admin searches skip. Bot ee list ni “--search-demand” tho
  chusi content gaps → review queue cheshtundi (auto-publish ledu).


= 1.3.0 (2026-09-18, v67) =
* Deep audit fixes: security hardening module, comments + sidebar templates, POT file,
  below-content ad slot, preconnect hints, focus-visible styles, button types,
  search noindex + search form, sticky sidebar ad, content-visibility

= 1.2.0 (2026-09-18, v66) =
* Consent Mode v2, ads.txt serving, news sitemap, LCP perf module, AdSense-first render,
  in-article ad, density cap, page gating, CLS reserved height, +12 options

= 1.1.0 (2026-09-18, v64) =
* StudentUp options page + REST, auto TOC, JSON-LD schema, author box, PWA, sticky ad

= 1.0.0 (2026-09-18, v61) =
* First release — Telugu student-first layout, dark mode, tiles, ticker, exam countdown
