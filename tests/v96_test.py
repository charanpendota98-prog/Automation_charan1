# -*- coding: utf-8 -*-
"""v96 tests — COVERAGE + SESSION DEPTH + REAL BUG FIXES (theme 1.9.7).

Mee brief (2026-09-22): "ts and ap studentski em em posts vasthunnai … anni
… job melas … every district pages jobs … university results … daily current
affairs … telegram and whatsapp buttons neatga madhyalo … ads refresh
ayyevidam ga plan — automation kadu, vere page ki vachi malli mundu page
vachelaga … thumbnails neatga and daniki name."

Ee suite v96 lo close ayina **nijamaina gaps** ni regression ga kāpādutundi:

  GAP-1 COVERAGE MISS — job melas, district/local jobs, university results,
        dedicated hall-ticket axis, daily current affairs: ee intents grid lo
        LEVU (radar districts generic news matrame teesedhi), keyword universe
        lo entities kuda levu. Fix: 180 sources (37 kotha) + 221 entities
        (18 kotha) → 12,344 keywords. Counts guardian/readiness lo lock.

  GAP-2 MID-ARTICLE JOIN BUTTONS LEVU (bot side) — bot posts lo WhatsApp/
        Telegram CTA post CHIVARA matrame. Chala mandi akkadi varaku scroll
        cheyyaru. Fix: `monetize.join_strip_block()` + `insert_join_strip()`
        — modati content H2 tarvata, idempotent, links levakapote khali.
        Theme `.su-join-inline` tho duplicate raakunda cta.php lo dedupe guard.

  GAP-3 "ADS REFRESH" ni POLICY-SAFE ga — timer/auto-reload = AdSense invalid
        traffic (ban risk). Fix: theme `inc/upnext.php` — Up Next block +
        mobile sticky next bar. Reader tap = NIJAMAINA kotha pageview = legit
        kotha ad request. JS lo timer/redirect ledu ani ee suite verify chestundi.

  GAP-4 THUMBNAIL NAME — featured image eppudu `{slug}.webp` ga upload
        ayyedi (Google Images ki category/year context ledu). Fix:
        `seo.image_filename()` + `seo.image_alt()` + pipeline wiring.

  GAP-5 (REAL BUG) WEBP → `image/jpeg` MIME — v81 lo webp default ayyaka
        `upload_media()` inka hardcoded `image/jpeg` pampedi. WordPress
        filetype mismatch valla konni hosts upload REJECT chestayi → featured
        image ledu → schema/Discover image ledu. Fix: extension → real MIME.

  GAP-6 (REAL BUG) REFRESH LO MONETIZE BLOCKS POYEVI — `update_existing_post`
        lo `monetize.append_blocks()` call ledu, so auto-refresh ayina prathi
        post nunchi Telegram CTA + affiliate + join strip **delete** ayyevi.
        Fix: update path lo kuda monetize + ad_manager wiring.

  GAP-7 DISTRICT PAGES LEVU — 59 districts radar lo scan avutayi kaani
        landing page okkati kuda ledu. Fix: `autoblog/district_hubs.py`
        (+ CLI) — thin-page guard tho (MIN_POSTS kanna takkuva unte page
        create AVVADU; khali shelves = scaled-content risk).

Checks (17). Run: python tests/v96_test.py   (or python run.py --test-all)
"""
from __future__ import annotations

import os
import re
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

THEME = ROOT / "wordpress-theme" / "studentup"
SUITES_EXPECTED = 82  # v96 tho


def read(rel: "Path | str") -> str:
    return Path(rel).read_text(encoding="utf-8")


# ------------------------------------------------------------------ GAP-1
def test_source_grid_expanded() -> None:
    from autoblog import config, sources_grid

    grid = sources_grid._S
    assert len(grid) == 180, f"180 sources undali, vachhindi {len(grid)}"
    names = " ".join(s[0] for s in grid).lower()
    queries = " ".join(s[1] for s in grid).lower()
    for needle in ("job mela", "district jobs", "jntuh results", "hall tickets",
                   "daily current affairs", "anganwadi"):
        assert needle in names, f"v96 source miss: {needle}"
    assert "job mela" in queries and "revaluation" in queries
    # categories anni config lo undali (lekapote WP lo junk category create avutundi)
    unknown = {s[2] for s in grid} - set(config.CATEGORIES)
    assert not unknown, f"grid categories config lo levu: {unknown}"
    # duplicate query ledu (same query 2 sarlu = wasted radar budget)
    qs = [s[1].lower() for s in grid]
    assert len(qs) == len(set(qs)), "duplicate radar query undi"
    daily = [s for s in grid if s[3]]
    assert 30 <= len(daily) <= 45, f"daily hot-list balance tappu: {len(daily)}"
    print(f"      grid 180 sources · {len(daily)} daily · melas/districts/universities ✔")


