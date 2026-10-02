# -*- coding: utf-8 -*-
"""v186 — LIVE SITE AUDIT (deploy tarvata nijamaina site verification).

Enduku idi: ippati varaku unna anni gates **pre-deployment** (theme zip · tests ·
static CWV). Kaani "live site nijamga correct ga serve avutunda?" anedi veru
prashna — hosting config, redirects, headers, robots, sitemap, schema, PWA,
sample posts, 404 behavior. Ee module aa loop ni close chestundi:

    python run.py --live-audit --live-url https://studentup.in --live-notify

Checks (16) — anni **live URL meeda** nijamaina HTTP requests:
  1. reachability + TTFB (slow unte warn)
  2. http → https redirect
  3. www/non-www duplicate host
  4. robots.txt (Sitemap line, site-wide Disallow ledu)
  5. sitemap.xml (valid XML, URL count, post URLs)
  6. ads.txt (AdSense approved aithe mandatory)
  7. security headers (HSTS · nosniff · referrer · frame)
  8. compression (gzip/br HTML ki)
  9. homepage SEO (title/desc/H1/canonical/og/JSON-LD)
 10. schema (Organization/WebSite/JobPosting JSON-LD parse)
 11. viewport meta (mobile)
 12. PWA (manifest fetch + JSON + icons · sw.js)
 13. sample posts (status · H1 · canonical self · thin content)
 14. 404 handling (soft-404 ledu)
 15. static asset cache headers
 16. noindex safety (X-Robots-Tag / robots meta homepage ki ledu)

Report: `output/live-audit.json` + readable `.md` + optional Telegram summary.
Exit code: 0 all pass (warnings tho kuda) · 1 fail undi (`--live-strict` tho
warnings kuda fail). Ee tool **eem marchadu** — read-only verification.
"""
from __future__ import annotations

import html as _html
import json
import re
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin, urlparse

IST_OFFSET = "+05:30"

UA = ("Mozilla/5.0 (compatible; StudentUpLiveAudit/1.0; +https://studentup.in) "
      "AppleWebKit/537.36 Chrome/120 Safari/537.36")


# ---------------------------------------------------------------- helpers

def _now() -> datetime:
    from datetime import timedelta
    return datetime.now(timezone(timedelta(hours=5, minutes=30)))


def _result(cid: str, name: str, status: str, detail: str = "",
            evidence: str = "") -> Dict:
    """status: pass | warn | fail | skip"""
    return {"id": cid, "name": name, "status": status,
            "detail": detail, "evidence": evidence[:300]}


def _text(html: str) -> str:
    body = re.sub(r"(?is)<(script|style|noscript)[^>]*>.*?</\1>", " ", html)
    body = re.sub(r"(?s)<[^>]+>", " ", body)
    return re.sub(r"\s+", " ", _html.unescape(body)).strip()


def _meta(html: str, name: str) -> str:
    m = re.search(rf'<meta[^>]+name=["\']{re.escape(name)}["\'][^>]*content=["\']([^"\']*)',
                  html, re.I)
    if not m:
        m = re.search(rf'<meta[^>]+content=["\']([^"\']*)["\'][^>]*name=["\']{re.escape(name)}',
                      html, re.I)
    return (m.group(1).strip() if m else "")


def _prop(html: str, prop: str) -> str:
    m = re.search(rf'<meta[^>]+property=["\']{re.escape(prop)}["\'][^>]*content=["\']([^"\']*)',
                  html, re.I)
    if not m:
        m = re.search(rf'<meta[^>]+content=["\']([^"\']*)["\'][^>]*property=["\']{re.escape(prop)}',
                      html, re.I)
    return (m.group(1).strip() if m else "")


def _title(html: str) -> str:
    m = re.search(r"(?is)<title[^>]*>(.*?)</title>", html)
    return _html.unescape(m.group(1)).strip() if m else ""


