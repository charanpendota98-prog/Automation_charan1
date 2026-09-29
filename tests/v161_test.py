# -*- coding: utf-8 -*-
"""v161 — draft vs official source fact cross-check."""
from __future__ import annotations

from pathlib import Path

from autoblog import factcheck as fc

ROOT = Path(__file__).resolve().parents[1]

SOURCE = ("<p>Total vacancies: 783 posts. Examination fee Rs 200. Last date for "
          "submission of online application: 2026-10-20. Pay scale Rs 40,000.</p>")


def test_date_formats_normalise_to_iso():
    assert fc.dates("last date 15 October 2026") == ["2026-10-15"]
    assert fc.dates("closes on Oct 15, 2026") == ["2026-10-15"]
    assert fc.dates("2026-10-15") == ["2026-10-15"]
    assert fc.dates("random 2026 number 45") == [], "date kaani dani ni date ga teesukundi"
    assert fc.dates("32 October 2026") == [], "invalid day accept chesindi"
    print("      three date formats normalise to the same ISO value ✔")


def test_wrong_date_is_a_conflict_not_a_warning():
    rep = fc.check("<p>Last date 15 October 2026, 783 posts, fee Rs 200.</p>", SOURCE)
    conflicts = [r for r in rep["conflicts"] if r["kind"] == "date"]
    assert conflicts and conflicts[0]["claimed"] == "2026-10-15"
    assert not rep["publishable"], "conflict unna publishable ani chepindi"
    print("      a date that disagrees with the source blocks publishing ✔")


def test_matching_facts_pass():
    rep = fc.check("<p>Last date 20 October 2026. 783 posts. Fee Rs 200.</p>", SOURCE)
    assert rep["publishable"] and not rep["conflicts"]
    assert len(rep["matched"]) == 3
    print("      draft matching the source is publishable ✔")


def test_absent_from_source_is_unverified_not_wrong():
    rep = fc.check("<p>Interview on 5 January 2027.</p>", SOURCE)
    row = rep["rows"][0]
    assert row["status"] == "NOT_FOUND", row
    assert rep["publishable"], "verify cheyyalenidi ni tappu ga treat chesindi"
    print("      unverifiable facts are flagged, not called false ✔")


def test_every_claimed_fact_is_checked():
    draft = "<p>Dates 01 March 2026 and 02 March 2026 with 100 posts and 200 posts.</p>"
    rep = fc.check(draft, SOURCE)
    kinds = [r["kind"] for r in rep["rows"]]
    assert kinds.count("date") == 2 and kinds.count("vacancies") == 2, kinds
    print("      all claims are checked, not just the first one ✔")


def test_cli_blocks_on_conflict(tmp_path):
    d = tmp_path / "d.html"
    s = tmp_path / "s.html"
    d.write_text("<p>Last date 15 October 2026.</p>", encoding="utf-8")
    s.write_text(SOURCE, encoding="utf-8")
    assert fc.run_cli(str(d), str(s)) == 1, "conflict unna exit 0 ichindi"
    d.write_text("<p>Last date 20 October 2026.</p>", encoding="utf-8")
    assert fc.run_cli(str(d), str(s)) == 0
    assert fc.run_cli(str(d), "") == 1, "source lekunda pass ayindi"
    print("      CLI exits non-zero on a conflict ✔")


def test_flag_documented():
    main = (ROOT / "autoblog" / "main.py").read_text(encoding="utf-8")
    assert '"--factcheck"' in main and "args.factcheck" in main
    for name in ("README.md", "MANUAL_ADVANCED_CHECKLIST.md", "GO_LIVE_CHECKLIST.md"):
        txt = (ROOT / name).read_text(encoding="utf-8")
        assert "--factcheck" in txt and "--against" in txt, name
    print("      --factcheck / --against documented in all 3 docs ✔")
