# Oracle Cloud (Always Free) vs MilesWeb — edi ekkada run cheyyali

Ee doc = "motham deploy ayyaka edi ekkada, crash avvakunda ela, money ela" — clear answer.

## 0) Short answer (TL;DR)

| Part | Best place | Enduku |
|---|---|---|
| **Website (WordPress blog + theme)** | **MilesWeb** (WordPress install) | WP shared hosting ki perfect fit |
| **Static preview site (optional mirror)** | **MilesWeb** `public_html` leda Oracle VM (Caddy static) | Static HTML ki 0 maintenance |
| **Auto-blogger bot (drafts + research + audits)** | **Oracle Cloud VM** (systemd timers) leda MilesWeb cron | Oracle: heavy runs + venv + long jobs; MilesWeb: simple cron (details `DEPLOY_MILESWEB.md`) |
| **Telegram approvals (✅/🗑️)** | Oracle VM daemon leda cron `--approval-poll` | Rendu chotla cron mode pani chestundi |
| **Cron / backups / watchdog** | Oracle VM (systemd timers) | 2-min checks + auto alerts possible |
| **Database** | Oracle VM disk (SQLite) + nightly backup | Chinna data (MBs) — SQLite saripothundi |

**Rendu kalipi vaadadam best:** MilesWeb = public face (website, WP, ads) · Oracle = engine room
(bot, watchdog, backups). Rendu okkati iddamani lera — MilesWeb lone anni pani cheyyagalavu
(cron-only: `DEPLOY_MILESWEB.md`), kaani heavy research runs + instant approvals ki Oracle VM
comfortable.

---

## 1) Oracle Cloud Always Free — nijamaina facts (2026)

