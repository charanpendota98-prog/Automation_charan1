"""Shared publish pipeline — run.py & Telegram approval bot okari okaru vadatam.

publish_article(): SEO enhance + internal links + featured image +
Rank Math meta + WP create + state + notification.
create_from_source(url): fetch source -> Gemini 100% original rewrite -> publish.
"""

import logging
from datetime import date
from pathlib import Path
from typing import Dict, Optional

from . import config, gemini_client, image_gen, notifier, seo, sources, state
from .wordpress_client import WordPressClient, WordPressError

log = logging.getLogger("autoblog.pipeline")


def publish_article(article: Dict, day: Optional[date] = None) -> Dict:
    """Full publish flow for a generated article dict. Returns WP result."""
    wp = WordPressClient()
    wp.check_connection()

    category_id = wp.get_or_create_term(article["category"], "categories")
    tag_ids = [wp.get_or_create_term(t, "tags") for t in article["tags"]]

    # --- SEO: internal links + TOC + keyword intro + external links ---
    recent = wp.get_recent_published(per_page=8)
    same_cat = [p for p in recent if category_id in p.get("categories", [])]
    internal = (same_cat or recent)[:4]
    final_html = seo.enhance(
        article["content_html"],
        focus_keyword=article.get("focus_keyword", ""),
        internal_links=[{"link": p["link"], "title": p["title"]} for p in internal],
        external_links=article.get("external_links", []),
    )

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
    try:
        notifier.notify_new_post(article, result)
    except Exception:
        log.exception("Notification failed (post safe ga save ayyindi)")
    return result


def create_from_source(url: str, mock: bool = False) -> Dict:
    """Vere site URL -> 100% original SEO article -> draft post."""
    if not sources.is_valid_source_url(url):
        raise ValueError("URL valid kadu (http/https link ivvandi)")

    if state.source_done(config.STATE_PATH, url):
        raise ValueError("Ee URL already process chesayi — duplicate!")

    log.info("Source fetch chestunnanu: %s", url)
    src = sources.fetch_source(url)
    log.info("Source ready: %s (%d chars)", src.title[:60], len(src.text))

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
            "external_links": [{"text": "Official Site", "url": "https://www.gov.in"}],
            "source_url": url,
            "source_title": src.title,
        }
    else:
        recent = state.recent_titles(config.STATE_PATH, limit=30)
        article = gemini_client.generate_article_from_source(src, recent, date.today().year)

    # slug safe ga
    from .main import _safe_slug
    article["slug"] = _safe_slug(article.get("slug", ""), article["title"])
    article.setdefault("focus_keyword", "")
    article.setdefault("external_links", [])

    return publish_article(article)
