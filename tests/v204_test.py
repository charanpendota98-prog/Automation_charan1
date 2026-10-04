# -*- coding: utf-8 -*-
"""v204 — compact TS/AP/Central homepage and visible grouped navigation.

Run: python3 tests/v204_test.py
"""
from __future__ import annotations

import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent.parent
THEME = ROOT / "wordpress-theme" / "studentup"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def test_homepage_is_focused_and_data_driven() -> None:
    page = read(THEME / "front-page.php")
    assert "studentup_home_opportunity_rows()" in page
    assert "studentup_breaking_section()" in page
    assert "studentup_jobs_table( 8, $su_page_rows )" in page
    assert "1 === $su_paged && $su_page_rows" not in page
    assert "$su_per_page    = 8" in page and "$su_card_rows   = array_slice( $su_page_rows, 0, 4 )" in page
    assert "foreach ( $su_card_rows as $su_row )" in page
    assert "studentup_home_opportunity_render_card( $su_row )" in page
    assert "if ( $su_page_rows )" in page
    for retired in (
        "studentup_hero_premium()", "studentup_latest_ticker()",
        "studentup_latest_notifications()", "studentup_most_used()",
        "studentup_hot_jobs()", "studentup_personal_picks()",
        "studentup_closing_week()", "studentup_popular_searches()",
        "studentup_daily_quiz()", "studentup_daily_poll()",
        "studentup_state_switch()", "studentup_trending_today()",
    ):
        assert retired not in page, f"legacy homepage module still called: {retired}"

    rows = read(THEME / "inc/opportunities.php")
    home_rows = rows[rows.index("function studentup_home_opportunity_rows"):]
    for section in ("'ts'", "'ap'", "'central'"):
        assert section in home_rows
    assert "'walkin'" not in home_rows and "'software'" not in home_rows
    assert "Not announced" in rows
    assert "function studentup_home_opportunity_render_card" in rows
    assert "function studentup_opportunity_render_card" in rows and "data-su-op-days" in rows

    table = read(THEME / "inc/jobtable.php")
    assert "studentup_home_opportunity_rows()" in table
    assert "Not announced" in table
    assert "studentup_qual_pretty( $row['qual'] )" in table
    assert "studentup_opportunity_last_date" in table
    assert "if ( ! $rows )" in table  # no empty table shell


def test_home_notice_filter_rejects_misfiled_editorial_posts() -> None:
    opportunities = read(THEME / "inc" / "opportunities.php")
    start = opportunities.index("function studentup_home_opportunity_is_notice")
    end = opportunities.index("function studentup_home_opportunity_rows", start)
    php = opportunities[start:end].lower()
    assert "studentup_opportunity_lower" in opportunities
    assert "function_exists( 'mb_strtolower' )" in opportunities
    assert "mb_strtolower( wp_strip_all_tags" not in opportunities
    assert "studentup_opportunity_category_slugs" in php
    assert "non_job_categories" in php and "editorial_or_other" in php
    assert "recruitment_signal" in php and "return (bool) preg_match" in php

    blocked_category = re.compile(
        r"scholarships?|fellowships?|internships?|results?|hall[- ]?tickets?|"
        r"software-jobs|private-jobs|current-affairs|success-stories", re.I
    )
    editorial = re.compile(
        r"\b(?:internships?|scholarships?|fellowships?|admissions?|hall[ -]?tickets?|"
        r"admit[ -]?cards?|results?|merit lists?|scorecards?|cut[ -]?offs?|answer[ -]?keys?|"
        r"selection lists?|selected candidates?|previous[ -]?(?:papers?|questions?)|"
        r"current affairs|success stories|syllab(?:us|i)|preparation|preparing|fitness|career advice|"
        r"study plan|exam tips|guide|work from home|private[ -]?(?:compan(?:y|ies)|sector|jobs?|hiring)|"
        r"mnc|bpo|top\s+\d+\s+(?:government\s+)?jobs?)\b",
        re.I,
    )
    private_company = re.compile(
        r"\b(?:infor|infosys|tcs|wipro|hcl|accenture|amazon|google|microsoft|ibm|"
        r"deloitte|cognizant|capgemini|tech mahindra|zoho|oracle|flipkart)\b", re.I
    )
    notice = re.compile(
        r"\b(?:recruit(?:ment|ing)?|notification|vacanc(?:y|ies)|apply(?: online)?|"
        r"application|posts?|openings?|hiring|exam(?:ination)?|selection|interviews?|tspsc|tgpsc|"
        r"appsc|upsc|ssc|rrb|ibps|sbi|nabard|railway|police|constable|sub[ -]?inspector|"
        r"group[ -]?[1-4]|teacher|forest service|defen[cs]e|army|navy)\b", re.I
    )

    def accepted(title: str, categories: tuple[str, ...] = ("central-govt-jobs",)) -> bool:
        return not any(blocked_category.search(c) for c in categories) and not editorial.search(title) \
            and not private_company.search(title) and bool(notice.search(title))

    assert accepted("UPSC Indian Forest Service Exam 2026 — Complete Details")
    assert accepted("Telangana Police Constable Interview Schedule 2026")
    for title in (
        "Infor Recruitment 2026: Software Engineer — Best Guide",
        "Private Company Recruitment 2026: Sales Executive openings",
        "MNC Hiring 2026: Customer Support Executive",
        "UPSC merit list 2026: selected candidates",
        "Central Government exam syllabus 2026",
        "Engineering students Government Internships 2026",
        "Central Government fitness 2026: UFC-inspired preparation guide",
        "NMMS Scholarship 2026: student financial aid",
        "Hall Ticket Verification 2026: exam-center instructions",
        "TS Police SI & Constable 2026: preparation guide",
    ):
        assert not accepted(title), f"misfiled non-notice would leak to homepage: {title}"
    assert not accepted("Unspecified government careers 2026")


