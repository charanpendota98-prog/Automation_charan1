"""Source article pipeline: fetch URL -> extract facts -> 100% original rewrite.

Copyright-safe approach: source article lo FACTS matrame teesukuntamu
(sentences copy cheyam). Gemini aa facts ni complete ga original ga,
extra advanced sections tho, Telugu+English mix lo rewrite chestundi.
"""

import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from io import BytesIO
from typing import List, Optional
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from . import config

log = logging.getLogger("autoblog.sources")

MAX_SOURCE_CHARS = 18000  # v85: lengthy sources cut = thin/hallucinated posts

BLOCKED_HOSTS = ("facebook.com", "twitter.com", "x.com", "instagram.com")

# v77: official-link priority — jobs/results/scholarships facts ki gov/edu first.
OFFICIAL_SUFFIX = (".gov.in", ".nic.in", ".gov", ".edu", ".ac.in", ".edu.in")
OFFICIAL_HOSTS = ("tspsc.gov.in", "appsc.gov.in", "upsc.gov.in", "ssc.gov.in",
                  "ibps.in", "rrbcdg.gov.in", "nta.ac.in", "scholarships.gov.in",
                  "nsdl.co.in", "cbse.gov.in", "bie.ap.gov.in", "bse.telangana.gov.in",
                  "nta.ac.in", "ugcnet.nta.ac.in", "ctet.nic.in", "rrbcdg.gov.in",
                  "epfindia.gov.in", "esic.gov.in", "sebi.gov.in", "dgt.gov.in",
                  "education.gov.in", "apmsrb.ap.gov.in", "telangana.gov.in",
                  "ap.gov.in", "osmania.ac.in", "jntuh.ac.in", "jntuk.ac.in",
                  "jntuk.edu.in", "andhrauniversity.edu.in", "braou.ac.in",
                  "kakatiya.ac.in")


@dataclass
class SourceArticle:
    url: str
    title: str = ""
    site_name: str = ""
    text: str = ""
    meta_description: str = ""
    image_url: str = ""
    published_date: str = ""
    updated_date: str = ""
    # v77: source page lopala unna useful outbound links (official-first rank).
    outbound: List[str] = field(default_factory=list)
    # Keep anchor text too: official apply/notification links must be mapped
    # from evidence, never invented by the model.
    outbound_links: List[dict] = field(default_factory=list)
    canonical_url: str = ""
    content_type: str = ""
    status_code: int = 200
    fetched_at: str = ""


def is_valid_source_url(url: str) -> bool:
    try:
        p = urlparse(url)
        return p.scheme in ("http", "https") and p.netloc and \
            not any(b in p.netloc for b in BLOCKED_HOSTS)
    except ValueError:
        return False


def _source_link_record(url: str, source_url: str, anchor_text: str = "",
                        verification_status: str = "present_in_source_text") -> dict:
    host = urlparse(url).netloc.lower().replace("www.", "")
    return {
        "url": url,
        "exact_url": url,
        "text": re.sub(r"\s+", " ", anchor_text or "")[:180],
        "anchor_text": re.sub(r"\s+", " ", anchor_text or "")[:180],
        "source_url": source_url,
        "canonical_url": url,
        "final_url": "",
        "domain_class": ("official_explicit" if host in OFFICIAL_HOSTS else
                          "official_suffix" if is_official_domain(host) else "external"),
        "link_type": _link_type(anchor_text, url) if "_link_type" in globals() else "unknown",
        "verification_status": verification_status,
    }


def _text_urls(text: str) -> List[str]:
    """Exact public URLs visible in extracted HTML/PDF text."""
    out, seen = [], set()
    for match in re.findall(r"https?://[^\s<>\"']+", text or "", re.I):
        value = match.rstrip(".,;:)]}")
        if is_valid_source_url(value) and value not in seen:
            seen.add(value)
            out.append(value)
    return out[:60]


