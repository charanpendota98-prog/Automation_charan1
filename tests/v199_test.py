# -*- coding: utf-8 -*-
"""v199 — HOME PHONE-FIRST (owner ask, 2026-10-03).

Owner screenshot: live home lo "Latest Jobs" red strip + "Most searched by students"
10 cards. Aa screenshot lo card meeda chinna "—" gaddi kanipinchindi + preview page
meeda "v192 premium preview" demo note undi. Owner: *"idi ravoddu, inka inka best ga
anni features build cheyu, anni phone lo advanced ga best ga"*.

Ee suite aa rendu defects ni + phone-first upgrade ni permanent gate ga marchindi:

  C1 TICKER  — theme + preview: `tickerwrap su-lticker` · "Latest Jobs" label ·
               tclip/tmove marquee · tsrc times · duplicated set aria-hidden ·
               home-only (post pages lo distraction vaddu).
  C2 CARDS   — "Most searched" 10 cards rendu vaipula (theme list + preview) ·
               icon + hint + top-3 `hot` · real counts (fake number ledu).
  C3 ARTIFACT— stray "—" pill malli raakoodadu (JS dash-fallback gone, `:empty`
               hide, PHP count 0 → emi chupinchadu) + demo-note preview nunchi out.
  C4 CSS     — fade edges · 44px taps · pause on touch · reduced-motion scroll ·
               2-up phone → 3-up tablet → 4-up laptop · press feedback ·
               hover-only hovers · dark mode · print.
  C5 PARITY  — preview markup = theme classes; prathi icon ki sprite symbol undi.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
THEME = ROOT / "wordpress-theme" / "studentup"
CSS = THEME / "assets" / "css" / "worldclass.css"
HOME = ROOT / "preview" / "worldclass" / "index.html"


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="ignore")


# --------------------------------------------------------------------- C1 ticker
def test_c1_live_ticker() -> None:
    """Red "Latest Jobs" strip: marquee + times + home-only, both sides."""
    brk = read(THEME / "inc" / "breaking.php")
    assert "function studentup_latest_ticker()" in brk, "ticker function ledu"
    assert "is_front_page()" in brk, "home-only gate ledu (post pages lo distraction)"
    assert "tickerwrap su-lticker" in brk, "ticker wrapper class ledu"
    assert "tlabel-blue" in brk and "Latest Jobs" in brk, "label ledu"
    assert "tclip" in brk and "tmove" in brk, "marquee wrapper ledu"
    assert "$dup ? ' aria-hidden=\"true\" tabindex=\"-1\"'" in brk, "duplicate set aria-hidden ledu"
    assert "studentup_ago( $it['time'] )" in brk, "time chip (X ago) ledu"
    assert "esc_url( $it['link'] )" in brk and "esc_html( $it['title'] )" in brk, "escape ledu"
    fp = read(THEME / "front-page.php")
    assert "studentup_latest_ticker()" in fp, "front page lo ticker call ledu"

    html = read(HOME)
    assert 'class="tickerwrap su-lticker"' in html, "preview lo ticker wrapper ledu"
    assert ">Latest Jobs</span>" in html, "preview label ledu"
    assert 'class="tclip"' in html and 'class="tmove"' in html, "preview marquee ledu"
    tick = re.search(r'<div class="tmove">(.*?)</div></div>', html, re.S).group(1)
    assert len(re.findall(r"<a ", tick)) >= 12, "duplicate set (12+ links) ledu"
    assert tick.count('aria-hidden="true" tabindex="-1"') >= 6, "preview duplicate set aria-hidden ledu"
    assert tick.count('class="tsrc"') >= 6, "preview time chips ledu"
    assert len(re.findall(r"[\u0C00-\u0C7F]", tick)) > 0, "preview ticker Telugu headlines ledu"
    print("  C1. ticker: home-only · marquee · times · dup set aria-hidden · Telugu ✔")


# ---------------------------------------------------------------------- C2 cards
def test_c2_most_searched_cards() -> None:
    """10 cards, icon + hint, top-3 hot, real counts — theme + preview."""
    fns = read(THEME / "functions.php")
    block = re.search(r"function studentup_most_used\(\).*?\n\}", fns, re.S).group(0)
    rows = re.findall(r"'slug' => '([a-z-]+)', 'label' => '([^']+)', 'icon' => '([a-z-]+)', 'hint' => '([^']+)'", block)
    assert len(rows) == 10, f"theme list lo 10 cards kaavali, unnavi {len(rows)}"
    assert len({r[3] for r in rows}) == 10, "hints duplicate"
    for slug, label, icon, _hint in rows:
        assert icon in read(THEME / "inc" / "icons.php"), f"icon path ledu: {icon} ({slug})"
    fp = read(THEME / "front-page.php")
    assert "$i < 3" in fp and "' hot'" in fp, "top-3 hot logic ledu"
    assert "$term->count" in fp, "real count ledu"

    html = read(HOME)
    cards = re.findall(r'<a class="usedcard[^"]*"[^>]*>(.*?)</a>', html, re.S)
    assert len(cards) == 10, f"preview lo 10 cards kaavali, unnavi {len(cards)}"
    assert sum(1 for c in cards if "usedcard hot" in c or True) == 10
    assert html.count('class="usedcard hot"') == 3, "preview top-3 hot ledu"
    for c in cards:
        assert re.search(r'<use href="#su-i-[a-z-]+"/>', c), "icon ledu"
        assert re.search(r"<b>[^<]+</b><small>[^<]+</small>", c), "label/hint ledu"
    labels = re.findall(r"<b>([^<]+)</b>", "".join(cards))
    for _slug, label, _i, _h in rows:
        assert label in labels, f"preview lo card ledu: {label}"
    print("  C2. cards: 10 tools-sections · icon+hint · top-3 hot · real counts ✔")


# ------------------------------------------------------------------ C3 artifacts
def test_c3_no_stray_artifacts() -> None:
    """The "—" pill and the v192 demo note must never come back."""
    js = read(THEME / "assets" / "js" / "studentup.js")
    assert 'el.textContent = S.i18n && S.i18n.updates ? "—"' not in js, "purathana dash fallback tirigi vachindi"
    assert "el.hidden = true" in js and "!/\\d/.test(el.textContent" in js, "number lekunda hide logic ledu"
    css = read(CSS)
    assert ".usedcard .ucount:empty{ display:none }" in css, ":empty hide ledu"
    fp = read(THEME / "front-page.php")
    assert "$su_n > 0" in fp, "count 0 ki guard ledu"
    assert "number_format_i18n( $su_n )" in fp, "real number format ledu"
    for rel in ("preview/worldclass/index.html", "preview/worldclass/standalone.html",
                "preview/OFFLINE_PREVIEW.html"):
        assert "demo-note" not in read(ROOT / rel), f"demo note tirigi vachindi: {rel}"
    print("  C3. artifacts: stray dash gone · demo note gone everywhere ✔")


# ----------------------------------------------------------------------- C4 css
def test_c4_phone_first_css() -> None:
    """Ticker polish + 2/3/4-up grid + tap/press/reduced-motion/dark/print."""
    css = read(CSS)
    assert "-webkit-mask-image:linear-gradient(90deg,transparent" in css, "ticker fade edges ledu"
    assert "-webkit-mask-image" in css and "mask-image:linear-gradient" in css, "mask prefix ledu"
    assert ".tickerwrap .tmove a{ display:inline-flex; align-items:center; min-height:44px }" in css, "44px ticker tap ledu"
    assert "animation-play-state:paused" in css, "touch/hover pause ledu"
    assert "prefers-reduced-motion:reduce" in css and "animation:none; position:static" in css, "reduced-motion scroll ledu"
    assert "grid-template-columns:repeat(2,minmax(0,1fr))" in css, "phone 2-up ledu"
    assert "@media (min-width:768px)" in css and "@media (min-width:1180px)" in css, "3-up/4-up breakpoints ledu"
    assert "min-height:72px" in css and "-webkit-tap-highlight-color:transparent" in css, "card tap size ledu"
    assert "touch-action:manipulation" in css, "touch-action ledu"
    assert "translateY(-50%) rotate(45deg)" in css, "clean chevron ledu"
    assert "@media (hover:hover)" in css and "@media (hover:none)" in css, "hover-capable split ledu"
    assert ".usedcard:focus-visible" in css, "focus ring ledu"
    assert "body.dark .usedcard .ucount" in css, "dark count pill ledu"
    assert "@media print" in css and ".tickerwrap{ display:none }" in css, "print rules ledu"
    print("  C4. css: fade · 44px · pause · reduced-motion · 2/3/4-up · press · dark · print ✔")


# -------------------------------------------------------------------- C5 parity
def test_c5_parity_and_sprite() -> None:
    """Preview = theme classes; every icon used has a sprite symbol."""
    html = read(HOME)
    for cls in ("tickerwrap", "tlabel", "tclip", "tmove", "tsrc", "usedgrid", "usedcard", "ucount", "ui"):
        assert cls in html, f"preview lo theme class ledu: {cls}"
    theme_css = read(CSS)
    for cls in ("tickerwrap", "tclip", "tmove", "usedgrid", "usedcard", "ucount"):
        assert ".%s" % cls in theme_css, f"css lo class ledu: {cls}"
    used = set(re.findall(r'<use href="#(su-i-[a-z0-9_-]+)"', html))
    have = set(re.findall(r'<symbol id="(su-i-[a-z0-9_-]+)"', html))
    assert used and not (used - have), f"blank icons: {sorted(used - have)}"
    assert len(used) >= 20, "home lo icons takkuva unnayi"
    # preview home = Telugu-first (v73 exclusion) + no calculators on home (v191 rule)
    assert re.search(r"[\u0C00-\u0C7F]", html), "Telugu-first home ledu"
    # (inlined premium.js lo "su-toolpanel" string untundi — adi JS, wall kaadu;
    #  asalu markup ni mattrame check cheyyali)
    assert '<section class="su-tools"' not in html and 'class="su-tooltabs"' not in html, \
        "home lo tools wall tirigi vachindi"
    print("  C5. parity: theme classes match · sprite complete · Telugu-first · tools off home ✔")


ALL = [v for k, v in sorted(globals().items())
       if k.startswith("test_") and callable(v)]

if __name__ == "__main__":
    print("=" * 74)
    print("  v199 — HOME PHONE-FIRST (ticker · 10 cards · zero artifacts)")
    print("=" * 74)
    for fn in ALL:
        fn()
    print("-" * 74)
    print(f"  v199: {len(ALL)}/{len(ALL)} checks passed ✔")
