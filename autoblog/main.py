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


def generate_one(category: str, mock: bool, mock_index: int = 0,
                 trend_topic: str = "") -> dict:
    """Generate an article with duplicate-avoidance retries."""
    recent = state.recent_titles(config.STATE_PATH, limit=50)
    avoid_extra = None
    for attempt in range(1, config.GEMINI_MAX_RETRIES + 1):
        if mock:
            article = topic_engine.mock_article(category, mock_index + attempt)
        else:
            article = gemini_client.generate_article(category, recent, year=_now().year,
                                                     avoid_extra=avoid_extra,
                                                     trend_topic=trend_topic)
        title = article["title"].strip()
        if not state.title_exists(config.STATE_PATH, title):
            article["title"] = title
            from . import seo as _seo
            article["slug"] = _seo.optimize_slug(
                _safe_slug(article.get("slug", ""), title),
                focus_keyword=article.get("focus_keyword", ""))
            return article
        log.warning("Duplicate title generated (%s) — retrying", title)
        avoid_extra = f"Already tried (do NOT repeat): {title}"
    raise RuntimeError("Could not generate a non-duplicate title after retries")


def run(dry_run: bool, force: bool, mock: bool, category: str = "",
        source_url: str = "", process_queue: int = 0, update_id: int = 0,
        listicle: str = "", auto_refresh_n: int = 0) -> int:
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

    # --- manual listicle mode (--listicle "Top 10 ...") ---------------------
    if listicle:
        result = pipeline.create_listicle(topic=listicle, mock=mock)
        log.info("LISTICLE READY ✔ %s (status=%s)", result["link"], result["status"])
        return 0

    # --- manual auto-refresh (--auto-refresh N) ------------------------------
    if auto_refresh_n:
        done = pipeline.auto_refresh(limit=auto_refresh_n)
        log.info("AUTO-REFRESH complete — %d posts updated", len(done))
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
        # daily auto-refresh (maintenance — plan lo leda parvaledu)
        if (config.AUTO_REFRESH_PER_DAY > 0
                and now_hour == config.AUTO_REFRESH_HOUR
                and not state.meta_get(config.STATE_PATH, f"autorefresh:{today.isoformat()}")):
            try:
                pipeline.auto_refresh(limit=config.AUTO_REFRESH_PER_DAY)
                state.meta_set(config.STATE_PATH, f"autorefresh:{today.isoformat()}", "1")
            except Exception:
                log.exception("Daily auto-refresh failed")
        if now_hour not in plan:
            log.info("Hour %02d:00 not in today's plan %s — nothing to do.", now_hour, plan)
            return 0
        log.info("Hour %02d:00 in plan %s — generating post (%d done today).",
                 now_hour, plan, count)

        # trending listicle quota: roju LISTICLES_PER_DAY stories
        lkey = f"listiclecount:{today.isoformat()}"
        lcount = int(state.meta_get(config.STATE_PATH, lkey) or 0)
        if lcount < config.LISTICLES_PER_DAY:
            log.info("Listicle slot (%d/%d today) — trending story mode",
                     lcount + 1, config.LISTICLES_PER_DAY)
            if not mock and not config.GEMINI_API_KEY:
                log.error("GEMINI_API_KEY ledu — listicle skip")
            else:
                try:
                    result = pipeline.create_listicle(mock=mock)
                    state.meta_set(config.STATE_PATH, lkey, str(lcount + 1))
                    log.info("LISTICLE READY ✔ %s (status=%s)",
                             result["link"], result["status"])
                    return 0
                except Exception:
                    log.exception("Listicle failed — normal post ki veltanu")

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

    # --- Google Trends trending topic (roju 1 post trend meeda) ---
    trend_topic = ""
    if not mock and config.USE_TRENDS and not state.meta_get(config.STATE_PATH, f"trend:{today}"):
        try:
            edu = topic_engine.filter_edu_trends(topic_engine.fetch_trending_topics())
            if edu:
                trend_topic = edu[0]["title"]
                state.meta_set(config.STATE_PATH, f"trend:{today}", trend_topic)
                log.info("🔥 Google Trends topic: %s", trend_topic)
        except Exception:
            log.exception("Trends fetch error (continue normal topic)")

    mock_index = state.today_count(config.STATE_PATH, today)
    article = generate_one(cat, mock, mock_index, trend_topic=trend_topic)
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


