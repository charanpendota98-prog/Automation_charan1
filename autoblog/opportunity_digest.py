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
    ("outsourcing", "Outsourcing & Contract Jobs", "💼"),
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
    "outsourcing": {"outsourcing", "outsourcing-jobs", "contract", "contract-basis"},
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
    # Outsourcing/contract posts: pipeline.py classification order ni mirror
    # chestundi (pipeline "Outsourcing Jobs" ani pettina post ikkada kanipinchali).
    if any(x in title for x in ("outsourcing", "contract basis", "contractual",
                                "outsourced", "guest faculty", "honorarium",
                                "అవుట్‌సోర్సింగ్", "కాంట్రాక్ట్")):
        return "outsourcing"
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


def parse_post_date(value: object) -> date | None:
    """REST `date` (ISO, time tho) → date. Unknown aithe None (guess cheyyadu)."""
    raw = str(value or "").strip()
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00")).date()
    except ValueError:
        try:
            return datetime.strptime(raw[:10], "%Y-%m-%d").date()
        except ValueError:
            return None


def stale_days_default() -> int:
    """Config nunchi stale window (0 = off). Import fail aithe 0 (safe)."""
    try:
        from . import config as _config
        return max(0, int(getattr(_config, "OPPORTUNITY_STALE_DAYS", 0) or 0))
    except Exception:  # noqa: BLE001 — config lekapote feature off
        return 0


def is_stale(row: Dict, today: date, stale_days: int) -> bool:
    """Deadline teliyani post chala puratana aithe active list nunchi teesestam.

    Enduku: govt job notice ki last date cheppakapovadam common (results /
    admit-card / listicle laantivi). Kaani **120+ rojula puratana** notice ni
    active board lo chupinchadam reader ni confuse chestundi (adi almost
    close ayyi untundi). Idi conservative default — 0 pettithe off.
    """
    if not stale_days:
        return False
    if parse_last_date(row.get("last_date")):
        return False                     # deadline unte adi ne decide chestundi
    published = parse_post_date(row.get("date"))
    if not published:
        return False                     # date teliyadu → guess cheyyadu
    return (today - published).days > stale_days


def title_key(value: object) -> str:
    """Same recruitment ki rendu/మూడు posts unte okate key ravali.

    Conservative: SEO suffixes + year + punctuation teesi, first 60 chars.
    Chinna title (<15 chars) ki key ivvadu — collision risk.
    """
    text = _clean(value, 300).lower()
    text = re.sub(r"\b20\d{2}\b", " ", text)
    text = re.sub(
        r"\b(?:notification|notifications|recruitment|apply online|application|"
        r"complete details|complete guide|latest update|official notification|"
        r"result|results|hall ticket|admit card|merit list|answer key|"
        r"revised|extended|update|job|jobs|posts?|vacancy|vacancies)\b",
        " ", text)
    text = re.sub(r"[^a-z0-9]+", "", text)
    return text[:60] if len(text) >= 10 else ""


def supersede(rows: List[Dict]) -> List[Dict]:
    """Same recruitment ki kotha post vaste puratana di list nunchi teesestam.

    Only same section + same title_key (≥15 chars) ki; newest date win.
    Ee pani reader ki "rendu sari same job" kanipinchakunda chestundi.
    """
    best: Dict[str, Dict] = {}
    out: List[Dict] = []
    for row in rows:
        key = f"{row.get('section')}|{title_key(row.get('title'))}"
        if key.endswith("|"):
            out.append(row)
            continue
        prev = best.get(key)
        if prev is None:
            best[key] = row
            out.append(row)
            continue
        # same key → newest wins; puratana di drop (superseded)
        if str(row.get("date") or "") > str(prev.get("date") or ""):
            out[out.index(prev)] = row
            row["superseded"] = prev.get("id")
            best[key] = row
        else:
            prev["superseded"] = row.get("id")
    return out


