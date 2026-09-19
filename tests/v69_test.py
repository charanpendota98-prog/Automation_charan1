# -*- coding: utf-8 -*-
"""v69 tests — TOP-LEVEL THEME STANDARDS PASS 3 + PARITY (emi miss avvakoodadu).

Mee requirement: "fix all bugs · advanced top-level website avvali · anni pin to pin ·
emi miss avvakoodadu · everything must check and implement/fix".

Ee suite ee pass lo chesina pani ni lock chestundi:

  · **version parity** — `style.css Version:` ↔ `STUDENTUP_VERSION` ↔ readme `Stable tag`
    (mundu style.css 1.0.0 vs PHP 1.3.0 — WP ki telisedi style.css!)
  · **block editor parity** — `editor-styles` + `wp-block-styles` + `assets/css/editor.css`
  · **WP standards** — `post_class()` loops lo · `aria-current="page"` nav filter ·
    `no_found_rows` custom WP_Query lo (extra SQL query aapadam)
  · **theme standards pass 3 audit** — version parity · editor styles · post_class ·
    no_found_rows · admin nonce checks — anni permanent ga audit lo
  · **parity audit** (`tools/parity_audit.py`) — CLI ↔ docs · dead modules · preview links ·
    preview meta · index files · tool references · placeholders · count sync
  · **automation wiring** — guardian + readiness lo code audit + parity audit checks
  · **preview integrity** — deployed pages ki robots meta · zip fresh (editor.css to)

Run: python tests/v69_test.py   (also via python run.py --test-all)
"""
from __future__ import annotations

import re
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

import code_audit  # noqa: E402
import parity_audit  # noqa: E402
import theme_audit  # noqa: E402

THEME = ROOT / "wordpress-theme" / "studentup"
PREVIEW = ROOT / "preview"


def read(p) -> str:
    return Path(p).read_text(encoding="utf-8")


def _versions() -> tuple:
    css = re.search(r"^Version:\s*(\S+)", read(THEME / "style.css"), re.M).group(1)
    php = re.search(r"STUDENTUP_VERSION',\s*'([^']+)'", read(THEME / "functions.php")).group(1)
    rm = re.search(r"^Stable tag:\s*(\S+)", read(THEME / "readme.txt"), re.M)
    return css, php, (rm.group(1) if rm else "")


# ------------------------------------------------------------------ theme standards

def test_theme_audit_clean():
    rep = theme_audit.run()
    assert rep["errors"] == [], rep["errors"]
    assert rep["warnings"] == [], rep["warnings"]
    kpi = rep.get("kpi", {})
    assert kpi.get("ad_positions") == 6, kpi
    assert kpi.get("php_files", 0) >= 28, kpi


def test_version_parity():
    """v69 bug: style.css Version 1.0.0 vs STUDENTUP_VERSION 1.3.0 — WP ki telisedi CSS."""
    css, php, stable = _versions()
    assert css == php, f"style.css '{css}' ≠ STUDENTUP_VERSION '{php}'"
    assert stable == php, f"readme Stable tag '{stable}' ≠ '{php}'"


def test_editor_parity():
    fn = read(THEME / "functions.php")
    assert "add_theme_support( 'editor-styles' )" in fn
    assert "add_theme_support( 'wp-block-styles' )" in fn
    m = re.search(r"add_editor_style\(\s*'([^']+)'", fn)
    assert m, "add_editor_style ledu"
    ed = THEME / m.group(1)
    assert ed.exists(), f"{m.group(1)} file ledu"
    body = read(ed)
    assert len(body) > 800 and ".editor-styles-wrapper" in body, "editor.css saripodu"
    assert "--navy" in body and "h2" in body, "editor.css lo front-end tokens/typography ledu"


def test_wp_standards_loops():
    """post_class() · aria-current · no_found_rows — WP standard + perf."""
    for rel in ("single.php", "page.php", "inc/template.php"):
        assert "post_class(" in read(THEME / rel), f"{rel}: post_class ledu"
    fn = read(THEME / "functions.php")
    assert "nav_menu_link_attributes" in fn and "aria-current" in fn, "aria-current filter ledu"
    for rel, fn_name in (("front-page.php", "grid query"), ("single.php", "related query")):
        code = read(THEME / rel)
        for m in re.finditer(r"new WP_Query\(", code):
            tail = code[m.end():m.end() + 700]
            assert "'no_found_rows'" in tail, f"{rel} ({fn_name}): no_found_rows ledu"


