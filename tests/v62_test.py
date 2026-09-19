# -*- coding: utf-8 -*-
"""v62 tests — TOP WEBSITE READINESS ("asalu 100% advanced ga unda?" ki proof).

Enduku idi:
  Mee prashna ki maatalu kaadu — verifiable numbers tho answer: content engine,
  SEO, ads, automation, real site, owner-pending — okka command lo measure.
  `python run.py --readiness` → score + artifacts (logs/readiness.json +
  output/readiness-<date>.md).

Checks (offline only):
  * checks contract: 17 check groups · rows ki section/label/value/ok/scored
  * run_report(): system score >= 90+ (ee repo lo 100/100 undali) · ok True
  * е honest note undali (ranking/revenue guarantee ledu)
  * blueprint check 90+ (3 sample keywords min) — post quality engine
  * freshness check: radar 4x/day · 59 districts (latest posts engine)
  * owner_pending >= 5 items, ప్రతిదానికి fix line
  * artifacts: logs/readiness.json + output/readiness-<date>.md (markdown sections)
  * CLI wiring (--readiness) + run.py docstring
  * no crash checks: prathi check callable (exception  → row lo ❌ ga vasthundi, crash ledu)
  * docs: MANUAL PART 21 + README + GO_LIVE

Run: python tests/v62_test.py   (also via python run.py --test-all)
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from autoblog import readiness  # noqa: E402

INDEX = ROOT / "preview" / "index.html"
MAIN = ROOT / "autoblog" / "main.py"


def test_checks_contract():
    assert len(readiness.CHECKS) >= 17, len(readiness.CHECKS)
    names = [n for n, _ in readiness.CHECKS]
    for want in ("blueprint", "gates", "coverage", "freshness", "schema", "index_files",
                 "rankmath", "ad_slots", "ads_txt", "money_engine", "ad_safety", "hooks",
                 "approval", "theme", "first_look", "counts_sync", "owner_pending"):
        assert want in names, want
    assert readiness.SECTION_ORDER == ["CONTENT ENGINE", "SEO", "ADS & MONEY", "AUTOMATION",
                                       "REAL SITE (WordPress theme)", "OWNER PENDING"]


def test_rows_shape():
    rows = []
    for name, fn in readiness.CHECKS:
        rows.extend(fn())
    assert rows, "rows khali"
    for r in rows:
        assert r["section"] in readiness.SECTION_ORDER, r
        assert r["label"] and r["value"], r
        assert isinstance(r["ok"], bool) and isinstance(r["scored"], bool)
    # prathi scored row ki detail leda value undali; pending rows ki fix undali
    for r in rows:
        if not r["scored"]:
            assert r["section"] == "OWNER PENDING" and r["detail"], r


def test_report_score():
    rep = readiness.run_report()
    assert rep["pending"] >= 5, rep["pending"]
    assert rep["score"] == round(100 * rep["passed"] / rep["total"])
    assert rep["score"] >= 90, "system score thakkuva: %s (%s/%s)" % (
        rep["score"], rep["passed"], rep["total"])
    assert rep["ok"] is True
    assert "guarantee" in rep["honest_note"] or "ivvadu" in rep["honest_note"]


def test_blueprint_check_is_quality_proof():
    rows = readiness.c_blueprint()
    assert len(rows) == 1 and rows[0]["ok"], rows
    score = int(re.search(r"(\d+)/100", rows[0]["value"]).group(1))
    assert score >= 90, rows[0]["value"]
    assert "TOP POST" in rows[0]["value"] or "STRONG" in rows[0]["value"]


def test_freshness_check_counts():
    rows = readiness.c_latest_news_engine()
    row = rows[0]
    assert row["ok"], row
    assert "4x/day" in row["value"] and "59 districts" in row["value"]
    assert "143 sources" in row["value"], row["value"]


def test_rankmath_live_check():
    rows = readiness.c_rankmath()
    assert rows[0]["ok"], rows[0]
    assert "rank_math_title" not in rows[0]["value"]  # value Telugu-friendly line
    assert "robots" in rows[0]["value"]


def test_owner_pending_items():
    rows = readiness.c_owner_pending()
    assert len(rows) >= 5, rows
    labels = " ".join(r["label"] for r in rows)
    for want in ("Domain", "WordPress", "Gemini", "Telegram", "AdSense", "Oracle"):
        assert want in labels, want
    for r in rows:
        assert not r["ok"] and not r["scored"] and r["detail"], r


def test_no_crash_on_failure(monkeypatch_free=None):
    """Check crash ayina report crash avvakudadu — ❌ row ga vastundi."""
    orig = readiness.CHECKS
    try:
        readiness.CHECKS = [("boom", lambda: (_ for _ in ()).throw(RuntimeError("x"))),
                            ("ok", lambda: [readiness._ok("fine", "1", "SEO")])]
        rep = readiness.run_report()
    finally:
        readiness.CHECKS = orig
    assert rep["total"] == 2 and rep["passed"] == 1 and rep["score"] == 50
    bad = [r for r in rep["rows"] if not r["ok"] and r["scored"]]
    assert bad and "RuntimeError" in bad[0]["value"], bad


def test_artifacts_and_markdown():
    rep = readiness.run_report()
    arts = readiness.write_artifacts(rep)
    assert Path(arts["json"]).exists() and Path(arts["md"]).exists()
    data = json.loads(Path(arts["json"]).read_text(encoding="utf-8"))
    assert data["score"] == rep["score"] and data["rows"]
    md = Path(arts["md"]).read_text(encoding="utf-8")
    for section in ("CONTENT ENGINE", "SEO", "ADS & MONEY", "AUTOMATION",
                    "REAL SITE (WordPress theme)", "OWNER PENDING"):
        assert "## " + section in md, section
    assert "TOP WEBSITE READINESS" in md and "⚠️" in md


def test_cli_wiring():
    main = MAIN.read_text(encoding="utf-8")
    assert "def readiness_run(" in main and '"--readiness"' in main
    assert "readiness.run_report()" in main and "readiness.write_artifacts" in main
    run = (ROOT / "run.py").read_text(encoding="utf-8")
    assert "--readiness" in run, "run.py help lo readiness undali"


def test_docs_v62():
    manual = (ROOT / "MANUAL_ADVANCED_CHECKLIST.md").read_text(encoding="utf-8")
    assert "PART 21" in manual and "READINESS" in manual
    go = (ROOT / "GO_LIVE_CHECKLIST.md").read_text(encoding="utf-8")
    assert "--readiness" in go
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "--readiness" in readme


def main():
    print("=" * 66)
    print("  v62 — TOP WEBSITE READINESS (proof tho: enti ready, enti mee pani)")
    print("=" * 66)
    tests = [
        ("checks contract (17 groups · 6 sections)", test_checks_contract),
        ("rows shape (label/value/ok/scored + pending fix)", test_rows_shape),
        ("report score >= 90 + honest note", test_report_score),
        ("blueprint 90+ (post quality engine)", test_blueprint_check_is_quality_proof),
        ("freshness: radar 4x/day · 59 districts · 143 sources", test_freshness_check_counts),
        ("Rank Math LIVE fields (not grep)", test_rankmath_live_check),
        ("owner pending 5+ items with fix lines", test_owner_pending_items),
        ("check crash ayina report crash kaadu", test_no_crash_on_failure),
        ("artifacts: readiness.json + markdown sections", test_artifacts_and_markdown),
        ("CLI wiring --readiness", test_cli_wiring),
        ("docs: MANUAL PART 21 + GO_LIVE + README", test_docs_v62),
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
    print("-" * 66)
    if failed:
        print(f"  {failed} TEST(S) FAILED ✘")
        return 1
    print("ALL v62 READINESS TESTS PASSED ✔")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
