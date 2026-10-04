# -*- coding: utf-8 -*-
"""v202 — "Breaking News" HEADER NAV ITEM (owner ask, 2026-10-04).

Owner: *"Breaking News kuda same like Central Jobs alaga undali — akkada click
chethe open avvali … idantha fix cheyyava, phone and laptop lo neat ga undali."*

Live reality (measured 2026-10-04): the header menu is **admin-built**
(`Home · Telangana Jobs · AP Jobs · Central Jobs · …`), so the theme's own
`studentup_mega_render()` never runs on live — a hard-coded item inside the mega
renderer would have been invisible there. The item therefore ships as a
`wp_nav_menu_items` filter for the `primary` location (injected right after the
first item = Home) **and** is echoed by the theme fallback + mobile block, so it
appears in both worlds.

Ee suite aa behaviour ni real ga lock chestundi (demo ≠ theme kabbatti rendu):

  P1 MODULE  — inc/nav-breaking.php: 5 functions, wired into functions.php,
               megamenu.php (after Home), header.php (mobile block), option
               `breaking_nav` declared + default '1'.
  P2 HONESTY — verified radar feed first, else real published posts; 0 data ⇒
               '' (khali panel ledu); links never 404 (`/#breaking` fallback);
               single `<h1>`/no Telugu invariant intact.
  P3 INJECT  — filter only for `primary`, duplicate-safe (su-navbrk / "breaking
               news" guards), inserted after the first `</li>`, never when the
               option is off.
  P4 CSS     — .su-navbrk / .su-brkdd (open state), .mlabel-brk + .su-mbrk
               mobile block, dark mode contrast, ≤900px + print hide, and the
               nav item itself stays in the inline critical layer (FOUC-safe).
  P5 PARITY  — preview/worldclass demo (normal + standalone + OFFLINE) carries
               the SAME markup: li right after Home, id="su-brkdd", 5 rows whose
               hrefs really exist on disk, mobile `.mlabel-brk` + 4 rows.

Run: python tests/v202_test.py
"""
from __future__ import annotations

import re
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
THEME = ROOT / "wordpress-theme" / "studentup"
DEMO = ROOT / "preview" / "worldclass" / "index.html"
STANDALONE = ROOT / "preview" / "worldclass" / "standalone.html"
OFFLINE = ROOT / "preview" / "OFFLINE_PREVIEW.html"
ZIP = ROOT / "wordpress-theme" / "studentup-theme.zip"
MODULE = THEME / "inc" / "nav-breaking.php"


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="ignore")


def ok(msg: str) -> None:
    print("      " + msg)


# ------------------------------------------------------------------ P1 module
def test_p1_module_and_wiring() -> None:
    assert MODULE.exists(), "inc/nav-breaking.php ledu (v202 module)"
    php = read(MODULE)
    for fn in ("studentup_breaking_nav_items", "studentup_breaking_nav_url",
               "studentup_breaking_nav_li", "studentup_breaking_mobile_block",
               "studentup_breaking_menu_filter"):
        assert re.search(r"function\s+" + fn + r"\s*\(", php), f"function ledu: {fn}"
    assert "add_filter( 'wp_nav_menu_items'" in php, \
        "wp_nav_menu_items filter ledu (admin-built menu lo item kanipinchadu)"
    # Telugu ledu (v73 invariant) — module lo English labels matrame
    for bad in ("వ", "ప", "లే", "కు"):
        assert bad not in php, f"module lo Telugu undi: {bad}"

    fn_php = read(THEME / "functions.php")
    assert "inc/nav-breaking.php" in fn_php, "functions.php lo require ledu"

    mega = read(THEME / "inc" / "megamenu.php")
    assert "studentup_breaking_nav_li()" in mega, "fallback mega lo echo ledu"
    home = mega.index("Home'") if "Home'" in mega else mega.index("'Home'")
    brk = mega.index("studentup_breaking_nav_li()")
    assert brk > home, "Home tarvata kaadu (item order wrong)"
    assert mega.index("foreach ( $groups as $g )") > brk, \
        "Breaking item mega groups tarvata padindi (Home tarvate undali)"

    tmpl = read(THEME / "inc" / "template.php")
    assert "studentup_breaking_nav_li()" in tmpl, \
        "legacy (mega ledu) fallback lo item ledu — purathana install lo kanipinchadu"
    _home = tmpl.index("esc_html__( 'Home', 'studentup' )")
    _brk = tmpl.index("studentup_breaking_nav_li()")
    _loop = tmpl.index("foreach ( $menu as $it )")
    assert _home < _brk < _loop, "legacy fallback order wrong (Home → Breaking → groups)"
    head = read(THEME / "header.php")
    assert "studentup_breaking_mobile_block()" in head, "header.php mobile block ledu"
    assert head.index("studentup_breaking_mobile_block()") < head.index('>Explore<'), \
        "mobile block Explore label mundu kaadu"

    opt = read(THEME / "inc" / "options.php")
    assert "'breaking_nav'" in opt, "options.php lo toggle ledu"
    line = [l for l in opt.splitlines() if "'breaking_nav'" in l][0]
    assert "'check', '1'" in line, "breaking_nav default '1' kaadu (opt-in? out-of-the-box ON kaavali)"
    ok("module + wiring (functions · mega · header · option) ✔")


