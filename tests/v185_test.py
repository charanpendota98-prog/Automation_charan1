# -*- coding: utf-8 -*-
"""v185 — world-class web-quality pass tests.

Cover:
  1. Deep theme audit pass 4 green (31 checks, 0 fail) + kotha check names
  2. No-flash dark mode: pre-paint inline script body taruvata, header mundu ·
     localStorage key match (inline ↔ footer JS)
  3. Native theming: color-scheme meta + CSS tokens (light/dark)
  4. Single H1 per view template (index.php fix tho saha)
  5. Perf: card containment rules + min.css fresh (minified < raw + tokens)
  6. Docs wiring: README v185 section + MANUAL PART 78
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
THEME = ROOT / "wordpress-theme" / "studentup"
sys.path.insert(0, str(ROOT))


def _read(rel: str) -> str:
    return (THEME / rel).read_text(encoding="utf-8")


def test_deep_audit_pass4_green():
    proc = subprocess.run([sys.executable, str(ROOT / "tools" / "theme_audit_deep.py")],
                          capture_output=True, text=True, cwd=str(ROOT), timeout=240)
    out = proc.stdout
    assert proc.returncode == 0, out[-800:]
    assert "PASS 4" in out and "WEB-QUALITY MATRIX" in out
    m = re.search(r"→ (\d+) pass · (\d+) warn · (\d+) fail", out)
    assert m, "KPI line ledu"
    passes, warns, fails = int(m.group(1)), int(m.group(2)), int(m.group(3))
    assert fails == 0, out[-500:]
    assert passes >= 30, f"checks thakkuva: {passes}"
    for name in ("single-h1-per-view", "no-flash-dark-mode", "color-scheme-css",
                 "css-containment", "responsive-images", "schema-rich-results",
                 "print-styles", "aria-live", "touch-targets"):
        assert name in out, f"check missing: {name}"
    print(f"  1. deep audit pass 4: {passes} pass · {warns} warn · {fails} fail ✔")


def test_no_flash_dark_mode():
    header = _read("header.php")
    body_at = header.find("<body")
    theme_at = header.find("data-su-theme", body_at)
    header_at = header.find("<header class=")
    assert body_at != -1 and theme_at != -1, "pre-paint theme script ledu"
    assert theme_at < header_at, "script header markup taruvata — flash vastundi"
    assert "document.body" in header[body_at:theme_at + 400], "body class set avvaledu"
    # saved preference key inline lo + footer JS lo same undali
    assert 'localStorage.getItem("su_theme")' in header
    js = _read("assets/js/studentup.js")
    assert 'localStorage.setItem("su_theme"' in js and 'localStorage.getItem("su_theme")' in js, \
        "footer JS lo key mismatch — toggle pani cheyyadu"
    # system preference fallback (JS off unna kuda dark motoriki)
    assert "prefers-color-scheme: dark" in header, "system preference fallback ledu"
    print("  2. no-flash dark mode (pre-paint · key parity · system fallback) ✔")


def test_native_theming_and_h1():
    header = _read("header.php")
    assert 'name="color-scheme" content="light dark"' in header, "color-scheme meta ledu"
    css = _read("style.css")
    assert "color-scheme:light" in css and "color-scheme:dark" in css
    assert "contain:content" in css and "contain:layout style" in css, "containment ledu"
    for name in ("front-page.php", "single.php", "index.php", "page.php",
                 "archive.php", "search.php", "404.php"):
        text = _read(name)
        assert text.count("<h1") == 1, f"{name}: h1 count {text.count('<h1')}"
    # index.php lo page title ippudu h1 (Search: / Latest updates)
    assert "<h1>" in _read("index.php")
    print("  3. color-scheme + containment + single-H1 per template ✔")


def test_css_min_fresh():
    raw = _read("style.css")
    mini = _read("style.min.css")
    assert len(mini) < len(raw), "style.min.css fresh ledu — minify build run cheyyandi"
    for token in ("color-scheme:light", "color-scheme:dark", "contain:content"):
        assert token.replace(" ", "") in mini.replace(" ", ""), f"min.css lo `{token}` ledu"
    ver_raw = re.search(r"Version:\s*([\d.]+)", raw).group(1)
    ver_min = re.search(r"Version:\s*([\d.]+)", mini).group(1)
    fn = _read("functions.php")
    ver_fn = re.search(r"STUDENTUP_VERSION',\s*'([\d.]+)'", fn).group(1)
    assert ver_raw == ver_min == ver_fn, (ver_raw, ver_min, ver_fn)
    print(f"  4. min.css fresh · version parity {ver_raw} ✔")


def test_docs_wiring():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "v185" in readme and "WEB-QUALITY" in readme.upper(), "README v185 section ledu"
    assert "theme_audit_deep" in readme, "README lo deep audit command ledu"
    manual = (ROOT / "MANUAL_ADVANCED_CHECKLIST.md").read_text(encoding="utf-8")
    assert "PART 78" in manual and "v185" in manual, "MANUAL PART 78 ledu"
    changelog = _read("readme.txt")
    assert "= 1.9.35" in changelog, "theme changelog 1.9.35 ledu"
    print("  5. docs wiring (README · MANUAL PART 78 · changelog) ✔")


def main() -> None:
    print("=" * 70)
    print("  v185 — WORLD-CLASS WEB QUALITY (deep audit pass 4)")
    print("=" * 70)
    test_deep_audit_pass4_green()
    test_no_flash_dark_mode()
    test_native_theming_and_h1()
    test_css_min_fresh()
    test_docs_wiring()
    print("-" * 70)
    print("ALL v185 WEB-QUALITY TESTS PASSED ✔")


if __name__ == "__main__":
    main()
