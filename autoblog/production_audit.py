"""v30 production safety/revenue audit.

This command is intentionally an audit, not a promise generator. It checks
what the bot can actually verify and labels Google/CMP/manual requirements as
WARN/INFO rather than pretending they are complete.
"""
from __future__ import annotations

import re
from typing import Dict, List
from urllib.parse import urlparse

from . import config


EXPECTED_PLUGINS = {
    "rank-math": "Rank Math",
    "redirection": "Redirection",
    "updraftplus": "UpdraftPlus",
    "wp-super-cache": "WP Super Cache",
}
LEGAL_SLUGS = (
    "privacy-policy", "about-us", "contact-us",
    "corrections-policy", "editorial-policy",
)


def _client_valid(value: str) -> bool:
    return re.fullmatch(r"ca-pub-\d{6,20}", (value or "").strip()) is not None


def _ga_valid(value: str) -> bool:
    return re.fullmatch(r"G-[A-Z0-9]{6,20}", (value or "").strip().upper()) is not None


def _add(rows: List[Dict], status: str, label: str, detail: str) -> None:
    rows.append({"status": status, "label": label, "detail": detail})


def local_checks() -> List[Dict]:
    """Config-only checks; deterministic and network-free for CI/tests."""
    rows: List[Dict] = []
    parsed = urlparse(config.WP_SITE)
    _add(rows, "PASS" if parsed.scheme == "https" else "FAIL",
         "WordPress HTTPS", config.WP_SITE or "WP_SITE missing")
    _add(rows, "PASS" if config.WP_USERNAME and config.WP_APP_PASSWORD else "FAIL",
         "WordPress credentials", "Application Password configured" if
         config.WP_USERNAME and config.WP_APP_PASSWORD else "WP_USERNAME/WP_APP_PASSWORD missing")
    keys = list(getattr(config, "GEMINI_API_KEYS", []) or [])
    if config.GEMINI_API_KEY and config.GEMINI_API_KEY not in keys:
        keys.insert(0, config.GEMINI_API_KEY)
    _add(rows, "PASS" if keys else "FAIL", "Gemini key rotation",
         f"{len(keys)} key(s) configured" if keys else "no Gemini key")
    _add(rows, "PASS" if config.FACT_STRICT else "FAIL", "Fact guard",
         "dates/counts must match source" if config.FACT_STRICT else "FACT_STRICT=0 is unsafe")
    _add(rows, "PASS" if config.ORIG_HARD_FLOOR >= 72 else "FAIL",
         "Originality floor", f"{config.ORIG_HARD_FLOOR:g}% (72% minimum recommended)")
    _add(rows, "PASS" if config.DEFAULT_POST_STATUS == "draft" else "WARN",
         "Human review mode", config.DEFAULT_POST_STATUS)
    qa_floor = int(getattr(config, "PUBLISH_QA_MIN_SCORE", 80))
    orig_floor = float(getattr(config, "PUBLISH_ORIGINALITY_MIN", 72))
    _add(rows, "PASS" if 70 <= qa_floor <= 100 else "FAIL",
         "Live QA gate", f"direct publish requires QA {qa_floor}/100")
    _add(rows, "PASS" if 70 <= orig_floor <= 100 else "FAIL",
         "Live originality gate", f"direct publish requires originality {orig_floor:g}%")
    _add(rows, "PASS" if config.SUPPORT_EMAIL and "@" in config.SUPPORT_EMAIL else "FAIL",
         "Corrections contact", config.SUPPORT_EMAIL or "missing")
    if getattr(config, "ADSENSE_ENABLED", False):
        if not getattr(config, "ADSENSE_APPROVED", False):
            _add(rows, "INFO", "AdSense pre-approval gate",
                 "ADSENSE_APPROVED=0; no loader or in-content ad spaces will be emitted")
        elif _client_valid(getattr(config, "ADSENSE_CLIENT_ID", "")):
            _add(rows, "PASS", "AdSense client id", "format valid; approval is still Google-side")
            _add(rows, "PASS" if config.ADSENSE_CONSENT_PROVIDER else "WARN",
                 "Consent/CMP", config.ADSENSE_CONSENT_PROVIDER or
                 "configure a Google-certified CMP and verify EEA/UK/CH consent")
        else:
            _add(rows, "WARN", "AdSense client id",
                 "approved gate on but client id is missing/invalid")
    else:
        _add(rows, "INFO", "AdSense loader", "ADSENSE_ENABLED=0")
    if config.GA4_ENABLED:
        _add(rows, "PASS" if _ga_valid(config.GA4_MEASUREMENT_ID) else "WARN",
             "GA4 measurement id", config.GA4_MEASUREMENT_ID or "invalid/missing")
    else:
        _add(rows, "INFO", "Analytics", "GA4 disabled; no tracking script emitted")
    _add(rows, "PASS" if 1 <= config.MAX_AD_SLOTS <= 5 else "FAIL",
         "Ad slot cap", str(config.MAX_AD_SLOTS))
    _add(rows, "PASS" if config.AD_CLS_WRAPPER else "WARN",
         "Ad CLS protection", "reserved slot wrapper enabled" if config.AD_CLS_WRAPPER else
         "enable AD_CLS_WRAPPER=1")
    return rows


