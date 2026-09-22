# -*- coding: utf-8 -*-
"""v89 tests — PREMIUM HOMEPAGE (theme 1.9.0).

User-reported bugs (screenshots):
  * TS/AP Govt Jobs cards+menu+chips asalu kanipinchaledu (slug mismatch:
    live categories `ts-govt-jobs` vs theme `ts-jobs` — silent fail)
  * Central Govt Jobs section ledu
  * social icons platform-wise tappu ga (emoji 💬✈️📸▶️)
  * "Read more" click dead (rendu `<b>` matrame — link kaadu)
  * search type chesinappudu results load avvadam ledu
  * qualification dropdown plain/ugly
  * latest jobs scrolling ledu
  * "Students Internet Center" brand block Telugu lo neat ga ledu

Checks (offline source audits + bot imports):
  * alias resolver + reverse map + anni call-sites (front/header/footer/menu)
  * Central entry (theme + bot + preview + jsdom + guardian sync, order parity)
  * latest ticker (front_page only, transient cache, same-tab post links, flush)
  * live search (header combobox + JS REST/Aria/keyboard + localize rest)
  * brand SVG icons everywhere; platform emojis gone from chrome
  * Read more real permalink link
  * Telugu Internet-center block + perks + WhatsApp icon
  * animated custom qual dropdown (quadd) + SSC wording/keywords
  * 1.9.2 parity + readme 1.9.0/1.9.1/1.9.2 changelog + suites 71 pins
    (v91 update: theme 1.9.0 → 1.9.2 bump · 69 → 71 suites)

Run: python tests/v89_test.py   (also via python run.py --test-all)
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

THEME = ROOT / "wordpress-theme" / "studentup"


def read(rel: Path | str) -> str:
    return Path(rel).read_text(encoding="utf-8")


def test_alias_resolver() -> None:
    fn = read(THEME / "functions.php")
    assert "function studentup_cat_aliases" in fn
    assert "function studentup_used_term" in fn
    assert "function studentup_theme_cat" in fn
    for alias in ("'ts-govt-jobs'", "'ap-govt-jobs'", "'central-govt-jobs'",
                  "'walkin-jobs', 'walkin'", "'software-jobs', 'software'",
                  "'hall-tickets', 'hallticket'"):
        assert alias in fn, alias
    # anni call-sites resolver vaadutunnayi (raw slug look-up emi migalakudadu)
    for rel in ("front-page.php", "header.php", "footer.php"):
        src = read(THEME / rel)
        assert "studentup_used_term( $m['slug'] )" in src, rel
        assert "get_category_by_slug( $m['slug'] )" not in src, rel + ": dead look-up inka undi"
    tpl = read(THEME / "inc" / "template.php")
    # v93: menu fallback grouped dropdowns ki rewrite ayyindi — resolver ippudu
    # closure (`$term_of = function ( $slug ) { return studentup_used_term( $slug ); }`)
    # tho call avutundi. Intent same: fallback **alias-aware resolver** ne vaadali,
    # raw slug look-up (get_category_by_slug) eppudu vadakoodadu.
    _fb = tpl[tpl.index("function studentup_menu_fallback"):]
    _fb = _fb[:_fb.index("\nfunction ", 10)]
    assert "studentup_used_term( $slug )" in _fb, "menu fallback resolver ledu"
    assert "get_category_by_slug(" not in _fb, "menu fallback lo dead raw look-up undi"
    assert "studentup_theme_cat(" in tpl, "card cat reverse-map ledu"
    print("  alias resolver + 4 call-sites ✔")


def test_central_everywhere() -> None:
    fn = read(THEME / "functions.php")
    slugs = re.findall(r"'slug' => '([a-z-]+)', 'label' => '([^']+)'", fn)
    assert [s for s, _ in slugs][:3] == ["ts-jobs", "ap-jobs", "central-jobs"], slugs[:3]
    from autoblog import breaking
    assert breaking.most_used_cats()[:3] == ["ts-jobs", "ap-jobs", "central-jobs"]
    # theme labels == bot labels (v73 parity rule keeps working)
    assert [l for _, l in slugs] == [m["label"] for m in breaking.most_used()], \
        "theme/bot most-used labels desync"
    html = read(ROOT / "preview" / "index.html")
    assert html.count('data-ucount=') == len(breaking.most_used()) == 9
    assert 'data-goto-cat="central-jobs"' in html
    grd = read(ROOT / "autoblog" / "guardian.py")
    assert "len(used) != 9" in grd, "guardian 9-tile pin update avvaledu"
    js = read(ROOT / "tests" / "runtime" / "jsdom_runtime_test.js")
    assert 'usedTiles.length === 9' in js and '"central-jobs","hallticket"' in js
    print("  Central: theme + bot + preview + jsdom + guardian ✔")


def test_latest_ticker() -> None:
    br = read(THEME / "inc" / "breaking.php")
    assert "function studentup_latest_ticker_items" in br
    assert "get_transient( 'su_latest_ticker' )" in br
    assert "set_transient( 'su_latest_ticker'" in br
    assert "add_action( 'save_post', 'studentup_latest_ticker_flush'" in br, "cache flush ledu"
    assert "function studentup_latest_ticker" in br
    assert "is_front_page()" in br, "ticker anni pages lo kakudadu (reading distraction)"
    seg = br.split("function studentup_latest_ticker()", 1)[1]
    assert "target=\"_blank\"" not in seg, "internal post link new tab kakudadu"
    assert "Latest Jobs" in seg
    assert "latest_ticker" in read(THEME / "inc" / "options.php"), "admin option ledu"
    fp = read(THEME / "front-page.php")
    assert "studentup_latest_ticker()" in fp
    css = read(THEME / "style.css")
    assert ".su-lticker{" in css and ".tlabel-blue" in css and "animation-play-state:paused" in css
    print("  latest-jobs ticker (own posts · click→post · hover pause) ✔")


def test_live_search() -> None:
    hd = read(THEME / "header.php")
    for needle in ("su-livesearch", "su-sres", "role=\"combobox\"", "aria-activedescendant"):
        assert needle in hd + read(THEME / "assets" / "js" / "studentup.js"), needle
    js = read(THEME / "assets" / "js" / "studentup.js")
    for needle in ("AbortController", "per_page=7", "encodeURIComponent(q)",
                   "ArrowDown", "aria-expanded", "fetch(url"):
        assert needle in js, needle
    fn = read(THEME / "functions.php")
    assert "'rest'" in fn and "rest_url( 'wp/v2/' )" in fn, "REST URL localize ledu"
    css = read(THEME / "style.css")
    assert ".su-sres{" in css and ".su-srow" in css and "suSresIn" in css
    print("  live search (REST · debounce · keyboard · click→post) ✔")


def test_brand_icons_no_emoji() -> None:
    opt = read(THEME / "inc" / "options.php")
    assert "function studentup_social_icon" in opt
    for key in ("'whatsapp'", "'telegram'", "'instagram'", "'youtube'", "'x'", "'call'", "'email'"):
        assert key in opt, key
    # chrome emoji teesesaam — brand SVG classes replaced them
    ft = read(THEME / "footer.php")
    assert "💬" not in ft and "✈" not in ft and "📸" not in ft and "▶" not in ft
    for cls in ("su-rail-wa", "su-rail-tg", "su-rail-ig", "su-rail-yt"):
        assert cls in ft, cls
    hd = read(THEME / "header.php")
    assert "wa.me/919182739312" not in hd and "t.me/studentup_in" not in hd, \
        "mpanel hardcoded socials inka unnayi — options vaadaali"
    for cls in ("su-msoc-wa", "su-msoc-tg", "su-msoc-ig", "su-msoc-yt"):
        assert cls in hd, cls
    sp = read(THEME / "single.php")
    for cls in ("su-share-wa", "su-share-tg", "su-share-x"):
        assert cls in sp, cls
    assert "Share on WhatsApp" in sp, "v61 pin: share label povvakudadu"
    ab = read(THEME / "inc" / "author-box.php")
    assert "✈" not in ab and "💬" not in ab
    css = read(THEME / "style.css")
    for cls in (".su-rail-wa", ".su-rail-ig", ".su-share-wa", ".su-msoc-wa"):
        assert cls in css, cls
    print("  brand SVG icons (rail · mpanel · share · author) — emoji out ✔")


def test_read_more_real_link() -> None:
    tpl = read(THEME / "inc" / "template.php")
    assert "su-readmore" in tpl and "Read more" in tpl
    assert "<b><?php echo esc_html( 'Read guide" not in tpl, "dead bold text inka undi"
    assert re.search(r"su-readmore\" href=\"<\?php the_permalink\(\); \?>", tpl), \
        "read-more permalink link kaadu?"
    assert ".su-readmore" in read(THEME / "style.css")
    print("  card 'Read more' = real permalink link ✔")


def test_telugu_internet_center_brand() -> None:
    cta = read(THEME / "inc" / "cta.php")
    assert "విద్యార్థుల ఇంటర్నెట్ సెంటర్" in cta, "Telugu brand name ledu"
    assert "Students Internet Center · Telangana &amp;" in cta or \
           "Students Internet Center · Telangana &" in cta
    assert "ఎక్కడికీ వెళ్లవలసిన అవసరం లేదు" in cta, "Telugu lead ledu"
    assert "పూర్తి Guidance" in cta and "Preparation Group" in cta and "Application PDF" in cta
    assert "WhatsApp లో documents పంపండి" in cta
    assert "social_icon( 'whatsapp'" in cta, "WhatsApp brand icon ledu"
    assert "tel:+91" in cta
    css = read(THEME / "style.css")
    assert ".su-ic-perks" in css and ".su-ic-sub" in css
    print("  Telugu Internet-center brand + perks + WA button ✔")


def test_quadd_and_ssc() -> None:
    qf = read(THEME / "inc" / "qual-filter.php")
    assert "'SSC · 10th'" in qf, "SSC wording ledu"
    assert "data-icons" in qf and "🎯 Your qualification:" in qf
    for kw in ("'ssc gd'", "'ssc mts'", "'ssc chsl'", "'matriculation'"):
        assert kw in qf, kw
    js = read(THEME / "assets" / "js" / "studentup.js")
    for needle in ("quadd-btn", "quadd-panel", "quadd-item", "requestAnimationFrame",
                   "aria-haspopup\", \"listbox", '"SSC · 10th"'):
        assert needle in js, needle
    css = read(THEME / "style.css")
    for needle in (".quadd{", ".quadd.open .quadd-panel", ".quadd-item[aria-selected=\"true\"]",
                   "cubic-bezier"):
        assert needle in css, needle
    assert ".qualsel.quadd-src" in css, "native select hiding CSS ledu (no-JS safe)"
    print("  animated quadd dropdown + SSC/10+2 mapping ✔")


def test_layout_premium_css() -> None:
    css = read(THEME / "style.css")
    assert "grid-template-columns:repeat(3,minmax(0,1fr))" in css, "laptop 3-col grid ledu"
    assert "min-width:981px" in css
    assert ".menu-primary{" in css and "overflow-x:auto" in css, "laptop menu scroll ledu"
    assert "current-menu-item>a" in css, "current-page pin ledu"
    assert ".hero-slim h1{background:" in css or ".hero-slim h1{" in css
    hot = read(THEME / "front-page.php")
    assert "( $i < 3 )" in hot, "TS·AP·Central hot highlight ledu"
    print("  laptop 3×3 strip + 3-col grid + menu polish ✔")


def test_version_and_pins() -> None:
    # v91: theme 1.9.2 (notify 1.9.1 + telegram tools 1.9.2) · suites 71
    php = re.search(r"STUDENTUP_VERSION',\s*'([^']+)'", read(THEME / "functions.php")).group(1)
    css = re.search(r"Version:\s*([0-9.]+)", read(THEME / "style.css")).group(1)
    stable = re.search(r"Stable tag:\s*([0-9.]+)", read(THEME / "readme.txt")).group(1)
    assert php == css == stable == "1.9.8", f"parity tappu: {php}·{css}·{stable}"
    readme = read(THEME / "readme.txt")
    for entry in ("= 1.9.0", "= 1.9.1", "= 1.9.2", "= 1.9.3", "= 1.9.4", "= 1.9.5", "= 1.9.6", "= 1.9.7", "= 1.9.8"):
        assert entry in readme, f"readme changelog {entry} ledu"
    assert "Central Govt Jobs" in readme
    for f in ("v75_test.py", "v76_test.py", "v77_test.py", "v78_test.py",
              "v79_test.py", "v80_test.py", "v81_test.py"):
        assert "suites == 80" in read(ROOT / "tests" / f), f + " (69→74 pin)"
    suites = len(list((ROOT / "tests").glob("*_test.py")))
    assert suites == 80, f"suites {suites} (v100 tho 80)"
    print("  version parity 1.9.2 + suites pins 71 ✔")


TESTS = [
    ("alias resolver + call-sites", test_alias_resolver),
    ("Central everywhere sync", test_central_everywhere),
    ("latest-jobs ticker", test_latest_ticker),
    ("live search", test_live_search),
    ("brand icons / no chrome emoji", test_brand_icons_no_emoji),
    ("read-more real link", test_read_more_real_link),
    ("telugu internet-center brand", test_telugu_internet_center_brand),
    ("quadd + SSC", test_quadd_and_ssc),
    ("premium layout css", test_layout_premium_css),
    ("version + pins", test_version_and_pins),
]


def main() -> None:
    os.chdir(ROOT)
    print("=" * 70)
    print("v89 PREMIUM HOMEPAGE — regression tests")
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
    print("ALL v89 PREMIUM-HOMEPAGE TESTS PASSED ✔")


if __name__ == "__main__":
    main()
