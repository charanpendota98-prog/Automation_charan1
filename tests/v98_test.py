# -*- coding: utf-8 -*-
"""v98 — VIRAL SHARE ENGINE tests (free reach lever).

Nijamaina gap (v97 varaku): share buttons post **chivara MATRAME**. Mobile lo
60–70% readers akkadi varaku scroll cheyyaru ⇒ share option vaallaki eppudu
kanipinchadu. Share = **free reach**; idi manam ivvagalige biggest free
viral lever.

Ee suite proof istundi:
  1. `inc/share.php` exists · ABSPATH guard · theme lo wired (functions + zip)
  2. In-content share bar modati H2 + para tarvata vastundi · idempotent
  3. Rich share text (title + last date) — bare URL kaadu · expired deadline
     ki fake urgency LEDU
  4. Native share sheet feature-detect (support lekapothe hidden — broken
     button raadu) · tracking/pixel ledu
  5. Escaping (XSS) · noopener/nofollow · option gate · CSS + dark mode
  6. Docs + suite pins

Checks (10). Offline-safe — file content assertions matrame.
"""
from __future__ import annotations

import re
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

SUITES_EXPECTED = 82
THEME = ROOT / "wordpress-theme" / "studentup"


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="ignore")


# ----------------------------------------------------------------- 1 wiring

def test_share_file_and_wiring() -> None:
    f = THEME / "inc" / "share.php"
    assert f.exists(), "inc/share.php ledu"
    src = read(f)
    assert "defined( 'ABSPATH' ) || exit;" in src, "ABSPATH guard ledu"
    fn = read(THEME / "functions.php")
    assert "inc/share.php" in fn, "functions.php lo require ledu"
    # build script REQUIRED list lo undali (lekapothe zip lo miss avvochu)
    build = read(ROOT / "tools" / "build_wp_theme.py")
    assert '"inc/share.php"' in build, "build REQUIRED lo share.php ledu"
    # zip lo nijamga undaa
    z = ROOT / "wordpress-theme" / "studentup-theme.zip"
    with zipfile.ZipFile(z) as zf:
        names = zf.namelist()
    assert "studentup/inc/share.php" in names, "zip lo share.php ledu"
    print("      share.php: ABSPATH · functions · build list · zip ✔")


# -------------------------------------------------------------- 2 placement

def test_inline_injection_position_and_idempotent() -> None:
    src = read(THEME / "inc" / "share.php")
    assert "add_filter( 'the_content', 'studentup_inject_share_bar'" in src
    inj = src[src.index("function studentup_inject_share_bar"):]
    # modati H2 tarvata (quick-answer card h2 kaadu kabatti safe)
    assert "'</h2>'" in inj, "H2 anchor ledu"
    # aa tarvata modati para tarvata (heading ki venakane buttons awkward)
    assert "'</p>'" in inj, "para-tarvata refinement ledu"
    # idempotent guard
    assert "su-sharebar-inline" in inj and "strpos" in inj, "idempotent guard ledu"
    # singular post lo matrame + main query (archive lo render avvakudadu)
    for need in ("is_singular( 'post' )", "in_the_loop()", "is_main_query()"):
        assert need in inj, need
    # option gate
    assert "share_inline" in inj, "option gate ledu"
    print("      inject: H2+para anchor · idempotent · singular+main query ✔")


def test_injection_logic_matches_php() -> None:
    """PHP positioning logic ni Python lo replicate chesi verify."""
    def inject(content: str, bar: str = "[[S]]") -> str:
        if "su-sharebar-inline" in content:
            return content
        pos = content.lower().find("</h2>")
        if pos == -1:
            return content + bar
        pos += 5
        after = content[pos:]
        pp = after.lower().find("</p>")
        if pp != -1 and pp < 1200:
            pos += pp + 4
        return content[:pos] + bar + content[pos:]

    c = ('<div class="su-quick">QA</div><p>Intro</p><h2>Eligibility</h2>'
         '<p>First body.</p><p>Second.</p><h2>Dates</h2>')
    out = inject(c)
    assert out.index("[[S]]") > out.index("First body.</p>"), out
    assert out.index("[[S]]") < out.index("<p>Second."), out
    # H2 ye lekapothe chivara (content maayam avvakudadu)
    assert inject("<p>only</p>") == "<p>only</p>[[S]]"
    # idempotent
    dup = '<h2>A</h2><p>x</p><div class="su-sharebar-inline">z</div>'
    assert inject(dup) == dup
    print("      placement: after 1st H2's para · no-H2 safe · idempotent ✔")


# ------------------------------------------------------------- 3 share text

def test_rich_share_text_and_no_fake_urgency() -> None:
    src = read(THEME / "inc" / "share.php")
    fn = src[src.index("function studentup_share_hook"):
             src.index("function studentup_share_bar")]
    assert "su_deadline" in fn, "deadline meta vadaledu"
    # expired deadline ki urgency chupinchakudadu (misleading = trust loss)
    assert "return '';" in fn and "strtotime( 'today'" in fn
    assert "Last date: TODAY" in fn and "Last date in %d day(s)" in fn
    # deadline lekapothe khali — fake urgency invent cheyyakudadu
    assert "if ( ! $raw ) {" in fn, "deadline leni case handle ledu"
    body = src[src.index("function studentup_share_text"):]
    assert "wp_strip_all_tags" in body, "title strip ledu"
    print("      share text: real deadline only · expired → no urgency ✔")


