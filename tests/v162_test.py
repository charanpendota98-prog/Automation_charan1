# -*- coding: utf-8 -*-
"""v162 — ad slot A/B (slot lab)."""
from __future__ import annotations

from pathlib import Path

from autoblog import slot_lab as sl

ROOT = Path(__file__).resolve().parents[1]
THEME = ROOT / "wordpress-theme" / "studentup"


def _csv(tmp_path: Path, body: str) -> Path:
    p = tmp_path / "ads.csv"
    p.write_text(body, encoding="utf-8")
    return p


def test_real_adsense_headers_parse(tmp_path):
    rows = sl.parse_csv(_csv(tmp_path,
        'Ad unit,Ad impressions,Estimated earnings (INR)\n'
        'mid-A,"24,120","1,880.50"\n'))
    assert rows == [{"name": "mid-A", "impressions": 24120, "revenue": 1880.50}], rows
    print("      AdSense locale headers and comma numbers parse ✔")


def test_thin_data_never_declares_a_winner(tmp_path):
    rows = sl.parse_csv(_csv(tmp_path,
        "Ad unit,Impressions,Revenue\nmid-A,900,100\nmid-B,800,10\n"))
    res = sl.compare(sl.group(rows)["mid"])
    assert res["verdict"] == "NEED_DATA", res
    print("      a 10x 'lift' on 900 impressions is refused, not celebrated ✔")


def test_small_lift_is_called_noise(tmp_path):
    rows = sl.parse_csv(_csv(tmp_path,
        "Ad unit,Impressions,Revenue\nmid-A,50000,1000\nmid-B,50000,1010\n"))
    res = sl.compare(sl.group(rows)["mid"])
    assert res["verdict"] == "NO_WINNER", res
    print("      a 1% difference is reported as noise ✔")


def test_clear_winner_is_reported(tmp_path):
    rows = sl.parse_csv(_csv(tmp_path,
        "Ad unit,Impressions,Revenue\nmid-A,24120,1880.50\nmid-B,23940,2310.75\n"))
    res = sl.compare(sl.group(rows)["mid"])
    assert res["verdict"] == "WINNER" and res["winner"] == "B"
    assert res["lift"] > 20
    print("      a real 23% RPM lift is declared a winner ✔")


def test_units_without_variant_suffix_are_ignored(tmp_path):
    rows = sl.parse_csv(_csv(tmp_path,
        "Ad unit,Impressions,Revenue\nsidebar,12000,300\nmid-A,20000,500\n"))
    grouped = sl.group(rows)
    assert "sidebar" not in grouped and "mid" in grouped
    print("      non-experiment ad units stay out of the comparison ✔")


def test_theme_split_is_off_without_a_b_slot():
    php = (THEME / "inc" / "slotlab.php").read_text(encoding="utf-8")
    assert "'' === $slot_b || ! studentup_opt( 'slot_lab', '0' )" in php, \
        "B id lekunda kuda traffic split avutundi"
    assert "static $variant" in php, "request lo variant stable ga ledu"
    assert "setcookie" not in php and "REMOTE_ADDR" not in php, \
        "cookie/IP vaadutundi — consent problem"
    ads = (THEME / "inc" / "ads.php").read_text(encoding="utf-8")
    assert "studentup_slot_for(" in ads, "ads.php variant slot vaadatledu"
    opts = (THEME / "inc" / "options.php").read_text(encoding="utf-8")
    assert "'slot_lab'" in opts and "adsense_slot_mid_b" in opts
    funcs = (THEME / "functions.php").read_text(encoding="utf-8")
    assert "inc/slotlab.php" in funcs
    print("      no B slot id => no split, no cookies, no IP ✔")


def test_flag_documented():
    main = (ROOT / "autoblog" / "main.py").read_text(encoding="utf-8")
    assert '"--slot-lab"' in main and "args.slot_lab" in main
    for name in ("README.md", "MANUAL_ADVANCED_CHECKLIST.md", "GO_LIVE_CHECKLIST.md"):
        assert "--slot-lab" in (ROOT / name).read_text(encoding="utf-8"), name
    print("      --slot-lab documented in all 3 docs ✔")
