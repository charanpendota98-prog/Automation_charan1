# 🚀 START HERE — studentup.in Founder Manual (v39)
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

> 🚀 **Kotha (v41 deploy pack):** full guide `DEPLOY.md` lo — 3 paths (VPS+Caddy ⭐ /
> Docker / PaaS). Okka command install: `sudo DOMAIN=exams.college.edu bash deploy/install-vps.sh`
> Ready-a ani check: `python run.py --deploy-check` (deps/env/disk/port + exam portal ni
> **nijamga boot chesi** `/healthz` hit chestundi).

```bash
# 0. deploy readiness (ee okka command chalu — enti miss undo cheptundi)
python run.py --deploy-check

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

---

## 🏆 v38 TOP POST ENGINE — "top post veyyali, anni keywords" (new)

| Em | Command |
|---|---|
| Anni 11,192 keywords + CSV export | `run.py --keyword-universe` |
| Oka keyword ki top-post blueprint (title/meta/outline/keywords/schema/E-E-A-T) | `run.py --top-post "TSPSC Group 2 2026 notification"` |
| 90-day publishing calendar (pillar + support mix) | `run.py --top-post-plan --top-post-days 90` |
| Blueprint nunchi article generate + draft | `run.py --top-post "NSP Scholarship last date" --publish-top-post` |
| Ee file/HTML top post aa? measure chey | `run.py --score-post file.html --score-keyword "ssc cgl 2026"` |

- Blueprint files: `output/top-posts/<slug>.html` (stylized page — browser lo open cheyandi), `.md`, `.json`
- Keywords CSV: `output/keywords/keyword_universe.csv` (Excel lo sort chesi plan cheyochu)
- Publish apudu bot **automatic ga** score chestundi (30+ checks) + structural
  harden (meta/slug/snippet/FAQ/density cap). Score < 78 unte **live publish block**
  (`TOP_POST_STRICT=0` tho off cheyochu) — draft-first lo block undadu.
- Repo sample: `docs/design-archive/top-post-blueprint.html` + `docs/design-archive/dominance-plan-90-days.md`
- ⚠️ Volume/difficulty bands **heuristic estimate** (Google data kaadu); ranking
  guarantee ledu; dates/fee/vacancies official notice nunchi matrame.

**AdSense approve ayyaka kuda:** `.env` lo `ADSENSE_APPROVED=1` + valid client ID/CMP/ads.txt verify chesi matrame ads consider cheyandi. `DEFAULT_POST_STATUS=publish` before independent human/editorial review verify cheyakandi; draft-first mode safer.

---

## 🎓 v39 COLLEGE EXAM PORTAL — "college ki exams easy ga, students easy ga join" (new)

| Em | Command |
|---|---|
| Sample exam + students tho portal start (try cheyyadaniki) | `run.py --exam-portal-demo` |
| Empty portal (kotha exams create cheyyandi) | `run.py --exam-portal` |
| Port / public URL tho | `run.py --exam-portal --exam-port 9000 --exam-base-url https://exams.college.edu` |
| Telegram/webhook notification test | `run.py --exam-portal-test-channels` |
| Test suite (14 sections) | `python tests/v39_exam_portal_test.py` |

**College ki 5 nimishalu setup:**
1. `run.py --exam-portal` → boot lo **admin key** print avutundi (adhi save cheyandi).
2. Browser lo `/admin` → key tho login → **+ New exam** (title, duration, marks,
   negative marks, pass marks, roster ON/OFF …).
3. **Questions tab** → Word/Excel nunchi paste (blocks / CSV / JSON — prathi
   tappu line-wise report avutundi, silent ga skip avvadu) → Publish.
4. **Student list tab** → roll numbers paste (oka line ki okka roll).
5. **Share tab** → student link + WhatsApp/notice template copy → students ki pampandi.

**Exam day (okka click):**
- Students link open chesi **roll number** tho join avutaru (password ledu;
  okka roll = okka device; same device lo resume ayithe answers safe).
- Andaru join ayyaka admin **🚀 START NOW** → andariki same timer + paper lock.
- Admin **🔒 CLOSE NOW** → pending students auto-submit + results compute
  (idempotent — rendu sarlu chesina okkate). Time ayyaka **automatic close**
  kuda untundi (admin marchipoyina kuda).
- Live monitor: evaru writing/submitted/offline, tab-switch count, announcement
  banner (students screen lo live), `+5 min` extend, late-join ON/OFF.
- Results tab: rank, pass/fail, topper, average, question-wise analysis
  (ekkada andaru tappu chesaro), CSV exports (results/questions/analysis/audit).

⚠️ Honest note: ranking/AdSense/RPM guarantee ledu (ade repo policy) — exam lo
kuda ilage: results, deadlines, keys anni **meeru verify chesi** publish cheyandi.
Public internet lo pettali ante HTTPS reverse proxy vadandi, admin key share
cheyyakandi (per-exam manage link share cheyandi).

---

## 🧹 v41 SITE AUDIT + FIX — "anni tappalu okate scan lo, malli raakunda" (new)