def test_core_theme_supports_and_hooks():
    fn = read(THEME / "functions.php")
    for sup in ("title-tag", "post-thumbnails", "html5", "responsive-embeds", "custom-logo"):
        assert f"'{sup}'" in fn, f"add_theme_support('{sup}') ledu"
    assert "register_nav_menus" in fn and "register_sidebar" in fn
    header = read(THEME / "header.php")
    assert "wp_head()" in header and "wp_body_open()" in header and "language_attributes()" in header
    assert "wp_footer()" in read(THEME / "footer.php")


# ------------------------------------------------------------------ parity (emi miss avvakoodadu)

def test_parity_audit_clean():
    rep = parity_audit.run()
    assert rep["errors"] == [], rep["errors"]
    assert rep["warnings"] == [], rep["warnings"]


def test_parity_detects_broken_link():
    """Detection ability: preview lo broken local link unte parity audit pattukovali."""
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "preview").mkdir()
        (root / "preview" / "index.html").write_text(
            '<!doctype html><html><head><title>x</title>'
            '<meta name="description" content="d"><link rel="canonical" href="/">'
            '<meta name="robots" content="index"><meta property="og:title" content="t">'
            '<meta property="og:image" content="/i.png"><meta name="viewport" content="w">'
            '</head><body><a href="missing-page.html">x</a></body></html>', encoding="utf-8")
        old_root, old_prev = parity_audit.ROOT, parity_audit.PREVIEW
        try:
            parity_audit.ROOT = root
            parity_audit.PREVIEW = root / "preview"
            rep = {"errors": [], "warnings": [], "info": []}
            parity_audit.p3_preview_links(rep)
        finally:
            parity_audit.ROOT, parity_audit.PREVIEW = old_root, old_prev
        assert any("missing-page.html" in e for e in rep["errors"]), rep["errors"]


def test_cli_flags_documented():
    """Prathi run.py flag README/MANUAL/GO_LIVE lo undali (owner ki teliyali)."""
    flags = sorted(set(re.findall(r'add_argument\(\s*"(--[a-z0-9-]+)"',
                                  read(ROOT / "autoblog" / "main.py"))))
    docs = "\n".join(read(p) for p in (ROOT / "README.md",
                                       ROOT / "MANUAL_ADVANCED_CHECKLIST.md",
                                       ROOT / "GO_LIVE_CHECKLIST.md",
                                       ROOT / "docs" / "BA_REQUIREMENTS_MATRIX.md"))
    missing = [f for f in flags if f not in docs]
    assert missing == [], f"docs lo leni flags: {missing}"
    # v74: 9 dead flags poyayi (--exam-* ×8 + --deploy-port), 1 kotha (--approval-poll)
    assert len(flags) >= 85, f"flag count {len(flags)}"


def test_no_dead_modules():
    mods = [p.stem for p in (ROOT / "autoblog").glob("*.py") if p.stem != "__init__"]
    hay = ""
    for p in list((ROOT / "autoblog").glob("*.py")) + [ROOT / "run.py"] \
            + list((ROOT / "tests").glob("*.py")) + list((ROOT / "tools").glob("*.py")):
        hay += read(p)
    dead = [m for m in mods if hay.count(m) <= 1]
    assert dead == [], f"dead modules: {dead}"


def test_preview_deployed_pages_meta():
    for f in sorted((PREVIEW / "pages").glob("*.html")):
        text = read(f)
        assert 'name="robots"' in text, f"{f.name}: robots meta ledu"
        assert "<title>" in text and 'name="description"' in text


def test_preview_placeholders_clean():
    for base in (PREVIEW, THEME):
        for p in base.rglob("*"):
            if p.is_dir() or p.suffix not in (".html", ".php", ".js", ".css", ".json", ".xml"):
                continue
            text = read(p)
            if p.suffix == ".php":
                text = theme_audit._strip_php_comments(text)
            hits = re.findall(r"\b(TODO|FIXME|lorem ipsum)\b", text, re.I)
            assert not hits, f"{p.relative_to(ROOT)}: {hits}"


# ------------------------------------------------------------------ automation wiring

def test_guardian_and_readiness_wired():
    from autoblog import guardian, readiness

    g_ids = [row[0] for row in guardian.CHECKS]
    assert "code_audit" in g_ids and "parity_audit" in g_ids, g_ids
    r_ids = [name for name, _fn in readiness.CHECKS]
    assert "parity_audit" in r_ids and "code_audit" in r_ids, r_ids
    rep = readiness.run_report()
    assert rep["total"] >= 28, rep["total"]
    assert rep["score"] == 100, f"readiness {rep['score']} — fails: " + "; ".join(
        r["label"] for r in rep["rows"] if r.get("scored") and not r["ok"])


