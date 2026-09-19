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
from datetime import datetime, timedelta, timezone
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
        listicle: str = "", auto_refresh_n: int = 0,
        quiz: bool = False, quiz_topic: str = "", quiz_level: int = 0,
        quiz_questions: int = 0, notebooklm_brief_file: str = "",
        target_year: int = 0) -> int:
    now = _now()
    today = now.date()
    now_hour = now.hour
    state.init(config.STATE_PATH)
    try:  # scheduler heartbeat (watchdog kosam)
        state.meta_set(config.STATE_PATH, "heartbeat", now.isoformat())
    except Exception as exc:  # noqa: BLE001 — best-effort (silent kaadu)
        log.debug("run skip: %s", exc)

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

    # --- manual quiz mode (--quiz / --quiz-topic "...") ----------------------
    if quiz or quiz_topic:
        result = pipeline.create_quiz(topic=quiz_topic, level=quiz_level,
                                      questions=quiz_questions, mock=mock,
                                      dry_run=dry_run)
        log.info("QUIZ READY ✔ %s (status=%s)", result["link"], result["status"])
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
        brief = ""
        if notebooklm_brief_file:
            brief_path = Path(notebooklm_brief_file)
            if not brief_path.exists():
                log.error("NotebookLM brief file ledu: %s", notebooklm_brief_file)
                return 2
            brief = brief_path.read_text(encoding="utf-8", errors="replace")[:18000]
        result = pipeline.create_from_source(
            source_url, mock=mock, category=category, notebooklm_brief=brief,
            target_year=target_year or None)
        log.info("SOURCE POST READY ✔ %s (status=%s)", result["link"], result["status"])
        return 0

    # --- schedule check ----------------------------------------------------
    if not (force or dry_run):
        # v20: hub pages auto-rebuild — week ki okkaru (Mon after 07h), playbook
        # Phase-2 authority engine. Fail ayna daily flow pariparu (try/except).
        iso = today.isocalendar()
        hkey = f"hubweek:{iso[0]}-{iso[1]}"
        if now_hour >= config.ACTIVE_HOUR_START \
                and not state.meta_get(config.STATE_PATH, hkey):
            state.meta_set(config.STATE_PATH, hkey, "1")
            try:
                from . import hubs as _hubs

                n = len(_hubs.rebuild_hubs())
                log.info("WEEKLY HUBS: %d pages refreshed", n)
            except Exception:
                log.exception("Weekly hub rebuild failed (non-fatal)")
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
        # --- v59: బ్రేకింగ్ న్యూస్ feed — radar sweep tarvata site ticker fresh ---
        if (getattr(config, "BREAKING_ENABLED", True)
                and now_hour >= getattr(config, "RADAR_HOUR", 7)
                and not state.meta_get(config.STATE_PATH, f"breaking:{today.isoformat()}")):
            try:
                from . import breaking, news_radar

                _r = news_radar.run_radar()
                _bres = breaking.publish(_r.get("items", []))
                state.meta_set(config.STATE_PATH, f"breaking:{today.isoformat()}", "1")
                log.info("BREAKING FEED ✔ %d items (site ticker)", _bres["count"])
                try:  # v61: theme ki kuda push (WP theme active unte)
                    from . import wp_theme_sync

                    _tres = wp_theme_sync.push()
                    log.info("WP THEME SYNC %s — %s", "✔" if _tres.get("ok") else "skip",
                             _tres.get("reason") or _tres.get("updated"))
                except Exception:
                    log.exception("wp theme sync failed (non-fatal)")
            except Exception:
                log.exception("breaking feed failed (non-fatal)")
        # --- v60: SITE GUARDIAN — roju okkasari system motham check + report ---
        if (getattr(config, "GUARDIAN_ENABLED", True)
                and now_hour >= getattr(config, "GUARDIAN_HOUR", 20)
                and not state.meta_get(config.STATE_PATH, f"guardian:{today.isoformat()}")):
            try:
                from . import guardian

                _g = guardian.guard(notify=True, print_out=False)
                state.meta_set(config.STATE_PATH, f"guardian:{today.isoformat()}", "1")
                log.info("SITE GUARDIAN ✔ %d/%d ok · %d owner-pending",
                         _g["passed"], _g["checked"], _g.get("warned", 0))
                for _r in _g["results"]:
                    if not _r["ok"] and not _r.get("warn_only"):
                        log.warning("GUARDIAN ❌ %s: %s (%s)", _r["id"], _r["detail"], _r["fix"])
            except Exception:
                log.exception("site guardian failed (non-fatal)")
        # --- v57: AD ADVISOR — roju okkasari: e network ki eppudu apply cheyyali ---
        if (getattr(config, "AD_ADVISOR_ENABLED", True)
                and now_hour >= getattr(config, "AD_ADVISOR_HOUR", 10)
                and not state.meta_get(config.STATE_PATH,
                                       f"advisor:{today.isoformat()}")):
            try:
                from . import ad_advisor as _adv

                _res = _adv.advice(notify=True)
                state.meta_set(config.STATE_PATH, f"advisor:{today.isoformat()}", "1")
                log.info("AD ADVISOR ✔ %s", _res["action"]["title"])
                for _k in _res["new_milestones"]:
                    log.info("AD ADVISOR milestone: %s — Telegram alert pampindi", _k)
            except Exception:
                log.exception("Ad advisor failed (non-fatal)")
        # --- v26: Daily Quiz slot — roju okati, QUIZ_HOUR tarvata ---
        if (config.QUIZ_ENABLED
                and now_hour >= config.QUIZ_HOUR
                and not state.meta_get(config.STATE_PATH,
                                       f"quizdate:{today.isoformat()}")):
            if not mock and not config.GEMINI_API_KEY \
                    and not getattr(config, "GEMINI_API_KEYS", []):
                log.warning("QUIZ skip — GEMINI_API_KEY ledu")
            else:
                try:
                    result = pipeline.create_quiz(mock=mock)
                    state.meta_set(config.STATE_PATH,
                                   f"quizdate:{today.isoformat()}", "1")
                    log.info("DAILY QUIZ READY ✔ %s (status=%s)",
                             result["link"], result["status"])
                    return 0
                except ValueError as exc:
                    # already generated today (manual --quiz) — mark & move on
                    state.meta_set(config.STATE_PATH,
                                   f"quizdate:{today.isoformat()}", "1")
                    log.info("Daily quiz already done: %s", exc)
                except Exception:
                    log.exception("Daily quiz failed — regular posting continues")
        # --- v15/v16: Breaking-News Radar — every RADAR_INTERVAL_HOURS ---
        if (config.RADAR_ENABLED
                and (now_hour - config.RADAR_HOUR) % max(1, config.RADAR_INTERVAL_HOURS) == 0
                and now_hour >= config.RADAR_HOUR
                and not state.meta_get(config.STATE_PATH,
                                       f"radar:{today.isoformat()}:{now_hour}")):
            state.meta_set(config.STATE_PATH, f"radar:{today.isoformat()}:{now_hour}", "1")
            log.info("RADAR: scheduled district+grid+watch sweep (hour %02d)", now_hour)
            try:
                radar_run()
            except Exception:
                log.exception("RADAR run failed — regular posting continues")
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
        print("      -> matching post ni --update cheyandi OR fresh deep article")
        print("         ravadam (title/desc/content optimize -> CTR perugutundi)")
    print("\n  Next step: matching post ni human ga inspect chesi title/snippet or content/internal links "
          "test cheyandi. Search Console lo before/after data tho impact measure cheyandi; "
          "traffic percentage or timing guarantee ledu.")

    # v21: GSC real data → queue priority boost (radar/keyword queue lo
    # ee queries matche ayye items mundu process avutayi)
    try:
        import json as _json
        import re as _re

        from . import sources as _src
        from . import state as _st

        boost = []
        for q in opps[:5]:
            for tok in _re.findall(r"[a-z0-9ఀ-౿]{3,}",
                                   q["query"].lower()):
                if tok not in boost:
                    boost.append(tok)
        boost = boost[:25]
        if boost:
            _st.meta_set(config.STATE_PATH, "gscboost:v1",
                         _json.dumps(boost, ensure_ascii=False))
            n = _src.apply_queue_boost(boost)
            print(f"  ✅ Queue boost: {len(boost)} GSC terms saved"
                  f" + {n} queue line(s) top ki move ayayi")
    except Exception:
        log.exception("Queue boost apply failed (non-fatal)")
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
        (config.OUTPUT_DIR / ".ping").write_text("ok", encoding="utf-8")
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
    # v38: top-post engine summary (offline — no network calls)
    try:
        from . import top_post as _tp
        _st = _tp.universe_stats()
        print(f"  Top Post Engine {'ON' if config.TOP_POST_ENGINE else 'OFF'} | "
              f"gate {config.TOP_POST_MIN_SCORE}/100 "
              f"({'strict' if config.TOP_POST_STRICT else 'off'}) | "
              f"{_st['total']} keywords ({_st['entities']} entities × "
              f"{_st['intents']} intents) | {_st['clusters']} clusters")
    except Exception as exc:  # noqa: BLE001
        print(f"  Top Post Engine: ❌ {str(exc)[:60]}")
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


