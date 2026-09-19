# -*- coding: utf-8 -*-
"""v67 tests — DEEP AUDIT (expert/BA level) + top-theme hardening + revenue slots.

Mee requirement: "inka chala mistakes unnayi · deep audit cheyyi · expert level · BA level ·
anni fix cheyyi · theme top-most ga + highest revenue".

Ee suite aa deep audit (**tools/theme_audit_deep.py**) + v67 theme fixes ni verify chestundi:
  · deep audit 0 errors · 0 warnings (templates · security · perf · a11y · ads · standards)
  · audit **detection ability**: missing module require · dead option · eval() · screenshot dims
  · audit **string-aware comment stripper** (URLs lo `//` comment kaadu — v67 bug fix)
  · security module (headers · XML-RPC off · author enumeration · attachment redirect · flood guard)
  · top-theme files: comments.php · sidebar.php · readme.txt · languages/studentup.pot
  · revenue slots: below-content ad (6/6 positions) · sticky sidebar · POT auto-build
  · perf/a11y: preconnect · wp_robots noindex · content-visibility toggle · focus-visible · button types

Run: python tests/v67_test.py   (also via python run.py --test-all)
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

import theme_audit  # noqa: E402
import theme_audit_deep  # noqa: E402

THEME = ROOT / "wordpress-theme" / "studentup"


def read(p) -> str:
    return Path(p).read_text(encoding="utf-8")


def tpl(name: str) -> str:
    return read(THEME / name)


def test_deep_audit_clean():
    rep = theme_audit.run()
    assert rep["errors"] == [], rep["errors"]
    assert rep["warnings"] == [], rep["warnings"]
    kpi = rep.get("kpi", {})
    assert kpi.get("ad_positions") == 6, kpi
    assert not kpi.get("ad_positions_missing"), kpi
    assert kpi.get("php_files", 0) >= 27, kpi
    assert kpi.get("css_kb", 999) < 120, kpi


def _fake_theme(tmp: Path, extra_php: str = "", screenshot=None) -> None:
    (tmp / "inc").mkdir(parents=True, exist_ok=True)
    (tmp / "assets" / "js").mkdir(parents=True, exist_ok=True)
    (tmp / "functions.php").write_text(
        "<?php\nif ( ! defined( 'ABSPATH' ) ) { exit; }\n"
        "add_theme_support( 'title-tag' );\nadd_theme_support( 'post-thumbnails' );\n"
        "add_theme_support( 'html5' );\nadd_theme_support( 'responsive-embeds' );\n"
        "register_nav_menus( array( 'primary' => 'P' ) );\n"
        "require_once get_template_directory() . '/inc/options.php';\n" + extra_php,
        encoding="utf-8")
    (tmp / "inc" / "options.php").write_text(
        "<?php\nif ( ! defined( 'ABSPATH' ) ) { exit; }\n"
        "settings_fields( 'g' );\ncurrent_user_can( 'manage_options' );\n"
        "register_setting( 'g', 'studentup_ok_field', 'sanitize_text_field' );\n"
        "return array( 'ok_field' => array( 'L', 'text', '', '' ),\n"
        "              'dead_field' => array( 'D', 'text', '', '' ) );\n", encoding="utf-8")
    for name in ("header.php", "footer.php", "index.php", "single.php", "page.php",
                 "archive.php", "search.php", "404.php"):
        (tmp / name).write_text(
            "<?php\nif ( ! defined( 'ABSPATH' ) ) { exit; }\n"
            "?><html <?php language_attributes(); ?>><body <?php body_class(); ?>>"
            "<?php wp_head(); ?><?php wp_footer(); ?></body></html>\n", encoding="utf-8")
    (tmp / "style.css").write_text(
        "/*\nTheme Name: Fake\nVersion: 1.0.0\nText Domain: fake\nLicense: GPL\n"
        "Requires at least: 6.0\nRequires PHP: 7.4\n*/\n"
        ":focus-visible{outline:2px}\n.su-ad{display:block;margin:10px}\n", encoding="utf-8")
    (tmp / "theme.json").write_text(json.dumps({"version": 2, "settings": {"layout": {}}}),
                                    encoding="utf-8")
    (tmp / "assets" / "js" / "studentup.js").write_text("// js\n", encoding="utf-8")
    if screenshot is not None:
        import struct
        import zlib

        w, h = screenshot

        def chunk(tag, data):
            return (struct.pack(">I", len(data)) + tag + data
                    + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))

        ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
        row = b"\x00" + b"\x00" * (w * 3)
        raw = chunk(b"IHDR", ihdr) + chunk(b"IDAT", zlib.compress(row * h)) + chunk(b"IEND", b"")
        (tmp / "screenshot.png").write_bytes(b"\x89PNG\r\n\x1a\n" + raw)


def test_deep_audit_detects():
    """Audit nijamaina problems pattukuntunda (missing require · dead option · eval · dims)."""
    with tempfile.TemporaryDirectory() as tmp:
        t = Path(tmp)
        _fake_theme(t, extra_php="", screenshot=(1000, 800))
        (t / "inc" / "rogue.php").write_text(
            "<?php\nif ( ! defined( 'ABSPATH' ) ) { exit; }\n"
            "eval( 'echo 1;' );\nget_option( 'studentup_ok_field' );\n", encoding="utf-8")
        old = theme_audit.THEME, theme_audit_deep.THEME
        try:
            theme_audit.THEME = t
            theme_audit_deep.THEME = t
            bad = theme_audit.run()
        finally:
            theme_audit.THEME, theme_audit_deep.THEME = old
    joined = " | ".join(bad["errors"] + bad["warnings"] + bad["info"])
    assert "inc/rogue.php" in joined and "require ledu" in joined, joined       # dead module
    assert "eval" in joined, joined                                            # dangerous fn
    assert "dead_field" in joined and "declared kaani eppudu read avvatledu" in joined, joined
    assert "screenshot.png 1000x800" in joined, joined
    assert bad["ok"] is False


def test_audit_comment_stripper_url_safe():
    """v67 bug fix: `https://...` URLs comments la theeseyakudadu (string-aware stripper)."""
    code = ('<?php\n// real comment <script>x</script>\n'
            '$u = "https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js";\n'
            "/* block comment */\n$v = 'https://www.googletagmanager.com/gtag/js';\n")
    out = theme_audit._strip_php_comments(code)
    assert "pagead2.googlesyndication.com" in out
    assert "googletagmanager.com" in out
    assert "real comment" not in out and "block comment" not in out


def test_security_module():
    sec = read(THEME / "inc" / "security.php")
    for needle in ("X-Content-Type-Options", "X-Frame-Options", "Referrer-Policy",
                   "Permissions-Policy", "xmlrpc_enabled", "studentup_block_author_enum",
                   "is_attachment()", "get_post_parent()", "preprocess_comment",
                   "DISALLOW_FILE_EDIT", "wp_generator", "studentup_security_on",
                   "security_hardening"):
        assert needle in sec, needle
    assert "send_headers" in sec and "wp_safe_redirect" in sec
    assert "?>" not in sec.split("if ( ! defined( 'ABSPATH' ) )")[0], "ABSPATH guard first"
    fn = tpl("functions.php")
    assert "inc/security.php" in fn


def test_top_theme_files():
    for rel, must in (("comments.php", ("wp_list_comments", "comment_form", "studentup")),
                      ("sidebar.php", ("is_active_sidebar", "dynamic_sidebar",
                                       "studentup_ad( 'sidebar' )")),
                      ("readme.txt", ("=== StudentUp ===", "== Changelog ==", "1.3.0")),
                      ("languages/studentup.pot", ("msgid", "studentup", "Content-Type"))):
        assert (THEME / rel).exists(), rel
        body = read(THEME / rel)
        for needle in must:
            assert needle in body, (rel, needle)
    single = tpl("single.php")
    assert "comments_template()" in single and "studentup_ad( 'below-content' )" in single
    for rel in ("archive.php", "search.php"):
        assert "get_sidebar()" in tpl(rel), rel
    # comments toggle nijam ga wire ayyindi
    tpl_code = tpl("inc/template.php")
    assert "comments_open" in tpl_code and "comments_on" in tpl_code
    # POT auto-build lo regenerate avutundi
    build = read(ROOT / "tools" / "build_wp_theme.py")
    assert "build_pot.py" in build


def test_revenue_slots_six():
    ads = read(THEME / "inc" / "ads.php")
    assert "'below-content' => 280" in ads
    assert "su-ad-below" in ads
    assert "su-ad-sticky" in ads
    style = read(THEME / "style.css")
    for tok in (".su-ad-below", ".su-ad-sticky", ".su-sidebar", ".su-btn",
                ":focus-visible", "body.su-cv"):
        assert tok in style, tok
    opts = read(THEME / "inc" / "options.php")
    assert "adsense_slot_below_content" in opts
    assert "content_visibility" in opts and "comments_on" in opts
    perf = read(THEME / "inc" / "perf.php")
    assert "su-cv" in perf and "studentup_cv_body_class" in perf


def test_perf_and_a11y():
    perf = read(THEME / "inc" / "perf.php")
    for needle in ("wp_resource_hints", "pagead2.googlesyndication.com",
                   "googleads.g.doubleclick.net", "googletagmanager.com",
                   "wp_robots", "is_search()", "is_404()", "noindex"):
        assert needle in perf, needle
    # anni buttons ki type attribute (form submit bug prevent)
    for rel in ("header.php", "footer.php", "front-page.php", "single.php"):
        for m in re.finditer(r"<button(?![^>]*\btype=)[^>]*>", tpl(rel)):
            raise AssertionError(f"{rel}: button type ledu → {m.group(0)[:60]}")
    # focus styles + skip link
    style = read(THEME / "style.css")
    assert ":focus-visible" in style and ".skip-link:focus" in style
    assert re.search(r'class="[^"]*skip-link', tpl("header.php"))


def test_search_page_form():
    search = tpl("search.php")
    assert "get_search_form()" in search
    # v73: English empty state
    assert "su-empty" in search and "No results" in search


def test_zip_has_new_files():
    zip_path = ROOT / "wordpress-theme" / "studentup-theme.zip"
    assert zip_path.exists(), "zip ledu — tools/build_wp_theme.py run cheyandi"
    import zipfile

    with zipfile.ZipFile(zip_path) as zf:
        names = zf.namelist()
    for rel in ("studentup/comments.php", "studentup/sidebar.php", "studentup/readme.txt",
                "studentup/inc/security.php", "studentup/languages/studentup.pot"):
        assert rel in names, (rel, names[:12])
    # zip source kanna paata kaadu (fresh)
    newest_src = max((THEME.rglob("*")).__iter__().__next__().stat().st_mtime for _ in [0])
    newest = max(p.stat().st_mtime for p in THEME.rglob("*") if p.is_file())
    assert zip_path.stat().st_mtime >= newest - 1, "zip stale — build malli run cheyandi"
    assert newest_src  # (trivial use — lint)


def test_audit_wired_into_gates():
    build = read(ROOT / "tools" / "build_wp_theme.py")
    assert "theme_audit.py" in build and "audit.returncode" in build
    from autoblog import guardian, readiness

    ids = [c[0] for c in guardian.CHECKS]
    assert "theme_audit" in ids
    assert "theme_audit" in [n for n, _ in readiness.CHECKS]
    rep = readiness.run_report()
    assert rep["score"] == 100 and rep["total"] >= 26, rep


def test_docs_v67():
    readme = read(ROOT / "README.md")
    assert "v67" in readme and "deep audit" in readme.lower()
    manual = read(ROOT / "MANUAL_ADVANCED_CHECKLIST.md")
    assert "PART 26" in manual and "theme_audit_deep" in manual
    matrix = ROOT / "docs" / "BA_REQUIREMENTS_MATRIX.md"
    assert matrix.exists(), "BA requirements matrix ledu"
    body = read(matrix)
    assert "requirement" in body.lower() and "evidence" in body.lower()
    go = read(ROOT / "GO_LIVE_CHECKLIST.md")
    assert "security" in go.lower() and "comments" in go.lower()


def main():
    print("=" * 70)
    print("  v67 — DEEP AUDIT (expert/BA) + TOP-THEME HARDENING + 6/6 REVENUE SLOTS")
    print("=" * 70)
    tests = [
        ("deep audit: 0 errors · 0 warnings · 6/6 ad slots", test_deep_audit_clean),
        ("deep audit detection (dead module · eval · dead option · screenshot)", test_deep_audit_detects),
        ("audit comment-stripper URL-safe (v67 bug fix)", test_audit_comment_stripper_url_safe),
        ("security module (headers · XML-RPC off · enumeration · flood guard)", test_security_module),
        ("top-theme files (comments · sidebar · readme · POT · wiring)", test_top_theme_files),
        ("6/6 revenue slots (below-content · sticky sidebar · options)", test_revenue_slots_six),
        ("perf + a11y (preconnect · robots · focus-visible · button types)", test_perf_and_a11y),
        ("search page: form + empty state", test_search_page_form),
        ("theme zip: new files + fresh", test_zip_has_new_files),
        ("audit gates (build · guardian · readiness 100/100)", test_audit_wired_into_gates),
        ("docs: README v67 + MANUAL PART 26 + BA matrix", test_docs_v67),
    ]
    failed = 0
    for name, fn in tests:
        try:
            fn()
            print(f"  {name} ✔")
        except AssertionError as exc:
            failed += 1
            print(f"  {name} ✘  {exc}")
        except Exception as exc:  # noqa: BLE001
            failed += 1
            print(f"  {name} ✘  {type(exc).__name__}: {exc}")
    print("-" * 70)
    if failed:
        print(f"  {failed} TEST(S) FAILED ✘")
        return 1
    print("ALL v67 DEEP-AUDIT + TOP-THEME TESTS PASSED ✔")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
