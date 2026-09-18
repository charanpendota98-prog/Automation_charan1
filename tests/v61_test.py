# -*- coding: utf-8 -*-
"""v61 tests — REAL WEBSITE: StudentUp WordPress theme (design = preview design).

Enduku idi:
  Mee prashna: "real website ela untundi — WordPress lo leda customized website?"
  Answer: **WordPress + mana custom theme (idi)**. preview/index.html design ne
  WordPress theme ga (ticker · most-used · cards · ad slots · dark mode), kaani
  dynamic — bot post rasthe site automatic ga update avutundi.

Checks (offline only):
  * theme files anni unnayi + style.css header valid + design tokens
  * ABSPATH guard every PHP file + escape cheyyani echo ledu (XSS)
  * functions.php: menus (primary/mobile/footer) · no jQuery · localize · most_used order
  * most_used slugs+labels = preview site + bot order (okate source)
  * front-page order: used → ad → hero → breaking → grid (+ chips, countdown)
  * ads.php: SPONSORED label · rel sponsored nofollow · adsense client regex · day rotation
  * breaking.php: option → transient → file · honest empty · REST endpoint
  * single.php: ads + share + trust note + related
  * JS: no lib · dark mode · mobile panel · chips filter · countdown
  * packager: validate + zip root structure + theme.json palette
  * bot bridge: wp_theme_sync payload + CLI wiring + daily hook
  * docs: MANUAL PART 20 + README-THEME.md + GO_LIVE

Run: python tests/v61_test.py   (also via python run.py --test-all)
"""
from __future__ import annotations

import io
import json
import re
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from autoblog import config, wp_theme_sync  # noqa: E402

SRC = ROOT / "wordpress-theme" / "studentup"
ZIP = ROOT / "wordpress-theme" / "studentup-theme.zip"
PY = sys.executable


def read(rel: str) -> str:
    return (SRC / rel).read_text(encoding="utf-8")


def test_theme_files_exist():
    need = ["style.css", "index.php", "functions.php", "header.php", "footer.php",
            "front-page.php", "single.php", "page.php", "archive.php", "search.php",
            "404.php", "searchform.php", "theme.json", "README-THEME.md",
            "inc/breaking.php", "inc/ads.php", "inc/template.php",
            "assets/js/studentup.js"]
    missing = [n for n in need if not (SRC / n).exists()]
    assert not missing, missing


def test_style_header_and_tokens():
    css = read("style.css")
    for field in ("Theme Name: StudentUp", "Text Domain: studentup", "License:"):
        assert field in css, field
    # v69: version ni **constant nunchi** verify (hardcode vaddu — bump aithe test break avvakoodadu)
    php_ver = re.search(r"STUDENTUP_VERSION',\s*'([^']+)'",
                        (SRC / "functions.php").read_text(encoding="utf-8")).group(1)
    css_ver = re.search(r"^Version:\s*(\S+)", css, re.M).group(1)
    assert css_ver == php_ver, f"style.css {css_ver} ≠ STUDENTUP_VERSION {php_ver}"
    for token in ("--navy:#0f2e62", "--orange:#ed8a32", ".tickerwrap", ".usedgrid",
                  ".newsgrid", ".su-ad", ".breaking", "body.dark", "@media(max-width:600px)"):
        assert token in css, token


def test_php_guards_and_escaping():
    for php in SRC.rglob("*.php"):
        text = php.read_text(encoding="utf-8")
        rel = php.relative_to(SRC).as_posix()
        assert "ABSPATH" in text, f"{rel}: ABSPATH guard ledu"
        assert not re.search(r"<\?php\s+echo\s+\$", text), f"{rel}: escape cheyyani echo $"
    # prathi dynamic output ki escape function undali
    fp = read("front-page.php")
    for fn in ("esc_html", "esc_url", "esc_attr"):
        assert fn in fp, fn


def test_functions_setup():
    f = read("functions.php")
    assert "load_theme_textdomain" in f and "add_theme_support( 'title-tag' )" in f
    assert "'primary'" in f and "'mobile'" in f and "'footer'" in f
    assert "wp_enqueue_style" in f and "wp_enqueue_script" in f
    assert "wp_localize_script" in f
    assert "array(), STUDENTUP_VERSION, true" in f, "script deps khali — library vaddu"
    assert "wp_enqueue_script( 'jquery'" not in f, "jackpot: jquery enlist cheyyakudadu"


