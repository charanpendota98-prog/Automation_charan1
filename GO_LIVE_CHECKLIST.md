# GO-LIVE CHECKLIST (v53) — deploy cheyocha? Enti migilindi?

**Short answer: CODE ready ✅ · DEPLOY ready ✅ · 5 panulu MEE accounts lo cheyyali ⏳.**
Ee doc = okka page lo motham. Kramam ga cheyyandi.

---

## A) Ippude ready (proof tho)

| Item | Proof |
|---|---|
| Test suites | **41/41** pass (`python run.py --test-all`) |
| Production check | **11/11** pass (`python run.py --production-audit`) |
| Browser runtime | **108/108** checks (`node tests/runtime/jsdom_runtime_test.js`) |
| Deploy check | 8 ok · 4 warn · 0 fail (`python run.py --deploy-check`) |
| Website | 16 categories · 129 sources · 10,682 keywords · menu + chips |
| Ads | AdSense gate · sponsor console · rate card · house ads |
| Safety | QA 80 · originality 72% · manual approval · corrections email |
| Crash-proof | systemd restart · 2-min watchdog · backups · /healthz |

⛔ Deploy ni aaputhunna vi (nijam): **WordPress creds · Gemini key · Telegram token** ledu +
`studentup.in` registrations mee daggara ledu. Code valla kaadu — accounts valla.

---

## B) MEE panulu (5 — order lo)

- [ ] **1. Domain + hosting** — studentup.in (leda mee peru) + MilesWeb cPanel plan (₹59–180/నెల).
      → WordPress install + SSL (Let's Encrypt) ON.
- [ ] **2. WordPress setup** — Rank Math, GA4, IndexNow; `wp-admin → Users → Application
      Passwords` → app password create cheyyandi.
- [ ] **2b. AdSense approve ayyaka** — `.env` lo `ADSENSE_CLIENT_ID=ca-pub-…` petti
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
| 08:00 | 3–5 posts (16 pillars) → Telegram ✅/🗑️ | bot + **mee approval** |
| 09:00, 18:00 | Current affairs + breaking refresh | auto |
| Roju | Poll + quiz update + auto-refresh purana posts | auto |
| Roju | 📞 లీడ్లు చూసి 2 అమ్మకాల మెసేజ్‌లు (కళాశాల/కోచింగ్) పంపండి | **మీరు (15 నిమిషాలు)** |
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

*Last updated: v55 (2026-09-18) · 41/41 suites · 108/108 runtime · 11/11 production checks*
