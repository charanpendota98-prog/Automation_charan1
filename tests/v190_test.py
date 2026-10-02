# -*- coding: utf-8 -*-
"""v190 — `--daily` OKE COMMAND tests (offline).

User ask: "draf elaga chesthavo alaga cheyali anthe daily okaynaa malli anni nuvve
set cheyu perefctgaa" → oke command: drafts (hook lead tho) → guardian → list (ade
hook format) → Telegram + WhatsApp send. Anni nene set chesi, cron lo okka line.

Cover:
  1. daily_run order + step chaining (radar → guardian → run_morning)
  2. Non-fatal: draft step fail/exception aina list step continue (drafts fail ≠ list fail)
  3. Flags: --daily-no-drafts / --daily-no-guardian / --daily-no-send / --forward-no-whatsapp
  4. rc passthrough (list rc as-is: 0/1/2/3)
  5. CONSISTENCY ("draф elaga chesthavo alaga"): draft hook subject == list item subject
     (okate `hooks` module — drift raakudadu) + list Telugu / draft English (v73 gate)
  6. cron okka line (`30 6` → `--daily`) + docs wiring
"""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from autoblog import hooks as hk, main as mn, opportunity_digest as od  # noqa: E402

TODAY = date(2026, 10, 2)


def _patch(monkey_daily, calls, radar_rc=0, list_rc=0, radar_exc=False):
    """daily_run lopala unna step functions ni replace (offline)."""
    import autoblog.main as m

    def fake_radar(process_posts=True):
        calls.append(("radar", process_posts))
        if radar_exc:
            raise RuntimeError("network down (test)")
        return radar_rc

    def fake_guardian(notify=False, quiet=False):
        calls.append(("guardian", quiet))
        return 0

    def fake_morning(save_files=True, today=None, send=True, whatsapp=True, telegram=True):
        calls.append(("list", send, whatsapp, telegram, save_files))
        return list_rc

    m.radar_run = fake_radar
    m.guardian_run = fake_guardian
    monkey_daily["forward_list"].run_morning = fake_morning


def test_daily_order():
    import autoblog.forward_list as flm
    calls: list = []
    old_radar, old_guard = mn.radar_run, mn.guardian_run
    old_morning = flm.run_morning
    _patch({"forward_list": flm}, calls)
    try:
        rc = mn.daily_run()
        assert rc == 0
        assert [c[0] for c in calls] == ["radar", "guardian", "list"], calls
        assert calls[0][1] is True, "radar process_posts=True kaadu"
        assert calls[1][1] is True, "guardian quiet=True kaadu"
        assert calls[2][1:] == (True, True, True, True), calls[2]
    finally:
        mn.radar_run, mn.guardian_run, flm.run_morning = old_radar, old_guard, old_morning
    print("  1. daily_run order (drafts → guardian → list+send) ✔")


def test_non_fatal_steps():
    import autoblog.forward_list as flm
    calls: list = []
    old_radar, old_guard = mn.radar_run, mn.guardian_run
    old_morning = flm.run_morning
    # radar exception → list step kuda jaragali (drafts fail ≠ list fail)
    _patch({"forward_list": flm}, calls, radar_exc=True)
    try:
        assert mn.daily_run() == 0
        assert [c[0] for c in calls] == ["radar", "guardian", "list"], calls
        # radar non-zero rc → continue
        calls.clear()
        _patch({"forward_list": flm}, calls, radar_rc=1)
        assert mn.daily_run() == 0
        assert [c[0] for c in calls] == ["radar", "guardian", "list"]
    finally:
        mn.radar_run, mn.guardian_run, flm.run_morning = old_radar, old_guard, old_morning
    print("  2. non-fatal (draft step fail/exception aina list continue) ✔")


