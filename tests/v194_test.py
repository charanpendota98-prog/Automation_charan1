# -*- coding: utf-8 -*-
"""v194 — LIVE AUDIT FIXES (studentup.in, 2026-10-03) — offline gates.

Audit lo kanipinchina, **code nunchi** fix cheyyagaligina defects ki permanent
regression gate. Prathi defect ki: enti jarigindi → enduku risk → ippudu gate.

  1. Policy pages lo "This page was created automatically when the StudentUp
     theme was activated … before applying to any ad network" template note.
     AdSense reviewer idi chusi "untouched template" ani reject chestadu.
  2. Students Internet Center (paid offline service) disclosure publisher
     content nunchi separate ga ledu → monetisation-policy clarity gate.
  3. Duplicate policy pages (/privacy/ vs /privacy-policy/ vs -2 · /terms/ vs
     /terms-conditions/ · /contact/ vs /contact-us/) → thin duplicate content.
     One-click repair: duplicate = DRAFT (delete kaadu).
  4. Public byline lo "Source-backed draft; verify the official notice" →
     reader ki draft, reviewer ki auto-generated content signal.
  5. Featured/inline image alt brand "studentup.in" → TTS "studentup dot in"
     (keyword stuffing). Ippudu "StudentUp".
  6. Demo/junk pages (Lorem ipsum blocks, /3452-2/ internal checklist) index
     avutunnayi → noindex + attachment 301 + empty-search noindex.

Ee suite offline (network ledu), PHP execute cheyyadu — source-level gates.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
THEME = ROOT / "wordpress-theme" / "studentup"
sys.path.insert(0, str(ROOT))


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def theme_php_text() -> str:
    """Anni theme PHP files okate blob ga (site-wide grep gates ki)."""
    return "\n".join(
        f.read_text(encoding="utf-8", errors="ignore")
        for f in sorted(THEME.rglob("*.php"))
    )


# ---------------------------------------------------------------- 1. template note
def test_no_template_placeholder_note() -> None:
    """Defect 1: auto-created placeholder note RENDER avvakudadu.

    Note: repair function lopala idi search-needle ga untundi (${'$'}stale) —
    anduke rule: phrase unna line '$stale' assignment matrame avvali, HTML
    output lo (e.g. '<p>' . $stale) asalu undakudadu.
    """
    needle = "created automatically when the StudentUp theme was activated"
    others = [f for f in sorted(THEME.rglob("*.php"))
              if f.name != "firstrun.php"]
    for f in others:
        assert needle not in f.read_text(encoding="utf-8", errors="ignore"), \
            f"{f.name} lo placeholder note undi"
    first = read(THEME / "inc" / "firstrun.php")
    bad = [ln.strip() for ln in first.splitlines()
           if needle in ln and not ln.strip().startswith("$stale")]
    assert not bad, f"note HTML output lo undi: {bad}"
    # page body builder + service block lo note asalu undakudadu (removal code
    # reply function lo matrame undali — adi delete cheyyadaniki, chupinchadaniki kaadu)
    body_fn = first.split("function studentup_setup_page_body", 1)[1] \
        .split("function studentup_repair_pages_run", 1)[0]
    assert needle not in body_fn, "page body builder lo note undi"
    assert "$base = '';" in body_fn, "page body builder $base khali kaadu"
    for phrase in ("before applying to any ad network",
                   "Please replace this text with your own details"):
        assert phrase not in read(THEME / "inc" / "firstrun.php") or \
            f"$stale2" in first, phrase
    assert "$base = '';" in first, "firstrun $base khali kaadu"
    assert "(undefined)" not in body_fn, "page body builder lo (undefined) artefact undi"
    # built preview pages lo kuda note undakudadu
    for page in sorted((ROOT / "preview" / "pages").glob("*.html")):
        assert needle not in page.read_text(encoding="utf-8", errors="ignore"), \
            f"{page.name} lo placeholder note undi"
    print("  1. policy template note: render path lo 0 occurrences · $base khali ✔")


# ---------------------------------------------------------------- 2. service block
def test_service_disclosure_separated() -> None:
    """Defect 2: paid offline service disclosure — publisher content nunchi separate."""
    first = read(THEME / "inc" / "firstrun.php")
    assert "function studentup_setup_service_block()" in first, "service block helper ledu"
    assert "Students Internet Center" in first, "service disclosure text ledu"
    # 4 point clarity: optional · free content · WhatsApp service-only · official notice
    assert "optional" in first and "free to read" in first, "optional/free clarity ledu"
    assert "Only for that offline service" in first, "service-only WhatsApp scope ledu"
    assert "official notification" in first, "official-notice line ledu"
    assert "nofollow noopener" in first, "WhatsApp link rel safety ledu"
    assert re.search(r"if \( '' === \$wa \) \{\s*return '';", first), "khali WA guard ledu"
    # policy pages ki attach (About/Privacy kuda — live lo adi miss ayindi)
    assert "in_array( $slug, array( 'about', 'contact', 'privacy'" in first, \
        "policy page list ki service block attach ledu"
    print("  2. Students Internet Center disclosure: separate · optional · service-only ✔")


# ---------------------------------------------------------------- 3. duplicate pages
def test_duplicate_page_repair() -> None:
    """Defect 3: duplicate policy pages → one-click repair (draft, never delete)."""
    first = read(THEME / "inc" / "firstrun.php")
    assert "function studentup_repair_pages_run()" in first, "repair runner ledu"
    for dup, canon in (("privacy-policy", "privacy"), ("privacy-policy-2", "privacy"),
                       ("terms-conditions", "terms"), ("contact-us", "contact")):
        assert f"'{dup}'" in first, f"duplicate map lo {dup} ledu"
        assert f"'{canon}'" in first, f"canonical {canon} ledu"
    assert "'post_status' => 'draft'" in first, "duplicate → draft ledu"
    repair = first.split("function studentup_repair_pages_run()", 1)[1]
    assert "wp_delete_post" not in repair, "repair pages ni delete chestundi (danger)"
    # admin UI: second button + handler
    assert first.count("studentup_repair_run") == 2, "repair button/handler wiring ledu"
    print("  3. duplicate pages: 4 pairs → draft · delete ledu · admin button ✔")


# ---------------------------------------------------------------- 4/5. bot copy
def test_byline_has_no_draft_wording() -> None:
    """Defect 4: public byline lo 'draft' word undakudadu."""
    from autoblog import config, seo

    src = read(ROOT / "autoblog" / "seo.py")
    # comment lines lo phrase undachu (audit reference); code/render lo undakudadu
    bad = [ln.strip() for ln in src.splitlines()
           if "Source-backed draft" in ln and not ln.strip().startswith("#")]
    assert not bad, f"byline lo draft wording code lo undi: {bad}"
    old = config.EDITORIAL_REVIEWER
    try:
        config.EDITORIAL_REVIEWER = ""
        by = seo.byline_block("ssc-cgl-2026", "Oct 3, 2026")
        assert "draft" not in by.lower(), f"byline lo draft undi: {by}"
        assert "official notification" in by, f"byline lo source-honesty line ledu: {by}"
        assert "Reviewed by" not in by, "reviewer ledu kaani reviewed claim undi"
        config.EDITORIAL_REVIEWER = "Named Editor"
        by2 = seo.byline_block("ssc-cgl-2026", "Oct 3, 2026")
        assert "Reviewed by Named Editor" in by2, "reviewer unte byline ledu"
        assert "draft" not in by2.lower()
    finally:
        config.EDITORIAL_REVIEWER = old
    print("  4. byline: draft wording 0 · honesty line + real reviewer path ✔")


def test_image_alt_brand_clean() -> None:
    """Defect 5: alt brand 'studentup.in' → 'StudentUp' (TTS keyword stuffing)."""
    from autoblog import seo

    alt = seo.image_alt("SSC CGL 2026", "Central Govt Jobs", 2026)
    assert alt.endswith("| StudentUp"), alt
    assert ".in" not in alt, f"alt lo domain undi: {alt}"
    assert seo.image_alt("SSC CGL 2026", brand="My Site").endswith("| My Site")
    # telugu-only keyword → empty line ki brand matrame (crash kaadu)
    assert seo.image_alt("", "", 0) == "StudentUp"
    print(f"  5. image alt: {alt} ✔")


# ---------------------------------------------------------------- 6. index hygiene
def test_livefix_module() -> None:
    """Defect 6: demo/junk pages noindex + attachment/empty-search cleanup."""
    live = THEME / "inc" / "livefix.php"
    assert live.exists(), "inc/livefix.php ledu"
    s = read(live)
    assert "defined( 'ABSPATH' ) || exit;" in s, "ABSPATH guard ledu"
    for marker in ("Lorem ipsum", "SEO Optimisation Checklist"):
        assert marker in s, f"demo marker {marker!r} ledu"
    assert "add_filter( 'wp_robots'" in s, "core wp_robots filter ledu"
    assert "add_filter( 'rank_math/frontend/robots'" in s, "Rank Math robots filter ledu"
    assert "$robots['noindex']" in s, "noindex set avvaledu"
    assert "is_attachment()" in s and "wp_safe_redirect" in s, "attachment 301 ledu"
    assert "is_search()" in s and "have_posts()" in s, "empty search noindex ledu"
    assert "wp_delete_post" not in s and "update_option" not in s, "livefix destructive undi"
    fn = read(THEME / "functions.php")
    assert "/inc/livefix.php" in fn, "functions.php lo livefix require ledu"
    print("  6. livefix: demo noindex · attachment 301 · empty search noindex ✔")


def test_audit_evidence_file() -> None:
    """Deliverable gate: audit report + fix guide workspace lo unnavi."""
    rep = ROOT / "LIVE_SITE_AUDIT_2026-10.md"
    guide = ROOT / "LIVE_FIX_GUIDE.md"
    assert rep.exists(), "LIVE_SITE_AUDIT_2026-10.md ledu"
    assert guide.exists(), "LIVE_FIX_GUIDE.md ledu"
    r = read(rep)
    for section in ("AdSense", "Top 50", "Launch", "Score"):
        assert section.lower() in r.lower(), f"report lo {section} section ledu"
    assert len(r) > 8000, f"report chala chinna: {len(r)} bytes"
    assert "studentup.in" in r
    print(f"  7. deliverables: audit {len(r)//1024} KB + fix guide ✔")


def main() -> None:
    print("=" * 70)
    print("  v194 — LIVE AUDIT FIXES (policy · duplicates · byline · index hygiene)")
    print("=" * 70)
    test_no_template_placeholder_note()
    test_service_disclosure_separated()
    test_duplicate_page_repair()
    test_byline_has_no_draft_wording()
    test_image_alt_brand_clean()
    test_livefix_module()
    test_audit_evidence_file()
    print("-" * 70)
    print("ALL v194 LIVE-AUDIT FIX TESTS PASSED ✔")


if __name__ == "__main__":
    main()