def _extract_pdf(url: str, content: bytes, canonical_url: str = "",
                 status_code: int = 200) -> SourceArticle:
    """Extract text from public notification PDFs without storing the file."""
    try:
        from pypdf import PdfReader
    except ImportError as exc:  # pragma: no cover - dependency is in requirements
        raise ValueError("PDF source requires the pypdf dependency") from exc
    try:
        reader = PdfReader(BytesIO(content))
        pages = []
        for page in reader.pages[:40]:
            text = page.extract_text() or ""
            if text.strip():
                pages.append(text)
        extracted = re.sub(r"\n{2,}", "\n", "\n".join(pages)).strip()
    except Exception as exc:  # noqa: BLE001
        raise ValueError("PDF text extraction failed; open this source manually") from exc
    if not extracted:
        raise ValueError("PDF has no selectable text; open this source manually")
    filename = urlparse(url).path.rsplit("/", 1)[-1]
    title = re.sub(r"[_+%20-]+", " ", filename.rsplit(".", 1)[0]).strip() or url
    date_match = re.search(r"(?:dated?|date)\D{0,12}(\d{1,2}[^\n]{0,20}20\d{2})",
                           extracted, re.I)
    clipped = extracted[:MAX_SOURCE_CHARS]
    return SourceArticle(
        url=url,
        title=title,
        site_name=urlparse(url).netloc,
        text=clipped,
        meta_description="Public PDF notification; verify the cited page before publishing.",
        published_date=date_match.group(1).strip() if date_match else "",
        outbound_links=[_source_link_record(found, url, "PDF source URL")
                        for found in _text_urls(clipped)],
        canonical_url=canonical_url or url,
        content_type="application/pdf",
        status_code=int(status_code),
        fetched_at=datetime.now(timezone.utc).isoformat(),
    )


