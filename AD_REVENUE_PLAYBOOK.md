# AD REVENUE PLAYBOOK (v52) — highest revenue, policy-safe

Ee doc = "adi best?" + "highest revenue ads" + "mana valu kuda post pettelaga" +
"private ads kuda pettelaga" — anni answers okka chota.

---

## 0) BEST OPTION (recommendation)

| Priority | Setup | Enduku best |
|---|---|---|
| ⭐ **Recommended** | **MilesWeb** (website + WordPress) **+ Oracle Cloud Always Free VM** (bot + watchdog + guardian) | Website fast & cheap; bot 24×7 + auto-heal + mee data mee control. Rendu kalipi ~₹0–500/నెల |
| Budget-only | MilesWeb lone anni (WP + bot cron + approval cron) | Okka bill, okka panel — bot heavy runs lo slow avvochu |
| Scale (traffic spike) | Cloudflare free CDN + MilesWeb cache | Bot cron schedules ki move cheyyali (heavy runs off-peak) |

Reason: website = static/WP (MilesWeb perfect) · bot = timers + cron
+ watchdog (VM perfect). Rendu dochulu: **motham deploy = website MilesWeb, engine Oracle**.

## 0.1) Live calculator — "10k views vasthe entha?"

```bash
python tools/revenue_estimate.py --views 10k     # leda 50k / 1l / 3l / 1m
```
10,000 నెలవారీ views → **₹400–₹4,200/నెల** (AdSense ₹400–₹2,500 + 0–1 sponsor ₹0–₹2,700).
1,00,000 views → ₹5,000–₹23,100. Tool rate card ni LIVE advertise page nunchi chaduvutundi
(prices okate chota untayi), house ads ni revenue lo count cheyyadu.

## 0.2) 3 స్థాయిలు (v54) — 'top level' ante idi

| స్థాయి | ఎలా | 10k views/నెల | 1L views/నెల |
|---|---|---|---|
| 1) BASELINE | AdSense మాత్రమే | ₹400–₹2,500 | ₹4,000–₹25,000 |
| 2) STANDARD | + స్పాన్సర్ స్లాట్లు (rate card) | ₹400–₹4,200 | ₹5,000–₹23,100 |
| 3) **ADVANCED** | + **లీడ్లు** (₹150–₹400/లీడ్) + స్పాన్సర్డ్ ఆర్టికల్స్ (₹8,000–₹15,000) + బ్రాడ్‌కాస్ట్ + అఫిలియేట్ | **₹16,050–₹64,350** | **₹60,000+** |

3వ స్థాయి = **manual ga nadapalsina revenue**: website lead form nunchi వచ్చిన
విద్యార్థి enquiries (పేరు + నంబర్) కళాశాలలకు/కోచింగ్‌లకు అమ్మడం. Setup ippude
ready (ఫారం + admin panel + CSV) — kaavalsindi **2 అమ్మకాల మెసేజ్‌లు రోజూ**
(SALES_KIT_ADVERTISERS.md lo టెంప్లేట్లు).

## 0.3) ADS-ONLY revenue (v55) — 'ads tho entha vastundi?'

```bash
python tools/revenue_estimate.py --views 100000 --ads-only
```

| views/నెల | AdSense (₹40–250 RPM) | Sponsor slots | **మొత్తం** |
|---|---|---|---|
| 10,000 | ₹400–₹2,500 | ₹0–₹2,700 | ₹400–₹4,200 |
| 50,000 | ₹2,000–₹12,500 | ₹1,000–₹8,100 | ₹3,000–₹15,600 |
| 1,00,000 | ₹4,000–₹25,000 | ₹1,000–₹8,100 | ₹5,000–₹23,100 |
| 3,00,000 | ₹12,000–₹75,000 | ₹3,000–₹16,200 | ₹15,000–₹61,200 |
| 10,00,000 | ₹40,000–₹2,50,000 | ₹6,000–₹32,400 | ₹46,000–₹1,82,400 |

**Idi maths: ads revenue = views × RPM.** Views perugakunda ads-only ceiling peragadu.
Per-view value (RPM) penche levers — anni ippude siddham:

