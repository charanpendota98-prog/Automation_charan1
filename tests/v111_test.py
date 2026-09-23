# -*- coding: utf-8 -*-
"""v111 — correction transparency ledger."""
from __future__ import annotations
import json,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from autoblog import config, corrections  # noqa: E402
SUITES_EXPECTED=96

def test_record_and_chain():
 with tempfile.TemporaryDirectory() as d:
  old=config.OUTPUT_DIR;config.OUTPUT_DIR=Path(d)
  try:
   a=corrections.record(1,"Post","new official date",["https://gov.in/a"],"backup.json")
   b=corrections.record(1,"Post","corrected fee",["https://gov.in/b"])
   assert a["record_hash"] and b["previous_hash"]==a["record_hash"]
   assert corrections.verify()["valid"] and corrections.verify()["records"]==2
  finally:config.OUTPUT_DIR=old
 print("      correction records hash-chained and verifiable ✔")

def test_tamper_detected():
 with tempfile.TemporaryDirectory() as d:
  old=config.OUTPUT_DIR;config.OUTPUT_DIR=Path(d)
  try:
   corrections.record(1,"Post","reason",[]);p=Path(d)/"corrections"/"ledger.jsonl"
   item=json.loads(p.read_text().strip());item["reason"]="tampered";p.write_text(json.dumps(item)+"\n")
   assert not corrections.verify()["valid"]
  finally:config.OUTPUT_DIR=old
 print("      ledger tampering detected ✔")

def test_pipeline_and_cli():
 p=(ROOT/"autoblog/pipeline.py").read_text(encoding="utf-8");m=(ROOT/"autoblog/main.py").read_text(encoding="utf-8")
 assert "corrections as _corr" in p and "--corrections-audit" in m
 print("      update path + correction audit CLI wired ✔")

def test_docs():
 r=(ROOT/"README.md").read_text(encoding="utf-8");m=(ROOT/"MANUAL_ADVANCED_CHECKLIST.md").read_text(encoding="utf-8")
 assert "### v111" in r and "PART 68" in m and "96/96" in r and "96/96" in m
 print("      README v111 + PART 68 + 96/96 pinned ✔")
TESTS=[("chain",test_record_and_chain),("tamper",test_tamper_detected),("wiring",test_pipeline_and_cli),("docs",test_docs)]
def main():
 bad=0
 for n,f in TESTS:
  try:f();print(f"  {n} ✔")
  except Exception as e:bad+=1;print(f"  {n} ✘ {type(e).__name__}: {e}")
 print("-"*70);print("ALL v111 CORRECTION TESTS PASSED ✔" if not bad else f"{bad} TEST(S) FAILED ✘");return int(bool(bad))
if __name__=="__main__":raise SystemExit(main())