def test_most_used_order_matches_site():
    f = read("functions.php")
    slugs = re.findall(r"'slug' => '([a-z-]+)', 'label' => '([^']+)'", f)
    assert len(slugs) == 8, slugs
    assert [s for s, _ in slugs] == ["ts-jobs", "ap-jobs", "hall-tickets", "results",
                                     "walkin-jobs", "software-jobs", "private-jobs",
                                     "current-affairs"], slugs
    labels = [l for _, l in slugs]
    assert labels[0].startswith("టీఎస్") and labels[1].startswith("ఏపీ")
    assert "హాల్ టికెట్లు" in labels and "ఫలితాలు" in labels and "వాక్-ఇన్" in labels[4]
    # bot MOST_USED order same (breaking.py)
    from autoblog import breaking

    assert [m["label"] for m in breaking.most_used()][:2] == labels[:2], "site/bot order desync"
    assert breaking.most_used_cats()[:2] == ["ts-jobs", "ap-jobs"]


def test_front_page_order():
    fp = read("front-page.php")
    order = [fp.index("studentup_most_used()"), fp.index("studentup_ad( 'leaderboard' )"),
             fp.index('class="hero"'), fp.index("studentup_breaking_section()"),
             fp.index('id="grid"')]
    assert order == sorted(order), order
    for needle in ('id="chips"', 'data-cat="all"', "data-deadline", "studentup_ad( 'mid' )",
                   "studentup_card(", "next_posts_link"):
        assert needle in fp, needle
    assert "విద్యార్థులు ఎక్కువగా వెతికేవి" in fp
    hdr = read("header.php")
    assert "studentup_breaking_ticker()" in hdr
    assert hdr.index("studentup_breaking_ticker()") < hdr.index('<div class="mpanel"')


def test_ads_safety():
    ads = read("inc/ads.php")
    assert "SPONSORED" in ads
    assert 'rel="sponsored nofollow noopener"' in ads
    assert re.search(r"\^ca-pub-\\d\{10,20\}\$", ads), "adsense client regex"
    assert "studentup_rotate_house" in ads and "gmdate( 'z' ) % $n" in ads, "day rotation"
    assert "esc_url(" in ads and "esc_html(" in ads and "esc_attr(" in ads
    assert "adsbygoogle" in ads


def test_breaking_feed_contract():
    b = read("inc/breaking.php")
    assert "studentup_breaking_json" in b and "get_transient( 'studentup_breaking_feed' )" in b
    assert "/data/breaking.json" in b, "file fallback (bot radar rasi file)"
    assert "ప్రస్తుతం కొత్త verified బ్రేకింగ్ అప్డేట్‌లు లేవు" in b, "honest empty message"
    assert "sanitize_key" in b and "esc_url_raw" in b and "wp_strip_all_tags" in b
    assert "studentup/v1" in b and "edit_posts" in b, "REST push endpoint + auth"
    assert "studentup_tag_label" in b and "studentup_ago" in b


def test_single_and_templates():
    s = read("single.php")
    for needle in ("the_content()", "studentup_ad( 'mid' )", "studentup_trust_note()",
                   "studentup_reading_time()", "షేర్", "studentup_breadcrumbs()", "related"):
        assert needle in s, needle
    foot = read("footer.php")
    assert "su-social" in foot and "wp_footer()" in foot and "Telegram" in foot
    page = read("page.php")
    assert "the_content()" in page and "studentup_trust_note()" in page


def test_js_no_lib_and_features():
    js = read("assets/js/studentup.js")
    assert not re.search(r"\bjQuery\s*\(|\$\(document", js), "library use vaddu"
    for feat in ("su_theme", "mpanel", 'getElementById("grid")',
                 "data-deadline", "data-cat", "addEventListener"):
        assert feat in js, feat


def test_theme_json_palette():
    data = json.loads(read("theme.json"))
    slugs = [c["slug"] for c in data["settings"]["color"]["palette"]]
    for want in ("navy", "blue", "orange"):
        assert want in slugs, slugs
    assert data["settings"]["layout"]["wideSize"] == "1180px"


