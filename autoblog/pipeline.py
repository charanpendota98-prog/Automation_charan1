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
from .wordpress_client import WordPressClient

log = logging.getLogger("autoblog.pipeline")

# ---------------------------------------------------------------- auto category

CATEGORY_RULES = [
    # live-site categories (v14) — specific rules first (tie-break priority)
    ("TS Govt Jobs", ["tspsc", "telangana", "ts police", "ts genco", "transco",
                      "తెలంగాణ", "gurukul", "tgpsc"]),
    ("AP Govt Jobs", ["appsc", "andhra", "ap police", "apsrtc", "ap genco",
                      "ఆంధ్రప్రదేశ్", "ap dsc", "grama sachivalayam"]),
    ("Central Govt Jobs", ["ssc", "upsc", "rrb", "ibps", "sbi po", "sbi clerk",
                           "india post", "agniveer", "job", "vacancy",
                           "recruitment", "bharti", "notification", "posts",
                           "ఉద్యోగ", "నియామక", "ఖాళీల", "si ", "constable"]),
    ("Software Jobs", ["software", "developer", "engineer", "it jobs",
                       "coding", "full stack", "data analyst", "devops",
                       "testing"]),
    ("Private Jobs", ["tcs", "infosys", "wipro", "hcl", "cognizant",
                      "accenture", "fresher", "off campus", "private", "mnc"]),
    ("Part Time Jobs", ["part time", "part-time", "work from home",
                        "freelance", "data entry", "tutor"]),
    ("Walkin Jobs", ["walkin", "walk-in", "walk in", "direct interview"]),
    ("Hall Tickets", ["admit card", "hall ticket", "హాల్ టికెట్", "call letter"]),
    ("Scholarships", ["scholarship", "fellowship", "nsp", "fee reimbursement",
                      "స్కాలర్", "రుసుము", "pragati", "saksham", "yasasvi"]),
    ("Results", ["result", "ఫలిత", "marks list", "manabadi", "grade",
                 "cutoff", "cut-off", "answer key"]),
    ("Internships", ["internship", "ఇంటర్న్"]),
    ("Online Education", ["admission", "counselling", "counseling", "web options",
                          "dost", "eamcet", "eapcet", "icet", "pgecet", "ప్రవేశ",
                          "online mba", "online degree", "course", "syllabus",
                          "preparation", "study plan", "exam date", "పరీక్ష"]),
]


def classify_category(title: str, text: str = "") -> str:
    """URL mode lo category auto-detect (Telugu + English keywords)."""
    blob = f"{title} {title} {text[:600]}".lower()
    best, best_hits = "Online Education", 0
    for cat, words in CATEGORY_RULES:
        hits = sum(1 for w in words if w in blob)
        if hits > best_hits:
            best, best_hits = cat, hits
    return best


def _hygiene(article: Dict) -> Dict:
    """Chinna chinna quality fixes publish mundhe."""
    # title too long -> seo_title use cheyi (Rank Math 60-75 chars ideal)
    title = article.get("title", "")
    seo_title = article.get("seo_title", "")
    if len(title) > 85 and seo_title and 20 <= len(seo_title) <= 85:
        article["title"] = seo_title
    # tags: dedupe + max 32 chars + max 8
    seen, tags = set(), []
    for t in article.get("tags", []):
        t = str(t).strip()[:32]
        if t and t.lower() not in seen:
            seen.add(t.lower())
            tags.append(t)
    article["tags"] = tags[:8]
    # meta description fallback: quick_answer or first para nunchi
    md = (article.get("meta_description") or "").strip()
    if len(md) < 120:
        base = article.get("quick_answer") or validator.strip_tags(
            article.get("content_html", ""))
        base = " ".join(base.split())
        article["meta_description"] = (base[:155].rsplit(" ", 1)[0]) if base else md
    return article


