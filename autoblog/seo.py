"""SEO enhancer — Rank Math 100% score kosam article optimize chestundi.

Checks (Rank Math):
  - focus keyword: SEO title lo, meta description lo, URL (slug) lo,
    first paragraph lo, subheadings lo
  - keyword density (~1-1.5%), content length 1500+ words
  - TOC (table of contents), internal links, external links
  - image alt text lo keyword
"""

import logging
import re
from typing import Dict, List, Optional
from urllib.parse import urlparse

log = logging.getLogger("autoblog.seo")


def _slugify_id(text: str, index: int) -> str:
    ascii_part = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:30]
    return ascii_part or f"section-{index}"


def add_table_of_contents(html: str) -> str:
    """First paragraph tarvata TOC insert chestundi + h2 anchors."""
    h2s = re.findall(r"<h2[^>]*>(.*?)</h2>", html, flags=re.S)
    if len(h2s) < 3:
        return html

    items = []
    for i, raw in enumerate(h2s, 1):
        clean = re.sub(r"<[^>]+>", "", raw).strip()
        anchor = _slugify_id(clean, i)
        items.append(f'<li><a href="#{anchor}">{clean}</a></li>')

    toc = ('<h2 id="table-of-contents">విషయ సూచిక (Table of Contents)</h2>'
           "<ul>" + "".join(items) + "</ul>")

    # TOC after the first paragraph (intro paragraph first ga untali SEO ki)
    idx = html.find("</p>")
    if idx == -1:
        return toc + html
    end = idx + 4
    html = html[:end] + toc + html[end:]

    # h2 tags ki ids
    count = [0]

    def _add_id(m: re.Match) -> str:
        count[0] += 1
        inner = m.group(2)
        clean = re.sub(r"<[^>]+>", "", inner).strip()
        anchor = _slugify_id(clean, count[0])
        return f'<h2 id="{anchor}">{inner}</h2>'

    return re.sub(r"<h2([^>]*)>(.*?)</h2>", lambda m: _add_id(m), html, flags=re.S)


def ensure_keyword_first_para(html: str, keyword: str) -> str:
    """Focus keyword first paragraph lo leda ante natural intro para add."""
    if not keyword:
        return html
    m = re.search(r"<p>(.*?)</p>", html, flags=re.S)
    first = re.sub(r"<[^>]+>", "", m.group(1)).lower() if m else ""
    if keyword.lower() in first:
        return html
    intro = (f"<p><strong>{keyword}</strong> గురించి పూర్తి వివరాలు — ఎలిజిబిలిటీ, "
             "అప్లై చేసే విధానం, ముఖ్యమైన తేదీలు, టిప్స్ అన్నీ ఈ ఆర్టికల్‌లో "
             "స్టెప్ బై స్టెప్‌గా తెలుసుకోండి.</p>")
    return intro + html


def add_internal_links(html: str, links: List[Dict[str, str]]) -> str:
    """Related articles section (internal links) add."""
    if not links:
        return html
    items = "".join(
        f'<li><a href="{l["link"]}">{l["title"]}</a></li>' for l in links
    )
    section = ('<h2 id="related-articles">మరిన్ని ఉపయోగకరమైన ఆర్టికల్స్</h2>'
               f"<ul>{items}</ul>")
    return html + section


def add_external_links(html: str, links: List[Dict[str, str]]) -> str:
    """Official/authority links (external) section add."""
    valid = []
    for l in links or []:
        url = (l.get("url") or "").strip()
        text = (l.get("text") or "Official Website").strip()
        if url.startswith("http") and urlparse(url).netloc:
            valid.append(f'<li><a href="{url}" target="_blank" '
                         f'rel="nofollow noopener">{text}</a></li>')
    if not valid:
        return html
    section = ('<h2 id="official-links">అధికారిక లింక్స్ (Official Links)</h2>'
               f"<ul>{''.join(valid)}</ul>")
    return html + section


def word_count(html: str) -> int:
    text = re.sub(r"<[^>]+>", " ", html)
    return len([w for w in text.split() if w])


def enhance(
    html: str,
    focus_keyword: str,
    internal_links: List[Dict[str, str]],
    external_links: List[Dict[str, str]],
) -> str:
    """Full SEO pipeline: keyword intro -> TOC -> internal + external links."""
    html = ensure_keyword_first_para(html, focus_keyword)
    html = add_table_of_contents(html)
    html = add_internal_links(html, internal_links)
    html = add_external_links(html, external_links)
    n = word_count(html)
    log.info("SEO enhanced: %d words, keyword=%r", n, focus_keyword)
    if n < 1200:
        log.warning("Word count takkuva (%d) — Rank Math full score kosari 1500+ kavali", n)
    return html


def rankmath_meta(
    focus_keyword: str,
    description: str,
    seo_title: str,
) -> Dict[str, str]:
    """Rank Math REST meta payload (plugin active unte work avtundi)."""
    return {
        "rank_math_focus_keyword": focus_keyword[:120],
        "rank_math_description": description[:160],
        "rank_math_title": seo_title[:160],
    }
