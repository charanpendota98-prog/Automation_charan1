"""End-to-end tests: SEO enhancer, source extraction, full rewrite pipeline.

Fakes: source website + WordPress REST + Telegram API.
Verifies:
  1. seo.enhance: TOC anchors, keyword first-para, internal+external links
  2. sources.fetch_source: title/text extraction from HTML
  3. pipeline.create_from_source (mock): draft + Rank Math meta + buttons + dedupe
  4. Rank Math meta fallback (plugin ledu -> retry without meta)
"""

import json
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from autoblog import config, notifier, seo, sources, state  # noqa: E402
from autoblog.wordpress_client import WordPressClient  # noqa: E402

tg_sent = []
wp_state = {"meta_mode": True, "created": []}

SAMPLE_NEWS_HTML = """<html><head>
<title>SSC New Recruitment 2026 Notification Released - ExampleSite</title>
<meta property="og:site_name" content="ExampleSite">
<meta property="og:description" content="SSC released new notification">
</head><body>
<nav>menu junk</nav>
<article>
<h1>SSC New Recruitment 2026 Notification Released</h1>
<p>Staff Selection Commission released a fresh recruitment notification for multiple posts across departments with a total of 3,200 vacancies for the year 2026 according to the official announcement published on Wednesday.</p>
<p>The online application process will begin next week on the official website ssc.gov.in and candidates must possess a bachelor degree from a recognized university to be eligible for these posts as per the detailed notification.</p>
<p>The selection process involves a computer based test followed by document verification and the application fee is one hundred rupees for general category candidates.</p>
<ul><li>Apply online through ssc.gov.in</li><li>Check eligibility before applying</li></ul>
</article>
<script>var x=1;</script>
</body></html>"""


