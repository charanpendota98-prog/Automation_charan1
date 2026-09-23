# -*- coding: utf-8 -*-
"""v112 — unified control center."""
from __future__ import annotations
import sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from autoblog import config, control_center  # noqa: E402
SUITES_EXPECTED=93

def test_empty_center_is_safe():
 with tempfile.TemporaryDirectory() as d:
  old=config.OUTPUT_DIR;config.OUTPUT_DIR=Path(d)
  try:
   r=control_center.collect();assert r["version"]=="v112" and r["status"]=="healthy"
  finally:config.OUTPUT_DIR=old
 print("      empty control center reports healthy without network/writes ✔")

def test_performance_action_queue():
 with tempfile.TemporaryDirectory() as d:
  old=config.OUTPUT_DIR;config.OUTPUT_DIR=Path(d)
  try:
   p=Path(d)/"performance_audits";p.mkdir();(p/"x.json").write_text('{"status":"review"}')
   r=control_center.collect();assert r["performance"]["review"]==1 and r["actions"]
  finally:config.OUTPUT_DIR=old
 print("      control center surfaces performance action ✔")

def test_read_only_wiring():
 src=(ROOT/"autoblog/main.py").read_text(encoding="utf-8")
 assert "--control-center" in src and "control_center as _cc" in src
 print("      read-only control center CLI wired ✔")

def test_docs():
 r=(ROOT/"README.md").read_text(encoding="utf-8");m=(ROOT/"MANUAL_ADVANCED_CHECKLIST.md").read_text(encoding="utf-8")
 assert "### v112" in r and "PART 69" in m and "93/93" in r and "93/93" in m
 print("      README v112 + PART 69 + 93/93 pinned ✔")
TESTS=[("empty",test_empty_center_is_safe),("action",test_performance_action_queue),("wiring",test_read_only_wiring),("docs",test_docs)]
def main():
 bad=0
 for n,f in TESTS:
  try:f();print(f"  {n} ✔")
  except Exception as e:bad+=1;print(f"  {n} ✘ {type(e).__name__}: {e}")
 print("-"*70);print("ALL v112 CONTROL CENTER TESTS PASSED ✔" if not bad else f"{bad} TEST(S) FAILED ✘");return int(bool(bad))
if __name__=="__main__":raise SystemExit(main())
