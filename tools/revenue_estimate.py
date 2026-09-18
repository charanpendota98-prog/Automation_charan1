#!/usr/bin/env python3
"""Ad revenue estimator — studentup.in (v53).

"Oka 10k views vasthe manaku entha vasthundi?" — ee tool adi realistic ga cheptundi.

Do not overpromise: numbers are ranges from public 2026 benchmarks for Indian
traffic, not a guarantee. AdSense line uses blended page RPM for the
jobs/education niche (Indian traffic); direct line uses the LIVE rate card
printed on preview/pages/advertise.html (single source of truth).

Usage:
    .venv/bin/python tools/revenue_estimate.py                # 10k views/month
    .venv/bin/python tools/revenue_estimate.py --views 100000
    .venv/bin/python tools/revenue_estimate.py --views 10k --json
"""
from __future__ import annotations

import argparse
import io
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ADVERTISE = ROOT / "preview" / "pages" / "advertise.html"

# Blended page RPM (₹ per 1,000 pageviews), Indian traffic, jobs/education niche.
# 2026 public benchmarks: India general ₹50-250 RPM; Jobs & Education $0.10-$2.00
# per 1,000 (≈₹9-₹180); AdSense pays per impression/click, never per "view".
RPM_BANDS = (
    ("జాగ్రత్త (conservative)", 40),
    ("సాధారణ (realistic)", 90),
    ("మంచి (strong)", 150),
    ("అత్యుత్తమ (best case)", 250),
)

# Google Display (India, 2026 avg) ≈ ₹50 CPM — market reference for advertisers.
DISPLAY_CPM_INR = 50

# How many paid slots a site of this size can realistically sell per month.
FILL_BANDS = (
    (25_000, 0, 1),
    (100_000, 1, 3),
    (300_000, 3, 6),
    (float("inf"), 6, 12),
)


def parse_rate_card(path: Path = ADVERTISE) -> list[dict]:
    """Live rate card table → [{'slot','price','bundle'}] (single source of truth)."""
    html = io.open(path, encoding="utf-8").read()
    table = re.search(r"<table>.*?</table>", html, re.S)
    if not table:
        raise SystemExit(f"rate card table dorakaledu: {path}")
    slots = []
    for row in re.findall(r"<tr>(.*?)</tr>", table.group(0), re.S):
        name = re.search(r"<b>([^<]+)</b>", row)
        price = re.search(r"<b>₹([\d,]+)</b>", row)
        if not name or not price:
            continue
        slots.append({
            "slot": name.group(1).strip(),
            "price": int(price.group(1).replace(",", "")),
            "bundle": False,
        })
    if len(slots) < 5:
        raise SystemExit("rate card lo 5+ slots undali")
    top = max(s["price"] for s in slots)
    for s in slots:
        s["bundle"] = s["price"] == top and len(slots) > 1
    return slots


def parse_views(text: str) -> int:
    t = str(text).strip().lower().replace(",", "")
    mult = 1
    if t.endswith("k"):
        mult, t = 1_000, t[:-1]
    elif t.endswith("l") or t.endswith("lak"):
        mult, t = 100_000, t.rstrip("lak")
    elif t.endswith("m"):
        mult, t = 1_000_000, t[:-1]
    return int(float(t) * mult)


def adsense_table(views: int) -> list[dict]:
    per_1k = views / 1000.0
    return [{"band": name, "rpm": rpm, "revenue": int(round(per_1k * rpm))}
            for name, rpm in RPM_BANDS]


def fill_range(views: int) -> tuple[int, int]:
    for cap, lo, hi in FILL_BANDS:
        if views <= cap:
            return lo, hi
    return 6, 12


def direct_table(views: int) -> dict:
    slots = parse_rate_card()
    singles = [s for s in slots if not s["bundle"]]
    bundle = next((s for s in slots if s["bundle"]), None)
    lo, hi = fill_range(views)
    cheapest = min(s["price"] for s in singles)
    avg = int(round(sum(s["price"] for s in singles) / len(singles)))
    return {
        "slots": slots,
        "cheapest_single": cheapest,
        "avg_single": avg,
        "bundle": bundle["price"] if bundle else None,
        "fill": (lo, hi),
        "conservative": lo * cheapest,
        "realistic": hi * avg,
    }


def market_reference(views: int) -> dict:
    """What an advertiser would pay for the same impressions on Google Display."""
    return {"cpm": DISPLAY_CPM_INR, "value": int(round(views / 1000.0 * DISPLAY_CPM_INR))}


def totals(views: int) -> dict:
    ads = {b["band"]: b["revenue"] for b in adsense_table(views)}
    direct = direct_table(views)
    low = ads["జాగ్రత్త (conservative)"] + direct["conservative"]
    high = ads["మంచి (strong)"] + direct["realistic"]
    return {"low": low, "high": high, "adsense": ads, "direct": direct}