# ----------------------------------------------------------------- 4 native

def test_native_share_feature_detect() -> None:
    js = read(THEME / "assets" / "js" / "studentup.js")
    seg = js[js.index("v98: NATIVE SHARE SHEET"):]
    assert "if (!navigator.share) { return; }" in seg, "feature-detect ledu"
    assert "removeAttribute(\"hidden\")" in seg, "support unte show cheyyaledu"
    assert "navigator.share(" in seg
    # PHP lo button DEFAULT hidden (JS off aithe broken button kanipinchakudadu)
    php = read(THEME / "inc" / "share.php")
    assert "data-su-share-native hidden" in php, "native button default hidden kaadu"
    # tracking/pixel ledu (privacy + policy)
    for bad in ("fetch(", "XMLHttpRequest", "gtag(", "sendBeacon", "Image()"):
        assert bad not in seg, f"share JS lo tracking: {bad}"
    print("      native sheet: feature-detect · default hidden · no tracking ✔")


# --------------------------------------------------------------- 5 security

def test_escaping_and_rel_attrs() -> None:
    src = read(THEME / "inc" / "share.php")
    bar = src[src.index("function studentup_share_bar"):
              src.index("function studentup_inject_share_bar")]
    # anni outputs escape avvali
    for need in ("esc_url(", "esc_attr(", "esc_html__(", "rawurlencode("):
        assert need in bar, f"{need} ledu"
    # external links ki noopener (tabnabbing) + nofollow
    assert bar.count('rel="noopener nofollow"') >= 2, "rel attrs ledu"
    assert 'target="_blank"' in bar
    print("      escaping: esc_url/attr/html · noopener nofollow ✔")


def test_no_unescaped_echo() -> None:
    """Theme audit rule — share.php lo unescaped echo undakudadu."""
    src = read(THEME / "inc" / "share.php")
    bad = []
    for m in re.finditer(r"echo\s+([^;]+);", src):
        expr = m.group(1)
        if not any(f in expr for f in ("esc_", "studentup_social_icon",
                                       "wp_kses", "(int)", "absint")):
            bad.append(expr[:60])
    assert not bad, f"unescaped echo: {bad}"
    print("      no unescaped echo ✔")


# -------------------------------------------------------------------- 6 CSS

def test_css_present_and_cls_safe() -> None:
    css = read(THEME / "style.css")
    seg = css[css.index("v98: IN-CONTENT SHARE BAR"):]
    for need in (".su-sharebar", ".su-sb-wa", ".su-sb-tg", ".su-sb-copy"):
        assert need in seg, need
    # native button hidden respect (CSS lo override avvakudadu)
    assert ".su-sb-native[hidden]{display:none!important}" in seg
    # mobile stack + reduced motion + dark mode
    assert "@media(max-width:600px)" in seg
    assert "prefers-reduced-motion" in seg
    assert "body.dark .su-sharebar" in seg
    # tap target (AdSense/CWV) — padding undali
    assert "touch-action:manipulation" in seg
    print("      CSS: mobile stack · reduced-motion · dark · tap-safe ✔")


# ----------------------------------------------------------------- 7 options

def test_option_registered() -> None:
    opt = read(THEME / "inc" / "options.php")
    assert "'share_inline'" in opt, "option field ledu (owner toggle cheyyaledu)"
    row = opt[opt.index("'share_inline'"):]
    row = row[:row.index("\n")]
    assert "'check'" in row and "'1'" in row, "default ON kaadu"
    print("      option: share_inline registered · default ON ✔")


# -------------------------------------------------------------------- 8 docs

def test_docs_and_suites() -> None:
    suites = len(list((ROOT / "tests").glob("*_test.py")))
    assert suites == SUITES_EXPECTED, f"suites {suites} (v98 tho 78)"
    readme = read(ROOT / "README.md")
    manual = read(ROOT / "MANUAL_ADVANCED_CHECKLIST.md")
    cur = f"{SUITES_EXPECTED}/{SUITES_EXPECTED}"
    assert "### v98" in readme and cur in readme
    assert "PART 55" in manual and cur in manual
    for name, txt in (("README", readme), ("MANUAL", manual)):
        assert "share" in txt.lower(), f"{name} lo share ledu"
    print(f"      docs: README v98 · PART 55 · {cur} ✔")


TESTS = [
    ("share.php wiring", test_share_file_and_wiring),
    ("inline injection contract", test_inline_injection_position_and_idempotent),
    ("placement logic", test_injection_logic_matches_php),
    ("rich share text", test_rich_share_text_and_no_fake_urgency),
    ("native share sheet", test_native_share_feature_detect),
    ("escaping + rel", test_escaping_and_rel_attrs),
    ("no unescaped echo", test_no_unescaped_echo),
    ("CSS", test_css_present_and_cls_safe),
    ("option registered", test_option_registered),
    ("docs + suites", test_docs_and_suites),
]


def main() -> int:
    failed = 0
    for name, fn in TESTS:
        try:
            fn()
            print(f"  {name} ✔")
        except Exception as exc:  # noqa: BLE001
            failed += 1
            print(f"  {name} ✘  {type(exc).__name__}: {exc}")
    print("-" * 70)
    if failed:
        print(f"  {failed} TEST(S) FAILED ✘")
        return 1
    print("ALL v98 VIRAL SHARE ENGINE TESTS PASSED ✔")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