def test_shell_scripts_syntax():
    """P9 hygiene: deploy shell scripts `bash -n` clean (deploy lo syntax error = fail)."""
    shells = sorted(list(ROOT.glob("*.sh")) + list((ROOT / "deploy").glob("*.sh")))
    assert shells, "shell scripts ledu"
    for sh in shells:
        proc = subprocess.run(["bash", "-n", str(sh)], capture_output=True, text=True,
                              timeout=120)
        assert proc.returncode == 0, f"{sh.name}: {proc.stderr.strip()[:120]}"


def test_secrets_not_committed():
    """P9 hygiene: tracked files lo real API tokens ledu (example/dummy ok)."""
    proc = subprocess.run(["git", "grep", "-nI", "-E",
                           r"AIza[0-9A-Za-z_-]{30,}|[0-9]{8,10}:AA[A-Za-z0-9_-]{30,}|"
                           r"sk-[A-Za-z0-9]{30,}", "--", "."],
                          capture_output=True, text=True, cwd=str(ROOT), timeout=180)
    hits = [l for l in (proc.stdout or "").splitlines() if l.strip()]
    assert hits == [], f"secrets: {hits[:3]}"


def test_code_audit_clean():
    rep = code_audit.run()
    assert rep["errors"] == [], rep["errors"]
    assert rep["warnings"] == [], rep["warnings"]


def test_theme_zip_fresh_with_editor_css():
    zips = sorted((ROOT / "wordpress-theme").glob("studentup*.zip"))
    assert zips, "zip ledu"
    newest = max(p.stat().st_mtime for p in THEME.rglob("*") if p.is_file())
    assert zips[-1].stat().st_mtime >= newest, "zip stale — tools/build_wp_theme.py run cheyandi"
    names = zipfile.ZipFile(zips[-1]).namelist()
    for need in ("studentup/assets/css/editor.css", "studentup/style.css",
                 "studentup/inc/indexnow.php", "studentup/readme.txt"):
        assert need in names, need


def test_counts_synced():
    """v70: docs claims ↔ nijamaina suite count · public surfaces lo developer text ledu."""
    suites = len(list((ROOT / "tests").glob("*_test.py")))
    readme = read(ROOT / "README.md")
    assert f"{suites}/{suites}" in readme, f"README claim ledu ({suites})"
    assert f"{suites}/{suites}" in read(ROOT / "MANUAL_ADVANCED_CHECKLIST.md")
    idx = read(PREVIEW / "index.html")
    assert "qtile" not in idx and "టెస్ట్ సూట్" not in idx
    theme = "".join(p.read_text(encoding="utf-8") for p in THEME.rglob("*.php"))
    assert "studentup_proof_tiles" not in theme and "proof_json" not in theme


def test_docs_current():
    readme = read(ROOT / "README.md")
    assert "### v69" in readme, "README v69 block ledu"
    assert "parity_audit" in readme, "README lo parity audit ledu"
    manual = read(ROOT / "MANUAL_ADVANCED_CHECKLIST.md")
    assert "PART 28" in manual, "MANUAL PART 28 ledu"
    assert "v69" in manual
    ba = read(ROOT / "docs" / "BA_REQUIREMENTS_MATRIX.md")
    assert "R26" in ba, "BA matrix R26 ledu"
    assert "parity" in ba.lower()


# ------------------------------------------------------------------ runner

def main() -> int:
    tests = [(n, f) for n, f in sorted(globals().items())
             if n.startswith("test_") and callable(f)]
    print("=" * 70)
    print("  🏅 v69 — THEME STANDARDS PASS 3 + PARITY (pin-to-pin) TESTS")
    print("=" * 70)
    failed = 0
    for name, fn in tests:
        try:
            fn()
            print(f"  {name} ✔")
        except AssertionError as exc:
            failed += 1
            print(f"  {name} ✘  {exc}")
        except Exception as exc:  # noqa: BLE001
            failed += 1
            print(f"  {name} ✘  {type(exc).__name__}: {exc}")
    print("-" * 70)
    if failed:
        print(f"  {failed} TEST(S) FAILED ✘")
        return 1
    print(f"ALL v69 PARITY + STANDARDS TESTS PASSED ✔  ({len(tests)} checks)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
