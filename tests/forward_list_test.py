# -*- coding: utf-8 -*-
"""v183 — daily forward list tests (offline, temp-path isolated).

Cover:
  1. Outsourcing section: category + contract-basis title → 'outsourcing'
  2. WhatsApp plain text: no HTML tags, *bold* headers, real links, today block
  3. Chunking: peddha list → chunks under limit, item boundaries intact
  4. save(): daily file + latest file
  5. run_cli: WP fail → rc 1 with honest message; rows → rc 0 + files
  6. Docs/cron wiring: --forward-list documented (parity gate) + theme board parity
"""
from __future__ import annotations

import sys
import tempfile
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from autoblog import config, forward_list as fl, opportunity_digest as od  # noqa: E402

TODAY = date(2026, 10, 2)

ROWS = [
    {"id": 11, "title": "TSPSC Group 2 Notification 2026 – Complete Details",
     "link": "https://studentup.in/tspsc-group-2/", "date": "2026-10-02",
     "category_slugs": ["ts-jobs"], "last_date": "2026-10-20"},
    {"id": 12, "title": "Anganwadi Outsourcing posts TS 2026",
     "link": "https://studentup.in/anganwadi-outsourcing/", "date": "2026-10-02",
     "category_slugs": ["outsourcing-jobs"], "last_date": ""},
    {"id": 13, "title": "Contract basis guest faculty recruitment AP",
     "link": "https://studentup.in/guest-faculty-ap/", "date": "2026-09-30",
     "category_slugs": [], "last_date": ""},
    {"id": 14, "title": "AP DSC Hall Ticket 2026 download",
     "link": "https://studentup.in/ap-dsc-hall-ticket/", "date": "2026-09-29",
     "category_slugs": ["hall-tickets"], "last_date": "2026-11-01"},
    {"id": 15, "title": "Expired old notice", "link": "https://studentup.in/old/",
     "date": "2026-08-01", "category_slugs": ["ts-jobs"], "last_date": "2026-09-01"},
]


def test_outsourcing_section():
    assert od.section_for_row(ROWS[1]) == "outsourcing", "outsourcing category map kaledu"
    assert od.section_for_row(ROWS[2]) == "outsourcing", "contract-basis title fallback ledu"
    groups = od.group_rows(ROWS, today=TODAY)
    assert len(groups["outsourcing"]) == 2, groups["outsourcing"]
    assert len(groups["ts"]) == 1 and len(groups["hall-tickets"]) == 1
    assert od.section_for_row(ROWS[4]) == "ts"          # expired gating veru
    print("  1. outsourcing section (category + title fallback) ✔")


def test_whatsapp_format():
    text = fl.build_whatsapp("https://studentup.in", ROWS, today=TODAY)
    assert "<b>" not in text and "<a href" not in text, "WhatsApp ki HTML tags poyayi"
    assert "*StudentUp — Daily Updates List*" in text
    assert "🆕 *IVVALTI KOTHAAVI (today)*" in text
    assert "💼 *OUTSOURCING & CONTRACT JOBS*" in text
    assert "🆕" in text and "*TELANGANA GOVERNMENT JOBS*" in text
    assert "TSPSC Group 2 Notification 2026" in text
    assert "*COMPLETE DETAILS*" not in text and "Complete Details" not in text
    assert "https://studentup.in" in text
    assert "verify cheyyandi" in text
    assert "Expired old notice" not in text, "expired post list lo undi"
    assert text.count("TSPSC Group 2") >= 1
    print("  2. WhatsApp plain-text format (sections · today · no HTML) ✔")