def gsc_opportunities(csv_path: str) -> int:
    """Search Console 'Top queries' export -> striking-distance opportunities.

    Top revenue trick (real data driven): rank 5-20 lo unna queries =
    page-1/2 lo untayi kani clicks takkuva. Veeti posts ni improve cheyali
    (update + optimize) -> fastest traffic gain. Idi guess-work kadu —
    me own Google data.
    """
    import csv as _csv

    path = Path(csv_path)
    if not path.exists():
        print(f"❌ file ledu: {csv_path}")
        print("   Search Console > Performance > Queries > Export CSV download cheyandi")
        return 1

    rows = list(_csv.reader(path.open(encoding="utf-8-sig", errors="replace")))
    # GSC export: first row header ("Top queries"/"Queries"), second row maybe dates group
    if not rows or "quer" not in (rows[0][0] if rows[0] else "").lower():
        print("❌ idi 'Top queries' export kadu (first column 'Top queries' kavali)."
              "\n   Search Console > Performance > Export (Queries) cheyandi.")
        return 1
    data_rows = [r for r in rows[1:] if len(r) >= 5 and r[0].strip()]
    # skip group-date row (Clicks header repeat)
    data_rows = [r for r in data_rows if not r[1].lower().startswith("clicks")]

    queries = []
    for r in data_rows:
        try:
            clicks = int(r[1])
            impressions = int(r[2])
            ctr_s = r[3].strip().rstrip("%")
            ctr = float(ctr_s) / 100.0   # GSC export always percentage format
            position = float(r[4])
        except (ValueError, IndexError):
            continue
        queries.append({"query": r[0].strip(), "clicks": clicks,
                        "impressions": impressions, "ctr": ctr,
                        "position": position})

    if not queries:
        print("❌ parse ayye rows levu — GSC 'Queries' export check cheyandi")
        return 1

    # striking distance filter: impressions 100+, position 4-20, low CTR
    opps = [q for q in queries
            if q["impressions"] >= 100 and 4 <= q["position"] <= 20 and q["ctr"] < 0.05]
    opps.sort(key=lambda q: q["impressions"] * (21 - q["position"]), reverse=True)

    print("=" * 70)
    print(f"  SEARCH CONSOLE OPPORTUNITIES ({len(queries)} queries, "
          f"{len(opps)} striking-distance)")
    print("=" * 70)
    if not opps:
        print("  Ippudu striking-distance queries levu — inka traffic early stage."
              "\n  2-3 nelalu posts perigaka malli run cheyandi.")
        return 0

    print(f"  {'QUERY':38} {'IMPR':>7} {'POS':>5} {'CTR':>6}")
    print("  " + "-" * 66)
    for q in opps[:20]:
        print(f"  {q['query'][:36]:38} {q['impressions']:>7} "
              f"{q['position']:>5.1f} {q['ctr']*100:>5.1f}%")
    print("-" * 70)
    top3 = [q["query"] for q in opps[:3]]
    print("  🎯 ACTION PLAN (top 3 — immediate):")
    for i, q in enumerate(top3, 1):
        print(f"   {i}. \"{q}\" — ee query meeda already rank {opps[i-1]['position']:.0f}")
        print(f"      -> matching post ni --update cheyandi OR fresh deep article")
        print(f"         ravadam (title/desc/content optimize -> CTR perugutundi)")
    print("\n  Formula: veeti posts improve cheste 2-4 nelallo traffic 30-100%+ "
          "perugutundi (industry-proven striking-distance strategy).")
    print("=" * 70)
    return 0