| Lever | Status |
|---|---|
| **ads.txt** (buyers idi chustaru; lekapote demand takkuva) | ✅ auto (`python tools/build_policy_pages.py`) — approval tarvata line fill |
| Auto Ads loader (anchor/in-feed formats) | ✅ `ADSENSE_AUTO_ADS=1` |
| Viewability (sticky sidebar + in-feed + leaderboard) | ✅ |
| Page speed (fast load = ekkuva viewable impressions) | ✅ static site |
| Session depth (ఒక్క విజిట్‌లో ఎక్కువ పేజీలు: hubs, quiz, daily question, related) | ✅ |
| High-CPC pillars (Govt jobs, Results, Current affairs, Scholarships) | ✅ 17 pillars |
| Tier-1 / NRI-దేశీ ట్రాఫిక్ (విదేశీ ఉద్యోగాలు, IELTS, visa) | ✅ v58 pillar LIVE (roju 1–2 posts) |
| Topa ki 2 ads cap (policy + UX protect) | ✅ |

**Mana site ki asalu answer:** ads-only tho 1 లక్ష views = ₹5,000–₹23,100/నెల.
Adi automatic ga peragali ante **posts + SEO + shares** (roju 3–5 posts bot chestundi) —
traffic ravali. Per-view value penchalante leads/premium (`--views` chudandi, 4–5×).

## 0.4) Networks (v56) — '50k tarvata 2x avutaya?'

```bash
python tools/ad_network_plan.py --views 50k --tier1 0.30
```
| Network | Minimum | Uplift nijam |
|---|---|---|
| AdSense | trafic minimum ledu | baseline |
| Ezoic / header bidding | ~1k sessions | **+30–70%** (automatic 2x kaadu) |
| Monumetric | 10k pageviews | +30–60% |
| Raptive | 25k pageviews + ~50% Tier-1 | premium band (exclusive) |
| Mediavine | 50k **sessions** + Tier-1 majority | 2–4x (exclusive) |

**Rendu networks kalipi 2x avvavu** (okate demand koraku poti). 2x ante Tier-1 ట్రాఫిక్ +
premium network + direct sponsors. Full detail: `AD_NETWORKS_PLAN.md`.

## 0.5) AUTO ADVISOR (v57) — eppudu apply cheyyali ani bot cheptundi

```bash
python run.py --ad-advisor                                  # ippudu enti eligible
python run.py --ad-advisor --traffic-csv ga4.csv            # GA4 export import
python run.py --ad-advisor --traffic-views 25k --tier1 0.5  # manual
```
* Traffic data: `logs/traffic.json` (GA4 CSV) leda `.env AD_MONTHLY_VIEWS`
* Bot roju **ADVISOR_HOUR (10:00)** tarvata okkasari run avutundi; kotha network
  threshold cross ayyaka **Telegram alert** (milestone ki okkasari)
* `ADSENSE_APPROVED=1` ayyaka checklist alert (ads.txt status tho saha)
* **Publisher ID:** AdSense `ca-pub-…` **mareadu** (account ki okate id) · Ezoic ade
  account vaadutundi · Raptive/Mediavine exclusive — vaalla tags, AdSense line thiyyali

## 1) Revenue lines (4 — anni ippude ready)

| # | Line | Status | Ekkada control |
|---|---|---|---|
| 1 | **Google AdSense** | `ADSENSE_APPROVED=0` (approval tarvata auto ON); max 1 personal ad/post | `.env` |
| 2 | **Direct sponsors** (private ads) | ✅ LIVE — rate card + booking page | `pages/advertise.html` + admin console "📢 ప్రకటనలు" |
| 3 | **House ads** (mana sonta promos) | ✅ LIVE — slot khali ga undadu | `ads/house.json` |
| 4 | **Sponsor packages** (full package ₹8,000/నెల) | ✅ rate card ready | advertise page |
| 5 | **లీడ్ జనరేషన్** (విద్యార్థి enquiries → కళాశాలలు/కోచింగ్) | ✅ లైవ్ (ఫారం + admin + CSV) | `📞 లీడ్లు` panel |
| 6 | **స్పాన్సర్డ్ ఆర్టికల్స్** (₹8,000–₹15,000/పాజ్) | ✅ listed | advertise page |