def test_keyword_universe_expanded() -> None:
    from autoblog import top_post

    top_post._UNIVERSE_CACHE = None
    uni = top_post.keyword_universe()
    assert len(top_post.ENTITIES) == 221, len(top_post.ENTITIES)
    assert len(uni) == 12_344, len(uni)
    kws = " ".join(k["kw"] for k in uni)
    for needle in ("jntuh results", "job mela", "anganwadi", "daily current affairs"):
        assert needle in kws, f"keyword miss: {needle}"
    # entity names lo duplicates undakoodadu (universe lo double counting)
    names = [e[0] for e in top_post.ENTITIES]
    assert len(names) == len(set(names)), "duplicate entity undi"
    # prathi entity ki valid live category
    bad = [e for e in top_post.ENTITIES if e[1] not in top_post.LIVE_CATEGORIES]
    assert not bad, f"unknown category entity: {bad[:3]}"
    print("      universe 221 entities · 12,344 keywords · uni/mela/anganwadi ✔")


def test_counts_locked_in_guardian_and_readiness() -> None:
    from autoblog import guardian, readiness

    ok, detail, _fix = guardian.check_keyword_pillar_lock()
    assert ok, f"guardian counts lock fail: {detail}"
    assert "221 entities" in detail and "180 sources" in detail, detail
    rows = readiness.c_pillars_and_keywords()
    assert rows[0]["ok"], rows[0]
    assert "12,344" in rows[0]["value"], rows[0]["value"]
    print("      guardian + readiness counts lock (17 · 221 · 12,344 · 180) ✔")


# ------------------------------------------------------------------ GAP-2
def test_join_strip_block() -> None:
    """Mid-article WhatsApp/Telegram strip — safe + idempotent + empty-safe."""
    import importlib

    os.environ["TELEGRAM_CHANNEL_URL"] = "https://t.me/studentup_in"
    os.environ["SOCIAL_WHATSAPP"] = "9182739312"
    from autoblog import config, monetize

    importlib.reload(config)
    importlib.reload(monetize)
    try:
        assert monetize.whatsapp_channel_url() == "https://wa.me/919182739312"
        block = monetize.join_strip_block()
        assert "su-join-strip" in block and "wa.me/919182739312" in block
        assert "t.me/studentup_in" in block
        assert 'rel="noopener nofollow"' in block, "rel safety ledu"
        html = ('<section class="su-quick-answer-card"><h2>Q</h2><p>a</p></section>'
                "<h2>Eligibility</h2><p>Degree pass avvali.</p>"
                "<h2>Fee</h2><p>500 rupees.</p>")
        out = monetize.insert_join_strip(html)
        # quick-answer section ni skip chesi CONTENT h2 tarvata padindi
        assert out.index("su-join-strip") > out.index("Degree pass avvali"), \
            "strip quick-answer lo padindi"
        assert out.index("su-join-strip") < out.index("<h2>Fee</h2>"), \
            "strip chala kindaki poyindi"
        # idempotent
        assert monetize.insert_join_strip(out) == out, "idempotent kaadu"
        # sanitizer (publish path) block ni thoseyyakudadu
        from autoblog import validator

        assert "su-join-strip" in validator.sanitize_html(out), "sanitizer strip chesindi"
    finally:
        os.environ["TELEGRAM_CHANNEL_URL"] = ""
        os.environ["SOCIAL_WHATSAPP"] = ""
        importlib.reload(config)
        importlib.reload(monetize)
    # links levakapote — fake buttons raavu
    html2 = "<h2>A</h2><p>x</p>"
    assert monetize.join_strip_block() == ""
    assert monetize.insert_join_strip(html2) == html2, "links levu kaani strip vachindi"
    print("      join strip: position · idempotent · sanitizer-safe · empty-safe ✔")


