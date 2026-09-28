# -*- coding: utf-8 -*-
"""v148 — daily quiz draft bot command + up-next recirculation card."""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from autoblog import daily_quiz  # noqa: E402

THEME = ROOT / "wordpress-theme" / "studentup"


class _FakeWP:
    """Minimal stand-in: records what the bot would send to WordPress."""

    def __init__(self, existing=None):
        self.existing = existing or []
        self.created = []

    def search_posts(self, term, per_page=10):
        return self.existing

    def get_or_create_term(self, name, term_type):
        return 7

    def create_post(self, **kwargs):
        self.created.append(kwargs)
        return {"id": 4242, "link": "https://example.com/?p=4242"}


def test_daily_quiz_is_always_a_draft():
    wp = _FakeWP()
    r = daily_quiz.run(wp=wp, day=date(2026, 9, 28))
    assert r["action"] == "created", r
    assert len(wp.created) == 1
    assert wp.created[0]["status"] == "draft", "bot eppudu publish cheyyakoodadu"
    assert wp.created[0]["slug"] == "daily-quiz-2026-09-28"
    assert wp.created[0]["content_html"].strip(), "quiz body khaali"
    print("      daily quiz lands as a DRAFT, never published ✔")


def test_daily_quiz_is_idempotent():
    wp = _FakeWP(existing=[{"id": 11, "slug": "daily-quiz-2026-09-28"}])
    r = daily_quiz.run(wp=wp, day=date(2026, 9, 28))
    assert r["action"] == "skipped" and not wp.created, "duplicate draft create ayyindi"
    print("      re-running the same day does not duplicate the draft ✔")


def test_quiz_changes_every_day():
    a = daily_quiz.build(date(2026, 9, 28))
    b = daily_quiz.build(date(2026, 9, 29))
    c = daily_quiz.build(date(2026, 9, 30))
    assert a["slug"] != b["slug"] != c["slug"]
    assert a["content_html"] != b["content_html"] != c["content_html"], "roju same paper vastundi"
    assert a["uid"] != b["uid"]
    print("      every day gets a different paper ✔")


def test_dry_run_touches_nothing():
    r = daily_quiz.run(wp=_FakeWP(), day=date(2026, 9, 28), dry=True)
    assert r["action"] == "dry-run" and r["post_id"] is None
    print("      dry run plans only, no WordPress writes ✔")


def test_cli_flag_wired():
    src = (ROOT / "autoblog" / "main.py").read_text(encoding="utf-8")
    assert "--daily-quiz" in src and "daily_quiz as _dq" in src
    print("      run.py --daily-quiz wired ✔")


def test_up_next_card_is_honest():
    src = (THEME / "inc" / "engage.php").read_text(encoding="utf-8")
    assert "studentup_up_next" in src
    assert "is_single()" in src, "up-next card only on posts"
    assert "su-upnext-x" in src, "dismiss button ledu"
    assert "sessionStorage" in src, "dismiss remembered in the reader's browser"
    assert "location.href" not in src and "window.open" not in src, "auto-redirect/pop-up vaddu"
    single = (THEME / "single.php").read_text(encoding="utf-8")
    assert "studentup_up_next();" in single
    opts = (THEME / "inc" / "options.php").read_text(encoding="utf-8")
    assert "'up_next'" in opts, "admin toggle ledu"
    print("      up-next card: dismissible, single posts only, no pop-up tricks ✔")


TESTS = [
    ("draft only", test_daily_quiz_is_always_a_draft),
    ("idempotent", test_daily_quiz_is_idempotent),
    ("daily rotation", test_quiz_changes_every_day),
    ("dry run", test_dry_run_touches_nothing),
    ("cli", test_cli_flag_wired),
    ("up next", test_up_next_card_is_honest),
]


def main() -> int:
    bad = 0
    for name, fn in TESTS:
        try:
            fn()
            print(f"  {name} ✔")
        except Exception as exc:  # noqa: BLE001
            bad += 1
            print(f"  {name} ✘ {type(exc).__name__}: {exc}")
    print("-" * 70)
    print("ALL v148 TESTS PASSED ✔" if not bad else f"{bad} TEST(S) FAILED ✘")
    return int(bool(bad))


if __name__ == "__main__":
    raise SystemExit(main())


def test_daily_quiz_notify_is_optional_and_safe():
    import inspect
    from autoblog import daily_quiz as dq
    src = inspect.getsource(dq.run_cli)
    assert "notify" in src and "send_telegram" in src
    assert "except Exception" in src, "alert fail ayina draft fail avvakoodadu"
    print("      telegram alert optional + non-fatal ✔")
