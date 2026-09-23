# -*- coding: utf-8 -*-
"""v95 tests — SEO 100 pin-to-pin + TERMS + IN-BODY SIGNALS (theme 1.9.6).

Brief: "fix" — అంటే remaining audit gaps (Rank Math / SEO 100 · Google-suggest
keywords · contextual linking · terms page) ni okati okati ga close cheyyadam.

Ee suite v95 lo fix ayyina **nijamaina gaps** ni regression ga kāpādutundi:

  GAP-1 CONTENT LOPALA IMAGE LEDU — featured image mattrame undi, article
        `<img>` ledu. Effects: Rank Math "Focus Keyword in Image Alt" test fail,
        Discover/rich-result ki in-article image support takkuva, engagement
        takkuva. Fix: `seo.attach_inline_image()` (idempotent · width/height tho
        CLS-safe · lazy + async decode → LCP ni touch cheyyadu) + pipeline wiring
        (featured upload tarvata, real URL tho) + `content_image` gate check.

  GAP-2 CONTEXTUAL INTERNAL LINKS LEDU — `su-related` section links mattrame
        (footer-style, weak signal). Fix: `seo.contextual_links()` — paragraph
        **lopala** natural anchor (modati occurrence mattrame · `<a>` unna
        paragraph skip → nested link ledu · tag attributes touch cheyyadu ·
        idempotent · `CONTEXTUAL_LINKS_MAX` limit).

  GAP-3 RANK MATH PARITY — URL length check ledu (75 chars), image-alt check
        ledu. Fix: `slug-length` (rm100 `_trim_slug` guarantee) + conditional
        `kw-in-img-alt` (image unte mattrame add → gate fair).

  GAP-4 TERMS PAGE LEDU — AdSense/Google policy completeness ki ToS page kavali
        (usage rules · copyright · ads disclosure · liability limits · governing
        law). Fix: `tools/build_policy_pages.py` TERMS + nav + sitemap + footer
        link (theme).

Checks (13): contextual_links API/safety · attach_inline_image API/safety · enhance()
wiring · config knob · validator parity checks · rm100 slug trim · post_gate
`content_image` (68/68 certificate) · pipeline wiring · terms page (builder ·
nav · sitemap · footer) · version parity 1.9.6 · suite pins 75 · zip packaged.

Run: python tests/v95_test.py   (also via python run.py --test-all)
"""
from __future__ import annotations

import os
import re
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

THEME = ROOT / "wordpress-theme" / "studentup"
SUITES_EXPECTED = 89  # v95 tho


def read(rel: Path | str) -> str:
    return Path(rel).read_text(encoding="utf-8")


# ------------------------------------------------------------------ 1
def test_contextual_links_api() -> None:
    from autoblog import seo

    html = (
        "<h2>ఉద్యోగ నోటిఫికేషన్</h2>"
        "<p>TSPSC Group 2 notification vachindi. ఇది అందరికీ ముఖ్యం.</p>"
        "<p>TSPSC Group 2 notification dates ikkada unnayi.</p>"
    )
    links = [{"title": "TSPSC Group 2 Notification 2026 – studentup.in",
              "link": "https://studentup.in/tspsc-group-2"}]
    out = seo.contextual_links(html, links, max_links=3)
    assert out.count('class="su-ctx"') == 1, "in-body link add avvaledu"
    # modati occurrence mattrame (rendo paragraph lo malli link vaddhu)
    assert out.count('href="https://studentup.in/tspsc-group-2"') == 1, "double link"
    # idempotent — malli run cheste kotha link ledu
    assert seo.contextual_links(out, links).count('class="su-ctx"') == 1, "idempotent kaadu"
    # link ledapote as-is
    assert seo.contextual_links(html, []) == html, "links levu → html marindi"
    print("      in-body contextual link · idempotent · empty-safe ✔")


