# -*- coding: utf-8 -*-
"""v78 tests — TOP-BLOG PERFECTION PASS (fallbacks + neat look).

Enduku idi:
  Real probe lo dorikina NIJAMAINA gaps (dummy kaadu — pipeline ni nijamga
  nadipe chusamu): tables 0 · FAQ ledu · tags 3 passthrough · ORIG None ·
  theme lo su-lede/su-faq styles levu (live ugly!). v78 = deterministic
  fallbacks (LLM marchipoina kuda post perfect) + neat CSS.

Checks (offline only):
  * extract_facts: Telugu job HTML nunchi 7 facts (dates/fee/vacancies/age/qual/salary)
  * fix_table fallback: structured fields lekunna su-facts table guarantee
  * fix_faq fallback: faq=[] aina facts nunchi Q/A + su-faq wrapper; no-facts=honest skip
  * auto-tags: focus+secondary+category+acronyms merge; junk out; cap 8
  * _orig feed: _deep_sources nunchi kuda originality score (None kaadu)
  * RESEARCH_MAX_SOURCES default 5 (many sources)
  * para split: 100+ word paras ~70 chunks; short untouched
  * theme CSS: su-lede + su-faq cards + dark + zebra
  * end-to-end: table + faq + tags + TOP>=85 (thin input tho kuda)
  * docs: README v78 + MANUAL PART 37 + 71/71

Run: python tests/v78_test.py   (also via python run.py --test-all)
"""
from __future__ import annotations

import os
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from autoblog import config, pipeline, rm100, state  # noqa: E402
from autoblog.sources import SourceArticle  # noqa: E402

THEME = ROOT / "wordpress-theme" / "studentup"

BODY = ("<h2>TSPSC Group 2 — వివరాలు</h2><p>మొత్తం 500 ఖాళీలు ఉన్నాయి. "
        "దరఖాస్తు ఫీజు 350 రూపాయలు. వయోపరిమితి 18 నుండి 44 సంవత్సరాలు. "
        "డిగ్రీ ఉత్తీర్ణులై ఉండాలి. చివరి తేదీ నవంబర్ 4. "
        "పరీక్ష తేదీ డిసెంబర్ 20. వేతనం ₹40000 - ₹80000.</p>")

E2E_EXTRA = ("<h2>దరఖాస్తు విధానం TSPSC Group 2</h2><p>"
             "OTR రిజిస్ట్రేషన్ పూర్తి చేసి లాగిన్ అవ్వండి. ఫారం నింపి "
             "ఫీజు చెల్లించి సబ్‌మిట్ చేయండి. ప్రింట్ తీసుకోవడం మర్చిపోవద్దు. "
             "గడువు కంటే ముందే దరఖాస్తు చేయడం మంచిది.</p>"
             "<h2>ఎంపిక ప్రక్రియ TSPSC Group 2</h2><p>"
             "ఎంపిక రాత పరీక్ష ద్వారా జరుగుతుంది. అర్హత సాధించిన వారికి "
             "ధ్రువపత్రాల పరిశీలన ఉంటుంది. తుది ఎంపిక మెరిట్ ఆధారంగా. "
             "సిలబస్ మరియు పరీక్ష విధానం నోటిఫికేషన్‌లో చూడండి.</p>")


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


# ------------------------------------------------- 1-3. facts/table/faq

def test_extract_facts():
    facts = rm100.extract_facts(BODY)
    assert facts.get("last_date") == "నవంబర్ 4", facts
    assert facts.get("exam_date") == "డిసెంబర్ 20", facts
    assert facts.get("vacancies") == "500", facts
    assert "350" in facts.get("fee", ""), facts
    assert "18" in facts.get("age", "") and "44" in facts.get("age", ""), facts
    assert facts.get("qualification") == "డిగ్రీ", facts
    assert "40000" in facts.get("salary", ""), facts
    print(f"  extract_facts: 7/7 ({len(facts)} keys) ✔")


def test_table_fallback():
    art = {"title": "TSPSC Group 2 Notification 2026",
           "category": "State Govt Jobs", "focus_keyword": "TSPSC Group 2"}
    out = rm100.fix_table(art, BODY)
    assert 'class="su-facts"' in out, "table guarantee fail"
    assert out.count("<tr>") >= 5, out.count("<tr>")
    assert "నవంబర్ 4" in out and "500" in out
    print(f"  table fallback: {out.count('<tr>')} rows, no fields needed ✔")