def test_breaking_news_is_verified_local_news_only() -> None:
    breaking = read(THEME / "inc/breaking.php")
    for tag in ("ts-state-news", "ap-state-news", "ts-district-news", "ap-district-news"):
        assert tag in breaking
    for gate in ("source_verified", "verified", "36 * HOUR_IN_SECONDS", "studentup_breaking_local_kind"):
        assert gate in breaking
    assert r"\bjobs?\b" in breaking and r"\bexam(?:ination)?\b" in breaking
    assert "studentup_breaking_items( 6 )" in breaking
    section = breaking[breaking.index("function studentup_breaking_section"):]
    assert "if ( ! $items )" in section and "return;" in section
    nav_breaking = read(THEME / "inc/nav-breaking.php")
    assert "get_posts(" not in nav_breaking
    assert "latest published posts" not in nav_breaking.lower()

    # Dedicated local-news sources classify as local, but job/exam cues always win.
    sys.path.insert(0, str(ROOT))
    from autoblog import breaking as bot_breaking  # noqa: PLC0415

    assert bot_breaking.classify_tag("Council approves new drinking-water project", "TS State News") == "ts-state-news"
    assert bot_breaking.classify_tag("TSPSC Group 1 recruitment notification", "TS State News") != "ts-state-news"
    assert bot_breaking.classify_tag("Andhra district scholarship exam results", "AP District News") != "ap-district-news"

    feed = json.loads(read(ROOT / "preview" / "data" / "breaking.json"))
    assert feed["verified_only"] is True and feed["items"] == []


def test_desktop_and_mobile_navigation_are_one_hierarchy() -> None:
    template = read(THEME / "inc/template.php")
    primary = template[template.index("function studentup_primary_job_items"):template.index("function studentup_menu_more_items")]
    assert primary.index("'ts-jobs'") < primary.index("'ap-jobs'") < primary.index("'central-jobs'")
    fallback = template[template.index("function studentup_menu_fallback"):template.index("function studentup_breadcrumbs")]
    assert fallback.index("esc_html__( 'Home'") < fallback.index("studentup_primary_job_items()")
    assert fallback.index("studentup_primary_job_items()") < fallback.index("esc_html__( 'More'")
    assert "studentup_menu_more_items()" in fallback and 'class="sub-menu"' in fallback

    header = read(THEME / "header.php")
    assert header.count('id="mpanel"') == 1, "duplicate mobile drawer markup"
    assert header.count('<nav class="su-mobile-nav"') == 1
    assert header.count('id="su-mobile-more"') == 1
    assert 'studentup_breaking_mobile_block()' not in header  # all secondary links live under More
    assert 'id="menubtn"' in header and 'class="menubtn-label">Menu</span>' in header
    assert 'studentup_breaking_items( 1 )' in template[template.index("function studentup_menu_more_items"):template.index("function studentup_menu_fallback")]
    assert "get_categories( array( 'hide_empty' => true" in template

    js = read(THEME / "assets" / "js" / "studentup-menu.js")
    assert 'getElementById("su-bnav-menu")' in js  # retained for non-home templates
    assert 'bnavMenu.setAttribute("aria-expanded"' in js
    assert 'btnLabel.textContent = open ? "Close" : "Menu"' in js
    assert 'panel.setAttribute("inert"' in js and 'panel.removeAttribute("inert")' in js
    assert 'e.key === "Escape"' in js and 'if (e.key === "Tab")' in js
    assert 'if (current) current.open = true;' in js
    assert '(current || groups[0])' not in js  # More remains collapsed by default

    common_js = read(THEME / "assets" / "js" / "studentup.js")
    assert not re.search(r"\bI\.(?:menu|close)\b", common_js)
    assert not re.search(r"^\s*(?:menu|close):\s*SUICON", common_js, re.M)
    assert "home · ts · ap · central" in read(THEME / "assets" / "css" / "worldclass.css").lower()
    assert ".header .menu-primary .su-more-menu>.sub-menu{top:100%" in read(THEME / "assets" / "css" / "worldclass.css")


