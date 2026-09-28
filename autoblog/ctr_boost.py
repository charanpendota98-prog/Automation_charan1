# -*- coding: utf-8 -*-
"""v149 — CTR opportunity finder.

Rankings alone do not pay: a page sitting at position 4 with a 2% CTR is losing
most of its traffic to the title above it. This tool compares each page's real
CTR against a published position-CTR benchmark and ranks the pages where a
better title/description would win the most extra clicks.

Honest by design:

* It **never rewrites anything**. It prints suggestions the owner applies by hand.
* Benchmarks are a documented curve, not a promise — the report says "estimate".
* It works from a Search Console CSV export, so no API key is required.
"""
from __future__ import annotations

import csv
import logging
from pathlib import Path
from typing import Dict, Iterable, List, Optional

log = logging.getLogger(__name__)

#: Rough organic CTR by average position (share of clicks per impression).
#: Public industry benchmarks; used only to rank opportunities, never quoted
#: to readers as a fact about this site.
POSITION_CTR = {
    1: 0.275, 2: 0.152, 3: 0.098, 4: 0.070, 5: 0.053,
    6: 0.041, 7: 0.033, 8: 0.027, 9: 0.023, 10: 0.020,
}
TAIL_CTR = 0.011  # positions 11-20
MIN_IMPRESSIONS = 200


def expected_ctr(position: float) -> float:
    if position <= 0:
        return 0.0
    if position > 20:
        return 0.004
    slot = int(round(position))
    return POSITION_CTR.get(slot, TAIL_CTR)


def suggestions_for(query: str, title: str = "") -> List[str]:
    """Concrete, policy-safe title ideas for a job/exam query."""
    q = (query or "").strip()
    base = title.strip() or q.title()
    tips: List[str] = []
    low = (base + " " + q).lower()

    if not any(y in low for y in ("2025", "2026", "2027")):
        tips.append("Title lo year add cheyandi (freshness = higher CTR)")
    if "last date" not in low and "last-date" not in low:
        tips.append("‘Last Date’ add cheyandi — urgency clicks penchutundi")
    if not any(w in low for w in ("posts", "vacancies", "vacancy")):
        tips.append("Vacancy count add cheyandi (e.g. ‘783 Posts’) — number titles ekkuva click avutayi")
    if "apply" not in low:
        tips.append("‘Apply Online’ / ‘Direct Link’ add cheyandi — intent match avutundi")
    if len(base) > 60:
        tips.append(f"Title {len(base)} chars undi — 60 lopala trim cheyandi, lekapote Google cut chestundi")
    if not tips:
        tips.append("Title already strong — meta description lo eligibility + last date pettandi")
    return tips


def analyse(rows: Iterable[Dict], min_impressions: int = MIN_IMPRESSIONS) -> Dict:
    """Rank CTR opportunities. rows: query/page, clicks, impressions, ctr, position."""
    out: List[Dict] = []
    for row in rows:
        try:
            impressions = int(float(row.get("impressions") or 0))
            clicks = int(float(row.get("clicks") or 0))
            position = float(row.get("position") or 0)
        except (TypeError, ValueError):
            continue
        if impressions < min_impressions or position <= 0:
            continue
        ctr = clicks / impressions if impressions else 0.0
        target = expected_ctr(position)
        if ctr >= target:
            continue
        extra = (target - ctr) * impressions
        if extra < 1:
            continue
        key = str(row.get("query") or row.get("page") or "").strip()
        out.append({
            "key": key,
            "impressions": impressions,
            "clicks": clicks,
            "ctr": round(ctr, 4),
            "benchmark_ctr": round(target, 4),
            "position": round(position, 1),
            "extra_clicks_estimate": int(round(extra)),
            "suggestions": suggestions_for(key, str(row.get("title") or "")),
        })
    out.sort(key=lambda r: r["extra_clicks_estimate"], reverse=True)
    total = sum(r["extra_clicks_estimate"] for r in out)
    return {
        "version": "v149",
        "pages": len(out),
        "extra_clicks_estimate": total,
        "opportunities": out,
        "status": "review" if out else "clean",
    }


def load_csv(path: Path) -> List[Dict]:
    """Read a Search Console CSV export (Queries or Pages tab)."""
    rows: List[Dict] = []
    with Path(path).open(newline="", encoding="utf-8-sig") as fh:
        for raw in csv.DictReader(fh):
            row = { (k or "").strip().lower(): (v or "").strip() for k, v in raw.items() }
            ctr = row.get("ctr", "").replace("%", "").strip()
            rows.append({
                "query": row.get("top queries") or row.get("query") or "",
                "page": row.get("top pages") or row.get("page") or "",
                "clicks": row.get("clicks") or 0,
                "impressions": row.get("impressions") or 0,
                "ctr": ctr,
                "position": row.get("position") or row.get("average position") or 0,
            })
    return rows


def run_cli(csv_path: str = "", min_impressions: int = MIN_IMPRESSIONS) -> int:
    if not csv_path:
        print("=" * 74)
        print("  CTR BOOST: Search Console CSV kavali")
        print("=" * 74)
        print("  Search Console → Performance → Export → CSV, taruvata:")
        print("  python run.py --ctr-boost Queries.csv")
        return 1

    path = Path(csv_path)
    if not path.exists():
        print(f"❌ File ledu: {path}")
        return 1

    report = analyse(load_csv(path), min_impressions)
    print("=" * 74)
    print(f"  CTR OPPORTUNITIES: {report['pages']} pages · ~{report['extra_clicks_estimate']} extra clicks/month (estimate)")
    print("=" * 74)
    if not report["opportunities"]:
        print("  ✅ CTR already at or above the position benchmark — nothing to fix.")
        return 0
    for row in report["opportunities"][:15]:
        print(f"\n  {row['key'][:70]}")
        print(f"    pos {row['position']} · {row['impressions']} impressions · "
              f"CTR {row['ctr']:.1%} vs benchmark {row['benchmark_ctr']:.1%} "
              f"→ ~{row['extra_clicks_estimate']} clicks lost")
        for tip in row["suggestions"]:
            print(f"      · {tip}")
    print("\n  Note: benchmark = public position-CTR curve. Titles meere edit cheyali;")
    print("  ee tool automatic ga emi maarchadu.")
    return 0