def test_faq_fallback_and_honest_skip():
    art = {"title": "TSPSC Group 2", "focus_keyword": "TSPSC Group 2",
           "faq": []}
    out = rm100.fix_faq(art, BODY)
    assert 'class="su-faq"' in out, "faq wrapper ledu"
    assert out.count("<h3>") >= 3, out.count("<h3>")
    plain = "<p>Just a simple note about weather today nothing else here.</p>"
    assert rm100.fix_faq(art, plain) == plain, "no-facts = skip avvali"
    assert rm100.fix_table(art, plain) == plain, "no-facts table skip"
    print(f"  faq fallback: {out.count('<h3>')} Q/A + honest skip ✔")


# ------------------------------------------------- 4-5. tags + orig

def test_auto_tags_and_hygiene():
    art = {"title": "TSPSC Group 2 Notification 2026 — Apply Online",
           "category": "State Govt Jobs", "focus_keyword": "TSPSC Group 2",
           "secondary_keywords": ["group 2 syllabus", "tspsc hall tickets"],
           "tags": ["group2", "News"], "content_html": BODY,
           "quick_answer": "qa"}
    got = pipeline._hygiene(art)
    tags = got["tags"]
    assert "TSPSC Group 2" in tags, tags
    assert "State Govt Jobs" in tags, tags
    assert "TSPSC" in tags, tags
    assert not any(t.lower() == "news" for t in tags), tags
    assert 5 <= len(tags) <= 8, tags
    print(f"  auto-tags: {len(tags)} ({', '.join(tags[:4])}…) ✔")


class _FakeWP:
    def check_connection(self):
        return True

    def get_or_create_term(self, name, taxonomy):
        return 60 if taxonomy == "categories" else 9

    def get_recent_published(self, per_page=8):
        return []

    def get_term_link(self, term_id, taxonomy):
        return "https://studentup.in/c/"

    def upload_media(self, path, title="", alt_text="", filename="", **kw):
        return 88

    def create_post(self, **kwargs):
        return {"id": 1, "status": kwargs.get("status", "draft"),
                "link": "https://studentup.in/x/"}

    def update_post(self, post_id, **kwargs):
        return {"id": post_id, "status": "publish", "link": "https://x/"}

    def verify_meta(self, post_id, keys):
        return {k: True for k in keys}


def _publish(art: dict) -> dict:
    real_wp, real_state = pipeline.WordPressClient, config.STATE_PATH
    saved = (config.DEFAULT_POST_STATUS, config.EDITORIAL_REVIEWER,
             config.PUBLISH_QA_MIN_SCORE, config.PUBLISH_ORIGINALITY_MIN,
             config.TOP_POST_STRICT)
    with tempfile.TemporaryDirectory() as td:
        try:
            pipeline.WordPressClient = _FakeWP
            config.STATE_PATH = Path(td) / "s.db"
            state.init(config.STATE_PATH)
            config.DEFAULT_POST_STATUS = "draft"
            config.EDITORIAL_REVIEWER = ""
            config.PUBLISH_QA_MIN_SCORE = 0
            config.PUBLISH_ORIGINALITY_MIN = 0
            config.TOP_POST_STRICT = False
            res = pipeline.publish_article(art)
            assert res["status"] == "draft", res
            return art
        finally:
            pipeline.WordPressClient = real_wp
            config.STATE_PATH = real_state
            (config.DEFAULT_POST_STATUS, config.EDITORIAL_REVIEWER,
             config.PUBLISH_QA_MIN_SCORE, config.PUBLISH_ORIGINALITY_MIN,
             config.TOP_POST_STRICT) = saved


def test_orig_fed_from_deep_sources():
    donor = SourceArticle(url="http://127.0.0.1/d", title="D",
                          text="alpha beta gamma delta zeta " * 60)
    art = {"title": "Test orig feed guide", "slug": "v78-orig-1",
           "category": "Results", "focus_keyword": "orig feed test",
           "meta_description": "x" * 130, "tags": ["a"],
           "content_html": ("<h2>A</h2><p>" + "completely different words "
                            "about monsoon cricket cinema library " * 25
                            + "</p><h2>B</h2><p>" + "fresh unique sentences "
                            "hospital bank traffic museum " * 25 + "</p>"),
           "quick_answer": "qa", "faq": [], "external_links": [],
           "banner_text": "Test", "_deep_sources": [donor]}
    _publish(art)
    assert art.get("_orig") is not None, "_orig None (feed fail)"
    assert art["_originality"]["verdict"] == "fresh", art["_originality"]
    print(f"  _orig feed: {art['_orig']}% + {art['_originality']['verdict']} ✔")


# ------------------------------------------------- 6-8. depth + paras + css

def test_research_default_five():
    want = int(os.environ.get("RESEARCH_MAX_SOURCES", "5"))
    assert config.RESEARCH_MAX_SOURCES == want, config.RESEARCH_MAX_SOURCES
    print(f"  research depth: default {want} sources ✔")


