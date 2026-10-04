# -*- coding: utf-8 -*-
"""Compatibility gates for the breaking-feed pipeline and v204 homepage.

The old v59 test filename remains in the all-tests manifest, but the current
contract is compact Government Jobs, grouped More navigation, no fabricated
job cards, and conditional verified local news. Backend feed-building checks
remain useful and are kept here.

Run: python3 tests/v59_test.py
"""
from __future__ import annotations

import json
import re
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from autoblog import breaking, config  # noqa: E402

INDEX = ROOT / "preview" / "index.html"
MAIN = ROOT / "autoblog" / "main.py"
FEED = ROOT / "preview" / "data" / "breaking.json"


def test_config_flags():
    assert isinstance(config.BREAKING_MAX, int) and config.BREAKING_MAX >= 5
    assert str(config.BREAKING_FEED_PATH).endswith("breaking.json")
    assert "preview" in str(config.BREAKING_FEED_PATH)


def test_most_used_order():
    cats = breaking.most_used_cats()
    assert cats == ["ts-jobs", "ap-jobs", "central-jobs", "hallticket", "results", "walkin",
                    "software", "success-stories", "private", "current"], cats
    for m in breaking.most_used():
        assert m["cat"] and m["label"] and m["icon"] and m["hint"], m
        # v73: English UI — labels + hints English (site/bot parity)
        assert not re.search(r"[\u0C00-\u0C7F]", m["label"] + m["hint"]), m
    labels = [m["label"] for m in breaking.most_used()]
    assert labels[0].startswith("TS") and labels[1].startswith("AP"), labels
    assert "Hall Tickets" in labels and "Results" in labels, labels


def test_build_items_dedupe_and_guards():
    # pub dates anni dynamic (fixed date = time-bomb; sort deterministic undali).
    _now = datetime.now(timezone.utc).replace(microsecond=0)
    _pub_new = format_datetime(_now, usegmt=True)
    raw = [
        {"title": "TSPSC Group 2 హాల్ టికెట్ విడుదల - Eenadu",
         "link": "https://a.example.org/1", "pub": _pub_new,
         "source_name": "Google News · తెలుగు",
         "verified": True, "source_verified": True},
        {"title": "TSPSC Group 2 హాల్ టికెట్ విడుదల - Eenadu",
         "link": "https://a.example.org/1?utm=2", "pub": "",
         "verified": True, "source_verified": True},                   # dup title+link
        {"title": "చిన్నది", "link": "https://a.example.org/2",
         "verified": True, "source_verified": True},                   # too short
        {"title": "లింక్ లేని వార్త — పరీక్షల అప్డేట్", "link": "javascript:bad",
         "verified": True, "source_verified": True},
        {"title": "a.example.org నుండి మూడో వార్త వివరాలు",
         "link": "https://a.example.org/3",
         "pub": format_datetime(_now - timedelta(hours=2), usegmt=True),
         "verified": True, "source_verified": True},
        {"title": "a.example.org నాలుగో వార్త వివరాలు",
         "link": "https://a.example.org/4",
         "pub": format_datetime(_now - timedelta(hours=3), usegmt=True),
         "verified": True, "source_verified": True},
    ]
    items = breaking.build_items(raw)
    titles = [i["title"] for i in items]
    assert len(titles) == len(set(titles)), titles
    assert all(i["link"].startswith("https://") for i in items)
    assert all(len(i["title"]) >= breaking.MIN_TITLE for i in items)
    assert sum(1 for i in items if i["link"].startswith("https://a.example.org")) <= breaking.MAX_PER_SOURCE
    assert items[0]["tag"] == "hallticket"
    assert items[0]["title"] == "TSPSC Group 2 హాల్ టికెట్ విడుదల", items[0]["title"]
    assert items[0]["time"].endswith("+05:30"), items[0]["time"]   # IST


def test_classify_tags():
    cases = [
        ("TSPSC గ్రూప్ 2 హాల్ టికెట్ డౌన్‌లోడ్", "hallticket"),
        ("APPSC ఫలితాలు విడుదల — కటాఫ్", "results"),
        ("తెలంగాణ ప్రభుత్వ ఉద్యోగ నోటిఫికేషన్", "ts-jobs"),
        ("ఆంధ్రప్రదేశ్ డీఎస్సీ నోటిఫికేషన్", "ap-jobs"),
        ("Dubai గల్ఫ్ ఉద్యోగాలు — వీసా ప్రక్రియ", "abroad"),
        ("SSC CGL కేంద్ర ప్రభుత్వ ఉద్యోగాలు", "central-jobs"),
        ("NSP స్కాలర్‌షిప్ చివరి తేదీ", "scholarship"),
        ("వాక్-ఇన్ ఇంటర్వ్యూ హైదరాబాద్", "walkin"),
        ("రోజు ప్రస్తుతాంశాలు — పథకం వివరాలు", "current"),
    ]
    bad = [(t, breaking.classify_tag(t), want) for t, want in cases
           if breaking.classify_tag(t) != want]
    assert not bad, bad
    # The regional news lanes are distinct; job/exam cues always win.
    assert breaking.classify_tag(
        "Telangana cabinet approves a new public transport policy",
        source_name="TS State News",
    ) == "ts-state-news"
    assert breaking.classify_tag(
        "Hyderabad civic services receive a new public portal",
        district="Hyderabad", state="TS",
    ) == "ts-district-news"
    assert breaking.classify_tag(
        "Telangana Police recruitment notification",
        source_name="TS State News",
    ) == "ts-jobs"
    # An explicit known category hint remains authoritative when safe.
    assert breaking.classify_tag("కొత్త నోటిఫికేషన్ వివరాలు", "results") == "results"


