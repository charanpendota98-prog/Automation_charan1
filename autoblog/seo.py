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

from . import config

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


INTRO_TEMPLATES = [
    "<p><strong>{kw}</strong> గురించి మీరు వెతుకుతున్న పూర్తి వివరాలు — ఎలిజిబిలిటీ, అప్లై విధానం, ఫీ, డాక్యుమెంట్స్ — అన్నీ ఈ ఆర్టికల్‌లో స్టెప్ బై స్టెప్‌గా ఉన్నాయి.</p>",
    "<p><strong>{kw}</strong> సంపూర్ణ సమాచారం ఒకే చోట — స్కీమ్ వివరాలు, అప్లై స్టెప్స్, ముఖ్యమైన అంశాలు చివరి వరకూ తెలుసుకోండి.</p>",
    "<p><strong>{kw}</strong> తో ముడిపడిన ప్రతి ముఖ్యమైన అంశం ఈ గైడ్‌లో స్పష్టంగా వివరించబడింది — పూర్తిగా చదవండి.</p>",
    "<p><strong>{kw}</strong> లేటెస్ట్ అప్డేట్ పూర్తి సమాచారం ఇక్కడ — ఎలిజిబిలిటీ నుంచి అప్లై ప్రాసెస్ వరకు అన్నీ ఉన్నాయి.</p>",
]

RELATED_HEADINGS = [
    "మరిన్ని ఉపయోగకరమైన ఆర్టికల్స్",
    "ఇవి కూడా చదవండి",
    "సంబంధిత ఆర్టికల్స్",
]


def _pick(seq, seed: str):
    return seq[hash(seed) % len(seq)] if seed else seq[0]


def ensure_keyword_first_para(html: str, keyword: str, seed: str = "") -> str:
    """Focus keyword first paragraph lo leda ante VARIED intro para add.

    Templates rotate avtayi — prathi post lo oke para repeat avvakunda
    (boilerplate/spam footprint avoid — important!).
    """
    if not keyword:
        return html
    m = re.search(r"<p>(.*?)</p>", html, flags=re.S)
    first = re.sub(r"<[^>]+>", "", m.group(1)).lower() if m else ""
    if keyword.lower() in first:
        return html
    intro = _pick(INTRO_TEMPLATES, (seed or keyword)).format(kw=keyword)
    return intro + html


def add_internal_links(html: str, links: List[Dict[str, str]], seed: str = "") -> str:
    """Related articles section (internal links) — heading rotate avtundi."""
    if not links:
        return html
    items = "".join(
        f'<li><a href="{l["link"]}">{l["title"]}</a></li>' for l in links
    )
    heading = _pick(RELATED_HEADINGS, seed)
    section = f'<h2 id="related-articles">{heading}</h2><ul>{items}</ul>'
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


