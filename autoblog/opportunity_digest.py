# -*- coding: utf-8 -*-
"""Deadline-aware active-opportunity board and share digest.

The public site must not keep expired application notices in a daily list, but
expired article URLs should remain available for corrections and SEO history.
This module deliberately treats a missing deadline as "not announced" rather
than guessing an expiry date.
"""
from __future__ import annotations

import html
import re
from datetime import date, datetime, timedelta, timezone
from typing import Dict, Iterable, List
from urllib.parse import urlparse

IST = timezone(timedelta(hours=5, minutes=30))

# These are display sections, not a second WordPress taxonomy.  The category
# names are aliases because older sites may use "ts-govt-jobs" while newer
# sites use the shorter "ts-jobs" archive.
SECTIONS = [
    ("ts", "Telangana Government Jobs", "🏛️"),
    ("ap", "Andhra Pradesh Government Jobs", "🏛️"),
    ("central", "Central Government Jobs", "🇮🇳"),
    ("walkin", "Walk-in Jobs", "🚶"),
    ("job-melas", "Job Melas & Job Fairs", "🤝"),
    ("software", "Software Jobs", "💻"),
    ("private", "Private Jobs", "🏢"),
    ("scholarships", "Scholarships", "🎓"),
    ("results", "Results", "📄"),
    ("hall-tickets", "Hall Tickets", "🎫"),
    ("current-affairs", "Daily Current Affairs", "📰"),
]

CATEGORY_ALIASES = {
    "ts": {"ts-jobs", "ts-govt-jobs", "telangana-govt-jobs"},
    "ap": {"ap-jobs", "ap-govt-jobs", "andhra-pradesh-govt-jobs"},
    "central": {"central", "central-jobs", "central-govt-jobs"},
    "walkin": {"walkin", "walkin-jobs", "walk-in-jobs"},
    "software": {"software", "software-jobs"},
    "private": {"private", "private-jobs"},
    "scholarships": {"scholarship", "scholarships"},
    "results": {"result", "results"},
    "hall-tickets": {"hall-ticket", "hall-tickets", "hallticket"},
    "current-affairs": {"current", "current-affairs", "daily-current-affairs"},
}


def _clean(value: object, limit: int = 220) -> str:
    text = html.unescape(re.sub(r"<[^>]+>", " ", str(value or "")))
    return re.sub(r"\s+", " ", text).strip()[:limit]


def display_title(value: object, limit: int = 145) -> str:
    """Forward-card title: remove generic English SEO suffixes only.

    The WordPress title and URL are not changed. This keeps the circulation
    card natural for Telugu readers while preserving the article's SEO title.
    """
    title = _clean(value, limit)
    title = re.sub(
        r"\s*(?:[–—|:|-]\s*)?(?:complete\s+details|complete\s+guide|"
        r"apply\s+online|official\s+notification|latest\s+update)\s*$",
        "", title, flags=re.I,
    )
    return re.sub(r"\s+[–—|:,-]\s*$", "", title).strip()[:limit]


def parse_last_date(value: object) -> str:
    raw = str(value or "").strip()
    if not re.fullmatch(r"20\d{2}-\d{2}-\d{2}", raw):
        return ""
    try:
        datetime.strptime(raw, "%Y-%m-%d")
    except ValueError:
        return ""
    return raw


def is_active(last_date: object, today: date | None = None) -> bool:
    """Unknown date stays visible; a notice is inactive after its real date."""
    iso = parse_last_date(last_date)
    if not iso:
        return True
    return datetime.strptime(iso, "%Y-%m-%d").date() >= (today or datetime.now(IST).date())


def days_left(last_date: object, today: date | None = None) -> int | None:
    iso = parse_last_date(last_date)
    if not iso:
        return None
    return (datetime.strptime(iso, "%Y-%m-%d").date() - (today or datetime.now(IST).date())).days


