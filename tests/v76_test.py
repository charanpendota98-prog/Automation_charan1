# -*- coding: utf-8 -*-
"""v76 tests — QUALIFICATION DROPDOWN (chips → select) + UI DE-JUNK.

Enduku idi:
  10th/Inter/Degree filters mobile lo chips ga clutter — dropdown best
  (native control · counts · shareable ?qual= link). Preview + WP theme
  rendu marayi (parity), logic/filtering same (v72 engine intact).
  Same pass lo UI sodi clean + live-exam remnants final proof.

Checks (offline only):
  * preview: select#qualsel + 9 options order + label + qcount (chips levu)
  * preview JS: change filter + live counts + ?qual= deep-link + URL sync
  * preview CSS: .qualsel shipped · .qchip poyindi
  * jsdom 164/164 (behavioral — dropdown tho kuda green)
  * theme: qual_bar form+select+noscript+closing+counts · JS wiring + state sync
  * theme CSS + php-lint + zip fresh + qualsel zip lo
  * bot pins: guardian/readiness qualsel needles (chips pins poyayi)
  * live-exam remnants: product surfaces lo 0 (quiz = practice matrame)
  * UI sodi: ad dup text poyindi · tel: 10-digit intact · poll/quiz distinct
  * docs: README v76 + MANUAL PART 35 + 58/58 claims

Run: python tests/v76_test.py   (also via python run.py --test-all)
"""
from __future__ import annotations

import re
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

PREVIEW = ROOT / "preview"
THEME = ROOT / "wordpress-theme" / "studentup"
ORDER = ["all", "10th", "inter", "iti", "diploma", "degree", "pg", "btech",
         "closing"]


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


# ------------------------------------------------- 1-3. preview dropdown

def test_preview_dropdown_markup():
    html = read(PREVIEW / "index.html")
    assert 'class="chip qchip' not in html and "soonchip" not in html, \
        "chips inka unnayi"
    sel = re.search(r'<select[^>]*id="qualsel"[^>]*>(.*?)</select>', html, re.S)
    assert sel, "qualsel dropdown ledu"
    opts = re.findall(r'<option value="([a-z0-9]+)"', sel.group(1))
    assert opts == ORDER, f"option order tappu: {opts}"
    assert '<label class="quallabel" for="qualsel">' in html
    assert 'id="qcount"' in html
    assert "10th Pass" in sel.group(1), "10th label best ga ledu"


def test_preview_dropdown_js():
    html = read(PREVIEW / "index.html")
    for needle in ('getElementById("qualsel")', 'addEventListener("change"',
                   "qualSel.value", "?qual=", "replaceState",
                   'o.textContent+" ("+n+")"', "activeQual", "okQual"):
        assert needle in html, f"JS needle ledu: {needle}"
    assert 'querySelectorAll(".qchip")' not in html


def test_preview_dropdown_css():
    html = read(PREVIEW / "index.html")
    assert ".qualsel{" in html and ".quallabel{" in html
    assert ".qchip{" not in html and ".soonchip{" not in html


# ------------------------------------------------- 4. jsdom behavioral

def test_jsdom_still_green():
    proc = subprocess.run(["node", str(ROOT / "tests" / "runtime" /
                                       "jsdom_runtime_test.js")],
                          capture_output=True, text=True, timeout=180,
                          cwd=ROOT / "tests" / "runtime")
    out = (proc.stdout or "") + (proc.stderr or "")
    assert proc.returncode == 0, out[-400:]
    assert "164/164 checks passed" in out, out[-200:]
    assert "check count drift" not in out


# ------------------------------------------------- 5-6. theme parity

def test_theme_dropdown_markup_and_js():
    q = read(THEME / "inc" / "qual-filter.php")
    for needle in ('<form class="qrow qualform"', 'id="qualsel"',
                   'name="qual"', "<noscript>", 'value="closing"',
                   "studentup_qual_count( $slug )", "selected( $current"):
        assert needle in q, f"qual_bar needle ledu: {needle}"
    assert "qchip" not in q and "qchips" not in q
    js = read(THEME / "assets" / "js" / "studentup.js")
    for needle in ('getElementById("qualsel")', 'addEventListener("change"',
                   "qualsel.value", "replaceState"):
        assert needle in js, f"theme JS needle ledu: {needle}"
    assert 'querySelectorAll(".qchip")' not in js
    css = read(THEME / "style.css")
    assert ".qualsel{" in css and ".qchip{" not in css


