"""v33 public Google-facing page audit.

Uses the public PageSpeed Insights endpoint when available and independently
checks rendered HTML basics. This is not Search Console, Rich Results Test, or
AdSense account access; those require the site owner's authenticated account.
"""
from __future__ import annotations

import json
import re
from html import unescape
from typing import Dict, List
from urllib.parse import urlparse

import requests

from . import config

PSI_ENDPOINT = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"


def _row(status: str, label: str, detail: str) -> Dict:
    return {"status": status, "label": label, "detail": detail}


def _valid_url(url: str) -> bool:
    parsed = urlparse((url or "").strip())
    return parsed.scheme in ("http", "https") and bool(parsed.netloc)


def html_checks(url: str, html: str, status_code: int = 200) -> List[Dict]:
    rows: List[Dict] = []
    parsed = urlparse(url)
    rows.append(_row("PASS" if parsed.scheme == "https" else "FAIL",
                     "HTTPS", "secure URL" if parsed.scheme == "https" else "HTTP URL"))
    rows.append(_row("PASS" if status_code == 200 else "WARN",
                     "HTTP response", str(status_code)))
    title = re.search(r"<title[^>]*>(.*?)</title>", html or "", re.I | re.S)
    title_text = " ".join(unescape(re.sub(r"<[^>]+>", " ", title.group(1))).split()) if title else ""
    rows.append(_row("PASS" if 20 <= len(title_text) <= 65 else "WARN",
                     "Title", f"{len(title_text)} chars: {title_text[:90] or 'missing'}"))
    desc = re.search(r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']*)', html or "", re.I)
    desc = desc or re.search(r'<meta[^>]+content=["\']([^"\']*)["\'][^>]+name=["\']description', html or "", re.I)
    desc_text = unescape(desc.group(1)).strip() if desc else ""
    rows.append(_row("PASS" if 100 <= len(desc_text) <= 170 else "WARN",
                     "Meta description", f"{len(desc_text)} chars" if desc_text else "missing"))
    canonical = re.search(r'<link[^>]+rel=["\']canonical["\'][^>]+href=["\']([^"\']+)', html or "", re.I)
    canonical = canonical or re.search(r'<link[^>]+href=["\']([^"\']+)["\'][^>]+rel=["\']canonical', html or "", re.I)
    canonical_url = canonical.group(1).strip() if canonical else ""
    requested = url.rstrip("/") or url
    canon_normal = canonical_url.rstrip("/") if canonical_url else ""
    rows.append(_row("PASS" if canonical and canon_normal == requested else "WARN",
                     "Canonical", canonical_url or "missing/mismatch"))
    noindex = bool(re.search(r'<meta[^>]+name=["\']robots["\'][^>]+content=["\'][^"\']*noindex', html or "", re.I))
    rows.append(_row("WARN" if noindex else "PASS", "Indexability",
                     "noindex present" if noindex else "no noindex directive"))
    h1 = len(re.findall(r"<h1\b", html or "", re.I))
    rows.append(_row("PASS" if h1 == 1 else "WARN", "H1", f"{h1} found"))
    viewport = bool(re.search(r'<meta[^>]+name=["\']viewport["\']', html or "", re.I))
    rows.append(_row("PASS" if viewport else "WARN", "Mobile viewport", "present" if viewport else "missing"))
    lang = re.search(r"<html\b[^>]*\blang=[\"']([^\"']+)", html or "", re.I)
    rows.append(_row("PASS" if lang else "WARN", "HTML language",
                     lang.group(1) if lang else "missing"))
    for prop, label in (("og:title", "Open Graph title"),
                        ("og:description", "Open Graph description"),
                        ("og:image", "Open Graph image")):
        found = bool(re.search(
            rf'<meta[^>]+property=["\']{re.escape(prop)}["\'][^>]+content=["\'][^"\']+',
            html or "", re.I))
        rows.append(_row("PASS" if found else "INFO", label,
                         "present" if found else "optional/missing"))
    scripts = re.findall(r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
                         html or "", re.I | re.S)
    valid_jsonld = 0
    for script in scripts:
        try:
            json.loads(unescape(script).strip())
            valid_jsonld += 1
        except (TypeError, ValueError, json.JSONDecodeError):
            pass
    rows.append(_row("PASS" if scripts and valid_jsonld == len(scripts) else "WARN",
                     "JSON-LD", f"{valid_jsonld}/{len(scripts)} valid script(s)"))
    images = re.findall(r"<img\b[^>]*>", html or "", re.I)
    missing_alt = sum(1 for image in images if not re.search(r"\balt\s*=\s*[\"'][^\"']*", image, re.I))
    rows.append(_row("PASS" if not missing_alt else "WARN", "Image alt text",
                     f"{missing_alt} missing of {len(images)}"))
    return rows


