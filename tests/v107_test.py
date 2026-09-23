# -*- coding: utf-8 -*-
"""v107 — direct GSC API sync and alert logic."""
from __future__ import annotations
import json, sys, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from autoblog import config, gsc_api  # noqa: E402
SUITES_EXPECTED = 89


def test_api_rows_become_refresh_pages():
    rows = gsc_api._rows_to_pages([{"keys": ["https://studentup.in/a"], "clicks": 20, "impressions": 1000, "position": 8}])
    assert rows[0]["url"].endswith("/a") and rows[0]["ctr"] == .02 and rows[0]["score"] > 0
    print("      GSC API rows converted to v102 priority format ✔")


def test_position_ctr_alerts():
    old = {"https://studentup.in/a": {"url": "https://studentup.in/a", "impressions": 1000, "position": 5, "ctr": .10}}
    new = [{"url": "https://studentup.in/a", "impressions": 1000, "position": 9, "ctr": .05}]
    alerts = gsc_api._alerts(old, new)
    assert alerts and alerts[0]["position_drop"] == 4
    print("      28-day position/CTR deterioration alert generated ✔")


def test_low_impression_noise_ignored():
    old = {"https://studentup.in/a": {"url": "https://studentup.in/a", "impressions": 10, "position": 5, "ctr": .10}}
    new = [{"url": "https://studentup.in/a", "impressions": 10, "position": 20, "ctr": 0}]
    assert not gsc_api._alerts(old, new)
    print("      low-impression noise suppressed ✔")


def test_missing_credentials_clear():
    old = config.GSC_SERVICE_ACCOUNT_FILE
    config.GSC_SERVICE_ACCOUNT_FILE = ""
    config.GSC_SERVICE_ACCOUNT_JSON = ""
    try:
        try: gsc_api._token(); raise AssertionError("missing credentials accepted")
        except RuntimeError as exc: assert "credentials missing" in str(exc)
    finally: config.GSC_SERVICE_ACCOUNT_FILE = old
    print("      missing API credentials fail clearly, no fake sync ✔")


def test_cli_wired_and_docs():
    src = (ROOT / "autoblog" / "main.py").read_text(encoding="utf-8")
    r = (ROOT / "README.md").read_text(encoding="utf-8")
    m = (ROOT / "MANUAL_ADVANCED_CHECKLIST.md").read_text(encoding="utf-8")
    assert "--gsc-sync" in src and "gsc_api as _ga" in src
    assert "### v107" in r and "PART 64" in m and "89/89" in r and "89/89" in m
    print("      GSC API CLI + README/PART 64/87-87 pinned ✔")

TESTS = [("rows", test_api_rows_become_refresh_pages), ("alerts", test_position_ctr_alerts),
         ("noise", test_low_impression_noise_ignored), ("credentials", test_missing_credentials_clear),
         ("CLI/docs", test_cli_wired_and_docs)]
def main():
    bad=0
    for n,f in TESTS:
        try: f(); print(f"  {n} ✔")
        except Exception as e: bad+=1; print(f"  {n} ✘ {type(e).__name__}: {e}")
    print("-"*70); print("ALL v107 GSC API TESTS PASSED ✔" if not bad else f"{bad} TEST(S) FAILED ✘"); return int(bool(bad))
if __name__ == "__main__": raise SystemExit(main())
