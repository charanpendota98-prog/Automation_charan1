# -*- coding: utf-8 -*-
"""v162 — Slot lab: ad slot A/B measurement (`--slot-lab`).

`--rpm-report` cheptundi *ye page* earn chestondo. Ee module cheptundi
*ye slot configuration* earn chestondo — ade nijamaina revenue lever.

Ela pani chestundi:

  1. Theme prati visitor ni oke variant lo ne stable ga pedutundi
     (`studentup_slot_variant()` — day+IP kaadu, cookie-free stable hash).
     Variant peru ad unit name lo velthundi: `in-article-A`, `in-article-B`.
  2. 7-10 rojula taruvata meeru AdSense CSV export chestaru
     (Reports → Ad units → add "Ad unit" dimension, revenue + impressions).
  3. `python run.py --slot-lab adsense.csv` aa CSV ni chadivi prati variant
     RPM + lift compute chestundi.

**Nenu emi guess cheyyanu.** Data saripodhu ante "inka wait cheyandi" ani ne
cheptundi — chinna sample meeda winner declare cheyyadam ante random noise ni
strategy ga marchadam. Minimum 10,000 impressions per variant, and rendu
variants madhya difference noise kanna peddaga undali.

CSV columns (peru ela unna case/space matter kaadu):
    ad unit / unit / name , impressions / views / pageviews , revenue / earnings
"""
from __future__ import annotations

import csv
import math
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

MIN_IMPRESSIONS = 10_000    # per variant, before any verdict
MIN_LIFT_PCT = 5.0          # ee lopu difference = noise, winner ledu

_NAME_KEYS = ("ad unit", "ad_unit", "unit", "name", "slot", "page")
_IMP_KEYS = ("impressions", "ad impressions", "views", "pageviews", "page views")
_REV_KEYS = ("revenue", "earnings", "estimated earnings", "est. earnings")

# "in-article-A" → ("in-article", "A")
_VARIANT = re.compile(r"^(?P<slot>.+?)[-_](?P<variant>[A-Z])$")


def _pick(row: Dict[str, str], keys: Tuple[str, ...]) -> Optional[str]:
    """Column ni peru batti vetakadam.

    AdSense export headers currency/locale batti maruthayi — "Estimated
    earnings (INR)", "Revenue (₹)", "Ad impressions". Andhuke exact match
    kaadu, substring match: mundu exact, adi dorakakapothe contains.
    """
    lowered = {str(k).strip().lower(): v for k, v in row.items() if k}
    for key in keys:
        if key in lowered and str(lowered[key]).strip() != "":
            return str(lowered[key]).strip()
    for key in keys:
        for col, val in lowered.items():
            if key in col and str(val).strip() != "":
                return str(val).strip()
    return None


def _num(raw: Optional[str]) -> float:
    if raw is None:
        return 0.0
    cleaned = re.sub(r"[^\d.\-]", "", raw.replace(",", ""))
    try:
        return float(cleaned) if cleaned not in ("", "-", ".") else 0.0
    except ValueError:
        return 0.0


def parse_csv(path: Path) -> List[Dict]:
    rows: List[Dict] = []
    with path.open(newline="", encoding="utf-8-sig", errors="ignore") as fh:
        for raw in csv.DictReader(fh):
            name = _pick(raw, _NAME_KEYS)
            if not name:
                continue
            imps = int(_num(_pick(raw, _IMP_KEYS)))
            rev = _num(_pick(raw, _REV_KEYS))
            if imps <= 0:
                continue
            rows.append({"name": name, "impressions": imps, "revenue": rev})
    return rows


def group(rows: List[Dict]) -> Dict[str, Dict[str, Dict]]:
    """slot -> variant -> totals. Variant suffix lenivi skip."""
    out: Dict[str, Dict[str, Dict]] = {}
    for r in rows:
        m = _VARIANT.match(r["name"].strip())
        if not m:
            continue
        slot = m.group("slot").strip().lower()
        var = m.group("variant")
        bucket = out.setdefault(slot, {}).setdefault(
            var, {"impressions": 0, "revenue": 0.0})
        bucket["impressions"] += r["impressions"]
        bucket["revenue"] += r["revenue"]
    return out


def _rpm(revenue: float, impressions: int) -> float:
    return (revenue / impressions * 1000.0) if impressions > 0 else 0.0


