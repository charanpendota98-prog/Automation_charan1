# -*- coding: utf-8 -*-
"""v151 — saved-job reminders, RPM report, save-as-PDF."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from autoblog import rpm_report  # noqa: E402

THEME = ROOT / "wordpress-theme" / "studentup"

ROWS = [
    {"name": "/tspsc-group-2", "views": 12000, "revenue": 42.5},
    {"name": "/old-post", "views": 9000, "revenue": 2.1},
    {"name": "/ssc-cgl", "views": 6000, "revenue": 25.0},
    {"name": "/tiny", "views": 20, "revenue": 0.0},
]


def test_site_rpm_maths():
    rep = rpm_report.analyse(ROWS)
    assert rep["views"] == 27020
    assert abs(rep["site_rpm"] - round(69.6 / 27020 * 1000, 2)) < 0.05
    print("      site RPM computed from real totals ✔")


def test_weak_slots_flagged_with_upside():
    rep = rpm_report.analyse(ROWS)
    weak = [r["name"] for r in rep["weak"]]
    assert "/old-post" in weak, "low-RPM high-traffic page miss ayyindi"
    assert "/tiny" not in weak, "noise (low views) filter ledu"
    assert rep["upside_estimate"] > 0 and rep["status"] == "review"
    print("      weak pages flagged with an honest upside estimate ✔")


def test_rpm_tool_is_read_only():
    src = (ROOT / "autoblog" / "rpm_report.py").read_text(encoding="utf-8")
    for banned in ("wordpress_client", "update_post", "create_post", "adsbygoogle"):
        assert banned not in src, f"{banned} undakoodadu — report-only tool"
    print("      RPM tool never edits ad code ✔")


def test_csv_loader(tmp_path):
    p = tmp_path / "Pages.csv"
    p.write_text("Page,Pageviews,Estimated earnings\n/a,1200,5.50\n", encoding="utf-8")
    rows = rpm_report.load_csv(p)
    assert rows[0]["name"] == "/a" and rows[0]["views"] == "1200"
    print("      AdSense CSV export parses ✔")


def test_cli_wired():
    src = (ROOT / "autoblog" / "main.py").read_text(encoding="utf-8")
    assert "--rpm-report" in src and "rpm_report as _rr" in src
    print("      run.py --rpm-report wired ✔")


def test_saved_reminders_are_privacy_safe():
    src = (THEME / "inc" / "remind.php").read_text(encoding="utf-8")
    assert "localStorage" in src, "reminders must read the reader's own saved list"
    assert "fetch(" not in src and "XMLHttpRequest" not in src, "server ki data pampakoodadu"
    assert "Notification.requestPermission" in src
    assert "su-remind-allow" in src, "permission prompt button vెనుక undali"
    # the prompt must be behind a click, never fired on load
    before_click = src.split("requestPermission")[0]
    assert "addEventListener('click'" in before_click, "unsolicited notification prompt vaddu"
    fns = (THEME / "functions.php").read_text(encoding="utf-8")
    assert "inc/remind.php" in fns
    print("      reminders: local only, permission behind a click ✔")


def test_pdf_button_is_browser_only():
    src = (THEME / "inc" / "engage.php").read_text(encoding="utf-8")
    assert "studentup_pdf_button" in src and "window.print()" in src
    assert "is_single()" in src
    css = (THEME / "style.css").read_text(encoding="utf-8")
    print_blocks = [b[:500] for b in css.split("@media print")[1:]]
    assert any(".su-ad" in b and "display:none" in b for b in print_blocks), \
        "print sheet lo ads hide cheyali"
    single = (THEME / "single.php").read_text(encoding="utf-8")
    assert "studentup_pdf_button();" in single
    print("      save-as-PDF uses the browser only, ads hidden in print ✔")


TESTS = [
    ("rpm maths", test_site_rpm_maths),
    ("weak slots", test_weak_slots_flagged_with_upside),
    ("read-only", test_rpm_tool_is_read_only),
    ("cli", test_cli_wired),
    ("reminders", test_saved_reminders_are_privacy_safe),
    ("pdf", test_pdf_button_is_browser_only),
]


def main() -> int:
    bad = 0
    for name, fn in TESTS:
        try:
            fn()
            print(f"  {name} ✔")
        except Exception as exc:  # noqa: BLE001
            bad += 1
            print(f"  {name} ✘ {type(exc).__name__}: {exc}")
    print("-" * 70)
    print("ALL v151 TESTS PASSED ✔" if not bad else f"{bad} TEST(S) FAILED ✘")
    return int(bool(bad))


if __name__ == "__main__":
    raise SystemExit(main())
