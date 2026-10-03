# DEPLOY NOW — studentup.in (final, ఈ రోజు చేయండి)

**Theme:** 1.9.37 · zip **117 files · 1042 KB** · sha256 `4fa81c83bf42…`
**Verified:** 139/139 suites ✔ · parity PIN-TO-PIN ✔ · php-lint 88/88 ✔ · cwv 0/0 ✔ · visual 100/100 ✔
**Audit:** [`LIVE_SITE_AUDIT_2026-10.md`](LIVE_SITE_AUDIT_2026-10.md) · **Fix runbook:** [`LIVE_FIX_GUIDE.md`](LIVE_FIX_GUIDE.md)

---

## STEP 0 — Theme zip download (2 నిమిషాలు)

**మొబైల్ లేదా ల్యాప్టాప్ బ్రౌజర్లో ఈ link open చేయండి:**

```
https://github.com/charanpendota98-prog/Automation_charan1/blob/arena/01a10001-automation-charan1/wordpress-theme/studentup-theme.zip
```

పైన కుడి corner లో **Download** button నొక్కండి (లేదా "Raw").
ఫైల్ పేరు: **`studentup-theme.zip`** · సైజు **1042 KB** — ఇదే సరైనది.

> ❌ పొరపాటుగా "studentup-theme-1.9.35.zip" వంటి పాత zip తీసుకోకండి. **Version 1.9.37** మాత్రమే.

---

## STEP 1 — Demo/junk pages delete (10 నిమిషాలు · WP Admin)

1. **Pages** → ఈ slugs hover → **Trash**:
   `table-block` · `image-gallery-block` · `quote-block` · `columns-block` · `left-sidebar` · `right-sidebar` · `default-width` · `narrow-width` · `3029-2` · `3452-2`
2. **Trash → Empty Trash**
3. ✅ Pages list లో ఇవి మాత్రమే ఉండాలి: About, Contact, Privacy Policy, Terms, Disclaimer, Editorial Policy, Advertise, My Workspace, Saved, Compare Jobs, Tools

## STEP 2 — 2020/demo images delete (5 నిమిషాలు)

**Media → List view** → Date column (ascending) → 2020/2021 uploads + demo images → **Delete permanently**

## STEP 3 — Theme upload + activate (5 నిమిషాలు) ⭐

1. **Appearance → Themes → Add New → Upload Theme** → `studentup-theme.zip` select → **Install Now**
2. **Activate**
3. **Appearance → StudentUp Setup → Run setup now** (ఉన్నవి touch చేయదు, కొత్తవి సృష్టిస్తుంది)
4. ✅ Verify (`view-source:` లో `studentup/style.css?ver=1.9.37`)

## STEP 3b — Run setup (hub pages + editorial page) (2 నిమిషాలు) 🆕 v195

After activating the theme: **Appearance → StudentUp Setup → Run setup now**.
Idi ee kotha pages ni create chestundi (delete/overwrite cheyyadu):
- Hub pages: `/ts-jobs-hub/` · `/ap-jobs-hub/` · `/central-jobs-hub/` · `/results-hub/` · `/scholarships-hub/` (footer menu lo links kuda)
- `/editorial-team/` — author profile + verification process (E-E-A-T; AdSense/Google News reviewers idi chustaru)
- Person schema + Organization.founder automatic ga vastayi.

**Tarvata 3 నిమిషాలు:** Appearance → **StudentUp** → ఇవి నింపండి:
- `Author name` = మీ నిజమైన పేరు · `Author role` (v195) · `Author expertise` (v195) · `Publishing since` (v195)
- `Reviewer name` (v195) = draft review chesina నిజమైన వ్యక్తి పేరు (ఖాళీగా ఉంచితే "Sources verified: <date>" అని మాత్రమే చూపిస్తుంది — తప్పుడు "reviewed by" claim ఉండదు)
- `Author photo URL` — Media Library లో ఫోటో upload చేసి URL paste చేయండి

## STEP 3c — v196 pages (calendar · pricing · corrections) (2 నిమిషాలు) 🆕 v196

Step 3b (Run setup) ఇవి కూడా create చేస్తుంది — template auto-assign తోనే:
- **`/exam-calendar/`** — confirmed last-dates month-wise + **"Add all dates to my calendar (.ics)"** button (student deadline intelligence)
- **`/internet-center/`** — **transparent price list** (₹50 / ₹100 / ₹150 — Appearance → StudentUp లో మార్చవచ్చు), what's included, "what we never do", govt-fee separation, refund rule
- **`/corrections/`** — public correction log (bot/admin `studentup_correction_note` meta నింపితే automatic ga list avutundi)

Verify: మూడు pages open అవ్వాలి · calendar page లో dates kanipinchali (`studentup_last_date` unna posts ఉంటే) · `.ics` download పని చేయాలి.

## STEP 4 — Repair live pages (2 నిమిషాలు) ⭐ — ఒక్క click

**Appearance → StudentUp Setup** → కింద **"Repair live pages (older sites)"** → **Repair live pages**
Expected green lines:
- `Policy/About pages cleaned: N updated (template note removed, service disclosure added).`
- `Duplicate page /privacy-policy/ → draft (canonical /privacy/).` (3–4 lines)
- `Compare Jobs page template set (page-compare.php).`