def pin_check_run() -> int:
    """v65/v66: pin-to-pin certificate proof (67 checks · deterministic fixture)."""
    from . import post_gate

    return post_gate.main()


def trends_run(queue: bool = True) -> int:
    """v65: Google Trends + Suggest capture (niche filter → topic queue)."""
    from . import trends

    if queue:
        return trends.main()
    res = trends.capture(queue=False)
    print(f"trends: {res['trends']} · suggest: {res['suggest']}")
    for t in res["top"]:
        print("   -", str(t.get("title"))[:70])
    return 0


def rm100_run() -> int:
    """v64: Rank Math 100 engine proof — imperfect draft → 100/100 breakdown."""
    from . import rm100, validator

    
    art = rm100.sample_article()
    res = rm100.apply(art)
    checks = validator.rankmath_strict(art, art.get("content_html", "")).get("checks", [])
    print("=" * 70)
    print("  🎯 RANK MATH 100 ENGINE — proof (deterministic fixes, LLM ledu)")
    print("=" * 70)
    print(f"  score: {res['before']}/100  →  {res['after']}/100"
          f"   ({len(checks)} on-page tests)")
    print(f"  fixes: {', '.join(res['applied']) or '—'}")
    print(f"  migilinavi: {res['remaining'] or 'emi ledu ✔'}")
    print(f"  title: {art['title']} ({len(art['title'])} ch)")
    print(f"  meta: {len(art['meta_description'])} ch · slug: {art['slug']}"
          f" · words: {rm100._words(art['content_html'])}")
    if checks:
        print("-" * 70)
        for c in checks:
            print(f"    {'✅' if c['ok'] else '❌'} {c['item']:26s} {c['points']} pts")
    print("=" * 70)
    return 0 if res["after"] == 100 else 1


def readiness_run() -> int:
    """v62: TOP WEBSITE READINESS — okka command lo motham system proof."""
    from . import readiness

    rep = readiness.run_report()
    arts = readiness.write_artifacts(rep)
    readiness.print_report(rep, arts)
    return 0 if rep.get("ok") else 1


def push_theme_data(dry_run: bool = False) -> int:
    """v61: bot data → WordPress theme (breaking · proof · house ads).

    v73: countdown/deadline push teesesaamu (hero card user brief tho poyindi).
    """
    from . import wp_theme_sync

    payload = wp_theme_sync.build_payload()
    if not payload:
        print("  ⚠️  push cheyyalsina data ledu (breaking feed/house ads/proof khali)")
        return 0
    res = wp_theme_sync.push(payload, dry_run=dry_run)
    print("=" * 62)
    print("  🎨 WP THEME SYNC — bot data → site theme")
    print("=" * 62)
    for k, v in res.get("sent", {}).items():
        print(f"  • {k}: {v if not isinstance(v, list) else str(len(v)) + ' items'}")
    if res.get("ok"):
        extra = " (dry-run, network call ledu)" if res.get("dry_run") else ""
        print(f"  ✅ push OK{extra} — updated: {res.get('updated', [])}")
        return 0
    print(f"  ❌ push fail: {res.get('reason')}")
    print("     ↳ fix: .env lo WP_SITE/WP_USERNAME/WP_APP_PASSWORD + theme activate")
    return 1


def guardian_run(notify: bool = False, quiet: bool = False) -> int:
    """v60: SITE GUARDIAN — system motham check (site/UI/SEO/ads/feed/storage)."""
    from . import guardian

    summary = guardian.guard(notify=notify, print_out=not quiet)
    return 0 if summary.get("ok") else 1


def breaking_feed_run(from_file: str = "") -> int:
    """v59: బ్రేకింగ్ న్యూస్ feed build — site ticker + section ki.

    Default: radar sweep (district + 143 official sources) → verified items
    matrame → preview/data/breaking.json. `--breaking-from FILE` tho offline
    (test/approved list) nunchi kuda generate cheyochu.
    """
    import json as _json

    from . import breaking

    print("=" * 62)
    print("  🚨 BREAKING NEWS FEED — site ticker + బ్రేకింగ్ న్యూస్ section")
    print("=" * 62)
    raw = []
    if from_file:
        try:
            data = _json.loads(Path(from_file).read_text(encoding="utf-8"))
            raw = data.get("items", data) if isinstance(data, dict) else data
            print(f"  source file: {from_file} ({len(raw)} raw items)")
        except Exception as exc:  # noqa: BLE001
            print(f"  ⛔ file chadavalekapoyindi: {exc}")
            return 1
    else:
        from . import news_radar

        summary = news_radar.run_radar()
        raw = summary.get("items", [])
        if not summary.get("enabled", True):
            print("  RADAR_ENABLED=0 — feed khali ga untundi (fake news ledu)")
    res = breaking.publish(raw, source="file" if from_file else "radar")
    st = breaking.stats()
    print(f"  feed: {res['count']} items → {res['path']}")
    print(f"  updated: {res['updated']}")
    if st["by_tag"]:
        print("  tags: " + " · ".join(f"{k}:{v}" for k, v in st["by_tag"].items()))
    if not res["count"]:
        print("  ℹ️  ippudu verified breaking item ledu — site 'kotha update ledu' ani cheptundi")
    print("  most-used order: " + " · ".join(breaking.most_used_cats()))
    print("=" * 62)
    return 0


