# -*- coding: utf-8 -*-
"""v186 — live site audit tests (offline, local mock servers).

Rendu mock sites ni serve chestam:

  * GOOD  → anni checks pass avvali (robots · sitemap · schema · PWA · headers ·
            compression · posts · 404 · asset cache)
  * BROKEN→ fail/warn checks exact ga ravali (no robots, bad sitemap, soft-404,
            no h1, thin posts, no manifest, security headers ledu)

Cover:
  1. GOOD site: score · verdict HEALTHY · fail=0
  2. BROKEN site: fail/warn ids (robots · sitemap · homepage-seo · 404 · posts)
  3. ads.txt policy: approved → mandatory · not approved → skip
  4. Sample-post checks: status fail / thin warn / pass
  5. report_text + save_report (JSON + MD) + run_cli exit codes (0 / 1 / 2 strict)
  6. Docs wiring: --live-audit README/MANUAL/GO_LIVE + crontab + .env knobs
"""
from __future__ import annotations

import gzip
import http.server
import json
import socketserver
import sys
import tempfile
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from autoblog import config, live_audit as la  # noqa: E402

# ------------------------------------------------------------------ fixtures

POST_HTML = """<!DOCTYPE html><html lang="en-IN"><head>
<title>TS DSC Hall Ticket 2026 Download Link – StudentUp</title>
<meta name="description" content="TS DSC hall ticket 2026 download link, exam date and
instructions — verified from the official portal with step-by-step guide.">
<link rel="canonical" href="{url}">
<meta property="og:title" content="TS DSC Hall Ticket 2026">
<meta name="viewport" content="width=device-width,initial-scale=1">
</head><body><h1>TS DSC Hall Ticket 2026</h1>
<p>{body}</p></body></html>"""

HOME_HTML = """<!DOCTYPE html><html lang="en-IN"><head>
<title>StudentUp: TS &amp; AP Jobs, Scholarships, Results &amp; Exams 2026</title>
<meta name="description" content="TS &amp; AP govt jobs, scholarships, results, hall
tickets and exam updates — verified daily from official sources.">
<link rel="canonical" href="{url}/">
<meta property="og:title" content="StudentUp">
<meta name="viewport" content="width=device-width,initial-scale=1">
<link rel="manifest" href="{url}/manifest.webmanifest">
<link rel="stylesheet" href="{url}/style.css">
<script type="application/ld+json">{{"@type":"Organization","name":"StudentUp"}}</script>
<script type="application/ld+json">{{"@type":"WebSite","name":"StudentUp"}}</script>
</head><body><h1>StudentUp — every student update</h1></body></html>"""

WORDS = " ".join(["verified"] * 320)


