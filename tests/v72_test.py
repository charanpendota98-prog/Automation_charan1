# -*- coding: utf-8 -*-
"""v72 tests — QUALIFICATION FILTER · HEADER SEARCH · PWA INSTALL · CLEAN COPY.

Mee requirement (v72):
  * బ్రేకింగ్ న్యూస్ అవసరం లేదు — teeseyandi (public site clean)
  * internal metrics / "నమూనా" / demo maatalu public ga vaddu
  * విద్యార్హత ప్రకారం ఉద్యోగాలు automatic ga filter avvali (10th · 10+2 · డిగ్రీ · పీజీ …)
    — WordPress lo kuda, manual tagging lekunda
  * menu pakkana search + app-laga install (PWA) + mobile lo neat premium look

Ee suite ee pani ni lock chestundi (preview + theme + bot + docs).

Run: python tests/v72_test.py   (also via python run.py --test-all)
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

THEME = ROOT / "wordpress-theme" / "studentup"
PREVIEW = ROOT / "preview"


def read(p) -> str:
    return Path(p).read_text(encoding="utf-8")


# ---------------------------------------------------------------- 1. clean copy
def test_breaking_removed_from_public():
    html = read(PREVIEW / "index.html")
    for needle in ('id="tickerwrap"', 'id="brklist"', 'id="breaking"', "navbrk", "బ్రేకింగ్"):
        assert needle not in html, f"preview/index.html lo '{needle}' inka undi (v72: teeseyali)"
    header = read(THEME / "header.php")
    assert "#breaking" not in header and "navbrk" not in header, "theme header lo breaking link undi"
    fb = read(THEME / "inc" / "template.php")
    assert "#breaking" not in fb, "theme menu fallback lo breaking link undi"


def test_breaking_backend_still_available_opt_in():
    opts = read(THEME / "inc" / "options.php")
    m = re.search(r"'breaking_enabled' => array\([^,]+, 'check', '(\d)'", opts)
    assert m and m.group(1) == "0", "breaking_enabled default OFF kaadu"
    breaking = read(THEME / "inc" / "breaking.php")
    assert "studentup_breaking_enabled()" in breaking and breaking.count(
        "! studentup_breaking_enabled()") >= 2, "ticker/section gate ledu"
    from autoblog import breaking as brk  # noqa: PLC0415
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "breaking.json"
        res = brk.write_feed([], path=out)
        assert res["count"] == 0 and "బ్రేకింగ్" in json.loads(out.read_text(encoding="utf-8"))["note"]


def test_no_internal_metrics_or_sample_text_public():
    html = read(PREVIEW / "index.html")
    for needle in ("11,192", "143 మూలాల", "59 జిల్లాల", "రాడార్", "కీవర్డ్లు",
                   "జిల్లాల పర్యవేక్షణ", "నమూనా", "DEMO", "hero-proof"):
        assert needle not in html, f"public homepage lo '{needle}' undi (v72: andariki chudakoodadu)"
    for page in (PREVIEW / "pages").glob("*.html"):
        text = read(page)
        assert "నమూనా" not in text, f"{page.name} lo 'నమూనా' undi"
        assert "DEMO" not in text, f"{page.name} lo 'DEMO' undi"


# ---------------------------------------------------------------- 2. search
def test_header_search_preview():
    html = read(PREVIEW / "index.html")
    for needle in ('id="searchbtn"', 'id="searchpanel"', 'id="qtop"', 'id="searchgo"',
                   'id="searchclose"', 'id="msearch"'):
        assert needle in html, f"preview lo {needle} ledu"
    assert 'aria-controls="searchpanel"' in html, "search button aria-controls ledu"
    assert 'e.key==="/"' in html, "keyboard '/' shortcut ledu"
    assert "applyFilter(); open(false);" in html, "search panel grid filter ni drive cheyyadu"


def test_header_search_theme():
    header = read(THEME / "header.php")
    for needle in ('id="searchbtn"', 'id="searchpanel"', 'id="qtop"', 'name="s"'):
        assert needle in header, f"theme header lo {needle} ledu"
    js = read(THEME / "assets" / "js" / "studentup.js")
    assert "searchOpen" in js and "searchbtn" in js, "theme search JS ledu"


# ---------------------------------------------------------------- 3. qualification filter
def test_qualification_filter_preview():
    html = read(PREVIEW / "index.html")
    slugs = re.findall(r'data-qual="([a-z0-9]+)"', html)
    assert slugs[:9] == ["all", "10th", "inter", "iti", "diploma", "degree", "pg", "btech",
                         "closing"], f"chips order tappu: {slugs[:9]}"
    cards = re.findall(r'<article class="news"[^>]*>', html)
    assert cards, "job cards dorakaledu"
    missing = [c[:60] for c in cards if "data-qual=" not in c]
    assert not missing, f"data-qual lekunda cards: {missing}"
    assert "data-qual=\"all\"" in html and 'id="qcount"' in html
    assert "activeQual" in html and "okQual" in html, "applyFilter lo qualification logic ledu"
    assert "expired" in html and "qbadge" in html, "closing/expired logic ledu"


def test_qualification_filter_theme():
    q = read(THEME / "inc" / "qual-filter.php")
    for fn in ("studentup_qual_terms", "studentup_qual_keywords", "studentup_detect_qual",
               "studentup_qual_assign", "studentup_qual_bar", "studentup_qual_pre_get_posts",
               "studentup_qual_count", "studentup_qual_backfill", "studentup_qual_chip",
               "studentup_last_date_badge", "studentup_register_qual_meta"):
        assert f"function {fn}" in q, f"qual-filter.php lo {fn}() ledu"
    assert "add_action( 'save_post'" in q, "save_post auto-tag hook ledu"
    assert "add_action( 'pre_get_posts'" in q, "server-side filter hook ledu"
    assert "WP_CLI" in q, "WP-CLI backfill ledu"
    assert "register_post_meta" in q and "studentup_qual" in q
    fn = read(THEME / "functions.php")
    assert "inc/qual-filter.php" in fn, "functions.php lo qual-filter require ledu"
    assert "studentup_qual_query_args" in q and "studentup_qual_active_note" in q, \
        "custom WP_Query ki filter args helper ledu (front-page bypass avutundi)"
    fp = read(THEME / "front-page.php")
    assert "studentup_qual_bar()" in fp, "front-page lo filter bar ledu"
    assert "studentup_qual_query_args(" in fp, "front-page custom query ki filter apply avvatledu"
    assert "studentup_qual_active_note()" in fp, "filter active note ledu"


def test_qual_slug_and_keyword_parity_bot_vs_theme():
    from autoblog import qual as q  # noqa: PLC0415
    php = read(THEME / "inc" / "qual-filter.php")
    php_slugs = re.findall(r"'(\w+)'\s*=>\s*'[^']*',\n", php.split("function studentup_qual_terms")[1]
                           .split("}", 1)[0], re.S)
    assert list(q.QUALS.keys()) == [s for s in php_slugs if s in q.QUALS], \
        f"slug parity tappu: bot={list(q.QUALS)} php={php_slugs}"
    kws_php = php.split("function studentup_qual_keywords")[1].split("}", 1)[0]
    for slug, words in q.KEYWORDS.items():
        assert words[0] in kws_php, f"theme lo '{slug}' keyword '{words[0]}' ledu (parity)"


def test_qual_detection_python():
    from autoblog import qual as q  # noqa: PLC0415
    assert q.detect("10వ తరగతి పాస్ ఉద్యోగాలు") == ["10th"]
    assert "degree" in q.detect("Any degree candidates eligible; B.Com preferred")
    assert "pg" in q.detect("MBA / PG graduates ki preference")
    assert "btech" in q.detect("B.Tech / BE freshers walk-in")
    assert q.detect("ఉద్యోగం లేదు") == []
    art = {"title": "TSPSC Group 2 notification — any degree",
           "recruitment": {"apply_end": "2026-10-15",
                           "eligibility": "Degree + PG eligible"}}
    meta = q.post_meta(art)
    assert meta["studentup_qual"] == "degree pg" and meta["studentup_last_date"] == "2026-10-15"
    assert q.post_meta({"title": "వేరే వార్త"}) == {}, "unauthored meta pampakoodadu"
    assert q.last_date({"title": "x", "recruitment": {"apply_end": "not-a-date"}}) == "", \
        "date guess cheyyakoodadu"


def test_pipeline_qual_wiring():
    pl = read(ROOT / "autoblog" / "pipeline.py")
    assert "post_gate, qual, research" in pl or "import (config" in pl and " qual," in pl, \
        "pipeline lo qual import ledu"
    assert "qual.post_meta(article)" in pl, "pipeline meta lo qual tag add avvatledu"
    assert "studentup_qual" in pl, "meta verify lo studentup_qual ledu"


# ---------------------------------------------------------------- 4. PWA install
def test_pwa_preview():
    man = json.loads(read(PREVIEW / "manifest.webmanifest"))
    assert man["display"] == "standalone" and man["shortcuts"], "manifest incomplete"
    sw = read(PREVIEW / "sw.js")
    assert "addEventListener(\"fetch\"" in sw and "OFFLINE" in sw, "sw.js cache/offline logic ledu"
    html = read(PREVIEW / "index.html")
    for needle in ('rel="manifest"', 'rel="apple-touch-icon"', 'id="installbtn"',
                   "beforeinstallprompt", "serviceWorker.register"):
        assert needle in html, f"preview PWA lo {needle} ledu"
    assert 'name="theme-color"' in html


def test_pwa_theme():
    pwa = read(THEME / "inc" / "pwa.php")
    assert "studentup_sw_js" in pwa and "Service-Worker-Allowed" in pwa
    assert "studentup_sw" in pwa and "application/javascript" in pwa
    assert "studentup-pwa" in pwa and "wp_localize_script" in pwa
    fn = read(THEME / "functions.php")
    assert "assets/js/studentup-pwa.js" in fn, "functions.php lo pwa JS enqueue ledu"
    footer = read(THEME / "footer.php")
    assert 'id="installbtn"' in footer and 'id="installhint"' in footer
    js = read(THEME / "assets" / "js" / "studentup-pwa.js")
    assert "beforeinstallprompt" in js and "appinstalled" in js and "Add to Home Screen" in js


def test_mobile_icon_sizes_neat():
    small = re.compile(r"\.su-social a\{[^}]*34px[^}]*34px")
    css = read(THEME / "style.css")
    prev = read(PREVIEW / "index.html")
    assert small.search(css), "theme mobile icons chinna kaavu"
    assert small.search(prev), "preview mobile icons chinna kaavu"
    assert "@media(max-width:400px)" in css or "31px" in css, "chala chinna screen rule ledu"


# ---------------------------------------------------------------- 5. theme release hygiene
def test_theme_version_parity_v72():
    css = re.search(r"^Version:\s*(\S+)", read(THEME / "style.css"), re.M).group(1)
    php = re.search(r"STUDENTUP_VERSION',\s*'([^']+)'", read(THEME / "functions.php")).group(1)
    stable = re.search(r"^Stable tag:\s*(\S+)", read(THEME / "readme.txt"), re.M).group(1)
    assert css == php == stable == "1.7.2", f"version parity tappu: {css} · {php} · {stable}"
    assert "= 1.7.2" in read(THEME / "readme.txt")
    assert "v72" in read(THEME / "README-THEME.md")


def test_theme_zip_fresh_and_complete():
    zip_path = ROOT / "wordpress-theme" / "studentup-theme.zip"
    assert zip_path.exists(), "theme zip ledu (python tools/build_wp_theme.py)"
    with zipfile.ZipFile(zip_path) as z:
        names = z.namelist()
    assert any("inc/qual-filter.php" in n for n in names), "zip lo qual-filter.php ledu"
    assert any("studentup-pwa.js" in n for n in names), "zip lo studentup-pwa.js ledu"
    newest = max(p.stat().st_mtime for p in THEME.rglob("*") if p.is_file()
                 and "__pycache__" not in str(p))
    assert zip_path.stat().st_mtime >= newest - 5, "zip stale — malli build cheyandi"


def test_php_lint_clean():
    proc = subprocess.run(["node", str(ROOT / "tools" / "php_lint.js")],
                          capture_output=True, text=True, timeout=180, cwd=str(ROOT))
    assert proc.returncode == 0, f"php-lint fail: {proc.stdout[-200:]}"
    assert "files OK" in proc.stdout


def test_theme_audit_deep_clean():
    import theme_audit  # noqa: PLC0415
    rep = theme_audit.run()
    assert not rep["errors"], f"theme audit errors: {rep['errors'][:3]}"


# ---------------------------------------------------------------- 6. docs + counts
def test_counts_and_docs_v72():
    jsdom = read(ROOT / "tests" / "runtime" / "jsdom_runtime_test.js")
    n = int(re.search(r"EXPECTED_CHECKS\s*=\s*(\d+)", jsdom).group(1))
    suites = len(list((ROOT / "tests").glob("*_test.py")))
    readme = read(ROOT / "README.md")
    manual = read(ROOT / "MANUAL_ADVANCED_CHECKLIST.md")
    go_live = read(ROOT / "GO_LIVE_CHECKLIST.md")
    for name, txt in (("README", readme), ("MANUAL", manual), ("GO_LIVE", go_live)):
        assert f"{n}/{n}" in txt, f"{name} lo '{n}/{n}' jsdom claim ledu"
        assert f"{suites}/{suites}" in txt, f"{name} lo '{suites}/{suites}' suites claim ledu"
    assert "v72" in readme and "QUALIFICATION" in readme.upper()
    assert "విద్యార్హత" in readme or "qualification" in readme.lower()
    assert "v72" in manual and "v72" in read(ROOT / "CONTENT_PLAN_DAILY.md")


def test_options_v72_fields():
    opts = read(THEME / "inc" / "options.php")
    for key in ("'qual_filter'", "'install_prompt'", "'breaking_enabled'"):
        assert key in opts, f"options lo {key} ledu"


def test_preview_writes_clean_js():
    html = read(PREVIEW / "index.html")
    scripts = re.findall(r"<script>(.*?)</script>", html, re.S)
    assert scripts, "inline JS ledu"
    for i, code in enumerate(scripts):
        with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False,
                                         encoding="utf-8") as fh:
            fh.write(code)
            tmp = fh.name
        proc = subprocess.run(["node", "--check", tmp], capture_output=True, text=True, timeout=60)
        Path(tmp).unlink(missing_ok=True)
        assert proc.returncode == 0, f"inline script {i} syntax error: {proc.stderr[:160]}"
    for js in (THEME / "assets" / "js").glob("*.js"):
        proc = subprocess.run(["node", "--check", str(js)], capture_output=True, text=True, timeout=60)
        assert proc.returncode == 0, f"{js.name} syntax error: {proc.stderr[:160]}"



# ---------------------------------------------------------------- v72.1 (follow-up pass)
def test_topbar_and_coverage_lines_gone():
    html = read(PREVIEW / "index.html")
    assert 'class="topbar"' not in html, "topbar (coverage line) inka undi"
    assert ".topbar{" not in html and ".toplinks{" not in html, "topbar CSS migilindi"
    for phrase in ("(33 జిల్లాలు", "(26 జిల్లాలు", "జిల్లాల పర్యవేక్షణ", "ప్రతిరోజూ ధృవీకృత"):
        assert phrase not in html, f"'{phrase}' public HTML lo inka undi"


def test_demo_article_removed():
    html = read(PREVIEW / "index.html")
    for needle in ("7 విషయాలు", "QUICK ANSWER", "ఎడిటర్ ఎంపిక", 'id="wa"', 'id="copylink"'):
        assert needle not in html, f"demo article element '{needle}' inka undi"
    assert 'class="article"' not in html, "article block migilindi"


def test_ads_are_house_creatives_not_fake_advertisers():
    html = read(PREVIEW / "index.html")
    for needle in ("example.com", "ABC IAS", "ABC ఇంజినీరింగ్", "abc-college-demo",
                   "tuition-demo", "stationery-demo"):
        assert needle not in html, f"demo advertiser '{needle}' inka undi"
    assert html.count("SPONSORED") >= 4, "SPONSORED labels poyayi (AdSense rule)"
    assert "pages/advertise.html" in html, "ad slot CTA Partner page ki vellatledu"


def test_countdown_is_data_driven():
    """v73: hero countdown card poyindi — kabatti data plumbing kuda undakoodadu.

    Mundu (v72.1): hardcoded date → preview/data/deadline.json + theme option.
    Ippudu (v73, user brief): hero block + countdown motham teesesaamu, so bot
    writer/option/JS anni teesesaayi — page lo honest line mattrame.
    """
    html = read(PREVIEW / "index.html")
    assert "new Date(2026,9,15" not in html, "hardcoded sample countdown inka undi"
    for gone in ('id="cd-none"', 'id="cd-box"', "data-deadline", 'fetch("data/deadline.json',
                 'class="timer"', 'class="hcard-row"'):
        assert gone not in html, gone + " — v73 lo hero countdown teeseyali"
    assert "hero-slim" in html and "official notification" in html, "honest hero line ledu"
    theme_js = read(THEME / "assets" / "js" / "studentup.js")
    theme_fp = read(THEME / "front-page.php")
    assert "data-deadline" not in theme_js and "data-cd=" not in theme_js + theme_fp
    # bot + preview plumbing teesesaamu (dead code ledu)
    assert "write_preview_deadline" not in read(ROOT / "autoblog" / "wp_theme_sync.py")
    assert not (ROOT / "preview" / "data" / "deadline.json").exists()


def test_app_download_is_always_visible():
    html = read(PREVIEW / "index.html")
    m = re.search(r'<button[^>]*id="installbtn"[^>]*>', html)
    assert m and "hidden" not in m.group(0), "download button inka hidden"
    # v73: English UI copy
    assert "⬇️ Download App" in html and 'class="ibadge"' in html
    assert 'id="installhint"' in html and html.count('id="isteps"') == 1
    assert "openSheet" in html and "beforeinstallprompt" in html
    theme_footer = read(THEME / "footer.php")
    assert 'id="installbtn"' in theme_footer and 'id="installhint"' in theme_footer
    assert 'id="installbtn">⬇️ Download App' in theme_footer, "theme button wording v73 kaadu"
    pwa_js = read(THEME / "assets" / "js" / "studentup-pwa.js")
    assert "openSheet" in pwa_js and "beforeinstallprompt" in pwa_js


def test_qualification_directory_automatic():
    html = read(PREVIEW / "index.html")
    assert 'id="qsplit"' in html and html.count('class="qgroup"') == 8
    assert "buildQualSections" in html, "preview lo auto grouping JS ledu"
    js = read(THEME / "assets" / "js" / "studentup.js")
    assert "buildQualSections" in js, "theme lo auto grouping JS ledu"
    q = read(THEME / "inc" / "qual-filter.php")
    assert "studentup_qual_directory" in q and "add_action( 'wp_footer'" in q
    assert "studentup_hidden_note" in q and "wp_dashboard_setup" in q
    card = read(THEME / "inc" / "template.php")
    assert "data-last=" in card, "theme card lo data-last ledu (closing filter kaadu)"


def test_theme_version_1721():
    css = re.search(r"^Version:\s*(\S+)", read(THEME / "style.css"), re.M).group(1)
    php = re.search(r"STUDENTUP_VERSION',\s*'([^']+)'", read(THEME / "functions.php")).group(1)
    stable = re.search(r"^Stable tag:\s*(\S+)", read(THEME / "readme.txt"), re.M).group(1)
    assert css == php == stable == "1.7.2", f"version parity tappu: {css} · {php} · {stable}"
    assert "= 1.7.2" in read(THEME / "readme.txt")

TESTS = [
    ("బ్రేకింగ్ న్యూస్ public site nunchi poyindi", test_breaking_removed_from_public),
    ("బ్రేకింగ్ backend opt-in (default OFF) ga migilindi", test_breaking_backend_still_available_opt_in),
    ("internal metrics + 'నమూనా/DEMO' public lo levu", test_no_internal_metrics_or_sample_text_public),
    ("menu pakkana search (preview)", test_header_search_preview),
    ("menu pakkana search (WordPress theme)", test_header_search_theme),
    ("విద్యార్హత ఫిల్టర్ chips + cards + logic (preview)", test_qualification_filter_preview),
    ("విద్యార్హత ఫిల్టర్ module (theme · auto-tag · CLI)", test_qualification_filter_theme),
    ("bot ↔ theme slug/keyword parity", test_qual_slug_and_keyword_parity_bot_vs_theme),
    ("qualification detect + last date (bot)", test_qual_detection_python),
    ("pipeline lo qual meta wiring", test_pipeline_qual_wiring),
    ("యాప్గా ఇన్స్టాల్ (preview PWA)", test_pwa_preview),
    ("యాప్గా ఇన్స్టాల్ (theme PWA + install prompt)", test_pwa_theme),
    ("mobile icons chinna ga (neat)", test_mobile_icon_sizes_neat),
    ("theme version parity 1.7.2", test_theme_version_parity_v72),
    ("theme zip fresh + v72 files", test_theme_zip_fresh_and_complete),
    ("php-lint clean (real PHP 8 grammar)", test_php_lint_clean),
    ("theme deep audit 0 errors", test_theme_audit_deep_clean),
    ("docs counts + v72 sections", test_counts_and_docs_v72),
    ("options lo v72 fields", test_options_v72_fields),
    ("preview + theme JS syntax clean", test_preview_writes_clean_js),
    ("v72.1: topbar/coverage lines poyayi", test_topbar_and_coverage_lines_gone),
    ("v72.1: demo 7-point article poyindi", test_demo_article_removed),
    ("v72.1: fake advertiser creatives → house partner slots", test_ads_are_house_creatives_not_fake_advertisers),
    ("v73: fake countdown + deadline plumbing ledu", test_countdown_is_data_driven),
    ("v72.1: Download App button prathi visit lo (English copy)", test_app_download_is_always_visible),
    ("v72.1: అర్హత ప్రకారం విభాగాలు automatic (preview + theme)", test_qualification_directory_automatic),
    ("v74: theme version 1.7.2 parity", test_theme_version_1721),
]


def main() -> int:
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
        return 1
    print(f"ALL v72 TESTS PASSED ✔  ({len(TESTS)} checks)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
