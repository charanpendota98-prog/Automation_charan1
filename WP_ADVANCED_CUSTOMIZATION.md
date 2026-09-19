# 🛠️ WP ADVANCED CUSTOMIZATION — studentup.in (v42)
### "WordPress lo ippudu website customize cheyyadaniki — em, ela, exactly anni."
*Ee file matrame follow cheyandi. Bot automatic ga chesthunna varam manakai rework cheyakapovadu — divide clear ga:*

---

## 0️⃣ DIVIDE — BOT automatic ga chesthundhi vs MEERU chadaru

| ✅ BOT (commands) — automatic | 👤 MEERU (wp-admin) — manual 1-time |
|---|---|
| `--setup` — tagline, timezone IST, comments OFF, footer legal menu, favicon, category SEO | **Theme install + activate** (Part 1) |
| `--plugins` — Rank Math, Redirection, UpdraftPlus, WP Super Cache | **WP Code snippets paste** (Part 2 — repo lo ready files!) |
| `--polish` — site-wide Design Kit CSS (brand, tables, cards, dark mode, quiz UI) | **Rank Math advanced** (Part 3 — Local SEO location!) |
| `--quiz-kit` / `--adsense-kit` / `--service-center` / `--ensure-adsense` | **Cloudflare + cache settings** (Part 4) |
| `--rebuild-hubs` — authority hub pages + internal links | **Footer menu assign + verify** (Part 2.3) |
| `--site-audit-fix --site-audit-apply` — 20 safe fixes (junk pages, PII, tags) | **Wordfence 2FA** (Part 6) |
| Prathi post ki — Rank Math meta, schema, TOC, countdown, fact guard, thumbnail | **PSI + Rich Results verify** (Part 7) |

> **Rule:** mee 70% work already bot chesthundi. Meeku **~60 minutes** manual kaavali matrame — ee file order lo follow cheyyandi.

---

## 1️⃣ FOUNDATION (10 min — one-time, theme decision + settings)

### 1.1 Theme — final decision (advanced users ki)
**Option A (RECOMMENDED): GeneratePress (FREE, classic)** — CWV green, config minimal
1. `pagespeed.web.dev` lo `studentup.in` test → **Mobile 80+** unte: **theme change cheyaku** (bot `--polish` already design chesthundi — same theme vadeyandi)
2. **80 kante takkuva** unte:
   - WP Admin → **Appearance → Themes → Add New** → search **"GeneratePress"** → Install → **Activate**
   - Theme change taruvata **1 min** lo: **Appearance → Menus** → `studentup-legal` menu (bot create chesindi) → **Footer** location lo assign (drop-down, 30 sec)
3. **Block theme alternative** (full site editor kavali ante): "Twenty Twenty-Five" (free) → **Appearance → Editor** lo header/footer edit cheyochu — kaani speed + readability lo GeneratePress safe. **Verdict: GeneratePress.**

### 1.2 Settings (bot `--setup` automatic ga chesthundi — verify matrame)
| Item | Location | Correct value |
|---|---|---|
| Discourage search engines | Settings → Reading | ❌ UNCHECKED (bot `--setup` BLOCK ga flag chesthundi) |
| Permalinks | Settings → Permalinks | **Post name** (`/tspsc-group-2/` lanti URL) |
| Timezone | Settings → General | **Asia/Kolkata** |
| Posts per page | Settings → Reading | **10** |
| Comments | Settings → Discussion | **OFF** (bot set chesthundi) |
| Site icon | Settings → General | 512×512 logo (bot `SITE_LOGO_URL` tho auto-set chesthundi) |
| Tagline | Settings → General | bot tagline (Telugu) |

✅ Verify: server lo `python run.py --setup --dry-run` → **"0 blockers"** avvali.

---

## 2️⃣ ADVANCED DESIGN CONTROL (20 min)