def section_for_row(row: Dict) -> str:
    """Choose the narrowest display section from trusted category + title.

    Title fallback is only for legacy posts whose WordPress category was not
    created correctly; it never creates a deadline or changes article facts.
    """
    cats = {str(x).strip().lower().replace("_", "-") for x in (row.get("category_slugs") or [])}
    title = _clean(row.get("title"), 500).lower()
    blob = title + " " + " ".join(cats)

    if any(x in blob for x in ("job mela", "job fair", "mega job fair", "employment fair", "mela")):
        return "job-melas"
    for key, aliases in CATEGORY_ALIASES.items():
        if cats & aliases:
            return key
    # Conservative legacy fallback. Generic "notification" alone is never a
    # government category.
    if any(x in title for x in ("scholarship", "fellowship", "nsp", "epass", "e-pass")):
        return "scholarships"
    if any(x in title for x in ("result", "scorecard", "answer key", "merit list")):
        return "results"
    if any(x in title for x in ("hall ticket", "admit card", "call letter")):
        return "hall-tickets"
    if any(x in title for x in ("current affairs", "daily current", "daily gk", "daily news")):
        return "current-affairs"
    if any(x in title for x in ("walk-in", "walk in", "walkin", "direct interview")):
        return "walkin"
    if any(x in title for x in ("software", "developer", "full stack", "data analyst", "devops", "it job")):
        return "software"
    if any(x in title for x in ("tcs", "infosys", "wipro", "private job", "off campus", "mnc")):
        return "private"
    if any(x in title for x in ("tspsc", "tgpsc", "telangana", "ts police", "gurukul")):
        return "ts"
    if any(x in title for x in ("appsc", "andhra pradesh", "ap police", "apsrtc", "ap dsc")):
        return "ap"
    if any(x in title for x in ("ssc", "upsc", "rrb", "railway", "ibps", "sbi", "army", "navy")):
        return "central"
    return ""  # not every published article belongs in the active-opportunity board


def normalize_rows(rows: Iterable[Dict], today: date | None = None, limit: int = 240) -> List[Dict]:
    """Drop expired rows and normalize the REST response for grouping."""
    today = today or datetime.now(IST).date()
    out: List[Dict] = []
    seen = set()
    for raw in rows or []:
        row = dict(raw or {})
        if not is_active(row.get("last_date"), today):
            continue
        key = str(row.get("id") or row.get("link") or row.get("title") or "").strip()
        if not key or key in seen:
            continue
        section = section_for_row(row)
        if not section:
            continue
        seen.add(key)
        row["title"] = _clean(row.get("title"), 180)
        row["last_date"] = parse_last_date(row.get("last_date"))
        row["section"] = section
        row["days_left"] = days_left(row.get("last_date"), today)
        out.append(row)
    # Known deadlines first, with the closest closing date at the top. Unknown
    # dates follow, newest published posts first; nothing is fabricated.
    out.sort(key=lambda x: (
        0 if x.get("days_left") is not None else 1,
        x.get("days_left") if x.get("days_left") is not None else 999999,
        str(x.get("date") or ""),
    ), reverse=False)
    # Keep newest date ordering among unknown dates and a stable deadline order.
    known = [x for x in out if x.get("days_left") is not None]
    unknown = [x for x in out if x.get("days_left") is None]
    known.sort(key=lambda x: (x.get("days_left", 999999), str(x.get("date") or "")), reverse=False)
    unknown.sort(key=lambda x: str(x.get("date") or ""), reverse=True)
    return (known + unknown)[:max(1, int(limit))]


def group_rows(rows: Iterable[Dict], today: date | None = None, per_section: int = 8) -> Dict[str, List[Dict]]:
    groups = {key: [] for key, _, _ in SECTIONS}
    for row in normalize_rows(rows, today=today):
        bucket = groups.get(row.get("section"))
        if bucket is not None and len(bucket) < max(1, int(per_section)):
            bucket.append(row)
    return groups


def compact_site_link(site: str, row: Dict) -> str:
    """Use a configured shortener for owned posts, with safe native fallback."""
    long_url = str(row.get("link") or "").strip()
    site_url = str(site or "").rstrip("/")
    site_host = urlparse(site_url).netloc.lower().replace("www.", "")
    link_host = urlparse(long_url).netloc.lower().replace("www.", "")
    if long_url and site_host and link_host == site_host:
        try:
            from . import config as _config
            if getattr(_config, "SHORTLINK_ENABLED", False):
                from .link_shortener import shorten
                provider_url = shorten(long_url, title=str(row.get("title") or ""))
                if provider_url and provider_url != long_url:
                    return provider_url
        except Exception:  # noqa: BLE001 — native fallback is always available
            pass
    post_id = str(row.get("id") or "").strip()
    if post_id.isdigit() and site_url:
        return f"{site_url}/?p={post_id}"
    return long_url