def test_join_strip_number_parsing() -> None:
    """Owner number junk unna crash avvakudadu (config typo-safe)."""
    import importlib

    from autoblog import config, monetize

    cases = {
        "9182739312": "https://wa.me/919182739312",
        "+91 91827 39312": "https://wa.me/919182739312",
        "https://chat.whatsapp.com/ABC123": "https://chat.whatsapp.com/ABC123",
        "not-a-number": None,
        "": None,
    }
    for raw, want in cases.items():
        os.environ["SOCIAL_WHATSAPP"] = raw
        importlib.reload(config)
        importlib.reload(monetize)
        assert monetize.whatsapp_channel_url() == want, f"{raw!r} → {want!r}"
    os.environ["SOCIAL_WHATSAPP"] = ""
    importlib.reload(config)
    importlib.reload(monetize)
    print("      wa number: 10-digit · +91 spaced · invite link · junk → None ✔")


def test_theme_join_dedupe_guard() -> None:
    """Bot strip unte theme inkoka join box render cheyyakudadu."""
    cta = read(THEME / "inc" / "cta.php")
    m = re.search(r"function studentup_inject_join_cta\(.*?\n\}", cta, re.S)
    assert m, "studentup_inject_join_cta() ledu"
    body = m.group(0)
    assert "su-join-strip" in body, "v96 dedupe guard ledu (duplicate join box vastundi)"
    assert "su-join-inline" in body, "v79 self guard poyindi"
    print("      theme dedupe: bot strip unte inline strip skip ✔")


# ------------------------------------------------------------------ GAP-3
def test_upnext_module_is_policy_safe() -> None:
    """Up Next = real links. Timer/auto-refresh/redirect ABSOLUTELY vaddu."""
    php = read(THEME / "inc" / "upnext.php")
    assert "studentup_upnext_posts" in php and "studentup_upnext_block" in php
    assert "post__not_in" in php, "same post malli suggest avutundi"
    assert "'no_found_rows'      => true" in php or "no_found_rows" in php, \
        "perf: count query off cheyyandi"
    for banned in ("setInterval", "setTimeout", "location.reload",
                   "location.href =", "meta http-equiv=\"refresh\"",
                   "googletag.pubads().refresh"):
        assert banned not in php, f"policy risk: {banned} (AdSense invalid traffic)"
    # option gates (owner OFF cheyyagalaru)
    assert "'upnext'" in php and "'upnext_bar'" in php
    opts = read(THEME / "inc" / "options.php")
    assert "'upnext'" in opts and "'upnext_bar'" in opts, "options lo register avvaledu"
    fn = read(THEME / "functions.php")
    assert "inc/upnext.php" in fn, "upnext.php require avvaledu (dead file)"
    single = read(THEME / "single.php")
    assert "studentup_upnext_block" in single, "single.php lo render avvaledu"
    assert single.index("studentup_upnext_block") < single.index("'below-content'"), \
        "content link ad ki MUNDU undali"
    print("      upnext: real links · no timer/redirect · options + wiring ✔")


def test_upnext_js_and_css() -> None:
    js = read(THEME / "assets" / "js" / "studentup.js")
    assert "su-nextbar" in js, "sticky bar JS ledu"
    tail = js[js.index("data-su-nextbar"):]
    for banned in ("setInterval", "location.reload", "window.open"):
        assert banned not in tail, f"policy risk in JS: {banned}"
    assert "passive: true" in tail, "scroll listener passive undali (INP)"
    assert "sessionStorage" in tail, "dismiss/seen memory ledu"
    css = read(THEME / "style.css")
    for token in (".su-upnext", ".su-nextbar",
                  "body.su-has-stickyad .su-nextbar"):
        assert token in css, f"CSS token ledu: {token}"
    assert ".su-join-strip" in css, "bot join strip ki theme CSS ledu"
    print("      upnext JS (passive · sessionStorage · no timer) + CSS + collision ✔")


