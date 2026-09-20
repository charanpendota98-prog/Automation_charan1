# GO-LIVE CHECKLIST (v60) — deploy cheyocha? Enti migilindi?

**Short answer: CODE ready ✅ · DEPLOY ready ✅ · 5 panulu MEE accounts lo cheyyali ⏳.**
Ee doc = okka page lo motham. Kramam ga cheyyandi.

---

## A0) ARCHITECTURE — edi ekkada run avutundi? (rendu kaavala?)

**Short answer: 🌐 WordPress = website (MilesWeb) · ⚙️ Bot = engine (Oracle leda MilesWeb cron).
Rendu "support" kaadu — rendu okate system lo rendu roles. Bot ki WordPress tho link = HTTPS REST API.**

```
        విద్యార్థులు / మీరు (browser)
                  │  https://studentup.in
                  ▼
  ┌──────────────────────────────────────────┐
  │  studentup.in  ── MilesWeb public face ──│
  │  WordPress + Rank Math + AdSense ads     │
  │  (posts · pages · ads.txt · sitemap.xml) │
  └───────────────┬──────────────────────────┘
                  │  WordPress REST API  (https://studentup.in/wp-json/wp/v2)
                  │  Application Password tho — internet meeda link, folder kaadu
                  ▼
  ┌──────────────────────────────────────────┐
  │  BOT (Python) ── engine room ────────────│
  │  research → fact-guard → draft → publish │
  │  radar (6h) · breaking feed · guardian   │
  │  ── EKKADA run avvali? okka chota: ──    │
  │    (a) Oracle VM 24×7 systemd  ⭐ best   │
  │    (b) MilesWeb cron (5-job limit)       │
  └──────────────────────────────────────────┘
                  ▲
  ┌───────────────┴──────────────────────────┐
  │  APPROVALS — Telegram ✅/🗑️ (cron poll)  │
  │  Oracle daemon leda MilesWeb cron */5    │
  └──────────────────────────────────────────┘
```

### Motham chain (links anni ela kalisi pani chestayi)

```
GitHub repo (mee code)  →  server lo git pull  →  cron/systemd bot ni run chestundi
   →  bot sources chadivi post rasi  →  WP REST API tho studentup.in lo draft  →
   →  Telegram lo ✅/🗑️  →  mee approval  →  post live  →  ads.txt/sitemap WP root lo serve
   →  GA4 + Search Console + AdSense ee domain ni track chestayi
```

⛔ **Okate trap undi:** bot ni **rendu chotla** schedule cheyyakandi (MilesWeb cron + Oracle timer
rendu) — **duplicate posts** vasthayi. Bot ki okka home select cheyandi; migilinadi backup ga undochu
(bot off, uptime monitor matrame).

### Rendu kaadu — 3 combos (okati select cheyandi)

| Combo | Ekkada enti | Kharchu | Evariki |
|---|---|---|---|
| **A. MilesWeb only** | WP + bot (cron) + approvals (`--approval-poll` cron) anni MilesWeb lo | ₹59–180/నెల | Simple, budget — approvals ~5 min late (cron rhythm), daemon ledu |
| **B. MilesWeb + Oracle** ⭐ | WP = MilesWeb · bot + guardian + watchdog = Oracle Always Free 24×7 | ₹0 extra | **Recommended** — heavy bot runs + uptime + mee data mee control lo |
| **C. Oracle only** | WP kuda Oracle VM lo (PHP + MySQL + Caddy) | ₹0 | Server telisina vallaki — WP updates/backups meeru chuskovali |

**Frontend kuda okati select cheyandi** (rendu kaadu): studentup.in root lo **WordPress + StudentUp theme** ⭐
(v61 — `wordpress-theme/studentup-theme.zip`, install 5 నిమిషాలు) leda **static preview**
(`preview/index.html` → public_html). **WP + theme select chesthe site design = preview design**
(టికర్ · ఎక్కువగా వెతికేవి · కార్డులు · ads) kaani dynamic — bot post rasthe site automatic ga update.
Static select chesthe bot posts WP lo untayi kaani site lo kanipinchavu.

**Ippude cheyyalsina 5 steps (combo B):**
1. MilesWeb: domain + WordPress + SSL + Application Password → `.env`
2. Oracle: VM create → `bash deploy/install-vps.sh` → bot systemd timer + watchdog timer
3. Oracle lo `.env` pettandi (Gemini · Telegram · WP creds) → `python run.py --doctor` 0 problems
4. `python run.py --check-wp` (Oracle nunchi WP ki link test) · `python run.py --guardian` 10/11
5. UptimeRobot → `https://<domain>/` (5-min ping) + roju Telegram guardian report

