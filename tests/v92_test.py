# -*- coding: utf-8 -*-
"""v92 tests — SAVED / reader retention (theme 1.9.3).

Brief: readers job notification ni save chesi tarvata chudali antaru — kaani
ippati varaku daari ledu. v92 = bookmark layer: 🔖 save/un-save (cards + single),
saved rail + drawer, `[studentup_saved]` shortcode (/saved/ page), and reading
history. Antha **localStorage** lo — DB ledu, cookie ledu, server round-trip ledu.

Checks:
  * theme inc/saved.php: ABSPATH + option gate + escaping + storage-key constants
  * save button helper (aria-pressed, data attrs) + shortcode + panel + body class
  * assets/js/studentup-saved.js: no jQuery, guarded storage, no innerHTML,
    data-su-saved-open trigger, deferred via wp_enqueue_script
  * theme integration: functions.php require/version, header button, footer panel,
    single.php + card call-site, options field declared, style.css rules
  * REAL behaviour: node tests/runtime/saved_runtime_test.js (jsdom) — 53 checks
  * version parity 1.9.3 (php · css · stable) + readme changelog entries
  * suite pins (v75–v81 → "suites == 72") + docs 72/72 claims
  * zip: saved.php + studentup-saved.js packed, theme version 1.9.3

Run: python tests/v92_test.py   (also via python run.py --test-all)
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

THEME = ROOT / "wordpress-theme" / "studentup"
ZIP = ROOT / "wordpress-theme" / "studentup-theme.zip"
SUITES_EXPECTED = 94  # v95 tho


def read(rel: Path | str) -> str:
    return Path(rel).read_text(encoding="utf-8")


def test_module_exists_and_guarded() -> None:
    src = read(THEME / "inc" / "saved.php")
    assert "ABSPATH" in src, "ABSPATH guard ledu"
    assert "STUDENTUP_SAVED_STORE" in src, "storage key constant ledu"
    assert "studentup_saved_v1" in src, "saved key value ledu"
    assert "studentup_recent_v1" in src, "recent key value ledu"
    # escaping — raw echo of a variable vaddhu (XSS)
    assert not re.search(r"<\?php\s+echo\s+\$", src), "escape cheyyani echo $ undi"


def test_option_gate_and_fields() -> None:
    src = read(THEME / "inc" / "saved.php")
    assert "studentup_opt( 'saved_enabled'" in src, "saved_enabled gate ledu"
    assert "studentup_opt( 'saved_max'" in src, "saved_max limit ledu"
    assert "function studentup_saved_on()" in src, "saved_on() ledu"
    assert "function studentup_saved_max()" in src, "saved_max() ledu"
    # clamp — limit ni 5..200 madhya hold cheyyali
    assert "$max < 5" in src and "$max > 200" in src, "max clamp ledu"
    opts = read(THEME / "inc" / "options.php")
    assert "'saved_enabled' => array(" in opts, "options page lo field ledu"
    assert "'saved_max' => array(" in opts, "options page lo limit field ledu"


def test_save_button_helper() -> None:
    src = read(THEME / "inc" / "saved.php")
    assert "function studentup_save_button(" in src, "save button helper ledu"
    for attr in ("data-su-save", "data-id", "data-title", "data-url", "data-cat",
                 "aria-pressed", "aria-label"):
        assert attr in src, f"button lo {attr} ledu"
    # escaping helpers vadali
    for fn in ("esc_attr(", "esc_url(", "esc_html__(", "esc_attr__("):
        assert fn in src, f"{fn} use ledu (escaping)"


def test_shortcode_and_panel() -> None:
    src = read(THEME / "inc" / "saved.php")
    assert "add_shortcode( 'studentup_saved'" in src, "shortcode register ledu"
    assert "function studentup_saved_panel(" in src, "panel render ledu"
    assert "function studentup_saved_body_class(" in src, "body class ledu"
    assert "su-has-saved" in src, "body class value ledu"
    assert "data-su-saved-open" in src, "panel open trigger ledu"
    # empty-state server-side — JS lekunda kuda page baagundi
    assert "su-saved-empty" in src, "empty state ledu"


def test_assets_enqueue() -> None:
    src = read(THEME / "inc" / "saved.php")
    assert "studentup-saved.js" in src, "JS enqueue ledu"
    assert "wp_enqueue_script" in src, "wp_enqueue_script ledu"
    assert "wp_localize_script" in src, "localize ledu"
    assert "'studentup-saved'" in src, "script handle ledu"
    assert "STUDENTUP_SAVED" in src, "localize object ledu"
    assert "is_admin()" in src, "admin guard ledu"
    # defer/footer — 4th arg true
    assert re.search(r"'studentup-saved',[^;]+STUDENTUP_VERSION,\s*true", src), "footer load ledu"


def test_js_engine_source() -> None:
    src = read(THEME / "assets" / "js" / "studentup-saved.js")
    # comments theesesi code mattrame check cheyyali (comment lo mention cheste fail avvakoodadu)
    code = re.sub(r"/\*.*?\*/", "", src, flags=re.S)
    code = re.sub(r"//[^\n]*", "", code)
    assert not re.search(r"\bjQuery\s*\(|\$\(document", code), "jQuery use undi (vaddu)"
    # storage accesses anni try/catch lo (private mode crash vaddhu)
    assert "localStorage" in src, "localStorage use ledu"
    assert "catch (e) { return []; }" in src, "read guard ledu"
    assert "setItem" in src and "getItem" in src, "storage read/write ledu"
    assert "data-su-save" in src, "save click wiring ledu"
    assert "data-su-remove" in src, "remove wiring ledu"
    assert "aria-pressed" in src, "a11y state sync ledu"
    # XSS — title ni innerHTML lo pettakoodadu
    assert "innerHTML" not in code, "innerHTML use undi (XSS risk)"
    assert "textContent" in code, "textContent render ledu"
    assert "data-su-saved-open" in src, "panel open trigger wire ledu"
    assert "Escape" in src, "Escape close ledu"


def test_theme_integration() -> None:
    fn = read(THEME / "functions.php")
    assert "inc/saved.php" in fn, "functions.php lo require ledu"
    assert re.search(r"STUDENTUP_VERSION',\s*'([^']+)'", fn).group(1) == "1.9.8"
    header = read(THEME / "header.php")
    assert "data-su-saved-open" in header, "header lo saved button ledu"
    assert "data-su-saved-count" in header, "header lo count badge ledu"
    footer = read(THEME / "footer.php")
    assert "studentup_saved_panel()" in footer, "footer lo panel call ledu"
    single = read(THEME / "single.php")
    assert "studentup_save_button" in single, "single.php lo save button ledu"
    tpl = read(THEME / "inc" / "template.php")
    assert "studentup_save_button" in tpl, "card lo save button ledu"
    css = read(THEME / "style.css")
    for rule in (".su-save-btn", ".su-saved-panel", ".su-saved-toast", ".su-saved-page",
                 "body.dark .su-saved-panel"):
        assert rule in css, f"style.css lo {rule} ledu"


def test_real_behaviour_jsdom() -> None:
    """Idi static audit kaadu — nijamaina browser behaviour (jsdom)."""
    node = shutil.which("node")
    runner = ROOT / "tests" / "runtime" / "saved_runtime_test.js"
    assert runner.exists(), "saved_runtime_test.js ledu"
    if not node:
        print("      (node ledu — behavioural test SKIP)")
        return
    proc = subprocess.run([node, str(runner)], capture_output=True, text=True,
                          cwd=str(ROOT), timeout=300)
    out = (proc.stdout or "") + (proc.stderr or "")
    m = re.search(r"(\d+)/(\d+) checks passed", out)
    assert m, "runtime test run avvaledu:\n" + out[-800:]
    passed, total = int(m.group(1)), int(m.group(2))
    assert proc.returncode == 0 and passed == total, \
        f"behaviour fail: {passed}/{total}\n" + out[-800:]
    assert total >= 50, f"behaviour checks thakkuva: {total}"


def test_version_parity_193() -> None:
    php = re.search(r"STUDENTUP_VERSION',\s*'([^']+)'", read(THEME / "functions.php")).group(1)
    css = re.search(r"Version:\s*([0-9.]+)", read(THEME / "style.css")).group(1)
    stable = re.search(r"Stable tag:\s*([0-9.]+)", read(THEME / "readme.txt")).group(1)
    assert php == css == stable == "1.9.8", f"parity tappu: {php}·{css}·{stable}"
    readme = read(THEME / "readme.txt")
    for entry in ("= 1.9.0", "= 1.9.1", "= 1.9.2", "= 1.9.3", "= 1.9.4", "= 1.9.5", "= 1.9.6", "= 1.9.7", "= 1.9.8"):
        assert entry in readme, f"readme changelog {entry} ledu"
    assert "saved" in readme.lower(), "readme lo saved feature ledu"


def test_suite_pins_and_docs() -> None:
    for f in ("v75_test.py", "v76_test.py", "v77_test.py", "v78_test.py",
              "v79_test.py", "v80_test.py", "v81_test.py", "v89_test.py", "v91_test.py"):
        assert f"suites == {SUITES_EXPECTED}" in read(ROOT / "tests" / f), \
            f"{f} lo {SUITES_EXPECTED} pin ledu"
    suites = len(list((ROOT / "tests").glob("*_test.py")))
    assert suites == SUITES_EXPECTED, f"suites {suites} ({SUITES_EXPECTED} expect)"
    for doc in ("README.md", "MANUAL_ADVANCED_CHECKLIST.md", "GO_LIVE_CHECKLIST.md"):
        txt = read(ROOT / doc)
        assert f"{SUITES_EXPECTED}/{SUITES_EXPECTED}" in txt, f"{doc} lo {SUITES_EXPECTED}/{SUITES_EXPECTED} ledu"
        assert "v92" in txt, f"{doc} lo v92 ledu"


def test_zip_packaged() -> None:
    if not ZIP.exists():
        print("      (zip ledu — build_wp_theme.py run cheyandi, SKIP)")
        return
    z = zipfile.ZipFile(ZIP)
    names = z.namelist()
    for rel in ("studentup/inc/saved.php", "studentup/assets/js/studentup-saved.js"):
        assert rel in names, f"zip lo {rel} ledu"
    css = z.read("studentup/style.css").decode("utf-8")
    assert re.search(r"Version:\s*1\.9\.8", css), "zip lo css version 1.9.8 kaadu"
    php = z.read("studentup/functions.php").decode("utf-8")
    assert re.search(r"STUDENTUP_VERSION',\s*'1\.9\.8'", php), "zip lo php version 1.9.8 kaadu"
    assert all(n.startswith("studentup/") for n in names), "zip root tappu"


TESTS = [
    ("module + guards", test_module_exists_and_guarded),
    ("option gate + fields", test_option_gate_and_fields),
    ("save button helper", test_save_button_helper),
    ("shortcode + panel", test_shortcode_and_panel),
    ("assets enqueue", test_assets_enqueue),
    ("JS engine source", test_js_engine_source),
    ("theme integration", test_theme_integration),
    ("REAL behaviour (jsdom)", test_real_behaviour_jsdom),
    ("version parity (current)", test_version_parity_193),
    ("suite pins + docs", test_suite_pins_and_docs),
    ("zip packaged", test_zip_packaged),
]


def main() -> None:
    os.chdir(ROOT)
    print("=" * 70)
    print("v92 SAVED — reader retention regression tests (theme 1.9.3)")
    print("=" * 70)
    failed = 0
    for name, fn in TESTS:
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
        raise SystemExit(1)
    print("ALL v92 SAVED TESTS PASSED ✔")


if __name__ == "__main__":
    main()
