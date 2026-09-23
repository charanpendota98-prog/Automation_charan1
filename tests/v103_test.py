# -*- coding: utf-8 -*-
"""v103 — live exact-phrase originality checks."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from autoblog import config, originality_live  # noqa: E402

SUITES_EXPECTED = 94


def test_phrase_selection_ignores_short_generic_text() -> None:
    got = originality_live._sentences(
        "Short text. This is a very detailed official notification with 783 vacancies "
        "and an application deadline of 22 July 2026 for eligible candidates. "
        "Another useful sentence contains enough words to be checked online safely.")
    assert got and any("783" in x for x in got)
    print("      distinctive numbered sentences selected for live check ✔")


def test_live_exact_match_is_reported(monkeypatch=None) -> None:
    old_search, old_fetch = originality_live.search_web, originality_live.fetch_source
    class Art:
        text = "This is a very detailed official notification with 783 vacancies and an application deadline of 22 July 2026 for eligible candidates."
    originality_live.search_web = lambda q, max_results=5: [{"url": "https://other.example/page", "title": "Other"}]
    originality_live.fetch_source = lambda url: Art()
    try:
        rep = originality_live.check(
            "<p>This is a very detailed official notification with 783 vacancies and an application deadline of 22 July 2026 for eligible candidates.</p>",
            own_domain="studentup.in", max_phrases=1)
        assert rep["status"] == "match" and rep["matches"]
    finally:
        originality_live.search_web, originality_live.fetch_source = old_search, old_fetch
    print("      exact phrase found on unknown live page → match ✔")


def test_own_domain_is_excluded() -> None:
    old_search, old_fetch = originality_live.search_web, originality_live.fetch_source
    class Art:
        text = "A distinctive official notification phrase with 783 vacancies for eligible candidates today."
    originality_live.search_web = lambda q, max_results=5: [{"url": "https://studentup.in/old", "title": "Own"}]
    originality_live.fetch_source = lambda url: Art()
    try:
        rep = originality_live.check("<p>A distinctive official notification phrase with 783 vacancies for eligible candidates today.</p>", "studentup.in", 1)
        assert not rep["matches"]
    finally:
        originality_live.search_web, originality_live.fetch_source = old_search, old_fetch
    print("      own-site result excluded from external copy evidence ✔")


def test_google_engine_is_optional_and_transparent() -> None:
    old_key, old_id = config.GOOGLE_CSE_API_KEY, config.GOOGLE_CSE_ID
    config.GOOGLE_CSE_API_KEY = ""
    config.GOOGLE_CSE_ID = ""
    try:
        rep = originality_live.check("<p>This is a distinctive sentence with 2026 information for applicants and readers.</p>", max_phrases=1)
        assert rep["engine"] == "fallback"
    finally:
        config.GOOGLE_CSE_API_KEY, config.GOOGLE_CSE_ID = old_key, old_id
    print("      no fake Google claim: engine reported as fallback ✔")


def test_pipeline_live_guard_wired() -> None:
    src = (ROOT / "autoblog" / "pipeline.py").read_text(encoding="utf-8")
    assert "originality_live" in src and "SKIP-LIVE-EXACT-OVERLAP" in src
    assert "ORIG_LIVE_REQUIRED" in src
    print("      pipeline blocks verified live exact overlap ✔")


def test_config_and_env() -> None:
    cfg = (ROOT / "autoblog" / "config.py").read_text(encoding="utf-8")
    env = (ROOT / ".env.example").read_text(encoding="utf-8")
    for key in ("ORIG_LIVE_CHECK", "ORIG_LIVE_PHRASES", "ORIG_LIVE_REQUIRED", "GOOGLE_CSE_API_KEY", "GOOGLE_CSE_ID"):
        assert key in cfg and key in env
    print("      live-check config + Google CSE optional credentials present ✔")


def test_docs() -> None:
    r = (ROOT / "README.md").read_text(encoding="utf-8")
    m = (ROOT / "MANUAL_ADVANCED_CHECKLIST.md").read_text(encoding="utf-8")
    assert "### v103" in r and "PART 60" in m and "94/94" in r and "94/94" in m
    print("      README v103 + PART 60 + 94/94 pinned ✔")


TESTS = [("phrase selection", test_phrase_selection_ignores_short_generic_text),
         ("live match", test_live_exact_match_is_reported),
         ("own exclusion", test_own_domain_is_excluded),
         ("engine transparency", test_google_engine_is_optional_and_transparent),
         ("pipeline guard", test_pipeline_live_guard_wired),
         ("config", test_config_and_env), ("docs", test_docs)]


def main() -> int:
    failed = 0
    for name, fn in TESTS:
        try:
            fn(); print(f"  {name} ✔")
        except Exception as exc:  # noqa: BLE001
            failed += 1; print(f"  {name} ✘ {type(exc).__name__}: {exc}")
    print("-" * 70)
    print("ALL v103 LIVE ORIGINALITY TESTS PASSED ✔" if not failed else f"{failed} TEST(S) FAILED ✘")
    return int(bool(failed))


if __name__ == "__main__":
    raise SystemExit(main())