Detail docs: `DEPLOY_MILESWEB.md` (cPanel steps) · `DEPLOY_ORACLE_CLOUD.md` (VM + watchdog + limits) ·
`DEPLOY.md` (VPS/Docker/PaaS paths).

---

## A) Ippude ready (proof tho)

| Item | Proof |
|---|---|
| Test suites | **71/71** pass (`python run.py --test-all`) |
| Site guardian | **`python run.py --guardian`** — site/UI/SEO/ads/feed/storage/theme 12 checks (11 ok · 1 owner-pending) |
| Readiness score | **`python run.py --readiness`** — **100/100** · 27/27 system checks · 10 owner-pending |
| Production check | **11/11** pass (`python run.py --production-audit`) |
| Browser runtime | **164/164** checks (`node tests/runtime/jsdom_runtime_test.js`) |
| Public surface | developer/proof text **ledu** — `python run.py --guardian` → `counts_sync` · dev archive `docs/design-archive/` (website meeda serve avvadu) |
| Business deal | no public rate card — prices live in `autoblog/rate_card.py`, print with `python run.py --rate-card` and negotiate personally |
| Contact routes | set `SOCIAL_WHATSAPP` + `SOCIAL_TELEGRAM` in `.env` → `python run.py --push-theme-data` (site WhatsApp boxes + rail follow it) |
| Qualification filter | theme `inc/qual-filter.php` — post save tho automatic tags + `wp studentup-qual-backfill` (purana posts) + bot `autoblog/qual.py` meta; proof: `python tests/v72_test.py` |
| Install as an app | `preview/manifest.webmanifest` + `preview/sw.js` · theme `?studentup_sw=1` (root-scope SW, server config avasaram ledu) + install prompt |
| Site copy clean | బ్రేకింగ్/internal metrics/demo maatalu public lo levu — `python run.py --guardian` → `first_look_ui` |
| Deploy check | 9 ok · 3 warn · 0 fail (`python run.py --deploy-check`) |
| Website | 17 categories · 143 sources · 11,192 keywords · menu + chips |
| Ads | AdSense gate · sponsor inventory · rate card · house ads |
| Safety | QA 80 · originality 72% · manual approval · corrections email |
| Crash-proof | systemd timers · 2-min watchdog (site+bot+TLS) · backups · homepage ping |

⛔ Deploy ni aaputhunna vi (nijam): **WordPress creds · Gemini key · Telegram token** ledu +
`studentup.in` registrations mee daggara ledu. Code valla kaadu — accounts valla.

---

## B) MEE panulu (5 — order lo)