def fetch_source(url: str, retries: int = 2) -> SourceArticle:
    """Fetch a web page and extract title + readable main text.

    Retries: normal browser UA -> Googlebot UA (chala sites bot ki
    full content istayi). Encoding auto-detect (Telugu sites safe).
    """
    import time

    uas = [
        ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
         "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"),
        "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
    ]
    last_exc: Exception = None
    resp = None
    for attempt in range(retries):
        headers = {
            "User-Agent": uas[attempt % len(uas)],
            "Accept-Language": "te,en;q=0.8",
        }
        try:
            resp = requests.get(url, headers=headers, timeout=config.HTTP_TIMEOUT,
                                allow_redirects=True)
            if resp.status_code == 200:
                break
            last_exc = ValueError(f"HTTP {resp.status_code}")
        except Exception as exc:
            last_exc = exc
        time.sleep(1.5)
    if resp is None or resp.status_code != 200:
        raise ValueError(f"Source fetch fail: {last_exc}")

    ctype = resp.headers.get("content-type", "").lower()
    if "pdf" in ctype or urlparse(url).path.lower().endswith(".pdf"):
        return _extract_pdf(url, resp.content, canonical_url=str(resp.url or url),
                            status_code=resp.status_code)

    # encoding fix: chala Indian sites wrong charset declare chestayi
    if not resp.encoding or resp.encoding.lower() == "iso-8859-1":
        resp.encoding = resp.apparent_encoding or "utf-8"
    if "html" not in ctype and "text" not in ctype and ctype:
        raise ValueError(f"Not an HTML page: {ctype[:60]}")

    soup = BeautifulSoup(resp.text, "html.parser")
    canonical_tag = soup.find("link", rel=lambda value: value and "canonical" in value)
    canonical_url = urljoin(url, canonical_tag.get("href", "").strip()) if canonical_tag and canonical_tag.get("href") else str(resp.url or url)
    # v85: decompose MUNDU JSON-LD backup (JS-site fallback kosam).
    jsonld_backup = _jsonld_article_text(soup)
    for tag in soup(["script", "style", "nav", "header", "footer", "aside",
                     "form", "iframe", "noscript", "button", "svg"]):
        tag.decompose()

    src = SourceArticle(
        url=url,
        canonical_url=canonical_url,
        content_type=ctype.split(";", 1)[0].strip().lower(),
        status_code=int(resp.status_code),
        fetched_at=datetime.now(timezone.utc).isoformat(),
    )

    # title: og:title > twitter:title > <title> > first h1
    og = soup.find("meta", attrs={"property": "og:title"})
    if not og:
        og = soup.find("meta", attrs={"name": "twitter:title"})
    src.title = (og.get("content", "").strip() if og else "") \
        or (soup.title.string.strip() if soup.title and soup.title.string else "") \
        or (soup.h1.get_text(strip=True) if soup.h1 else "") \
        or url

    desc = soup.find("meta", attrs={"property": "og:description"}) or \
        soup.find("meta", attrs={"name": "description"})
    src.meta_description = desc.get("content", "").strip() if desc else ""

    def _meta_value(names):
        for attrs in names:
            tag = soup.find("meta", attrs=attrs)
            if tag and tag.get("content", "").strip():
                return tag.get("content", "").strip()
        return ""

    src.published_date = _meta_value([
        {"property": "article:published_time"},
        {"name": "datePublished"},
        {"itemprop": "datePublished"},
    ])
    src.updated_date = _meta_value([
        {"property": "article:modified_time"},
        {"name": "dateModified"},
        {"itemprop": "dateModified"},
    ])
    if not src.published_date:
        time_tag = soup.find("time", attrs={"datetime": True})
        src.published_date = time_tag.get("datetime", "").strip() if time_tag else ""

    og_site = soup.find("meta", attrs={"property": "og:site_name"})
    src.site_name = og_site.get("content", "").strip() if og_site else urlparse(url).netloc

    og_img = soup.find("meta", attrs={"property": "og:image"})
    src.image_url = og_img.get("content", "").strip() if og_img else ""

    # main text: prefer <article>, else whole body
    container = soup.find("article") or soup.body or soup
    # v85: TABLES + HEADINGS kuda (job vacancy/fee/age tables miss ayithe
    # LLM facts guess chestundi — hallucination root cause!).
    chunks = []
    for el in container.find_all(["h2", "h3", "p", "li", "table"]):
        if el.name == "table":
            rows = []
            for tr in el.find_all("tr"):
                cells = [c.get_text(" ", strip=True)
                         for c in tr.find_all(["th", "td"])]
                cells = [c for c in cells if c]
                if cells:
                    rows.append(" | ".join(cells))
            if rows:
                chunks.append("TABLE:\n" + "\n".join(rows[:30]))
        else:
            t = el.get_text(" ", strip=True)
            min_len = 3 if el.name in ("h2", "h3") else 25
            if len(t) > min_len:
                chunks.append(("[H] " if el.name in ("h2", "h3") else "") + t)
    text = "\n".join(chunks)
    text = re.sub(r"\n{2,}", "\n", text)
    src.text = text[:MAX_SOURCE_CHARS]
    if not src.text:
        # v85: JS-site fallback — JSON-LD articleBody (news/SPA sites embed
        # full text for Google; manam kuda vadukovachu — honest extraction).
        src.text = jsonld_backup[:MAX_SOURCE_CHARS]
    if not src.text:
        raise ValueError("Source article lo text dorakaledu (JavaScript site ayi untundi)")
    # v77: related useful links — content lopala unna outbound (official-first).
    src.outbound_links = _page_link_records(container, url)
    known = {item.get("exact_url") or item.get("url") for item in src.outbound_links}
    for found in _text_urls(src.text):
        if found not in known:
            src.outbound_links.append(_source_link_record(found, url, "URL in source text"))
    src.outbound = rank_outbound([item["url"] for item in src.outbound_links], url)
    return src


def _jsonld_article_text(soup) -> str:
    """JSON-LD blocks nunchi articleBody/headline/description (JS fallback)."""
    out = []
    for tag in soup.find_all("script", attrs={"type": "application/ld+json"}):
        raw = (tag.string or "").strip()
        if not raw:
            continue
        try:
            data = json.loads(raw)
        except Exception:  # noqa: BLE001 — broken JSON-LD skip
            continue
        nodes = data if isinstance(data, list) else [data]
        for node in nodes:
            if not isinstance(node, dict):
                continue
            for key in ("articleBody", "text"):
                val = node.get(key)
                if isinstance(val, str) and len(val.strip()) > 100:
                    out.append(val.strip())
            if not out:
                head = node.get("headline") or ""
                desc = node.get("description") or ""
                if len((head + desc).strip()) > 100:
                    out.append((head + "\n" + desc).strip())
    return "\n".join(out)


