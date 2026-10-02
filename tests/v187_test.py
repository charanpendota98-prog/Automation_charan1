# -*- coding: utf-8 -*-
"""v187 — multi-link intake + rich WhatsApp list tests (offline).

Cover:
  1. parse_links: WhatsApp/notes paste (numbered name line + markdown link),
     plain URLs, dedupe, label capture
  2. load_links: file + inline combo, missing file → FileNotFoundError
  3. intake: prathi link ki **veru draft** (fake creator) · refresh detect ·
     okka link fail aina migilinavi continue · limit cap · dry-run plan
  4. report_text + run_cli rc (dry-run 0 · empty 2 · created 0) + report file
  5. WhatsApp list v187: posts count · last-date line · section totals
  6. docs/cron/.env wiring
"""
from __future__ import annotations

import json
import re
import sys
import tempfile
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from autoblog import config, link_intake as li, opportunity_digest as od  # noqa: E402

PASTE = """# Aa roju list
1. **ECIL (310 ITI Trade Apprentice Posts)**
   - [https://www.ecil.co.in](https://www.ecil.co.in)
2. **IIT Hyderabad (Project Associate Positions)**
   - [https://www.iith.ac.in/careers](https://www.iith.ac.in/careers)
3. SSC CGL 2026 Notification (1000+ posts)
   - [Apply here](https://ssc.gov.in/notice.pdf)

https://ssc.gov.in/notice.pdf      # duplicate — okkasari mattrame
"""


def test_parse_links():
    pairs = li.parse_links(PASTE)
    assert len(pairs) == 3, pairs
    labels = [l for l, _ in pairs]
    urls = [u for _, u in pairs]
    assert labels[0].startswith("ECIL (310 ITI"), labels
    assert labels[1].startswith("IIT Hyderabad"), labels
    assert labels[2] == "Apply here", labels
    assert urls == ["https://www.ecil.co.in", "https://www.iith.ac.in/careers",
                    "https://ssc.gov.in/notice.pdf"]
    # plain + trailing punctuation
    plain = li.parse_links("see https://a.com/x). and https://b.com/y")
    assert [u for _, u in plain] == ["https://a.com/x", "https://b.com/y"], plain
    assert li.parse_links("no links here") == []
    print("  1. parse_links (paste · markdown · dedupe · punctuation) ✔")


def test_load_links_and_missing_file():
    with tempfile.TemporaryDirectory() as tmp:
        f = Path(tmp) / "links.txt"
        f.write_text(PASTE, encoding="utf-8")
        pairs = li.load_links("https://inline.com/z", str(f))
        assert len(pairs) == 4 and pairs[-1][1] == "https://inline.com/z", pairs
        try:
            li.load_links("", str(Path(tmp) / "nope.txt"))
            raise AssertionError("missing file raise avvali")
        except FileNotFoundError:
            pass
    print("  2. load_links (file + inline · missing file) ✔")


def test_intake_separate_drafts():
    calls = []

    def fake_creator(url):
        calls.append(url)
        if "iith" in url:
            raise RuntimeError("source fetch fail (test)")
        if "ecil" in url:
            return {"status": "refresh", "link": "https://studentup.in/ecil/"}
        return {"link": "https://studentup.in/ssc-cgl/"}

    pairs = li.parse_links(PASTE)
    rep = li.intake(pairs, limit=10, creator=fake_creator)
    assert calls == [u for _, u in pairs], "prathi link ki separate call ravali"
    assert rep["created"] == 1 and rep["refreshed"] == 1 and rep["failed"] == 1, rep
    assert rep["items"][1]["status"] == "failed" and "fetch fail" in rep["items"][1]["detail"]
    # limit cap
    calls.clear()
    rep2 = li.intake(pairs, limit=2, creator=fake_creator)
    assert len(calls) == 2 and rep2["skipped"] == 1, rep2
    # dry-run → eem create cheyyadu
    calls.clear()
    rep3 = li.intake(pairs, limit=10, dry_run=True, creator=fake_creator)
    assert calls == [] and rep3["dry_run"] and len(rep3["items"]) == 3
    print("  3. intake: separate drafts · refresh · per-link fail · limit · dry-run ✔")


def test_report_and_cli():
    with tempfile.TemporaryDirectory() as tmp:
        old = (config.LINK_INTAKE_REPORT, config.LINK_INTAKE_MAX)
        try:
            config.LINK_INTAKE_REPORT = Path(tmp) / "intake.json"
            config.LINK_INTAKE_MAX = 5
            # dry-run rc 0 + report file
            assert li.run_cli(links="https://a.com/x", dry_run=True) == 0
            data = json.loads(config.LINK_INTAKE_REPORT.read_text(encoding="utf-8"))
            assert data["dry_run"] and data["items"][0]["url"] == "https://a.com/x"
            # links ledu → rc 2
            assert li.run_cli() == 2
            assert li.run_cli(file_path=str(Path(tmp) / "nope.txt")) == 2
        finally:
            config.LINK_INTAKE_REPORT, config.LINK_INTAKE_MAX = old
        rep = {"created": 2, "refreshed": 0, "failed": 1, "skipped": 0,
               "items": [{"status": "created", "label": "ECIL", "url": "u", "post": "p"},
                         {"status": "failed", "label": "", "url": "v",
                          "detail": "ValueError: x"}]}
        text = li.report_text(rep)
        assert "2 kotha draft" in text and "[failed]" in text
    print("  4. report + CLI rc (dry-run 0 · empty 2) + report file ✔")