def test_theme_lint_and_zip():
    proc = subprocess.run(["node", str(ROOT / "tools" / "php_lint.js")],
                          capture_output=True, text=True, timeout=120)
    assert "files OK" in (proc.stdout or ""), proc.stdout + proc.stderr
    proc2 = subprocess.run(["node", "--check",
                            str(THEME / "assets" / "js" / "studentup.js")],
                           capture_output=True, text=True, timeout=60)
    assert proc2.returncode == 0, proc2.stderr[:200]
    zpath = ROOT / "wordpress-theme" / "studentup-theme.zip"
    newest = max(p.stat().st_mtime for p in THEME.rglob("*") if p.is_file())
    assert zpath.stat().st_mtime >= newest, "zip stale — rebuild cheyandi"
    zf = zipfile.ZipFile(zpath)
    assert "studentup_wa_number" in zf.read(
        "studentup/inc/options.php").decode("utf-8")
    assert 'id="qualsel"' in zf.read(
        "studentup/inc/qual-filter.php").decode("utf-8")


# ------------------------------------------------- 7. bot pins moved

def test_bot_pins_use_qualsel():
    guardian = read(ROOT / "autoblog" / "guardian.py")
    readiness = read(ROOT / "autoblog" / "readiness.py")
    assert "'id=\"qualsel\"'" in guardian or 'id="qualsel"' in guardian
    assert 'id="qualsel"' in readiness and 'value="10th"' in readiness
    assert "qchip" not in guardian and "qchip" not in readiness


# ------------------------------------------------- 8-9. exam-free + sodi

def test_no_live_exam_remnants():
    blobs = []
    for p in list(PREVIEW.rglob("*.html")) + \
            list((THEME).rglob("*.php")) + [ROOT / "ads" / "house.json"]:
        blobs.append(read(p))
    if (PREVIEW / "manifest.webmanifest").exists():
        blobs.append(read(PREVIEW / "manifest.webmanifest"))
    joint = "\n".join(blobs)
    assert not re.search(r"live[\s_-]*exam", joint, re.I), "live-exam remnant!"
    assert "#exam" not in joint and "live_exam" not in joint
    assert '"url": "./index.html#quiz"' in joint, "quiz shortcut poyindi?"


def test_ui_sodi_clean():
    html = read(PREVIEW / "index.html")
    assert "Your brand<br>right here<br>Your brand here" not in html
    assert "Your brand<br>right here" in html
    assert "tel:9182739312" in html and "tel:+91" not in html
    assert 'id="poll"' in html and 'id="quiz"' in html and \
        'id="quizpromo"' in html, "poll/quiz blocks intact undali"


# ------------------------------------------------- 10. docs

def test_docs_v76():
    suites = len(list((ROOT / "tests").glob("*_test.py")))
    assert suites == 58, f"suites {suites} (v76 tho 58 expect)"
    readme = read(ROOT / "README.md")
    manual = read(ROOT / "MANUAL_ADVANCED_CHECKLIST.md")
    go_live = read(ROOT / "GO_LIVE_CHECKLIST.md")
    assert "### v76" in readme and "58/58" in readme
    assert "PART 35" in manual and "v76" in manual and "58/58" in manual
    assert "58/58" in go_live
    for name, txt in (("README", readme), ("MANUAL", manual),
                      ("GO_LIVE", go_live)):
        assert "164/164" in txt, f"{name} lo jsdom claim poyindi"


TESTS = [
    ("preview dropdown markup (9 options + label)", test_preview_dropdown_markup),
    ("preview dropdown JS (counts + ?qual= + URL)", test_preview_dropdown_js),
    ("preview CSS (.qualsel, chips gone)", test_preview_dropdown_css),
    ("jsdom 164/164 behavioral", test_jsdom_still_green),
    ("theme dropdown + JS parity", test_theme_dropdown_markup_and_js),
    ("theme lint + zip fresh", test_theme_lint_and_zip),
    ("bot pins moved to qualsel", test_bot_pins_use_qualsel),
    ("live-exam remnants 0", test_no_live_exam_remnants),
    ("UI sodi clean", test_ui_sodi_clean),
    ("docs: README v76 + MANUAL PART 35 + 58/58", test_docs_v76),
]


def main() -> None:
    print("=" * 70)
    print("  v76 — QUALIFICATION DROPDOWN + UI DE-JUNK")
    print("=" * 70)
    failed = 0
    for name, fn in TESTS:
        try:
            fn()
        except AssertionError as exc:
            failed += 1
            print(f"  {name} ✘  {exc}")
        except Exception as exc:  # noqa: BLE001
            failed += 1
            print(f"  {name} ✘  {type(exc).__name__}: {exc}")
        else:
            print(f"  {name} ✔")
    print("-" * 70)
    if failed:
        print(f"  {failed} TEST(S) FAILED ✘")
        raise SystemExit(1)
    print("ALL v76 QUAL-DROPDOWN TESTS PASSED ✔")


if __name__ == "__main__":
    main()
