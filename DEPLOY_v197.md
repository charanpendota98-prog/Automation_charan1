# DEPLOY v197 — 10 nimushalu (click-by-click)

> Theme **1.9.38** · zip: `wordpress-theme/studentup-theme.zip` (134 files · 1160 KB)
> Direct download (GitHub raw):
> `https://raw.githubusercontent.com/charanpendota98-prog/Automation_charan1/arena/01a10001-automation-charan1/wordpress-theme/studentup-theme.zip`

Ee page lo unna steps **order lo** cheyyandi. Prathi step tarvata OK sign
chudandi — tappu aithe aa step ne malli cheyyandi, munduku vellakandi.

---

## 0) Mundu (2 nimushalu) — safety

| # | Pani | Ekkada |
| --- | --- | --- |
| 0.1 | **Backup** — WP Admin → (hosting lo) MilesWeb mPanel → **File Manager** → `public_html/studentup/` → `wp-content/themes/studentup` ni **Compress** chesi `studentup-backup-YYYYMMDD.zip` ga save cheyyandi | mPanel → File Manager |
| 0.2 | LiteSpeed cache off pettandi (temporary): WP Admin → **LiteSpeed Cache → Toolbox → Purge All** | WP Admin |

Rollback (eppudaina): purathana zip ni upload chesi malli activate — 2 nimushalu.

---

## 1) Theme zip upload (3 nimushalu)

1. WP Admin → **Appearance → Themes → Add New → Upload Theme**
2. **Choose File** → `studentup-theme.zip` → **Install Now**
3. **Replace current with uploaded** (leda **Activate**)

✅ Check: WP Admin → **Appearance → Themes** lo `StudentUp 1.9.38` kanipinchali
(puthana 1.9.36 undakoodadu).

---

## 2) Setup run (2 nimushalu) — quiz page + menu + options

1. WP Admin → **StudentUp** (left menu) → **Run setup now**
2. Wait — "daily-quiz page created" / "menu ready" lines chudandi

✅ Check: **Pages** lo `Daily Quiz & Polls` (slug `daily-quiz`) undali.

---

## 3) Purge + live check (2 nimushalu)

1. WP Admin → **LiteSpeed Cache → Toolbox → Purge All**
2. Browser lo: `https://studentup.in/` ni **hard refresh** (Ctrl+Shift+R · phone lo
   private tab)

✅ Check home page lo:
- Header lo **Jobs ▾ · Exams ▾ · Scholarships ▾ · Tools ▾ · More ▾** — hover/tap
  cheste **columns tho mega panel** terustundi (icons tho).
- Konchem kinda **DAILY QUIZ** card — 5 questions + "Check answers".
- Aa kinda **READER POLL** — okka option select chesi **Vote**.

---

## 4) Proof command (cPanel lo — 1 nimushalu)

mPanel → **Advanced → Cron Jobs → "Run command"** (Terminal akkarledu):

```
cd ~/bot && source venv/bin/activate && python run.py --verify-deploy --verify-notify
```

Aa report lo **11 checks**: theme version, mega menu, menu/engage JS, quiz, poll,
`/daily-quiz/`, CSS classes, sprite, sitemap, poll REST, raw-SVG regression.
- `verdict: LIVE ✔ · score 100/100` → **deploy complete** 🎉
- Fail unte report lo ne **next step** rasi untundi (zip malli upload / Run setup
  now / purge).

Report file: `~/bot/output/deploy-verify.md`

---

## 5) Tarvata (roju automatic ga jarigedi)

| Time | Pani | Command |
| --- | --- | --- |
| Radar 4×/day | kotha notifications → **drafts** | `python run.py` (cron already) |
| Morning | Telugu list → Telegram / WhatsApp | `python run.py --daily` |
| Same run lo | **[3/5] DAILY ENGAGE** — quiz draft + poll push | `DAILY_ENGAGE=1` (default) |
| Same run lo | **[4/5] AUTO-PUBLISH** — gate-pass drafts mattrame publish | `AUTO_PUBLISH_DAILY=1` (default **0 = off**) |

Auto-publish gate: official source URL + 700+ words + **Rank Math ≥ 80 readback** +
fresh draft + no placeholder → appude publish. Edaina fail aithe draft ga ne untundi
(review ki).

---

## 6) Owner pending (ivi code tho jaragavu — mee account + time)

1. **AdSense**: approval + `ADSENSE_CLIENT_ID` + `ADSENSE_APPROVED=1` + ads.txt live
   (WP Admin → StudentUp → AdSense section).
2. **Search Console**: sitemap submit (`https://studentup.in/sitemap_index.xml`) + GA4.
3. **IndexNow key**: `python run.py --index-key-gen` → key ni `.env` + site root lo.
4. CMP (AdSense → Privacy & messaging → CMP ON) — EEA/UK traffic ki.

Ee naalugu tarvata: ads revenue + Google indexing start avutundi. Ranking / traffic /
approval **Google + mee accounts + time** batti — code side motham ready.

---

## Quick troubleshooting

| Symptom | Fix |
| --- | --- |
| Mega menu kanipinchaledu | Purge All → hard refresh. Still ledu? StudentUp → options → `mega_menu` ON check |
| Quiz/poll kanipinchaledu | StudentUp → options lo `daily_quiz` / `polls` ON; front page lo "Show on front page" setting |
| `/daily-quiz/` 404 | **Run setup now** malli okkasari |
| Icons blank ga unnayi | Purge All (sprite + CSS cache) |
| 502 / site slow | LiteSpeed cache ON cheyyandi (step 3.1 reverse) |
