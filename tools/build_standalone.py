#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v193 — regenerate preview/worldclass/standalone.html from the live demo.

Why: standalone.html is the single-file version of the demo (CSS inlined, works
without any external request). It kept going STALE every time the design changed,
so nobody could trust it. Now it is generated — never hand-edited:

    demo (index.html)  →  same HTML, <link> tags replaced by inlined CSS

Run: python3 tools/build_standalone.py   (also runs inside the preview build)
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEMO = ROOT / "preview" / "worldclass" / "index.html"
OUT = ROOT / "preview" / "worldclass" / "standalone.html"
THEME = ROOT / "wordpress-theme" / "studentup"


def main() -> int:
    demo = DEMO.read_text(encoding="utf-8")
    title = "StudentUp — WorldClass v2 standalone (single file)"
    if OUT.exists():
        m = re.search(r"<title>([^<]*)</title>", OUT.read_text(encoding="utf-8"))
        if m:
            title = m.group(1)

    style_css = (THEME / "style.css").read_text(encoding="utf-8").rstrip("\n")
    wc_css = (THEME / "assets" / "css" / "worldclass.css").read_text(encoding="utf-8").rstrip("\n")

    # v201: demo live CSS stack ne load chestundi — style.css → premium.css → worldclass.css
    prem_css = (THEME / "assets" / "css" / "premium.css").read_text(encoding="utf-8").rstrip("\n")

    links = re.findall(r'<link rel="stylesheet" href="[^"]*">\n?', demo)
    if len(links) != 3:
        print(f"  ❌ demo lo {len(links)} stylesheet link(s) — 3 expect chesam (style·premium·worldclass)")
        return 1

    for i, css in enumerate((style_css, prem_css, wc_css)):
        out = demo.replace(links[i], f"<style>\n{css}\n</style>\n", 1)
        demo = out
    out = re.sub(r"<title>[^<]*</title>", f"<title>{title}</title>", out, count=1)

    # v197: theme JS bhi inline — single-file page must not fetch anything.
    def _inline_script(m: "re.Match[str]") -> str:
        src = m.group(1)
        target = (ROOT / src).resolve()
        if not target.exists() or THEME not in target.parents:
            return m.group(0)
        js = target.read_text(encoding="utf-8").rstrip("\n")
        return "<script>\n" + js + "\n</script>"

    out, n_js = re.subn(r'<script src="([^"]+)"[^>]*></script>', _inline_script, out)

    # a single-file page must not fetch external CSS/JS
    if 'rel="stylesheet"' in out:
        print("  ❌ standalone lo inka stylesheet link undi")
        return 1
    OUT.write_text(out, encoding="utf-8")
    print(f"  ✅ standalone.html  {len(out.encode()) / 1024:.0f} KB · CSS+JS inline ({n_js} script) · "
          f"demo tho 100% sync → {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
