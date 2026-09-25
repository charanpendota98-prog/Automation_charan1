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


def _research_queries(title: str) -> list[str]:
    """Build a small fact-intent query fan-out instead of one shallow search."""
    base = _clean_query(title)
    if not base:
        return []
    queries = [
        base,
        f"{base} official notification",
        f"{base} last date fee exam date",
        f"{base} result syllabus documents apply",
    ]
    # Preserve order while removing repeated words/queries.
    out, seen = [], set()
    for query in queries:
        key = query.lower().strip()
        if key and key not in seen:
            seen.add(key)
            out.append(query[:120])
    return out


def research_topic(
    primary: SourceArticle,
    max_extra: int = 3,
):
    """Primary article topic meeda multi-intent web research -> extra sources.

    Search fan-out covers the official notice, deadline/fee/exam-date details
    and result/documents/apply intent. It gathers a wider candidate pool, then
    fetches at most ``max_extra`` distinct domains after the primary source.
    Search results are discovery only; fetched facts still go through the
    official-first/editorial verification rules.

    Returns (extras, competitor_titles):
      extras            -> list[SourceArticle] (fetch avtayina sources)
      competitor_titles -> search result titles (keyword intelligence)
    """
    queries = _research_queries(primary.title)
    if not queries:
        return [], []
    # Fetch a wider candidate pool than the final source count. Fan-out is
    # intentionally bounded (four queries) and sequential to remain polite.
    candidates, seen_urls = [], set()
    for query in queries:
        for row in search_web(query, max_results=max(10, max_extra * 3)):
            url = (row.get("url") or "").strip()
            if not url or url in seen_urls:
                continue
            seen_urls.add(url)
            candidates.append(row)

    results = sorted(candidates, key=lambda item: _source_priority(item.get("url", "")))
    own_domain = urlparse(config.WP_SITE).netloc.replace("www.", "")
    primary_domain = urlparse(primary.url).netloc.replace("www.", "")
    skip_domains = {primary_domain, own_domain}
    competitor_titles = []
    seen_titles = set()
    for row in results:
        host = urlparse(row["url"]).netloc.replace("www.", "")
        title = row.get("title", "")
        if host in skip_domains or title in seen_titles:
            continue
        seen_titles.add(title)
        competitor_titles.append(title)
        if len(competitor_titles) >= 8:
            break

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
    for row in results:
        if len(extras) >= max_extra:
            break
        netloc = urlparse(row["url"]).netloc.replace("www.", "")
        if netloc in skip_domains or not is_valid_source_url(row["url"]):
            continue
        try:
            art = fetch_source(row["url"])
            if len(art.text) > 300:
                extras.append(art)
                skip_domains.add(netloc)
                log.info("Research source add: %s (%d chars)", netloc, len(art.text))
        except Exception as exc:
            log.debug("Research fetch skip %s: %s", row["url"][:60], exc)
            continue
        time.sleep(1.0)  # polite crawling
    log.info(
        "Research fan-out complete: %d intent queries · %d unique candidates · "
        "%d/%d extra domains fetched · %d competitor titles",
        len(queries), len(candidates), len(extras), max_extra, len(competitor_titles),
    )
    return extras, competitor_titles
