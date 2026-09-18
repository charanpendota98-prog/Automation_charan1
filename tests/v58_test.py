# -*- coding: utf-8 -*-
"""v58 tests — 17వ pillar: విదేశీ ఉద్యోగాలు (Abroad Jobs / Gulf · visa · IELTS · NRI).

Enduku idi: Tier-1 (US/UK/Gulf) ట్రాఫిక్ + high-CPC topics (IELTS, visa, education
loan, consultancy) — AdSense RPM 3-5x + Raptive/Mediavine eligibility ki asalu daari.

Checks (offline only):
  * category 17 pillars lo undi + priority boost + auto-create ready
  * classifier: Gulf/visa/IELTS/study-abroad → Abroad Jobs; TS/AP/Central tests intact
  * Gemini seeds + 14 official sources (grid category + daily hot-list)
  * radar source whitelist + config CATEGORIES round-trip
  * website: nav dropdown + chip + mobile link + card + tiles 17/143
  * advisor Tier-1 advice prakaram ee pillar ni suggest chestundi
  * robots.txt internal artifacts ni block chestundi + top-200 CSV engine tho match

Run: python tests/v58_test.py   (also via python run.py --test-all)
"""
from __future__ import annotations

import csv
import io
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from autoblog import ad_advisor, config, gemini_client, pipeline, sources_grid  # noqa: E402

INDEX = ROOT / "preview" / "index.html"


def test_config_has_17th_pillar():
    assert len(config.CATEGORIES) == 17, config.CATEGORIES
    assert "Abroad Jobs" in config.CATEGORIES
    assert config.CATEGORIES[-1] == "Abroad Jobs", "kotha pillar last lo add avvali"
    assert config.CATEGORY_PRIORITY.get("Abroad Jobs") == 4, "high-CPC pillar → priority 4"
    assert len(set(config.CATEGORIES)) == len(config.CATEGORIES), "duplicates vaddu"


def test_classifier_abroad():
    cases = [
        ("Dubai jobs for Indians 2026 — salary and accommodation", "Abroad Jobs"),
        ("IELTS exam date change: new fee and test centres", "Abroad Jobs"),
        ("గల్ఫ్ ఉద్యోగాలు: కొత్త నోటిఫికేషన్ వివరాలు", "Abroad Jobs"),
        ("Canada work visa update for Indian students", "Abroad Jobs"),
        ("study abroad scholarship for Indian students 2026", "Abroad Jobs"),
        ("Saudi Arabia recruitment drive for nurses from Telangana", "Abroad Jobs"),
        # vivaramaina rules ippatiki pani cheyyali (regression)
        ("TSPSC group 2 notification 2026", "TS Govt Jobs"),
        ("SSC CGL apply online 2026", "Central Govt Jobs"),
        ("software developer off campus drive", "Software Jobs"),
        ("walk-in interview Hyderabad tomorrow", "Walkin Jobs"),
    ]
    bad = [(t, pipeline.classify_category(t, ""), want)
           for t, want in cases if pipeline.classify_category(t, "") != want]
    assert not bad, bad


def test_classifier_abroad_rule_is_first():
    """Abroad rule list lo modati di — generic "ఉద్యోగాలు" Central ki vellakudadu."""
    first_cat = pipeline.CATEGORY_RULES[0][0]
    assert first_cat == "Abroad Jobs", first_cat
    words = pipeline.CATEGORY_RULES[0][1]
    for needle in ("గల్ఫ్ ఉద్యోగాలు", "విదేశీ ఉద్యోగాలు", "ielts exam", "study abroad",
                   "work visa", "visa appointment"):
        assert needle in words, f"phrase miss: {needle}"


