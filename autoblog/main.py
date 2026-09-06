"""Main orchestrator: schedule -> generate -> image -> publish.

Usage (see run.py):
  python run.py               # scheduled run (used by cron/systemd hourly)
  python run.py --force       # post immediately, ignore schedule
  python run.py --dry-run     # generate locally, do NOT touch WordPress
  python run.py --mock        # offline test article (no Gemini key needed)
  python run.py --status      # show today's plan & stats
  python run.py --check-wp    # verify WordPress credentials only
"""

import argparse
import json
import logging
import re
import sys
import unicodedata
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from . import config, gemini_client, image_gen, notifier, pipeline, sources, state, topic_engine, wordpress_client

log = logging.getLogger("autoblog")

KOLKATA_OFFSET = timezone(timedelta(hours=5, minutes=30))


def _now() -> datetime:
    try:
        from zoneinfo import ZoneInfo

        return datetime.now(ZoneInfo(config.TIMEZONE))
    except Exception:
        return datetime.now(KOLKATA_OFFSET)


def _setup_logging() -> None:
    config.LOG_DIR.mkdir(parents=True, exist_ok=True)
    fmt = logging.Formatter("%(asctime)s %(levelname)-7s %(name)s: %(message)s")
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(fmt)
    root.addHandler(console)
    from logging.handlers import TimedRotatingFileHandler

    filehandler = TimedRotatingFileHandler(
        config.LOG_DIR / "autoblog.log", when="midnight", backupCount=7, encoding="utf-8"
    )
    filehandler.setFormatter(fmt)
    root.addHandler(filehandler)


def _safe_slug(slug: str, fallback_title: str) -> str:
    slug = (slug or "").strip().lower()
    slug = re.sub(r"[^a-z0-9-]+", "-", slug).strip("-")[:60]
    if not slug:
        # transliteration fallback: strip non-ascii from title (English words in Telugu titles)
        ascii_part = unicodedata.normalize("NFKD", fallback_title).encode("ascii", "ignore").decode()
        slug = re.sub(r"[^a-z0-9]+", "-", ascii_part.lower()).strip("-")[:60] or "studentup-post"
    return slug


def generate_one(category: str, mock: bool, mock_index: int = 0) -> dict:
    """Generate an article with duplicate-avoidance retries."""
    recent = state.recent_titles(config.STATE_PATH, limit=50)
    avoid_extra = None
    for attempt in range(1, config.GEMINI_MAX_RETRIES + 1):
        if mock:
            article = topic_engine.mock_article(category, mock_index + attempt)
        else:
            article = gemini_client.generate_article(category, recent, year=_now().year,
                                                     avoid_extra=avoid_extra)
        title = article["title"].strip()
        if not state.title_exists(config.STATE_PATH, title):
            article["title"] = title
            article["slug"] = _safe_slug(article.get("slug", ""), title)
            return article
        log.warning("Duplicate title generated (%s) — retrying", title)
        avoid_extra = f"Already tried (do NOT repeat): {title}"
    raise RuntimeError("Could not generate a non-duplicate title after retries")