def compare(variants: Dict[str, Dict]) -> Dict:
    """Okate slot lo unna variants ni compare cheyyadam."""
    table = []
    for name, v in sorted(variants.items()):
        table.append({
            "variant": name,
            "impressions": v["impressions"],
            "revenue": round(v["revenue"], 2),
            "rpm": round(_rpm(v["revenue"], v["impressions"]), 3),
        })

    thin = [t for t in table if t["impressions"] < MIN_IMPRESSIONS]
    if len(table) < 2:
        return {"table": table, "verdict": "NEED_TWO",
                "note": "rendu variants data raaledu"}
    if thin:
        need = ", ".join(
            f"{t['variant']} ki inka {MIN_IMPRESSIONS - t['impressions']:,} impressions"
            for t in thin)
        return {"table": table, "verdict": "NEED_DATA", "note": need}

    best, second = sorted(table, key=lambda t: t["rpm"], reverse=True)[:2]
    if second["rpm"] <= 0:
        return {"table": table, "verdict": "NEED_DATA",
                "note": "revenue zero — inka wait cheyandi"}
    lift = (best["rpm"] - second["rpm"]) / second["rpm"] * 100.0

    # Poisson-ish noise floor: chinna revenue counts meeda peddha lift kuda
    # random kavachu. Impressions ekkuva unte noise thakkuva.
    noise = 100.0 / math.sqrt(min(best["impressions"], second["impressions"]))
    if lift < max(MIN_LIFT_PCT, noise):
        return {"table": table, "verdict": "NO_WINNER",
                "note": f"lift {lift:.1f}% — noise floor {max(MIN_LIFT_PCT, noise):.1f}% lopu",
                "lift": round(lift, 2)}

    return {"table": table, "verdict": "WINNER", "winner": best["variant"],
            "lift": round(lift, 2),
            "note": f"{best['variant']} RPM {best['rpm']} vs {second['variant']} {second['rpm']}"}


def analyse(path: Path) -> Dict:
    rows = parse_csv(path)
    grouped = group(rows)
    return {"rows": len(rows), "slots": {s: compare(v) for s, v in grouped.items()}}


def run_cli(csv_path: str = "") -> int:
    print("=" * 74)
    print("  SLOT LAB — ad slot A/B (RPM) measurement")
    print("=" * 74)
    if not csv_path:
        print("  Setup:")
        print("   1. Theme lo slot variants ON (Appearance → StudentUp → Slot lab)")
        print("   2. 7-10 rojulu run cheyandi")
        print("   3. AdSense → Reports → Ad units → CSV export")
        print("   4. python run.py --slot-lab adsense.csv")
        print("-" * 74)
        print(f"  Verdict ki minimum {MIN_IMPRESSIONS:,} impressions per variant.")
        print("  Ala lekapothe winner cheppadam ante noise ni strategy ga marchadam.")
        return 0

    path = Path(csv_path)
    if not path.exists():
        print(f"  ❌ CSV dorakaledu: {csv_path}")
        return 1

    rep = analyse(path)
    if not rep["slots"]:
        print(f"  ⚠️  {rep['rows']} rows chadivanu, kani variant-suffix unna")
        print("      ad unit peru (udaa: in-article-A / in-article-B) dorakaledu.")
        print("      AdSense lo ad unit names ni variant tho create cheyandi.")
        return 1

    icon = {"WINNER": "🏆", "NO_WINNER": "🤝", "NEED_DATA": "⏳", "NEED_TWO": "⚠️"}
    for slot, res in sorted(rep["slots"].items()):
        print(f"\n  {slot}")
        for t in res["table"]:
            print(f"    {t['variant']}  {t['impressions']:>9,} imp   "
                  f"₹{t['revenue']:>9,.2f}   RPM {t['rpm']:.3f}")
        print(f"    {icon[res['verdict']]} {res['verdict']}: {res['note']}")
    print("-" * 74)
    winners = [s for s, r in rep["slots"].items() if r["verdict"] == "WINNER"]
    if winners:
        print(f"  {len(winners)} slot(s) lo clear winner undi — losing variant "
              f"ni theme lo off cheyandi.")
    else:
        print("  Inka clear winner ledu. Data penchandi, config marchakandi —")
        print("  test madhyalo marchithe data motham waste avutundi.")
    return 0