def test_chunking():
    many = []
    for i in range(60):
        many.append({"id": 500 + i, "title": f"Post number {i} with a reasonably long title",
                     "link": f"https://studentup.in/post-{i}/", "date": "2026-09-20",
                     "category_slugs": ["ts-jobs"], "last_date": ""})
    chunks = od.render_whatsapp_messages("https://studentup.in", many, today=TODAY,
                                         per_section=60, today_block=False, max_chars=1200)
    assert len(chunks) >= 2, "peddha list split kaledu"
    for chunk in chunks:
        assert len(chunk) <= 1400, (len(chunk), chunk[:120])
    for chunk in chunks[1:]:
        assert chunk.startswith("📋 *StudentUp Daily List (contd.)*"), chunk[:40]
    joined = "\n".join(chunks)
    for i in range(60):
        assert f"🔗 https://studentup.in/post-{i}/" in joined
    print(f"  3. chunking ({len(chunks)} chunks · item boundaries intact) ✔")


def test_save_files():
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp) / "forward-list.txt"
        written = fl.save(["hello list"], path=base, today=TODAY)
        assert len(written) == 2
        assert (Path(tmp) / "forward-list-2026-10-02.txt").read_text(encoding="utf-8").strip() == "hello list"
        assert base.read_text(encoding="utf-8").strip() == "hello list"
    print("  4. save(): roju file + latest file ✔")


def test_run_cli_paths():
    import autoblog.forward_list as fl_mod

    old_path, old_site = config.FORWARD_LIST_PATH, config.WP_SITE
    real_gather = fl_mod.gather
    try:
        with tempfile.TemporaryDirectory() as tmp:
            config.FORWARD_LIST_PATH = Path(tmp) / "fwd.txt"
            config.WP_SITE = "https://studentup.in"

            def boom(**kw):
                raise RuntimeError("WP offline (test)")
            fl_mod.gather = boom
            assert fl.run_cli(save_files=False, today=TODAY) == 1, "WP fail ki rc 1 ravali"

            fl_mod.gather = lambda **kw: ROWS
            assert fl.run_cli(save_files=True, today=TODAY) == 0
            saved = config.FORWARD_LIST_PATH.read_text(encoding="utf-8")
            assert "OUTSOURCING & CONTRACT JOBS" in saved

            fl_mod.gather = lambda **kw: []
            assert fl.run_cli(save_files=False, today=TODAY) == 1, "empty list ki rc 1"
    finally:
        fl_mod.gather = real_gather
        config.FORWARD_LIST_PATH, config.WP_SITE = old_path, old_site
    print("  5. run_cli: WP fail / rows / empty paths ✔")


def test_docs_and_board_parity():
    for name in ("README.md", "MANUAL_ADVANCED_CHECKLIST.md", "MILESWEB_GO_LIVE.md"):
        text = (ROOT / name).read_text(encoding="utf-8")
        assert "--forward-list" in text, f"{name} lo --forward-list ledu"
    cron = (ROOT / "crontab.example").read_text(encoding="utf-8")
    assert "--forward-list" in cron, "crontab lo forward line ledu"
    php = (ROOT / "wordpress-theme/studentup/inc/opportunities.php").read_text(encoding="utf-8")
    assert "'outsourcing'" in php and "Outsourcing & Contract Jobs" in php, \
        "site board lo outsourcing section ledu (site ↔ bot parity)"
    py = (ROOT / "autoblog/opportunity_digest.py").read_text(encoding="utf-8")
    assert "outsourcing" in py and "Outsourcing & Contract Jobs" in py, \
        "bot digest lo outsourcing section ledu"
    env = (ROOT / ".env.example").read_text(encoding="utf-8")
    assert "FORWARD_LIST_PATH" in env, ".env.example lo FORWARD_LIST_PATH ledu"
    print("  6. docs · cron · .env · site↔bot board parity ✔")


def main() -> None:
    print("=" * 70)
    print("  v183 — DAILY FORWARD LIST (WhatsApp-ready)")
    print("=" * 70)
    test_outsourcing_section()
    test_whatsapp_format()
    test_chunking()
    test_save_files()
    test_run_cli_paths()
    test_docs_and_board_parity()
    print("-" * 70)
    print("ALL v183 FORWARD-LIST TESTS PASSED ✔")


if __name__ == "__main__":
    main()
