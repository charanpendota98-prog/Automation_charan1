# -*- coding: utf-8 -*-
"""v86 tests — PROFESSIONAL POST AUDIT (end-to-end post quality).

Enduku idi:
  v85 tarvata user: "oka professional post avvali kada — inka emaina bugs
  vunnaya, advanced ga best ga audit chesi fix cheyu". Full pipeline ni
  local source tho end-to-end run chesi FINAL post HTML audit cheste
  dorikina 6 REAL bugs:
  duplicate related/read-also · news-source "official" mislabel ·
  Telugu TOC anchors · double breadcrumbs · pin-gate silent success
  (URL path + update path).

Checks (offline only):
  * e2e mock: no breadcrumb, ONE related, no read-also, ASCII anchors,
    featured image, excerpt, ASCII slug, no Source-N, su-source kept
  * official gate: gov → append, news → skip, dupes skip
  * is_official_domain: hosts + full URLs
  * anchors: Telugu heading → section-N, links match ids
  * bot: pin-gate error dict → honest ⛔ (source + update paths)
  * docs: README v86 + MANUAL PART 44 + counts

Run: python tests/v86_test.py   (also via python run.py --test-all)
"""
from __future__ import annotations

import json
import os
import re
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from autoblog import (  # noqa: E402
    approval_bot,
    config,
    pipeline,
    rm100,
    sources,
    state,
)


def _page(title: str) -> str:
    return ("<html><head><title>" + title + "</title></head><body><article>"
            "<h1>" + title + "</h1>"
            "<p>Content para for testing the pipeline end to end with words. "
            * 6 + "</p><h2>Details</h2><p>Detail text here for extraction. "
            * 6 + "</p><h2>How to Apply</h2><p>Apply steps text goes here. "
            * 6 + "</p></article></body></html>")


class _Src(BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802
        body = _page("AP DSC 2026 Notification Teacher Posts").encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):  # noqa: N802
        pass


CAP: dict = {}


class _FakeWP(BaseHTTPRequestHandler):
    def _ok(self, obj):  # noqa: N802
        body = json.dumps(obj).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):  # noqa: N802
        if "users" in self.path:
            self._ok({"name": "tester", "roles": ["editor"]})
        elif "posts" in self.path and "categories" not in self.path \
                and "tags" not in self.path:
            self._ok({"id": 999, "meta": {}})
        else:
            self._ok([])

    def do_POST(self):  # noqa: N802
        ln = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(ln) if ln else b"{}"
        try:
            data = json.loads(body)
            if "content" in data:
                CAP.update(data)
        except Exception:  # noqa: BLE001 — fake server
            pass
        self._ok({"id": 999, "status": "draft",
                  "link": "http://x/?p=999"})

    def log_message(self, *a):  # noqa: N802
        pass


class _FakeTG(BaseHTTPRequestHandler):
    def do_POST(self):  # noqa: N802
        ln = int(self.headers.get("Content-Length", 0))
        if ln:
            self.rfile.read(ln)
        body = b'{"ok": true, "result": {"message_id": 1}}'
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):  # noqa: N802
        pass


def _run_pipeline_e2e() -> dict:
    db = Path("/tmp/v86_e2e.db")
    db.unlink(missing_ok=True)
    state.init(db)
    servers = []
    for cls in (_Src, _FakeWP, _FakeTG):
        srv = HTTPServer(("127.0.0.1", 0), cls)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        servers.append(srv)
    src_srv, wp_srv, tg_srv = servers
    old = (config.STATE_PATH, config.WP_SITE, config.TELEGRAM_BOT_TOKEN,
           config.TELEGRAM_CHAT_ID, config.TELEGRAM_API_BASE, config.OUTPUT_DIR)
    outdir = Path("/tmp/v86_e2e_out")
    outdir.mkdir(exist_ok=True)
    try:
        config.STATE_PATH = db
        config.WP_SITE = f"http://127.0.0.1:{wp_srv.server_address[1]}"
        config.TELEGRAM_BOT_TOKEN = "TEST"
        config.TELEGRAM_CHAT_ID = "555"
        config.TELEGRAM_API_BASE = f"http://127.0.0.1:{tg_srv.server_address[1]}"
        config.OUTPUT_DIR = outdir
        url = f"http://127.0.0.1:{src_srv.server_address[1]}/dsc"
        CAP.clear()
        pipeline.create_from_source(url, mock=True)
        return dict(CAP)
    finally:
        config.STATE_PATH, config.WP_SITE, config.TELEGRAM_BOT_TOKEN, \
            config.TELEGRAM_CHAT_ID, config.TELEGRAM_API_BASE, \
            config.OUTPUT_DIR = old
        for srv in servers:
            srv.shutdown()
        db.unlink(missing_ok=True)


