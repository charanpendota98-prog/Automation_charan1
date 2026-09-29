# -*- coding: utf-8 -*-
"""v160 — final go-live audit orchestrator."""
from __future__ import annotations

from pathlib import Path

from autoblog import final_audit

ROOT = Path(__file__).resolve().parents[1]


def test_every_gate_command_exists():
    for label, cmd, meaning in final_audit.GATES:
        assert label and meaning, "gate ki label/meaning ledu"
        if cmd[0] in ("node",):
            target = ROOT / cmd[1]
        elif "-m" in cmd:
            continue  # module call (pytest)
        else:
            target = ROOT / cmd[1]
        assert target.exists(), f"gate script ledu: {target}"
    print(f"      all {len(final_audit.GATES)} gate scripts exist ✔")


def test_a_failing_gate_blocks_go(monkeypatch, capsys):
    monkeypatch.setattr(final_audit, "GATES",
                        [("fake", ["false"], "never passes")])
    monkeypatch.setattr(final_audit, "_run", lambda cmd: (False, "boom"))
    rc = final_audit.run_cli()
    out = capsys.readouterr().out
    assert rc == 1, "fail ayina GO ichindi"
    assert "NO-GO" in out and "never passes" in out
    print("      a failing gate produces NO-GO with the fix hint ✔")


def test_all_green_gives_go(monkeypatch, capsys):
    monkeypatch.setattr(final_audit, "GATES",
                        [("fake", ["true"], "passes")])
    monkeypatch.setattr(final_audit, "_run", lambda cmd: (True, "ok"))
    monkeypatch.setattr(final_audit, "theme_zip",
                        lambda: (ROOT / "wordpress-theme" / "studentup-theme.zip", "830 KB"))
    rc = final_audit.run_cli()
    out = capsys.readouterr().out
    assert rc == 0 and "GO" in out and "NO-GO" not in out
    print("      all-green run prints GO with the zip path ✔")


def test_missing_zip_is_a_blocker(monkeypatch, capsys):
    monkeypatch.setattr(final_audit, "GATES", [])
    monkeypatch.setattr(final_audit, "theme_zip", lambda: (ROOT / "nope.zip", ""))
    rc = final_audit.run_cli()
    assert rc == 1, "zip lekunda kuda GO ichindi"
    assert "build_wp_theme" in capsys.readouterr().out
    print("      missing theme zip blocks the release ✔")


def test_real_zip_is_built():
    path, size = final_audit.theme_zip()
    assert path.exists() and size, "theme zip build avvaledu"
    print(f"      theme zip present ({size}) ✔")


def test_flag_documented():
    main = (ROOT / "autoblog" / "main.py").read_text(encoding="utf-8")
    assert '"--final-audit"' in main and "args.final_audit" in main
    for name in ("README.md", "MANUAL_ADVANCED_CHECKLIST.md", "GO_LIVE_CHECKLIST.md"):
        assert "--final-audit" in (ROOT / name).read_text(encoding="utf-8"), name
    print("      --final-audit wired and documented in all 3 docs ✔")