def test_whatsapp_rich_items():
    """v187.2 (user feedback): Telugu list · no duplicate today block · software English."""
    rows = [
        {"id": 1, "title": "ECIL ITI Trade Apprentice Recruitment 2026 – Complete Details",
         "link": "https://studentup.in/ecil/", "date": "2026-10-02",
         "category_slugs": ["central-jobs"], "last_date": "2026-10-20",
         "vacancies": "310", "salary": "₹18,000 – ₹22,000"},
        {"id": 2, "title": "SSC CGL 2026 Notification", "link": "https://studentup.in/ssc/",
         "date": "2026-10-02", "category_slugs": ["central-jobs"],
         "last_date": "2026-10-04", "vacancies": "1000+"},
        {"id": 3, "title": "TSPSC Group 2 Notification", "link": "https://studentup.in/tspsc/",
         "date": "2026-10-01", "category_slugs": ["ts-jobs"], "last_date": "",
         "vacancies": ""},
        {"id": 4, "title": "Infosys Off Campus Drive 2026 – System Engineer",
         "link": "https://studentup.in/infosys/", "date": "2026-10-01",
         "category_slugs": ["software-jobs"], "last_date": "2026-10-04",
         "vacancies": "40"},
    ]
    text = od.render_whatsapp("https://studentup.in", rows, today=date(2026, 10, 2))
    # Telugu list header + no duplicate today block (user: "idi kuda vaddu")
    assert "📋 *StudentUp — నేటి ఉద్యోగాల లిస్ట్*" in text
    assert "IVVALTI" not in text and "Daily Updates List" not in text
    assert "🗓 శుక్రవారం, 02 అక్టోబర్ 2026" in text
    # per-item date line ledu; Telugu wording: "ఉద్యోగాలు <count>"
    assert "📅" not in text and "Last date:" not in text
    assert "1) 🆕 *SSC CGL 2026 ఉద్యోగాలు* — 1,000+ పోస్టులు · ⏰ 2 రోజులు మాత్రమే" in text
    assert "— 310 పోస్టులు · 💰 ₹18,000 – ₹22,000" in text
    assert "Complete Details" not in text, "SEO suffix clean avvaledu"
    # prathi item kinda mee site link (anni open cheyyagalaru)
    assert text.count("🔗 https://studentup.in/") == 4, text
    # Telugu section headers + counts
    assert "🇮🇳 *కేంద్ర ప్రభుత్వ ఉద్యోగాలు* (2 ఉద్యోగాలు)" in text
    assert "🏛️ *తెలంగాణ ప్రభుత్వ ఉద్యోగాలు* (1 ఉద్యోగం)" in text
    # software section English (user: "software vasthe english vundu")
    assert "💻 *SOFTWARE JOBS* (1 job)" in text
    assert "— 40 openings · ⏰ 2 days left" in text, "software English ledu"
    assert "*Infosys Off Campus Drive 2026 Jobs*" in text, "software hook headline ledu"
    # Telugu footer + disclaimer
    assert "✅ *4 ఉద్యోగాలు*" in text and "👥 *1,350+ పోస్టులు*" in text
    assert "అధికారిక నోటిఫికేషన్‌లో వివరాలు వెరిఫై చేసుకోండి" in text
    # helpers (Telugu / English templates)
    assert od.vacancies_note("") == "" and od.vacancies_note("approx") == ""
    assert od.vacancies_note("8,326") == "ఉద్యోగాలు 8,326"
    assert od.vacancies_count("8326") == "8,326" and od.vacancies_count("2000+") == "2,000+"
    assert od.vacancies_note("40", word="openings", word_first=False) == "40 openings"
    assert od.vacancies_count("1000+") == "1,000+"
    assert od.wa_deadline_note(2, telugu=True) == "⏰ 2 రోజులు మాత్రమే"
    assert od.wa_deadline_note(0, telugu=True) == "⏰ ఈరోజే చివరి రోజు!"
    assert od.wa_deadline_note(None) == "" and od.wa_deadline_note(9) == ""
    assert od.salary_note("") == "" and od.salary_note("₹18,000 – ₹56,900") == "💰 ₹18,000 – ₹56,900"
    # Telegram digest (existing) format marchaledu — backward compatible
    tg = od.render_digest("https://studentup.in", rows, today=date(2026, 10, 2))
    assert "Last date:" not in tg and "<b>" in tg
    print("  5. WhatsApp Telugu list (no duplicate · udyogalu · software EN) ✔")


def test_docs_wiring():
    for name in ("README.md", "MANUAL_ADVANCED_CHECKLIST.md", "MILESWEB_GO_LIVE.md"):
        text = (ROOT / name).read_text(encoding="utf-8")
        assert "--links-file" in text, f"{name} lo --links-file ledu"
    env = (ROOT / ".env.example").read_text(encoding="utf-8")
    assert "LINK_INTAKE_MAX" in env and "LINK_INTAKE_REPORT" in env
    print("  6. docs/.env wiring ✔")


def main() -> None:
    print("=" * 70)
    print("  v187 — MULTI-LINK INTAKE + RICH WHATSAPP LIST")
    print("=" * 70)
    test_parse_links()
    test_load_links_and_missing_file()
    test_intake_separate_drafts()
    test_report_and_cli()
    test_whatsapp_rich_items()
    test_docs_wiring()
    print("-" * 70)
    print("ALL v187 MULTI-LINK TESTS PASSED ✔")


if __name__ == "__main__":
    main()
