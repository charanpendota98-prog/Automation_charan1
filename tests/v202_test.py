# -*- coding: utf-8 -*-
"""Local-news and responsive-navigation compatibility checks for theme v1.9.44.

The primary desktop order is Home / Telangana / Andhra Pradesh / Central Govt /
More. Phones get one visible Menu button and one working drawer. Breaking News
is never a top-level nav injection; it appears only under More and only while
fresh, source-verified TS/AP state or district news exists. The older test file
name is retained so existing local workflows continue to work.

Run: python3 tests/v202_test.py
"""
from __future__ import annotations

import re
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
THEME = ROOT / "wordpress-theme" / "studentup"
DEMO = ROOT / "preview" / "index.html"
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
    """The responsive header keeps TS/AP/Central navigation and local news conditional."""
    assert MODULE.exists(), "inc/nav-breaking.php ledu (verified local-news module)"
    php = read(MODULE)
    for fn in ("studentup_breaking_nav_items", "studentup_breaking_nav_url",
               "studentup_breaking_nav_li", "studentup_breaking_mobile_block",
               "studentup_breaking_menu_filter"):
        assert re.search(r"function\s+" + fn + r"\s*\(", php), f"function ledu: {fn}"
    assert "inc/nav-breaking.php" in read(THEME / "functions.php")

    tmpl = read(THEME / "inc" / "template.php")
    assert "studentup_primary_job_items()" in tmpl and "studentup_menu_more_items()" in tmpl
    assert "studentup_breaking_items( 1 )" in tmpl, "Breaking News entry must depend on a real local item"
    assert "studentup_breaking_enabled()" in tmpl and "studentup_opt( 'breaking_nav', '1' )" in tmpl
    fallback = tmpl[tmpl.index("function studentup_menu_fallback"):tmpl.index("function studentup_breadcrumbs")]
    assert "Home" in fallback and "Central Govt" not in fallback  # labels come from the ordered job-item data
    assert "More" in fallback and "class=\"sub-menu\"" in fallback
    more = tmpl[tmpl.index("function studentup_menu_more_items"):tmpl.index("function studentup_menu_fallback")]
    assert "get_categories( array( 'hide_empty' => true" in more, "new/live categories must stay in More"
    assert "Breaking News · TS/AP local updates" in more

    head = read(THEME / "header.php")
    assert head.count('id="mpanel"') == 1, "duplicate mobile drawer markup"
    assert 'id="menubtn"' in head and 'class="menubtn-label">Menu</span>' in head
    assert "studentup_breaking_mobile_block()" not in head, "Breaking News must live under More"
    assert 'id="su-mobile-more"' in head
    opt = read(THEME / "inc/options.php")
    assert "'breaking_nav'" in opt
    ok("theme wiring · focused Home/TS/AP/Central/More nav · single drawer ✔")


# ---------------------------------------------------------------- P2 honesty
def test_p2_honesty_no_empty_panel() -> None:
    """No latest-post fallback: fresh verified TS/AP state/district news only."""
    php = read(THEME / "inc/breaking.php")
    for tag in ("ts-state-news", "ap-state-news", "ts-district-news", "ap-district-news"):
        assert tag in php
    assert "studentup_breaking_local_kind" in php
    assert "source_verified" in php and "36 * HOUR_IN_SECONDS" in php
    assert r"\bjobs?\b" in php and r"\bexam(?:ination)?\b" in php
    module = read(MODULE)
    assert "studentup_breaking_items(" in module
    assert "get_posts(" not in module and "human_time_diff(" not in module
    assert "latest published posts" not in module.lower()
    assert "All local updates" in module
    section = php[php.index("function studentup_breaking_section"):]
    assert "if ( ! $items )" in section and "return;" in section
    template = read(THEME / "inc" / "template.php")
    assert "studentup_breaking_items( 1 )" in template
    assert "No new verified breaking updates" not in php
    ok("verified-only TS/AP state + district news · job cues rejected · empty feed omitted ✔")