def test_packager_builds_zip():
    out = subprocess.run([PY, str(ROOT / "tools" / "build_wp_theme.py")],
                         capture_output=True, text=True, cwd=str(ROOT))
    assert out.returncode == 0, out.stdout[-400:] + out.stderr[-200:]
    assert "ANNI OK" in out.stdout
    assert ZIP.exists(), "zip create avvali"
    with zipfile.ZipFile(ZIP) as zf:
        names = zf.namelist()
        for want in ("studentup/style.css", "studentup/front-page.php",
                     "studentup/inc/breaking.php", "studentup/assets/js/studentup.js"):
            assert want in names, want
        assert all(n.startswith("studentup/") for n in names), "zip root okkate folder undali"
        css = zf.read("studentup/style.css").decode("utf-8")
        assert "Theme Name: StudentUp" in css


def test_bot_bridge_payload_and_cli():
    payload = wp_theme_sync.build_payload()
    assert "proof" in payload
    assert payload["proof"]["keywords"] == 11_192 and payload["proof"]["sources"] == 143
    assert payload["proof"]["categories"] == len(config.CATEGORIES)
    assert "house_ads" in payload and isinstance(payload["house_ads"], list)
    assert "breaking" in payload and isinstance(payload["breaking"], list)
    res = wp_theme_sync.push(payload, dry_run=True)
    assert res["ok"] and res["dry_run"] and IS_SENT(res)
    main = (ROOT / "autoblog" / "main.py").read_text(encoding="utf-8")
    assert "def push_theme_data(" in main and '"--push-theme-data"' in main
    assert "wp_theme_sync.push()" in main, "daily hook (breaking feed tarvata theme sync)"
    assert "/wp-json/studentup/v1/theme-data" in wp_theme_sync.REST_PATH
    env = (ROOT / ".env.example").read_text(encoding="utf-8")
    assert "POST_DEADLINE_TITLE" in env and "POST_DEADLINE_ISO" in env


def IS_SENT(res: dict) -> bool:
    return all(k in res.get("sent", {}) for k in ("proof", "house_ads", "breaking"))


def test_docs_v61():
    manual = (ROOT / "MANUAL_ADVANCED_CHECKLIST.md").read_text(encoding="utf-8")
    assert "PART 20" in manual and "StudentUp theme" in manual
    theme_readme = read("README-THEME.md")
    assert "Appearance → Themes" in theme_readme and "studentup_site" not in theme_readme
    assert "theme-data" in theme_readme, "REST push document avvali"
    go = (ROOT / "GO_LIVE_CHECKLIST.md").read_text(encoding="utf-8")
    assert "wordpress-theme" in go.lower() or "StudentUp theme" in go, "A0 lo theme install"
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "--push-theme-data" in readme and "studentup-theme.zip" in readme


def main():
    print("=" * 66)
    print("  v61 — REAL WEBSITE: WordPress + StudentUp theme (preview design = live design)")
    print("=" * 66)
    tests = [
        ("theme files anni unnayi", test_theme_files_exist),
        ("style.css header + design tokens", test_style_header_and_tokens),
        ("ABSPATH guard + escaping (XSS safe)", test_php_guards_and_escaping),
        ("functions: menus · no jQuery · localize", test_functions_setup),
        ("most-used order: theme = site = bot", test_most_used_order_matches_site),
        ("front-page order: used → ad → hero → breaking → grid", test_front_page_order),
        ("ads safety: SPONSORED · rel · rotation · AdSense", test_ads_safety),
        ("breaking feed: option/transient/file + REST + honest empty", test_breaking_feed_contract),
        ("single/page/footer templates", test_single_and_templates),
        ("JS: no library · dark · menu · chips · countdown", test_js_no_lib_and_features),
        ("theme.json palette", test_theme_json_palette),
        ("packager: validate + zip (WP upload ready)", test_packager_builds_zip),
        ("bot bridge: payload + CLI + daily hook", test_bot_bridge_payload_and_cli),
        ("docs: MANUAL PART 20 + README-THEME + GO_LIVE", test_docs_v61),
    ]
    failed = 0
    for name, fn in tests:
        try:
            fn()
            print(f"  {name} ✔")
        except AssertionError as exc:
            failed += 1
            print(f"  {name} ✘  {exc}")
        except Exception as exc:  # noqa: BLE001
            failed += 1
            print(f"  {name} ✘  {type(exc).__name__}: {exc}")
    print("-" * 66)
    if failed:
        print(f"  {failed} TEST(S) FAILED ✘")
        return 1
    print("ALL v61 REAL-WEBSITE (WP THEME) TESTS PASSED ✔")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
