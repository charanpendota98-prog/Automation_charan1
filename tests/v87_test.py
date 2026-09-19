# -*- coding: utf-8 -*-
"""v87 tests — FIX-ALL ROUND (update e2e + quiz + banners + hygiene).

Enduku idi:
  user: "fix all". Update flow e2e probe + quiz/banner visual audit cheste
  dorikina 7 REAL fixes:
  update rm100 KeyError (v84 feature dead!) · update official-links leda ·
  quiz level crash + questions unclamped + dup-guard late · Telugu banner
  tofu boxes · long-token overflow · footer overlap · empty-kw drafts ·
  auto-refresh silent.

Checks (offline only):
  * update e2e: rm100 score set, seo_score meta, dates, related=1,
    official-helper called + _source_urls set
  * quiz: level 9 → Top Level, questions 500 → ≤30, no crash
  * translit: Telugu → ASCII Latin (matras/conjuncts/digits)
  * banner: Telugu + long-token renders fit (webp, 1200x675)
  * hygiene: empty kw → title-derived
  * refresh: owner summary sent (mocked)
  * docs: README v87 + MANUAL PART 45 + counts

Run: python tests/v87_test.py   (also via python run.py --test-all)
"""
from __future__ import annotations

import json
import os
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from autoblog import (  # noqa: E402
    config,
    image_gen,
    pipeline,
    state,
)

OLD_HTML = ("<p>Old content para one with enough words for the test.</p>"
            "<h2>Sec</h2><p>Text here for testing.</p>"
            "<h2>More</h2><p>Extra words here.</p>")

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
            self._ok({"name": "t", "roles": ["editor"]})
        elif "posts/123" in self.path:
            self._ok({"id": 123, "slug": "s", "link": "http://x/s/",
                      "date": "2026-09-01T10:00:00",
                      "title": {"raw": "AP DSC 2026 Guide",
                                "rendered": "AP DSC 2026 Guide"},
                      "content": {"raw": OLD_HTML, "rendered": OLD_HTML},
                      "meta": {}})
        elif "posts" in self.path:
            self._ok([{"id": 1, "link": "http://x/a/",
                       "title": {"rendered": "Post A"}, "categories": []}])
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
        self._ok({"id": 123, "status": "draft", "link": "http://x/s/"})

    def log_message(self, *a):  # noqa: N802
        pass


class _Src(BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802
        body = ("<html><head><title>G</title></head><body><article>"
                "<h1>G</h1><p>" + "Gov notice text here. " * 10
                + "</p></article></body></html>").encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):  # noqa: N802
        pass


def test_update_e2e():
    db = Path("/tmp/v87_upd_e2e.db")
    db.unlink(missing_ok=True)
    state.init(db)
    srvs = []
    for cls in (_Src, _FakeWP):
        srv = HTTPServer(("127.0.0.1", 0), cls)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        srvs.append(srv)
    src_srv, wp_srv = srvs
    old = (config.STATE_PATH, config.WP_SITE)
    calls = []
    orig_helper = pipeline._append_official_sources

    def spy(article):
        calls.append(list(article.get("_source_urls") or []))
        return orig_helper(article)

    pipeline._append_official_sources = spy
    try:
        config.STATE_PATH = db
        config.WP_SITE = f"http://127.0.0.1:{wp_srv.server_address[1]}"
        CAP.clear()
        url = f"http://127.0.0.1:{src_srv.server_address[1]}/g"
        pipeline.update_post(123, new_source_urls=[url], mock=True)
    finally:
        config.STATE_PATH, config.WP_SITE = old
        pipeline._append_official_sources = orig_helper
        for srv in srvs:
            srv.shutdown()
        db.unlink(missing_ok=True)
    html = CAP.get("content") or ""
    assert CAP.get("title") == "AP DSC 2026 Guide", "title preserve kaledu"
    assert (CAP.get("meta") or {}).get("rank_math_seo_score"), \
        "rm100 score meta lo ledu (KeyError dead?)"
    assert '"datePublished": "2026-09-01"' in html, "published preserve kaledu"
    assert html.count('id="related-articles"') == 1
    assert calls and calls[0] and calls[0][0].endswith("/g"), \
        "update official-helper call kaledu"
    print("  update e2e: rm100 + dates + related + official ✔")