# ------------------------------------------------------------------ GAP-4/5
def test_image_filename_and_alt() -> None:
    from autoblog import seo

    name = seo.image_filename("TSPSC Group 2 Notification 2026",
                              "tspsc-group-2-notification", "TS Govt Jobs", 2026)
    assert name.endswith(".webp"), name
    assert name.startswith("tspsc-group-2-notification-2026"), name
    assert "--" not in name and " " not in name
    assert len(name) <= seo.IMAGE_NAME_MAX + 6, name
    # duplicate tokens repeat avvakudadu
    stem = name.rsplit(".", 1)[0].split("-")
    assert len(stem) == len(set(stem)), f"duplicate token: {name}"
    # Telugu-only keyword → ascii fallback (file name khali kaadu)
    te = seo.image_filename("ఉద్యోగ నోటిఫికేషన్", "", "Results", 2026)
    assert te and te.endswith(".webp") and re.match(r"^[a-z0-9-]+\.webp$", te), te
    # extension follows caller
    assert seo.image_filename("ssc cgl", ext="jpg").endswith(".jpg")
    alt = seo.image_alt("SSC CGL 2026", "Central Govt Jobs", 2026)
    assert alt.startswith("SSC CGL 2026") and alt.endswith("| studentup.in")
    print(f"      thumbnail name/alt: {name} ✔")


def test_upload_media_mime_and_filename() -> None:
    """REAL BUG: .webp ni image/jpeg ga upload cheyyadam (WP reject risk)."""
    src = read(ROOT / "autoblog" / "wordpress_client.py")
    assert '"image/jpeg"' in src and "_MIME" in src, "MIME map ledu"
    from autoblog.wordpress_client import WordPressClient

    mime = WordPressClient._MIME
    assert mime[".webp"] == "image/webp" and mime[".png"] == "image/png"
    assert mime[".jpg"] == "image/jpeg"
    # signature lo filename support
    import inspect

    sig = inspect.signature(WordPressClient.upload_media)
    assert "filename" in sig.parameters, "SEO filename param ledu"
    # Content-Disposition kuda kotha name vadali (purana bug: image_path.name)
    body = src[src.index("def upload_media"):src.index("def get_recent_published")]
    assert 'filename=\\"{name}\\"' in body or 'filename="{name}"' in body, \
        "Content-Disposition lo purana name undi"
    pipe = read(ROOT / "autoblog" / "pipeline.py")
    assert "seo.image_filename(" in pipe and "filename=img_name" in pipe, \
        "pipeline lo wire avvaledu"
    assert "seo.image_alt(" in pipe, "alt helper wire avvaledu"
    print("      upload_media: webp→image/webp · SEO filename · pipeline wired ✔")


# ------------------------------------------------------------------ GAP-6
def test_update_flow_keeps_monetize_blocks() -> None:
    """REAL BUG: refresh lo Telegram CTA + join strip delete ayyevi."""
    src = read(ROOT / "autoblog" / "pipeline.py")
    upd = src[src.index("def update_post("):src.index("def create_listicle")]
    assert "append_blocks" in upd, "update path lo monetize blocks ledu (CTA poతundi)"
    assert "ad_manager" in upd, "update path lo owner ads inject avvatledu"
    # QA/gate ki MUNDU run avvali (score nijamaina final HTML meeda)
    assert upd.index("append_blocks") < upd.index("validate_article"), \
        "QA blocks ki mundu run avutundi (score tappu)"
    print("      refresh: monetize + ads inject → QA/gate tarvata ✔")


