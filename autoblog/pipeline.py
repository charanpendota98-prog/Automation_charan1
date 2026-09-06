"""Shared publish pipeline — run.py & Telegram approval bot okari okaru vadatam.

publish_article(): SEO enhance + internal links + featured image +
Rank Math meta + WP create + state + notification.
create_from_source(url): fetch source -> Gemini 100% original rewrite -> publish.
"""

import logging
from datetime import date
from pathlib import Path
from typing import Dict, Optional
from urllib.parse import urlparse

from . import config, gemini_client, image_gen, notifier, research, seo, sources, state, validator
from .notifier import esc, send_telegram
from .wordpress_client import WordPressClient, WordPressError

log = logging.getLogger("autoblog.pipeline")


def publish_article(article: Dict, day: Optional[date] = None) -> Dict:
    """Full publish flow for a generated article dict. Returns WP result."""
    wp = WordPressClient()
    wp.check_connection()

    # --- QA step 1: HTML sanitize (Gemini bad tags strip) ---
    article["content_html"] = validator.sanitize_html(article["content_html"])

    category_id = wp.get_or_create_term(article["category"], "categories")
    tag_ids = [wp.get_or_create_term(t, "tags") for t in article["tags"]]

    # --- SEO: quick answer + internal links + TOC + schema ---
    recent = wp.get_recent_published(per_page=8)
    same_cat = [p for p in recent if category_id in p.get("categories", [])]
    internal = (same_cat or recent)[:4]
    today_str = (day or date.today()).isoformat()
    final_html = seo.enhance(
        article["content_html"],
        focus_keyword=article.get("focus_keyword", ""),
        internal_links=[{"link": p["link"], "title": p["title"]} for p in internal],
        external_links=article.get("external_links", []),
        quick_answer=article.get("quick_answer", ""),
        faq=article.get("faq", []),
        date_str=today_str,
        slug=article["slug"],
        title=article["title"],
        description=article["meta_description"],
        category=article.get("category", ""),
        source_domains=article.get("_source_domains"),
    )

    # --- QA step 2: validation score + originality proof ---
    qa = validator.validate_article(article, final_html)
    article["_qa"] = qa
    if article.get("_source_texts"):
        article["_orig"] = validator.originality_score(
            final_html, article["_source_texts"])
    log.info("QA score %s/100 (words=%d) originality=%s%% issues=%s",
             qa["score"], qa["words"], article.get("_orig", "n/a"),
             qa["issues"][:3] or "none")

    # --- featured image (alt text lo focus keyword) ---
    image_path = Path(config.OUTPUT_DIR / "images" / f"{article['slug']}.jpg")
    media_id = None
    if config.IMAGE_ENABLED:
        fk = article.get("focus_keyword") or article["banner_text"]
        year = article.get("year", date.today().year)
        if image_gen.generate_featured_image(article["banner_text"], article["category"], image_path):
            media_id = wp.upload_media(
                image_path,
                title=article["title"],
                alt_text=f"{fk} – {article['category']} {year} | studentup.in",
            )

    # --- Rank Math meta (plugin active unte) ---
    meta = None
    if config.RANK_MATH_META_ENABLED:
        meta = seo.rankmath_meta(
            focus_keyword=article.get("focus_keyword", article["title"][:60]),
            description=article["meta_description"],
            seo_title=article.get("seo_title") or article["title"],
            secondary_keywords=article.get("secondary_keywords", []),
        )

    result = wp.create_post(
        title=article["title"],
        content_html=final_html,
        slug=article["slug"],
        category_id=category_id,
        tag_ids=tag_ids,
        excerpt=article["meta_description"],
        media_id=media_id,
        meta=meta,
    )
    state.record_post(config.STATE_PATH, article["title"], article["slug"],
                      article["category"], result["link"], result["status"])
    state.bump_today_count(config.STATE_PATH, day or date.today())
    if article.get("source_url"):
        state.mark_source_done(config.STATE_PATH, article["source_url"], result.get("id"))

    log.info("POST CREATED ✔ id=%s status=%s link=%s",
             result.get("id"), result.get("status"), result.get("link"))
    if result.get("status") == "publish":
        _after_publish_push(article, result)
    try:
        notifier.notify_new_post(article, result)
    except Exception:
        log.exception("Notification failed (post safe ga save ayyindi)")
    return result


def _after_publish_push(article: Dict, result: Dict) -> None:
    """Publish ayyaka instant traffic/indexing push (best-effort)."""
    # 1) IndexNow (Bing/Yandex instant indexing)
    try:
        from . import indexnow

        if indexnow.submit(result.get("link", "")):
            article["_indexnow"] = True
    except Exception:
        log.exception("IndexNow push failed")
    # 2) Telegram channel auto-post (instant traffic + social signal)
    try:
        if config.TELEGRAM_CHANNEL_CHAT_ID:
            qa = article.get("_qa") or {}
            send_telegram(
                f"🆕 <b>{esc(article['title'])}</b>\n\n"
                f"{esc((article.get('meta_description') or '')[:180])}\n\n"
                f"🔗 {esc(result.get('link', ''))}\n"
                f"📊 QA {qa.get('score', '-')}/100 · ~{qa.get('reading_min', '-')} min read",
                chat_id=config.TELEGRAM_CHANNEL_CHAT_ID,
            )
    except Exception:
        log.exception("Channel auto-post failed")


