# LIVE FIX GUIDE — studentup.in (ఈ రోజు చేయాల్సినవి)

**Audit report:** `LIVE_SITE_AUDIT_2026-10.md` · **Code fixes:** v194 (this repo) · **Total time:** ≈90 నిమిషాలు (blockers) + 3 వారాల publishing
**Rule:** ఒక్కో step పూర్తయ్యాక ✅ tick చేయండి. Step order మార్చకండి — 1–2 ముందు చేయకపోతే repair button అనవసరం.

---

## PART A — WordPress Admin (60 నిమిషాలు)

### A1. Demo/junk pages delete (10 pages) — 10 నిమిషాలు
1. WP Admin → **Pages** (left menu).
2. ఈ slugs కోసం వెతకండి, ఒక్కోదానిపై hover → **Trash**:
   `table-block` · `image-gallery-block` · `quote-block` · `columns-block` · `left-sidebar` · `right-sidebar` · `default-width` · `narrow-width` · `3029-2` · `3452-2`
3. `Trash → Empty Trash` (అప్పుడే sitemap నుంచి పోతాయి).
4. **Pages list లో ఇవి మాత్రమే ఉండాలి:** About, Contact, Privacy Policy, Terms, Disclaimer, Editorial Policy, Advertise, My Workspace, Saved, Compare Jobs, Tools.
5. ✅ Done: Page list clean.

### A2. 2020/Unsplash media delete — 5 నిమిషాలు
1. **Media → List view** (top-left icon) → "Date" column click (ascending).
2. 2020/2021 uploads + demo images → select → **Delete permanently**.
3. ✅ Done: Media library లో demo images లేవు.

### A3. Repair button (one click) — 2 నిమిషాలు  ← **v194 code**
1. WP Admin → **Appearance → StudentUp Setup**.
2. కిందకి scroll → **"Repair live pages (older sites)"** → **Repair live pages** button.
3. Green list లో ఇవి కనిపించాలి:
   - `Policy/About pages cleaned: N updated (template note removed, service disclosure added).`
   - `Duplicate page /privacy-policy/ → draft (canonical /privacy/).` (ఇలాంటివి 3–4 lines)
   - `Compare Jobs page template set (page-compare.php).`
4. ✅ Done: "This page was created automatically…" text అన్ని pages నుంచి పోయింది.
> ఏమి delete అవ్వదు — duplicate pages **draft** లోకి మాత్రమే వెళ్తాయి (మళ్ళీ publish చేయవచ్చు).

### A4. About page rewrite — 20 నిమిషాలు
1. Pages → **About** → Edit.
2. ఇవి ఉండాలి (400+ పదాలు):
   - ఎవరు నడుపుతున్నారు (పేరు, ఊరు), ఎప్పటి నుంచి.
   - Content ఎలా verify చేస్తారు (official notification → source link → publish).
   - Correction policy: తప్పు కనిపిస్తే ఎలా చెప్పాలి, ఎన్ని గంటల్లో correct చేస్తారు.
   - Contact: working email + WhatsApp.
3. **"Students Internet Center" paragraph ఉంచండి** — కానీ "separate offline service, optional, website content free" అనే line తో (repair button ఇచ్చిన block అలాగే ఉంచవచ్చు).
4. Save → Purge cache.
5. ✅ Done: About page professional ga undi.

### A5. Contact + emails fix — 5 నిమిషాలు
1. Appearance → **StudentUp** → **Contact email** = `support@studentup.in` (లేదా మీకు నచ్చిన domain email) → Save.
2. `/contact/` (మరియు `/contact-us/` draft అయ్యిందో check) → Save.
3. మీ hosting లో domain email forward create చేయండి (mPanel → Email). `info@charanpendota` అనే address **తప్పు** — పోయిందని confirm చేయండి.
4. Site-wide service block లో `charan.pendota2026@gmail.com` → domain email కి మార్చండి.
5. ✅ Done: ఏ page లోనూ broken email లేదు.

### A6. Cookie banner — 10 నిమిషాలు
1. WP Admin → **WP Consent** (లేదా Consent → Settings).
2. Cookie list లో `__utma/__utmb/__utmc/__utmz` (పాత GA.js names) తీసేయండి → `_ga`, `_ga_XXXXXXX`, `_gid`, `_gcl_au` పెట్టండి.
3. AdSense cookies కి ఒక separate category ("Advertising") add చేయండి (Google AdSense, DoubleClick).
4. "Powered by wpconsent.com" badge option ఉంటే **off** చేయండి (paid tier), లేదా certified CMP plan ki upgrade చేయండి.
5. ✅ Done: consent list honest + no third-party branding.