- [ ] **1. Domain + hosting** — studentup.in (leda mee peru) + MilesWeb cPanel plan (₹59–180/నెల).
      → WordPress install + SSL (Let's Encrypt) ON.
- [ ] **2. WordPress setup** — Rank Math; theme install (**v74**: theme **1.7.2** —
      `python tools/build_wp_theme.py` → zip → Appearance → Themes → Upload → Activate);
      `wp-admin → Users → Application Passwords` → app password create cheyyandi.
      **v68**: IndexNow key file ni **theme ne serve chestundi** (`/<key>.key`) — cPanel lo
      upload cheyyalsina pani ledu. Key: `python run.py --index-key-gen` → `.env` →
      `python run.py --push-theme-data`.
- [ ] **2a. Google Search Console + GA4** — GSC lo domain verify → `sitemap.xml` submit;
      GA4 property create → measurement ID. (GSC = rankings data, GA4 = traffic data —
      bot ki `--gsc` CSV tho ee data tho priority decide chestundi.)
- [ ] **2b. Website options** — WP Admin → **StudentUp** menu → tabs (Ads · Socials ·
      Content · Advanced) lo mee WhatsApp/Telegram/Instagram/YouTube,
      AdSense client + slots, sticky ad ON/OFF pettandi. Bot `--push-theme-data` tho
      JSON fields (breaking/house/indexnow) automatic ga sync avutayi.
- [ ] **2c. AdSense CMP (EEA/UK consent)** — AdSense → **Privacy & messaging** → GDPR/CCPA
      message + Google-certified CMP **ON**. Theme lo **Consent Mode v2** (v66) already ON:
      EEA/GB/CH ki ad_storage/ad_user_data/ad_personalization **denied** default, mee CMP
      snippet sattinappudu `consent_cmp_id` option tho message banner (WP Admin → StudentUp).
      (Ee step lekapote EEA/UK users ki ads
      chupinchadu — Google rule; India ki impact ledu kaani overseas traffic ki important.)
- [ ] **2d. 25k pageviews tarvata** — `python tools/ad_network_plan.py --views 50k --tier1 0.3`
      → Raptive/Ezoic ki apply (detail: AD_NETWORKS_PLAN.md). Partner lines ni
      `ads/ads_txt_extra.txt` lo paste chesi `python tools/build_policy_pages.py` run cheyyandi.
- [ ] **3b. Pin-to-pin gate + trends** — prathi post ki certificate
      (`output/certificates/`) automatic ga untundi; critical fail unte publish aagutundi
      (`PIN_GATE_BLOCK=1`). `python run.py --pin-check` tho gate proof;
      `python run.py --trends --trends-queue` tho trending topics queue (radar lo daily auto).
- [ ] **2e. AdSense approve ayyaka** — `.env` lo `ADSENSE_CLIENT_ID=ca-pub-…` petti
      `python tools/build_policy_pages.py` run cheyyandi → **`ads.txt` automatic ga live** avutundi
      (idi lekapote konni ads rakavu → RPM takkuva). Tarvata `ADSENSE_APPROVED=1`.
- [ ] **2f. Instant indexing (v68 — trending ki)** — publish ayyaka URL ni ventane
      search engines ki notify:
      · **IndexNow** (Bing/Yandex): `python run.py --index-key-gen` → `.env INDEXNOW_KEY=…`
        → `python run.py --index-status` (verify). Key file theme serve chestundi.
      · **Google Indexing API** (JobPosting pages — Google officially support chese use case):
        Google Cloud → Service account → **Indexing API enable** → JSON key →
        `.env GOOGLE_INDEXING_SA_JSON=/opt/studentup/service-account.json` →
        **Search Console lo aa SA email ni Owner ga add cheyyandi**. Verify:
        `python run.py --index-status`.
      · Manual submit eppudaina: `python run.py --index-now https://studentup.in/<slug>/`.
      (Signing ki `cryptography` leda `openssl` — rendu lekapote automatic skip, publish aagadu.)
- [ ] **3. Gemini API key** — aistudio.google.com → API key (free tier chaalu).
- [ ] **4. Telegram bot** — @BotFather → token + mee chat id (@userinfobot).
- [ ] **5. Oracle Cloud** (recommended) — Always Free VM (2 OCPU/12GB) + SSH key.

Ee 5 tarvata → `.env` file lo pettandi (`.env.example` nunchi copy):

```bash
cp .env.example .env
# WP_USERNAME, WP_APP_PASSWORD, GEMINI_API_KEY, TELEGRAM_BOT_TOKEN,
# TELEGRAM_CHAT_ID, SITE_URL, ADSENSE_APPROVED=0 (approval tarvata 1),
# HOUSE_AD_ENABLED=1
python run.py --production-audit     # 3 blockers → 0 avvali
```

---

## C) Deploy order (2 dochulu)

**1) Website + bot → MilesWeb** (`DEPLOY_MILESWEB.md`)
```bash
# cPanel → Terminal: mkdir ~/bot → repo upload → python3 -m venv .venv → pip install
# cPanel → Cron Jobs: hourly run.py + */5 run.py --approval-poll (+ guardian/audit)
python run.py --production-audit && python run.py --check-wp
```
**2) Engine (bot + watchdog) → Oracle VM** (`DEPLOY_ORACLE_CLOUD.md`)
```bash
sudo DOMAIN=studentup.in bash deploy/install-vps.sh   # systemd timers + venv + check
sudo systemctl status studentup-bot.timer su-watchdog.timer --no-pager
```
**3) Deploy tarvata verify**
```bash
python run.py --production-audit     # 0 blockers
python run.py --deploy-check         # 0 fail
python run.py --google-audit https://studentup.in
curl -s https://studentup.in/ads.txt      # ads.txt host ayyindi leda chudandi
curl -s https://studentup.in/news-sitemap.xml | head -5   # v66: News/Discover eligibility
python tools/theme_audit.py --verbose     # v66/v67: theme mistakes 0 errors · 0 warnings
python tools/theme_audit_deep.py          # v67: deep audit (templates · security · perf · a11y · ads)
# v72 notes: qualification tags — pehli sari `wp studentup-qual-backfill --limit=500` (leda
#  wp-admin okasari open cheyandi — 20/batch automatic). బ్రేకింగ్ section kavali ante
#  StudentUp → కంటెంట్ → 'బ్రేకింగ్ న్యూస్ సెక్షన్ ON' (default OFF).
# v69 notes: theme v1.5.0 (author archive + editor styles) · `python tools/parity_audit.py` —
#  CLI ↔ docs · dead modules · preview links/meta · counts (0 errors · 0 warnings).
# v68 notes: bot + theme **code-level audit** (tools/code_audit.py) — 0 errors · 0 warnings.
#  Ee audit nijamaina bugs pattukuntundi: undefined config attr · duplicate dict key ·
#  silent `except: pass` · PHP printf arg mismatch · bot push key ↔ theme option typo ·
#  AdSense markup (data-ad-layout/fluid) · .env drift. Roju git tarvata okkasari:
#  python tools/code_audit.py
# v67 notes: theme lo security hardening ON (XML-RPC off · headers · enumeration block).
# Jetpack/old mobile apps vaadithe StudentUp → Advanced → Security hardening OFF cheyandi.
# Comments: StudentUp → Advanced → కామెంట్లు ON/OFF (default ON — engagement + freshness).
python run.py --readiness | head -30      # v66: ads/consent/audit checks kalisi 100/100
python tools/revenue_estimate.py --views 10000        # leads/premium kalipi
python tools/revenue_estimate.py --views 10000 --ads-only   # ads-only ladder
```
UptimeRobot → `https://studentup.in/` (5-min ping) — watchdog ki rendo kanna.

