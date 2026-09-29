# -*- coding: utf-8 -*-
"""v164 — revenue plan (GSC × AdSense join)."""
from __future__ import annotations

from pathlib import Path

from autoblog import revenue_plan as rp

ROOT = Path(__file__).resolve().parents[1]

GSC = ("Page,Clicks,Impressions,CTR,Position\n"
       "https://x.in/a,120,9000,1.33%,3.2\n"
       "https://x.in/b,15,4200,0.36%,12.4\n")
ADS = ('Page,Pageviews,Estimated earnings (INR)\n'
       '/a,5000,"1,200.00"\n'
       '/b,900,60.00\n')


def _files(tmp_path):
    g, a = tmp_path / "g.csv", tmp_path / "a.csv"
    g.write_text(GSC, encoding="utf-8")
    a.write_text(ADS, encoding="utf-8")
    return g, a


def test_full_urls_and_paths_match(tmp_path):
    g, a = _files(tmp_path)
    rep = rp.build(rp.read_gsc(g), rp.read_adsense(a))
    assert rep["matched_pages"] == 2, "GSC full URL vs AdSense path join avvatledu"
    print("      GSC full URLs join with AdSense paths ✔")


def test_no_double_counting_per_url(tmp_path):
    g, a = _files(tmp_path)
    rep = rp.build(rp.read_gsc(g), rp.read_adsense(a))
    organic = [x for x in rep["actions"] if x["type"] in ("CTR", "PAGE2")]
    urls = [x["url"] for x in organic]
    assert len(urls) == len(set(urls)), f"oke URL ki rendu organic actions: {urls}"
    total = round(sum(x["gain_inr"] for x in rep["actions"]), 2)
    assert total == rep["upside_inr"]
    print("      one organic action per URL — upside is not inflated ✔")


def test_ctr_curve_is_calibrated_from_own_data():
    gsc = {f"/p{i}": {"clicks": 300.0, "impressions": 1000.0, "position": 3.0}
           for i in range(5)}
    curve = rp.calibrate(gsc)
    assert abs(curve[3] - 0.30) < 0.01, f"sonta data nunchi calibrate avvaledu: {curve[3]}"
    thin = {"/p": {"clicks": 300.0, "impressions": 1000.0, "position": 3.0}}
    assert rp.calibrate(thin)[3] == rp._CTR_CURVE[3], "1 page meeda curve marchindi"
    print("      CTR curve calibrates from our own data, ignores thin samples ✔")


def test_low_volume_pages_are_ignored(tmp_path):
    g = tmp_path / "g.csv"
    a = tmp_path / "a.csv"
    g.write_text("Page,Clicks,Impressions,CTR,Position\n/a,0,50,0%,30\n", encoding="utf-8")
    a.write_text("Page,Pageviews,Revenue\n/a,40,1.00\n", encoding="utf-8")
    rep = rp.build(rp.read_gsc(g), rp.read_adsense(a))
    assert not rep["actions"], "noise meeda action ichindi"
    print("      pages below the volume floor produce no advice ✔")


def test_rpm_gap_uses_the_sites_own_average(tmp_path):
    g, a = _files(tmp_path)
    rep = rp.build(rp.read_gsc(g), rp.read_adsense(a))
    rpm_rows = [x for x in rep["actions"] if x["type"] == "RPM"]
    assert rpm_rows and rpm_rows[0]["url"] == "/b"
    assert rep["site_rpm"] > 0
    print("      RPM gaps are measured against the site's own average ✔")


def test_cli_refuses_without_both_exports():
    assert rp.run_cli("", "") == 1, "data lekunda plan ichindi"
    print("      no data => no plan, by design ✔")


def test_flag_documented():
    main = (ROOT / "autoblog" / "main.py").read_text(encoding="utf-8")
    assert '"--revenue-plan"' in main and "args.revenue_plan" in main
    for name in ("README.md", "MANUAL_ADVANCED_CHECKLIST.md", "GO_LIVE_CHECKLIST.md"):
        assert "--revenue-plan" in (ROOT / name).read_text(encoding="utf-8"), name
    print("      --revenue-plan documented in all 3 docs ✔")
