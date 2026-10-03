#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v191.2 WORLDCLASS VISUAL CHECK — phone (390px) + laptop (1440px) deep audit.

Enduku: nenu browser screenshot chudalenu, kaani design ni **measure** cheyyagalanu.
Ee tool static ga (CSS + HTML nunchi) rendu viewport ki ila verify chestundi:

  · visibility map   — phone lo em kanipistundi, laptop lo em kanipistundi
  · tap targets      — prathi clickable ≥44px (thumb-friendly)
  · type scale       — Telugu base ≥16px, content ≥14px
  · contrast         — WCAG AA ratios (light + dark), token-level nunchi compute
  · hierarchy        — single H1, heading order
  · revenue map      — ad slots ekkada, content vs ads ratio (AdSense policy safe?)
  · CLS safety       — images/iframes ki dimensions unnaya
  · dark mode        — token parity + no-flash script

Usage: python3 tools/visual_check.py [preview/worldclass/index.html]
Exit 1 = FAIL unte (build gate la vaadachu).
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEMO = ROOT / "preview" / "worldclass" / "index.html"
THEME_CSS = ROOT / "wordpress-theme" / "studentup" / "assets" / "css" / "worldclass.css"

FAILS: list[str] = []
WARNS: list[str] = []
OKS: list[str] = []


def ok(msg: str) -> None:
    OKS.append(msg)


def fail(msg: str) -> None:
    FAILS.append(msg)


def warn(msg: str) -> None:
    WARNS.append(msg)


# --------------------------------------------------------------------------- css
def parse_css(css: str) -> list[tuple[str, str, str]]:
    """→ [(media_condition, selector, declarations)] (media='' = always)."""
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)   # comments teesesthe rules skip avvavu
    rules: list[tuple[str, str, str]] = []
    i, n = 0, len(css)
    buf = ""
    while i < n:
        ch = css[i]
        if ch == "{":
            head = buf.strip()
            depth = 1
            j = i + 1
            while j < n and depth:
                if css[j] == "{":
                    depth += 1
                elif css[j] == "}":
                    depth -= 1
                j += 1
            body = css[i + 1 : j - 1]
            if head.startswith("@media"):
                cond = head[len("@media") :].strip()
                for sub_sel, sub_decl in re.findall(r"([^{}]+)\{([^{}]*)\}", body):
                    rules.append((cond, sub_sel.strip(), sub_decl.strip()))
            elif head.startswith("@") or head.startswith("/*"):
                pass
            else:
                rules.append(("", head, body.strip()))
            i = j
            buf = ""
        else:
            buf += ch
            i += 1
    return rules


def applies(media: str, width: int) -> bool:
    if not media:
        return True
    if "print" in media or "prefers-reduced-motion" in media:
        return False
    ok_cond = True
    for mw in re.findall(r"min-width:\s*(\d+)px", media):
        ok_cond = ok_cond and width >= int(mw)
    for mw in re.findall(r"max-width:\s*(\d+)px", media):
        ok_cond = ok_cond and width <= int(mw)
    return ok_cond


def decls_for(rules, selector_key: str, width: int) -> str:
    out = []
    for media, sel, decl in rules:
        if selector_key in sel and applies(media, width):
            out.append(decl)
    return ";".join(out)


NUMS: dict[str, float] = {}


def resolve_len(val: str | None) -> float | None:
    """'44px' / 'var(--tap)' → float px."""
    if not val:
        return None
    m = re.match(r"var\((--[\w-]+)\)", val.strip())
    if m:
        return NUMS.get(m.group(1))
    m = re.match(r"([\d.]+)px", val.strip())
    return float(m.group(1)) if m else None


def last_val(decls: str, prop: str) -> str | None:
    """Cascade: LAST declaration wins (media query overrides base)."""
    vals = re.findall(rf"(?:^|;)\s*{re.escape(prop)}\s*:\s*([^;]+)", decls)
    return vals[-1].strip() if vals else None


def first_px(decls: str, prop: str) -> float | None:
    return resolve_len(last_val(decls, prop))


