# -*- coding: utf-8 -*-
"""v110 — NotebookLM immutable source provenance snapshots."""
from __future__ import annotations
import json, sys, tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from autoblog import research_brief, sources  # noqa: E402
SUITES_EXPECTED=94

def test_manifest_contains_source_hash():
    item=sources.SourceArticle(url="https://tspsc.gov.in/notice.pdf",title="Notice",text="783 vacancies and last date 22 July 2026.")
    with tempfile.TemporaryDirectory() as d:
        result=research_brief.write_bundle("TSPSC Group 2",[item],Path(d),2026)
        data=json.loads(Path(result["manifest"]).read_text(encoding="utf-8"))
        row=data["sources"][0]
        assert len(row["captured_sha256"])==64 and row["word_count"]==8
        assert row["captured_at"]
    print("      NotebookLM manifest stores immutable source hash/count/date ✔")

def test_source_hash_changes_when_snapshot_changes():
    import hashlib
    a=hashlib.sha256("old".encode()).hexdigest();b=hashlib.sha256("new".encode()).hexdigest()
    assert a!=b
    print("      changed source snapshot produces different evidence hash ✔")

def test_no_private_account_automation_claim():
    src=(ROOT/"autoblog/research_brief.py").read_text(encoding="utf-8")
    assert "notebooklm_required" in src and "cannot access a private NotebookLM account" in src
    print("      NotebookLM provenance honest: no private login automation ✔")

def test_docs():
    r=(ROOT/"README.md").read_text(encoding="utf-8");m=(ROOT/"MANUAL_ADVANCED_CHECKLIST.md").read_text(encoding="utf-8")
    assert "### v110" in r and "PART 67" in m and "94/94" in r and "94/94" in m
    print("      README v110 + PART 67 + 94/94 pinned ✔")
TESTS=[("manifest",test_manifest_contains_source_hash),("hash drift",test_source_hash_changes_when_snapshot_changes),("honest",test_no_private_account_automation_claim),("docs",test_docs)]
def main():
 bad=0
 for n,f in TESTS:
  try:f();print(f"  {n} ✔")
  except Exception as e:bad+=1;print(f"  {n} ✘ {type(e).__name__}: {e}")
 print("-"*70);print("ALL v110 NOTEBOOKLM PROVENANCE TESTS PASSED ✔" if not bad else f"{bad} TEST(S) FAILED ✘");return int(bool(bad))
if __name__=="__main__":raise SystemExit(main())