def _esc(t: str) -> str:
    return (t or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def quick_answer_block(focus_keyword: str, quick_answer: str, updated: str) -> str:
    """Featured-snippet bait: direct answer top lo + fresh date."""
    if not quick_answer:
        return ""
    return (
        f'<h2 id="quick-answer">Quick Answer – {focus_keyword}</h2>'
        f"<p><strong>{quick_answer.strip()}</strong></p>"
        f'<p><em>Last Updated: {updated} | studentup.in</em></p>'
    )


def reading_badge(words: int, minutes: int) -> str:
    """Top lo reading time badge — UX signal + dwell time."""
    return (f'<p><em>⏱️ Reading Time: ~{minutes} నిమిషాలు · {words} పదాలు · '
            f'తెలుగు + English</em></p>')


def trust_box(date_str: str, source_domains: Optional[List[str]] = None) -> str:
    """E-E-A-T trust signals: editorial review + sources + freshness."""
    domains = ", ".join(source_domains[:4]) if source_domains else "official notification"
    return (
        '<h2 id="about-this-article">About This Article</h2>'
        "<p>ఈ ఆర్టికల్ <strong>studentup.in</strong> ఎడిటోరియల్ టీమ్ తయారు చేసింది — "
        "అధికారిక నోటిఫికేషన్ & ప్రముఖ వార్తా సంస్థల సమాచారం ఆధారంగా "
        f"({domains}) సమీక్షించబడింది. తేదీ: {date_str}. "
        "ఏమైనా సందేహాలు ఉంటే అధికారిక వెబ్‌సైట్‌లో ధృవీకరించండి.</p>"
    )


def schema_jsonld(
    title: str,
    description: str,
    faq: List[Dict[str, str]],
    date_published: str,
    slug: str,
    date_modified: str = "",
    category: str = "",
    list_items: Optional[List[str]] = None,
) -> str:
    """Google rich results: FAQPage + Article + BreadcrumbList (+ItemList)."""
    import json as _json

    if not config.SEO_SCHEMA_ENABLED:
        return ""
    scripts = []
    clean_faq = [f for f in (faq or []) if f.get("question") and f.get("answer")]
    if clean_faq:
        scripts.append({
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": [
                {
                    "@type": "Question",
                    "name": f["question"],
                    "acceptedAnswer": {"@type": "Answer", "text": f["answer"]},
                }
                for f in clean_faq
            ],
        })
    scripts.append({
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": title[:110],
        "description": description[:300],
        # Google guideline: datePublished preserve, dateModified matrame update
        "datePublished": date_published,
        "dateModified": date_modified or date_published,
        # E-E-A-T: Person author (editorial team) + publisher logo rich-results
        "author": {
            "@type": "Person",
            "name": "StudentUp Editorial Team",
            "url": config.WP_SITE.rstrip("/") + "/about/",
            "worksFor": {"@type": "Organization", "name": "studentup.in"},
        },
        "editor": {"@type": "Person", "name": "StudentUp Editorial Team"},
        "publisher": {"@type": "Organization", "name": "studentup.in",
                      "url": config.WP_SITE,
                      **({"logo": {"@type": "ImageObject",
                                   "url": config.SITE_LOGO_URL}}
                         if config.SITE_LOGO_URL else {})},
        "mainEntityOfPage": f"{config.WP_SITE}/{slug}/",
        "inLanguage": "te",
    })
    if list_items:
        scripts.append({
            "@context": "https://schema.org",
            "@type": "ItemList",
            "name": title[:110],
            "numberOfItems": len(list_items),
            "itemListElement": [
                {"@type": "ListItem", "position": i, "name": name[:110]}
                for i, name in enumerate(list_items, 1)
            ],
        })
    scripts.append({
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home",
             "item": config.WP_SITE},
            {"@type": "ListItem", "position": 2, "name": category or "Articles",
             "item": f"{config.WP_SITE}/"},
            {"@type": "ListItem", "position": 3, "name": title[:110]},
        ],
    })
    return "".join(
        '<script type="application/ld+json">'
        + _json.dumps(s, ensure_ascii=False)
        + "</script>"
        for s in scripts
    )


def enhance(
    html: str,
    focus_keyword: str,
    internal_links: List[Dict[str, str]],
    external_links: List[Dict[str, str]],
    quick_answer: str = "",
    faq: Optional[List[Dict[str, str]]] = None,
    date_str: str = "",
    date_modified: str = "",
    slug: str = "",
    title: str = "",
    description: str = "",
    category: str = "",
    source_domains: Optional[List[str]] = None,
    list_items: Optional[List[str]] = None,
) -> str:
    """Full top-level SEO pipeline: reading badge -> quick answer -> keyword
    intro (varied) -> TOC -> internal/external links -> E-E-A-T box ->
    FAQ+Article+Breadcrumb(+ItemList) JSON-LD schema."""
    from . import validator as _v

    words = _v.word_count(html)
    minutes = _v.reading_minutes(words)
    html = reading_badge(words, minutes) + html
    html = ensure_keyword_first_para(html, focus_keyword, seed=slug)
    if quick_answer:
        # visible badge: modified date (fresh look); schema published original
        html = quick_answer_block(focus_keyword, quick_answer,
                                  date_modified or date_str) + html
    html = add_table_of_contents(html)
    html = add_internal_links(html, internal_links, seed=slug)
    html = add_external_links(html, external_links)
    # Read-also block: article end lo related posts (session time + crawl)
    if internal_links:
        items = "".join(
            f'<li><a href="{l["link"]}" internal="true">'
            f'{_esc(l["title"])}</a></li>'
            for l in internal_links[:4]
        )
        html += ('<h2 id="read-also">వీటిని కూడా చదవండి</h2>'
                 f'<ul>{items}</ul>')
    html += trust_box(date_modified or date_str, source_domains)
    html += schema_jsonld(title or focus_keyword, description or "", faq or [],
                          date_str, slug, category=category,
                          date_modified=date_modified, list_items=list_items)
    log.info("SEO enhanced: %d words, keyword=%r", words, focus_keyword)
    if words < 1200:
        log.warning("Word count takkuva (%d) — Rank Math full score kosari 1500+ kavali", words)
    return html