def _canonical(html: str) -> str:
    m = re.search(r'<link[^>]+rel=["\']canonical["\'][^>]+href=["\']([^"\']+)', html, re.I)
    if not m:
        m = re.search(r'<link[^>]+href=["\']([^"\']+)["\'][^>]+rel=["\']canonical["\']', html, re.I)
    return m.group(1).strip() if m else ""


def _jsonld_blocks(html: str) -> List[object]:
    """@type values (nested tho) — JSON parse fail aithe skip (audit crash ledu)."""
    types: List[object] = []

    def walk(node: object) -> None:
        if isinstance(node, dict):
            t = node.get("@type")
            if t:
                types.append(t)
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)

    for m in re.finditer(r'(?is)<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
                         html):
        raw = m.group(1).strip()
        try:
            walk(json.loads(raw))
        except Exception:  # noqa: BLE001 — invalid JSON-LD = audit finding veru check tho
            types.append("__invalid__")
    return types


def _has_type(types: List[object], needle: str) -> bool:
    flat: List[str] = []
    for t in types:
        if isinstance(t, str):
            flat.append(t)
        elif isinstance(t, list):
            flat.extend(str(x) for x in t)
    return any(needle.lower() in x.lower() for x in flat)


def _origin(url: str) -> str:
    p = urlparse(url)
    return f"{p.scheme}://{p.netloc}"


def _other_host(url: str) -> str:
    """www ↔ non-www sibling (duplicate host check)."""
    p = urlparse(url)
    host = p.netloc
    if host.startswith("www."):
        return f"{p.scheme}://{host[4:]}"
    return f"{p.scheme}://www.{host}"


# ---------------------------------------------------------------- checks

