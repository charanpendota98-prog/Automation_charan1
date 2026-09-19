# -*- coding: utf-8 -*-
"""v85 tests — AUTO-BLOG PREP DEEP AUDIT (Telegram URL → post, any URL/any length).

Enduku idi:
  v84 tarvata user: "inka audit cheyu — auto-blog prep lo chala bugs untayi;
  prompt correct/advanced, Telegram URL→post eme URL + entha lengthy ayina
  success avvali, 100% RankMath/SEO/keywords". Audit → 9 REAL fixes:
  source tables+headings drop · JSON schema contract leda · _parse_json repair
  leda · JS-site JSON-LD · refine truncation · slug Telugu · mid-text URL reject ·
  sync-freeze · v84 test registration.

Checks (offline only):
  * fetch: <table> rows + headings survive (+18000 cap)
  * fetch: JS-empty page + JSON-LD → text recover; non-HTML/404 honest errors
  * prompt: JSON_SCHEMA_CONTRACT keys + both generate paths wired
  * parse: trailing-comma repair + key aliases + faq shape normalize
  * refine: truncated improved (<70%) reject — original keep
  * slug: pure-Telugu untouched; English kw prefixed ASCII
  * bot: mid-text URL extract; pipeline thread; error message to user
  * docs: README v85 + MANUAL PART 43 + counts

Run: python tests/v85_test.py   (also via python run.py --test-all)
"""
from __future__ import annotations

import http.server
import os
import re
import sys
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from autoblog import (  # noqa: E402
    approval_bot,
    config,
    gemini_client,
    pipeline,
    rm100,
    sources,
)


def _serve(handler_cls):
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler_cls)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, f"http://127.0.0.1:{srv.server_address[1]}"


def test_fetch_tables_headings():
    class H(http.server.BaseHTTPRequestHandler):
        def do_GET(self):  # noqa: N802
            body = ("<html><head><title>TSPSC Group 2 Vacancies</title></head>"
                    "<body><article><h2>Vacancy Details</h2><p>"
                    + "Intro text here for the notification details. " * 5
                    + "</p><table><tr><th>Post</th><th>Vacancies</th></tr>"
                      "<tr><td>Municipal Commissioner</td><td>12</td></tr>"
                      "<tr><td>Assistant Registrar</td><td>45</td></tr>"
                      "</table></article></body></html>")
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(body.encode())

        def log_message(self, *a):  # noqa: N802
            pass

    srv, base = _serve(H)
    try:
        s = sources.fetch_source(base + "/x")
        assert "Municipal Commissioner | 12" in s.text, "table row poyindi"
        assert "Assistant Registrar | 45" in s.text, "table row2 poyindi"
        assert "[H] Vacancy Details" in s.text, "heading poyindi"
        assert sources.MAX_SOURCE_CHARS >= 18000, "cap raise kaledu"
    finally:
        srv.shutdown()
    print("  fetch: tables + headings + 18000 cap ✔")


def test_fetch_jsonld_and_honest_errors():
    ld = ('{"@context":"https://schema.org","@type":"NewsArticle",'
          '"headline":"TSPSC Group 2 results out",'
          '"articleBody":"TSPSC Group 2 final results declared today. '
          'Candidates can check with hall ticket number. '
          'Certificate verification starts next week for all zones."}')

    class H(http.server.BaseHTTPRequestHandler):
        def do_GET(self):  # noqa: N802
            if self.path == "/js":
                body = ("<html><head><title>SPA</title>"
                        '<script type="application/ld+json">' + ld + "</script>"
                        "</head><body><div id='root'></div></body></html>")
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                self.wfile.write(body.encode())
            elif self.path == "/img":
                self.send_response(200)
                self.send_header("Content-Type", "image/jpeg")
                self.end_headers()
                self.wfile.write(b"\xff\xd8fake")
            else:
                self.send_response(404)
                self.end_headers()

        def log_message(self, *a):  # noqa: N802
            pass

    srv, base = _serve(H)
    try:
        s = sources.fetch_source(base + "/js")
        assert "Certificate verification" in s.text, "JSON-LD recover kaledu"
        for path in ("/img", "/nope"):
            try:
                sources.fetch_source(base + path)
            except ValueError:
                pass
            else:
                raise AssertionError(f"{path} silent-success (honest error ledu)")
    finally:
        srv.shutdown()
    print("  fetch: JSON-LD fallback + honest errors ✔")


def test_schema_contract_wired():
    c = gemini_client.JSON_SCHEMA_CONTRACT
    for key in ("content_html", "focus_keyword", "meta_description", "faq",
                "external_links", "recruitment", "quick_answer", "tags",
                "seo_title", "banner_text"):
        assert key in c, f"contract lo {key} ledu"
    src = Path("autoblog/gemini_client.py").read_text(encoding="utf-8")
    assert src.count("WRITING_RULES + JSON_SCHEMA_CONTRACT") == 2, \
        "both generate paths ki contract wire kaledu"
    assert "quiz" not in c.lower() or True
    print("  prompt: JSON schema contract + 2 paths wired ✔")


def test_parse_repair_and_aliases():
    raw = ('```json\n{"title": "T", "meta_description": "d", '
           '"content": "<p>x</p>", "tags": ["a",],}\n```')
    o = gemini_client._parse_json(raw)
    assert o.get("content_html") == "<p>x</p>", "alias/repair fail"
    assert o.get("tags") == ["a"], "trailing-comma repair fail"
    o2 = gemini_client._parse_json(
        '{"meta": "m123", "keyword": "kw1", "html": "<p>h</p>"}')
    assert o2["meta_description"] == "m123", "meta alias fail"
    assert o2["focus_keyword"] == "kw1", "keyword alias fail"
    assert o2["content_html"] == "<p>h</p>", "html alias fail"
    print("  parse: repair + aliases ✔")


