# -*- coding: utf-8 -*-
"""v59 tests — site first-look: బ్రేకింగ్ న్యూస్ + "విద్యార్థులు ఎక్కువగా వెతికేవి" + పర్ఫెక్ట్ మెనూ.

Enduku idi:
  student site open cheyagane (a) ippude em jarigindo (బ్రేకింగ్) + (b) tanaki
  panikocche avakashalu (TS/AP jobs · హాల్ టికెట్లు · ఫలితాలు · వాక్-ఇన్ ·
  సాఫ్ట్‌వేర్) modati screen lo chudali. Menu lo order student-vadana
  prakaram undali.

Checks (offline only):
  * config flags + breaking.most_used() order (bot/site okate)
  * build_items: dedupe · per-source cap · short/bad link drop · tag classify
  * write/read feed: atomic JSON + honest empty note + 18h rolling window
  * committed feed: valid JSON + example.com/demo links ledu
  * site: ticker + used strip (8 tiles, MOST_USED order) + breaking section
  * menu order: హోమ్ · ఉద్యోగాలు · హాల్ టికెట్లు · ఫలితాలు · బ్రేకింగ్ · స్కాలర్
  * grid: TS/AP cards mundu · radar hook + CLI wiring · docs

Run: python tests/v59_test.py   (also via python run.py --test-all)
"""
from __future__ import annotations

import io
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
    assert cats == ["ts-jobs", "ap-jobs", "hallticket", "results", "walkin",
                    "software", "private", "current"], cats
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
         "source_name": "Google News · తెలుగు"},
        {"title": "TSPSC Group 2 హాల్ టికెట్ విడుదల - Eenadu",
         "link": "https://a.example.org/1?utm=2", "pub": ""},          # dup title+link
        {"title": "చిన్నది", "link": "https://a.example.org/2"},       # too short
        {"title": "లింక్ లేని వార్త — పరీక్షల అప్డేట్", "link": "javascript:bad"},
        {"title": "a.example.org నుండి మూడో వార్త వివరాలు",
         "link": "https://a.example.org/3",
         "pub": format_datetime(_now - timedelta(hours=2), usegmt=True)},
        {"title": "a.example.org నాలుగో వార్త వివరాలు",
         "link": "https://a.example.org/4",
         "pub": format_datetime(_now - timedelta(hours=3), usegmt=True)},
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
    # official source hint unte adi win avvali
    assert breaking.classify_tag("కొత్త నోటిఫికేషన్ వివరాలు", "results") == "results"


def test_write_read_feed_roundtrip():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "data" / "breaking.json"
        items = breaking.build_items([
            {"title": "TSPSC హాల్ టికెట్ విడుదల అయ్యింది", "link": "https://b.example.org/1"}])
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
                           "link": "https://r.example.org/1"}], path=path)
        breaking.publish([{"title": "APPSC ఫలితాలు విడుదల అయ్యాయి",
                           "link": "https://r.example.org/2"}], path=path)
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
    """v72: ticker/బ్రేకింగ్ teesesaam — badulu search + అర్హత ఫిల్టర్ + install block lu."""
    html = INDEX.read_text(encoding="utf-8")
    assert 'id="tickerwrap"' not in html and "బ్రేకింగ్" not in html, "v72: ticker/బ్రేకింగ్ teeseyali"
    assert 'href="#breaking"' not in html and "brklist" not in html
    used = re.findall(r'<a class="usedcard[^"]*" href="#jobs" data-goto-cat="([a-z-]+)" '
                      r'data-count-cat="[a-z-]+">', html)
    assert used == breaking.most_used_cats(), used
    assert html.count('data-ucount=') == len(breaking.most_used())
    # v72 first-look blocks
    assert 'id="searchbtn"' in html and 'id="searchpanel"' in html and 'id="qtop"' in html
    assert 'data-qual="10th"' in html and 'id="qcount"' in html
    assert 'id="installbtn"' in html and 'rel="manifest"' in html
    assert html.index('class="usedwrap"') < html.index('data-slot="top-leaderboard"') < html.index('class="hero')
    assert "quickbar" not in html