def test_flags_and_rc():
    import autoblog.forward_list as flm
    calls: list = []
    old_radar, old_guard = mn.radar_run, mn.guardian_run
    old_morning = flm.run_morning
    try:
        # --daily-no-drafts + --daily-no-guardian → list mattrame
        _patch({"forward_list": flm}, calls)
        rc = mn.daily_run(drafts=False, guardian_check=False)
        assert rc == 0 and [c[0] for c in calls] == ["list"], calls
        # --daily-no-send / --forward-no-whatsapp passthrough
        calls.clear()
        _patch({"forward_list": flm}, calls)
        mn.daily_run(send=False, whatsapp=False, drafts=False, guardian_check=False)
        assert calls == [("list", False, False, True, True)], calls
        # rc passthrough (list rc as-is)
        for expected in (1, 2, 3):
            calls.clear()
            _patch({"forward_list": flm}, calls, list_rc=expected)
            assert mn.daily_run(drafts=False, guardian_check=False) == expected
    finally:
        mn.radar_run, mn.guardian_run, flm.run_morning = old_radar, old_guard, old_morning
    print("  3. flags + rc passthrough (0/1/2/3) ✔")


def test_draft_list_consistency():
    """'draf elaga chesthavo alaga' — rendu okate hooks module nunchi."""
    titles = [
        "SSC CHSL 2026 Notification – Apply Online",
        "IBPS Clerk Recruitment 2026 – Complete Details",
        "Infosys Off Campus Drive 2026 – System Engineer",
    ]
    for title in titles:
        subj = hk.subject(title)
        assert subj, title
        list_line = hk.headline(title, telugu=True)
        draft_lead = hk.article_lead(title)
        assert subj in list_line, (title, list_line)
        assert f"<strong>{subj}</strong>" in draft_lead, (title, draft_lead)
    # nijamaina renderlo kuda same subject (drift ledu)
    rows = [{"id": 1, "title": "SSC CHSL 2026 Notification – Apply Online",
             "link": "https://studentup.in/ssc-chsl-2026/", "date": "2026-10-02",
             "category_slugs": ["central-jobs"], "last_date": "2026-10-20",
             "vacancies": "2000+", "salary": ""}]
    text = od.render_whatsapp("https://studentup.in", rows, today=TODAY)
    assert f"*{hk.subject(rows[0]['title'])} ఉద్యోగాలు*" in text, text
    draft = hk.hook_html(rows[0]["title"], vacancies=rows[0]["vacancies"])
    assert "<strong>SSC CHSL 2026</strong>" in draft
    # list Telugu · draft English (site public surfaces English-only, v73 gate)
    assert "ఉద్యోగాలు" in text and "ఉద్యోగాలు" not in draft
    assert "recruitment" in draft
    print("  4. draft ↔ list consistency (okate hooks module · Telugu/EN) ✔")


def test_cron_and_docs():
    cron = (ROOT / "crontab.example").read_text(encoding="utf-8")
    daily_lines = [l for l in cron.splitlines()
                   if "--daily" in l and "--daily-quiz" not in l and not l.strip().startswith("#")]
    assert daily_lines, "crontab lo --daily morning line ledu"
    assert any(l.strip().startswith("30 6") for l in daily_lines), daily_lines
    for name in ("README.md", "MANUAL_ADVANCED_CHECKLIST.md", "MILESWEB_GO_LIVE.md"):
        doc = (ROOT / name).read_text(encoding="utf-8")
        assert "--daily" in doc, f"{name} lo --daily ledu"
    print("  5. cron (okka line 6:30 AM) + docs ✔")


def main() -> None:
    print("=" * 70)
    print("  v190 — --daily: OKE COMMAND (drafts → health → list → send)")
    print("=" * 70)
    test_daily_order()
    test_non_fatal_steps()
    test_flags_and_rc()
    test_draft_list_consistency()
    test_cron_and_docs()
    print("-" * 70)
    print("ALL v190 DAILY ROUTINE TESTS PASSED ✔")


if __name__ == "__main__":
    main()