def _link_type(anchor_text: str, url: str) -> str:
    """Infer purpose only from observable label/path; unknown stays unknown."""
    haystack = f"{anchor_text} {url}".lower()
    patterns = (
        ("application", r"apply|application|registration|online form|career|careers|jobs|สมัคร|దరఖాస్తు"),
        ("official_notice", r"notification|notice|advertisement| भर्ती|విజ్ఞప్తి|circular|pdf"),
        ("result", r"result|merit|selection list|shortlist|ఫలిత"),
        ("admit_card", r"admit|hall ticket|call letter| प्रवेश पत्र|హాల్ టికెట్"),
        ("syllabus", r"syllabus|scheme|exam pattern|సిలబస్"),
        ("fee_payment", r"fee|payment|challan|pay now|ఫీజు"),
        ("contact", r"contact|helpdesk|helpline|support|సంప్రదించ"),
        ("organization", r"official website|department|board|university|about us|home"),
    )
    for kind, pattern in patterns:
        if re.search(pattern, haystack, re.I):
            return kind
    return "unknown"


def _page_link_records(container, base_url: str) -> List[dict]:
    """Content-area links with anchor text and auditable source provenance.

    Boilerplate was removed before this helper runs. Anchor text is evidence
    for mapping an official Apply/Notification URL; the model is never allowed
    to create an arbitrary path merely because a host looks official.
    """
    out, seen = [], set()
    for anchor in container.find_all("a", href=True):
        href = (anchor.get("href") or "").strip()
        if not href or href.startswith(("#", "javascript:", "mailto:", "tel:")):
            continue
        absolute = urljoin(base_url, href).split("#")[0]
        if not is_valid_source_url(absolute) or absolute in seen:
            continue
        seen.add(absolute)
        text = re.sub(r"\s+", " ", anchor.get_text(" ", strip=True))[:180]
        host = urlparse(absolute).netloc.lower().replace("www.", "")
        out.append({
            "url": absolute,
            "exact_url": absolute,
            "text": text,
            "anchor_text": text,
            "source_url": base_url,
            "canonical_url": absolute,
            "final_url": "",
            "domain_class": "official_explicit" if host in OFFICIAL_HOSTS else (
                "official_suffix" if is_official_domain(host) else "external"),
            "link_type": _link_type(text, absolute),
            "verification_status": "present_in_source_html",
            "rel": list(anchor.get("rel") or [])[:8],
        })
    return out[:60]


def _page_links(container, base_url: str) -> List[str]:
    """Backward-compatible URL-only view of content-area links."""
    return [item["url"] for item in _page_link_records(container, base_url)]


def is_official_domain(netloc_or_url: str) -> bool:
    """v86: gov/edu/nic ⇒ official (pipeline official-links gate)."""
    host = (netloc_or_url or "").lower()
    if "://" in host:
        host = urlparse(host).netloc
    return _official_score(host) > 0


def _official_score(netloc: str) -> int:
    host = (netloc or "").lower().replace("www.", "")
    if host in OFFICIAL_HOSTS:
        return 3
    if host.endswith(OFFICIAL_SUFFIX) or host in {suffix.lstrip(".") for suffix in OFFICIAL_SUFFIX}:
        return 2
    if host.endswith((".org", ".info")):
        return 1
    return 0


def rank_outbound(links: List[str], page_url: str) -> List[str]:
    """Outbound links: official-first, same-site de-prioritized, social out."""
    try:
        own = urlparse(page_url).netloc.lower().replace("www.", "")
    except Exception:  # noqa: BLE001
        own = ""
    scored = []
    for i, link in enumerate(links or []):
        try:
            host = urlparse(link).netloc.lower().replace("www.", "")
        except Exception:  # noqa: BLE001
            continue
        if not host or any(b in host for b in BLOCKED_HOSTS):
            continue
        same = 1 if host == own else 0
        scored.append((-_official_score(host), same, i, link))
    scored.sort()
    return [link for _, _, _, link in scored][:25]


