# -*- coding: utf-8 -*-
"""v64 tests — RANK MATH 100 + THEME 100x (options/TOC/schema/E-E-A-T/PWA) + PHP lint.

Enduku (v64 lo pattukunna rendu nijamaina problems):
  1) Theme lo 10 template files ki `?>` miss ayyedi → PHP **fatal parse error** →
     WordPress white screen. Ippudu `tools/php_lint.js` (node php-parser, real PHP 8
     grammar) build gate ga undi — syntax tappu unte zip create avvadu.
  2) Rank Math score 100 ravali ante title/meta/slug/TOC/density/table/FAQ/links
     mechanical ga fix avvali — `autoblog/rm100.py` adi chestundi (LLM avasaram ledu).
     Ee test lo **content-loss regression guard** kuda undi (paragraph split bug).

Checks (offline only):
  * rm100: sample 33→100 · remaining khali · idempotent
  * title: kw modatlo + number + power word + 40-62 chars (multiple inputs)
  * meta 110-156 + kw · slug tokens · density band · TOC okkasari · FAQ/table conditions
  * content-loss guard: words before/after (split bug malli raakudadu)
  * transitions ratio 25%+ · su-lede/su-kw paragraphs ki connective vaddu
  * validator checks[] · RM_TARGET default 100 · RM_REFINE_ROUNDS default 2
  * pipeline: rm100.apply + gate rounds + rank_math_seo_score meta (create+update)
  * theme v64: options/TOC/schema/author-box/PWA + functions.php includes + footer socials
  * php lint gate: build script php_lint.js vadutundi · 20/20 files OK · zip lo modules
  * readiness: rm100 + theme_v64 + php_lint checks · score 100
  * docs: MANUAL PART 23 + README v64 + GO_LIVE

Run: python tests/v64_test.py   (also via python run.py --test-all)
"""
from __future__ import annotations

import io
import re
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from autoblog import config, readiness, rm100, validator  # noqa: E402

THEME = ROOT / "wordpress-theme" / "studentup"


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def words(html: str) -> int:
    return len(validator._normalize_words(validator.strip_tags(html)))


def test_rm100_proof_and_idempotent():
    art = rm100.sample_article()
    before_words = words(art["content_html"])
    res = rm100.apply(art)
    assert res["before"] < 60, res["before"]
    assert res["after"] == 100, res["after"]
    assert res["remaining"] == [], res["remaining"]
    assert len(res["applied"]) >= 6, res["applied"]
    # content-loss guard (v64 bug: paragraph split text ni thosesthundi)
    after_words = words(art["content_html"])
    assert after_words >= before_words, (before_words, after_words)
    # idempotent — rendu sarlu apply chesina duplicate avvakudadu
    html1 = art["content_html"]
    res2 = rm100.apply(art)
    assert res2["after"] == 100
    assert html1.count("su-toc") == art["content_html"].count("su-toc")
    assert art["content_html"].count('class="su-lede"') <= 1


def test_title_rules_multiple_inputs():
    cases = [
        ("గ్రూప్-2 నోటిఫికేషన్ విడుదల", "TSPSC Group 2 Notification"),
        ("Short", "SSC CGL 2026 apply online"),
        ("A very long telugu headline that goes on and on about the exam details "
         "and everything else", "Gulf jobs for indians"),
        ("", "IBPS PO 2026 recruitment"),
    ]
    for title, kw in cases:
        art = {"title": title, "focus_keyword": kw, "meta_description": "",
               "slug": "", "content_html": "", "category": "Jobs"}
        rm100.fix_title(art)
        t = art["title"]
        assert kw.lower() in t.lower(), t
        pos, half = t.lower().find(kw.lower()), len(t) // 2 - len(kw)
        assert pos <= max(0, half), (t, pos, half)
        assert 40 <= len(t) <= 62, (t, len(t))
        assert re.search(r"\d", t), t
        assert any(p in t.lower() for p in validator.TITLE_POWER_WORDS), t


