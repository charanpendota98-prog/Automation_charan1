=== StudentUp ===
Contributors: studentup
Requires at least: 6.0
Tested up to: 6.7
Stable tag: 1.9.5
Requires PHP: 7.4
Version: 1.9.5
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
 * "⬇️ Download App" button on every visit (mobile first) + device-wise install sheet
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
