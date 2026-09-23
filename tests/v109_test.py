# -*- coding: utf-8 -*-
"""v109 — PageSpeed/CWV/accessibility audit."""
from __future__ import annotations
import sys, tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from autoblog import config, performance_audit  # noqa: E402
SUITES_EXPECTED=92
class Resp:
    status_code=200
    def json(self):
        return {"lighthouseResult":{"categories":{"performance":{"score":.9},"accessibility":{"score":.95},"seo":{"score":.92}},"audits":{"largest-contentful-paint":{"numericValue":2200,"displayValue":"2.2 s","score":.9},"cumulative-layout-shift":{"numericValue":.03,"displayValue":"0.03","score":.98},"interaction-to-next-paint":{"numericValue":120,"displayValue":"120 ms","score":.95},"first-contentful-paint":{"numericValue":1000,"displayValue":"1.0 s","score":.95},"unused-javascript":{"score":.4,"title":"Reduce unused JS","displayValue":"100 KiB","details":{"type":"opportunity"}}}}}
def test_fetch_maps_scores(monkeypatch=None):
    old=performance_audit.requests.get;performance_audit.requests.get=lambda *a,**k:Resp()
    try:
        r=performance_audit.fetch("https://studentup.in/")
        assert r["scores"]=={"performance":90,"accessibility":95,"seo":92}
        assert r["metrics"]["largest-contentful-paint"]["display"]=="2.2 s"
        assert r["opportunities"]
    finally: performance_audit.requests.get=old
    print("      PageSpeed scores + LCP/CLS/INP/SEO mapped ✔")
def test_review_status():
    old=performance_audit.requests.get
    class Bad(Resp):
        def json(self):
            x=super().json();x["lighthouseResult"]["categories"]["performance"]["score"]=.4;return x
    performance_audit.requests.get=lambda *a,**k:Bad()
    try: assert performance_audit.fetch("https://x/")["status"]=="review"
    finally: performance_audit.requests.get=old
    print("      low performance becomes review, never fake pass ✔")
def test_report_save():
    with tempfile.TemporaryDirectory() as d:
        old=config.OUTPUT_DIR;config.OUTPUT_DIR=Path(d)
        try:
            p=performance_audit.save({"url":"https://studentup.in/x/","status":"review"})
            assert p.exists() and "studentup-in-x" in p.name
        finally: config.OUTPUT_DIR=old
    print("      performance report persists ✔")
def test_cli_docs():
    src=(ROOT/"autoblog/main.py").read_text(encoding="utf-8");r=(ROOT/"README.md").read_text(encoding="utf-8");m=(ROOT/"MANUAL_ADVANCED_CHECKLIST.md").read_text(encoding="utf-8")
    assert "--performance-audit" in src and "performance_audit as _pa" in src
    assert "### v109" in r and "PART 66" in m and "92/92" in r and "92/92" in m
    print("      performance CLI + README/PART 66/89-89 pinned ✔")
TESTS=[("scores",test_fetch_maps_scores),("status",test_review_status),("save",test_report_save),("CLI/docs",test_cli_docs)]
def main():
 bad=0
 for n,f in TESTS:
  try:f();print(f"  {n} ✔")
  except Exception as e:bad+=1;print(f"  {n} ✘ {type(e).__name__}: {e}")
 print("-"*70);print("ALL v109 PERFORMANCE TESTS PASSED ✔" if not bad else f"{bad} TEST(S) FAILED ✘");return int(bool(bad))
if __name__=="__main__":raise SystemExit(main())
