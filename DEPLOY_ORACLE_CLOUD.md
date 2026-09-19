# Oracle Cloud (Always Free) vs MilesWeb — edi ekkada run cheyyali

Ee doc = "motham deploy ayyaka edi ekkada, crash avvakunda ela, money ela" — clear answer.

## 0) Short answer (TL;DR)

| Part | Best place | Enduku |
|---|---|---|
| **Website (Telugu pages, ads, poll UI)** | **MilesWeb** `public_html` (static) leda WordPress | Static HTML ki 0 maintenance; WordPress ni cPanel 1-click |
| **WordPress blog + plugins (Rank Math etc.)** | **MilesWeb** | WP shared hosting ki perfect fit |
| **Exam portal + daily poll (`/exam`, `/admin`, `/poll`)** | **Oracle Cloud Always Free VM** (systemd + Caddy HTTPS) | 24×7 process, automatic restart, mee data mee control lo |
| **Auto-blogger bot (deep research + NotebookLM)** | **Oracle Cloud VM** (systemd timer) | Heavy multi-source work + venv + long runs; shared hosting cron ki limit |
| **Cron / backups / watchdog** | Oracle VM (systemd timers) | 5-cron limit undadu, 2-min checks possible |
| **Database** | Oracle VM disk (SQLite) + nightly backup | Chinna data (MBs) — SQLite saripothundi |

**Rendu kalipi vaadadam best:** MilesWeb = public face (website, WP, ads) · Oracle = engine room
(portal, bot, watchdog). Rendu okkati iddamani lera — MilesWeb lone anni pani cheyyagalavu
(portal WSGI tho: `DEPLOY_MILESWEB.md`), kaani bot heavy runs + 24×7 portal ki Oracle VM
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
     80/tcp 0.0.0.0/0   (HTTP → Caddy redirect)
     443/tcp 0.0.0.0/0  (HTTPS)
     ⛔ 8080/22 ni public ga open cheyyakandi (22 ni mee IP ki matrame)
4. SSH: ssh ubuntu@<public-ip>
     sudo apt update && sudo apt install -y git
     git clone https://github.com/charanpendota98-prog/Automation_charan1.git
     cd Automation_charan1
     sudo DOMAIN=portal.studentup.in bash deploy/install-vps.sh
5. Watchdog ON (crash-proof):
     sudo cp deploy/su-watchdog.sh /opt/studentup/deploy/ && sudo chmod +x /opt/studentup/deploy/su-watchdog.sh
     sudo cp deploy/systemd/su-watchdog.service deploy/systemd/su-watchdog.timer /etc/systemd/system/
     sudo systemctl daemon-reload && sudo systemctl enable --now su-watchdog.timer
6. Verify:
     curl -s https://portal.studentup.in/healthz
     sudo systemctl status exam-portal su-watchdog.timer
     python run.py --deploy-check
```
Ubuntu ARM lo iptables rules kuda kavali (Oracle images lo default deny untundi):
```
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 80 -j ACCEPT
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 443 -j ACCEPT
sudo netfilter-persistent save
```

## 3) "Crash avvakunda" — 7 layers (code lo unnayi)

| # | Layer | Enti chestundi |
|---|---|---|
| 1 | **systemd `Restart=always`** | Process chachina 3 sec lo automatic malli start (`deploy/exam-portal.service`) |
| 2 | **Watchdog timer (2 min)** | `/healthz` check → 3 consecutive failures ayyaka **restart + Telegram alert**; disk/memory/load/TLS expiry alerts (`deploy/su-watchdog.sh`) |
| 3 | **Health endpoint** | `/healthz` → `{"ok":true}` — monitor ki, watchdog ki okkate source of truth |
| 4 | **Alerts (throttled)** | 30 min lo okkate alert — spam ledu, kaani crash gurtu thappadu |
| 5 | **Auto-heal proof** | Watchdog ni live test chesanu: fail count → `DRY-RUN: would restart exam-portal` → `portal recovered` |
| 6 | **Backups + prune** | `deploy/backup.sh` nightly DB/state backup; `tools/prune_media.py --days 30 --apply` disk clean; SQLite `VACUUM` |
| 7 | **Graceful degradation** | Poll/portal down unte website "⚠️ పోల్ అందుబాటులో లేదు" ani chupistundi — page crash avvadu |

Ivi raka **uptime monitor** add cheyandi (free): UptimeRobot / BetterStack → `https://portal.studentup.in/healthz`
ki 1-minute checks + email/Telegram alerts. Idi external check (VM motham down aithe kuda telustundi).

## 4) Money: ads + sponsors (highest, kaani policy-safe)

```
Revenue lines (ivi matrame):
  1. Google AdSense  → ADSENSE_APPROVED=1 ayyaka auto ON (max 1 personal ad/post)
  2. Direct sponsors → admin console → "📢 ప్రకటనలు" → college banner / coaching /
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
eki guarantee ledu**. Final numbers mee AdSense/Search Console lo ne. (Ee doc lo unna 5 gates +
watchdog mistakes ni taggistayi, magic cheyyavu.)

## 5) Edaina inkedi kavali ante

| Situation | Recommendation |
|---|---|
| Chinna start, tight budget | MilesWeb lone anni (`DEPLOY_MILESWEB.md` — WSGI portal + cron) |
| Portfolio/platform build | MilesWeb (website+WP) + Oracle VM (portal + bot + watchdog) ← **recommended** |
| Students exam concurrent — 100+ same time | Oracle PAYG 4 OCPU/24 GB leda ₹500/నెల VPS; SQLite → Postgres ki move |
| Zero-maintenance | Website static ga MilesWeb, bot GitHub Actions (free, kaani 15–45 min delay + default-branch rule) |

---
*Last updated: v51 (2026-09-18) · watchdog live-tested (dry-run auto-heal) · free-tier limits verified against 2026 sources.*