def test_para_split():
    long_para = "<p>" + "మంచి వాక్యం ముగిసింది. " * 40 + "</p>"  # ~120 words
    out = rm100.fix_paragraph_len({}, long_para)
    assert out.count("<p") >= 2, "100+ para split avvaledu"
    for chunk in re.findall(r"<p[^>]*>(.*?)</p>", out, flags=re.S):
        assert len(chunk.split()) <= 100, len(chunk.split())
    short = "<p>Chinna para okate.</p>"
    assert rm100.fix_paragraph_len({}, short) == short
    print(f"  para split: 120w → {out.count('<p')} paras ✔")


def test_theme_neat_css():
    css = read(THEME / "style.css")
    for needle in (".su-lede{", ".su-faq h3{", ".su-faq h3+p{",
                   "body.dark .su-lede{", "body.dark .su-faq h3{",
                   "table.su-facts tr:nth-child(even)"):
        assert needle in css, f"CSS needle ledu: {needle}"
    print("  theme CSS: lede + faq cards + dark + zebra ✔")


# ------------------------------------------------- 9-10. e2e + docs

def test_end_to_end_perfection():
    donor = SourceArticle(url="https://tspsc.gov.in/n", title="N",
                          text="official notification text tspsc group vacancies " * 60)
    art = {"title": "TSPSC Group 2 Notification 2026 — 500 Posts, Apply Online",
           "slug": "v78-e2e-1", "category": "State Govt Jobs",
           "focus_keyword": "TSPSC Group 2",
           "meta_description": "TSPSC Group 2 notification 2026: 500 posts, "
           "fee, age, dates, apply online. Full details in Telugu here."[:160],
           "tags": ["tspsc"], "content_html": BODY + BODY + E2E_EXTRA,
           "quick_answer": "TSPSC Group 2 2026: 500 posts.",
           "faq": [], "external_links": [{"url": "https://tspsc.gov.in",
                                          "text": "TSPSC Official"}],
           "source_url": "https://tspsc.gov.in/notification",
           "secondary_keywords": ["group 2 syllabus", "tspsc hall tickets",
                                  "group 2 apply online"],
           "banner_text": "TSPSC Group 2", "_deep_sources": [donor]}
    _publish(art)
    html = art["content_html"]
    assert "<table" in html, "e2e table ledu"
    assert 'class="su-faq"' in html, "e2e faq ledu"
    assert len(art["tags"]) >= 4, art["tags"]
    assert art.get("_orig") is not None
    top = (art.get("_top") or {}).get("score", 0)
    assert top >= 85, f"TOP {top} < 85"
    print(f"  e2e: table + faq + {len(art['tags'])} tags + TOP {top} ✔")


def test_docs_v78():
    suites = len(list((ROOT / "tests").glob("*_test.py")))
    assert suites == 93, f"suites {suites} (v113 tho 93 expect)"
    readme = read(ROOT / "README.md")
    manual = read(ROOT / "MANUAL_ADVANCED_CHECKLIST.md")
    go_live = read(ROOT / "GO_LIVE_CHECKLIST.md")
    assert "### v78" in readme and "71/71" in readme
    assert "PART 37" in manual and "v78" in manual and "71/71" in manual
    assert "71/71" in go_live
    for name, txt in (("README", readme), ("MANUAL", manual),
                      ("GO_LIVE", go_live)):
        assert "164/164" in txt, f"{name} lo jsdom claim poyindi"
    print("  docs: README v78 + MANUAL PART 37 + 71/71 ✔")


TESTS = [
    ("extract_facts 7/7", test_extract_facts),
    ("table fallback", test_table_fallback),
    ("faq fallback + honest skip", test_faq_fallback_and_honest_skip),
    ("auto-tags + hygiene", test_auto_tags_and_hygiene),
    ("_orig feed", test_orig_fed_from_deep_sources),
    ("research default 5", test_research_default_five),
    ("para split", test_para_split),
    ("theme neat CSS", test_theme_neat_css),
    ("end-to-end perfection", test_end_to_end_perfection),
    ("docs: v78 + PART 37 + 71/71", test_docs_v78),
]


def main() -> None:
    print("=" * 70)
    print("  v78 — TOP-BLOG PERFECTION PASS (fallbacks + neat look)")
    print("=" * 70)
    failed = 0
    for name, fn in TESTS:
        try:
            fn()  # fns print their own proof line on success
        except AssertionError as exc:
            failed += 1
            print(f"  {name} ✘  {exc}")
        except Exception as exc:  # noqa: BLE001
            failed += 1
            print(f"  {name} ✘  {type(exc).__name__}: {exc}")
    print("-" * 70)
    if failed:
        print(f"  {failed} TEST(S) FAILED ✘")
        raise SystemExit(1)
    print("ALL v78 PERFECTION TESTS PASSED ✔")


if __name__ == "__main__":
    main()
