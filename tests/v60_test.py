# -*- coding: utf-8 -*-
"""v60 tests — SITE GUARDIAN: "eppatiki advanced ga" automatic keeper.

Enduku idi:
  Site/bot rojuki roju advanced ga undali ante — tiles desync, menu item poyadam,
  feed aagipovadam, ads.txt poyadam lantivi silent ga jaruguthayi. Guardian roju
  okkasari anni check chesi Telegram alert + logs/guardian.json status istundi.

Checks (offline only):
  * 11 checks unnayi, okkokkati (ok, detail, fix) istundi
  * tiles sync: site tiles ↔ tests/*.py count ↔ jsdom literal
  * first-look UI blocks (ticker/used/breaking/feed fetch/nav) guard — remove ayithe fail
  * warn_only severity: env creds pending = warn (system break kaadu), exit 0
  * status file: atomic + 14-run history
  * Telegram summary text: ok/warn/fail icons + fix lines
  * CLI wiring + daily hook (roju okkasari, state meta tho once/day)
  * docs (MANUAL PART 19 + GO_LIVE + README)

Run: python tests/v60_test.py   (also via python run.py --test-all)
"""
from __future__ import annotations

import io
import json
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from autoblog import config, guardian  # noqa: E402

INDEX = ROOT / "preview" / "index.html"
JSDOM = ROOT / "tests" / "runtime" / "jsdom_runtime_test.js"
MAIN = ROOT / "autoblog" / "main.py"


def test_checks_contract():
    assert len(guardian.CHECKS) >= 11, guardian.CHECKS
    ids = [c[0] for c in guardian.CHECKS]
    for want in ("site_files", "first_look_ui", "tiles_sync", "robots_sitemap",
                 "ads_txt", "breaking_feed", "ads_inventory", "keyword_pillar_lock",
                 "menu_wiring", "storage", "env_readiness"):
        assert want in ids, want
    assert len(set(ids)) == len(ids), "duplicate check ids"
    for name, fn, warn_only in guardian.CHECKS:
        ok, detail, fix = fn()
        assert isinstance(ok, bool) and detail, (name, detail)
        assert isinstance(fix, str)


def test_summary_shape_and_severity():
    summary = guardian.run_checks()
    assert summary["checked"] == len(guardian.CHECKS)
    assert summary["passed"] + summary["failed"] + summary["warned"] == summary["checked"]
    assert summary["ok"] is (summary["failed"] == 0)
    bad = [r["id"] for r in summary["results"] if not r["ok"] and not r["warn_only"]]
    assert not bad, "system checks fail ayinayi: %s" % bad
    warn_only_ids = {c[0] for c in guardian.CHECKS if c[2]}
    assert warn_only_ids == {"env_readiness"}, warn_only_ids


def test_tiles_sync_detects_desync():
    """Tile number ni temporarily change chesi — guardian pattukuntunda?"""
    html = INDEX.read_text(encoding="utf-8")
    suites = len(list((ROOT / "tests").glob("*_test.py")))
    m = re.search(r'<div class="qtile"><b>(\d+)/\1</b>', html)
    assert m and m.group(1) == str(suites), "suite tile %s vs files %d" % (m.group(1) if m else "?", suites)  # noqa: E501
    broken = html.replace("<b>%d/%d</b>" % (suites, suites), "<b>7/7</b>", 1)
    with tempfile.TemporaryDirectory() as tmp:
        preview = Path(tmp) / "preview"
        preview.mkdir()
        (preview / "index.html").write_text(broken, encoding="utf-8")
        orig = guardian.PREVIEW
        try:
            guardian.PREVIEW = preview
            ok, detail, fix = guardian.check_tiles_sync()
        finally:
            guardian.PREVIEW = orig
    assert not ok, "desync pattukovadam ledu: " + detail
    assert "7/7" in detail, detail


def test_first_look_guard_detects_missing_block():
    html = INDEX.read_text(encoding="utf-8")
    stripped = html.replace('id="tickerwrap"', 'id="gone"', 1)
    with tempfile.TemporaryDirectory() as tmp:
        preview = Path(tmp) / "preview"
        preview.mkdir()
        (preview / "index.html").write_text(stripped, encoding="utf-8")
        orig = guardian.PREVIEW
        try:
            guardian.PREVIEW = preview
            ok, detail, _fix = guardian.check_first_look_ui()
        finally:
            guardian.PREVIEW = orig
    assert not ok and "టికర్" in detail, detail


def test_status_file_history():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "guardian.json"
        for i in range(16):
            summary = {"at": "2026-09-18T20:0%d:00+05:30" % (i % 10), "checked": 11,
                       "passed": 10, "failed": 0, "warned": 1,
                       "results": [{"id": "x", "ok": True, "warn_only": False,
                                    "detail": "d", "fix": "", "ms": 1}]}
            guardian.write_status(summary, path=path)
        data = json.loads(path.read_text(encoding="utf-8"))
        assert len(data["history"]) == 14, (len(data["history"]), "history 14 varaku cap avvali")
        assert not list(Path(tmp).glob("*.tmp")), "atomic write tarvata .tmp undakudadu"