## STEP 5 — About page rewrite (20 నిమిషాలు)

Pages → **About** → Edit → 400+ పదాలు: ఎవరు నడుపుతున్నారు · ఎప్పటి నుంచి · facts ఎలా verify చేస్తారు · correction policy · working contact.
(Repair దిద్దిన "Students Internet Center — separate offline service" block అలాగే ఉంచండి.)

## STEP 6 — Contact emails (5 నిమిషాలు)

**Appearance → StudentUp → Contact email** = `support@studentup.in` (domain email create చేయండి) → Save.
Site-wide service block లోని `charan.pendota2026@gmail.com` → domain email కి మార్చండి.

## STEP 7 — ads.txt fix (3 నిమిషాలు) ⭐ BLOCKER

**mPanel → File Manager → `public_html/studentup/ads.txt` → Edit → మొత్తం తీసేసి ఇది మాత్రమే:**

```
google.com, pub-XXXXXXXXXXXXXXXX, DIRECT, f08c47fec0942fa0
```

`pub-XXXXXXXX` స్థానంలో **AdSense → Sites → ads.txt** లో చూపిన మీ exact publisher line paste చేయండి. Plain text — `<br>`, `<p>`, `#` comments ఉండకూడదు.
✅ Check: `view-source:https://studentup.in/ads.txt`

## STEP 8 — robots.txt fix (2 నిమిషాలు)

`public_html/studentup/robots.txt`:

```
User-agent: *
Disallow: /wp-admin/
Allow: /wp-admin/admin-ajax.php
Sitemap: https://studentup.in/sitemap_index.xml
```

## STEP 9 — LiteSpeed cache purge (1 నిమిషం)

WP Admin → **LiteSpeed Cache → Purge → Purge All** → reload ×2 (`miss` → `hit`)

## STEP 10 — (.htaccess) HSTS (3 నిమిషాలు · optional but recommended)

File Manager → `public_html/studentup/.htaccess` → **backup copy** → `# BEGIN WordPress` కి పైన add:

```
<IfModule mod_headers.c>
Header always set Strict-Transport-Security "max-age=31536000; includeSubDomains"
</IfModule>
```

## STEP 11 — Bot restart + content (30 నిమిషాలు)

```bash
cd ~/bot && venv/bin/python run.py --check-wp
venv/bin/python run.py --daily --daily-no-send      # dry run
```
- `.env` లో: `EDITORIAL_REVIEWER=Charan Pendota`
- ఈ రోజు **3 posts publish** → రోజూ 1–3 చొప్పున 3 వారాలు
- ఏ post లోనూ "Last date: Not announced" ఉండకూడదు (job data box నింపండి / ఖాళీగా వదలండి)
- ⚠️ `wp-cli cron event run --due-now --path=public_html/studentup/public` job ni **touch చేయకండి**

## STEP 12 — Google Search Console (15 నిమిషాలు)

1. Search Console → property `studentup.in` → verify
2. Sitemaps → `sitemap_index.xml` submit
3. 22 posts → URL Inspection → **Request Indexing**
4. Rank Math → Redirections → `/privacy-policy/` → `/privacy/` మొదలైన 301s (draft చేసిన pages కి)
5. Rank Math → Sitemap → **Regenerate** (demo pages పోయాక)

---

## FINAL VERIFY (deploy తర్వాత 10 నిమిషాలు)

| # | Check | Expected |
|---|---|---|
| 1 | `view-source:https://studentup.in/` | `style.css?ver=1.9.37` |
| 2 | Home page (phone) | calculators/quiz **లేవు** · bottom nav ఉంది · emoji లేవు |
| 3 | `/tools/` | salary · age · fee · syllabus tools పని చేస్తున్నాయి |
| 4 | `/about/` | "created automatically" line **లేదు** |
| 5 | `/3452-2/` | 404 (delete అయ్యింది) |
| 6 | `/ads.txt` | `google.com, pub-…` line |
| 7 | `/privacy-policy/` | draft/redirect (canonical `/privacy/`) |
| 8 | `/exam-calendar/` · `/internet-center/` · `/corrections/` | pages load · .ics download · price table · hub/editorial links |
| 8b | `/ts-jobs-hub/` + `/editorial-team/` | pages load · footer లో hub links · Person/ItemList schema (`view-source` లో `"@type":"Person"`) |
| 9 | Lighthouse (mobile) | Speed Index ≤ 4.0s · `PAGE_HUNG` లేదు (per-template critical CSS kotha inline layer) |
| 10 | GSC | sitemap "Success" · indexed pages పెరుగుతున్నాయి |

## ROLLBACK (ఏదైనా తప్పు జరిగితే)

WP Admin → **Appearance → Themes** → పాత theme కనిపిస్తే **Activate**.
White screen అయితే: mPanel File Manager → `public_html/studentup/wp-content/themes/studentup/` folder rename → WP automatically default theme కి వెళ్తుంది.

---

## నాకు తెలియజేయండి (deploy తర్వాత)

ఇవి పంపండి — నేను verify చేసి, మిగిలినవి fix చేస్తా:
1. `view-source:https://studentup.in/` లో `style.css?ver=` line (screenshot లేదా text)
2. Repair button green output lines
3. `https://studentup.in/ads.txt` screenshot
4. Home page phone screenshot
