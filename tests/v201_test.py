# -*- coding: utf-8 -*-
"""v201 — PREVIEW ↔ LIVE PARITY (owner ask, 2026-10-04).

Owner: *"ikkada preview lo chupinchindi theme upload chesthe zip chesthe live lo
alaga ledu enti asalu ndhuku"* — i.e. the uploaded theme did **not** look like the
preview. Root cause: `preview/worldclass/index.html` is a hand-written demo; its
markup (hero H1 + quick chips, the "LIVE Latest Notifications" sliding track and
that track's JS) was never rendered by the theme's PHP. Static gates + jsdom were
reading the demo, so everything stayed "green" while live differed.

Ee suite aa gap ni permanent gate ga marchindi:

  P1 HERO      — theme PHP renders the demo's h1 copy + search + 8 chips;
                 "Breaking News" uses .su-hact--breaking (inline style ledu),
                 links never 404 (term leda → /#jobs).
  P2 SLIDER    — inc/slider.php builds the demo's track markup from REAL
                 published posts (fake card ledu), front page only.
  P3 JS        — assets/js/studentup-slider.js ships the autoslide behaviour
                 (3200ms, prev/pause/next, hover/focus/touch/visibility,
                 ←/→, reduced-motion, "/" search focus) and the demo loads the
                 same file — demo inline copy poyindi.
  P4 ORDER     — front-page: ticker → hero → latest notifications; page 1 ki
                 okkate <h1> (hero), sr-only h1 page-2 ki mattrame.
  P5 CSS/DOCS  — the classes the new markup uses really have rules, README
                 documents the parity + the honest remaining differences,
                 zip fresh.

Run: python tests/v201_test.py
"""
from __future__ import annotations

import re
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
THEME = ROOT / "wordpress-theme" / "studentup"
DEMO = ROOT / "preview" / "worldclass" / "index.html"
ZIP = ROOT / "wordpress-theme" / "studentup-theme.zip"

CHIPS = ["Breaking News", "Latest Jobs", "TSPSC / Telangana", "APPSC / Andhra Pradesh",
         "Central Govt", "Police / Defence", "10th / Inter", "Results &amp; Keys"]
H1 = "Government Jobs, Results &amp; Notifications"
H1_PHP = "Government Jobs, Results & Notifications"


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="ignore")


def plain(t: str) -> str:
    """HTML entities → plain text (PHP renders `&`, demo HTML ships `&amp;`)."""
    return t.replace("&amp;", "&")


# ------------------------------------------------------------------ P1 hero
def test_p1_hero_markup_in_theme() -> None:
    """Demo hero (h1 + search + 8 chips) ni theme PHP render chestundo."""
    prem = read(THEME / "inc" / "premium.php")
    assert H1_PHP in prem, "hero h1 copy ledu (demo: Government Jobs, Results & Notifications)"
    assert re.search(r'<h1[^>]*class="su-hero-title"', prem), "su-hero-title <h1> ledu"
    assert "su-search-wrap" in prem, "search wrapper ledu"
    assert 'id="su-q"' in prem and 'class="su-kbd"' in prem, "search input / kbd hint ledu"
    assert "screen-reader-text" in prem and 'for="su-q"' in prem, "search label ledu"
    premp = plain(prem)
    for label in CHIPS:
        assert plain(label) in premp, f"hero chip ledu: {label}"
    assert "su-hact--breaking" in prem, "Breaking News class ledu (inline style footgun)"
    # chip links: real term or jobs-board fallback — 404 eppudu raakoodadu
    assert "studentup_used_term(" in prem and "home_url( '/#jobs' )" in prem, \
        "chip link fallback ledu"
    # purathana hero slogans / dead decorations malli raakoodadu (demo lo levu)
    for gone in ("One place for every", "su-hero-orb", "su-hero-kicker"):
        assert gone not in prem, f"purathana hero markup inka undi: {gone}"
    # live hero lo unna "Trending today" strip + state bar + workspace chip
    assert "studentup_trending_today()" in prem and "studentup_state_switch()" in prem, \
        "trending/state bar call ledu (live sthayilo unna sections)"
    assert "My Workspace" in prem and "studentup_workspace_url()" in prem, "workspace chip ledu"