def _digest_parts(site: str, rows: Iterable[Dict], today: date | None = None,
                  per_section: int = 6):
    """Build section blocks without Telegram's 4,096-char truncation."""
    today = today or datetime.now(IST).date()
    groups = group_rows(rows, today=today, per_section=per_section)
    header = [
        "📋 <b>StudentUp Active Opportunities</b>",
        "",
    ]
    section_meta = {key: (label, icon) for key, label, icon in SECTIONS}
    blocks = []
    total = 0
    for key, _, _ in SECTIONS:
        items = groups.get(key) or []
        if not items:
            continue
        label, icon = section_meta[key]
        block = [f"{icon} <b>{html.escape(label)}</b>", ""]
        for row in items:
            total += 1
            title = html.escape(display_title(row.get("title"), 145))
            # Configured shortener resolves to this exact StudentUp URL. If
            # provider is absent/unavailable, compact_site_link safely falls
            # back to the native WordPress URL.
            raw_link = compact_site_link(site, row)
            safe_link = html.escape(raw_link, quote=True)
            # Deadline is used internally to keep this list current, but is
            # intentionally not printed in the forward card. The student sees
            # the useful verified post title and the exact StudentUp article.
            block.append(
                f"• <b>{title}</b>\n"
                f"  🔗 <a href=\"{safe_link}\">{safe_link}</a>"
            )
        block.append("")
        blocks.append("\n".join(block))
    footer = [
        f"✅ <b>{total} updates</b>",
        "ℹ️ Apply cheyyemundu article lo unna official notification verify cheyyandi.",
    ]
    return header, blocks, footer, total


def render_digest(site: str, rows: Iterable[Dict], today: date | None = None,
                  per_section: int = 6) -> str:
    """Full forward-ready HTML digest with each real blog permalink visible."""
    header, blocks, footer, total = _digest_parts(site, rows, today, per_section)
    if not total:
        return ""
    return "\n".join(header + blocks + footer)


def render_digest_messages(site: str, rows: Iterable[Dict], today: date | None = None,
                           per_section: int = 6, max_chars: int = 3800) -> List[str]:
    """Split a large list into forwardable Telegram-safe messages."""
    header, blocks, footer, total = _digest_parts(site, rows, today, per_section)
    if not total:
        return []
    prefix = "\n".join(header)
    footer_text = "\n".join(footer)
    # A single category can itself be larger than Telegram's limit. Split it
    # between complete items, never in the middle of a URL.
    safe_blocks: List[str] = []
    for block in blocks:
        if len(prefix) + len(block) + len(footer_text) <= max_chars:
            safe_blocks.append(block)
            continue
        pieces = block.split("\n• ")
        section_head = pieces[0]
        current_block = section_head
        for piece in pieces[1:]:
            item = "\n• " + piece
            if (current_block != section_head and
                    len(prefix) + len(current_block) + len(item) + len(footer_text) > max_chars):
                safe_blocks.append(current_block + "\n<i>Continued…</i>")
                current_block = section_head + "\n<i>Continued…</i>"
            current_block += item
        safe_blocks.append(current_block)

    chunks: List[str] = []
    current = prefix
    for block in safe_blocks:
        candidate = current + "\n" + block
        if current != prefix and len(candidate) + len(footer_text) > max_chars:
            chunks.append(current.rstrip())
            current = prefix + "\n<i>Continued…</i>"
        current += "\n" + block
    current += "\n" + footer_text
    # Every split is made at an item boundary. This guard is only defensive for
    # an unexpectedly huge title/URL and keeps Telegram from truncating it.
    if len(current) > max_chars:
        chunks.append(current[:max_chars])
    else:
        chunks.append(current)
    return chunks
