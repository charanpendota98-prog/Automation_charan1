# studentup.in on MilesWeb (cPanel) — advanced setup

Answer to "MilesWeb lo advanced ga work avutunda?" → **అవుతుంది**, with one split:
the **website + bot** run fully on MilesWeb; the **exam portal** also runs there
through Python App (WSGI) — this repo now ships the adapter (`passenger_wsgi.py`).

| Part | Where it runs | Verified |
|---|---|---|
| Public website (Telugu pages, ads, poll UI) | MilesWeb cPanel → `public_html` (static HTML or WordPress) | any static host ✔ |
| WordPress auto-blogger | MilesWeb **cron job** calling `run.py` (Python App venv), or GitHub Actions | Python 3.9+/3.11 via **Setup Python App** (CloudLinux + Passenger) [1](https://www.milesweb.in/hosting-faqs/install-and-configure-django-from-cpanel/) |
| Exam portal (`/exam`, `/admin`, `/poll`) | MilesWeb **Setup Python App** using `passenger_wsgi.py` (same features as local server) | `tests/v49_wsgi_test.py` — 8 checks ✔ |
| SQLite DBs (`state.db`, `exam_portal.db`) | app folder (never `public_html`) | FAQ confirms SQLite works [1](https://www.milesweb.in/hosting-faqs/install-and-configure-django-from-cpanel/) |

MilesWeb cPanel plan facts (their own plan page): base plan gives **3,00,000 inodes,
5 cron jobs**, higher tiers **unlimited cron**, 756 MB RAM / 1 CPU (base) to
3 GB / 3 cores; disk 50 GB → 200 GB → unlimited. [2](https://www.milesweb.in/hosting/cpanel-hosting)

---

## 1) Website (10 minutes)

Option A — **static preview** (what `preview/` is):
```
cPanel → File Manager → public_html/
  upload every file from preview/   (index.html, pages/, robots.txt, sitemap.xml, favicon.svg,
                                     manifest.webmanifest, sw.js)   # v72: ee rendu files PWA ki kaavali
```
**v72.1 (App డౌన్‌లోడ్) note:** `manifest.webmanifest` + `sw.js` **root lo** undali (index.html
pakkana). Munde install chesina phone lo kotha assets ravalante `sw.js` lo `VERSION` bump
(`su-v73-1` ippudu undi) — browser purana cache vadadam aaputundi. `data/deadline.json` ippudu ledu (v73 countdown removal)
ante hero countdown honest line chupistundi (fake date eppudu vaddu) — bot
`python run.py --push-theme-data` tho ee file rasi pettedi.

**v72 (PWA) note:** `manifest.webmanifest` + `sw.js` **root lo** undali (index.html pakkana).
Ee rendu unte "యాప్గా ఇన్స్టాల్" button + offline page pani chestayi. WordPress route lo idi
theme ne chestundi (`?studentup_manifest=1` / `?studentup_sw=1`) — server config avasaram ledu.

Design drafts (`ads-preview.html`, `legacy-concept.html`, `v*.html`, `top-post-blueprint.html`)
**ippudu repo lo `docs/design-archive/` lo unnayi** (v70) — website server aa folder ni serve
cheyyadu, anduku upload gurinchi aalochinchakandi. (Safety-net: robots.txt lo `Disallow: /_dev/`
unchamu — purana deploy lo aa folder unte index avvakoodadu.)

Option B — **WordPress** (recommended for the real blog):
```
cPanel → WordPress Toolkit / Softaculous → install on studentup.in
plugins: Rank Math (SEO) · WP Super Cache / LiteSpeed Cache · UpdraftPlus (backup)
theme: GeneratePress (free) → tools/wp-advanced.css + tools/wp-advanced-snippets.php
```
Then in `.env` set `WP_URL`, `WP_USERNAME`, `WP_APP_PASSWORD` (Application Password
from wp-admin → Users → Profile) and the bot posts straight into WordPress.

## 2) Bot on MilesWeb (cron)

```
cPanel → Setup Python App → Create Application
  Python version      : 3.11 (3.9+ works)
  Application root    : bot            ← /home/<user>/bot
  Application URL     : bot.example.in (or leave blank; we only need the venv)
  Startup file        : passenger_wsgi.py
```
Upload the repo into that root, then via cPanel's terminal (or SSH):
```
source /home/<user>/virtualenv/bot/3.11/bin/activate
cd ~/bot && pip install -r requirements.txt
cp .env.example .env      # WP creds, GEMINI keys, ADSENSE_APPROVED etc.
crontab -e
```
Cron entries (base plan allows 5 — that is plenty):
```
0 6,12,18 * * *  cd /home/<user>/bot && /home/<user>/virtualenv/bot/3.11/bin/python run.py --run >> logs/bot.log 2>&1
30 7 * * *       cd /home/<user>/bot && /home/<user>/virtualenv/bot/3.11/bin/python run.py --deep-research auto >> logs/deep.log 2>&1
0 9 * * 1        cd /home/<user>/bot && /home/<user>/virtualenv/bot/3.11/bin/python run.py --site-audit >> logs/audit.log 2>&1
0 3 * * 0        cd /home/<user>/bot && /home/<user>/virtualenv/bot/3.11/bin/python tools/prune_media.py --days 30 --apply >> logs/prune.log 2>&1
```
Note: bot posts still pass the **human-review gate** (draft + Telegram approval) —
cron only *prepares* posts.

**Free alternative to MilesWeb cron:** GitHub Actions schedule (`ci/github-actions-tests.yml`
shows the pattern). Caveats that are real: scheduled workflows only fire from the
**default branch**, are **best-effort** (15–45 min delay is normal), private repos on
the free plan share **2,000 minutes/month**, and schedules in repos with no activity for
60 days get disabled. [3](https://github.com/orgs/community/discussions/197954) [4](https://devactivity.com/insights/github-actions-cron-schedules-a-hidden-free-tier-hurdle-impacting-developer-productivity/)
So: MilesWeb cron = predictable; GitHub Actions = free backup.

## 3) Exam portal on MilesWeb (Python App)

```
cPanel → Setup Python App → Create Application
  Python version   : 3.11
  Application root : examportal          ← /home/<user>/examportal
  Application URL  : studentup.in        URI: exam
  Startup file     : passenger_wsgi.py
Environment variables (in the same screen):
  EXAM_DB        = /home/<user>/examportal/exam_portal.db
  EXAM_ADMIN_KEY = <a long random secret — this is the admin/ads key>
```
Upload: `exam_portal/`, `autoblog/` (for ad_manager), `passenger_wsgi.py`, `run.py`,
`requirements.txt`, `ads/inventory.json`.
Restart the app → open `https://studentup.in/exam/admin` (or `/admin` when the app
root serves the domain). Poll endpoints: `/poll/today`, `/poll/vote`.

Same code runs on a VPS with gunicorn if you ever move:
```
gunicorn --workers 2 --bind 0.0.0.0:8080 passenger_wsgi:application
```

## 4) Ads — "ఏదీ miss అవ్వదు" (never missed)

* Admin console → **📢 ప్రకటనలు** → add/edit/delete. Saved to `ads/inventory.json`,
  used by the bot on the next post (SPONSORED + `rel="sponsored nofollow"`).
* Every public page (home + 5 policy pages) already carries a labelled SPONSORED slot.
* Rotation: `ads/rotation.json` remembers when each ad last ran → **every active ad
  gets its turn**; a category mismatch falls back instead of silently dropping the slot.
* Strict mode (only category-matched ads): `.env` → `AD_FALLBACK_ALWAYS=0`.
* Safety that stays on: max 2 ads/post (`MAX_PERSONAL_AD_SLOTS`; auto 1 once
  `ADSENSE_APPROVED=1`), no ad near a link, CLS-safe wrapper, no clickbait, no fake clicks.

## 5) Storage — numbers, not worries

Measured in this repo: **public site 276 KB**, `exam_portal.db` ~96 KB, `state.db` ~40 KB.
A 1200×675 JPEG (quality 86) post image ≈ **150–250 KB** → 1 post/day ≈ **6 MB/month,
~75 MB/year** locally; WordPress media lives in MilesWeb disk (50 GB base plan →
years of headroom). The real limit on shared hosting is often **inodes (file count)**,
not size — base plan allows 3,00,000.

Keep it flat:
```
python tools/prune_media.py                    # report
python tools/prune_media.py --days 30 --apply  # delete local images older than 30 days
python tools/prune_media.py --db-vacuum --apply
```
Published WordPress media is never touched — only local working copies.

## 6) Honest limits (shared hosting)

* **No long-lived sockets**: MilesWeb serves the portal through Passenger/WSGI. Two admins
  editing *at the same second* are fine (SQLite + short transactions); for a state-level
  exam with thousands of concurrent students, move the portal to a VPS/cloud instance and
  point `EXAM_DB` at the same code — the WSGI adapter is unchanged.
* **Cron granularity**: 5 jobs on the base plan; if you need per-15-minute polling, use the
  higher tier or GitHub Actions to trigger `--run`.
* No code can guarantee Google rankings, AdSense approval or revenue — the gates reduce
  mistakes; final numbers come from your own Search Console / AdSense account.

---
*Last updated: v49 (2026-09-18) · tested with `python run.py --test-all` (35 suites) and `tests/v49_wsgi_test.py`.*