def test_menu_order_perfect():
    html = INDEX.read_text(encoding="utf-8")
    nav = re.search(r'<nav class="nav"[^>]*>(.*?)</nav>', html, re.S).group(1)

    def strip_drop(block: str) -> str:
        """<span class="drop">…</span> blocks ni remove (nested spans tho saha)."""
        out, i = [], 0
        while True:
            j = block.find('<span class="drop"', i)
            if j < 0:
                out.append(block[i:])
                break
            out.append(block[i:j])
            depth, k = 1, block.find(">", j) + 1
            while depth and k > 0:
                nxt_open = block.find("<span", k)
                nxt_close = block.find("</span>", k)
                if nxt_close < 0:
                    break
                if 0 <= nxt_open < nxt_close:
                    depth += 1
                    k = nxt_open + 5
                else:
                    depth -= 1
                    k = nxt_close + 7
            i = k
        return "".join(out)

    heads = [re.sub(r"<[^>]+>", "", x).strip()
             for x in re.findall(r'<a[^>]*>(.*?)</a>', strip_drop(nav), re.S)]
    norm = lambda x: x.replace("\u200c", "").replace("▾", "").strip()  # noqa: E731
    order = [norm(h) for h in heads if norm(h)]
    # v73: English UI
    want = ["Home", "Jobs", "Hall Tickets", "Results",
            "Scholarships", "Current Affairs", "Exams", "More"]
    assert [norm(x) for x in order[:8]] == [norm(x) for x in want], order[:12]

    drop = re.search(r'<span class="drop" role="menu" aria-label="Job categories">(.*?)</span>\s*</span>',
                     nav, re.S).group(1)
    cats = re.findall(r'data-goto-cat="([a-z-]+)"', drop)
    assert cats == ["ts-jobs", "ap-jobs", "central-jobs", "private", "walkin",
                    "software", "outsourcing", "parttime", "abroad"], cats

    mp_start = html.index('<div class="mpanel"')
    mp = html[mp_start:html.index('<div id="top">', mp_start)]
    # v72+v73: mobile panel — search link mundu, breaking ledu (English UI)
    assert mp.index(">Search<") < mp.index("Hall Tickets") < mp.index("Most searched by students")
    assert "బ్రేకింగ్" not in mp and "Breaking" not in mp
    mp_used = re.findall(r'data-goto-cat="([a-z-]+)"', mp)
    assert mp_used[2:10] == breaking.most_used_cats(), mp_used[:12]


def test_grid_student_first_order():
    html = INDEX.read_text(encoding="utf-8")
    zone = html.split('id="grid"')[1].split('id="nores"')[0]
    cats = re.findall(r'<article class="news" data-state="[^"]*" data-cat="([^"]+)"', zone)
    assert len(cats) == 14, len(cats)
    assert "ts-jobs" in cats[0] and ("ts-jobs" in cats[1] or "ap-jobs" in cats[1])
    assert "ap-jobs" in cats[2]
    assert cats.index([c for c in cats if "results" in c][0]) < cats.index(
        [c for c in cats if "current" in c][0])


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
    print("  v59 — FIRST LOOK: బ్రేకింగ్ న్యూస్ + విద్యార్థులు ఎక్కువగా వెతికేవి + మెనూ")
    print("=" * 66)
    tests = [
        ("config flags (BREAKING_MAX/feed path)", test_config_flags),
        ("most_used order: TS · AP · హాల్ టికెట్ · ఫలితాలు · వాక్-ఇన్ · సాఫ్ట్‌వేర్", test_most_used_order),
        ("feed build: dedupe · per-source cap · bad link drop · publisher strip", test_build_items_dedupe_and_guards),
        ("tag classifier (TS/AP/కేంద్ర/విదేశీ/ఫలితాలు/హాల్ టికెట్)", test_classify_tags),
        ("write/read feed: atomic + honest empty note", test_write_read_feed_roundtrip),
        ("feed rolling window: kotha + puratana (18h) + expiry", test_feed_rolling_window),
        ("committed feed: valid + demo links ledu", test_committed_feed_is_honest),
        ("site: ticker + used strip + breaking section wiring", test_site_first_look_wiring),
        ("menu order perfect (top-level + jobs dropdown + mobile)", test_menu_order_perfect),
        ("grid: TS/AP cards mundu", test_grid_student_first_order),
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
    print("ALL v59 FIRST-LOOK TESTS PASSED ✔")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
