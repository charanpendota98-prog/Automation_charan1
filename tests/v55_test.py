# -*- coding: utf-8 -*-
"""v55 tests — ads-only revenue: ads.txt + the ads ladder ("ads tho entha vastundi").

Real levers checked:
  * preview/ads.txt exists, is honest while AdSense is unapproved and flips to the
    real publisher line the moment ADSENSE_CLIENT_ID is set (IAB format).
  * robots.txt never blocks /ads.txt and allows Mediapartners-Google.
  * adsense_kit.ads_txt_status() reports live / placeholder / warn / missing.
  * tools/revenue_estimate.py --ads-only prints the ads ladder (no leads line).
  * ad-safety defaults stay intact (approval gate off, Auto Ads on, cap 2).

Offline only. Run: python tests/v55_test.py   (also via python run.py --test-all)
"""
from __future__ import annotations

import io
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from autoblog import adsense_kit, config            # noqa: E402
from tools import revenue_estimate as rev            # noqa: E402

BUILDER = ROOT / "tools" / "build_policy_pages.py"
ADS_TXT = ROOT / "preview" / "ads.txt"
ROBOTS = ROOT / "preview" / "robots.txt"
PY = sys.executable
LIVE_ID = "ca-pub-1234567890123456"
LINE_RE = re.compile(r"^google\.com, pub-\d{10,20}, DIRECT, f08c47fec0942fa0$")


def _build(env_extra=None):
    env = dict(os.environ)
    env.pop("ADSENSE_CLIENT_ID", None)
    env.pop("ADSENSE_CLIENT", None)
    if env_extra:
        env.update(env_extra)
    out = subprocess.run([PY, str(BUILDER)], capture_output=True, text=True, cwd=str(ROOT), env=env)
    assert out.returncode == 0, out.stderr[-400:]
    return out.stdout


def _restore_placeholder():
    _build()


def test_ads_txt_ships_honest_placeholder():
    assert ADS_TXT.exists(), "preview/ads.txt undali (host cheyyalsina file)"
    text = ADS_TXT.read_text(encoding="utf-8")
    assert "IAB ads.txt standard" in text
    assert not any(LINE_RE.match(ln.strip()) for ln in text.splitlines()), \
        "approval lekunda real publisher line undakudadu"
    assert "placeholder" in text.lower()
    assert "ADSENSE_CLIENT_ID" in text


def test_ads_txt_flips_to_live_line():
    try:
        out = _build({"ADSENSE_CLIENT_ID": LIVE_ID})
        assert "ads.txt (live)" in out, out[-200:]
        text = ADS_TXT.read_text(encoding="utf-8")
        line = next(ln.strip() for ln in text.splitlines() if ln.strip().startswith("google.com,"))
        assert LINE_RE.match(line), line
        assert "pub-1234567890123456" in line
        assert adsense_kit.ads_txt_status()[0] == "live"
    finally:
        _restore_placeholder()
    assert adsense_kit.ads_txt_status()[0] == "placeholder", "placeholder restore avvali"


def test_ads_txt_rejects_bad_id():
    try:
        _build({"ADSENSE_CLIENT_ID": "ca-pub-abc"})
        text = ADS_TXT.read_text(encoding="utf-8")
        assert not any(ln.strip().lower().startswith("google.com,") for ln in text.splitlines())
        assert "placeholder" in text.lower()
    finally:
        _restore_placeholder()


def test_ads_txt_status_states():
    tmp = Path(tempfile.mkdtemp(prefix="v55-"))
    missing = tmp / "nope.txt"
    assert adsense_kit.ads_txt_status(missing)[0] == "missing"
    warn_file = tmp / "ads.txt"
    warn_file.write_text("google.com, pub-999, DIRECT, f08c47fec0942fa0\n", encoding="utf-8")
    assert adsense_kit.ads_txt_status(warn_file)[0] == "warn"
    good = tmp / "good.txt"
    good.write_text("# hdr\ngoogle.com, pub-1234567890123456, DIRECT, f08c47fec0942fa0\n",
                    encoding="utf-8")
    state, detail = adsense_kit.ads_txt_status(good)
    assert state in ("live", "warn") and "pub-1234567890123456" in detail
    empty = tmp / "empty.txt"
    empty.write_text("# nothing here\n", encoding="utf-8")
    assert adsense_kit.ads_txt_status(empty)[0] == "warn"


