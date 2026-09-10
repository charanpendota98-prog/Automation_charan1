# 🚀 START HERE — studentup.in Founder Manual (v23)
### "Nenu em cheyali?" — ee file matrame chalu. Settings anni bot automatic ga set chesthundi.

---

##  Divide cheddam: enti BOT chesthundhi, enti MEERU cheppali

| ✅ BOT (code) automatic ga chesthundhi | 👤 MEERU cheppalsinadi (vastha 5 items matrame!) |
|---|---|
| Daily original Telugu articles (research → write → SEO → image) | **1. Gemini keys** — aistudio.google.com nunchi 2-3 free keys → `.env` lo `GEMINI_API_KEYS=...` (429 quota fix — idi oka MUST) |
| Rank Math meta + honest strict scoring + auto-refine | **2. Server commands** — kirem block copy-paste (kirem ade) |
| WordPress SITE settings (`--setup`: tagline, timezone, comments OFF, footer menu, category SEO, favicon) | **3. AdSense signup** — adsense.google.com lo account + `--ensure-adsense` cheppina ads.txt paste (site 20+ posts taruvata APPLY) |
| Google Jobs schema, countdown, facts guard, bylines, E-E-A-T | **4. Search Console + Analytics** — Rank Math → Google Console module lo "Authenticate" click (2 min OAuth) — ee okka click tho `--gsc` loop full power |
| Radar → real news links queue (never fake news) | **5. Rozu 10 nimishalu** — Telegram approve buttons (draft mode lo unnapudu) + week ki okka saru `--gsc` CSV (optional kaani powerful) |
| Hub pages, internal links, thumbnails, IndexNow | — |

> WP admin lo meeru em settings **cheyalsidi kaadu** — `--setup` chesthundhi. Theme koncham matrame (kirem chustha).

---

## 🖌️ THEME — final answer

**Rule:** speed + readability = ranking + AdSense approval + RPM. Content posts lo unnadi — theme marchina **emi poyipokadu** (safe).

1. Ippudu mee theme fast aa check: **pagespeed.web.dev** lo `studentup.in` test → **Mobile score 80+** unte → ✅ same theme vadeyandi (font polish bot already chesthundhi — v23 `Noto Sans Telugu` auto add avutundi prathi post ki)
2. **80 kante takkuva** unte → WP Admin → Appearance → Themes → Install **"GeneratePress"** (FREE) activate cheyandi. Enduku:
   - India's top content sites (Way2Point/TV9 Telugu lanti speed profile) — CWV green
   - Almost config emi kavali (bot `--setup` thodanne anni set chesthundhi)
   - Ad units + lists + tables clean ga kanipisthayi
   - Alternative (koncham fancy features kaavali ante): **Blocksy** (free) — sticky header + news layouts
3. Theme change taruvata: Appearance → Menus lo `studentup-legal` footer menu (bot create chesindi) footer location ki assign cheyandi (okka drop-down, 30 sec) — `--setup` already attempt chesthundhi
4. Logo/favicon: `SITE_LOGO_URL=https://studentup.in/logo.png` (512×512) `.env` lo pettandi → bot favicon ga auto-set chesthundhi (Google/AdSense card lo brand kanipisthundi)

---

## 🎬 ONE-TIME DEPLOY (server SSH lo — ee order ga)

```bash
# 1. code
git pull
# 2. keys (.env edit: nano .env)
#    GEMINI_API_KEYS=key2,key3          ← MUST (429 fix)
#    SITE_LOGO_URL=https://studentup.in/logo.png
# 3. checks + auto-setup
.venv/bin/python run.py --doctor
.venv/bin/python run.py --setup --dry-run   ← report chudandi
.venv/bin/python run.py --setup             ← auto-fixes
.venv/bin/python run.py --ensure-adsense    ← 5 policy pages
.venv/bin/python run.py --rebuild-hubs      ← authority hubs
# 4. services restart (mee systemd names)
sudo systemctl restart autoblog.timer
# 5. ⛔ blockers echadu unte → aa admin fix chesi --setup malli run
```

---

## 📅 ROZU / VARAM Routine

| Frequency | Em | Time |
|---|---|---|
| Rozu | Telegram drafts approve (⛔ Fact flags unte mathrame chaduvandi — bot flags chesthundhi) | 5-10 min |
| Varam | GSC → Performance → Queries → Export CSV → `run.py --gsc file.csv` (queue auto-priority) | 5 min |
| Nela | `--setup --dry-run` (blockers audit) + `--rebuild-hubs` | 10 min |
| Nela | Coaching centers 2-3 ki email (featured listing ₹3-8k/month deal — 5th revenue stream; `FEATURED_CTA_HTML` lo paste) | 20 min |

**AdSense approve ayyaka:** `.env` lo `DEFAULT_POST_STATUS=publish` petti auto-publish ki switch cheyandi (before that — human review = Google/AdSense trust ✅).

---

## 💰 Money — honest plan (expectations realistic ga)

| Phase | Timeline | Expected | Chese padaluku |
|---|---|---|---|
| Foundation | Month 1-2 | ₹0 — traffic ledu | Bot rozu 5-8 posts; hubs; 20+ posts reach. **Apply cheyakudadu AdSense ki inka** |
| Traction | Month 2-4 | Hall-ticket/result spikes tho first 1k-5k/day views | Exams calendar pramukam ga publish avuthundi. AdSense APPLY (pages+menu+originality ready) |
| Monetize | Month 4-8 | AdSense ₹150-800/day (IN education RPM ₹15-40 moderate — volume game) | Auto ads ON kaani placement review. Session depth = internal links already wired |
| Diversify | Month 6+ | Coaching leads + featured listings + **Telegram premium alerts** (₹99/mo "job alerts" — owned channel, Google-dependent kaadu) | Channel growth = site footer + post end CTA (bot already telegram_cta block vesthundhi) |

> Single AdSense meeda 100% dependence = one policy review distance. Playbook rule: **5 streams** — bot + routine lo anni wired unnayi.

---

## 🔥 Viral levers (top-site pattern — bot lo automatic)
1. **Result/Hall-ticket = instant share** — deadline countdown + "N days left 🔥" badge (already in every post)
2. **Cut-off trend tables** — niche lo ekkuva re-shared content; keyword engine gap-targets veetini cover chesthundhi
3. **WhatsApp forward-friendly** — quick answer box first 40 words lo complete answer (forward chesinappudu adhe kanipisthundi)
4. **Colloquial headlines** — "Apply ela cheyali?" style (student bhasha) = CTR
5. **Bylines + corrections** — trust; Google News Publisher lo apply cheyandi (month 2: publishercenter.withgoogle.com — feed `https://studentup.in/feed/`) → Discover traffic = free rocket 🚀
6. **Telegram channel** — `TELEGRAM_CHANNEL_CHAT_ID` pettaka prathi published post automatic channel ki (monthly audience compound avutundi)

---

## ❓ "Asalu naku settings teliyadu" — tension enduku?
- Teliyalsinadi **emmi ledu** — anni commands eppudu copy-paste matrame
- WP admin lo meeru emaina break cheyakunda: bot **create/update matrame chesthundhi, delete emi ledu**
- Edaina doubt → `run.py --doctor` + `run.py --setup --dry-run` — rendu milipi **meeru cheppalsinanni English/Telugu lo checkisthayi**
- Code problem vasthe Arena lo cheppandi — fix chestha 🔧

*Last updated: v23 (font polish + full site automation). Ee file repo lo unnadi — server lo kuda adhe path.*
