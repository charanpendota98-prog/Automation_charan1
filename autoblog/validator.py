"""Article QA engine — originality proof, validation scoring, HTML sanitizer.

1. originality_score(): 5-gram shingle containment — final article vs
   source texts. Idi measurable "no copy" proof (prompt hope kadu).
2. sanitize_html(): Gemini output lo ALLOWED tags tappa anni strip.
3. validate_article(): Rank Math-style checks -> score/100 + issues.
"""

import logging
import re
from typing import Dict, List, Optional

log = logging.getLogger("autoblog.validator")

ALLOWED_TAGS = {
    "h2", "h3", "p", "ul", "ol", "li", "strong", "em",
    "table", "thead", "tbody", "tr", "th", "td", "a",
}


def strip_tags(html: str) -> str:
    return re.sub(r"<[^>]+>", " ", html)


def _normalize_words(text: str) -> List[str]:
    text = re.sub(r"[^\w\u0c00-\u0c7f]+", " ", text.lower())
    return re.sub(r"\s+", " ", text).split()


def text_shingles(text: str, n: int = 5) -> set:
    words = _normalize_words(text)
    return {" ".join(words[i:i + n]) for i in range(len(words) - n + 1)}


def originality_score(article_html: str, source_texts: List[str]) -> float:
    """100 = fully original. Worst-case containment across sources."""
    art_shingles = text_shingles(strip_tags(article_html))
    if not art_shingles:
        return 100.0
    worst = 0.0
    for src in source_texts or []:
        src_shingles = text_shingles(src)
        if not src_shingles:
            continue
        overlap = len(art_shingles & src_shingles)
        containment = overlap / min(len(art_shingles), len(src_shingles))
        worst = max(worst, containment)
    return round(100.0 * (1.0 - worst), 1)


def sanitize_html(html: str) -> str:
    """Allowed tags tappa anni strip (content ni preserve chesi)."""
    if not html:
        return html
    # full script/style blocks remove
    html = re.sub(r"<(script|style|iframe|form)[^>]*>.*?</\1>", "", html,
                  flags=re.S | re.I)
    html = re.sub(r"</?(html|head|body|!doctype)[^>]*>", "", html, flags=re.I)
    # markdown artifacts
    html = html.replace("```html", "").replace("```", "")

    def _keep(m: re.Match) -> str:
        return m.group(0) if m.group(1).lower() in ALLOWED_TAGS else ""

    html = re.sub(r"</?([a-zA-Z][a-zA-Z0-9]*)[^>]*>", _keep, html)
    # empty paragraphs / excess newlines clean
    html = re.sub(r"<p>\s*</p>", "", html)
    html = re.sub(r"\n{3,}", "\n\n", html)
    return html.strip()


def word_count(html: str) -> int:
    return len(_normalize_words(strip_tags(html)))


def reading_minutes(words: int) -> int:
    return max(1, round(words / 200))


def validate_article(article: Dict, final_html: str = "") -> Dict:
    """Rank Math-style QA score. Returns {score, issues, words, reading_min}."""
    issues: List[str] = []
    html = final_html or article.get("content_html", "")
    plain = strip_tags(html)
    words = word_count(html)
    kw = (article.get("focus_keyword") or "").strip()

    def add(ok: bool, points: int, msg: str) -> int:
        if not ok:
            issues.append(msg)
        return points if ok else 0

    score = 0
    score += add(bool(kw), 5, "focus_keyword ledu")
    if kw:
        score += add(kw.lower() in article.get("title", "").lower(), 10,
                     "focus keyword title lo ledu")
        first_p = re.search(r"<p>(.*?)</p>", html, flags=re.S)
        first_txt = strip_tags(first_p.group(1)) if first_p else ""
        score += add(kw.lower() in first_txt.lower(), 10,
                     "focus keyword first paragraph lo ledu")
        h2s = re.findall(r"<h2[^>]*>(.*?)</h2>", html, flags=re.S)
        kw_in_h2 = sum(1 for h in h2s if kw.lower() in strip_tags(h).lower())
        score += add(kw_in_h2 >= 1, 10, "focus keyword subheadings lo ledu")
        density = plain.lower().count(kw.lower()) / max(1, words)
        score += add(0.004 <= density <= 0.03, 5,
                     f"keyword density out of range ({density:.3f})")

    score += add(words >= 1500, 15, f"word count takkuva ({words} < 1500)")
    score += add("<table" in html, 5, "table ledu (snippet eligibility)")
    score += add(len(article.get("faq") or []) >= 3, 10, "FAQ 3+ kavali")
    score += add(bool(article.get("external_links")), 5, "external links ledu")
    meta_desc = article.get("meta_description") or ""
    score += add(120 <= len(meta_desc) <= 170 and (not kw or kw.lower() in meta_desc.lower()),
                 10, "meta description length/keyword problem")
    score += add(5 <= len(article.get("tags") or []) <= 8, 5, "tags 5-8 kavali")
    score += add(bool(article.get("quick_answer")), 5, "quick_answer ledu (snippet bait)")
    score += add(len(article.get("secondary_keywords") or []) >= 3, 5,
                 "secondary keywords 3+ kavali")

    return {
        "score": score,
        "issues": issues,
        "words": words,
        "reading_min": reading_minutes(words),
    }