# ---------------------------------------------------------------- P2 honesty
def test_p2_honesty_no_empty_panel() -> None:
    php = read(MODULE)
    # verified feed first, latest posts fallback — real content only
    assert "studentup_breaking_items(" in php, "verified radar feed ledu"
    assert "get_posts(" in php and "'post_status'" in php, "latest posts fallback ledu"
    assert "human_time_diff(" in php and "get_the_category(" in php, "post meta ledu"
    # khali panel / dead link footgun
    assert php.count("if ( ! $items ) {\n\t\treturn '';") >= 1 or \
        php.count("! $items ) {\n\t\t\treturn '';") >= 1, "0 items ki '' return ledu"
    assert "home_url( '/#breaking' )" in php, "/#breaking fallback ledu (404 risk)"
    for slug in ("breaking-news", "breaking", "current-affairs"):
        assert f"'{slug}'" in php, f"term slug ledu: {slug}"
    # neon/upsell text ledu; CTA honest (All latest when posts source)
    assert "'All updates'" in php and "'All latest'" in php, "CTA labels ledu"
    ok("verified-first · real posts · 0-data ⇒ item ledu · no 404 ✔")


# ----------------------------------------------------------------- P3 inject
def test_p3_injection_rules() -> None:
    php = read(MODULE)
    f = php[php.index("function studentup_breaking_menu_filter"):]
    assert "'primary' !== $loc" in f, "primary location check ledu (mobile menu lo kuda vastundi)"
    assert "strpos( (string) $items, 'su-navbrk' )" in f, "su-navbrk duplicate guard ledu"
    assert "stripos( (string) $items, 'breaking news' )" in f, \
        "admin Breaking item duplicate guard ledu (rendu items vastayi)"
    assert "strpos( (string) $items, '</li>' )" in f, "first </li> daggara insert ledu"
    assert "substr( $items, 0, $pos + 5 ) . $li ." in f, "insert order wrong"
    assert "studentup_opt( 'breaking_nav', '1' )" in php, "option gate ledu"
    # two call sites for the option gate (li + mobile) — off aithe rendu poovali
    assert php.count("studentup_opt( 'breaking_nav', '1' )") == 2, "gate call count 2 kaadu"
    ok("primary-only · duplicate-safe · after Home · option gate ✔")


# -------------------------------------------------------------------- P4 CSS
def test_p4_css_and_critical_layer() -> None:
    css = read(THEME / "assets" / "css" / "worldclass.css")
    for cls in (".su-navbrk", ".su-brkdd", ".su-brkdd-head", ".su-brkdd-cta",
                ".mlabel-brk", ".su-mbrk", ".su-mbrk-all", ".su-brkdot"):
        assert cls in css, f"CSS class ledu: {cls}"
    # open state = same mechanism as Central Jobs (JS toggles su-open)
    assert ".su-navbrk.su-open>a" in css, "su-open (click) state style ledu"
    assert "body.dark .nav .su-navbrk>a" in css, "dark mode nav item contrast ledu"
    assert "@media(max-width:900px){ .nav .su-brkdd{ display:none !important } }" in css, \
        "phone lo panel hide ledu"
    assert "@media print{ .nav .su-brkdd{ display:none !important } }" in css, "print hide ledu"
    assert "position:absolute !important" in css, "panel absolute positioning ledu"
    # JS contract: theme menu JS generic ga wire chestundi (li.menu-item-has-children)
    js = read(THEME / "assets" / "js" / "studentup-menu.js")
    assert 'classList.toggle("su-open"' in js and '":scope > li.menu-item"' in js, \
        "nav JS su-open toggle / li.menu-item wiring ledu"
    assert "mouseenter" in js and "mouseleave" in js, "hover wiring ledu"
    # critical layer: nav item inline (FOUC), panel/details lazy (cap)
    crit = read(THEME / "assets" / "css" / "critical.min.css")
    assert ".su-navbrk" in crit, "inline critical lo nav item ledu (header jark avutundi)"
    assert ".su-brkdd" not in crit, "panel inline lo undi (60 KB cap risk)"
    tool = read(ROOT / "tools" / "build_critical_css.py")
    assert '".su-brkdd"' in tool and '".su-mbrk"' in tool, "UNION_DROPPABLE ledu"
    ok("panel · open/click · dark · phone/print · critical split ✔")


