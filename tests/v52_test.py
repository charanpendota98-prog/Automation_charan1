# -*- coding: utf-8 -*-
"""v52 tests — house ads (mana sonta ads) + advertise page / rate card.

Answers: "mana valu kuda ads pettelaga undali" + "private ads pettelaga undali"
+ "highest revenue" — with executable checks, no promises.

Offline only. Run: python tests/v52_test.py   (also via python run.py --test-all)
"""
from __future__ import annotations

import io
import json
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from autoblog import ad_manager, config            # noqa: E402

PREVIEW = ROOT / "preview"
ADV = PREVIEW / "pages" / "advertise.html"


def _setup(tmp: Path, sponsor_ads=None, house_ads=None):
    """Point the ad manager at temp inventory/house files; reset rotation."""
    inv = tmp / "inventory.json"
    inv.write_text(json.dumps(
        {"version": 1, "policy": {"label": "SPONSORED", "max_personal_ads_per_post": 2},
         "ads": sponsor_ads or []}, ensure_ascii=False), encoding="utf-8")
    house = tmp / "house.json"
    house.write_text(json.dumps(
        {"version": 1, "ads": house_ads if house_ads is not None else [
            {"id": "house-services", "title": "దరఖాస్తు సహాయం — StudentUp సేవలు",
             "link": "https://studentup.in/#services", "active": True}]},
        ensure_ascii=False), encoding="utf-8")
    config.ADS_INVENTORY_PATH = str(inv)
    config.HOUSE_ADS_PATH = str(house)
    config.HOUSE_AD_ENABLED = True
    for f in ("rotation.json",):
        try:
            (tmp / f).unlink()
        except FileNotFoundError:
            pass
    return inv, house


def _html():
    return ("<html><body><article><h1>టెస్ట్</h1><p>%s</p></article></body></html>"
            % ("word " * 300))


def _ad(i="paid-1", **kw):
    base = {"id": i, "name": i, "title": "కళాశాల ప్రకటన " + i, "type": "college_banner",
            "layout": "card", "link": "https://example.com/" + i, "categories": "",
            "active": True, "start": "2020-01-01", "end": "2099-12-31"}
    base.update(kw)
    return base


# ------------------------------------------------------------- house ads

def test_house_json_shipped_with_studentup_promos():
    f = ROOT / "ads" / "house.json"
    assert f.exists(), "ads/house.json missing"
    data = json.loads(f.read_text(encoding="utf-8"))
    ids = [a["id"] for a in data["ads"]]
    assert len(ids) >= 3, ids
    assert any("services" in i for i in ids) and any("quiz" in i for i in ids)
    for a in data["ads"]:
        assert a.get("link", "").startswith("http"), a
        assert a.get("house") is True
    print("  house ads: %d StudentUp promos shipped (services/quiz/jobs) ✔" % len(ids))


def test_house_ad_fills_empty_slot():
    tmp = Path(tempfile.mkdtemp(prefix="v52-"))
    _setup(tmp)
    out, rep = ad_manager.inject(_html(), {"title": "TSPSC", "category": "Jobs"})
    assert rep and rep[0]["kind"] == "house", rep
    assert out != _html(), "slot left empty despite house ads"
    print("  house ads: sponsor lekapoyina slot khali ga ledu (auto-fill) ✔")


def test_house_ad_is_not_labelled_sponsored():
    tmp = Path(tempfile.mkdtemp(prefix="v52-"))
    _setup(tmp)
    out, rep = ad_manager.inject(_html(), {"title": "x", "category": "Jobs"})
    assert "SPONSORED" not in out.upper(), "house ad must never claim SPONSORED"
    assert 'rel="sponsored' not in out, "house links must not be rel=sponsored"
    assert "utm_medium=house" in out, "house ad analytics must be separated"
    assert "aria-label=\"StudentUp" in out or "StudentUp ·" in out
    assert "not a paid" in out.lower() or "our service" in out.lower(), "house disclosure missing"
    print("  house ads: honest label (never SPONSORED) + utm_medium=house ✔")


