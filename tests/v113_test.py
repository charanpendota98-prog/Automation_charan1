# -*- coding: utf-8 -*-
"""v113 — deduplicated operations alerts."""
from __future__ import annotations
import sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from autoblog import config, ops_alerts, state  # noqa: E402
SUITES_EXPECTED=95

def test_alert_dedup():
 with tempfile.TemporaryDirectory() as d:
  old=config.STATE_PATH;config.STATE_PATH=Path(d)/"state.db"
  try:
   state.init(config.STATE_PATH)
   old_collect=ops_alerts.control_center.collect
   ops_alerts.control_center.collect=lambda:{"status":"action-required","actions":["review GSC alert"]}
   a=ops_alerts.check_and_alert(send=False);b=ops_alerts.check_and_alert(send=False)
   assert a["changed"] is True and b["changed"] is False
  finally:
   ops_alerts.control_center.collect=old_collect;config.STATE_PATH=old
 print("      identical action alerts deduplicated ✔")

def test_healthy_no_alert():
 with tempfile.TemporaryDirectory() as d:
  old=config.STATE_PATH;config.STATE_PATH=Path(d)/"state.db"
  try:
   state.init(config.STATE_PATH);old_collect=ops_alerts.control_center.collect
   ops_alerts.control_center.collect=lambda:{"status":"healthy","actions":[]}
   r=ops_alerts.check_and_alert(send=False);assert r["changed"] is False and not r["actions"]
  finally:ops_alerts.control_center.collect=old_collect;config.STATE_PATH=old
 print("      healthy run creates no alert noise ✔")

def test_wiring_docs():
 src=(ROOT/"autoblog/main.py").read_text(encoding="utf-8");r=(ROOT/"README.md").read_text(encoding="utf-8");m=(ROOT/"MANUAL_ADVANCED_CHECKLIST.md").read_text(encoding="utf-8")
 assert "--ops-alert" in src and "ops_alerts as _oa" in src and "### v113" in r and "PART 70" in m and "95/95" in r and "95/95" in m
 print("      ops-alert CLI/config/docs wired ✔")
TESTS=[("dedupe",test_alert_dedup),("healthy",test_healthy_no_alert),("wiring",test_wiring_docs)]
def main():
 bad=0
 for n,f in TESTS:
  try:f();print(f"  {n} ✔")
  except Exception as e:bad+=1;print(f"  {n} ✘ {type(e).__name__}: {e}")
 print("-"*70);print("ALL v113 OPS ALERT TESTS PASSED ✔" if not bad else f"{bad} TEST(S) FAILED ✘");return int(bool(bad))
if __name__=="__main__":raise SystemExit(main())