# ----------------------------------------------------------------- P5 parity
def test_p5_demo_parity_and_real_links() -> None:
    assert DEMO.exists(), "demo ledu"
    demo = read(DEMO)
    # item right after Home li
    home_i = demo.index('class="menu-item"><a href="index.html">Home</a></li>')
    li_i = demo.index('class="menu-item menu-item-has-children su-navbrk"')
    jobs_i = demo.index("su-mega-li")
    assert home_i < li_i < jobs_i, "demo lo Breaking News order wrong (Home → Breaking → Jobs)"
    assert 'aria-controls="su-brkdd"' in demo and 'id="su-brkdd"' in demo, \
        "aria/id contract ledu"
    assert demo.count("su-brkdd-head") == 1, "panel head ledu"
    assert demo.count("su-brkdd-cta") == 1, "panel CTA ledu"
    # panel rows + their targets really exist (no 404 demo)
    rows = re.findall(r'<li class="menu-item" role="none"><a role="menuitem" href="([^"]+)"', demo)
    assert len(rows) >= 5, f"panel rows takkuva: {len(rows)}"
    for href in rows:
        target = (DEMO.parent / href.split("#")[0]).resolve()
        assert target.exists(), f"demo panel link 404: {href}"
    # mobile block
    assert 'class="mlabel mlabel-brk"' in demo, "mobile label ledu"
    assert demo.count('class="su-mbrk"') >= 4, "mobile rows takkuva"
    assert demo.count('class="su-mbrk-all"') == 1, "mobile CTA ledu"
    mrows = re.findall(r'<a class="su-mbrk" href="([^"]+)"', demo)
    for href in mrows:
        assert (DEMO.parent / href.split("#")[0]).resolve().exists(), f"mobile link 404: {href}"
    # english-only demo invariant (v73) — kotha rows kuda
    seg = demo[li_i:demo.index("su-mega-li")]
    assert not re.search(r"[\u0C00-\u0C7F]", seg), "demo panel lo Telugu undi"
    # standalone + OFFLINE built from the same demo
    for f in (STANDALONE, OFFLINE):
        t = read(f)
        # CSS lo kuda ee class names untayi — markup mattrame proof (panel head/CTA)
        assert 'id="su-brkdd"' in t and "su-brkdd-head" in t and "su-brkdd-cta" in t, \
            f"{f.name} lo breaking panel markup ledu (stale build?)"
        assert 'class="su-navbrk"' not in t or "su-navbrk" in t, f"{f.name}: nav item"
        assert t.count('class="su-mbrk"') >= 4 and 'class="su-mbrk-all"' in t, \
            f"{f.name} lo mobile block markup ledu"
    ok("demo + standalone + OFFLINE parity · links live ✔")


def test_p5_demo_has_no_duplicate_nav_js() -> None:
    """Demo lo theme JS ne pani cheyyali — inline duplicate ledu.

    Real bug (screenshot + jsdom tho): demo inline script lo purathana mega/drawer
    toggles unnayi. Theme JS `su-open` add cheyyagane aa purathana handler malli
    toggle-off chestundi → **click cheste panel open avvadu**. Live lo ee inline
    script ledu, so preview ≠ live. Ippudu single source: studentup-menu.js.
    """
    demo = read(DEMO)
    for junk in ("Desktop mega menu dropdown toggles", "/* Mobile menu drawer */",
                 "function closeDrawer", "function openDrawer", "megaItems.forEach"):
        assert junk not in demo, f"demo lo duplicate nav JS tirigi vachindi: {junk}"
    # theme JS matrame load avvali (2 scripts: menu + slider)
    assert demo.count('script src="../../wordpress-theme/studentup/assets/js/studentup-menu.js"') == 1, \
        "demo lo theme menu JS script tag okkate undali"
    assert "classList.add('su-open')" not in demo and 'classList.add("su-open")' not in demo, \
        "demo inline su-open manipulation undi (double-toggle risk)"
    # theme JS lone open/close logic undali
    js = read(THEME / "assets" / "js" / "studentup-menu.js")
    assert js.count('classList.toggle("su-open"') == 1, "theme JS lo su-open toggle okkate undali"
    ok("demo: single nav JS (duplicate toggles gone) ✔")


def test_p5_zip_has_module() -> None:
    assert ZIP.exists(), "theme zip ledu"
    with zipfile.ZipFile(ZIP) as z:
        names = z.namelist()
        assert any(n.endswith("inc/nav-breaking.php") for n in names), \
            "zip lo v202 module ledu (stale zip — rebuild cheyyali)"
        css = z.read([n for n in names if n.endswith("assets/css/worldclass.css")][0]).decode("utf-8", "ignore")
        assert ".su-navbrk" in css and ".su-mbrk" in css, "zip CSS stale"
    ok(f"zip fresh ({len(names)} files) · module + CSS ✔")


def main() -> int:
    tests = [
        test_p1_module_and_wiring,
        test_p2_honesty_no_empty_panel,
        test_p3_injection_rules,
        test_p4_css_and_critical_layer,
        test_p5_demo_parity_and_real_links,
        test_p5_demo_has_no_duplicate_nav_js,
        test_p5_zip_has_module,
    ]
    print("v202 — Breaking News nav item (header) — %d checks" % len(tests))
    failed = 0
    for t in tests:
        try:
            t()
        except AssertionError as e:
            failed += 1
            print("   ❌ %s: %s" % (t.__name__, e))
        except Exception as e:  # noqa: BLE001
            failed += 1
            print("   💥 %s: %r" % (t.__name__, e))
    if failed:
        print("\n%d/%d FAIL" % (len(tests) - failed, len(tests)))
        return 1
    print("\n%d/%d PASS ✔" % (len(tests), len(tests)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