| Item | Value | Note |
|---|---|---|
| ARM (Ampere A1) compute | **2 OCPU / 12 GB** for new pure-Always-Free tenancies (was 4/24) | 2026 lo Oracle free allocation tagginchindi; **PAYG (Pay-As-You-Go) tenancy lo 4 OCPU/24 GB free allowance intact** [1](https://terminalbytes.com/oracle-cloud-free-tier-changes-2026/) [2](https://www.reddit.com/r/oraclecloud/comments/1ubk2qy/new_always_free_tier_limits_21june2026_update/) |
| AMD micro VMs | 2 × 1/8 OCPU, 1 GB RAM | unchanged |
| Block storage | **200 GB total** | unchanged; boot volume default 50 GB |
| Outbound data | **10 TB/month** | website ki chala ekkuva |
| Cost | $0 (within limits) | **credit/debit card verification** signup lo kavali [3](https://space-node.net/blog/oracle-vps-free-tier-review-2026) |
| Region | Mumbai / Hyderabad (India) | mee users ki closest = fast |
| Risk | **Idle instances Oracle reclaim cheyyochu** + regional capacity "out of host capacity" errors | Signup timing, PAYG upgrade, leda paid micro VPS alternatives [3](https://space-node.net/blog/oracle-vps-free-tier-review-2026) |

**Nijam cheppali:** Always Free = "guaranteed VPS" kaadu — capacity, signup approval, idle-reclaim
policy meeda depend. Mission-critical ki: PAYG upgrade (free limits intact) leda ₹300–500/నెల
chinna paid VPS.

## 2) Setup (Oracle VM, ~20 nimushalu)

```
1. cloud.oracle.com → sign up (card verification) → home region: Mumbai/Hyderabad
2. Compute → Instances → Create
     Shape : VM.Standard.A1.Flex (Ampere ARM) — 2 OCPU / 12 GB (leda PAYG: 4/24)
     Image : Ubuntu 24.04 (ARM)
     Boot volume : 50 GB (200 GB varaku free)
     SSH key : mee public key add cheyandi
3. Networking → Security List → Ingress rules:
     80/tcp 0.0.0.0/0   (HTTP — static site vadithe)
     443/tcp 0.0.0.0/0  (HTTPS — static site vadithe)
     ⛔ 22 ni mee IP ki matrame open cheyandi
4. SSH: ssh ubuntu@<public-ip>
     sudo apt update && sudo apt install -y git
     git clone https://github.com/charanpendota98-prog/Automation_charan1.git
     cd Automation_charan1
     sudo DOMAIN=studentup.in bash deploy/install-vps.sh
5. Watchdog ON (crash-proof) — installer automatic ga enable chestundi:
     sudo systemctl status studentup-bot.timer su-watchdog.timer
6. Verify:
     sudo -u studentup nano /opt/studentup/.env   # WP_* / GEMINI_* / TELEGRAM_*
     sudo systemctl start studentup-bot
     sudo journalctl -u studentup-bot -n 50
     sudo -u studentup /opt/studentup/.venv/bin/python run.py --deploy-check
```
Ubuntu ARM lo iptables rules kuda kavali (Oracle images lo default deny untundi):
```
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 80 -j ACCEPT
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 443 -j ACCEPT
sudo netfilter-persistent save
```

## 3) "Crash avvakunda" — 6 layers (code lo unnayi)

| # | Layer | Enti chestundi |
|---|---|---|
| 1 | **systemd timers (`Persistent=true`)** | Missed runs catch-up (reboot tarvata kuda bot run avutundi) |
| 2 | **Watchdog timer (2 min)** | Website HTTP check + bot freshness (`state.db` 26h stale?) + disk/memory/load/TLS expiry → Telegram alerts (`deploy/su-watchdog.sh`) |
| 3 | **Alerts (throttled)** | 30 min lo okkate alert — spam ledu, kaani crash gurtu thappadu |
| 4 | **Auto-check proof** | Watchdog ni live test chesanu: dead site → `ALERT site_down`; stale bot → `ALERT bot_stale` (`tests/v51_test.py`) |
| 5 | **Backups + prune** | `deploy/backup.sh` nightly DB/state backup; `tools/prune_media.py --days 30 --apply` disk clean; SQLite `VACUUM` |
| 6 | **Graceful degradation** | Daily question/quiz 100% browser JS — server ledu kabatti down ayye scope ledu |

Ivi raka **uptime monitor** add cheyandi (free): UptimeRobot / BetterStack → `https://studentup.in/`
ki 5-minute checks + email/Telegram alerts. Idi external check (VM motham down aithe kuda telustundi).

## 4) Money: ads + sponsors (highest, kaani policy-safe)

```
Revenue lines (ivi matrame):
  1. Google AdSense  → ADSENSE_APPROVED=1 ayyaka auto ON (max 1 personal ad/post)
  2. Direct sponsors → ads/inventory.json → college banner / coaching /
                       shop / service / outsourcing partner
  3. High-value pillars (highest CPC/session value): Govt Jobs · Upcoming Exams ·
     Current Affairs · Scholarships · Results
  4. Placement (highest viewability): top leaderboard · in-feed (grid) ·
     mid-article (after quick-answer) · sidebar sticky · policy-page inline
  5. Rotation: ads/rotation.json → prathi sponsor ad ki turn (eda miss avvadu)
```
**Rules (AdSense ban raakunda):**
* SPONSORED label eppudu · `rel="sponsored nofollow"` · link pakkana ad ledu (150-char rule)
* Max 2 personal ads/post (`MAX_PERSONAL_AD_SLOTS`), AdSense approve ayyaka cap 1
* CLS-safe wrapper, no popup/interstitial, no clickbait, no fake clicks
* **Never**: "click cheyandi" ani adi, incentive clicks, ad ni content laaga dhaachesi

**Nijam:** ivi reach + CTR + sponsor value penchutayi — kaani **revenue, ranking, AdSense approval
ki guarantee ledu**. Final numbers mee AdSense/Search Console lo ne. (Ee doc lo unna gates +
watchdog mistakes ni taggistayi, magic cheyyavu.)

## 5) Edaina inkedi kavali ante

| Situation | Recommendation |
|---|---|
| Chinna start, tight budget | MilesWeb lone anni (`DEPLOY_MILESWEB.md` — cron-only bot) |
| Portfolio/platform build | MilesWeb (website+WP) + Oracle VM (bot + watchdog + backups) ← **recommended** |
| Heavy traffic / big research jobs | Oracle PAYG 4 OCPU/24 GB leda ₹500/నెల VPS |
| Zero-maintenance | Website static ga MilesWeb, bot GitHub Actions (free, kaani 15–45 min delay + default-branch rule) |

---
*Last updated: v74 (2026-09-19) · cron-only bot · watchdog live-tested (dead-site + stale-bot alerts) · free-tier limits verified against 2026 sources.*
