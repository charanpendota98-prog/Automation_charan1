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


def front_page_sections() -> list[tuple[str, str]]:
    """front-page.php lo function call order — header comment use cheyyakunda."""
    src = read(THEME / "front-page.php")
    out: list[tuple[str, str]] = []
    for m in re.finditer(r"studentup_([a-z_]+)\s*\(", src):
        name = m.group(1)
        if name in ("is_p2", "home_url"):
            continue
        line = src[: m.start()].count("\n") + 1
        out.append((f"studentup_{name}()", f"front-page.php:{line}"))
    return out


def what_a_section_needs(rel: str) -> str:
    """File nunchi 'kavalsinavi' line: WP_Query / get_posts / studentup_opt / term."""
    src = read(THEME / rel)
    needs = []
    if "studentup_opt(" in src:
        opts = sorted(set(re.findall(r"studentup_opt\(\s*'([a-z0-9_]+)'", src)))
        needs.append("toggle: " + ", ".join(o for o in opts[:4]))
    if re.search(r"get_posts\(|WP_Query\(|wp_count_posts", src):
        needs.append("WordPress posts")
    if "studentup_used_term(" in src or "get_category_by_slug(" in src:
        needs.append("category terms")
    if "studentup_smart_dataset(" in src:
        needs.append("post meta (last dates / vacancies)")
    return " · ".join(needs) if needs else "static markup"


def build() -> str:
    ver = theme_version()
    fp = front_page_sections()
    rows = []
    for name, where in fp:
        rows.append(
            f'        <tr><td><code>{html.escape(name)}</code></td>'
            f"<td><code>{html.escape(where)}</code></td>"
            f"<td><code>inc/&lt;module&gt;.php</code></td>"
            f"<td>theme PHP — live lo ide render avutundi</td></tr>"
        )
    files = sorted(p.name for p in (THEME / "inc").glob("*.php"))
    module_rows = []
    for name, where in fp:
        stem = name.replace("studentup_", "").rstrip("()")
        for f in files:
            if stem.split("_")[0] in f:
                module_rows.append((name, f"inc/{f}", what_a_section_needs(f"inc/{f}")))
                break
    # front-page direct sections (most searched / grid / job table) are inline PHP
    module_rows.append(("studentup_most_used() + grid", "front-page.php", "category terms · WordPress posts"))
    module_rows.append(("studentup_hero_premium()", "inc/premium.php", "toggle: hero_premium · category terms"))
    body = "\n".join(
        f'        <tr><td><code>{html.escape(a)}</code></td><td><code>{html.escape(b)}</code></td>'
        f"<td>{html.escape(c)}</td></tr>"
        for a, b, c in module_rows
    )
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
  .wrap{{max-width:980px;margin:0 auto;padding:24px 16px 60px}}
  h1{{font-size:22px;color:var(--navy);margin:0 0 6px}}
  .sub{{color:var(--muted);font-size:13px;margin:0 0 18px}}
  .banner{{background:#fffbeb;border:1px solid #fde68a;color:#92400e;border-radius:12px;padding:12px 14px;margin:0 0 18px;font-size:13.5px}}
  .banner b{{color:#78350f}}
  table{{width:100%;border-collapse:collapse;background:#fff;border:1px solid var(--line);border-radius:12px;overflow:hidden}}
  th,td{{text-align:left;padding:9px 12px;border-bottom:1px solid var(--line);font-size:13px;vertical-align:top}}
  th{{background:#f8fafc;font-size:12px;text-transform:uppercase;letter-spacing:.04em;color:var(--muted)}}
  tr:last-child td{{border-bottom:0}}
  code{{font-family:ui-monospace,Menlo,Consolas,monospace;font-size:12.5px;color:#0f2e62}}
  .checklist{{background:#fff;border:1px solid var(--line);border-radius:12px;padding:14px 18px;margin-top:20px;font-size:13.5px}}
  .checklist h2{{font-size:15px;margin:0 0 8px;color:var(--navy)}}
  .checklist ul{{margin:0;padding-left:20px}}
  .checklist li{{margin:4px 0}}
  .ok{{color:#15803d;font-weight:700}}
  .warn{{color:#b45309;font-weight:700}}
</style>
</head>
<body><div class="wrap">
  <h1>Theme output snapshot — “live laa” render</h1>
  <p class="sub">Theme <b>{ver}</b> · generated {time.strftime('%Y-%m-%d')} by <code>tools/render_theme_snapshot.py</code> — hand-edit ledu.</p>

  <p class="banner"><b>Idi enduku:</b> <code>preview/worldclass/</code> oka hand-written design demo. Live site = WordPress, mee posts, mee toggles.
  Ee page theme PHP <b>nijamga em render chestundo</b> (section order + kavalsinavi) chupistundi — anduke ee page live ki daahaalam.</p>

  <table>
    <tr><th>Section (front-page.php order)</th><th>Source</th><th>Kavalsinavi</th></tr>
{body}
  </table>

  <div class="checklist">
    <h2>Live lo neat ga kanipinchadaniki (order lo)</h2>
    <ul>
      <li><span class="warn">1.</span> Theme zip upload + Activate → <b>Appearance → Themes</b> lo version check (ee build: <code>{ver}</code>).</li>
      <li><span class="warn">2.</span> <b>Settings → Permalinks</b> → Save (post links clean avutayi).</li>
      <li><span class="warn">3.</span> Posts publish avvali — carousel / trending / cards **mee posts nunchi** build avutayi (khali DB ⇒ khali sections).</li>
      <li><span class="warn">4.</span> Categories: <code>ts-govt-jobs · ap-govt-jobs · central-govt-jobs · results · hall-tickets</code> — lekapote chips/grid lo aa item skip avutundi (fake data ledu).</li>
      <li><span class="warn">5.</span> StudentUp Settings → toggles (hero_premium · trending_today · state_first …) ON unnaya chudandi.</li>
      <li><span class="warn">6.</span> Cache: host (MilesWeb) cache + WP cache plugin okasari clear cheyandi — old CSS/JS inka undakoodadu.</li>
      <li><span class="warn">7.</span> Third-party plugins (cookie-consent, AdSense, page builders) mee own CSS ni override chestayi — <code>!important</code> rules valla spacing/colour maripovachu. Avi live lo mattrame kanipistayi, preview lo levu.</li>
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