def test_e2e_professional_post():
    cap = _run_pipeline_e2e()
    html = cap.get("content") or ""
    assert len(html) > 3000, f"post too thin ({len(html)})"
    assert "su-breadcrumbs" not in html, "DOUBLE breadcrumb (theme + content)"
    assert html.count('id="related-articles"') == 1, "related block != 1"
    assert 'id="read-also"' not in html, "read-also duplicate undi"
    assert "Source 1" not in html, "news source official-links loki"
    assert "su-source" in html, "provenance su-source poyindi"
    assert '"BreadcrumbList"' in html, "schema breadcrumb poyindi"
    anchors = re.findall(r'href="#([^"]+)"', html)
    assert anchors, "TOC links levu"
    bad = [a for a in anchors if not a.isascii()]
    assert not bad, f"non-ASCII anchors: {bad[:3]}"
    assert cap.get("featured_media"), "featured image ledu"
    assert (cap.get("excerpt") or {}).get("raw"), "excerpt ledu"
    assert (cap.get("slug") or "").isascii(), "slug non-ASCII"
    print("  e2e: professional post (7 sub-checks) ✔")


def test_official_gate():
    art = {"external_links": [{"text": "Official Site",
                               "url": "https://www.gov.in"}],
           "_source_urls": ["https://ssc.gov.in/notice.pdf",
                            "https://eenadu.net/ap-dsc-news",
                            "https://www.gov.in/"]}
    pipeline._append_official_sources(art)
    urls = [l["url"] for l in art["external_links"]]
    assert "https://ssc.gov.in/notice.pdf" in urls, "gov append kaledu"
    assert "https://eenadu.net/ap-dsc-news" not in urls, "news mislabel!"
    assert sum(u.rstrip("/") == "https://www.gov.in" for u in urls) == 1, \
        "dupe append"
    assert any("Official Notice" in l["text"] for l in art["external_links"])
    print("  official gate: gov-only + dedupe ✔")


def test_is_official_domain():
    assert sources.is_official_domain("ssc.gov.in")
    assert sources.is_official_domain("https://apdsc.apcfss.ap.gov.in/x")
    assert sources.is_official_domain("nta.ac.in")
    assert not sources.is_official_domain("eenadu.net")
    assert not sources.is_official_domain("127.0.0.1:1234")
    assert not sources.is_official_domain("")
    print("  is_official_domain ✔")


def test_anchors_ascii():
    art = {"title": "T", "slug": "s", "focus_keyword": "k",
           "meta_description": "m" * 140,
           "content_html": "<p>i</p><h2>ముఖ్య వివరాలు</h2><p>a</p>"
                           "<h2>Key Details</h2><p>b</p>"
                           "<h2>దరఖాస్తు విధానం</h2><p>c</p>"}
    out = rm100.fix_toc(art, art["content_html"])
    ids = re.findall(r'id="([^"]+)"', out)
    links = re.findall(r'href="#([^"]+)"', out)
    assert ids and all(i.isascii() for i in ids), ids
    assert set(links) <= set(ids), "TOC link↔id mismatch"
    assert "ముఖ్య-వివరాలు" not in out, "Telugu anchor undi"
    print("  anchors: ASCII + link↔id match ✔")


def test_bot_pingate_honest():
    bot = approval_bot.ApprovalBot.__new__(approval_bot.ApprovalBot)
    sent = []
    bot.tg = lambda method, payload: sent.append(payload.get("text", "")) or {}
    old_create = pipeline.create_from_source
    old_update = pipeline.update_post
    err = {"error": "pin_gate", "detail": "critical: thin-content",
           "gate": {}}
    pipeline.create_from_source = lambda *a, **k: err
    pipeline.update_post = lambda *a, **k: err
    try:
        bot._run_source_pipeline("123", "https://example.com/x")
        bot.run_update(999, "123")
    finally:
        pipeline.create_from_source = old_create
        pipeline.update_post = old_update
    assert len(sent) == 2, sent
    assert all("⛔" in s and "thin-content" in s for s in sent), sent
    assert not any("ayyindi ✔" in s for s in sent), "false success!"
    print("  bot: pin-gate honest ⛔ (source + update) ✔")


def test_docs_v86():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    manual = (ROOT / "MANUAL_ADVANCED_CHECKLIST.md").read_text(encoding="utf-8")
    assert "### v86" in readme and "PART 44" in manual and "v86" in manual
    print("  docs: README v86 + MANUAL PART 44 ✔")


TESTS = [
    ("e2e professional post", test_e2e_professional_post),
    ("official gate", test_official_gate),
    ("is_official_domain", test_is_official_domain),
    ("anchors ASCII", test_anchors_ascii),
    ("bot pin-gate honest", test_bot_pingate_honest),
    ("docs: v86 + PART 44", test_docs_v86),
]


def main() -> None:
    os.chdir(ROOT)
    print("=" * 70)
    print("v86 PROFESSIONAL POST AUDIT — regression tests")
    print("=" * 70)
    failed = 0
    for name, fn in TESTS:
        try:
            fn()
        except AssertionError as exc:
            failed += 1
            print(f"  {name} ✘  {exc}")
        except Exception as exc:  # noqa: BLE001
            failed += 1
            print(f"  {name} ✘  {type(exc).__name__}: {exc}")
    print("-" * 70)
    if failed:
        print(f"  {failed} TEST(S) FAILED ✘")
        raise SystemExit(1)
    print("ALL v86 PROFESSIONAL POST AUDIT TESTS PASSED ✔")


if __name__ == "__main__":
    main()