def test_write_read_feed_roundtrip():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "data" / "breaking.json"
        items = breaking.build_items([
            {"title": "TSPSC హాల్ టికెట్ విడుదల అయ్యింది", "link": "https://b.example.org/1",
             "verified": True, "source_verified": True}])
        res = breaking.write_feed(items, path=path)
        assert Path(res["path"]).exists() and res["count"] == 1
        data = breaking.read_feed(path)
        assert data["count"] == 1 and data["items"][0]["title"].startswith("TSPSC")
        assert not list(Path(tmp).rglob("*.tmp")), "atomic write tarvata .tmp undakudadu"
        # khali feed → honest note (fake headline ledu)
        res0 = breaking.write_feed([], path=path)
        data0 = breaking.read_feed(path)
        assert data0["count"] == 0 and "లేవు" in data0["note"], data0["note"]
        assert res0["count"] == 0


def test_feed_rolling_window():
    """Ticker eppudu khali avvakudadu (18h window), kaani paata news expire avvali."""
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "data" / "breaking.json"
        breaking.publish([{"title": "TSPSC హాల్ టికెట్ విడుదల అయ్యింది",
                           "link": "https://r.example.org/1",
                           "verified": True, "source_verified": True}], path=path)
        breaking.publish([{"title": "APPSC ఫలితాలు విడుదల అయ్యాయి",
                           "link": "https://r.example.org/2",
                           "verified": True, "source_verified": True}], path=path)
        assert breaking.read_feed(path)["count"] == 2, "puratana items feed nunchi poyayi"
        old = {"updated": "", "items": [{"title": "పాత వార్త శీర్షిక ఇక్కడ ఉంది",
               "link": "https://r.example.org/9", "tag": "current", "source": "radar",
               "time": "2026-09-16T10:00:00+05:30"}]}
        path.write_text(json.dumps(old, ensure_ascii=False), encoding="utf-8")
        breaking.publish([], path=path)
        assert breaking.read_feed(path)["count"] == 0, "18 గంటల పాత items expire avvali"


def test_committed_feed_is_honest():
    assert FEED.exists(), "preview/data/breaking.json commit avvali (site fetch chestundi)"
    data = json.loads(FEED.read_text(encoding="utf-8"))
    assert isinstance(data.get("items"), list)
    assert set(data) >= {"updated", "source", "count", "note", "items"}
    for it in data["items"]:
        assert it["link"].startswith("http"), it
        assert it["tag"] in {t for t, _ in breaking.TAG_RULES} | {"current"}, it
        assert "example.com" not in it["link"], "demo link site ki vellakudadu"
        assert re.search(r"[\u0C00-\u0C7F]", it["title"]), it["title"]


def test_site_first_look_wiring():
    """The preview is compact/data-free and omits Breaking News when empty."""
    html = INDEX.read_text(encoding="utf-8")
    assert 'id="tickerwrap"' not in html and 'class="su-bnav"' not in html
    for retired in ("Trending today", "Your state", "Popular searches",
                    "Your 5 today", "Students Internet Center", "Compare Jobs"):
        assert retired not in html, f"retired homepage widget remains: {retired}"
    assert '<h1 id="su-home-title">Government Jobs</h1>' in html
    assert "Telangana · Andhra Pradesh · Central Government" in html
    assert 'id="menubtn"' in html and 'menubtn-label">Menu</span>' in html
    assert html.count('id="mpanel"') == 1 and 'id="su-mobile-more"' in html
    assert "No job sample data is shown in this preview." in html
    assert '<article class="news su-op-card"' not in html, "preview must not fabricate vacancies"
    # Preview and theme both short-circuit an empty, stale, or unverified feed.
    data = json.loads(FEED.read_text(encoding="utf-8"))
    assert data["verified_only"] is True and data["items"] == []
    assert 'if (!rows.length) return;' in html and "brklist" in html
    assert "data/breaking.json" in html


