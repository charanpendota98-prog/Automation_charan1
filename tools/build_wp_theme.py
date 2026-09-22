# -*- coding: utf-8 -*-
"""v61: StudentUp WordPress theme — validate + package (zip).

Enduku:
  Mee website = WordPress (MilesWeb). Design (preview/index.html) ni WordPres lo
  ki teesukelle theme `wordpress-theme/studentup/` lo undi. Idi:
    1) required files + theme header validate chestundi (WP install fail avvakunda)
    2) wordpress-theme/studentup-theme.zip create chestundi (WP Admin → Upload Theme)
    3) REAL PHP lint: node php-parser (PHP 8 grammar) — `php -l` unte adi kuda
       (v64: syntax tappu/build break unte zip create avvadu — hard gate)

Run: python tools/build_wp_theme.py   [--out wordpress-theme/studentup-theme.zip]
"""
from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "wordpress-theme" / "studentup"
DEFAULT_OUT = ROOT / "wordpress-theme" / "studentup-theme.zip"

REQUIRED = [
    "style.css", "index.php", "functions.php", "header.php", "footer.php",
    "front-page.php", "single.php", "page.php", "archive.php", "search.php",
    "404.php", "searchform.php", "theme.json",
    "inc/breaking.php", "inc/ads.php", "inc/template.php", "inc/seo-bridge.php",
    "inc/options.php", "inc/toc.php", "inc/schema.php", "inc/author-box.php",
    "inc/pwa.php",
    "assets/js/studentup.js",
]
SKIP_DIRS = {"__pycache__", ".git", "node_modules"}


def validate() -> list[str]:
    problems: list[str] = []
    for rel in REQUIRED:
        if not (SRC / rel).exists():
            problems.append("missing: " + rel)
    css = (SRC / "style.css").read_text(encoding="utf-8") if (SRC / "style.css").exists() else ""
    for field in ("Theme Name:", "Version:", "License:", "Text Domain: studentup"):
        if field not in css:
            problems.append("style.css header lo ledu: " + field)
    for token in ("--navy:#0f2e62", "--orange:#ed8a32", ".tickerwrap", ".usedgrid",
                  ".newsgrid", ".su-ad", "body.dark"):
        if token not in css:
            problems.append("style.css lo design token ledu: " + token)
    for php in SRC.rglob("*.php"):
        text = php.read_text(encoding="utf-8")
        rel = php.relative_to(SRC).as_posix()
        if "ABSPATH" not in text:
            problems.append(f"{rel}: ABSPATH guard ledu")
        if re.search(r"<\?php\s+echo\s+\$", text):
            problems.append(f"{rel}: escape cheyyani echo $ (XSS risk)")
    js = (SRC / "assets/js/studentup.js").read_text(encoding="utf-8") if (SRC / "assets/js/studentup.js").exists() else ""
    if re.search(r"\bjQuery\s*\(|\$\(document", js):
        problems.append("studentup.js: jQuery library use (vaddu — speed)")
    theme_json = SRC / "theme.json"
    if theme_json.exists():
        import json

        try:
            data = json.loads(theme_json.read_text(encoding="utf-8"))
            slugs = [c.get("slug") for c in data.get("settings", {}).get("color", {}).get("palette", [])]
            for want in ("navy", "blue", "orange"):
                if want not in slugs:
                    problems.append("theme.json palette lo ledu: " + want)
        except ValueError as exc:
            problems.append(f"theme.json invalid JSON: {exc}")
    return problems