def publish_article(article: Dict, day: Optional[date] = None) -> Dict:
    """Full publish flow for a generated article dict. Returns WP result."""
    wp = WordPressClient()
    wp.check_connection()

    # --- QA step 1: HTML sanitize (Gemini bad tags strip) ---
    article["content_html"] = validator.sanitize_html(article["content_html"])
    article = _hygiene(article)

    category_id = wp.get_or_create_term(article["category"], "categories")
    tag_ids = [wp.get_or_create_term(t, "tags") for t in article["tags"]]

    # --- SEO: quick answer + internal links + TOC + schema ---
    recent = wp.get_recent_published(per_page=8)
    same_cat = [p for p in recent if category_id in p.get("categories", [])]
    internal = (same_cat or recent)[:4]
    # Money-page strategy: traffic posts nunchi high-CPC posts ki link priority
    from . import monetize as _mz

    internal = _mz.prioritize_money_pages(internal)[:4]
    # Internal-link fallback: kotha site lo published posts levu ->
    # category archive links istundi (Rank Math internal-link check pass)
    if len(internal) < 2:
        cat_link = wp.get_term_link(category_id, "categories")
        if cat_link:
            internal.append({"link": cat_link,
                             "title": f"{article['category']} – Latest Articles"})
        if len(internal) < 2:
            internal.append({"link": f"{config.WP_SITE}/", "title": "studentup.in – Home"})
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
        list_items=article.get("list_items") if article.get("article_type") == "listicle" else None,
    )
    # in-content ads (viewability-optimized slots; AD_SHORTCODE set unte matrame)
    if config.AD_SHORTCODE:
        final_html = seo.insert_ad_shortcodes(
            final_html, config.AD_SHORTCODE,
            max_ads=config.MAX_AD_SLOTS, cls_safe=config.AD_CLS_WRAPPER)
    # revenue blocks: affiliate section + channel CTA (schema mundu insert)
    from . import monetize

    final_html = monetize.append_blocks(final_html, article)

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
            # disk full avvakunda — upload ayyaka local file delete
            if media_id and not config.KEEP_IMAGES:
                image_path.unlink(missing_ok=True)

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
                      article["category"], result["link"], result["status"],
                      qa_score=(article.get("_qa") or {}).get("score"),
                      orig_score=article.get("_orig"), wp_id=result.get("id"))
    state.bump_today_count(config.STATE_PATH, day or date.today())
    if article.get("source_url"):
        state.mark_source_done(config.STATE_PATH, article["source_url"], result.get("id"))
    try:
        state.meta_cleanup(config.STATE_PATH)  # purana rojuvella keys tidy
    except Exception:
        pass

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


def create_from_source(url: str, mock: bool = False, category: str = "") -> Dict:
    """Vere site URL -> 100% original SEO article -> draft post.

    category empty aite auto-classify (Telugu+English keywords tho).
    """
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
            "category": category or classify_category(src.title, src.text),
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
        if category:
            article["category"] = category
        elif article.get("category", "Education News") == "Education News":
            article["category"] = classify_category(
                f"{src.title} {article['title']}", src.text)
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

    # slug safe ga + Rank Math optimize (keyword tokens + stopwords)
    from .main import _safe_slug
    article["slug"] = seo.optimize_slug(
        _safe_slug(article.get("slug", ""), article["title"]),
        focus_keyword=article.get("focus_keyword", ""))
    article.setdefault("focus_keyword", "")
    article.setdefault("external_links", [])
    article.setdefault("secondary_keywords", [])
    article.setdefault("quick_answer", "")
    article.setdefault("faq", [])
    article.setdefault("seo_title", "")

    return publish_article(article)


# ------------------------------------------------------------------ update flow

