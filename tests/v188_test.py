# -*- coding: utf-8 -*-
"""v188 — HOOK ENGINE tests (offline).

User ask: "blog lo ... main gaa enti ani ssc chsl uryogalu IBPS clerk jobs ilaga main
enti ani cheppi kinda links ravali mana blog links manam post chesinavi mattrame".

Cover:
  1. subject(): boilerplate teesi main ento mattrame ('SSC CHSL 2026 Notification – Apply
     Online' → 'SSC CHSL 2026') · subtitle cut · idempotent (ఉద్యోగాలు/Jobs repeat vaddhu)
  2. headline(): Telugu 'SSC CHSL 2026 ఉద్యోగాలు' · software English '… Jobs' ·
     walk-in de-dup ('Walk-in Interview' title lo unte suffix vaddhu)
  3. article_lead/hook_html: English hook (site English-only gate) · nijamaina
     vacancies/last date unte mattrame · render-safe
  4. ensure_lead: idempotent · intro lo subject already unte skip · empty title safe
  5. Daily list items: hook main line + 'N పోస్టులు' chips + mana blog link mattrame
     (external source URL eppudu list lo ledu)
  6. Theme + docs wiring (su-hook CSS, version 1.9.40, README/MANUAL)
"""
from __future__ import annotations

import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from autoblog import hooks as hk, opportunity_digest as od  # noqa: E402

TODAY = date(2026, 10, 2)


def test_subject_and_headline():
    assert hk.subject("SSC CHSL 2026 Notification – Apply Online") == "SSC CHSL 2026"
    assert hk.subject("IBPS Clerk Recruitment 2026 – Complete Details") == "IBPS Clerk 2026"
    assert hk.subject("ECIL ITI Trade Apprentice Recruitment 2026") == "ECIL ITI Trade Apprentice 2026"
    # subtitle cut (hook lo main ento mattrame)
    assert hk.subject("Infosys Off Campus Drive 2026 – System Engineer") == "Infosys Off Campus Drive 2026"
    assert hk.subject("") == ""
    assert hk.headline("SSC CHSL 2026 Notification – Apply Online") == "SSC CHSL 2026 ఉద్యోగాలు"
    assert hk.headline("IBPS Clerk 2026 ఉద్యోగాలు") == "IBPS Clerk 2026 ఉద్యోగాలు"   # idempotent
    assert hk.headline("Infosys Off Campus Drive 2026 – System Engineer",
                       telugu=False) == "Infosys Off Campus Drive 2026 Jobs"
    assert hk.headline("TCS NQT 2026 Registration Open", telugu=False).endswith("Jobs")
    # walk-in: title lo already walk-in → suffix vaddhu (rendu language lo)
    assert hk.headline("RRB NTPC Walk-in Interview 2026 – Hyderabad") == "RRB NTPC Walk-in Interview 2026"
    assert hk.headline("Anganwadi Supervisor", telugu=False, kind="walkin").endswith("Walk-in")
    assert hk.headline("", "") == ""
    print("  1. subject/headline (hook main line · idempotent · walk-in) ✔")


def test_article_lead():
    lead = hk.article_lead("SSC CHSL 2026 Notification", vacancies="2000+")
    assert lead.startswith("<strong>SSC CHSL 2026</strong> recruitment")
    assert "2,000+ vacancies" in lead and "in one place" in lead
    # numbers/dates teliyakapote aa clauses asalu raavu (fabricate ledu)
    bare = hk.article_lead("IBPS Clerk Recruitment 2026")
    assert "vacancies" not in bare and "last date" not in bare, bare
    with_date = hk.article_lead("IBPS Clerk 2026", last_date="28 October 2026")
    assert "last date 28 October 2026" in with_date
    # HTML escape (title lo angle brackets unna safe)
    assert "<script>" not in hk.article_lead("<script>alert(1)</script> SSC 2026")
    assert hk.article_lead("") == ""
    block = hk.hook_html("SSC CHSL 2026 Notification – Apply Online", vacancies="2000+")
    assert block.startswith('<p class="su-hook">') and block.endswith("</p>")
    print("  2. article_lead/hook_html (English · real facts mattrame · escape) ✔")