def php_lint() -> tuple[int, str]:
    """v64: mundu REAL PHP parse lint (node php-parser), tarvata php -l (unte)."""
    node = shutil.which("node")
    linter = ROOT / "tools" / "php_lint.js"
    if node and linter.exists():
        out = subprocess.run([node, str(linter)], capture_output=True, text=True,
                             cwd=str(ROOT), timeout=300)
        tail = (out.stdout or "").strip().splitlines()
        msg = tail[-1] if tail else ""
        if out.returncode != 0:
            fails = [l for l in tail if l.startswith("✘")][:3]
            return 1, "PHP PARSE FAIL: " + "; ".join(fails) + (f" ({msg})" if msg else "")
        if msg and not msg.startswith("SKIP"):
            return 0, msg + "  (php-parser · real PHP 8 syntax)"
    php = shutil.which("php")
    if not php:
        return 0, "php ledu — lint skip (WP install ni adi aapadu)"
    checked, fails = 0, []
    for f in SRC.rglob("*.php"):
        checked += 1
        out = subprocess.run([php, "-l", str(f)], capture_output=True, text=True, timeout=60)
        if out.returncode != 0:
            fails.append(f"{f.relative_to(SRC)}: {out.stdout.strip() or out.stderr.strip()}")
    if fails:
        return 1, f"{checked} files lint — {len(fails)} FAIL: " + "; ".join(fails[:3])
    return 0, f"{checked} PHP files lint PASS ✔"


def package(out: Path) -> tuple[int, int]:
    """v95: REPRODUCIBLE zip — entry timestamps fix (sha256 build-to-build same).

    Enduku: GO_LIVE checklist lo zip sha256 record chestamu (upload ayyina zip
    ide ani verify cheyyadam kosam). `zf.write()` mtime ni store chestundi →
    prathi build ki sha maripoyedi, aa record waste ayyedi. Fixed date_time +
    stable attrs tho same content ⇒ byte-identical zip ⇒ same sha256.
    """
    files = 0
    fixed = (2026, 1, 1, 0, 0, 0)   # deterministic (reproducible artifact)
    out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(SRC.rglob("*")):
            if path.is_dir() or any(part in SKIP_DIRS for part in path.parts):
                continue
            info = zipfile.ZipInfo(
                str(Path("studentup") / path.relative_to(SRC)), date_time=fixed)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            zf.writestr(info, path.read_bytes())
            files += 1
    return files, out.stat().st_size


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="StudentUp WP theme validate + zip")
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    args = ap.parse_args(argv)

    print("=" * 66)
    print("  🎨 STUDENTUP WORDPRESS THEME — validate + package (v61)")
    print("=" * 66)
    problems = validate()
    for p in problems:
        print("  ❌ " + p)
    if not problems:
        print("  ✅ structure + theme header + tokens + escaping — ANNI OK")
    code, msg = php_lint()
    print(("  ✅ " if code == 0 else "  ❌ ") + msg)
    # v67: POT (i18n) ni build lo regenerate — strings maarithe stale avvakunda
    pot = subprocess.run([sys.executable, str(ROOT / "tools" / "build_pot.py")],
                         capture_output=True, text=True, cwd=str(ROOT), timeout=300)
    pot_line = [l for l in (pot.stdout or "").splitlines() if "strings:" in l]
    print(("  ✅ " if pot.returncode == 0 else "  ❌ ")
          + "pot: " + (pot_line[0].strip() if pot_line else "fail"))
    # v66: static theme audit (undefined functions · option keys · hooks · ads)
    audit = subprocess.run([sys.executable, str(ROOT / "tools" / "theme_audit.py")],
                           capture_output=True, text=True, cwd=str(ROOT), timeout=300)
    tail = [l for l in (audit.stdout or "").splitlines() if l.strip()]
    summary = tail[-2].strip() if len(tail) >= 2 else ""
    print(("  ✅ " if audit.returncode == 0 else "  ❌ ") + "theme audit: " + summary)
    if audit.returncode != 0:
        for line in tail:
            if line.strip().startswith("❌"):
                print("     " + line.strip())
    if problems or code or audit.returncode:
        print("  ⛔ package cheyyaledu — paina problems fix cheyandi")
        return 1
    out = Path(args.out)
    files, size = package(out)
    with zipfile.ZipFile(out) as zf:
        names = zf.namelist()
        has_style = "studentup/style.css" in names and "studentup/front-page.php" in names
    print(f"  ✅ zip: {out.relative_to(ROOT)} — {files} files · {size/1024:.0f} KB")
    print(f"     root: {'studentup/ ✔' if has_style else '⛔ tappu structure'}")
    print("     install: WP Admin → Appearance → Themes → Add New → Upload Theme → Activate")
    print("=" * 66)
    return 0 if has_style else 1


if __name__ == "__main__":
    raise SystemExit(main())