def pricing_advice(views: int) -> list[str]:
    if views < 25_000:
        return [
            "ఇప్పుడు: స్టార్టర్ ధర — సైడ్‌బార్ ₹500–₹1,000 · ఇన్-ఫీడ్ ₹1,000/నెల (trust build avvali)",
            "లక్ష్యం: రోజూ 800+ views (నెలకు 25k) → అప్పుడు ఫుల్ రేట్ కార్డ్ పనిచేస్తుంది",
        ]
    if views < 100_000:
        return [
            "ఇప్పుడు: రేట్ కార్డ్‌లో కింది స్లాట్లు ₹1,000–₹2,000 కి అమ్మండి (2–3 స్పాన్సర్లు)",
            "లక్ష్యం: నెలకు 1 లక్ష → ₹3,000–₹4,000 స్లాట్లు అమ్మగలరు",
        ]
    if views < 300_000:
        return [
            "ఇప్పుడు: ఫుల్ రేట్ కార్డ్ (₹1,000–₹4,000) + ఫుల్ ప్యాకేజీ ₹8,000 — 3–4 స్పాన్సర్లు",
            "AdSense కూడా గుర్తించదగ్గ స్థాయికి వస్తుంది — రెండూ కలిపి",
        ]
    return [
        "ఇప్పుడు: రేట్ కార్డ్ + ప్యాకేజీ + స్పాన్సర్డ్ ఆర్టికల్స్ (₹8,000–₹15,000/ఆర్టికల్)",
        "ధరలు 30–50% పెంచొచ్చు; 6–12 స్పాన్సర్లు + AdSense = రెండు పెద్ద లైన్లు",
    ]


def scale_rows() -> list[dict]:
    rows = []
    for v in (10_000, 25_000, 50_000, 100_000, 300_000, 1_000_000):
        t = totals(v)
        ads = t["adsense"]
        rows.append({
            "views": v,
            "adsense_low": ads["జాగ్రత్త (conservative)"],
            "adsense_high": ads["అత్యుత్తమ (best case)"],
            "direct_low": t["direct"]["conservative"],
            "direct_high": t["direct"]["realistic"],
            "total_low": t["low"],
            "total_high": t["high"],
        })
    return rows


def human(n: int) -> str:
    s = f"{n:,}"
    return s


def render(views: int) -> str:
    t = totals(views)
    direct = t["direct"]
    ref = market_reference(views)
    out = []
    A = out.append
    A("=" * 74)
    A(f"  REVENUE ESTIMATE — నెలకు {human(views)} page views (studentup.in)")
    A("=" * 74)
    A("")
    A(f"  ఈ ట్రాఫిక్‌కు AdSense (Indian jobs/education RPM ranges):")
    for b in adsense_table(views):
        A(f"    {b['band']:<26} ₹{b['rpm']:>3}/1000 views  →  ₹{human(b['revenue'])}/నెల")
    A("")
    A(f"  Direct (private) sponsors — LIVE rate card nunchi:")
    for s in direct["slots"]:
        tag = " (bundle)" if s["bundle"] else ""
        A(f"    {s['slot']}{tag:<0}  ₹{human(s['price'])}/నెల")
    A(f"    ఇప్పుడు అమ్మగలిగే స్లాట్లు: {direct['fill'][0]}–{direct['fill'][1]} (ఈ ట్రాఫిక్ స్థాయికి)")
    A(f"    → conservative ₹{human(direct['conservative'])} · realistic ₹{human(direct['realistic'])}/నెల")
    A("")
    A(f"  House ads (మన సొంత ప్రచురణలు): ₹0 — ఇవి ఆదాయం కాదు, మన quiz/exam కి ట్రాఫిక్.")
    A(f"  Advertiser market reference: Google Display ₹{ref['cpm']} CPM → ఈ views విలువ ₹{human(ref['value'])}")
    A("")
    A("-" * 74)
    A(f"  ⇒ మొత్తం నెలవారీ అంచనా (realistic band):  ₹{human(t['low'])} — ₹{human(t['high'])}")
    A("-" * 74)
    A("")
    A("  ధరల సలహా (traffic batti):")
    for line in pricing_advice(views):
        A(f"    • {line}")
    A("")
    A("  Scale (నెలవారీ views → AdSense + direct = మొత్తం):")
    A("    {:>10}  {:>19}  {:>19}  {:>19}".format("views", "AdSense", "Direct", "మొత్తం"))
    for r in scale_rows():
        A("    {:>10}  {:>19}  {:>19}  {:>19}".format(
            human(r["views"]),
            f"₹{human(r['adsense_low'])}–₹{human(r['adsense_high'])}",
            f"₹{human(r['direct_low'])}–₹{human(r['direct_high'])}",
            f"₹{human(r['total_low'])}–₹{human(r['total_high'])}"))
    A("")
    A("  ⚠️  ఇవి 2026 public benchmarks (Indian traffic) ఆధారంగా అంచనాలు — AdSense approval,")
    A("      ranking, sponsor sales ఏవీ గ్యారంటీ కావు. నిజమైన సంఖ్యలు AdSense dashboard,")
    A("      Search Console మరియు sponsor contracts లోనే కనిపిస్తాయి.")
    A("      AdSense pay chesedi impressions/clicks కి; 'view' కి కాదు.")
    A("=" * 74)
    return "\n".join(out)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="studentup.in ad revenue estimator")
    ap.add_argument("--views", default="10000",
                    help="నెలకు page views (10000 / 10k / 1l / 3l / 1m)")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    args = ap.parse_args(argv)
    views = parse_views(args.views)
    if views <= 0:
        raise SystemExit("views > 0 undali")
    if args.json:
        print(json.dumps({"views": views, "totals": totals(views),
                          "scale": scale_rows(), "market": market_reference(views)},
                         ensure_ascii=False, indent=2))
    else:
        print(render(views))
    return 0


if __name__ == "__main__":
    sys.exit(main())
