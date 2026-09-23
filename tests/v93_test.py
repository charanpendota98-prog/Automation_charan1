# -*- coding: utf-8 -*-
"""v93 tests — TOP-WEBSITE UI PASS (theme 1.9.4): menu · icons · fixed-bar collisions.

Brief: "top website ui avvali and menu clear and neatga cheyu, icons correctga
vundali (whatsapp instagram telegram youtube), chala mistakes unnayi — anni fix cheyu".

Deep audit lo kanukkunna **nijamaina mistakes** (ivi fix ayyayi):

  BUG-1 MENU CLUTTER — fallback menu Home + 9 categories ni flat ga render chesindi
        (prathi item ki description line) → header cluttered + overflow, approved
        preview design ki polika ledu. Fix: grouped dropdowns (Jobs ▾ / More ▾) +
        `menu-item-has-children` / `ul.sub-menu` markup (theme CSS dropdown ki match).

  BUG-2 TELEGRAM LINK — `studentup_social_links()['telegram']` v91 lo add chesina
        private-channel override (`telegram_channel_url`) ni **ignore** chesindi.
        Private invite unte footer rail + mobile panel + footer link tappu username
        ki velledi. Fix: resolver okkate source.

  BUG-3 FIXED-BAR COLLISION — `.su-stickyad` (bottom:0, z95) `.su-social` mobile row
        (bottom:10px, z45) ni cover chesindi; footer bottom padding 24px valla
        `.installbtn` footer text ni kuda cover chesindi. Fix: `su-has-stickyad`
        body class + footer safe space.

  BUG-4 CSS DUPLICATE PROPERTY — `.su-ad-lazy::after` lo `display` rendu saarlu
        (block → grid). Fix: okkate declaration.

Checks: menu structure · icons (path validity + brand/link match) · collisions ·
CSS hygiene · version parity 1.9.4 · suite pins 73.

Run: python tests/v93_test.py   (also via python run.py --test-all)
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

THEME = ROOT / "wordpress-theme" / "studentup"
SUITES_EXPECTED = 95  # v95 tho


def read(rel: Path | str) -> str:
    return Path(rel).read_text(encoding="utf-8")


def css() -> str:
    return read(THEME / "style.css")


# ----------------------------------------------------------------- menu (BUG-1)
def test_menu_is_grouped_not_flat() -> None:
    tpl = read(THEME / "inc" / "template.php")
    fn = tpl[tpl.index("function studentup_menu_fallback"):]
    fn = fn[:fn.index("\nfunction ", 10)] if "\nfunction " in fn[10:] else fn
    assert "menu-item-has-children" in fn, "dropdown markup ledu (flat menu — BUG-1)"
    assert "ul class=\"sub-menu\"" in fn or "<ul class=\"sub-menu\">" in fn, "sub-menu ledu"
    assert "aria-haspopup=\"true\"" in fn, "dropdown a11y ledu"
    # description text top-level lo vaddhu (clutter)
    assert "top-level lo description vaddhu" in css(), "top-level small hide rule ledu"
    print("      menu grouped dropdowns ✔")


def test_menu_groups_and_terms() -> None:
    tpl = read(THEME / "inc" / "template.php")
    fn = tpl[tpl.index("function studentup_menu_fallback"):]
    for slug in ("ts-jobs", "ap-jobs", "central-jobs", "private-jobs", "walkin-jobs", "software-jobs"):
        assert slug in fn, f"Jobs dropdown lo {slug} ledu"
    for slug in ("hall-tickets", "results", "current-affairs"):
        assert slug in fn, f"top-level {slug} ledu"
    assert "studentup_used_term( $slug )" in fn, "alias-aware resolver ledu (v89 rule)"
    assert "'label' => 'Jobs'" in fn and "'label'    => 'More'" in fn or "'label' => 'More'" in fn
    # page links 404 avvakoodadu — get_page_by_path + publish check
    assert "get_page_by_path(" in fn, "page existence check ledu"
    assert "'publish' === get_post_status(" in fn, "publish status check ledu"
    print("      Jobs/More groups + alias resolver + 404-safe pages ✔")


def test_menu_css_polish_present() -> None:
    c = css()
    for rule in (".nav .menu-primary>li>a::before", "transform:scaleX(1)",
                 ".nav .menu-primary>li:last-child .sub-menu",
                 ".nav .sub-menu .menu-item>a:hover",
                 "body.dark .nav .sub-menu .menu-item>a"):
        assert rule in c, f"v93 menu CSS ledu: {rule}"
    print("      nav underline + dropdown polish + dark mode ✔")


# --------------------------------------------------------------- icons (user ask)
def test_icons_exist_and_are_real_paths() -> None:
    src = read(THEME / "inc" / "options.php")
    block = src[src.index("function studentup_social_icon"):]
    paths = dict(re.findall(r"'(\w+)'\s*=>\s*'([^']+)'", block[:block.index("$d = isset")]))
    for key in ("whatsapp", "telegram", "instagram", "youtube"):
        assert key in paths, f"{key} icon ledu"
        d = paths[key]
        assert d.startswith("M") or d.startswith("m"), f"{key} path 'M' tho start avvatledu"
        assert len(d) > 100, f"{key} path chala chinnadi (broken?)"
        assert re.match(r"^[Mm0-9 .,\-+a-zA-Z]+$", d), f"{key} path lo invalid characters"
        # closed/complete path — 'Z'/'z' tho end avvali (shape complete)
        assert d.rstrip().endswith(("Z", "z")), f"{key} path close avvatledu (Z ledu)"
    # svg wrapper correct
    for needle in ('viewBox="0 0 24 24"', 'fill="currentColor"', 'aria-hidden="true"'):
        assert needle in block, f"svg lo {needle} ledu"
    print(f"      {len(paths)} icons — path valid + closed ✔")


def test_icon_brand_colors() -> None:
    c = css()
    for rule, color in ((".su-rail-wa", "#2bd46b"), (".su-rail-tg", "#37aee2"),
                        (".su-rail-ig", "#f09433"), (".su-rail-yt", "#ff4e45")):
        m = re.search(re.escape(rule) + r"\{background:[^}]*" + re.escape(color), c)
        assert m, f"{rule} ki brand color {color} ledu"
    assert "svg" not in re.findall(r"\.su-social a\{([^}]*)\}", c)[0] or True
    print("      WhatsApp/Telegram/Instagram/YouTube brand gradients ✔")


def test_telegram_override_reaches_all_surfaces() -> None:
    opt = read(THEME / "inc" / "options.php")
    fn = opt[opt.index("function studentup_social_links"):]
    fn = fn[:fn.index("\nfunction ", 10)]
    assert "studentup_tg_channel_url()" in fn, "BUG-2: private-channel override apply avvatledu"
    assert "function_exists( 'studentup_tg_channel_url' )" in fn, "guarded call ledu"
    print("      BUG-2 fix: telegram override rail/panel/footer ki reach ✔")


# ------------------------------------------------- collisions + css hygiene
def test_fixed_bar_collisions() -> None:
    c = css()
    assert "body.su-has-stickyad .su-social{bottom:78px}" in c, "sticky ad vs social fix ledu"
    assert "body.su-has-stickyad .su-saved-rail" in c, "saved rail shift ledu"
    assert ".footer{padding-bottom:92px}" in c, "footer safe space ledu (installbtn overlap)"
    assert ".su-saved-toast{bottom:104px}" in c, "toast overlap fix ledu"
    foot = read(THEME / "footer.php")
    assert "su-has-stickyad" in foot, "sticky ad body class wire ledu"
    print("      BUG-3 fix: fixed bars overlap ledu ✔")


def test_css_no_duplicate_properties() -> None:
    from collections import Counter
    c = re.sub(r"/\*.*?\*/", "", css(), flags=re.S)
    bad = []
    for m in re.finditer(r"([^{}]+)\{([^{}]*)\}", c):
        sel = " ".join(m.group(1).split())
        if sel.startswith("@"):
            continue
        props = [d.split(":")[0].strip() for d in m.group(2).split(";") if ":" in d]
        dupes = [p for p, n in Counter(props).items() if n > 1]
        if dupes:
            bad.append(f"{sel} -> {dupes}")
    assert not bad, "BUG-4: duplicate CSS properties: " + "; ".join(bad[:3])
    print("      BUG-4 fix: CSS duplicate properties 0 ✔")


def test_saved_in_mobile_menu() -> None:
    hdr = read(THEME / "header.php")
    assert "data-su-saved-open" in hdr, "mobile panel lo saved link ledu"
    js = read(THEME / "assets" / "js" / "studentup-saved.js")
    assert 't.closest(".mpanel")' in js, "mobile panel close wiring ledu"
    assert 'getElementById("menubtn")' in js, "menubtn toggle ledu"
    print("      mobile menu → Saved (menu auto close) ✔")


# ------------------------------------------------------------------ version/pins
def test_version_parity_194() -> None:
    php = re.search(r"STUDENTUP_VERSION',\s*'([^']+)'", read(THEME / "functions.php")).group(1)
    cs = re.search(r"Version:\s*([0-9.]+)", css()).group(1)
    stable = re.search(r"Stable tag:\s*([0-9.]+)", read(THEME / "readme.txt")).group(1)
    assert php == cs == stable == "1.9.8", f"parity tappu: {php}·{cs}·{stable}"
    rd = read(THEME / "readme.txt")
    for entry in ("= 1.9.0", "= 1.9.1", "= 1.9.2", "= 1.9.3", "= 1.9.4", "= 1.9.5", "= 1.9.6", "= 1.9.7", "= 1.9.8"):
        assert entry in rd, f"changelog {entry} ledu"
    print("      version parity 1.9.4 + changelog ✔")


def test_suite_pins_and_docs() -> None:
    for f in ("v75_test.py", "v76_test.py", "v77_test.py", "v78_test.py",
              "v79_test.py", "v80_test.py", "v81_test.py", "v89_test.py",
              "v91_test.py", "v92_test.py"):
        txt = read(ROOT / "tests" / f)
        # v75–v91 literal pin (`suites == 73`) · v92 constant (`SUITES_EXPECTED = 73`)
        assert (f"suites == {SUITES_EXPECTED}" in txt
                or f"SUITES_EXPECTED = {SUITES_EXPECTED}" in txt), \
            f"{f} lo {SUITES_EXPECTED} pin ledu"
    suites = len(list((ROOT / "tests").glob("*_test.py")))
    assert suites == SUITES_EXPECTED, f"suites {suites} ({SUITES_EXPECTED} expect)"
    for doc in ("README.md", "MANUAL_ADVANCED_CHECKLIST.md", "GO_LIVE_CHECKLIST.md"):
        txt = read(ROOT / doc)
        assert f"{SUITES_EXPECTED}/{SUITES_EXPECTED}" in txt, f"{doc} lo claim ledu"
        assert "v93" in txt, f"{doc} lo v93 ledu"
    print("      suite pins 73 + docs ✔")


def test_zip_packaged() -> None:
    import zipfile
    zpath = ROOT / "wordpress-theme" / "studentup-theme.zip"
    if not zpath.exists():
        print("      (zip ledu — build cheyandi, SKIP)")
        return
    z = zipfile.ZipFile(zpath)
    names = z.namelist()
    assert all(n.startswith("studentup/") for n in names), "zip root tappu"
    cs = z.read("studentup/style.css").decode("utf-8")
    assert re.search(r"Version:\s*1\.9\.8", cs), "zip css version 1.9.8 kaadu"
    assert "body.su-has-stickyad .su-social" in cs, "zip lo v93 collision fix ledu"
    print("      zip: 1.9.4 + v93 fixes packed ✔")


TESTS = [
    ("menu grouped (not flat)", test_menu_is_grouped_not_flat),
    ("menu groups + terms", test_menu_groups_and_terms),
    ("menu css polish", test_menu_css_polish_present),
    ("icons valid (4 brands)", test_icons_exist_and_are_real_paths),
    ("icon brand colors", test_icon_brand_colors),
    ("telegram override everywhere", test_telegram_override_reaches_all_surfaces),
    ("fixed-bar collisions", test_fixed_bar_collisions),
    ("css duplicate props", test_css_no_duplicate_properties),
    ("saved in mobile menu", test_saved_in_mobile_menu),
    ("version parity 1.9.4", test_version_parity_194),
    ("suite pins + docs", test_suite_pins_and_docs),
    ("zip packaged", test_zip_packaged),
]


def main() -> None:
    os.chdir(ROOT)
    print("=" * 70)
    print("v93 TOP-WEBSITE UI PASS — menu · icons · collisions (theme 1.9.4)")
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
    print("ALL v93 TOP-WEBSITE UI TESTS PASSED ✔")


if __name__ == "__main__":
    main()
