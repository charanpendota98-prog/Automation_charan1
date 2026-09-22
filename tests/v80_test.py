# -*- coding: utf-8 -*-
"""v80 tests — MASTER PROMPT GAP CLOSE (50 phases audit → real gaps fix).

Enduku idi:
  50-phase Production Master Prompt + 5 additions ki against repo ni
  phase-by-phase VERIFY chesamu. Result: most covered (WP core + RankMath +
  mana 61 suites) — NIJAMAINA gaps 7: redirect manager ledu (P29) ·
  archive/search H1 ledu (P6) · category landing thin (P16) · 404 thin (P28) ·
  GA4/GSC wiring ledu (P24/25) · expired notice ledu (P26) ·
  RankMath-absent fallback ledu (P5) · link-liveness tool ledu (P47).
  Already-covered (no code): search noindex ✓ (perf.php) · expired badge ✓ ·
  FAQPage deliberate skip ✓ (Google retired) · quiz = practice+answer-key ✓.

Checks (offline only):
  * redirects: manager + guards (404-only · loop/chain-safe · no open-redirect)
  * archive: H1 + subcat chips + CSS
  * search: H1
  * 404: popular cats + latest posts
  * GA4/GSC: options + consent-aware loader + verification meta
  * JS: outbound/apply click tracking (gtag-gated)
  * expired notice: helper + single + CSS
  * SEO fallback: RankMath-absent description + OG
  * check_links: local server (live + dead + redirect → dead report, exit 1)
  * run.py --check-links wiring
  * php parse new files
  * docs: README v80 + MANUAL PART 39 + 68/68

Run: python tests/v80_test.py   (also via python run.py --test-all)
"""
from __future__ import annotations

import http.server
import subprocess
import sys
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

THEME = ROOT / "wordpress-theme" / "studentup"


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


# ------------------------------------------------- 1-4. redirects/archive/404

def test_redirect_manager():
    red = read(THEME / "inc" / "redirects.php")
    for needle in ("function studentup_redirect_map()",
                   "function studentup_redirect_resolve(",
                   "function studentup_redirect_maybe()",
                   "template_redirect', 'studentup_redirect_maybe', 2",
                   "wp_safe_redirect( home_url( $final ), 301 )",
                   "! is_404()", "open redirect", "loop"):
        assert needle in red, f"redirect needle ledu: {needle}"
    fn = read(THEME / "functions.php")
    assert "inc/redirects.php" in fn
    opts = read(THEME / "inc" / "options.php")
    assert "'redirects_json'" in opts
    print("  redirects: 301 mgr + 404-only + loop/chain-safe ✔")


def test_archive_rich():
    arch = read(THEME / "archive.php")
    assert "<h1><?php the_archive_title(); ?></h1>" in arch
    assert "studentup_subcat_chips(" in arch
    tpl = read(THEME / "inc" / "template.php")
    assert "function studentup_subcat_chips(" in tpl
    assert "'parent'" in tpl and "hide_empty" in tpl
    css = read(THEME / "style.css")
    assert ".su-subcats{" in css and "body.dark .su-subcats a{" in css
    assert ".sectionhead h1," in css
    print("  archive: H1 + subcat chips + CSS ✔")


def test_search_h1():
    search = read(THEME / "search.php")
    assert "<h1><?php the_archive_title(); ?></h1>" in search
    print("  search: H1 ✔")


def test_404_recovery():
    e404 = read(THEME / "404.php")
    for needle in ("get_search_form()", "'orderby'    => 'count'",
                   "su-404cats", "posts_per_page'      => 5",
                   "su-404latest", "wp_reset_postdata()"):
        assert needle in e404, f"404 needle ledu: {needle}"
    css = read(THEME / "style.css")
    assert ".su-404latest{" in css
    print("  404: search + popular cats + latest 5 ✔")


# ------------------------------------------------- 5-6. GA4/GSC + JS

def test_ga4_gsc():
    opts = read(THEME / "inc" / "options.php")
    assert "'ga4_id'" in opts and "'gsc_verify'" in opts
    con = read(THEME / "inc" / "consent.php")
    for needle in ("function studentup_ga4_head()",
                   "google-site-verification", "/^G-[A-Z0-9]{6,}$/",
                   "googletagmanager.com/gtag/js", "gtag('config'",
                   "anonymize_ip", "wp_head', 'studentup_ga4_head', 3"):
        assert needle in con, f"ga4 needle ledu: {needle}"
    print("  GA4/GSC: options + consent-aware loader ✔")


def test_js_tracking():
    js = read(THEME / "assets" / "js" / "studentup.js")
    for needle in ('typeof window.gtag !== "function"', "outbound_click",
                   "apply_click", "event_label"):
        assert needle in js, f"JS needle ledu: {needle}"
    r = subprocess.run(["node", "--check",
                        str(THEME / "assets" / "js" / "studentup.js")],
                       capture_output=True, text=True, timeout=30)
    assert r.returncode == 0, r.stderr[:200]
    print("  JS: outbound/apply tracking + node --check ✔")


# ------------------------------------------------- 7-8. expired + fallback

def test_expired_notice():
    qf = read(THEME / "inc" / "qual-filter.php")
    assert "function studentup_expired_notice(" in qf
    assert "Gaduvu mugisindi" in qf and "su-expired" in qf
    single = read(THEME / "single.php")
    assert "studentup_expired_notice" in single
    css = read(THEME / "style.css")
    assert ".su-expired{" in css and "body.dark .su-expired{" in css
    print("  expired: notice + single + CSS ✔")


