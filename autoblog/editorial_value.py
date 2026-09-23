# -*- coding: utf-8 -*-
"""v104 — EDITORIAL VALUE + CLAIM PROVENANCE LEDGER.

Original wording alone is not enough. A paraphrased source summary can still be
low-value and risky at scale. This module records which sources support the
article's factual claims and scores whether the article adds practical value:
actions, checklists, local context, comparison/table structure and source
transparency.

The ledger is machine evidence for human review — not a fake E-E-A-T badge.
"""
from __future__ import annotations

import re
from datetime import date
from typing import Dict, Iterable, List
from urllib.parse import urlparse

from . import deep_research, validator

_DATE = re.compile(r"\b(?:\d{4}-\d{1,2}-\d{1,2}|\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4})\b")
_NUM = re.compile(r"\b\d[\d,]{1,7}\b")
_ACTION = re.compile(
    r"\b(?:apply|download|check|visit|submit|carry|upload|verify|open|select|"
    r"follow|contact|register|prepare|read|చూడండి|దరఖాస్తు|డౌన్లోడ్|సంప్రదించండి)\b",
    re.I,
)
_LOCAL = re.compile(r"\b(?:telangana|andhra pradesh|hyderabad|warangal|vijayawada|"
                    r"district|mandal|telugu|తెలంగాణ|ఆంధ్రప్రదేశ్|జిల్లా)\b", re.I)


def _source_obj(source, index: int) -> Dict:
    if isinstance(source, dict):
        url = source.get("url", "")
        title = source.get("title", "")
        text = source.get("text", "")
    else:
        url = getattr(source, "url", "")
        title = getattr(source, "title", "")
        text = getattr(source, "text", "")
    return {
        "id": f"source-{index}",
        "url": url,
        "title": title,
        "domain": urlparse(url).netloc.lower().replace("www.", ""),
        "tier": deep_research.source_tier(url) if url else 3,
        "checked_at": date.today().isoformat(),
        "word_count": len((text or "").split()),
        "has_text": bool(text),
    }


def _tokens(text: str) -> set:
    return {x.lower() for x in re.findall(r"[\w\u0c00-\u0c7f]+", text or "")
            if len(x) > 2}


def _claim_support(claim: str, source_texts: Iterable[str]) -> List[int]:
    """Approximate support: exact date/number or enough claim tokens in source."""
    support = []
    ct = _tokens(claim)
    for i, source in enumerate(source_texts):
        st = source or ""
        claim_dates = [d.group(0) for d in _DATE.finditer(claim)]
        claim_nums = [n.group(0).replace(",", "") for n in _NUM.finditer(claim)]
        source_flat = st.replace(",", "")
        # Numeric/date claims require their specific values. Generic word
        # overlap must never "support" a made-up vacancy or deadline.
        has_fact = bool(claim_dates or claim_nums)
        facts_ok = (all(d in st for d in claim_dates)
                    and all(n in source_flat for n in claim_nums))
        if (facts_ok if has_fact else
                (len(ct) >= 4 and len(ct & _tokens(st)) / len(ct) >= 0.62)):
            support.append(i)
    return support


def build_ledger(article: Dict, html: str, sources: Iterable) -> Dict:
    source_list = list(sources or [])
    source_texts = [getattr(s, "text", "") if not isinstance(s, dict)
                    else s.get("text", "") for s in source_list]
    records = [_source_obj(s, i + 1) for i, s in enumerate(source_list)]
    text = validator.strip_tags(html or "")
    dates = sorted({m.group(0) for m in _DATE.finditer(text)})
    numbers = sorted({m.group(0) for m in _NUM.finditer(text)})
    claims = []
    # Facts are evidence-sensitive; do not pretend every prose sentence is a
    # claim. Keep the ledger compact and reviewable.
    for value in dates + numbers:
        context = next((s.strip() for s in re.split(r"[.!?\n]", text)
                        if value in s), value)
        support = _claim_support(context, source_texts)
        claims.append({"claim": context[:240], "value": value,
                       "supported_by": [records[i]["id"] for i in support],
                       "status": "supported" if support else "unverified"})

    source_links = len(re.findall(r"<a\b[^>]+href=[\"']https?://", html or "", re.I))
    headings = len(re.findall(r"<h[2-4]\b", html or "", re.I))
    lists = len(re.findall(r"<(?:ul|ol|table)\b", html or "", re.I))
    action_count = len(_ACTION.findall(text))
    local_count = len(_LOCAL.findall(text))
    verified = sum(1 for c in claims if c["status"] == "supported")
    unsupported = [c for c in claims if c["status"] == "unverified"]

    # Value score is advisory: it rewards usefulness, never rewards word count.
    score = 30
    score += min(20, len(records) * 5)
    score += min(15, action_count * 2)
    score += min(10, headings * 2)
    score += min(10, lists * 3)
    score += min(10, local_count * 2)
    score += 5 if source_links else 0
    if claims:
        score += round(10 * verified / len(claims))
        score -= min(25, len(unsupported) * 5)
    score = max(0, min(100, score))

    return {
        "version": "v104",
        "checked_at": date.today().isoformat(),
        "score": score,
        "grade": "strong" if score >= 75 else "review" if score >= 55 else "thin-risk",
        "sources": records,
        "claims": claims[:80],
        "unsupported_claims": unsupported[:20],
        "signals": {"source_links": source_links, "headings": headings,
                    "lists_or_tables": lists, "action_terms": action_count,
                    "local_context_terms": local_count},
        "recommendation": (
            "publish candidate: source-backed practical value"
            if score >= 75 and not unsupported else
            "human review: add original context or verify unsupported claims"
        ),
    }


def gate(ledger: Dict, minimum: int = 55) -> List[str]:
    flags = []
    if ledger.get("score", 0) < minimum:
        flags.append(f"EDITORIAL-VALUE score {ledger.get('score', 0)} < {minimum}")
    if ledger.get("unsupported_claims"):
        flags.append(f"UNVERIFIED-CLAIMS {len(ledger['unsupported_claims'])}")
    if not ledger.get("sources"):
        flags.append("NO-PROVENANCE-SOURCES")
    return flags