def update_post(post_id: int, new_source_urls=None, mock: bool = False) -> Dict:
    """Already-published/draft post ni kotha info tho IMPROVE chesi update.

    Same URL (slug preserve) — Google lo freshness boost + SEO juice safe.
    new_source_urls: user ichina kotha source URLs (optional).
    Levu ante post title meeda auto web research chestundi.
    """
    wp = WordPressClient()
    wp.check_connection()
    post = wp.get_post(post_id)
    title = (post.get("title") or {}).get("raw") or (post.get("title") or {}).get("rendered", "")
    existing_html = (post.get("content") or {}).get("raw", "") or (post.get("content") or {}).get("rendered", "")
    slug = post.get("slug", "")
    link = post.get("link", "")
    existing_text = validator.strip_tags(existing_html)
    log.info("Update mode: post %s '%s' (%d chars)", post_id, title[:50], len(existing_text))

    # --- kotha sources gather ---
    extras = []
    from .sources import SourceArticle as SA

    for u in (new_source_urls or []):
        try:
            extras.append(sources.fetch_source(u))
        except Exception as exc:
            log.warning("New source fetch fail (%s): %s", u[:60], exc)
    if config.RESEARCH_ENABLED and not mock and len(extras) < 2:
        try:
            pseudo = SA(url=link or f"{config.WP_SITE}/?p={post_id}",
                        title=title, site_name="studentup.in", text="")
            more, _unused = research.research_topic(pseudo, config.RESEARCH_MAX_SOURCES)
            extras.extend(more)
        except Exception:
            log.exception("Auto research fail — manual sources tho continue")
    if not extras and not mock:
        raise ValueError("Kotha information dorakaledu — source URL ivvandi "
                         "or konchem rojulu tarvata try cheyandi")

    # --- generate updated version ---
    if mock:
        article = {
            "title": title,
            "slug": slug or "keep",
            "meta_description": f"{title[:100]} — updated version.",
            "tags": ["2026", "Students", "Telugu", "Guide"],
            "banner_text": "Updated Guide",
            "content_html": (
                "<p>Ee updated test article — kotha info merge ayyindi.</p>"
                "<h2>Key Details</h2><ul><li>Old point</li><li>Kotha point add ayyindi</li></ul>"
                "<h2>Process</h2><ol><li>Step one</li><li>Step two</li></ol>"
                "<h2>FAQ</h2><h3>Q?</h3><p>A</p>"
            ),
            "category": "Education News",
            "model": "mock",
            "focus_keyword": "test guide 2026",
            "secondary_keywords": ["update test"],
            "quick_answer": "Updated quick answer for the test.",
            "faq": [{"question": "Q?", "answer": "A"}],
            "update_notes": "• Kotha fee details add chesayi (test)",
        }
    else:
        fk = ""
        try:
            fk = (post.get("meta") or {}).get("rank_math_focus_keyword", "") or ""
            fk = fk.split(",")[0].strip()
        except Exception:
            pass
        article = gemini_client.generate_update(
            title, existing_text, fk, extras, date.today().year,
        )

    # identity preserve — URL marakudadu
    article["title"] = title
    article["slug"] = slug
    article["content_html"] = validator.sanitize_html(article["content_html"])
    article = _hygiene(article)
    article.setdefault("update_notes", "")

    # --- SEO re-enhance (fresh TOC/quick answer/schema) ---
    recent = wp.get_recent_published(per_page=8)
    internal = [p for p in recent if p.get("id") != post_id][:4]
    final_html = seo.enhance(
        article["content_html"],
        focus_keyword=article.get("focus_keyword", ""),
        internal_links=[{"link": p["link"], "title": p["title"]} for p in internal],
        external_links=article.get("external_links", []),
        quick_answer=article.get("quick_answer", ""),
        faq=article.get("faq", []),
        # Google freshness rule: original datePublished preserve, dateModified new
        date_str=(post.get("date") or date.today().isoformat())[:10],
        date_modified=date.today().isoformat(),
        slug=slug,
        title=title,
        description=article["meta_description"],
        category=article.get("category", ""),
        source_domains=[e.site_name for e in extras],
    )
    qa = validator.validate_article(article, final_html)
    article["_qa"] = qa
    log.info("Update QA %s/100 words=%d", qa["score"], qa["words"])

    meta = None
    if config.RANK_MATH_META_ENABLED:
        meta = seo.rankmath_meta(
            focus_keyword=article.get("focus_keyword", title[:60]),
            description=article["meta_description"],
            seo_title=article.get("seo_title") or title,
            secondary_keywords=article.get("secondary_keywords", []),
        )

    result = wp.update_post(
        post_id,
        content_html=final_html,
        title=title,  # same title enforce (URL + identity safe)
        excerpt=article["meta_description"],
        meta=meta,
    )
    log.info("POST UPDATED ✔ id=%s link=%s", post_id, result.get("link"))
    article["source_url"] = None
    try:
        state.record_refresh(config.STATE_PATH, post_id)
    except Exception:
        pass
    try:
        from . import indexnow

        indexnow.submit(result.get("link", ""))
    except Exception:
        pass
    try:
        notifier.notify_updated_post(article, result)
    except Exception:
        log.exception("Update notification failed (post update safe)")
    return result


# ------------------------------------------------------------------ listicles

def create_listicle(topic: str = "", mock: bool = False) -> Dict:
    """Trending listicle post (Top 10 jobs lanti 'stories')."""
    from . import topic_engine

    idea = topic or topic_engine.pick_listicle_idea(
        state.recent_titles(config.STATE_PATH, limit=30))
    log.info("Listicle idea: %s", idea)

    if mock:
        article = topic_engine.mock_listicle(idea,
                                             state.today_count(config.STATE_PATH, date.today()))
    else:
        if not config.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY ledu — listicle generate avvaledu")
        recent = state.recent_titles(config.STATE_PATH, limit=30)
        article = gemini_client.generate_listicle(idea, recent, date.today().year)

    from .main import _safe_slug
    article["slug"] = seo.optimize_slug(
        _safe_slug(article.get("slug", ""), article["title"]),
        focus_keyword=article.get("focus_keyword", "") or idea)
    for k, v in (("focus_keyword", idea), ("external_links", []),
                 ("secondary_keywords", []), ("quick_answer", ""),
                 ("faq", []), ("seo_title", ""), ("list_items", None)):
        article.setdefault(k, v)
    return publish_article(article)


# ------------------------------------------------------------------ auto refresh

def auto_refresh(limit: int = 1, older_days: int = None) -> list:
    """Purana published posts ni kotha research tho refresh (daily maintenance).

    Google freshness signal — rankings long-term lo stable.
    """
    older = older_days if older_days is not None else config.AUTO_REFRESH_MIN_AGE_DAYS
    targets = state.posts_to_refresh(config.STATE_PATH, older_days=older, limit=limit)
    if not targets:
        log.info("Auto-refresh: eligible posts levu (min %d days old)", older)
        return []
    results = []
    for t in targets:
        try:
            log.info("Auto-refresh: post %s '%s'", t["wp_id"], t["title"][:50])
            results.append(update_post(t["wp_id"]))
        except Exception:
            log.exception("Auto-refresh fail: post %s", t["wp_id"])
    return results
