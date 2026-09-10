"""v15: District Breaking-News Radar + Telegram/web channel watch.

Real data matrame (fake news kaadu): Google News RSS (Telugu edition) nunchi
TS 33 + AP 26 district-level breaking news → education-relevant filter →
sources_queue.txt → mana pipeline 100% original article rashtundi.

WATCH_SOURCES (.env, comma list):
- https://t.me/s/CHANNEL   → public Telegram channel preview (bot join avalsu ledu)
- RSS feed / website URL   → kotha article links queue
Channel text posts (URL leni vi) → topics_queue.txt → trend-topic articles.
"""

import hashlib
import html
import logging
import re
from pathlib import Path
from typing import Dict, List
from urllib.parse import quote

import requests

from . import config, state
from .topic_engine import TREND_EDU_PATTERNS

log = logging.getLogger("autoblog.radar")

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")

GOOGLE_NEWS_RSS = "https://news.google.com/rss/search?q={q}&hl=te&gl=IN&ceid=IN:te"
EDU_TERMS = "education OR jobs OR scholarship OR exam OR result OR admission OR notification"

# Telangana 33 districts (2026 reorg: Warangal merged -> Hanumakonda)
TS_DISTRICTS = [
    "Adilabad", "Bhadradri Kothagudem", "Hanumakonda", "Hyderabad", "Jagtial",
    "Jangaon", "Jayashankar Bhupalpally", "Jogulamba Gadwal", "Kamareddy",
    "Karimnagar", "Khammam", "Kumuram Bheem Asifabad", "Mahabubabad",
    "Mahabubnagar", "Mancherial", "Medak", "Medchal Malkajgiri", "Mulugu",
    "Nagarkurnool", "Nalgonda", "Narayanpet", "Nirmal", "Nizamabad",
    "Peddapalli", "Rajanna Sircilla", "Rangareddy", "Sangareddy", "Siddipet",
    "Suryapet", "Vikarabad", "Wanaparthy", "Warangal", "Yadadri Bhuvanagiri",
]

# Andhra Pradesh 26 districts
AP_DISTRICTS = [
    "Alluri Sitharama Raju", "Anakapalli", "Ananthapuramu", "Annamayya",
    "Bapatla", "Chittoor", "Dr B.R. Ambedkar Konaseema", "East Godavari",
    "Eluru", "Guntur", "Kakinada", "Krishna", "Kurnool", "Nandyal", "NTR",
    "Palnadu", "Parvathipuram Manyam", "Prakasam", "Sri Potti Sriramulu Nellore",
    "Sri Sathya Sai", "Srikakulam", "Tirupati", "Visakhapatnam",
    "Vizianagaram", "West Godavari", "YSR Kadapa",
]

ALL_DISTRICTS = ([(d, "TS") for d in TS_DISTRICTS]
                 + [(d, "AP") for d in AP_DISTRICTS])


def _district_query(district: str) -> str:
    return f'"{district}" ({EDU_TERMS})'


def topics_queue_path() -> Path:
    return config.OUTPUT_DIR / "topics_queue.txt"


# ------------------------------------------------------------------ fetchers

def _fetch_text(url: str, timeout: int = 20) -> str:
    resp = requests.get(url, timeout=timeout, headers={"User-Agent": UA})
    resp.raise_for_status()
    if not resp.encoding or resp.encoding.lower() == "iso-8859-1":
        resp.encoding = resp.apparent_encoding or "utf-8"
    return resp.text


def fetch_google_news(query: str, limit: int = 5) -> List[Dict]:
    """Google News Telugu RSS -> [{title, link, pub}] (fail-safe [])."""
    url = GOOGLE_NEWS_RSS.format(q=quote(query))
    try:
        text = _fetch_text(url)
    except Exception as exc:
        log.debug("google news fetch fail (%s): %s", query[:40], exc)
        return []
    return _parse_feed(text, limit)


def _parse_feed(xml_text: str, limit: int) -> List[Dict]:
    import xml.etree.ElementTree as ET

    out: List[Dict] = []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return []
    for item in root.iter("item"):
        title = html.unescape((item.findtext("title") or "").strip())
        link = (item.findtext("link") or "").strip()
        pub = (item.findtext("pubDate") or "").strip()
        if not title or not link:
            continue
        out.append({"title": title, "link": link, "pub": pub})
        if len(out) >= limit:
            break
    return out


def _edu_relevant(text: str) -> bool:
    """Education/jobs/scholarship relevant matrame (sports/politics filter)."""
    hay = (text or "").lower()
    return any(p in hay for p in TREND_EDU_PATTERNS)


# ------------------------------------------------------------------ queues

def _queue_url(url: str) -> bool:
    """Kotha news URL -> sources_queue.txt (state+file dedup). True=queued."""
    url = (url or "").strip()
    if not url.startswith("http"):
        return False
    from . import sources as _src

    if not _src.is_valid_source_url(url):
        return False
    try:
        if state.source_done(config.STATE_PATH, url):
            return False
    except Exception:
        pass
    key = "radar:url:" + hashlib.md5(url.encode("utf-8")).hexdigest()[:16]
    try:
        if state.meta_get(config.STATE_PATH, key):
            return False
    except Exception:
        pass
    path = config.SOURCES_QUEUE_PATH
    try:
        existing = path.read_text(encoding="utf-8") if path.exists() else ""
    except OSError:
        existing = ""
    if url in existing:
        try:
            state.meta_set(config.STATE_PATH, key, "1")
        except Exception:
            pass
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(url + "\n")
    try:
        state.meta_set(config.STATE_PATH, key, "1")
    except Exception:
        pass
    return True