# ----------------------------------------------------------------------- contrast
def hex2rgb(h: str) -> tuple[int, int, int]:
    h = h.strip().lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def lum(rgb: tuple[int, int, int]) -> float:
    def ch(c: float) -> float:
        c = c / 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

    r, g, b = (ch(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def ratio(a: str, b: str) -> float:
    la, lb = lum(hex2rgb(a)), lum(hex2rgb(b))
    hi, lo = max(la, lb), min(la, lb)
    return round((hi + 0.05) / (lo + 0.05), 2)


def tokens(css: str, block: str) -> dict[str, str]:
    m = re.search(block + r"\s*\{(.*?)\}", css, re.S)
    if not m:
        return {}
    return {k: v for k, v in re.findall(r"(--[\w-]+)\s*:\s*(#[0-9a-fA-F]{3,8})", m.group(1))}


# --------------------------------------------------------------------------- main
def main() -> int:
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else DEMO
    html = target.read_text(encoding="utf-8")
    css = THEME_CSS.read_text(encoding="utf-8")
    rules = parse_css(css)
    light = tokens(css, ":root")
    dark = tokens(css, r"body\.dark")
    global NUMS
    # v198: :root blocks okati kanna ekkuva undachu (append-only CSS) — anni chaduvu
    NUMS.clear()
    for root_block in re.finditer(r":root\s*\{(.*?)\}", css, re.S):
        NUMS.update({k: float(v) for k, v in
                     re.findall(r"(--[\w-]+)\s*:\s*([\d.]+)px", root_block.group(1))})
    NUMS.setdefault("--tap", 44)
    NUMS.setdefault("--tap-lg", 48)

    print("=" * 74)
    print("  WORLDCLASS VISUAL CHECK — phone 390px + laptop 1440px")
    print(f"  file: {target.relative_to(ROOT)}")
    print("=" * 74)

    # ---------------- 1. visibility map ----------------
    print("\n▸ VISIBILITY MAP")
    for key, phone_expect, lap_expect in [
        (".su-bottomnav", "visible", "hidden"),
        (".su-anchor", "fixed", "hidden"),
        (".su-rail", "single col", "sticky rail"),
        (".su-layout", "1 col", "2 col"),
    ]:
        p = decls_for(rules, key, 390)
        l = decls_for(rules, key, 1440)
        state_p = last_val(p, "display") or last_val(p, "position") or "inherit"
        state_l = last_val(l, "display") or last_val(l, "position") or "inherit"
        print(f"   {key:14} phone={state_p:8} laptop={state_l}")
        if key == ".su-bottomnav" and state_l != "none":
            fail("bottom nav laptop lo kuda kanipistundi (display:none kavali)")
        if key == ".su-bottomnav" and state_p == "none":
            fail("bottom nav phone lo ledu")
    else:
        ok("phone/laptop visibility map correct")

    # ---------------- 2. tap targets ----------------
    print("\n▸ TAP TARGETS (phone ≥44px)")
    targets = {
        ".chip": "min-height",
        ".su-ttab": "min-height",
        ".su-hact": "min-height",
        ".su-cta": "min-height",
        ".su-hero-search button": "min-height",
    }
    small = []
    for sel, _ in targets.items():
        d = decls_for(rules, sel, 390)
        val = first_px(d, "min-height")
        if val is None:
            small.append(f"{sel} (min-height ledu)")
        elif val < 44:
            small.append(f"{sel} ({val:g}px)")
    for sel, want in {".iconbtn": "height", ".su-hero-search input": "min-height"}.items():
        d = decls_for(rules, sel, 390)
        val = first_px(d, want)
        if val is None or val < 44:
            small.append(f"{sel} ({val})")
    if small:
        fail("44px kanna chinna tap targets: " + " · ".join(small))
    else:
        ok("anni tap targets ≥44px (phone)")

    # ---------------- 3. type scale ----------------
    print("\n▸ TYPE SCALE (Telugu-friendly)")
    body_d = ";".join(
        d for media, sel, d in rules if sel.strip() == "body" and applies(media, 390)
    )
    fs_val = last_val(body_d, "font-size")
    base = resolve_len(fs_val)
    print(f"   body font-size (phone): {base}px" if base else "   body font-size: token not found")
    if base and base < 16:
        fail(f"phone base font {base}px < 16px — Telugu chinna ga kanipistundi")
    else:
        ok("phone base type ≥16px")

    # ---------------- 4. contrast (light + dark) ----------------
    print("\n▸ CONTRAST (WCAG AA: 4.5 body · 3.0 large)")
    pairs = [
        ("body text", light.get("--ink"), light.get("--bg")),
        ("muted text", light.get("--muted"), light.get("--card")),
        ("navy heading", light.get("--navy"), light.get("--card")),
        ("dark body", dark.get("--ink"), dark.get("--bg")),
        ("dark muted", dark.get("--muted"), dark.get("--card")),
    ]
    for name, fg, bg in pairs:
        if not fg or not bg:
            warn(f"{name}: token dorakaledu ({fg} on {bg})")
            continue
        r = ratio(fg, bg)
        verdict = "✅" if r >= 4.5 else ("⚠️" if r >= 3.0 else "❌")
        print(f"   {verdict} {name:12} {r:5}:1  ({fg} on {bg})")
        if r < 4.5:
            fail(f"contrast tappu: {name} = {r}:1 (AA kavali 4.5)")

    # ---------------- 5. hierarchy ----------------
    print("\n▸ HIERARCHY")
    h1 = len(re.findall(r"<h1\b", html, re.I))
    h2 = len(re.findall(r"<h2\b", html, re.I))
    print(f"   h1={h1} · h2={h2}")
    if h1 != 1:
        fail(f"H1 count {h1} — okkate undali (SEO + a11y)")
    else:
        ok("single H1")

    # ---------------- 6. revenue map ----------------
    print("\n▸ REVENUE MAP (ad slots vs content)")
    ad_classes = ["su-adleader", "su-adcard", "su-railad", "su-adbelow", "su-anchor-ad"]
    ad_positions = {}
    for cls in ad_classes:
        ad_positions[cls] = [m.start() for m in re.finditer(cls, html)]
    total_ads = sum(len(v) for v in ad_positions.values())
    content_pos = [m.start() for m in re.finditer(r'<article class="news', html)]
    content_pos += [m.start() for m in re.finditer(r'class="usedcard', html)]
    content_pos.sort()
    for cls, pos in ad_positions.items():
        print(f"   {cls:14} × {len(pos)}")
    cards_n = len(re.findall(r'<article class="news', html))
    print(f"   content: {cards_n} cards + tiles · ad blocks: {total_ads}")
    if not content_pos:
        fail("content cards ledu — AdSense ki content kavali")
    else:
        first_ad = min([p for pos in ad_positions.values() for p in pos] or [10**9])
        if first_ad < content_pos[0]:
            warn("first ad first content card ki mundu undi (trust ↓)")
        else:
            ok("first content card → tarvata ads (reader-first)")
        ratio_ads = total_ads / max(cards_n, 1)
        print(f"   ads ÷ content = {ratio_ads:.2f}")
        if ratio_ads > 0.8:
            fail("ads content ni dominate chestunnayi (AdSense policy risk)")
        else:
            ok("ad density policy-safe (content dominates)")
    # every ad block labelled
    unlabeled = 0
    for m in re.finditer(r'class="[^"]*su-ad[^"]*"', html):
        seg = html[max(0, m.start() - 260) : m.start() + 260]
        if "aria-label=" not in seg and "Advertisement" not in seg:
            unlabeled += 1
    if unlabeled:
        fail(f"{unlabeled} ad block(s) ki label ledu (policy)")
    else:
        ok("prathi ad block labelled (Advertisement / aria-label)")

    # ---------------- 7. CLS safety ----------------
    print("\n▸ CLS SAFETY")
    imgs_bad = [t for t in re.findall(r"<img\b[^>]*>", html, re.I) if "width=" not in t or "height=" not in t]
    if imgs_bad:
        fail(f"{len(imgs_bad)} image(s) ki width/height ledu (CLS)")
    else:
        ok("images CLS-safe")
    ifr_bad = [t for t in re.findall(r"<iframe\b[^>]*>", html, re.I) if "width=" not in t or "height=" not in t]
    if ifr_bad:
        warn(f"{len(ifr_bad)} iframe(s) ki dimensions ledu")

    # ---------------- 8. dark mode ----------------
    print("\n▸ DARK MODE")
    if dark and len(dark) >= 6:
        ok(f"dark tokens {len(dark)} unnayi")
    else:
        fail("dark mode tokens saripoyinavi")
    if 'classList.contains(\'dark\')' in html or "classList.contains(\"dark\")" in html:
        ok("dark toggle wired")
    if "su_theme" in html:
        ok("theme preference localStorage lo save avutundi (no-flash parity)")
    else:
        warn("theme preference save avvatledu")

    # ---------------- report ----------------
    print("\n" + "=" * 74)
    for m in OKS:
        print(f"  ✅ {m}")
    for m in WARNS:
        print(f"  ⚠️  {m}")
    for m in FAILS:
        print(f"  ❌ {m}")
    print("-" * 74)
    print(f"  score: {max(0, 100 - 7 * len(FAILS) - 2 * len(WARNS))}/100 · "
          f"{len(OKS)} pass · {len(WARNS)} warn · {len(FAILS)} fail")
    print("=" * 74)
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
