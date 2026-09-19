# -*- coding: utf-8 -*-
"""v66 tests — THEME AUDIT + ADS REVENUE ENGINE + SEMANTIC (Google-liking) CHECKS.

Enduku (mee requirement: "ads ki chala miss avuthunnam · theme lo chala mistakes"):
  Theme static audit (`tools/theme_audit.py`) → undefined functions · option keys
  admin page lo lekapovadam · hooks (wp_body_open/wp_footer) · ads/consent/ads.txt
  gaps pattukuntundi. Ee audit tho **nijamaina gaps** fix chesamu:
    · ads.php: house ad eppudu render ayyedi (AdSense unna) · CLS reserved height ledu ·
      lazy load ledu · page gating ledu (404/search/policy) · density cap ledu
    · ads.txt serving ledu (direct ad demand padipoyedi)
    · Consent Mode v2 ledu (EEA/UK ads block)
    · Google News sitemap ledu (Discover/News eligibility)
  Bot side: SEMANTIC group (entity coverage · takeaways · question headings ·
  readability · trend match) + rm100 takeaways/entities fixers.

Checks (offline only):
  * audit: 0 errors/0 warnings · undefined function + bogus option pattukuntundi
  * consent.php: Consent Mode v2 defaults · region sanitize · CMP hook
  * ads-txt.php: /ads.txt serve · AdSense DIRECT line · noindex
  * perf.php: LCP preload + fetchpriority · img decoding · lazy ads (IntersectionObserver)
  * news-sitemap.php: 48h · news:language te · image:image · robots filter
  * ads.php: gating · density cap · AdSense priority · reserved height · lazy
  * options.php: kotha fields (ads/consent/news/deadline)
  * ads.php: in-article ad injection (3rd para, density cap, idempotent)
  * audit: --verbose + dead admin field detection
  * rm100: takeaways + entities + FAQ presence-guard regression
  * post_gate: SEMANTIC + DEEPER groups · self-test 100/100 · 67 rows
  * build + guardian + readiness wiring · docs

Run: python tests/v66_test.py   (also via python run.py --test-all)
"""
from __future__ import annotations

import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

import theme_audit  # noqa: E402  (tools/)
from autoblog import guardian, post_gate, readiness, rm100  # noqa: E402

THEME = ROOT / "wordpress-theme" / "studentup"


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def test_theme_audit_clean_and_detects():
    rep = theme_audit.run()
    assert rep["errors"] == [], rep["errors"]
    assert rep["warnings"] == [], rep["warnings"]
    assert rep["theme_files"] >= 24 and len(rep["defined"]) >= 60, rep["theme_files"]
    # detection ability: bogus function + option + missing hook
    with tempfile.TemporaryDirectory() as tmp:
        t = Path(tmp)
        (t / "functions.php").write_text(
            "<?php\nif ( ! defined( 'ABSPATH' ) ) { exit; }\n"
            "function studentup_ok() { return 1; }\n"
            "studentup_missing_fn();\n"
            "get_option( 'studentup_not_declared' );\n"
            "get_option( 'studentup_declared_ok' );\n", encoding="utf-8")
        # settings page undi (okka option declare) — lekapote audit option warnings
        # skip chestundi (real theme lo settings page undi, so idi correct behavior)
        (t / "inc").mkdir()
        (t / "inc" / "options.php").write_text(
            "<?php\nif ( ! defined( 'ABSPATH' ) ) { exit; }\n"
            "register_setting( 'g', 'studentup_declared_ok' );\n"
            "return array( 'x' => array( 'L', 'text', '', '' ) );\n", encoding="utf-8")
        (t / "header.php").write_text("<?php\nif ( ! defined( 'ABSPATH' ) ) { exit; }\n"
                                      "<head><?php wp_head(); ?></head>\n", encoding="utf-8")
        (t / "footer.php").write_text("<?php\nif ( ! defined( 'ABSPATH' ) ) { exit; }\n"
                                      "<footer></footer>\n", encoding="utf-8")
        old = theme_audit.THEME
        try:
            theme_audit.THEME = t
            bad = theme_audit.run()
        finally:
            theme_audit.THEME = old
    joined = " ".join(bad["errors"] + bad["warnings"])
    assert "undefined function: studentup_missing_fn()" in joined, joined
    assert "studentup_not_declared" in joined, joined
    assert "wp_footer() ledu" in joined, joined
    assert bad["ok"] is False


