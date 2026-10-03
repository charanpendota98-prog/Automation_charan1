# -*- coding: utf-8 -*-
"""v197 AUTO-PUBLISH LANE — morning drafts → evening live posts (gate tho mattrame).

Owner ask (Telugu): "daily advanced ga bot tho draft chesi post chesthu vundali".

Ee module aa pani **safe ga** chestundi:

  morning  : radar → drafts (v190 daily flow — already exists)
  evening  : THIS module — prathi draft ni gate pass chesthe mattrame publish

Ee gates anni pass avvali (okkatina fail aithe draft ga ne untundi):

  1. **Source proof** — `studentup_source_url` meta undali + real http(s) URL
     (official notification). Source lekunda publish avvadu — E-E-A-T rule.
  2. **Word count** — 700+ words (config: AUTO_PUBLISH_MIN_WORDS).
  3. **Rank Math readback** — live score >= AUTO_PUBLISH_MIN_SCORE (default 80).
     Score chadavalekapote **refuse** (guess tho publish cheyyamu).
  4. **Freshness** — draft intha kanna pathadi aithe skip (default: 1 day).
     Purana draft ni suddenly publish cheste feed/Discover ki tappu signal.
  5. **Hygiene** — TODO/FIXME/lorem/placeholder text unte skip.
  6. **Idempotent** — already publish aina post ni malli touch cheyyadu.

Prathi decision ki reason + evidence print avutundi (`--auto-publish-dry` tho
motta chudandi). Telegram lo summary (notifier వున్నప్పుడు).

Run:
    python run.py --auto-publish-dry      # emi publish cheyyadu — report mattrame
    python run.py --auto-publish          # gate-passed drafts ni publish
    AUTO_PUBLISH_DAILY=1 + python run.py --daily   # daily flow lo automatic
"""
from __future__ import annotations

import html as _html
import logging
import re
from datetime import datetime, timezone
from typing import Dict, List, Optional

from . import config
from .wordpress_client import WordPressClient, WordPressError

log = logging.getLogger(__name__)

BAD_TEXT = re.compile(r"\b(TODO|FIXME|XXX|lorem ipsum|placeholder text|dummy content)\b", re.I)
TAG_RE = re.compile(r"<[^>]+>")


def _strip(html: str) -> str:
    return _html.unescape(TAG_RE.sub(" ", html or ""))


def _words(html: str) -> int:
    return len([w for w in re.split(r"\s+", _strip(html)) if w.strip()])


def _min_score() -> int:
    try:
        return int(getattr(config, "AUTO_PUBLISH_MIN_SCORE", 80) or 80)
    except (TypeError, ValueError):
        return 80


def _min_words() -> int:
    try:
        return int(getattr(config, "AUTO_PUBLISH_MIN_WORDS", 700) or 700)
    except (TypeError, ValueError):
        return 700


def _max_age_days() -> int:
    try:
        return int(getattr(config, "AUTO_PUBLISH_MAX_AGE_DAYS", 1) or 1)
    except (TypeError, ValueError):
        return 1


