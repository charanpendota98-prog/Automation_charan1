# -*- coding: utf-8 -*-
"""v79 tests — AUTHOR + MID-ARTICLE JOIN + MISS-AUDIT CLOSE.

Enduku idi:
  "Author kuda unte best kada? Blogs madhyalo Telegram/WhatsApp join isthava?
  Inka em miss avuthunnama?" — audit chesamu: author box basic (emoji, Person
  ledu) · mid-article join LEDU (footer lo matrame) · single.php lo tags +
  prev/next LEVU. v79 = anni close (existing join reuse, kotha duplicate kaadu).

Checks (offline only):
  * inline join: div-only (no <p>/<h2> — ad math + TOC safe) · same social opts
  * injector: priority 12 (ad 20 kanna mundhu) · guards (singular/loop/query/feed)
    option gate · once-guard · 2nd para position
  * author upgrade: logo avatar + Person schema + jobTitle + reviewed + follow
  * single: the_tags + prev/next nav (v64 pins hold: author_box + last_updated)
  * CSS: join-inline + author img + tags + post-nav + dark variants
  * no-dummy: join links = studentup_social_links() (option-driven, kotha hardcode ledu)
  * miss-audit: progress + crumbs + reading-time + share + trust + author +
    comments + related + tags + nav + TOC-opt + join (single surface complete)
  * options: join_cta_inline registered (default 1)
  * php lint: cta/author-box/single parse (node php parser unte; lekapothe SKIP-safe)
  * docs: README v79 + MANUAL PART 38 + 71/71

Run: python tests/v79_test.py   (also via python run.py --test-all)
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

THEME = ROOT / "wordpress-theme" / "studentup"


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


# ------------------------------------------------- 1-2. inline join

def test_inline_join_markup():
    cta = read(THEME / "inc" / "cta.php")
    assert "function studentup_cta_join_inline()" in cta
    assert "function studentup_inject_join_cta(" in cta
    body = cta.split("function studentup_cta_join_inline()")[1].split(
        "function studentup_inject_join_cta(")[0]
    assert "<p" not in body, "join strip lo <p> unte ad position break"
    assert "<h2" not in body, "join strip lo <h2> unte TOC pollute"
    assert "su-join-inline" in body and "su-join-wa" in body
    assert "su-join-tg" in body
    assert "studentup_social_links()" in body, "same options reuse avvali"
    print("  inline join: div-only + no-h2 + same social opts ✔")


def test_injector_rules():
    cta = read(THEME / "inc" / "cta.php")
    assert "add_filter( 'the_content', 'studentup_inject_join_cta', 12 )" in cta
    ads = read(THEME / "inc" / "ads.php")
    assert "studentup_inject_in_article_ad', 20" in ads, "ad priority 20 hold?"
    fn = cta.split("function studentup_inject_join_cta(")[1].split(
        "add_filter( 'the_content', 'studentup_inject_join_cta'")[0]
    for guard in ("is_singular( 'post' )", "in_the_loop()", "is_main_query()",
                  "is_feed()", "join_cta_inline', '1'", "su-join-inline' )",
                  "explode( '</p>', $content, 3 )"):
        assert guard in fn, f"injector guard ledu: {guard}"
    print("  injector: prio 12 + guards + option + 2nd-para ✔")


# ------------------------------------------------- 3-4. author + single

def test_author_upgrade():
    box = read(THEME / "inc" / "author-box.php")
    for needle in ("get_theme_mod( 'custom_logo' )", "get_site_icon_url",
                   '"https://schema.org/Person"', 'itemprop="jobTitle"',
                   "Reviewed:", "$soc['telegram']", "$soc['whatsapp']",
                   "Report mistakes", "Editorial policy",
                   '"https://schema.org/Organization"'):
        assert needle in box, f"author needle ledu: {needle}"
    print("  author: logo + Person + reviewed + follow ✔")


def test_single_complete():
    single = read(THEME / "single.php")
    for needle in ("the_tags(", "previous_post_link(", "next_post_link(",
                   "studentup_author_box()", "studentup_last_updated()",
                   "su-progress", "studentup_breadcrumbs()",
                   "studentup_reading_time()", 'class="share"',
                   "studentup_trust_note()", "comments_template()",
                   "su-tags", "post-nav"):
        assert needle in single, f"single needle ledu: {needle}"
    print("  single: tags + prev/next + v64 pins hold ✔")


# ------------------------------------------------- 5-6. css + no-dummy

def test_css_v79():
    css = read(THEME / "style.css")
    for needle in (".su-join-inline{", ".su-join-inline-btns a{",
                   "body.dark .su-join-inline{", ".su-author-avatar img{",
                   ".su-tags{", ".post-nav{", "body.dark .post-nav a{"):
        assert needle in css, f"CSS needle ledu: {needle}"
    print("  CSS: join strip + author img + tags + nav + dark ✔")


def test_no_dummy_links():
    cta = read(THEME / "inc" / "cta.php")
    inline = cta.split("function studentup_cta_join_inline()")[1].split(
        "function studentup_inject_join_cta(")[0]
    assert "t.me/" not in inline and "wa.me/" not in inline, \
        "hardcoded join links = dummy risk (options nunchi ravali)"
    box = read(THEME / "inc" / "author-box.php")
    assert "t.me/" not in box and "wa.me/" not in box
    print("  no-dummy: join/follow links 100% option-driven ✔")


# ------------------------------------------------- 7-8. audit + options

def test_miss_audit_surface():
    single = read(THEME / "single.php")
    surface = {"progress": "su-progress", "crumbs": "studentup_breadcrumbs",
               "read time": "studentup_reading_time",
               "mid ad": "studentup_ad( 'mid' )", "share": 'class="share"',
               "trust": "studentup_trust_note",
               "author": "studentup_author_box", "tags": "the_tags(",
               "prev/next": "post-nav", "comments": "comments_template",
               "related": "WP_Query", "last-date badge": "studentup_last_date_badge",
               "qual": "studentup_qual_labels"}
    missing = [k for k, v in surface.items() if v not in single]
    assert not missing, f"single surface miss: {missing}"
    cta = read(THEME / "inc" / "cta.php")
    assert "studentup_cta_join()" in cta and "studentup_cta_join_inline()" in cta
    print("  miss-audit: single surface 13/13 + join x2 ✔")


def test_options_registered():
    opts = read(THEME / "inc" / "options.php")
    assert "'join_cta_inline'" in opts
    assert "'social_whatsapp'" in opts and "'social_telegram'" in opts
    print("  options: join_cta_inline + socials registered ✔")


# ------------------------------------------------- 9-10. lint + docs

def test_php_parse():
    import shutil
    import subprocess

    if shutil.which("php") is None:
        print("  php lint: SKIP (php ledu, CI lo 32/32 gate undi) ✔")
        return
    for f in ("inc/cta.php", "inc/author-box.php", "single.php",
              "inc/options.php"):
        r = subprocess.run(["php", "-l", str(THEME / f)], capture_output=True,
                           text=True, timeout=30)
        assert r.returncode == 0, f"{f}: {r.stderr or r.stdout}"
    print("  php -l: cta + author-box + single + options ✔")


def test_docs_v79():
    suites = len(list((ROOT / "tests").glob("*_test.py")))
    assert suites == 96, f"suites {suites} (v116 tho 96 expect)"
    readme = read(ROOT / "README.md")
    manual = read(ROOT / "MANUAL_ADVANCED_CHECKLIST.md")
    go_live = read(ROOT / "GO_LIVE_CHECKLIST.md")
    assert "### v79" in readme and "71/71" in readme
    assert "PART 38" in manual and "v79" in manual and "71/71" in manual
    assert "71/71" in go_live
    for name, txt in (("README", readme), ("MANUAL", manual),
                      ("GO_LIVE", go_live)):
        assert "164/164" in txt, f"{name} lo jsdom claim poyindi"
    print("  docs: README v79 + MANUAL PART 38 + 71/71 ✔")


TESTS = [
    ("inline join markup", test_inline_join_markup),
    ("injector rules", test_injector_rules),
    ("author upgrade", test_author_upgrade),
    ("single complete", test_single_complete),
    ("CSS v79", test_css_v79),
    ("no-dummy links", test_no_dummy_links),
    ("miss-audit surface", test_miss_audit_surface),
    ("options registered", test_options_registered),
    ("php parse", test_php_parse),
    ("docs: v79 + PART 38 + 71/71", test_docs_v79),
]


def main() -> None:
    print("=" * 70)
    print("  v79 — AUTHOR + MID-ARTICLE JOIN + MISS-AUDIT CLOSE")
    print("=" * 70)
    failed = 0
    for name, fn in TESTS:
        try:
            fn()  # fns print their own proof line on success
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
    print("ALL v79 AUTHOR + JOIN TESTS PASSED ✔")


if __name__ == "__main__":
    main()
