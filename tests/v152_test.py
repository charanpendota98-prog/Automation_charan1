# -*- coding: utf-8 -*-
"""v152 — minified CSS build (speed) with a safe fallback."""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import minify_assets  # noqa: E402

THEME = ROOT / "wordpress-theme" / "studentup"


def test_strings_and_urls_survive():
    css = '.a:after{content:" (" attr(href) ")";}\n.b{background:url(img/x.png) no-repeat}\n'
    out = minify_assets.minify_css(css)
    assert '" ("' in out and '")"' in out, "string literal broke"
    assert "url(img/x.png)" in out, "url() broke"
    print("      strings and url() untouched ✔")


def test_comments_go_but_rules_stay():
    # The first comment is the file header (WordPress needs it) and is kept
    # by design; every later comment is stripped.
    css = "/* header */\n.a{color:red}\n/* note */\n.b{color:blue}\n"
    out = minify_assets.minify_css(css)
    assert "header" in out, "file header comment poyindi"
    assert "note" not in out, "inner comments strip avvaledu"
    assert out.count("{") == 2
    print("      inner comments removed, rule count identical ✔")


def test_media_queries_and_pseudo_selectors_survive():
    css = "@media (max-width:640px){.a > .b:not(.c){margin:0 auto}}\n"
    out = minify_assets.minify_css(css)
    assert "@media (max-width:640px)" in out
    assert ".a>.b:not(.c)" in out
    assert "margin:0 auto" in out, "shorthand value corrupt ayyindi"
    print("      media queries + combinators survive ✔")


def test_built_files_exist_and_are_smaller():
    for src in (THEME / "style.css", THEME / "assets" / "css" / "premium.css"):
        mini = src.with_suffix(".min.css")
        assert mini.exists(), f"{mini.name} build ledu"
        assert len(mini.read_bytes()) < len(src.read_bytes()), "minified file peddadi ayyindi"
        assert mini.read_text(encoding="utf-8").count("{") == \
            src.read_text(encoding="utf-8").count("{"), "rules poyayi"
    print("      built min.css files are smaller and complete ✔")


def test_theme_header_survives_in_style_min():
    head = (THEME / "style.min.css").read_text(encoding="utf-8")[:400]
    assert "Theme Name:" in head, "WP theme header poyindi — theme break avutundi"
    print("      WordPress theme header preserved ✔")


def test_theme_falls_back_when_min_missing():
    fns = (THEME / "functions.php").read_text(encoding="utf-8")
    assert "studentup_css_url" in fns
    body = fns.split("function studentup_css_url")[1][:800]
    assert "file_exists" in body, "min file leకpote fallback ledu"
    assert "SCRIPT_DEBUG" in body, "debug mode lo source CSS ivvali"
    assert re.search(r"return get_template_directory_uri\(\) \. '/' \. \$rel;", body), "fallback return ledu"
    print("      falls back to the readable source when needed ✔")


def test_build_wires_minify():
    src = (ROOT / "tools" / "build_wp_theme.py").read_text(encoding="utf-8")
    assert "minify_assets" in src, "zip build lo minify wiring ledu"
    print("      zip build runs the minifier ✔")


TESTS = [
    ("literals", test_strings_and_urls_survive),
    ("comments", test_comments_go_but_rules_stay),
    ("media", test_media_queries_and_pseudo_selectors_survive),
    ("built", test_built_files_exist_and_are_smaller),
    ("header", test_theme_header_survives_in_style_min),
    ("fallback", test_theme_falls_back_when_min_missing),
    ("build", test_build_wires_minify),
]


def main() -> int:
    bad = 0
    for name, fn in TESTS:
        try:
            fn()
            print(f"  {name} ✔")
        except Exception as exc:  # noqa: BLE001
            bad += 1
            print(f"  {name} ✘ {type(exc).__name__}: {exc}")
    print("-" * 70)
    print("ALL v152 TESTS PASSED ✔" if not bad else f"{bad} TEST(S) FAILED ✘")
    return int(bool(bad))


if __name__ == "__main__":
    raise SystemExit(main())