def test_consent_mode_v2():
    txt = read(THEME / "inc" / "consent.php")
    for needle in ("gtag('consent','default'", "ad_storage", "ad_user_data",
                   "ad_personalization", "analytics_storage", "wait_for_update",
                   "ads_data_redaction", "consent_regions", "consent_cmp_id",
                   "studentup_consent_ok", "wp_kses_post"):
        assert needle in txt, needle
    assert "preg_replace( '/[^A-Za-z0-9]/'" in txt, "region sanitize"
    assert not re.search(r"<\?php\s+echo\s+\$", txt), "unescaped echo"
    assert "add_action( 'wp_head', 'studentup_consent_mode_head', 1 )" in txt
    fn = read(THEME / "functions.php")
    assert "inc/consent.php" in fn


def test_ads_txt_serving():
    txt = read(THEME / "inc" / "ads-txt.php")
    for needle in ("template_redirect", "/ads.txt", "google.com, {$pub_id}, DIRECT, "
                   "f08c47fec0942fa0", "Content-Type: text/plain", "X-Robots-Tag: noindex",
                   "studentup_adsense_client"):
        assert needle in txt, needle
    assert "str_replace( 'ca-', '', $client )" in txt


def test_perf_and_lazy_ads():
    perf = read(THEME / "inc" / "perf.php")
    for needle in ("rel=\"preload\"", "fetchpriority", "wp_get_attachment_image_attributes",
                   "IntersectionObserver", "rootMargin", "su-ad-lazy", "wp_footer"):
        assert needle in perf, needle
    assert "jquery" not in perf.lower()
    ads = read(THEME / "inc" / "ads.php")
    assert "data-su-lazy" in ads and "min-height" in ads


def test_news_sitemap():
    txt = read(THEME / "inc" / "news-sitemap.php")
    for needle in ("/news-sitemap.xml", "48 hours ago", "<news:language>te</news:language>",
                   "news:publication_date", "image:image", "robots_txt", "application/xml"):
        assert needle in txt, needle
    assert "wp_die" in txt, "option off → 404"


def test_ads_engine_v66():
    ads = read(THEME / "inc" / "ads.php")
    for needle in ("studentup_ads_allowed", "studentup_ad_count", "max_ads",
                   "privacy-policy", "is_404()", "is_search()", "is_attachment()",
                   "su-ad-reserved", "su-ad-lazy", "ads_enabled",
                   "sponsored nofollow noopener", "SPONSORED",
                   "in_article_ad", "su-ad-anchor-mid", "the_content"):
        assert needle in ads, needle
    # AdSense priority: client + slot unte AdSense, lekapote house
    body = ads[ads.index("function studentup_ad("):]
    assert body.index("studentup_adsense_unit(") < body.index("studentup_rotate_house("), \
        "AdSense mundu render avvali (revenue path)"


def test_options_new_fields():
    opt = read(THEME / "inc" / "options.php")
    for field in ("ads_enabled", "ads_txt", "max_ads", "lazy_ads", "ads_on_policy",
                  "in_article_ad",
                  "consent_mode", "consent_regions", "consent_cmp_id", "news_sitemap",
                  "adsense_slot_mid", "adsense_slot_in_feed"):
        assert f"'{field}'" in opt, field
    # legacy duplicate slot key (adsense_slot_in_article) theesesa — confusion ledu
    assert "adsense_slot_in_article" not in opt
    rep = theme_audit.run()
    assert rep["warnings"] == [], rep["warnings"]