# ------------------------------------------------------------------ GAP-7
def test_district_hubs_builder() -> None:
    from autoblog import district_hubs as dh

    assert len(dh.districts()) == 59, len(dh.districts())
    assert len(dh.districts("TS")) == 33 and len(dh.districts("AP")) == 26
    posts = [{"title": f"Karimnagar Recruitment {i} 2026",
              "link": f"https://studentup.in/post-{i}", "date": "2026-09-01"}
             for i in range(5)]
    html = dh.build_hub_html("Karimnagar", "TS", posts, year=2026,
                             site="https://studentup.in")
    assert "Karimnagar" in html and "Telangana" in html
    assert html.count("<h2") >= 5, "sections thakkuva (thin page)"
    # page-specific coverage counts (boilerplate kaadu — Google ki unique)
    assert "coverage" in html and "త్వరలో" in html, "coverage block ledu"
    words = len(re.sub(r"<[^>]+>", " ", html).split())
    assert words >= 220, f"hub page thin: {words} words"
    assert "job-melas" in html, "job mela section ledu"
    assert "https://studentup.in/post-0" in html
    # neighbouring district cross-links (cluster) — self link vaddu
    assert "khammam-jobs" in html, "nearby district links levu"
    assert "karimnagar-jobs" not in html, "self-link undi"
    # escaping: junk title HTML ga inject avvakudadu
    evil = [{"title": '<script>x</script>', "link": 'https://a.b/"onx',
             "date": "2026-01-01"}] * 3
    out = dh.build_hub_html("Guntur", "AP", evil)
    assert "<script>" not in out, "XSS: title escape avvaledu"
    # slug/title limits
    slug = dh.hub_slug("Dr B.R. Ambedkar Konaseema")
    assert re.match(r"^[a-z0-9-]+$", slug) and len(slug) <= 60, slug
    long_title = dh.hub_title("Sri Potti Sriramulu Nellore", "AP", 2026)
    assert len(long_title) <= 70, long_title
    print("      district hubs: 59 · sections · cross-links · escaping · limits ✔")


def test_district_hub_coverage_is_data_driven() -> None:
    """Coverage counts posts batti marali — same boilerplate anni pages lo vaddu."""
    from autoblog import district_hubs as dh

    melas = [{"title": f"Guntur job mela {i} 2026", "link": f"https://s.in/{i}",
              "date": "2026-09-01"} for i in range(4)]
    results = [{"title": f"Guntur university results {i} 2026",
                "link": f"https://s.in/{i}", "date": "2026-09-01"} for i in range(4)]
    a = dh.build_hub_html("Guntur", "AP", melas)
    b = dh.build_hub_html("Guntur", "AP", results)
    assert a != b, "coverage block static (page-specific kaadu)"
    assert "Job melas &amp; walk-ins</strong> — ప్రస్తుతం 4" in a, a[:200]
    assert "Results &amp; merit lists</strong> — ప్రస్తుతం 4" in b
    # zero-hit types ni "unnayi" ani fake cheyyakudadu
    assert "Hall tickets &amp; admit cards — త్వరలో" in a
    print("      coverage block: data-driven · no fake claims ✔")


def test_district_hubs_thin_page_guard() -> None:
    """Khali shelves publish avvakudadu (scaled-content / AdSense risk)."""
    from autoblog import district_hubs as dh

    class FakeWP:
        def __init__(self, n):
            self.n = n
            self.pages = []

        def search_posts(self, term, per_page=10):
            return [{"title": f"{term} post {i}", "link": f"https://s.in/{i}",
                     "date": "2026-09-01"} for i in range(self.n)]

        def upsert_page(self, title, html, slug):
            self.pages.append(slug)
            return {"link": f"https://studentup.in/{slug}/"}

    thin = FakeWP(1)
    rows = dh.rebuild("TS", apply=True, wp=thin)
    assert not thin.pages, "thin districts publish ayyayi (guard fail)"
    assert all(not r["publish"] for r in rows)
    assert "thin page guard" in rows[0]["reason"]

    rich = FakeWP(5)
    rows = dh.rebuild("AP", apply=True, wp=rich)
    assert len(rich.pages) == 26, len(rich.pages)
    assert all(r["publish"] and r.get("link") for r in rows)
    # dry-run lo network write ledu
    dry = FakeWP(5)
    dh.rebuild("AP", apply=False, wp=dry)
    assert not dry.pages, "dry-run lo publish ayyindi"
    print("      thin-page guard: 1 post → 0 pages · 5 posts → 26 pages · dry-run safe ✔")


def test_district_hubs_cli_wired() -> None:
    main = read(ROOT / "autoblog" / "main.py")
    for flag in ("--district-hubs", "--district-hubs-apply", "--district-hubs-state"):
        assert flag in main, f"CLI flag ledu: {flag}"
    assert "district_hubs" in main and "run_cli" in main
    docs = read(ROOT / "README.md") + read(ROOT / "MANUAL_ADVANCED_CHECKLIST.md")
    assert "--district-hubs" in docs, "docs lo CLI ledu (owner ki teliyadu)"
    print("      district hubs CLI + docs ✔")


