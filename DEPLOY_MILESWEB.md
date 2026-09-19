# studentup.in on MilesWeb (cPanel) — full setup

Answer to "MilesWeb lo anni work avutunda?" → **అవుతుంది**. v74 nunchi bot
**cron-only** (live-exam server teesesam) — MilesWeb shared hosting lo anni
3 parts run avutayi, **24×7 daemon / Python web app avasaram ledu**.

| Part | Where it runs | Verified |
|---|---|---|
| Public website (WordPress blog + theme) | MilesWeb cPanel → WordPress install (Toolkit/Softaculous) | standard WP ✔ |
| Static preview site (optional mirror) | MilesWeb cPanel → `public_html` (upload `preview/`) | any static host ✔ |
| Auto-blogger bot (drafts + research + audits) | MilesWeb **cron job** calling repo `run.py` (venv python) | cron docs [1](https://www.milesweb.in/hosting-faqs/cron-jobs-cpanel/) |
| Telegram approvals (✅ Publish / 🗑️ Delete) | MilesWeb **cron** (`--approval-poll` every 5 min) | `tests/v74_test.py` — offline mock ✔ |
| Daily question + quiz + WhatsApp form | **No server** — pure browser JS (works on any host) | jsdom 164/164 ✔ |
| SQLite DB (`state.db`) | bot folder (never `public_html`) | FAQ confirms SQLite works [2](https://www.milesweb.in/hosting-faqs/install-and-configure-django-from-cpanel/) |

MilesWeb cPanel facts: **unlimited cron jobs** on hosting packages [1](https://www.milesweb.in/hosting-faqs/cron-jobs-cpanel/),
Python available via cPanel (venv in your home dir, no root needed). The real limit
on shared hosting is often **inodes (file count)**, not size.

---

## 1) Website (10 minutes)

Option A — **WordPress** (recommended for the real blog):
```
cPanel → WordPress Toolkit / Softaculous → install on studentup.in
plugins: Rank Math (SEO) · WP Super Cache / LiteSpeed Cache · UpdraftPlus (backup)
theme: wp-admin → Appearance → Themes → Upload → wordpress-theme/studentup-theme.zip → Activate
```
Then in the bot `.env` set `WP_URL`, `WP_USERNAME`, `WP_APP_PASSWORD`
(Application Password from wp-admin → Users → Profile) and the bot posts
straight into WordPress (drafts first — you approve on Telegram).

Option B — **static preview** (what `preview/` is):
```
cPanel → File Manager → public_html/
  upload every file from preview/   (index.html, pages/, robots.txt, sitemap.xml, favicon.svg,
                                     manifest.webmanifest, sw.js, data/)
```
PWA note: `manifest.webmanifest` + `sw.js` **root lo** undali (index.html
pakkana). Munde install chesina phone lo kotha assets ravalante `sw.js` lo
`VERSION` bump — browser purana cache vadadam aaputundi.
Current version: `su-v73-1` (DevTools → Application → Service Workers lo kanipistundi;
upload tarvata version maaraledante hard-refresh cheyandi).
Design drafts repo lo `docs/design-archive/` lo unnayi — website server aa
folder ni serve cheyyadu, anduku upload gurinchi aalochinchakandi.
(Safety-net: robots.txt lo `Disallow: /_dev/` unchamu.)

## 2) Bot on MilesWeb (cron — 15 minutes, one time)

```
cPanel → Terminal (leda SSH) → one-time setup:
  mkdir -p ~/bot && cd ~/bot
  # repo files ni ikkada upload cheyandi (File Manager zip upload + extract, leda git clone)
  python3 -m venv .venv
  .venv/bin/pip install -r requirements.txt
  cp .env.example .env      # WP creds, GEMINI keys, TELEGRAM creds pettandi
  .venv/bin/python run.py --deploy-check     # anni green ravali
  .venv/bin/python run.py --check-wp         # WordPress login ok-a?
```

cPanel → **Cron Jobs** → add (paths ni mee username tho marchandi):
```
0 * * * *      cd /home/<user>/bot && /home/<user>/bot/.venv/bin/python run.py >> log/cron.log 2>&1
*/5 * * * *    cd /home/<user>/bot && /home/<user>/bot/.venv/bin/python run.py --approval-poll >> log/approval.log 2>&1
0 7 * * *      cd /home/<user>/bot && /home/<user>/bot/.venv/bin/python run.py --guardian >> log/guardian.log 2>&1
0 3 * * 0      cd /home/<user>/bot && /home/<user>/bot/.venv/bin/python run.py --site-audit >> log/audit.log 2>&1
30 3 * * 0     cd /home/<user>/bot && /home/<user>/bot/.venv/bin/python tools/prune_media.py --days 30 --apply >> log/prune.log 2>&1
```
Note: bot posts still pass the **human-review gate** (draft + Telegram approval)
— cron only *prepares* posts. Approval taps reach the bot within ~5 minutes
(cron rhythm) instead of instantly — adi okkate shared-hosting tradeoff.

**Python version note:** bot ki Python 3.10+ kavali (`run.py --deploy-check`
cheptundi). cPanel terminal lo `python3 --version` 3.10 kanna thakkuva unte,
hosting support ni adagandi (CloudLinux Python Selector / alt-python) —
code marchalsina pani ledu.

**Free alternative to MilesWeb cron:** GitHub Actions schedule (`ci/github-actions-tests.yml`
shows the pattern). Caveats that are real: scheduled workflows only fire from the
**default branch**, are **best-effort** (15–45 min delay is normal), private repos on
the free plan share **2,000 minutes/month**, and schedules in repos with no activity for
60 days get disabled. So: MilesWeb cron = predictable; GitHub Actions = free backup.

## 3) Ads — "ఏదీ miss అవ్వదు" (never missed)

* Owner ads: `ads/inventory.json` file lo (bot chaduvutundi — SPONSORED +
  `rel="sponsored nofollow"`).
* Every public page (home + policy pages) already carries a labelled SPONSORED slot.
* Rotation: `ads/rotation.json` remembers when each ad last ran → **every active ad
  gets its turn**; a category mismatch falls back instead of silently dropping the slot.
* Strict mode (only category-matched ads): `.env` → `AD_FALLBACK_ALWAYS=0`.
* Safety that stays on: max 2 ads/post (`MAX_PERSONAL_AD_SLOTS`; auto 1 once
  `ADSENSE_APPROVED=1`), no ad near a link, CLS-safe wrapper, no clickbait, no fake clicks.

## 4) Storage — numbers, not worries

Measured in this repo: **public site ~300 KB**, `state.db` ~40 KB.
A 1200×675 JPEG (quality 86) post image ≈ **150–250 KB** → 1 post/day ≈ **6 MB/month,
~75 MB/year** locally; WordPress media lives in MilesWeb disk (50 GB base plan →
years of headroom).

Keep it flat:
```
python tools/prune_media.py                    # report
python tools/prune_media.py --days 30 --apply  # delete local images older than 30 days
python tools/prune_media.py --db-vacuum --apply
```
Published WordPress media is never touched — only local working copies.

## 5) Honest limits (shared hosting)

* **Approval latency ~5 min**: cron rhythm (not instant daemon). Drafts wait for
  you — emi auto-publish avvadu.
* **No long-lived processes**: shared hosting kills background daemons — anduke
  bot antha cron jobs ga design ayyindi (v74). Heavy concurrent traffic
  (lakhs of visitors) vasthe VPS/Cloud ki move avvachu — bot code ade.
* No code can guarantee Google rankings, AdSense approval or revenue — the gates reduce
  mistakes; final numbers come from your own Search Console / AdSense account.

---
*Last updated: v74 (2026-09-19) · cron-only bot · tested with `python run.py --test-all`.*