def _score(value) -> str:
    try:
        return str(round(float(value) * 100)) + "/100"
    except (TypeError, ValueError):
        return "n/a"


def pagespeed_check(url: str, strategy: str = "mobile") -> List[Dict]:
    params = {"url": url, "strategy": strategy, "category": ["performance", "accessibility", "best-practices", "seo"]}
    if config.PAGESPEED_API_KEY:
        params["key"] = config.PAGESPEED_API_KEY
    try:
        response = requests.get(PSI_ENDPOINT, params=params, timeout=config.GOOGLE_AUDIT_TIMEOUT)
        if response.status_code != 200:
            return [_row("WARN", f"PageSpeed {strategy}", f"HTTP {response.status_code}; API quota/key/network may be required")]
        data = response.json() or {}
        categories = data.get("lighthouseResult", {}).get("categories", {})
        rows = []
        for key, label in (("performance", "Performance"), ("accessibility", "Accessibility"),
                           ("best-practices", "Best Practices"), ("seo", "SEO")):
            score = categories.get(key, {}).get("score")
            rows.append(_row("PASS" if isinstance(score, (int, float)) and score >= .90 else "WARN",
                             f"PageSpeed {strategy} {label}", _score(score)))
        audits = data.get("lighthouseResult", {}).get("audits", {})
        for key, label in (("largest-contentful-paint", "LCP"),
                           ("cumulative-layout-shift", "CLS"),
                           ("interaction-to-next-paint", "INP")):
            audit = audits.get(key) or {}
            if audit:
                rows.append(_row("INFO", f"PageSpeed {strategy} {label}",
                                 str(audit.get("displayValue") or audit.get("numericValue") or "n/a")))
        return rows
    except Exception as exc:  # noqa: BLE001
        return [_row("WARN", f"PageSpeed {strategy}", str(exc)[:150])]


def audit_url(url: str, include_pagespeed: bool = True) -> List[Dict]:
    if not _valid_url(url):
        return [_row("FAIL", "URL", "Use a valid http(s) URL")]
    try:
        response = requests.get(url, timeout=config.GOOGLE_AUDIT_TIMEOUT,
                                headers={"User-Agent": "studentup-public-audit/1.0"})
        rows = html_checks(url, response.text[:2_000_000], response.status_code)
    except Exception as exc:  # noqa: BLE001
        rows = [_row("FAIL", "Page fetch", str(exc)[:150])]
    if include_pagespeed:
        rows.extend(pagespeed_check(url, "mobile"))
        rows.extend(pagespeed_check(url, "desktop"))
    return rows


def run(url: str) -> int:
    rows = audit_url(url)
    print("=" * 78)
    print(f"  GOOGLE-FACING PUBLIC PAGE AUDIT: {url}")
    print("=" * 78)
    for item in rows:
        icon = {"PASS": "✅", "WARN": "⚠️ ", "FAIL": "⛔", "INFO": "ℹ️ "}[item["status"]]
        print(f"  {icon} {item['label']:<28.28s} {item['detail'][:160]}")
    fails = sum(item["status"] == "FAIL" for item in rows)
    warns = sum(item["status"] == "WARN" for item in rows)
    print("-" * 78)
    print(f"  {len(rows) - fails - warns} pass · {warns} warnings · {fails} blockers")
    print("  This checks public HTML/PSI only; Search Console and AdSense account review need owner login.")
    print("=" * 78)
    return 1 if fails else 0
