# 🚀 START HERE — studentup.in Founder Manual (v35)
### "Nenu em cheyali?" — ee file matrame chalu. Settings anni bot automatic ga set chesthundi.

---

##  Divide cheddam: enti BOT chesthundhi, enti MEERU cheppali

| ✅ BOT (code) automatic ga chesthundhi | 👤 MEERU cheppalsinadi (vastha 7 items matrame!) |
|---|---|
| Daily original Telugu articles (research → write → SEO → image) | **1. Gemini keys** — aistudio.google.com nunchi 2-3 free keys → `.env` lo `GEMINI_API_KEYS=...` (429 quota fix — idi oka MUST) |
| Rank Math meta + honest strict scoring + auto-refine | **2. Server commands** — kirem block copy-paste (kirem ade) |
| WordPress SITE settings (`--setup`: tagline, timezone, comments OFF, footer menu, category SEO, favicon) | **3. AdSense signup** — adsense.google.com lo owner account + `--ensure-adsense` checklist; Google fixed post-count guarantee ivvadu |
| v28 plugin stack (`--plugins`: Rank Math, Redirection, UpdraftPlus, WP Super Cache) + active theme audit | **4. AdSense approval ayyaka** `ADSENSE_CLIENT_ID=ca-pub-...` `.env` lo pettandi; loader script matrame auto-install avutundi |
| Student Internet Center service page + call/WhatsApp/private-upload workflow | **7. Business details** — `SERVICE_CENTER_PHONE`, WhatsApp and secure upload URL configure cheyandi |
| Google Jobs schema, countdown, facts guard, bylines, E-E-A-T | **5. Search Console + Analytics** — Rank Math → Google Console module lo "Authenticate" click (2 min OAuth) — ee okka click tho `--gsc` loop full power |
| Radar → real news links queue (never fake news) | **6. Rozu 10 nimishalu** — Telegram approve buttons (draft mode lo unnapudu) + week ki okka saru `--gsc` CSV (optional kaani powerful) |
| Hub pages, internal links, thumbnails, IndexNow | — |

> WP admin lo meeru em settings **cheyalsidi kaadu** — `--setup` chesthundhi. Theme koncham matrame (kirem chustha).

---

## 🖌️ THEME — final answer

**Rule:** speed + readability support a better user experience and conversions; rankings, AdSense approval and RPM are never guaranteed. Content posts lo unnadi — theme marchina **emi poyipokadu** (safe).

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
.venv/bin/python run.py --production-audit  ← live safety/revenue gate
.venv/bin/python run.py --content-audit       ← existing posts quality report
.venv/bin/python run.py --google-audit https://studentup.in/ ← public Google-facing check
.venv/bin/python run.py --research-brief "TSPSC Group 2 2027 notification" --research-year 2027 ← year-locked NotebookLM source bundle
.venv/bin/python run.py --setup --dry-run   ← report chudandi
.venv/bin/python run.py --setup             ← settings + theme audit + plugin stack + widgets
.venv/bin/python run.py --plugins --dry-run  ← plugin plan alone chudali ante
.venv/bin/python run.py --ensure-adsense    ← 5 policy pages
.venv/bin/python run.py --adsense-kit --dry-run  ← valid client id unte loader preview
.venv/bin/python run.py --service-center --dry-run ← service page preview
.venv/bin/python run.py --service-center          ← service page publish/update
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
| Nela | Relevant coaching/service partners ni contact cheyandi; paid listing unte clear disclosure + `rel=sponsored nofollow` use cheyandi | 20 min |

**AdSense approve ayyaka kuda:** `.env` lo `ADSENSE_APPROVED=1` + valid client ID/CMP/ads.txt verify chesi matrame ads consider cheyandi. `DEFAULT_POST_STATUS=publish` before independent human/editorial review verify cheyakandi; draft-first mode safer.

---

## 💰 Money — honest plan (expectations realistic ga)

| Phase | Timeline | Expected | Chese padaluku |
|---|---|---|---|
| Foundation | Month 1-2 | Revenue unknown; traffic baseline build cheyali | 3–5 quality drafts/day, human review, hubs and corrections workflow |
| Traction | Month 2-4 | Search Console data tho measure cheyali | Striking-distance queries, indexing and Core Web Vitals improve cheyali |
| Monetize | After approval | AdSense RPM/CPC unknown; Google account/traffic batti change avtayi | CMP, ads.txt, policy center and placements manually verify cheyali |
| Diversify | Later | Service/affiliate/partner revenue only if real demand exists | Clear disclosures, configured contact details and no forced sales |

> Single AdSense meeda 100% dependence = one policy review distance. Playbook rule: **5 streams** — bot + routine lo anni wired unnayi.

---

## 🔥 Viral levers (top-site pattern — bot lo automatic)
1. **Result/Hall-ticket = instant share** — deadline countdown + "N days left 🔥" badge (already in every post)
2. **Cut-off trend tables** — niche lo ekkuva re-shared content; keyword engine gap-targets veetini cover chesthundhi
3. **WhatsApp forward-friendly** — quick answer box first 40 words lo complete answer (forward chesinappudu adhe kanipisthundi)
4. **Colloquial headlines** — "Apply ela cheyali?" style (student bhasha) = CTR
5. **Bylines + corrections** — trust signals; Google News/Discover visibility is editorially and algorithmically decided, not guaranteed by applying
6. **Telegram channel** — `TELEGRAM_CHANNEL_CHAT_ID` pettaka prathi published post automatic channel ki (monthly audience compound avutundi)

---

## ❓ "Asalu naku settings teliyadu" — tension enduku?
- Teliyalsinadi **emmi ledu** — anni commands eppudu copy-paste matrame
- WP admin lo meeru emaina break cheyakunda: bot **create/update matrame chesthundhi, delete emi ledu**
- Edaina doubt → `run.py --doctor` + `run.py --setup --dry-run` — rendu milipi **meeru cheppalsinanni English/Telugu lo checkisthayi**
- Code problem vasthe Arena lo cheppandi — fix chestha 🔧

*Last updated: v31 (Student Internet Center service workflow + advanced UI + production audit). Ee file repo lo unnadi — server lo kuda adhe path.*
