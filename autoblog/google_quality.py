# -*- coding: utf-8 -*-
"""Google people-first self-assessment and transparent methodology block.

This is not a ranking predictor. It turns Google's public Who/How/Why and
helpful-content questions into verifiable editorial checks before WordPress is
written. It rewards evidence and task completion, never keyword count.
"""
from __future__ import annotations

import html as _html
import re
from datetime import date
from typing import Dict, List, Tuple
from urllib.parse import urlparse

from . import config, validator

MARKER = "su-methodology"


def _source_rows(article: Dict) -> List[Tuple[str, str]]:
    rows, seen = [], set()
    sources = list(article.get("_deep_sources") or [])
    for source in sources:
        if isinstance(source, dict):
            url, title = source.get("url", ""), source.get("title", "")
        else:
            url = getattr(source, "url", "")
            title = getattr(source, "title", "")
        host = urlparse(url).netloc.lower().replace("www.", "") if url else ""
        if not url.startswith("http") or not host or host in seen:
            continue
        seen.add(host)
        rows.append((url, (title or host).strip()[:90]))
    return rows[:5]


def inject_methodology(html: str, article: Dict) -> str:
    """Visible Who/How/Why disclosure with crawlable editorial citations."""
    if MARKER in (html or "") or article.get("article_type") == "quiz":
        return html
    source_audit = article.get("_source_audit") or {}
    rows = _source_rows(article)
    reviewer = (getattr(config, "EDITORIAL_REVIEWER", "") or "").strip()
    reviewer_text = reviewer if reviewer else "Editorial review pending"
    links = "".join(
        '<li><a href="{}" target="_blank" rel="noopener">{}</a></li>'.format(
            _html.escape(url, quote=True), _html.escape(title))
        for url, title in rows
    )
    sources_text = (
        f"{source_audit.get('independent_domains', len(rows))} independent sources; "
        f"{source_audit.get('official_count', 0)} official source(s); "
        f"evidence confidence {source_audit.get('confidence', 0)}/100"
    )
    block = (
        f'<section class="{MARKER}" aria-labelledby="how-prepared">'
        '<h2 id="how-prepared">ఈ Article ఎలా Prepare చేశాము?</h2>'
        '<p><strong>Who:</strong> StudentUp editorial workflow; review: '
        f'{_html.escape(reviewer_text)}.</p>'
        '<p><strong>How:</strong> Automation source discovery, comparison, formatting కోసం మాత్రమే. '
        'Dates, Vacancies, Fee, Age Limit, Salary వంటి facts official sourceతో verify చేశాము; '
        'conflict ఉన్న claim publish చేయము.</p>'
        '<p><strong>Why:</strong> AP/TS applicants Official Notification చదివి safeగా '
        'Apply Online చేయడానికి clear, action-ready summary ఇవ్వడం.</p>'
        f'<p><strong>Evidence:</strong> {_html.escape(sources_text)}. '
        f'Last checked: {date.today().isoformat()}.</p>'
        + (f'<h3>Sources checked</h3><ul>{links}</ul>' if links else '')
        + '</section>'
    )
    # Before related links/schema so this stays part of the main editorial body.
    for marker in ('<section class="su-related"', '<script type="application/ld+json"'):
        pos = html.find(marker)
        if pos >= 0:
            return html[:pos] + block + html[pos:]
    return html + block