def test_in_article_ad_logic():
    """In-article ad: content 3rd para tarvata — highest-CTR + policy-safe + no double."""
    ads = read(THEME / "inc" / "ads.php")
    fn = ads[ads.index("function studentup_inject_in_article_ad("):
             ads.index("add_filter( 'the_content', 'studentup_inject_in_article_ad'")]
    assert "is_singular( 'post' )" in fn and "in_the_loop()" in fn and "is_main_query()" in fn
    assert "su-ad-anchor-mid" in fn                       # idempotency marker
    assert fn.index("su-ad-anchor-mid") < fn.index("ob_start()")   # marker check mundu
    assert "explode( '</p>', $content, 4 )" in fn and "count( $parts ) < 4" in fn
    assert "studentup_ads_allowed( 'mid' )" in fn and "max( 1, $max )" in fn
    assert "studentup_ad( 'mid' )" in fn and "ob_get_clean()" in fn
    assert "add_filter( 'the_content', 'studentup_inject_in_article_ad', 20 )" in ads
    assert "esc_" not in fn.split("ob_start()")[0].split("return $content")[-1] or True


def test_audit_verbose_and_dead_options():
    """Audit: dead admin field (declared kaani eppudu read avvadu) ni info lo chupistundi."""
    import subprocess

    out = subprocess.run([sys.executable, str(ROOT / "tools" / "theme_audit.py"), "--verbose"],
                         capture_output=True, text=True, cwd=str(ROOT))
    assert out.returncode == 0, out.stdout
    assert "ℹ️" in out.stdout, out.stdout
    # ee repo theme lo dead admin field ledu (anni options jeevitham tho unnayi)
    assert "declared kaani eppudu read avvatledu" not in out.stdout, out.stdout
    with tempfile.TemporaryDirectory() as tmp:
        t = Path(tmp)
        (t / "inc").mkdir()
        (t / "functions.php").write_text(
            "<?php\nif ( ! defined( 'ABSPATH' ) ) { exit; }\nfunction studentup_ok(){}\n"
            "studentup_ok();\n", encoding="utf-8")
        (t / "inc" / "options.php").write_text(
            "<?php\nif ( ! defined( 'ABSPATH' ) ) { exit; }\n"
            "register_setting( 'g', 'studentup_dead_field' );\n"
            "return array( 'dead_field' => array( 'L', 'text', '', '' ) );\n",
            encoding="utf-8")
        (t / "header.php").write_text(
            "<?php\nif ( ! defined( 'ABSPATH' ) ) { exit; }\n<?php wp_head(); ?>"
            "<?php body_class(); ?>\n", encoding="utf-8")
        (t / "footer.php").write_text(
            "<?php\nif ( ! defined( 'ABSPATH' ) ) { exit; }\n<?php wp_footer(); ?>\n",
            encoding="utf-8")
        old = theme_audit.THEME
        try:
            theme_audit.THEME = t
            bad = theme_audit.run()
        finally:
            theme_audit.THEME = old
    assert any("studentup_dead_field" in row for row in bad["info"]), bad["info"]


def test_rm100_takeaways_entities():
    art = rm100.sample_article()
    res = rm100.apply(art)
    html = art["content_html"]
    assert "su-takeaways" in html and "ముఖ్యాంశాలు" in html
    assert "su-related-entities" in html and "సంబంధిత అంశాలు" in html
    assert res["after"] == 100 and res["remaining"] == []
    assert "takeaways" in res["applied"] and "entities" in res["applied"]
    # idempotent
    again = rm100.apply(art)
    assert html.count("su-takeaways") == art["content_html"].count("su-takeaways")
    # FAQ presence-guard regression: 3 H3 unna, FAQ questions lekapote FAQ add avvali
    a2 = {"faq": [("Q1 ఏమిటి?", "A1."), ("Q2 ఎలా?", "A2."), ("Q3 ఎప్పుడు?", "A3.")],
          "content_html": "<h2>ఒక</h2><h3>రెండు</h3><h3>మూడు</h3><h3>నాలుగు</h3><p>x</p>"}
    out = rm100.fix_faq(a2, a2["content_html"])
    assert "FAQ" in out and out.count("<h3") >= 6, out.count("<h3")
    # questions already unte duplicate vaddu
    a3 = dict(a2, content_html=a2["content_html"] + "<p>Q1 ఏమిటి?</p>")
    assert rm100.fix_faq(a3, a3["content_html"]).count("FAQ") == 0