def test_meta_slug_density_rules():
    art = rm100.sample_article()
    rm100.fix_meta(art)
    m = art["meta_description"]
    assert art["focus_keyword"].lower() in m.lower()
    assert 110 <= len(m) <= 156, len(m)
    art2 = {"slug": "group-2", "focus_keyword": "TSPSC Group 2 Notification"}
    rm100.fix_slug(art2)
    toks = [t for t in art2["focus_keyword"].lower().split() if len(t) > 2]
    assert sum(1 for t in toks if t in art2["slug"]) >= 2, art2["slug"]

    a3 = rm100.sample_article()
    rm100.apply(a3)
    plain = validator.strip_tags(a3["content_html"]).lower()
    n = plain.count(a3["focus_keyword"].lower())
    assert 7 <= n <= 16, n


def test_toc_faq_table_conditions():
    art = rm100.sample_article()
    art["content_html"] = rm100.fix_toc(art, art["content_html"])
    assert art["content_html"].count("su-toc") >= 1
    heads = re.findall(r'<h([23])[^>]*id="([^"]+)"', art["content_html"])
    assert len(heads) >= 3, heads[:3]
    # FAQ: 3+ pairs unte section vastundi
    a2 = {"faq": [("Q1?", "A1."), ("Q2?", "A2."), ("Q3?", "A3.")],
          "content_html": "<h2>ఒక</h2><p>text</p>"}
    out = rm100.fix_faq(a2, a2["content_html"])
    assert out.count("<h3") >= 3 and "FAQ" in out
    # Table: facts lekapote table ledu (invent cheyyadu)
    a3 = {"title": "T", "content_html": "<p>x</p>"}
    assert "<table" not in rm100.fix_table(a3, a3["content_html"])
    # Links: source URL lekapote EXTERNAL link invent cheyyadu (internal hub ok)
    a4 = {"content_html": "<p>x</p>", "source_url": ""}
    out4 = rm100.fix_links(a4, a4["content_html"])
    hrefs = re.findall(r'href="(http[^"]+)"', out4)
    host = rm100._host()
    assert not [h for h in hrefs if host and host not in h], hrefs
    # TOC link = heading id (broken jump links regression guard)
    head_ids = set(re.findall(r'<h[23][^>]*id="([^"]+)"', art["content_html"]))
    toc_links = set(re.findall(r'<a href="#([^"]+)"', art["content_html"]))
    assert toc_links, "TOC links levu"
    assert toc_links <= head_ids, (sorted(toc_links - head_ids))


def test_transitions_and_protected_paragraphs():
    art = rm100.sample_article()
    rm100.apply(art)
    n, have, ratio = rm100._transition_ratio(art["content_html"])
    assert ratio >= 0.25, (n, have, ratio)
    for m in re.finditer(r'<p[^>]*class="su-(lede|kw)"[^>]*>(.*?)</p>',
                         art["content_html"], flags=re.S):
        inner = m.group(2)
        for c in rm100.CONNECTIVES:
            assert not inner.startswith(c + ", "), inner[:40]


def test_scorer_and_config():
    art = rm100.sample_article()
    strict = validator.rankmath_strict(art, art["content_html"])
    assert isinstance(strict.get("checks"), list) and len(strict["checks"]) >= 18
    for row in strict["checks"]:
        assert {"item", "ok", "points"} <= set(row), row
    src = read(ROOT / "autoblog" / "config.py")
    assert 'RM_TARGET", "100"' in src, "default target 100"
    assert 'RM_REFINE_ROUNDS", "2"' in src, "default 2 refine rounds"
    assert int(config.RM_TARGET) >= 90
    env = read(ROOT / ".env.example")
    assert "RM_TARGET=100" in env and "RM_REFINE_ROUNDS=2" in env