def audit(article: Dict, html: str, live: bool = False) -> Dict:
    plain = validator.strip_tags(html or "")
    source_audit = article.get("_source_audit") or {}
    editorial = article.get("_editorial_value") or {}
    content = article.get("_content_quality") or {}
    rows: List[Dict] = []

    def add(cid: str, ok: bool, detail: str, critical: bool = True) -> None:
        rows.append({"id": cid, "ok": bool(ok), "detail": detail,
                     "critical": critical})

    applicable = article.get("article_type") != "quiz"
    if not applicable:
        return {"applicable": False, "ok": True, "score": 100,
                "rows": [], "flags": [], "warnings": []}
    add("evidence", bool(source_audit.get("ok")),
        f"sources={source_audit.get('independent_domains', 0)}; "
        f"official={source_audit.get('official_count', 0)}; "
        f"confidence={source_audit.get('confidence', 0)}")
    add("claims", not editorial.get("unsupported_claims"),
        f"unsupported={len(editorial.get('unsupported_claims') or [])}")
    add("original_value", int(editorial.get("score") or 0) >= 55,
        f"editorial value={editorial.get('score', 0)}/100")
    add("reader_quality", not content.get("flags"),
        ", ".join(content.get("flags") or []) or "no filler/repetition")
    add("methodology", MARKER in html and "<strong>Who:</strong>" in html
        and "<strong>How:</strong>" in html and "<strong>Why:</strong>" in html,
        "transparent Who/How/Why")
    add("citations", len(_source_rows(article)) >= 3,
        f"{len(_source_rows(article))} crawlable source citations")
    topic = " ".join((str(article.get("title") or ""),
                      str(article.get("category") or ""))).lower()
    if re.search(r"hall ticket|admit card", topic):
        task_terms = r"direct link|download|registration|reporting|id proof|exam date"
        task_detail = "Hall Ticket status + download/exam-day details"
    elif re.search(r"result|merit list|scorecard|cut.?off", topic):
        task_terms = r"direct link|result status|scorecard|revaluation|supplementary|cut.?off"
        task_detail = "Result status + checking/next-step details"
    else:
        task_terms = r"apply|దరఖాస్తు|documents|డాక్యుమెంట్స్|eligibility"
        task_detail = "table + applicant action details"
    add("task_completion", "<table" in html and len(re.findall(
        task_terms, plain, re.I)) >= 2, task_detail)
    is_story = bool(re.search(r"success stor|selected candidate|ranker|topper|journey", topic))
    if is_story:
        add("verified_story", bool(source_audit.get("ok")) and len(_source_rows(article)) >= 3
            and not editorial.get("unsupported_claims"),
            "named success story requires 3-source identity/result support")
    add("quick_answer", "quick-answer" in html or "su-takeaways" in html,
        "direct answer/takeaways")
    bad_claims = re.findall(
        r"(?:100%\s*(?:job|selection|guarantee)|guaranteed\s+(?:job|selection)|"
        r"Google\s*(?:rank|approval)\s*guarantee)", plain, re.I)
    add("no_guarantees", not bad_claims,
        "no ranking/job guarantees" if not bad_claims else ", ".join(bad_claims[:3]))
    estimated_facts = re.findall(
        r"(?:estimated|approximately|around|అంచనా|సుమారు)\s*(?:గా\s*)?"
        r"(?:₹\s*)?[\d,.]+\s*(?:posts?|vacanc(?:y|ies)|ఖాళీ|పోస్టు|లక్ష|వేల)?",
        plain, re.I)
    add("no_estimated_critical_facts", not estimated_facts,
        "no estimated recruitment numbers" if not estimated_facts
        else ", ".join(estimated_facts[:3]))
    pending_public = bool(re.search(
        r"source-backed draft|review pending|verify (?:the )?official notice|"
        r"official (?:source|notification)తో verify చేయాలి", plain, re.I))
    add("review_state", not pending_public if live else True,
        "no draft/review-pending label on public article", critical=live)
    reviewer = (getattr(config, "EDITORIAL_REVIEWER", "") or "").strip()
    add("human_reviewer", bool(reviewer) if live else True,
        reviewer or "required before live publish", critical=live)

    scored = [r for r in rows if r["critical"] or not live]
    passed = sum(r["ok"] for r in scored)
    score = round(100 * passed / max(1, len(scored)))
    flags = [r["id"] + ": " + r["detail"] for r in rows
             if r["critical"] and not r["ok"]]
    warnings = [r["id"] + ": " + r["detail"] for r in rows
                if not r["critical"] and not r["ok"]]
    return {"applicable": True, "ok": not flags, "score": score,
            "rows": rows, "flags": flags, "warnings": warnings}
