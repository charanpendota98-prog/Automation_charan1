=== StudentUp ===
Contributors: studentup
Requires at least: 6.0
Tested up to: 6.7
Stable tag: 1.6.0
Requires PHP: 7.4
Version: 1.3.0
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
  (TS/AP), breaking ticker, exam countdown, related posts, author box (E-E-A-T)
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
Client/slot lekapote house ads (Bot nimpinaవి) render avutayi.

= Rank Math fields land avvatledu? =
Theme lo REST bridge (`inc/seo-bridge.php`) undi. Mee koరaku `manage_options` unna
user tho App Password ivvandi (Administrator role).

== Changelog ==

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
