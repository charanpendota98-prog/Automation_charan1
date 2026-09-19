# -*- coding: utf-8 -*-
"""v84 tests — FULL BUG HUNT REGRESSIONS (money + ads + approvals).

Enduku idi:
  v83 tarvata user: "inka chala bugs undochu — anni fix cheyali, lekapothe
  amount/ads/approvals pothayi". Systematic hunt → 10 REAL fixes:
  schema-word pollution · UTC/IST deadline · AdSense approval gate ·
  hour double-post race · orphans default + dead-URLs · SQLite lock ·
  TG 4096 · date-archive noindex · DOUBLE TOC · update rm100.

Checks (offline only):
  * strip_tags: script/style blocks drop (schema JSON count loki raadu)
  * gate: thin+schema = FAIL (false-pass hole closed)
  * ist_today: IST date (server UTC kaadu)
  * approval gate: ads.php + options.php + pwa shared function
  * orphan_crawl: local 404 → DEAD report (real HTTP server)
  * orphans: no-URL → WP sitemap default (needle)
  * SQLite: WAL mode (overlap lock fix)
  * TG: 5000-char → truncate + send (mock post)
  * SEO: is_date noindex + Yoast/AIOSEO stand-down (needles)
  * TOC: add_table_of_contents idempotent (double-call = 1 box)
  * update: rm100 re-run present (needle)
  * first-para: ad <p> skip (utility classes)
  * docs: README v84 + MANUAL PART 42 + 65/65

Run: python tests/v84_test.py   (also via python run.py --test-all)
"""
from __future__ import annotations

import http.server
import sys
import tempfile
import threading
from datetime import datetime
from pathlib import Path
from unittest import mock
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

from autoblog import post_gate, rm100, seo, state, validator  # noqa: E402
from autoblog import notifier  # noqa: E402


def test_strip_tags_drops_script():
    html = "<h2>T</h2><p>" + "word " * 100 + "</p>"
    with_schema = html + seo.schema_jsonld(
        "T", "d" * 140, [], "2026-09-10", "s1",
        recruitment={"org_name": "TSPSC", "apply_end": "2026-12-31"})
    a = len(validator.strip_tags(html).split())
    b = len(validator.strip_tags(with_schema).split())
    assert a == b == 101, f"schema pollution: {a} vs {b}"
    css = html + "<style>.x{color:red}</style>"
    assert len(validator.strip_tags(css).split()) == 101
    print("  strip_tags: script/style drop (101=101) ✔")


def test_gate_thin_schema_fails():
    thin = "<h2>T</h2><p>" + "word " * 1400 + "</p>"
    thin += seo.schema_jsonld("T", "d" * 140, [], "2026-09-10", "s1")
    art = {"title": "T", "slug": "s", "focus_keyword": "k",
           "meta_description": "d" * 140}
    gate = post_gate.run(art, thin)
    rows = {r["id"]: r for r in gate["rows"]}
    assert rows["words"]["ok"] is False, "thin+schema false-PASS!"
    print(f"  gate: thin+schema FAIL ({rows['words']['detail']}) ✔")


def test_ist_today():
    expect = datetime.now(ZoneInfo("Asia/Kolkata")).date()
    assert validator.ist_today() == expect, "IST mismatch"
    print(f"  ist_today: {validator.ist_today()} ✔")


def test_approval_gate_needles():
    ads = (ROOT / "wordpress-theme" / "studentup" / "inc" / "ads.php"
           ).read_text(encoding="utf-8")
    opt = (ROOT / "wordpress-theme" / "studentup" / "inc" / "options.php"
           ).read_text(encoding="utf-8")
    pwa = (ROOT / "wordpress-theme" / "studentup" / "inc" / "pwa.php"
           ).read_text(encoding="utf-8")
    assert "adsense_approved" in opt, "option missing"
    fn = ads.split("function studentup_adsense_client()")[1].split(
        "\n}\n")[0]
    assert "adsense_approved" in fn, "ads.php gate missing"
    assert "studentup_adsense_client()" in pwa, "pwa bypass!"
    assert "ca-pub-" in fn, "regex gate missing"
    print("  approval gate: option + ads.php + pwa ✔")


class _H(http.server.BaseHTTPRequestHandler):
    def _send(self, code, body, ctype="text/html"):
        raw = body.encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(raw))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        base = f"http://127.0.0.1:{self.server.server_address[1]}"
        if self.path == "/sitemap.xml":
            self._send(200, f'<?xml version="1.0"?><urlset><url><loc>{base}/ok</loc></url>'
                            f'<url><loc>{base}/gone</loc></url></urlset>', "text/xml")
        elif self.path == "/ok":
            self._send(200, "<p>fine</p>")
        else:
            self._send(404, "nope")

    def log_message(self, *a):
        pass


def test_orphan_crawl_dead_report(capsys=None):
    import check_links as cl
    import io
    from contextlib import redirect_stdout

    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), _H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        base = f"http://127.0.0.1:{srv.server_address[1]}"
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = cl.orphan_crawl(base + "/sitemap.xml", timeout=5)
        out = buf.getvalue()
        assert "DEAD" in out and "/gone" in out, out
        assert "dead: 1" in out, out
        assert rc == 1, f"orphan exit 1 expect, got {rc}"
    finally:
        srv.shutdown()
    print("  orphan_crawl: DEAD report + exit 1 ✔")


def test_orphans_default_needle():
    main_src = (ROOT / "autoblog" / "main.py").read_text(encoding="utf-8")
    assert '"/wp-sitemap.xml"' in main_src, "orphans default missing"
    cron = (ROOT / "crontab.example").read_text(encoding="utf-8")
    assert "--orphans" in cron, "cron orphans line missing"
    print("  orphans default + cron ✔")