def create_from_source(url: str, mock: bool = False) -> Dict:
    """Vere site URL -> 100% original SEO article -> draft post."""
    if not sources.is_valid_source_url(url):
        raise ValueError("URL valid kadu (http/https link ivvandi)")

    if state.source_done(config.STATE_PATH, url):
        raise ValueError("Ee URL already process chesayi — duplicate!")

    log.info("Source fetch chestunnanu: %s", url)
    src = sources.fetch_source(url)
    log.info("Source ready: %s (%d chars)", src.title[:60], len(src.text))

    # --- multi-source research: internet lo same topic articles ---
    extras, competitor_titles = [], []
    if config.RESEARCH_ENABLED and not mock:
        try:
            extras, competitor_titles = research.research_topic(
                src, config.RESEARCH_MAX_SOURCES)
            if extras:
                log.info("Research: +%d extra sources (MERGE & BEAT mode)", len(extras))
            else:
                log.info("Research: extra sources levu — primary source tho rewrite")
        except Exception:
            log.exception("Research step failed — primary source tho continue")

    if mock:
        article = {
            "title": f"{src.title[:80]} – Complete Guide 2026 (Original)",
            "slug": "src-" + src.title.lower().replace(" ", "-")[:30],
            "meta_description": f"{src.title[:100]} — Telugu lo complete details.",
            "tags": ["2026", "Students", "Telugu", "Guide", "News"],
            "banner_text": "Students Guide 2026",
            "content_html": (
                "<p>Ee article source nunchi facts teesi original ga "
                f"rayabadda test article. Source: {src.title}</p>"
                "<h2>Key Details</h2><ul><li>Point one</li><li>Point two</li></ul>"
                "<h2>Process</h2><ol><li>Step one</li><li>Step two</li></ol>"
                "<h2>FAQ</h2><h3>Question?</h3><p>Answer</p>"
            ),
            "category": "Education News",
            "model": "mock",
            "focus_keyword": "test guide 2026",
            "seo_title": "Test Guide 2026 – Complete Details",
            "secondary_keywords": ["test guide details", "2026 guide telugu"],
            "quick_answer": ("Test guide 2026 gurinchi menu thelisi untundi — "
                             "ee quick answer featured snippet test kosam."),
            "faq": [
                {"question": "Ee guide em gurinchi?", "answer": "Test guide gurinchi."},
                {"question": "Ela apply cheyali?", "answer": "Online lo apply cheyali."},
            ],
            "external_links": [{"text": "Official Site", "url": "https://www.gov.in"}],
            "source_url": url,
            "source_title": src.title,
        }
    else:
        recent = state.recent_titles(config.STATE_PATH, limit=30)
        article = gemini_client.generate_article_from_source(
            src, recent, date.today().year, extras=extras,
            competitor_titles=competitor_titles,
        )
        # --- originality guard: 70% kante takkuva aite OKKO regenerate ---
        source_texts = [src.text] + [e.text for e in extras]
        article["content_html"] = validator.sanitize_html(article["content_html"])
        orig = validator.originality_score(article["content_html"], source_texts)
        if orig < 70.0:
            log.warning("Originality %.1f%% takkuva — inko sari regenerate", orig)
            try:
                retry_article = gemini_client.generate_article_from_source(
                    src, recent, date.today().year, extras=extras,
                    competitor_titles=competitor_titles,
                )
                retry_article["content_html"] = validator.sanitize_html(
                    retry_article["content_html"])
                retry_orig = validator.originality_score(
                    retry_article["content_html"], source_texts)
                if retry_orig > orig:
                    log.info("Regenerate better: %.1f%% -> %.1f%%", orig, retry_orig)
                    article, orig = retry_article, retry_orig
            except gemini_client.GeminiError:
                log.exception("Regenerate failed — first version e continue")

    # --- QA data (notification + trust box kosam) ---
    article["_source_texts"] = [src.text] + [e.text for e in extras]
    article["_source_domains"] = [
        d for d in [urlparse(src.url).netloc.replace("www.", "")]
        + [urlparse(e.url).netloc.replace("www.", "") for e in extras]
    ]

    # slug safe ga + new fields default
    from .main import _safe_slug
    article["slug"] = _safe_slug(article.get("slug", ""), article["title"])
    article.setdefault("focus_keyword", "")
    article.setdefault("external_links", [])
    article.setdefault("secondary_keywords", [])
    article.setdefault("quick_answer", "")
    article.setdefault("faq", [])
    article.setdefault("seo_title", "")

    return publish_article(article)
