# SET UP ALL — theme + bot (okka file, click-level)

> Theme **1.9.42** · bot v198 · created 2026-10-03 (v201 preview-parity build).
> Ee file rendu panulu cover chestundi: **(A) theme site ki**, **(B) bot hosting ki**.
> Order: A mundu (site kanipinchali), tarvata B (bot site lo rasthadu).

---

## 0) Modata: kit download (2 nimushalu)

**GitHub → repo → ee rendu zip files:**

| Enti | File | Ekkada upload |
| --- | --- | --- |
| Theme | `milesweb-kit/studentup-theme-1.9.42.zip` | WP Admin → Appearance → Themes |
| Bot | `milesweb-kit/studentup-bot-cron.zip` | cPanel → File Manager → `~/bot/` |

Direct links (branch `arena/01a10001-automation-charan1`):

```
https://raw.githubusercontent.com/charanpendota98-prog/Automation_charan1/arena/01a1035e-automation-charan1/milesweb-kit/studentup-theme-1.9.42.zip
https://raw.githubusercontent.com/charanpendota98-prog/Automation_charan1/arena/01a10001-automation-charan1/milesweb-kit/studentup-bot-cron.zip
```

**sha256 (upload tarvata verify — `sha256sum <file>`):**

| Zip | size | sha256 (mundu 16) |
| --- | --- | --- |
| studentup-theme-1.9.42.zip | 137 files · 928 KB | `933751ca13d4` |
| studentup-bot-cron.zip | 355 files · 3949 KB | `198cea49aecbb311` |
| studentup-static-site.zip (optional) | 36 files · 556 KB | `251db4308a75b51c` |
| studentup-seo-bridge-1.1.0.zip (optional) | 2 files | `2132fbe7d9653dfd` |

> Puratana **1.9.40 / 1.9.39 / 1.9.36 zip** ippudu kit lo ledu (v198 lo auto-purge) — porapatuna puratana
> zip upload cheyyakandi; version check: WP → Appearance → Themes lo **1.9.42** kanipinchali.

---

## A) THEME — 5 clicks (10 nimushalu)

1. **WP Admin** → Appearance → Themes → **Add New** → **Upload Theme** →
   `studentup-theme-1.9.42.zip` → **Install Now**.
2. Same screen lo → **Replace current with uploaded** (leda Activate). Me content,
   posts, images, settings **emi poyipokavu** — theme mattrame marutundi.
3. **WP Admin → StudentUp → Run setup now** (okka click).
   Idi chestundi: `/tools/`, `/daily-quiz/`, `/exam-calendar/`, corrections log,
   hub pages, menus, tagline/timezone, comments off, Rank Math meta — anni.
   > Ee click **lekapote** quiz/poll pages 404 istayi.
4. **LiteSpeed Cache → Purge All** (leda WP Admin top bar → Purge All).
5. Phone lo **hard refresh** (Chrome → ⋮ → Refresh / cache clear) → `studentup.in/tools/`
   open chesi chudandi.

### A-verify (okka command — mee laptop/SSH nunchi repo folder lo)

```
python run.py --verify-deploy --verify-notify
```

**`LIVE ✔ 100/100`** vasthe theme side complete. Emaina fail aithe adi **exact next step**
print chestundi (zip upload / Run setup now / purge). Offline lo (`UNREACHABLE`) vasthe
adi mee hosting/SSL state — code tappu kaadu.

---

## B) BOT — hosting lo (15 nimushalu, one-time)

1. cPanel → **File Manager** → home folder lo `bot` folder create cheyyandi.
2. `studentup-bot-cron.zip` upload → **Extract** → files `~/bot/` lo undali
   (`~/bot/studentup-bot-cron/...` lo extract aithe aa files ni `~/bot/` ki move cheyyandi).
3. **SSH** (cPanel → SSH Auth tab) leda cron "Run command" runner:

```bash
cd ~/bot
python3 --version                 # 3.10+ undali
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
mkdir -p log
.venv/bin/python run.py --doctor
```

4. **`.env`** (File Manager → `~/bot/.env` → Edit) — ee keys pettandi:

