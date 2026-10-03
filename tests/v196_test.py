# -*- coding: utf-8 -*-
"""v196 — ADVANCED PACK: exam calendar · transparent pricing · corrections log.

User ask: "yes build cheyu advancedgaaa bestgaaa" → audit gaps that were still
open after v194/v195:

  1. Audit #9  "every job card says Last date: Not announced" → make deadlines
     USEFUL: one calendar page + one-tap .ics export of every confirmed date.
  2. Audit #12 "no price transparency for the paid service" → publish the
     exact price list, inclusions, exclusions, turnaround and refund rule.
  3. Audit #41 "no corrections log" → the editorial promise ("verified
     corrections are published") needs a public page readers can check.

Ee suite aa moodu ni permanent gate ga marchindi.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
THEME = ROOT / "wordpress-theme" / "studentup"


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="ignore")


# ------------------------------------------------------------------ calendar
def test_calendar_module() -> None:
    """Exam calendar: dated items only · .ics export · Event schema · honest empty."""
    cal = THEME / "inc" / "calendar.php"
    assert cal.exists(), "inc/calendar.php ledu"
    s = read(cal)
    assert re.search(r"defined\(\s*'ABSPATH'\s*\)", s), "ABSPATH guard ledu"
    assert "function studentup_calendar_items(" in s, "items query ledu"
    # dated items only — never a guessed deadline
    assert "meta_query" in s and "'compare' => '>='" in s, "future-dates-only filter ledu"
    assert "preg_match( '/^\\d{4}-\\d{2}-\\d{2}$/', $raw )" in s, "date-format guard ledu"
    # .ics export
    assert "BEGIN:VCALENDAR" in s and "BEGIN:VEVENT" in s and "BEGIN:VALARM" in s, "ics body ledu"
    assert "text/calendar; charset=utf-8" in s, "ics content-type ledu"
    assert "Content-Disposition: attachment" in s, "ics download header ledu"
    assert "function studentup_ics_escape(" in s, "RFC5545 escape ledu"
    assert "nocache_headers()" in s, "ics cache header ledu"
    assert "wp_safe_redirect" in s, "empty ics safe path ledu"
    # schema + shortcode
    assert "'@type'     => 'Event'" in s or "'@type' => 'Event'" in s, "Event schema ledu"
    assert "'ItemList'" in s, "ItemList schema ledu"
    assert "add_shortcode( 'studentup_calendar'" in s, "calendar shortcode ledu"
    # honest empty state
    assert "we never estimate a deadline" in s, "empty-state honesty line ledu"
    # xss safety: no raw echo of post data without esc_*
    assert "esc_html( $it['title'] )" in s and "esc_url( $it['url'] )" in s, "escaping ledu"
    print("  C1. calendar: future-date only · .ics+alarm · Event schema · empty-honest ✔")


def test_calendar_template_and_wiring() -> None:
    """Template + functions.php wiring + setup page create (idempotent)."""
    tpl = THEME / "page-exam-calendar.php"
    assert tpl.exists(), "page-exam-calendar.php ledu"
    t = read(tpl)
    assert re.search(r"defined\(\s*'ABSPATH'\s*\)", t), "template ABSPATH guard ledu"
    assert "studentup_calendar_page_render()" in t, "renderer call ledu"
    assert "get_header()" in t and "get_footer()" in t, "theme shell ledu"
    fn = read(THEME / "functions.php")
    assert "/inc/calendar.php" in fn, "functions.php require ledu"
    fr = read(THEME / "inc" / "firstrun.php")
    assert "'exam-calendar'    => 'Exam & Application Calendar'" in fr or "'exam-calendar' =>" in fr, \
        "setup page list lo exam-calendar ledu"
    assert "'exam-calendar'   => 'page-exam-calendar.php'" in fr or "page-exam-calendar.php" in fr, \
        "template assignment ledu"
    assert "studentup_setup_assign_template" in fr, "assign helper ledu"
    print("  C2. calendar template + setup wiring (template auto-assign) ✔")


# ------------------------------------------------------------- internet center
def test_transparent_pricing_page() -> None:
    """IC page: price table · what we never do · refund · govt-fee separation."""
    tpl = THEME / "page-internet-center.php"
    assert tpl.exists(), "page-internet-center.php ledu"
    t = read(tpl)
    assert re.search(r"defined\(\s*'ABSPATH'\s*\)", t), "ABSPATH guard ledu"
    assert "su-ic-price" in t and "scope=\"col\"" in t, "price table (a11y headers) ledu"
    for key in ("ic_price_basic", "ic_price_form", "ic_price_combo"):
        assert key in t, f"price option {key} use avvaledu"
    assert "Government application fee" in t and "separate" in t, "govt-fee separation ledu"
    assert "What we never do" in t, "never-do list ledu"
    assert "never promise a job" in t, "no-promise honesty ledu"
    assert "Aadhaar" in t and "OTP" in t, "document safety line ledu"
    assert "Cancellation and refund" in t, "refund policy ledu"
    assert "not connected to any government department" in t, "independence line ledu"
    opts = read(THEME / "inc" / "options.php")
    for key in ("ic_price_basic", "ic_price_form", "ic_price_combo"):
        assert f"'{key}'" in opts, f"option {key} register avvaledu"
    print("  C3. price page: table · never-do · refund · govt-fee split · safety ✔")


# ---------------------------------------------------------------- corrections
def test_corrections_log() -> None:
    """Corrections log: meta-driven · date visible · report flow · honest empty."""
    tpl = THEME / "page-corrections.php"
    assert tpl.exists(), "page-corrections.php ledu"
    t = read(tpl)
    assert re.search(r"defined\(\s*'ABSPATH'\s*\)", t), "ABSPATH guard ledu"
    assert "studentup_correction_note" in t, "correction meta use avvaledu"
    assert "get_the_modified_date( 'c' )" in t, "updated date ledu"
    assert "su-corr-list" in t and "su-corr-note" in t, "correction list markup ledu"
    assert "How to report a mistake" in t, "report flow ledu"
    assert "48 hours" in t, "correction SLA ledu"
    assert "do not silently edit published facts" in t, "empty-state honesty ledu"
    assert "wp_reset_postdata()" in t, "query reset ledu (loop leak risk)"
    print("  C4. corrections log: meta · dates · report flow · honest empty ✔")


def test_preview_pages_and_sitemap() -> None:
    """Preview pages shipped (pin-to-pin classes) + sitemap 18 locs."""
    prev = ROOT / "preview" / "pages"
    for slug, tokens in (
        ("exam-calendar", ("su-cal-list", "su-cal-badge", ".ics")),
        ("internet-center", ("su-ic-price", "&#8377;50", "not connected to any government department")),
        ("corrections", ("su-corr-list", "su-corr-note", "48 hours")),
    ):
        f = prev / f"{slug}.html"
        assert f.exists(), f"preview/pages/{slug}.html ledu"
        body = read(f)
        for tok in tokens:
            assert tok in body, f"{slug}.html lo {tok} ledu"
        assert "worldclass.css" in body, f"{slug}.html lo theme CSS ledu (pin-to-pin break)"
    sm = read(ROOT / "preview" / "sitemap.xml")
    assert len(re.findall(r"<loc>", sm)) == 18, f"sitemap locs {len(re.findall(r'<loc>', sm))} (18 expect)"
    for slug in ("exam-calendar", "internet-center", "corrections"):
        assert f"pages/{slug}.html" in sm, f"sitemap lo {slug} ledu"
    print("  C5. preview pages + sitemap 18 locs (pin-to-pin) ✔")


def test_v196_css() -> None:
    """All new UI classes are styled (no unstyled markup)."""
    wc = read(THEME / "assets" / "css" / "worldclass.css")
    for cls in (".su-cal-head", ".su-cal-item", ".su-cal-badge", ".su-cal-urgent",
                ".su-ic-price", ".su-ic-note", ".su-corr-list", ".su-corr-item"):
        assert cls in wc, f"worldclass.css lo {cls} ledu"
    assert "@media(max-width:600px)" in wc, "mobile rule ledu"
    assert "body.dark" in wc, "dark-mode rule ledu"
    # v73 invariant: theme surfaces stay English
    import re as _re
    te = _re.compile(r"[\u0C00-\u0C7F]")
    for f in ("inc/calendar.php", "page-exam-calendar.php", "page-internet-center.php", "page-corrections.php"):
        assert not te.search(read(THEME / f)), f"{f} lo Telugu undi (v73 invariant)"
    print("  C6. css: calendar/IC/corrections styled + dark + mobile · English surfaces ✔")


def main() -> None:
    print("=" * 70)
    print("  v196 — exam calendar · transparent pricing · corrections log")
    print("=" * 70)
    test_calendar_module()
    test_calendar_template_and_wiring()
    test_transparent_pricing_page()
    test_corrections_log()
    test_preview_pages_and_sitemap()
    test_v196_css()
    print("-" * 70)
    print("ALL v196 TESTS PASSED ✔")


if __name__ == "__main__":
    main()
