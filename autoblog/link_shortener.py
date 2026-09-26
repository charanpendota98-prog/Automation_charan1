# -*- coding: utf-8 -*-
"""Safe first-party URL shortener for owner-forwarded StudentUp lists.

The preferred provider is the StudentUp WordPress theme itself: a short root
slug such as ``/ssc-cgl-2026`` is stored in WordPress and 302-redirects to the
exact article while counting clicks. TinyURL/Bitly/Short.io remain optional
adapters. Any failure falls back to a native StudentUp URL.
"""
from __future__ import annotations

import hashlib
import html
import json
import logging
import os
import re
from pathlib import Path
from typing import Dict
from urllib.parse import urlparse

import requests
from requests.auth import HTTPBasicAuth

from . import config

log = logging.getLogger("autoblog.link_shortener")


def _cache_path() -> Path:
    raw = getattr(config, "SHORTLINK_CACHE", "") or str(config.LOG_DIR / "shortlinks.json")
    return Path(raw)


def _read_cache() -> Dict[str, str]:
    try:
        data = json.loads(_cache_path().read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError, TypeError):
        return {}


def _write_cache(data: Dict[str, str]) -> None:
    path = _cache_path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(tmp, path)
    except OSError:
        log.warning("short-link cache write skipped", exc_info=True)


def _valid_http(value: object) -> str:
    parsed = urlparse(str(value or "").strip())
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        return ""
    return str(value).strip()


def _slug_from_title(title: str, long_url: str, suffix: str = "") -> str:
    text = html.unescape(re.sub(r"<[^>]+>", " ", str(title or ""))).lower()
    words = re.findall(r"[a-z0-9]+", text)
    stop = {"complete", "details", "guide", "apply", "online", "official", "latest", "update", "the", "for", "and"}
    words = [word for word in words if word not in stop]
    slug = "-".join(words[:5]).strip("-")[:34]
    if len(slug) < 3:
        slug = "job-" + hashlib.sha1(long_url.encode("utf-8", "ignore")).hexdigest()[:8]
    if suffix:
        slug = f"{slug[:27].rstrip('-')}-{suffix[:6]}"
    return slug[:40].strip("-")


def _wordpress_link(long_url: str, title: str = "") -> str:
    """Create a first-party /slug link through the authenticated WP bridge."""
    site = str(getattr(config, "WP_SITE", "") or "").rstrip("/")
    username = str(getattr(config, "WP_USERNAME", "") or "")
    password = str(getattr(config, "WP_APP_PASSWORD", "") or "")
    if not site or not username or not password:
        return ""
    endpoint = f"{site}/wp-json/studentup/v1/shortlinks"
    timeout = int(getattr(config, "SHORTLINK_TIMEOUT", 12) or 12)
    slug = _slug_from_title(title, long_url)
    auth = HTTPBasicAuth(username, password)
    for candidate in (slug, _slug_from_title(title, long_url, hashlib.sha1(long_url.encode()).hexdigest())):
        resp = requests.post(
            endpoint, auth=auth,
            json={"slug": candidate, "original_url": long_url},
            timeout=timeout,
        )
        if resp.ok:
            link = _valid_http((resp.json() or {}).get("short_url"))
            if link:
                return link
        if resp.status_code not in (400, 409):
            log.warning("StudentUp short-link bridge failed: HTTP %s", resp.status_code)
            break
    return ""


def _provider_link(long_url: str, title: str = "") -> str:
    provider = str(getattr(config, "SHORTLINK_PROVIDER", "wordpress") or "wordpress").strip().lower()
    token = str(getattr(config, "SHORTLINK_API_TOKEN", "") or "").strip()
    domain = str(getattr(config, "SHORTLINK_DOMAIN", "") or "").strip()
    timeout = int(getattr(config, "SHORTLINK_TIMEOUT", 12) or 12)

    if provider in {"wordpress", "studentup", "own"}:
        return _wordpress_link(long_url, title)

    if provider == "bitly":
        if not token:
            return ""
        payload = {"long_url": long_url}
        if domain:
            payload["domain"] = domain
        resp = requests.post(
            "https://api-ssl.bitly.com/v4/shorten",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json=payload, timeout=timeout,
        )
        if resp.ok:
            return _valid_http((resp.json() or {}).get("link"))
        log.warning("Bitly short-link request failed: HTTP %s", resp.status_code)
        return ""

    if provider in {"tinyurl", "tiny"}:
        if not token:
            log.info("TinyURL selected but SHORTLINK_API_TOKEN is not configured")
            return ""
        resp = requests.post(
            "https://api.tinyurl.com/create",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json={"url": long_url}, timeout=timeout,
        )
        if resp.ok:
            data = resp.json() or {}
            data = data.get("data") if isinstance(data.get("data"), dict) else data
            return _valid_http(data.get("tiny_url") or data.get("url"))
        log.warning("TinyURL API request failed: HTTP %s", resp.status_code)
        return ""

    if provider in {"shortio", "short.io"}:
        if not token or not domain:
            return ""
        resp = requests.post(
            "https://api.short.io/links",
            headers={"Authorization": token, "Content-Type": "application/json"},
            json={"originalURL": long_url, "domain": domain}, timeout=timeout,
        )
        if resp.ok:
            data = resp.json() or {}
            return _valid_http(data.get("shortURL") or data.get("secureShortURL"))
        log.warning("Short.io short-link request failed: HTTP %s", resp.status_code)
        return ""

    if provider in {"isgd", "is.gd"}:
        resp = requests.get(
            "https://is.gd/create.php", params={"format": "simple", "url": long_url}, timeout=timeout,
        )
        if resp.ok:
            return _valid_http(resp.text.strip())
        log.warning("is.gd short-link request failed: HTTP %s", resp.status_code)
    return ""


def shorten(long_url: str, title: str = "") -> str:
    """Return a cached short URL, or the original URL on any safe failure."""
    long_url = _valid_http(long_url)
    if not long_url:
        return ""
    if not getattr(config, "SHORTLINK_ENABLED", False):
        return long_url
    cache = _read_cache()
    if _valid_http(cache.get(long_url)):
        return cache[long_url]
    try:
        short = _provider_link(long_url, title=title)
    except Exception:  # noqa: BLE001 — a provider must never stop the digest
        log.exception("short-link provider unavailable")
        short = ""
    if not short or short == long_url:
        return long_url
    cache[long_url] = short
    _write_cache(cache)
    return short
