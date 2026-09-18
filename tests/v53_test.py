# -*- coding: utf-8 -*-
"""v53 tests — revenue estimator ("10k views vasthe entha vasthundi?").

Checks that the number-crunching tool is honest (ranges, no guarantee),
pulled from the LIVE rate card (single source of truth) and that house ads
are never counted as revenue.

Offline only. Run: python tests/v53_test.py   (also via python run.py --test-all)
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tools import revenue_estimate as rev            # noqa: E402

ADV = ROOT / "preview" / "pages" / "advertise.html"


def test_tool_and_rate_card():
    assert rev.ADVERTISE == ADV and ADV.exists(), "advertise page dorakaledu"
    slots = rev.parse_rate_card()
    assert len(slots) == 6, f"6 slots undali, vachhindi {len(slots)}"
    prices = sorted(s["price"] for s in slots)
    assert prices == [1000, 2000, 3000, 3500, 4000, 8000], prices
    bundles = [s for s in slots if s["bundle"]]
    assert len(bundles) == 1 and bundles[0]["price"] == 8000, "full package okate bundle"


def test_live_rate_card_prices_match_page():
    """Tool price lu page meeda unna ₹ numbers tho exact ga match avvali."""
    html = io.open(ADV, encoding="utf-8").read()
    for s in rev.parse_rate_card():
        assert f"₹{s['price']:,}" in html, f"page lo ₹{s['price']:,} kanipinchaledu"
        assert s["slot"] in html, f"slot peru page lo ledu: {s['slot']}"


def test_adsense_math():
    a = {b["band"]: b["revenue"] for b in rev.adsense_table(10_000)}
    assert a["జాగ్రత్త (conservative)"] == 400, a
    assert a["సాధారణ (realistic)"] == 900, a
    assert a["మంచి (strong)"] == 1_500, a
    assert a["అత్యుత్తమ (best case)"] == 2_500, a
    # 1 lakh views → RPM line linear ga scale avvali
    big = {b["band"]: b["revenue"] for b in rev.adsense_table(100_000)}
    assert big["సాధారణ (realistic)"] == 9_000 and big["అత్యుత్తమ (best case)"] == 25_000


def test_views_parsing():
    assert rev.parse_views("10000") == 10_000
    assert rev.parse_views("10k") == 10_000
    assert rev.parse_views("10,000") == 10_000
    assert rev.parse_views("1l") == 100_000
    assert rev.parse_views("1m") == 1_000_000


def test_10k_views_realistic_band():
    t = rev.totals(10_000)
    assert t["low"] == 400, t["low"]                      # AdSense conservative only
    assert 3_000 <= t["high"] <= 8_000, t["high"]         # strong AdSense + 1 sponsor
    d = t["direct"]
    assert d["fill"] == (0, 1), "10k views ki 0–1 sponsor realistic"
    assert d["cheapest_single"] == 1_000 and d["bundle"] == 8_000


def test_fill_bands_grow_with_traffic():
    assert rev.fill_range(10_000) == (0, 1)
    assert rev.fill_range(50_000) == (1, 3)
    assert rev.fill_range(300_000) == (3, 6)
    assert rev.fill_range(1_000_000) == (6, 12)


def test_scale_table_covers_growth():
    rows = rev.scale_rows()
    assert [r["views"] for r in rows] == [10_000, 25_000, 50_000, 100_000, 300_000, 1_000_000]
    for r in rows:
        assert r["total_low"] <= r["total_high"], r
        assert r["adsense_low"] <= r["adsense_high"], r
    assert rows[0]["total_high"] < rows[-1]["total_low"]   # scale avvali


def test_market_reference():
    ref = rev.market_reference(10_000)
    assert ref["cpm"] == rev.DISPLAY_CPM_INR == 50
    assert ref["value"] == 500, ref


def test_house_ads_never_counted_as_revenue():
    """House ads = mana sonta promos → ₹0 revenue (funnel matrame)."""
    t = rev.totals(10_000)
    assert t["low"] == rev.adsense_table(10_000)[0]["revenue"] + t["direct"]["conservative"]
    text = rev.render(10_000)
    assert "House ads" in text and "₹0" in text, "house ads ₹0 ani cheppali"


def test_output_is_honest_no_guarantee():
    text = rev.render(10_000)
    assert "గ్యారంటీ కావు" in text, "no-guarantee line undali"
    assert "dashboard" in text and "impressions/clicks" in text.replace("\n", "")
    assert "10,000" in text


def test_cli_json_and_text():
    import subprocess
    py = sys.executable
    out = subprocess.run([py, str(ROOT / "tools" / "revenue_estimate.py"), "--views", "50k", "--json"],
                         capture_output=True, text=True, cwd=str(ROOT))
    assert out.returncode == 0, out.stderr
    data = json.loads(out.stdout)
    assert data["views"] == 50_000 and data["market"]["value"] == 2_500
    assert len(data["scale"]) == 6
    txt = subprocess.run([py, str(ROOT / "tools" / "revenue_estimate.py")],
                         capture_output=True, text=True, cwd=str(ROOT))
    assert txt.returncode == 0 and "REVENUE ESTIMATE" in txt.stdout
    assert "₹400" in txt.stdout and "₹4,200" in txt.stdout, "10k views default band"


def main():
    print("=" * 64)
    print("  v53 — REVENUE ESTIMATOR (10k views = entha?)")
    print("=" * 64)
    tests = [
        ("tool + live rate card (6 slots, ₹1,000–₹8,000)", test_tool_and_rate_card),
        ("prices = page meeda unna ₹ numbers (single source)", test_live_rate_card_prices_match_page),
        ("AdSense math (₹40/90/150/250 RPM → ₹400…₹2,500 @10k)", test_adsense_math),
        ("views parsing (10k / 1l / 1m / commas)", test_views_parsing),
        ("10k views realistic band (₹400–₹4,200)", test_10k_views_realistic_band),
        ("sponsor fill bands scale tho perugutayi", test_fill_bands_grow_with_traffic),
        ("scale table (10k → 10 lakh views)", test_scale_table_covers_growth),
        ("market reference (Google Display ₹50 CPM)", test_market_reference),
        ("house ads revenue lo count avvavu (₹0)", test_house_ads_never_counted_as_revenue),
        ("output honest — no guarantee + dashboard line", test_output_is_honest_no_guarantee),
        ("CLI text + --json rendu pani chestayi", test_cli_json_and_text),
    ]
    failed = 0
    for name, fn in tests:
        try:
            fn()
            print(f"  {name} ✔")
        except AssertionError as exc:
            failed += 1
            print(f"  {name} ✘  {exc}")
        except Exception as exc:  # noqa: BLE001
            failed += 1
            print(f"  {name} ✘  {type(exc).__name__}: {exc}")
    print("-" * 64)
    if failed:
        print(f"  {failed} TEST(S) FAILED ✘")
        return 1
    print("ALL v53 REVENUE-ESTIMATOR TESTS PASSED ✔")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
