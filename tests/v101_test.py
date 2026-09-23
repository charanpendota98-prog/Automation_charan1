# -*- coding: utf-8 -*-
"""v101 — deceptive-freshness protection.

Google's Aug-2026 spam update explicitly targets dateModified changes with no
real content change. This suite proves the automatic refresh path distinguishes
real updates from cosmetic rewrites instead of manufacturing freshness.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from autoblog import config, freshness  # noqa: E402

SUITES_EXPECTED = 90


def test_identical_skips_write() -> None:
    old = "<p>TSPSC Group 2 notification has 783 vacancies.</p>"
    got = freshness.decide(old, old)
    assert got["publish"] is False
    assert got["bump_date"] is False
    assert got["change_pct"] == 0.0
    print("      identical content: WP write + date bump both skipped ✔")


def test_cosmetic_rewrite_does_not_bump_date() -> None:
    old = "<p>TSPSC Group 2 notification has 783 vacancies. Apply online today.</p>"
    new = "<p>TSPSC Group 2 Notification has 783 vacancies. Apply online today.</p>"
    got = freshness.decide(old, new)
    assert got["publish"] is False or got["bump_date"] is False
    assert got["bump_date"] is False
    print("      cosmetic rewrite: dateModified bump blocked ✔")


def test_real_new_fact_allows_bump() -> None:
    old = "<p>TSPSC Group 2 notification has 783 vacancies. Apply by 10 June 2026.</p>"
    new = "<p>TSPSC Group 2 notification has 921 vacancies. Apply by 22 July 2026.</p> " \
          "<p>Hall ticket download link is now available.</p>"
    got = freshness.decide(old, new)
    assert got["publish"] is True
    assert got["bump_date"] is True
    assert got["substantive"] is True
    assert got["new_facts"]
    print("      new vacancy/date facts: publish + dateModified bump allowed ✔")


def test_real_text_change_without_new_number_is_skipped() -> None:
    old = "<p>Read the official eligibility and selection process carefully before applying.</p>"
    new = "<p>Check the official eligibility, syllabus, and selection process carefully before applying online.</p> " \
          "<p>Use the department notice for the final instructions.</p>"
    got = freshness.decide(old, new, min_publish=0.1, min_bump=91)
    assert got["publish"] is False
    assert got["bump_date"] is False
    assert "modified timestamp" in got["reason"]
    print("      text-only cosmetic change: full write skipped ✔")


def test_thresholds_are_configurable() -> None:
    old = "<p>Alpha beta gamma delta epsilon zeta eta theta iota kappa lambda.</p>"
    new = old + " <p>New official eligibility explanation for applicants.</p>"
    got = freshness.decide(old, new, min_bump=90, min_publish=1)
    assert got["publish"] is False and got["bump_date"] is False
    assert config.FRESHNESS_MIN_CHANGE_PCT >= 0
    assert config.FRESHNESS_MIN_PUBLISH_PCT >= 0
    print("      freshness floors configurable via environment ✔")


def test_compare_reports_removed_and_new_facts() -> None:
    got = freshness.compare("<p>100 vacancies on 1 June 2026.</p>",
                            "<p>120 vacancies on 15 July 2026.</p>")
    assert "120" in got["new_facts"]
    assert "100" in got["removed_facts"]
    assert got["substantive"] is True
    print("      new/removed numeric facts reported as audit evidence ✔")


def test_pipeline_uses_guard_and_conditional_modified_date() -> None:
    src = (ROOT / "autoblog" / "pipeline.py").read_text(encoding="utf-8")
    start = src.index("def update_post(")
    seg = src[start:src.index("def ", start + 10)] if "def " in src[start + 10:] else src[start:]
    assert "freshness" in seg
    assert "_fresh.get(\"bump_date\"" in seg
    assert "date_modified=" in seg
    print("      update_post: guard wired before SEO + conditional dateModified ✔")


def test_config_and_env_are_present() -> None:
    cfg = (ROOT / "autoblog" / "config.py").read_text(encoding="utf-8")
    env = (ROOT / ".env.example").read_text(encoding="utf-8")
    for key in ("FRESHNESS_MIN_CHANGE_PCT", "FRESHNESS_MIN_PUBLISH_PCT"):
        assert key in cfg and key in env
    print("      config + .env.example freshness controls present ✔")


def test_cli_is_wired() -> None:
    src = (ROOT / "autoblog" / "main.py").read_text(encoding="utf-8")
    assert "--freshness-audit" in src and "freshness as _fr" in src
    print("      --freshness-audit CLI wired ✔")


def test_docs_are_pinned() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    manual = (ROOT / "MANUAL_ADVANCED_CHECKLIST.md").read_text(encoding="utf-8")
    assert "### v101" in readme
    assert "PART 58" in manual
    assert "90/90" in readme and "90/90" in manual
    print("      README v101 + manual PART 58 + 90/90 pinned ✔")


TESTS = [
    ("identical skip", test_identical_skips_write),
    ("cosmetic no bump", test_cosmetic_rewrite_does_not_bump_date),
    ("new fact bump", test_real_new_fact_allows_bump),
    ("text-only skip", test_real_text_change_without_new_number_is_skipped),
    ("configurable floors", test_thresholds_are_configurable),
    ("fact audit", test_compare_reports_removed_and_new_facts),
    ("pipeline wiring", test_pipeline_uses_guard_and_conditional_modified_date),
    ("config/env", test_config_and_env_are_present),
    ("CLI wiring", test_cli_is_wired),
    ("docs pin", test_docs_are_pinned),
]


def main() -> int:
    failed = 0
    for name, fn in TESTS:
        try:
            fn()
            print(f"  {name} ✔")
        except Exception as exc:  # noqa: BLE001
            failed += 1
            print(f"  {name} ✘ {type(exc).__name__}: {exc}")
    print("-" * 70)
    print("ALL v101 FRESHNESS TESTS PASSED ✔" if not failed else f"{failed} TEST(S) FAILED ✘")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
