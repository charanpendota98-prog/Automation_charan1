# -*- coding: utf-8 -*-
"""v191 — WORLDCLASS v2 design gates (offline).

User ask: "ui theme ultra advanced ga, highest revenue vache la, neat ga undali …
100 times check chesko laptop lo and phone lo elaga vasthundi ani".

Ee suite aa maata ni **permanent gate** ga marchindi — design, revenue slots,
policy safety, phone/laptop parity anni prathi release lo verify avutayi:

  1. visual_check (phone 390 + laptop 1440): score 100/100, 0 fail
  2. CWV + a11y static audit: 0 errors (preview pages anni)
  3. Device gallery (devices.html): phone + laptop frames (lazy, sized) unnaya
  4. Money layout: front page lo ad slots + content kanna ads dominate cheyyavu
  5. Neat home: tools/quiz/stories widget wall HOME lo ledu (page-tools.php lo undi)
  6. Helpers: preview server (proxy-safe, port≠8090) + standalone build
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
THEME = ROOT / "wordpress-theme" / "studentup"
DEMO = ROOT / "preview" / "worldclass"


def _run(*args: str) -> tuple[int, str]:
    p = subprocess.run(
        [sys.executable, *args], cwd=str(ROOT), capture_output=True, text=True, timeout=300
    )
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def test_visual_check_green():
    code, out = _run("tools/visual_check.py")
    assert code == 0, "visual_check FAIL:\n" + "\n".join(out.splitlines()[-18:])
    m = re.search(r"score:\s*(\d+)/100\s*·\s*(\d+) pass · (\d+) warn · (\d+) fail", out)
    assert m, "visual_check score line ledu"
    score, passed, warns, fails = (int(x) for x in m.groups())
    assert score == 100 and fails == 0, f"design score {score}/100 ({fails} fail)"
    assert passed >= 10, f"checks takkuva: {passed}"
    print(f"  1. visual check phone 390 + laptop 1440 — {score}/100 · {passed} checks ✔")


def test_cwv_a11y_clean():
    code, out = _run("tools/cwv_audit.py")
    assert code == 0, "cwv_audit FAIL:\n" + "\n".join(out.splitlines()[-12:])
    m = re.search(r"errors\s+(\d+)\s+·\s+warnings\s+(\d+)", out)
    assert m, "cwv summary ledu"
    errors, warnings = int(m.group(1)), int(m.group(2))
    assert errors == 0, f"CWV/a11y errors: {errors}"
    print(f"  2. CWV + a11y static audit — 0 errors · {warnings} warn ✔")


def test_device_gallery():
    dev = DEMO / "devices.html"
    assert dev.exists(), "devices.html ledu (phone + laptop gallery)"
    html = dev.read_text(encoding="utf-8")
    for needle in ('id="f-phone"', 'id="f-lap"', 'width="390"', 'width="1440"'):
        assert needle in html, f"devices.html lo {needle} ledu"
    assert html.count('loading="lazy"') >= 2, "iframes lazy ledu (audit fail avutundi)"
    print("  3. device gallery — phone 390 + laptop 1440 frames (lazy, sized) ✔")


def test_money_layout():
    fp = (THEME / "front-page.php").read_text(encoding="utf-8")
    slots = ["studentup_ad( 'leaderboard' )", "studentup_ad( 'in-feed' )",
             "studentup_ad( 'mid' )", "studentup_ad( 'below-content' )"]
    for s in slots:
        assert s in fp, f"front-page lo ad slot ledu: {s}"
    # content-first: grid (money content) ad slots ki madhya lo, tools wall tarvata
    assert fp.index("studentup_ad( 'leaderboard' )") < fp.index('id="grid"'), \
        "leaderboard → grid order tappu (reader-first kavali)"
    assert fp.index('id="grid"') < fp.index("studentup_ad( 'below-content' )"), \
        "below-content ad grid tarvata undali"
    demo = (DEMO / "index.html").read_text(encoding="utf-8")
    cards = len(re.findall(r'<article class="news', demo))
    ads = sum(demo.count(c) for c in ("su-adleader", "su-adcard", "su-railad", "su-adbelow", "su-anchor-ad"))
    assert cards > 0 and ads > 0
    ratio = ads / cards
    assert ratio <= 0.8, f"ads content ni dominate chestunnayi ({ratio:.2f})"
    # prathi ad labelled (AdSense policy)
    for m in re.finditer(r'class="[^"]*su-ad[^"]*"', demo):
        seg = demo[max(0, m.start() - 260): m.start() + 260]
        assert "aria-label=" in seg or "Advertisement" in seg, "ad block ki label ledu"
    print(f"  4. money layout — 4 slots wired · demo {cards} cards vs {ads} ads ({ratio:.2f}) ✔")


def test_home_is_neat():
    fp = (THEME / "front-page.php").read_text(encoding="utf-8")
    # v197.1: owner ippudu quiz + poll ni EXPLICIT ga adigaru (engagement content,
    # calculator kaadu) — anduke avi banned list nunchi teesam. Kaani wall
    # avvakoodadu: oke quiz call + oke poll call, migilinavi anni banned.
    banned = ["studentup_tools_tabs", "studentup_stories",
              "studentup_for_you", "studentup_scholarship_strip", "studentup_salary_calc",
              "studentup_age_calculator_block", "studentup_resume_maker_block"]
    found = [b for b in banned if b in fp]
    assert not found, f"home lo widget wall inka undi: {found}"
    assert fp.count("studentup_daily_quiz(") == 1, "home lo quiz call okkate undali (wall vaddhu)"
    assert fp.count("studentup_daily_poll(") == 1, "home lo poll call okkate undali (wall vaddhu)"
    tools = THEME / "page-tools.php"
    assert tools.exists(), "page-tools.php ledu (tools ki separate page)"
    ts = tools.read_text(encoding="utf-8")
    assert "Template Name: StudentUp Tools" in ts and "studentup_tools_tabs" in ts
    assert "ABSPATH" in ts, "page-tools.php ki ABSPATH guard ledu"
    css = (THEME / "assets" / "css" / "worldclass.css").read_text(encoding="utf-8")
    for needle in ("min-height:44px", 'data-accent="ts"', ".su-adleader", ".su-adbelow",
                   "su-bottomnav", "prefers-reduced-motion"):
        assert needle in css, f"worldclass.css lo {needle} ledu"
    print("  5. neat home — widget wall poyindi · tools /tools/ page ki move · 44px + accents ✔")


def test_helpers():
    srv = (ROOT / "tools" / "preview_server.py").read_text(encoding="utf-8")
    assert "HTTP/1.1" in srv and "no-store" in srv, "preview server proxy-safe ledu"
    assert "8090" not in srv, "8090 old portal marker (v74) — veru port vaadandi"
    assert "302" in srv, "'/' → demo redirect ledu"
    standalone = DEMO / "standalone.html"
    assert standalone.exists(), "standalone.html ledu (server lekunda preview)"
    sh = standalone.read_text(encoding="utf-8")
    assert "<link" not in sh.split("<body")[0], "standalone lo external CSS links inka unnai"
    assert ".su-adleader" in sh and "su-bottomnav" in sh, "standalone lo worldclass CSS inline avvaledu"
    print("  6. helpers — proxy-safe server (port≠8090) + standalone single-file ✔")


def test_perf_and_a11y_gates():
    """v191.3/.4: speed + zoom + editor parity + mobile JS budget — permanent gates."""
    theme = THEME
    # 1) critical CSS lo kotha design undali (lekapthe phone lo first paint lo
    #    purathana design flash avutundi — "neat" pothundi)
    crit = (theme / "assets" / "css" / "critical.min.css").read_text(encoding="utf-8")
    for tok in ("su-bottomnav", "news--lead", "su-adleader", "su-trust"):
        assert tok in crit, f"critical.min.css lo {tok} ledu (first-paint flash)"
    assert len(crit.encode("utf-8")) < 60000, "critical CSS inline cap (60 KB) dhaatindi"
    # 2) pinch-zoom allowed (WCAG 1.4.4) — maximum-scale/user-scalable block undakoodadu
    head = (theme / "header.php").read_text(encoding="utf-8")
    import re as _re
    vp = _re.search(r'<meta name="viewport" content="([^"]+)"', head)
    assert vp, "viewport meta ledu"
    assert "user-scalable=no" not in vp.group(1) and "maximum-scale" not in vp.group(1), \
        f"viewport zoom block inka undi (a11y fail): {vp.group(1)}"
    assert "width=device-width" in vp.group(1), "viewport width=device-width ledu"
    wc = (theme / "assets" / "css" / "worldclass.css").read_text(encoding="utf-8")
    assert "touch-action:manipulation" in wc, "double-tap zoom guard ledu (touch-action)"
    # 3) real theme bottom nav (.su-bnav) kuda kotha design tho match avvali
    assert ".su-bnav" in wc and "su-bnav a.on" in wc, "real bottom nav redesign ledu"
    # 4) mobile JS budget: command palette (Ctrl+K) phone ki vaddu
    fns = (theme / "functions.php").read_text(encoding="utf-8")
    assert "wp_is_mobile()" in fns and "studentup-cmdk" in fns, "cmdk mobile gate ledu"
    # 5) Gutenberg editor palette = site palette (consistency)
    import json as _json
    tj = _json.loads((theme / "theme.json").read_text(encoding="utf-8"))
    colors = [c["color"].lower() for c in tj["settings"]["color"]["palette"]]
    assert "#0b2447" in colors and "#f08a24" in colors, "editor palette sync ledu"
    # 6) minified build fresh + lighter
    raw = (theme / "assets" / "css" / "worldclass.css").read_text(encoding="utf-8")
    mn = (theme / "assets" / "css" / "worldclass.min.css").read_text(encoding="utf-8")
    assert len(mn.encode()) < len(raw.encode()), "worldclass.min.css stale"
    print("  7. perf + a11y — critical CSS fresh · zoom ON · bnav match · cmdk desktop-only · editor palette ✔")

def test_sidebar_revenue_layout():
    """v191.5: desktop 2-col + sticky sidebar (300×250) — article pages lo RPM slot."""
    theme = THEME
    wc = (theme / "assets" / "css" / "worldclass.css").read_text(encoding="utf-8")
    for needle in (".su-layout{", ".su-sidebar{", ".su-sidebar-ad{", ":has(> .su-sidebar)"):
        assert needle in wc, f"worldclass.css lo {needle} ledu"
    for f in ("single.php", "archive.php", "search.php", "author.php"):
        t = (theme / f).read_text(encoding="utf-8")
        assert 'class="su-layout"' in t and 'class="su-main"' in t, f"{f}: 2-column layout ledu"
        assert "get_sidebar()" in t, f"{f}: sidebar call ledu"
    sb = (theme / "sidebar.php").read_text(encoding="utf-8")
    assert "studentup_ads_allowed( 'sidebar' )" in sb and "is_active_sidebar" in sb, "sidebar.php ad/widget guard ledu"
    crit = (theme / "assets" / "css" / "critical.min.css").read_text(encoding="utf-8")
    assert ".su-sidebar" in crit, "sidebar CSS critical lo ledu (FOUC)"
    print("  8. sidebar revenue — 4 templates 2-col · sticky 300×250 slot · guarded ✔")

def test_preview_pin_to_pin():
    """v193: prathi preview page okate design system (real theme CSS) vaadali.

    Mundu: pages/ + posts/ purathana design (veru palette), demo nunchi click
    cheste veru site la kanipinchedi. Ippudu anna okate shell.
    """
    import json as _json
    prev = ROOT / "preview"
    theme_css = ROOT / "wordpress-theme" / "studentup" / "assets" / "css" / "worldclass.css"

    # 1) pages + posts → real theme CSS (pin-to-pin by construction)
    for f in sorted((prev / "pages").glob("*.html")) + sorted((prev / "posts").glob("*.html")):
        h = f.read_text(encoding="utf-8")
        assert "assets/css/worldclass.css" in h, f"{f.name}: theme CSS link ledu"
        assert 'class="su-bottomnav"' in h, f"{f.name}: phone bottom nav ledu"
        assert 'class="su-foot"' in h and 'class="header"' in h, f"{f.name}: shared header/footer ledu"
        assert 'href="#"' not in h, f"{f.name}: dead href='#' link undi"
        assert "../wordpress-theme/studentup/style.css" in h, f"{f.name}: theme base CSS ledu"
    assert theme_css.exists(), "worldclass.css ledu"

    # 2) policy pages English-only (public legal text; AdSense/Ad review)
    for f in sorted((prev / "pages").glob("*.html")):
        h = f.read_text(encoding="utf-8")
        assert not __import__("re").findall("[\u0c00-\u0c7f]", h), f"{f.name}: Telugu undi (English-only rule)"

    # 3) article pages: real reading layout (mirrors single.php)
    for name in ("upsc-junior-assistant-2026.html", "engineering-internships-2026.html"):
        a = (prev / "posts" / name).read_text(encoding="utf-8")
        for needle in ('class="su-layout"', 'class="su-main"', 'class="su-sidebar"', "su-sidebar-ad",
                       'class="su-hook"', 'class="article-content"', "su-adleader", "su-adbelow"):
            assert needle in a, f"posts/{name}: {needle} ledu"
        assert '"@type":"Article"' in a, f"posts/{name}: Article schema ledu"
        assert a.count("<h2>") >= 3, f"posts/{name}: content thin (h2 < 3)"

    # 4) static home shares the design + phone nav
    home = (prev / "index.html").read_text(encoding="utf-8")
    assert "worldclass.css" in home and 'class="su-bottomnav"' in home, "static home design-nnav ledu"

    # 5) demo: functional filter + empty state + card data attributes
    demo = (prev / "worldclass" / "index.html").read_text(encoding="utf-8")
    assert "data-su-card" in demo and demo.count("data-su-card") >= 8, "demo cards ki data-su-card ledu"
    assert "su-empty" in demo, "empty state ledu"
    assert "CHIPS" in demo and "el.hidden = !ok" in demo, "chips nijamga filter avvatledu"
    assert 'href="../index.html"' not in demo, "demo lo purathana home ki link undi"

    # 6) tools page: real target for every "Tools" button (home lo tools undakoodadu)
    tools = prev / "tools" / "index.html"
    assert tools.exists(), "preview/tools/index.html ledu"
    th = tools.read_text(encoding="utf-8")
    for needle in ("assets/css/worldclass.css", 'class="su-tools"', 'role="tablist"',
                   "t-salary-out", "t-age-out", "t-score-out", "t-fee-out", 'class="su-anchor"'):
        assert needle in th, f"tools page: {needle} ledu"
    assert "function salary()" in th and "function fee()" in th, "tools JS pani cheyyadu"
    # dead anchor sweep: #tools ki link evaru ivvakoodadu (section ledu home lo)
    demo_path = prev / "worldclass" / "index.html"
    for f in list((prev / "pages").glob("*.html")) + list((prev / "posts").glob("*.html")) + [demo_path]:
        h = f.read_text(encoding="utf-8")
        assert 'href="#tools"' not in h, f"{f.name}: #tools dead anchor undi"
        assert "tools/index.html" in h, f"{f.name}: tools page ki link ledu"

    # 7) standalone = demo + inlined CSS (never hand-edited → never stale)
    st = (prev / "worldclass" / "standalone.html").read_text(encoding="utf-8")
    assert 'rel="stylesheet"' not in st, "standalone lo external stylesheet undi"
    assert "su-cov-mono" in st and "su-empty" in st, "standalone CSS stale"
    demo_body = demo.split("<body>", 1)[1]
    st_body = st.split("<body>", 1)[1]
    assert demo_body.strip() == st_body.strip(), "standalone body demo tho sync lo ledu"
    print("  9. preview pin-to-pin — pages+posts same theme CSS · demo filter · static home ✔")


def main() -> None:
    print("=" * 70)
    print("  v191 — WORLDCLASS v2: main enti → neat · money-first · phone+laptop")
    print("=" * 70)
    test_visual_check_green()
    test_cwv_a11y_clean()
    test_device_gallery()
    test_money_layout()
    test_home_is_neat()
    test_helpers()
    test_perf_and_a11y_gates()
    test_sidebar_revenue_layout()
    test_preview_pin_to_pin()
    print("-" * 70)
    print("ALL v191 WORLDC LASS TESTS PASSED ✔".replace("WORLDC LASS", "WORLDCLASS"))


if __name__ == "__main__":
    main()