---

## D) Aa tarvata: Roju nadavalsina pani (automatic)

| Time | Pani | Evaru |
|---|---|---|
| 08:00 | 3–5 posts (17 pillars) → Telegram ✅/🗑️ | bot + **mee approval** |
| 09:00, 18:00 | Current affairs + breaking refresh | auto |
| Roju | Daily question + quiz (server lekunda) + auto-refresh purana posts | auto |
| Roju | 📞 WhatsApp లీడ్లు చూసి 2 అమ్మకాల మెసేజ్‌లు (కళాశాల/కోచింగ్) పంపండి | **మీరు (15 నిమిషాలు)** |
| Roju 10:00 | **ad advisor** — e network ki eppudu apply cheyyali (kotha milestone ki Telegram) | auto |
| నెలకు ఒకసారి | GA4 CSV export → `python run.py --ad-advisor --traffic-csv ga4.csv` | మీరు (2 నిమిషాలు) |
| 2 nimishalku okasari | Website + bot + TLS check → alert | watchdog |
| 02:00 | Backup + media prune | cron |

---

## E) Money — "10k views vasthe entha vasthundi?"

**Nijam ga ₹400 – ₹4,200/నెల** (AdSense ₹400–₹2,500 + 0–1 sponsor ₹0–₹2,700).
Detail: `python tools/revenue_estimate.py --views 10k`

| నెలవారీ views | AdSense | Direct sponsors | మొత్తం అంచనా |
|---|---|---|---|
| 10,000 | ₹400–₹2,500 | ₹0–₹2,700 | **₹400–₹4,200** (advanced: ₹16,050+) |
| 50,000 | ₹2,000–₹12,500 | ₹1,000–₹8,100 | ₹3,000–₹15,600 |
| 1,00,000 | ₹4,000–₹25,000 | ₹1,000–₹8,100 | ₹5,000–₹23,100 |
| 3,00,000 | ₹12,000–₹75,000 | ₹3,000–₹16,200 | ₹15,000–₹61,200 |
| 10,00,000 | ₹40,000–₹2,50,000 | ₹6,000–₹32,400 | ₹46,000–₹1,82,400 |

* AdSense RPM band ₹40–₹250/1000 views (Indian jobs/education niche, 2026 benchmarks).
* Real ga ₹ varaku ravali ante **direct sponsors** (rate card) — adi 4–5× ekkuva.
* **1 lakh views** daggara revenue break-out avvala: daily ~3,300 views + 2–3 sponsors.
* House ads = ₹0 (mana quiz/services ki traffic).
* ⚠️ Ivi benchmarks — **AdSense approval / ranking / revenue గ్యారంటీ కావు**.

---

## F) Cheyyakudadu (once and for all)
Clickbait titles · fake clicks · popups · "Google tricks" · ad ni content laaga dhaachadam ·
job guarantee promises (advertisers kuda). Ivi AdSense ban + trust damage.

*Last updated: v91 (2026-09-20) · 71/71 suites · 164/164 runtime · 11/11 production checks · theme v1.9.2 · v90 notifications + v91 Telegram tools*