def _wordpress_checks(wp, rows: List[Dict]) -> None:
    try:
        me = wp.check_connection()
        roles = ", ".join(me.get("roles") or []) or "unknown"
        _add(rows, "PASS", "WordPress REST/auth", f"connected; roles={roles}")
    except Exception as exc:  # noqa: BLE001
        _add(rows, "FAIL", "WordPress REST/auth", str(exc)[:160])
        return

    try:
        code, text = wp.public_get_status("/robots.txt")
        blocked = "Disallow: /" in (text or "").replace("\r", "")
        _add(rows, "FAIL" if blocked else "PASS", "Robots visibility",
             "Disallow: / found" if blocked else f"HTTP {code}; no global block detected")
    except Exception as exc:  # noqa: BLE001
        _add(rows, "WARN", "Robots visibility", str(exc)[:120])
    try:
        code, _ = wp.public_get_status("/sitemap_index.xml")
        if code != 200:
            code, _ = wp.public_get_status("/sitemap.xml")
        _add(rows, "PASS" if code == 200 else "WARN", "XML sitemap", f"HTTP {code}")
    except Exception as exc:  # noqa: BLE001
        _add(rows, "WARN", "XML sitemap", str(exc)[:120])

    try:
        plugins = wp.list_plugins()
        by_slug = {}
        for item in plugins:
            slug = (item.get("slug") or item.get("plugin", "").split("/", 1)[0]).lower()
            by_slug[slug] = item
        missing = [slug for slug in EXPECTED_PLUGINS if slug not in by_slug]
        inactive = [slug for slug in EXPECTED_PLUGINS
                    if slug in by_slug and by_slug[slug].get("status") != "active"]
        if missing or inactive:
            detail = []
            if missing:
                detail.append("missing: " + ", ".join(EXPECTED_PLUGINS[x] for x in missing))
            if inactive:
                detail.append("inactive: " + ", ".join(EXPECTED_PLUGINS[x] for x in inactive))
            _add(rows, "WARN", "Plugin stack", "; ".join(detail))
        else:
            _add(rows, "PASS", "Plugin stack", "reviewed SEO/cache/backup stack active")
    except Exception as exc:  # noqa: BLE001
        _add(rows, "WARN", "Plugin stack", str(exc)[:120])

    try:
        themes = wp.list_themes()
        active = next((t for t in themes if t.get("status") == "active"), None)
        _add(rows, "PASS" if active else "WARN", "Active theme",
             (active.get("name") or active.get("slug", "unknown")) if active else
             "active theme not visible via REST")
    except Exception as exc:  # noqa: BLE001
        _add(rows, "WARN", "Active theme", str(exc)[:120])

    missing_pages = []
    for slug in LEGAL_SLUGS:
        try:
            if not wp.get_page_by_slug(slug):
                missing_pages.append(slug)
        except Exception:
            missing_pages.append(slug)
    _add(rows, "PASS" if not missing_pages else "WARN", "Policy pages",
         "all five pages found" if not missing_pages else "missing: " + ", ".join(missing_pages))

    if (getattr(config, "ADSENSE_APPROVED", False)
            and _client_valid(getattr(config, "ADSENSE_CLIENT_ID", ""))):
        try:
            code, text = wp.public_get_status("/ads.txt")
            expected = "pub-" + config.ADSENSE_CLIENT_ID[7:]
            _add(rows, "PASS" if code == 200 and expected in text else "WARN",
                 "ads.txt", "publisher line found" if code == 200 and expected in text else
                 "host the exact publisher line at /ads.txt")
        except Exception as exc:  # noqa: BLE001
            _add(rows, "WARN", "ads.txt", str(exc)[:120])


def collect(wp=None) -> List[Dict]:
    rows = local_checks()
    if wp is not None:
        _wordpress_checks(wp, rows)
    return rows


def run(wp=None, connect: bool = True) -> int:
    """Print audit and return non-zero only for objectively unsafe failures."""
    if connect and wp is None:
        from .wordpress_client import WordPressClient
        wp = WordPressClient()
    rows = collect(wp)
    print("=" * 72)
    print("  PRODUCTION SAFETY + REVENUE AUDIT (v30)")
    print("=" * 72)
    for row in rows:
        icon = {"PASS": "✅", "WARN": "⚠️ ", "FAIL": "⛔", "INFO": "ℹ️ "}[row["status"]]
        print(f"  {icon} {row['label']:<25.25s} {row['detail'][:170]}")
    fails = sum(1 for row in rows if row["status"] == "FAIL")
    warns = sum(1 for row in rows if row["status"] == "WARN")
    print("-" * 72)
    print(f"  Result: {len(rows) - fails - warns} pass · {warns} warnings · {fails} blockers")
    print("  Google approval/revenue are never guaranteed by code; review WARN items manually.")
    print("=" * 72)
    return 1 if fails else 0
