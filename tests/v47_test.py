# -*- coding: utf-8 -*-
"""v47 self-test — static daily poll/question & bot ads-inventory contract.

v74 rewrite: exam portal teesesam → poll ippudu **server lekunda** (7-question
bank, date rotation, localStorage vote, correct-answer reveal). Portal poll API
+ portal admin-ads tests poyayi; bot-side inventory contract matram migilindi
(ad_manager ni bot direct ga vadutundi).

Run:  python tests/v47_test.py        (also picked up by: python run.py --test-all)
Offline-only: no network, no server process.
"""

from __future__ import annotations

import json
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from autoblog import ad_manager  # noqa: E402

INDEX = ROOT / "preview" / "index.html"
CONTACT = ROOT / "preview" / "pages" / "contact.html"
PRIVACY = ROOT / "preview" / "pages" / "privacy.html"
TE = re.compile(r"[\u0c00-\u0c7f]")


def _html() -> str:
    return INDEX.read_text(encoding="utf-8")


def test_poll_bank_shape_and_rotation():
    html = _html()
    m = re.search(r"var POLL_BANK=\[(.*?)\];", html, re.S)
    assert m, "POLL_BANK ledu"
    bank = m.group(1)
    items = re.findall(r"\{t:\"(.*?)\",o:\[(.*?)\],a:(\d+),w:\"(.*?)\"\}", bank)
    assert len(items) == 7, f"poll bank 7 undali, unnayi: {len(items)}"
    for t, opts, a, w in items:
        assert len(t) > 10 and len(w) > 10, "question/explanation chinnadi"
        assert not TE.search(t + opts + w), "poll bank English-only (v73 scope)"
        options = re.findall(r"\"(.*?)\"", opts)
        assert len(options) == 4, f"4 options undali: {t[:30]}"
        assert 0 <= int(a) < 4, f"answer index tappu: {t[:30]}"
    assert "dayNum%POLL_BANK.length" in html, "date rotation ledu"
    assert "330+new Date().getTimezoneOffset()" in html, "IST day logic ledu"
    print("  poll: 7-question bank · 4 options each · valid answers · IST rotation ✔")


def test_poll_has_no_server():
    html = _html()
    for needle in ('/poll/today', '/poll/vote', '"/poll', "'/poll", "base()+",
                   "localhost:8080", "8080-", "exam portal is offline",
                   "exam portal is online"):
        assert needle not in html, f"server vestige inka undi: {needle}"
    assert "studentup-poll-v1-" in html, "localStorage vote key ledu"
    assert '" correct"' in html and '" wrong"' in html, "correct/wrong reveal ledu"
    assert "poll-result-note" in html, "explanation note ledu"
    assert "no fake numbers" in html, "honesty comment ledu"
    print("  poll: fetch/base/portal URLs levu · localStorage vote · instant reveal ✔")


def test_poll_markup_and_css_intact():
    html = _html()
    for needle in ('id="poll"', 'id="pollbox"', 'id="pollday"', "Today's question"):
        assert needle in html, f"poll markup poyindi: {needle}"
    css = " ".join(re.findall(r"<style>(.*?)</style>", html, re.S))
    assert ".poll{" in css and "body.dark .poll-opt" in css, "poll CSS poyindi"
    assert ".poll-opt" in css and ".poll-result-note" in css
    print("  poll: section markup + responsive/dark CSS intact ✔")


def test_privacy_tells_browser_only_truth():
    priv = PRIVACY.read_text(encoding="utf-8")
    assert "exam portal" not in priv.lower(), "privacy lo portal vestige"
    assert "IP address" not in priv, "IP voting claim inka undi"
    assert "Your browser only" in priv and "poll" in priv
    print("  privacy: portal/IP claims poyayi · browser-only truth ✔")


def test_contact_form_whatsapp_compose():
    html = CONTACT.read_text(encoding="utf-8")
    for needle in ('id="leadform"', 'id="ld-phone"', 'id="ld-interest"',
                   'class="lead-hp"', "wa.me", "WA_NUMBER", "w.opener=null",
                   "nothing is stored", "privacy.html"):
        assert needle in html, f"contact form lo ledu: {needle}"
    assert 'api()+"/lead"' not in html and "/lead" not in html, "/lead vestige undi"
    assert "/^[6-9]\\d{9}$/" in html, "client-side phone check undali"
    assert "spam trap" in html, "honeypot logic ledu"
    index = _html()
    assert 'id="leadform"' not in index, "homepage lo form undakoodadu (v71)"
    print("  contact: WhatsApp-compose form · honeypot · phone check · no /lead ✔")


def test_inventory_bot_contract():
    d = Path(tempfile.mkdtemp(prefix="v47-ads-"))
    p = d / "inventory.json"
    p.write_text(json.dumps({
        "version": 3,
        "policy": {"label": "SPONSORED", "max_personal_ads_per_post": 2},
        "ads": [
            {"id": "college-banner-demo", "type": "college_banner",
             "title": "Demo College", "link": "https://example.com/c",
             "layout": "banner", "active": True},
            {"id": "coaching-hyd-1", "type": "coaching", "layout": "banner",
             "title": "Hyderabad coaching — TSPSC batch", "desc": "Test series.",
             "link": "https://example.com/coaching", "cta": "Join",
             "placements": ["top"], "active": True},
            {"id": "old-shop", "type": "shop", "layout": "card",
             "title": "Old shop", "link": "https://example.com/s", "active": False},
        ]}, ensure_ascii=False), encoding="utf-8")
    inv = ad_manager.load_inventory(path=p)
    assert inv.get("policy", {}).get("label") == "SPONSORED"
    picked = [a["id"] for a in ad_manager.active_ads(inv)]
    assert "coaching-hyd-1" in picked and "college-banner-demo" in picked, picked
    assert "old-shop" not in picked, "inactive ad active ayyindi!"
    print("  inventory: bot load + policy + active-filter (inactive out) ✔")


def test_inventory_render_safety():
    d = Path(tempfile.mkdtemp(prefix="v47-render-"))
    p = d / "inventory.json"
    p.write_text(json.dumps({
        "version": 3, "policy": {"label": "SPONSORED"},
        "ads": [{"id": "xss-try", "type": "shop", "layout": "card",
                 "title": "<img src=x>", "link": "https://example.com/x",
                 "active": True}]}, ensure_ascii=False), encoding="utf-8")
    inv = ad_manager.load_inventory(path=p)
    out = ad_manager.render_ad(inv["ads"][0], "mid", ad_manager.policy_of(inv))
    assert "SPONSORED" in out, "label ledu"
    assert "<img src=x>" not in out, "XSS escape avvaledu!"
    assert "sponsored" in out and "nofollow" in out, "rel=sponsored nofollow ledu"
    print("  inventory: SPONSORED label + rel + XSS escape ✔")


def main() -> None:
    test_poll_bank_shape_and_rotation()
    test_poll_has_no_server()
    test_poll_markup_and_css_intact()
    test_privacy_tells_browser_only_truth()
    test_contact_form_whatsapp_compose()
    test_inventory_bot_contract()
    test_inventory_render_safety()
    print("ALL v47 STATIC-POLL + ADS-CONTRACT TESTS PASSED ✔")


if __name__ == "__main__":
    main()
