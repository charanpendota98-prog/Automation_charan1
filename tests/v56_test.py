# -*- coding: utf-8 -*-
"""v56 tests — ad-network expansion ("50k dataka ivanni apply cheyyocha? 2x avutaya?").

Checks:
  * the plan tool's eligibility logic (pageviews vs SESSIONS vs Tier-1 share)
  * uplift is reported as a sane range and never as an automatic 2x claim
  * premium networks are flagged exclusive (AdSense replace avutundi)
  * multi-network ads.txt (partner lines from ads/ads_txt_extra.txt)
  * the honest doc + thresholds table exist

Offline only. Run: python tests/v56_test.py   (also via python run.py --test-all)
"""
from __future__ import annotations

import io
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tools import ad_network_plan as plan            # noqa: E402

PLAN_DOC = ROOT / "AD_NETWORKS_PLAN.md"
EXTRA = ROOT / "ads" / "ads_txt_extra.txt"
BUILDER = ROOT / "tools" / "build_policy_pages.py"
ADS_TXT = ROOT / "preview" / "ads.txt"
PY = sys.executable


def _rows(views, sessions=None, tier1=0.05):
    sessions = sessions if sessions is not None else plan.default_sessions(views)
    return {r["key"]: r for r in plan.assess(views, sessions, tier1)}


def _build(env_extra=None):
    env = dict(os.environ)
    env.pop("ADSENSE_CLIENT_ID", None)
    if env_extra:
        env.update(env_extra)
    out = subprocess.run([PY, str(BUILDER)], capture_output=True, text=True,
                         cwd=str(ROOT), env=env)
    assert out.returncode == 0, out.stderr[-300:]
    return out.stdout


def test_network_catalog():
    assert len(plan.NETWORKS) == 6
    keys = {n["key"] for n in plan.NETWORKS}
    assert keys == {"adsense", "ezoic", "monumetric", "adversal", "raptive", "mediavine"}
    rapt = next(n for n in plan.NETWORKS if n["key"] == "raptive")
    media = next(n for n in plan.NETWORKS if n["key"] == "mediavine")
    assert rapt["min_views"] == 25_000, "Raptive 2026 lo 25k pageviews"
    assert media["min_sessions"] == 50_000 and media["min_views"] == 0, \
        "Mediavine laskinchidi SESSIONS (50k)"
    assert rapt["tier1"] == 0.5 and media["tier1"] == 0.5


def test_eligibility_at_10k_views():
    r = _rows(10_000)                      # 6,250 sessions, 5% Tier-1
    assert r["adsense"]["eligible"] and r["ezoic"]["eligible"]
    assert not r["monumetric"]["eligible"], "30% Tier-1 lekunda Monumetric kaadu"
    assert not r["raptive"]["eligible"] and any("pageviews" in x for x in r["raptive"]["reasons"])
    assert not r["mediavine"]["eligible"]
    assert not r["adversal"]["eligible"], "50k pageviews kavali"


def test_eligibility_at_30k_views_with_tier1():
    r = _rows(30_000, sessions=18_000, tier1=0.55)
    assert r["raptive"]["eligible"], "25k views + 55% Tier-1 → Raptive eligible"
    assert not r["mediavine"]["eligible"], "50k sessions lekunda Mediavine kaadu"
    assert r["raptive"]["rpm"] == (600, 3000), "Tier-1 unte premium band vadali"


def test_eligibility_at_100k_views_60k_sessions():
    r = _rows(100_000, sessions=60_000, tier1=0.60)
    assert r["raptive"]["eligible"] and r["mediavine"]["eligible"] and r["adversal"]["eligible"]
    assert r["mediavine"]["revenue_low"] >= 80_000, r["mediavine"]  # 100 × ₹800
    # sessions tho counting — 50k pageviews + 30k sessions tho Mediavine raadu
    r2 = _rows(50_000, sessions=30_000, tier1=0.60)
    assert not r2["mediavine"]["eligible"]


def test_uplift_is_a_sane_range():
    rows = plan.assess(10_000, plan.default_sessions(10_000), 0.05)
    base = next(r for r in rows if r["key"] == "adsense")
    ezoic = next(r for r in rows if r["key"] == "ezoic")
    lo, hi = sorted(plan.uplift(base, ezoic))
    assert 0 < lo <= hi < 400, (lo, hi)
    text = plan.render(10_000, plan.default_sessions(10_000), 0.05)
    assert "automatic 2x KAADU" in text, "2x automatic kaadu ani cheppali"
    assert "exclusive" in text and "Tier-1" in text
    assert "గ్యారంటీ కావు" in text