def _queue_topic(text: str) -> bool:
    """Channel/keyword text item -> topics_queue.txt (edu filter + dedup)."""
    text = " ".join((text or "").split())[:300]
    if len(text) < 20 or not _edu_relevant(text):
        return False
    key = "radar:topic:" + hashlib.md5(text.encode("utf-8")).hexdigest()[:16]
    try:
        if state.meta_get(config.STATE_PATH, key):
            return False
    except Exception:
        pass
    p = topics_queue_path()
    try:
        existing = p.read_text(encoding="utf-8") if p.exists() else ""
    except OSError:
        existing = ""
    if text in existing:
        try:
            state.meta_set(config.STATE_PATH, key, "1")
        except Exception:
            pass
        return False
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as fh:
        fh.write(text + "\n")
    try:
        state.meta_set(config.STATE_PATH, key, "1")
    except Exception:
        pass
    return True


def pending_topics(limit: int = 5) -> List[str]:
    p = topics_queue_path()
    if not p.exists():
        return []
    try:
        lines = [l.strip() for l in p.read_text(encoding="utf-8").splitlines()
                 if l.strip()]
    except OSError:
        return []
    return lines[:limit]


def mark_topic_done(text: str) -> None:
    p = topics_queue_path()
    if not p.exists():
        return
    want = " ".join(text.split())
    keep = [l for l in p.read_text(encoding="utf-8").splitlines()
            if l.strip() and " ".join(l.split()) != want]
    p.write_text("\n".join(keep) + ("\n" if keep else ""), encoding="utf-8")


# ------------------------------------------------------------------ radar

def radar_districts(per_run: int = None) -> List[Dict]:
    """Rotation over 59 districts -> queue new edu-relevant news URLs."""
    per_run = per_run or config.RADAR_DISTRICTS_PER_RUN
    total = len(ALL_DISTRICTS)
    try:
        last = int(state.meta_get(config.STATE_PATH, "radar:last_idx") or -1)
    except (TypeError, ValueError):
        last = -1
    start = (last + 1) % total
    new_items: List[Dict] = []
    for i in range(per_run):
        district, st_code = ALL_DISTRICTS[(start + i) % total]
        try:
            items = fetch_google_news(_district_query(district))
        except Exception as exc:
            log.debug("radar fetch fail (%s): %s", district, exc)
            items = []
        for it in items:
            if not _edu_relevant(it["title"]):
                continue
            if _queue_url(it["link"]):
                new_items.append({"title": it["title"], "link": it["link"],
                                  "district": district, "state": st_code})
    state.meta_set(config.STATE_PATH, "radar:last_idx",
                   str((start + per_run - 1) % total))
    return new_items


def _watch_telegram(chan_url: str) -> int:
    """t.me/s/ public channel page -> new edu-relevant messages -> topics."""
    text = _fetch_text(chan_url)
    queued = 0
    for m in re.finditer(r"tgme_widget_message_text[^>]*>(.*?)</div>", text, re.S):
        raw = re.sub(r"<br\s*/?>", "\n", m.group(1))
        msg = html.unescape(re.sub(r"<[^>]+>", " ", raw))
        msg = " ".join(msg.split())
        if len(msg) >= 25 and _edu_relevant(msg) and _queue_topic(msg):
            queued += 1
        if queued >= 10:
            break
    return queued


def _watch_site(url: str) -> int:
    """RSS feed (items) or HTML page (article-ish links) -> URL queue."""
    from urllib.parse import urlparse

    text = _fetch_text(url)
    host = urlparse(url).netloc
    if "<item>" in text.lower():
        queued = 0
        for it in _parse_feed(text, 15):
            if _edu_relevant(it["title"]) and _queue_url(it["link"]):
                queued += 1
        return queued
    queued = 0
    seen: set = set()
    for m in re.finditer(r'href="(https?://[^"]+)"[^>]*>([^<]{10,120})<', text):
        u = m.group(1)
        label = html.unescape(" ".join(m.group(2).split()))
        if urlparse(u).netloc != host or u in seen:
            continue
        seen.add(u)
        if not _edu_relevant(label or u):
            continue
        if _queue_url(u):
            queued += 1
        if queued >= 5:
            break
    return queued


def watch_channels() -> int:
    """WATCH_SOURCES (t.me/s/ channels + RSS/websites) -> queue new items."""
    total = 0
    for url in [s.strip() for s in config.WATCH_SOURCES.split(",") if s.strip()]:
        try:
            if "t.me/" in url:
                total += _watch_telegram(url)
            else:
                total += _watch_site(url)
        except Exception as exc:
            log.warning("watch fail (%s): %s", url[:60], exc)
    return total


def run_radar() -> dict:
    """Full radar sweep: districts + official sources grid + watch sources."""
    if not config.RADAR_ENABLED:
        return {"enabled": False, "districts": 0, "grid": 0, "watch": 0,
                "items": []}
    d_items = radar_districts()
    g_items: List[Dict] = []
    try:
        from . import sources_grid

        g_items = sources_grid.radar_sources()
    except Exception:
        log.exception("official sources grid skip")
    w = watch_channels() if config.WATCH_SOURCES.strip() else 0
    summary = {"enabled": True, "districts": len(d_items), "grid": len(g_items),
               "watch": w, "items": (d_items + g_items)[:20]}
    log.info("RADAR: %d district + %d grid URLs + %d watch topics queued",
             summary["districts"], summary["grid"], w)
    return summary
