# -*- coding: utf-8 -*-
"""v81 tests — ULTIMATE SPEC GAP CLOSE (99 sections audit → real gaps fix).

Enduku idi:
  99-section Ultimate Spec ki against repo ni verify chesamu. Most covered
  (v80 audit + WP core + quiz analysis already · JobPosting validThrough ✓ ·
  nav/footer menus ✓). NIJAMAINA gaps 8: ?qual= indexable (P72) · rich tags
  strip (§2) · mobile tables overflow (§7) · JPEG only (§22) · orphan
  detection ledu (§32) · admin health widget ledu (§65) · search tracking
  ledu (§37) · HSTS option ledu (§76). Honest skips: mock-test series
  (accounts/infra — roadmap), CSP (AdSense break risk), WebP server-side
  (bot emits webp ✓).

Checks (offline only):
  * qual noindex: ?qual= → noindex,follow (perf.php)
  * sanitizer: blockquote/pre/code keep · script/iframe/video strip
  * prompt: tag lists updated (3 spots)
  * CSS: mobile table scroll + pre/code + dark
  * webp: .webp → WEBP format · .jpg → JPEG (PIL verify)
  * orphans: local sitemap crawl → inbound-0 report + exit 1
  * health widget: dashboard + deadlines + redirects + require
  * JS search tracking + node --check
  * HSTS: option + is_ssl guard
  * docs: README v81 + MANUAL PART 40 + 66/66

Run: python tests/v81_test.py   (also via python run.py --test-all)
"""
from __future__ import annotations

import http.server
import subprocess
import sys
import tempfile
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

from autoblog import image_gen, validator  # noqa: E402

THEME = ROOT / "wordpress-theme" / "studentup"


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


# ------------------------------------------------- 1-4. noindex/tags/css

def test_qual_noindex():
    perf = read(THEME / "inc" / "perf.php")
    assert "wp_robots', 'studentup_robots_thin'" in perf
    assert "isset( $_GET['qual'] )" in perf
    fn = perf.split("function studentup_robots_thin(")[1].split(
        "add_filter( 'wp_robots'")[0]
    assert "$robots['noindex'] = true;" in fn and "is_search()" in fn
    print("  qual noindex: ?qual= filter dupes closed ✔")


def test_rich_tags():
    html = ('<blockquote>note</blockquote><pre><code>x = 1</code></pre>'
            '<script>alert(1)</script><iframe src="x"></iframe>'
            '<video src="v.mp4"></video><p>ok</p>')
    out = validator.sanitize_html(html)
    for keep in ("<blockquote>", "<pre>", "<code>"):
        assert keep in out, f"strip avvakudadu: {keep}"
    for drop in ("<script", "<iframe", "<video"):
        assert drop not in out, f"strip avvali: {drop}"
    print("  sanitizer: callout/code keep + active strip ✔")


def test_prompt_tags():
    src = read(ROOT / "autoblog" / "gemini_client.py")
    assert src.count("blockquote pre code") == 3, src.count("blockquote")
    print("  prompt: rich tags 3/3 spots ✔")


def test_css_v81():
    css = read(THEME / "style.css")
    for needle in (".article-content table{display:block;overflow-x:auto",
                   ".article-content pre{", ".article-content p code{",
                   "body.dark .article-content pre{"):
        assert needle in css, f"CSS needle ledu: {needle}"
    print("  CSS: mobile tables + code blocks ✔")


# ------------------------------------------------- 5-6. webp + orphans

def test_webp_emit():
    from PIL import Image

    with tempfile.TemporaryDirectory() as td:
        w = Path(td) / "slug-name.webp"
        j = Path(td) / "slug-name.jpg"
        assert image_gen.generate_featured_image("Test Banner", "Results", w)
        assert image_gen.generate_featured_image("Test Banner", "Results", j)
        assert Image.open(w).format == "WEBP", "webp emit fail"
        assert Image.open(j).format == "JPEG", "jpg compat break"
        assert w.stat().st_size < j.stat().st_size, "webp smaller avvali"
    pipe = read(ROOT / "autoblog" / "pipeline.py")
    assert "{article['slug']}.webp" in pipe
    print("  webp: emit + jpg-compat + smaller ✔")


