# -*- coding: utf-8 -*-
"""v195 — A) per-template critical CSS · B) hub pages · C) author E-E-A-T pack.

User ask: "A) Telugu font subsetting + per-template critical CSS → Speed Index
fix · B) Hub pages (TS/AP/Central/Results/Scholarships) + internal links ON ·
C) Author/editorial pages + Person schema (E-E-A-T pack) — anni cheyu".

Ee suite aa moodu ni permanent gate ga marchindi:

  A. Per-template critical CSS
     · critical-home/single/archive .min.css unnavi + inline cap (<60 KB)
     · prathi file lo aa template first-paint tokens unnavi (flash ledu)
     · inc/critical-css.php context batti pick chestundi + union fallback
     · Fonts: system stack (webfont ledu → zero font delay; subset avasaram ledu)
  B. Hub pages + internal links
     · inc/hubs.php: 5 hubs plan · shortcode · ItemList/CollectionPage schema
     · firstrun lo hub pages + footer links create avutayi (idempotent)
     · autolink engine (the_content, default ON) + hub targets filter
     · empty hub → dead-end ledu (honest fallback)
  C. Author / E-E-A-T pack
     · editorial-team page + [studentup_author_profile] shortcode
     · Person schema (#founder) + ProfilePage on author archive
     · Organization.founder + ContactPoint
     · reviewer line: peru unte "Reviewed by X", lekapote date (fake claim ledu)
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
THEME = ROOT / "wordpress-theme" / "studentup"
CSS = THEME / "assets" / "css"


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="ignore")


ABSPATH_RE = re.compile(r"defined\(\s*'ABSPATH'\s*\)")


def has_abspath_guard(src: str) -> bool:
    """Both styles ok: `defined( 'ABSPATH' ) || exit;` leda if(...){exit;}."""
    return bool(ABSPATH_RE.search(src))


# ------------------------------------------------------------------ A. critical
def test_per_template_critical_files() -> None:
    """Template-wise inline CSS files unnavi + cap lopala + tokens sariyaina."""
    expects = {
        "home": (".newsgrid", ".news--lead"),
        "single": (".article-head", ".su-ab"),
        "archive": (".newsgrid", ".chip"),
    }
    for name, tokens in expects.items():
        minf = CSS / f"critical-{name}.min.css"
        raw = CSS / f"critical-{name}.css"
        assert minf.exists(), f"critical-{name}.min.css ledu (build run cheyandi)"
        assert raw.exists(), f"critical-{name}.css (raw) ledu"
        body = read(minf)
        kb = len(body.encode("utf-8")) / 1024
        assert kb < 59, f"critical-{name}.min.css {kb:.1f} KB — inline cap dhaatindi"
        assert kb > 5, f"critical-{name}.min.css {kb:.1f} KB — chala chinna (build fail?)"
        for tok in tokens:
            assert tok in body, f"critical-{name}.min.css lo {tok} ledu (first-paint flash)"
    # union (fallback) kuda undali + cap
    union = CSS / "critical.min.css"
    assert union.exists()
    assert len(read(union).encode("utf-8")) < 60000, "union inline cap dhaatindi"
    print("  A1. per-template critical CSS: home·single·archive + union, anni <59 KB ✔")


def test_critical_context_picker() -> None:
    """Theme context batti file pick chestundi + fallback chain undi."""
    php = read(THEME / "inc" / "critical-css.php")
    assert "function studentup_critical_context()" in php, "context function ledu"
    for bit in ("is_front_page()", "is_singular( 'post' )", "return 'archive';"):
        assert bit in php, f"context logic lo {bit} ledu"
    assert "critical-' . $ctx . '.min.css" in php, "per-template file path ledu"
    assert "critical.min.css" in php, "union fallback ledu"
    assert "is_readable( $specific )" in php and "elseif ( is_readable( $union ) )" in php, \
        "fallback chain ledu (file lekapote theme break avutundi)"
    assert "SCRIPT_DEBUG" in php, "SCRIPT_DEBUG safe path ledu"
    print("  A2. picker: home/single/archive + union fallback + SCRIPT_DEBUG ✔")


def test_fonts_are_system_stack() -> None:
    """No webfont = zero font delay (audit lo 'font subset' suggestion ki honest answer)."""
    for f in ("style.css", "assets/css/worldclass.css", "assets/css/premium.css"):
        body = read(THEME / f)
        assert "@font-face" not in body, f"{f} lo @font-face undi — font payload check cheyandi"
        assert "fonts.googleapis" not in body, f"{f} lo Google Fonts link undi"
    crit = read(CSS / "critical.min.css")
    assert "system-ui" in crit and "Noto Sans Telugu" in crit, "Telugu fallback stack ledu"
    print("  A3. fonts: system stack + Noto Sans Telugu fallback · 0 webfont bytes ✔")


# ---------------------------------------------------------------------- B. hubs
def test_hub_module() -> None:
    """Hub module: 5 hubs · shortcode · schema · safety."""
    hp = THEME / "inc" / "hubs.php"
    assert hp.exists(), "inc/hubs.php ledu"
    s = read(hp)
    assert has_abspath_guard(s), "ABSPATH guard ledu"
    for slug in ("ts-jobs-hub", "ap-jobs-hub", "central-jobs-hub", "results-hub", "scholarships-hub"):
        assert slug in s, f"hub plan lo {slug} ledu"
    assert "add_shortcode( 'studentup_hub'" in s, "shortcode register ledu"
    assert "studentup_hub_section" in s and "studentup_hub_card" in s, "render helpers ledu"
    # safety: sanitize + escape + cache + empty state
    assert "sanitize_title" in s and "esc_url" in s and "esc_html" in s, "escape/sanitize ledu"
    assert "set_transient(" in s and "MINUTE_IN_SECONDS" in s, "cache ledu (DB load)"
    assert "New notifications are added every day" in s, "empty-hub fallback ledu"
    assert "no_found_rows" in s, "query optimize ledu"
    # schema + autolink targets
    assert "'CollectionPage'" in s and "'ItemList'" in s, "hub schema ledu"
    assert "add_filter( 'studentup_autolink_map'" in s, "hub autolink targets ledu"
    # theme wiring
    fn = read(THEME / "functions.php")
    assert "/inc/hubs.php" in fn, "functions.php lo hubs require ledu"
    print("  B1. hubs: 5 pages · shortcode · ItemList · cache · empty-state ✔")


def test_internal_links_on() -> None:
    """Internal link engine default ON + hub targets + the_content wiring."""
    al = read(THEME / "inc" / "autolink.php")
    assert "add_filter( 'the_content', 'studentup_autolink_content', 16 )" in al, \
        "autolink the_content ki wire avvaledu"
    assert "(array) apply_filters( 'studentup_autolink_map', $map )" in al, \
        "autolink map filter ledu (hub targets add avvavu)"
    opts = read(THEME / "inc" / "options.php")
    assert "'autolink' => array( 'Auto internal links in posts', 'check', '1'" in opts, \
        "autolink default ON ledu"
    assert "'autolink_max'" in opts, "max-links option ledu"
    assert "mb_strlen( $title ) < 14" in al, "short-phrase guard ledu (spam risk)"
    # safety guards (headings/links/scripts touch cheyyadu)
    for guard in ("<a\\b", "<h[1-6]\\b", "<script\\b", "<code\\b"):
        assert guard in al, f"protected block {guard} ledu"
    print("  B2. internal links: the_content ON (default) · hub targets · guards ✔")


def test_hub_pages_created() -> None:
    """Firstrun hub + editorial pages create chestundi (idempotent) + footer links."""
    fr = read(THEME / "inc" / "firstrun.php")
    assert "function studentup_setup_hub_body" in fr, "hub body builder ledu"
    assert "studentup_setup_editorial_body" in fr, "editorial body builder ledu"
    assert "foreach ( studentup_hub_plan() as $hslug => $hinfo )" in fr, "hub create loop ledu"
    assert "get_page_by_path( 'editorial-team' )" in fr, "editorial page create ledu"
    assert "$foot_items['editorial-team']" in fr, "footer lo editorial link ledu"
    assert "get_page_by_path( $hslug ) instanceof WP_Post" in fr, "idempotent guard ledu"
    print("  B3. setup: 5 hubs + editorial page + footer links (idempotent) ✔")


# ------------------------------------------------------------- C. author E-E-A-T
def test_author_pack() -> None:
    """Author/editorial pack: profile card · shortcode · Person/ProfilePage schema."""
    ap = THEME / "inc" / "author-profile.php"
    assert ap.exists(), "inc/author-profile.php ledu"
    s = read(ap)
    assert has_abspath_guard(s), "ABSPATH guard ledu"
    assert "function studentup_author_card_data()" in s, "card data fn ledu"
    assert "add_shortcode( 'studentup_author_profile'" in s, "profile shortcode ledu"
    assert "'ProfilePage'" in s, "ProfilePage schema ledu"
    assert "'@type'       => 'Person'" in s or "'@type' => 'Person'" in s, "Person schema ledu"
    assert "'knowsAbout'" in s, "knowsAbout (expertise) ledu"
    assert "#founder" in s, "founder @id ledu"
    assert "itemprop=\"name\"" in s and "itemprop=\"jobTitle\"" in s, "microdata ledu"
    assert "How every update is verified" in s, "verification process copy ledu"
    fn = read(THEME / "functions.php")
    assert "/inc/author-profile.php" in fn, "functions.php lo author-profile require ledu"
    print("  C1. author profile: card · shortcode · Person/ProfilePage · knowsAbout ✔")


def test_organization_identity() -> None:
    """Organization.founder + editorial contactPoint + reviewer honesty."""
    sc = read(THEME / "inc" / "schema.php")
    assert "'founder'" in sc and "#founder" in sc, "Organization.founder ledu"
    assert "'ContactPoint'" in sc and "'editorial'" in sc, "editorial contactPoint ledu"
    opts = read(THEME / "inc" / "options.php")
    for key in ("author_role", "author_expertise", "author_since", "author_reviewer"):
        assert f"'{key}'" in opts, f"option {key} ledu (v195)"
    ab = read(THEME / "inc" / "author-box.php")
    assert "author_reviewer" in ab, "reviewer option use avvaledu"
    assert "Reviewed by" in ab, "reviewed-by line ledu"
    assert "esc_html_e( 'Sources verified:', 'studentup' )" in ab, \
        "reviewer lekapote honest fallback ledu"
    print("  C2. identity: founder + contactPoint + reviewer(real)/honest fallback ✔")


def test_v195_css_and_packaging() -> None:
    """New UI classes styled + raw critical files zip lo ship avvavu."""
    wc = read(CSS / "worldclass.css")
    for cls in (".su-hub-h", ".su-hub-card", ".su-ab--page", ".su-ab-steps", ".su-trust--expertise"):
        assert cls in wc, f"worldclass.css lo {cls} ledu"
    bw = read(ROOT / "tools" / "build_wp_theme.py")
    assert "critical-home.css" in bw or "critical-archive.css" in bw, \
        "PACKAGE_SKIP lo per-template raw files ledu (zip bloat)"
    plan = read(ROOT / "tools" / "build_critical_css.py")
    assert "CORE = {" in plan and "TEMPLATES = {" in plan, "builder lo CORE/TEMPLATES ledu"
    assert "use_exact=False" in plan, "template build use_exact=False ledu"
    print("  C3. css + packaging: hub/profile styles · raw critical skipped ✔")


def main() -> None:
    print("=" * 70)
    print("  v195 — A) per-template critical CSS · B) hubs · C) author E-E-A-T")
    print("=" * 70)
    test_per_template_critical_files()
    test_critical_context_picker()
    test_fonts_are_system_stack()
    test_hub_module()
    test_internal_links_on()
    test_hub_pages_created()
    test_author_pack()
    test_organization_identity()
    test_v195_css_and_packaging()
    print("-" * 70)
    print("ALL v195 TESTS PASSED ✔")


if __name__ == "__main__":
    main()
