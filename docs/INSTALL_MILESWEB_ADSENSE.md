# StudentUp theme — MilesWeb install + AdSense/Discover approval guide

Theme: `wordpress-theme/studentup-theme.zip` (v1.9.15)
Verified before shipping: PHP lint **54/54 files OK**, theme audit **0 errors / 0 warnings**,
deep audit **0/0**, zip packaged from the same source tree.

---

## 1. Upload (5 minutes)

1. WP Admin → **Appearance → Themes → Add New → Upload Theme**
2. `studentup-theme.zip` select → **Install Now** → **Activate**
3. Activation lo theme automatic ga chestundi:
   - missing categories seed (TS/AP/Central jobs, Results, Hall Tickets, Scholarships, Daily Quiz, …)
   - PWA manifest + service worker routes
   - fallback menu (menu assign cheyyakapoina header lo anni sections vastayi)

> Upload fail aithe (`The link you followed has expired`): MilesWeb cPanel → **MultiPHP INI Editor** →
> `upload_max_filesize = 64M`, `post_max_size = 64M`, `max_execution_time = 300`.

## 2. Settings (10 minutes)

| Where | What |
|---|---|
| Settings → Permalinks | **Post name** → Save |
| Settings → Reading | "Discourage search engines" **unchecked** |
| Appearance → Customize → Site Identity | Logo + **Site icon** (512×512) |
| Appearance → Menus | Menu create → location **Main menu (header)** |
| Appearance → **StudentUp Settings** | Social handles, Telegram channel, contact email |
| Appearance → **StudentUp Score** | 100/100 varaku follow avvandi |

## 3. MilesWeb specific

- **SSL**: cPanel → *SSL/TLS Status* → **Run AutoSSL** → tarvata Settings → General lo rendu URLs `https://`.
- **PHP version**: cPanel → *Select PHP Version* → **8.1 or 8.2**, extensions: `imagick`, `intl`, `curl`, `zip` ON.
- **Object cache / LiteSpeed**: LiteSpeed Cache plugin unte —
  - Cache → **ON**, Purge on upgrade ON
  - Optimize → **Do NOT** combine/defer `studentup-premium.js`, `studentup-smart.js`, `studentup-cmdk.js`
    (ivi already footer-deferred; combine chesthe command palette + quiz break avvachu)
  - CSS: minify OK, **critical CSS generation OK**, "Remove unused CSS" **OFF** (theme lo dynamic classes unnayi)
- **Cron**: shared hosting lo WP-Cron slow — cPanel → *Cron Jobs*:
  `wget -q -O /dev/null https://studentup.in/wp-cron.php?doing_wp_cron` (every 15 min), tarvata
  `wp-config.php` lo `define('DISABLE_WP_CRON', true);`
- **Backups**: cPanel → JetBackup → weekly full backup ON.

## 4. AdSense approval checklist (theme already covers the code side)

Theme side ✅ (already shipped):
- Policy pages footer lo prathi page nunchi link (publish chesthe chaalu)
- `ads.txt` serving, ad density cap (`max_ads`), lazy below-fold ads, **no ads until you switch
  "AdSense APPROVED" ON** (blank-box/policy risk zero)
- Consent Mode v2 + CMP snippet field (EEA/UK/CH)
- Author box + editorial policy + source links (E-E-A-T)

Meeru cheyyalsinavi:
1. **6 policy pages** publish: `privacy`, `about`, `contact`, `disclaimer`, `terms`, `editorial-policy`
   (slugs ivi ne — theme automatic ga footer lo link chestundi)
2. **25+ original posts**, prathi post lo official source link + verified date
3. Apply → approval mail vachaka: StudentUp Settings → **Ads** tab
   - `adsense_client` = `ca-pub-…`
   - **AdSense APPROVED** toggle ON
   - slot IDs paste (top-leaderboard, in-feed, mid, below-content, sidebar, anchor)
   - `ads.txt` line paste
4. Auto ads vaddu modatlo — manual slots RPM ekkuva, policy risk thakkuva.

## 5. Google Discover / News

- Prathi post ki **1200×675+ featured image** (theme `studentup-discover` size register chesindi)
- `/news-sitemap.xml` Search Console lo submit cheyandi
- IndexNow key (Advanced tab) pettandi → Bing/Yandex instant indexing
- Homepage lo ItemList schema + post lo Article schema automatic
- Title lo clickbait vaddu, date + source clear ga — Discover policy safe

## 6. Post publish workflow (features live avvadaniki)

Prathi job post lo **"StudentUp job data"** box nimpandi:

| Field | Example |
|---|---|
| Last date to apply | `2026-10-05` |
| Salary / pay scale | `₹18,000 – ₹56,900` |
| Total vacancies | `8326` |
| Min / Max age | `18` / `27` |
| Qualification tags | `10th, inter` |
| Official apply URL | `https://ssc.gov.in/...` |
| Source URL + verified on | notification PDF + `2026-09-27` |

Idi nimpithe automatic ga: hot cards chips, AI job match, eligibility checker (✅/❌),
job calendar, compare table, urgency badges — anni live.

## 7. Launch-day smoke test (10 clicks)

1. Home page: hero search, 4 quick pills, hot-jobs rail scroll
2. `Ctrl/⌘ + K` → palette open → type "ssc" → result open
3. Daily quiz: 5 questions answer → score + explanation
4. AI job match: qualification + age → ✅/❌ badges
5. Salary calculator: numbers marchithe in-hand update
6. Phone lo: bottom nav 5 icons, right-middle social rail, menu panel
7. Dark mode toggle → anni sections readable
8. `/compare/` page (template assign chesaka) → table scroll
9. Alerts card → "Turn on alerts" → permission → test notification
10. Appearance → **StudentUp Score** → 100/100