def test_paid_ad_always_beats_house_ad():
    tmp = Path(tempfile.mkdtemp(prefix="v52-"))
    _setup(tmp, sponsor_ads=[_ad()])
    out, rep = ad_manager.inject(_html(), {"title": "x", "category": "Jobs"})
    assert rep[0]["kind"] == "sponsor", rep
    assert "కళాశాల ప్రకటన" in out and "దరఖాస్తు సహాయం" not in out
    assert "SPONSORED" in out.upper() and 'rel="sponsored' in out
    print("  house ads: paying sponsor always wins (house only fills gaps) ✔")


def test_house_rotation_and_disable_switch():
    tmp = Path(tempfile.mkdtemp(prefix="v52-"))
    _setup(tmp, house_ads=[_ad("h-a", house=True), _ad("h-b", house=True)])
    first = ad_manager.select_house_ads(limit=1, record=True)
    second = ad_manager.select_house_ads(limit=1, record=True)
    assert first and second and first[0]["id"] != second[0]["id"], (first, second)
    config.HOUSE_AD_ENABLED = False
    try:
        assert ad_manager.load_house_ads() == []
        out, rep = ad_manager.inject(_html(), {"title": "x", "category": "Jobs"})
        assert rep == [] and out == _html(), "HOUSE_AD_ENABLED=0 must disable them"
    finally:
        config.HOUSE_AD_ENABLED = True
    print("  house ads: rotate fairly + HOUSE_AD_ENABLED=0 switches them off ✔")


def test_broken_house_file_never_blocks_posting():
    tmp = Path(tempfile.mkdtemp(prefix="v52-"))
    _setup(tmp)
    (tmp / "house.json").write_text("{not json", encoding="utf-8")
    out, rep = ad_manager.inject(_html(), {"title": "x", "category": "Jobs"})
    assert out == _html() and rep == [], "broken house file must not break the post"
    print("  house ads: broken file → post safe ga continue (no crash) ✔")


# ------------------------------------------------- advertise page / revenue

def test_partner_page_exists_and_is_indexable():
    """v71: advertise page = 'Partner with us' (English-first, indexable, canonical)."""
    assert ADV.exists(), "pages/advertise.html missing"
    html = ADV.read_text(encoding="utf-8")
    # v73: English UI
    assert '<html lang="en">' in html and 'property="og:locale" content="en_IN"' in html
    assert "canonical" in html and "studentup.in/pages/advertise.html" in html
    assert "Partner with us" in html
    assert "SPONSORED" in html and "house ads" in html.lower()
    print("  partner page: exists · canonical · SPONSORED/house-ads explained ✔")


def test_no_public_rate_card_on_the_website():
    """v71 (mee directive): prices/slot table website lo undakoodadu — personal ga deal."""
    html = ADV.read_text(encoding="utf-8")
    assert "₹" not in html, "partner page lo ₹ price undi — prices public ga vaddhu"
    assert "<table>" not in html, "partner page lo table (rate card/booking) undi"
    assert "Booking" not in html and "బుకింగ్" not in html, "public booking flow vaddhu"
    idx = (PREVIEW / "index.html").read_text(encoding="utf-8")
    assert "₹" not in idx, "homepage lo rate card prices unnayi"
    print("  no public prices/booking (homepage + partner page clean) ✔")


def test_rates_shared_personally_with_contact_routes():
    html = ADV.read_text(encoding="utf-8")
    assert "personally" in html
    assert "mailto:" in html and "studentupinformative@gmail.com" in html
    assert re.search(r"wa\.me/\d{6,}", html), "WhatsApp route ledu"
    print("  partner page: rates shared personally + WhatsApp/email routes ✔")


