# -*- coding: utf-8 -*-
"""v181 — sponsor pipeline (direct-sales loop) tests (offline).

Cover:
  1. add/update validation + activity log
  2. today_plan(): kotha outreach (limit) + overdue follow-ups
  3. forecast(): pipeline/expected/won values + win rate
  4. outreach_message(): rate card numbers + honest framing (SPONSORED label)
  5. CLI: add → crm → update → notify path (no Telegram creds = skip, rc 0)
  6. docs wiring: MILESWEB_GO_LIVE.md cron line mentions --sponsor-crm
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from autoblog import config, rate_card, sponsor_crm  # noqa: E402


def test_add_update_validation():
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "sp.json"
        row = sponsor_crm.add("Sri Coaching", "coaching", "Hyderabad", "9848012345",
                              8000, path=p)
        assert row["stage"] == "new" and row["value"] == 8000
        assert row["next_followup"], "kotha prospect ki today follow-up date undali"
        try:
            sponsor_crm.add("Sri Coaching", path=p)
            raise AssertionError("duplicate name allow avvakudadu")
        except ValueError:
            pass
        try:
            sponsor_crm.update("Sri Coaching", stage="nonsense", path=p)
            raise AssertionError("tappu stage reject avvali")
        except ValueError:
            pass
        row = sponsor_crm.update("Sri Coaching", stage="negotiating",
                                 note="call chesam", path=p)
        assert row["stage"] == "negotiating"
        assert "call chesam" in row["notes"]
        data = json.loads(p.read_text(encoding="utf-8"))
        assert len(data["activity"]) == 2                     # add + update
        try:
            sponsor_crm.update("Lenin College", stage="contacted", path=p)
            raise AssertionError("unknown prospect reject avvali")
        except ValueError:
            pass
    print("  1. add/update validation + activity log ✔")


def test_today_plan_and_forecast():
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "sp.json"
        sponsor_crm.add("A College", "college", "Warangal", "9000000001", 5000, path=p)
        sponsor_crm.add("B Coaching", "coaching", "Guntur", "9000000002", 8000, path=p)
        sponsor_crm.add("C Books", "bookshop", "Hyderabad", "9000000003", 3000, path=p)
        # B ni contacted chesi follow-up ni yesterday ki set (overdue)
        data = sponsor_crm.load(p)
        data["prospects"][1]["stage"] = "contacted"
        data["prospects"][1]["next_followup"] = "2026-09-30"
        sponsor_crm.save(data, p)
        plan = sponsor_crm.today_plan(limit=2, path=p)
        assert len(plan["outreach"]) == 2, "roju outreach limit apply avvali"
        assert plan["followups"] and plan["followups"][0]["name"] == "B Coaching"
        fc = sponsor_crm.forecast(p)
        assert fc["prospects"] == 3 and fc["open"] == 3
        assert fc["pipeline_value"] == 16000
        # expected = 5000*0.05 + 8000*0.15 + 3000*0.05
        assert fc["expected_value"] == round(250 + 1200 + 150)
        assert fc["win_rate"] == 0.0
        sponsor_crm.update("A College", stage="won", value=5500, path=p)
        fc2 = sponsor_crm.forecast(p)
        assert fc2["won_value"] == 5500 and fc2["win_rate"] == 1.0
    print("  2. today plan (limit + overdue) + forecast ✔")


def test_outreach_message():
    msg = sponsor_crm.outreach_message({"name": "Sri Coaching", "type": "coaching"})
    slot = rate_card.highest_ticket()
    pkg = rate_card.full_package_price()
    assert "Sri Coaching" in msg
    assert f"₹{slot:,}" in msg and f"₹{pkg:,}" in msg      # rate card nunchi
    assert "SPONSORED" in msg                              # policy-safe promise
    assert "studentup.in" in msg
    print("  3. outreach template (rate card + policy-safe) ✔")


def test_cli_paths():
    with tempfile.TemporaryDirectory() as tmp:
        old = config.SPONSOR_PIPELINE_PATH
        try:
            config.SPONSOR_PIPELINE_PATH = Path(tmp) / "cli.json"
            assert sponsor_crm.run_cli(notify=False) == 0          # empty pipeline
            assert sponsor_crm.add("Test Inst", "coaching", "Hyd", "999", 4000)["stage"] == "new"
            assert sponsor_crm.run_cli(notify=False, templates=True) == 0
            assert sponsor_crm.update("Test Inst", stage="replied", note="ok")["stage"] == "replied"
            assert sponsor_crm.targets_cli() == 0
        finally:
            config.SPONSOR_PIPELINE_PATH = old
    print("  4. CLI paths (add → plan → update → targets) ✔")


def test_docs_wiring():
    kit = (ROOT / "MILESWEB_GO_LIVE.md").read_text(encoding="utf-8")
    assert "--sponsor-crm" in kit, "go-live guide lo sponsor loop ledu"
    assert "--search-demand" in kit and "--rank-trend" in kit
    deploy = (ROOT / "DEPLOY_MILESWEB.md").read_text(encoding="utf-8")
    assert "--rank-trend" in deploy
    cron = (ROOT / "crontab.example").read_text(encoding="utf-8")
    assert "--sponsor-crm" in cron
    print("  5. docs + cron wiring ✔")


def main() -> None:
    print("=" * 70)
    print("  v181 — SPONSOR PIPELINE (direct sales loop)")
    print("=" * 70)
    test_add_update_validation()
    test_today_plan_and_forecast()
    test_outreach_message()
    test_cli_paths()
    test_docs_wiring()
    print("-" * 70)
    print("ALL v181 SPONSOR-PIPELINE TESTS PASSED ✔")


if __name__ == "__main__":
    main()
