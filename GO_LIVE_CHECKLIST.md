# GO-LIVE CHECKLIST (v60) — deploy cheyocha? Enti migilindi?

**Short answer: CODE ready ✅ · DEPLOY ready ✅ · 5 panulu MEE accounts lo cheyyali ⏳.**
Ee doc = okka page lo motham. Kramam ga cheyyandi.

---

## A0) ARCHITECTURE — edi ekkada run avutundi? (rendu kaavala?)

**Short answer: 🌐 WordPress = website (MilesWeb) · ⚙️ Bot + portal = engine (Oracle leda MilesWeb cron).
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
  │  EXAM PORTAL (Python) — /exam /admin     │
  │  Oracle VM WSGI  leda  MilesWeb WSGI App │
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
| **A. MilesWeb only** | WP + bot (cron) + portal (Setup Python App) anni MilesWeb lo | ₹59–180/నెల | Simple, budget — kaani cron 5-job limit + 24×7 daemon ledu (approval poll cron tho) |
| **B. MilesWeb + Oracle** ⭐ | WP = MilesWeb · bot + portal + guardian = Oracle Always Free 24×7 | ₹0 extra | **Recommended** — heavy bot runs + uptime + mee data mee control lo |
| **C. Oracle only** | WP kuda Oracle VM lo (PHP + MySQL + Caddy) | ₹0 | Server telisina vallaki — WP updates/backups meeru chuskovali |

**Frontend kuda okati select cheyandi** (rendu kaadu): studentup.in root lo **WordPress + StudentUp theme** ⭐
(v61 — `wordpress-theme/studentup-theme.zip`, install 5 నిమిషాలు) leda **static preview**
(`preview/index.html` → public_html). **WP + theme select chesthe site design = preview design**
(టికర్ · ఎక్కువగా వెతికేవి · కార్డులు · ads) kaani dynamic — bot post rasthe site automatic ga update.
Static select chesthe bot posts WP lo untayi kaani site lo kanipinchavu.

**Ippude cheyyalsina 5 steps (combo B):**
1. MilesWeb: domain + WordPress + SSL + Application Password → `.env`
2. Oracle: VM create → `bash deploy/install-vps.sh` → bot systemd timer + portal HTTPS
3. Oracle lo `.env` pettandi (Gemini · Telegram · WP creds) → `python run.py --doctor` 0 problems
4. `python run.py --check-wp` (Oracle nunchi WP ki link test) · `python run.py --guardian` 10/11
5. UptimeRobot → `https://<domain>/healthz` + roju Telegram guardian report

Detail docs: `DEPLOY_MILESWEB.md` (cPanel steps) · `DEPLOY_ORACLE_CLOUD.md` (VM + watchdog + limits) ·
`DEPLOY.md` (VPS/Docker/PaaS paths).

---

## A) Ippude ready (proof tho)

| Item | Proof |
|---|---|
| Test suites | **51/51** pass (`python run.py --test-all`) |
| Site guardian | **`python run.py --guardian`** — site/UI/SEO/ads/feed/storage/theme 12 checks (11 ok · 1 owner-pending) |
| Readiness score | **`python run.py --readiness`** — **100/100** · 25/25 system checks · 8 owner-pending |
| Production check | **11/11** pass (`python run.py --production-audit`) |
| Browser runtime | **122/122** checks (`node tests/runtime/jsdom_runtime_test.js`) |
| Deploy check | 8 ok · 4 warn · 0 fail (`python run.py --deploy-check`) |
| Website | 17 categories · 143 sources · 11,192 keywords · menu + chips |
| Ads | AdSense gate · sponsor console · rate card · house ads |
| Safety | QA 80 · originality 72% · manual approval · corrections email |
| Crash-proof | systemd restart · 2-min watchdog · backups · /healthz |

⛔ Deploy ni aaputhunna vi (nijam): **WordPress creds · Gemini key · Telegram token** ledu +
`studentup.in` registrations mee daggara ledu. Code valla kaadu — accounts valla.

---

## B) MEE panulu (5 — order lo)

