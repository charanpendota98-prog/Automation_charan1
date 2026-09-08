"""Source article pipeline: fetch URL -> extract facts -> 100% original rewrite.

Copyright-safe approach: source article lo FACTS matrame teesukuntamu
(sentences copy cheyam). Gemini aa facts ni complete ga original ga,
extra advanced sections tho, Telugu+English mix lo rewrite chestundi.
"""

import logging
import re
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from . import config

log = logging.getLogger("autoblog.sources")

MAX_SOURCE_CHARS = 6000

BLOCKED_HOSTS = ("facebook.com", "twitter.com", "x.com", "instagram.com")


@dataclass
class SourceArticle:
    url: str
    title: str = ""
    site_name: str = ""
    text: str = ""
    meta_description: str = ""
    image_url: str = ""


def is_valid_source_url(url: str) -> bool:
    try:
        p = urlparse(url)
        return p.scheme in ("http", "https") and p.netloc and \
            not any(b in p.netloc for b in BLOCKED_HOSTS)
    except ValueError:
        return False


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

    # encoding fix: chala Indian sites wrong charset declare chestayi
    if not resp.encoding or resp.encoding.lower() == "iso-8859-1":
        resp.encoding = resp.apparent_encoding or "utf-8"
    ctype = resp.headers.get("content-type", "")
    if "html" not in ctype and "text" not in ctype and ctype:
        raise ValueError(f"Not an HTML page: {ctype[:60]}")

    soup = BeautifulSoup(resp.text, "html.parser")
    for tag in soup(["script", "style", "nav", "header", "footer", "aside",
                     "form", "iframe", "noscript", "button", "svg"]):
        tag.decompose()

    src = SourceArticle(url=url)

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

    og_site = soup.find("meta", attrs={"property": "og:site_name"})
    src.site_name = og_site.get("content", "").strip() if og_site else urlparse(url).netloc

    og_img = soup.find("meta", attrs={"property": "og:image"})
    src.image_url = og_img.get("content", "").strip() if og_img else ""

    # main text: prefer <article>, else whole body
    container = soup.find("article") or soup.body or soup
    paragraphs = [p.get_text(" ", strip=True) for p in container.find_all(["p", "li"])]
    text = "\n".join(p for p in paragraphs if len(p) > 25)
    text = re.sub(r"\n{2,}", "\n", text)
    src.text = text[:MAX_SOURCE_CHARS]
    if not src.text:
        raise ValueError("Source article lo text dorakaledu (JavaScript site ayi untundi)")
    return src


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
            return url
    return None


def mark_done_and_clean(url: str) -> None:
    from . import state

    state.mark_source_done(config.STATE_PATH, url)
    path = queue_file_path()
    if path.exists():
        lines = [l for l in path.read_text(encoding="utf-8").splitlines()
                 if l.strip() != url.strip()]
        path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
