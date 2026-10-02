# -*- coding: utf-8 -*-
"""v182 — editorial calendar tests (offline).

Cover:
  1. candidate collection from demand/refresh queues (+ dedupe)
  2. balancing rules: per-day category cap, cluster cap, refresh slot
  3. plan shape + save (json + md) + apply_to_queue (dedupe, refresh skip)
  4. revenue boost: category/token signals score penchutunnaya
  5. CLI: plan only (no writes outside tmp) + error path with zero signals
"""
from __future__ import annotations

import json
import sys
import tempfile
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from autoblog import config, editorial_calendar as ec, state  # noqa: E402


def test_candidates_and_dedupe():
    with tempfile.TemporaryDirectory() as tmp:
        dq = Path(tmp) / "demand.json"
        dq.write_text(json.dumps({"queue": [
            {"term": "tspsc group 2 hall ticket", "reason": "no-results", "count": 9},
            {"term": "tspsc group 2 hall ticket", "reason": "weak-coverage", "count": 3},
            {"term": "nsp scholarship status", "reason": "weak-coverage", "count": 4},
            {"term": "ab", "reason": "no-results", "count": 50},          # too short
        ]}), encoding="utf-8")
        rq = Path(tmp) / "refresh.json"
        rq.write_text(json.dumps({"queue": [
            {"url": "https://studentup.in/old-post/", "clicks_before": 30,
             "clicks": 8, "position_before": 6.0, "position": 12.0,
             "clicks_delta": -22},
        ]}), encoding="utf-8")
        demand = ec.demand_candidates(dq)
        refresh = ec.refresh_candidates(rq)
        assert len(demand) == 3, demand                       # short term filtered
        zero = [c for c in demand if "result ledu" in c["reason"]]
        assert zero and zero[0]["score"] >= 100 + 15           # zero-result bonus
        ref = refresh[0]
        assert ref["score"] == 90 + 22 and "clicks 30→8" in ref["reason"]
        # collect() dedupe (same term rendu rows unna okate) + queue paths
        old_cfg = (config.SEARCH_DEMAND_QUEUE, config.RANK_REFRESH_QUEUE,
                   config.REVENUE_INSIGHTS_PATH)
        try:
            config.SEARCH_DEMAND_QUEUE, config.RANK_REFRESH_QUEUE = dq, rq
            config.REVENUE_INSIGHTS_PATH = Path(tmp) / "rev.json"
            cands = ec.collect([], use_universe=False)
            titles_lower = [c["title"].lower() for c in cands]
            assert len(titles_lower) == len(set(titles_lower)) == 3, titles_lower
        finally:
            (config.SEARCH_DEMAND_QUEUE, config.RANK_REFRESH_QUEUE,
             config.REVENUE_INSIGHTS_PATH) = old_cfg
    print("  1. demand/refresh candidates + dedupe ✔")


def test_balancing_rules():
    with tempfile.TemporaryDirectory() as tmp:
        titles = state.recent_titles(config.STATE_PATH, limit=10)
        old = (config.SEARCH_DEMAND_QUEUE, config.RANK_REFRESH_QUEUE,
               config.REVENUE_INSIGHTS_PATH, config.STATE_PATH)
        try:
            config.STATE_PATH = Path(tmp) / "s.db"
            state.init(config.STATE_PATH)
            config.SEARCH_DEMAND_QUEUE = Path(tmp) / "d.json"
            config.RANK_REFRESH_QUEUE = Path(tmp) / "r.json"
            config.REVENUE_INSIGHTS_PATH = Path(tmp) / "rev.json"
            config.SEARCH_DEMAND_QUEUE.write_text(json.dumps({"queue": [
                {"term": f"tspsc group 2 hall ticket {i}", "reason": "no-results",
                 "count": 10 - i} for i in range(4)
            ] + [
                {"term": f"ap police constable notification {i}", "reason": "weak-coverage",
                 "count": 5} for i in range(4)
            ]}), encoding="utf-8")
            config.RANK_REFRESH_QUEUE.write_text(json.dumps({"queue": [
                {"url": f"https://studentup.in/old-{i}/", "clicks_before": 20,
                 "clicks": 5, "position_before": 5.0, "position": 11.0,
                 "clicks_delta": -15} for i in range(3)
            ]}), encoding="utf-8")
            rep = ec.plan(days=4, per_day=3, use_universe=False)
            assert rep["total_slots"] > 0
            # refresh slot prathi roju (1), Sunday ki 2
            for row in rep["schedule"]:
                kinds = [s["type"] for s in row["slots"]]
                assert len(kinds) <= 3, kinds
            # same day lo okate cluster rendu saari raakudadu
            for row in rep["schedule"]:
                clusters = [s.get("cluster") for s in row["slots"]
                            if s["type"] == "new"]
                assert len(clusters) == len(set(clusters)), clusters
            assert rep["by_source"].get("refresh", 0) >= 1
            assert rep["by_source"].get("demand", 0) >= 1
        finally:
            (config.SEARCH_DEMAND_QUEUE, config.RANK_REFRESH_QUEUE,
             config.REVENUE_INSIGHTS_PATH, config.STATE_PATH) = old
        assert titles is not None  # lint-ish
    print("  2. balancing: per-day caps + cluster + refresh slot ✔")


