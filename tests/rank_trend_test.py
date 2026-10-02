# -*- coding: utf-8 -*-
"""v181 — rank trend / decay loop tests (offline).

Cover:
  1. ingest + idempotency (same date replaces) + history cap
  2. trend(): RISING / DECAYING / NEW / FLAT classification
  3. small-sample guard (clicks < MIN_CLICKS tho DECAY cheppadu)
  4. queue_refresh(): merge + ordering by click loss
  5. refresh_scores(): existing gsc_refresh store update
  6. run_cli(): CSV ingest end-to-end (temp paths)
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from autoblog import config, gsc_refresh, rank_trend, state  # noqa: E402


def _rows(spec):
    out = []
    for url, clicks, impr, pos in spec:
        ctr = clicks / impr if impr else 0.0
        out.append({"url": url, "clicks": clicks, "impressions": impr,
                    "ctr": round(ctr, 5), "position": pos,
                    "score": gsc_refresh.score(impr, clicks, ctr, pos)})
    return out


def test_ingest_idempotent_and_cap():
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "h.json"
        rank_trend.ingest(_rows([("https://s.in/a/", 5, 100, 8)]), day="2026-09-25", path=p)
        rank_trend.ingest(_rows([("https://s.in/a/", 6, 120, 7)]), day="2026-09-25", path=p)
        hist = rank_trend.load_history(p)
        assert len(hist["snapshots"]) == 1, "same date replace avvali"
        assert hist["snapshots"][0]["rows"][0]["clicks"] == 6
        for i in range(config.RANK_HISTORY_MAX_SNAPSHOTS + 10):
            rank_trend.ingest(_rows([("https://s.in/a/", i, 10, 5)]),
                              day=f"2026-01-{i % 28 + 1:02d}", path=p)
        assert len(rank_trend.load_history(p)["snapshots"]) <= config.RANK_HISTORY_MAX_SNAPSHOTS
    print("  1. ingest: idempotent + history cap ✔")


def test_trend_classification():
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "h.json"
        base = _rows([
            ("https://s.in/decay/", 20, 900, 6.0),
            ("https://s.in/rise/", 4, 300, 14.0),
            ("https://s.in/flat/", 8, 200, 9.0),
        ])
        latest = _rows([
            ("https://s.in/decay/", 9, 700, 11.0),     # clicks -55%, pos +5 → DECAYING
            ("https://s.in/rise/", 12, 400, 7.0),      # clicks +200%, pos -7 → RISING
            ("https://s.in/flat/", 8, 210, 9.2),       # FLAT
            ("https://s.in/new/", 3, 50, 22.0),        # NEW
        ])
        rank_trend.ingest(base, day="2026-09-25", path=p)
        rank_trend.ingest(latest, day="2026-10-02", path=p)
        rep = rank_trend.trend(window=7, path=p)
        assert rep["ready"] is True
        states = {m["url"]: m["state"] for m in
                  rep["decaying"] + rep["rising"] + rep["new"]}
        assert states["https://s.in/decay/"] == "DECAYING"
        assert states["https://s.in/rise/"] == "RISING"
        assert states["https://s.in/new/"] == "NEW"
        assert rep["decaying"][0]["clicks_delta"] == -11
        assert rep["baseline"] == "2026-09-25"
    print("  2. trend: RISING / DECAYING / NEW / FLAT ✔")


def test_small_sample_guard():
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "h.json"
        rank_trend.ingest(_rows([("https://s.in/tiny/", 2, 50, 5.0)]),
                          day="2026-09-25", path=p)
        rank_trend.ingest(_rows([("https://s.in/tiny/", 0, 40, 12.0)]),
                          day="2026-10-02", path=p)
        rep = rank_trend.trend(window=7, path=p)
        assert all(m["url"] != "https://s.in/tiny/" for m in rep["decaying"]), \
            "chinna sample tho decay cheppakudadu"
    print("  3. small-sample guard (clicks < 3) ✔")


def test_queue_and_scores():
    with tempfile.TemporaryDirectory() as tmp:
        hp = Path(tmp) / "h.json"
        qp = Path(tmp) / "q.json"
        rank_trend.ingest(_rows([("https://s.in/a/", 30, 1000, 5.0),
                                 ("https://s.in/b/", 12, 500, 8.0)]),
                          day="2026-09-25", path=hp)
        rank_trend.ingest(_rows([("https://s.in/a/", 8, 800, 12.0),
                                 ("https://s.in/b/", 11, 500, 9.0)]),
                          day="2026-10-02", path=hp)
        rep = rank_trend.trend(window=7, path=hp)
        out = rank_trend.queue_refresh(rep, qp)
        assert out and out.exists()
        queue = json.loads(out.read_text(encoding="utf-8"))["queue"]
        assert queue[0]["url"] == "https://s.in/a/"          # worst click loss first
        assert queue[0]["clicks_delta"] == -22
        assert queue[0]["first_seen"]
        # gsc_refresh store: store lo unna decaying URL scores update avvali
        old_state = config.STATE_PATH
        try:
            config.STATE_PATH = Path(tmp) / "s.db"
            state.init(config.STATE_PATH)
            state.meta_set(config.STATE_PATH, gsc_refresh.KEY, json.dumps(
                {"source": "test", "rows": _rows([("https://s.in/a/", 30, 1000, 5.0)])}))
            changed = rank_trend.refresh_scores(rep, path=hp)
            assert changed == 1, changed
            stored = gsc_refresh.load()
            assert stored["https://s.in/a/"]["clicks"] == 8      # fresh numbers
        finally:
            config.STATE_PATH = old_state
    print("  4. refresh queue + gsc store score update ✔")


def test_cli_csv_end_to_end():
    with tempfile.TemporaryDirectory() as tmp:
        csv1 = Path(tmp) / "d1.csv"
        csv2 = Path(tmp) / "d2.csv"
        csv1.write_text(
            "Top pages,Clicks,Impressions,CTR,Position\n"
            "https://studentup.in/ssc-cgl/,25,900,2.8%,6.2\n", encoding="utf-8")
        csv2.write_text(
            "Top pages,Clicks,Impressions,CTR,Position\n"
            "https://studentup.in/ssc-cgl/,6,700,0.9%,11.5\n", encoding="utf-8")
        old = (config.RANK_HISTORY_PATH, config.RANK_REFRESH_QUEUE, config.STATE_PATH)
        try:
            config.RANK_HISTORY_PATH = Path(tmp) / "hist.json"
            config.RANK_REFRESH_QUEUE = Path(tmp) / "queue.json"
            config.STATE_PATH = Path(tmp) / "s.db"
            state.init(config.STATE_PATH)
            # day 1: manual ingest (day pin tho), day 2: CLI csv ingest (today)
            rc0 = rank_trend.run_cli(csv_path=str(csv1))
            assert rc0 == 0
            hist = rank_trend.load_history()
            first_day = hist["snapshots"][0]["date"]
            # rewrite day-1 date so the 7-day window has a baseline
            hist["snapshots"][0]["date"] = "2026-09-25"
            rank_trend.save_history(hist)
            rc = rank_trend.run_cli(csv_path=str(csv2))
            assert rc == 0
            q = json.loads((Path(tmp) / "queue.json").read_text(encoding="utf-8"))
            assert q["queue"] and q["queue"][0]["clicks_delta"] == -19
            assert first_day  # (lint)
        finally:
            (config.RANK_HISTORY_PATH, config.RANK_REFRESH_QUEUE,
             config.STATE_PATH) = old
    print("  5. CLI CSV ingest → decay → queue ✔")


def main() -> None:
    print("=" * 70)
    print("  v181 — RANK TREND LOOP (GSC time-series → decay → refresh)")
    print("=" * 70)
    test_ingest_idempotent_and_cap()
    test_trend_classification()
    test_small_sample_guard()
    test_queue_and_scores()
    test_cli_csv_end_to_end()
    print("-" * 70)
    print("ALL v181 RANK-TREND TESTS PASSED ✔")


if __name__ == "__main__":
    main()
