# -*- coding: utf-8 -*-
"""v103 — real-time web phrase originality check.

Local donor-source comparison cannot catch copy pasted from a source we did not
fetch. This module samples distinctive article phrases, searches them live, and
fetches returned pages to verify exact presence. It is an evidence check, not a
magical "AI detector" and never claims 100% legal/copyright certainty.

Google Custom Search is used when GOOGLE_CSE_API_KEY + GOOGLE_CSE_ID exist.
Without those credentials, the configured search fallback is used honestly.
"""
from __future__ import annotations

import html
import logging
import re
from typing import Dict, List
from urllib.parse import quote_plus, urlparse

import requests

from . import config
from .research import HEADERS, search_web
from .sources import fetch_source, is_valid_source_url

log = logging.getLogger("autoblog.originality_live")
_WORD = re.compile(r"[\w\u0c00-\u0c7f]+", re.UNICODE)


def _sentences(article_html: str) -> List[str]:
    text = re.sub(r"<[^>]+>", " ", article_html or "")
    text = html.unescape(re.sub(r"\s+", " ", text)).strip()
    out = []
    for s in re.split(r"(?<=[.!?।])\s+", text):
        words = _WORD.findall(s)
        if 9 <= len(words) <= 24:
            out.append(" ".join(words))
    # Distinctive first: long phrases with numbers/proper-looking tokens beat
    # generic "apply online for more details" sentences.
    out.sort(key=lambda x: (sum(ch.isdigit() for ch in x), len(x)), reverse=True)
    return out


def _google(query: str, limit: int = 5) -> List[Dict]:
    key = getattr(config, "GOOGLE_CSE_API_KEY", "")
    cx = getattr(config, "GOOGLE_CSE_ID", "")
    if not key or not cx:
        return []
    r = requests.get("https://www.googleapis.com/customsearch/v1",
                     params={"key": key, "cx": cx, "q": query, "num": limit},
                     headers=HEADERS, timeout=config.HTTP_TIMEOUT)
    r.raise_for_status()
    return [{"url": x.get("link", ""), "title": x.get("title", "")}
            for x in r.json().get("items", []) if x.get("link")]


def check(article_html: str, own_domain: str = "", max_phrases: int = 3) -> Dict:
    phrases = _sentences(article_html)[:max(1, max_phrases)]
    if not phrases:
        return {"status": "no-phrases", "checked": 0, "matches": [], "engine": "none"}
    matches = []
    errors = []
    engine = "google-cse" if (getattr(config, "GOOGLE_CSE_API_KEY", "") and
                                getattr(config, "GOOGLE_CSE_ID", "")) else "fallback"
    for phrase in phrases:
        query = '"' + phrase[:220] + '"'
        try:
            results = _google(query) if engine == "google-cse" else search_web(query, max_results=5)
            # Google CSE failure should not silently pretend it was checked.
            if engine == "google-cse" and not results:
                errors.append("google returned no results")
        except Exception as exc:  # noqa: BLE001
            errors.append(f"search: {type(exc).__name__}")
            continue
        for result in results[:5]:
            url = result.get("url", "")
            if not is_valid_source_url(url):
                continue
            host = urlparse(url).netloc.lower().replace("www.", "")
            if own_domain and host == own_domain.lower().replace("www.", ""):
                continue
            try:
                art = fetch_source(url)
                # whitespace-insensitive exact phrase evidence
                hay = re.sub(r"\s+", " ", (art.text or "")).lower()
                needle = re.sub(r"\s+", " ", phrase).lower()
                if needle in hay:
                    matches.append({"phrase": phrase, "url": url,
                                    "title": result.get("title", "")})
                    break
            except Exception as exc:  # noqa: BLE001
                log.debug("live phrase fetch skip %s: %s", url[:80], exc)
    status = "match" if matches else ("checked" if not errors else "partial")
    return {"status": status, "checked": len(phrases), "matches": matches,
            "errors": errors[:5], "engine": engine}


def format_report(rep: Dict) -> str:
    return (f"live originality: {rep.get('status')} · engine={rep.get('engine')} · "
            f"phrases={rep.get('checked', 0)} · exact matches={len(rep.get('matches', []))}")