def test_contextual_links_safety() -> None:
    from autoblog import seo

    # (a) `<a>` LOPALA unna text ni malli link cheyyadu (nested link = HTML bug)
    html = ('<p>Chudu <a href="https://x.com/a">TSPSC Group 2 Notification</a> '
            'ikkada undi.</p>')
    out = seo.contextual_links(html, [{"title": "TSPSC Group 2 Notification",
                                       "link": "https://studentup.in/t"}])
    assert out.count("<a ") == 1 and "su-ctx" not in out, "nested link create ayyindi"
    # (a2) link unna paragraph lo BAYATA unna text ki link vachina — nesting ledu
    mixed = ('<p>TSPSC Group 2 Notification vachindi. '
             '<a href="https://x.com/a">source</a> chudu.</p>')
    out_m = seo.contextual_links(mixed, [{"title": "TSPSC Group 2 Notification",
                                          "link": "https://studentup.in/t"}])
    assert out_m.count("su-ctx") == 1, "bayata unna text ki link raledu"
    assert not re.search(r"<a[^>]*>[^<]*<a", out_m), "nested link (mixed case)"
    # (b) heading / attributes ni touch cheyyadu
    html2 = ("<h2>TSPSC Group 2 Notification</h2>"
             '<p class="TSPSC Group 2 Notification">vere text</p>')
    out2 = seo.contextual_links(html2, [{"title": "TSPSC Group 2 Notification",
                                         "link": "https://studentup.in/t"}])
    assert "<h2>" in out2 and "su-ctx" not in out2.split("<h2>")[1].split("</h2>")[0], \
        "heading lo link vachindi"
    # (c) max_links limit
    paras = "".join(f"<p>Topic {i} TSPSC Group 2 Notification gurinchi.</p>"
                    for i in range(5))
    many = [{"title": "TSPSC Group 2 Notification", "link": f"https://studentup.in/{i}"}
            for i in range(5)]
    assert seo.contextual_links(paras, many, max_links=2).count("su-ctx") == 2, \
        "max_links limit fail"
    # (d) already-unna URL malli link cheyyadu
    used = '<p>TSPSC Group 2 Notification</p><p><a href="https://studentup.in/t">x</a></p>'
    assert seo.contextual_links(used, [{"title": "TSPSC Group 2 Notification",
                                        "link": "https://studentup.in/t"}]).count(
        "su-ctx") == 0, "already-unna URL malli link ayyindi"
    print("      nested-link skip · heading/tag skip · max limit · dup URL ✔")


# ------------------------------------------------------------------ 2
def test_attach_inline_image_api() -> None:
    from autoblog import seo

    html = "<h2>A</h2><p>x</p><h2>B</h2><p>y</p>"
    out = seo.attach_inline_image(html, "https://studentup.in/img/featured.webp",
                                 "ఉద్యోగ నోటిఫికేషన్ 2026", caption="ఉదాహరణ", width=1200,
                                 height=675)
    assert out.count("su-figure") == 1, "figure add avvaledu"
    assert 'width="1200"' in out and 'height="675"' in out, "CLS dims levu"
    assert 'loading="lazy"' in out and 'decoding="async"' in out, "lazy/async levu"
    assert "ఉద్యోగ నోటిఫికేషన్ 2026" in out, "alt text ledu"
    # 2nd H2 tarvata (top-of-article, Discover)
    assert out.index("su-figure") > out.index("</h2>"), "position tappu"
    # idempotent: <img> unte no-op
    assert seo.attach_inline_image(out, "https://x/y.webp", "z").count("<img") == 1, \
        "idempotent kaadu"
    # empty url → as-is
    assert seo.attach_inline_image(html, "", "a") == html, "empty URL mutate ayyindi"
    # image ledu + h2 ledu → first </p> tarvata
    assert "su-figure" in seo.attach_inline_image("<p>ok</p>", "https://a/b.webp", "z")
    print("      figure · dims · lazy · 2nd-H2 position · idempotent · empty-safe ✔")


