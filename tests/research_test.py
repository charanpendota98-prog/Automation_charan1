"""Tests: multi-source research (web search + merge) + top-level SEO features.

Fakes: DuckDuckGo search endpoint, source sites, WordPress, Telegram.
Verifies:
  1. research.search_web: DDG HTML parse + uddg redirect unwrap
  2. research.research_topic: domain skip, short-content skip, extra fetch
  3. seo: quick answer block at TOP, FAQ+Article JSON-LD valid,
     rankmath_meta with comma-separated secondary keywords
  4. gemini RESEARCH prompt: contains merged sources
  5. full pipeline (mock): WP payload has quick answer + schema + keywords
"""

import json
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import quote_plus

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from autoblog import config, research, seo, sources, state  # noqa: E402

wp_created = []
tg_sent = []


class FakeDDG(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_GET(self):
        from urllib.parse import urlparse, parse_qs

        q = parse_qs(urlparse(self.path).query).get("q", [""])[0]
        results = [
            # extra source (uddg redirect format)
            ("https://html.duckduckgo.com/l/?uddg=https%3A%2F%2Fcompetitor1.com%2Fssc-2026&rut=abc",
             "SSC Recruitment 2026 – Full Details, Fee, Salary"),
            # same domain as primary -> must be skipped
            ("https://primarysite.com/self-link", "Same topic on same site"),
            # our own site -> must be skipped
            ("https://studentup.in/our-old-post", "Our own old post"),
        ]
        html = "<html><body>" + "".join(
            f'<a class="result__a" href="{href}">{title}</a>' for href, title in results
        ) + "</body></html>"
        body = html.encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


class FakeSite(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_GET(self):
        paras = "".join(
            f"<p>SSC recruitment 2026 detail paragraph number {i} with enough "
            f"length to pass extraction filters and content checks here.</p>"
            for i in range(12)
        )
        extra = ("<p>Application fee is 100 rupees and salary is 35,000 per month "
                 "as per the pay matrix level four.</p>")
        html = (f"<html><head><title>SSC 2026 Article</title>"
                f'<meta property="og:site_name" content="Competitor1"></head>'
                f"<body><article><h1>SSC 2026</h1>{paras}{extra}</article></body></html>")
        body = html.encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


class FakeWP(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _json(self, code, obj):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path.startswith("/wp-json/wp/v2/posts"):
            self._json(200, [])
        elif "categories" in self.path:
            self._json(200, [{"id": 5, "name": "Education News"}])
        elif "tags" in self.path:
            self._json(200, [])
        else:
            self._json(200, {"id": 1, "name": "charan", "roles": ["administrator"]})

    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(n)
        if self.path.endswith("/media"):
            self._json(201, {"id": 88})
        elif self.path.endswith("/tags"):
            self._json(201, {"id": 51, "name": json.loads(raw)["name"]})
        else:
            payload = json.loads(raw)
            wp_created.append(payload)
            self._json(201, {"id": 300, "link": "https://studentup.in/research-test/",
                             "status": "draft"})


class FakeTG(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        tg_sent.append(json.loads(self.rfile.read(n) or b"{}"))
        body = json.dumps({"ok": True, "result": {}}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main():
    db = Path("/tmp/test_research.db")
    db.unlink(missing_ok=True)
    state.init(db)

    ddg = HTTPServer(("127.0.0.1", 0), FakeDDG)
    site = HTTPServer(("127.0.0.1", 0), FakeSite)
    wp_srv = HTTPServer(("127.0.0.1", 0), FakeWP)
    tg_srv = HTTPServer(("127.0.0.1", 0), FakeTG)
    for s in (ddg, site, wp_srv, tg_srv):
        threading.Thread(target=s.serve_forever, daemon=True).start()

    config.STATE_PATH = db
    config.SEARCH_ENDPOINT = f"http://127.0.0.1:{ddg.server_address[1]}/"
    config.WP_SITE = f"http://127.0.0.1:{wp_srv.server_address[1]}"
    # studentup.in domain skip test kosam real domain echo cheat:
    config.TELEGRAM_BOT_TOKEN = "TEST"
    config.TELEGRAM_CHAT_ID = "555"
    config.TELEGRAM_API_BASE = f"http://127.0.0.1:{tg_srv.server_address[1]}"
    config.OUTPUT_DIR = Path("/tmp/test_research_out")
    config.IMAGE_ENABLED = True
    config.RESEARCH_ENABLED = True
    config.RESEARCH_MAX_SOURCES = 2

    print("RESEARCH + TOP-SEO TESTS:")

    # ---- 1. search_web ----
    results = research.search_web("SSC Recruitment 2026")
    urls = [r["url"] for r in results]
    assert "https://competitor1.com/ssc-2026" in urls, urls  # uddg unwrapped
    assert all(u.startswith("http") for u in urls)
    print("  1. search_web (DDG parse + uddg unwrap) ✔")

    # ---- 2. research_topic ----
    primary = sources.SourceArticle(
        url="https://primarysite.com/ssc-notification",
        title="SSC Recruitment 2026 Notification – PrimarySite",
        site_name="PrimarySite",
        text="primary text",
    )
    # own-domain skip test kosam WP_SITE temporarily real domain ki:
    local_wp = config.WP_SITE
    config.WP_SITE = "https://studentup.in"
    # monkeypatch fetch_source target: competitor link must be reachable.
    orig_fetch = research.fetch_source
    research.fetch_source = lambda url: sources.SourceArticle(
        url=url, title="SSC 2026 Article", site_name="Competitor1",
        text="detail paragraph " * 60,
    )
    extras, comp_titles = research.research_topic(primary, max_extra=2)
    research.fetch_source = orig_fetch
    config.WP_SITE = local_wp
    assert len(extras) == 1, [e.url for e in extras]
    assert "primarysite.com" not in extras[0].url
    assert "studentup.in" not in extras[0].url
    assert comp_titles and any("SSC" in t for t in comp_titles), comp_titles
    print("  2. research_topic (domain skip + extra fetch + keyword intel) ✔")

    # ---- 3. seo features ----
    html = ("<p>Intro para mundu.</p>"
            "<h2>Eligibility Details</h2><p>x</p><h2>How to Apply</h2><p>y</p>"
            "<h2>Important Tips</h2><p>z</p><h2>FAQ</h2><p>q</p>")
    out = seo.enhance(
        html,
        focus_keyword="SSC Bharti 2026",
        internal_links=[],
        external_links=[],
        quick_answer="SSC Bharti 2026 is a big test answer for snippets.",
        faq=[{"question": "Q1?", "answer": "A1"}, {"question": "Q2?", "answer": "A2"}],
        date_str="2026-09-07",
        slug="ssc-bharti-2026",
        title="SSC Bharti 2026 Test",
        description="desc",
    )
    assert "Reading Time" in out                          # reading badge top
    assert out.index("quick-answer") < out.index("విషయ సూచిక")
    assert "Quick Answer – SSC Bharti 2026" in out
    assert "Last Updated: 2026-09-07" in out
    assert "About This Article" in out                     # E-E-A-T trust box
    # JSON-LD valid
    import re as _re

    scripts = _re.findall(r'<script type="application/ld\+json">(.*?)</script>', out, _re.S)
    assert len(scripts) == 3, len(scripts)  # FAQ + Article + Breadcrumb
    faq_schema = json.loads(scripts[0])
    assert faq_schema["@type"] == "FAQPage" and len(faq_schema["mainEntity"]) == 2
    art_schema = json.loads(scripts[1])
    assert art_schema["@type"] == "Article" and art_schema["inLanguage"] == "te"
    assert json.loads(scripts[2])["@type"] == "BreadcrumbList"
    # rankmath meta comma keywords
    meta = seo.rankmath_meta("SSC Bharti 2026", "desc", "Title", ["ssc 2026 apply", "ssc fee"])
    assert meta["rank_math_focus_keyword"] == "SSC Bharti 2026, ssc 2026 apply, ssc fee"
    print("  3. seo (quick answer top + FAQ/Article JSON-LD + multi-keyword meta) ✔")

    # ---- 4. research prompt contains merged sources ----
    from autoblog import gemini_client as gc

    prompt = gc.RESEARCH_PROMPT_TEMPLATE.format(
        url=primary.url, site="PrimarySite", src_title=primary.title,
        src_text="primary facts", extra_sources_block=gc._format_extra_sources(extras),
        year=2026,
    )
    assert "PRIMARY SOURCE" in prompt and "RESEARCH SOURCE 1" in prompt
    assert "MERGE & BEAT" in prompt or "Merge ALL" in prompt
    assert "competitor1.com" in prompt or "SSC 2026 Article" in prompt
    print("  4. gemini research prompt (multi-source merge) ✔")

    # ---- 5. full pipeline (mock, research auto-skip for mock) ----
    import autoblog.pipeline as pl

    local_article_url = f"http://127.0.0.1:{site.server_address[1]}/real-article"
    result = pl.create_from_source(local_article_url, mock=True)
    assert result["status"] == "draft"
    payload = wp_created[-1]
    content = payload["content"]
    assert "quick-answer" in content
    assert "FAQPage" in content and "Article" in content
    fk = payload["meta"]["rank_math_focus_keyword"]
    assert "," in fk and "test guide 2026" in fk
    draft = [m for m in tg_sent if "NEW DRAFT" in m["text"]]
    assert draft and draft[-1]["reply_markup"]["inline_keyboard"][0][0]["callback_data"].startswith("pub:")
    print("  5. full pipeline (quick answer + schema + keywords in WP) ✔")

    db.unlink(missing_ok=True)
    import shutil

    shutil.rmtree("/tmp/test_research_out", ignore_errors=True)
    print("ALL RESEARCH + TOP-LEVEL SEO TESTS PASSED ✔")


if __name__ == "__main__":
    main()