- [ ] **1. Domain + hosting** — studentup.in (leda mee peru) + MilesWeb cPanel plan (₹59–180/నెల).
      → WordPress install + SSL (Let's Encrypt) ON.
- [ ] **2. WordPress setup** — Rank Math, IndexNow; theme install (**v61**:
      `python tools/build_wp_theme.py` → zip → Appearance → Themes → Upload → Activate);
      `wp-admin → Users → Application Passwords` → app password create cheyyandi.
- [ ] **2a. Google Search Console + GA4** — GSC lo domain verify → `sitemap.xml` submit;
      GA4 property create → measurement ID. (GSC = rankings data, GA4 = traffic data —
      bot ki `--gsc` CSV tho ee data tho priority decide chestundi.)
- [ ] **2b. Website options** — WP Admin → **StudentUp** menu → tabs (Ads · Socials ·
      Content · Advanced) lo mee WhatsApp/Telegram/Instagram/YouTube, exam portal URL,
      AdSense client + slots, sticky ad ON/OFF pettandi. Bot `--push-theme-data` tho
      JSON fields (breaking/house/proof/deadline) automatic ga sync avutayi.
- [ ] **2c. AdSense CMP (EEA/UK consent)** — AdSense → **Privacy & messaging** → GDPR/CCPA
      message + Google-certified CMP **ON**. (Ee step lekapote EEA/UK users ki ads
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

**1) Website → MilesWeb** (`DEPLOY_MILESWEB.md`)
```bash
# cPanel → Setup Python App (Python 3.11, app root examportal, URI /exam)
# Git Version Control → clone → pip install -r requirements.txt
python run.py --production-audit && python run.py --check-wp
```
**2) Engine (portal + bot + watchdog) → Oracle VM** (`DEPLOY_ORACLE_CLOUD.md`)
```bash
sudo bash deploy/install-vps.sh          # systemd + Caddy + venv
sudo systemctl enable --now exam-portal studentup-bot.timer su-watchdog.timer
curl -s https://exam.studentup.in/healthz   # {"status":"ok"}
```
**3) Deploy tarvata verify**
```bash
python run.py --production-audit     # 0 blockers
python run.py --deploy-check         # 0 fail
python run.py --google-audit https://studentup.in
curl -s https://studentup.in/ads.txt      # ads.txt host ayyindi leda chudandi
python tools/revenue_estimate.py --views 10000        # leads/premium kalipi
python tools/revenue_estimate.py --views 10000 --ads-only   # ads-only ladder
```
UptimeRobot → `https://exam.studentup.in/healthz` (5-min ping) — watchdog ki rendo kanna.

---

## D) Aa tarvata: Roju nadavalsina pani (automatic)

| Time | Pani | Evaru |
|---|---|---|
| 08:00 | 3–5 posts (17 pillars) → Telegram ✅/🗑️ | bot + **mee approval** |
| 09:00, 18:00 | Current affairs + breaking refresh | auto |
| Roju | Poll + quiz update + auto-refresh purana posts | auto |
| Roju | 📞 లీడ్లు చూసి 2 అమ్మకాల మెసేజ్‌లు (కళాశాల/కోచింగ్) పంపండి | **మీరు (15 నిమిషాలు)** |
| Roju 10:00 | **ad advisor** — e network ki eppudu apply cheyyali (kotha milestone ki Telegram) | auto |
| నెలకు ఒకసారి | GA4 CSV export → `python run.py --ad-advisor --traffic-csv ga4.csv` | మీరు (2 నిమిషాలు) |
| 2 nimishalku okasari | Health check → crash ayite restart + alert | watchdog |
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
* House ads = ₹0 (mana quiz/exam ki traffic).
* ⚠️ Ivi benchmarks — **AdSense approval / ranking / revenue గ్యారంటీ కావు**.

---

## F) Cheyyakudadu (once and for all)
Clickbait titles · fake clicks · popups · "Google tricks" · ad ni content laaga dhaachadam ·
job guarantee promises (advertisers kuda). Ivi AdSense ban + trust damage.

*Last updated: v60 (2026-09-18) · 45/45 suites · 122/122 runtime · 11/11 production checks*