def test_enhance_and_pipeline_wiring() -> None:
    from autoblog import config, seo

    assert hasattr(config, "CONTEXTUAL_LINKS_MAX"), "config knob ledu"
    assert config.CONTEXTUAL_LINKS_MAX >= 1, config.CONTEXTUAL_LINKS_MAX
    src = read(ROOT / "autoblog" / "pipeline.py")
    assert "seo.attach_inline_image(" in src, "pipeline lo inline image wiring ledu"
    assert '"content_image"' in src, "post-gate publish-time list lo content_image ledu"
    # enhance() contextual links ni pilustunda
    from autoblog import validator
    body = ("<p>TSPSC Group 2 notification vachindi. Ee roju release ayyindi. "
            "Students andaru check cheyyali. Details ikkada unnayi.</p>") * 3
    out = seo.enhance(body, "TSPSC Group 2 Notification",
                      [{"title": "TSPSC Group 2 Notification 2026 – studentup.in",
                        "link": "https://studentup.in/tspsc"}], [])
    assert 'class="su-ctx"' in out, "enhance() lo contextual links wire avvaledu"
    assert validator.word_count(out) > 100, "enhance output tappu"
    print("      config knob · pipeline wiring · enhance() in-body link ✔")


# ------------------------------------------------------------------ 3
def test_validator_parity_checks() -> None:
    from autoblog import validator

    base = {
        "title": "TSPSC Group 2 Notification 2026 — Complete Details",
        "focus_keyword": "TSPSC Group 2 Notification",
        "meta_description": ("TSPSC Group 2 Notification 2026 details — eligibility, "
                             "dates, fees and how to apply. Official source link tho."),
        "slug": "tspsc-group-2-notification",
    }
    html = "<h2>TSPSC Group 2 Notification</h2><p>TSPSC Group 2 Notification text.</p>"
    res = validator.rankmath_strict(dict(base, content_html=html), html)
    items = {c["item"]: c for c in res["checks"]}
    assert "slug-length" in items, "slug-length check ledu"
    assert items["slug-length"]["ok"], "short slug fail ayyindi"
    # image ledu → conditional img-alt check add avvadu (gate fair)
    assert "kw-in-img-alt" not in items, "image lekunda img-alt check add ayyindi"
    # image unte → check vasthundi
    img_html = html + '<img src="https://x/y.webp" alt="TSPSC Group 2 Notification 2026">'
    items2 = {c["item"]: c for c in validator.rankmath_strict(
        dict(base, content_html=img_html), img_html)["checks"]}
    assert items2.get("kw-in-img-alt", {}).get("ok") is True, "kw alt tho fail ayyindi"
    bad = html + '<img src="https://x/y.webp" alt="random photo">'
    items3 = {c["item"]: c for c in validator.rankmath_strict(
        dict(base, content_html=bad), bad)["checks"]}
    assert items3["kw-in-img-alt"]["ok"] is False, "kw lekunda pass ayyindi"
    # pedda slug → fail (fixer guarantee ledu anedi pattukovali)
    long_slug = "tspsc-group-2-notification-" + "x" * 70
    items4 = {c["item"]: c for c in validator.rankmath_strict(
        dict(base, slug=long_slug, content_html=html), html)["checks"]}
    assert items4["slug-length"]["ok"] is False, "pedda slug pass ayyindi"
    print("      slug-length · img-alt conditional (fair) · honest fail ✔")


def test_rm100_slug_trim() -> None:
    from autoblog import rm100

    long_slug = "tspsc-group-2-notification-" + "-".join(["verylongsegment"] * 6)
    art = {"focus_keyword": "TSPSC Group 2 Notification", "slug": long_slug,
           "title": "x", "content_html": ""}
    assert rm100.fix_slug(art) is True, "pedda slug fix avvaledu"
    assert len(art["slug"]) <= 75, f"slug inka pedda: {len(art['slug'])}"
    assert "tspsc" in art["slug"], "keyword tokens poyayi"
    # short + tokens unte touch cheyyadu (False = no change)
    ok = {"focus_keyword": "TSPSC Group 2 Notification",
          "slug": "tspsc-group-2-notification", "title": "x", "content_html": ""}
    assert rm100.fix_slug(ok) is False, "manchi slug ni marchindi"
    print("      rm100 _trim_slug ≤75 · good slug untouched ✔")