def radar_run(process_posts: bool = True) -> int:
    """v15/v16/v17: full radar sweep — districts + official grid + watch.
    # v65: Google Trends/Suggest capture (network lekapote silent skip)
    if getattr(config, "TRENDS_ENABLED", True):
        try:
            from . import trends as _tr

            _cap = _tr.capture(queue=True)
            if _cap.get("trends") or _cap.get("suggest"):
                log.info("v65 trends: %d niche trends · %d suggest · queue +%s",
                         _cap["trends"], _cap["suggest"],
                         (_cap.get("queue") or {}).get("added", 0))
        except Exception:  # noqa: BLE001 — trends bot ni aapakudadu
            log.info("trends capture skip (safe)")

    Queue fresh edu news URLs + channel topics; optionally process up to
    RADAR_POSTS_PER_DAY articles (topics first, then source queue URLs).
    """
    from . import news_radar

    state.init(config.STATE_PATH)
    print("=" * 62)
    print("  📡 BREAKING NEWS RADAR — TS 33 + AP 26 districts")
    print("     + official sources grid + watch channels")
    print("=" * 62)
    summary = news_radar.run_radar()
    if not summary.get("enabled", True):
        print("  RADAR_ENABLED=0 — skip chesesaru")
        return 0
    d = summary.get("districts", 0)
    g = summary.get("grid", 0)
    w = summary.get("watch", 0)
    print(f"  New queue items: {d} district + {g} grid URLs | {w} channel topics")

    # v59: same sweep → site బ్రేకింగ్ న్యూస్ feed (ticker + section)
    try:
        from . import breaking

        if config.BREAKING_ENABLED:
            bres = breaking.publish(summary.get("items", []))
            print(f"  🚨 breaking feed: {bres['count']} items → preview/data/breaking.json")
    except Exception as exc:  # noqa: BLE001
        log.warning("breaking feed skip: %s", exc)

    # v21: GSC boost (state meta) → queue re-sort — real impressions decide
    # ee roju enti process avalo (radar sweep tarvata automatic).
    try:
        import json as _json

        _boost = _json.loads(state.meta_get(config.STATE_PATH,
                                            "gscboost:v1") or "[]")
        if _boost:
            from . import sources as _src

            _nb = _src.apply_queue_boost(_boost)
            if _nb:
                print(f"  GSC boost: {_nb} queue line(s) prioritized")
    except Exception as exc:  # noqa: BLE001 — best-effort (silent kaadu)
        log.debug("radar_run skip: %s", exc)

    # v17: keyword dominance — prathi roju 1 saari autocomplete + gap analyse
    kw_queued = 0
    try:
        from . import keyword_engine as ke

        kw = ke.daily_keyword_harvest(max_queue=config.KEYWORD_DAILY_QUEUE)
        kw_queued = int(kw.get("queued", 0) or 0)
        if kw_queued:
            print(f"  Keyword engine: {kw_queued} keyword topics queued")
    except Exception as exc:
        print(f"  keyword engine skip: {exc}")

    if not process_posts:
        print("  (posts processing skip — --dry-run mode)")
        return 0
    if not config.GEMINI_API_KEY:
        print("  GEMINI_API_KEY ledu — queue fill ayyindi, posts skip")
        return 0

    n = min(config.RADAR_POSTS_PER_DAY, d + g + w + kw_queued)
    done = 0
    # 1) pending topics first (channel texts + keyword gap targets)
    for topic in news_radar.pending_topics(limit=n):
        try:
            cat = pipeline.classify_category(topic)
            recent = state.recent_titles(config.STATE_PATH, limit=40)
            article = gemini_client.generate_article(
                cat, recent, year=_now().year, trend_topic=topic)
            title = (article.get("title") or "").strip()
            if not title or state.title_exists(config.STATE_PATH, title):
                news_radar.mark_topic_done(topic)
                continue
            from . import seo as _seo

            article["slug"] = _seo.optimize_slug(
                _safe_slug(article.get("slug", ""), title),
                focus_keyword=article.get("focus_keyword", ""))
            for k, v in (("external_links", []), ("secondary_keywords", []),
                         ("quick_answer", ""), ("faq", []), ("seo_title", ""),
                         ("focus_keyword", topic[:60])):
                article.setdefault(k, v)
            result = pipeline.publish_article(article, day=_now().date())
            done += 1
            print(f"  RADAR POST ✔ {result['link']}")
        except Exception as exc:
            log.error("radar topic post failed (%s): %s", topic[:50], exc)
        finally:
            news_radar.mark_topic_done(topic)  # poison-loop kaadu
    # 2) source queue URLs (district/grid news) — original rewrite flow
    while done < n:
        url = sources.pending_from_queue()
        if not url:
            break
        try:
            result = pipeline.create_from_source(url)
            done += 1
            print(f"  RADAR POST ✔ {result['link']}")
        except Exception as exc:
            log.error("radar URL failed (%s): %s — skip", url[:60], exc)
        finally:
            sources.mark_done_and_clean(url)
    print(f"  Radar posts created: {done}")
    return 0


def sources_view() -> int:
    """v16.1: official sources grid anni chupinchu (verify coverage)."""
    from . import sources_grid as sg

    by_cat: dict = {}
    for s_ in sg.SOURCES_GRID:
        by_cat.setdefault(s_["cat"], []).append(s_)
    daily_n = sum(1 for s_ in sg.SOURCES_GRID if s_.get("daily"))
    print("=" * 62)
    print(f"  OFFICIAL SOURCES GRID — {len(sg.SOURCES_GRID)} sources "
          f"({daily_n} daily hot-list, rest rotation)")
    print("=" * 62)
    for cat in sorted(by_cat):
        print(f"\n  [{cat}] ({len(by_cat[cat])})")
        for s_ in by_cat[cat]:
            print(f"    - {s_['name']}" + ("  ★ daily" if s_.get("daily") else ""))
    print()
    return 0