def test_internal_rate_card_is_the_source_of_truth():
    """Prices ippudu internal card lo (autoblog/rate_card.py) — bot/owner ki mattrame."""
    from autoblog import rate_card

    rows = rate_card.as_rows()
    assert len(rows) == 6, f"6 rows (5 slots + package) undali, vachhindi {len(rows)}"
    assert sorted(int(r["price"]) for r in rows) == [1000, 2000, 3000, 3500, 4000, 8000]
    assert len([r for r in rows if r["bundle"]]) == 1
    assert len(rate_card.PREMIUM) >= 3, "premium services (advertorial/leads/broadcast) undali"
    assert "₹" in rate_card.as_markdown(), "Telegram/console card lo prices undali"
    print("  internal rate card: 5 slots + package ₹1,000–₹8,000 + 3 premium services ✔")


def test_ad_policy_is_strict_and_adsense_safe():
    html = ADV.read_text(encoding="utf-8")
    for rule in ["SPONSORED", 'rel="sponsored nofollow"', "Clickbait", "Fake clicks",
                 "pop-ups", "gambling"]:
        assert rule in html, "policy rule missing: " + rule
    assert "never guarantee" in html, "honest no-guarantee note missing"
    print("  partner page: strict policy (no clickbait/fake clicks/popups) + honest note ✔")


def test_house_ads_explained_to_advertisers():
    html = ADV.read_text(encoding="utf-8")
    assert "house ads" in html.lower()
    assert "never looks empty" in html, "must explain that slots never look empty"
    print("  partner page: house ads explained (slot never looks empty) ✔")


def test_site_links_to_the_advertise_page():
    index = (PREVIEW / "index.html").read_text(encoding="utf-8")
    assert "pages/advertise.html" in index, "index does not link the advertise page"
    assert index.count("pages/advertise.html") >= 2, "link in dropdown + mobile panel"
    sm = (PREVIEW / "sitemap.xml").read_text(encoding="utf-8")
    assert "advertise.html" in sm
    robots = (PREVIEW / "robots.txt").read_text(encoding="utf-8")
    assert "advertise" not in robots.lower() or "Allow" in robots
    print("  site: dropdown + mobile panel link it · sitemap included ✔")


def test_index_has_no_rate_card_and_shows_service_card():
    """v71: sidebar lo rate card ledu — Students Internet Center card + partner link undi."""
    index = (PREVIEW / "index.html").read_text(encoding="utf-8")
    assert "₹" not in index, "homepage lo prices unnayi (public rate card vaddhu)"
    assert "Students Internet Center" in index, "services card ledu"
    assert 'href="pages/advertise.html"' in index, "partner page link ledu"
    print("  site: no public rate card · Students Internet Center card + partner link ✔")


def test_advertise_page_passes_public_audit():
    html = ADV.read_text(encoding="utf-8")
    title = re.search(r"<title>(.*?)</title>", html, re.S).group(1)
    desc = re.search(r'name="description" content="([^"]*)"', html).group(1)
    assert 20 <= len(title) <= 70, len(title)
    assert 100 <= len(desc) <= 175, len(desc)
    assert "application/ld+json" in html and 'og:image' in html
    assert html.count("<h1>") == 1
    print("  advertise page: audit-ready (title %d · desc %d · JSON-LD · OG) ✔"
          % (len(title), len(desc)))


def main() -> None:
    test_house_json_shipped_with_studentup_promos()
    test_house_ad_fills_empty_slot()
    test_house_ad_is_not_labelled_sponsored()
    test_paid_ad_always_beats_house_ad()
    test_house_rotation_and_disable_switch()
    test_broken_house_file_never_blocks_posting()
    test_partner_page_exists_and_is_indexable()
    test_no_public_rate_card_on_the_website()
    test_internal_rate_card_is_the_source_of_truth()
    test_rates_shared_personally_with_contact_routes()
    test_ad_policy_is_strict_and_adsense_safe()
    test_house_ads_explained_to_advertisers()
    test_site_links_to_the_advertise_page()
    test_index_has_no_rate_card_and_shows_service_card()
    test_advertise_page_passes_public_audit()
    print("ALL v52 HOUSE-AD + ADVERTISE-PAGE TESTS PASSED ✔")


if __name__ == "__main__":
    main()
