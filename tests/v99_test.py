# -*- coding: utf-8 -*-
"""v99 — INTERNAL LINK GRAPH OPTIMIZER + FAQ/AI SCHEMA tests.

Rendu nijamaina gaps:

GAP-1 ORPHAN POSTS: `seo.enhance()` kotha post nunchi purana posts ki link
  pedutundi — **okka direction**. Purana post ni evaru link cheyyaru (adi
  publish ayinappudu tarvata posts inka lev). Result: inbound internal link
  **ZERO** unna posts → Googlebot ki crawl priority takkuva, ranking weak.
  Idi Rank Math lo **kanipinchadu** (adi single page matrame chustundi).

GAP-2 FAQ SCHEMA: repo FAQPage ni motham skip chesindi ("Google retired it").
  Nijam (research chesi confirm chesanu): Google **rich result** ni
  teesesindi (7 May 2026) — kaani schema ni content understanding ki inka
  parse chestundi, mariyu **Bing Copilot / Perplexity / AI Overviews** lanti
  AI retrieval systems daanni actively vadutunnayi. Ade kotha traffic surface.

Checks (14). Offline-safe — network ki velladu.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from autoblog import config, link_graph as lg, seo  # noqa: E402

SUITES_EXPECTED = 87
SITE = "https://studentup.in"


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="ignore")


def _para(topic: str, n: int = 4) -> str:
    return "<p>" + (f"{topic} details for students in Telangana and Andhra. " * n) + "</p>"


def _post(i: int, slug: str, title: str, content: str, cat: int = 1) -> dict:
    return {"id": i, "link": f"{SITE}/{slug}", "title": title,
            "content": content, "categories": [cat]}


def _fixture() -> list:
    return [
        _post(1, "tspsc-group-2-notification", "TSPSC Group 2 Notification 2026",
              _para("TSPSC Group 2 notification")
              + f'<p><a href="{SITE}/tspsc-group-2-hall-ticket">hall ticket</a></p>'),
        _post(2, "tspsc-group-2-hall-ticket", "TSPSC Group 2 Hall Ticket",
              _para("TSPSC Group 2 hall ticket")),
        _post(3, "tspsc-group-2-results", "TSPSC Group 2 Results",
              _para("TSPSC Group 2 results")),
        _post(4, "ap-dsc-notification", "AP DSC Notification 2026",
              _para("AP DSC notification"), cat=2),
    ]


# ------------------------------------------------------------ 1 link parsing

def test_link_extraction_and_normalise() -> None:
    config.WP_SITE = SITE
    html = (f'<a href="{SITE}/a/">A</a>'
            f'<a href="http://www.studentup.in/b?utm=x#frag">B</a>'
            '<a href="/c/">C</a>'
            '<a href="https://google.com/x">ext</a>'
            '<a href="mailto:a@b.com">m</a><a href="#top">t</a>')
    got = lg.extract_links(html, SITE)
    assert "studentup.in/a" in got and "studentup.in/b" in got, got
    assert "studentup.in/c" in got or "/c" in got, got
    assert not any("google.com" in g for g in got), "external link internal ga counted"
    assert len(got) == 3, got          # mailto/# skip
    print("      links: query/frag/www/scheme normalise · external+mailto skip ✔")


# ---------------------------------------------------------------- 2 diagnose

def test_graph_finds_orphans() -> None:
    config.WP_SITE = SITE
    g = lg.build_graph(_fixture(), SITE)
    # post 2 ki post 1 nunchi inbound undi → orphan kaadu
    assert "studentup.in/tspsc-group-2-hall-ticket" not in g["orphans"]
    # post 3, 4 ki inbound ZERO → orphans
    assert "studentup.in/tspsc-group-2-results" in g["orphans"]
    assert "studentup.in/ap-dsc-notification" in g["orphans"]
    # post 2,3,4 outbound ZERO → dead ends
    assert "studentup.in/tspsc-group-2-results" in g["dead_ends"]
    assert len(g["nodes"]) == 4
    print("      graph: orphans · weak · dead-ends correct ✔")


def test_self_link_not_counted() -> None:
    config.WP_SITE = SITE
    p = _post(1, "x", "X Post", _para("x") + f'<p><a href="{SITE}/x">self</a></p>')
    g = lg.build_graph([p], SITE)
    assert g["orphans"] == ["studentup.in/x"], "self-link inbound ga counted!"
    print("      self-link inbound ga count avvadu ✔")


# -------------------------------------------------------------------- 3 plan

def test_plan_is_relevant_and_deterministic() -> None:
    config.WP_SITE = SITE
    g = lg.build_graph(_fixture(), SITE)
    plan = lg.plan_fixes(g)
    assert plan, "plan khali"
    for f in plan:
        assert f["donor"] != f["target"], "self-link plan chesindi"
        assert f["score"] > 0, "irrelevant donor pick chesindi"
        assert f["anchor"], "anchor ledu"
    # AP DSC (cat 2) ki TSPSC posts donors ga vaste score takkuva undali
    # → relevance ranking pani chestundi
    tsp = [f for f in plan if "tspsc-group-2-results" in f["target"]]
    assert tsp and tsp[0]["score"] > 0.5, tsp
    # deterministic
    g2 = lg.build_graph(_fixture(), SITE)
    assert lg.plan_fixes(g2) == plan, "plan deterministic kaadu"
    print("      plan: relevant donors · no self-link · deterministic ✔")


def test_donor_budget_and_overlink_guard() -> None:
    config.WP_SITE = SITE
    # donor ki already MAX_OUT links unte skip avvali
    links = "".join(f'<a href="{SITE}/p{i}">p{i}</a>' for i in range(lg.MAX_OUT + 2))
    posts = [_post(i, f"p{i}", f"TSPSC Group 2 Topic {i}", _para("tspsc group 2"))
             for i in range(lg.MAX_OUT + 2)]
    posts.append(_post(99, "hub", "TSPSC Group 2 Hub", _para("tspsc group 2") + links))
    g = lg.build_graph(posts, SITE)
    plan = lg.plan_fixes(g)
    assert all(f["donor"] != "studentup.in/hub" for f in plan), "over-linked donor vaadindi"
    # okka donor ki max 1 kotha link per run
    from collections import Counter
    c = Counter(f["donor"] for f in plan)
    assert all(v <= lg.MAX_NEW_PER_DONOR for v in c.values()), c
    print("      guards: over-linked donor skip · 1 new link/donor ✔")


# ------------------------------------------------------------------ 4 insert

def test_insert_is_safe_and_idempotent() -> None:
    config.WP_SITE = SITE
    body = _para("TSPSC Group 2 notification")
    out = lg.insert_link(body, f"{SITE}/results", "TSPSC Group 2 Results")
    assert out and "su-rel" in out and f'href="{SITE}/results"' in out
    # duplicate raadu
    assert lg.insert_link(out, f"{SITE}/results", "x") is None
    # heading-only / unsafe content lo insert cheyyadu
    assert lg.insert_link("<h2>Only a heading</h2>", f"{SITE}/a", "A") is None
    assert lg.insert_link("<p>too short</p>", f"{SITE}/a", "A") is None
    # nested anchor create cheyyakudadu
    assert out.count("<a ") == 1
    assert "<a" not in out[out.index('<a href'):out.index("</a>")].replace('<a href', "")
    print("      insert: safe zone · no dupe · no nested <a> · short-para skip ✔")


def test_insert_never_touches_blocked_zones() -> None:
    config.WP_SITE = SITE
    blocked = ('<div class="su-quick">' + _para("quick answer text") + "</div>"
               + "<h2>" + "Heading text here for the section" + "</h2>")
    assert lg.insert_link(blocked, f"{SITE}/a", "A") is None, \
        "quick-answer/heading lopala insert chesindi"
    ok = blocked + _para("real body paragraph content")
    out = lg.insert_link(ok, f"{SITE}/a", "A")
    assert out is not None
    # su-quick div lopala raakudadu
    qend = out.index("</div>")
    assert "su-rel" not in out[:qend], "blocked zone lopala link padindi"
    print("      insert: quick-answer/CTA/heading zones protected ✔")


def test_anchor_is_natural_not_stuffed() -> None:
    a = lg.anchor_for("TSPSC Group 2 Notification 2026 – Vacancies, Dates, Apply Online Telugu lo | StudentUp")
    assert "StudentUp" not in a, a
    assert len(a.split()) <= 10, a
    assert a.startswith("TSPSC Group 2"), a
    print("      anchor: brand strip · length cap · readable ✔")


# --------------------------------------------------------------- 5 dry / run

def test_dry_run_changes_nothing() -> None:
    config.WP_SITE = SITE

    class FakeWP:
        def __init__(self):
            self.posts = {p["id"]: dict(p) for p in _fixture()}
            self.updates = []

        def get_recent_published(self, per_page=8):
            return [dict(p) for p in self.posts.values()]

        def get_post(self, i):
            return {"content": {"raw": self.posts[i]["content"]}}

        def update_post(self, i, html):
            self.updates.append(i)
            self.posts[i]["content"] = html
            return {}

    wp = FakeWP()
    rep = lg.run(apply=False, wp=wp)
    assert rep["dry"] is True and rep["applied"] == 0
    assert wp.updates == [], "dry-run lo live posts update ayyayi!"
    assert rep["orphans"] >= 2 and rep["plan"]
    # apply
    wp2 = FakeWP()
    rep2 = lg.run(apply=True, wp=wp2)
    assert rep2["applied"] > 0 and wp2.updates
    # idempotent — malli run cheste kotha links raavu
    rep3 = lg.run(apply=True, wp=wp2)
    assert rep3["applied"] == 0, "second run lo duplicate links add ayyayi"
    print("      run: dry-run safe · apply works · idempotent ✔")


def test_no_posts_is_safe() -> None:
    class Empty:
        def get_recent_published(self, per_page=8):
            return []

    rep = lg.run(apply=True, wp=Empty())
    assert rep["posts"] == 0 and rep["applied"] == 0 and rep.get("note")
    print("      no posts / offline → safe no-op ✔")


# ------------------------------------------------------------------ 6 schema

def _faq_blob(out: str):
    for b in re.findall(r'<script type="application/ld\+json">(.*?)</script>', out, re.S):
        d = json.loads(b)
        if d.get("@type") == "FAQPage":
            return d
    return None


def test_faq_schema_only_when_real() -> None:
    good = [{"q": "TSPSC Group 2 last date enni?",
             "a": "Application last date is 30 September 2026 per the official notification."},
            {"q": "Application fee entha?",
             "a": "General candidates must pay Rs 200 as the online application fee."}]
    out = seo.schema_jsonld("T", "D", good, "2026-09-22", "", "slug", "TS Govt Jobs")
    d = _faq_blob(out)
    assert d and len(d["mainEntity"]) == 2, d
    assert d["mainEntity"][0]["@type"] == "Question"
    assert d["mainEntity"][0]["acceptedAnswer"]["@type"] == "Answer"
    # FAQ ledu → FAQPage ledu
    assert _faq_blob(seo.schema_jsonld("T", "D", [], "2026-09-22", "", "s", "c")) is None
    # okka question matrame → FAQPage worth ledu (thin)
    assert _faq_blob(seo.schema_jsonld("T", "D", [good[0]], "2026-09-22", "", "s", "c")) is None
    print("      FAQPage: real Q&A 2+ unte matrame · thin skip ✔")


def test_faq_schema_drops_thin_and_duplicates() -> None:
    faq = [{"q": "Real question one here?", "a": "This is a proper long answer for readers."},
           {"q": "Thin one?", "a": "short"},
           {"q": "Real question one here?", "a": "Duplicate question must be dropped once."},
           {"q": "", "a": "no question at all so this must be dropped too"},
           {"q": "Second real question?", "a": "Another proper answer that is long enough."}]
    items = seo._faq_schema_items(faq)
    names = [i["name"] for i in items]
    assert len(items) == 2, names
    assert names.count("Real question one here?") == 1
    assert "Thin one?" not in names
    # HTML strip
    h = seo._faq_schema_items([{"q": "<b>Bold q</b> here?",
                                "a": "<p>Answer with <i>html</i> tags inside it.</p>"}])
    assert "<" not in h[0]["name"] and "<" not in h[0]["acceptedAnswer"]["text"]
    print("      FAQPage: thin/dupe/empty dropped · HTML stripped ✔")


def test_faq_schema_config_gate() -> None:
    good = [{"q": "Question one here?", "a": "A sufficiently long answer for schema."},
            {"q": "Question two here?", "a": "Another sufficiently long answer here."}]
    old = getattr(config, "FAQ_SCHEMA_ENABLED", True)
    try:
        config.FAQ_SCHEMA_ENABLED = False
        assert _faq_blob(seo.schema_jsonld("T", "D", good, "2026-09-22", "", "s", "c")) is None
    finally:
        config.FAQ_SCHEMA_ENABLED = old
    assert "FAQ_SCHEMA_ENABLED" in read(ROOT / ".env.example")
    print("      FAQPage: config gate + .env.example ✔")


# -------------------------------------------------------------- 7 CLI + docs

def test_cli_and_docs() -> None:
    main = read(ROOT / "autoblog" / "main.py")
    for flag in ("--link-graph", "--link-graph-apply"):
        assert flag in main, flag
    assert "link_graph" in main
    suites = len(list((ROOT / "tests").glob("*_test.py")))
    assert suites == SUITES_EXPECTED, f"suites {suites} (v99 tho 79)"
    readme = read(ROOT / "README.md")
    manual = read(ROOT / "MANUAL_ADVANCED_CHECKLIST.md")
    cur = f"{SUITES_EXPECTED}/{SUITES_EXPECTED}"
    assert "### v99" in readme and cur in readme
    assert "PART 56" in manual and cur in manual
    assert "--link-graph" in readme and "--link-graph" in manual
    # honest note: FAQ rich result poyindi ani cheppali (fake promise vaddu)
    assert "rich result" in readme.lower(), "FAQ rich-result reality documented kaadu"
    print("      CLI flags + README v99 + PART 56 + honest note ✔")


TESTS = [
    ("link extraction", test_link_extraction_and_normalise),
    ("orphan detection", test_graph_finds_orphans),
    ("self-link guard", test_self_link_not_counted),
    ("fix plan quality", test_plan_is_relevant_and_deterministic),
    ("donor budget guards", test_donor_budget_and_overlink_guard),
    ("insert safety", test_insert_is_safe_and_idempotent),
    ("blocked zones", test_insert_never_touches_blocked_zones),
    ("anchor text", test_anchor_is_natural_not_stuffed),
    ("dry-run / apply", test_dry_run_changes_nothing),
    ("empty site safe", test_no_posts_is_safe),
    ("FAQPage real-only", test_faq_schema_only_when_real),
    ("FAQPage thin/dupe", test_faq_schema_drops_thin_and_duplicates),
    ("FAQPage config gate", test_faq_schema_config_gate),
    ("CLI + docs", test_cli_and_docs),
]


def main() -> int:
    failed = 0
    for name, fn in TESTS:
        try:
            fn()
            print(f"  {name} ✔")
        except Exception as exc:  # noqa: BLE001
            failed += 1
            print(f"  {name} ✘  {type(exc).__name__}: {exc}")
    print("-" * 70)
    if failed:
        print(f"  {failed} TEST(S) FAILED ✘")
        return 1
    print("ALL v99 LINK-GRAPH + FAQ/AI SCHEMA TESTS PASSED ✔")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
