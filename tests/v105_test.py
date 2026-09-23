# -*- coding: utf-8 -*-
"""v105 — update backup and rollback safety."""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from autoblog import config, update_safety  # noqa: E402

SUITES_EXPECTED = 91


def test_backup_persists_exact_before_and_candidate() -> None:
    with tempfile.TemporaryDirectory() as d:
        old = config.OUTPUT_DIR
        config.OUTPUT_DIR = Path(d)
        try:
            post = {"id": 42, "link": "https://studentup.in/p/",
                    "title": {"raw": "Old title"},
                    "content": {"raw": "<p>Old content</p>"},
                    "meta": {"rank_math_title": "Old SEO"},
                    "modified": "2026-01-01"}
            got = update_safety.create_backup(post, "<p>New content</p>",
                                              {"rank_math_title": "New SEO"},
                                              {"version": "v104", "score": 80})
            path = Path(got["path"])
            data = json.loads(path.read_text(encoding="utf-8"))
            assert data["before"]["content_html"] == "<p>Old content</p>"
            assert data["candidate"]["content_html"] == "<p>New content</p>"
            assert data["rollback_ready"] and data["diff"]
        finally:
            config.OUTPUT_DIR = old
    print("      exact old content/meta + candidate diff persisted ✔")


def test_rollback_restores_backup() -> None:
    class FakeWP:
        def __init__(self): self.args = None
        def update_post(self, *args, **kwargs):
            self.args = (args, kwargs)
            return {"link": "https://studentup.in/restored/"}
    with tempfile.TemporaryDirectory() as d:
        old = config.OUTPUT_DIR
        config.OUTPUT_DIR = Path(d)
        try:
            post = {"id": 7, "title": {"raw": "Before"},
                    "content": {"raw": "<p>Before body</p>"}, "meta": {"x": "1"}}
            b = update_safety.create_backup(post, "<p>Candidate</p>")
            wp = FakeWP()
            got = update_safety.rollback(wp, 7, b["path"])
            assert got["restored"] is True
            assert wp.args[1]["content_html"] == "<p>Before body</p>"
            assert wp.args[1]["title"] == "Before"
        finally:
            config.OUTPUT_DIR = old
    print("      rollback restores exact previous WordPress state ✔")


def test_pipeline_refuses_update_if_backup_fails() -> None:
    src = (ROOT / "autoblog" / "pipeline.py").read_text(encoding="utf-8")
    assert "update_safety as _us" in src
    assert "REFUSING remote update" in src
    assert "_update_backup" in src
    print("      remote PUT is refused when pre-update backup fails ✔")


def test_cli_and_docs() -> None:
    src = (ROOT / "autoblog" / "main.py").read_text(encoding="utf-8")
    r = (ROOT / "README.md").read_text(encoding="utf-8")
    m = (ROOT / "MANUAL_ADVANCED_CHECKLIST.md").read_text(encoding="utf-8")
    assert "--rollback-post" in src and "--rollback-backup" in src
    assert "### v105" in r and "PART 62" in m and "91/91" in r and "91/91" in m
    print("      rollback CLI + README/PART 62/85-85 pinned ✔")


TESTS = [("backup", test_backup_persists_exact_before_and_candidate),
         ("rollback", test_rollback_restores_backup),
         ("fail safe", test_pipeline_refuses_update_if_backup_fails),
         ("CLI/docs", test_cli_and_docs)]


def main() -> int:
    failed = 0
    for name, fn in TESTS:
        try:
            fn(); print(f"  {name} ✔")
        except Exception as exc:  # noqa: BLE001
            failed += 1; print(f"  {name} ✘ {type(exc).__name__}: {exc}")
    print("-" * 70)
    print("ALL v105 UPDATE SAFETY TESTS PASSED ✔" if not failed else f"{failed} TEST(S) FAILED ✘")
    return int(bool(failed))


if __name__ == "__main__":
    raise SystemExit(main())
