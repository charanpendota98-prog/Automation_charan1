# -*- coding: utf-8 -*-
"""v148 — daily quiz draft.

One command, run once a day (cron / Task Scheduler), that prepares **tomorrow's
reader habit**: a fresh quiz post left in WordPress as a **draft** so the owner
reads it, fixes anything, and presses Publish.

Deliberate rules:

* It never publishes. `status` is hard-coded to ``draft`` — `DEFAULT_POST_STATUS`
  cannot accidentally turn this into a live post.
* It is idempotent: if today's quiz slug already exists (draft or published) the
  command reports ``skipped`` instead of creating a duplicate.
* It works offline: with no Gemini key it falls back to the repo question bank,
  so the draft is always there even when the API is down.
* Questions rotate by weekday topic + a date seed, so two days never get the
  same paper.
"""
from __future__ import annotations

import logging
from datetime import date
from typing import Dict, Optional

from . import config, quiz_engine

log = logging.getLogger(__name__)

DRAFT_STATUS = "draft"


def slug_for(day: Optional[date] = None) -> str:
    day = day or date.today()
    return f"daily-quiz-{day.isoformat()}"


def title_for(day: Optional[date] = None, topic_te: str = "") -> str:
    day = day or date.today()
    nice = day.strftime("%d %b %Y")
    if topic_te:
        return f"డైలీ క్విజ్ {nice} — {topic_te}"
    return f"డైలీ క్విజ్ {nice}"


def build(day: Optional[date] = None) -> Dict:
    """Build today's quiz payload without touching the network."""
    day = day or date.today()
    topic_en, topic_te, level, n = quiz_engine.pick_daily_topic(day)
    quiz = quiz_engine.mock_quiz(topic_en, topic_te, level, n, day=day)
    quiz = quiz_engine.normalize_quiz(quiz, n)
    content, uid = quiz_engine.build_quiz_html(quiz, topic_en, topic_te, level, n, day)
    problems = quiz_engine.validate_quiz(quiz, n)
    return {
        "day": day.isoformat(),
        "topic_en": topic_en,
        "topic_te": topic_te,
        "level": level,
        "questions": n,
        "uid": uid,
        "slug": slug_for(day),
        "title": title_for(day, topic_te),
        "content_html": content,
        "excerpt": f"{topic_te} — {n} ప్రశ్నలు. సమాధానాలు చివర్లో ఇవ్వబడ్డాయి.",
        "problems": problems,
    }


def run(wp=None, day: Optional[date] = None, dry: bool = False) -> Dict:
    """Create today's quiz as a WordPress draft (or report what would happen)."""
    day = day or date.today()
    plan = build(day)
    result = {
        "version": "v148",
        "day": plan["day"],
        "slug": plan["slug"],
        "title": plan["title"],
        "topic": plan["topic_te"],
        "questions": plan["questions"],
        "status": DRAFT_STATUS,
        "problems": plan["problems"],
        "action": "dry-run",
        "post_id": None,
    }

    if plan["problems"]:
        result["action"] = "blocked"
        log.warning("Daily quiz draft blocked: %s", "; ".join(plan["problems"]))
        return result

    if dry or wp is None:
        return result

    existing = None
    try:
        existing = wp.search_posts(plan["slug"], per_page=5)
    except Exception:  # noqa: BLE001 — a search hiccup must not duplicate posts
        log.debug("slug search unavailable", exc_info=True)
        existing = None
    if existing:
        for post in existing:
            if str(post.get("slug", "")) == plan["slug"]:
                result["action"] = "skipped"
                result["post_id"] = post.get("id")
                return result

    category_id = None
    try:
        category_id = wp.get_or_create_term(getattr(config, "QUIZ_CATEGORY", "Daily Quiz"), "categories")
    except Exception:  # noqa: BLE001 — a missing category must not stop the draft
        log.debug("quiz category unavailable", exc_info=True)

    created = wp.create_post(
        title=plan["title"],
        content_html=plan["content_html"],
        slug=plan["slug"],
        category_id=category_id,
        tag_ids=[],
        excerpt=plan["excerpt"],
        media_id=None,
        status=DRAFT_STATUS,
    )
    result["action"] = "created"
    result["post_id"] = created.get("id") if isinstance(created, dict) else None
    result["link"] = created.get("link") if isinstance(created, dict) else None
    return result


def run_cli(dry: bool = False, notify: bool = False) -> int:
    """Print a short, honest report of the daily quiz draft."""
    wp = None
    if not dry:
        try:
            from . import wordpress_client
            wp = wordpress_client.WordPressClient()
        except Exception as exc:  # noqa: BLE001 — offline run still prints the plan
            log.warning("WordPress not reachable (%s) — showing the plan only", exc)
            wp = None

    report = run(wp=wp, dry=dry)
    print("=" * 74)
    print(f"  DAILY QUIZ DRAFT · {report['day']} · {report['topic']}")
    print("=" * 74)
    print(f"  title     : {report['title']}")
    print(f"  slug      : {report['slug']}")
    print(f"  questions : {report['questions']}")
    print(f"  status    : {report['status']} (this command never publishes)")
    print(f"  action    : {report['action']}")
    if report.get("post_id"):
        print(f"  post id   : {report['post_id']}")
    for problem in report["problems"]:
        print(f"  ⚠ {problem}")
    if report["action"] == "created":
        print("  ✅ Draft ready — open WordPress, read it once, then press Publish.")
        if notify:
            try:
                from . import notifier
                sent = notifier.send_telegram(
                    "📝 <b>Daily quiz draft ready</b>\n"
                    f"{report['title']}\n"
                    f"{report['questions']} questions · status: draft\n"
                    "WordPress lo chadivi Publish nokkandi."
                )
                print("  ✅ Telegram alert sent." if sent else "  ⚠ Telegram alert pampaledu (token/chat id check cheyandi).")
            except Exception as exc:  # noqa: BLE001 — alerting must never fail the draft
                print(f"  ⚠ Telegram alert skipped: {exc}")
    elif report["action"] == "skipped":
        print("  ✅ Today's quiz draft already exists — nothing duplicated.")
    return 0 if report["action"] in {"created", "skipped", "dry-run"} else 1
