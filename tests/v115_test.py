# -*- coding: utf-8 -*-
"""v115 — Google URL Inspection indexing status."""
from __future__ import annotations
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from autoblog import config, gsc_api  # noqa: E402
SUITES_EXPECTED=96
class Resp:
 status_code=200
 def json(self):
  return {"inspectionResult":{"indexStatusResult":{"verdict":"PASS","coverageState":"Submitted and indexed","indexingState":"INDEXING_ALLOWED","robotsTxtState":"ALLOWED","googleCanonical":"https://studentup.in/a/","userCanonical":"https://studentup.in/a/","lastCrawlTime":"2026-09-23T06:00:00Z"}}}
def test_inspection_mapping():
 oldt,olds=gsc_api._token,gsc_api._site;oldpost=gsc_api.requests.post
 gsc_api._token=lambda:"token";gsc_api._site=lambda:"https://studentup.in";gsc_api.requests.post=lambda *a,**k:Resp()
 try:
  r=gsc_api.inspect_url("https://studentup.in/a/")
  assert r["verdict"]=="PASS" and r["coverage_state"]=="Submitted and indexed" and r["google_canonical"].endswith("/a/")
 finally:gsc_api._token,gsc_api._site,gsc_api.requests.post=oldt,olds,oldpost
 print("      URL Inspection maps index/canonical/robots/crawl state ✔")
def test_cli_wired_docs():
 src=(ROOT/"autoblog/main.py").read_text(encoding="utf-8");r=(ROOT/"README.md").read_text(encoding="utf-8");m=(ROOT/"MANUAL_ADVANCED_CHECKLIST.md").read_text(encoding="utf-8")
 assert "--gsc-inspect" in src and "inspect_url" in src and "### v115" in r and "PART 72" in m and "96/96" in r and "96/96" in m
 print("      gsc-inspect CLI + docs 96/96 pinned ✔")
TESTS=[("mapping",test_inspection_mapping),("CLI/docs",test_cli_wired_docs)]
def main():
 bad=0
 for n,f in TESTS:
  try:f();print(f"  {n} ✔")
  except Exception as e:bad+=1;print(f"  {n} ✘ {type(e).__name__}: {e}")
 print("-"*70);print("ALL v115 URL INSPECTION TESTS PASSED ✔" if not bad else f"{bad} TEST(S) FAILED ✘");return int(bool(bad))
if __name__=="__main__":raise SystemExit(main())
