# -*- coding: utf-8 -*-
"""v108 — generated media originality and licence ledger."""
from __future__ import annotations
import sys, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from autoblog import config, media_ledger  # noqa: E402
SUITES_EXPECTED = 95

def test_media_record_hash_dimensions():
    with tempfile.TemporaryDirectory() as d:
        old = config.OUTPUT_DIR; config.OUTPUT_DIR = Path(d)
        try:
            p = Path(d) / "sample.bin"; p.write_bytes(b"original-media-bytes")
            got = media_ledger.record(p, "tspsc-group-2", "TSPSC Group 2 jobs 2026")
            assert len(got["sha256"]) == 64 and got["licence"] == "original-generated"
            assert Path(d, "media_ledger", "tspsc-group-2.json").exists()
        finally: config.OUTPUT_DIR = old
    print("      media SHA-256 + original-generated licence ledger ✔")

def test_duplicate_hash_detected():
    with tempfile.TemporaryDirectory() as d:
        old = config.OUTPUT_DIR; config.OUTPUT_DIR = Path(d)
        try:
            p = Path(d) / "x.bin"; p.write_bytes(b"same")
            a = media_ledger.record(p, "a", "a")
            b = media_ledger.record(p, "b", "b")
            assert media_ledger.duplicate_hash(b["sha256"], "b") == "a"
        finally: config.OUTPUT_DIR = old
    print("      repeated thumbnail hash flagged ✔")

def test_pipeline_media_ledger_gate():
    src = (ROOT / "autoblog" / "pipeline.py").read_text(encoding="utf-8")
    assert "media_ledger" in src and "_media_flags" in src
    assert "LIVE-PUBLISH BLOCKED: media asset review" in src
    print("      media ledger + live gate wired ✔")

def test_docs():
    r=(ROOT/"README.md").read_text(encoding="utf-8");m=(ROOT/"MANUAL_ADVANCED_CHECKLIST.md").read_text(encoding="utf-8")
    assert "### v108" in r and "PART 65" in m and "95/95" in r and "95/95" in m
    print("      README v108 + PART 65 + 95/95 pinned ✔")
TESTS=[("record",test_media_record_hash_dimensions),("duplicate",test_duplicate_hash_detected),("gate",test_pipeline_media_ledger_gate),("docs",test_docs)]
def main():
    bad=0
    for n,f in TESTS:
        try:f();print(f"  {n} ✔")
        except Exception as e:bad+=1;print(f"  {n} ✘ {type(e).__name__}: {e}")
    print("-"*70);print("ALL v108 MEDIA TESTS PASSED ✔" if not bad else f"{bad} TEST(S) FAILED ✘");return int(bool(bad))
if __name__=="__main__":raise SystemExit(main())
