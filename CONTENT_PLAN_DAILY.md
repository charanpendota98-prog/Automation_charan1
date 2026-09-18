# STUDENTUP DAILY CONTENT PLAN (v50)

Ee plan = "anni categories, chala posts, daily refresh, manual gate" — code lo
wire ayyi unna configuration ki match avutundi (`tests/v50_test.py` ee plan ni
verify chestundi).

---

## 1) PILLARS — 17 categories (TS + AP students kosam)

| # | Pillar | Enduku | Priority tickets | Official sources |
|---|--------|--------|------------------|------------------|
| 1 | **TS Govt Jobs** | TSPSC, TS Police, Gurukul, GENCO/TRANSCO | 4 | 10 |
| 2 | **AP Govt Jobs** | APPSC, AP Police, APSRTC, DSC, Sachivalayam | 3 | 8 |
| 3 | **Central Govt Jobs** | SSC, UPSC, RRB, IBPS, SBI, Defence | 4 | 33 |
| 4 | **Outsourcing Jobs** ⭐new | TS/AP outsourcing, CRC, contract basis, guest faculty | 3 | 8 |
| 5 | **Walkin Jobs** | walk-in drives, direct interviews | 0 | 5 |
| 6 | **Private Jobs** | TCS/Infosys/Wipro fresher drives | 2 | 1 |
| 7 | **Software Jobs** | dev/analyst roles, off-campus | 2 | 14 |
| 8 | **Part Time Jobs** | WFH, freelance, data entry (scam checks) | 0 | 2 |
| 9 | **Scholarships** | NSP, Jnanabhumi, fee reimbursement | 3 | 7 |
| 10 | **Upcoming Exams** ⭐new | exam calendar, tentative schedules | 4 | 6 |
| 11 | **Current Affairs** ⭐new | daily current affairs (PIB/govt releases) | 3 | 6 |
| 12 | **Exam Tips** ⭐new | preparation strategy, previous papers | 2 | 4 |
| 13 | **Hall Tickets** | admit cards, exam-day rules | 0 | 1 |
| 14 | **Results** | board/competitive results, answer keys | 3 | 5 |
| 15 | **Internships** | internships, training programs | 0 | 4 |
| 16 | **Online Education** | admissions, counselling, online degrees | 0 | 15 |

**Total: 143 official-source queries · 11,192 keywords (203 అంశాలు)**, 4×/day check (daily hot-list + rotation).
Kotha pillar ki source ledu anukunte: `autoblog/sources_grid.py` lo add cheyandi —
`tests/v50_test.py::test_official_source_grid_covers_every_pillar` ventane fail avutundi.

### విదేశీ ఉద్యోగాలు (Abroad Jobs) — 17వ pillar
Gulf/abroad jobs, visa, IELTS/PTE, study abroad, NRI guidance · roju 1–2 posts · Tier-1 ట్రాఫిక్ + high-CPC

## 2) ROJU PLAN (daily rhythm)

```
06:00  RADAR run      → 143 sources check → edu-relevant items → topic queue
07:00  DEEP run       → top queued topic: multi-source facts + cross-verify
       (NotebookLM brief optional — unte inka strong)
08:00  DRAFTS         → 3-5 drafts (pillars rotate: jobs → scholarships →
                        current affairs → exams → tips)
09:00  TELEGRAM       → mee approve/reject (draft-only default)
10:00  PUBLISH        → approve chesina vi matrame publish (QA≥80, orig≥72%)
14:00  Radar 2        → breaking news + notification changes
18:00  Drafts 2       → 1-3 more (evening audience)
21:00  Auto-refresh   → purana top posts ni kotha info tho update
```
Volume: `DAILY_MIN=3 → DAILY_MAX=5` draft slots/roju (`.env` lo penchochu).

## 3) AUTO-REFRESH (trending malli ravali ante)

* `python run.py --auto-refresh 2` → purana published posts ni kotha dates/info tho
  update (state lo `refreshed_at` record avutundi, so same post malli malli kaadu).