---

## PART B — mPanel File Manager (10 నిమిషాలు)

### B1. ads.txt fix (BLOCKER)
1. mPanel → **File Manager** → `public_html/studentup/`.
2. `ads.txt` → Edit → **అందులో ఉన్నది మొత్తం తీసేసి** ఇది మాత్రమే paste చేయండి (మీ AdSense publisher ID తో):
   ```
   google.com, pub-0000000000000000, DIRECT, f08c47fec0942fa0
   ```
3. AdSense → Sites → మీ site click → "ads.txt" snippet copy (అక్కడే exact line ఉంటుంది) → అదే paste చేయండి.
4. Plain text మాత్రమే — `<br>`, `<p>`, `#` comments ఉండకూడదు.
5. Browser లో `https://studentup.in/ads.txt` open చేసి confirm చేయండి.
6. ✅ Done: publisher line live.

### B2. robots.txt fix
1. File Manager → `public_html/studentup/robots.txt` → Edit.
2. ఇలా ఉండాలి:
   ```
   User-agent: *
   Disallow: /wp-admin/
   Allow: /wp-admin/admin-ajax.php
   Sitemap: https://studentup.in/sitemap_index.xml
   ```
3. Save → `https://studentup.in/robots.txt` check.
4. ✅ Done: sitemap line live.

### B3. Purge cache
1. WP Admin → **LiteSpeed Cache → Purge → Purge All**.
2. ✅ Done: మొదటి reload లో `x-litespeed-cache: miss`, తరవాత `hit`.

### B4. (Optional, security) HSTS
1. File Manager → `public_html/studentup/.htaccess` → **backup copy** తీసుకోండి.
2. `# BEGIN WordPress` line కి **పైన** add చేయండి:
   ```
   <IfModule mod_headers.c>
   Header always set Strict-Transport-Security "max-age=31536000; includeSubDomains"
   </IfModule>
   ```
3. Save → site reload → DevTools → Network → Response Headers లో `strict-transport-security` కనిపించాలి.
4. ✅ Done.

---

## PART C — Theme upload (5 నిమిషాలు) ⭐ ఇది ముఖ్యం

1. మీ దగ్గర `wordpress-theme/studentup-theme.zip` (117 files · version 1.9.37) ఉంది — GitHub repo లో ఈ path లో ఉంటుంది.
2. WP Admin → **Appearance → Themes → Add New → Upload Theme** → zip select → **Install Now** → **Activate**.
3. Activate చేసిన వెంటనే: **Appearance → StudentUp Setup → Run setup now** (categories/menus/pages safe ga create అవుతాయి — ఉన్నవి touch చేయదు).
4. LiteSpeed → Purge All.
5. Verify (phone + laptop రెండింటిలో):
   - Home page లో **calculators/quiz లేవు** (అవి `/tools/` లో ఉంటాయి).
   - `/tools/` page పని చేస్తుంది (salary, age, fee, syllabus).
   - Bottom navigation (Home · Jobs · Tools · Saved · Menu) mobile లో కనిపిస్తుంది.
   - ఏ button లోనూ emoji లేదు (SVG icons).
6. ✅ Done: live theme = 1.9.37.

> **ఎందుకు:** 1.9.37 లోనే neat home, tools page, CWV/a11y 100/100, livefix (demo pages noindex), repair button ఉన్నాయి. Live లో 1.9.36 ఉంది — మీ మంచి పని server మీద లేదు.

---

## PART D — Bot + content engine (30 నిమిషాలు + రోజూ)

1. మీ server లో (SSH Auth ఉంటే) లేదా cron "Run command" ద్వారా:
   ```
   cd ~/bot && venv/bin/python run.py --check-wp
   ```
   Expected: WP REST auth OK · Gemini key OK · Telegram verified.
2. Dry run:
   ```
   venv/bin/python run.py --daily --daily-no-send
   ```
   1 draft generate అవ్వాలి (error లేకుండా).
3. Cron confirm: మీ 5 lines అలాగే ఉండాలి; **`wp-cli cron event run --due-now --path=public_html/studentup/public` job ni touch చేయకండి** (interval `35 * * * *`).
4. `.env` లో ఇది set చేయండి (byline fix):
   ```
   EDITORIAL_REVIEWER=Charan Pendota
   ```
   (ఇది set చేస్తే byline "Reviewed by Charan Pendota" అవుతుంది; లేకపోతే "Every fact is linked to the official notification" అని వస్తుంది — ఇప్పుడు "draft" అనే word పోయింది.)