def rankmath_meta(
    focus_keyword: str,
    description: str,
    seo_title: str,
    secondary_keywords: Optional[List[str]] = None,
) -> Dict[str, str]:
    """Rank Math REST meta payload (plugin active unte work avtundi).

    Focus keyword field lo primary + secondary keywords comma tho —
    Rank Math anni track chestundi.
    """
    keywords = focus_keyword[:120]
    if secondary_keywords:
        extras = ", ".join(k.strip() for k in secondary_keywords if k.strip())[:120]
        if extras:
            keywords = f"{keywords}, {extras}"[:240]
    meta = {
        "rank_math_focus_keyword": keywords,
        "rank_math_description": description[:160],
        "rank_math_title": seo_title[:160],
        # Social sharing (Facebook/WhatsApp/Twitter preview) — CTR boost
        "rank_math_facebook_title": seo_title[:160],
        "rank_math_facebook_description": description[:160],
        "rank_math_twitter_title": seo_title[:160],
        "rank_math_twitter_description": description[:160],
        "rank_math_twitter_use_open_graph": "on",
    }
    # Google Discover eligibility: big image preview allow
    # (Rank Math > Titles & Meta lo kuda set cheyandi — idhi per-post)
    if config.DISCOVER_META_ENABLED:
        meta["rank_math_robots"] = ["index, follow, max-image-preview:large"]
    return meta


def insert_ad_shortcodes(html: str, shortcode: str, max_ads: int = 3,
                         cls_safe: bool = True) -> str:
    """In-content ad shortcodes — viewability-optimized positions.

    High-viewability slots (users actually SEE these ads):
      after 2nd paragraph (above-fold-ish), after each </table> (natural
    pause point), mid-article, before FAQ. Max ads capped (default 3) —
    content-dominance policy safe. Long articles ki 4-5 ok (news standard).

    cls_safe: min-height wrapper tho ad space reserve chestundi —
    layout shift (CLS) radu -> Core Web Vitals + ad viewability better.
    """
    if not shortcode:
        return html
    import re as _re

    positions = []
    paras = list(_re.finditer(r"</p>", html))
    if len(paras) >= 2:
        positions.append(paras[1].end())            # after 2nd para
    for m in _re.finditer(r"</table>", html):
        positions.append(m.end())                   # tables tarvata (pause point)
    if len(paras) >= 8:
        positions.append(paras[len(paras) // 2].end())  # mid article
    faq_m = _re.search(r"<h2[^>]*>[^<]*FAQ", html)
    if faq_m:
        positions.append(faq_m.start())             # FAQ mundu
    positions = sorted(set(positions))[:max(max_ads, 0)]
    if not positions:
        return html

    if cls_safe:
        open_w = '<div style="min-height:280px">'
        close_w = "</div>"
    else:
        open_w = close_w = ""

    out, last = [], 0
    for pos in positions:
        out.append(html[last:pos])
        out.append(f"\n{open_w}{shortcode}{close_w}\n")
        last = pos
    out.append(html[last:])
    return "".join(out)


# ------------------------------------------------------------------ slug optimizer

# Rank Math URL check: stopwords penalty + focus keyword in URL
SLUG_STOPWORDS = {
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "is", "are", "was", "were", "be", "been",
    "how", "what", "when", "where", "who", "why", "will", "that", "this",
    "it", "its", "as", "your", "you", "elaa", "andhu",
}


def optimize_slug(slug: str, focus_keyword: str = "", max_len: int = 60) -> str:
    """Rank Math-friendly slug: stopwords strip + keyword tokens include.

    Trick: focus keyword lo English tokens (ssc, cgl, 2026...) slug lo
    pakka untayi -> 'Focus Keyword in URL' check pass avtundi.
    """
    words = [w for w in (slug or "").lower().split("-") if w]
    cleaned = [w for w in words if w not in SLUG_STOPWORDS]
    base = "-".join(cleaned)[:max_len].strip("-")

    fk_tokens = [t.lower() for t in re.findall(r"[a-zA-Z0-9]+", focus_keyword or "")]
    fk_tokens = [t for t in fk_tokens if t and t not in SLUG_STOPWORDS]
    if fk_tokens:
        have = set(base.split("-"))
        missing = [t for t in fk_tokens if t not in have]
        if missing:
            prefix = "-".join(missing)
            if base and len(prefix) + 1 + len(base) <= max_len:
                base = f"{prefix}-{base}"
            elif not base:
                base = prefix[:max_len]
            else:
                # slug full ayyindi -> keyword prefix ki priority
                base = f"{prefix}-{base}"[:max_len]
    return (base or "-".join(words))[:max_len].strip("-") or "studentup-post"