| Em kavali | Command |
|---|---|
| Audit matrame (read-only, emi maradu) | `run.py --site-audit` |
| Audit + fixes plan (dry-run — emi apply avvadu) | `run.py --site-audit-fix` |
| Fixes ni nijamga apply | `run.py --site-audit-fix --site-audit-apply` |
| Junk/demo pages ni trash cheyyadaniki permission | `run.py --site-audit-fix --site-audit-apply --site-audit-trash` |
| Only konni fixers (ex: PII + shortcode) | `... --site-audit-action strip_pii,strip_shortcode` |
| Network ledu / site reach avvatledu (offline proof) | `run.py --site-audit --site-audit-snapshot demo` |
| Test suite (14 sections) | `python tests/v41_site_audit_test.py` |
| ANNI suites okate command tho (30/30) | `run.py --test-all` |

**Enti pattukuntundi:** title ledu / content khali / junk HTML dump / broken heading tags /
featured image ledu / private company "Govt Jobs" category lo / walk-in job
"Internships" lo / Uncategorized posts / body lo phone number (PII) / raw
`[adinsert]` shortcode / TOC lo duplicate anchors / off-topic article / stale dates /
mixed image formats / theme demo pages live / `/privacy-policy/` lo "About us" /
duplicate contact pages / 200+ tags (85% zero) / truncated tag name / duplicate tags /
empty categories / timezone UTC / Rank Math Local SEO location lekunda.

**Safety (zero-mistake rules):**
- Default **dry-run** → `--site-audit-apply` ivvakapote okka write kuda jaragadu.
- Destructive (draft/trash) ki **`--site-audit-trash`** permission kavali.
- Junk content **delete avvadu** — draft/trash matrame (revisions tho tirigi techukovachu).
- Duplicate tags **lossless merge** — posts anni keep-tag ki reassign ayyaka ne delete.
- Prathi fix audit log + `output/audit/site-audit-<date>.md` report.

**Malli raakunda (root cause):** live publish (`DEFAULT_POST_STATUS=publish`) ki mundu
ippudu **v41 site gate** kuda run avutundi — empty title/excerpt, image ledu, junk HTML,
registered-kaani shortcode, duplicate anchor, `U+2011`/"today" template, stale date,
PII phone, Govt category lo private company, off-topic entity → **block**. Drafts
eppudu allow (human review ki).

**CI:** `ci/github-actions-tests.yml` — prathi push/PR ki **30 suites** (Python
3.10/3.11/3.12) + offline audit job. Okka manual step: aa file ni GitHub lo
`.github/workflows/tests.yml` ki copy cheyandi (agent token ki `workflows`
permission ledu — workflow file push cheyyaleru; migilinavi automatic).
Local ga same: `run.py --test-all`.

⚠️ Audit ni **mee network nunchi** run cheyandi (repo sandbox/proxy lo studentup.in
direct access block avutundi — appudu `--site-audit-snapshot` mode undi, leda mee
server lo `--site-audit-save` tho snapshot teesukoni ikkada run cheyandi).

---

## 📢 v43 AD MANAGER — "vare ads: college banners, shop, services" (new)

| Em kavali | Command |
|---|---|
| Inventory status + slot plans | `run.py --ads` |
| Visible placement preview (browser lo) | `run.py --ads-demo` → `output/ads-preview.html` |
| Real ad add cheyandi | `ads/inventory.json` lo ad add (demo:true remove) → next post automatic |

- **Highest-CTR slots:** TOP (Quick Answer taruvata) · MID (first H2 taruvata) · BOTTOM (related mundu)
- **100% safe:** visible SPONSORED label + `rel="sponsored nofollow"` + no-ads-near-links + CLS-safe + max 2/post (AdSense approval ayyaka auto 1)
- **UTM auto-tagging** → GA4 lo ad-wise CTR reports
- Strategy + 14 safe high-CTR tricks + college deal template: `AD_STRATEGY_ADVANCED.md`

## 🔬 v44 DEEP POST ENGINE — "deep analyse, perfect posts, mistakes leku" (new)

| Em kavali | Command |
|---|---|
| Deep research report (confidence/conflicts/gaps) | `run.py --deep-research "TSPSC Group 2 2027" --research-year 2027` |
| NotebookLM deep prompt (passes 6–8) | `run.py --deep-research "..." --deep` |
| NotebookLM output merge + verify | `run.py --deep-research "..." --notebooklm-brief brief.txt` |
| Post ki deep analysis auto | Automatic — ≥2 sources unna posts lo "In-Depth Analysis" section |

**Perfect gates (live publish lo BLOCK):** source conflicts (2 last dates) · article lo 2
different "last date" values · stale years (current year dates levu) · uncited NotebookLM
brief. Drafts lo flags (Telegram review) — override cheyaku.

**Mee manual workflow:** `MANUAL_ADVANCED_CHECKLIST.md` — Part 1 (per-post 10-15 min:
deep-research → NotebookLM loop → generate → review) + Part 2 (weekly loop) + Part 3
(10 zero-mistake rules) + Part 4 (LIVE-PUBLISH BLOCKED fix table).

- **Source tiering:** T1 official (.gov.in/.edu.in) > T2 major media > T3 other — T1-weighted
- **Cross-verification:** confirmed (2+ sources) / official (T1) / single-source / ⛔ conflict
- **Confidence 0-100** — 75+ strong, <50 = official source add cheyandi
- Reports: `output/deep/<topic>-<date>.md` + `.json`

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

*Last updated: v39 (College Exam Portal — admin START/CLOSE, roll-number join, auto-close/auto-submit, multi-channel notifications + 14-section test suite). Ee file repo lo unnadi — server lo kuda adhe path.*
