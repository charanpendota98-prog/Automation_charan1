# -*- coding: utf-8 -*-
"""v57 tests — AD ADVISOR: automatic "eppudu e network ki apply cheyyali".

Checks:
  * traffic sources (logs/traffic.json · .env overrides · CLI) + GA4 CSV import
  * no-data honesty (guessing ledu)
  * next-action engine: AdSense first → header-bidding networks → premium → sponsors
  * milestone Telegram alert exactly once per network (state file)
  * AdSense-approved alert once, with ads.txt status inside
  * daily scheduler hook wired in main.run (run avutundi, notify=True)
  * publisher-ID note (ca-pub stays the same; Ezoic uses it; premium = exclusive)

Offline only. Run: python tests/v57_test.py   (also via python run.py --test-all)
"""
from __future__ import annotations

import io
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from autoblog import ad_advisor, config, notifier      # noqa: E402

MAIN_SRC = io.open(ROOT / "autoblog" / "main.py", encoding="utf-8").read()


def _isolate(tmp: Path):
    """Config ni temp paths ki point chesi, original values return chey."""
    originals = {k: getattr(config, k, None) for k in
                 ("AD_TRAFFIC_PATH", "AD_ADVISOR_STATE", "AD_MONTHLY_VIEWS",
                  "AD_MONTHLY_SESSIONS", "AD_TIER1_SHARE", "ADSENSE_APPROVED")}
    config.AD_TRAFFIC_PATH = str(tmp / "traffic.json")
    config.AD_ADVISOR_STATE = str(tmp / "advisor_state.json")
    config.AD_MONTHLY_VIEWS = 0
    config.AD_MONTHLY_SESSIONS = 0
    config.AD_TIER1_SHARE = 0.0
    return originals


def _restore(originals):
    for k, v in originals.items():
        setattr(config, k, v)


def test_no_data_is_honest():
    tmp = Path(tempfile.mkdtemp(prefix="v57a-"))
    orig = _isolate(tmp)
    try:
        t = ad_advisor.load_traffic()
        assert t["known"] is False and t["pageviews"] == 0 and t["source"] == "unknown"
        text = ad_advisor.render(ad_advisor.advice())
        assert "data ledu" in text and "--traffic-csv" in text
        assert "గ్యారంటీ కావు" in text
    finally:
        _restore(orig)


def test_traffic_sources_precedence():
    tmp = Path(tempfile.mkdtemp(prefix="v57b-"))
    orig = _isolate(tmp)
    try:
        ad_advisor.save_traffic(12_000, 7_500, 0.04, source="test")
        t = ad_advisor.load_traffic()
        assert t["pageviews"] == 12_000 and t["sessions"] == 7_500 and t["known"] is True
        config.AD_MONTHLY_VIEWS = 30_000          # .env beats the file
        t2 = ad_advisor.load_traffic()
        assert t2["pageviews"] == 30_000 and ".env" in t2["source"]
        assert t2["sessions"] == ad_advisor.default_sessions(30_000), "sessions auto-fill"
        t3 = ad_advisor.load_traffic(views=55_000, tier1=0.6)   # CLI beats .env
        assert t3["pageviews"] == 55_000 and t3["tier1_share"] == 0.6
        assert t3["sessions"] == ad_advisor.default_sessions(55_000)
        assert ad_advisor.save_traffic(1_000).exists()
    finally:
        _restore(orig)


def test_ga4_csv_import():
    tmp = Path(tempfile.mkdtemp(prefix="v57c-"))
    orig = _isolate(tmp)
    try:
        csv = tmp / "ga4.csv"
        csv.write_text("month,pageviews,sessions,tier1_share\n"
                       "2026-08,15000,9000,4\n2026-09,12000,8000,6\n", encoding="utf-8")
        info = ad_advisor.import_ga4_csv(csv)
        assert info["pageviews"] == 27_000 and info["sessions"] == 17_000, info
        assert abs(info["tier1_share"] - 0.06) < 1e-9, info      # % → share
        t = ad_advisor.load_traffic()
        assert t["pageviews"] == 27_000 and "ga4_csv" in t["source"] and t["month"] == "2026-09"
        bad = tmp / "bad.csv"
        bad.write_text("foo,bar\n1,2\n", encoding="utf-8")
        try:
            ad_advisor.import_ga4_csv(bad)
            raise AssertionError("tappu CSV accept avvakudadu")
        except ValueError as exc:
            assert "pageviews" in str(exc)
    finally:
        _restore(orig)


