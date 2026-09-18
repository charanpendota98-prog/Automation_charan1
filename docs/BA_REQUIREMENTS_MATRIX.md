# BA REQUIREMENTS MATRIX — studentup.in (v42 → v67)

**Idi enduku:** business analyst (BA) level lo prathi requirement → implementation → automated
test → evidence command → status. Ee file chuste "asalu enti chesindi, enti verify ayyindi,
enti mee (owner) cheyyali" ani okka chota telustundi — memory meeda depend avvakunda (v60 rule).

**Verify command (okate line, anni gates):**
```bash
python run.py --test-all          # 53 suites (unit + integration, offline)
python run.py --readiness         # 100/100 · 26/26 system checks · 8 owner-pending
python run.py --pin-check         # per-post certificate (67 checks) sample
python run.py --guardian          # site + theme + audit daily checks
python tools/theme_audit.py --verbose   # theme mistakes 0 errors · 0 warnings
python tools/build_wp_theme.py    # php-lint + audit + POT + zip (theme install file)
```

---

## 1) KPI DASHBOARD (measurable targets — business view)

| KPI | Target | Current (measured) | Command |
|---|---|---|---|
| Post quality gates | 100/100 · 0 critical | **100/100 · 67/67 · critical 0** | `python run.py --pin-check` |
| Rank Math score | 100 | **100** (draft 33 → 100 deterministic) | `--pin-check` / WP post edit |
| System readiness | 100/100 | **100/100 · 26/26 system · 8 owner-pending** | `python run.py --readiness` |
| Test coverage | all green | **54/54 suites · 122/122 runtime · 18 v68 checks** | `--test-all` + jsdom |
| Theme audit | 0 errors · 0 warnings | **0 · 0** (27 files · 75 functions · 34 options) | `tools/theme_audit.py` |
| PHP syntax (real PHP 8) | 100% | **27/27 files OK** | `tools/build_wp_theme.py` |
| Ad positions live in theme | 6/6 | **6/6** (leaderboard · in-article · in-feed · sidebar-sticky · below-content · anchor) | audit KPI row |
| Ad density per page | ≤ 4–5 | **max_ads default 4** (cap enforced) | StudentUp → Ads |
| CLS (layout shift) | < 0.1 | reserved heights on all units + img width/height rules | theme CSS + gate `img_dimensions` |
| LCP (mobile) | < 2.5 s | LCP preload + `fetchpriority=high` + preconnect + content-visibility | `inc/perf.php` |
| ads.txt | served + valid | `/ads.txt` auto (AdSense DIRECT line) | `curl https://studentup.in/ads.txt` |
| Consent Mode v2 | ON (EEA/UK safe) | head priority 1 · denied default + CMP bridge | `inc/consent.php` |
| Discovery surfaces | sitemap + news sitemap + RSS | `/sitemap.xml` · `/news-sitemap.xml` (48h · te) · feed | curl + GSC |
| Posting cadence | ≥ 20 posts/day (IST) | 3–5 manual slots + radar 4×/day + breaking + auto-refresh | `python run.py --status` |
| Manual approval | 100% drafts | draft → Telegram ✅/🗑️ (no auto-publish without approval) | bot logs |
| Revenue engines | all wired | 6/6 (rate card · house ads · calculator · network plan · advisor · leads) | `--readiness` |

> **Honest note (v62 rule):** ee KPIs anni **code-side verifiable**. Google ranking, traffic,
> AdSense approval, actual revenue = Google + mee accounts + time — **guarantee ledu**, idi
> proof matrix mattrame.

---

## 2) REQUIREMENTS → IMPLEMENTATION → TEST → EVIDENCE

