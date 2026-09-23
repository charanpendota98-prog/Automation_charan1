# -*- coding: utf-8 -*-
"""v102 — GSC Pages evidence-based refresh prioritisation."""
from __future__ import annotations

import csv
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from autoblog import config, gsc_refresh, state  # noqa: E402

SUITES_EXPECTED = 88


def _csv(path: Path) -> None:
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["Top pages", "Clicks", "Impressions", "CTR", "Position"])
        w.writerow(["https://studentup.in/low-ctr", "20", "1000", "2%", "8"])
        w.writerow(["https://studentup.in/high-ctr", "180", "1000", "18%", "8"])
        w.writerow(["https://studentup.in/deep", "2", "300", "0.6%", "35"])


def test_pages_csv_parses_and_scores() -> None:
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "pages.csv"
        _csv(p)
        rows = gsc_refresh.parse(str(p))
    assert rows[0]["url"].endswith("/low-ctr")
    assert rows[0]["score"] > rows[1]["score"]
    assert all("query" not in r for r in rows)
    print("      GSC Pages CSV: low CTR + striking position scores highest ✔")


def test_query_export_rejected() -> None:
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "queries.csv"
        p.write_text("Top queries,Clicks,Impressions,CTR,Position\nfoo,2,100,2%,8\n", encoding="utf-8")
        try:
            gsc_refresh.parse(str(p))
            raise AssertionError("query-only export accepted as page evidence")
        except ValueError as exc:
            assert "Pages" in str(exc)
    print("      query-only CSV rejected (no URL guessing) ✔")


def test_ingest_persists_and_cli_data_loads() -> None:
    with tempfile.TemporaryDirectory() as d:
        old = config.STATE_PATH
        config.STATE_PATH = Path(d) / "state.db"
        try:
            state.init(config.STATE_PATH)
            p = Path(d) / "pages.csv"
            _csv(p)
            gsc_refresh.ingest(str(p))
            data = gsc_refresh.load()
            assert "https://studentup.in/low-ctr" in data
        finally:
            config.STATE_PATH = old
    print("      GSC scores persist in SQLite meta and reload ✔")


def test_state_picks_gsc_match_before_oldest() -> None:
    with tempfile.TemporaryDirectory() as d:
        old = config.STATE_PATH
        config.STATE_PATH = Path(d) / "state.db"
        try:
            state.init(config.STATE_PATH)
            state.record_post(config.STATE_PATH, "Old no evidence", "old", "Jobs",
                              "https://studentup.in/old", "publish", wp_id=1)
            state.record_post(config.STATE_PATH, "GSC opportunity", "opp", "Jobs",
                              "https://studentup.in/low-ctr", "publish", wp_id=2)
            state.meta_set(config.STATE_PATH, gsc_refresh.KEY,
                           '{"rows":[{"url":"https://studentup.in/low-ctr","score":999}]}')
            got = state.posts_to_refresh(config.STATE_PATH, older_days=0, limit=1)
            assert got[0]["wp_id"] == 2, got
        finally:
            config.STATE_PATH = old
    print("      auto-refresh selects matched GSC opportunity first ✔")


def test_unmatched_pages_do_not_displace_evidence() -> None:
    with tempfile.TemporaryDirectory() as d:
        old = config.STATE_PATH
        config.STATE_PATH = Path(d) / "state.db"
        try:
            state.init(config.STATE_PATH)
            state.record_post(config.STATE_PATH, "No match", "x", "Jobs",
                              "https://studentup.in/x", "publish", wp_id=1)
            state.record_post(config.STATE_PATH, "Matched", "y", "Jobs",
                              "https://studentup.in/y/", "publish", wp_id=2)
            state.meta_set(config.STATE_PATH, gsc_refresh.KEY,
                           '{"rows":[{"url":"https://studentup.in/y?utm=csv","score":2}]}')
            assert state.posts_to_refresh(config.STATE_PATH, older_days=0, limit=1)[0]["wp_id"] == 2
        finally:
            config.STATE_PATH = old
    print("      URL query/trailing-slash normalisation works ✔")


def test_pipeline_and_cli_wired() -> None:
    main = (ROOT / "autoblog" / "main.py").read_text(encoding="utf-8")
    st = (ROOT / "autoblog" / "state.py").read_text(encoding="utf-8")
    assert "--gsc-refresh" in main and "gsc_refresh as _gr" in main
    assert "gsc:refresh-priority:v1" in st and "posts_to_refresh" in st
    print("      CLI + automatic selection wiring present ✔")


def test_score_defensive() -> None:
    assert gsc_refresh.score(0, 0, 0, 5) == 0
    assert gsc_refresh.score(100, 10, 200, 5) >= 0
    assert gsc_refresh.score(100, 10, 0.01, 8) > gsc_refresh.score(100, 80, 0.8, 8)
    print("      score handles malformed CTR and zero metrics safely ✔")


def test_docs() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    manual = (ROOT / "MANUAL_ADVANCED_CHECKLIST.md").read_text(encoding="utf-8")
    assert "### v102" in readme and "PART 59" in manual
    assert "88/88" in readme and "88/88" in manual
    print("      README v102 + PART 59 + 88/88 pinned ✔")


TESTS = [("parse + score", test_pages_csv_parses_and_scores),
         ("reject query export", test_query_export_rejected),
         ("persist scores", test_ingest_persists_and_cli_data_loads),
         ("GSC first", test_state_picks_gsc_match_before_oldest),
         ("unmatched safe", test_unmatched_pages_do_not_displace_evidence),
         ("wiring", test_pipeline_and_cli_wired),
         ("defensive score", test_score_defensive),
         ("docs", test_docs)]


def main() -> int:
    failed = 0
    for name, fn in TESTS:
        try:
            fn(); print(f"  {name} ✔")
        except Exception as exc:  # noqa: BLE001
            failed += 1; print(f"  {name} ✘ {type(exc).__name__}: {exc}")
    print("-" * 70)
    print("ALL v102 GSC PRIORITY TESTS PASSED ✔" if not failed else f"{failed} TEST(S) FAILED ✘")
    return int(bool(failed))


if __name__ == "__main__":
    raise SystemExit(main())