### Rate card (site lo live)
| Slot | ఎక్కడ | నెలకు |
|---|---|---|
| Top leaderboard | home header kinda (andariki) | ₹4,000 |
| Mid-article | prathi article quick-answer tarvata | ₹3,500 |
| In-feed card | news grid madhyalo | ₹3,000 |
| Sidebar sticky | desktop pakkana | ₹2,000 |
| Policy pages inline | About/Contact/Editorial | ₹1,000 |
| **Full package** | anni slots + bot articles | **₹8,000** |

## 2) Private ads (sponsors) — end-to-end flow

```
Advertiser → pages/advertise.html → email/Telegram (checklist: peru, pattanam, slot, nelalu, link, banner)
   ↓
Owner → admin console → "📢 ప్రకటనలు" → add (type: college_banner|coaching|shop|service|sponsorship)
   ↓
ads/inventory.json → website slots + bot articles (SPONSORED label, rel=sponsored nofollow)
   ↓
start/end dates → kaalapramanam ayyaka auto ga aagutundi
```
* **Private ad = paid sponsor ad** → eppudu SPONSORED label + `rel="sponsored nofollow"` + `utm_*` tag
  (GA4 lo ee campaign clicks chudochu).
* Google policy safe: max 2/post, link ki 150-char dooram, CLS-safe, popup ledu.

## 3) House ads (mana valu kuda post pettelaga) — idi kotha feature

```
ads/house.json → StudentUp sonta promos (services · daily quiz · daily question)
Kaani: SPONSORED label VEYYAMU — "StudentUp · మా సేవ" ani verega label
Paid sponsor unte → sponsor FIRST (rotation + demo/real priority)
House ads kuda rotation lo turn teesukuntayi (ads/rotation.json)
Off cheyyali ante: .env → HOUSE_AD_ENABLED=0
```
Ante: **edi miss avvadu, slot khali ga kanipinchadu, kaani nijam kadu ani cheppamu** — paid ad ki
SPONSORED, mana ad ki "StudentUp సేవ".

## 4) "Anni generate ayyaaya?" — status board

| Item | Status |
|---|---|
| 17 content pillars · 143 sources · 11,192 keywords (incl. విదేశీ/గల్ఫ్ = Tier-1 line) | ✅ |
| Rank Math fields + canonical + JSON-LD + IndexNow | ✅ |
| Manual gate (draft → Telegram ✅) + QA 80 + originality 72% | ✅ |
| Daily question + quiz (server lekunda) + admin ads (WP) | ✅ |
| Category menu (TS/AP/Central/Walk-in/Software/Private/Hall tickets/Results…) | ✅ |
| Policy pages (About/Contact/Privacy/Disclaimer/Editorial) + robots/sitemap/favicon | ✅ |
| **Advertise page + rate card + booking flow** | ✅ (v52) |
| **House ads (mana sonta ads)** | ✅ (v52) |
| Watchdog auto-heal + backups | ✅ |
| AdSense ON | ⏳ `ADSENSE_APPROVED=1` pettagane (approval tarvata) |
| Oracle VM + MilesWeb accounts, domain, GA4, Search Console | ⏳ mee accounts lo (nen guide cheyyagalanu) |

## 5) Highest revenue — nijamaina levers (order lo)

1. **Sponsor sales** (highest ₹ per slot) — advertise page + local outreach (colleges, coaching,
   stationery, hostels, hospitals, banks, mobile shops). 1 full package = ₹8,000/నెల.
2. **AdSense** — approve ayyaka auto; jobs/scholarships pages ki CPC ekkuva.
3. **Repeat traffic** — daily question, daily current affairs, auto-refresh → sessions per user ↑ → ad
   impressions ↑.
4. **Refresh + IndexNow** — purana posts malli crawl → impressions ↑.
5. **House ads** — traffic ni quiz/services/question ki pampistundi (mana own funnel).

⛔ **Cheyyakudadu (once and for all):** clickbait titles, fake clicks, popup/interstitial,
"Google tricks", ad ni content laaga dhaachadam, incentive clicks. Ivi AdSense ban + reputation damage.

⚠️ **Nijam:** evi rank/revenue guarantee cheyyavu. Ee setup mistakes taggistundi + revenue
opportunities add chestundi. Real numbers mee AdSense / Search Console / sponsor contracts lo ne.

---
*Last updated: v52 (2026-09-18) · 38/38 test suites · 102/102 runtime checks*