class _H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        port = self.server.server_address[1]
        base = f"http://127.0.0.1:{port}"
        if self.path == "/sitemap.xml":
            body = ("<?xml version='1.0'?><urlset>"
                    f"<url><loc>{base}/</loc></url>"
                    f"<url><loc>{base}/a</loc></url>"
                    f"<url><loc>{base}/orphan</loc></url></urlset>")
            raw = body.encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/xml")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)
        elif self.path == "/":
            body = (f'<a href="{base}/a">a</a>').encode()
            self.send_response(200)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif self.path == "/a":
            body = b"<p>leaf</p>"
            self.send_response(200)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif self.path == "/orphan":
            body = b"<p>lonely</p>"
            self.send_response(200)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404)
            self.send_header("Content-Length", "0")
            self.end_headers()

    def log_message(self, *a):
        pass


def test_orphan_crawl():
    import check_links as cl

    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), _H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        base = f"http://127.0.0.1:{srv.server_address[1]}"
        rc = cl.orphan_crawl(base + "/sitemap.xml", timeout=5)
        assert rc == 1, f"orphans undali (exit 1), got {rc}"
    finally:
        srv.shutdown()
    r = subprocess.run([sys.executable, str(ROOT / "run.py"), "--help"],
                       capture_output=True, text=True, timeout=60,
                       cwd=str(ROOT))
    assert "--orphans" in r.stdout
    print("  orphans: sitemap crawl + run.py --orphans ✔")


# ------------------------------------------------- 7-9. widget/js/hsts

def test_health_widget():
    h = read(THEME / "inc" / "health.php")
    for needle in ("wp_add_dashboard_widget(", "studentup_health_widget_render",
                   "studentup_last_date", "'BETWEEN'", "Expiring (7 days)",
                   "Expired (update/refresh)", "studentup_redirect_map"):
        assert needle in h, f"widget needle ledu: {needle}"
    assert "inc/health.php" in read(THEME / "functions.php")
    print("  health widget: deadlines + redirects ✔")


def test_search_tracking():
    js = read(THEME / "assets" / "js" / "studentup.js")
    assert 'input[name="s"]' in js and 'gtag("event", "search"' in js
    r = subprocess.run(["node", "--check",
                        str(THEME / "assets" / "js" / "studentup.js")],
                       capture_output=True, text=True, timeout=30)
    assert r.returncode == 0, r.stderr[:200]
    print("  JS: search event + node --check ✔")


def test_hsts_option():
    sec = read(THEME / "inc" / "security.php")
    assert "Strict-Transport-Security" in sec
    assert "hsts_enforce', '0'" in sec and "is_ssl()" in sec
    assert "CSP deliberate skip" in sec
    assert "'hsts_enforce'" in read(THEME / "inc" / "options.php")
    print("  HSTS: opt-in + SSL-guard + CSP note ✔")


# ------------------------------------------------- 10. docs

def test_docs_v81():
    suites = len(list((ROOT / "tests").glob("*_test.py")))
    assert suites == 66, f"suites {suites} (v85 tho 66 expect)"
    readme = read(ROOT / "README.md")
    manual = read(ROOT / "MANUAL_ADVANCED_CHECKLIST.md")
    go_live = read(ROOT / "GO_LIVE_CHECKLIST.md")
    assert "### v81" in readme and "66/66" in readme
    assert "PART 40" in manual and "v81" in manual and "66/66" in manual
    assert "66/66" in go_live
    for name, txt in (("README", readme), ("MANUAL", manual),
                      ("GO_LIVE", go_live)):
        assert "164/164" in txt, f"{name} lo jsdom claim poyindi"
    print("  docs: README v81 + MANUAL PART 40 + 66/66 ✔")


TESTS = [
    ("qual noindex", test_qual_noindex),
    ("rich tags sanitize", test_rich_tags),
    ("prompt tags", test_prompt_tags),
    ("CSS v81", test_css_v81),
    ("webp emit", test_webp_emit),
    ("orphan crawl", test_orphan_crawl),
    ("health widget", test_health_widget),
    ("search tracking", test_search_tracking),
    ("HSTS option", test_hsts_option),
    ("docs: v81 + PART 40 + 66/66", test_docs_v81),
]


def main() -> None:
    print("=" * 70)
    print("  v81 — ULTIMATE SPEC GAP CLOSE")
    print("=" * 70)
    failed = 0
    for name, fn in TESTS:
        try:
            fn()  # fns print their own proof line on success
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
    print("ALL v81 ULTIMATE-SPEC TESTS PASSED ✔")


if __name__ == "__main__":
    main()