def doctor() -> int:
    """Deployment health check — Oracle lo first run mundu okka command."""
    import requests as _rq
    import shutil as _sh

    ok = True
    results = []

    def check(label, fn):
        nonlocal ok
        try:
            detail = fn()
            results.append((True, label, detail or "OK"))
        except Exception as exc:
            ok = False
            results.append((False, label, f"FAIL: {exc}"))

    print("=" * 62)
    print("  DOCTOR — Deployment Health Check")
    print("=" * 62)

    # 1) Gemini key + live validation
    def _gemini():
        if not config.GEMINI_API_KEY:
            raise RuntimeError("GEMINI_API_KEY ledu (.env)")
        r = _rq.get(f"{config.GEMINI_API_BASE}/models",
                    params={"key": config.GEMINI_API_KEY}, timeout=15)
        if r.status_code != 200:
            raise RuntimeError(f"API {r.status_code} — key invalid?")
        n = len(r.json().get("models", []))
        return f"key valid, {n} models (model={config.GEMINI_MODEL})"
    check("Gemini API", _gemini)

    # 2) WordPress REST + auth
    def _wp():
        from .wordpress_client import WordPressClient
        wp = WordPressClient()
        me = wp.check_connection()
        cats = wp.list_categories()
        return f"{me.get('name', '?')} @ {config.WP_SITE} | {len(cats)} categories"
    check("WordPress REST", _wp)

    # 3) Telegram bot token (getMe — non-intrusive)
    def _tg():
        if not config.TELEGRAM_BOT_TOKEN:
            raise RuntimeError("TELEGRAM_BOT_TOKEN ledu")
        r = _rq.get(f"{config.TELEGRAM_API_BASE}/bot{config.TELEGRAM_BOT_TOKEN}/getMe",
                    timeout=10)
        data = r.json()
        if not data.get("ok"):
            raise RuntimeError(f"getMe fail ({r.status_code})")
        if not config.TELEGRAM_CHAT_ID:
            raise RuntimeError("TELEGRAM_CHAT_ID ledu")
        return f"@{data['result'].get('username', '?')} -> chat {config.TELEGRAM_CHAT_ID}"
    check("Telegram bot", _tg)

    # 4) IndexNow key format
    def _in():
        if not config.INDEXNOW_KEY:
            return "not set (optional — instant indexing ki set cheyandi)"
        k = config.INDEXNOW_KEY.strip()
        if not (8 <= len(k) <= 128) or not re.fullmatch(r"[A-Za-z0-9-]+", k):
            raise RuntimeError("key format wrong (A-Za-z0-9- chars only)")
        return f"set ({len(k)} chars)"
    check("IndexNow", _in)

    # 5) state DB + output dirs writable
    def _db():
        state.init(config.STATE_PATH)
        state.meta_set(config.STATE_PATH, "doctor:ping", "1")
        assert state.meta_get(config.STATE_PATH, "doctor:ping") == "1"
        config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        (config.OUTPUT_DIR / ".ping").write_text("ok")
        (config.OUTPUT_DIR / ".ping").unlink()
        return f"{config.STATE_PATH} + {config.OUTPUT_DIR} writable"
    check("Storage", _db)

    # 6) disk space (Oracle free VM 25GB; images + DB perugutayi)
    def _disk():
        free_gb = _sh.disk_usage(str(config.OUTPUT_DIR)).free / 1e9
        if free_gb < 1:
            raise RuntimeError(f"only {free_gb:.1f} GB free — clean cheyandi!")
        return f"{free_gb:.1f} GB free"
    check("Disk", _disk)

    for good, label, detail in results:
        print(f"  {'✅' if good else '❌'} {label:14} {detail}")

    # config summary
    print("-" * 62)
    print(f"  Plan: {config.DAILY_MIN}-{config.DAILY_MAX} posts/day + "
          f"{config.LISTICLES_PER_DAY} listicles | auto-refresh "
          f"{config.AUTO_REFRESH_PER_DAY}/day @ {config.AUTO_REFRESH_HOUR}:00")
    print(f"  Trends {'ON' if config.USE_TRENDS else 'OFF'} | Discover meta "
          f"{'ON' if config.DISCOVER_META_ENABLED else 'OFF'} | ads "
          f"{config.MAX_AD_SLOTS} slots"
          + (" (shortcode set)" if config.AD_SHORTCODE else " (NO shortcode!)"))
    print("=" * 62)
    if ok:
        print("  ALL SYSTEMS GO 🚀  — bot ready, start: systemctl --user start autoblog")
    else:
        print("  ❌ problems unna — ventane fix cheyandi (upper errors chudu)")
    print("=" * 62)
    return 0 if ok else 1


def trends_check() -> int:
    """Google Trends India daily — education-relevant trends display."""
    print("=" * 62)
    print("  GOOGLE TRENDS (India) — TODAY")
    print("=" * 62)
    topics = topic_engine.fetch_trending_topics()
    if not topics:
        print("  (fetch fail / empty — network check cheyandi)")
        return 1
    print("\n  TOP 10 (anni):")
    for i, t in enumerate(topics[:10], 1):
        print(f"  {i:2}. {t['title']}  [{t['traffic'] or '?'} searches]")
    edu = topic_engine.filter_edu_trends(topics)
    print(f"\n  EDUCATION-RELEVANT ({len(edu)}):")
    for t in edu:
        print(f"  🎓 {t['title']}  [{t['traffic'] or '?'}]")
        if t["news_title"]:
            print(f"      ↳ {t['news_title'][:70]}")
    if edu:
        print("\n  ↳ USE_TRENDS=1 unte bot automatically ee topic meeda article"
              " rashtundi (1/day).")
    print("=" * 62)
    return 0


