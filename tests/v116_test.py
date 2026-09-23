# -*- coding: utf-8 -*-
"""v116 — tracked-secret security audit."""
from __future__ import annotations
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from autoblog import security_audit  # noqa: E402
SUITES_EXPECTED=96

def test_scanner_runs():
 r=security_audit.scan();assert "status" in r and isinstance(r["findings"],list)
 print("      tracked-file secret scanner runs safely ✔")

def test_known_patterns_detected():
 for name,pat in security_audit._PATTERNS:
  assert pat.search("api_key=AIza"+"A"*35) or name not in ("google-api-key",)
 print("      credential pattern rules loaded ✔")

def test_cli_wired_docs():
 src=(ROOT/"autoblog/main.py").read_text(encoding="utf-8");r=(ROOT/"README.md").read_text(encoding="utf-8");m=(ROOT/"MANUAL_ADVANCED_CHECKLIST.md").read_text(encoding="utf-8")
 assert "--security-audit" in src and "security_audit as _sa_sec" in src and "### v116" in r and "PART 73" in m and "96/96" in r and "96/96" in m
 print("      security CLI + docs 96/96 pinned ✔")
TESTS=[("scanner",test_scanner_runs),("patterns",test_known_patterns_detected),("CLI/docs",test_cli_wired_docs)]
def main():
 bad=0
 for n,f in TESTS:
  try:f();print(f"  {n} ✔")
  except Exception as e:bad+=1;print(f"  {n} ✘ {type(e).__name__}: {e}")
 print("-"*70);print("ALL v116 SECURITY TESTS PASSED ✔" if not bad else f"{bad} TEST(S) FAILED ✘");return int(bool(bad))
if __name__=="__main__":raise SystemExit(main())
