# Ad Networks Application Kit — review + apply order (v77)

> Nenu (bot) prathi network requirements ni **mana site tho review chesa**.
> Apply matram **owner account tho owner cheyyali** (login + domain verify) —
> kindha order + ready-material anni ready ga unnayi. Reach vachina ventane
>apply cheyandi — code-side emi marchalsina pani ledu.

## Verdict table (honest)

| # | Network | Min. traffic | Mana status | Verdict |
|---|---------|--------------|-------------|---------|
| 1 | **Google AdSense** | none (quality) | policy pages 6/6 · ads.txt ready · original Telugu content · no fake ads | ✅ **APPLY FIRST** (day 1) |
| 2 | **Ezoic** | none (Access Now) | Ezoic = nameserver/CDN switch — code change ZERO; AdSense approve ayyaka join | ✅ **JOIN SECOND** (RPM 2-3x jump) |
| 3 | **Media.net** | none (US/UK traffic) | mana traffic India-heavy → fill rate low; tire-1 traffic unte try | ⚠️ LATER (Tier-1 unte) |
| 4 | **Mediavine Journey** | 50k sessions/mo | install + grow ayyaka; requirements: good standing AdSense + original content | ⏳ 50k sessions tarvata |
| 5 | **Monumetric** | 10k views/mo | $99 setup (<80k views) — revenue batti decide | ⏳ 10k+ views + revenue |
| 6 | **Adsterra** | none | popunder/native — AdSense tho kalipi vadakandi (policy risk); fallback ga | ⚠️ OPTIONAL fallback |
| 7 | **Direct sponsors** | — | bot ad-manager READY (`ads/inventory.json` + demo page + rotation + reports) | ✅ inbound vachinappudu |

## Why this order (money logic)

1. **AdSense** = base approval (anni networks "AdSense good standing" adugutayi).
2. **Ezoic** = same AdSense demand + AI placements + premium partners (typical
   India education uplift 50-200% — guarantee kaadu, demand batti).
3. **Scale** → Mediavine/Monumetric (US RPMs kavali ante Tier-1 traffic penchandi:
   abroad-jobs pillar + English guides).

## Site readiness proof (reviewer ki chupinchandi)

- Policy: `/pages/privacy.html` · disclaimer · about · contact · editorial-policy · advertise
- Ads honesty: SPONSORED labels · `rel="sponsored nofollow"` · density cap (max 4/page) ·
  no auto-refresh · consent mode (CMP ready) · ads.txt auto on approval
- Content: 100% original (rewrite-distance scored — certificate per post) ·
  author box (E-E-A-T) · dates (published + modified) · news sitemap (48h + updates)
- Tech: CLS-safe reserved heights · lazy below-fold · Core Web Vitals theme

## Apply checklist (owner — 30 min)

- [ ] AdSense: account → site add → code (`ADSENSE_CLIENT_ID` + `ADSENSE_APPROVED=1` in `.env`)
- [ ] `python run.py --adsense-kit` (Auto Ads loader) + `python run.py --guardian`
- [ ] ads.txt live verify (site.com/ads.txt → `google.com, pub-XXXX, DIRECT`)
- [ ] 2-4 weeks: Ezoic join (nameserver change — host DNS lo)
- [ ] Reach milestones: Journey @50k sessions · Monumetric @10k views
- [ ] NEVER: AdSense + popunders same page · ad auto-refresh · ads on 404/thank-you

## Code switches (already built — flip only)

| .env key | Effect |
|---|---|
| `ADSENSE_CLIENT_ID=ca-pub-…` + `ADSENSE_APPROVED=1` | Auto Ads + manual units LIVE (triple-gated, pre-approval silent) |
| `ADSENSE_AUTO_ADS=0` | Auto Ads off, manual slots only |
| `AD_MANAGER_ENABLED=0` | owner ads off (posts clean) |
| `HOUSE_AD_ENABLED=0` | house promos off |
| `MAX_PERSONAL_AD_SLOTS` / theme `max_ads` | density caps |

Honest note: network approvals + RPMs = Google/partners + mee traffic quality +
time. Ee kit = fastest honest path, guarantee kaadu.
