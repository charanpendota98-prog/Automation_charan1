"""v72: Qualification auto-tag — 10th · 10+2 · ITI · Diploma · Degree · PG · B.Tech.

Enti chestundi (automatic, manual tagging ledu):
  * Post title + notification body ni chusi edi apply cheyyagalaro (education
    eligibility) detect chesi `studentup_qual` meta ki pampistundi.
  * Last date unte `studentup_last_date` (YYYY-MM-DD) kuda — site lo
    "⏳ 7 రోజుల్లో ముగుస్తుంది" badge + 'closing soon' filter ki.

Ee slugs WordPress theme (`inc/qual-filter.php`) chips ki exact ga match avvali —
anduku tests/v72_test.py lo slug parity test undi.

Bot meta pampakapoyina theme kuda title/content nunchi automatic ga detect
chestundi (double safety) — kaani bot value strong (article structure telusu).
"""

from __future__ import annotations

import re
from datetime import date, datetime
from typing import Dict, List, Optional

# Order = site chips order (theme inc/qual-filter.php same order).
QUALS: Dict[str, str] = {
    "10th": "10వ తరగతి",
    "inter": "ఇంటర్ (10+2)",
    "iti": "ఐటీఐ",
    "diploma": "డిప్లొమా",
    "degree": "డిగ్రీ",
    "pg": "పీజీ",
    "btech": "బీటెక్",
}

# Keywords — Telugu + English (lowercase compare).
KEYWORDS: Dict[str, List[str]] = {
    "10th": ["10వ తరగతి", "10వ", "10th", "tenth", "10th class", "10th pass",
             "పదవ తరగతి", "group d", "sgl"],
    "inter": ["ఇంటర్", "inter", "intermediate", "10+2", "plus two",
              "junior intermediate", "intermediate pass"],
    "iti": ["ఐటీఐ", "iti", "nctvt", "trade certificate"],
    "diploma": ["డిప్లొమా", "diploma", "polytechnic", "పాలిటెక్నిక్"],
    "degree": ["డిగ్రీ", "degree", "graduate", "graduation", "any degree",
               "b.a", "b.sc", "b.com", "బీఏ", "బీఎస్సీ", "బీకాం"],
    "pg": ["పీజీ", "pg", "post graduate", "postgraduate", "m.a", "m.sc",
           "m.com", "mba", "ఎంఏ", "ఎంఎస్సీ", "ఎంబీఏ"],
    "btech": ["బీటెక్", "b.tech", "btech", "b.e", "engineering", "ఇంజినీరింగ్"],
}

_ISO = re.compile(r"\b(\d{4}-\d{2}-\d{2})\b")


def detect(text: str) -> List[str]:
    """Text nunchi qualification slugs (order = QUALS order)."""
    hay = (text or "").lower()
    if not hay:
        return []
    hit: List[str] = []
    for slug in QUALS:
        for word in KEYWORDS[slug]:
            if word.lower() in hay:
                hit.append(slug)
                break
    return hit


def detect_meta(article: dict) -> str:
    """Meta value string — 'degree pg' (space separated, empty ledu ante)."""
    parts = detect(article_text(article))
    # 10వ/ఇంటర్ unte 'all' lantidi — jobs lo 'any degree' unte degree kuda vastundi (fine)
    return " ".join(parts)


def article_text(article: dict) -> str:
    """Article nunchi detect ki saripoyina text (title + eligibility + body)."""
    if not isinstance(article, dict):
        return str(article or "")
    chunks: List[str] = [
        str(article.get("title") or ""),
        str(article.get("meta_description") or ""),
        str(article.get("focus_keyword") or ""),
    ]
    rec = article.get("recruitment") or {}
    if isinstance(rec, dict):
        chunks.append(str(rec.get("eligibility") or ""))
        chunks.append(str(rec.get("qualification") or ""))
        chunks.append(str(rec.get("post_name") or ""))
    body = article.get("body_html") or article.get("content_html") or ""
    if body:
        # HTML tags teesi (keyword detect clean)
        chunks.append(re.sub(r"<[^>]+>", " ", str(body))[:20000])
    for key in ("eligibility", "qualification", "key_facts", "faq"):
        val = article.get(key)
        if isinstance(val, list):
            chunks.extend(str(v) for v in val)
        elif val:
            chunks.append(str(val))
    return " ".join(chunks)


def last_date(article: dict) -> str:
    """Article nunchi last date (YYYY-MM-DD) — guess cheyyamu, unte matrame."""
    if not isinstance(article, dict):
        return ""
    rec = article.get("recruitment") or {}
    for raw in (
        (rec.get("apply_end") if isinstance(rec, dict) else ""),
        article.get("last_date"),
        article.get("apply_end"),
        article.get("deadline"),
    ):
        m = _ISO.search(str(raw or ""))
        if m:
            try:
                datetime.strptime(m.group(1), "%Y-%m-%d")
            except ValueError:
                continue
            return m.group(1)
    return ""


def post_meta(article: dict) -> Dict[str, str]:
    """WP REST 'meta' payload ki add cheyyalsina fields (v72).

    Returns: {'studentup_qual': 'degree pg', 'studentup_last_date': '2026-10-15'}
    (khali aithe aa key pampamu — meta overwrite avvadu).
    """
    out: Dict[str, str] = {}
    quals = detect_meta(article)
    if quals:
        out["studentup_qual"] = quals
    end = last_date(article)
    if end:
        out["studentup_last_date"] = end
    return out


def describe(article: dict, today: Optional[date] = None) -> str:
    """Log/Telegram line — 'అర్హత: డిగ్రీ · పీజీ · closes 2026-10-15 (26 రోజులు)'."""
    quals = detect_meta(article)
    labels = " · ".join(QUALS[s] for s in quals.split() if s in QUALS)
    end = last_date(article)
    parts = []
    if labels:
        parts.append("అర్హత: " + labels)
    if end:
        try:
            left = (datetime.strptime(end, "%Y-%m-%d").date()
                    - (today or date.today())).days
            parts.append(f"closes {end} ({left} రోజులు)")
        except ValueError:
            parts.append("closes " + end)
    return " · ".join(parts) or "అర్హత: general"