def test_robots_allows_ads_txt_and_adsense_crawler():
    text = ROBOTS.read_text(encoding="utf-8")
    assert re.search(r"User-agent: Mediapartners-Google\s*\nAllow: /", text), \
        "Mediapartners-Google (AdSense crawler) allow undali"
    assert not re.search(r"Disallow:\s*/ads\.txt", text), "/ads.txt block avvakudadu"
    assert not re.search(r"Disallow:\s*/\s*$", text, re.M), "motham site block avvakudadu"


def test_builder_idempotent():
    first = _build()
    a = ADS_TXT.read_text(encoding="utf-8")
    second = _build()
    b = ADS_TXT.read_text(encoding="utf-8")
    assert a == b, "rendu sarlu run chesthe ads.txt marakudadu"
    assert "ads.txt (placeholder)" in first and "ads.txt (placeholder)" in second


def test_estimator_ads_only_ladder():
    out = subprocess.run([PY, str(ROOT / "tools" / "revenue_estimate.py"),
                          "--views", "10k", "--ads-only"], capture_output=True, text=True, cwd=str(ROOT))
    assert out.returncode == 0, out.stderr[-300:]
    text = out.stdout
    assert "ADS-ONLY REVENUE LADDER" in text
    assert "₹400–₹2,500" in text and "₹0–₹2,700" in text and "₹400–₹4,200" in text
    assert "₹46,000–₹182,400" in text, "10 lakh views row"
    assert "గ్యారంటీ కావు" in text
    assert "proportion" in text
    # leads line thappithe (ads-only lo premium/leads undakudadu)
    assert "లీడ్లు" not in text.split("Idi 'ads tho'")[0]


def test_ads_only_numbers_match_tiers():
    t = rev.tiers(100_000)
    ads = rev.adsense_table(100_000)
    d = rev.direct_table(100_000)
    assert ads[0]["revenue"] == t["baseline"][0] and ads[-1]["revenue"] == t["baseline"][1]
    assert t["standard"] == (ads[0]["revenue"] + d["conservative"],
                             ads[2]["revenue"] + d["realistic"])


def test_ad_safety_defaults_intact():
    assert config.ADSENSE_APPROVED is False, "approval gate default off undali"
    assert config.ADSENSE_AUTO_ADS is True, "Auto Ads loader default on"
    assert getattr(config, "MAX_PERSONAL_AD_SLOTS", 2) == 2, "posta ki 2 ads cap"
    assert config.AD_MANAGER_ENABLED is True and config.AD_FALLBACK_ALWAYS is True
    assert config.HOUSE_AD_ENABLED is True


def test_docs_mention_ads_txt():
    for rel in ("GO_LIVE_CHECKLIST.md", "AD_REVENUE_PLAYBOOK.md", "MANUAL_ADVANCED_CHECKLIST.md"):
        text = io.open(ROOT / rel, encoding="utf-8").read()
        assert "ads.txt" in text, f"{rel} lo ads.txt step ledu"


def main():
    print("=" * 64)
    print("  v55 — ADS-ONLY REVENUE (ads.txt + ads ladder)")
    print("=" * 64)
    tests = [
        ("ads.txt ships honest (placeholder, IAB header)", test_ads_txt_ships_honest_placeholder),
        ("ADSENSE_CLIENT_ID set → live publisher line", test_ads_txt_flips_to_live_line),
        ("bad client id → placeholder (fake line ledu)", test_ads_txt_rejects_bad_id),
        ("ads_txt_status: live/placeholder/warn/missing", test_ads_txt_status_states),
        ("robots.txt: /ads.txt open + Mediapartners-Google OK", test_robots_allows_ads_txt_and_adsense_crawler),
        ("builder idempotent (rendu sarlu same file)", test_builder_idempotent),
        ("--ads-only ladder (10k → 10L views)", test_estimator_ads_only_ladder),
        ("ads-only numbers ⇄ tiers numbers match", test_ads_only_numbers_match_tiers),
        ("ad-safety defaults intact (gate off · cap 2)", test_ad_safety_defaults_intact),
        ("docs lo ads.txt step undi", test_docs_mention_ads_txt),
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
    _restore_placeholder()          # suite end lo placeholder state ki tirigi pettali
    print("-" * 64)
    if failed:
        print(f"  {failed} TEST(S) FAILED ✘")
        return 1
    print("ALL v55 ADS-ONLY REVENUE TESTS PASSED ✔")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
