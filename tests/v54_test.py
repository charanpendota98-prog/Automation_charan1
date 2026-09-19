# -*- coding: utf-8 -*-
"""v54 tests — "inka inka best ga ravali": highest-revenue engine.

v74 rewrite: exam portal teesesam → lead store/API/HTTP/WSGI/admin-panel tests
poyayi. Lead capture ippudu contact page WhatsApp-compose form (server ledu).
Migilinavi: premium products + estimator advanced tier + sales kit.

Offline only. Run: python tests/v54_test.py   (also via python run.py --test-all)
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tools import revenue_estimate as rev              # noqa: E402

ADV = ROOT / "preview" / "pages" / "advertise.html"
INDEX = ROOT / "preview" / "index.html"
KIT = ROOT / "SALES_KIT_ADVERTISERS.md"


def test_premium_products_are_internal_only():
    """v71: premium services (advertorial/leads/broadcast) ippudu internal card lo mattrame."""
    from autoblog import rate_card

    services = " ".join(str(p["service"]) for p in rate_card.PREMIUM).lower()
    assert "advertorial" in services and "lead" in services and "broadcast" in services
    card = rate_card.as_markdown()
    for needle in ("8,000", "150", "1,500"):
        assert needle in card, f"internal card lo ledu: {needle}"
    html = io.open(ADV, encoding="utf-8").read()
    assert "₹" not in html, "partner page lo prices undakoodadu (v71)"
    assert "never guarantee" in html, "honest no-guarantee note undali"


def test_estimator_advanced_tier():
    t = rev.tiers(10_000)
    assert t["baseline"] == (400, 2500), t["baseline"]
    assert t["standard"] == (rev.totals(10_000)["low"], rev.totals(10_000)["high"]), t["standard"]
    assert t["advanced"][0] > t["standard"][0] and t["advanced"][1] > t["standard"][1]
    lines = t["lines"]
    assert lines["leads_range"] == (30, 80), lines["leads_range"]
    assert lines["leads"] == (4500, 24000), lines["leads"]
    assert lines["advertorial"] == (8000, 30000), lines["advertorial"]
    assert lines["affiliate"] == 150
    text = rev.render(10_000)
    assert "ADVANCED" in text and "SALES_KIT_ADVERTISERS.md" in text, "advanced tier + sales kit link"
    assert "కొనుగోలుదారు ఉంటే మాత్రమే" in text, "leads conditional ani cheppali"
    assert len(rev.tier_rows()) == 4


def test_lead_form_lives_on_contact_page():
    """v74: WhatsApp-compose form (server ledu) — homepage lo join block matrame."""
    contact = io.open(ROOT / "preview" / "pages" / "contact.html", encoding="utf-8").read()
    for needle in ('id="leadform"', 'id="ld-phone"', 'id="ld-interest"', 'class="lead-hp"',
                   "WA_NUMBER", "wa.me", "w.opener=null", "nothing is stored"):
        assert needle in contact, f"contact page lo ledu: {needle}"
    assert '"/lead"' not in contact and "'/lead'" not in contact, "/lead vestige undi"
    assert "/^[6-9]\\d{9}$/" in contact, "client-side phone check undali"
    assert "privacy.html" in contact, "privacy link undali"
    index = io.open(INDEX, encoding="utf-8").read()
    assert 'id="leadform"' not in index, "homepage lo form undakoodadu (v71)"
    assert 'id="join"' in index and "wa.me" in index and "t.me" in index, "join block undali"


def test_sales_kit_exists():
    text = io.open(KIT, encoding="utf-8").read()
    for needle in ("WhatsApp మెసేజ్", "Subject:", "objection", "90-day plan",
                   "గ్యారంటీ", "studentup.in/pages/advertise.html"):
        assert needle.lower() in text.lower(), f"sales kit lo ledu: {needle}"



def main():
    print("=" * 64)
    print("  v54 — HIGHEST-REVENUE ENGINE (premium + estimator + sales kit)")
    print("=" * 64)
    tests = [
        ("premium services internal card lo (public page lo prices ledu)", test_premium_products_are_internal_only),
        ("estimator: 3 tiers — advanced ₹16,050 ఉదాహరణ", test_estimator_advanced_tier),
        ("lead form contact page lo (WhatsApp-compose, no server)", test_lead_form_lives_on_contact_page),
        ("sales kit: templates + 90-day plan + honesty", test_sales_kit_exists),
    ]
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
    print("-" * 64)
    if failed:
        print(f"  {failed} TEST(S) FAILED ✘")
        return 1
    print("ALL v54 HIGHEST-REVENUE TESTS PASSED ✔")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
