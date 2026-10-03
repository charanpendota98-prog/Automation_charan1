# -*- coding: utf-8 -*-
"""v198 — TOOLS ADVANCED (owner ask, 2026-10-03).

Owner: "Tools em avasaram ledu [on home], tools and UI advanced ga vundali,
neat ga, phone lo easy ga click vachelaga plan cheyu and advanced ga".

Ee suite aa naalugu nibandhanalu permanent gate ga marchindi:

  C1  THEME hub — 8 tools, finder + chips + sticky strip + swipe wrapper,
      per-tool formula/source (E-E-A-T), "next tool", back-to-top, no-JS
      fallback, anni escaped.
  C2  ENGINE    — assets/js/studentup-tools.js: tab selection, steppers,
      copy/share/print/reset, deep link (?tool=), swipe, "/" shortcut,
      no dependencies, no network, no personal data.
  C3  WIRING    — tools engine tool page ki mattrame enqueue; home lo tools
      section asalu ledu (owner rule).
  C4  CSS       — sticky strip, 48px taps, one-column phone fields, dark mode,
      print (results on paper), focus ring, reduced-motion.
  C5  PREVIEW   — pin-to-pin classes/data attributes, engine **inline from the
      theme file** (copy kaadu), English-only, 8 tools each with a result.
  C6  NO-JS     — engine lenu aina anni tools kanipistayi (noscript), page
      content server-rendered.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
THEME = ROOT / "wordpress-theme" / "studentup"
ENGINE = THEME / "assets" / "js" / "studentup-tools.js"
TOOLS = ROOT / "preview" / "tools" / "index.html"
TE = re.compile(r"[\u0C00-\u0C7F]")


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="ignore")


# ------------------------------------------------------------------- C1 theme
def test_c1_theme_hub() -> None:
    """Hub markup: 8 tools · finder · chips · sticky strip · swipe · E-E-A-T."""
    s = read(THEME / "inc" / "premium.php")
    assert "function studentup_tools_tabs()" in s, "hub ledu"
    assert 'data-su-tools' in s, "engine hook (data-su-tools) ledu"
    assert 'data-su-tool-find' in s and 'data-su-tool-clear' in s, "finder ledu"
    assert 'class="su-toolcats"' in s and 'data-su-tool-cat' in s, "category chips ledu"
    assert 'data-su-tool-strip' in s, "sticky strip hook ledu"
    assert 'data-su-tool-swipe' in s, "swipe wrapper ledu"
    assert 'data-su-tool-top' in s, "back-to-top button ledu"
    assert 'data-su-next' in s, "next tool button ledu"
    assert 'data-su-tool-none' in s and 'data-su-tool-q' in s, "empty state ledu"
    # per-tool metadata (formula + source) for every tool
    assert s.count("'formula' =>") == 8, "formula lines 8 kaavali"
    assert s.count("'source' =>") == 8, "source lines 8 kaavali"
    assert s.count("'keys' =>") == 8, "search keywords 8 kaavali"
    assert s.count("'cat' =>") == 8, "category 8 kaavali"
    assert 'data-su-formula="<?php echo esc_attr' in s, "formula escape ledu"
    assert 'data-su-source="<?php echo esc_attr' in s, "source escape ledu"
    # no-JS safety + escaping hygiene
    assert "<noscript><style>.su-toolpanel[hidden]{display:block!important}" in s, "noscript fallback ledu"
    assert "esc_html_e(" in s and "esc_attr(" in s, "i18n escaping ledu"
    for bad in ("echo $", "<?php echo  $"):
        assert bad not in s.replace("<?php echo studentup_ui_icon", ""), f"raw echo: {bad}"
    print("  C1. theme hub: 8 tools · finder · chips · sticky · swipe · formula+source · noscript ✔")


# ------------------------------------------------------------------ C2 engine
def test_c2_engine() -> None:
    """The engine: selection · steppers · actions · deep link · swipe · safety."""
    assert ENGINE.exists(), "assets/js/studentup-tools.js ledu"
    js = read(ENGINE)
    for needle, why in (
        ("function select(", "tab selection"),
        ("data-su-step-done", "stepper wiring"),
        ("su-tstep-minus", "decrement button"),
        ("Copy result", "copy action"),
        ("navigator.share", "native share"),
        ("window.print", "print action"),
        ("Reset", "reset action"),
        ("history.replaceState", "shareable ?tool= link"),
        ("popstate", "back/forward support"),
        ("touchstart", "swipe detection"),
        ("data-su-tool-cat", "category filter"),
        ("prefers-reduced-motion", "reduced motion"),
        ("Decrease", "a11y labels on steppers"),
    ):
        assert needle in js, f"engine lo {why} ledu"
    # dependency-free + privacy + performance
    # `$(` = our own querySelector helper (function $(sel, root)); jQuery kosam
    # gate: `jQuery` string ledu + `$.ajax`/`$(document).ready` ledu.
    assert "jQuery" not in js and "$.ajax" not in js and "$(document)" not in js, "jQuery vaddhu"
    assert "fetch(" not in js and "XMLHttpRequest" not in js, "network call vaddhu"
    assert "localStorage" not in js, "tools engine emi store cheyyakoodadu"
    assert "{ passive: true }" in js, "scroll/touch listeners passive kaavu"
    # every visible panel gets the same treatment
    assert "tabs.forEach(function (t)" in js, "per-tab wiring ledu"
    assert "addSteppers(p)" in js and "addHow(p)" in js and "addActions(p" in js, "panel enhancements ledu"
    assert len(js.encode()) < 26000, f"engine peddadi ({len(js.encode())} B)"
    print("  C2. engine: select · steppers · copy/share/print/reset · ?tool= · swipe · no deps ✔")


# ------------------------------------------------------------------- C3 wiring
def test_c3_wiring_and_rule() -> None:
    """Engine enqueued on the tools page only; home has no tools section."""
    fns = read(THEME / "functions.php")
    assert "is_page_template( 'page-tools.php' )" in fns, "tools page gate ledu"
    assert "studentup-tools.js" in fns, "engine enqueue ledu"
    assert fns.index("is_page_template( 'page-tools.php' )") < fns.index("studentup-tools.js"), \
        "enqueue gate tarvata undali"
    # tools never on the home (owner rule) — home has quiz/poll only
    fp = read(THEME / "front-page.php")
    assert "studentup_tools_tabs" not in fp, "home lo tools wall tirigi vachindi!"
    assert "studentup_salary_calc" not in fp and "studentup_age_calculator_block" not in fp, \
        "home lo calculators tirigi vachayi"
    assert "studentup_daily_quiz(" in fp, "home lo quiz undali (engagement)"
    page = read(THEME / "page-tools.php")
    assert "studentup_tools_tabs()" in page, "tools page lo hub ledu"
    print("  C3. wiring: engine tools-page only · home clean (no tools wall) ✔")


# ---------------------------------------------------------------------- C4 css
def test_c4_css() -> None:
    """Phone-first: sticky strip, 48px taps, single column, dark, print."""
    css = read(THEME / "assets" / "css" / "worldclass.css")
    assert "--tap-lg:48px" in css, "48px tap token ledu"
    assert re.search(r"\.su-tooltabs\{[^}]*position:sticky", css), "sticky strip ledu"
    assert "scroll-snap-type:x mandatory" in css, "strip snap ledu"
    assert ".su-tstep-btn{" in css and "var(--tap-lg)" in css, "stepper tap size ledu"
    assert ".su-tools{ overflow:visible }" in css, "sticky ni clip chestundi (overflow fix)"
    assert "@media(max-width:620px)" in css and ".su-fields{ grid-template-columns:1fr" in css, \
        "phone lo one-column fields ledu"
    assert "@media print" in css and ".su-tooltabs,.su-toolcats,.su-toolfind" in css, "print rules ledu"
    assert "body.dark .su-tstep-btn" in css, "dark mode ledu"
    assert ":focus-visible" in css, "focus ring ledu"
    assert "@media(prefers-reduced-motion:reduce)" in css, "reduced motion ledu"
    assert ".su-tool-how" in css and ".su-tool-actions" in css, "results/how styles ledu"
    # critical layer stays small: tools-only selectors inline lo vaddhu
    crit = read(THEME / "assets" / "css" / "critical.css")
    for tok in (".su-tstep", ".su-toolfind", ".su-tcat"):
        assert tok not in crit, f"inline critical lo tools token undi: {tok}"
    print("  C4. css: sticky · 48px · one-column phone · dark · print · focus · reduced-motion ✔")


# ------------------------------------------------------------------ C5 preview
def test_c5_preview_parity() -> None:
    """Preview = theme classes/attrs + the same engine file, English-only."""
    assert TOOLS.exists(), "preview/tools/index.html ledu"
    html = read(TOOLS)
    for needle in ('data-su-tools', 'data-su-tool-find', 'class="su-toolcats"',
                   'data-su-tool-strip', 'data-su-tool-swipe', 'data-su-tool-top',
                   'data-su-next', 'data-su-tool-none', 'data-su-formula=', 'data-su-source='):
        assert needle in html, f"preview lo theme markup ledu: {needle}"
    assert html.count('class="su-ttab') == 8, "preview lo 8 tabs ledu"
    assert html.count('class="su-toolpanel') == 9, "preview lo 8 panels + wrapper ledu"
    assert html.count("data-su-result") >= 9, "result hooks ledu"
    assert html.count('data-su-tool-cat="') >= 6, "chips ledu"
    assert "<noscript><style>.su-toolpanel[hidden]" in html, "preview no-JS fallback ledu"
    # the engine on the page IS the theme file (single source of truth)
    engine = read(ENGINE)
    assert engine in html, "preview engine theme file kaadu (copy drift!)"
    assert not TE.search(re.search(r"<main[\s\S]*?</main>", html).group(0)), \
        "tools page main content lo Telugu undi (English UI rule)"
    # theme parity of the fields the engine enhances
    for tok in ("su-tstep", "su-tact", "su-tnext", "su-tool-how"):
        assert tok in read(ENGINE) or tok in read(THEME / "assets" / "css" / "worldclass.css"), tok
    print("  C5. preview: pin-to-pin markup · engine inline (single source) · English · 8 tools ✔")


# -------------------------------------------------------------------- C6 no-JS
def test_c6_no_js_and_budget() -> None:
    """JS lekapote anni tools kanipistayi; engine chinnadi + tool page ki mattrame."""
    hub_php = read(THEME / "inc" / "premium.php")
    assert "noscript" in hub_php and "display:block!important" in hub_php, "no-JS display ledu"
    html = read(TOOLS)
    assert re.search(r'<div class="su-toolpanel[^"]*"[^>]* hidden>', html), \
        "panels server-side hidden ga levu (no-JS lo anni kanipinchali)"
    assert html.count('value="18000"') == 1 and 'value="200"' in html, \
        "inputs server-rendered defaults ledu"
    # engine budget: 4 HTTP requests per page max on tools (css already counted), JS tiny
    size = len(read(ENGINE).encode())
    assert size < 26000, f"engine {size} B — budget fail"
    print(f"  C6. no-JS: fallback present · defaults server-rendered · engine {size} B ✔")


# ------------------------------------------------- v120 utilities (regression)
def test_c7_reader_utils_restored() -> None:
    """v198 lo tools engine rewrite valla v120 reader utilities (compare ·
    reminder .ics · print · text-size · in-article calculators) pogakoodadu —
    adi single post + card buttons ki JS. Separate file + enqueue gate ikkada."""
    ru = THEME / "assets" / "js" / "studentup-reader-utils.js"
    assert ru.exists(), "studentup-reader-utils.js ledu (compare/reminder/print dead!)"
    js = read(ru)
    for needle, why in (
        ("data-su-compare", "compare rail"),
        ("data-su-reminder", "reminder .ics"),
        ("data-su-print", "print/PDF"),
        ("data-su-font", "text size buttons"),
        ("su-calc-age-btn", "in-article age calc"),
        ("su-calc-fee-btn", "in-article fee calc"),
        ("syllabus-tracker", "syllabus tracker"),
        ("studentup:compare-refresh", "smart-search ↔ compare bridge"),
    ):
        assert needle in js, f"reader util ledu: {why}"
    tools_php = read(THEME / "inc" / "student-tools.php")
    assert "studentup-reader-utils.js" in tools_php, "reader utils enqueue ledu"
    assert "'studentup-reader'" in tools_php, "handle studentup-reader ledu"
    assert "STUDENTUP_TOOLS" in tools_php and "wp_localize_script(" in tools_php, "localize ledu"
    assert "array( 'studentup-reader' )" in tools_php, "opportunities dependency ledu"
    # hub engine (tools page) + reader layer clash avvakoodadu
    hub = read(ENGINE)
    assert '.su-tools[data-su-tools]' in hub, "hub selector scope ledu (student-tools clash)"
    prem = read(THEME / "assets" / "js" / "studentup-premium.js")
    assert 'if (strip.hasAttribute("data-su-tool-strip")) return;' in prem, \
        "premium.js double-handling guard ledu"
    # enqueue separation: hub = tools page · reader = everywhere
    fns = read(THEME / "functions.php")
    assert "'studentup-reader'," in fns, "reader defer list lo ledu"
    print("  C7. v120 reader utils: restored (compare · reminder · print · text size · calculators) ✔")


# ------------------------------------------------------- C8 kit + setup single
def test_c8_setup_all_and_kit() -> None:
    """v198: okka setup file (theme + bot) + kit fresh (puratana zip footgun ledu)."""
    setup = read(ROOT / "SETUP_ALL.md")
    for needle in ("studentup-theme-1.9.39.zip", "studentup-bot-cron.zip",
                   "Run setup now", "--verify-deploy", "WP_APP_PASSWORD",
                   "GEMINI_API_KEYS", "AUTO_PUBLISH_DAILY", "0 7 * * *",
                   "30 6 * * *", "sha256", "rollback", "1.9.39"):
        assert needle in setup, f"SETUP_ALL.md lo ledu: {needle}"
    assert "--check-wp" in setup and "--daily --daily-no-send" in setup, "verify steps ledu"
    assert "wp-cli cron event run" in setup, "WP-cron warning ledu"
    # kit builder: stale zip purge + v197/v198 module requirements
    kit = read(ROOT / "tools" / "build_milesweb_kit.py")
    for needle in ("autoblog/publish_lane.py", "autoblog/engage_push.py",
                   "autoblog/deploy_verify.py", "studentup-reader-utils.js",
                   'glob("studentup-*.zip")', "DEPLOY_v197.md"):
        assert needle in kit, f"kit builder lo ledu: {needle}"
    print("  C8. setup-all file + kit freshness (stale zip purge · v197/v198 modules) ✔")


ALL = [v for k, v in sorted(globals().items())
       if k.startswith("test_") and callable(v)]

if __name__ == "__main__":
    print("=" * 74)
    print("  v198 — TOOLS ADVANCED (neat · phone-first · zero guesswork)")
    print("=" * 74)
    for fn in ALL:
        fn()
    print("-" * 74)
    print(f"  v198: {len(ALL)}/{len(ALL)} checks passed ✔")