def test_static_preview_is_current_and_has_live_local_links() -> None:
    preview_path = ROOT / "preview" / "index.html"
    preview = read(preview_path)
    assert "Telangana, Andhra Pradesh &amp; Central Government Jobs" in preview
    assert preview.count('id="mpanel"') == 1
    assert 'id="menubtn"' in preview and 'menubtn-label">Menu</span>' in preview
    assert 'class="su-bnav"' not in preview
    assert "breaking-mount" not in preview
    assert "No job sample data is shown in this preview." in preview
    assert "studentup-slider.js" not in preview and "studentup-smart.js" not in preview

    class Links(HTMLParser):
        def __init__(self) -> None:
            super().__init__()
            self.targets: list[str] = []

        def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
            for key, value in attrs:
                if key in {"href", "src"} and value:
                    self.targets.append(value)

    parser = Links()
    parser.feed(preview)
    for value in parser.targets:
        parsed = urlsplit(value)
        if parsed.scheme or value.startswith("#"):
            continue
        target = (preview_path.parent / parsed.path).resolve()
        assert target.exists(), f"preview local link is missing: {value}"

    server = read(ROOT / "tools" / "preview_server.py")
    assert 'DEMO = "/preview/index.html"' in server
    assert '"/preview/worldclass/index.html"' in server


def test_homepage_cleanup_deadlines_and_critical_css() -> None:
    functions = read(THEME / "functions.php")
    assert "studentup-smart.js" not in functions and "studentup-slider.js" not in functions
    footer = read(THEME / "footer.php")
    assert "if ( ! is_front_page() && ! is_home() ) { studentup_cta_section(); }" in footer
    assert "su-footer-home" in footer
    assert "! is_front_page() && ! is_home() && studentup_opt( 'pwa', '1' )" in footer
    premium = read(THEME / "inc" / "premium.php")
    bottom_nav = premium[premium.index("function studentup_bottom_nav"):premium.index("add_action( 'wp_footer', 'studentup_bottom_nav'")]
    assert "is_front_page() || is_home()" in bottom_nav
    for file in (footer, read(THEME / "inc/megamenu.php"), read(THEME / "inc/student-tools.php")):
        assert "data-su-compare" not in file
        assert "Compare Jobs</a>" not in file

    table = read(THEME / "inc/jobtable.php")
    assert "Not announced" in table
    css = read(THEME / "assets" / "css" / "worldclass.css")
    assert ".su-jt tbody tr{display:grid" in css
    assert "body.home #surail" in css and "body.front-page #surail" in css
    assert ".mpanel .su-mobile-more:not([open])>.mgroup-body{display:none!important}" in css
    assert ".header .menubtn-label{display:inline}" in css
    assert ".header .logo .mark{display:none!important}" in css
    assert ".header .logo .brand" in css and "text-shadow:none" in css
    assert "body.front-page .su-bnav" in css
    critical = read(THEME / "assets" / "css" / "critical-home.min.css")
    assert len(critical.encode("utf-8")) < 60000
    for token in ("su-home-intro", "su-op-card", "su-jt", "body.front-page #surail",
                  ".mpanel", ".mbackdrop", ".su-mobile-more", ".su-more-menu"):
        assert token in critical, f"first paint is missing menu/home rule: {token}"
    assert ".su-social" not in critical

    style = read(THEME / "style.css")
    readme = read(THEME / "readme.txt")
    functions = read(THEME / "functions.php")
    assert "Version: 1.9.44" in style
    assert "Stable tag: 1.9.44" in readme
    assert "define( 'STUDENTUP_VERSION', '1.9.44' )" in functions


def main() -> int:
    tests = [
        test_homepage_is_focused_and_data_driven,
        test_home_notice_filter_rejects_misfiled_editorial_posts,
        test_breaking_news_is_verified_local_news_only,
        test_desktop_and_mobile_navigation_are_one_hierarchy,
        test_static_preview_is_current_and_has_live_local_links,
        test_homepage_cleanup_deadlines_and_critical_css,
    ]
    for test in tests:
        test()
        print(f"  PASS {test.__name__}")
    print(f"v204: {len(tests)}/{len(tests)} focused checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