def test_menu_order_perfect():
    html = INDEX.read_text(encoding="utf-8")
    nav = re.search(r'<nav class="nav"[^>]*>(.*?)</nav>', html, re.S).group(1)
    labels = ["Home", "Telangana", "Andhra Pradesh", "Central Govt", "More"]
    positions = [nav.index(">" + label + "</a>") for label in labels]
    assert positions == sorted(positions), positions
    assert 'class="menu-item menu-item-has-children su-more-menu"' in nav
    dropdown = re.search(r'<ul class="sub-menu"[^>]*>(.*?)</ul>', nav, re.S).group(1)
    categories = [re.sub(r"<[^>]+>", "", value).strip()
                  for value in re.findall(r"<a[^>]*>(.*?)</a>", dropdown, re.S)]
    categories = [value.replace("&amp;", "&") for value in categories]
    assert len(categories) >= 12 and "Results" in categories and "Scholarships" in categories
    assert "All active opportunities" in categories
    assert "Breaking News" not in categories, "empty local-news feed must not add a More item"

    start = html.index('<aside class="mpanel"')
    panel = html[start:html.index('</aside>', start)]
    mobile_labels = ["Home", "Telangana", "Andhra Pradesh", "Central Govt", "More categories"]
    mobile_positions = [panel.index(label) for label in mobile_labels]
    assert mobile_positions == sorted(mobile_positions), mobile_positions
    details = re.search(r'<details class="mgroup su-mobile-more"[^>]*>', panel).group(0)
    assert " open" not in details, "More should start collapsed"
    assert panel.count('id="su-mobile-more"') == 1


def test_grid_student_first_order():
    """The real homepage is data-driven and applies the TS/AP/Central notice gate."""
    page = (ROOT / "wordpress-theme" / "studentup" / "front-page.php").read_text(encoding="utf-8")
    opportunities = (ROOT / "wordpress-theme" / "studentup" / "inc" / "opportunities.php").read_text(encoding="utf-8")
    assert "studentup_home_opportunity_rows()" in page
    assert "studentup_home_opportunity_render_card( $su_row )" in page
    assert "studentup_home_opportunity_is_notice( $row )" in opportunities
    assert "studentup_jobs_table( 8, $su_page_rows )" in page
    assert "array( 'ts', 'ap', 'central' )" in opportunities
    assert 'id="grid"></div>' in INDEX.read_text(encoding="utf-8"), "static preview should contain no job fixtures"


def test_bot_wiring_radar_and_cli():
    main = MAIN.read_text(encoding="utf-8")
    assert "def breaking_feed_run(" in main
    assert '"--breaking-feed"' in main and '"--breaking-from"' in main
    assert "breaking.publish(summary.get(\"items\", []))" in main, "radar hook missing"
    run = (ROOT / "run.py").read_text(encoding="utf-8")
    assert "--breaking-feed" in run, "run.py help lo flag undali"


def test_docs_v59():
    manual = (ROOT / "MANUAL_ADVANCED_CHECKLIST.md").read_text(encoding="utf-8")
    assert "PART 18" in manual
    # v72: site nunchi తీసేసినా, backend feed (opt-in) docs/env lo undali
    assert "breaking" in manual.lower() or "బ్రేకింగ్" in manual
    assert "విద్యార్థులు ఎక్కువగా వెతికేవి" in manual
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "breaking" in readme.lower()
    env = (ROOT / ".env.example").read_text(encoding="utf-8")
    assert "BREAKING_ENABLED" in env and "BREAKING_MAX" in env


def main():
    print("=" * 66)
    print("  v204 compatibility — compact jobs home + verified local news")
    print("=" * 66)
    tests = [
        ("config flags (BREAKING_MAX/feed path)", test_config_flags),
        ("most_used order: TS · AP · హాల్ టికెట్ · ఫలితాలు · వాక్-ఇన్ · సాఫ్ట్‌వేర్", test_most_used_order),
        ("feed build: dedupe · per-source cap · bad link drop · publisher strip", test_build_items_dedupe_and_guards),
        ("tag classifier (TS/AP/కేంద్ర/విదేశీ/ఫలితాలు/హాల్ టికెట్)", test_classify_tags),
        ("write/read feed: atomic + honest empty note", test_write_read_feed_roundtrip),
        ("feed rolling window: kotha + puratana (18h) + expiry", test_feed_rolling_window),
        ("committed feed: valid + demo links ledu", test_committed_feed_is_honest),
        ("site: compact data-free preview + conditional Breaking News", test_site_first_look_wiring),
        ("desktop Home/TS/AP/Central/More + one mobile drawer", test_menu_order_perfect),
        ("homepage: active TS/AP/Central rows + notice gate", test_grid_student_first_order),
        ("bot: radar hook + --breaking-feed CLI", test_bot_wiring_radar_and_cli),
        ("docs: MANUAL PART 18 + README + .env.example", test_docs_v59),
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
    print("ALL v204 compatibility checks passed ✔")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
