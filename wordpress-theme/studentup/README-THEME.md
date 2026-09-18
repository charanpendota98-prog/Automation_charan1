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
| `studentup_proof_json` | trust tiles numbers | `{"keywords":11192,"sources":143,"entities":203}` |
| `studentup_deadline_json` | ముఖ్య గడువు countdown | `{"title":"TSPSC దరఖాస్తు","date":"2026-10-15T17:00:00+05:30"}` |
| `studentup_house_ads` | house/sponsor ads (day rotation) | `[{"title":"…","desc":"…","link":"https://…","cta":"…"}]` |
| `studentup_adsense_client` | AdSense client id | `ca-pub-1234567890123456` |
| `studentup_exam_url` | పరీక్షల పోర్టల్ లింక్ | `https://exams.studentup.in` |

**Bot push (REST):** `POST /wp-json/studentup/v1/theme-data` — Application Password tho auth
(edit_posts). Idi lekapote: WP root lo `/data/breaking.json` file pettandi (theme 10 నిమిషాల
transient cache tho chadivi chupistundi).

## Em unnayi (files)

```
style.css            design tokens + anni components (Telugu fonts, dark mode, responsive)
front-page.php       home order: used-strip → ప్రకటన → hero+countdown → బ్రేకింగ్ → grid+chips
header.php           logo/menu/actions/mobile panel + టికర్
footer.php           footer + కుడి వైపు నిలువుగా socials
single.php           article + ads + share + related + trust note
index/archive/search/page/404/searchform.php
inc/breaking.php     feed (option → transient file → honest empty) + REST push
inc/ads.php          AdSense unit + house ads (SPONSORED label, rel=sponsored)
inc/template.php     cards, proof tiles, countdown, breadcrumbs (Rank Math compat), menu fallback
assets/js/studentup.js  dark mode, mobile panel, chips filter, countdown
theme.json           block editor colors/Typography (navy/blue/orange)
```

## Nijam (honest)

- Ivi **Preview design = production design**. Chinnavi matrame marutayi (WP nav_menu hook, real URLs).
- **Speed:** no jQuery, 1 CSS + 1 JS, lazy images — GeneratePress kante light (custom theme,
  add-ons ledu).
- **AdSense:** SPONSORED labels + rel=sponsored + ad units ki minimum height (CLS safe).
  Auto Ads ki `functions.php` lo em ledu — AdSense ki aa pani varasam (plugin leda site code).
- **Rank Math** unte breadcrumbs + meta aa plugin nunchi vasthayi (theme detect chestundi).
