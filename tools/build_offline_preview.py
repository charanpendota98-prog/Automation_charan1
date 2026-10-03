#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v196.1 — OFFLINE SINGLE-FILE PREVIEW builder (server avasaram ledu).

Enduku: sandbox prathi turn ki processes ni aapestundi → preview server eppudu
502 istundi. Anduke anni key pages ni **okate HTML file** lo (CSS inline, tab
navigation tho) build chestundi — ee file ni browser lo direct ga open cheyyachu,
server / port / proxy avasaram asalu ledu.

Pages: home demo · devices gallery · tools · ts-jobs hub · editorial team ·
exam calendar · internet-center pricing · corrections · privacy/terms.

Run: python3 tools/build_offline_preview.py
Out: preview/OFFLINE_PREVIEW.html
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PREVIEW = ROOT / "preview"
OUT = PREVIEW / "OFFLINE_PREVIEW.html"

PAGES = [
    ("home", "Home (demo)", PREVIEW / "worldclass" / "index.html"),
    ("devices", "Phone + Laptop", PREVIEW / "worldclass" / "devices.html"),
    ("tools", "Tools", PREVIEW / "tools" / "index.html"),
    ("hub", "TS Jobs hub", PREVIEW / "pages" / "ts-jobs-hub.html"),
    ("calendar", "Exam calendar (new)", PREVIEW / "pages" / "exam-calendar.html"),
    ("pricing", "Internet Center (new)", PREVIEW / "pages" / "internet-center.html"),
    ("corrections", "Corrections (new)", PREVIEW / "pages" / "corrections.html"),
    ("editorial", "Editorial team (new)", PREVIEW / "pages" / "editorial-team.html"),
    ("about", "About", PREVIEW / "pages" / "about.html"),
    ("privacy", "Privacy", PREVIEW / "pages" / "privacy.html"),
]

STYLES = [
    ROOT / "wordpress-theme" / "studentup" / "style.css",
    ROOT / "wordpress-theme" / "studentup" / "assets" / "css" / "worldclass.css",
]


def body_inner(html: str) -> str:
    m = re.search(r"<body[^>]*>(.*?)</body>", html, re.S | re.I)
    return m.group(1) if m else html


def page_style(html: str) -> str:
    return "\n".join(m.group(1) for m in re.finditer(r"<style[^>]*>(.*?)</style>", html, re.S | re.I))


def main() -> int:
    css = "\n".join(p.read_text(encoding="utf-8") for p in STYLES if p.exists())
    nav, slides = [], []
    for pid, label, path in PAGES:
        if not path.exists():
            print(f"  (skip {pid} — file ledu)")
            continue
        html = path.read_text(encoding="utf-8", errors="ignore")
        css += "\n" + page_style(html)
        nav.append(f'<button class="of-nav" type="button" data-t="{pid}">{label}</button>')
        slides.append(
            f'<section class="of-page" id="of-{pid}" data-p="{pid}" hidden>\n'
            f'<div class="of-bar">{label} <span class="of-note">· preview copy of the real page</span></div>\n'
            f'{body_inner(html)}\n</section>'
        )
        print(f"  ✔ {pid:<12} {label}")

    doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>StudentUp — offline preview (all pages)</title>
<style>
{css}
/* --- offline preview chrome (not part of the theme) --- */
.of-top{{position:sticky;top:0;z-index:9999;background:#0b2447;color:#fff;padding:8px 12px;
  display:flex;gap:8px;overflow-x:auto;align-items:center}}
.of-top b{{font-size:13px;white-space:nowrap;opacity:.9;margin-right:6px}}
.of-nav{{flex:0 0 auto;border:1px solid rgba(255,255,255,.35);background:rgba(255,255,255,.08);
  color:#fff;border-radius:999px;padding:7px 13px;font:700 12.5px/1 system-ui,sans-serif;cursor:pointer}}
.of-nav[aria-pressed="true"]{{background:#ed8a32;border-color:#ed8a32;color:#fff}}
.of-bar{{background:#eef4ff;color:#0b2447;font:700 12.5px/1.4 system-ui,sans-serif;padding:8px 14px;border-bottom:1px solid #d7e3f7}}
.of-note{{font-weight:600;opacity:.65}}
.of-page[hidden]{{display:none}}
</style>
</head>
<body>
<div class="of-top"><b>StudentUp preview</b>{''.join(nav)}</div>
{''.join(slides)}
<script>
(function(){{
  var btns = document.querySelectorAll('.of-nav');
  var pages = document.querySelectorAll('.of-page');
  function show(id){{
    pages.forEach(function(p){{ p.hidden = p.getAttribute('data-p') !== id; }});
    btns.forEach(function(b){{ b.setAttribute('aria-pressed', String(b.getAttribute('data-t') === id)); }});
    window.scrollTo(0,0);
  }}
  btns.forEach(function(b){{ b.addEventListener('click', function(){{ show(b.getAttribute('data-t')); }}); }});
  if (btns.length) {{ show(btns[0].getAttribute('data-t')); }}
}})();
</script>
</body>
</html>
"""
    OUT.write_text(doc, encoding="utf-8")
    print(f"\n  ✅ {OUT.relative_to(ROOT)} — {len(doc.encode('utf-8'))/1024:.0f} KB · self-contained (server avasaram ledu)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
