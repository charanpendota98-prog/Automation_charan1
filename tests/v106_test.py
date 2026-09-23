# -*- coding: utf-8 -*-
"""v106 — search intent and cannibalization audit."""
from __future__ import annotations
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from autoblog import cannibalization  # noqa: E402
SUITES_EXPECTED = 96


def test_intent_classification():
    assert cannibalization.intent("TSPSC Group 2 Hall Ticket Download") == "hall-ticket"
    assert cannibalization.intent("TSPSC Group 2 Result 2026") == "result"
    assert cannibalization.intent("NSP Scholarship Apply Online") == "scholarship"
    print("      notification/apply/hall-ticket/result intent map ✔")


def test_duplicate_intent_pair_flagged():
    posts = [{"title": "TSPSC Group 2 Notification 2026", "link": "/g2/"},
             {"title": "TSPSC Group 2 Latest Notification Vacancies", "link": "/g2-latest/"}]
    r = cannibalization.analyze(posts)
    assert r["conflicts"] and r["conflicts"][0]["recommendation"] in ("merge_or_301", "choose_pillar_and_canonical")
    print("      same-intent duplicate pair flagged safely ✔")


def test_separate_intents_not_false_positive():
    posts = [{"title": "TSPSC Group 2 Notification 2026", "link": "/notice/"},
             {"title": "TSPSC Group 2 Syllabus and Exam Pattern", "link": "/syllabus/"}]
    r = cannibalization.analyze(posts)
    assert not r["conflicts"]
    print("      notification vs syllabus separate intent preserved ✔")


def test_recommendation_never_destructive():
    posts = [{"title": "SSC CGL Result 2026", "link": "/a/"},
             {"title": "SSC CGL Result Cutoff 2026", "link": "/b/"}]
    r = cannibalization.analyze(posts)
    assert r["conflicts"]
    assert "merge" in r["conflicts"][0]["recommendation"] or "canonical" in r["conflicts"][0]["recommendation"]
    print("      audit recommends only — no automatic destructive merge ✔")


def test_cli_wired():
    src = (ROOT / "autoblog" / "main.py").read_text(encoding="utf-8")
    assert "--cannibalization-audit" in src and "cannibalization as _ca" in src
    print("      cannibalization CLI wired ✔")


def test_docs():
    r = (ROOT / "README.md").read_text(encoding="utf-8")
    m = (ROOT / "MANUAL_ADVANCED_CHECKLIST.md").read_text(encoding="utf-8")
    assert "### v106" in r and "PART 63" in m and "96/96" in r and "96/96" in m
    print("      README v106 + PART 63 + 96/96 pinned ✔")

TESTS = [("intent", test_intent_classification), ("duplicate", test_duplicate_intent_pair_flagged),
         ("separate", test_separate_intents_not_false_positive), ("safe", test_recommendation_never_destructive),
         ("CLI", test_cli_wired), ("docs", test_docs)]

def main():
    failed = 0
    for n, f in TESTS:
        try: f(); print(f"  {n} ✔")
        except Exception as e: failed += 1; print(f"  {n} ✘ {type(e).__name__}: {e}")
    print("-" * 70)
    print("ALL v106 CANNIBALIZATION TESTS PASSED ✔" if not failed else f"{failed} TEST(S) FAILED ✘")
    return int(bool(failed))
if __name__ == "__main__": raise SystemExit(main())