```ini
# --- WordPress (Application Password: WP Admin → Users → Profile → Application Passwords)
WP_URL=https://studentup.in
WP_USER=your-admin-username
WP_APP_PASSWORD=xxxx xxxx xxxx xxxx xxxx xxxx

# --- Gemini (aistudio.google.com → API key; 2-3 keys pedithe quota safe)
GEMINI_API_KEYS=key1,key2

# --- Telegram (BotFather → token; @userinfobot → chat id)
TELEGRAM_BOT_TOKEN=123456:ABC...
TELEGRAM_CHAT_ID=123456789

# --- roju quiz + poll push (v197)
DAILY_ENGAGE=1
ENGAGE_QUIZ_PUBLISH=0        # 1 = quiz post live ga (review avasaram ledu)

# --- auto-publish lane (v197): gate-pass aithe mattrame publish avutundi
AUTO_PUBLISH_DAILY=0         # 1 = evening auto-publish ON (safe default 0)
AUTO_PUBLISH_MIN_WORDS=700
AUTO_PUBLISH_MIN_SCORE=80

# --- optional kaani useful
INDEXNOW_KEY=your-indexnow-key
WHATSAPP_GROUP_URL=https://chat.whatsapp.com/xxxxx
```

5. cPanel → **Cron Jobs** → ee **5 core lines** paste cheyyandi
   (`<user>` ni mee cPanel username tho marchandi):

```cron
0 * * * *      cd /home/<user>/bot && /home/<user>/bot/.venv/bin/python run.py >> log/cron.log 2>&1
*/5 * * * *    cd /home/<user>/bot && /home/<user>/bot/.venv/bin/python run.py --approval-poll >> log/approval.log 2>&1
0 7 * * *      cd /home/<user>/bot && /home/<user>/bot/.venv/bin/python run.py --guardian >> log/guardian.log 2>&1
30 6 * * *     cd /home/<user>/bot && /home/<user>/bot/.venv/bin/python run.py --daily >> log/daily.log 2>&1
0 3 * * 0      cd /home/<user>/bot && /home/<user>/bot/.venv/bin/python run.py --site-audit >> log/audit.log 2>&1
```

**`--daily` (6:30 AM) lopala 5 steps automatic ga jarugutayi:**

```
[1/5] DRAFTS        research → original Telugu article → WordPress DRAFT
[2/5] GUARDIAN      site health (broken link, stale post, media)
[3/5] DAILY ENGAGE  quiz post + reader poll push
[4/5] AUTO-PUBLISH  gate-pass drafts publish (AUTO_PUBLISH_DAILY=1 unte mattrame)
[5/5] LIST + SEND   morning Telugu list → Telegram (+WhatsApp)
```

> **WP-cron job ni touch cheyyakandi:** `wp-cli cron event run --due-now` (35 * * * *)
> job alage undali — adi WordPress di, bot di kaadu.

### B-verify (rendu dry-run — emi publish avvadu)

```bash
cd ~/bot && .venv/bin/python run.py --check-wp          # WP credentials test
cd ~/bot && .venv/bin/python run.py --daily --daily-no-send   # full daily, pampakunda
```

Reudu clean ga pass aithe → bot complete. Telegram lo **✅ Publish** button kanipistundi
(approval mode) — tap cheste post live.

---

## C) Nijam enti — honest limits (v198)

| Enti | State |
| --- | --- |
| Theme code (1.9.42) | ✅ complete + 147/147 suites · jsdom 230/230 · php-lint 98/98 · parity PIN-TO-PIN · sprite gate (blank icons = build fail) |
| Bot code | ✅ complete — offline dry-run lo anni network steps graceful ga skip (no crash, no fake success) |
| Zip kit | ✅ fresh (theme 1.9.39 + bot v197/v198 modules) |
| **Live site** | ⏳ zip upload pending — mee **zip upload** tarvate 1.9.42 avutundi (ee file A section) |
| **Bot live** | ⏳ mee `~/bot` upload + `.env` + cron tarvate run avutundi (B section) |
| AdSense money | ⏳ mee AdSense account + approval (code side ready; income guarantee ledu) |
| Ranking/traffic | ⏳ rojuvari posts + time (code side ready; rank/traffic guarantee ledu) |

**Naadi cheyyagalige pani ee file lo unna steps ni tests tho prove cheyyadam matrame** —
mee server ki nenu direct ga login cheyyalenu, so A + B mee chetullo. Emaina step
fail aithe aa error message pampandi — nenu exact fix isthanu.

---

## D) Emaina tappu jarigithe (rollback)

| Problem | Fix |
| --- | --- |
| Theme site ni break chesindi | Puratana theme zip malli upload → Activate (2 nimushalu, content safe) |
| Bot posts double avutunnayi | MilesWeb lo mattrame cron undali (Oracle/vere host lo OFF cheyyandi) |
| `/tools/` 404 | WP Admin → **StudentUp → Run setup now** (malli) |
| Cache purana version chupistundi | LiteSpeed → Purge All + phone hard refresh |
| `--verify-deploy` fail | Output lo print ayye **next step** line follow avvandi (zip / setup / purge) |