def test_mediavine_sessions_note_and_unlock_tips():
    text = plan.render(50_000, 30_000, 0.5)
    assert "sessions" in text
    tips = plan.next_unlock(plan.assess(50_000, 30_000, 0.5), 50_000, 30_000, 0.5)
    assert any("Mediavine" in t and "sessions" in t for t in tips), tips
    low = plan.next_unlock(plan.assess(10_000, 6_250, 0.05), 10_000, 6_250, 0.05)
    assert any("Tier-1" in t for t in low), low


def test_cli_json_and_text():
    out = subprocess.run([PY, str(ROOT / "tools" / "ad_network_plan.py"),
                          "--views", "50k", "--tier1", "0.3", "--json"],
                         capture_output=True, text=True, cwd=str(ROOT))
    assert out.returncode == 0, out.stderr[-300:]
    data = json.loads(out.stdout)
    assert data["views"] == 50_000 and data["tier1"] == 0.3
    assert len(data["networks"]) == 6 and "uplift" in data and "next" in data
    txt = subprocess.run([PY, str(ROOT / "tools" / "ad_network_plan.py"), "--views", "50k"],
                         capture_output=True, text=True, cwd=str(ROOT))
    assert txt.returncode == 0 and "AD-NETWORK PLAN" in txt.stdout


def test_partner_ads_txt_lines():
    assert EXTRA.exists(), "ads/ads_txt_extra.txt undali (partner lines paste cheyyadaniki)"
    base = EXTRA.read_text(encoding="utf-8")
    assert "#" in base and "google.com," in base, "examples comments lo unna format"
    try:
        EXTRA.write_text(base + "ezoic.com, 12345, DIRECT\n", encoding="utf-8")
        out = _build({"ADSENSE_CLIENT_ID": "ca-pub-1234567890123456"})
        assert "partners(1)" in out, out[-160:]
        text = ADS_TXT.read_text(encoding="utf-8")
        body = [ln.strip() for ln in text.splitlines() if ln.strip() and not ln.startswith("#")]
        assert "google.com, pub-1234567890123456, DIRECT, f08c47fec0942fa0" in body
        assert "ezoic.com, 12345, DIRECT" in body, body
        # comment lines never leak into ads.txt body
        assert not any("paste cheyyandi" in ln for ln in body)
    finally:
        EXTRA.write_text(base, encoding="utf-8")
        _build()
    body = [ln.strip() for ln in ADS_TXT.read_text(encoding="utf-8").splitlines()
            if ln.strip() and not ln.startswith("#")]
    assert body == [], f"restore tarvata ads.txt khali undali: {body}"


def test_doc_has_thresholds_and_honesty():
    text = io.open(PLAN_DOC, encoding="utf-8").read()
    for needle in ("25,000 pageviews", "50,000 sessions", "10,000 pageviews",
                   "+30% – +70%", "exclusive", "2x", "గ్యారంటీ కావు", "ads_txt_extra.txt"):
        assert needle in text, f"doc lo ledu: {needle}"


def main():
    print("=" * 64)
    print("  v56 — AD NETWORKS (50k tarvata enti? 2x avutaya?)")
    print("=" * 64)
    tests = [
        ("network catalog + 2026 thresholds", test_network_catalog),
        ("10k views: AdSense + Ezoic eligible, premium kadu", test_eligibility_at_10k_views),
        ("30k views + 55% Tier-1 → Raptive eligible (premium band)", test_eligibility_at_30k_views_with_tier1),
        ("100k views / 60k sessions → Mediavine + Raptive", test_eligibility_at_100k_views_60k_sessions),
        ("uplift range sane + 'automatic 2x KAADU' line", test_uplift_is_a_sane_range),
        ("sessions vs pageviews note + unlock tips", test_mediavine_sessions_note_and_unlock_tips),
        ("CLI text + --json rendu pani chestayi", test_cli_json_and_text),
        ("multi-network ads.txt (partner lines, comments skip)", test_partner_ads_txt_lines),
        ("doc: thresholds + uplift + honesty", test_doc_has_thresholds_and_honesty),
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
    print("ALL v56 AD-NETWORK TESTS PASSED ✔")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
