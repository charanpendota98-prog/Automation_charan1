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
    rows = [
        {"id": 1, "title": "ECIL ITI Trade Apprentice Recruitment 2026",
         "link": "https://studentup.in/ecil/", "date": "2026-10-02",
         "category_slugs": ["central-jobs"], "last_date": "2026-10-20",
         "vacancies": "310"},
        {"id": 2, "title": "SSC CGL 2026 Notification", "link": "https://studentup.in/ssc/",
         "date": "2026-10-02", "category_slugs": ["central-jobs"],
         "last_date": "2026-10-04", "vacancies": "1000+"},
        {"id": 3, "title": "TSPSC Group 2 Notification", "link": "https://studentup.in/tspsc/",
         "date": "2026-10-01", "category_slugs": ["ts-jobs"], "last_date": "",
         "vacancies": ""},
    ]
    text = od.render_whatsapp("https://studentup.in", rows, today=date(2026, 10, 2))
    assert "· 310 posts" in text, text[:400]
    assert "· 1000+ posts" in text
    assert "📅 Last date: 20 Oct 2026" in text
    assert "📅 Last date: 04 Oct 2026 · ⏰ 2 days left" in text
    assert "🇮🇳 *CENTRAL GOVERNMENT JOBS* (2 jobs · 1,310 posts)" in text
    assert "🏛️ *TELANGANA GOVERNMENT JOBS* (1)" in text  # posts meta ledu → puratana format
    # deadline teliyani post ki date line raakudadu (guess ledu)
    tspsc_block = text.split("TELANGANA GOVERNMENT JOBS")[1].split("CENTRAL")[0]
    assert "Last date" not in tspsc_block
    assert od.vacancies_note("") == "" and od.vacancies_note("approx") == ""
    assert od.vacancies_note("8,326") == "8,326 posts"
    # Telegram digest (existing) lo date line raakudadu — backward compatible
    tg = od.render_digest("https://studentup.in", rows, today=date(2026, 10, 2))
    assert "Last date:" not in tg
    print("  5. WhatsApp rich items (posts · last date · section totals) ✔")


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
