"""Internet research module — multi-source gathering for super-complete articles.

Mi URL ichaka: bot internet lo aa same topic (same notification/scheme)
meeda article search chestundi (DuckDuckGo — API key avasaram ledu),
top competitor articles nunchi EXTRA facts teesukuntundi. Primary URL lo
miss ayyina info kuda add avtundi. Still 100% original writing.
"""

import logging
import time
from urllib.parse import parse_qs, quote_plus, unquote, urlparse

import requests
from bs4 import BeautifulSoup

from . import config, sources
from .sources import SourceArticle, fetch_source, is_valid_source_url

log = logging.getLogger("autoblog.research")

HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) "
                   "Chrome/124.0 Safari/537.36"),
    "Accept-Language": "en,te;q=0.8",
}


def _unwrap_ddg_url(href: str) -> str:
    """DuckDuckGo redirect links (/l/?uddg=...) ni real URL ga marchi."""
    try:
        if href.startswith("//"):
            href = "https:" + href
        parsed = urlparse(href)
        if "uddg" in (parsed.query or ""):
            real = parse_qs(parsed.query).get("uddg", [""])[0]
            return unquote(real)
        return href
    except ValueError:
        return ""


def search_web(query: str, max_results: int = 6) -> list:
    """DuckDuckGo HTML search (no API key). Returns [{url, title}]."""
    endpoint = config.SEARCH_ENDPOINT
    try:
        resp = requests.get(
            endpoint, params={"q": quote_plus(query)}, headers=HEADERS,
            timeout=config.HTTP_TIMEOUT,
        )
        if resp.status_code != 200:
            log.warning("Search failed: HTTP %s — research skip", resp.status_code)
            return []
        soup = BeautifulSoup(resp.text, "html.parser")
        results = []
        seen = set()
        for a in soup.select("a.result__a"):
            href = _unwrap_ddg_url(a.get("href", ""))
            title = a.get_text(strip=True)
            if not href.startswith("http") or href in seen:
                continue
            seen.add(href)
            results.append({"url": href, "title": title})
            if len(results) >= max_results:
                break
        log.info("Search '%s' -> %d results", query[:50], len(results))
        return results
    except Exception:
        log.exception("Search error — research skip (primary source tho continue)")
        return []


def _clean_query(title: str) -> str:
    """Source title ni search query ga marchi (site names/junk remove)."""
    import re

    q = re.sub(r"\s*[-|–]\s*[^-|–]{3,30}$", "", title)  # "- SiteName" strip
    q = re.sub(r"\s+", " ", q).strip()
    return q[:90]


def research_topic(
    primary: SourceArticle,
    max_extra: int = 3,
) -> list:
    """Primary article topic meeda web search -> extra source articles.

    Returns list[SourceArticle] (primary domain + studentup.in skip avtai).
    """
    query = _clean_query(primary.title)
    if not query:
        return []
    results = search_web(query)

    own_domain = urlparse(config.WP_SITE).netloc.replace("www.", "")
    skip_domains = {urlparse(primary.url).netloc.replace("www.", ""), own_domain}
    extras: list = []
    for r in results:
        if len(extras) >= max_extra:
            break
        netloc = urlparse(r["url"]).netloc.replace("www.", "")
        if netloc in skip_domains or not is_valid_source_url(r["url"]):
            continue
        try:
            art = fetch_source(r["url"])
            if len(art.text) > 300:
                extras.append(art)
                skip_domains.add(netloc)
                log.info("Research source add: %s (%d chars)", netloc, len(art.text))
        except Exception as exc:
            log.debug("Research fetch skip %s: %s", r["url"][:60], exc)
            continue
        time.sleep(1.0)  # polite crawling
    return extras