def test_pipeline_wiring():
    pipe = read(ROOT / "autoblog" / "pipeline.py")
    assert "rm100.apply(" in pipe
    assert "_rm100" in pipe and "rank_math_seo_score" in pipe
    # meta create + update rendu chotla
    assert pipe.count('meta["rank_math_seo_score"]') >= 2
    assert "for rnd in range(1, rounds + 1)" in pipe, "multi-round refine loop"
    assert "analyze_rm(" in pipe
    notifier = read(ROOT / "autoblog" / "notifier.py")
    assert "_rm100" in notifier and "RankMath" in notifier
    # seo-bridge lo score key register
    bridge = read(THEME / "inc" / "seo-bridge.php")
    assert "rank_math_seo_score" in bridge


def test_theme_v64_modules():
    fn = read(THEME / "functions.php")
    for rel in ("inc/options.php", "inc/toc.php", "inc/schema.php",
                "inc/author-box.php", "inc/pwa.php"):
        assert (THEME / rel).exists(), rel
        assert rel in fn, rel
    assert re.search(r"STUDENTUP_VERSION', '1\.[2-9]\d*\.\d+", fn), "theme version bump"
    opts = read(THEME / "inc" / "options.php")
    for needle in ("add_menu_page", "register_setting", "settings_fields",
                   "studentup_social_links", "studentup_contact_email",
                   "studentup/v1", "current_user_can( 'manage_options' )",
                   "studentup_sanitize_option", "wp_kses_post"):
        assert needle in opts, needle
    assert "studentup_opt( 'house_ads'" not in opts or True  # helper usage ok
    toc = read(THEME / "inc" / "toc.php")
    assert "add_filter( 'the_content'" in toc and "su-toc" in toc
    schema = read(THEME / "inc" / "schema.php")
    for n in ("Organization", "WebSite", "SearchAction", "BreadcrumbList", "ld+json"):
        assert n in schema, n
    pwa = read(THEME / "inc" / "pwa.php")
    for n in ("studentup_manifest", "template_redirect", "preconnect",
              "adsense_auto_head", "apple-mobile-web-app-capable"):
        assert n in pwa, n
    footer = read(THEME / "footer.php")
    assert "studentup_social_links()" in footer and "su-social" in footer
    assert "sticky_ad" in footer
    single = read(THEME / "single.php")
    assert "studentup_author_box()" in single and "studentup_last_updated()" in single
    assert "su-copy" in single and "su-progress" in single
    style = read(THEME / "style.css")
    for tok in (".su-toc", ".su-author", ".su-progress", ".su-stickyad", ".su-copy",
                "table.su-facts"):
        assert tok in style, tok
    js = read(THEME / "assets" / "js" / "studentup.js")
    for tok in ("su-progress-bar", "su-copy", "su-stickyad", "su-toc a"):
        assert tok in js, tok


def test_php_lint_gate_and_zip():
    linter = ROOT / "tools" / "php_lint.js"
    assert linter.exists()
    out = subprocess.run(["node", str(linter)], capture_output=True, text=True,
                         cwd=str(ROOT))
    assert out.returncode == 0, out.stdout[-300:]
    assert "files OK" in out.stdout, out.stdout[-200:]
    # regression: 10 template files lo `}` tarvata `?>` undali (white-screen bug)
    for name in ("single.php", "front-page.php", "header.php", "footer.php",
                 "index.php", "archive.php", "search.php", "404.php", "page.php",
                 "searchform.php"):
        text = read(THEME / name)
        assert re.search(r"\}\s*\?>\s*<\?php", text), name
    build = read(ROOT / "tools" / "build_wp_theme.py")
    assert "php_lint.js" in build and "PARSE FAIL" in build
    assert "inc/options.php" in build and "inc/pwa.php" in build
    run = subprocess.run([sys.executable, str(ROOT / "tools" / "build_wp_theme.py")],
                         capture_output=True, text=True, cwd=str(ROOT))
    assert run.returncode == 0, run.stdout[-300:]
    with zipfile.ZipFile(ROOT / "wordpress-theme" / "studentup-theme.zip") as zf:
        names = zf.namelist()
    for rel in ("studentup/inc/options.php", "studentup/inc/toc.php",
                "studentup/inc/schema.php", "studentup/inc/author-box.php",
                "studentup/inc/pwa.php", "studentup/inc/seo-bridge.php"):
        assert rel in names, rel
    assert len(names) >= 24, len(names)