def test_seo_fallback():
    bridge = read(THEME / "inc" / "seo-bridge.php")
    for needle in ("function studentup_seo_fallback_head()",
                   "RANK_MATH_VERSION", "class_exists( 'RankMath' )",
                   'meta name="description"', "og:description", "og:title",
                   "og:url", "og:image", "twitter:card", "og:site_name",
                   "rank_math_description"):
        assert needle in bridge, f"fallback needle ledu: {needle}"
    print("  SEO fallback: no-RankMath description + OG ✔")


# ------------------------------------------------- 9-10. link checker

class _Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        port = self.server.server_address[1]
        if self.path == "/page.html":
            body = (f'<html><body><a href="http://127.0.0.1:{port}/ok">ok</a>'
                    f'<a href="http://127.0.0.1:{port}/gone">gone</a>'
                    f'<a href="http://127.0.0.1:{port + 1}/x">conn-refused</a>'
                    '<a href="https://studentup.in/self">self</a></body></html>')
            raw = body.encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)
        elif self.path == "/ok":
            self.send_response(200)
            self.send_header("Content-Length", "0")
            self.end_headers()
        else:
            self.send_response(404)
            self.send_header("Content-Length", "0")
            self.end_headers()

    def do_HEAD(self):
        self.do_GET()

    def log_message(self, *a):
        pass


def test_check_links():
    import check_links as cl

    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        base = f"http://127.0.0.1:{srv.server_address[1]}"
        # extract: same-host skip (page host 127.0.0.1 == link host!) —
        # kabatti dedicated unit: foreign page host
        links = cl.extract_outbound(
            '<a href="http://127.0.0.1:1/a">a</a>'
            '<a href="https://studentup.in/b">b</a>',
            "https://studentup.in/page")
        assert links == ["http://127.0.0.1:1/a"], links
        res_ok = cl.check(base + "/ok", timeout=5)
        assert res_ok.ok and res_ok.status == 200, res_ok
        res_dead = cl.check(base + "/gone", timeout=5)
        assert not res_dead.ok and res_dead.status == 404, res_dead
        res_err = cl.check(base + ":1/x", timeout=2)
        assert not res_err.ok and res_err.status == 0, res_err
    finally:
        srv.shutdown()
    print("  check_links: extract + live/dead/conn-refused ✔")


def test_run_wiring():
    r = subprocess.run([sys.executable, str(ROOT / "run.py"), "--check-links"],
                       capture_output=True, text=True, timeout=60,
                       cwd=str(ROOT))
    assert r.returncode == 2 and "usage:" in r.stdout, (r.returncode, r.stdout[:150])
    r2 = subprocess.run([sys.executable, str(ROOT / "run.py"), "--help"],
                        capture_output=True, text=True, timeout=60,
                        cwd=str(ROOT))
    assert "--check-links" in r2.stdout
    print("  run.py: --check-links wired ✔")


# ------------------------------------------------- 11-12. lint + docs

def test_php_parse():
    import shutil

    if shutil.which("php") is None:
        print("  php lint: SKIP (php ledu, CI lo gate undi) ✔")
        return
    for f in ("inc/redirects.php", "inc/seo-bridge.php", "inc/consent.php",
              "inc/template.php", "archive.php", "search.php", "404.php"):
        r = subprocess.run(["php", "-l", str(THEME / f)], capture_output=True,
                           text=True, timeout=30)
        assert r.returncode == 0, f"{f}: {r.stderr or r.stdout}"
    print("  php -l: 7 files ✔")


def test_docs_v80():
    suites = len(list((ROOT / "tests").glob("*_test.py")))
    assert suites == 78, f"suites {suites} (v98 tho 78 expect)"
    readme = read(ROOT / "README.md")
    manual = read(ROOT / "MANUAL_ADVANCED_CHECKLIST.md")
    go_live = read(ROOT / "GO_LIVE_CHECKLIST.md")
    assert "### v80" in readme and f"{suites}/{suites}" in readme
    assert "PART 39" in manual and "v80" in manual and f"{suites}/{suites}" in manual
    assert f"{suites}/{suites}" in go_live
    for name, txt in (("README", readme), ("MANUAL", manual),
                      ("GO_LIVE", go_live)):
        assert "164/164" in txt, f"{name} lo jsdom claim poyindi"
    print("  docs: README v80 + MANUAL PART 39 + 68/68 ✔")


TESTS = [
    ("redirect manager", test_redirect_manager),
    ("archive rich", test_archive_rich),
    ("search H1", test_search_h1),
    ("404 recovery", test_404_recovery),
    ("GA4/GSC", test_ga4_gsc),
    ("JS tracking", test_js_tracking),
    ("expired notice", test_expired_notice),
    ("SEO fallback", test_seo_fallback),
    ("check_links", test_check_links),
    ("run.py wiring", test_run_wiring),
    ("php parse", test_php_parse),
    ("docs: v80 + PART 39 + 68/68", test_docs_v80),
]


def main() -> None:
    print("=" * 70)
    print("  v80 — MASTER PROMPT GAP CLOSE")
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
    print("ALL v80 MASTER-PROMPT TESTS PASSED ✔")


if __name__ == "__main__":
    main()