# ---------------------------------------------------------------- P2 slider
def test_p2_slider_from_real_posts() -> None:
    """inc/slider.php — demo track markup, real posts nunchi, front page only."""
    p = THEME / "inc" / "slider.php"
    assert p.exists(), "inc/slider.php ledu"
    s = read(p)
    assert "function studentup_latest_notifications(" in s, "renderer function ledu"
    assert "is_front_page()" in s, "front-page gate ledu"
    assert "get_posts(" in s and re.search(r"'post_status'\s*=>\s*'publish'", s), \
        "real posts query ledu"
    # demo markup: section + head + viewport + track + 3 buttons
    for needle in ('class="su-slider-sec"', 'class="su-slider-head"', 'su-slider-badge',
                   'class="su-slider-ctrls"', 'class="su-slider-viewport"',
                   'id="su-jobs-track-wrap"', 'class="su-slider-track"',
                   'id="su-jobs-track"', 'id="su-track-prev"', 'id="su-track-pause"',
                   'id="su-track-next"'):
        assert needle in s, f"demo track markup ledu: {needle}"
    # rich card + honest metadata (fake values ledu)
    for needle in ("su-scard", "su-scard-tag", "su-scard-hot", "su-scard-meta",
                   "studentup_opportunity_last_date", "studentup_opportunity_days_left",
                   "studentup_qual_labels", "studentup_card_accent",
                   "'Full details & Apply'", "studentup_social_icon( 'whatsapp'"):
        assert needle in s, f"card piece ledu: {needle}"
    # no fake numbers: meta lines only when the post really has them
    assert re.search(r"\$vac\s*!==\s*''", s) or "$vac" in s, "vacancy guard ledu"
    assert "esc_html" in s and "esc_url" in s, "escaping ledu"
    assert "foreach ( $posts as $post )" in s, "post loop ledu"
    assert "get_permalink( $post )" in s and "get_the_title( $post )" in s, \
        "real post data vaadataledu"


# -------------------------------------------------------------------- P3 JS
def test_p3_shipped_slider_js() -> None:
    """Theme JS lo autoslide behaviour + demo adi ne vaadutundo."""
    js = read(THEME / "assets" / "js" / "studentup-slider.js")
    for needle in ("su-jobs-track-wrap", "su-track-next", "su-track-prev", "su-track-pause",
                   "3200", "mouseenter", "mouseleave", "focusin", "touchstart",
                   "visibilitychange", "ArrowRight", "ArrowLeft", "prefers-reduced-motion",
                   "scrollBy", "scrollTo"):
        assert needle in js, f"slider JS lo ledu: {needle}"
    assert "310" in js, "demo step (310px) ledu"
    proc = subprocess.run(["node", "--check", str(THEME / "assets" / "js" / "studentup-slider.js")],
                          capture_output=True, text=True)
    assert proc.returncode == 0, f"slider JS syntax tappu: {proc.stderr[-200:]}"

    fns = read(THEME / "functions.php")
    assert "inc/slider.php" in fns, "functions.php slider.php require cheyyaledu"
    assert "studentup-slider" in fns and "studentup-slider.js" in fns, "enqueue ledu"
    assert re.search(r"is_front_page\(\)[^{]*\{[^}]*studentup-slider", fns, re.S), \
        "enqueue front-page gate ledu"

    demo = read(DEMO)
    assert "assets/js/studentup-slider.js" in demo, "demo shipped JS ni load cheyyatledu"
    assert "setInterval(slideNext" not in demo, "demo lo inline slider copy inka undi"
    assert 'class="su-hact su-hact--breaking"' in demo, "demo breaking chip class kaadu"
    assert "style=\"border-color:#fca5a5" not in demo, "demo chip lo inline style inka undi"
    demop = plain(demo)
    for label in CHIPS:
        assert plain(label) in demop, f"demo lo chip ledu: {label}"
    # demo kuda live hero ne chupinchali: trending strip + state bar + workspace
    for needle in ('class="su-trend"', 'class="su-trend-list"', 'class="su-statebar"',
                   'data-su-state-bar', "My Workspace"):
        assert needle in demo, f"demo hero lo ledu: {needle}"