### 2.1 Advanced CSS + PHP packs — repo lo ready files (paste matrame)
**Files:**
- `tools/wp-advanced.css` — 12 advanced blocks: sticky header + blur, card hover, LCP image containment, table mobile scroll, 44px tap targets, focus-visible, reduced-motion, print styles, dark-mode compat
- `tools/wp-advanced-snippets.php` — 7 guarded PHP functions (`su_` prefix, idempotent, zero conflicts)

**Install (WP Code plugin — free, 2 min):**
1. WP Admin → **Plugins → Add New** → search **"WPCode"** (formerly Code Snippets) → Install + Activate
2. **WPCode → Add New Snippet**:
   - **Snippet 1:** Name `studentup advanced pack` → code box lo `tools/wp-advanced-snippets.php` content full ga paste → Location: *Run snippet everywhere* → **Activate**
   - **Snippet 2:** Name `studentup advanced css` → Type: *HTML head* → code box lo:
     ```html
     <style>
     (tools/wp-advanced.css content full ga)
     </style>
     ```
     → **Activate**
3. Front page refresh → header sticky ga untundi, cards hover chesthayi, mobile lo tables scroll avutayi.

> ⚠️ **Conflict check:** `--polish` (Design Kit) already run ayyina varam — Design Kit = post-internal components (quick answer, TOC, tables, share bar), ee packs = site-shell layer (header, interaction, mobile). Rendu **complement** avutayi, fight avvakapovadu (low-specificity selectors).

### 2.2 Header/footer advanced (GeneratePress lo)
- **Appearance → Customize → Header:**
  - Top bar: contact email + social (optional)
  - Primary: logo left + menu right + **CTA button** "📞 Get Help" (Menu lo custom link — URL `#services`, class `su2-cta` CSS already pack lo unti)
  - Sticky: bot CSS `position:sticky` + scroll shadow (Part 2.1)
- **Appearance → Customize → Footer:**
  - 3 columns: (1) brand + tagline (2) Explore links (3) Legal menu (`studentup-legal`)
  - **Appearance → Menus** lo `studentup-legal` → Footer location assign (bot attempt chesthundi — verify cheyyandi)
- **Block themes ( Twenty Twenty-Five) unte:** Appearance → **Editor** → Header template → blocks drag (logo + navigation + button) → Pattern ga save cheyandi.

### 2.3 Homepage layout advanced (block editor lo)
WP Admin → **Pages → Home → Edit** (block theme/Gutenberg unte):
- **Hero section:** heading (H1 ekkuva matrame!) + sub + 2 buttons (Explore / Try Exam)
- **Quick access grid:** 4 items (Jobs / Scholarships / Results / Daily Quiz) — *Columns block 4-col*
- **Fresh updates:** *Query Loop* block — latest 8 posts, **Cards layout** (bot content matrame vasthundi)
- **Editor's pick:** *Query Loop* — 1 post large
- **Quiz widget:** bot `--quiz-kit` already site-wide widget install chesthundi (verify: sidebar lo "Daily Quiz")
- **Sidebar:** Trending (Widget: Popular Posts) + Service card (bot `--service-center` page link)

---

## 3️⃣ RANK MATH ADVANCED (15 min — "Google top" lo biggest manual lever)

Bot already: prathi post ki focus keyword, meta (59/154 target), schema (Article/Breadcrumb/eligible JobPosting), internal links, hub links — set chesthundi.

**Mee advanced settings:**

