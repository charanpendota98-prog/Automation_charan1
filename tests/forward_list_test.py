# -*- coding: utf-8 -*-
"""v183 — daily forward list tests (offline, temp-path isolated).

Cover:
  1. Outsourcing section: category + contract-basis title → 'outsourcing'
  2. WhatsApp plain text: no HTML tags, *bold* headers, real links, today block
  3. Chunking: peddha list → chunks under limit, item boundaries intact
  4. save(): daily file + latest file
  5. run_cli: WP fail → rc 1 with honest message; rows → rc 0 + files
  6. Docs/cron wiring: --forward-list documented (parity gate) + theme board parity
  7. v184 hygiene: stale sweep · supersede (same recruitment) · closing-soon ⏰
  8. v184 state diff: new/gone + reasons (last date · kotha version) + state file
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
    """v187.2: Telugu wording · today block ledu (duplicate vaddhu) · prathi item ki link."""
    text = fl.build_whatsapp("https://studentup.in", ROWS, today=TODAY)
    assert "<b>" not in text and "<a href" not in text, "WhatsApp ki HTML tags poyayi"
    assert "*StudentUp — నేటి ఉద్యోగాల లిస్ట్*" in text
    assert "IVVALTI" not in text and "Daily Updates List" not in text, \
        "pata today block inka undi (user: idi kuda vaddu)"
    assert "🏛️ *తెలంగాణ ప్రభుత్వ ఉద్యోగాలు*" in text
    assert "💼 *అవుట్‌సోర్సింగ్ & కాంట్రాక్ట్ ఉద్యోగాలు*" in text
    assert "🆕" in text
    assert "TSPSC Group 2 Notification 2026" in text
    assert "*COMPLETE DETAILS*" not in text and "Complete Details" not in text
    assert "https://studentup.in" in text
    assert "వెరిఫై చేసుకోండి" in text, "Telugu disclaimer ledu"
    assert "Expired old notice" not in text, "expired post list lo undi"
    assert text.count("TSPSC Group 2") >= 1
    # v187.2: prathi item kinda mee site link — anni links open cheyyagalaru
    assert text.count("🔗 https://studentup.in/") == 4, text  # 5 rows -1 expired
    print("  2. WhatsApp Telugu format (sections · no duplicate · links) ✔")


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
        assert chunk.startswith("📋 *StudentUp — నేటి ఉద్యోగాల లిస్ట్ (ఇంకా)*"), chunk[:40]
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
    old_state = getattr(config, "FORWARD_LIST_STATE_PATH", None)
    real_gather = fl_mod.gather
    try:
        with tempfile.TemporaryDirectory() as tmp:
            config.FORWARD_LIST_PATH = Path(tmp) / "fwd.txt"
            config.FORWARD_LIST_STATE_PATH = Path(tmp) / "state.json"
            config.WP_SITE = "https://studentup.in"

            def boom(**kw):
                raise RuntimeError("WP offline (test)")
            fl_mod.gather = boom
            assert fl.run_cli(save_files=False, today=TODAY) == 1, "WP fail ki rc 1 ravali"

            fl_mod.gather = lambda **kw: ROWS
            assert fl.run_cli(save_files=True, today=TODAY) == 0
            saved = config.FORWARD_LIST_PATH.read_text(encoding="utf-8")
            assert "అవుట్‌సోర్సింగ్ & కాంట్రాక్ట్ ఉద్యోగాలు" in saved

            fl_mod.gather = lambda **kw: []
            assert fl.run_cli(save_files=False, today=TODAY) == 1, "empty list ki rc 1"
    finally:
        fl_mod.gather = real_gather
        config.FORWARD_LIST_PATH, config.WP_SITE = old_path, old_site
        if old_state is not None:
            config.FORWARD_LIST_STATE_PATH = old_state
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


def _row(rid, title, pub, slug, last_date="", cats=("ts-jobs",)):
    return {"id": rid, "title": title, "link": f"https://studentup.in/{slug}/",
            "date": pub, "category_slugs": list(cats), "last_date": last_date}


def test_v184_hygiene():
    """Expired out · stale (undated 120+) out · supersede · closing ⏰ marker."""
    rows = [
        _row(21, "TSPSC Group 2 Notification 2026 – Complete Details",
             "2026-09-20", "tspsc-old", "2026-10-10"),
        _row(22, "TSPSC Group 2 Notification 2026 – Apply Online",
             "2026-10-01", "tspsc-new", "2026-10-10"),
        _row(23, "Old undated notice", "2026-05-01", "old-undated"),
        _row(24, "SSC CGL Notification 2026", "2026-09-20", "ssc", "2026-09-30"),
        _row(25, "TS DSC Hall Ticket 2026", "2026-10-02", "ts-ht",
             "2026-10-04", cats=("hall-tickets",)),
        _row(26, "Ancient post with real deadline", "2026-01-01", "ancient", "2026-11-30"),
    ]
    norm = od.normalize_rows(rows, today=TODAY, stale_days=120)
    ids = {r["id"] for r in norm}
    assert 21 not in ids, "supersede jaragaledu (puratana version list lo undi)"
    assert 22 in ids, "kotha version list lo ledu"
    assert 23 not in ids, "stale (undated 120+) post list lo undi"
    assert 24 not in ids, "expired post list lo undi"
    assert 25 in ids and 26 in ids
    # deadline unna puratana post stay (guess cheyyakudadu)
    assert [r["superseded"] for r in norm if r["id"] == 22] == [21]
    soon = {r["id"]: r for r in norm}
    assert soon[25]["closing_soon"] is True and soon[26]["closing_soon"] is False
    assert od.wa_deadline_note(soon[25]["days_left"]) == "⏰ 2 days left"
    assert od.wa_deadline_note(None) == "" and od.wa_deadline_note(9) == ""
    assert od.wa_deadline_note(0) == "⏰ last date TODAY"
    text = od.render_whatsapp("https://studentup.in", rows, today=TODAY,
                              changes={"new": 2, "gone": 1})
    # v187.2 Telugu wording (v184 hygiene logic same — markers mattrame Telugu)
    assert "⏰ 2 రోజులు మాత్రమే" in text and "కొత్త ఉద్యోగాలు" in text
    assert "📈" in text and "IVVALTI" not in text
    print("  7. v184 hygiene: expired/stale/supersede/closing-soon ✔")


def test_v184_state_diff():
    """Roju state: 🆕 new ids · ❌ gone + honest reasons (last date / kotha version)."""
    with tempfile.TemporaryDirectory() as tmp:
        st = Path(tmp) / "state.json"
        day1 = [
            _row(31, "TSPSC Group 2 Notification 2026", "2026-09-20", "a", "2026-10-05"),
            _row(32, "RRB NTPC Notification 2026", "2026-09-25", "b", "2026-10-15"),
        ]
        new1, gone1, data, target = fl.diff_and_update(day1, today=date(2026, 10, 1), path=st)
        assert {r["id"] for r in new1} == {31, 32} and gone1 == []
        assert target.exists() and data["items"]["31"]["first_seen"] == "2026-10-01"

        day2 = [
            _row(33, "TSPSC Group 2 Notification 2026 – Apply Online", "2026-10-02",
                 "a2", "2026-10-05"),                      # same recruitment → supersede
            _row(32, "RRB NTPC Notification 2026", "2026-09-25", "b", "2026-10-15"),
            _row(34, "Fresh AP DSC Recruitment 2026", "2026-10-02", "c", ""),
        ]
        new2, gone2, data2, _ = fl.diff_and_update(day2, today=date(2026, 10, 2), path=st)
        assert {r["id"] for r in new2} == {33, 34}, [r["id"] for r in new2]
        reasons = {str(r["id"]): r["reason"] for r in gone2}
        assert "31" in reasons and "kotha version" in reasons["31"], reasons
        # last-date expiry reason (post was active yesterday, deadline passed today)
        assert "last date" in fl._reason_gone(
            {"last_date": "2026-10-01", "section": "ts", "title": "X Recruitment"},
            date(2026, 10, 2), 120, {})
        # corrupt state file → fresh start (list eppudu block avvadu)
        st.write_text("{not json", encoding="utf-8")
        new3, gone3, _, _ = fl.diff_and_update(day2, today=date(2026, 10, 3), path=st)
        assert {r["id"] for r in new3} == {33, 34, 32}, [r["id"] for r in new3]
    print("  8. v184 state diff: new/gone + reasons + corrupt-file safety ✔")


def test_v184_php_and_env_parity():
    php = (ROOT / "wordpress-theme/studentup/inc/opportunities.php").read_text(encoding="utf-8")
    for needle in ("studentup_opportunity_stale_days", "studentup_opportunity_title_key",
                   "studentup_opportunity_is_stale", "apply_filters( 'studentup_opportunity_stale_days'"):
        assert needle in php, f"PHP parity miss: {needle}"
    env = (ROOT / ".env.example").read_text(encoding="utf-8")
    for knob in ("OPPORTUNITY_STALE_DAYS", "FORWARD_LIST_STATE_PATH"):
        assert knob in env, f".env.example lo {knob} ledu"
    py = (ROOT / "autoblog/opportunity_digest.py").read_text(encoding="utf-8")
    assert "def title_key" in py and "def supersede" in py and "def is_stale" in py
    print("  9. v184 PHP ↔ bot ↔ .env parity ✔")


def main() -> None:
    print("=" * 70)
    print("  v183+v184 — DAILY FORWARD LIST (WhatsApp-ready · open/expire/new)")
    print("=" * 70)
    test_outsourcing_section()
    test_whatsapp_format()
    test_chunking()
    test_save_files()
    test_run_cli_paths()
    test_docs_and_board_parity()
    test_v184_hygiene()
    test_v184_state_diff()
    test_v184_php_and_env_parity()
    print("-" * 70)
    print("ALL v183+v184 FORWARD-LIST TESTS PASSED ✔")


if __name__ == "__main__":
    main()