def test_next_action_order():
    rows_10k = ad_advisor.assess(10_000, 6_250, 0.05)
    a = ad_advisor.next_action(rows_10k, 10_000, 6_250, 0.05, adsense_approved=False)
    assert a["key"] == "adsense" and "apply" in a["title"].lower(), a
    assert any("ADSENSE_CLIENT_ID" in s for s in a["steps"]), "ads.txt step undali"
    # AdSense approved + 30k views + Tier-1 → Raptive recommend (premium warning tho)
    rows_30k = ad_advisor.assess(30_000, 18_000, 0.55)
    b = ad_advisor.next_action(rows_30k, 30_000, 18_000, 0.55, adsense_approved=True)
    assert b["key"] in ("raptive", "adversal", "monumetric"), b["key"]
    assert "EXCLUSIVE" in b["detail"] or b["key"] not in ad_advisor.PREMIUM
    # 10k views approved → Ezoic next (Monumetric blocked by Tier-1)
    c = ad_advisor.next_action(rows_10k, 10_000, 6_250, 0.05, adsense_approved=True)
    assert c["key"] == "ezoic", c
    # Tier-1 ready, 12k views → Monumetric (pageviews first)
    rows_12k = ad_advisor.assess(12_000, 7_500, 0.6)
    d = ad_advisor.next_action(rows_12k, 12_000, 7_500, 0.6, adsense_approved=True)
    assert d["key"] == "monumetric", d


def test_gap_ordering_and_tips():
    rows = ad_advisor.assess(10_000, 6_250, 0.05)
    gaps = ad_advisor.gap_to_next(rows, 10_000, 6_250, 0.05)
    kinds = [g["kind"] for g in gaps]
    assert kinds.index("pageviews") < kinds.index("tier1"), "pageview gaps mundu"
    mon = next(g for g in gaps if g["key"] == "monumetric")
    assert mon["gap"] == 0 and mon["kind"] == "tier1", mon      # 10k views unnai, Tier-1 ledu
    rap = next(g for g in gaps if g["key"] == "raptive")
    assert rap["kind"] == "pageviews" and rap["gap"] == 15_000, rap


def test_milestones_notify_once():
    tmp = Path(tempfile.mkdtemp(prefix="v57d-"))
    orig = _isolate(tmp)
    sent = []
    orig_tg = notifier.send_telegram
    notifier.send_telegram = lambda text, *a, **k: (sent.append(text), True)[1]
    try:
        fresh = ad_advisor.check_milestones(10_000, 7_000, 0.05, notify=True)
        assert [r["key"] for r in fresh] == ["ezoic"], fresh
        assert len(sent) == 1 and "Ezoic" in sent[0] and "apply" in sent[0]
        assert "గ్యారంటీ కాదు" in sent[0]
        again = ad_advisor.check_milestones(10_000, 7_000, 0.05, notify=True)
        assert again == [] and len(sent) == 1, "milestone okkasari matrame"
        state = json.loads(Path(config.AD_ADVISOR_STATE).read_text(encoding="utf-8"))
        assert state["notified"].get("milestone:ezoic") and state["milestones"]["ezoic"]
        # premium milestone → exclusive warning
        ad_advisor.check_milestones(30_000, 18_000, 0.55, notify=True)
        assert any("EXCLUSIVE" in s and "Raptive" in s for s in sent), sent[-1]
        # data lekapote (0 views) alerts ledu
        n_before = len(sent)
        assert ad_advisor.check_milestones(0, 0, 0.0, notify=True) in ([], [])
        assert len(sent) == n_before
    finally:
        notifier.send_telegram = orig_tg
        _restore(orig)


