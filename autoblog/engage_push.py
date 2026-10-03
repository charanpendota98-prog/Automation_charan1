# -*- coding: utf-8 -*-
"""v197 DAILY ENGAGE PUSH — quiz + poll ni site ki roju pampadam.

Owner ask: "quiz polls daily advanced ga bot tho ... post chesthu vundali".

Idi emi chestundi (rendu separate, rendu idempotent):

  1. **Daily quiz post** — `daily_quiz.build()` (v148 module) tho roju oka quiz
     post: draft ga (owner review flow intact) leda `--publish` tho live.
  2. **Daily poll** — theme options ki `poll_question` / `poll_opts` / `poll_id`
     / `poll_note` push (route: `/wp-json/studentup/v1/options`). Theme aa
     question ni home + /daily-quiz/ page lo render chestundi; votes theme
     side lo count avutayi (no personal data).

Poll bank offline lo kuda pani chestundi — WP connection lekapote **skip**
(never crash the daily run), and the theme's own daily rotation continues.

Run:
    python run.py --daily-engage            # quiz draft + poll push
    python run.py --daily-engage --publish  # quiz ni direct publish (gate safe)
"""
from __future__ import annotations

import logging
from datetime import date
from typing import Dict, Optional

from . import config
from .wordpress_client import WordPressAuthError, WordPressClient, WordPressError

log = logging.getLogger(__name__)

# Weekly poll rotation — reader opinion drives content + product decisions.
POLL_BANK = [
    ("Which update do you want first on WhatsApp?",
     ["New job notifications", "Exam date changes", "Results & hall tickets", "Scholarship deadlines"],
     "This decides what the morning list leads with."),
    ("Which exam are you preparing for right now?",
     ["TSPSC / Group-2", "APPSC / Group-1", "SSC CGL / CHSL", "Banking (IBPS / RRB)"],
     "Practice questions follow the most-voted exam."),
    ("What stops you from applying to a government job?",
     ["Fee / documents cost", "Not sure I am eligible", "Form filling is confusing", "I miss the last date"],
     "Guides are written around the top answer."),
    ("Where do you read StudentUp mostly?",
     ["Phone", "Laptop", "College computer", "Internet center"],
     "Design priority follows this."),
    ("Which free tool should be built next?",
     ["Resume builder", "Exam date planner", "Cut-off predictor", "Study timetable"],
     "The top option gets built first."),
    ("Do you want a Telugu version of every article?",
     ["Yes — Telugu first", "English is fine", "Both side by side", "Only for exams"],
     "Honest answer helps us plan translation work."),
    ("How many notifications per day is OK for you?",
     ["Only urgent (max 2)", "3-5 updates", "One morning list", "No alerts, I check myself"],
     "We cap alerts based on this."),
]


def poll_for(day: Optional[date] = None) -> Dict:
    """Today's poll payload (deterministic rotation — same as theme bank)."""
    day = day or date.today()
    idx = (day.timetuple().tm_yday + day.year) % len(POLL_BANK)
    q, opts, note = POLL_BANK[idx]
    return {
        "poll_question": q,
        "poll_opts": "\n".join(opts),
        "poll_note": note,
        "poll_id": "d" + day.strftime("%Y%m%d"),
        "polls": 1,
    }


def push_poll(day: Optional[date] = None,
              client: Optional[WordPressClient] = None) -> Dict:
    """Push today's poll question to the theme (idempotent — same id = same poll)."""
    payload = poll_for(day)
    wp = client or WordPressClient()
    try:
        res = wp.set_theme_options(payload)
        print(f"  ✅ poll pushed: {payload['poll_question'][:70]} "
              f"(id {payload['poll_id']})")
        return {"ok": True, "id": payload["poll_id"], "saved": res.get("saved", [])}
    except (WordPressAuthError, WordPressError) as exc:
        print(f"  ⚠️  poll push skip — {exc}")
        return {"ok": False, "reason": str(exc)[:200]}
    except Exception as exc:  # noqa: BLE001 — daily run never dies for the poll
        log.info("poll push fail: %s", exc)
        print(f"  ⚠️  poll push skip — {type(exc).__name__} (theme rotation continues)")
        return {"ok": False, "reason": type(exc).__name__}


def push_quiz(day: Optional[date] = None, publish: bool = False,
              client: Optional[WordPressClient] = None) -> Dict:
    """Create today's quiz post (v148 daily_quiz module — the review-safe path).

    Default = **draft** (owner reviews once). `publish=True` tho adi live avutundi
    — kaani appudu kuda `daily_quiz` content rules (validate_quiz) paatinchali.
    """
    from . import daily_quiz

    day = day or date.today()
    wp = client or WordPressClient()
    report = daily_quiz.run(wp=wp, dry=False, day=day)
    action = report.get("action")
    post_id = report.get("post_id")
    status = report.get("status", "draft")

    if publish and post_id and action == "created":
        try:
            wp.set_post_status(int(post_id), "publish")
            status = "publish"
            print(f"  ✅ quiz published (gate-safe content) #{post_id}")
        except Exception as exc:  # noqa: BLE001
            log.exception("quiz publish fail: %s", exc)
            print(f"  ⚠️  quiz draft ga ne undi — publish fail: {exc}")

    print(f"  ✅ quiz {status}: {report.get('title', '')[:60]} "
          f"(#{post_id or '—'}) {report.get('questions', '')} questions")
    return {"ok": action in {"created", "skipped", "dry-run"}, "action": action,
            "id": post_id, "slug": report.get("slug"), "status": status,
            "questions": report.get("questions")}


def run(publish_quiz: bool = False, client: Optional[WordPressClient] = None) -> Dict:
    """Quiz + poll for today — one command."""
    wp = client or WordPressClient()
    print("  ▸ daily engage: quiz + poll")
    try:
        quiz = push_quiz(publish=publish_quiz, client=wp)
    except Exception as exc:  # noqa: BLE001 — WP unreachable: crash vaddhu
        log.info("quiz push skip (WP unreachable?): %s", exc)
        print(f"  ⚠️  quiz push skip — WordPress not reachable ({type(exc).__name__})")
        quiz = {"ok": False, "reason": type(exc).__name__}
    try:
        poll = push_poll(client=wp)
    except Exception as exc:  # noqa: BLE001
        log.info("poll push skip: %s", exc)
        print(f"  ⚠️  poll push skip — {type(exc).__name__}")
        poll = {"ok": False, "reason": type(exc).__name__}
    ok_any = bool(quiz.get("ok")) or bool(poll.get("ok"))
    print("  ▸ daily engage done: quiz=%s poll=%s" % (
        "ok" if quiz.get("ok") else quiz.get("reason", "skip"),
        "ok" if poll.get("ok") else poll.get("reason", "skip")))
    return {"quiz": quiz, "poll": poll, "ok": ok_any}
