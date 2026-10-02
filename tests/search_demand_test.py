# -*- coding: utf-8 -*-
"""v181 — on-site search demand loop tests (offline).

Cover:
  1. import formats (JSON + CSV) — normalize/dedupe
  2. analyze(): zero-result gaps first, weak coverage detection vs titles
  3. write_queue(): merge + first_seen preserve + count max
  4. report_text(): Telegram HTML shape
  5. run_cli(): offline import → queue file (temp paths, no network)
  6. theme wiring: inc/searchlog.php (privacy + REST + bot/admin guard) is
     included, and search.php logs server-side
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from autoblog import config, search_demand  # noqa: E402


def test_import_formats():
    with tempfile.TemporaryDirectory() as tmp:
        j = Path(tmp) / "d.json"
        j.write_text(json.dumps({"terms": [
            {"term": "  TSPSC Group 2  ", "count": 7, "zero": False},
            {"term": "ssc cgl", "count": 3, "zero": True},
            {"term": "", "count": 9},
        ]}), encoding="utf-8")
        rows = search_demand.parse_import(str(j))
        assert len(rows) == 2, rows
        assert rows[0]["term"] == "tspsc group 2"      # normalized
        c = Path(tmp) / "d.csv"
        c.write_text("term,count,zero\nnsp scholarship,5,1\nrrb ntpc,2,0\n",
                     encoding="utf-8")
        rows2 = search_demand.parse_import(str(c))
        assert rows2[0] == {"term": "nsp scholarship", "count": 5, "zero": True}
    print("  1. import JSON/CSV + normalize ✔")


def test_analyze_gaps_and_weak():
    terms = [
        {"term": "tspsc group 2 hall ticket", "count": 12, "zero": True},
        {"term": "ssc cgl apply online", "count": 9, "zero": False},
        {"term": "nsp scholarship status", "count": 4, "zero": False},
    ]
    titles = ["SSC CGL 2026 apply online notification — eligibility & dates"]
    rep = search_demand.analyze(terms, titles)
    assert rep["total_searches"] == 25
    assert rep["gaps"][0]["term"] == "tspsc group 2 hall ticket"
    assert rep["gaps"][0]["priority"] == 1
    # ssc cgl title lo unna tokens cover ayyayi → gap kaadu
    assert all(g["term"] != "ssc cgl apply online" for g in rep["gaps"])
    # nsp scholarship ki dedicated post ledu → weak coverage
    weak_terms = [w["term"] for w in rep["weak"]]
    assert "nsp scholarship status" in weak_terms, weak_terms
    assert rep["zero_share"] == round(1 / 3, 3)
    print("  2. analyze: zero-result gaps + weak coverage ✔")


def test_write_queue_merge():
    with tempfile.TemporaryDirectory() as tmp:
        qp = Path(tmp) / "q.json"
        rep1 = search_demand.analyze(
            [{"term": "ts dsc hall ticket", "count": 5, "zero": True}], [])
        search_demand.write_queue(rep1, qp)
        first = json.loads(qp.read_text(encoding="utf-8"))["queue"]
        assert first[0]["term"] == "ts dsc hall ticket"
        assert first[0]["first_seen"]
        # second run: same term + kotha term → merge (count max, first_seen preserve)
        rep2 = search_demand.analyze(
            [{"term": "ts dsc hall ticket", "count": 9, "zero": True},
             {"term": "ap police constable", "count": 2, "zero": True}], [])
        search_demand.write_queue(rep2, qp)
        rows = {r["term"]: r for r in json.loads(qp.read_text(encoding="utf-8"))["queue"]}
        assert rows["ts dsc hall ticket"]["count"] == 9
        assert rows["ts dsc hall ticket"]["first_seen"] == first[0]["first_seen"]
        assert "ap police constable" in rows
    print("  3. queue: merge + first_seen + count max ✔")


def test_report_and_cli():
    terms = [{"term": "rrb group d result", "count": 6, "zero": True}]
    rep = search_demand.analyze(terms, [])
    text = search_demand.report_text(rep, Path("/tmp/x.json"))
    assert "ON-SITE SEARCH DEMAND" in text and "rrb group d result" in text
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "in.json"
        src.write_text(json.dumps({"terms": terms}), encoding="utf-8")
        old_q = config.SEARCH_DEMAND_QUEUE
        try:
            config.SEARCH_DEMAND_QUEUE = Path(tmp) / "out-queue.json"
            rc = search_demand.run_cli(import_path=str(src), queue=True)
        finally:
            config.SEARCH_DEMAND_QUEUE = old_q
        assert rc == 0
        assert (Path(tmp) / "out-queue.json").exists()
    print("  4. report + offline CLI → queue ✔")


def test_theme_wiring():
    theme = ROOT / "wordpress-theme" / "studentup"
    php = (theme / "inc" / "searchlog.php").read_text(encoding="utf-8")
    for token in ("register_rest_route", "studentup_searchlog_record",
                  "edit_posts", "sanitize_text_field", "set_transient",
                  "ABSPATH", "rest_post_dispatch"):
        assert token in php, "searchlog.php lo ledu: " + token
    # privacy: IP/user persist avvakudadu
    assert "REMOTE_ADDR" in php and "md5(" in php   # throttle transient lo matrame
    assert "update_option( STUDENTUP_SEARCHLOG_OPTION" in php
    fn = (theme / "functions.php").read_text(encoding="utf-8")
    assert "inc/searchlog.php" in fn, "theme include ledu"
    sp = (theme / "search.php").read_text(encoding="utf-8")
    assert "studentup_searchlog_page" in sp, "search.php server-side log ledu"
    # bot module REST path/method match
    assert search_demand.REST_PATH == "/wp-json/studentup/v1/search-log"
    print("  5. theme wiring: REST + guards + privacy ✔")


def main() -> None:
    print("=" * 70)
    print("  v181 — SEARCH DEMAND LOOP (readers → content gaps)")
    print("=" * 70)
    test_import_formats()
    test_analyze_gaps_and_weak()
    test_write_queue_merge()
    test_report_and_cli()
    test_theme_wiring()
    print("-" * 70)
    print("ALL v181 SEARCH-DEMAND TESTS PASSED ✔")


if __name__ == "__main__":
    main()