def test_save_and_apply_queue():
    with tempfile.TemporaryDirectory() as tmp:
        old = (config.SEARCH_DEMAND_QUEUE, config.RANK_REFRESH_QUEUE,
               config.REVENUE_INSIGHTS_PATH, config.STATE_PATH, config.OUTPUT_DIR)
        try:
            config.STATE_PATH = Path(tmp) / "s.db"
            state.init(config.STATE_PATH)
            config.OUTPUT_DIR = Path(tmp)
            config.SEARCH_DEMAND_QUEUE = Path(tmp) / "d.json"
            config.RANK_REFRESH_QUEUE = Path(tmp) / "r.json"
            config.REVENUE_INSIGHTS_PATH = Path(tmp) / "rev.json"
            config.SEARCH_DEMAND_QUEUE.write_text(json.dumps({"queue": [
                {"term": "rrb ntpc admit card download", "reason": "no-results",
                 "count": 12}]}), encoding="utf-8")
            config.RANK_REFRESH_QUEUE.write_text(json.dumps({"queue": []}),
                                                 encoding="utf-8")
            rep = ec.plan(days=3, per_day=2, use_universe=False)
            jp, mp = ec.save_plan(rep, Path(tmp) / "cal.json")
            assert jp.exists() and mp.exists()
            md = mp.read_text(encoding="utf-8")
            assert "editorial calendar" in md and "rrb ntpc admit card" in md.lower()
            res = ec.apply_to_queue(rep, limit=5)
            assert res["queued"] >= 1, res
            qfile = Path(res["file"])
            assert qfile.exists() and "rrb ntpc" in qfile.read_text(encoding="utf-8").lower()
            # second apply → dedupe (0 kotha)
            res2 = ec.apply_to_queue(rep, limit=5)
            assert res2["queued"] == 0, res2
        finally:
            (config.SEARCH_DEMAND_QUEUE, config.RANK_REFRESH_QUEUE,
             config.REVENUE_INSIGHTS_PATH, config.STATE_PATH, config.OUTPUT_DIR) = old
    print("  3. save (json+md) + queue apply + dedupe ✔")


def test_revenue_boost():
    with tempfile.TemporaryDirectory() as tmp:
        old = (config.SEARCH_DEMAND_QUEUE, config.RANK_REFRESH_QUEUE,
               config.REVENUE_INSIGHTS_PATH, config.STATE_PATH)
        try:
            config.STATE_PATH = Path(tmp) / "s.db"
            state.init(config.STATE_PATH)
            config.SEARCH_DEMAND_QUEUE = Path(tmp) / "d.json"
            config.RANK_REFRESH_QUEUE = Path(tmp) / "r.json"
            config.REVENUE_INSIGHTS_PATH = Path(tmp) / "rev.json"
            config.SEARCH_DEMAND_QUEUE.write_text(json.dumps({"queue": [
                {"term": "bank po salary details", "reason": "weak-coverage", "count": 5}]}),
                encoding="utf-8")
            config.RANK_REFRESH_QUEUE.write_text(json.dumps({"queue": []}), encoding="utf-8")
            base = ec.collect([], use_universe=False)[0]["score"]
            config.REVENUE_INSIGHTS_PATH.write_text(json.dumps({
                "category_rpm": {"Central Govt Jobs": 180.0},
                "high_rpm_tokens": {"salary": 185.5}}), encoding="utf-8")
            boosted = ec.collect([], use_universe=False)[0]
            assert boosted["score"] > base, (base, boosted)
            assert "high-RPM topic" in boosted["reason"]
        finally:
            (config.SEARCH_DEMAND_QUEUE, config.RANK_REFRESH_QUEUE,
             config.REVENUE_INSIGHTS_PATH, config.STATE_PATH) = old
    print("  4. revenue boost (category + token) ✔")


def test_cli_and_empty_path():
    with tempfile.TemporaryDirectory() as tmp:
        old = (config.SEARCH_DEMAND_QUEUE, config.RANK_REFRESH_QUEUE,
               config.REVENUE_INSIGHTS_PATH, config.STATE_PATH, config.EDITORIAL_CALENDAR_PATH)
        try:
            config.STATE_PATH = Path(tmp) / "s.db"
            state.init(config.STATE_PATH)
            config.SEARCH_DEMAND_QUEUE = Path(tmp) / "d.json"
            config.RANK_REFRESH_QUEUE = Path(tmp) / "r.json"
            config.REVENUE_INSIGHTS_PATH = Path(tmp) / "rev.json"
            config.EDITORIAL_CALENDAR_PATH = Path(tmp) / "cal.json"
            # signals levu + universe off → honest error (rc 1)
            assert ec.run_cli(days=5, per_day=2, universe=False) == 1
            config.SEARCH_DEMAND_QUEUE.write_text(json.dumps({"queue": [
                {"term": "ts dsc hall ticket download link", "reason": "no-results",
                 "count": 7}]}), encoding="utf-8")
            rc = ec.run_cli(days=5, per_day=2, universe=False)
            assert rc == 0
            assert (Path(tmp) / "cal.json").exists()
            rep = json.loads((Path(tmp) / "cal.json").read_text(encoding="utf-8"))
            assert rep["total_slots"] >= 1
            assert date.fromisoformat(rep["schedule"][0]["date"])
        finally:
            (config.SEARCH_DEMAND_QUEUE, config.RANK_REFRESH_QUEUE,
             config.REVENUE_INSIGHTS_PATH, config.STATE_PATH,
             config.EDITORIAL_CALENDAR_PATH) = old
    print("  5. CLI plan + honest empty-signal path ✔")


def main() -> None:
    print("=" * 70)
    print("  v182 — EDITORIAL CALENDAR (90-day plan)")
    print("=" * 70)
    test_candidates_and_dedupe()
    test_balancing_rules()
    test_save_and_apply_queue()
    test_revenue_boost()
    test_cli_and_empty_path()
    print("-" * 70)
    print("ALL v182 EDITORIAL-CALENDAR TESTS PASSED ✔")


if __name__ == "__main__":
    main()