| # | Requirement (mee maata) | Ver | Implementation | Automated test | Evidence |
|---|---|---|---|---|---|
| R1 | Pure-Telugu website content (English mix ok) | v47 | theme templates + prompts (`autoblog/prompts.py`) | `v47_test`, jsdom Telugu-dominance | `--test-all` |
| R2 | Exam portal (polls/quiz daily update) | v46-v47 | `exam_portal/`, `quiz_engine.py` | `quiz_test` | `python -m exam_portal.server` + `/healthz` |
| R3 | Posts perfect + **manufactured proof** | v48/v65 | `validator.py`, `post_gate.py` (67 checks) | `validator_test`, `v65_test`, `v66_test` | `--pin-check` certificate |
| R4 | Highest-revenue ads, safe (no clickbait) | v49/v52/v66 | `ad_manager.py`, theme `inc/ads.php` (6/6 slots) | `v49_test`, `v52_test`, `v66_test`, `v67_test` | audit KPI `ad_positions 6/6` |
| R5 | House/private ads placeable from admin | v52/v64 | theme options `house_ads` + REST + `tools/build_wp_theme.py` | `v52_test`, `v64_test` | StudentUp → Ads |
| R6 | Low revenue → real engines (never guarantee) | v53-v55 | `monetize.py`, `workbook` rate card, `tools/revenue_estimate.py` | `v53/v54/v55_test` | `python tools/revenue_estimate.py` |
| R7 | Menu = your category list, Telugu labels | v51/v59 | `inc/template.php` + WP menus + `menu_wiring` guardian check | `v51_test`, `v59_test`, guardian | `--guardian` |
| R8 | Socials right side, vertically centered | v50 | `footer.php` `.su-social` (WhatsApp/Telegram/Instagram/YouTube) | `v50_test` | theme zip |
| R9 | Breaking news best-grade + ticker | v59 | `inc/breaking.php`, `autoblog/breaking.py`, feed JSON | `v59_test`, `live_feed_test` | `--breaking-feed` |
| R10 | Website must look like the preview | v61 | WordPress custom theme `wordpress-theme/studentup/` | `v61_test`, jsdom 122 checks | `preview/index.html` + zip |
| R11 | Everything changeable from admin (ads esp.) | v52/v64 | StudentUp Settings page (Ads · Socials · Content · Advanced) + REST | `v64_test` | WP Admin → StudentUp |
| R12 | 100% SEO fields never silently miss | v63 | `inc/seo-bridge.php` (REST meta bridge) + post-publish verify + Telegram warning | `v63_test` | bot logs + `--readiness` |
| R13 | Rank Math 100 per post | v64 | `autoblog/rm100.py` deterministic fixers + `RM_TARGET=100` + refine rounds | `v64_test` (33→100 idempotent) | `--pin-check` shows 100/100 |
| R14 | Theme "inka inka best" (options/TOC/schema/E-E-A-T/PWA) | v64 | `inc/options.php`, `inc/toc.php`, `inc/schema.php`, `inc/author-box.php`, `inc/pwa.php` | `v64_test` | theme zip 34 files |
| R15 | Pin-to-pin check + per-post certificate | v65 | `autoblog/post_gate.py` (67 checks · 8 groups) + `output/certificates/` | `v65_test`, `v66_test` | `--pin-check` |
| R16 | Google Trends/Suggest → trending topics | v65 | `autoblog/trends.py` (RSS IN + Suggest + queue) | `v65_test` | `python run.py --trends --trends-queue` |
| R17 | Ads "highest" ki unna misses fix | v66 | page gating · density cap · AdSense-first · CLS reserved · lazy · in-article · ads.txt · Consent Mode v2 · news sitemap · LCP | `v66_test` (13 checks) | `output/v66-proof-2026-09-18.md` |
| R18 | Blog rasthunnapudu deeper checks | v66/v67 | gate SEMANTIC + DEEPER (67) + **gate fails → LLM refine hints** | `v66_test` SEMANTIC/DEEPER asserts | `--pin-check` 67/67 |
| R19 | Theme mistakes **deep audit** + expert/BA level | v67 | `tools/theme_audit.py` + `tools/theme_audit_deep.py` (templates · security · perf · a11y · ads · standards · KPI) | `v67_test` (11 checks, detection ability tho) | `tools/theme_audit.py --verbose` |
| R20 | Top-most theme (WordPress standards) | v67 | comments.php · sidebar.php · readme.txt · `languages/studentup.pot` (+ auto POT build) · screenshot 1200×900 · theme.json v2 | `v67_test` | zip 34 files · WP → Appearance → Themes |
| R21 | Highest revenue, 100% safe | v67 | **6/6 ad slots** (new below-content + sticky sidebar) · spacing policy CSS · `max_ads` cap · consent · ads.txt | `v67_test` revenue asserts | audit KPI row |
| R22 | Security hardening (top-site level) | v67 | `inc/security.php` (headers · XML-RPC off · enumeration block · attachment redirect · comment flood guard · DISALLOW_FILE_EDIT) | `v67_test` security asserts | theme file + docs |
| R23 | Fast (CWV) + accessible | v67 | preconnect · LCP preload · content-visibility toggle (`su-cv`) · `:focus-visible` · skip-link · button types · `contains` sizes | `v67_test` perf/a11y asserts | `inc/perf.php` + `style.css` |
| R24 | Never fake/guarantee numbers | v62 | `readiness.honest_note` + docs + owner-pending section | `v62_test` | `--readiness` output |
| R25 | Instant indexing (trending) | publish → IndexNow + Google Indexing API (JobPosting) · key file theme serve · `--index-now/--status/--key-gen` | autoblog/indexing.py · inc/indexnow.php · v68_test | ✔ engine · ⏳ owner key/SA |

