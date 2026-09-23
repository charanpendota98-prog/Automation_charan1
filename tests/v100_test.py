# -*- coding: utf-8 -*-
"""v100 — AUTOMATION WIRING + 3 REAL BUG FIXES (audit release).

Ee release lo kotha feature kanna **nijamaina bugs + missing wiring** meeda
focus chesanu — naa sonta v96–v99 code ni kuda audit chesi.

GAP-1 🐞 AUTOMATION LEDU: district hubs (v96) + link graph (v99) **CLI-only**.
  Ante owner prathi vaaram gurtu pettukoni manual ga run cheyyali. Adi
  jaragadu — orphan posts perigipotayi, district pages stale avutayi.
  Ippudu rendu weekly cron slot lopala (hub rebuild jarige chotane).

GAP-2 🐞 RELATIVE LINKS RESOLVE AVVATLEDU (link_graph bug — naa code):
  `/tspsc-group-2/` lanti site-relative link graph lo match avvadu → nijamga
  inbound links unna posts kuda **orphans ga report** ayyevi (false positive)
  → anavasaram ga extra links add ayyevi. WordPress themes relative links
  emit chestayi kabatti idi real-world lo common.

GAP-3 🐞 `javascript:` URL href lo velthundi (XSS vector):
  `seo._esc()` **text** ni escape chestundi kaani URL **scheme** ni validate
  cheyyadu. So district hub table lo / link-graph insert lo
  `href="javascript:alert(1)"` appatike emit ayyedi.
  Fix: `seo.safe_url()` — scheme allowlist + obfuscation (java\\tscript:) guard.

GAP-4 HUB PAGES INSTANT INDEXING KI POVATLEDU: posts submit avutayi
  (`pipeline._after_publish_push`), kaani hub/district pages organic crawl
  kosam wait chesevi — konni rojulu.

Checks (12). Offline-safe.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from autoblog import config, district_hubs as dh, link_graph as lg, seo  # noqa: E402

SUITES_EXPECTED = 95
SITE = "https://studentup.in"


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="ignore")


def _body(t: str, n: int = 6) -> str:
    return "<p>" + (f"{t} content here for students today. " * n) + "</p>"


# ------------------------------------------------------- 1 relative link bug

def test_relative_links_resolve() -> None:
    config.WP_SITE = SITE
    a = {"id": 1, "link": f"{SITE}/alpha", "title": "Alpha TSPSC Post",
         "content": _body("alpha"), "categories": [1]}
    b = {"id": 2, "link": f"{SITE}/b", "title": "B TSPSC Post",
         "content": _body("b") + '<p><a href="/alpha/">rel</a></p>', "categories": [1]}
    c = {"id": 3, "link": f"{SITE}/c", "title": "C TSPSC Post",
         "content": _body("c") + '<p><a href="//studentup.in/alpha">proto</a></p>',
         "categories": [1]}
    g = lg.build_graph([a, b, c], SITE)
    inbound = g["inbound"]["studentup.in/alpha"]
    assert "studentup.in/b" in inbound, f"relative link miss: {inbound}"
    assert "studentup.in/c" in inbound, f"protocol-relative miss: {inbound}"
    assert "studentup.in/alpha" not in g["orphans"], "false-positive orphan!"
    print("      relative + protocol-relative links resolve ✔")


def test_relative_link_dedupe() -> None:
    """Already `/alpha/` ga link unte, absolute URL tho duplicate raakudadu."""
    config.WP_SITE = SITE
    html = _body("x") + '<p><a href="/alpha/">x</a></p>'
    assert lg.insert_link(html, f"{SITE}/alpha", "Alpha") is None, \
        "relative link unna duplicate add chesindi"
    print("      relative-link duplicate guard ✔")


def test_trailing_slash_and_case() -> None:
    config.WP_SITE = SITE
    p = {"id": 1, "link": f"{SITE}/Alpha/", "title": "Alpha TSPSC",
         "content": _body("a") + f'<p><a href="{SITE}/alpha">self</a></p>',
         "categories": [1]}
    g = lg.build_graph([p], SITE)
    assert g["orphans"] == ["studentup.in/alpha"], "self-link counted as inbound"
    print("      case / trailing-slash normalise · self-link guard ✔")


# --------------------------------------------------------------- 2 safe_url

def test_safe_url_blocks_xss_schemes() -> None:
    for bad in ("javascript:alert(1)", "JaVaScRiPt:x", "java\tscript:alert(1)",
                "java\nscript:x", "data:text/html,<script>x</script>",
                "vbscript:msgbox", "  javascript:x  "):
        assert seo.safe_url(bad) == "", f"unsafe scheme pass ayindi: {bad!r}"
    for ok in (f"{SITE}/a", "http://x.com/y", "/rel/path", "#frag",
               "mailto:a@b.com", "tel:+919182739312"):
        assert seo.safe_url(ok), ok
    # fallback
    assert seo.safe_url("javascript:x", SITE) == SITE
    # quotes escape (attribute breakout guard)
    assert '"' not in seo.safe_url('https://x.com/a"onmouseover=1')
    print("      safe_url: js/data/vbscript + obfuscation blocked ✔")


def test_district_hub_no_js_href() -> None:
    posts = [{"title": "t", "link": "javascript:alert(1)", "date": "2026-01-01"}] * 3
    html = dh.build_hub_html("Karimnagar", "TS", posts)
    assert "javascript:alert" not in html, "district hub lo js href!"
    # normal link pani cheyyali
    ok = [{"title": "t", "link": f"{SITE}/p", "date": "2026-01-01"}] * 3
    assert f'href="{SITE}/p"' in dh.build_hub_html("Karimnagar", "TS", ok)
    print("      district hub: js href blocked · real link works ✔")


def test_link_graph_no_js_href() -> None:
    config.WP_SITE = SITE
    html = _body("body")
    assert lg.insert_link(html, "javascript:alert(1)", "Click") is None
    out = lg.insert_link(html, f"{SITE}/ok", "A & B <script>")
    assert out and f'href="{SITE}/ok"' in out
    assert "<script>" not in out and "&lt;script&gt;" in out, "anchor escape ledu"
    print("      link insert: js blocked · anchor escaped ✔")


# ------------------------------------------------------------- 3 automation

def test_weekly_automation_wired() -> None:
    src = read(ROOT / "autoblog" / "main.py")
    seg = src[src.index("hubweek"):src.index("count = state.today_count")]
    assert "district_hubs" in seg, "district hubs weekly slot lo ledu"
    assert "link_graph" in seg, "link graph weekly slot lo ledu"
    # apply=True ga run avvali (dry-run cron lo use ledu)
    assert "apply=True" in seg
    # prathi okkati try/except — okati fail aithe daily posting aagakudadu
    assert seg.count("except Exception") >= 3, "non-fatal guards ledu"
    # config gates
    for gate in ("DISTRICT_HUBS_AUTO", "LINK_GRAPH_AUTO"):
        assert gate in seg, gate
        assert hasattr(config, gate), f"config lo {gate} ledu"
    assert hasattr(config, "LINK_GRAPH_LIMIT")
    env = read(ROOT / ".env.example")
    for key in ("DISTRICT_HUBS_AUTO", "LINK_GRAPH_AUTO", "LINK_GRAPH_LIMIT"):
        assert key in env, f".env.example lo {key} ledu"
    print("      weekly cron: district hubs + link graph · gated · non-fatal ✔")


def test_automation_is_non_fatal() -> None:
    """Weekly job crash aithe daily posting flow aagakudadu."""
    src = read(ROOT / "autoblog" / "main.py")
    seg = src[src.index("hubweek"):src.index("count = state.today_count")]
    for block in ("district_hubs", "link_graph"):
        i = seg.index(block)
        after = seg[i:i + 700]
        assert "except Exception" in after, f"{block} guard ledu"
        assert "log.exception" in after, f"{block} silent fail avutundi"
    print("      weekly jobs non-fatal + logged ✔")


# ---------------------------------------------------------------- 4 indexing

def test_hub_pages_submitted_to_indexnow() -> None:
    for mod, name in ((read(ROOT / "autoblog" / "district_hubs.py"), "district_hubs"),
                      (read(ROOT / "autoblog" / "hubs.py"), "hubs")):
        assert "indexnow" in mod, f"{name}: instant indexing ledu"
        i = mod.index("indexnow")
        assert "except Exception" in mod[i - 400:i + 400], \
            f"{name}: indexnow best-effort kaadu (crash risk)"
    # dry-run lo submit cheyyakudadu
    d = read(ROOT / "autoblog" / "district_hubs.py")
    seg = d[d.index("v100: kotha/update"):]
    assert "if apply:" in seg, "dry-run lo kuda indexnow pilustundi"
    print("      hub + district pages → IndexNow (apply only, best-effort) ✔")


def test_indexnow_failure_does_not_break_rebuild() -> None:
    """IndexNow throw chesina district rebuild complete avvali."""
    import autoblog.indexnow as ixn

    class FakeWP:
        def search_posts(self, term, per_page=10):
            return [{"title": f"{term} job {i}", "link": f"{SITE}/{i}",
                     "date": "2026-09-01"} for i in range(4)]

        def upsert_page(self, t, h, s):
            return {"link": f"{SITE}/{s}/"}

    real = ixn.submit
    ixn.submit = lambda urls: (_ for _ in ()).throw(RuntimeError("boom"))
    try:
        rows = dh.rebuild(state="TS", apply=True, wp=FakeWP())
        assert rows and any(r.get("link") for r in rows), "rebuild ఆగిపోయింది"
    finally:
        ixn.submit = real
    print("      IndexNow fail → rebuild continues ✔")


# ------------------------------------------------------------------ 5 no-regress

def test_existing_guards_still_hold() -> None:
    """v99 safety guards ee release lo break avvakudadu."""
    config.WP_SITE = SITE
    html = _body("body")
    out = lg.insert_link(html, f"{SITE}/t", "Target Post Title")
    assert out and lg.insert_link(out, f"{SITE}/t", "x") is None   # dupe
    assert lg.insert_link("<h2>Heading only here now</h2>", f"{SITE}/a", "A") is None
    assert out.count("<a ") == 1
    print("      v99 guards intact (dupe · heading · single anchor) ✔")


def test_docs_and_suites() -> None:
    suites = len(list((ROOT / "tests").glob("*_test.py")))
    assert suites == SUITES_EXPECTED, f"suites {suites} (v115 tho 95)"
    readme = read(ROOT / "README.md")
    manual = read(ROOT / "MANUAL_ADVANCED_CHECKLIST.md")
    cur = f"{SUITES_EXPECTED}/{SUITES_EXPECTED}"
    assert "### v100" in readme and cur in readme
    assert "PART 57" in manual and cur in manual
    print(f"      docs: README v100 · PART 57 · {cur} ✔")


TESTS = [
    ("relative link resolve (bug)", test_relative_links_resolve),
    ("relative dedupe", test_relative_link_dedupe),
    ("case/slash normalise", test_trailing_slash_and_case),
    ("safe_url XSS guard (bug)", test_safe_url_blocks_xss_schemes),
    ("district hub js href", test_district_hub_no_js_href),
    ("link insert js href", test_link_graph_no_js_href),
    ("weekly automation wired", test_weekly_automation_wired),
    ("weekly jobs non-fatal", test_automation_is_non_fatal),
    ("hub pages indexnow", test_hub_pages_submitted_to_indexnow),
    ("indexnow fail safe", test_indexnow_failure_does_not_break_rebuild),
    ("v99 guards intact", test_existing_guards_still_hold),
    ("docs + suites", test_docs_and_suites),
]


def main() -> int:
    failed = 0
    for name, fn in TESTS:
        try:
            fn()
            print(f"  {name} ✔")
        except Exception as exc:  # noqa: BLE001
            failed += 1
            print(f"  {name} ✘  {type(exc).__name__}: {exc}")
    print("-" * 70)
    if failed:
        print(f"  {failed} TEST(S) FAILED ✘")
        return 1
    print("ALL v100 AUTOMATION + BUG-FIX TESTS PASSED ✔")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