def _site(kind: str):
    class Handler(http.server.BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def _send(self, code, body: bytes, ctype="text/html; charset=utf-8", extra=None):
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            for k, v in (extra or {}).items():
                self.send_header(k, v)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_HEAD(self):
            self.do_GET(head=True)

        def do_GET(self, head=False):  # noqa: F811
            host = f"http://{self.headers.get('Host', '127.0.0.1')}"
            path = self.path.split("?")[0]
            if kind == "good":
                extra = {"Strict-Transport-Security": "max-age=31536000",
                         "X-Content-Type-Options": "nosniff",
                         "Referrer-Policy": "strict-origin-when-cross-origin",
                         "X-Frame-Options": "SAMEORIGIN"}
                if path == "/":
                    body = HOME_HTML.format(url=host).encode()
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html")
                    self.send_header("Content-Encoding", "gzip")
                    for k, v in extra.items():
                        self.send_header(k, v)
                    raw = gzip.compress(body)
                    self.send_header("Content-Length", str(len(raw)))
                    self.end_headers()
                    if not head:
                        self.wfile.write(raw)
                    return
                if path == "/robots.txt":
                    return self._send(200, b"User-agent: *\nAllow: /\nSitemap: " +
                                      host.encode() + b"/sitemap.xml\n", "text/plain")
                if path == "/sitemap.xml":
                    urls = "".join(
                        f"<url><loc>{host}/post-{i}/</loc></url>" for i in range(1, 4))
                    return self._send(200, f'<?xml version="1.0"?><urlset>{urls}</urlset>'.encode(),
                                      "application/xml")
                if path == "/style.css":
                    return self._send(200, b"body{color:#111}",
                                      "text/css", {"Cache-Control": "public, max-age=31536000"})
                if path == "/manifest.webmanifest":
                    return self._send(200, json.dumps({
                        "name": "StudentUp", "start_url": "/",
                        "icons": [{"src": "/icon.png", "sizes": "192x192"}]}).encode(),
                        "application/manifest+json")
                if path == "/sw.js":
                    return self._send(200, b"self.addEventListener('fetch',()=>{})",
                                      "application/javascript")
                if path.startswith("/post-"):
                    return self._send(200, POST_HTML.format(url=host + path, body=WORDS).encode())
                return self._send(404, b"<h1>404</h1>")
            # ---------------- broken ----------------
            if path == "/":
                html = ("<html><head><title>x</title></head><body>"
                        "<h1>a</h1><h1>b</h1><img src='/x.png'></body></html>")
                return self._send(200, html.encode(), extra={"X-Robots-Tag": "noindex"})
            if path == "/sitemap.xml":
                return self._send(200, b"<urlset><url><loc>broken XML", "application/xml")
            if path.startswith("/wp-json/wp/v2/posts"):
                return self._send(200, json.dumps(
                    [{"link": f"{host}/post-{i}/"} for i in range(1, 3)]).encode(),
                    "application/json")
            if path.startswith("/post-"):
                return self._send(200, b"<html><title>thin</title><body>short</body></html>")
            if path == "/style.css":
                return self._send(200, b"body{}", "text/css")   # cache header ledu
            return self._send(200, b"<h1>soft 404</h1>")       # unknown → 200!

    return Handler


class _Server(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


def start(kind: str):
    srv = _Server(("127.0.0.1", 0), _site(kind))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, f"http://127.0.0.1:{srv.server_address[1]}"


def _by_id(rep):
    return {r["id"]: r for r in rep["checks"]}


# ------------------------------------------------------------------ tests

def test_good_site_healthy():
    srv, url = start("good")
    try:
        rep = la.LiveAudit(url, timeout=5, posts=2).run()
        rows = _by_id(rep)
        assert rep["counts"]["fail"] == 0, la.report_text(rep)
        assert rep["verdict"] == "HEALTHY", rep["verdict"]
        assert rep["score"] >= 80, rep["score"]
        for cid in ("reachability", "robots", "sitemap", "security-headers",
                    "compression", "homepage-seo", "schema", "viewport",
                    "noindex", "pwa", "posts", "404", "asset-cache"):
            assert rows[cid]["status"] == "pass", (cid, rows[cid])
        assert rows["https-redirect"]["status"] == "skip"  # local http = N/A (honest)
        assert "gzip" in rows["compression"]["detail"]
        assert rows["sitemap"]["detail"].startswith("/sitemap.xml") or "3 URLs" in rows["sitemap"]["detail"]
    finally:
        srv.shutdown()
    print("  1. GOOD site → HEALTHY · anni core checks pass ✔")


def test_broken_site_findings():
    srv, url = start("broken")
    try:
        rep = la.LiveAudit(url, timeout=5, posts=2).run()
        rows = _by_id(rep)
        assert rep["counts"]["fail"] > 0 and rep["verdict"] == "BROKEN"
        assert rows["robots"]["status"] == "fail"          # 200 (soft) lekapote fail
        assert rows["sitemap"]["status"] == "fail"          # invalid XML
        assert rows["sitemap-fallback"]["status"] == "warn"  # REST fallback · id clash ledu
        assert rows["homepage-seo"]["status"] == "fail"     # title/H1/desc/canonical
        assert "noindex" in rows["noindex"]["detail"] and rows["noindex"]["status"] == "fail"
        assert rows["security-headers"]["status"] == "warn"
        assert rows["compression"]["status"] == "warn"
        assert rows["viewport"]["status"] == "fail"
        assert rows["404"]["status"] == "warn"              # soft 404
        assert rows["posts"]["status"] == "warn"            # thin + no H1/title SEO
        assert rows["asset-cache"]["status"] == "skip"      # HTML lo asset link ledu
        assert rows["pwa"]["status"] == "warn"
        text = la.report_text(rep)
        assert "❌" in text and "BROKEN" in text
    finally:
        srv.shutdown()
    print("  2. BROKEN site → fail/warn ids exact ga (robots · sitemap · SEO · 404 · posts) ✔")


def test_ads_txt_policy():
    srv, url = start("good")
    try:
        assert _by_id(la.LiveAudit(url, timeout=5, posts=0).run())["ads-txt"]["status"] == "skip"
        assert _by_id(la.LiveAudit(url, timeout=5, posts=0,
                                   adsense_approved=True).run())["ads-txt"]["status"] == "fail"
    finally:
        srv.shutdown()
    srv2, url2 = start("broken")
    try:
        assert _by_id(la.LiveAudit(url2, timeout=5, posts=0,
                                   adsense_approved=True).run())["ads-txt"]["status"] == "fail"
    finally:
        srv2.shutdown()
    print("  3. ads.txt: approve kaaledu → skip · approved → mandatory fail ✔")


def test_sample_post_thin_and_missing():
    srv, url = start("broken")
    try:
        rep = la.LiveAudit(url, timeout=5, posts=3).run()
        assert _by_id(rep)["posts"]["status"] in ("warn", "fail")
        r0 = la.LiveAudit(url, timeout=5, posts=0).run()
        assert _by_id(r0)["posts"]["status"] == "skip", "posts=0 ki skip ravali"
    finally:
        srv.shutdown()
    print("  4. sample posts: thin warn · posts=0 skip ✔")


def test_report_save_and_cli():
    srv, url = start("good")
    old = (config.LIVE_AUDIT_PATH, config.WP_SITE, config.LIVE_AUDIT_POSTS,
           config.LIVE_AUDIT_TIMEOUT)
    try:
        with tempfile.TemporaryDirectory() as tmp:
            config.LIVE_AUDIT_PATH = Path(tmp) / "live.json"
            config.WP_SITE = url
            config.LIVE_AUDIT_POSTS = 1
            config.LIVE_AUDIT_TIMEOUT = 5
            rep = la.LiveAudit(url, timeout=5, posts=1).run()
            written = la.save_report(rep, config.LIVE_AUDIT_PATH)
            assert len(written) == 2 and all(p.exists() for p in written)
            data = json.loads(config.LIVE_AUDIT_PATH.read_text(encoding="utf-8"))
            assert data["url"] == url and data["checks"]
            assert config.LIVE_AUDIT_PATH.with_suffix(".md").read_text(encoding="utf-8").startswith("```")
            # CLI: healthy → rc 0 · URL ledu → rc 2
            assert la.run_cli(url, posts=1) == 0
            assert la.run_cli("ftp://nope") == 2
            config.WP_SITE = ""
            assert la.run_cli("") == 2, "URL ledu (flag + .env rendu) → usage error (2)"
            config.WP_SITE = url
            # strict: khali khali warn unna rc 1 avvali — broken site tho verify
            srv_b, url_b = start("broken")
            try:
                assert la.run_cli(url_b, posts=1) == 1, "broken site rc 1 ravali"
                assert la.run_cli(url_b, posts=1, strict=True) == 1
            finally:
                srv_b.shutdown()
    finally:
        (config.LIVE_AUDIT_PATH, config.WP_SITE, config.LIVE_AUDIT_POSTS,
         config.LIVE_AUDIT_TIMEOUT) = old
        srv.shutdown()
    print("  5. report/save/CLI exit codes (0/1/2) ✔")


def test_docs_wiring():
    for name in ("README.md", "MANUAL_ADVANCED_CHECKLIST.md", "MILESWEB_GO_LIVE.md"):
        text = (ROOT / name).read_text(encoding="utf-8")
        assert "--live-audit" in text, f"{name} lo --live-audit ledu"
    cron = (ROOT / "crontab.example").read_text(encoding="utf-8")
    assert "--live-audit" in cron, "crontab lo live audit line ledu"
    env = (ROOT / ".env.example").read_text(encoding="utf-8")
    for knob in ("LIVE_AUDIT_PATH", "LIVE_AUDIT_POSTS", "LIVE_AUDIT_TIMEOUT"):
        assert knob in env, f".env.example lo {knob} ledu"
    print("  6. docs/cron/.env wiring ✔")


def main() -> None:
    print("=" * 70)
    print("  v186 — LIVE SITE AUDIT (16 checks · real HTTP)")
    print("=" * 70)
    test_good_site_healthy()
    test_broken_site_findings()
    test_ads_txt_policy()
    test_sample_post_thin_and_missing()
    test_report_save_and_cli()
    test_docs_wiring()
    print("-" * 70)
    print("ALL v186 LIVE-AUDIT TESTS PASSED ✔")


if __name__ == "__main__":
    main()
