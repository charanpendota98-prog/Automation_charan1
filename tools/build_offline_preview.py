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
    ("quiz", "Daily quiz + poll (new)", PREVIEW / "pages" / "daily-quiz.html"),
    ("calendar", "Exam calendar (new)", PREVIEW / "pages" / "exam-calendar.html"),
    ("pricing", "Internet Center (new)", PREVIEW / "pages" / "internet-center.html"),
    ("corrections", "Corrections (new)", PREVIEW / "pages" / "corrections.html"),
    ("editorial", "Editorial team (new)", PREVIEW / "pages" / "editorial-team.html"),
    ("post1", "Article: SSC CHSL", PREVIEW / "posts" / "upsc-junior-assistant-2026.html"),
    ("post2", "Article: internships", PREVIEW / "posts" / "engineering-internships-2026.html"),
    ("about", "About", PREVIEW / "pages" / "about.html"),
    ("privacy", "Privacy", PREVIEW / "pages" / "privacy.html"),
    # v197: migilina pages kuda — offline bundle lo anni links pani cheyyali.
    ("results", "Results hub", PREVIEW / "pages" / "results-hub.html"),
    ("scholarships", "Scholarships hub", PREVIEW / "pages" / "scholarships-hub.html"),
    ("contact", "Contact", PREVIEW / "pages" / "contact.html"),
    ("advertise", "Advertise", PREVIEW / "pages" / "advertise.html"),
    ("editorial-policy", "Editorial policy", PREVIEW / "pages" / "editorial-policy.html"),
    ("terms", "Terms", PREVIEW / "pages" / "terms.html"),
    ("disclaimer", "Disclaimer", PREVIEW / "pages" / "disclaimer.html"),
]

STYLES = [
    ROOT / "wordpress-theme" / "studentup" / "style.css",
    ROOT / "wordpress-theme" / "studentup" / "assets" / "css" / "worldclass.css",
]


def body_inner(html: str) -> str:
    m = re.search(r"<body[^>]*>(.*?)</body>", html, re.S | re.I)
    body = m.group(1) if m else html
    body = re.sub(r'src="\.\./assets/img/', 'src="assets/img/', body)
    return inline_theme_scripts(body)


def inline_theme_scripts(html: str) -> str:
    """v197: `<script src="../../wordpress-theme/...">` ni inline chey.

    Offline file lo external request eppudu pani cheyyadu — menu/quiz JS theme
    nunchi ne (single source of truth) teesukoni lopala pettamu.
    """
    def repl(m: "re.Match[str]") -> str:
        target = (ROOT / m.group(1)).resolve()
        if not target.exists():
            return ""
        js = target.read_text(encoding="utf-8").rstrip("\n")
        return "<script>\n" + js + "\n</script>"

    return re.sub(r'<script src="([^"]+)"[^>]*></script>', repl, html)


def page_style(html: str) -> str:
    return "\n".join(m.group(1) for m in re.finditer(r"<style[^>]*>(.*?)</style>", html, re.S | re.I))


# v197: preview lo unna relative links ni tab anchors ki map chestundi — offline
# single file lo relative paths pani cheyyavu (adi file-system layout ki vellayi).
LINK_TABS = {
    "../worldclass/index.html": "home", "index.html": "home",
    "../worldclass/devices.html": "devices",
    "../tools/index.html": "tools", "tools/index.html": "tools",
    "../tools/index.html?tool=age": "tools", "../tools/index.html?tool=salary": "tools",
    "../pages/ts-jobs-hub.html": "hub", "ts-jobs-hub.html": "hub",
    "../pages/daily-quiz.html": "quiz", "daily-quiz.html": "quiz",
    "../pages/exam-calendar.html": "calendar", "exam-calendar.html": "calendar",
    "../pages/internet-center.html": "pricing", "internet-center.html": "pricing",
    "../pages/corrections.html": "corrections", "corrections.html": "corrections",
    "../pages/editorial-team.html": "editorial", "editorial-team.html": "editorial",
    "../pages/about.html": "about", "about.html": "about",
    "../pages/privacy.html": "privacy", "privacy.html": "privacy",
    "../pages/results-hub.html": "results", "results-hub.html": "results",
    "../pages/scholarships-hub.html": "scholarships", "scholarships-hub.html": "scholarships",
    "../pages/contact.html": "contact", "contact.html": "contact",
    "../pages/advertise.html": "advertise", "advertise.html": "advertise",
    "../pages/editorial-policy.html": "editorial-policy", "editorial-policy.html": "editorial-policy",
    "../pages/terms.html": "terms", "terms.html": "terms",
    "../pages/disclaimer.html": "disclaimer", "disclaimer.html": "disclaimer",
    "../index.html": "home",
    "standalone.html": "home", "../worldclass/standalone.html": "home",
    "../posts/upsc-junior-assistant-2026.html": "post1",
    "../posts/engineering-internships-2026.html": "post2",
    "../posts/post-office-gds-2026.html": "post1",
    "../posts/ibps-clerk-2026.html": "post1",
    "../posts/rrb-ntpc-2026.html": "post1",
    "../posts/ap-police-constable-2026.html": "post1",
    "post-office-gds-2026.html": "post1",
    "ibps-clerk-2026.html": "post1",
    "rrb-ntpc-2026.html": "post1",
    "ap-police-constable-2026.html": "post1",
}


def retarget_links(html: str) -> str:
    """href="…/x.html[#frag]" → href="#of-<tab>" (jeevam unna tab navigation).

    v197.1: `.html#jobs` lanti fragment links kuda map chestam (327 links!) —
    fragment ni drop chestam, endukante aa section target tab lopala ne undi.
    """
    def repl(m: "re.Match[str]") -> str:
        href = m.group(1)
        base = href.split("?")[0].split("#")[0]
        tab = LINK_TABS.get(href) or LINK_TABS.get(base)
        if not tab:
            return m.group(0)
        return 'href="#of-%s"' % tab

    return re.sub(r'href="([^"]+\.html(?:\?[^"#]*)?(?:#[^"]*)?)"', repl, html)


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
            f'{retarget_links(body_inner(html))}\n</section>'
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
  /* v197: lopala unna links (#of-quiz lantivi) + browser back button pani cheyyali */
  function fromHash(){{
    var h = (location.hash || '').replace('#of-', '');
    if (h) show(h);
  }}
  window.addEventListener('hashchange', fromHash);
  fromHash();
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
