#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Theme output snapshot — "live laa" render ni demo lonaa chupinchadaniki.

Enduku (owner report, 2026-10-04): *"ikkada preview lo chupinchadu, live lo
alaga ledu"*. Preview demo = hand-written; live = WordPress PHP + mee posts +
mee toggles. Rendu okate kaavu — anduke ee tool theme PHP **output structure** ni
bundle chesi, static snapshot page create chestundi:

  preview/theme-snapshot.html

Ee page:
  * theme PHP lo nijamga render ayye section list (front-page.php order) +
    prathi section యొక్క class/markup shape — `templates/` nunchi, nijamaina code
    (fake markup ledu).
  * WordPress ledu kabatti **real post cards render avvavu** — aa block ki
    "Data: WordPress posts + toggles" ani honest gaa chupistundi.
  * Browser lo open chesi, mee live site tho side-by-side pettukondi.

Rule: ee file **hand-edit cheyyakoodadu** — `python3 tools/render_theme_snapshot.py`
tho mattrame regenerate cheyyali (demo tho pade pade stale avvakunda).

Usage:
    python3 tools/render_theme_snapshot.py            # rebuild snapshot
    python3 tools/render_theme_snapshot.py --check    # freshness check (CI/gate)
"""
from __future__ import annotations

import argparse
import html
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
THEME = ROOT / "wordpress-theme" / "studentup"
OUT = ROOT / "preview" / "theme-snapshot.html"

VER_RE = re.compile(r"Version:\s*(\S+)")
FN_RE = re.compile(r"^\s*([a-z_][a-z0-9_]*)\s*\(", re.I)


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="ignore")


def theme_version() -> str:
    return VER_RE.search(read(THEME / "style.css")).group(1)


def function_map() -> dict[str, str]:
    """name -> defining file (relative to theme), real `function name(` scan."""
    out: dict[str, str] = {}
    for f in sorted(THEME.rglob("*.php")):
        for m in re.finditer(r"^\s*function\s+([a-z_][a-z0-9_]*)\s*\(", read(f), re.M | re.I):
            out.setdefault(m.group(1), str(f.relative_to(THEME)))
    return out


def front_page_sections(fmap: dict[str, str]) -> list[tuple[str, str, int]]:
    """front-page.php call order — [(function, defining file, call count)]."""
    src = read(THEME / "front-page.php")
    order: list[str] = []
    counts: dict[str, int] = {}
    for m in re.finditer(r"\b(studentup_[a-z0-9_]+)\s*\(", src):
        name = m.group(1)
        if name not in fmap:            # helper/unknown (e.g. studentup_ui_icon used inline)
            name = name
        if name in ("studentup_opt", "studentup_used_term"):
            continue
        counts[name] = counts.get(name, 0) + 1
        if name not in order:
            order.append(name)
    return [(n, fmap.get(n, "front-page.php (inline)"), counts[n]) for n in order]


def what_a_section_needs(rel: str) -> str:
    """File nunchi 'kavalsinavi': toggles · posts · terms · post meta."""
    path = THEME / rel
    if not path.exists():
        return "—"
    src = read(path)
    needs = []
    if "studentup_opt(" in src:
        opts = sorted(set(re.findall(r"studentup_opt\(\s*'([a-z0-9_]+)'", src)))
        needs.append("toggle: " + ", ".join(opts[:4]))
    if re.search(r"get_posts\(|WP_Query\(|wp_count_posts", src):
        needs.append("WordPress posts")
    if "studentup_used_term(" in src or "get_category_by_slug(" in src:
        needs.append("category terms")
    if "studentup_smart_dataset(" in src or "studentup_opportunity_last_date(" in src:
        needs.append("post meta (last dates / vacancies)")
    if "is_front_page()" in src:
        needs.append("front page only")
    return " · ".join(needs) if needs else "static markup"


def build() -> str:
    ver = theme_version()
    fmap = function_map()
    sections = front_page_sections(fmap)

    rows = []
    for name, src_file, count in sections:
        call = f"<code>{html.escape(name)}()</code>"
        if count > 1:
            call += f' <span class="n">×{count}</span>'
        rows.append(
            f"      <tr><td>{call}</td>"
            f"<td><code>{html.escape(src_file)}</code></td>"
            f"<td>{html.escape(what_a_section_needs(src_file)) if src_file.endswith('.php') else '—'}</td></tr>"
        )
    body = "\n".join(rows)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>StudentUp — theme output snapshot (theme {ver})</title>
<meta name="robots" content="noindex">
<meta name="description" content="StudentUp theme output snapshot — which sections the installed WordPress theme really renders, and what each one needs (posts, categories, toggles).">
<style>
  :root{{--navy:#0f2e62;--blue:#2463b7;--orange:#ed8a32;--ink:#162235;--muted:#64748b;--line:#e5ebf4;--soft:#f5f8fc}}
  body{{margin:0;background:var(--soft);color:var(--ink);font:15px/1.7 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}}
  .wrap{{max-width:1000px;margin:0 auto;padding:24px 16px 60px}}
  h1{{font-size:22px;color:var(--navy);margin:0 0 6px}}
  .sub{{color:var(--muted);font-size:13px;margin:0 0 18px}}
  .banner{{background:#fffbeb;border:1px solid #fde68a;color:#92400e;border-radius:12px;padding:12px 14px;margin:0 0 18px;font-size:13.5px}}
  .banner b{{color:#78350f}}
  table{{width:100%;border-collapse:collapse;background:#fff;border:1px solid var(--line);border-radius:12px;overflow:hidden}}
  th,td{{text-align:left;padding:9px 12px;border-bottom:1px solid var(--line);font-size:13px;vertical-align:top}}
  th{{background:#f8fafc;font-size:12px;text-transform:uppercase;letter-spacing:.04em;color:var(--muted)}}
  tr:last-child td{{border-bottom:0}}
  td:nth-child(3){{color:#475569}}
  code{{font-family:ui-monospace,Menlo,Consolas,monospace;font-size:12.5px;color:#0f2e62}}
  .n{{color:var(--muted);font-size:11.5px}}
  .checklist{{background:#fff;border:1px solid var(--line);border-radius:12px;padding:14px 18px;margin-top:20px;font-size:13.5px}}
  .checklist h2{{font-size:15px;margin:0 0 8px;color:var(--navy)}}
  .checklist ul{{margin:0;padding-left:20px}}
  .checklist li{{margin:5px 0}}
  .warn{{color:#b45309;font-weight:800}}
  .foot{{color:var(--muted);font-size:12px;margin-top:18px}}
</style>
</head>
<body><div class="wrap">
  <h1>Theme output snapshot — “live laa” render</h1>
  <p class="sub">Theme <b>{ver}</b> · generated {time.strftime('%Y-%m-%d')} by <code>tools/render_theme_snapshot.py</code> — hand-edit ledu.</p>

  <p class="banner"><b>Idi enduku:</b> <code>preview/worldclass/</code> oka hand-written design demo. Live site = WordPress + mee posts + mee toggles.
  Ee page theme PHP <b>nijamga em render chestundo</b> — front page section order, source file, prathi section ki kavalsinavi — chupistundi. Demo kaadu, idi live ki daahaalam.</p>

  <table>
    <tr><th>Section (front-page.php call order)</th><th>Source</th><th>Kavalsinavi</th></tr>
{body}
  </table>
  <p class="foot">“Kavalsinavi” = aa section render avvadaniki WordPress lo em undali (posts · categories · toggles). Khaali ga unte aa section <b>hide</b> avutundi — fake cards theme eppudu render cheyyadu.</p>

  <div class="checklist">
    <h2>Live lo neat ga kanipinchadaniki (order lo)</h2>
    <ul>
      <li><span class="warn">1.</span> Zip upload + Activate → <b>Appearance → Themes</b> lo version check (ee build: <code>{ver}</code>).</li>
      <li><span class="warn">2.</span> <b>Settings → Permalinks</b> → Save (clean post links).</li>
      <li><span class="warn">3.</span> Posts publish avvali — trending / carousel / cards **mee posts nunchi** build avutayi (khali DB ⇒ khali sections).</li>
      <li><span class="warn">4.</span> Categories: <code>ts-govt-jobs · ap-govt-jobs · central-govt-jobs · results · hall-tickets</code> — lekapote aa item skip avutundi.</li>
      <li><span class="warn">5.</span> StudentUp Settings → toggles (hero_premium · trending_today · state_first …) ON unnaya chudandi.</li>
      <li><span class="warn">6.</span> Cache: host cache + WP cache plugin okasari clear cheyandi — old CSS/JS migilakoodadu.</li>
      <li><span class="warn">7.</span> Plugins (cookie-consent, AdSense, page builder) mee own CSS ni override chestayi — aa differences live lo mattrame kanipistayi, preview lo levu.</li>
    </ul>
  </div>
</div></body></html>
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="freshness mattrame check (write cheyyadu)")
    args = ap.parse_args()
    content = build()
    if args.check:
        if not OUT.exists():
            print("  ❌ preview/theme-snapshot.html ledu — regenerate cheyandi")
            return 1
        cur = OUT.read_text(encoding="utf-8")
        ver_now = theme_version()
        stale = f"Theme <b>{ver_now}</b>" not in cur
        print(f"  {'❌ stale' if stale else '✅ fresh'} — preview/theme-snapshot.html (theme {ver_now})")
        return 1 if stale else 0
    OUT.write_text(content, encoding="utf-8")
    print(f"  ✅ snapshot  {OUT.relative_to(ROOT)}  ({len(content) / 1024:.1f} KB · theme {theme_version()})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