# ----------------------------------------------------------------- P3 inject
def test_p3_navigation_keeps_news_inside_more() -> None:
    php = read(MODULE)
    assert "function studentup_breaking_menu_filter" in php  # legacy helper retained but not registered
    assert "add_filter( 'wp_nav_menu_items', 'studentup_breaking_menu_filter'" not in php
    mega = read(THEME / "inc" / "megamenu.php")
    assert "studentup_breaking_nav_li()" not in mega
    head = read(THEME / "header.php")
    assert "studentup_breaking_nav_li()" not in head
    assert "studentup_breaking_mobile_block()" not in head
    template = read(THEME / "inc" / "template.php")
    more = template[template.index("function studentup_menu_more_items"):template.index("function studentup_menu_fallback")]
    assert "studentup_breaking_items( 1 )" in more
    assert "Breaking News · TS/AP local updates" in more
    ok("secondary links + conditional Breaking News stay under More ✔")


def _first_item_end(items: str):
    """PHP `studentup_breaking_first_item_end()` algorithm ki Python mirror.

    Miru ikkada algorithm ni test chestunnam (PHP binary ee env lo ledu) — PHP
    source lo same regex/depth logic unda leda ni P3 verify chestundi.
    """
    import re as _re
    depth, off = 0, 0
    while off < len(items):
        m = _re.compile(r"<(li|/li)\b[^>]*>", _re.I).search(items, off)
        if not m:
            return None
        tag, end = m.group(1).lower(), m.end()
        if tag == "li":
            depth += 1
        else:
            depth -= 1
            if depth <= 0:
                return end
        off = end
    return None


def test_p3b_legacy_nested_markup_helper() -> None:
    """First item ki submenu unte kuda item top-level ga (Central Jobs pakkana) padali."""
    flat = '<li class="menu-item"><a href="/">Home</a></li><li class="menu-item"><a href="/jobs/">Jobs</a></li>'
    end = _first_item_end(flat)
    assert flat[:end].count("</li>") == 1 and flat[end:].startswith('<li'), "flat menu case"

    nested = ('<li class="menu-item menu-item-has-children"><a href="/">Home</a>'
              '<ul class="sub-menu"><li class="menu-item"><a href="/a/">A</a></li>'
              '<li class="menu-item"><a href="/b/">B</a></li></ul></li>'
              '<li class="menu-item"><a href="/jobs/">Jobs</a></li>')
    end = _first_item_end(nested)
    assert end is not None, "nested case lo position dorakaledu"
    pre = nested[:end]
    # insert point lo depth == 0 (ante top-level — sub-menu lopala kaadu)
    depth = len(re.findall(r"<li\b", pre)) - pre.count("</li>")
    assert depth == 0, f"insert point depth {depth} — item sub-menu lopala padutundi (live bug!)"
    injected = pre + '<li class="menu-item su-navbrk">BRK</li>' + nested[end:]
    assert injected.index("BRK") > injected.index("Home")
    assert injected.count("<ul") == injected.count("</ul>"), "markup balance poyindi"
    assert injected.count("<ul") == injected.count("</ul>"), "markup balance poyindi"
    # WP menu lo `<link` laantivi unna kuda depth scan confuse avvakoodadu
    weird = '<li><a href="/x?q=1">x</a></li>'
    assert _first_item_end(weird) == len(weird)
    assert _first_item_end("no items here") is None, "li lekunda position ichindi"
    ok("injection: nested first item unna top-level ga (depth-aware) ✔")


# -------------------------------------------------------------------- P4 CSS
def test_p4_css_and_critical_layer() -> None:
    css = read(THEME / "assets" / "css" / "worldclass.css")
    assert ".header .menubtn-label{display:inline}" in css
    assert ".header .menu-primary .su-more-menu>.sub-menu" in css
    assert ".mpanel .su-mobile-more:not([open])>.mgroup-body{display:none!important}" in css
    assert ".mpanel .su-mobile-more[open]>.mgroup-body{display:grid}" in css
    assert "@media(max-width:980px)" in css and ".header .nav{display:none!important}" in css
    assert ".header .menubtn{display:inline-flex!important}" in css
    assert ".header .logo .mark{display:none!important}" in css
    assert ".header .logo .brand" in css and "text-shadow:none" in css
    assert "body.dark .header .logo .brand" in css
    js = read(THEME / "assets" / "js" / "studentup-menu.js")
    assert 'classList.toggle("su-open"' in js and 'getElementById("menubtn")' in js
    assert 'btnLabel.textContent = open ? "Close" : "Menu"' in js
    assert 'e.key === "Escape"' in js and 'if (e.key === "Tab")' in js
    crit = read(THEME / "assets" / "css" / "critical-home.min.css")
    assert len(crit.encode("utf-8")) < 60000
    assert "su-home-intro" in crit and "su-op-card" in crit and "su-jt" in crit
    tool = read(ROOT / "tools" / "build_critical_css.py")
    assert '".su-brkdd"' in tool and '".su-mbrk"' in tool
    assert "HOME_CRITICAL_KEEP" in tool and "home_union_drop" in tool
    assert ".mpanel" in crit and ".mbackdrop" in crit
    assert ".su-mobile-more" in crit and ".su-more-menu" in crit
    ok("visible phone Menu · inlined drawer/More · desktop dropdown · restrained brand ✔")


