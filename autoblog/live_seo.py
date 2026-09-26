"""Read-only validation of the real WordPress/Rank Math result.

This module never derives a Rank Math score from a local checklist. The only
Rank Math score it reports is the numeric value returned by WordPress/StudentUp
SEO bridge. A separate ``public_seo_coverage`` score measures observed HTML
coverage and is explicitly not a Rank Math score.
"""
from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Dict, Optional
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from . import config
from .wordpress_client import WordPressClient

log = logging.getLogger("autoblog.live_seo")


def _fetch_public(url: str) -> Dict:
    try:
        response = requests.get(
            url,
            headers={"User-Agent": "StudentUp-LiveSEOAudit/1.0"},
            timeout=min(int(getattr(config, "HTTP_TIMEOUT", 30)), 30),
            allow_redirects=True,
        )
        return {
            "status": int(response.status_code),
            "final_url": str(response.url or url),
            "html": response.text or "",
            "error": "",
        }
    except Exception as exc:  # noqa: BLE001 — unknown is never PASS
        return {"status": 0, "final_url": url, "html": "", "error": str(exc)[:240]}


def _field(fields: Dict, key: str) -> str:
    value = fields.get(key, "") if isinstance(fields, dict) else ""
    if isinstance(value, list):
        return ", ".join(str(item) for item in value if str(item).strip())
    return str(value or "").strip()


def _keyword(value: str) -> str:
    return next((part.strip() for part in str(value or "").split(",") if part.strip()), "")


def _check(name: str, ok: bool, detail: str, points: int) -> Dict:
    return {"name": name, "ok": bool(ok), "detail": detail, "points": int(points)}


def _public_checks(post: Dict, html: str, final_url: str, fields: Dict) -> list:
    soup = BeautifulSoup(html or "", "html.parser")
    tag_ids = post.get("tags") or []
    category_ids = post.get("categories") or []
    plain = " ".join(soup.get_text(" ", strip=True).split())
    keyword = _keyword(_field(fields, "rank_math_focus_keyword"))
    keyword_low = keyword.casefold()
    title = soup.title.get_text(" ", strip=True) if soup.title else ""
    description_tag = soup.find("meta", attrs={"name": "description"})
    description = str(description_tag.get("content", "")).strip() if description_tag else ""
    canonical_tag = soup.find("link", rel=lambda value: value and "canonical" in value)
    canonical = str(canonical_tag.get("href", "")).strip() if canonical_tag else ""
    og_title = soup.find("meta", attrs={"property": "og:title"})
    og_description = soup.find("meta", attrs={"property": "og:description"})
    og_image = soup.find("meta", attrs={"property": "og:image"})
    h1 = soup.find("h1")
    jsonld = []
    for node in soup.find_all("script", attrs={"type": "application/ld+json"}):
        try:
            jsonld.append(json.loads(node.string or node.get_text() or "{}"))
        except (TypeError, ValueError):
            continue
    jsonld_text = json.dumps(jsonld, ensure_ascii=False).lower()
    content = soup.find("article") or soup.find("main") or soup.body
    first_para = content.find("p").get_text(" ", strip=True) if content and content.find("p") else ""
    internal_links = [a.get("href", "") for a in soup.find_all("a", href=True)
                      if urlparse(a.get("href", "")).netloc in ("", urlparse(final_url).netloc)]
    url_path = urlparse(final_url).path.casefold()
    keyword_tokens = [token for token in re.findall(r"[a-z0-9]+", keyword_low)
                      if len(token) > 2]
    headings = [node.get_text(" ", strip=True).casefold()
                for node in soup.find_all(["h2", "h3"])]
    images = soup.find_all("img")
    alt_values = [str(node.get("alt") or "").strip().casefold() for node in images]
    author_observed = bool(
        soup.select_one("[itemprop='author'], .su-author, .su-author-meta")
        or '"author"' in jsonld_text
    )

    return [
        _check("Public HTTP response", True, "public HTML was fetched", 5),
        _check("Rank Math focus keyword stored", bool(keyword), "present" if keyword else "missing", 10),
        _check("Public title", bool(title), f"{len(title)} characters" if title else "missing", 8),
        _check("Keyword in public title", bool(keyword and keyword_low in title.casefold()), "observed" if keyword else "not testable", 10),
        _check("Keyword in public URL", bool(keyword_tokens) and all(token in url_path for token in keyword_tokens), url_path or "missing", 7),
        _check("Meta description", 110 <= len(description) <= 170, f"{len(description)} characters", 10),
        _check("Keyword in meta description", bool(keyword and keyword_low in description.casefold()), "observed" if keyword else "not testable", 8),
        _check("Canonical", bool(canonical and canonical.startswith(("http://", "https://"))), "present" if canonical else "missing", 8),
        _check("Open Graph", bool(og_title and og_description and og_image), "title/description/image present" if og_title and og_description and og_image else "one or more OG fields missing", 8),
        _check("Article schema", '"article"' in jsonld_text or '"newsarticle"' in jsonld_text, "Article/NewsArticle JSON-LD observed" if jsonld else "not observed", 8),
        _check("Breadcrumb schema", "breadcrumb" in jsonld_text, "BreadcrumbList observed" if "breadcrumb" in jsonld_text else "not observed", 5),
        _check("Single H1", bool(h1), "present" if h1 else "missing", 5),
        _check("Keyword in first paragraph", bool(keyword and keyword_low in first_para.casefold()), "observed" if keyword else "not testable", 5),
        _check("Keyword in H2/H3", bool(keyword and any(keyword_low in heading for heading in headings)), f"{len(headings)} H2/H3 headings", 6),
        _check("Image alt text", bool(images and all(alt_values) and keyword and any(keyword_low in alt for alt in alt_values)), f"{len(images)} image(s) with alt text", 6),
        _check("Author / E-E-A-T surface", author_observed, "author/byline observed" if author_observed else "author surface missing", 5),
        _check("Relevant internal link", bool(internal_links), f"{len(internal_links)} same-site links", 5),
        _check("Category taxonomy", bool(category_ids), f"{len(category_ids)} category id(s)", 3),
        _check("Keyword/tag taxonomy", bool(tag_ids), f"{len(tag_ids)} tag id(s); relevance still needs editorial review", 3),
        _check("Readable article content", len(plain.split()) >= 300, f"{len(plain.split())} rendered words", 6),
    ]