def run(dry_run: bool, force: bool, mock: bool, category: str = "",
        source_url: str = "", process_queue: int = 0, update_id: int = 0) -> int:
    now = _now()
    today = now.date()
    now_hour = now.hour
    state.init(config.STATE_PATH)
    try:  # scheduler heartbeat (watchdog kosam)
        state.meta_set(config.STATE_PATH, "heartbeat", now.isoformat())
    except Exception:
        pass

    # --- bulk queue mode: --process-queue N (N URLs ippude process) ---------
    if process_queue:
        done = 0
        while done < process_queue:
            url = sources.pending_from_queue()
            if not url:
                log.info("Queue empty — %d URLs process ayyayi", done)
                break
            try:
                result = pipeline.create_from_source(url, mock=mock, category=category)
                log.info("QUEUE POST ✔ %s -> %s", url[:60], result["link"])
                done += 1
            except Exception as exc:
                log.error("Queue URL failed (%s): %s — skip", url[:60], exc)
            finally:
                sources.mark_done_and_clean(url)
        return 0

    # --- update mode: existing post ni kotha info tho improve --------------
    if update_id:
        result = pipeline.update_post(update_id,
                                      new_source_urls=[source_url] if source_url else None,
                                      mock=mock)
        log.info("POST UPDATED ✔ %s", result.get("link"))
        return 0

    # --- explicit source URL mode (--url / Telegram) -----------------------
    if source_url:
        if not mock and not config.GEMINI_API_KEY:
            log.error("GEMINI_API_KEY set kavali! .env file lo key pettandi.")
            return 2
        result = pipeline.create_from_source(source_url, mock=mock, category=category)
        log.info("SOURCE POST READY ✔ %s (status=%s)", result["link"], result["status"])
        return 0

    # --- schedule check ----------------------------------------------------
    if not (force or dry_run):
        count = state.today_count(config.STATE_PATH, today)
        if count >= config.DAILY_MAX:
            log.info("Daily limit reached (%d/%d) — stopping.", count, config.DAILY_MAX)
            return 0
        plan = state.today_plan(
            config.STATE_PATH, today,
            config.ACTIVE_HOUR_START, config.ACTIVE_HOUR_END,
            config.DAILY_MIN, config.DAILY_MAX,
        )
        if now_hour not in plan:
            log.info("Hour %02d:00 not in today's plan %s — nothing to do.", now_hour, plan)
            return 0
        log.info("Hour %02d:00 in plan %s — generating post (%d done today).",
                 now_hour, plan, count)

    # --- source queue check (sources_queue.txt lo URLs unnaye priority) ----
    queued = sources.pending_from_queue()
    if queued:
        log.info("Sources queue lo URL dorikindi — original rewrite mode: %s", queued)
        if not mock and not config.GEMINI_API_KEY:
            log.error("GEMINI_API_KEY ledu — ee URL skip chesi mark chestanu")
            sources.mark_done_and_clean(queued)
        else:
            try:
                result = pipeline.create_from_source(queued, mock=mock,
                                                     category=category)
                log.info("SOURCE POST READY ✔ %s (status=%s)", result["link"], result["status"])
                return 0
            except Exception as exc:
                log.error("Queue URL failed (%s) — mark chesi normal post ki veltanu: %s",
                          queued, exc)
            finally:
                sources.mark_done_and_clean(queued)

    # --- generate (auto topic) ---------------------------------------------
    cat = category or topic_engine.pick_category(config.STATE_PATH)
    log.info("Category selected: %s%s", cat, " (forced)" if category else "")

    if not mock and not config.GEMINI_API_KEY:
        log.error("GEMINI_API_KEY set kavali! .env file lo key pettandi.")
        return 2

    mock_index = state.today_count(config.STATE_PATH, today)
    article = generate_one(cat, mock, mock_index)
    article.setdefault("focus_keyword", "")
    article.setdefault("external_links", [])
    article.setdefault("seo_title", "")
    log.info("Article ready: %s (slug=%s, model=%s)",
             article["title"], article["slug"], article.get("model"))

    # --- featured image (dry-run kosam; real publish lo pipeline chestundi) --
    image_path: Path = Path(
        config.OUTPUT_DIR / "images" / f"{article['slug']}.jpg"
    )
    if dry_run and config.IMAGE_ENABLED:
        if not image_gen.generate_featured_image(
            article["banner_text"], article["category"], image_path
        ):
            image_path = None
    else:
        image_path = None

    # --- publish / dry-run -------------------------------------------------
    if dry_run:
        out_dir = config.OUTPUT_DIR / today.isoformat() / article["slug"]
        out_dir.mkdir(parents=True, exist_ok=True)
        html = (
            f"<!doctype html><html><head><meta charset='utf-8'>"
            f"<title>{article['title']}</title></head><body>"
            f"<h1>{article['title']}</h1>"
            f"{article['content_html']}</body></html>"
        )
        (out_dir / "article.html").write_text(html, encoding="utf-8")
        (out_dir / "meta.json").write_text(
            json.dumps(
                {
                    "title": article["title"],
                    "slug": article["slug"],
                    "category": article["category"],
                    "tags": article["tags"],
                    "meta_description": article["meta_description"],
                    "focus_keyword": article.get("focus_keyword"),
                    "seo_title": article.get("seo_title"),
                    "external_links": article.get("external_links"),
                    "image": image_path.name if image_path else None,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        if image_path and image_path.exists():
            import shutil

            shutil.copy(image_path, out_dir / "featured.jpg")
        log.info("DRY-RUN saved to %s (state lo record cheyaledu — dedupe "
                 "pollution avoid)", out_dir)
        return 0

    wp = wordpress_client.WordPressClient()
    wp.check_connection()

    result = pipeline.publish_article(article, day=today)
    if result["status"] == "draft":
        log.info("DRAFT saved (review kosam) id=%s", result["id"])

    # --- end-of-day digest (roji chivari slot lo summary message) ---
    if not (force or dry_run) and now_hour >= config.ACTIVE_HOUR_END:
        digest_key = f"digest:{today.isoformat()}"
        if not state.meta_get(config.STATE_PATH, digest_key):
            count = state.today_count(config.STATE_PATH, today)
            summary = state.status_summary(config.STATE_PATH, limit=5)
            try:
                notifier.daily_digest(count, summary.get("last", []))
                state.meta_set(config.STATE_PATH, digest_key, "1")
            except Exception:
                log.exception("Daily digest failed")
    return 0


def show_status() -> int:
    state.init(config.STATE_PATH)
    today = _now().date()
    plan = state.today_plan(
        config.STATE_PATH, today,
        config.ACTIVE_HOUR_START, config.ACTIVE_HOUR_END,
        config.DAILY_MIN, config.DAILY_MAX,
    )
    summary = state.status_summary(config.STATE_PATH)
    print(f"Site         : {config.WP_SITE}")
    print(f"Today        : {today}  (now {_now().strftime('%H:%M')})")
    print(f"Today plan   : {plan}  -> posts done: {state.today_count(config.STATE_PATH, today)}")
    print(f"Total posts  : {summary['total']}")
    avgs = state.avg_scores(config.STATE_PATH)
    if avgs["n"]:
        print(f"Quality      : avg QA {avgs['qa']}/100 · avg originality {avgs['orig']}%"
              f"  ({avgs['n']} posts measured)")
    print("Last posts:")
    for p in summary["last"]:
        print(f"  [{p['created_at']}] ({p['status']}) {p['title']}  ->  {p['link']}")
    return 0


def check_wp() -> int:
    state.init(config.STATE_PATH)
    try:
        wp = wordpress_client.WordPressClient()
        me = wp.check_connection()
        print(f"OK! Connected as {me.get('name')} — roles: {me.get('roles')}")
        cats = wp.ensure_categories()
        print(f"Categories ready: {len(cats)} ids")
        return 0
    except wordpress_client.WordPressError as exc:
        print(f"FAILED: {exc}")
        return 1


def notify_test() -> int:
    """Send a test notification to all configured channels."""
    ok_any = False
    if config.TELEGRAM_BOT_TOKEN:
        ok = notifier.send_telegram(
            "🧪 <b>Test message</b> — studentup.in auto-blogger Telegram connect ayyindi ✔"
        )
        ok_any = ok_any or ok
    if config.WHATSAPP_CALLMEBOT_URL:
        ok = notifier.send_whatsapp("🧪 Test — studentup auto-blogger WhatsApp connect ayyindi ✔")
        ok_any = ok_any or ok
    if not ok_any:
        print("Emi channel configure cheyaledu (.env lo TELEGRAM_BOT_TOKEN / WHATSAPP_CALLMEBOT_URL)")
        return 1
    print("Test notification pampinchi!" if ok_any else "Notification fail ayyindi — log chudandi")
    return 0 if ok_any else 4


def main() -> int:
    parser = argparse.ArgumentParser(description="studentup.in auto-blogger")
    parser.add_argument("--dry-run", action="store_true", help="generate locally, no publishing")
    parser.add_argument("--force", action="store_true", help="ignore schedule & post now")
    parser.add_argument("--mock", action="store_true", help="offline mock article (no Gemini)")
    parser.add_argument("--category", default="", help="force a category")
    parser.add_argument("--url", default="", help="source URL -> 100%% original rewrite post")
    parser.add_argument("--process-queue", type=int, default=0, metavar="N",
                        help="sources_queue.txt lo first N URLs ippude process chey")
    parser.add_argument("--update", type=int, default=0, metavar="POST_ID",
                        help="existing post ni kotha info tho improve chesi update chey")
    parser.add_argument("--add-source", default="",
                        help="--update tho extra source URL (kotha info)")
    parser.add_argument("--status", action="store_true", help="show stats & today's plan")
    parser.add_argument("--check-wp", action="store_true", help="verify WP credentials")
    parser.add_argument("--notify-test", action="store_true", help="send test notification")
    args = parser.parse_args()

    _setup_logging()

    if args.status:
        return show_status()
    if args.check_wp:
        return check_wp()
    if args.notify_test:
        return notify_test()
    try:
        src = args.add_source or args.url
        return run(dry_run=args.dry_run, force=args.force, mock=args.mock,
                   category=args.category, source_url=src,
                   process_queue=args.process_queue, update_id=args.update)
    except wordpress_client.WordPressAuthError as exc:
        log.error("%s", exc)
        return 3
    except (wordpress_client.WordPressError, gemini_client.GeminiError) as exc:
        log.error("Publishing failed: %s", exc)
        return 4
    except Exception:
        log.exception("Unexpected error")
        return 5