---

## 3) OWNER-PENDING (business actions — code tho cheyyalem)

| # | Action | Where | Why it matters | Blocker for |
|---|---|---|---|---|
| O1 | Domain + hosting + SSL (MilesWeb cPanel) | GO_LIVE PART B-1 | site live avvadam | everything |
| O2 | WordPress install + theme zip upload/activate | GO_LIVE PART B-2 | real site rendering | posts live |
| O3 | Gemini API key (.env `GEMINI_API_KEYS`) | GO_LIVE PART B-3 | post generation | daily posting |
| O4 | Telegram bot token + chat id (.env) | GO_LIVE PART B-4 | approval flow | publish control |
| O5 | GSC + GA4 verify + sitemap submit | GO_LIVE PART B-2a | indexing + measurement | traffic data |
| O6 | AdSense apply → approve → `ADSENSE_CLIENT_ID` + slots | GO_LIVE PART B-2e | revenue | money |
| O7 | AdSense CMP (Privacy & messaging) ON | GO_LIVE PART B-2c | EEA/UK ads eligible | RPM uplift |
| O8 | Oracle VM (bot 24×7) + UptimeRobot | DEPLOY_ORACLE_CLOUD.md | automation uptime | cadence |
| O9 | Ad network apply @ 25k pageviews | `tools/ad_network_plan.py` | RPM step-up | revenue scale |

---

## 4) RISK REGISTER (BA view)

| Risk | Impact | Mitigation (implemented) | Status |
|---|---|---|---|
| AdSense policy violation (density/placement) | account ban | density cap · policy pages OFF · spacing · SPONSORED labels · no guaranteed-claim text in posts | ✅ mitigated |
| Google penalty (thin/duplicate/AI-spam) | deindex | 67-check gate · near-duplicate block · fact guard · manual approval | ✅ mitigated |
| Layout shift / slow mobile | CWV fail → ranking + RPM dip | reserved heights · lazy ads · LCP preload · content-visibility | ✅ mitigated |
| EEA/UK ads blocked (no consent) | revenue loss | Consent Mode v2 + CMP bridge + ads_data_redaction | ✅ mitigated |
| ads.txt missing/unverified | direct demand closed | theme serves `/ads.txt` from AdSense client + manual lines | ✅ mitigated |
| Theme fatal error after edits | white screen | php-parser gate (27/27) + deep audit (0/0) + guardian | ✅ mitigated |
| Bot publish without approval | reputation risk | draft-first + Telegram ✅/🗑️ + pin gate block on critical | ✅ mitigated |
| Credentials shared in chat | security | never asked; App Password + REST + `.env` only | ✅ policy |
| Revenue/ranking expectations | wrong decisions | v62 no-guarantee rule + measured readiness only | ✅ policy |

---

*Last updated: v67 (2026-09-18) — deep audit (expert/BA) · top-theme hardening · 6/6 ad slots ·
54/54 suites · readiness 100/100 (27/27) · theme audit 0/0 · code audit 0/0 (E1–E12 · W1–W7).*