# ------------------------------------------------------------------ meta
def test_theme_version_and_zip() -> None:
    css = re.search(r"Version:\s*([0-9.]+)", read(THEME / "style.css")).group(1)
    php = re.search(r"STUDENTUP_VERSION',\s*'([^']+)'",
                    read(THEME / "functions.php")).group(1)
    stable = re.search(r"Stable tag:\s*([0-9.]+)",
                       read(THEME / "readme.txt")).group(1)
    assert css == php == stable == "1.9.8", f"parity tappu: {css}·{php}·{stable}"
    assert "= 1.9.7" in read(THEME / "readme.txt"), "changelog entry ledu"
    zpath = ROOT / "wordpress-theme" / "studentup-theme.zip"
    with zipfile.ZipFile(zpath) as z:
        names = z.namelist()
        assert "studentup/inc/upnext.php" in names, "zip lo upnext.php ledu"
        style = z.read("studentup/style.css").decode("utf-8")
    assert "Version: 1.9.8" in style, "zip stale (build_wp_theme.py run cheyandi)"
    assert ".su-upnext" in style and ".su-join-strip" in style
    print(f"      theme 1.9.8 · zip {len(names)} files · upnext + CSS inside ✔")


def test_suite_pins_and_docs() -> None:
    n = len(list((ROOT / "tests").glob("*_test.py")))
    assert n == SUITES_EXPECTED, f"suites {n} != {SUITES_EXPECTED}"
    for f in sorted((ROOT / "tests").glob("v*_test.py")):
        m = re.search(r"SUITES_EXPECTED\s*=\s*(\d+)", read(f))
        if m:
            assert int(m.group(1)) == SUITES_EXPECTED, f"{f.name} pin {m.group(1)} stale"
    readme = read(ROOT / "README.md")
    manual = read(ROOT / "MANUAL_ADVANCED_CHECKLIST.md")
    assert "v96" in readme, "README lo v96 ledu"
    assert "PART 53" in manual, "MANUAL lo PART 53 ledu"
    assert f"{SUITES_EXPECTED}/{SUITES_EXPECTED}" in readme, "README suites count stale"
    assert f"{SUITES_EXPECTED}/{SUITES_EXPECTED}" in manual, "MANUAL suites count stale"
    print(f"      suites {SUITES_EXPECTED} · README v96 · MANUAL PART 53 ✔")


TESTS = [
    ("sources grid 180 (melas · districts · universities)", test_source_grid_expanded),
    ("keyword universe 221 · 12,344", test_keyword_universe_expanded),
    ("counts locked (guardian + readiness)", test_counts_locked_in_guardian_and_readiness),
    ("mid-article join strip", test_join_strip_block),
    ("wa number parsing (junk-safe)", test_join_strip_number_parsing),
    ("theme join dedupe guard", test_theme_join_dedupe_guard),
    ("upnext policy-safe (no timer/refresh)", test_upnext_module_is_policy_safe),
    ("upnext JS + CSS + sticky collision", test_upnext_js_and_css),
    ("thumbnail file name + alt", test_image_filename_and_alt),
    ("upload_media MIME bug fix", test_upload_media_mime_and_filename),
    ("refresh keeps monetize blocks (bug fix)", test_update_flow_keeps_monetize_blocks),
    ("district hub builder", test_district_hubs_builder),
    ("district hub coverage data-driven", test_district_hub_coverage_is_data_driven),
    ("district hub thin-page guard", test_district_hubs_thin_page_guard),
    ("district hubs CLI + docs", test_district_hubs_cli_wired),
    ("theme 1.9.7 + zip", test_theme_version_and_zip),
    ("suite pins + docs", test_suite_pins_and_docs),
]


def main() -> None:
    os.chdir(ROOT)
    print("=" * 70)
    print("v96 COVERAGE + SESSION DEPTH + REAL BUG FIXES (theme 1.9.7)")
    print("=" * 70)
    failed = 0
    for name, fn in TESTS:
        try:
            fn()
            print(f"  {name} ✔")
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
    print("ALL v96 COVERAGE + SESSION-DEPTH TESTS PASSED ✔")


if __name__ == "__main__":
    main()