5. ఈ రోజు **3 posts publish** చేయండి → రోజూ 1–3 చొప్పున 3 వారాలు.
6. ఏ post లోనూ "Last date: Not announced" ఉండకూడదు — job data box (`inc/jobmeta.php` fields) నింపండి, తెలియకపోతే ఖాళీగా వదిలేయండి.
7. ✅ Done: రోజూ కొత్త content.

---

## PART E — Google Search Console + AdSense (30 నిమిషాలు, 3 వారాల తరవాత apply)

1. **GSC:** `search.google.com/search-console` → property `studentup.in` → verify (DNS లేదా HTML tag).
2. Sitemaps → `sitemap_index.xml` submit. 22 posts కి "Request indexing" (URL Inspection → Request Indexing).
3. Rank Math → **Sitemap Settings**: news sitemap 48 గంటల posts మాత్రమే ఉండేలా; demo pages delete అయ్యాక sitemap మళ్ళీ generate అవ్వాలి (Rank Math → Sitemap → Regenerate).
4. Rank Math → **Redirections**: `/privacy-policy/` → `/privacy/`, `/privacy-policy-2/` → `/privacy/`, `/terms-conditions/` → `/terms/`, `/contact-us/` → `/contact/` — 301 పెట్టండి (draft చేసిన pages కి).
5. 3 వారాల తరవాత (30+ posts, impressions >100/day): AdSense → **Apply now**.
6. Approval వచ్చాక: Auto Ads ON → "In-page" + "Anchor" formats → exclusions లో `.su-quick-facts`, `.su-apply-bar`, forms, quiz పెట్టండి → 1 వారం viewability చూసి తక్కువ unna units తీసేయండి.
7. ✅ Done: measurement + monetisation live.

---

## PART F — ఈ v194 code changes ఏమి చేశాయి (reference)

| # | File | Change | ఎందుకు |
|---|------|--------|--------|
| 1 | `inc/firstrun.php` | `$base` template note = `''` | AdSense reviewer "unfinished template" చూడకూడదు |
| 2 | `inc/firstrun.php` | `studentup_setup_service_block()` — separated disclosure ("Students Internet Center — separate offline service, optional, free to read") | Publisher content vs paid service separation (policy clarity) |
| 3 | `inc/firstrun.php` | `studentup_repair_pages_run()` + **Repair live pages** button | Live pages లో note తీసేయడం, disclosure add చేయడం, duplicate pages → draft, Compare template |
| 4 | `inc/livefix.php` (NEW) | Lorem ipsum / "SEO Optimisation Checklist" pages → **noindex**; attachment pages → 301; empty search → noindex | Junk pages Google index లోకి పోకుండా (owner delete చేసే వరకు) |
| 5 | `functions.php` | `require inc/livefix.php` | Module load |
| 6 | `autoblog/seo.py` | Byline: "Source-backed draft; verify the official notice" → "Every fact is linked to the official notification" | "draft" word public ga ఉండకూడదు |
| 7 | `autoblog/seo.py` | `image_alt()` default brand `studentup.in` → `StudentUp` | TTS "studentup dot in" keyword-stuffing laga vinipistundi |
| 8 | `tests/v194_test.py` (NEW) | 7 gates (note absent, disclosure, duplicates, byline, alt, livefix, deliverables) | ఈ defects మళ్ళీ రాకుండా permanent test |

**Proof commands (local):**
```
node tools/php_lint.js wordpress-theme/studentup      → 88/88 files OK
python run.py --test-all --test-only v194             → ALL v194 TESTS PASSED
python run.py --test-all                              → all suites
```

---

## FINAL CHECKLIST (print this)

- [ ] A1 demo pages trash + empty trash
- [ ] A2 2020 media delete
- [ ] A3 Repair live pages (Appearance → StudentUp Setup)
- [ ] A4 About page rewritten
- [ ] A5 contact emails fixed
- [ ] A6 cookie banner cleaned
- [ ] B1 ads.txt publisher line
- [ ] B2 robots.txt sitemap line
- [ ] B3 LiteSpeed purge
- [ ] B4 HSTS (.htaccess)
- [ ] C  theme 1.9.37 uploaded + activated + setup run + phone/laptop verification
- [ ] D  bot `--check-wp` green + dry-run + 3 posts published today
- [ ] D  `EDITORIAL_REVIEWER` set in `.env`
- [ ] E  GSC verified + sitemap submitted + 301 redirects
- [ ] E  3 weeks later: AdSense apply
