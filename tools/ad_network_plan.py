#!/usr/bin/env python3
"""Ad-network expansion plan — studentup.in (v56).

"50k dataka avere ads ki apply cheyyocha? appudu 2x avutaya?" ki nijamaina jawabu.

Public 2026 facts (sources in AD_NETWORKS_PLAN.md):
  * Raptive (ex-AdThrive)  : 25,000 pageviews/month + ~50% Tier-1 traffic
  * Mediavine              : 50,000 sessions/month (~65-80k pageviews) + Tier-1 majority
  * Monumetric             : 10,000 pageviews/month
  * Ezoic (Access Now)     : no strict minimum, needs AdSense in good standing
  * Adversal / Revcontent  : 50,000 pageviews/month
  * Google AdSense         : no traffic minimum (approval-based)

RPM bands below are ₹/1000 pageviews for an INDIAN-traffic Telugu site — the
premium networks pay 2-4x only when a large share of traffic is Tier-1
(US/UK/CA/AU/NZ), so their band is applied only when that condition is met.

Usage:
    .venv/bin/python tools/ad_network_plan.py                      # 10k views, 5% Tier-1
    .venv/bin/python tools/ad_network_plan.py --views 50k --tier1 0.6
    .venv/bin/python tools/ad_network_plan.py --views 100k --sessions 60000 --json
"""
from __future__ import annotations

import argparse
import json
import sys

# name, min pageviews/month, min sessions/month, min Tier-1 share, (rpm_low, rpm_high), note
NETWORKS = (
    dict(key="adsense", name="Google AdSense", min_views=0, min_sessions=0, tier1=0.0,
         rpm=(40, 250), note="approx-based; no traffic minimum; base demand"),
    dict(key="ezoic", name="Ezoic (Access Now)", min_views=0, min_sessions=1_000, tier1=0.0,
         rpm=(60, 350), note="header bidding + AdX; AdSense 'good standing' kavali"),
    dict(key="monumetric", name="Monumetric", min_views=10_000, min_sessions=0, tier1=0.30,
         rpm=(80, 400), note="10k pageviews; US-centric demand, per-view India lo takkuva"),
    dict(key="adversal", name="Adversal / Revcontent", min_views=50_000, min_sessions=0, tier1=0.30,
         rpm=(40, 150), note="50k pageviews; native/video fill (AdSense ki add-on)"),
    dict(key="raptive", name="Raptive (ex-AdThrive)", min_views=25_000, min_sessions=0,
         tier1=0.50, rpm=(250, 900), rpm_tier1=(600, 3000),
         note="25k pageviews + ~50% Tier-1; managed, exclusive"),
    dict(key="mediavine", name="Mediavine", min_views=0, min_sessions=50_000, tier1=0.50,
         rpm=(250, 900), rpm_tier1=(800, 3500),
         note="50k sessions (~65-80k pageviews) + Tier-1 majority; Net-65"),
)


def parse_views(text) -> int:
    t = str(text).strip().lower().replace(",", "")
    mult = 1
    if t.endswith("k"):
        mult, t = 1_000, t[:-1]
    elif t.endswith("l"):
        mult, t = 100_000, t[:-1]
    elif t.endswith("m"):
        mult, t = 1_000_000, t[:-1]
    return int(float(t) * mult)


def default_sessions(views: int) -> int:
    """Typical 1.6 pageviews/session (Mediavine counts sessions, not views)."""
    return int(views / 1.6)


def assess(views: int, sessions: int, tier1: float) -> list[dict]:
    rows = []
    for n in NETWORKS:
        reasons = []
        if views < n["min_views"]:
            reasons.append(f"{n['min_views']:,}+ pageviews kavali")
        if sessions < n["min_sessions"]:
            reasons.append(f"{n['min_sessions']:,}+ sessions kavali")
        if tier1 < n["tier1"]:
            reasons.append(f"{int(n['tier1'] * 100)}%+ Tier-1 traffic kavali")
        eligible = not reasons
        rpm = n.get("rpm_tier1", n["rpm"]) if (eligible and tier1 >= n["tier1"]) else n["rpm"]
        rows.append({
            "key": n["key"], "name": n["name"], "eligible": eligible, "reasons": reasons,
            "rpm": rpm, "revenue_low": int(views / 1000 * rpm[0]),
            "revenue_high": int(views / 1000 * rpm[1]),
            "note": n["note"],
            "needs": {"pageviews": n["min_views"], "sessions": n["min_sessions"],
                      "tier1": n["tier1"]},
        })
    return rows


def uplift(base: dict, other: dict) -> tuple[int, int]:
    """Percentage uplift range vs the base network (AdSense)."""
    lo = int(round((other["revenue_low"] / base["revenue_low"] - 1) * 100)) if base["revenue_low"] else 0
    hi = int(round((other["revenue_high"] / base["revenue_high"] - 1) * 100)) if base["revenue_high"] else 0
    return lo, hi


def next_unlock(rows: list[dict], views: int, sessions: int, tier1: float) -> list[str]:
    tips = []
    for r in rows:
        if r["eligible"]:
            continue
        need = r["needs"]
        if need["pageviews"] and views < need["pageviews"]:
            tips.append(f"{r['name']}: {need['pageviews']:,} pageviews/నెల కావాలి "
                        f"(ఇప్పుడు {views:,}) → +{need['pageviews'] - views:,} views")
        elif need["sessions"] and sessions < need["sessions"]:
            tips.append(f"{r['name']}: {need['sessions']:,} sessions/నెల కావాలి "
                        f"(ఇప్పుడు {sessions:,}) — sessions = ప్రతి విజిట్‌లో ఎక్కువ పేజీలు")
        elif need["tier1"] and tier1 < need["tier1"]:
            tips.append(f"{r['name']}: Tier-1 (US/UK/Gulf) ట్రాఫిక్ "
                        f"{int(need['tier1'] * 100)}%+ కావాలి (ఇప్పుడు {int(tier1 * 100)}%) — "
                        f"విదేశీ ఉద్యోగాలు/NRI కంటెంట్‌తో పెరుగుతుంది")
    return tips