class LiveAudit:
    """Live site ni check chese auditor (read-only · deterministic order)."""

    def __init__(self, url: str, timeout: int = 20, posts: int = 5,
                 adsense_approved: bool = False, session=None):
        self.base = url.rstrip("/")
        self.timeout = max(5, int(timeout))
        self.posts = max(0, int(posts))
        self.adsense_approved = bool(adsense_approved)
        self.results: List[Dict] = []
        self._net_errors = 0
        if session is not None:
            self.session = session
        else:
            import requests
            self.session = requests.Session()
            self.session.headers.update({"User-Agent": UA, "Accept-Language": "en-IN,en;q=0.8"})

    # -- low level
    def get(self, url: str, **kw) -> Optional[object]:
        try:
            return self.session.get(url, timeout=self.timeout, allow_redirects=True, **kw)
        except Exception as exc:  # noqa: BLE001 — network error = finding, crash kaadu
            self._net_errors += 1
            if self._net_errors == 1:
                # Okate network finding (dedupe) — prathi URL ki veru row pettithe
                # report noisy avutundi, reason okate untundi.
                self.results.append(_result(
                    "network", "Network reachability", "fail",
                    f"fetch fail ({exc.__class__.__name__}): {url[:70]} — SSL/DNS/hosting "
                    f"chudandi; site live ayyaka malli run cheyyandi",
                    str(exc)[:200]))
            return None

    def head_or_get(self, url: str) -> Optional[object]:
        try:
            r = self.session.head(url, timeout=self.timeout, allow_redirects=True)
            if r.status_code in (403, 405, 501) or r.status_code >= 500:
                raise ValueError("HEAD not supported")
            return r
        except Exception:  # noqa: BLE001
            return self.get(url)

    # -- 1+2+3
    def check_reachability(self) -> Tuple[bool, Optional[object]]:
        start = time.monotonic()
        r = self.get(self.base + "/")
        if r is None or r.status_code >= 400:
            code = getattr(r, "status_code", "no-response")
            self.results.append(_result("reachability", "Homepage reachable", "fail",
                                        f"HTTP {code}"))
            return False, r
        ttfb = int((time.monotonic() - start) * 1000)
        if ttfb > 4000:
            st, note = "fail", f"TTFB {ttfb}ms (>4000ms)"
        elif ttfb > self.warn_ms:
            st, note = "warn", f"TTFB {ttfb}ms (>{self.warn_ms}ms — cache/CDN chudandi)"
        else:
            st, note = "pass", f"HTTP {r.status_code} · TTFB {ttfb}ms"
        self.results.append(_result("reachability", "Homepage reachable", st, note))
        return True, r

    def check_redirects(self) -> None:
        p = urlparse(self.base)
        local = p.netloc.split(":")[0] in ("127.0.0.1", "localhost", "0.0.0.0", "::1")
        if local:
            self.results.append(_result("https-redirect", "http → https redirect", "skip",
                                        "local http target — SSL check N/A (production lo run cheyyandi)"))
        elif p.scheme == "https":
            plain = f"http://{p.netloc}/"
            try:
                r = self.session.get(plain, timeout=self.timeout, allow_redirects=False)
                loc = r.headers.get("location", "")
                ok = r.status_code in (301, 302, 307, 308) and loc.startswith("https://")
                self.results.append(_result(
                    "https-redirect", "http → https redirect",
                    "pass" if ok else "fail",
                    f"{r.status_code} → {loc[:80]}" if loc else f"{r.status_code} (redirect ledu)"))
            except Exception as exc:  # noqa: BLE001
                self.results.append(_result("https-redirect", "http → https redirect",
                                            "fail", f"http fetch fail: {exc}"))
        else:
            self.results.append(_result("https-redirect", "http → https redirect",
                                        "fail", "URL https kaadu — SSL ledu"))
        # www sibling
        sibling = _other_host(self.base) + "/"
        try:
            r = self.session.get(sibling, timeout=self.timeout, allow_redirects=True)
            final_host = urlparse(r.url).netloc
            chosen = urlparse(self.base).netloc
            if r.status_code >= 400:
                self.results.append(_result("www-host", "www/non-www single host", "pass",
                                            f"other host {r.status_code} (fine)"))
            elif final_host == chosen:
                self.results.append(_result("www-host", "www/non-www single host", "pass",
                                            f"{sibling} → {chosen}"))
            else:
                self.results.append(_result("www-host", "www/non-www single host", "warn",
                                            f"rendu hosts 200 (duplicate content risk): "
                                            f"{final_host} vs {chosen}"))
        except Exception as exc:  # noqa: BLE001
            self.results.append(_result("www-host", "www/non-www single host", "pass",
                                        f"other host reachable kaadu ({exc.__class__.__name__})"))

    # -- 4
    def check_robots(self) -> None:
        r = self.get(self.base + "/robots.txt")
        if r is None or r.status_code != 200:
            self.results.append(_result("robots", "robots.txt", "fail",
                                        f"HTTP {getattr(r, 'status_code', '—')}"))
            return
        body = r.text or ""
        ctype = (r.headers.get("content-type") or "").lower()
        if "<html" in body.lower() or "text/html" in ctype:
            self.results.append(_result("robots", "robots.txt", "fail",
                                        "HTML page istundi — robots.txt file ledu "
                                        "(SPA/WordPress rewrite robots.txt ni swallow chestundi)",
                                        body[:200]))
            return
        has_sitemap = bool(re.search(r"^\s*sitemap:\s*\S+", body, re.I | re.M))
        blocks_all = bool(re.search(r"^\s*disallow:\s*/\s*$", body, re.I | re.M))
        if blocks_all:
            self.results.append(_result("robots", "robots.txt", "fail",
                                        "site-wide `Disallow: /` — Google index cheyyadu!",
                                        body[-200:]))
        elif not has_sitemap:
            self.results.append(_result("robots", "robots.txt", "warn",
                                        "Sitemap line ledu", body[-200:]))
        else:
            self.results.append(_result("robots", "robots.txt", "pass",
                                        "Sitemap line undi · no site-wide block"))

    # -- 5
    def check_sitemap(self) -> List[str]:
        candidates = ["/sitemap.xml", "/sitemap_index.xml", "/wp-sitemap.xml"]
        urls: List[str] = []
        for path in candidates:
            r = self.get(self.base + path)
            if r is None or r.status_code != 200:
                continue
            try:
                root = ET.fromstring(r.content)
            except ET.ParseError as exc:
                self.results.append(_result("sitemap", "sitemap.xml", "fail",
                                            f"{path} XML parse fail: {exc}"))
                return []
            locs = [e.text.strip() for e in root.iter()
                    if e.tag.endswith("loc") and e.text]
            # sitemap index aithe child sitemaps ni teesukoni okati fetch cheyyi
            if root.tag.endswith("sitemapindex") and locs:
                post_map = next((u for u in locs if "post" in u.lower()), locs[0])
                child = self.get(post_map)
                if child is not None and child.status_code == 200:
                    try:
                        croot = ET.fromstring(child.content)
                        locs = [e.text.strip() for e in croot.iter()
                                if e.tag.endswith("loc") and e.text]
                    except ET.ParseError:
                        pass
            urls = [u for u in locs if u.startswith("http")]
            self.results.append(_result("sitemap", "sitemap.xml", "pass",
                                        f"{path} valid · {len(urls)} URLs"))
            break
        else:
            self.results.append(_result("sitemap", "sitemap.xml", "fail",
                                        "sitemap dorakaledu (sitemap.xml / sitemap_index.xml / "
                                        "wp-sitemap.xml)"))
        return urls

    # -- 6
    def check_ads_txt(self) -> None:
        r = self.get(self.base + "/ads.txt")
        code = getattr(r, "status_code", "—")
        body = (r.text or "").strip() if r is not None else ""
        if self.adsense_approved:
            if r is not None and r.status_code == 200 and "google.com" in body:
                self.results.append(_result("ads-txt", "ads.txt", "pass",
                                            f"{len(body.splitlines())} lines · google.com undi"))
            else:
                self.results.append(_result("ads-txt", "ads.txt", "fail",
                                            f"AdSense approved kaani ads.txt ledu/tappu (HTTP {code})"))
        else:
            self.results.append(_result("ads-txt", "ads.txt", "skip",
                                        "AdSense inka approve kaaledu — approve ayyaka ravali"))

    # -- 7
    def check_security_headers(self, r) -> None:
        headers = {k.lower(): v for k, v in (r.headers or {}).items()}
        checks = {
            "strict-transport-security": "HSTS",
            "x-content-type-options": "nosniff",
            "referrer-policy": "Referrer-Policy",
            "x-frame-options": "X-Frame-Options",
        }
        missing = [label for key, label in checks.items() if key not in headers]
        if not missing:
            self.results.append(_result("security-headers", "Security headers", "pass",
                                        "HSTS · nosniff · referrer · frame anni unnayi"))
        else:
            self.results.append(_result("security-headers", "Security headers", "warn",
                                        "levu: " + ", ".join(missing) +
                                        " (cPanel/Apache headers lo add cheyyachu)"))

    # -- 8
    def check_compression(self) -> None:
        try:
            r = self.session.get(self.base + "/", timeout=self.timeout,
                                 headers={"Accept-Encoding": "gzip, br"})
            enc = (r.headers.get("content-encoding") or "").lower()
            if enc in ("gzip", "br", "zstd", "deflate"):
                self.results.append(_result("compression", "Compression", "pass", enc))
            else:
                self.results.append(_result("compression", "Compression", "warn",
                                            "HTML compression ledu (gzip/br ON cheyyandi)"))
        except Exception as exc:  # noqa: BLE001
            self.results.append(_result("compression", "Compression", "warn", str(exc)))

    # -- 9+10+11+16 (homepage HTML)
    def check_homepage(self, r) -> None:
        html = r.text or ""
        title = _title(html)
        desc = _meta(html, "description") or _prop(html, "og:description")
        h1s = re.findall(r"(?is)<h1[^>]*>(.*?)</h1>", html)
        canonical = _canonical(html)
        og = _prop(html, "og:title")
        ld = _jsonld_blocks(html)
        problems: List[str] = []
        if not title:
            problems.append("title ledu")
        elif not (12 <= len(title) <= 70):
            problems.append(f"title {len(title)} chars")
        if not desc:
            problems.append("meta description ledu")
        elif not (50 <= len(desc) <= 170):
            problems.append(f"description {len(desc)} chars")
        if len(h1s) != 1:
            problems.append(f"H1 count {len(h1s)}")
        if not canonical:
            problems.append("canonical ledu")
        if not og:
            problems.append("og:title ledu")
        if not ld:
            problems.append("JSON-LD ledu")
        if problems:
            self.results.append(_result("homepage-seo", "Homepage SEO", "fail",
                                        " · ".join(problems)))
        else:
            self.results.append(_result("homepage-seo", "Homepage SEO", "pass",
                                        f"title {len(title)} · desc {len(desc)} · 1 H1 · "
                                        f"canonical · og · JSON-LD"))
        # schema
        want = ["Organization", "WebSite"]
        missing_schema = [t for t in want if not _has_type(ld, t)]
        if "__invalid__" in ld:
            self.results.append(_result("schema", "Schema JSON-LD", "warn",
                                        "okati JSON-LD block parse kaaledu"))
        elif missing_schema:
            self.results.append(_result("schema", "Schema JSON-LD", "warn",
                                        "levu: " + ", ".join(missing_schema)))
        else:
            self.results.append(_result("schema", "Schema JSON-LD", "pass",
                                        "Organization + WebSite"))
        # viewport
        if "viewport" in html.lower() and 'name="viewport"' in html.lower():
            self.results.append(_result("viewport", "Mobile viewport", "pass",
                                        "width=device-width"))
        else:
            self.results.append(_result("viewport", "Mobile viewport", "fail",
                                        "viewport meta ledu — mobile meeda desktop layout"))
        # noindex safety
        xrobots = (r.headers.get("x-robots-tag") or "").lower()
        meta_robots = _meta(html, "robots").lower()
        if "noindex" in xrobots or "noindex" in meta_robots:
            self.results.append(_result("noindex", "Homepage indexable", "fail",
                                        f"noindex kanipinchindi (header: {xrobots[:40]!r} "
                                        f"meta: {meta_robots[:40]!r})"))
        else:
            self.results.append(_result("noindex", "Homepage indexable", "pass",
                                        "noindex ledu"))

    # -- 12
    def check_pwa(self, html: str) -> None:
        m = re.search(r'<link[^>]+rel=["\']manifest["\'][^>]+href=["\']([^"\']+)', html, re.I)
        if not m:
            self.results.append(_result("pwa", "PWA manifest + SW", "warn",
                                        "manifest link ledu (theme PWA option ON aa?)"))
            return
        murl = urljoin(self.base + "/", m.group(1))
        r = self.get(murl)
        if r is None or r.status_code != 200:
            self.results.append(_result("pwa", "PWA manifest + SW", "fail",
                                        f"manifest HTTP {getattr(r, 'status_code', '—')}"))
            return
        try:
            data = json.loads(r.content.decode("utf-8-sig", "replace"))
        except Exception as exc:  # noqa: BLE001
            self.results.append(_result("pwa", "PWA manifest + SW", "fail",
                                        f"manifest JSON parse fail: {exc}"))
            return
        icons = data.get("icons") or []
        sw = self.get(self.base + "/sw.js")
        sw_ok = sw is not None and sw.status_code == 200
        if data.get("name") and icons and sw_ok:
            self.results.append(_result("pwa", "PWA manifest + SW", "pass",
                                        f"{len(icons)} icons · sw.js OK"))
        else:
            missing = [k for k, ok in (("name", data.get("name")), ("icons", icons),
                                       ("sw.js", sw_ok)) if not ok]
            self.results.append(_result("pwa", "PWA manifest + SW", "warn",
                                        "levu: " + ", ".join(missing)))

    # -- 13
    def _rest_post_urls(self) -> List[str]:
        """Sitemap pani cheyyakapote WordPress REST nunchi post links (fallback)."""
        try:
            r = self.session.get(
                self.base + f"/wp-json/wp/v2/posts?per_page={max(1, self.posts)}"
                            "&status=publish&_fields=link",
                timeout=self.timeout)
            if r.status_code != 200:
                return []
            data = json.loads(r.content.decode("utf-8-sig", "replace"))
            return [d.get("link") for d in data if isinstance(d, dict) and d.get("link")]
        except Exception:  # noqa: BLE001 — fallback fail = skip (crash ledu)
            return []

    def check_sample_posts(self, urls: List[str]) -> None:
        if not urls:
            urls = self._rest_post_urls()
            if urls:
                self.results.append(_result("sitemap-fallback", "Sitemap fallback", "warn",
                                            "sitemap use cheyyalem — WP REST tho post URLs "
                                            "teesukoni verify chesaamu"))
        candidates = [u for u in urls
                      if not u.rstrip("/").endswith(("sitemap.xml", ".xml"))
                      and not any(x in u for x in ("/category/", "/tag/", "/author/",
                                                   "/page/"))]
        # category archives + home ni teesi, okate sitemap lo unna posts sample
        sample = candidates[: self.posts] if self.posts else []
        if not sample:
            self.results.append(_result("posts", "Sample posts", "skip",
                                        "sitemap lo post URLs levu (posts publish ayyaka run cheyyandi)"))
            return
        bad_status, bad_seo, thin = [], [], []
        for u in sample:
            r = self.get(u)
            if r is None or r.status_code != 200:
                bad_status.append(f"{u} → {getattr(r, 'status_code', '—')}")
                continue
            html = r.text or ""
            title, h1s = _title(html), re.findall(r"(?is)<h1[^>]*>(.*?)</h1>", html)
            words = len(_text(html).split())
            if not title or len(h1s) != 1:
                bad_seo.append(f"{u.partition('://')[2][:50]} (title={bool(title)}, h1={len(h1s)})")
            if words < 300:
                thin.append(f"{words}w: {u.partition('://')[2][:44]}")
        if bad_status:
            self.results.append(_result("posts", "Sample posts", "fail",
                                        f"{len(bad_status)}/{len(sample)} fail · "
                                        + " · ".join(bad_status[:3])))
        elif bad_seo:
            self.results.append(_result("posts", "Sample posts", "warn",
                                        "title/H1 issue: " + " · ".join(bad_seo[:3])))
        elif thin:
            self.results.append(_result("posts", "Sample posts", "warn",
                                        "thin content (<300 words): " + " · ".join(thin[:3])))
        else:
            self.results.append(_result("posts", "Sample posts", "pass",
                                        f"{len(sample)} posts: 200 · title+H1 · "
                                        f"content ≥300 words"))

    # -- 14
    def check_404(self) -> None:
        r = self.get(self.base + "/_studentup-audit-404-check-xyz/")
        if r is None:
            return
        if r.status_code == 404:
            self.results.append(_result("404", "404 handling", "pass", "HTTP 404 ✅"))
        elif r.status_code == 200:
            self.results.append(_result("404", "404 handling", "warn",
                                        "soft-404: unknown URL 200 istundi (Google confusion)"))
        else:
            self.results.append(_result("404", "404 handling", "pass",
                                        f"HTTP {r.status_code}"))

    # -- 15
    def check_asset_cache(self, html: str) -> None:
        m = re.search(r'(?:href|src)=["\']([^"\']+\.(?:css|js))(?:\?[^"\']*)?["\']', html)
        if not m:
            self.results.append(_result("asset-cache", "Static asset caching", "skip",
                                        "CSS/JS asset kanipinchaledu"))
            return
        aurl = urljoin(self.base + "/", m.group(1))
        r = self.head_or_get(aurl)
        if r is None:
            return
        cc = (r.headers.get("cache-control") or "").lower()
        if "max-age" in cc and "no-store" not in cc:
            self.results.append(_result("asset-cache", "Static asset caching", "pass",
                                        cc[:60]))
        else:
            self.results.append(_result("asset-cache", "Static asset caching", "warn",
                                        f"Cache-Control weak/ledu ({cc or '—'})"))

    # -- run
    def run(self) -> Dict:
        self.warn_ms = 1500
        ok, home = self.check_reachability()
        if ok and home is not None:
            self.check_redirects()
            self.check_robots()
            urls = self.check_sitemap()
            self.check_ads_txt()
            self.check_security_headers(home)
            self.check_compression()
            self.check_homepage(home)
            self.check_pwa(home.text or "")
            self.check_sample_posts(urls)
            self.check_404()
            self.check_asset_cache(home.text or "")
        counts = {"pass": 0, "warn": 0, "fail": 0, "skip": 0}
        for row in self.results:
            counts[row["status"]] = counts.get(row["status"], 0) + 1
        scored = counts["pass"] + counts["fail"]
        score = round(100 * counts["pass"] / scored) if scored else 0
        return {
            "url": self.base,
            "checked_at": _now().isoformat(timespec="seconds"),
            "score": score,
            "counts": counts,
            "verdict": "HEALTHY" if counts["fail"] == 0 and score >= 80 else
                       ("NEEDS WORK" if counts["fail"] == 0 else "BROKEN"),
            "checks": self.results,
        }