* `python run.py --update <POST_ID>` → oka post ni manually refresh (kotha sources tho).
* Refresh roju 1-2 posts chalu; Google ki "fresh" signal + malli crawl avutundi.
* Schedule (MilesWeb cron la): `0 21 * * *  run.py --auto-refresh 2`

## 4) MANUAL GATE — publish mundu aduguthundi ✔

```
DEFAULT_POST_STATUS=draft        → draft lo create avutundi, public kaadu
Telegram approval bot            → mee ✅ tho matrame publish
PUBLISH_QA_MIN_SCORE=80          → direct live publish ki quality gate
PUBLISH_ORIGINALITY_MIN=72       → copy kadu ani proof (kotha content)
deep publish gate                → source conflict / stale data unte HARD BLOCK
```
`--dry-run` (generate only) and `--mock` (offline test) kuda unnayi.

## 5) SEO — 100% packed (Rank Math tho)

Prathi post ki automatic ga:
* **Rank Math fields**: `rank_math_focus_keyword`, `rank_math_title` (≤160),
  `rank_math_description` (≤160), Facebook + Twitter title/description,
  `rank_math_robots = index, follow, max-image-preview:large`.
* **HTML/SEO**: canonical, OG tags, JSON-LD (Article + FAQ), quick-answer card
  (Google featured snippet target), auto table of contents, internal links,
  official source links, "updated on" badge.
* **No copy**: originality floor 72% + deep cross-verification (2+ sources,
  T1 weight) + conflict block.
* **IndexNow** support (`indexnow.py`) → publish ayyaka search engines ki ping.

Rank Math plugin settings checklist (WP admin):
```
Rank Math → Titles & Meta → Posts: Title "%title% %sep% %sitename%"
Rank Math → Sitemap: ON (posts, categories, news sitemap optional)
Rank Math → Schema: Article default; FAQ schema automatic (blog lo unnadi)
Rank Math → Focus keyword: bot nunchi vastundi (edit cheyyakandi)
```

## 6) TRENDING/REVENUE TRICKS (safe vi matrame)

| Trick | Status | Note |
|---|---|---|
| High-CPC pillars ki priority tickets | ✅ on | Jobs/Exams/Current Affairs |
| Seasonal rotation (exam/results/admission seasons) | ✅ on | 12 నెలల plan |
| Daily current affairs (repeat-visit driver) | ✅ new | PIB + govt releases |
| Autocomplete keyword harvest → gaps | ✅ on | `--keywords` |
| Auto-refresh purana posts | ✅ on | roju 1-2 |
| IndexNow ping | ✅ on | instant indexing |
| Internal linking + hubs | ✅ on | `hubs.py` |
| Clickbait / fake clicks / "Google tricks" | ⛔ NEVER | AdSense ban risk |

**Honest note:** ee plan reach/frequency improve chestundi kaani Google ranking,
AdSense approval leda revenue evi guarantee cheyyaledu. Final numbers mee Search
Console / AdSense account lo ne vastayi.

---
## First look (v59) — site open cheyagane

1. 🔴 బ్రేకింగ్ టికర్ (radar verified feed; khali aithe hide)
2. విద్యార్థులు ఎక్కువగా వెతికేవి: టీఎస్ · ఏపీ · హాల్ టికెట్లు · ఫలితాలు · వాక్-ఇన్ · సాఫ్ట్‌వేర్ · ప్రైవేట్ · ప్రస్తుతాంశాలు (live counts)
3. బ్రేకింగ్ న్యూస్ section (top 6) + grid lo TS/AP cards mundu

Posting rhythm idi follow avvali: breaking/exam-mechanics items (ఫలితాలు · హాల్ టికెట్లు ·
గడువు) ki **priority** — avi students ekkuvaga vethikevi.

*Last updated: v59 (2026-09-18) — 17 pillars · 143 official sources · 52/52 test suites · 122/122 runtime checks*