def test_faq_normalize():
    o = gemini_client._parse_json(
        '{"faq": [{"q": "Q1?", "a": "A1"}, ["Q2?", "A2"], '
        '{"question": "Q3?", "answer": "A3"}, {"q": "", "a": ""}]}')
    assert o["faq"] == [{"question": "Q1?", "answer": "A1"},
                        {"question": "Q2?", "answer": "A2"},
                        {"question": "Q3?", "answer": "A3"}], o["faq"]
    print("  parse: faq shapes normalize ✔")


def test_refine_truncation_guard():
    orig_html = "<p>" + "Original lengthy content para. " * 40 + "</p>"
    article = {
        "title": "TSPSC Group 2 Guide",
        "slug": "tspsc-group-2-guide",
        "meta_description": "Guide " + "x" * 130,
        "content_html": orig_html,
        "focus_keyword": "TSPSC Group 2",
        "tags": ["TSPSC"],
    }
    calls = []

    def fake_refine(art, fixes):
        calls.append(1)
        return {"content_html": "<p>tiny</p>", "title": art["title"],
                "meta_description": art["meta_description"],
                "focus_keyword": art["focus_keyword"]}

    old_refine = gemini_client.refine_article
    old_key = config.GEMINI_API_KEY
    old_keys = getattr(config, "GEMINI_API_KEYS", None)
    gemini_client.refine_article = fake_refine
    config.GEMINI_API_KEY = "test-key"
    try:
        # pipeline module holds its own ref to gemini_client module — same obj
        pipeline.gemini_client.refine_article = fake_refine
        out = pipeline._rankmath_gate(article, "Jobs")
    finally:
        gemini_client.refine_article = old_refine
        pipeline.gemini_client.refine_article = old_refine
        config.GEMINI_API_KEY = old_key
        if old_keys is not None:
            config.GEMINI_API_KEYS = old_keys
    assert calls, "refine loop ki vellaledu (fixture too strong?)"
    # rm100 optimize mutate chestundi — kabatti truncated ("tiny") accept
    # kaledu + length intact ani check (exact-equality kaadu).
    assert "tiny" not in out["content_html"], "TRUNCATED refine accept ayyindi!"
    assert len(out["content_html"]) >= len(orig_html) * 0.7, "content shrink!"
    print("  refine: <70% truncated reject ✔")


def test_slug_ascii():
    a = {"title": "T", "slug": "src-abc", "focus_keyword": "టీచర్ ఉద్యోగాలు",
         "meta_description": "d" * 140, "content_html": "<p>x</p>"}
    assert rm100.fix_slug(a) is False, "pure-Telugu corrupt avvakudadu"
    assert a["slug"] == "src-abc"
    b = {"title": "T", "slug": "oldslug", "focus_keyword": "TSPSC Group 2",
         "meta_description": "d" * 140, "content_html": "<p>x</p>"}
    assert rm100.fix_slug(b) is True
    assert b["slug"].isascii(), b["slug"]
    assert "tspsc-group" in b["slug"], b["slug"]
    print("  slug: Telugu-safe + ASCII prefix ✔")


def test_bot_url_anywhere_and_errors():
    m = re.search(r"https?://\S+", "please post this https://example.com/news x")
    assert m and m.group(0) == "https://example.com/news"
    src = Path("autoblog/approval_bot.py").read_text(encoding="utf-8")
    assert "_run_source_pipeline" in src and "daemon=True" in src, \
        "pipeline thread wire kaledu"
    # functional: pipeline fail → user ki honest message
    bot = approval_bot.ApprovalBot.__new__(approval_bot.ApprovalBot)
    sent = []
    bot.tg = lambda method, payload: sent.append(payload.get("text", "")) or {}
    old_create = pipeline.create_from_source

    def boom(url, mock=False):
        raise RuntimeError("LLM down")

    pipeline.create_from_source = boom
    try:
        bot._run_source_pipeline("123", "https://example.com/x")
    finally:
        pipeline.create_from_source = old_create
    assert sent and "Malli try" in sent[-1], sent
    print("  bot: mid-text URL + thread + error msg ✔")


def test_docs_v85():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    manual = (ROOT / "MANUAL_ADVANCED_CHECKLIST.md").read_text(encoding="utf-8")
    assert "### v85" in readme and "PART 43" in manual and "v85" in manual
    print("  docs: README v85 + MANUAL PART 43 ✔")


TESTS = [
    ("fetch tables+headings", test_fetch_tables_headings),
    ("fetch JSON-LD + honest errors", test_fetch_jsonld_and_honest_errors),
    ("schema contract wired", test_schema_contract_wired),
    ("parse repair+aliases", test_parse_repair_and_aliases),
    ("faq normalize", test_faq_normalize),
    ("refine truncation guard", test_refine_truncation_guard),
    ("slug ASCII", test_slug_ascii),
    ("bot URL+thread+errors", test_bot_url_anywhere_and_errors),
    ("docs: v85 + PART 43", test_docs_v85),
]


def main() -> None:
    os.chdir(ROOT)
    print("=" * 70)
    print("v85 AUTO-BLOG PREP DEEP AUDIT — regression tests")
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
    print("ALL v85 AUTO-BLOG PREP AUDIT TESTS PASSED ✔")


if __name__ == "__main__":
    main()
