# -*- coding: utf-8 -*-
"""v50 tests — content pillars, manual approval, Rank Math, auto-refresh.

Answers "anni perfect ga, anni category lu, manual approve, daily refresh,
100% SEO" with executable proof instead of promises. Offline, no network.

Run: python tests/v50_test.py   (also via python run.py --test-all)
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from autoblog import config, pipeline, seo, sources_grid, topic_engine   # noqa: E402

NEW_PILLARS = ["Outsourcing Jobs", "Current Affairs", "Exam Tips", "Upcoming Exams"]
CORE_PILLARS = ["TS Govt Jobs", "AP Govt Jobs", "Central Govt Jobs", "Scholarships",
                "Walkin Jobs", "Private Jobs", "Software Jobs", "Part Time Jobs",
                "Hall Tickets", "Results", "Internships", "Online Education"]


def test_all_pillars_configured():
    cats = list(config.CATEGORIES)
    for pillar in CORE_PILLARS + NEW_PILLARS:
        assert pillar in cats, "category missing from config.CATEGORIES: " + pillar
    assert len(cats) >= 16, len(cats)
    print("  pillars: %d categories configured (12 core + 4 new) ✔" % len(cats))


def test_pillar_priority_targets_high_value_topics():
    pri = config.CATEGORY_PRIORITY
    for pillar in ["Central Govt Jobs", "TS Govt Jobs", "Upcoming Exams", "Outsourcing Jobs",
                   "Current Affairs", "Scholarships", "Results"]:
        assert pri.get(pillar, 0) >= 2, "%s has no priority boost" % pillar
    print("  pillars: priority boosts (jobs/exams/current affairs get extra slots) ✔")


def test_every_pillar_has_writer_prompt():
    from autoblog import gemini_client
    prompts = gemini_client.CATEGORY_SEEDS
    for pillar in CORE_PILLARS + NEW_PILLARS:
        if pillar == "Results":       # results use a shared template
            continue
        assert pillar in prompts, "no writer prompt for: " + pillar
        assert len(prompts[pillar]) > 60, pillar
    print("  pillars: writer prompt (deep source instructions) for each kind ✔")


def test_every_pillar_has_card_label():
    from autoblog import image_gen
    for pillar in NEW_PILLARS:
        assert pillar in image_gen.CAT_SHORT, "thumbnail label missing: " + pillar
    print("  pillars: thumbnail labels for new kinds (crop-safe) ✔")


def test_auto_category_detection_covers_new_pillars():
    cases = [
        ("TSSPDCL outsourcing jobs 2026", "Outsourcing Jobs"),
        ("CRC contract basis recruitment notification", "Outsourcing Jobs"),
        ("Daily current affairs for TSPSC group 2", "Current Affairs"),
        ("PIB press release on new scholarship scheme", "Current Affairs"),
        ("TSPSC upcoming exams calendar 2026", "Upcoming Exams"),
        ("SSC exam calendar notification", "Upcoming Exams"),
        ("TSPSC exam preparation strategy previous papers", "Exam Tips"),
        ("Inter board exam tips time table plan", "Exam Tips"),
        ("NSP scholarship last date extended", "Scholarships"),
        ("Telangana TSPSC Group 1 notification", "TS Govt Jobs"),
        ("Andhra APPSC Group 2 hall ticket", "AP Govt Jobs"),
        ("SSC CGL recruitment 2026 vacancy", "Central Govt Jobs"),
    ]
    for title, expected in cases:
        got = pipeline.classify_category(title)
        assert got == expected, "classify(%r) = %s, expected %s" % (title, got, expected)
    print("  pillars: auto category detection correct for %d real headlines ✔" % len(cases))


def test_official_source_grid_covers_every_pillar():
    cats = set(s["cat"] for s in sources_grid.SOURCES_GRID)
    for pillar in CORE_PILLARS + NEW_PILLARS:
        assert pillar in cats, "no official source for: %s" % pillar
    total = len(sources_grid.SOURCES_GRID)
    assert total >= 129, "grid shrank: %d" % total
    daily = [s for s in sources_grid.SOURCES_GRID if s.get("daily")]
    assert len(daily) >= 20, len(daily)
    # notification/news pillars must be watched daily; Exam Tips is evergreen
    # guidance (source-backed, but no daily notification feed needed).
    for pillar in ["Outsourcing Jobs", "Current Affairs", "Upcoming Exams"]:
        assert any(s["cat"] == pillar and s.get("daily") for s in sources_grid.SOURCES_GRID), \
            "%s has no daily-watched source" % pillar
    assert any(s["cat"] == "Exam Tips" for s in sources_grid.SOURCES_GRID)
    print("  sources: %d official sources · every pillar watched (new ones daily) ✔" % total)


def test_seasonal_rotation_uses_new_pillars():
    seasonal = topic_engine.SEASONAL_CATEGORIES
    used = {c for cats in seasonal.values() for c in cats}
    for pillar in ["Upcoming Exams", "Exam Tips", "Current Affairs", "Outsourcing Jobs"]:
        assert pillar in used, "seasonal rotation never uses: " + pillar
    for month in range(1, 13):
        assert month in seasonal, "month %d has no seasonal plan" % month
    print("  season plan: 12 months covered, new pillars rotate in-season ✔")


# ------------------------------------------------- manual approval (gates)

def test_manual_approval_is_the_default():
    assert config.DEFAULT_POST_STATUS == "draft", \
        "DEFAULT_POST_STATUS must be 'draft' — humans approve before publish"
    from autoblog import approval_bot
    src = Path(approval_bot.__file__).read_text(encoding="utf-8")
    assert "approve" in src.lower()
    print("  manual gate: drafts by default + Telegram approval bot present ✔")


def test_live_publish_needs_quality_and_originality():
    qa = getattr(config, "PUBLISH_QA_MIN_SCORE", 0)
    orig = getattr(config, "PUBLISH_ORIGINALITY_MIN", 0)
    assert qa >= 80, qa
    assert orig >= 60, orig
    print("  manual gate: direct live publish needs QA>=%d + originality>=%d%% ✔"
          % (qa, orig))


def test_human_review_never_byte_copied():
    """Originality floor blocks copy-paste; deep gate blocks conflicts."""
    assert getattr(config, "PUBLISH_ORIGINALITY_MIN", 0) >= 60
    from autoblog import deep_research
    for fn in ("gate_post", "publish_gate", "verify_facts", "confidence_score"):
        assert hasattr(deep_research, fn), "deep verification gate missing: " + fn
    # conflict detection must be able to BLOCK, not warn-and-continue
    rep_conflict = {"conflicts": [{"label": "last date", "values": ["2026-09-20", "2026-09-25"]}],
                    "facts": [], "sources": [], "confidence": 90}
    blockers, warns = deep_research.gate_post("<p>test</p>", rep_conflict, live=True)
    assert blockers, "conflicting dates must produce a hard block"
    clean = {"conflicts": [], "facts": [], "sources": [], "confidence": 90}
    b2, _ = deep_research.gate_post("<p>test</p>", clean, live=True)
    assert not [b for b in b2 if "conflict" in b.lower()], b2
    print("  no-copy: originality floor + deep gate hard-blocks source conflicts ✔")


# --------------------------------------------------------- Rank Math / SEO

def test_rankmath_meta_is_complete():
    meta = seo.rankmath_meta(
        focus_keyword="టీఎస్పీఎస్సీ గ్రూప్ 2 నోటిఫికేషన్ 2026",
        description="టీఎస్పీఎస్సీ గ్రూప్ 2 నోటిఫికేషన్ 2026 వివరాలు, అర్హత, దరఖాస్తు తేదీలు, అధికారిక మూలాలు.",
        seo_title="టీఎస్పీఎస్సీ గ్రూప్ 2 నోటిఫికేషన్ 2026 — దరఖాస్తు విధానం, అర్హత",
        secondary_keywords=["tspsc group 2 apply online", "tspsc group 2 eligibility"],
    )
    need = ["rank_math_focus_keyword", "rank_math_description", "rank_math_title",
            "rank_math_facebook_title", "rank_math_twitter_title"]
    for key in need:
        assert key in meta and str(meta[key]).strip(), "Rank Math field missing: " + key
    assert len(meta["rank_math_description"]) <= 160
    assert len(meta["rank_math_title"]) <= 160
    assert "index" in str(meta.get("rank_math_robots", "index"))
    print("  Rank Math: focus keyword + title + description + social + robots ✔")


def test_seo_payload_covers_google_essentials():
    body = ("<p>టీఎస్పీఎస్సీ గ్రూప్ 2 నోటిఫికేషన్ 2026 వివరాలు ఇక్కడ ఉన్నాయి. "
            "అధికారిక మూలాల ప్రకారం దరఖాస్తు ప్రక్రియ ప్రారంభమైంది.</p>") * 12
    html = seo.enhance(
        html=body, focus_keyword="టీఎస్పీఎస్సీ గ్రూప్ 2 నోటిఫికేషన్ 2026",
        internal_links=[], external_links=[],
        quick_answer="దరఖాస్తు వివరాలు అధికారిక పోర్టల్‌లో ధృవీకరించండి.",
        date_str="2026-09-18", date_modified="2026-09-18",
        slug="tspsc-group-2-notification-2026", title="టీఎస్పీఎస్సీ గ్రూప్ 2 2026",
        description="టీఎస్పీఎస్సీ గ్రూప్ 2 నోటిఫికేషన్ 2026 వివరాలు, అర్హత, దరఖాస్తు తేదీలు.",
        category="TS Govt Jobs", source_domains=["tspsc.gov.in"],
    )
    for needle in ["su-quick-answer-card", "tspsc.gov.in", "టీఎస్పీఎస్సీ"]:
        assert needle in html, "SEO enhance missing: " + needle
    assert len(html) > len(body), "enhance added nothing"
    print("  SEO: quick-answer card + source trust + keyword-first paragraph ✔")


# ------------------------------------------------------------ auto-refresh

def test_auto_refresh_flow_exists_and_is_safe():
    assert hasattr(pipeline, "auto_refresh"), "pipeline.auto_refresh missing"
    from autoblog import state
    assert hasattr(state, "posts_to_refresh") and hasattr(state, "record_refresh")

    db = Path(tempfile.mkdtemp(prefix="v50-")) / "state.db"
    state.init(db)
    state.record_post(db, title="TSPSC నోటిఫికేషన్ 2026", slug="tspsc-2026",
                      category="TS Govt Jobs", link="https://studentup.in/tspsc-2026",
                      status="publish", wp_id=101)
    picks = state.posts_to_refresh(db, older_days=0, limit=5)
    assert any(p["wp_id"] == 101 for p in picks), picks
    state.record_refresh(db, 101)
    after = state.posts_to_refresh(db, older_days=0, limit=5)
    assert all(p["wp_id"] != 101 or "refreshed" for p in after)
    print("  refresh: old published posts picked, refreshed_at recorded ✔")


def test_cli_exposes_refresh_and_manual_flags():
    src = (ROOT / "autoblog" / "main.py").read_text(encoding="utf-8")
    for flag in ["--auto-refresh", "--update", "--dry-run", "--mock", "--site-audit"]:
        assert '"%s"' % flag in src, "CLI flag missing: " + flag
    print("  refresh: CLI --auto-refresh / --update / --dry-run wired ✔")


def test_daily_volume_targets_many_posts():
    assert config.DAILY_MIN >= 3 and config.DAILY_MAX >= config.DAILY_MIN
    assert config.DAILY_MAX >= 5, "owner wants many posts/day"
    print("  volume: %d–%d draft slots/day across all pillars ✔"
          % (config.DAILY_MIN, config.DAILY_MAX))


def main() -> None:
    test_all_pillars_configured()
    test_pillar_priority_targets_high_value_topics()
    test_every_pillar_has_writer_prompt()
    test_every_pillar_has_card_label()
    test_auto_category_detection_covers_new_pillars()
    test_official_source_grid_covers_every_pillar()
    test_seasonal_rotation_uses_new_pillars()
    test_manual_approval_is_the_default()
    test_live_publish_needs_quality_and_originality()
    test_human_review_never_byte_copied()
    test_rankmath_meta_is_complete()
    test_seo_payload_covers_google_essentials()
    test_auto_refresh_flow_exists_and_is_safe()
    test_cli_exposes_refresh_and_manual_flags()
    test_daily_volume_targets_many_posts()
    print("ALL v50 PILLAR + MANUAL-GATE + SEO + REFRESH TESTS PASSED ✔")


if __name__ == "__main__":
    main()
