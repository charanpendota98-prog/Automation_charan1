"""v32 existing-post quality audit and safe refresh planning.

This module audits live WordPress content before any rewrite. It never bulk
rewrites posts blindly: title/URL ownership, source freshness, facts and
manual editorial decisions must be visible first.
"""
from __future__ import annotations

import re
from typing import Dict, List
from urllib.parse import urlparse

from . import config, validator


def _text(value) -> str:
    if isinstance(value, dict):
        return value.get("rendered") or value.get("raw") or ""
    return str(value or "")


def fetch_published(wp, limit: int = 500) -> List[Dict]:
    """Fetch published posts in pages without relying on local state.db."""
    posts: List[Dict] = []
    page = 1
    while len(posts) < max(1, limit):
        per_page = min(100, max(1, limit - len(posts)))
        r = wp._request("GET", "posts", params={
            "status": "publish", "context": "view", "page": page,
            "per_page": per_page,
            "_fields": "id,link,title,content,excerpt,date,modified,featured_media,categories",
        })
        if not r.ok:
            break
        batch = r.json() or []
        posts.extend(batch)
        if len(batch) < per_page:
            break
        page += 1
    return posts[:limit]


def audit_post(post: Dict) -> Dict:
    html = _text(post.get("content"))
    title = _text(post.get("title")).strip()
    link = post.get("link", "")
    words = validator.word_count(html)
    h2_count = len(re.findall(r"<h2\b", html, re.I))
    table = bool(re.search(r"<table\b", html, re.I))
    faq = bool(re.search(r"faq|frequently asked|related questions|సందేహాలు", html, re.I))
    quick = bool(re.search(r"quick-answer|quick answer|సంక్షిప్త సమాధానం", html, re.I))
    images = re.findall(r"<img\b[^>]*>", html, re.I)
    missing_alt = sum(1 for image in images if not re.search(r"\balt\s*=\s*[\"'][^\"']+", image, re.I))
    site_host = urlparse(config.WP_SITE).netloc
    links = re.findall(r'href=["\'](https?://[^"\']+)', html, re.I)
    internal = sum(1 for url in links if site_host and site_host in urlparse(url).netloc)
    external = sum(1 for url in links if not site_host or site_host not in urlparse(url).netloc)
    issues = []
    if len(title) < 25 or len(title) > 85:
        issues.append("title-length")
    if words < 900:
        issues.append("thin-content")
    if h2_count < 3:
        issues.append("few-sections")
    if not table:
        issues.append("no-summary-table")
    if not quick:
        issues.append("no-quick-answer")
    if not faq:
        issues.append("no-faq")
    if internal < 1:
        issues.append("no-internal-link")
    if external < 1:
        issues.append("no-external-link")
    if missing_alt:
        issues.append(f"{missing_alt}-image-alt")
    # A bounded score makes the report useful without pretending to be Google.
    checks = [
        25 <= len(title) <= 85, words >= 900, h2_count >= 3, table,
        quick, faq, internal >= 1, external >= 1, not missing_alt,
    ]
    score = round(100 * sum(checks) / len(checks))
    action = "keep"
    if score < 55:
        action = "priority-refresh"
    elif score < 78:
        action = "editorial-refresh"
    elif issues:
        action = "small-fix"
    return {
        "id": post.get("id"), "link": link, "title": title,
        "modified": post.get("modified", ""), "words": words,
        "h2": h2_count, "internal": internal, "external": external,
        "score": score, "action": action, "issues": issues,
    }


def audit_posts(wp, limit: int = 500) -> List[Dict]:
    return [audit_post(post) for post in fetch_published(wp, limit=limit)]


def summary(rows: List[Dict]) -> Dict:
    if not rows:
        return {"posts": 0, "average": 0, "priority": 0, "refresh": 0, "small_fix": 0}
    return {
        "posts": len(rows),
        "average": round(sum(row["score"] for row in rows) / len(rows)),
        "priority": sum(row["action"] == "priority-refresh" for row in rows),
        "refresh": sum(row["action"] == "editorial-refresh" for row in rows),
        "small_fix": sum(row["action"] == "small-fix" for row in rows),
    }


def run(wp=None, limit: int = 500) -> int:
    from .wordpress_client import WordPressClient
    wp = wp or WordPressClient()
    try:
        wp.check_connection()
        rows = audit_posts(wp, limit=limit)
    except Exception as exc:  # noqa: BLE001
        print(f"❌ Content audit failed: {exc}")
        return 1
    rep = summary(rows)
    print("=" * 78)
    print(f"  EXISTING POST QUALITY AUDIT ({rep['posts']} posts; not a Google guarantee)")
    print("=" * 78)
    if not rows:
        print("  No published posts returned — check REST permissions/status.")
    else:
        print(f"  Average quality: {rep['average']}/100")
        print(f"  Priority refresh: {rep['priority']} · Editorial refresh: {rep['refresh']} · Small fixes: {rep['small_fix']}")
        print("\n  SCORE  ACTION             WORDS  ISSUES                         TITLE")
        print("  " + "-" * 72)
        for row in sorted(rows, key=lambda item: (item["score"], item["id"])):
            issues = ", ".join(row["issues"][:3]) or "none"
            print(f"  {row['score']:>3}/100  {row['action']:<18} {row['words']:>5}  {issues:<29} {row['title'][:54]}")
    print("-" * 78)
    print("  Audit is read-only. Refresh only after source/fact review; URLs are preserved.")
    print("  Use --auto-refresh for the existing controlled refresh flow, not blind bulk rewriting.")
    print("=" * 78)
    return 0