def test_post_gate_content_image() -> None:
    from autoblog import post_gate

    res = post_gate.self_test()
    rows = {r["id"]: r for r in res["rows"]}
    assert "content_image" in rows, "post_gate lo content_image check ledu"
    assert rows["content_image"]["ok"] is True, rows["content_image"]["detail"]
    txt = post_gate.certificate_text(res)
    assert "68/68" in txt, "certificate 68/68 kaadu"
    assert "100/100" in txt, "certificate 100/100 kaadu"
    print(f"      content_image gate · certificate {res['score']}/100 · "
          f"{res['passed']}/{res['total']} checks ✔")


# ------------------------------------------------------------------ 4
def test_terms_page_built() -> None:
    builder = read(ROOT / "tools" / "build_policy_pages.py")
    assert "TERMS = \"\"\"" in builder, "TERMS body ledu"
    assert '("terms", "Terms of service",' in builder, "PAGE_DEFS lo terms ledu"
    for needle in ("Governing law", "copyright", "SPONSORED", "rel=\"sponsored nofollow\"",
                   "privacy.html", "disclaimer.html"):
        assert needle in builder, f"terms body lo '{needle}' ledu"
    page = ROOT / "preview" / "pages" / "terms.html"
    assert page.exists(), "preview/pages/terms.html ledu (builder run cheyandi)"
    html = read(page)
    assert html.count("<h2>") >= 8, "terms page lo sections takkuva"
    assert "Terms of service" in html and "studentup.in" in html, "terms page content tappu"
    assert 'href="terms.html"' in read(ROOT / "preview" / "pages" / "privacy.html"), \
        "privacy page nunchi terms link ledu"
    smap = read(ROOT / "preview" / "sitemap.xml")
    assert "terms.html" in smap, "sitemap lo terms ledu"
    print(f"      terms.html · {html.count('<h2>')} sections · nav + sitemap ✔")


def test_footer_has_terms_link() -> None:
    footer = read(THEME / "footer.php")
    assert "'terms'" in footer, "footer lo terms link ledu"
    for slug in ("privacy", "about", "contact", "disclaimer", "editorial-policy", "terms"):
        assert f"'{slug}'" in footer, f"footer lo {slug} ledu"
    print("      footer: 6 policy links (404-safe) ✔")


# ------------------------------------------------------------------ 5
def test_theme_assets_and_version() -> None:
    css = read(THEME / "style.css")
    php = re.search(r"STUDENTUP_VERSION',\s*'([^']+)'", read(THEME / "functions.php")).group(1)
    stable = re.search(r"Stable tag:\s*([\d.]+)", read(THEME / "readme.txt")).group(1)
    vcss = re.search(r"Version:\s*([\d.]+)", css).group(1)
    assert vcss == php == stable == "1.9.8", f"parity tappu: {vcss}·{php}·{stable}"
    for entry in ("= 1.9.4", "= 1.9.5", "= 1.9.6"):
        assert entry in read(THEME / "readme.txt"), f"changelog {entry} ledu"
    assert ".su-figure" in css and "su-figure figcaption" in css, "figure CSS ledu"
    assert "a.su-ctx" in css, "contextual link CSS ledu"
    print("      theme 1.9.6 · figure + su-ctx CSS · changelog ✔")