def test_gemini_seeds_and_sources():
    assert "Abroad Jobs" in gemini_client.CATEGORY_SEEDS
    seed = gemini_client.CATEGORY_SEEDS["Abroad Jobs"]
    for needle in ("Gulf", "IELTS", "visa", "eMigrate", "NRI"):
        assert needle.lower() in seed.lower(), f"seed lo ledu: {needle}"

    grid = sources_grid._S
    assert len(grid) == 143, f"143 sources undali, vachhindi {len(grid)}"
    abroad = [s for s in grid if s[2] == "Abroad Jobs"]
    assert len(abroad) == 14, f"14 abroad sources undali, unnai {len(abroad)}"
    assert sum(1 for s in abroad if s[3]) >= 4, "daily hot-list lo kuda undali"
    names = " ".join(s[0] for s in abroad)
    for needle in ("eMigrate", "IELTS", "Gulf", "NRI", "Study Abroad"):
        assert needle in names, f"source miss: {needle}"


def test_source_categories_are_valid():
    cats = {s[2] for s in sources_grid._S}
    unknown = cats - set(config.CATEGORIES)
    assert not unknown, f"grid categories config lo levu: {unknown}"
    assert "Abroad Jobs" in cats
    daily = sources_grid.SOURCES_GRID
    assert all(set(s) >= {"name", "q", "cat"} for s in daily)


def test_website_wiring():
    html = io.open(INDEX, encoding="utf-8").read()
    assert 'data-cat="abroad"' in html, "chip/card ledu"
    assert 'data-goto-cat="abroad"' in html, "nav/mobile link ledu"
    assert html.count('data-goto-cat="abroad"') >= 2, "desktop dropdown + mobile panel"
    grid_zone = html.split('id="grid"')[1].split('id="nores"')[0]
    assert 'data-cat="abroad"' in grid_zone, "card #grid lopala undali (v51 lesson)"
    assert "విదేశీ ఉద్యోగాలు" in html
    assert "<b>17</b>" in html, "tile 17 categories"
    assert "<b>143</b>" in html, "tile 143 sources"
    # tiles: suites/runtime numbers
    assert "<b>44/44</b>" in html and "<b>109/109</b>" in html


def test_card_has_pure_telugu_and_no_leaks():
    html = io.open(INDEX, encoding="utf-8").read()
    card = html.split('data-cat="abroad" data-text')[1].split("</article>")[0]
    assert "గల్ఫ్" in card and "eMigrate" in card, "content undali"
    forbidden = (".env", "Demo contact", "http://localhost", "TODO")
    for bad in forbidden:
        assert bad not in card, f"leak: {bad}"


def test_advisor_uses_abroad_pillar_for_tier1():
    saved = config.ADSENSE_APPROVED
    config.ADSENSE_APPROVED = True
    try:
        # Tier-1 takkuva unte: Advisor ee pillar ni suggest cheyyali
        rows = ad_advisor.assess(12_000, 500, 0.10)          # Ezoic sessions lekunda block
        action = ad_advisor.next_action(rows, 12_000, 500, 0.10, adsense_approved=True)
        text = action["detail"] + " ".join(action["steps"])
        rendered = ad_advisor.render(ad_advisor.advice(pageviews=12_000, sessions=500,
                                                       tier1=0.10))
        assert "Abroad Jobs" in text or "Abroad Jobs" in rendered, text
        assert "Tier-1" in rendered
        gaps = ad_advisor.gap_to_next(ad_advisor.assess(10_000, 6_250, 0.05), 10_000, 6_250, 0.05)
        assert any(g["kind"] == "tier1" for g in gaps), gaps
    finally:
        config.ADSENSE_APPROVED = saved


def test_docs_updated():
    plan = io.open(ROOT / "CONTENT_PLAN_DAILY.md", encoding="utf-8").read()
    assert "17" in plan and "143" in plan and "Abroad" in plan.replace("విదేశీ", "Abroad"), \
        "content plan lo kotha pillar + sources update avvali"
    manual = io.open(ROOT / "MANUAL_ADVANCED_CHECKLIST.md", encoding="utf-8").read()
    assert "Abroad Jobs" in manual and "PART 17" in manual


