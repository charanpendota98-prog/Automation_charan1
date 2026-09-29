# -*- coding: utf-8 -*-
"""v151 — RPM report.

AdSense pays per 1000 pageviews (RPM), so the useful question is never
"how many clicks" but **which pages and which ad slots actually earn**.
This reads an AdSense/GA CSV export and prints:

  * site RPM and the honest revenue maths behind it,
  * the pages carrying the revenue (and the ones burning pageviews),
  * slots whose RPM is far below the site average — candidates to move or drop.

It reports. It never changes ad code, never injects units, never touches
WordPress: ad placement changes are the owner's call and AdSense policy
makes automated fiddling risky.
"""
from __future__ import annotations

import csv
import logging
from pathlib import Path
from typing import Dict, Iterable, List

log = logging.getLogger(__name__)

WEAK_SHARE = 0.5   # below 50% of site RPM = weak
MIN_VIEWS = 500    # ignore noise


def rpm(revenue: float, views: int) -> float:
    return (revenue / views * 1000.0) if views > 0 else 0.0


def analyse(rows: Iterable[Dict], min_views: int = MIN_VIEWS) -> Dict:
    clean: List[Dict] = []
    for row in rows:
        try:
            views = int(float(row.get("views") or 0))
            revenue = float(row.get("revenue") or 0)
        except (TypeError, ValueError):
            continue
        name = str(row.get("name") or "").strip()
        if not name or views <= 0:
            continue
        clean.append({"name": name, "views": views, "revenue": round(revenue, 2),
                      "rpm": round(rpm(revenue, views), 2)})

    total_views = sum(r["views"] for r in clean)
    total_rev = sum(r["revenue"] for r in clean)
    site_rpm = round(rpm(total_rev, total_views), 2)

    ranked = sorted(clean, key=lambda r: r["revenue"], reverse=True)
    weak = [r for r in clean
            if r["views"] >= min_views and r["rpm"] < site_rpm * WEAK_SHARE]
    weak.sort(key=lambda r: r["views"], reverse=True)

    # What the weak pages would earn at the site average — the honest upside.
    upside = sum((site_rpm - r["rpm"]) * r["views"] / 1000.0 for r in weak)

    return {
        "version": "v151",
        "rows": len(clean),
        "views": total_views,
        "revenue": round(total_rev, 2),
        "site_rpm": site_rpm,
        "top": ranked[:10],
        "weak": weak[:10],
        "upside_estimate": round(upside, 2),
        "status": "review" if weak else "clean",
    }


def load_csv(path: Path) -> List[Dict]:
    """Read an AdSense 'Pages'/'Ad units' CSV or a GA4 revenue export."""
    rows: List[Dict] = []
    with Path(path).open(newline="", encoding="utf-8-sig") as fh:
        for raw in csv.DictReader(fh):
            row = {(k or "").strip().lower(): (v or "").strip() for k, v in raw.items()}
            name = (row.get("page") or row.get("pages") or row.get("ad unit")
                    or row.get("ad units") or row.get("page path") or row.get("name") or "")
            views = (row.get("pageviews") or row.get("page views") or row.get("views")
                     or row.get("impressions") or row.get("screen page views") or 0)
            revenue = (row.get("estimated earnings") or row.get("earnings")
                       or row.get("revenue") or row.get("total ad revenue") or 0)
            rows.append({
                "name": name,
                "views": str(views).replace(",", ""),
                "revenue": str(revenue).replace(",", "").replace("₹", "").replace("$", "").strip(),
            })
    return rows


def run_cli(csv_path: str = "", min_views: int = MIN_VIEWS) -> int:
    if not csv_path:
        print("=" * 74)
        print("  RPM REPORT: AdSense CSV kavali")
        print("=" * 74)
        print("  AdSense → Reports → Pages (or Ad units) → Export CSV, taruvata:")
        print("  python run.py --rpm-report Pages.csv")
        return 1

    path = Path(csv_path)
    if not path.exists():
        print(f"❌ File ledu: {path}")
        return 1

    rep = analyse(load_csv(path), min_views)
    print("=" * 74)
    print(f"  RPM REPORT · {rep['rows']} rows · {rep['views']:,} views · "
          f"site RPM {rep['site_rpm']}")
    print("=" * 74)

    print("\n  TOP EARNERS (ivi ne inka ekkuva rayandi):")
    for r in rep["top"][:6]:
        print(f"    {r['name'][:56]:56} RPM {r['rpm']:>7} · {r['views']:>7,} views")

    if rep["weak"]:
        print(f"\n  WEAK (site RPM lo {int(WEAK_SHARE * 100)}% kanna thakkuva, traffic matram undi):")
        for r in rep["weak"][:6]:
            print(f"    {r['name'][:56]:56} RPM {r['rpm']:>7} · {r['views']:>7,} views")
        print(f"\n  Weak pages ni site average ki teeste: ~{rep['upside_estimate']} extra (estimate).")
        print("  Cheyyavalasinavi: above-fold slot check, content length penchandi,")
        print("  intent match chudandi. Ad count penchakandi — policy risk + UX debba.")
    else:
        print("\n  ✅ No page is dragging RPM down.")

    print("\n  Note: ee tool report matrame. Ad code ni automatic ga marchadu.")
    return 0