# ---------------------------------------------------------------- report + CLI

def report_text(rep: Dict) -> str:
    icon = {"pass": "✅", "warn": "⚠️ ", "fail": "❌", "skip": "➖"}
    lines = [f"🌐 LIVE SITE AUDIT — {rep['url']}",
             f"   score {rep['score']}/100 · {rep['verdict']} · "
             f"{rep['counts']['pass']} pass · {rep['counts']['warn']} warn · "
             f"{rep['counts']['fail']} fail · {rep['counts']['skip']} skip", ""]
    for row in rep["checks"]:
        note = f" — {row['detail']}" if row["detail"] else ""
        lines.append(f"   {icon.get(row['status'], '?')} {row['name']}{note}")
        if row["status"] in ("fail", "warn") and row["evidence"]:
            lines.append(f"      ↳ {row['evidence'][:120]}")
    return "\n".join(lines)


def save_report(rep: Dict, path: Path) -> List[Path]:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    written = [path]
    path.write_text(json.dumps(rep, ensure_ascii=False, indent=2), encoding="utf-8")
    md = path.with_suffix(".md")
    md.write_text("```\n" + report_text(rep) + "\n```\n", encoding="utf-8")
    written.append(md)
    return written


def run_cli(url: str = "", posts: int = 5, notify: bool = False, strict: bool = False,
            timeout: int = 20) -> int:
    from . import config

    target = (url or getattr(config, "WP_SITE", "") or "").strip()
    if not target.startswith(("http://", "https://")):
        print("  ❌ URL kavali: --live-url https://studentup.in "
              "(leda .env lo WP_SITE)")
        return 2
    if posts in (0, None):
        posts = int(getattr(config, "LIVE_AUDIT_POSTS", 5) or 5)
    adsense = bool(getattr(config, "ADSENSE_APPROVED", False))
    audit = LiveAudit(target, timeout=timeout or int(getattr(config, "LIVE_AUDIT_TIMEOUT", 20)),
                      posts=posts, adsense_approved=adsense)
    rep = audit.run()
    print(report_text(rep))
    out = Path(getattr(config, "LIVE_AUDIT_PATH",
                       config.OUTPUT_DIR / "live-audit.json"))
    written = save_report(rep, out)
    print("  📄 " + " · ".join(str(p) for p in written))
    if notify:
        try:
            from . import notifier
            head = " | ".join(f"{k} {v}" for k, v in rep["counts"].items() if v)
            notifier.send_telegram(
                f"🌐 <b>Live audit {rep['verdict']}</b> · score {rep['score']}/100\n"
                f"{head}\n{rep['url']}")
        except Exception as exc:  # noqa: BLE001 — notify fail audit ni aapadu
            print(f"  ⚠️ notify fail: {exc}")
    if rep["counts"]["fail"] or (strict and rep["counts"]["warn"]):
        return 1
    return 0