def human(n: int) -> str:
    return f"{n:,}"


def render(views: int, sessions: int, tier1: float) -> str:
    rows = assess(views, sessions, tier1)
    base = next(r for r in rows if r["key"] == "adsense")
    out = []
    A = out.append
    A("=" * 78)
    A(f"  AD-NETWORK PLAN — {human(views)} pageviews · {human(sessions)} sessions "
      f"· Tier-1 {int(tier1 * 100)}%")
    A("=" * 78)
    A("")
    A(f"  {'నెట్‌వర్క్':<24} {'స్థితి':<12} {'RPM (₹/1000)':<16} {'నెలవారీ అంచనా':<20}")
    for r in rows:
        status = "✅ eligible" if r["eligible"] else "⏳ " + r["reasons"][0][:22]
        A(f"  {r['name']:<24} {status:<12} "
          f"{('₹' + human(r['rpm'][0]) + '–₹' + human(r['rpm'][1])):<16} "
          f"{('₹' + human(r['revenue_low']) + '–₹' + human(r['revenue_high'])):<20}")
    A("")
    A("  ── '2x avutaya?' ki nijamaina jawabu ──")
    PREMIUM = ("raptive", "mediavine")
    typical = None
    for r in rows:
        if r["eligible"] and r["key"] not in ("adsense",) + PREMIUM:
            lo, hi = sorted(uplift(base, r))
            if typical is None or lo > typical[1]:
                typical = (r, lo, hi)
    if typical:
        r, lo, hi = typical
        A(f"  • Header-bidding network ({r['name']}) add chesthe: **+{lo}% – +{hi}%** "
          f"(AdSense baseline ₹{human(base['revenue_low'])} → ₹{human(r['revenue_low'])}/నెల నుంచి)")
        A("    Typical 30–70% · automatic 2x KAADU — rendu networks okate demand koraku poti")
        A("    padatayi. AdSense + idi parallel ga pani chestayi.")
    else:
        A("  • Ippudu add cheyyagalige second network ledu (AdSense + sponsor slots matrame).")
    prem = [r for r in rows if r["eligible"] and r["key"] in PREMIUM]
    if prem:
        for r in prem:
            extra = " (Tier-1 band)" if r["rpm"] == r.get("rpm_tier1", None) else ""
            A(f"  • ⭐ {r['name']} ipudu eligible → ₹{human(r['revenue_low'])}–"
              f"₹{human(r['revenue_high'])}/నెల{extra} — kaani **exclusive** (AdSense ni replace "
              f"chestundi, parallel kaadu) + Tier-1 share ni maintain cheyyali.")
    else:
        A("  • 2x–4x ఇచ్చే Mediavine/Raptive ki **Tier-1 ట్రాఫిక్ షేర్** (US/UK/CA/AU) kavali —")
        A("    విదేశీ/NRI ఉద్యోగాలు, IELTS, visa కంటెంట్ add chesthe adi perugutundi.")
        A("    ⚠️ Avi **exclusive** networks — join ayyaka AdSense/vere ads parallel ga undavu.")
    A("  • AdSense/network kanna mundu: **direct sponsors (rate card) 4–5× per-view** — adi")
    A("    ippude ready, traffic koraku wait cheyyalsina avasaram ledu.")
    A("")
    tips = next_unlock(rows, views, sessions, tier1)
    if tips:
        A("  ── Next tier unlock cheyyadaniki ──")
        for t in tips:
            A(f"    • {t}")
        A("")
    A("  ⚠️  Thresholds public ga update avutayi (Raptive 2025 lo 100k → 25k ki taggindi). Ivi")
    A("      benchmarks — approval, RPM, revenue ఏవీ గ్యారంటీ కావు. Apply cheyyakamundu aa")
    A("      network terms + mee GA4 numbers verify chesukondi (AD_NETWORKS_PLAN.md).")
    A("=" * 78)
    return "\n".join(out)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="ad-network expansion plan (studentup.in)")
    ap.add_argument("--views", default="10000", help="నెలవారీ pageviews (10000 / 50k / 1l)")
    ap.add_argument("--sessions", default="", help="నెలవారీ sessions (default: views/1.6)")
    ap.add_argument("--tier1", type=float, default=0.05,
                    help="Tier-1 (US/UK/CA/AU/NZ) ట్రాఫిక్ షేర్ 0–1 (default 0.05)")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    views = parse_views(args.views)
    sessions = parse_views(args.sessions) if args.sessions else default_sessions(views)
    tier1 = max(0.0, min(1.0, float(args.tier1)))
    if args.json:
        rows = assess(views, sessions, tier1)
        base = next(r for r in rows if r["key"] == "adsense")
        print(json.dumps({"views": views, "sessions": sessions, "tier1": tier1,
                          "networks": rows,
                          "uplift": {r["key"]: uplift(base, r) for r in rows},
                          "next": next_unlock(rows, views, sessions, tier1)},
                         ensure_ascii=False, indent=2))
    else:
        print(render(views, sessions, tier1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