def test_keyword_universe_has_abroad():
    from autoblog import top_post
    top_post._UNIVERSE_CACHE = None
    uni = top_post.keyword_universe()
    assert len(top_post.ENTITIES) == 203, len(top_post.ENTITIES)
    assert len(uni) == 11_192, len(uni)
    abroad = [k for k in uni if k["cat"] == "Abroad Jobs"]
    assert len(abroad) >= 400, f"abroad keywords thakkuva: {len(abroad)}"
    kws = " ".join(k["kw"] for k in abroad)
    for needle in ("gulf", "ielts", "passport"):
        assert needle in kws, f"keyword miss: {needle}"
    assert all(k["priority"] > 0 for k in abroad)
    # Telugu intents kuda generate avvali (visible content Telugu)
    assert any("telugu" in k["kw"] for k in abroad), "Telugu keyword variants undali"
    stats = top_post.universe_stats(uni)
    assert stats["entities"] == 203


def test_robots_blocks_internal_artifacts():
    """v58 audit: internal strategy/keyword artifacts public ga index avvakudadu."""
    txt = (ROOT / "preview" / "robots.txt").read_text(encoding="utf-8")
    for path in ("/admin", "/legacy-concept.html", "/ads-preview.html",
                 "/dominance-plan-90-days.md", "/top-post-blueprint.html",
                 "/keyword-universe-top200.csv", "/v38.html", "/v39.html",
                 "/v41.html"):
        assert "Disallow: %s" % path in txt, "robots disallow missing: " + path
    assert "Allow: /\n" in txt, "public pages allow avvali"
    assert "Sitemap: https://studentup.in/sitemap.xml" in txt


def test_keyword_csv_matches_engine():
    """Top-200 CSV engine nunchi generate avutundi — stale unte ee test fail (v58 audit)."""
    from autoblog import top_post
    rows = list(csv.DictReader(io.open(ROOT / "preview" / "keyword-universe-top200.csv",
                                       encoding="utf-8")))
    assert len(rows) == 200, len(rows)
    assert [r["rank"] for r in rows] == [str(i) for i in range(1, 201)], "rank order"
    live = {e["kw"] for e in top_post.keyword_universe()}
    stale = sorted({r["keyword"] for r in rows} - live)
    assert not stale, "CSV lo stale keywords: %s" % stale[:5]
    cats = set(config.CATEGORIES)
    assert {r["category"] for r in rows} <= cats, {r["category"] for r in rows} - cats
    assert any(r["category"] == "Abroad Jobs" for r in rows), "abroad row undali"


def main():
    print("=" * 66)
    print("  v58 — 17వ PILLAR: విదేశీ ఉద్యోగాలు (Tier-1 revenue unlock)")
    print("=" * 66)
    tests = [
        ("config: 17 pillars + Abroad priority 4", test_config_has_17th_pillar),
        ("classifier: Gulf/IELTS/visa → Abroad (10 cases)", test_classifier_abroad),
        ("Abroad rule list modati di + phrases", test_classifier_abroad_rule_is_first),
        ("Gemini seeds + 14 abroad sources (daily hot-list)", test_gemini_seeds_and_sources),
        ("grid categories anni config lo unnai (17)", test_source_categories_are_valid),
        ("site: nav + chip + mpanel + card + tiles 17/143", test_website_wiring),
        ("card content pure-Telugu + leaks ledu", test_card_has_pure_telugu_and_no_leaks),
        ("advisor Tier-1 advice ee daari chupistundi", test_advisor_uses_abroad_pillar_for_tier1),
        ("keyword universe: 203 entities · 11,192 keywords (+abroad)", test_keyword_universe_has_abroad),
        ("docs: content plan + manual PART 17", test_docs_updated),
        ("robots.txt internal artifacts block + sitemap intact", test_robots_blocks_internal_artifacts),
        ("top-200 CSV engine tho match (stale kaadu)", test_keyword_csv_matches_engine),
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
    print("ALL v58 ABROAD-PILLAR TESTS PASSED ✔")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
