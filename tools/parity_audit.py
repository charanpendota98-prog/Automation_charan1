# -*- coding: utf-8 -*-
"""v69: PARITY AUDIT — "emi miss avvakoodadu" (pin-to-pin cross-surface check).

Oka feature code lo undi kaani docs lo leda, leda preview lo link broken leda, leda module
enni rojullo evaru vaadakapoyina (dead code) — ivi **kanipinchavu** normally. Ee tool
anni surfaces ni okate chota kalipi check chestundi:

  P1  CLI parity        — `run.py` lo unna prathi flag README/MANUAL/GO_LIVE lo undali
  P2  Module parity     — `autoblog/*.py` prathi module ekkadaina import avvali (dead code ledu)
  P3  Preview links     — preview/**/*.html lo local href/src anni nijamaina files ki vellali
  P4  Preview meta      — prathi page ki title · meta description · canonical · robots
  P5  Index files       — robots.txt → sitemap · sitemap lo unna URLs files ga undali · ads.txt
  P6  Tool parity       — `tools/*.py` prathi script doc leda test lo reference avvali
  P7  Placeholder check — shipped surfaces lo TODO/FIXME/lorem ledu (demo text reject)
  P8  Count parity      — suites ↔ preview tile ↔ jsdom ↔ README claims

Run: python tools/parity_audit.py [--json output/parity_audit.json]
Exit 1 = errors unnayi.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PREVIEW = ROOT / "preview"
BOT = ROOT / "autoblog"
DOCS = [ROOT / "README.md", ROOT / "MANUAL_ADVANCED_CHECKLIST.md",
        ROOT / "GO_LIVE_CHECKLIST.md", ROOT / "CONTENT_PLAN_DAILY.md",
        ROOT / "docs" / "BA_REQUIREMENTS_MATRIX.md"]


def _read(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8")
    except OSError:
        return ""


def p1_cli_parity(rep: dict) -> None:
    main = _read(BOT / "main.py")
    flags = sorted(set(re.findall(r'add_argument\(\s*"(--[a-z0-9-]+)"', main)))
    docs = "\n".join(_read(p) for p in DOCS if p.exists())
    missing = [f for f in flags if f not in docs]
    rep["info"].append(f"P1 CLI: {len(flags)} flags · {len(flags) - len(missing)} docs lo unnayi")
    for f in missing:
        rep["warnings"].append(f"P1 CLI '{f}' docs lo ledu (README/MANUAL/GO_LIVE) — "
                               f"owner ki teliyadu")


def p2_module_parity(rep: dict) -> None:
    mods = sorted(p.stem for p in BOT.glob("*.py") if p.stem != "__init__")
    haystack = ""
    for p in list(BOT.glob("*.py")) + [ROOT / "run.py"] + list((ROOT / "tests").glob("*.py")) \
            + list((ROOT / "tools").glob("*.py")):
        haystack += _read(p)
    dead = [m for m in mods if haystack.count(m) <= 1]
    rep["info"].append(f"P2 modules: {len(mods)} · dead {len(dead)}")
    for m in dead:
        rep["warnings"].append(f"P2 autoblog/{m}.py evaru import cheyyaledu (dead module — "
                               f"engine pani cheyyadu)")


def p3_preview_links(rep: dict) -> None:
    checked = broken = 0
    for html in sorted(PREVIEW.rglob("*.html")):
        text = _read(html)
        body = re.sub(r"<script.*?</script>", "", text, flags=re.S)  # JS templates skip
        for m in re.finditer(r'(?:href|src)="([^"#][^"]*)"', body):
            url = m.group(1)
            if any(ch in url for ch in "+'${}"):     # dynamic (JS concat) — skip
                continue
            if url.startswith(("http://", "https://", "//", "mailto:", "tel:", "data:",
                               "javascript:")):
                continue
            if not re.match(r"^[A-Za-z0-9._/~-]+$", url):   # query/dynamic patterns
                continue
            target = url.split("?")[0].split("#")[0]
            if not target or target == "/":
                continue
            checked += 1
            base = html.parent if not target.startswith("/") else PREVIEW
            path = (base / target.lstrip("/")) if not target.startswith("/") else \
                (PREVIEW / target.lstrip("/"))
            if not path.exists():
                broken += 1
                rep["errors"].append(f"P3 {html.relative_to(ROOT)}: '{url}' file ledu "
                                     f"(broken link)")
    rep["info"].append(f"P3 preview links: {checked} checked · {broken} broken")


def p4_preview_meta(rep: dict) -> None:
    # Deploy ayyi unna pages mattrame (dev/blueprint pages preview-only — v38/v39/legacy)
    sm = _read(PREVIEW / "sitemap.xml")
    deployed = {PREVIEW / "index.html"}
    for u in re.findall(r"<loc>([^<]+)</loc>", sm):
        rel = re.sub(r"^https?://[^/]+/", "", u.strip()).strip("/")
        if not rel:
            deployed.add(PREVIEW / "index.html")
            continue
        for cand in (PREVIEW / rel / "index.html", PREVIEW / f"{rel}.html",
                     PREVIEW / rel, PREVIEW / "pages" / f"{rel}.html"):
            if cand.exists():
                deployed.add(cand)
    for html in sorted(deployed):
        text = _read(html)
        name = html.relative_to(ROOT)
        if "<title>" not in text:
            rep["errors"].append(f"P4 {name}: <title> ledu")
        for needle, why in (('name="description"', "meta description"),
                            ('rel="canonical"', "canonical"),
                            ('name="robots"', "robots meta"),
                            ('property="og:title"', "og:title"),
                            ('property="og:image"', "og:image"),
                            ('name="viewport"', "viewport")):
            if needle not in text:
                rep["warnings"].append(f"P4 {name}: {why} ledu")


def p5_index_files(rep: dict) -> None:
    robots = _read(PREVIEW / "robots.txt")
    if "Sitemap:" not in robots:
        rep["errors"].append("P5 robots.txt lo Sitemap line ledu")
    sm = _read(PREVIEW / "sitemap.xml")
    urls = re.findall(r"<loc>([^<]+)</loc>", sm)
    if not urls:
        rep["errors"].append("P5 sitemap.xml lo <loc> ledu")
    missing = []
    for u in urls:
        m = re.search(r"studentup\.in/?([^<]*)$", u.strip())
        rel = (m.group(1) if m else u.strip()).strip("/")
        # ekkada unnayi: root leda pages/
        candidates = [PREVIEW / (rel or "index.html"), PREVIEW / rel / "index.html",
                      PREVIEW / f"{rel}.html", PREVIEW / "pages" / f"{rel}.html"]
        if any(c.exists() for c in candidates):
            continue
        if rel in ("", "index.html"):
            continue
        missing.append(u)
    rep["info"].append(f"P5 sitemap: {len(urls)} URLs · {len(missing)} file mapping ledu")
    for u in missing:
        rep["warnings"].append(f"P5 sitemap URL '{u}' ki file preview lo ledu (deploy lo 404)")
    for f in ("ads.txt", "robots.txt", "sitemap.xml", "favicon.svg"):
        if not (PREVIEW / f).exists():
            rep["errors"].append(f"P5 preview/{f} ledu (deploy surface)")


def p6_tool_parity(rep: dict) -> None:
    docs = "\n".join(_read(p) for p in DOCS if p.exists())
    tests = "\n".join(_read(p) for p in (ROOT / "tests").glob("*.py"))
    for t in sorted((ROOT / "tools").glob("*.py")):
        if t.stem in ("__init__",):
            continue
        if t.stem not in docs and f"{t.name}" not in tests:
            rep["warnings"].append(f"P6 tools/{t.name} evaru reference cheyyaledu "
                                   f"(docs/test ledu)")
    rep["info"].append(f"P6 tools: {len(list((ROOT / 'tools').glob('*.py')))} scripts")


def p7_placeholders(rep: dict) -> None:
    bad = 0
    for base in (PREVIEW, ROOT / "wordpress-theme" / "studentup"):
        for p in base.rglob("*"):
            if p.is_dir() or p.suffix not in (".html", ".php", ".js", ".css", ".json", ".xml"):
                continue
            text = _read(p)
            if p.suffix == ".php":
                try:
                    import sys as _s

                    _s.path.insert(0, str(Path(__file__).resolve().parent))
                    from theme_audit import _strip_php_comments

                    text = _strip_php_comments(text)
                except Exception:  # noqa: BLE001
                    pass
            for m in re.finditer(r"\b(TODO|FIXME|lorem ipsum)\b", text, re.I):
                bad += 1
                rep["errors"].append(f"P7 {p.relative_to(ROOT)}: placeholder text "
                                     f"'{m.group(1)}' — shipped surface ki saripodu")
    rep["info"].append(f"P7 placeholders: {bad} found")


def p8_count_parity(rep: dict) -> None:
    suites = len(list((ROOT / "tests").glob("*_test.py")))
    tiles = re.findall(r"<b>(\d+)/\1</b>", _read(PREVIEW / "index.html"))
    jsdom = re.search(r"trust proof tiles: (\d+)/\d+", _read(ROOT / "tests" / "runtime" /
                                                             "jsdom_runtime_test.js"))
    readme = _read(ROOT / "README.md")
    ok = (str(suites) in tiles) and jsdom and int(jsdom.group(1)) == suites
    if not ok:
        rep["errors"].append(f"P8 count parity: suites {suites} · tiles {tiles} · "
                             f"jsdom {jsdom.group(1) if jsdom else '?'}")
    if f"{suites}/{suites}" not in readme:
        rep["warnings"].append(f"P8 README lo '{suites}/{suites}' claim ledu")
    rep["info"].append(f"P8 counts: suites {suites} · tiles {tiles}")


def run() -> dict:
    rep: dict = {"errors": [], "warnings": [], "info": []}
    for fn in (p1_cli_parity, p2_module_parity, p3_preview_links, p4_preview_meta,
               p5_index_files, p6_tool_parity, p7_placeholders, p8_count_parity):
        try:
            fn(rep)
        except Exception as exc:  # noqa: BLE001
            rep["errors"].append(f"{fn.__name__} crash: {type(exc).__name__}: {exc}")
    rep["ok"] = not rep["errors"]
    rep["counts"] = {"errors": len(rep["errors"]), "warnings": len(rep["warnings"]),
                     "info": len(rep["info"])}
    return rep


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="StudentUp parity audit (v69)")
    ap.add_argument("--json", default="")
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args(argv)
    rep = run()
    print("=" * 74)
    print("  🔗 PARITY AUDIT (v69) — CLI · modules · preview · docs · counts")
    print("=" * 74)
    print(f"  errors {len(rep['errors'])} · warnings {len(rep['warnings'])}")
    for row in rep["errors"]:
        print("  ❌ " + row)
    for row in rep["warnings"]:
        print("  ⚠️  " + row)
    if args.verbose:
        for row in rep["info"]:
            print("  ℹ️  " + row)
    if args.json:
        Path(args.json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.json).write_text(json.dumps(rep, ensure_ascii=False, indent=2),
                                   encoding="utf-8")
    print("-" * 74)
    print(f"  {'✅ PIN-TO-PIN OK' if rep['ok'] else '⛔ FIX CHEYANDI'}")
    print("=" * 74)
    return 0 if rep["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
