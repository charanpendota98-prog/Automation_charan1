#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v80 (P28/P47): outbound link-liveness checker.

Usage:
    python tools/check_links.py https://studentup.in/some-post/
    python tools/check_links.py URL1 URL2 --timeout 15

Enduku: expired official links (apply portals, PDFs) unna post trust +
ranking pothundi. Ee tool page lo outbound links anni HEAD/GET chesi
dead (4xx/5xx/timeout/DNS) + redirect-chain report istundi — pre-launch
crawl + monthly audit kosam. Auto-fix cheyyadu (human decision).

Exit: 0 = anni live · 1 = dead links unnayi · 2 = usage/fetch error.

v81 (§32/§60): --orphans SITEMAP-URL — sitemap URLs anni fetch chesi
internal-link graph build → inbound-0 pages = ORPHANS report.
Usage: python tools/check_links.py --orphans https://site/sitemap.xml
"""
from __future__ import annotations

import re
import sys
import urllib.parse
from dataclasses import dataclass


@dataclass
class LinkResult:
    url: str
    status: int       # 0 = fetch fail (DNS/timeout/refused)
    final_url: str
    hops: int
    ok: bool


def extract_outbound(html: str, page_url: str) -> list:
    """Page HTML nunchi absolute outbound http(s) links (dedupe, sorted)."""
    host = urllib.parse.urlparse(page_url).netloc.lower()
    out = set()
    for m in re.finditer(r'href=["\'](https?://[^"\']+)["\']', html, flags=re.I):
        u = m.group(1).strip()
        if urllib.parse.urlparse(u).netloc.lower() == host:
            continue
        out.add(u.split("#")[0])
    return sorted(out)


def check(url: str, timeout: int = 12) -> LinkResult:
    import requests

    try:
        r = requests.get(url, timeout=timeout, allow_redirects=True,
                         headers={"User-Agent": "StudentUp-LinkCheck/1.0"})
        hops = len(r.history)
        return LinkResult(url, r.status_code, r.url, hops,
                          ok=(r.status_code < 400 and hops <= 2))
    except Exception:  # noqa: BLE001 — DNS/timeout/refused = dead
        return LinkResult(url, 0, url, 0, ok=False)


def check_page(page_url: str, timeout: int = 12) -> tuple[list, list]:
    """Returns (dead, redirected). Prints report. Raises on page fetch fail."""
    import requests

    r = requests.get(page_url, timeout=timeout,
                     headers={"User-Agent": "StudentUp-LinkCheck/1.0"})
    r.raise_for_status()
    links = extract_outbound(r.text, page_url)
    print(f"page: {page_url}  (outbound: {len(links)})")
    dead, redir = [], []
    for u in links:
        res = check(u, timeout)
        if res.status == 0 or res.status >= 400:
            dead.append(res)
            print(f"  DEAD {res.status or 'ERR'}  {u}")
        elif res.hops > 0:
            redir.append(res)
            print(f"  REDIR {res.hops} hop(s) → {res.final_url}  ({u})")
        else:
            print(f"  ok {res.status}  {u}")
    return dead, redir


def _sitemap_urls(xml: str) -> list:
    locs = re.findall(r"<loc>\s*([^<]+?)\s*</loc>", xml)
    return sorted({u.strip() for u in locs if u.strip().startswith("http")})


def _internal_links(html: str, page_url: str) -> set:
    host = urllib.parse.urlparse(page_url).netloc.lower()
    out = set()
    for m in re.finditer(r'href=["\']([^"\']+)["\']', html, flags=re.I):
        u = urllib.parse.urljoin(page_url, m.group(1).strip()).split("#")[0]
        if urllib.parse.urlparse(u).netloc.lower() == host:
            out.add(u.rstrip("/") or u)
    return out


def orphan_crawl(sitemap_url: str, timeout: int = 12, limit: int = 200) -> int:
    """Sitemap → fetch (limit) → inbound graph → orphans print. Returns exit."""
    import requests

    try:
        xml = requests.get(sitemap_url, timeout=timeout,
                           headers={"User-Agent": "StudentUp-LinkCheck/1.0"}).text
    except Exception as exc:  # noqa: BLE001
        print(f"  SITEMAP FETCH FAIL: {exc}")
        return 2
    urls = [u for u in _sitemap_urls(xml)
            if not u.endswith(".xml")][:max(1, limit)]
    print(f"sitemap: {sitemap_url}  (pages: {len(urls)})")
    inbound: dict = {u.rstrip("/") or u: 0 for u in urls}
    fetched = 0
    dead: list = []  # v84: sitemap lone dead URLs (crawl-budget waste)
    for u in urls:
        try:
            resp = requests.get(u, timeout=timeout,
                                headers={"User-Agent": "StudentUp-LinkCheck/1.0"})
            if resp.status_code >= 400:
                dead.append(f"{resp.status_code} {u}")
                continue
            html = resp.text
        except Exception:  # noqa: BLE001 — dead page = 0 outbound, record
            dead.append(f"ERR {u}")
            continue
        fetched += 1
        for link in _internal_links(html, u):
            if link in inbound and link != (u.rstrip("/") or u):
                inbound[link] += 1
    orphans = sorted(k for k, v in inbound.items() if v == 0)
    print(f"  fetched {fetched}/{len(urls)} · dead: {len(dead)} · orphans: {len(orphans)}")
    for d in dead[:20]:
        print(f"  DEAD  {d}")
    if len(dead) > 20:
        print(f"  ... +{len(dead) - 20} more dead")
    for o in orphans[:30]:
        print(f"  ORPHAN  {o}")
    if len(orphans) > 30:
        print(f"  ... +{len(orphans) - 30} more")
    return 1 if orphans else 0


def main(argv: list) -> int:
    if "--orphans" in argv:
        rest = [a for a in argv[1:] if a != "--orphans" and not a.startswith("--")]
        if not rest:
            print("usage: python tools/check_links.py --orphans SITEMAP-URL [--timeout=N]")
            return 2
        timeout = 12
        for a in argv[1:]:
            if a.startswith("--timeout="):
                try:
                    timeout = max(3, min(60, int(a.split("=", 1)[1])))
                except ValueError:
                    pass
        return orphan_crawl(rest[0], timeout)
    urls = [a for a in argv[1:] if not a.startswith("--")]
    timeout = 12
    for a in argv[1:]:
        if a.startswith("--timeout="):
            try:
                timeout = max(3, min(60, int(a.split("=", 1)[1])))
            except ValueError:
                pass
    if not urls:
        print("usage: python tools/check_links.py URL [URL...] [--timeout=N]")
        return 2
    failed = False
    for u in urls:
        try:
            dead, _ = check_page(u, timeout)
            if dead:
                failed = True
        except Exception as exc:  # noqa: BLE001
            print(f"  FETCH FAIL {u}: {exc}")
            return 2
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
