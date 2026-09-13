"""Revenue maximization blocks — 100% AdSense/FTC compliant.

1. telegram_cta_block(): prathi post end lo "Join Channel" CTA —
   repeat visitors = more pageviews = more ad impressions (legit).
2. affiliate_block(): relevent posts lo affiliate links section —
   rel="sponsored nofollow" + disclosure tho (Google/FTC compliant).
"""

import logging
import re
from html import escape
from typing import Dict, List, Optional
from urllib.parse import urlparse

from . import config, validator

log = logging.getLogger("autoblog.monetize")


def _safe_http_url(raw: str) -> Optional[str]:
    """Only absolute HTTP(S) links enter generated HTML attributes."""
    raw = (raw or "").strip()
    parsed = urlparse(raw)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        return None
    return escape(raw, quote=True)


def telegram_cta_block() -> str:
    """Post end lo channel join CTA — repeat traffic engine."""
    url = _safe_http_url(config.TELEGRAM_CHANNEL_URL)
    if not url:
        return ""
    return (
        '<h2 id="join-alerts">రోజూ Job Alerts Free గా పొందండి 📥</h2>'
        "<p>కొత్త <strong>government jobs, scholarships, results, admit cards</strong> — "
        "అన్నీ మీకు మొదటగా కావాలా? మా "
        f'<a href="{url}" target="_blank" rel="noopener"><strong>Telegram '
        "Channel లో జాయిన్ అవ్వండి</strong></a> (పూర్తిగా ఉచితం). ప్రతిరోజూ "
        "అప్‌డేట్స్ మీ ఫోన్ కి నేరుగా!</p>"
    )


def _parse_affiliates() -> List[Dict[str, str]]:
    """AFFILIATE_LINKS format: 'label|url|keywords' (okka line okati)."""
    out = []
    for line in (config.AFFILIATE_LINKS or "").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = [p.strip() for p in line.split("|")]
        safe_url = _safe_http_url(parts[1] if len(parts) >= 2 else "")
        if len(parts) >= 2 and parts[0] and safe_url:
            out.append({
                "label": parts[0][:120],
                "url": safe_url,
                "keywords": parts[2].lower() if len(parts) > 2 else "",
            })
    return out


def affiliate_block(article: Dict) -> str:
    """Relevant posts lo affiliate section (disclosure + sponsored rel)."""
    affiliates = _parse_affiliates()
    if not affiliates:
        return ""
    blob = f"{article.get('title', '')} {article.get('category', '')}".lower()
    matched = [
        a for a in affiliates
        if not a["keywords"] or any(k in blob for k in a["keywords"].split(","))
    ]
    if not matched:
        return ""
    items = "".join(
        f'<li><a href="{a["url"]}" target="_blank" rel="sponsored nofollow noopener">'
        f"{escape(a['label'])}</a></li>"
        for a in matched[:4]
    )
    return (
        '<h2 id="recommended-resources">Students కోసం Recommended Resources 📚</h2>'
        f"<ul>{items}</ul>"
        '<p><em>Affiliate Disclosure: ఈ లింక్స్ ద్వారా కొనుగోలు చేస్తే మాకు చిన్న '
        "commission వస్తుంది — మీకు అదనపు ఖర్చు ఉండదు.</em></p>"
    )


def featured_block() -> str:
    """v20: coaching-center featured listing (AdSense policy: disclosure
    + rel=sponsored mandatory). FEATURED_CTA_HTML env lo set cheste active."""
    raw = (getattr(config, "FEATURED_CTA_HTML", "") or "").strip()
    # Sponsored HTML is owner-provided but still passes the same XSS sanitizer
    # as article content before it reaches a post.
    raw = validator.sanitize_html(raw)
    # Sponsored content must identify the relationship in the link itself;
    # silently accepting owner HTML without rel=sponsored is unsafe.
    if raw and not re.search(
            r"<a\b[^>]*rel=[\"'][^\"']*\bsponsored\b",
            raw, re.I):
        log.warning("FEATURED_CTA_HTML skipped: sponsored rel missing")
        return ""
    if not raw:
        return ""
    return (
        '<div style="border:1px solid #D8CFB8;background:#F1E8CE;'
        'padding:10px 14px;border-radius:6px;margin:18px 0;font-size:14px;">'
        '<span style="font-size:11px;font-weight:700;letter-spacing:.5px;'
        'text-transform:uppercase;color:#93711D;">Sponsored</span><br>'
        + raw + "</div>"
    )


def append_blocks(html: str, article: Dict) -> str:
    """Monetization blocks ni schema scripts mundu insert chey."""
    blocks = affiliate_block(article) + telegram_cta_block() + featured_block()
    if not blocks:
        return html
    idx = html.find('<script type="application/ld+json">')
    if idx == -1:
        return html + blocks
    return html[:idx] + blocks + html[idx:]


# Money-page keywords — ee titles match aina posts ki internal link priority
# (traffic pages nunchi money pages ki link -> high-CPC pageviews perugutayi)
MONEY_KEYWORDS = [
    "loan", "salary", "fee", "fees", "stipend", "bank", "compare",
    "best", "top 5", "top 7", "top 10", "highest paying", "course",
    "ఫీజు", "జీతం", "లోన్", "బ్యాంక్",
]


def prioritize_money_pages(posts: List[Dict]) -> List[Dict]:
    """Internal link selection: money pages (high-CPC) first, rest recent."""
    def is_money(p):
        t = (p.get("title") or "").lower()
        return any(k in t for k in MONEY_KEYWORDS)
    return sorted(posts, key=lambda p: not is_money(p))