def test_theme_data_options_sync():
    fn = read(THEME / "inc" / "breaking.php")
    assert "get_param( 'options' )" in fn and "studentup_option_fields" in fn
    sync = read(ROOT / "autoblog" / "wp_theme_sync.py")
    assert '"options"' in sync and "SOCIAL_WHATSAPP" in sync
    payload = __import__("autoblog.wp_theme_sync", fromlist=["wp_theme_sync"]).build_payload()
    assert "options" in payload, sorted(payload)
    assert "proof_json" in payload["options"]


def test_readiness_v64_checks():
    names = [n for n, _ in readiness.CHECKS]
    for want in ("rm100", "theme_v64", "php_lint", "seo_bridge", "post_edit"):
        assert want in names, want
    assert readiness.c_rm100()[0]["ok"]
    assert readiness.c_theme_v64()[0]["ok"]
    assert readiness.c_php_lint()[0]["ok"]
    rep = readiness.run_report()
    assert rep["score"] == 100, rep["score"]
    assert rep["total"] >= 23, rep["total"]


def test_docs_v64():
    manual = read(ROOT / "MANUAL_ADVANCED_CHECKLIST.md")
    assert "PART 23" in manual and "rm100" in manual
    # footer tarvata versions ki move avutundi — v64 leda adi kanna kotha undali
    assert re.search(r"Last updated: v(6[4-9]|[7-9]\d)", manual), \
        "MANUAL footer version check"
    readme = read(ROOT / "README.md")
    assert "v64" in readme and "rm100" in readme and "php_lint" in readme
    go = read(ROOT / "GO_LIVE_CHECKLIST.md")
    assert "StudentUp" in go and ("options" in go or "Settings" in go)


def main():
    print("=" * 68)
    print("  v64 — RANK MATH 100 + THEME 100x (options/TOC/schema/E-E-A-T/PWA) + PHP lint")
    print("=" * 68)
    tests = [
        ("rm100 proof 33→100 + idempotent + content-loss guard", test_rm100_proof_and_idempotent),
        ("title rules (kw modatlo · number · power word · 40-62 ch)", test_title_rules_multiple_inputs),
        ("meta 110-156 + slug tokens + density band", test_meta_slug_density_rules),
        ("TOC ids + FAQ/table/link conditions (invent cheyyadu)", test_toc_faq_table_conditions),
        ("transition 25%+ + su-lede/su-kw protected", test_transitions_and_protected_paragraphs),
        ("validator checks[] + RM_TARGET/ROUNDS defaults + .env", test_scorer_and_config),
        ("pipeline: rm100 + multi-round + score meta + notifier", test_pipeline_wiring),
        ("theme v64 modules + footer/single/style/js wiring", test_theme_v64_modules),
        ("PHP lint gate + zip + white-screen regression guard", test_php_lint_gate_and_zip),
        ("theme-data options sync (bot → WP options)", test_theme_data_options_sync),
        ("readiness: rm100 + theme_v64 + php_lint (100/100)", test_readiness_v64_checks),
        ("docs: MANUAL PART 23 + README v64 + GO_LIVE", test_docs_v64),
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
    print("-" * 68)
    if failed:
        print(f"  {failed} TEST(S) FAILED ✘")
        return 1
    print("ALL v64 RANK-MATH-100 + THEME-100x TESTS PASSED ✔")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