# ------------------------------------------------------------------ queue file

def queue_file_path():
    return config.SOURCES_QUEUE_PATH


def pending_from_queue() -> Optional[str]:
    """First URL in sources_queue.txt that isn't processed yet."""
    path = queue_file_path()
    if not path.exists():
        return None
    from . import state

    for line in path.read_text(encoding="utf-8").splitlines():
        url = line.strip()
        if url and url.startswith("http") and not state.source_done(config.STATE_PATH, url):
            try:
                state.mark_source_queued(config.STATE_PATH, url)
            except Exception:  # noqa: BLE001 — queue marking failure must not block the draft
                log.debug("source queue mark skip: %s", url, exc_info=True)
            return url
    return None


def mark_done_and_clean(
    url: str,
    completed: bool = True,
    failure_type: str = "draft_failed",
    details: str = "",
) -> None:
    """Remove a queue URL and finalize its source/opportunity state.

    Failed drafts are retryable, and their outcome is retained in the radar
    audit table rather than silently disappearing from the queue.
    """
    from . import state
    import hashlib

    if completed:
        state.mark_source_done(config.STATE_PATH, url)
        try:
            state.record_radar_event(config.STATE_PATH, "draft_ready", url,
                                     details="draft created after source preflight")
        except Exception:  # noqa: BLE001 — audit row failure must not lose the draft
            log.debug("radar draft_ready event skip: %s", url, exc_info=True)
    else:
        state.mark_source_retry(config.STATE_PATH, url)
        try:
            state.record_radar_event(config.STATE_PATH, failure_type, url,
                                     details=details)
        except Exception:  # noqa: BLE001 — audit row failure must not hide the retry
            log.debug("radar %s event skip: %s", failure_type, url, exc_info=True)
        url_key = "radar:url:" + hashlib.md5((url or "").encode("utf-8")).hexdigest()[:16]
        ref_key = url_key + ":opportunity"
        opportunity_key = state.meta_get(config.STATE_PATH, ref_key)
        for key in (url_key, ref_key, opportunity_key):
            if key:
                try:
                    state.meta_delete(config.STATE_PATH, key)
                except Exception:  # noqa: BLE001 — stale key cleanup is best effort
                    log.debug("radar meta cleanup skip: %s", key, exc_info=True)
    path = queue_file_path()
    if path.exists():
        lines = [l for l in path.read_text(encoding="utf-8").splitlines()
                 if l.strip() != url.strip()]
        path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


# ---------------------------------------------------------------- v21
def apply_queue_boost(boost_words: list) -> int:
    """GSC-data-driven priority: queue lines matching boost terms move to
    top (stable order otherwise). Returns matched count. Real impressions >
    guesses — radar/keyword queue processing order itself optimize avutundi."""
    if not boost_words:
        return 0
    import re as _re

    words = [w.lower() for w in boost_words if len(w) >= 3][:40]

    def score(line: str) -> int:
        low = line.lower()
        toks = set(_re.split(r"[^a-z0-9\u0c00-\u0c7f]+", low)) - {""}
        return sum(1 for w in words if w in toks or w in low)

    paths = []
    try:
        paths.append(queue_file_path())
    except Exception as exc:  # noqa: BLE001 — best-effort (silent kaadu)
        log.debug("sources.apply_queue_boost skip: %s", exc)
    try:
        from . import news_radar as _nr

        paths.append(_nr.topics_queue_path())
    except Exception as exc:  # noqa: BLE001 — best-effort (silent kaadu)
        log.debug("sources.apply_queue_boost skip: %s", exc)
    moved = 0
    for path in paths:
        try:
            if not path or not path.exists():
                continue
            lines = [ln for ln in path.read_text(encoding="utf-8").splitlines()
                     if ln.strip()]
            scored = [(-score(ln), i, ln) for i, ln in enumerate(lines)]
            if any(-sc > 0 for sc, _, _ in scored):
                moved += sum(1 for sc, _, _ in scored if -sc > 0)
                scored.sort()
                path.write_text(
                    "\n".join(ln for _, _, ln in scored) + "\n",
                    encoding="utf-8")
        except OSError:
            continue
    return moved