def test_telegram_summary_text():
    results = [
        {"id": "site_files", "ok": True, "warn_only": False, "detail": "12 files ready", "fix": "", "ms": 1},
        {"id": "tiles_sync", "ok": False, "warn_only": False, "detail": "tile mismatch", "fix": "bump", "ms": 1},
        {"id": "env_readiness", "ok": False, "warn_only": True, "detail": "creds ledu", "fix": ".env", "ms": 1},
    ]
    summary = {"checked": 3, "passed": 1, "failed": 1, "warned": 1, "results": results,
               "at": "2026-09-18T20:00:00+05:30", "ok": False}
    tg = guardian.summary_text(summary, telegram=True)
    assert "SITE GUARDIAN" in tg and "1/3" in tg
    assert "❌" in tg and "⚠️" in tg, tg[:200]
    assert "↳ fix:" in tg and "<code>bump</code>" in tg
    plain = guardian.summary_text(summary)
    assert "owner-pending" in plain and "tiles_sync" in plain


def test_guard_writes_status_and_returns():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "guardian.json"
        orig = config.GUARDIAN_STATE
        try:
            config.GUARDIAN_STATE = path          # _status_file() config nunchi teesukuntundi
            summary = guardian.guard(notify=False, print_out=False)
        finally:
            config.GUARDIAN_STATE = orig
        assert path.exists(), "status file rasi undali"
        assert summary["ok"] is True, "sandbox lo system checks pass avvali"


def test_env_readiness_is_warn_only():
    ok, detail, fix = guardian.check_env_readiness()
    if not ok:
        assert "set avvaledu" in detail and ".env" in fix, detail
    # readiness fail ayina system 'ok' ga undali (owner pani, break kaadu)
    assert guardian.CHECKS[[c[0] for c in guardian.CHECKS].index("env_readiness")][2] is True


def test_bot_wiring_cli_and_daily_hook():
    main = MAIN.read_text(encoding="utf-8")
    assert "def guardian_run(" in main
    assert '"--guardian"' in main and '"--guardian-notify"' in main
    assert "guardian.guard(notify=True, print_out=False)" in main, "daily hook missing"
    assert 'guardian:{today.isoformat()}' in main, "once-per-day state guard missing"
    assert 'breaking:{today.isoformat()}' in main, "v59 feed daily refresh hook missing"
    run = (ROOT / "run.py").read_text(encoding="utf-8")
    assert "--guardian" in run, "run.py help lo guardian undali"
    assert "GUARDIAN_ENABLED" in main and config.GUARDIAN_HOUR >= 0


def test_docs_v60():
    manual = (ROOT / "MANUAL_ADVANCED_CHECKLIST.md").read_text(encoding="utf-8")
    assert "PART 19" in manual and "SITE GUARDIAN" in manual
    go = (ROOT / "GO_LIVE_CHECKLIST.md").read_text(encoding="utf-8")
    assert "--guardian" in go
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "--guardian" in readme
    env = (ROOT / ".env.example").read_text(encoding="utf-8")
    assert "GUARDIAN_ENABLED" in env and "GUARDIAN_HOUR" in env


def main():
    print("=" * 66)
    print("  v60 — SITE GUARDIAN: eppatiki advanced ga (roju automatic check + alert)")
    print("=" * 66)
    tests = [
        ("11 checks contract (ok/detail/fix)", test_checks_contract),
        ("summary shape + severity (warn_only)", test_summary_shape_and_severity),
        ("tiles desync pattukuntundi", test_tiles_sync_detects_desync),
        ("first-look block poyinappudu fail", test_first_look_guard_detects_missing_block),
        ("status file: atomic + 14-run history", test_status_file_history),
        ("Telegram summary: icons + fix lines", test_telegram_summary_text),
        ("guard() status rasi summary istundi", test_guard_writes_status_and_returns),
        ("owner creds pending = warn (system break kaadu)", test_env_readiness_is_warn_only),
        ("bot wiring: CLI + daily hook + once/day", test_bot_wiring_cli_and_daily_hook),
        ("docs: MANUAL PART 19 + GO_LIVE + README", test_docs_v60),
    ]
    failed = 0
    for name, fn in tests:
        try:
            fn()
            print(f"  {name} ✔")
        except AssertionError as exc:
            failed += 1
            print(f"  {name} ✘  {exc}")
        except Exception as exc:  # noqa: BLE001
            failed += 1
            print(f"  {name} ✘  {type(exc).__name__}: {exc}")
    print("-" * 66)
    if failed:
        print(f"  {failed} TEST(S) FAILED ✘")
        return 1
    print("ALL v60 SITE-GUARDIAN TESTS PASSED ✔")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