def test_quiz_clamp():
    db = Path("/tmp/v87_quiz.db")
    db.unlink(missing_ok=True)
    state.init(db)
    old = (config.STATE_PATH, config.OUTPUT_DIR)
    outdir = Path("/tmp/v87_qout2")
    outdir.mkdir(exist_ok=True)
    try:
        config.STATE_PATH = db
        config.OUTPUT_DIR = outdir
        r = pipeline.create_quiz(topic="GK", level=9, questions=500,
                                 mock=True, dry_run=True)
        html = Path(r["link"]).read_text(encoding="utf-8")
        assert "Top Level" in html, "level 9 clamp kaledu"
        assert html.count('{&quot;q&quot;') <= 30, "questions clamp kaledu"
    finally:
        config.STATE_PATH, config.OUTPUT_DIR = old
        db.unlink(missing_ok=True)
    print("  quiz: level/questions clamp ✔")


def test_translit():
    f = image_gen.telugu_to_latin
    assert f("నోటిఫికేషన్") == "notiphikeshan", f("నోటిఫికేషన్")
    assert f("విడుదల") == "vidudala"
    assert f("ఉద్యోగాలు ౨౦౨౬") == "udyogaalu 2026"
    assert f("AP DSC 2026").isascii()
    assert f("క్షేత్ర") == "kshetra", f("క్షేత్ర")
    print("  translit: Telugu → Latin ✔")


def test_banner_render():
    d = Path("/tmp/v87_bnr")
    d.mkdir(exist_ok=True)
    p1 = image_gen.generate_featured_image(
        "AP DSC 2026 నోటిఫికేషన్ విడుదల", "AP Govt Jobs", d / "t.webp")
    p2 = image_gen.generate_featured_image(
        "Supercalifragilisticexpialidocious" * 3, "Jobs", d / "l.webp")
    assert p1 and p2, "render fail"
    from PIL import Image
    for p in (p1, p2):
        im = Image.open(p)
        assert im.size == (1200, 675), im.size
    print("  banner: Telugu + long-token fit ✔")


def test_hygiene_kw_fallback():
    art = {"title": "AP DSC 2026 Notification Out", "focus_keyword": "",
           "tags": [], "category": "Jobs", "meta_description": "m" * 150,
           "content_html": "<p>x</p>"}
    pipeline._hygiene(art)
    assert art["focus_keyword"], "kw fallback kaledu"
    assert "DSC" in art["focus_keyword"], art["focus_keyword"]
    print("  hygiene: empty kw → title-derived ✔")


def test_refresh_summary():
    from autoblog import notifier
    old_targets = state.posts_to_refresh
    old_update = pipeline.update_post
    old_send = notifier.send_telegram
    old_tok, old_chat = config.TELEGRAM_BOT_TOKEN, config.TELEGRAM_CHAT_ID
    sent = []
    state.posts_to_refresh = lambda *a, **k: [{"wp_id": 7, "title": "Old Post"}]
    pipeline.update_post = lambda pid, **k: {"id": pid, "link": "http://x/old"}
    notifier.send_telegram = lambda text, **k: sent.append(text)
    # pipeline imported send lazily (from .notifier import ...) — patch target ok
    import autoblog.pipeline as pl
    _ = pl
    config.TELEGRAM_BOT_TOKEN = "T"
    config.TELEGRAM_CHAT_ID = "1"
    try:
        res = pipeline.auto_refresh(limit=1)
    finally:
        state.posts_to_refresh = old_targets
        pipeline.update_post = old_update
        notifier.send_telegram = old_send
        config.TELEGRAM_BOT_TOKEN = old_tok
        config.TELEGRAM_CHAT_ID = old_chat
    assert res and sent and "Auto-refresh" in sent[0], sent
    assert "http://x/old" in sent[0], sent
    print("  refresh: owner summary ✔")


def test_docs_v87():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    manual = (ROOT / "MANUAL_ADVANCED_CHECKLIST.md").read_text(encoding="utf-8")
    assert "### v87" in readme and "PART 45" in manual and "v87" in manual
    print("  docs: README v87 + MANUAL PART 45 ✔")


TESTS = [
    ("update e2e", test_update_e2e),
    ("quiz clamp", test_quiz_clamp),
    ("translit", test_translit),
    ("banner render", test_banner_render),
    ("hygiene kw fallback", test_hygiene_kw_fallback),
    ("refresh summary", test_refresh_summary),
    ("docs: v87 + PART 45", test_docs_v87),
]


def main() -> None:
    os.chdir(ROOT)
    print("=" * 70)
    print("v87 FIX-ALL ROUND — regression tests")
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
    print("ALL v87 FIX-ALL TESTS PASSED ✔")


if __name__ == "__main__":
    main()