def test_ensure_lead():
    body = "<p>Some intro text.</p>"
    once = hk.ensure_lead(body, title="SSC CHSL 2026 Notification", vacancies="2000+")
    assert once.startswith('<p class="su-hook">') and body in once
    assert hk.ensure_lead(once, title="SSC CHSL 2026 Notification", vacancies="2000+") == once, \
        "double hook (idempotent kaadu)"
    # intro lo already subject unte hook vaddhu (natural intro chalu)
    natural = "<p>SSC CHSL 2026 is out now. Details below.</p>"
    assert hk.ensure_lead(natural, title="SSC CHSL 2026 Notification") == natural
    # title ledu → body as-is (crash ledu)
    assert hk.ensure_lead(body, title="") == body
    assert hk.ensure_lead("", title="SSC 2026 Notification") == ""
    print("  3. ensure_lead (idempotent · natural intro skip · empty-safe) ✔")


def test_daily_list_hooks():
    rows = [
        {"id": 1, "title": "SSC CHSL 2026 Notification – Apply Online",
         "link": "https://studentup.in/ssc-chsl-2026/", "date": "2026-10-02",
         "category_slugs": ["central-jobs"], "last_date": "2026-10-04",
         "vacancies": "2000+", "salary": "₹25,500 – ₹81,100"},
        {"id": 2, "title": "IBPS Clerk Recruitment 2026 – Complete Details",
         "link": "https://studentup.in/ibps-clerk-2026/", "date": "2026-10-02",
         "category_slugs": ["central-jobs"], "last_date": "2026-10-28",
         "vacancies": "", "salary": ""},
        {"id": 3, "title": "Infosys Off Campus Drive 2026 – System Engineer",
         "link": "https://studentup.in/infosys-2026/", "date": "2026-10-01",
         "category_slugs": ["software-jobs"], "last_date": "", "vacancies": "40",
         "salary": "₹3.6 – ₹6.5 LPA"},
    ]
    text = od.render_whatsapp("https://studentup.in", rows, today=TODAY)
    # main enti mundu → hook headline; chips kinda
    assert "1) 🆕 *SSC CHSL 2026 ఉద్యోగాలు* — 2,000+ పోస్టులు · 💰 ₹25,500 – ₹81,100 · ⏰ 2 రోజులు మాత్రమే" in text, text
    assert "*IBPS Clerk 2026 ఉద్యోగాలు*" in text
    assert "*Infosys Off Campus Drive 2026 Jobs* — 40 openings" in text
    # 'ఉద్యోగాలు' rendu sari ledu (headline + chip repeat fix)
    ssc_line = [l for l in text.splitlines() if "SSC CHSL" in l][0]
    assert ssc_line.count("ఉద్యోగాలు") == 1, ssc_line
    # mana blog links mattrame — prathi item ki okkati
    assert text.count("🔗 https://studentup.in/") == 3
    assert "ecil.co.in" not in text and "ssc.gov.in" not in text, \
        "external source link list lo ki vachindi (mana blog links mattrame)"
    assert "📅" not in text and "Last date:" not in text
    print("  4. daily list hooks (main enti · chips · mana links mattrame) ✔")


def test_theme_and_docs_wiring():
    css = (ROOT / "wordpress-theme/studentup/style.css").read_text(encoding="utf-8")
    assert ".su-hook{" in css and ".su-hook strong" in css, "hook CSS ledu"
    assert "body.dark .su-hook" in css, "dark mode hook style ledu"
    assert "Version: 1.9.40" in css
    func = (ROOT / "wordpress-theme/studentup/functions.php").read_text(encoding="utf-8")
    assert "STUDENTUP_VERSION', '1.9.40'" in func
    min_css = (ROOT / "wordpress-theme/studentup/style.min.css").read_text(encoding="utf-8")
    assert ".su-hook" in min_css, "min.css lo hook style ledu (build skip ayyindi)"
    for name in ("README.md", "MANUAL_ADVANCED_CHECKLIST.md"):
        doc = (ROOT / name).read_text(encoding="utf-8")
        assert "su-hook" in doc or "hook" in doc.lower(), f"{name} lo hook docs ledu"
    print("  5. theme (.su-hook CSS · 1.9.40 · min) + docs ✔")


def main() -> None:
    print("=" * 70)
    print("  v188 — HOOK ENGINE (main enti mundu · links kinda)")
    print("=" * 70)
    test_subject_and_headline()
    test_article_lead()
    test_ensure_lead()
    test_daily_list_hooks()
    test_theme_and_docs_wiring()
    print("-" * 70)
    print("ALL v188 HOOK TESTS PASSED ✔")


if __name__ == "__main__":
    main()
