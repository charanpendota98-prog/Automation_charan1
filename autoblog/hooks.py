# -*- coding: utf-8 -*-
"""v188 — HOOK ENGINE: "main enti?" mundu cheppi, links kinda ivvadam.

User feedback (verbatim): *"blog lo pedthav gaa same dani neatga hook ga vundali main gaa
enti ani ssc chsl uryogalu IBPS clerk jobs ilaga main enti ani cheppi kind alinks ravali
mana blog links manam post chesinavi matharame"*.

Rendu surfaces ki okate hook logic:

1. **WhatsApp forwarded list** (Telugu) — item `*SSC CHSL 2026 ఉద్యోగాలు*` (hook = main
   ento, boilerplate teesi) → kinda `— 2,000+ పోస్టులు · 💰 pay · ⏰ 2 రోజులు` → kinda
   **mana blog link** (external source URL eppudu ledu).
2. **Blog draft lead** (English — site public surfaces English-only gate) — article
   modati paragraph hook ga: "SSC CHSL 2026 recruitment — eligibility, important dates,
   vacancy details and the official apply link in one place." Fabricate cheyyadu:
   title/keyword + **nijamaina** count/deadline unte mattrame avi kalustaayi.

Doctrine: no fabricated numbers/dates · idempotent (okate post ki rendu sari lead ledu) ·
Telugu mattrame list ki (public site English).
"""
from __future__ import annotations

import html as _html
import re
from typing import Dict, Optional

# Title nunchi teesesevi — hook ki paniki raavu ("main enti" ki value add cheyyavu)
_BOILERPLATE = re.compile(
    r"\b(?:notification|notifications|recruitment|recruitments|apply\s+online|"
    r"online\s+application|application\s+form|advertisement|advt|notification\s+out|"
    r"out\s+now|released|latest\s+update|complete\s+details|complete\s+guide|"
    r"official\s+notification|vacancy\s+details|job\s+notification|"
    r"registration\s+(?:open|opens|opened|started|live)|registrations?\s+open|"
    r"link\s+active|apply\s+here|posts)\b",
    re.I,
)
_TAIL = re.compile(r"\s*[–—|:,\-]\s*$")
_SPACE = re.compile(r"\s{2,}")


def subject(title: object, limit: int = 52) -> str:
    """'SSC CHSL 2026 Notification – Apply Online' → 'SSC CHSL 2026'.

    display_title() cleaning (complete details / apply online tails) + boilerplate
    words teesestundi. Year/org/exam tokens eppudu nilabadtayi — hook lo avi mukhyam.
    """
    try:
        from .opportunity_digest import display_title
        text = display_title(title, limit + 40)
    except Exception:  # noqa: BLE001 — digest import fail aina hook pani cheyali
        text = re.sub(r"<[^>]+>", " ", str(title or ""))
    text = _BOILERPLATE.sub(" ", text)
    text = re.sub(r"\s*\(\s*\)", " ", text)
    text = _TAIL.sub("", _SPACE.sub(" ", text)).strip(" –—|:,-")
    # Subtitle cut: "Infosys Off Campus Drive 2026 – System Engineer" → "Infosys Off Campus Drive 2026"
    # (hook lo main ento mattrame; left part 18+ chars unte mattrame — safe)
    for sep in (" – ", " — ", " | ", ": "):
        if sep in text:
            left, right = text.split(sep, 1)
            if len(left.strip()) >= 18:
                text = left.strip()
                break
    return text[:limit].strip()


def headline(title: object, telugu: bool = True, kind: str = "jobs") -> str:
    """Hook line: 'SSC CHSL 2026 ఉద్యోగాలు' (Telugu) / 'Infosys Off Campus Drive 2026 Jobs' (EN).

    Subject already lo 'ఉద్యోగాలు'/'jobs' unte malli add cheyyadu (idempotent).
    kind='walkin' → Telugu 'వాక్-ఇన్', English 'Walk-in'.
    """
    text = subject(title)
    if not text:
        return ""
    low = text.lower()
    if re.search(r"walk-?\s?in", low):       # title ne walk-in cheppindi → auto kind
        kind = "walkin"
    if telugu:
        if "ఉద్యోగాలు" in text or "ఉద్యోగ" in text:
            return text
        if kind == "walkin":
            # title lo already walk-in cheppindi → suffix vaddhu
            return text if ("వాక్" in text or "walk" in low) else f"{text} వాక్-ఇన్"
        return f"{text} ఉద్యోగాలు"
    if re.search(r"\b(jobs?|openings?|vacancies|careers?|walk-?in)\b", low):
        return text
    return f"{text} Walk-in" if kind == "walkin" else f"{text} Jobs"


