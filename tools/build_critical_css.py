#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v171 — CRITICAL CSS builder (above-the-fold inline layer).

Problem: style.css + premium.css (~154 KB min) render-blocking ga prathi
pageload lo first paint ni aapestundi — phone lo idi "slow open" feel ivtundi.

Fix (top-tier perf technique):
  1) Above-the-fold components (header · hero · ticker · cards · bottom nav ·
     apply bar · saved panel …) rules matrame extract chesi
     `assets/css/critical.min.css` build chestundi.
  2) Theme aa file ni <head> lo INLINE chestundi (0 extra request) mariyu
     full stylesheets ni async ga (media="print" → onload swap) load chestundi.
     Result: first paint ki waiting CSS ledu — FCP/LCP big jump.

Safety:
  * Extraction conservative — rule ani rewrite cheyyadu, select + copy matrame.
  * critical.min.css file lekapothe theme normal blocking path ki velthundi
    (zero-risk fallback).
  * Keyframes: above-fold lo vadatayi (slide · blip · suPulse) matrame.

Run: python3 tools/build_critical_css.py
"""
from __future__ import annotations

import re
import re as _re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
THEME = ROOT / "wordpress-theme" / "studentup"
SRC = [THEME / "style.css", THEME / "assets" / "css" / "premium.css",
       THEME / "assets" / "css" / "worldclass.css"]  # v191.3: new design above-fold
OUT = THEME / "assets" / "css" / "critical.css"
OUT_MIN = THEME / "assets" / "css" / "critical.min.css"

# Tokens (classes/elements) that are visible WITHOUT scrolling on home,
# post, archive and search pages. A rule is kept when ANY selector token
# matches. Prefix entries match longer variants (.su-hero- -> .su-hero-title).
EXACT = {
    ":root", ".wrap",
    ".screen-reader-text", ".skip-link", ".topbar", ".header", ".headrow",
    ".logo", ".custom-logo", ".nav", ".menu-primary", ".sub-menu",
    ".headactions", ".iconbtn", ".callbtn", ".menubtn", ".searchpanel",
    ".bluebtn", ".tickerwrap", ".tclip", ".tmove", ".tlabel", ".sectionhead",
    ".chips", ".chip", ".usedwrap", ".usedhead", ".usedgrid", ".usedcard",
    ".newsgrid", ".news", ".crumbs", ".article-head", ".article-meta",
    ".su-progress", ".su-social", ".su-tab", ".su-close", ".su-bnav",
    ".su-hdr-saved", ".su-saved-count", ".su-uicon",
    # v191.3 WORLDCLASS above-fold: lead card, trust, ad slots, fixed bottom nav
    ".news--lead", ".su-trust", ".su-viewall", ".su-bottomnav", ".su-anchor",
    ".su-anchor-ad", ".su-adleader", ".su-adcard", ".su-adbelow", ".su-bi",
    ".su-cta", ".su-ttab", ".su-tools", ".su-tooltabs", ".su-toolpanel",
    ".su-fields", ".su-tout", ".su-mini", ".su-rail", ".su-railed",
    ".su-railad", ".su-callout", ".su-layout", ".su-quizcard",
}
PREFIX = (
    ".su-hero", ".su-hs", ".su-live-dot", ".su-trend", ".su-statebar",
    ".su-sres", ".su-apply", ".spanel-", ".su-social", ".su-hact", ".su-am",
    ".su-ws",
)
KEYFRAMES = {"slide", "blip", "suPulse", "suSresIn"}
MEDIA_KEEP = ("screen", "all", "print")


def _split_rules(css: str):
    """Yield top-level blocks: ('rule', selector, body) | ('at', head, body)."""
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    i, n = 0, len(css)
    while i < n:
        if css[i].isspace():
            i += 1
            continue
        start = i
        depth = 0
        while i < n:
            c = css[i]
            if c == "{":
                depth += 1
                if depth == 1:
                    head = css[start:i].strip()
            elif c == "}":
                depth -= 1
                if depth == 0:
                    yield head, css[css.index("{", start) + 1: i]
                    i += 1
                    break
            elif c == ";" and depth == 0:
                # top-level statement (@import etc.) — keep as-is
                yield css[start:i], None
                break
            i += 1
        else:
            return


def _tokens(selector: str):
    sel = re.sub(r"[>~+]", " ", selector)
    return [t for t in sel.split() if t]


PLAIN_ELEMENTS = {
    "a", "img", "html", "body", "*", "input", "button", "select", "textarea",
    "h1", "h2", "h3", "h4", "h5", "h6", "p", "ul", "ol", "li", "table",
    "thead", "tbody", "tr", "th", "td", "strong", "b", "small", "span", "svg",
    ":root",
}


BODY_KEEP = {"body.dark", "body.su-has-applybar"}   # dark base vars + applybar body padding (CLS)


def _norm(tok: str) -> str:
    """Strip pseudo-classes, but keep leading-colon selectors (`:root`) intact."""
    return tok if tok.startswith(":") else tok.split(":")[0].split("::")[0]


def _match(selector: str) -> bool:
    """Above-fold selector aa?

    * class/id unna selector → component token (header/hero/news/…) undali.
      (leak fix: `.mpanel a`, `.su-upnext-item a` lanti rules generic `a`
      token tho raavakunda.)
    * class leni plain selector (`a`, `img`, `*`, `:root`, `h1`…) → keep (base).
    * `body.dark{…}` / `body.su-has-applybar{…}` — dark base + CLS padding.
    """
    # v192: first paint ki hover/focus states avasaram ledu — avi user interact
    # chesaka matrame kanipistayi, appatiki full CSS already load ayyi untundi.
    # (idi phone lo inline CSS bytes thagginchadam — FCP fast.)
    if _re.search(r":(hover|focus|focus-visible|focus-within|active)\b", selector):
        return False
    toks = _tokens(selector)
    if not toks:
        return False
    if len(toks) == 1 and toks[0] in BODY_KEEP:
        return True
    classes = [t for t in toks if t.startswith(".") or t.startswith("#") or "[" in t]
    plain = {_norm(t) for t in toks if t not in classes}
    plain_ok = plain <= PLAIN_ELEMENTS
    if not classes:
        return plain_ok
    for tok in toks:
        base = _norm(tok)
        if base in EXACT:
            return True
        for p in PREFIX:
            if base.startswith(p):
                return True
    return False


def extract() -> tuple[str, int]:
    out, kept, total = [], 0, 0
    for src in SRC:
        for head, body in _split_rules(src.read_text(encoding="utf-8")):
            if body is None:            # @import / charset — skip (full css lo untundi)
                continue
            total += 1
            head_l = head.lower()
            if head_l.startswith("@keyframes") or head_l.startswith("@-webkit-keyframes"):
                name = re.sub(r"@(-webkit-)?keyframes\s+", "", head, flags=re.I).strip()
                if name in KEYFRAMES:
                    out.append(f"{head}{{{body}}}")
                    kept += 1
                continue
            if head_l.startswith("@media"):
                inner_rules = re.findall(r"([^{}]+)\{([^{}]*)\}", body)
                keep = [f"{sel}{{{inner}}}" for sel, inner in inner_rules if _match(sel)]
                if keep:
                    out.append(f"{head}{{{''.join(keep)}}}")
                    kept += 1
                continue
            if head_l.startswith("@supports") or head_l.startswith("@font-face"):
                continue                 # below-fold / no webfonts
            # plain rule — selector list split on commas
            parts = [s for s in head.split(",") if _match(s.strip())]
            if parts:
                out.append(",".join(parts) + "{" + body + "}")
                kept += 1
    header = ("/* AUTO-GENERATED by tools/build_critical_css.py — v171 critical "
              "inline layer. Full CSS async ga vastundi; idi edit cheyyakandi. */\n")
    return header + "\n".join(out) + "\n", kept


CAP_WARN = 56000   # inc/critical-css.php hard cap 60000 — inka dhaatithe inline skip avutundi
CAP_FAIL = 59000   # build kuda fail — malli rule add cheyyakoodadu


def main() -> int:
    css, kept = extract()
    OUT.write_text(css, encoding="utf-8")
    # minify in place (reuse the conservative minifier)
    sys.path.insert(0, str(ROOT / "tools"))
    from minify_assets import minify_css  # noqa: E402
    OUT_MIN.write_text(minify_css(css), encoding="utf-8")
    raw_kb = OUT.stat().st_size / 1024
    min_kb = OUT_MIN.stat().st_size / 1024
    print(f"  ✅ critical.css  {raw_kb:.1f} KB raw → {min_kb:.1f} KB inline "
          f"({kept} rules kept) → {OUT.relative_to(ROOT)}")
    # v192: cap guard — inc/critical-css.php 60000 B dhaatithe silent ga inline
    # skip chestundi (phone lo purathana design flash). Ippude aapi cheptham.
    size = OUT_MIN.stat().st_size
    if size >= CAP_FAIL:
        print(f"  ❌ FAIL: critical.min.css {size} B ≥ {CAP_FAIL} — inline CAP 60000 ni "
              f"dhaatuthundi. Above-fold rule thagginchandi (hover/transition vaddu).")
        return 1
    if size >= CAP_WARN:
        print(f"  ⚠️  WARN: critical.min.css {size} B — CAP 60000 ki daggarlo undi "
              f"(ika {60000 - size} B migilinayi).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