def _parse_wp_date(value: str) -> Optional[datetime]:
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime((value or "")[:19], fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


def check_draft(wp: WordPressClient, post: Dict, *, today=None) -> Dict:
    """Run all gates on one draft. Returns {ok, reasons[], evidence{}}."""
    reasons: List[str] = []
    pid = post.get("id")
    title = _html.unescape(((post.get("title") or {}).get("raw")
                            or (post.get("title") or {}).get("rendered") or "")).strip()
    content = ((post.get("content") or {}).get("raw")
               or (post.get("content") or {}).get("rendered") or "")
    meta = post.get("meta") or {}

    counted = _words(content)
    if counted < _min_words():
        reasons.append(f"word count {counted} < {_min_words()}")

    source = str(meta.get("studentup_source_url") or "").strip()
    if not source.lower().startswith(("http://", "https://")):
        reasons.append("source URL meta ledu (official notification proof)")

    if BAD_TEXT.search(content):
        reasons.append("placeholder text (TODO/FIXME/lorem) content lo undi")

    created = _parse_wp_date(post.get("date_gmt") or post.get("date") or "")
    if created and today is not None:
        age = (today - created.date()).days
        if age > _max_age_days():
            reasons.append(f"draft {age} rojulu pathadi (max {_max_age_days()})")

    score = None
    try:
        state = wp.read_rankmath_state(int(pid))
        score = state.get("rank_math_ui_score")
    except Exception as exc:  # noqa: BLE001 — readback fail = refuse (never guess)
        reasons.append(f"Rank Math score chadavalekapoyindi ({type(exc).__name__})")
    if score is None and not reasons:
        reasons.append("Rank Math score ledu (SEO readback fail)")
    elif score is not None and int(score) < _min_score():
        reasons.append(f"Rank Math score {int(score)} < {_min_score()}")

    return {
        "id": pid,
        "title": title,
        "ok": not reasons,
        "reasons": reasons,
        "evidence": {"words": counted, "score": score, "source": source[:120],
                     "created": (created.isoformat() if created else "")},
    }


def run(dry: bool = True, limit: Optional[int] = None,
        client: Optional[WordPressClient] = None) -> Dict:
    """Check queued drafts and (unless dry) publish the ones that clear every gate."""
    wp = client or WordPressClient()
    cap = limit if limit else int(getattr(config, "AUTO_PUBLISH_MAX", 3) or 3)
    today = datetime.now(timezone.utc)

    try:
        drafts = wp.list_drafts(per_page=max(1, min(50, cap * 5)))
    except Exception as exc:  # noqa: BLE001 — network/SSL/auth: crash vaddhu
        # MilesWeb shared hosting: SSL hiccup leda maintenance lo WP unreachable
        # avvachu. Appudu cron lo traceback raakoodadu — okka line + report.
        log.info("draft list fail (skip): %s", exc)
        print(f"  ⚠️  WordPress not reachable — auto-publish skip ({type(exc).__name__})")
        print("     check: WP_URL / app password / hosting status")
        return {"checked": 0, "published": [], "skipped": [], "dry": bool(dry),
                "error": f"{type(exc).__name__}: {exc}"}

    report: Dict = {"checked": 0, "published": [], "skipped": [], "dry": bool(dry),
                    "today": today.date().isoformat()}
    for post in drafts:
        report["checked"] += 1
        verdict = check_draft(wp, post, today=today)
        if not verdict["ok"]:
            report["skipped"].append({"id": verdict["id"], "title": verdict["title"],
                                      "why": verdict["reasons"]})
            print(f"  ⏭️  skip #{verdict['id']} {verdict['title'][:60]} — "
                  f"{'; '.join(verdict['reasons'])}")
            continue
        if len(report["published"]) >= cap:
            report["skipped"].append({"id": verdict["id"], "title": verdict["title"],
                                      "why": [f"cap {cap} reach ayyindi"]})
            continue
        if dry:
            print(f"  🔎 would publish #{verdict['id']} {verdict['title'][:60]} "
                  f"(score {verdict['evidence']['score']}, {verdict['evidence']['words']} words)")
            report["published"].append({"id": verdict["id"], "title": verdict["title"],
                                        "dry": True})
            continue
        try:
            wp.set_post_status(int(verdict["id"]), "publish")
            after = wp.get_post(int(verdict["id"])) or {}
            status = (after.get("status") or "").lower()
            if status != "publish":
                report["skipped"].append({"id": verdict["id"], "title": verdict["title"],
                                          "why": [f"publish readback '{status or '?'}'"]})
                print(f"  ⚠️  #{verdict['id']} publish readback fail ({status})")
                continue
            report["published"].append({"id": verdict["id"], "title": verdict["title"],
                                        "link": after.get("link", ""),
                                        "score": verdict["evidence"]["score"]})
            print(f"  ✅ published #{verdict['id']} {verdict['title'][:60]} → {after.get('link', '')}")
        except Exception as exc:  # noqa: BLE001 — okka post fail ina lane continue
            report["skipped"].append({"id": verdict["id"], "title": verdict["title"],
                                      "why": [f"publish exception {type(exc).__name__}"]})
            log.exception("publish fail (id=%s): %s", verdict["id"], exc)

    print(f"  ── auto-publish lane: {report['checked']} drafts checked · "
          f"{len(report['published'])} {'would publish' if dry else 'published'} · "
          f"{len(report['skipped'])} skipped")
    return report


def notify(report: Dict) -> None:
    """Telegram summary — silent ga fail avvali (lane ki adi non-critical)."""
    try:
        from . import notifier

        head = "AUTO-PUBLISH (dry run)" if report.get("dry") else "AUTO-PUBLISH"
        lines = [f"🚀 {head}: {len(report.get('published', []))} live · "
                 f"{len(report.get('skipped', []))} skipped (of {report.get('checked', 0)})"]
        for item in report.get("published", [])[:5]:
            lines.append(f"• #{item.get('id')} {item.get('title', '')[:70]}")
        for item in report.get("skipped", [])[:5]:
            lines.append(f"⏭️ #{item.get('id')} {'; '.join(item.get('why', []))[:90]}")
        notifier.send_text("\n".join(lines))
    except Exception as exc:  # noqa: BLE001
        log.info("auto-publish notify skip: %s", exc)