def posts_chip(vacancies: object) -> str:
    """'2,000+ పోస్టులు' — meta unte mattrame (guess ledu)."""
    try:
        from .opportunity_digest import vacancies_count
        count = vacancies_count(vacancies)
    except Exception:  # noqa: BLE001
        count = str(vacancies or "").strip()
    return f"{count} పోస్టులు" if count else ""


def jobs_chip(vacancies: object) -> str:
    """English chip (software/private EN rows): '2,000+ openings'."""
    try:
        from .opportunity_digest import vacancies_count
        count = vacancies_count(vacancies)
    except Exception:  # noqa: BLE001
        count = str(vacancies or "").strip()
    return f"{count} openings" if count else ""


def article_lead(title: object, focus_keyword: str = "", vacancies: object = "",
                 last_date: str = "") -> str:
    """English hook paragraph (draft modata paragraph) — fabricate ledu.

    Only uses: cleaned subject + focus keyword + **nijamaina** vacancies/last date
    (caller isthene). Numbers/dates teliyakapote aa clause asalu raadu.
    """
    subj = subject(title) or subject(focus_keyword) or str(focus_keyword or "").strip()
    if not subj:
        return ""
    bits = []
    try:
        from .opportunity_digest import vacancies_count
        count = vacancies_count(vacancies)
    except Exception:  # noqa: BLE001
        count = ""
    if count:
        bits.append(f"{count} vacancies")
    if last_date:
        bits.append(f"last date {last_date}")
    lead = f"<strong>{_html.escape(subj)}</strong> recruitment"
    if bits:
        lead += " (" + ", ".join(bits) + ")"
    lead += (" — eligibility, important dates, vacancy details and the official "
             "apply link in one place.")
    return lead


def hook_html(title: object, focus_keyword: str = "", vacancies: object = "",
              last_date: str = "") -> str:
    """`<p class="su-hook">…</p>` block (idempotent marker)."""
    lead = article_lead(title, focus_keyword, vacancies, last_date)
    if not lead:
        return ""
    return f'<p class="su-hook">{lead}</p>'


def _first_para_text(html: str) -> str:
    m = re.search(r"<p\b[^>]*>(.*?)</p>", html or "", flags=re.S | re.I)
    return re.sub(r"<[^>]+>", " ", m.group(1)) if m else ""


def ensure_lead(html: str, title: object = "", focus_keyword: str = "",
                vacancies: object = "", last_date: str = "") -> str:
    """Article modata hook lead add (ledu ante mattrame) — idempotent.

    - Already `su-hook` block unte: as-is (rendu sari add avvadu).
    - Modati paragraph lo subject tokens already unte: vaddu (natural intro saripothundi).
    """
    body = html or ""
    if not body.strip():                 # empty body ki hook veyyadu
        return body
    if "su-hook" in body:
        return body
    subj = subject(title) or subject(focus_keyword)
    if not subj:
        return body
    tokens = [t for t in re.split(r"\s+", subj.lower()) if len(t) > 2 and not t.isdigit()]
    first = _first_para_text(body).lower()
    if tokens and sum(1 for t in tokens if t in first) >= max(1, len(tokens) - 1):
        return body        # intro lo already main subject undi — hook vaddu
    block = hook_html(title, focus_keyword, vacancies, last_date)
    return (block + body) if block else body


def pick_vacancies(recruitment: Optional[Dict]) -> str:
    """recruitment/evidence dict nunchi nijamaina vacancies value (unte mattrame)."""
    if not isinstance(recruitment, dict):
        return ""
    for key in ("vacancies", "total_vacancies", "vacancy_count"):
        val = recruitment.get(key)
        if val not in (None, "", 0, "0"):
            return str(val)
    return ""
