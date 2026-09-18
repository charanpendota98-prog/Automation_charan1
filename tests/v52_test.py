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
    print("  house ads: %d StudentUp promos shipped (services/quiz/exam) ✔" % len(ids))


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
    assert "పెయిడ్ ప్రకటన కాదు" in out, "house disclosure missing"
    print("  house ads: honest label (SPONSORED kaadu) + utm_medium=house ✔")


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

def test_advertise_page_exists_and_is_pure_telugu():
    assert ADV.exists(), "pages/advertise.html missing"
    html = ADV.read_text(encoding="utf-8")
    assert '<html lang="te">' in html
    telugu = len(re.findall(r"[\u0C00-\u0C7F]", html))
    assert telugu > 1500, telugu
    assert "canonical" in html and "studentup.in/pages/advertise.html" in html
    print("  advertise page: pure Telugu (%d chars) + canonical ✔" % telugu)


def test_rate_card_has_all_slots_and_prices():
    html = ADV.read_text(encoding="utf-8")
    for slot in ["టాప్ లీడర్‌బోర్డ్", "ఇన్-ఫీడ్", "ఆర్టికల్ మధ్యలో",
                 "సైడ్‌బార్", "విధాన పేజీల", "ఫుల్ ప్యాకేజీ"]:
        assert slot in html, "rate card slot missing: " + slot
    for price in ["₹4,000", "₹3,500", "₹3,000", "₹2,000", "₹1,000", "₹8,000"]:
        assert price in html, "price missing: " + price
    print("  advertise page: 6 slots with ₹ rate card (₹1,000–₹8,000/నెల) ✔")


def test_booking_flow_and_contact_channels():
    html = ADV.read_text(encoding="utf-8")
    assert "mailto:" in html and "studentupinformative@gmail.com" in html
    assert "t.me/studentup_in" in html
    assert "బుకింగ్" in html and "3 అడుగులు" in html
    assert "ఇన్‌వాయిస్" in html and "రిఫండ్" in html
    print("  advertise page: 3-step booking + email/Telegram + invoice/refund policy ✔")


def test_ad_policy_is_strict_and_adsense_safe():
    html = ADV.read_text(encoding="utf-8")
    for rule in ["SPONSORED", 'rel="sponsored nofollow"', "క్లిక్‌బైట్",
                 "నకిలీ క్లిక్", "పాపప్", "జూదం"]:
        assert rule in html, "policy rule missing: " + rule
    assert "హామీ" in html, "honest no-guarantee note missing"
    print("  advertise page: strict policy (no clickbait/fake clicks/popups) + honest note ✔")


def test_house_ads_explained_to_advertisers():
    html = ADV.read_text(encoding="utf-8")
    assert "StudentUp సొంత" in html or "హౌస్" in html
    assert "ఖాళీగా కనిపించదు" in html, "must explain that slots never look empty"
    print("  advertise page: house ads explained (slot never looks empty) ✔")


def test_site_links_to_the_advertise_page():
    index = (PREVIEW / "index.html").read_text(encoding="utf-8")
    assert "pages/advertise.html" in index, "index does not link the advertise page"
    assert index.count("pages/advertise.html") >= 2, "link in dropdown + ads card"
    sm = (PREVIEW / "sitemap.xml").read_text(encoding="utf-8")
    assert "advertise.html" in sm
    robots = (PREVIEW / "robots.txt").read_text(encoding="utf-8")
    assert "advertise" not in robots.lower() or "Allow" in robots
    print("  site: dropdown + rate-card card link it · sitemap included ✔")


def test_index_rate_card_shows_live_prices():
    index = (PREVIEW / "index.html").read_text(encoding="utf-8")
    for price in ["₹4,000", "₹8,000"]:
        assert price in index, "index rate card missing: " + price
    assert "పూర్తి రేట్ కార్డ్" in index
    print("  site: sidebar card shows the live rate card + booking link ✔")


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
    test_advertise_page_exists_and_is_pure_telugu()
    test_rate_card_has_all_slots_and_prices()
    test_booking_flow_and_contact_channels()
    test_ad_policy_is_strict_and_adsense_safe()
    test_house_ads_explained_to_advertisers()
    test_site_links_to_the_advertise_page()
    test_index_rate_card_shows_live_prices()
    test_advertise_page_passes_public_audit()
    print("ALL v52 HOUSE-AD + ADVERTISE-PAGE TESTS PASSED ✔")


if __name__ == "__main__":
    main()