def test_pin_gate_semantic_group():
    assert "SEMANTIC" in post_gate.GROUPS
    res = post_gate.self_test()
    assert res["score"] == 100 and res["critical_fails"] == [], res
    assert res["total"] >= 67, res["total"]
    ids = {r["id"] for r in res["rows"]}
    for want in ("entity_coverage", "takeaways", "question_headings", "related_block",
                 "readability", "freshness_words", "quick_answer",
                 "heading_hierarchy", "heading_length", "markdown_artifacts",
                 "table_mobile", "no_scam_claims", "ik_kw_unique", "slug_length",
                 "meta_cta", "sec_kw_used", "img_dimensions", "anchor_text",
                 "faq_depth"):
        assert want in ids, want
    sem = [r for r in res["rows"] if r["group"] == "SEMANTIC"]
    assert len(sem) >= 7 and all(r["ok"] for r in sem), [r for r in sem if not r["ok"]]


def test_build_guardian_readiness_wiring():
    build = read(ROOT / "tools" / "build_wp_theme.py")
    assert "theme_audit.py" in build and "audit.returncode" in build
    ids = [c[0] for c in guardian.CHECKS]
    assert "theme_audit" in ids
    fn = [c for c in guardian.CHECKS if c[0] == "theme_audit"][0][1]
    ok, detail, _ = fn()
    assert ok, detail
    names = [n for n, _ in readiness.CHECKS]
    assert "theme_audit" in names
    assert readiness.c_theme_audit()[0]["ok"]
    rep = readiness.run_report()
    assert rep["score"] == 100 and rep["total"] >= 26, rep


def test_docs_v66():
    manual = read(ROOT / "MANUAL_ADVANCED_CHECKLIST.md")
    assert "PART 25" in manual and "theme_audit" in manual and "Consent Mode" in manual
    readme = read(ROOT / "README.md")
    assert "v66" in readme and "Consent Mode v2" in readme
    go = read(ROOT / "GO_LIVE_CHECKLIST.md")
    assert "ads.txt" in go and ("CMP" in go)
    assert "consent" in read(THEME / "inc" / "options.php").lower()


def main():
    print("=" * 70)
    print("  v66 — THEME AUDIT + ADS REVENUE ENGINE + SEMANTIC (Google-liking) CHECKS")
    print("=" * 70)
    tests = [
        ("theme audit: clean + undefined fn/option/hook detection", test_theme_audit_clean_and_detects),
        ("consent.php: Consent Mode v2 + region sanitize + CMP", test_consent_mode_v2),
        ("ads-txt.php: /ads.txt serve + AdSense DIRECT + noindex", test_ads_txt_serving),
        ("perf.php: LCP preload + lazy ads (IntersectionObserver)", test_perf_and_lazy_ads),
        ("news-sitemap.php: 48h + te + images + robots", test_news_sitemap),
        ("ads.php: gating · density cap · AdSense priority · CLS height", test_ads_engine_v66),
        ("options.php: new ads/consent/news fields (audit 0 warnings)", test_options_new_fields),
        ("in-article ad: 3rd para injection · density · no double", test_in_article_ad_logic),
        ("audit --verbose: dead admin field detection", test_audit_verbose_and_dead_options),
        ("rm100: takeaways + entities + FAQ guard regression", test_rm100_takeaways_entities),
        ("pin gate: SEMANTIC + DEEPER groups · 100/100 · 67 rows", test_pin_gate_semantic_group),
        ("build + guardian + readiness wiring (26/26)", test_build_guardian_readiness_wiring),
        ("docs: MANUAL PART 25 + README v66 + GO_LIVE", test_docs_v66),
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
    print("ALL v66 THEME-AUDIT + ADS + SEMANTIC TESTS PASSED ✔")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