def normalize_rows(rows: Iterable[Dict], today: date | None = None, limit: int = 240,
                   stale_days: int | None = None, dedupe: bool = True) -> List[Dict]:
    """Active rows mattrame: expired → out · chala puratana (undated) → out ·
    same recruitment ki kotha post vaste puratana di → out (superseded)."""
    today = today or datetime.now(IST).date()
    stale = stale_days_default() if stale_days is None else max(0, int(stale_days))
    out: List[Dict] = []
    seen = set()
    for raw in rows or []:
        row = dict(raw or {})
        if not is_active(row.get("last_date"), today):
            continue                      # last date ayyipoyindi → list nunchi out
        section = section_for_row(row)
        if not section:
            continue
        key = str(row.get("id") or row.get("link") or row.get("title") or "").strip()
        if not key or key in seen:
            continue
        if is_stale(row, today, stale):
            continue                      # deadline teliyadu + 120+ rojula puratana
        seen.add(key)
        row["title"] = _clean(row.get("title"), 180)
        row["last_date"] = parse_last_date(row.get("last_date"))
        row["section"] = section
        row["days_left"] = days_left(row.get("last_date"), today)
        published = parse_post_date(row.get("date"))
        row["is_new"] = bool(published and published >= today - timedelta(days=1))
        row["closing_soon"] = (row["days_left"] is not None and 0 <= row["days_left"] <= 3)
        row["stale_days"] = stale
        out.append(row)
    if dedupe:
        out = supersede(out)
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


def compact_site_link(site: str, row: Dict, prefer_permalink: bool = False) -> str:
    """Use a configured shortener for owned posts, with safe native fallback.

    `prefer_permalink=True` (v183 WhatsApp list): shortener lekapote `?p=ID`
    badulu **nijamaina permalink** vadutundi — forward chesinappudu readable
    URL (trust + clicks) and SEO-friendly. Telegram digest default behavior
    (`?p=ID`) marchadu.
    """
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
    if prefer_permalink and long_url:
        return long_url
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

# ---------------------------------------------------------------------------
# v183: WhatsApp forward list — plain text (WhatsApp HTML tags render cheyyadu)
# ---------------------------------------------------------------------------

WA_MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun",
             "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")
WA_DAYS = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")


def _wa_clean(value: object, limit: int = 110) -> str:
    """WhatsApp text ki safe: SEO suffix teesi, markers remove chesi, okate line.

    Same `display_title()` cleaning (Telegram card tho same look) — kaani
    WhatsApp ki `*`/`_` markers natural text lo unte bold/italic ayyipotayi,
    anduke avi teesestam (message formatting padipovadam ledu).
    """
    text = display_title(value, limit + 30)
    text = text.replace("*", "").replace("_", "").replace("~", "")
    return text[:limit].strip()


def wa_date_line(today: date) -> str:
    return f"{WA_DAYS[today.weekday()]}, {today.day:02d} {WA_MONTHS[today.month - 1]} {today.year}"


def _whatsapp_parts(site: str, rows: Iterable[Dict], today: date | None = None,
                    per_section: int = 6, today_block: bool = True,
                    today_limit: int = 5, new_ids: Iterable[object] | None = None,
                    changes: Dict | None = None):
    """WhatsApp plain-text parts: header + units + footer.

    Unit = (section header, [item, ...]) — item string lo title + link rendu
    lines unnayi ("1) Title\n🔗 url"). Chunking item boundaries lo jarugutundi
    (link madhya lo eppudu split avvadu).

    * `new_ids` — ippude (ninna list tho compare) kothaga add ayina post ids →
      aa items ki 🆕 marker.
    * `changes` — {"new": n, "gone": n} → header lo okka line ("em marindo").
    """
    today = today or datetime.now(IST).date()
    groups = group_rows(rows, today=today, per_section=per_section)
    site_url = str(site or "").rstrip("/")
    header = [
        "📋 *StudentUp — Daily Updates List*",
        f"🗓 {wa_date_line(today)} · 🌐 {site_url or 'studentup.in'}",
    ]
    if changes:
        bits = []
        if changes.get("new"):
            bits.append(f"🆕 {changes['new']} kotha")
        if changes.get("gone"):
            bits.append(f"❌ {changes['gone']} out (close/stale/duplicate)")
        if bits:
            header.append("📈 " + " · ".join(bits))
    total = 0
    units = []
    today_items = []
    if today_block:
        for key, _, _ in SECTIONS:
            for row in groups.get(key) or []:
                if str(row.get("date") or "")[:10] == today.isoformat():
                    today_items.append(row)
    fresh = {str(x) for x in (new_ids or [])}

    def _item(idx: int, row: Dict) -> str:
        mark = "🆕 " if (row.get("is_new") or str(row.get("id")) in fresh) else ""
        note = wa_deadline_note(row.get("days_left"))
        tail = f"  · {note}" if note else ""
        return (f"{idx}) {mark}{_wa_clean(row.get('title'))}{tail}\n"
                f"🔗 {compact_site_link(site, row, prefer_permalink=True)}")

    if today_items:
        items = [_item(idx, row)
                 for idx, row in enumerate(today_items[:today_limit], 1)]
        total += len(items)
        units.append((f"🆕 *IVVALTI KOTHAAVI (today)* ({len(items)})", items))
    section_meta = {key: (label, icon) for key, label, icon in SECTIONS}
    for key, _, _ in SECTIONS:
        rows_here = groups.get(key) or []
        if not rows_here:
            continue
        label, icon = section_meta[key]
        items = [_item(idx, row) for idx, row in enumerate(rows_here, 1)]
        total += len(items)
        units.append((f"{icon} *{label.upper()}* ({len(items)})", items))
    footer = [
        f"✅ *{total} updates* · 🌐 {site_url or 'studentup.in'}",
        "ℹ️ Apply cheyyemundu article lo unna official notification verify cheyyandi.",
    ]
    return header, units, footer, total