def keywords_view() -> int:
    """v17: keyword matrix + coverage vs live posts + live autocomplete."""
    state.init(config.STATE_PATH)
    from . import keyword_engine as ke

    matrix = ke.keyword_matrix()
    hot = [m for m in matrix if m["hot"]]
    print("=" * 62)
    print(f"  KEYWORD DOMINANCE ENGINE — {len(matrix)} keywords "
          f"({len(ke.EXAMS)} exams × {len(ke.INTENTS)} intents, {len(hot)} hot)")
    print("=" * 62)
    titles: list = []
    try:
        from .wordpress_client import WordPressClient

        titles = [t.get("title", "") for t in
                  WordPressClient().get_recent_published(per_page=100)]
    except Exception:
        print("  (live post titles raaledu — sandbox/network; coverage 0 ga untundi)")
    rep = ke.coverage_report(titles)
    print(f"\n  Coverage vs {rep['existing_posts']} live posts: "
          f"{rep['covered']}/{rep['total']} keywords ({rep['pct']}%)")
    print("\n  Sample keyword targets (hot first):")
    for m in matrix[:8]:
        print(f"    - {m['title']}")
    print("\n  Google Autocomplete harvest (live, top seeds):")
    for seed in ke.suggest_seeds()[:5]:
        sugg = ke.harvest_suggest(seed)
        print(f"    {seed}: {', '.join(sugg[:5]) or '(no data)'}")
    q = ke.daily_keyword_harvest(max_queue=config.KEYWORD_DAILY_QUEUE, force=True)
    print(f"\n  Daily harvest: {q.get('queued', 0)} keyword topics queued (topics_queue.txt)")
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
        ("AdSense pre-approval gate (ads intentionally off)",
         not bool(getattr(config, "ADSENSE_APPROVED", False))),
        ("ADSENSE_CLIENT_ID valid after approval",
         (not getattr(config, "ADSENSE_APPROVED", False)) or
         (bool(getattr(config, "ADSENSE_CLIENT_ID", ""))
          and re.fullmatch(r"ca-pub-\d{6,20}",
                           getattr(config, "ADSENSE_CLIENT_ID", "")) is not None)),
        ("AdSense loader enabled only after approval",
         not getattr(config, "ADSENSE_APPROVED", False) or
         bool(getattr(config, "ADSENSE_ENABLED", False))),
        ("AdSense CMP/provider after approval",
         not getattr(config, "ADSENSE_APPROVED", False) or
         bool(getattr(config, "ADSENSE_CONSENT_PROVIDER", ""))),
        ("Plugin auto-stack enabled", bool(getattr(config, "PLUGIN_AUTO_INSTALL", False))),
        ("AFFILIATE_LINKS set (affiliate income)",
         bool(config.AFFILIATE_LINKS)),
        ("AD_SHORTCODE gate (ignored before approval)",
         not getattr(config, "ADSENSE_APPROVED", False) or bool(config.AD_SHORTCODE)),
        (f"MAX_AD_SLOTS = {config.MAX_AD_SLOTS} (cap; unused before approval)",
         1 <= config.MAX_AD_SLOTS <= 5),
        ("CLS wrapper ON (layout-shift protection)",
         config.AD_CLS_WRAPPER),
        (f"Commercial-topic mix = {config.HIGH_CPC_SHARE}% (not a CPC promise)",
         0 <= config.HIGH_CPC_SHARE <= 50),
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
    ads_steps = ([
        "Keep ADSENSE_APPROVED=0; no ad spaces until the owner sees Google approval",
        "Use Search Console Indexing + Core Web Vitals reports weekly",
    ] if not getattr(config, "ADSENSE_APPROVED", False) else [
        "Verify AdSense Policy Center, CMP/consent, ads.txt and authorized sites",
        "Review Auto Ads/anchor placements manually; no forced clicks or refresh tricks",
    ])
    for item in ads_steps + [
        "Rank Math / Yoast plugin active + sitemap",
        "Caching plugin (LiteSpeed / WP-Optimize) — test real mobile UX",
        "Search Console lo sitemap submit and inspect important URLs",
        "Google News/Discover visibility is not guaranteed by an application",
        "Rank Math > Titles & Meta > Global Robots: 'Large' image preview set cheyandi (Discover)",
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


def content_audit_run(limit: int = 500) -> int:
    """Read-only audit of all published WP posts, independent of state.db."""
    from . import content_audit

    return content_audit.run(limit=limit)


def google_audit_run(url: str) -> int:
    from . import google_audit

    return google_audit.run(url)


def research_brief_run(seed: str, url_file: str = "", limit: int = 6,
                       target_year: int = 0) -> int:
    from . import research_brief

    return research_brief.run(
        seed, url_file=url_file, limit=max(1, min(limit, 12)),
        target_year=target_year or None)


# --------------------------------------------------------------- v38 top post

def top_post_run(keyword: str, category: str = "", publish: bool = False,
                 mock: bool = False, dry_run: bool = False) -> int:
    """v38: blueprint (plan) → optional article → draft/publish."""
    from . import top_post

    state.init(config.STATE_PATH)
    if publish:
        log.info("Top-post publish flow: keyword=%r mock=%s dry_run=%s",
                 keyword, mock, dry_run)
        try:
            result = top_post.create_top_post(keyword, mock=mock, dry_run=dry_run,
                                              category=category)
        except Exception as exc:  # noqa: BLE001
            log.error("Top-post create failed: %s", exc)
            top_post.run_blueprint(keyword, category=category)
            return 4
        print(f"🏆 TOP POST {'(dry-run) ' if dry_run else ''}created: "
              f"{result.get('link', '')} [{result.get('status')}]")
        return 0
    return top_post.run_blueprint(keyword, category=category)


def top_post_plan_run(days: int = 0, per_day: int = 1, show: int = 14) -> int:
    from . import top_post

    return top_post.run_plan(days=days or config.TOP_POST_PLAN_DAYS,
                             per_day=per_day, show=show)


def keyword_universe_view(export: bool = True, show: int = 12) -> int:
    from . import top_post

    return top_post.run_universe(export=export, show=show)


def score_post_run(path: str, keyword: str = "") -> int:
    from . import top_post

    return top_post.run_score_file(path, keyword)


# ------------------------------------------------------------- test runner

def test_all_run(only: str = "", quiet: bool = False) -> int:
    """v41: ANNI suites okate command tho (local + CI).

    ee command ne `.github/workflows/tests.yml` kuda run chestundi — so CI lo
    fail ayye suite ni local lo kuda exact ga reproduce cheyyachu.
    """
    import subprocess
    import sys as _sys
    from pathlib import Path as _Path

    root = _Path(__file__).resolve().parent.parent
    files = sorted((root / "tests").glob("*.py"))
    if only:
        files = [f for f in files if only in f.name]
    if not files:
        print("tests/ lo e suites levu")
        return 1
    passed, failed = [], []
    for f in files:
        try:
            proc = subprocess.run([_sys.executable, str(f)], cwd=root,
                                  capture_output=True, text=True, timeout=600)
        except subprocess.TimeoutExpired:
            failed.append((f.name, "TIMEOUT (>600s)"))
            print(f"  ⏱️  {f.name} — TIMEOUT")
            continue
        out = (proc.stdout or "").strip().splitlines()
        tail = out[-3:] if out else []
        if proc.returncode == 0:
            passed.append(f.name)
            print(f"  ✔ {f.name}" + ("" if quiet else f" — {tail[-1][:70] if tail else ''}"))
        else:
            failed.append((f.name, "\n".join((proc.stdout or "")[-1200:] +
                                              (proc.stderr or "")[-400:])))
            print(f"  ❌ {f.name}")
            if not quiet:
                print("\n".join("      " + ln for ln in
                                ((proc.stdout or "")[-1200:] +
                                 (proc.stderr or "")[-400:]).splitlines()[-14:]))
    print("=" * 62)
    print(f"  suites: {len(passed)} passed · {len(failed)} failed "
          f"(total {len(files)})")
    if failed:
        print("  FAILED: " + ", ".join(n for n, _ in failed))
        return 1
    print("  ALL SUITES PASSED ✔")
    return 0


# ------------------------------------------------------- v41 site audit + fix

def site_audit_run(fix: bool = False, apply: bool = False, allow_trash: bool = False,
                   actions: str = "", snapshot: str = "", save: str = "") -> int:
    """v41: studentup.in deep audit (+ optional safe autofix)."""
    from . import site_audit

    acts = [a.strip() for a in (actions or "").split(",") if a.strip()]
    return site_audit.run_audit(fix=fix, dry_run=not apply,
                                allow_trash=allow_trash, actions=acts or None,
                                snapshot=snapshot, save=save)


def service_center_setup(dry: bool = True, force: bool = False) -> int:
    """Publish/preview the Student Internet Center service landing page."""
    from . import service_center

    if not config.SERVICE_CENTER_ENABLED:
        print("📞 Student Service Center disabled: SERVICE_CENTER_ENABLED=0")
        return 0
    if dry:
        out = config.OUTPUT_DIR / "service-center.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        page = service_center.publish_page(None, dry=True)
        out.write_text(
            "<!doctype html><html lang='en'><head><meta charset='utf-8'>"
            f"<title>{page['title']}</title></head><body>{page['html']}</body></html>",
            encoding="utf-8",
        )
        print(f"📞 Service Center preview saved: {out}")
        if not (config.SERVICE_CENTER_PHONE or config.SERVICE_CENTER_WHATSAPP):
            print("⚠️  Add SERVICE_CENTER_PHONE or SERVICE_CENTER_WHATSAPP before publishing")
        return 0
    from .wordpress_client import WordPressClient
    try:
        wp = WordPressClient()
        wp.check_connection()
        result = service_center.publish_page(wp, dry=False, force=force)
        if result.get("status") == "manual-preserved":
            print(f"⚠️  Service Center page preserved: {result.get('detail', '')}")
            return 0
        print(f"📞 Service Center page: {result.get('link', result.get('slug'))}")
        return 0
    except Exception as exc:  # noqa: BLE001
        print(f"❌ Service Center page failed: {exc}")
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



PRIVACY_HTML = f"""<p>studentup.in visits gurinchi detailed ga explain chestunnam.</p>
<h2>Information We Collect</h2>
<p>Analytics or consent tools enabled in the site configuration may collect limited page-performance information. Login, OTP, passwords, UPI PINs or bank credentials adagabadu.</p>
<h2>Cookies &amp; Advertising</h2>
<p>Before AdSense approval, this project emits no AdSense loader or ad spaces. If advertising is later enabled, Google/other vendors may use cookies or similar technologies only under the configured consent and privacy controls. Users can review ad settings at <a href="https://www.google.com/settings/ads">google.com/settings/ads</a>.</p>
<h2>Contact</h2>
<p>Questions: <a href="mailto:{config.SUPPORT_EMAIL}">{config.SUPPORT_EMAIL}</a></p>"""

ABOUT_HTML = """<p>studentup.in — Telugu students kosam free education information portal: govt jobs, notifications, results, hall tickets, scholarships and learning guidance.</p>
<h2>Meeku enduku help avutundi?</h2>
<p>Prathi notification ni simple Telugu lo, steps/tables/visible FAQ tho explain chestam. Content team source-backed drafts prepare chestundi; human review and official-source verification workflow follow chestam.</p>"""

CONTACT_HTML = f"""<p>Mana team ki direct ga contact avvali:</p>
<ul>
<li>Editorial: <a href="mailto:{config.SUPPORT_EMAIL}">{config.SUPPORT_EMAIL}</a></li>
<li>Service Center: <a href="mailto:{config.SERVICE_CENTER_EMAIL or config.SUPPORT_EMAIL}">{config.SERVICE_CENTER_EMAIL or config.SUPPORT_EMAIL}</a></li>
</ul>
<p>Personal documents or sensitive credentials ni email lo pampakandi; configured private upload channel matrame use cheyandi.</p>"""

CORRECTIONS_HTML = f"""<p>studentup.in lo articles official notifications &amp; trusted sources aadharanga untayi. Emaina tappu dorikina:</p>
<ul>
<li><a href="mailto:{config.SUPPORT_EMAIL}">{config.SUPPORT_EMAIL}</a> ki post link + wrong detail pampandi</li>
<li>Team verify chesi correction note/update chestundi; response time workload batti untundi</li>
<li>Dates, fees, eligibility ki official website ni kuda confirm chesukondi</li>
</ul>
<p>Correction policy: <a href="/corrections-policy/">details chudandi</a>.</p>"""

EDITORIAL_HTML = f"""<p>studentup.in editorial standards — useful, source-backed and people-first content kosam.</p>
<h2>Content ela test</h2>
<ul>
<li>Official notifications &amp; trusted sources nunchi facts matrame; copied text kaadu</li>
<li>Dates/fees/eligibility verify cheyali; guessing banned</li>
<li>AI-assisted drafting + human review required before a draft is treated as final</li>
<li>Near-duplicate check: same topic revisit aithe merge/update, kotha thin page kaadu</li>
</ul>
<h2>Authors and corrections</h2>
<p>Configured author team bylines use chestundi. Mistakes report: <a href="mailto:{config.SUPPORT_EMAIL}">{config.SUPPORT_EMAIL}</a>.</p>"""

ADSENSE_PAGES = [
    ("Privacy Policy", "privacy-policy", PRIVACY_HTML),
    ("About Us", "about-us", ABOUT_HTML),
    ("Contact Us", "contact-us", CONTACT_HTML),
    ("Corrections Policy", "corrections-policy", CORRECTIONS_HTML),
    ("Editorial Policy", "editorial-policy", EDITORIAL_HTML),
]


def ensure_adsense() -> int:
    """AdSense preparation: policy pages + owner checklist; approval remains Google-side."""
    from .wordpress_client import WordPressClient

    print("\n========== GOOGLE ADSENSE APPROVAL CHECKLIST (v19) ==========")
    ok_all = True
    try:
        wp = WordPressClient()
        wp.check_connection()
        for title, slug, html in ADSENSE_PAGES:
            try:
                if wp.page_exists(slug):
                    print(f"[OK]     {title} page undi")
                else:
                    res = wp.create_page(title, html, slug)
                    print(f"[CREATE] {title} -> {res.get('link')}")
            except Exception as exc:  # noqa: BLE001 — network SSL errors tolidu
                ok_all = False
                print(f"[WARN]   {title}: {type(exc).__name__}")
    except Exception as exc:  # noqa: BLE001 — sandbox/server network variance
        ok_all = False
        print(f"[WARN] WP connect kaDU ({type(exc).__name__}) — pages manual ga create cheyandi")
    try:
        n = wp.published_count()
        if n >= 20:
            print(f"[INFO]   {n} published posts — content inventory check only; no fixed Google threshold")
        else:
            print(f"[INFO]   {n} published posts — continue building useful, original content; "
                  "Google has no code-verifiable fixed post-count threshold")
    except Exception as exc:  # noqa: BLE001 — best-effort (silent kaadu)
        log.debug("ensure_adsense skip: %s", exc)
    print("\n--- MANUAL CHECKS (bot cheyyaleru — mee browser/console lo) ---")
    for name, howto in [
        ("ads.txt", "https://studentup.in/ads.txt open chesi correct publisher ID verify (AdSense > Earn > Get code)"),
        ("Policy LINKS", "AUTO: run.py --setup — footer menu create+assign chesthundi (AdSense/Google News ki links mandatory)"),
        ("Originality", "Bot NO-COPY hard floor (72%) auto enforce; manual posts ki same rule paalinchandi"),
        ("Human eye", "Rozu okko auto-post human ga chaduvandi — 'AI at scale, unedited' Google demotion trigger #1"),
        ("Dead/expired links", "Month ki okkaru expired posts/links clean cheyandi (auto-refresh undi kaani manual spot-check best)"),
        ("No self-clicks", "mee own ads ni eppudu click cheyadraku — ban risk"),
        ("Traffic/posts", "useful original content + real organic traffic; no fixed post-count guarantee"),
        ("Search Console", "Sitemap submitted aa check (/sitemap_index.xml); Coverage + Core Web Vitals warnings fix"),
        ("Google News", "Bylines + Editorial Policy page LIVE ayaka Publisher Center lo site add cheyandi (news traffic = notification site oxygen)"),
        ("Auto Ads audit", "AdSense approved taraivata auto-ads placements month ki okkaru review — above-fold stack + interstitials avoid"),
        ("RPM reality", "Education/govt-jobs IN audience = moderate CPC; volume + session depth meeda focus (per-click value kaadu)"),
    ]:
        print(f"  [ ] {name}: {howto}")
    print("===============================================================\n")
    return 0 if ok_all else 1


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
    parser.add_argument("--approval-poll", action="store_true",
                        help="v74: Telegram approvals — okka poll pass (cron mode; "
                             "shared hosting lo */5 min cron; VPS lo daemon ki badulu)")
    parser.add_argument("--revenue-check", action="store_true",
                        help="revenue setup audit — em missing o cheptundi")
    parser.add_argument("--ad-advisor", action="store_true",
                        help="v57: eppudu e ad-network ki apply cheyyali (auto suggest)")
    parser.add_argument("--traffic-csv", default="", metavar="CSV",
                        help="GA4 CSV export -> logs/traffic.json (advisor kosam)")
    parser.add_argument("--traffic-views", default="", metavar="N",
                        help="advisor ki pageviews (10k / 25000) — data save avutundi")
    parser.add_argument("--traffic-sessions", default="", metavar="N", help="advisor ki sessions")
    parser.add_argument("--tier1", default="", metavar="SHARE",
                        help="Tier-1 traffic share 0-1 (0.5 = 50%%)")
    parser.add_argument("--gsc", default="", metavar="CSV",
                        help="Search Console queries CSV -> striking-distance opportunities")
    parser.add_argument("--doctor", action="store_true",
                        help="deployment health check — anni dependencies verify")
    parser.add_argument("--production-audit", action="store_true",
                        help="v30: production safety, consent, ads, plugins, theme, and legal audit")
    parser.add_argument("--service-center", action="store_true",
                        help="v31: preview/publish Student Internet Center services page")
    parser.add_argument("--content-audit", action="store_true",
                        help="v32: read-only audit of all published posts; no rewrite/no URL changes")
    parser.add_argument("--content-limit", type=int, default=500,
                        help="v32: maximum published posts to inspect (default: 500)")
    parser.add_argument("--google-audit", default="", metavar="URL",
                        help="v33: public HTML + PageSpeed mobile/desktop audit for a URL")
    parser.add_argument("--research-brief", default="", metavar="TOPIC_OR_URL",
                        help="v36: build a cited NotebookLM-ready source bundle")
    parser.add_argument("--research-urls", default="", metavar="FILE",
                        help="v36: optional file with checked public URLs, one per line")
    parser.add_argument("--research-limit", type=int, default=6, metavar="N",
                        help="v36: maximum public sources in the NotebookLM bundle")
    parser.add_argument("--research-year", type=int, default=0, metavar="YEAR",
                        help="v37: explicit target year; prevents mixing old/current cycles")
    parser.add_argument("--target-year", type=int, default=0, metavar="YEAR",
                        help="v37: target year for a source article, e.g. 2027")
    parser.add_argument("--notebooklm-brief", default="", metavar="FILE",
                        help="v36: use an editor-verified NotebookLM brief with --url")
    parser.add_argument("--deep-research", default="", metavar="TOPIC_OR_URL",
                        help="v44: DEEP POST ENGINE — source tiering + deep fact "
                             "extraction + cross-verification + confidence report "
                             "(--research-urls FILE / --research-limit N / "
                             "--research-year Y / --notebooklm-brief FILE / "
                             "--deep for NotebookLM passes 6-8)")
    parser.add_argument("--deep", action="store_true",
                        help="v44: emit extended NotebookLM prompt (passes 6-8: "
                             "year-over-year, ELI-12, gap priority)")
    parser.add_argument("--top-post", default="", metavar="KEYWORD",
                        help="v38: TOP POST BLUEPRINT — title/meta/outline/keywords/"
                             "schema/E-E-A-T plan for an exact search phrase "
                             "(save chesi chupistundi: output/top-posts/)")
    parser.add_argument("--top-post-category", default="", metavar="CAT",
                        help="v38: blueprint category override (default: auto)")
    parser.add_argument("--publish-top-post", action="store_true",
                        help="v38: blueprint + article generate chesi publish "
                             "(DEFAULT_POST_STATUS=draft tho review flow)")
    parser.add_argument("--top-post-plan", action="store_true",
                        help="v38: keyword domination calendar (pillar + support "
                             "posts, cluster balanced) — CSV/MD/JSON export")
    parser.add_argument("--top-post-days", type=int, default=0, metavar="N",
                        help="v38: plan length in days (default TOP_POST_PLAN_DAYS=90)")
    parser.add_argument("--top-post-per-day", type=int, default=1, metavar="N",
                        help="v38: posts per day in the plan (1-5)")
    parser.add_argument("--keyword-universe", action="store_true",
                        help="v38: ANNI keywords (9000+) stats + CSV/JSON export "
                             "(output/keywords/keyword_universe.csv)")
    parser.add_argument("--score-post", default="", metavar="FILE",
                        help="v38: any HTML/text file ni Top Post Score tho measure "
                             "(30+ checks + fixes)")
    parser.add_argument("--score-keyword", default="", metavar="KEYWORD",
                        help="v38: keyword for --score-post")
    parser.add_argument("--ads", action="store_true",
                        help="v43: AD MANAGER — owner ads (college banners/shop/"
                             "services) inventory status + per-category slot plan")
    parser.add_argument("--rate-card", action="store_true",
                        help="v71: rate card (internal) — prices site meeda public ga levu; "
                             "ee card ni WhatsApp/Telegram lo personal ga deal cheyyadaniki vaadandi")
    parser.add_argument("--ads-demo", action="store_true",
                        help="v43: AD MANAGER — visible ad placement preview "
                             "(output/ads-preview.html — browser lo open cheyandi)")
    parser.add_argument("--deploy-check", action="store_true",
                        help="v41: deploy readiness — python/deps/files/disk/env + "
                             "artifacts (server SSH lo; v74: portal boot ledu — "
                             "cron-only bot)")
    parser.add_argument("--test-all", action="store_true",
                        help="v41: ANNI suites okate command tho run chey "
                             "(--test-only NAME tho okka suite; CI idi ne run "
                             "chestundi)")
    parser.add_argument("--test-only", default="", metavar="NAME",
                        help="v41: --test-all tho okka suite matrame (ex: v41)")
    parser.add_argument("--site-audit", action="store_true",
                        help="v41: full site audit (21 problem classes — thin/junk "
                             "content, wrong category, PII, tags, timezone) + report")
    parser.add_argument("--site-audit-fix", action="store_true",
                        help="v41: audit + SAFE autofix (default dry-run)")
    parser.add_argument("--site-audit-apply", action="store_true",
                        help="v41: fixes ni nijamga apply chey (dry-run kaadu)")
    parser.add_argument("--site-audit-trash", action="store_true",
                        help="v41: demo/junk pages ni trash cheyyadaniki permission")
    parser.add_argument("--site-audit-action", default="",
                        help="v41: only ee fixers run chey (comma list, ex: "
                             "strip_pii,strip_shortcode)")
    parser.add_argument("--site-audit-snapshot", default="", metavar="FILE",
                        help="v41: offline audit from snapshot JSON "
                             "(leda 'demo' — engine proof, network avasaram ledu)")
    parser.add_argument("--site-audit-save", default="", metavar="FILE",
                        help="v41: fetched site data ni JSON snapshot ga save chey "
                             "(tarvata offline/CI audit ki)")
    parser.add_argument("--trends", action="store_true",
                        help="Google Trends India education trends chupinchindi")
    parser.add_argument("--pin-check", action="store_true",
                        help="Pin-to-pin certificate proof (67 checks, offline)")
    parser.add_argument("--index-now", default="", metavar="URL",
                        help="v68: IndexNow + Google Indexing API (JobPosting) ki URL submit")
    parser.add_argument("--index-status", action="store_true",
                        help="v68: instant-indexing configuration status (SA key · openssl · key file)")
    parser.add_argument("--index-key-gen", action="store_true",
                        help="v68: kotha IndexNow key generate (hex) + .env lo pettalsina line")
    parser.add_argument("--trends-queue", action="store_true",
                        help="v65: --trends tho paatu Suggest capture + topic queue")
    parser.add_argument("--rm100", action="store_true",
                        help="Rank Math 100 engine proof (imperfect draft → 100 breakdown)")
    parser.add_argument("--readiness", action="store_true",
                        help="v62: TOP WEBSITE READINESS — content/SEO/ads/automation/site score")
    parser.add_argument("--push-theme-data", action="store_true",
                        help="v61: bot data (breaking/proof/deadline/house ads) → WP theme REST")
    parser.add_argument("--guardian", action="store_true",
                        help="v60: SITE GUARDIAN — site/UI/SEO/ads/feed/storage full check")
    parser.add_argument("--guardian-notify", action="store_true",
                        help="v60: guardian report ni Telegram ki kuda pampu")
    parser.add_argument("--breaking-feed", action="store_true",
                        help="v59: బ్రేకింగ్ న్యూస్ feed build (radar → preview/data/breaking.json)")
    parser.add_argument("--breaking-from", default="", metavar="FILE",
                        help="v59: breaking feed ni JSON file nunchi generate (offline/test)")
    parser.add_argument("--radar", action="store_true",
                        help="breaking-news radar: TS+AP districts + grid + watch (queue+post)")
    parser.add_argument("--sources", action="store_true",
                        help="official sources grid (105 sources) list chupinchu")
    parser.add_argument("--rebuild-hubs", action="store_true",
                        help="authority hub pages: one per exam, auto-linked (weekly also auto)")
    parser.add_argument("--setup", action="store_true",
                        help="FULL WordPress site setup: audit + auto-fix settings, "
                             "footer menu, category SEO, robots/sitemap checks (add --dry-run to preview)")
    parser.add_argument("--plugins", action="store_true",
                        help="v28: install/activate only the reviewed plugin stack "
                             "(add --dry-run to preview)")
    parser.add_argument("--theme-audit", action="store_true",
                        help="v28: read-only active-theme audit; never switches themes")
    parser.add_argument("--adsense-kit", action="store_true",
                        help="v28: validate ADSENSE_CLIENT_ID and install/update "
                             "the site-wide Auto Ads loader widget")
    parser.add_argument("--ensure-adsense", action="store_true",
                        help="AdSense approval: mandatory pages auto-create + full checklist")
    parser.add_argument("--keywords", action="store_true",
                        help="keyword dominance engine: matrix + coverage + autocomplete")
    parser.add_argument("--polish", action="store_true",
                        help="v24: site-wide design kit CSS via footer widget — "
                             "colors/typography/tables/cards on ALL pages. "
                             "Idempotent; re-run after theme changes.")
    parser.add_argument("--quiz", action="store_true",
                        help="v26: generate today's Daily Quiz (auto topic rotation) "
                             "and publish")
    parser.add_argument("--quiz-topic", default="",
                        help="custom quiz topic (Telugu lo cheppina ok — "
                             "e.g. --quiz-topic \"స్కాలర్‌షిప్‌ల మీద క్విజ్\")")
    parser.add_argument("--quiz-level", type=int, default=0,
                        help="quiz difficulty 1-4 (default: day-based auto ramp)")
    parser.add_argument("--quiz-questions", type=int, default=0,
                        help="number of questions (default: QUIZ_QUESTIONS)")
    parser.add_argument("--quiz-kit", action="store_true",
                        help="v26: install/update site-wide quiz engine "
                             "(CSS+JS footer widget) — quiz UI, timers, scoring")
    args = parser.parse_args()

    _setup_logging()

    if args.status:
        return show_status()
    if args.check_wp:
        return check_wp()
    if args.notify_test:
        return notify_test()
    if args.approval_poll:
        from . import approval_bot

        return approval_bot.main_once()
    if args.revenue_check:
        return revenue_check()
    if args.gsc:
        return gsc_opportunities(args.gsc)
    if args.doctor:
        return doctor()
    if args.production_audit:
        from . import production_audit

        return production_audit.run()
    if args.service_center:
        return service_center_setup(dry=args.dry_run, force=args.force)
    if args.content_audit:
        return content_audit_run(limit=max(1, min(args.content_limit, 5000)))
    if args.rate_card:
        from . import rate_card as rc

        print(rc.as_markdown())
        print("\n⚠️  Public site lo prices chupinchakandi (v71 rule) — personal ga deal cheyandi.")
        return 0
    if args.ads or args.ads_demo:
        from . import ad_manager

        return ad_manager.run_cli("demo" if args.ads_demo else "status")
    if args.google_audit:
        return google_audit_run(args.google_audit)
    if args.deep_research:
        from . import deep_research

        return deep_research.run_cli(
            args.deep_research, url_file=args.research_urls,
            limit=max(1, args.research_limit), target_year=args.research_year,
            notebooklm_brief=args.notebooklm_brief,
            deep_prompt=args.deep)
    if args.research_brief:
        return research_brief_run(args.research_brief, args.research_urls,
                                  args.research_limit, args.research_year)
    if args.top_post:
        return top_post_run(args.top_post, category=args.top_post_category,
                            publish=args.publish_top_post, mock=args.mock,
                            dry_run=args.dry_run)
    if args.top_post_plan:
        return top_post_plan_run(args.top_post_days,
                                 per_day=args.top_post_per_day)
    if args.keyword_universe:
        return keyword_universe_view()
    if args.score_post:
        return score_post_run(args.score_post, args.score_keyword)
    if args.deploy_check:
        from . import deploy_check

        return deploy_check.run_deploy_check()
    if args.test_all:
        return test_all_run(only=args.test_only)
    if args.site_audit or args.site_audit_fix:
        return site_audit_run(fix=args.site_audit_fix, apply=args.site_audit_apply,
                              allow_trash=args.site_audit_trash,
                              actions=args.site_audit_action,
                              snapshot=args.site_audit_snapshot,
                              save=args.site_audit_save)
    if getattr(args, "index_key_gen", False):
        import secrets

        key = secrets.token_hex(16)
        print("=" * 62)
        print("  🔑 INDEXNOW KEY (kotha)")
        print("=" * 62)
        print(f"  {key}")
        print("\n  .env lo ee line pettandi:")
        print(f"  INDEXNOW_KEY={key}")
        print("\n  Tarvata: python run.py --push-theme-data  (theme /" + key + ".key serve chestundi)")
        print("           python run.py --index-status     (verify)")
        print("=" * 62)
        return 0
    if getattr(args, "index_status", False):
        from . import indexing

        st = indexing.status()
        print("=" * 62)
        print("  🔎 INSTANT INDEXING (v68)")
        print("=" * 62)
        print(f"  IndexNow key      : {'set ✔' if st['indexnow_key'] else 'ledu (INDEXNOW_KEY set cheyandi)'}")
        print(f"  Google SA         : {'configured ✔ ' + st['client_email'] if st['configured'] else 'ledu (GOOGLE_INDEXING_SA_JSON / GOOGLE_INDEXING_SA)'}")
        print(f"  RS256 signing     : {st['signing']} (openssl: {st['openssl']})")
        print("  IndexNow key file : theme /<key>.key serve chestundi (StudentUp → Advanced)")
        print("=" * 62)
        return 0
    if getattr(args, "index_now", ""):
        from . import indexnow, indexing

        url = args.index_now
        st = indexing.status()
        ok_bing = indexnow.submit(url)
        ok_google = indexing.publish_url(url, "URL_UPDATED") if st["configured"] else False
        print("=" * 62)
        print(f"  URL: {url}")
        print(f"  IndexNow (Bing/Yandex): {'✔ submitted' if ok_bing else '✘ skip (key ledu leda fail)'}")
        print(f"  Google Indexing API   : {'✔ submitted' if ok_google else '✘ skip (SA ledu leda JobPosting page kaadu)'}")
        print("=" * 62)
        return 0 if (ok_bing or ok_google) else 0
    if args.trends:
        rc = trends_check()
        if getattr(args, "trends_queue", False):
            trends_run(queue=True)
        return rc
    if args.sources:
        return sources_view()
    if args.keywords:
        return keywords_view()
    if args.ensure_adsense:
        return ensure_adsense()
    if args.setup:
        from . import site_setup

        return site_setup.run_setup(dry=args.dry_run)
    if args.plugins:
        from . import site_setup

        return site_setup.run_plugins(dry=args.dry_run)
    if args.theme_audit:
        from . import site_setup

        return site_setup.run_theme_audit()
    if args.adsense_kit:
        from . import site_setup

        return site_setup.run_adsense_kit(dry=args.dry_run)
    if args.polish:
        from . import design_kit
        from .wordpress_client import WordPressClient
        wp = WordPressClient()
        try:
            wp.check_connection()
        except Exception as exc:  # noqa: BLE001
            print(f"WP connect kaDU ({str(exc)[:70]}...) — "
                  "Appearance→Customize→Additional CSS lo paste cheyandi:")
            print(design_kit.build_css())
            return 0
        status, detail = design_kit.install(wp)
        f_stat, f_detail = design_kit.broken_footer_token(wp)
        print(f"🎨 Design kit: {status} — {detail}")
        print(f"🦶 Footer token: {f_stat} — {f_detail}")
        # v26: quiz engine site-wide CSS+JS (same widget mechanism)
        try:
            from . import quiz_engine
            q_stat, q_detail = quiz_engine.install(wp)
            print(f"🎯 Quiz engine: {q_stat} — {q_detail}")
        except Exception as exc:  # noqa: BLE001
            print(f"🎯 Quiz engine failed (harmless): {str(exc)[:100]}")
        return 0

    if args.ad_advisor or args.traffic_csv or args.traffic_views:
        from . import ad_advisor

        if args.traffic_csv:
            try:
                info = ad_advisor.import_ga4_csv(args.traffic_csv)
            except (OSError, ValueError) as exc:
                print(f"❌ traffic CSV chadavaleka poyindi: {exc}")
                return 6
            print(f"📈 traffic import: {info['pageviews']:,} pageviews · "
                  f"{info['sessions']:,} sessions · Tier-1 {int(info['tier1_share'] * 100)}% "
                  f"({info['rows']} rows) → {info['path']}")
        views = ad_advisor.parse_views(args.traffic_views) if args.traffic_views else 0
        sessions = ad_advisor.parse_views(args.traffic_sessions) if args.traffic_sessions else 0
        tier1 = None
        if args.tier1:
            try:
                tier1 = float(args.tier1)
                tier1 = tier1 / 100.0 if tier1 > 1 else tier1
            except ValueError:
                print("❌ --tier1 number ga undali (0.5 leda 50)")
                return 6
        result = ad_advisor.advice(pageviews=views or None,
                                   sessions=sessions or None, tier1=tier1)
        print(ad_advisor.render(result))
        return 0

    if args.quiz_kit:
        from . import quiz_engine
        from .wordpress_client import WordPressClient
        wp = WordPressClient()
        try:
            wp.check_connection()
        except Exception as exc:  # noqa: BLE001
            print(f"WP connect kaDU ({str(exc)[:70]}...) — "
                  "Appearance→Widgets lo text widget lo paste cheyandi:")
            print(quiz_engine.build_widget_html())
            return 0
        status, detail = quiz_engine.install(wp)
        print(f"🎯 Quiz engine: {status} — {detail}")
        return 0

    if args.rebuild_hubs:
        from . import hubs as _hubs

        rows = _hubs.rebuild_hubs()
        print(f"{len(rows)} hub pages upserted:")
        for r in rows:
            print(f"  • {r['exam']:<22} {r.get('posts', '?')} posts -> {r.get('link', r['slug'])}")
        return 0
    if getattr(args, "pin_check", False):
        return pin_check_run()
    if getattr(args, "trends", False):
        return trends_run(queue=not getattr(args, "no_queue", False))
    if getattr(args, "rm100", False):
        return rm100_run()
    if args.readiness:
        return readiness_run()
    if args.push_theme_data:
        return push_theme_data(dry_run=args.dry_run)
    if args.guardian or args.guardian_notify:
        return guardian_run(notify=args.guardian_notify)
    if args.breaking_feed or args.breaking_from:
        return breaking_feed_run(from_file=args.breaking_from)
    if args.radar:
        return radar_run(process_posts=not args.dry_run)
    try:
        src = args.add_source or args.url
        listicle_arg = args.listicle or ""
        if listicle_arg == "auto":
            listicle_arg = ""  # bot idea pick chestundi
        return run(dry_run=args.dry_run, force=args.force, mock=args.mock,
                   category=args.category, source_url=src,
                   process_queue=args.process_queue, update_id=args.update,
                   listicle=listicle_arg, auto_refresh_n=args.auto_refresh,
                   quiz=args.quiz, quiz_topic=args.quiz_topic,
                   quiz_level=args.quiz_level,
                   quiz_questions=args.quiz_questions,
                   notebooklm_brief_file=args.notebooklm_brief,
                   target_year=args.target_year)
    except wordpress_client.WordPressAuthError as exc:
        log.error("%s", exc)
        return 3
    except (wordpress_client.WordPressError, gemini_client.GeminiError) as exc:
        log.error("Publishing failed: %s", exc)
        return 4
    except Exception:
        log.exception("Unexpected error")
        return 5