def test_adsense_approved_alert_once():
    tmp = Path(tempfile.mkdtemp(prefix="v57e-"))
    orig = _isolate(tmp)
    sent = []
    orig_tg = notifier.send_telegram
    notifier.send_telegram = lambda text, *a, **k: (sent.append(text), True)[1]
    try:
        config.ADSENSE_APPROVED = False
        assert ad_advisor.notify_adsense_approved(notify=True) is False
        config.ADSENSE_APPROVED = True
        assert ad_advisor.notify_adsense_approved(notify=True) is True
        assert ad_advisor.notify_adsense_approved(notify=True) is False, "okkasari matrame"
        assert len(sent) == 1 and "AdSense APPROVED" in sent[0]
        assert "ADSENSE_CLIENT_ID" in sent[0] and "ads.txt" in sent[0]
        assert "publisher id — idi mareadu" in sent[0]
    finally:
        notifier.send_telegram = orig_tg
        _restore(orig)


def test_advice_payload_and_publisher_note():
    tmp = Path(tempfile.mkdtemp(prefix="v57f-"))
    orig = _isolate(tmp)
    try:
        ad_advisor.save_traffic(30_000, 18_000, 0.55, source="test")
        res = ad_advisor.advice()
        assert res["traffic"]["pageviews"] == 30_000
        assert res["action"]["key"]
        assert len(res["networks"]) == 6
        note = res["publisher_id_note"]
        assert "mareadu" in note and "Ezoic" in note and "Raptive/Mediavine" in note
        text = ad_advisor.render(res)
        assert "AD ADVISOR" in text and "Publisher ID" in text
        assert "Raptive" in text and "sessions" in text
    finally:
        _restore(orig)


def test_scheduler_hook_and_cli_wired():
    assert "--ad-advisor" in MAIN_SRC and "--traffic-csv" in MAIN_SRC
    assert "advisor:{today.isoformat()}" in MAIN_SRC, "roju okkasari run avvali"
    assert 'from . import ad_advisor' in MAIN_SRC
    assert "AD_ADVISOR_HOUR" in MAIN_SRC
    assert "_adv.advice(notify=True)" in MAIN_SRC, "daily hook notify=True tho run avvali"
    for flag in ("AD_ADVISOR_ENABLED", "AD_ADVISOR_HOUR", "AD_TRAFFIC_PATH",
                 "AD_ADVISOR_STATE", "AD_MONTHLY_VIEWS", "AD_MONTHLY_SESSIONS",
                 "AD_TIER1_SHARE"):
        assert hasattr(config, flag), f"config lo {flag} ledu"
    env_example = io.open(ROOT / ".env.example", encoding="utf-8").read()
    assert "AD_ADVISOR_ENABLED" in env_example and "AD_MONTHLY_VIEWS" in env_example


def main():
    print("=" * 66)
    print("  v57 — AD ADVISOR (eppudu e network ki apply cheyyali, automatic)")
    print("=" * 66)
    tests = [
        ("traffic data lekapote honest ga cheptundi", test_no_data_is_honest),
        ("traffic sources: file → .env → CLI (sessions auto-fill)", test_traffic_sources_precedence),
        ("GA4 CSV import (%, month, sums) + bad CSV reject", test_ga4_csv_import),
        ("next-action order: AdSense → Ezoic → Monumetric → premium", test_next_action_order),
        ("gap list: pageviews mundu, Tier-1 tarvata", test_gap_ordering_and_tips),
        ("milestone Telegram alert okkasari per network", test_milestones_notify_once),
        ("AdSense approved alert okkasari (ads.txt status tho)", test_adsense_approved_alert_once),
        ("advice payload + publisher-id note", test_advice_payload_and_publisher_note),
        ("daily scheduler hook + CLI + .env.example", test_scheduler_hook_and_cli_wired),
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
    print("-" * 66)
    if failed:
        print(f"  {failed} TEST(S) FAILED ✘")
        return 1
    print("ALL v57 AD-ADVISOR TESTS PASSED ✔")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