def revenue_check() -> int:
    """Revenue setup audit — em set ayyindi, em missing o cheptundi."""
    state.init(config.STATE_PATH)
    print("=" * 62)
    print("  STUDENTUP.IN REVENUE AUDIT")
    print("=" * 62)

    checks = [
        ("TELEGRAM_CHANNEL_URL set (repeat traffic CTA)",
         bool(config.TELEGRAM_CHANNEL_URL)),
        ("AFFILIATE_LINKS set (affiliate income)",
         bool(config.AFFILIATE_LINKS)),
        ("AD_SHORTCODE set (in-content ads)",
         bool(config.AD_SHORTCODE)),
        (f"MAX_AD_SLOTS = {config.MAX_AD_SLOTS} (3-5 ideal long articles)",
         1 <= config.MAX_AD_SLOTS <= 5),
        (f"CLS wrapper ON (layout-shift protection)",
         config.AD_CLS_WRAPPER),
        (f"HIGH_CPC_SHARE = {config.HIGH_CPC_SHARE}% (30 recommended)",
         20 <= config.HIGH_CPC_SHARE <= 50),
        (f"LISTICLES_PER_DAY = {config.LISTICLES_PER_DAY} (trending stories)",
         config.LISTICLES_PER_DAY >= 1),
        (f"Daily auto-refresh ON ({config.AUTO_REFRESH_PER_DAY}/day)",
         config.AUTO_REFRESH_PER_DAY >= 1),
        ("INDEXNOW_KEY set (instant indexing)",
         bool(config.INDEXNOW_KEY)),
        (f"Google Trends topics ON (USE_TRENDS={config.USE_TRENDS})",
         bool(config.USE_TRENDS)),
        (f"Discover max-image-preview meta ({'ON' if config.DISCOVER_META_ENABLED else 'OFF'})",
         bool(config.DISCOVER_META_ENABLED)),
    ]
    score = 0
    print("\nBOT-SIDE (.env):")
    for label, ok in checks:
        mark = "✅" if ok else "⚠️ "
        print(f"  {mark} {label}")
        score += 1 if ok else 0
    avgs = state.avg_scores(config.STATE_PATH)
    if avgs["n"]:
        print(f"  📊 Quality: avg QA {avgs['qa']}/100 · originality {avgs['orig']}%")

    print(f"\n  Bot-side score: {score}/{len(checks)}")

    print("\nSITE-SIDE (WordPress dashboard — manual cheyali):")
    for item in [
        "AdSense Auto Ads ON cheyandi",
        "Anchor ads (mobile sticky) allow cheyandi",
        "Rank Math / Yoast plugin active + sitemap",
        "Caching plugin (LiteSpeed / WP-Optimize) — speed = viewability",
        "Search Console lo sitemap submit",
        "30+ posts ayaka Google News Publisher apply",
        "Rank Math > Titles & Meta > Global Robots: 'Large' image preview set cheyandi (Discover)",
        "10K+ pageviews ayaka Ezoic / Monumetric apply (RPM 50-150% up)",
    ]:
        print(f"  🔧 {item}")

    print("\nPOLICY REMINDERS (ban risk nunchi kapadutayi):")
    for item in [
        "Own ads click cheyakudadu (instant ban)",
        "Forced navigation / back-refresh ad tricks cheyakudadu",
        "'Click here' arrows deggara ads pettakudadu",
    ]:
        print(f"  🚫 {item}")
    print("=" * 62)
    return 0


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
    parser.add_argument("--listicle", nargs="?", const="auto", default=None,
                        metavar="TOPIC",
                        help="trending listicle post (Top 10 jobs lanti stories); topic optional")
    parser.add_argument("--auto-refresh", type=int, default=0, metavar="N",
                        help="purana N posts ni kotha info tho refresh chey")
    parser.add_argument("--add-source", default="",
                        help="--update tho extra source URL (kotha info)")
    parser.add_argument("--status", action="store_true", help="show stats & today's plan")
    parser.add_argument("--check-wp", action="store_true", help="verify WP credentials")
    parser.add_argument("--notify-test", action="store_true", help="send test notification")
    parser.add_argument("--revenue-check", action="store_true",
                        help="revenue setup audit — em missing o cheptundi")
    parser.add_argument("--gsc", default="", metavar="CSV",
                        help="Search Console queries CSV -> striking-distance opportunities")
    parser.add_argument("--doctor", action="store_true",
                        help="deployment health check — anni dependencies verify")
    parser.add_argument("--trends", action="store_true",
                        help="Google Trends India education trends chupinchindi")
    args = parser.parse_args()

    _setup_logging()

    if args.status:
        return show_status()
    if args.check_wp:
        return check_wp()
    if args.notify_test:
        return notify_test()
    if args.revenue_check:
        return revenue_check()
    if args.gsc:
        return gsc_opportunities(args.gsc)
    if args.doctor:
        return doctor()
    if args.trends:
        return trends_check()
    try:
        src = args.add_source or args.url
        listicle_arg = args.listicle or ""
        if listicle_arg == "auto":
            listicle_arg = ""  # bot idea pick chestundi
        return run(dry_run=args.dry_run, force=args.force, mock=args.mock,
                   category=args.category, source_url=src,
                   process_queue=args.process_queue, update_id=args.update,
                   listicle=listicle_arg, auto_refresh_n=args.auto_refresh)
    except wordpress_client.WordPressAuthError as exc:
        log.error("%s", exc)
        return 3
    except (wordpress_client.WordPressError, gemini_client.GeminiError) as exc:
        log.error("Publishing failed: %s", exc)
        return 4
    except Exception:
        log.exception("Unexpected error")
        return 5