def test_suite_pins_and_docs() -> None:
    n = len(list((ROOT / "tests").glob("*_test.py")))
    assert n == SUITES_EXPECTED, f"suites {n} != {SUITES_EXPECTED}"
    for f in sorted((ROOT / "tests").glob("v*_test.py")):
        txt = read(f)
        m = re.search(r"SUITES_EXPECTED\s*=\s*(\d+)", txt)
        if m:
            assert int(m.group(1)) == SUITES_EXPECTED, f"{f.name} pin {m.group(1)} stale"
    readme = read(ROOT / "README.md")
    manual = read(ROOT / "MANUAL_ADVANCED_CHECKLIST.md")
    assert "v95" in readme, "README lo v95 ledu"
    assert "PART 52" in manual, "MANUAL lo PART 52 ledu"
    assert f"{SUITES_EXPECTED}/{SUITES_EXPECTED}" in readme, "README suites count stale"
    assert f"{SUITES_EXPECTED}/{SUITES_EXPECTED}" in manual, "MANUAL suites count stale"
    print(f"      suites {SUITES_EXPECTED} · README v95 · MANUAL PART 52 ✔")


def test_zip_sha_recorded() -> None:
    """GO_LIVE lo unna zip sha256 ↔ nijamaina zip sha256 (upload verify pin).

    v95 lo build ni reproducible chesam (fixed zip timestamps) — anduke ee pin
    stable: prathi `--test-all` lo zip rebuild ayyina sha same untundi.
    """
    import hashlib

    zip_path = ROOT / "wordpress-theme" / "studentup-theme.zip"
    actual = hashlib.sha256(zip_path.read_bytes()).hexdigest()
    go_live = read(ROOT / "GO_LIVE_CHECKLIST.md")
    assert actual in go_live, f"GO_LIVE lo zip sha stale — ippudu {actual}"
    src = read(ROOT / "tools" / "build_wp_theme.py")
    assert "date_time=fixed" in src or "ZipInfo(" in src, "build reproducible kaadu"
    print(f"      zip sha256 recorded + reproducible · {actual[:16]}… ✔")


def test_zip_packaged() -> None:
    zpath = ROOT / "wordpress-theme" / "studentup-theme.zip"
    assert zpath.exists(), "zip ledu"
    with zipfile.ZipFile(zpath) as z:
        names = z.namelist()
        assert len(names) >= 48, f"zip files {len(names)}"
        assert "studentup/footer.php" in names, "footer.php zip lo ledu"
        css = z.read("studentup/style.css").decode("utf-8")
        php = z.read("studentup/functions.php").decode("utf-8")
    assert re.search(r"Version:\s*1\.9\.8", css), "zip lo css version 1.9.8 kaadu"
    assert re.search(r"STUDENTUP_VERSION',\s*'1\.9\.8'", php), "zip lo php version 1.9.8 kaadu"
    assert ".su-figure" in css, "zip css lo su-figure ledu"
    print(f"      zip: {len(names)} files · theme 1.9.6 · su-figure inside ✔")


TESTS = [
    ("contextual links API", test_contextual_links_api),
    ("contextual links safety", test_contextual_links_safety),
    ("inline image API", test_attach_inline_image_api),
    ("enhance + pipeline wiring", test_enhance_and_pipeline_wiring),
    ("validator parity checks", test_validator_parity_checks),
    ("rm100 slug trim", test_rm100_slug_trim),
    ("post_gate content_image", test_post_gate_content_image),
    ("terms page built", test_terms_page_built),
    ("footer terms link", test_footer_has_terms_link),
    ("theme assets + 1.9.6", test_theme_assets_and_version),
    ("suite pins + docs", test_suite_pins_and_docs),
    ("zip sha recorded", test_zip_sha_recorded),
    ("zip packaged", test_zip_packaged),
]


def main() -> None:
    os.chdir(ROOT)
    print("=" * 70)
    print("v95 SEO-100 PIN-TO-PIN + TERMS + IN-BODY SIGNALS (theme 1.9.6)")
    print("=" * 70)
    failed = 0
    for name, fn in TESTS:
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
        raise SystemExit(1)
    print("ALL v95 SEO-100 + TERMS + IN-BODY TESTS PASSED ✔")


if __name__ == "__main__":
    main()