| Setting | Path | Value |
|---|---|---|
| **Local SEO location** ⚠️ *(audit finding!)* | Rank Math → **Local SEO → General** | Hyderabad, Telangana add — business name "studentup.in", address. *Without this: `locations.kml` live aa kaani location data ledu — audit 🔴.* |
| Sitelinks search box | Rank Math → Titles & Meta | ✅ ON (schema sitelinks search box vasthundi — `tools/...php` snippet #5 OFF ga undi, conflict lekapadi) |
| Breadcrumbs | Rank Math → Titles & Meta | ✅ ON, separator `›` |
| Sitemap exclusions | Rank Math → Sitemap Settings | **Tags OFF**, Categories lo 0-posts unna varam exclude, attachments OFF |
| GSC connect | Rank Math → Google Search Console | **Authenticate** (2-min OAuth) → index status + coverage auto |
| IndexNow | Rank Math → IndexNow | Key add (indexnow.org) + `KEY.key` site root lo upload |
| Data types | Rank Math → Titles & Meta → Data Types | Articles: `Article` schema; Products: OFF (edu site) |

**Search Appearance template (homepage title):**
```
%title% — studentup.in | TS & AP Students
```
*(Bot posts unna varam `%title%` already optimized — theme matrame set cheyandi)*

---

## 4️⃣ PERFORMANCE ADVANCED (10 min — Core Web Vitals green)

### 4.1 Cache (WP Super Cache — bot install chesthundi)
WP Admin → **Settings → Performance (WP Super Cache):**
- ✅ **Caching On**
- ✅ **Compress pages**
- ✅ **Compress CSS, JS and HTML**
- ✅ **Disable serving stale pages**
- Logged-in users lo caching OFF (auto)
- Prathi publish taruvata: *Super Cache → Advanced* lo **"Delete Cache"** — leda bot auto-invalidate chesthundi

### 4.2 Cloudflare (FREE — biggest jump)
1. Domain DNS → Cloudflare lo add (2-min) → nameservers WP admin lo update
2. Settings:
   - **SSL/TLS: Full (strict)**
   - **Caching → Browser Cache: 4 hours** (static assets 1 week — CF lo)
   - **Speed → Auto Minify: OFF** (theme/CSS packs already clean)
   - **Speed → Image Resizing: ON** (AVIF/WebP auto)
   - **Speed → Polish: Rocket Loader OFF** (quiz JS break avvakapovaddi safe measure)
   - **Page Rules:** `/wp-admin/*` → bypass cache
3. `https://studentup.in` → pagespeed.web.dev → **Mobile 90+ target**

### 4.3 LCP protection (content level)
- Prathi post lo **featured image 1200×675** (bot already)
- Hero/first image `loading="eager" fetchpriority="high"` — `tools/wp-advanced-snippets.php` snippet #6 automatic ga chesthundi
- Fonts: snippet #2 preconnect+preload (bot Design Kit `--polish` @import tho dedupe — clean)

---

## 5️⃣ TRUST + ADSENSE ADVANCED (10 min)

Bot `--ensure-adsense` already 5 policy pages create chesthundi: **About, Contact, Privacy Policy, Editorial Policy, Corrections**.

**Mee verify + fix:**
1. **Appearance → Menus** → `studentup-legal` → Footer lo assign (Part 2.3)
2. ⚠️ **Audit finding fix** (server lo): `python run.py --site-audit-fix --site-audit-apply`
   - `privacy-policy-2` slug fix · duplicate contact page → draft · demo pages → trash
   - PII phone strip · raw shortcode strip · tag merge (lossless) · timezone → IST
3. **AdSense approval ki extra advanced touches:**
   - Homepage lo **About + Contact links visible** (header/menu lo)
   - `ads.txt` — approval ayyaka: files/ads.txt create (Google dashboard lo exact content)
   - **ADSENSE_APPROVED=1** + `ADSENSE_CLIENT_ID=ca-pub-...` `.env` lo → bot `--adsense-kit` auto loader install chesthundi (3-slot cap, CLS-safe wrappers)
4. **Corrections workflow** (E-E-A-T): prathi post footer lo report-by-email line (bot already) + Corrections page lo form link

---

## 6️⃣ SECURITY ADVANCED (5 min)

| Item | Action |
|---|---|
| **2FA** | Plugins → **Wordfence** (free) → install → 2FA enable (QR scan) |
| **Login limit** | Wordfence → brute-force limit ON (5 tries / 10 min) |
| **Backups** | **UpdraftPlus** (bot install) → Settings → **Daily** backups → remote: **Google Drive** (free OAuth) |
| **Least privilege** | Bot ki **Application Password** matrame (wp-admin → Users → Application Passwords) — admin user/password .env lo lekapadam |
| **Author enumeration** | `tools/wp-advanced-snippets.php` snippet #7 — `/author/admin/` → 301 home |
| **PHP** | Host lo **PHP 8.1+** verify (WP 6.4+ requirement) |

---

## 7️⃣ VERIFICATION (10 min — "fully verify" loop)

**Server SSH lo (exact order):**
```bash
python run.py --doctor                      # env health
python run.py --setup --dry-run             # 0 blockers avvali
python run.py --production-audit            # 11/11 pass
python run.py --site-audit                  # findings
python run.py --site-audit-fix --site-audit-apply   # 20 safe fixes apply
python run.py --polish                      # design kit refresh
python run.py --rebuild-hubs                # hubs + internal links
python run.py --google-audit https://studentup.in/  # PUBLIC audit (PSI real scores)
```

**Browser lo:**
1. `pagespeed.web.dev` → studentup.in → **Mobile 90+** target (LCP < 2.5s, CLS < 0.1, INP < 200ms)
2. `search.google.com/test/rich-results` → homepage + 3 posts → **0 errors**
3. Google Search Console → **Indexing → Pages** → sample 5 URLs "Indexed"
4. Mobile browser: sticky header, tap targets, dark mode, quiz — 2-min manual pass
5. `view-source:` → JSON-LD 2+ blocks valid · canonical correct · OG tags present

---

## 8️⃣ 60-MINUTE SESSION CHECKLIST (copy-paste ga follow)

| # | Action | Time | Status |
|---|---|---|---|
| 1 | `--setup --dry-run` → 0 blockers | 2 min | ☐ |
| 2 | Theme: GeneratePress activate (PSI < 80 unte) | 3 min | ☐ |
| 3 | Footer menu assign (`studentup-legal` → Footer) | 2 min | ☐ |
| 4 | WP Code: `tools/wp-advanced-snippets.php` paste + activate | 3 min | ☐ |
| 5 | WP Code: `tools/wp-advanced.css` head snippet paste + activate | 3 min | ☐ |
| 6 | Rank Math: Local SEO location + Sitelinks + sitemap + GSC OAuth | 10 min | ☐ |
| 7 | WP Super Cache settings (Part 4.1) | 3 min | ☐ |
| 8 | Cloudflare: Full(strict) + browser cache + image resize | 10 min | ☐ |
| 9 | Wordfence 2FA + UpdraftPlus daily + Google Drive | 8 min | ☐ |
| 10 | `--site-audit-fix --site-audit-apply` (server) | 2 min | ☐ |
| 11 | `--google-audit https://studentup.in/` + PSI 90+ verify | 5 min | ☐ |
| 12 | Rich Results Test 0 errors + mobile manual pass | 7 min | ☐ |

**Total: ~58 min. Taruvata: "top website" — verified, audited, advanced.** ✅

---

## ❓ Common doubts

**Q: Bot `--polish` + mee CSS packs — conflict avvatada?**
A: Le. Design Kit = post-internal (tables/TOC/quick-answer/share), packs = site-shell (sticky header/interaction/mobile). Low-specificity selectors, `su2-` prefix.

**Q: Rank Math unna varam `SU_ADV_JSONLD` enable cheyyala?**
A: Default OFF ga undi. Sitelinks search box Rank Math tho matrame vadam best — duplicate WebSite JSON-LD redundant.

**Q: Theme change chesaka posts break avvatada?**
A: Le — posts/content theme-independent. Bot `--polish` widget theme-agnostic (body class based).

**Q: Cloudflare Rocket Loader enable cheyyala?**
A: **Le.** Quiz widget + design kit JS break avvakapovaddi. Auto Minify kuda OFF (already minified).

**Q: Ranking guarantee?**
A: **Le** (honest). EE: content quality + 11,192-keyword universe (17 pillars) + GSC loop + hubs + quiz/question + CWV green — anni ee setup tho ready. Google ranking content + time tho matrame vasthundi — code tho guarantee cheyagalanu.

*Last updated: v42 (2026-09-16) — Full verify + full audit: 30/30 suites · 39/39 runtime checks · 4/4 audit gates · report: `output/audit/full-verification-20260916.md`*