# ----------------------------------------------------------------- P4 order
def test_p4_front_page_order_and_single_h1() -> None:
    """Ticker → hero → slider order + page 1 ki okkate visible h1."""
    fp = read(THEME / "front-page.php")
    i_tick = fp.index("studentup_latest_ticker()")
    i_hero = fp.index("studentup_hero_premium()")
    assert i_tick < i_hero, "ticker hero kanna mundu undali (demo order)"
    assert "studentup_latest_notifications()" in fp, "slider call ledu"
    assert i_hero < fp.index("studentup_latest_notifications()"), \
        "slider hero tarvate undali"
    i_p2 = fp.index("$su_is_p2")
    assert fp.index("studentup_latest_notifications()") > i_p2, \
        "slider page-1 branch lo ledu (page 2 ki vaddu)"
    i_h1 = fp.index("<h1")
    gate = fp.rfind("$su_is_p2", 0, i_h1)
    assert gate != -1 and i_h1 - gate < 260, \
        "sr-only <h1> page-2 gate lopala ledu (page 1 double h1 avutundi)"
    assert fp.count("<h1") == 1, f"front-page.php lo {fp.count('<h1')} <h1> (okkate kavali)"


# ------------------------------------------------------------- P5 CSS/docs
def test_p5_css_docs_zip() -> None:
    """Kotha markup classes ki nijamaina rules + README + fresh zip."""
    css = read(THEME / "assets" / "css" / "worldclass.css")
    for sel in (".su-hact--breaking", ".su-slider-sec", ".su-slider-track",
                ".su-slider-viewport", ".su-scard", ".su-slider-ctrls"):
        assert sel in css, f"CSS rule ledu: {sel}"
    # trending strip + state bar rules premium.css lo — demo kuda adi load chestundi
    prem_css = read(THEME / "assets" / "css" / "premium.css")
    for sel in (".su-trend{", ".su-statebar{"):
        assert sel in prem_css, f"premium.css rule ledu: {sel}"
    demo_html = read(DEMO)
    assert "assets/css/premium.css" in demo_html, \
        "demo premium.css load cheyyatledu (live CSS stack parity ledu)"
    # breaking chip colour + dark mode
    assert re.search(r"\.su-hact--breaking\{[^}]*#b91c1c", css), "chip AA colour ledu"
    assert "body.dark .su-hact--breaking" in css, "chip dark-mode rule ledu"

    readme = read(ROOT / "README.md")
    assert "v201 — Preview ↔ live parity" in readme, "README lo v201 section ledu"
    assert "studentup_latest_notifications" in readme, "README lo slider doc ledu"
    assert "Honest remaining differences" in readme, "honest differences list ledu"

    ver = re.search(r"Version:\s*(\S+)", read(THEME / "style.css")).group(1)
    with zipfile.ZipFile(ZIP) as zf:
        names = zf.namelist()
        assert "studentup/inc/slider.php" in names, "zip lo slider.php ledu"
        assert "studentup/assets/js/studentup-slider.js" in names, "zip lo slider JS ledu"
        css_in_zip = zf.read("studentup/style.css").decode()
    assert f"Version: {ver}" in css_in_zip, "zip version mismatch"


ALL = [v for k, v in sorted(globals().items())
       if k.startswith("test_") and callable(v)]

if __name__ == "__main__":
    print("=" * 74)
    print("  v201 — PREVIEW ↔ LIVE PARITY (hero · slider · shipped JS · order)")
    print("=" * 74)
    for fn in ALL:
        fn()
        print(f"  ✔ {fn.__name__}")
    print("-" * 74)
    print(f"  v201: {len(ALL)}/{len(ALL)} checks passed ✔")
    print("=" * 74)
