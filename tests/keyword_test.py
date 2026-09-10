"""v17 tests: Keyword Dominance Engine.

Sections:
  1. Keyword matrix (60+ exams × 14 intents, unique, live categories only,
     year handling)
  2. Google Autocomplete harvest (fake requests — parse + failure-safe)
  3. Coverage/gap logic (word-boundary matching — no "date"⊂"dates" bug)
  4. daily_keyword_harvest: gap queue + once/day guard + force
  5. suggest_seeds() sane
  6. v16/v17 pools: VIRAL + TIPS ideas + picker shares + WRITING_RULES
     keyword-dominance/10x/no-copy sections present
"""

import json
import sys
import tempfile
import types
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from autoblog import config, keyword_engine as ke, news_radar, state  # noqa: E402

LIVE_CATS = {"Scholarships", "Central Govt Jobs", "TS Govt Jobs", "AP Govt Jobs",
             "Private Jobs", "Software Jobs", "Part Time Jobs", "Walkin Jobs",
             "Hall Tickets", "Results", "Internships", "Online Education",
             "Uncategorized"}


def main():
    print("v17 KEYWORD ENGINE TESTS:")
    tmp = Path(tempfile.mkdtemp(prefix="kw_test_"))
    config.OUTPUT_DIR = tmp
    config.STATE_PATH = tmp / "state.db"
    config.SOURCES_QUEUE_PATH = tmp / "sources_queue.txt"
    state.init(config.STATE_PATH)

    # ---- 1. matrix ----
    matrix = ke.keyword_matrix()
    assert len(ke.EXAMS) >= 60, len(ke.EXAMS)
    assert len(matrix) >= 800, len(matrix)
    kws = [e["kw"] for e in matrix]
    titles = [e["title"] for e in matrix]
    assert len(set(kws)) == len(kws), "duplicate kws"
    assert len(set(titles)) == len(titles), "duplicate titles"
    assert {e["cat"] for e in matrix} <= LIVE_CATS
    from datetime import date as _d
    y = str(_d.today().year)
    for e in matrix:
        assert e["exam"].lower().split()[0] in e["title"].lower(), e["title"]
        if e["intent"] != "previous papers":
            assert y in e["title"], e["title"]   # year-intent titles carry year
        else:
            assert y not in e["title"]          # previous papers = evergreen
    hot = [e for e in matrix if e["hot"]]
    assert len(hot) >= 240, len(hot)
    print(f"  1. keyword matrix ({len(matrix)} kws, {len(hot)} hot, cats valid) ✔")

    # ---- 2. autocomplete harvest ----
    good = json.dumps(["ssc cgl 2026", ["ssc cgl 2026 notification",
                                         "ssc cgl 2026 apply online",
                                         "ssc cgl 2026 hall ticket"]])

    class Resp:
        def __init__(self, text):
            self._t = text

        def json(self):
            return json.loads(self._t)

    real_requests = ke.requests
    ke.requests = types.SimpleNamespace(
        get=lambda url, params=None, timeout=None: Resp(good))
    try:
        out = ke.harvest_suggest("ssc cgl 2026")
        assert out == ["ssc cgl 2026 notification", "ssc cgl 2026 apply online",
                       "ssc cgl 2026 hall ticket"], out

        def boom(*a, **k):
            raise OSError("network down")

        ke.requests = types.SimpleNamespace(get=boom)
        assert ke.harvest_suggest("tspsc") == []
    finally:
        ke.requests = real_requests
    print("  2. autocomplete harvest (parse + failure-safe) ✔")

    # ---- 3. coverage word-boundary logic ----
    existing = [
        "SSC CGL 2026 Notification – Vacancies, Dates, Apply Online Telugu lo",
        "TSPSC Group 2 Syllabus 2026 – Complete Subject wise PDF Telugu lo",
        "IPL cricket highlights today",
    ]
    rep = ke.coverage_report(existing)
    assert rep["existing_posts"] == 3
    # SSC CGL title covers: notification + apply online + vacancies (3)
    # TSPSC G2 title covers: syllabus (1) — total 4; "date" NOT covered
    assert rep["covered"] == 4, rep
    m = {e["kw"]: e for e in matrix}
    assert ke.is_covered(m["ssc cgl 2026 notification"],
                         [ke._norm(existing[0])])
    assert not ke.is_covered(m["ssc cgl 2026 exam date"],
                             [ke._norm(existing[0])])
    gaps = ke.keyword_gaps(existing, limit=600)
    gapkws = {g["kw"] for g in gaps}
    assert "ssc cgl 2026 hall ticket" in gapkws            # uncovered -> gap
    assert "ssc cgl 2026 notification" not in gapkws       # covered -> excluded
    assert len(gaps) == 600, len(gaps)
    assert all(g["hot"] for g in gaps[:20]), "hot-first ordering"
    small = ke.keyword_gaps(existing, limit=10)
    assert len(small) == 10 and all(g["hot"] for g in small)
    print("  3. coverage/gap logic (word-boundary, hot-first) ✔")

    # ---- 4. daily harvest: queue + once/day guard + force ----
    def fake_harvest(seed, lang="te"):
        return [f"{seed.split()[0]} hall ticket download 2026 {lang}",
                "not edu random string zz"]

    real_harvest, real_seeds = ke.harvest_suggest, ke.suggest_seeds
    ke.harvest_suggest = fake_harvest
    ke.suggest_seeds = lambda: ["ssc cgl 2026 notification", "tspsc group 2 result"]
    try:
        r1 = ke.daily_keyword_harvest(max_queue=3, force=True)
        assert r1["queued"] == 3, r1
        tpath = news_radar.topics_queue_path()
        tlines = [l for l in tpath.read_text().splitlines() if l.strip()]
        assert len(tlines) >= 3, tlines
        # dedupe: second call same day -> guard skip
        r2 = ke.daily_keyword_harvest(max_queue=3)
        assert r2["queued"] == 0 and r2.get("skipped"), r2
        # force=True re-runs: suggest strings deduped (each appears once)
        r3 = ke.daily_keyword_harvest(max_queue=3, force=True)
        assert r3["queued"] <= 3, r3
        all_lines = tpath.read_text().splitlines()
        for dup in ("ssc hall ticket download 2026 te",
                    "ssc hall ticket download 2026 en",
                    "tspsc hall ticket download 2026 te"):
            assert all_lines.count(dup) <= 1, dup
    finally:
        ke.harvest_suggest = real_harvest
        ke.suggest_seeds = real_seeds
    print("  4. daily harvest (queue, guard, dedupe) ✔")

    # ---- 5. seeds ----
    seeds = ke.suggest_seeds()
    assert seeds and all("2026" in s for s in seeds), seeds[:3]
    print(f"  5. suggest seeds ({len(seeds)} seeds) ✔")

    # ---- 6. v16/v17 pools + rules ----
    from autoblog import topic_engine as te
    from autoblog import gemini_client

    assert len(te.VIRAL_LISTICLE_IDEAS) >= 18
    assert len(te.TIPS_IDEAS) >= 12
    orig_hc, orig_v, orig_t = (config.HIGH_CPC_SHARE,
                               config.VIRAL_LISTICLE_SHARE, config.TIPS_SHARE)
    try:
        config.HIGH_CPC_SHARE, config.VIRAL_LISTICLE_SHARE = 0, 100
        picks = {te.pick_listicle_idea() for _ in range(60)}
        assert picks and picks <= set(te.VIRAL_LISTICLE_IDEAS), picks
        config.VIRAL_LISTICLE_SHARE, config.TIPS_SHARE = 0, 100
        picks2 = {te.pick_listicle_idea() for _ in range(60)}
        assert picks2 and picks2 <= set(te.TIPS_IDEAS), picks2
    finally:
        config.HIGH_CPC_SHARE, config.VIRAL_LISTICLE_SHARE, config.TIPS_SHARE = \
            orig_hc, orig_v, orig_t
    wr = gemini_client.WRITING_RULES
    assert "NO-COPY RULE" in wr and "10X CONTENT STRATEGY" in wr
    assert "KEYWORD DOMINANCE" in wr
    print("  6. viral+tips pools + WRITING_RULES sections ✔")

    print("ALL v17 KEYWORD TESTS PASSED ✔")
    return 0


if __name__ == "__main__":
    sys.exit(main())