class FakeSourceSite(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_GET(self):
        body = SAMPLE_NEWS_HTML.encode()
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

    def _auth(self):
        return self.headers.get("Authorization", "").startswith("Basic ")

    def do_GET(self):
        if not self._auth():
            self._json(401, {"code": "rest_not_logged_in"})
            return
        path = self.path.split("?")[0]
        if path == "/wp-json/wp/v2/users/me":
            self._json(200, {"id": 1, "name": "charan", "roles": ["administrator"]})
        elif path == "/wp-json/wp/v2/posts":
            self._json(200, [
                {"id": 10, "link": "https://studentup.in/prev-post/",
                 "title": {"rendered": "Previous Post"}, "categories": [5]},
            ])
        elif path == "/wp-json/wp/v2/categories":
            self._json(200, [{"id": 5, "name": "Education News"}])
        elif path == "/wp-json/wp/v2/tags":
            self._json(200, [])
        else:
            self._json(404, {"code": "rest_no_route"})

    def do_POST(self):
        if not self._auth():
            self._json(401, {"code": "rest_not_logged_in"})
            return
        n = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(n)
        path = self.path.split("?")[0]
        if path == "/wp-json/wp/v2/media":
            self._json(201, {"id": 88})
        elif path == "/wp-json/wp/v2/tags":
            self._json(201, {"id": 51, "name": json.loads(raw)["name"]})
        elif path == "/wp-json/wp/v2/posts":
            payload = json.loads(raw)
            if payload.get("meta") and not wp_state["meta_mode"]:
                # Rank Math plugin ledu simulation
                self._json(400, {"code": "rest_invalid_param",
                                 "message": "Invalid parameter(s): meta"})
                return
            wp_state["created"].append(payload)
            self._json(201, {"id": 200 + len(wp_state["created"]),
                             "link": "https://studentup.in/rewrite-test/",
                             "status": payload.get("status", "draft")})
        else:
            self._json(404, {"code": "rest_no_route"})


class FakeTelegram(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        payload = json.loads(self.rfile.read(n) or b"{}")
        if self.path.endswith("/sendMessage"):
            tg_sent.append(payload)
        body = json.dumps({"ok": True, "result": {}}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def test_seo_enhance():
    html = ("<p>Mundu parichayam paragraaph idi kavali first lo untundi.</p>"
            "<h2>Eligibility Details</h2><p>details here</p>"
            "<h2>How to Apply</h2><p>steps</p>"
            "<h2>Important Tips</h2><p>tips</p>"
            "<h2>FAQ</h2><p>faq</p>")
    out = seo.enhance(
        html,
        focus_keyword="SSC CGL 2026",
        internal_links=[{"link": "https://studentup.in/x/", "title": "X Post"}],
        external_links=[{"text": "SSC Official", "url": "https://ssc.gov.in"}],
    )
    # keyword injected into new first paragraph
    first_p = out.split("</p>")[0]
    assert "SSC CGL 2026" in first_p, first_p
    # TOC after first paragraph, with anchors
    assert "విషయ సూచిక" in out
    assert 'href="#how-to-apply"' in out
    assert out.find('id="how-to-apply"') > out.find("విషయ సూచిక")
    # internal + external links sections
    assert "https://studentup.in/x/" in out and "X Post" in out
    assert 'https://ssc.gov.in' in out and "SSC Official" in out
    assert 'rel="nofollow noopener"' in out
    print("  1. seo.enhance (TOC + keyword intro + links) ✔")


def test_source_fetch():
    srv = HTTPServer(("127.0.0.1", 0), FakeSourceSite)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    url = f"http://127.0.0.1:{srv.server_address[1]}/news/ssc-2026"
    src = sources.fetch_source(url)
    assert "SSC" in src.title
    assert src.site_name == "ExampleSite"
    assert "3,200 vacancies" in src.text
    assert "bachelor degree" in src.text
    assert "var x" not in src.text and "menu junk" not in src.text
    # blocked hosts
    assert not sources.is_valid_source_url("https://facebook.com/x")
    assert sources.is_valid_source_url(url)
    print("  2. sources.fetch_source (extract, junk-free) ✔")
    return url, srv


def test_full_pipeline(url, wp_base):
    db = config.STATE_PATH
    result = __import__("autoblog.pipeline", fromlist=["pipeline"]).create_from_source(
        url, mock=True
    )
    assert result["status"] == "draft"
    # WP post created with Rank Math meta + internal link + TOC in content
    payload = wp_state["created"][-1]
    fk = payload["meta"]["rank_math_focus_keyword"]
    assert fk.startswith("test guide 2026") and "," in fk  # multi-keyword (secondary)
    assert payload["status"] == "draft"
    content = payload["content"]
    assert "విషయ సూచిక" in content
    assert "quick-answer" in content          # featured snippet block
    assert "FAQPage" in content               # JSON-LD schema
    assert "https://studentup.in/prev-post/" in content  # internal link added
    assert "https://www.gov.in" in content                # external link added
    assert payload["featured_media"] == 88
    # telegram draft message with buttons + source url shown
    draft_msgs = [m for m in tg_sent if "NEW DRAFT" in m["text"]]
    assert draft_msgs and "rewrite-test" in json.dumps(draft_msgs[-1])
    assert any("Source (original rewrite)" in m["text"] for m in draft_msgs)
    kb = draft_msgs[-1]["reply_markup"]["inline_keyboard"]
    assert kb[0][0]["callback_data"].startswith("pub:")
    # source marked done -> duplicate rejected
    assert state.source_done(db, url)
    try:
        __import__("autoblog.pipeline", fromlist=["pipeline"]).create_from_source(url, mock=True)
        raise AssertionError("duplicate should fail")
    except ValueError:
        pass
    print("  3. full pipeline: URL -> original draft + RankMath meta + buttons + dedupe ✔")


def test_rankmath_fallback(wp):
    wp_state["meta_mode"] = False  # simulate plugin not installed
    wp_state["created"].clear()
    client = WordPressClient(site=wp, username="u", password="p a")
    res = client.create_post(
        title="Fallback Test", content_html="<p>x</p>", slug="fallback-test",
        category_id=5, tag_ids=[], excerpt="e", media_id=None,
        meta={"rank_math_focus_keyword": "kw"},
    )
    assert res["id"]
    # first request (meta) rejected 400, retry-without-meta created the post
    assert len(wp_state["created"]) == 1
    assert "meta" not in wp_state["created"][-1]
    wp_state["meta_mode"] = True
    print("  4. Rank Math meta fallback (plugin ledu -> clean retry) ✔")


def main():
    db = Path("/tmp/test_seo_pipeline.db")
    db.unlink(missing_ok=True)
    state.init(db)

    wp_srv = HTTPServer(("127.0.0.1", 0), FakeWP)
    tg_srv = HTTPServer(("127.0.0.1", 0), FakeTelegram)
    for s in (wp_srv, tg_srv):
        threading.Thread(target=s.serve_forever, daemon=True).start()
    wp_base = f"http://127.0.0.1:{wp_srv.server_address[1]}"

    config.STATE_PATH = db
    config.WP_SITE = wp_base
    config.TELEGRAM_BOT_TOKEN = "TEST"
    config.TELEGRAM_CHAT_ID = "555"
    config.TELEGRAM_API_BASE = f"http://127.0.0.1:{tg_srv.server_address[1]}"
    config.OUTPUT_DIR = Path("/tmp/test_output_images")
    config.IMAGE_ENABLED = True

    print("SEO + SOURCES + PIPELINE TESTS:")
    test_seo_enhance()
    url, src_srv = test_source_fetch()
    test_full_pipeline(url, wp_base)
    test_rankmath_fallback(wp_base)
    src_srv.shutdown()

    db.unlink(missing_ok=True)
    import shutil

    shutil.rmtree("/tmp/test_output_images", ignore_errors=True)
    print("ALL ADVANCED FEATURE TESTS PASSED ✔")


if __name__ == "__main__":
    main()
