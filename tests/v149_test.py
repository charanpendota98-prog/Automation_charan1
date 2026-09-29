# -*- coding: utf-8 -*-
"""v149 — CTR opportunity finder (suggestions only, never auto-edits)."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from autoblog import ctr_boost  # noqa: E402

ROWS = [
    {"query": "tspsc group 2 notification", "clicks": 40, "impressions": 4000, "position": 3.2},
    {"query": "ap dsc 2026 apply online last date", "clicks": 560, "impressions": 2000, "position": 1.2},
    {"query": "tiny query", "clicks": 1, "impressions": 30, "position": 5.0},
]


def test_only_real_opportunities_are_listed():
    rep = ctr_boost.analyse(ROWS)
    keys = [r["key"] for r in rep["opportunities"]]
    assert "tspsc group 2 notification" in keys, "below-benchmark page miss ayyindi"
    assert "ap dsc 2026 apply online last date" not in keys, "already above benchmark — list cheyyakoodadu"
    assert "tiny query" not in keys, "low-impression noise filter ledu"
    print("      only genuine below-benchmark pages listed ✔")


def test_estimate_is_ranked_and_finite():
    rep = ctr_boost.analyse(ROWS)
    est = [r["extra_clicks_estimate"] for r in rep["opportunities"]]
    assert est == sorted(est, reverse=True) and all(e >= 1 for e in est)
    assert rep["extra_clicks_estimate"] == sum(est)
    print("      opportunities ranked by estimated extra clicks ✔")


def test_suggestions_are_concrete():
    tips = ctr_boost.suggestions_for("tspsc group 2 notification", "TSPSC Group 2 Notification")
    joined = " ".join(tips).lower()
    assert "year" in joined and "last date" in joined.lower()
    strong = ctr_boost.suggestions_for(
        "ssc cgl 2026 last date apply online 783 posts",
        "SSC CGL 2026 Last Date - Apply Online for 783 Posts")
    assert strong, "empty suggestion list raakoodadu"
    print("      suggestions are concrete and title-specific ✔")


def test_tool_never_edits_anything():
    src = (ROOT / "autoblog" / "ctr_boost.py").read_text(encoding="utf-8")
    for banned in ("update_post", "create_post", "wordpress_client"):
        assert banned not in src, f"CTR tool lo {banned} undakoodadu (read-only)"
    print("      read-only: no WordPress writes ✔")


def test_csv_loader_handles_gsc_export(tmp_path):
    p = tmp_path / "Queries.csv"
    p.write_text("Top queries,Clicks,Impressions,CTR,Position\n"
                 "tspsc group 2,40,4000,1%,3.2\n", encoding="utf-8")
    rows = ctr_boost.load_csv(p)
    assert rows and rows[0]["query"] == "tspsc group 2" and int(rows[0]["impressions"]) == 4000
    print("      Search Console CSV export parses ✔")


def test_cli_wired():
    src = (ROOT / "autoblog" / "main.py").read_text(encoding="utf-8")
    assert "--ctr-boost" in src and "ctr_boost as _cb" in src
    print("      run.py --ctr-boost wired ✔")


TESTS = [
    ("filter", test_only_real_opportunities_are_listed),
    ("ranking", test_estimate_is_ranked_and_finite),
    ("suggestions", test_suggestions_are_concrete),
    ("read-only", test_tool_never_edits_anything),
    ("cli", test_cli_wired),
]


def main() -> int:
    bad = 0
    for name, fn in TESTS:
        try:
            fn()
            print(f"  {name} ✔")
        except Exception as exc:  # noqa: BLE001
            bad += 1
            print(f"  {name} ✘ {type(exc).__name__}: {exc}")
    print("-" * 70)
    print("ALL v149 TESTS PASSED ✔" if not bad else f"{bad} TEST(S) FAILED ✘")
    return int(bool(bad))


if __name__ == "__main__":
    raise SystemExit(main())
