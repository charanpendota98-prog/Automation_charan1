"""Internet research module — multi-source gathering for super-complete articles.

Mi URL ichaka: bot internet lo aa same topic (same notification/scheme)
meeda article search chestundi (DuckDuckGo — API key avasaram ledu),
top competitor articles nunchi EXTRA facts teesukuntundi. Primary URL lo
miss ayyina info kuda add avtundi. Still 100% original writing.
"""

import logging
import time
from urllib.parse import parse_qs, unquote, urlparse

import requests
from bs4 import BeautifulSoup

from . import config
from .sources import SourceArticle, fetch_source, is_valid_source_url

# Telugu reporting adds local explanations; it never replaces an official
# notice. Official domains are fetched first, then Telugu publishers, then
# national authority media and other independent domains.
TELUGU_PUBLISHERS = {
    # Large Telugu education/news desks.
    "eenadu.net", "pratibha.eenadu.net", "sakshi.com", "education.sakshi.com",
    "tv9telugu.com", "ntnews.com", "telugu.abplive.com", "telugu.samayam.com",
    "andhrajyothy.com", "etelangana.org", "hmtvlive.com", "10tv.in",
    "v6velugu.com", "telugu.careerindia.com",
    # Telugu/AP/TS job-specialist publishers (discovery + explanation only;
    # facts still need an official notice or independent corroboration).
    "adda247.com", "jobupdatestelugu.com", "telugucareers.in",
    "telugujobspoint.com", "naajob.com", "telangana.indgovtjobs.net",
    "ap.indgovtjobs.net", "teachernews.in", "schools360.in",
    "manabadi.co.in", "vidyavision.com",
}

JOB_PUBLISHERS = {
    "freejobalert.com", "freshersnow.com", "testbook.com", "careerpower.in",
    "jagranjosh.com", "govtjobguru.in", "sarkariresult.com", "indgovtjobs.in",
    "employmentnews.gov.in", "fresherslive.com", "naukri.com", "foundit.in",
    "indeed.com", "jobs.com",
}


def _source_priority(url: str) -> tuple:
    from . import deep_research

    host = urlparse(url).netloc.lower().replace("www.", "")
    tier = deep_research.source_tier(url)
    if tier == 1:
        return (0, host)
    if host in TELUGU_PUBLISHERS or any(host.endswith("." + d) for d in TELUGU_PUBLISHERS):
        return (1, host)
    if tier == 2:
        return (2, host)
    if host in JOB_PUBLISHERS or any(host.endswith("." + d) for d in JOB_PUBLISHERS):
        return (3, host)
    return (4, host)

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
    """DuckDuckGo HTML search (no API key). Returns [{url, title}].

    Primary endpoint fail/block aite lite fallback try chestundi.
    NOTE: requests params automatic encode chestundi — raw query
    pampali (double-encoding bug fix).
    """
    endpoints = [config.SEARCH_ENDPOINT]
    if config.SEARCH_FALLBACK_ENDPOINT:
        endpoints.append(config.SEARCH_FALLBACK_ENDPOINT)

    results: list = []
    seen = set()
    for endpoint in endpoints:
        try:
            resp = requests.get(endpoint, params={"q": query}, headers=HEADERS,
                                timeout=config.HTTP_TIMEOUT)
            if resp.status_code != 200:
                log.warning("Search %s -> HTTP %s", endpoint, resp.status_code)
                continue
            soup = BeautifulSoup(resp.text, "html.parser")
            for a in soup.select("a.result__a") + soup.select("a.result-link"):
                href = _unwrap_ddg_url(a.get("href", ""))
                title = a.get_text(strip=True)
                if not href.startswith("http") or href in seen or not title:
                    continue
                seen.add(href)
                results.append({"url": href, "title": title})
                if len(results) >= max_results:
                    break
            if results:
                break
        except Exception:
            log.exception("Search error (%s) — next endpoint", endpoint)
            continue
    log.info("Search '%s' -> %d results", query[:50], len(results))
    return results


def _clean_query(title: str) -> str:
    """Source title ni search query ga marchi (site names/junk remove)."""
    import re

    q = re.sub(r"\s*[-|–]\s*[^-|–]{3,30}$", "", title)  # "- SiteName" strip
    q = re.sub(r"\s+", " ", q).strip()
    return q[:90]


def topic_source_candidates(topic: str, limit: int = 8) -> list:
    """Resolve a text-only job alert to source URLs, official/Telugu first."""
    rows = search_web(_clean_query(topic), max_results=max(limit * 2, 10))
    own = urlparse(config.WP_SITE).netloc.lower().replace("www.", "")
    seen, out = set(), []
    for row in sorted(rows, key=lambda item: _source_priority(item.get("url", ""))):
        url = (row.get("url") or "").strip()
        host = urlparse(url).netloc.lower().replace("www.", "")
        if not url or host == own or host in seen or not is_valid_source_url(url):
            continue
        seen.add(host)
        out.append({**row, "priority": _source_priority(url)[0]})
        if len(out) >= limit:
            break
    return out


def research_topic(
    primary: SourceArticle,
    max_extra: int = 3,
):
    """Primary article topic meeda web search -> extra source articles.

    Returns (extras, competitor_titles):
      extras            -> list[SourceArticle] (fetch avtayina sources)
      competitor_titles -> search result titles (KEYWORD INTELLIGENCE —
                           Google lo already ranking titles; prompt ki
                           istamu better keywords kosam)
    """
    query = _clean_query(primary.title)
    if not query:
        return [], []
    # Fetch a wider candidate pool than the final source count: duplicate
    # domains, own-site pages and failed fetches are removed below.
    results = search_web(query, max_results=max(10, max_extra * 3))
    results = sorted(results, key=lambda item: _source_priority(item.get("url", "")))

    own_domain = urlparse(config.WP_SITE).netloc.replace("www.", "")
    primary_domain = urlparse(primary.url).netloc.replace("www.", "")
    skip_domains = {primary_domain, own_domain}
    competitor_titles = [
        r["title"] for r in results
        if urlparse(r["url"]).netloc.replace("www.", "") not in skip_domains
    ][:8]

    extras = []
    # v77: source page lopala unna OFFICIAL links ni mundhu follow —
    # (notification PDFs · apply portals · syllabi) — related facts richest.
    for link in (getattr(primary, "outbound", None) or [])[:4]:
        if len(extras) >= max_extra:
            break
        netloc = urlparse(link).netloc.replace("www.", "")
        if netloc in skip_domains or not is_valid_source_url(link):
            continue
        try:
            art = fetch_source(link)
            if len(art.text) > 300:
                extras.append(art)
                skip_domains.add(netloc)
                log.info("Research official add: %s (%d chars)", netloc,
                         len(art.text))
        except Exception as exc:
            log.debug("Research official skip %s: %s", link[:60], exc)
            continue
        time.sleep(1.0)  # polite crawling
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
    return extras, competitor_titles
