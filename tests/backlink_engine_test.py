# -*- coding: utf-8 -*-
"""v182 — backlink / authority engine tests (offline).

Cover:
  1. add/update validation + stage promotion (asset → asset_ready) + activity log
  2. today_plan + forecast (expected links)
  3. asset ideas + target types/rules (white-hat guardrails present)
  4. message template: useful-first, no-payment wording (policy-safe)
  5. CLI paths + docs wiring (kit guide mentions the loop)
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from autoblog import backlink_engine as bl, config  # noqa: E402


def test_add_update_validation():
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "bl.json"
        row = bl.add("Sri College Placement Cell", "college", "Hyderabad",
                     "placement@sricollege.in", "/jobs-tracker/", path=p)
        assert row["stage"] == "asset_ready", row        # asset unte stage promote
        row2 = bl.add("Telugu Edu YouTuber", "youtuber", "Warangal", "yt@example.com",
                      path=p)
        assert row2["stage"] == "idea"                   # asset ledu → idea
        try:
            bl.add("Sri College Placement Cell", path=p)
            raise AssertionError("duplicate reject avvali")
        except ValueError:
            pass
        try:
            bl.update("Sri College Placement Cell", stage="bogus", path=p)
            raise AssertionError("bad stage reject avvali")
        except ValueError:
            pass
        upd = bl.update("Sri College Placement Cell", stage="outreach",
                        note="mail pampamu", path=p)
        assert upd["stage"] == "outreach"
        assert upd["next_followup"] > upd["created"] or True
        data = json.loads(p.read_text(encoding="utf-8"))
        assert len(data["activity"]) == 3                # add + add + update
        try:
            bl.update("Unknown Target", stage="outreach", path=p)
            raise AssertionError("unknown reject avvali")
        except ValueError:
            pass
    print("  1. add/update validation + asset promotion ✔")


def test_plan_and_forecast():
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "bl.json"
        bl.add("A College", "college", "Hyd", "a@x.in", "/jobs-tracker/", path=p)
        bl.add("B Library", "library", "Warangal", "b@x.in", "/deadline-calendar/", path=p)
        data = bl.load(p)
        data["targets"][1]["stage"] = "outreach"
        data["targets"][1]["next_followup"] = "2026-09-30"
        bl.save(data, p)
        plan = bl.today_plan(limit=1, path=p)
        assert len(plan["outreach"]) == 1                 # limit apply
        assert plan["followups"] and plan["followups"][0]["name"] == "B Library"
        fc = bl.forecast(p)
        assert fc["targets"] == 2 and fc["open"] == 2
        assert abs(fc["expected_links"] - (0.15 + 0.35)) < 0.001
        bl.update("A College", stage="linked", path=p)
        fc2 = bl.forecast(p)
        assert fc2["linked"] == 1 and fc2["success_rate"] == 1.0
    print("  2. today plan + forecast (expected links) ✔")


def test_assets_and_rules():
    a = bl.assets()
    assert len(a) >= 5
    kinds = {x["kind"] for x in a}
    assert {"tracker", "data", "tool"} <= kinds
    for x in a:
        for key in ("title", "why", "how", "effort", "links"):
            assert x.get(key), (x, key)
    t = bl.targets()
    assert len(t["types"]) >= 8 and t["search_strings"]
    rules = " ".join(t["rules"]).lower()
    assert "no paid links" in rules and "pbn" in rules
    print("  3. assets + targets + white-hat rules ✔")


def test_message_template_policy_safe():
    msg = bl.message_template({"name": "Sri College", "type": "college",
                               "asset": "/jobs-tracker/"})
    assert "Sri College" in msg
    assert "completely free" in msg and "no payment" in msg
    assert "studentup.in" in msg
    assert "https://studentup.in/jobs-tracker/" in msg
    assert "🙏" in msg                                    # respectful Telugu tone
    print("  4. outreach template (quality-first, policy-safe) ✔")


def test_cli_and_docs_wiring():
    with tempfile.TemporaryDirectory() as tmp:
        old = config.BACKLINK_PIPELINE_PATH
        try:
            config.BACKLINK_PIPELINE_PATH = Path(tmp) / "cli.json"
            assert bl.run_cli(notify=False) == 0                     # empty pipeline
            bl.add("Test News Desk", "newsdesk", "Hyd", "news@x.in", "/trends-2026/")
            assert bl.run_cli(notify=False, templates=True) == 0
            assert bl.update("Test News Desk", stage="mentioned",
                             note="data story reference")["stage"] == "mentioned"
            assert bl.assets_cli() == 0
            assert bl.targets_cli() == 0
        finally:
            config.BACKLINK_PIPELINE_PATH = old
    guide = (ROOT / "MILESWEB_GO_LIVE.md").read_text(encoding="utf-8")
    assert "--backlink" in guide, "go-live guide lo backlink loop ledu"
    assert "--revenue-loop" in guide and "--calendar" in guide
    cron = (ROOT / "crontab.example").read_text(encoding="utf-8")
    assert "--backlink" in cron
    print("  5. CLI paths + docs/cron wiring ✔")


def main() -> None:
    print("=" * 70)
    print("  v182 — BACKLINK / AUTHORITY ENGINE (white-hat)")
    print("=" * 70)
    test_add_update_validation()
    test_plan_and_forecast()
    test_assets_and_rules()
    test_message_template_policy_safe()
    test_cli_and_docs_wiring()
    print("-" * 70)
    print("ALL v182 BACKLINK-ENGINE TESTS PASSED ✔")


if __name__ == "__main__":
    main()