def audit(post_id: int, wp: Optional[WordPressClient] = None) -> Dict:
    """Audit one real post; missing access remains review/unknown."""
    client = wp or WordPressClient()
    try:
        post = client.get_post(int(post_id))
    except Exception as exc:  # noqa: BLE001
        return {
            "post_id": int(post_id), "status": "unknown",
            "error": f"WordPress post read failed: {type(exc).__name__}: {str(exc)[:180]}",
            "rank_math_actual_score": None, "rank_math_actual_100": False,
            "rank_math_live_min_score": int(getattr(config, "RM_LIVE_MIN_SCORE", 80) or 80),
            "rank_math_target_met": False,
            "public_seo_coverage": None, "checks": [],
        }
    link = str(post.get("link") or "").strip()
    state = client.read_rankmath_state(int(post_id)) if hasattr(client, "read_rankmath_state") else {}
    fields = state.get("fields") or {}
    actual_score = state.get("rank_math_ui_score")
    public = _fetch_public(link) if link else {"status": 0, "html": "", "final_url": link, "error": "post has no public link"}
    if public.get("status") != 200:
        return {
            "post_id": int(post_id), "link": link, "status": "review",
            "error": f"Public URL HTTP {public.get('status', 0)}; {public.get('error', '')}".strip(),
            "rank_math_actual_score": actual_score, "rank_math_actual_100": actual_score == 100,
            "rank_math_live_min_score": int(getattr(config, "RM_LIVE_MIN_SCORE", 80) or 80),
            "rank_math_target_met": actual_score is not None and actual_score >= int(getattr(config, "RM_LIVE_MIN_SCORE", 80) or 80),
            "public_seo_coverage": None, "checks": [], "fields_present": sorted(k for k, v in fields.items() if str(v).strip()),
        }
    checks = _public_checks(post, public.get("html", ""), public.get("final_url", link), fields)
    points = sum(row["points"] for row in checks)
    earned = sum(row["points"] for row in checks if row["ok"])
    coverage = round(earned * 100 / points, 1) if points else 0.0
    rankmath_fields_ok = all(_field(fields, key) for key in (
        "rank_math_focus_keyword", "rank_math_title", "rank_math_description",
    ))
    live_min = int(getattr(config, "RM_LIVE_MIN_SCORE", 80) or 80)
    coverage_min = float(getattr(config, "LIVE_SEO_MIN_COVERAGE", 80) or 80)
    target_met = actual_score is not None and actual_score >= live_min
    return {
        "post_id": int(post_id), "link": link,
        "status": "pass" if target_met and coverage >= coverage_min and rankmath_fields_ok else "review",
        "rank_math_actual_score": actual_score,
        "rank_math_actual_100": actual_score == 100,
        "rank_math_live_min_score": live_min,
        "rank_math_target_met": target_met,
        "rank_math_score_source": state.get("score_note", "WordPress SEO bridge readback"),
        "rank_math_fields_ok": rankmath_fields_ok,
        "public_seo_coverage": coverage,
        "public_seo_coverage_note": "Independent rendered-HTML coverage score; not Rank Math and not a Google score.",
        "checks": checks,
        "fields_present": sorted(k for k, v in fields.items() if str(v).strip()),
        "checked_url": public.get("final_url", link),
    }


def run_cli(post_id: int) -> int:
    report = audit(post_id)
    output = Path(config.LOG_DIR) / f"live-seo-post-{int(post_id)}.json"
    try:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError:
        log.exception("could not save live SEO report")
    print("=" * 76)
    print("  REAL LIVE SEO / RANK MATH VERIFICATION — read-only")
    print("=" * 76)
    print(f"  post: {post_id}")
    print(f"  Rank Math stored score: {report.get('rank_math_actual_score')!r}  (only WordPress value is accepted)")
    print(f"  Live minimum: {report.get('rank_math_live_min_score', 80)} · minimum met: {'YES' if report.get('rank_math_target_met') else 'NO / UNKNOWN'}")
    print(f"  Rank Math actual 100: {'YES' if report.get('rank_math_actual_100') else 'NO / UNKNOWN'}")
    print(f"  Public SEO coverage: {report.get('public_seo_coverage')!r}  (independent HTML audit, not Rank Math)")
    for row in report.get("checks", []):
        print(f"  {'✅' if row['ok'] else '❌'} {row['name']}: {row['detail']}")
    print(f"  report: {output}")
    print("  No score was calculated as Rank Math and no field was written.")
    print("=" * 76)
    return 0 if report.get("status") == "pass" else 1