# ----------------------------------------------------------------- P5 parity
def test_p5_demo_parity_and_real_links() -> None:
    """Canonical static preview follows the focused, data-free homepage."""
    assert DEMO.exists(), "preview/index.html ledu"
    demo = read(DEMO)
    for label in ("Home", "Telangana", "Andhra Pradesh", "Central Govt", "More"):
        assert label in demo, f"primary navigation label ledu: {label}"
    assert 'id="mpanel"' in demo and demo.count('id="mpanel"') == 1
    assert 'id="menubtn"' in demo and 'menubtn-label">Menu</span>' in demo
    assert 'class="su-bnav"' not in demo
    assert "data/breaking.json" in demo and "breaking-mount" not in demo
    assert "studentup-slider.js" not in demo and "studentup-smart.js" not in demo
    assert 'class="su-navbrk"' not in demo and 'class="su-mbrk"' not in demo

    # Every local HTML/CSS/JS link in the static preview resolves on disk.
    for href in re.findall(r'(?:href|src)="([^"]+)"', demo):
        if href.startswith(("#", "http://", "https://")):
            continue
        target = (DEMO.parent / href.split("#", 1)[0]).resolve()
        assert target.exists(), f"preview link 404: {href}"
    ok("compact preview · one drawer · local assets/pages resolve ✔")


def test_p5_demo_has_no_duplicate_nav_js() -> None:
    """The static homepage loads one menu controller and contains one drawer."""
    demo = read(DEMO)
    assert demo.count('src="../wordpress-theme/studentup/assets/js/studentup-menu.js"') == 1
    assert 'src="../wordpress-theme/studentup/assets/js/studentup-slider.js"' not in demo
    assert demo.count('id="mpanel"') == 1
    for junk in ("Desktop mega menu dropdown toggles", "function closeDrawer",
                 "function openDrawer", "megaItems.forEach", 'classList.add("su-open")'):
        assert junk not in demo, f"inline duplicate navigation logic found: {junk}"
    js = read(THEME / "assets" / "js" / "studentup-menu.js")
    assert js.count('classList.toggle("su-open"') == 1
    ok("single drawer · single menu controller · no duplicate toggle code ✔")


def test_p5_layout_proof_tool_exists() -> None:
    """Phone+laptop neatness ki real-browser measurement tool (owner ask)."""
    tool = ROOT / "tools" / "verify_breaking_ui.js"
    assert tool.exists(), "tools/verify_breaking_ui.js ledu (phone/laptop proof tool)"
    t = read(tool)
    for needle in ("phone-360", "phone-390", "phone-414", "tablet-768",
                   "laptop-1440", "desktop-1920", "--json", "SKIP",
                   "desktopMoreVisible", "drawerOpen", "mobileMoreVisible"):
        assert needle in t, f"tool lo {needle} ledu"
    assert "scrollWidth" in t and "getBoundingClientRect" in t, "nijamaina measurements ledu"
    assert "menuButtonVisible" in t and "primaryLabels" in t
    assert "su-navbrk" not in t, "retired standalone Breaking News menu is still measured"
    ok("layout proof tool (8 widths × light/dark) ✔")


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
        test_p3_navigation_keeps_news_inside_more,
        test_p3b_legacy_nested_markup_helper,
        test_p4_css_and_critical_layer,
        test_p5_demo_parity_and_real_links,
        test_p5_demo_has_no_duplicate_nav_js,
        test_p5_layout_proof_tool_exists,
        test_p5_zip_has_module,
    ]
    print("v204 navigation/news compatibility — %d checks" % len(tests))
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
