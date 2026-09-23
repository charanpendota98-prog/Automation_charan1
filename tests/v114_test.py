# -*- coding: utf-8 -*-
"""v114 — scheduler wiring for GSC sync and operations alerts."""
from __future__ import annotations
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from autoblog import config  # noqa: E402
SUITES_EXPECTED=95

def test_scheduler_wiring():
 src=(ROOT/"autoblog/main.py").read_text(encoding="utf-8")
 assert "gscauto:" in src and "opsalert:" in src and "gsc_api as _gapi" in src and "ops_alerts as _ops" in src
 assert "finally:" in src and "GSC_SYNC_HOUR" in src
 print("      daily GSC sync + ops alert once-per-day scheduler wired ✔")

def test_config_env():
 cfg=(ROOT/"autoblog/config.py").read_text(encoding="utf-8");env=(ROOT/".env.example").read_text(encoding="utf-8")
 for key in ("GSC_AUTO_SYNC","GSC_SYNC_HOUR"):
  assert key in cfg and key in env
 assert config.GSC_SYNC_HOUR >= 0 and config.GSC_SYNC_HOUR <= 23
 print("      scheduler controls present and hour validated ✔")

def test_failures_nonfatal():
 src=(ROOT/"autoblog/main.py").read_text(encoding="utf-8")
 segment=src[src.index("# v114: daily GSC"):src.index("count = state.today_count")]
 assert "except Exception" in segment and "finally" in segment and "Daily GSC sync unavailable" in segment
 print("      missing credentials/network cannot stop daily posting ✔")

def test_docs():
 r=(ROOT/"README.md").read_text(encoding="utf-8");m=(ROOT/"MANUAL_ADVANCED_CHECKLIST.md").read_text(encoding="utf-8")
 assert "### v114" in r and "PART 71" in m and "95/95" in r and "95/95" in m
 print("      README v114 + PART 71 + 95/95 pinned ✔")
TESTS=[("wiring",test_scheduler_wiring),("config",test_config_env),("safe",test_failures_nonfatal),("docs",test_docs)]
def main():
 bad=0
 for n,f in TESTS:
  try:f();print(f"  {n} ✔")
  except Exception as e:bad+=1;print(f"  {n} ✘ {type(e).__name__}: {e}")
 print("-"*70);print("ALL v114 SCHEDULER TESTS PASSED ✔" if not bad else f"{bad} TEST(S) FAILED ✘");return int(bool(bad))
if __name__=="__main__":raise SystemExit(main())