def wa_deadline_note(days_left: int | None) -> str:
    """Closing-soon urgency (3 rojula lopu mattrame) — honest, peddha date ledu."""
    if days_left is None or days_left > 3:
        return ""
    if days_left <= 0:
        return "⏰ last date TODAY"
    if days_left == 1:
        return "⏰ repu last date (1 day left)"
    return f"⏰ {days_left} days left"


def _render_units(units) -> List[str]:
    parts: List[str] = []
    for head, items in units:
        parts.append(head)
        parts.append("")
        for item in items:
            parts.append(item)
            parts.append("")
    return parts


def render_whatsapp(site: str, rows: Iterable[Dict], today: date | None = None,
                    per_section: int = 6, today_block: bool = True,
                    new_ids: Iterable[object] | None = None,
                    changes: Dict | None = None) -> str:
    """Okate plain-text message (WhatsApp group/status ki copy-paste cheyyadaniki)."""
    header, units, footer, total = _whatsapp_parts(site, rows, today, per_section,
                                                   today_block, new_ids=new_ids,
                                                   changes=changes)
    if not total:
        return ""
    return "\n".join(header + [""] + _render_units(units) + footer)


def render_whatsapp_messages(site: str, rows: Iterable[Dict], today: date | None = None,
                             per_section: int = 6, today_block: bool = True,
                             max_chars: int = 3900,
                             new_ids: Iterable[object] | None = None,
                             changes: Dict | None = None) -> List[str]:
    """Peddha list ni WhatsApp-safe chunks ga split (item madhya lo kaadu).

    Split **item boundaries** lo mattrame (URL eppudu cut avvadu). Oka item
    okkate chunk limit kanna peddha unte, adi ontariga okka chunk avutundi.
    """
    header, units, footer, total = _whatsapp_parts(site, rows, today, per_section,
                                                   today_block, new_ids=new_ids,
                                                   changes=changes)
    if not total:
        return []
    prefix = "\n".join(header) + "\n\n"
    contd = f"📋 *StudentUp Daily List (contd.)*\n🌐 {str(site or '').rstrip('/')}\n\n"
    footer_text = "\n" + "\n".join(footer)
    chunks: List[str] = []
    current = prefix
    for head, items in units:
        idx = 0
        while idx < len(items):
            block_head = head if idx == 0 else f"{head} (contd.)"
            room = max_chars - len(footer_text) - len(current) - len(block_head) - 6
            if room < 48 and current.strip() != prefix.strip():
                chunks.append(current.rstrip())
                current = contd
                continue
            take: List[str] = []
            size = 0
            while idx < len(items):
                piece_len = len(items[idx]) + 2
                if take and size + piece_len > room:
                    break
                take.append(items[idx])
                size += piece_len
                idx += 1
            if not take and idx < len(items):        # item okkate limit kanna peddha
                take = [items[idx]]
                idx += 1
            piece = block_head + "\n\n" + "\n\n".join(take) + "\n"
            if current.strip() != prefix.strip() and len(current) + len(piece) + len(footer_text) > max_chars:
                # Ee piece ikkada fit avvadu — kotha chunk ki pampu, items ni
                # malli try cheyyali (anduke idx venakki — items pogapoyevi ledu).
                chunks.append(current.rstrip())
                current = contd
                idx -= len(take)
                continue
            current += piece + "\n"
    current += footer_text
    chunks.append(current.rstrip())
    return [c for c in chunks if c.strip()]
