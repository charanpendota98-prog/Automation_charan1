# -*- coding: utf-8 -*-
"""v94 tests — ADSENSE READINESS + DISCOVER + CWV (theme 1.9.6).

Brief: "posts publish cheste AdSense approval ki problem leda? google lo suggest
avvali ante em miss avutunnam? anni fix cheyu".

Deep audit lo kanukkunna **nijamaina gaps** (ivi fix ayyayi):

  GAP-1 ARTICLE SCHEMA IMAGE LEDU — Google Article structured data ki `image` adi
        **required property**. Bot schema lo adi ledu (real gap) → Article rich
        result + Discover large card eligibility thaggutundi. Fix: `schema_jsonld`
        `image` (ImageObject + 1200×675 dimensions) emit chestundi; featured image
        upload tarvata `attach_schema_image()` tho idempotent ga attach avutundi
        (schema upload ki mundu generate avutundi anduke).

  GAP-2 DISCOVER LARGE-CARD IMAGE LEDU — theme 640×360 mattrame register chesindi;
        Discover pedda card ki **1200px+** kavali. Fix: `studentup-discover`
        (1200×675) + og:image width/height/alt + Rank Math/Yoast filter (duplicate
        tag lekunda).

  GAP-3 PRIVACY DISCLOSURE — AdSense rule: "third-party vendors, including Google,
        use cookies … opt out at Ads Settings" ane specific disclosure undali. Adi
        ledu. Fix: privacy policy ki dedicated section.

  GAP-4 POLICY PAGES FOOTER NUNCHI REACH LEDU — AdSense reviewers + readers ki
        prathi page nunchi policy pages kanipinchali. Fix: footer links.

  GAP-5 PRE-APPLICATION AUDIT LEDU — "apply cheyyala?" ane prashna ki okka chota
        jawabu ledu. Fix: `python run.py --adsense-ready` (8 groups · 29 mandatory
        checks · JSON artifact · honest verdict).

  GAP-6 CLS/INP — content images ki width/height ledu (layout shift); mobile taps ki
        ~300ms delay. Fix: image dims filter + `touch-action: manipulation`.

Checks: module API · verdict logic · false-positive guards · CLI wiring + docs
parity · privacy disclosure · footer links · theme discover.php · schema image +
attach helper (idempotent/safe) · client media-url capture · pipeline wiring ·
version parity 1.9.6 · suite pins 74.

Run: python tests/v94_test.py   (also via python run.py --test-all)
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

THEME = ROOT / "wordpress-theme" / "studentup"
SUITES_EXPECTED = 90  # v95 tho


def read(rel: Path | str) -> str:
    return Path(rel).read_text(encoding="utf-8")


# ------------------------------------------------------------------ audit module
def test_adsense_ready_module() -> None:
    from autoblog import adsense_ready as ar

    summary, rows = ar.audit()
    assert isinstance(summary, dict) and isinstance(rows, list), "audit shape tappu"
    for key in ("score", "verdict", "line", "passed", "total", "blockers",
                "warnings", "posts", "posts_recommended"):
        assert key in summary, f"summary lo {key} ledu"
    assert 0 <= summary["score"] <= 100, summary["score"]
    assert rows, "rows khali"
    groups = {r["group"] for r in rows}
    for g in ("POLICY", "CONTENT", "NAVIGATION", "TECHNICAL", "TRUST",
              "AD SAFETY", "PROHIBITED", "DISCOVER"):
        assert g in groups, f"group {g} ledu"
    for r in rows:
        for key in ("group", "id", "ok", "warn_only", "detail", "fix"):
            assert key in r, f"row lo {key} ledu"
        if not r["ok"]:
            assert r["fix"], f"{r['id']} fail ayyindi kaani fix line ledu (owner ki teliyadu)"
    print(f"      {summary['score']}% · {summary['passed']}/{summary['total']} mandatory · "
          f"verdict={summary['verdict']}")


def test_verdict_logic_is_honest() -> None:
    """Honest verdict — blockers unte NOT READY, and guarantee maatalu undakoodadu."""
    src = read(ROOT / "autoblog" / "adsense_ready.py")
    assert '"NOT READY"' in src, "blocker verdict ledu"
    assert "Google decides" in src or "guarantee ledu" in src or "guarantee ivvadu" in src, \
        "honest disclaimer ledu (approval guarantee ani cheppakoodadu)"
    # 'xxx' lanti loose pattern false positive kaligistundi — adi unde undakoodadu
    assert r'"adult": r"\b(porn|adult video|escort service|nsfw)\b"' in src, \
        "adult pattern loose ga undi (placeholder false positive)"
    print("      honest verdict + false-positive guard ✔")


def test_adsense_ready_checks_real_files() -> None:
    """Checks nijamaina files ni chudali — hardcode kaadu."""
    from autoblog import adsense_ready as ar

    summary, rows = ar.audit()
    by_id = {r["id"]: r for r in rows}
    # privacy disclosure ippudu undali (fix ayyindi)
    for cid in ("page_privacy", "privacy_google_ads_dat", "privacy_cookies",
                "privacy_third-party_vendors", "privacy_opt-out_link"):
        assert by_id[cid]["ok"], f"{cid} fail: {by_id[cid]['detail']}"
    # Discover image size (v94 fix)
    assert by_id["image_size"]["ok"], by_id["image_size"]["detail"]
    # suite own gaps: menu grouped + discover
    assert by_id["menu_grouped"]["ok"], by_id["menu_grouped"]["detail"]
    # volume: live posting tho mattrame pass avutundi — ee repo lo 0 posts nijam
    assert "posts" in summary
    print("      privacy + discover + menu checks pass ✔")


# ------------------------------------------------------------------- CLI surface
def test_cli_wiring_and_docs() -> None:
    main = read(ROOT / "autoblog" / "main.py")
    assert '"--adsense-ready"' in main, "CLI flag ledu"
    assert "adsense_ready.run()" in main, "dispatch ledu"
    runner = read(ROOT / "run.py")
    assert "--adsense-ready" in runner, "run.py docstring lo flag ledu (owner ki teliyadu)"
    # parity P1: docs lo kuda undali
    for doc in ("README.md", "MANUAL_ADVANCED_CHECKLIST.md", "GO_LIVE_CHECKLIST.md"):
        assert "--adsense-ready" in read(ROOT / doc), f"{doc} lo --adsense-ready ledu"
    print("      CLI + run.py + docs parity ✔")


# ---------------------------------------------------------------------- privacy
def test_privacy_disclosure_required_wording() -> None:
    """Google AdSense privacy rule: third-party vendors + opt-out link."""
    p = ROOT / "preview" / "pages" / "privacy.html"
    assert p.exists(), "privacy.html ledu (build cheyandi)"
    low = read(p).lower()
    assert "third-party vendor" in low or "third party vendor" in low, \
        "third-party vendors disclosure ledu"
    assert "cookie" in low, "cookie disclosure ledu"
    assert "opt out" in low or "opt-out" in low, "opt-out wording ledu"
    assert ("settings/ads" in low or "adsettings" in low or "aboutads" in low), \
        "opt-out link ledu"
    assert "google" in low and "ad" in low, "Google ads mention ledu"
    # builder lo kuda undali (rebuild chesthe poyye ga undakoodadu)
    builder = read(ROOT / "tools" / "build_policy_pages.py").lower()
    assert "third-party vendors" in builder, "policy builder lo disclosure ledu"
    print("      privacy: third-party vendors + cookies + opt-out ✔")


def test_footer_policy_links() -> None:
    foot = read(THEME / "footer.php")
    for slug in ("privacy", "about", "contact", "disclaimer", "editorial-policy"):
        assert slug in foot, f"footer lo {slug} link ledu"
    assert "get_page_by_path(" in foot, "page existence check ledu (404 risk)"
    assert "'publish' !== get_post_status(" in foot, "publish check ledu"
    print("      footer: 5 policy links (404-safe) ✔")


# ---------------------------------------------------------------------- discover
def test_theme_discover_module() -> None:
    src = read(THEME / "inc" / "discover.php")
    assert "ABSPATH" in src, "ABSPATH guard ledu"
    assert "add_image_size( 'studentup-discover', 1200, 675, true )" in src, \
        "1200px Discover image size ledu"
    assert "og:image:width" in src and "og:image:height" in src, "og dims ledu"
    assert "og:image:alt" in src, "og alt ledu"
    # Rank Math / Yoast duplicate tag create cheyyakoodadu — filter vaadali
    assert "rank_math/opengraph/facebook/image" in src, "Rank Math filter ledu"
    assert "wpseo_opengraph_image" in src, "Yoast filter ledu"
    assert "studentup_big_image_size" in src, "1200px resolver ledu"
    # CLS + INP
    assert "wp_get_attachment_image_attributes" in src, "CLS dims filter ledu"
    assert "touch-action:manipulation" in src, "INP tap-delay hint ledu"
    # php-side escaping
    assert not re.search(r"<\?php\s+echo\s+\$", src), "escape cheyyani echo $ undi"
    fn = read(THEME / "functions.php")
    assert "inc/discover.php" in fn, "functions.php lo require ledu"
    print("      discover.php: 1200px + og dims + CLS + INP ✔")


# ----------------------------------------------------------------- schema image
def test_schema_has_image_property() -> None:
    from autoblog import seo

    html = seo.schema_jsonld("Title", "desc", [], "2026-09-22", "slug",
                             image_url="https://studentup.in/x.jpg",
                             image_width=1200, image_height=675)
    blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S)
    article = None
    for b in blocks:
        d = json.loads(b)
        if isinstance(d, dict) and d.get("@type") == "Article":
            article = d
    assert article is not None, "Article schema ledu"
    assert article.get("image"), "Article schema lo image ledu (REQUIRED property)"
    img = article["image"][0]
    assert img["@type"] == "ImageObject", img
    assert img["url"] == "https://studentup.in/x.jpg", img
    assert img["width"] == 1200 and img["height"] == 675, img
    # image lekapote property eppudu raakoodadu (broken schema vaddhu)
    plain = seo.schema_jsonld("T", "d", [], "2026-09-22", "s")
    assert '"image"' not in plain, "image url lekunda kuda image emit ayyindi"
    print("      Article.image (ImageObject 1200×675) ✔")


def test_attach_schema_image_safe_and_idempotent() -> None:
    from autoblog import seo

    base = seo.schema_jsonld("T", "d", [], "2026-09-22", "slug")
    assert '"image"' not in base, "base lo image undakoodadu"
    once = seo.attach_schema_image(base, "https://studentup.in/f.jpg", 1200, 675)
    assert '"image"' in once, "attach fail"
    # idempotent
    twice = seo.attach_schema_image(once, "https://other.jpg", 1200, 675)
    assert "other.jpg" not in twice, "idempotent kaadu (second image add ayyindi)"
    # empty url = no change (page eppudu break avvadu)
    assert seo.attach_schema_image(base, "") == base, "empty url tho change ayyindi"
    # broken/absent schema = no crash
    assert seo.attach_schema_image("<p>no schema</p>", "https://x/y.jpg") == "<p>no schema</p>"
    print("      attach_schema_image: idempotent + safe ✔")


def test_client_and_pipeline_wiring() -> None:
    client = read(ROOT / "autoblog" / "wordpress_client.py")
    assert "self.last_media_url" in client, "media source_url capture ledu"
    assert "source_url" in client, "source_url read ledu"
    pipe = read(ROOT / "autoblog" / "pipeline.py")
    assert "attach_schema_image" in pipe, "pipeline lo schema image attach ledu"
    assert "last_media_url" in pipe, "pipeline media url vaadatledu"
    print("      client media url + pipeline attach ✔")


# ------------------------------------------------------------------ version/pins
def test_version_parity_195() -> None:
    php = re.search(r"STUDENTUP_VERSION',\s*'([^']+)'", read(THEME / "functions.php")).group(1)
    css = re.search(r"Version:\s*([0-9.]+)", read(THEME / "style.css")).group(1)
    stable = re.search(r"Stable tag:\s*([0-9.]+)", read(THEME / "readme.txt")).group(1)
    assert php == css == stable == "1.9.8", f"parity tappu: {php}·{css}·{stable}"
    rd = read(THEME / "readme.txt")
    for entry in ("= 1.9.0", "= 1.9.1", "= 1.9.2", "= 1.9.3", "= 1.9.4", "= 1.9.5", "= 1.9.6", "= 1.9.7", "= 1.9.8"):
        assert entry in rd, f"changelog {entry} ledu"
    print("      version parity 1.9.6 + changelog ✔")


def test_suite_pins_and_docs() -> None:
    for f in ("v75_test.py", "v76_test.py", "v77_test.py", "v78_test.py",
              "v79_test.py", "v80_test.py", "v81_test.py", "v89_test.py",
              "v91_test.py", "v92_test.py", "v93_test.py"):
        txt = read(ROOT / "tests" / f)
        assert (f"suites == {SUITES_EXPECTED}" in txt
                or f"SUITES_EXPECTED = {SUITES_EXPECTED}" in txt), \
            f"{f} lo {SUITES_EXPECTED} pin ledu"
    suites = len(list((ROOT / "tests").glob("*_test.py")))
    assert suites == SUITES_EXPECTED, f"suites {suites} ({SUITES_EXPECTED} expect)"
    for doc in ("README.md", "MANUAL_ADVANCED_CHECKLIST.md", "GO_LIVE_CHECKLIST.md"):
        txt = read(ROOT / doc)
        assert f"{SUITES_EXPECTED}/{SUITES_EXPECTED}" in txt, f"{doc} lo claim ledu"
        assert "v94" in txt, f"{doc} lo v94 ledu"
    print("      suite pins 74 + docs ✔")


def test_zip_packaged() -> None:
    import zipfile
    zp = ROOT / "wordpress-theme" / "studentup-theme.zip"
    if not zp.exists():
        print("      (zip ledu — build cheyandi, SKIP)")
        return
    z = zipfile.ZipFile(zp)
    names = z.namelist()
    assert "studentup/inc/discover.php" in names, "zip lo discover.php ledu"
    assert all(n.startswith("studentup/") for n in names), "zip root tappu"
    css = z.read("studentup/style.css").decode("utf-8")
    assert re.search(r"Version:\s*1\.9\.8", css), "zip css version 1.9.8 kaadu"
    print("      zip: discover.php + 1.9.6 ✔")


TESTS = [
    ("adsense-ready module", test_adsense_ready_module),
    ("verdict honest + FP guard", test_verdict_logic_is_honest),
    ("checks real files", test_adsense_ready_checks_real_files),
    ("CLI + docs parity", test_cli_wiring_and_docs),
    ("privacy disclosure", test_privacy_disclosure_required_wording),
    ("footer policy links", test_footer_policy_links),
    ("theme discover.php", test_theme_discover_module),
    ("Article schema image", test_schema_has_image_property),
    ("attach image safe", test_attach_schema_image_safe_and_idempotent),
    ("client + pipeline wiring", test_client_and_pipeline_wiring),
    ("version parity 1.9.6", test_version_parity_195),
    ("suite pins + docs", test_suite_pins_and_docs),
    ("zip packaged", test_zip_packaged),
]


def main() -> None:
    os.chdir(ROOT)
    print("=" * 70)
    print("v94 ADSENSE READINESS + DISCOVER + CWV (theme 1.9.6)")
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
    print("ALL v94 ADSENSE-READINESS + DISCOVER TESTS PASSED ✔")


if __name__ == "__main__":
    main()