def test_sqlite_wal():
    db = Path(tempfile.mkdtemp()) / "w.db"
    state.init(db)
    import sqlite3

    mode = sqlite3.connect(str(db)).execute(
        "PRAGMA journal_mode").fetchone()[0]
    assert mode.lower() == "wal", f"journal={mode}"
    print("  SQLite WAL ✔")


def test_tg_truncate():
    from autoblog import config

    seen = {}

    def _fake_post(url, json=None, timeout=None):
        seen["text"] = json["text"]

        class _R:
            status_code = 200

            def json(self):
                return {"ok": True}
        return _R()

    with mock.patch.object(config, "TELEGRAM_BOT_TOKEN", "T"), \
         mock.patch.object(config, "TELEGRAM_CHAT_ID", "1"), \
         mock.patch("autoblog.notifier.requests.post", _fake_post):
        ok = notifier.send_telegram("x" * 5000)
    assert ok is True
    assert len(seen["text"]) <= 4000, len(seen["text"])
    assert "cut" in seen["text"]
    print(f"  TG truncate: 5000→{len(seen['text'])} ✔")


def test_seo_needles():
    perf = (ROOT / "wordpress-theme" / "studentup" / "inc" / "perf.php"
            ).read_text(encoding="utf-8")
    bridge = (ROOT / "wordpress-theme" / "studentup" / "inc" / "seo-bridge.php"
              ).read_text(encoding="utf-8")
    fn = perf.split("function studentup_robots_thin(")[1].split(
        "add_filter( 'wp_robots'")[0]
    assert "is_date()" in fn, "date noindex missing"
    assert "WPSEO_VERSION" in bridge and "AIOSEO_VERSION" in bridge, \
        "Yoast/AIO stand-down missing"
    print("  date noindex + Yoast/AIO stand-down ✔")


def test_toc_idempotent():
    html = "".join(f"<h2>Sec {i}</h2><p>text here.</p>" for i in range(4))
    once = seo.add_table_of_contents(html)
    twice = seo.add_table_of_contents(once)
    assert once == twice, "TOC not idempotent!"
    assert once.count("su-toc") >= 1
    # rm100 TOC + enhance = single box
    art = {"title": "T", "focus_keyword": "k",
           "content_html": html}
    rm100.apply(art)
    merged = seo.add_table_of_contents(art["content_html"])
    boxes = merged.count('<div class="su-toc"') + merged.count(
        '<nav class="su-toc"')
    assert boxes == 1, f"TOC boxes: {boxes}"
    print("  TOC idempotent (1 box) ✔")


def test_update_rm100_needle():
    pipe = (ROOT / "autoblog" / "pipeline.py").read_text(encoding="utf-8")
    fn = pipe.split("def update_post(")[1].split("\n\n\n")[0]
    assert "rm100.optimize" in fn, "update rm100 missing"
    main_src = (ROOT / "autoblog" / "main.py").read_text(encoding="utf-8")
    assert 'f"post:{today.isoformat()}:{now_hour:02d}"' in main_src, \
        "hour-claim missing"
    print("  update rm100 + hour-claim ✔")


def test_first_para_skips_ads():
    from autoblog import top_post

    html = ('<p class="su-qa">Short qa.</p>'
            '<p class="su-ad-desc">TSPSC APPSC SSC quiz promo text here '
            'download app now extra words padding</p>'
            '<p>TSPSC Group 2 — real intro para with keyword and enough '
            'words to qualify as content here.</p>')
    fp = top_post._first_content_para(html)
    assert "real intro" in fp, f"ad hijack: {fp[:60]}"
    assert "su-ad-desc" in top_post.UTILITY_PARA_CLASSES or \
        "su-ad" in top_post.UTILITY_PARA_CLASSES
    print("  first-para skips ad <p> ✔")


def test_docs_v84():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    manual = (ROOT / "MANUAL_ADVANCED_CHECKLIST.md").read_text(encoding="utf-8")
    go_live = (ROOT / "GO_LIVE_CHECKLIST.md").read_text(encoding="utf-8")
    assert "### v84" in readme and "65/65" in readme
    assert "PART 42" in manual and "v84" in manual and "65/65" in manual
    assert "67/67" in go_live
    for name, txt in (("README", readme), ("MANUAL", manual)):
        assert "164/164" in txt, f"{name} lo jsdom claim poyindi"
    print("  docs: README v84 + MANUAL PART 42 + 65/65 ✔")


TESTS = [
    ("strip_tags drops script/style", test_strip_tags_drops_script),
    ("gate thin+schema fails", test_gate_thin_schema_fails),
    ("ist_today", test_ist_today),
    ("approval gate needles", test_approval_gate_needles),
    ("orphan_crawl DEAD report", test_orphan_crawl_dead_report),
    ("orphans default + cron", test_orphans_default_needle),
    ("SQLite WAL", test_sqlite_wal),
    ("TG truncate", test_tg_truncate),
    ("date noindex + stand-down", test_seo_needles),
    ("TOC idempotent", test_toc_idempotent),
    ("update rm100 + hour-claim", test_update_rm100_needle),
    ("first-para skips ads", test_first_para_skips_ads),  # v85: missing reg fix
    ("docs: v84 + PART 42 + 65/65", test_docs_v84),
]


def main() -> None:
    print("=" * 70)
    print("  v84 — FULL BUG HUNT REGRESSIONS")
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
    print("ALL v84 FULL-BUG-HUNT TESTS PASSED ✔")


if __name__ == "__main__":
    main()
