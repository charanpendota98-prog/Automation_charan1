"""v47 self-test — daily poll (rotation + voting) & admin-controlled ads.

Run:  python tests/v47_test.py        (also picked up by: python run.py --test-all)
Offline-only: temp DB + temp inventory file, no network, no server process.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from exam_portal import engine                     # noqa: E402
from exam_portal.server import Api                 # noqa: E402
from exam_portal.store import Store                # noqa: E402

ADMIN = "test-admin-key"


def _store(with_questions: bool = True) -> Store:
    tmp = Path(tempfile.mkdtemp(prefix="v47-db-"))
    st = Store(str(tmp / "test.db"))
    st.init()
    if with_questions:
        eid = st.create_exam(code="V47AAA", admin_token="tok", title="v47 bank",
                             duration_min=15, created_by="test")["id"]
        st.add_questions(eid, [
            {"text": "తెలంగాణ రాజధాని ఏది?", "options": ["వరంగల్", "హైదరాబాద్"],
             "correct_index": 1, "explanation": "హైదరాబాద్.", "topic": "జీకే"},
            {"text": "NSP పోర్టల్ ఏది?", "options": ["scholarships.gov.in", "nsp.in"],
             "correct_index": 0, "explanation": "scholarships.gov.in.", "topic": "జీకే"},
            {"text": "TSPSC పూర్తి రూపం?", "options": ["ఎ", "బి", "సి"],
             "correct_index": 2, "explanation": "సి.", "topic": "జీకే"},
        ])
    return st


def _api(st: Store) -> Api:
    return Api(st, ADMIN)


def _tmp_inventory(ads=None) -> str:
    d = Path(tempfile.mkdtemp(prefix="v47-ads-"))
    p = d / "inventory.json"
    p.write_text(json.dumps({"version": 3,
                             "policy": {"label": "SPONSORED", "max_personal_ads_per_post": 2},
                             "ads": ads if ads is not None else [
                                 {"id": "college-banner-demo", "type": "college_banner",
                                  "title": "Demo College", "link": "https://example.com/c",
                                  "layout": "banner", "active": True}]},
                            ensure_ascii=False), encoding="utf-8")
    os.environ["ADS_INVENTORY_PATH"] = str(p)
    return str(p)


# --------------------------------------------------------------------- store

def test_store_poll_schema_and_bank():
    st = _store()
    bank = st.bank_questions()
    assert len(bank) == 3, bank
    assert bank[0]["options"][1] == "హైదరాబాద్"
    assert bank[0]["correct_index"] == 1
    assert bank[2]["correct_index"] == 2
    print("  store: poll table + question bank (3 questions, Telugu intact) ✔")


def test_store_poll_vote_dedup_and_counts():
    st = _store()
    day = "2026-09-18"
    assert st.has_poll_vote(day, 1, "10.0.0.9") is False
    st.record_poll_vote(day, 1, 0, "10.0.0.9")
    assert st.has_poll_vote(day, 1, "10.0.0.9") is True
    assert st.poll_vote_counts(day, 1) == [1]
    st.record_poll_vote(day, 1, 0, "10.0.0.10")
    st.record_poll_vote(day, 1, 1, "10.0.0.11")
    assert st.poll_vote_counts(day, 1) == [2, 1]
    assert st.poll_vote_counts("2026-09-19", 1) == []
    assert st.poll_vote_counts(day, 2) == []
    print("  store: poll votes stored per (day, qid, ip) + dedup flag ✔")


# ----------------------------------------------------------------------- api

def test_poll_today_shape_and_rotation():
    st = _store()
    api = _api(st)
    p = api.today_poll()
    assert p["ok"] and p["day"] and p["bank_size"] == 3
    assert p["qid"] and p["text"] and len(p["options"]) >= 2
    assert isinstance(p["qid"], int) and p["qid"] > 0
    assert "correct_index" not in p, "leak-proof: answer must never be sent before voting"
    # rotation: index = day.toordinal() % bank
    import datetime as _dt
    d = _dt.date.fromisoformat(p["day"])
    assert st.bank_questions()[d.toordinal() % 3]["id"] == p["qid"]
    print("  api: /poll/today shape + date-rotation index + no answer leak ✔")


def test_poll_vote_flow_and_idempotency():
    st = _store()
    api = _api(st)
    p = api.today_poll()
    qid = p["qid"]
    r = api.vote_poll({"qid": qid, "choice": 0, "_ip": "1.1.1.1"})
    assert r["ok"] and r["total"] == 1 and r["already_voted"] is False
    assert len(r["votes"]) == len(p["options"])
    assert isinstance(r["correct_index"], int) and r["explanation"]
    again = api.vote_poll({"qid": qid, "choice": 1, "_ip": "1.1.1.1"})
    assert again["already_voted"] is True and again["total"] == 1
    other = api.vote_poll({"qid": qid, "choice": 1, "_ip": "2.2.2.2"})
    assert other["total"] == 2 and other["already_voted"] is False
    print("  api: /poll/vote counts + one vote per IP (idempotent) ✔")


def test_poll_vote_guards():
    api = _api(_store())
    p = api.today_poll()
    bad = [
        ({"qid": p["qid"] + 99, "choice": 0, "_ip": "3.3.3.3"}, "stale-poll"),
        ({"qid": p["qid"], "choice": 99, "_ip": "3.3.3.3"}, "bad-choice"),
        ({"qid": p["qid"], "choice": -1, "_ip": "3.3.3.3"}, "bad-choice"),
    ]
    for payload, code in bad:
        try:
            api.vote_poll(payload)
            raise AssertionError("expected block: %r" % payload)
        except engine.ExamError as exc:
            assert exc.code == code, (exc.code, code)
    # stale poll by date: qid belongs to a 1-question bank (rotated out)
    try:
        api.vote_poll({"qid": 123456, "choice": 0, "_ip": "9.9.9.9"})
        raise AssertionError("stale qid must be blocked")
    except engine.ExamError as exc:
        assert exc.code == "stale-poll"
    print("  api: stale poll / bad choice / junk qid all blocked ✔")


def test_poll_cors_headers():
    src = (Path(__file__).resolve().parent.parent / "exam_portal" / "server.py").read_text(encoding="utf-8")
    assert '"/poll/today"' in src and '"/poll/vote"' in src
    assert "Access-Control-Allow-Origin" in src and "do_OPTIONS" in src
    assert 'cors=True' in src
    print("  api: public poll routes + CORS/OPTIONS preflight wired ✔")


# ------------------------------------------------------------------ ads admin

def test_admin_ads_read_and_auth():
    _tmp_inventory()
    api = _api(_store(False))
    try:
        api.admin_ads("wrong")
        raise AssertionError("bad key allowed!")
    except engine.ExamError as exc:
        assert exc.code == "unauthorized"
    d = api.admin_ads(ADMIN)
    assert d["ok"] and d["version"] == 3 and len(d["ads"]) == 1
    assert d["path"].endswith("inventory.json")
    print("  ads: admin read + key guard (version/policy exposed) ✔")


def test_admin_ads_upsert_create_and_update():
    path = _tmp_inventory()
    api = _api(_store(False))
    ad = {"id": "shop-new-1", "type": "shop", "layout": "card",
          "title": "విద్యార్థి స్టేషనరీ షాప్ — పరీక్ష కిట్", "desc": "పెన్ను, నోట్‌బుక్.",
          "link": "https://example.com/shop", "cta": "చూడండి", "categories": "Careers",
          "start": "2026-09-01", "end": "2026-12-31", "placements": "top,mid", "active": True}
    r = api.upsert_ad(ADMIN, ad)
    assert r["ok"] and r["count"] == 2
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    assert data["version"] == 3, "version must be preserved"
    assert data["policy"]["label"] == "SPONSORED"
    new_ad = [a for a in data["ads"] if a["id"] == "shop-new-1"][0]
    assert new_ad["title"].startswith("విద్యార్థి")
    assert new_ad["placements"] == ["top", "mid"] and new_ad["name"], new_ad["placements"]
    # update in place
    ad2 = dict(ad, title="కొత్త శీర్షిక — పరీక్ష కిట్ ఆఫర్", active=False)
    r2 = api.upsert_ad(ADMIN, ad2)
    assert r2["count"] == 2, "update must not duplicate"
    data2 = json.loads(Path(path).read_text(encoding="utf-8"))
    row = [a for a in data2["ads"] if a["id"] == "shop-new-1"][0]
    assert row["title"].startswith("కొత్త") and row["active"] is False
    print("  ads: upsert (create + update in place) preserves version/policy ✔")


def test_admin_ads_delete():
    path = _tmp_inventory()
    api = _api(_store(False))
    r = api.delete_ad(ADMIN, "college-banner-demo")
    assert r["ok"] and r["count"] == 0
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    assert data["ads"] == []
    try:
        api.delete_ad(ADMIN, "nope-1")
        raise AssertionError("deleting missing ad must fail")
    except engine.ExamError as exc:
        assert exc.code == "ads-missing"
    print("  ads: delete + missing-id guard ✔")


def test_admin_ads_validation():
    _tmp_inventory()
    api = _api(_store(False))
    cases = [
        ({"id": "AB", "title": "valid title", "link": "https://a.co"}, "bad-ad-id"),
        ({"id": "good-id", "title": "x", "link": "https://a.co"}, "bad-ad-title"),
        ({"id": "good-id", "title": "valid title", "link": "javascript:alert(1)"}, "bad-ad-link"),
        ({"id": "good-id", "title": "valid title", "link": "http://a.co",
          "image": "data:text/html;base64,xx"}, "bad-ad-image"),
        ({"id": "good-id", "title": "valid title", "link": "https://a.co",
          "type": "evil"}, "bad-ad-type"),
        ({"id": "good-id", "title": "valid title", "link": "https://a.co",
          "layout": "popup"}, "bad-ad-layout"),
        ({"id": "good-id", "title": "valid title", "link": "https://a.co",
          "start": "31-12-2026"}, "bad-ad-start"),
    ]
    for payload, code in cases:
        try:
            api.upsert_ad(ADMIN, payload)
            raise AssertionError("unsafe ad accepted: %r" % payload)
        except engine.ExamError as exc:
            assert exc.code == code, (exc.code, code, payload)
    print("  ads: 7 validation rules block unsafe input (XSS/js links/data URIs) ✔")


def test_admin_ads_autocreate_and_writer_reads_stored_ads():
    d = Path(tempfile.mkdtemp(prefix="v47-ads-"))
    os.environ["ADS_INVENTORY_PATH"] = str(d / "nested" / "inventory.json")
    st = _store(False)
    api = _api(st)
    assert api.admin_ads(ADMIN)["ads"] == []
    r = api.upsert_ad(ADMIN, {"id": "first-ad", "title": "మొదటి ప్రకటన ఇక్కడ",
                              "link": "https://example.com/f"})
    assert r["ok"] and r["count"] == 1
    saved = json.loads((d / "nested" / "inventory.json").read_text(encoding="utf-8"))
    assert saved["ads"][0]["id"] == "first-ad"
    assert "policy" in saved and "version" in saved
    print("  ads: inventory auto-created with policy/version on first save ✔")


def test_admin_ads_ui_card_present():
    ui = (Path(__file__).resolve().parent.parent / "exam_portal" / "ui.py").read_text(encoding="utf-8")
    assert "ప్రకటనలు" in ui and "loadAds" in ui and "upsert_ad" not in ui, "UI must call the API, not internals"
    for field in ["a_id", "a_type", "a_layout", "a_title", "a_desc", "a_link",
                  "a_image", "a_cta", "a_cats", "a_start", "a_end", "a_placements", "a_active"]:
        assert 'id="%s"' % field in ui, "missing admin field: " + field
    assert "/api/admin/ads" in ui and "/api/admin/ads/delete" in ui
    assert "loadAds()" in ui, "ads must load right after admin login"
    print("  ui: admin 'ప్రకటనలు' card — 13 fields + load/edit/delete wired ✔")


def test_ad_bot_handoff_contract():
    """The bot's ad_manager must consume exactly what the admin UI writes."""
    path = _tmp_inventory()
    api = _api(_store(False))
    api.upsert_ad(ADMIN, {"id": "coaching-hyd-1", "type": "coaching", "layout": "banner",
                          "title": "హైదరాబాద్ కోచింగ్ — TSPSC బ్యాచ్", "desc": "టెస్ట్ సిరీస్.",
                          "link": "https://example.com/coaching", "cta": "జాయిన్",
                          "placements": ["top"], "active": True})
    from autoblog import ad_manager
    inv = ad_manager.load_inventory(path=Path(path))
    ids = [a.get("id") for a in inv.get("ads", [])]
    assert "coaching-hyd-1" in ids and "college-banner-demo" in ids, ids
    assert inv.get("policy", {}).get("label") == "SPONSORED"
    active = ad_manager.active_ads(inv)
    picked = [a["id"] for a in active]
    assert "coaching-hyd-1" in picked and "college-banner-demo" in picked, picked
    print("  handoff: bot ad_manager loads admin-saved inventory (policy intact) ✔")


def main() -> None:
    test_store_poll_schema_and_bank()
    test_store_poll_vote_dedup_and_counts()
    test_poll_today_shape_and_rotation()
    test_poll_vote_flow_and_idempotency()
    test_poll_vote_guards()
    test_poll_cors_headers()
    test_admin_ads_read_and_auth()
    test_admin_ads_upsert_create_and_update()
    test_admin_ads_delete()
    test_admin_ads_validation()
    test_admin_ads_autocreate_and_writer_reads_stored_ads()
    test_admin_ads_ui_card_present()
    test_ad_bot_handoff_contract()
    print("ALL v47 POLL + ADS-ADMIN TESTS PASSED ✔")


if __name__ == "__main__":
    main()
