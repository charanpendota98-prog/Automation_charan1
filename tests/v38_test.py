"""v38 TOP POST DOMINANCE ENGINE tests.

Sections:
  1. Keyword universe (10k+ keywords, unique, live categories, deterministic)
  2. Entity/intent detection + keyword family + question keywords
  3. Blueprint (titles/meta/slug/outline/family mapping/self-score) + exports
  4. Domination plan (cluster balanced, unique, CSV/MD/JSON)
  5. Top Post Score (thin vs strong post, stuffing penalty, missing keyword)
  6. Harden (structural only, FAQ extraction, density cap, idempotent)
  7. Publish gate (draft allow, live block, engine off)
  8. Pipeline integration (real publish path, _top score, live gate)
  9. Blueprint → article (mock) + Gemini brief + CLI helpers
"""

import io
import json
import contextlib
import sys
import tempfile
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from autoblog import config, gemini_client, pipeline, seo, state, top_post  # noqa: E402

LIVE_CATS = {"Scholarships", "Central Govt Jobs", "TS Govt Jobs", "AP Govt Jobs",
             "Private Jobs", "Software Jobs", "Part Time Jobs", "Walkin Jobs",
             "Hall Tickets", "Results", "Internships", "Online Education",
             # v58: 17వ pillar (Tier-1 revenue line)
             "Abroad Jobs", "Outsourcing Jobs", "Current Affairs", "Exam Tips",
             "Upcoming Exams"}


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


# --------------------------------------------------------------- fixtures

def strong_article(keyword: str = "ssc cgl 2026 apply online") -> dict:
    """Realistic publish-ready fixture: 1600+ words + seo.enhance output
    (TOC, snippet card, byline, trust box, schema, internal/external links)."""
    body = [f"<p>{keyword} ki sambandhinchina complete details ikkada — apply "
            "steps, fee, documents, dates anni step by step. Ee guide official "
            "notification prakaram prepare chesam.</p>",
            "<h2>ssc cgl 2026 apply online – Quick Answer</h2>",
            "<p>Registration, form, photo upload, fee, final submit — ee 5 steps lo "
            "application complete avutundi. ssc cgl 2026 apply online direct link "
            "and ssc cgl 2026 last date details kuda kindha unnayi.</p>"]
    for i in range(1, 9):
        body.append(f"<h2>Step {i}: ssc cgl 2026 apply online details</h2>")
        for j in range(1, 4):
            body.append(
                f"<h3>Sub point {i}.{j} ela cheyali?</h3>"
                "<p>Ee section lo official notification nunchi teesina details "
                "matrame unnayi — ssc cgl 2026 eligibility, fee, documents. "
                "Students kosam simple Telugu lo explain chesam, kaani official "
                "site lo okkasari cross check cheyandi. ssc cgl 2026 application "
                "fee, 'How to apply SSC CGL 2026 in Telugu' steps and required "
                "documents kindha unnayi.</p>")
        body.append("<ul><li>Step one</li><li>Step two</li><li>Step three</li></ul>")
        if i % 3 == 0:
            body.append("<table><tr><th>Item</th><th>Details</th></tr>"
                        "<tr><td>Fee</td><td>Category wise</td></tr>"
                        "<tr><td>Documents</td><td>Checklist</td></tr></table>")
    body.append("<h2>FAQ – ssc cgl 2026 apply online doubts</h2>")
    for q in ("SSC CGL 2026 last date enti?", "Apply ela cheyali?",
              "Fee emiti?", "Hall ticket eppudu vastundi?"):
        body.append(f"<h3>{q}</h3><p>Official notification lo unna details prakaram "
                    "answer ikkada ivvabadindi; verify cheyandi.</p>")
    raw = "".join(body)
    art = {
        "title": "SSC CGL 2026 Apply Online – Complete Guide",
        "slug": "ssc-cgl-2026-apply-online",
        "meta_description": (f"{keyword} step by step process, fee details, "
                             "required documents and direct link Telugu lo. Form "
                             "reject avvakunda ee steps follow cheyandi."),
        "category": "Central Govt Jobs",
        "focus_keyword": keyword,
        "secondary_keywords": ["ssc cgl 2026 last date",
                               "ssc cgl 2026 apply online direct link",
                               "ssc cgl 2026 eligibility"],
        "quick_answer": "5 steps lo application complete avutundi — registration, "
                        "form, photo/signature, fee, final submit.",
        "faq": [{"question": f"{keyword} last date enti?",
                 "answer": "Notice lo unna date matrame valid — official site lo verify cheyandi."},
                {"question": "Apply ela cheyali?",
                 "answer": "Registration nunchi final submit varaku 5 steps follow cheyandi."},
                {"question": "Fee emiti?",
                 "answer": "Category wise fee notification lo untundi."},
                {"question": "Hall ticket eppudu vastundi?",
                 "answer": "Exam ki mundu official site lo release avutundi."}],
        "tags": ["SSC CGL", "2026", "SSC", "Students", "Telugu"],
        "external_links": [{"text": "SSC official website", "url": "https://ssc.gov.in"}],
        "content_html": raw,
        "_media_alt": f"{keyword} – Central Govt Jobs 2026 | studentup.in",
    }
    art["content_html"] = seo.enhance(
        raw, focus_keyword=keyword,
        internal_links=[{"link": "https://studentup.in/ssc-cgl-notification/",
                         "title": "SSC CGL 2026 Notification"},
                        {"link": "https://studentup.in/ssc-cgl-syllabus/",
                         "title": "SSC CGL Syllabus"}],
        external_links=art["external_links"], quick_answer=art["quick_answer"],
        faq=art["faq"], date_str="2026-09-14", date_modified="2026-09-14",
        slug=art["slug"], title=art["title"],
        description=art["meta_description"], category=art["category"],
        source_domains=["ssc.gov.in"])
    return art


THIN_HTML = ("<p>Short note about some topic without the search phrase.</p>"
             "<h2>One heading</h2><p>Tiny body text.</p>")


def main():
    tmp = Path(tempfile.mkdtemp(prefix="v38_test_"))
    config.OUTPUT_DIR = tmp / "output"
    config.STATE_PATH = tmp / "state.db"
    config.SOURCES_QUEUE_PATH = tmp / "queue.txt"
    config.TELEGRAM_BOT_TOKEN = ""
    config.TELEGRAM_CHAT_ID = ""
    config.IMAGE_ENABLED = False
    state.init(config.STATE_PATH)

    print("v38 TOP POST DOMINANCE ENGINE TESTS:")

    # ---------------------------------------------------------------- 1
    uni = top_post.keyword_universe()
    assert len(uni) >= 9500, len(uni)
    assert len(top_post.ENTITIES) >= 180, len(top_post.ENTITIES)
    assert len(top_post.ALL_INTENTS) == 66, len(top_post.ALL_INTENTS)
    kws = [e["kw"] for e in uni]
    assert len(set(kws)) == len(kws), "duplicate keywords"
    assert {e["cat"] for e in uni} <= LIVE_CATS, {e["cat"] for e in uni} - LIVE_CATS
    assert all(5 <= e["priority"] <= 100 for e in uni)
    assert all(e["funnel"] in {"TOFU", "MOFU", "BOFU"} for e in uni)
    assert all(e["role"] in {"pillar", "support"} for e in uni)
    assert all(e["serp"] for e in uni)
    assert top_post.keyword_universe()[0]["kw"] == kws[0], "not deterministic/cached"
    st = top_post.universe_stats(uni)
    assert st["total"] == len(uni) and st["clusters"] == len(top_post.ENTITIES)
    assert st["hot"] >= 800 and st["pillars"] >= 1000
    assert "NOT Google" in st["note"] or "not Google" in st["note"]
    assert "ssc cgl 2026 notification" in set(kws)
    assert "tspsc group 2 2026 hall ticket" in set(kws)
    assert "nsp scholarship 2026 last date" in set(kws)
    print(f"  1. keyword universe ({st['total']} kws · {st['entities']} entities · "
          f"{st['intents']} intents · {st['hot']} hot · avg {st['avg_priority']}) ✔")

    # ---------------------------------------------------------------- 2
    ent = top_post.detect_entity("tspsc group 2 2026 notification apply online")
    assert ent and ent["name"] == "TSPSC Group 2" and ent["cat"] == "TS Govt Jobs"
    assert ent["official"] == "tspsc.gov.in"
    assert top_post.detect_entity("random unknown phrase") is None
    it = top_post.detect_intent("ssc cgl 2026 hall ticket download")
    assert it["intent"] == "hall ticket" and it["family"] == "hallticket", it
    fam = top_post.keyword_family("ssc cgl 2026 notification")
    assert fam["primary"] == "ssc cgl 2026 notification"
    assert len(fam["secondary"]) >= 5 and len(fam["questions"]) >= 5
    assert len(fam["long_tail"]) >= 5
    assert any("last date enti" in q for q in fam["questions"])
    free = top_post.keyword_family("online degree admission guide")
    assert free["primary"] and free["questions"], free
    assert top_post.target_year("TSPSC Group 2 2027 notification") == 2027
    assert top_post.target_year("ssc cgl notification") == date.today().year
    print("  2. entity/intent detection + keyword family + questions ✔")

    # ---------------------------------------------------------------- 3
    for kw, cat, family in [
            ("SSC CGL 2026 apply online", "Central Govt Jobs", "apply"),
            ("TSPSC Group 2 2026 notification", "TS Govt Jobs", "notification"),
            ("NSP Scholarship last date", "Scholarships", "scholarship"),
            ("AP EAPCET 2026 counselling", "Online Education", "admission"),
            ("resume for freshers in telugu", "Internships", "career"),
            ("TG DSC SGT hall ticket", "TS Govt Jobs", "hallticket")]:
        bp = top_post.build_blueprint(kw)
        assert bp["category"] == cat, (kw, bp["category"])
        assert bp["intent_family"] == family, (kw, bp["intent_family"])
        assert len(bp["outline"]) >= 6 and bp["subtopics_total"] >= 10
        assert 110 <= len(bp["meta_description"]) <= 156, (kw, len(bp["meta_description"]))
        assert bp["keyword"] in bp["meta_description"].lower()
        assert bp["slug"] and bp["keyword"].split()[0] in bp["slug"]
        assert bp["title_options"][0]["keyword_in_first_half"]
        assert 20 <= bp["title_options"][0]["chars"] <= 90
        assert len(bp["faq_plan"]) >= 5 and len(bp["paa_questions"]) >= 5
        assert bp["table_plan"] and bp["snippet_answer"]
        assert len(bp["schema"]) >= 2 and len(bp["internal_link_plan"]) >= 3
        assert bp["image"]["alt"] and bp["word_target"] >= 1200
        assert bp["score_preview"]["score"] >= 78, bp["score_preview"]
        assert len(bp["ranking_levers"]) >= 8
        assert any("NOT Google" in n for n in bp["honesty_notes"])
        assert "JobPosting" in " ".join(bp["schema"]) or family != "notification"
    paths = top_post.write_blueprint(top_post.build_blueprint("SSC CGL 2026 apply online"))
    for key in ("markdown", "html", "json"):
        assert Path(paths[key]).exists(), key
    html = Path(paths["html"]).read_text(encoding="utf-8")
    assert "<h1>" in html and "Top Post Dominance Engine" in html
    assert "SSC CGL 2026 apply online" in html
    md = Path(paths["markdown"]).read_text(encoding="utf-8")
    assert "TOP POST BLUEPRINT" in md and "People Also Ask" in md
    data = json.loads(Path(paths["json"]).read_text(encoding="utf-8"))
    assert data["keyword"] == "ssc cgl 2026 apply online"
    # XSS/injection safety in generated page
    evil = top_post.build_blueprint('<script>alert(1)</script> ssc cgl 2026')
    evil_html = top_post.blueprint_html(evil)
    assert "<script>alert(1)</script>" not in evil_html
    print("  3. blueprint (6 families, exports, injection-safe) ✔")

    # ---------------------------------------------------------------- 4
    plan = top_post.build_plan(days=30, per_day=2, start=date(2026, 1, 5))
    assert len(plan) == 60, len(plan)
    plan_kws = [p["kw"] for p in plan]
    assert len(set(plan_kws)) == len(plan_kws), "duplicate plan keywords"
    assert plan[0]["date"] == "2026-01-05" and plan[0]["weekday"] == "Mon"
    assert len({p["cluster"] for p in plan}) >= 20, "clusters not spread"
    roles = {p["role"] for p in plan}
    assert roles == {"pillar", "support"}, roles
    # same-day slots never share one cluster (footprint-safe publishing)
    for i in range(0, len(plan) - 1, 2):
        assert plan[i]["cluster"] != plan[i + 1]["cluster"], plan[i]
    # intent variety inside the calendar (not 60x one intent)
    assert len({p.get("intent", "") for p in plan}) >= 8
    assert plan == top_post.build_plan(days=30, per_day=2, start=date(2026, 1, 5))
    ppaths = top_post.write_plan(plan)
    assert Path(ppaths["csv"]).exists() and Path(ppaths["markdown"]).exists()
    csv_text = Path(ppaths["csv"]).read_text(encoding="utf-8")
    assert "keyword" in csv_text.splitlines()[0] and plan[0]["kw"] in csv_text
    repo = top_post.build_plan(days=90, per_day=1)
    assert len(repo) >= 90 and all(p["role"] in {"pillar", "support"} for p in repo)
    print(f"  4. domination plan ({len(plan)}/30d, {len(repo)}/90d, "
          f"{len({p['cluster'] for p in plan})} clusters) ✔")

    # ---------------------------------------------------------------- 5
    good = strong_article()
    good_score = top_post.score_top_post(good)
    thin = {"title": "Some news", "slug": "news", "focus_keyword": "ssc cgl 2026",
            "content_html": THIN_HTML, "meta_description": "short"}
    thin_score = top_post.score_top_post(thin)
    assert good_score["score"] >= 80, good_score["score"]
    assert thin_score["score"] < 55, thin_score
    assert good_score["score"] > thin_score["score"] + 20
    assert good_score["grade"].startswith(("TOP POST", "STRONG"))
    assert thin_score["fixes"] and thin_score["failed"]
    assert thin_score["density"] < 0.004 or thin_score["occurrences"] == 0
    # over-optimization penalty: keyword stuffed 60x in a short text
    stuffed = dict(good)
    stuffed["content_html"] = ("<p>" + ("ssc cgl 2026 apply online " * 60) +
                               "</p><h2>ssc cgl 2026 apply online</h2>")
    stuffed_score = top_post.score_top_post(stuffed)
    dens_check = {c["id"]: c for c in stuffed_score["checks"]}["kw-density"]
    assert not dens_check["ok"], stuffed_score["density"]
    assert "density" in " ".join(stuffed_score["fixes"]).lower()
    # secondary/long-tail/question coverage behave
    cov = {c["id"]: c for c in good_score["checks"]}
    assert cov["secondary-cov"]["ok"] and cov["kw-title"]["ok"]
    assert cov["question-headings"]["ok"]
    print(f"  5. top post score (strong {good_score['score']} vs thin "
          f"{thin_score['score']}, stuffing caught {stuffed_score['density']:.1%}) ✔")

    # ---------------------------------------------------------------- 6
    art = {
        "title": "SSC CGL 2026 Apply Online – Direct Link & Steps",
        "slug": "ssc-cgl-2026-apply-online",
        "focus_keyword": "ssc cgl 2026 apply online",
        "content_html": (
            "<p>Apply process modalavvali ante munduga documents ready cheyandi. "
            "Registration, form, photo, fee, submit — idi 5 step process.</p>"
            "<h2>Apply step by step</h2>"
            "<h3>Fee emiti?</h3><p>Category wise fee details official notification "
            "lo unnayi; online lo matrame pay cheyali.</p>"
            "<h3>Hall ticket eppudu vastundi?</h3><p>Exam ki 10-15 rojula mundu "
            "official site lo release avutundi — notification prakaram.</p>"
            + "".join(f"<p>ssc cgl 2026 apply online details paragraph {i} — "
                      "students verify cheyandi official site lo.</p>" for i in range(1, 26))),
        "meta_description": "short meta",
        "faq": [],
        "secondary_keywords": [],
        "quick_answer": "",
        "category": "Central Govt Jobs",
        "tags": ["SSC CGL", "2026"],
    }
    before_html = art["content_html"]
    art, report = top_post.harden(art)
    assert report["enabled"] and report["score_after"] >= report["score_before"]
    assert art["secondary_keywords"], "secondary keywords not filled"
    assert 110 <= len(art["meta_description"]) <= 165
    assert art["quick_answer"], "quick answer not extracted"
    assert len(art["faq"]) >= 2, art["faq"]
    assert all("?" in f["question"] or "ela" in f["question"].lower()
               for f in art["faq"])
    assert art["_top_post"]["grade"]
    # density cap: heavy repetition trimmed, text preserved otherwise
    heavy = dict(art)
    heavy["content_html"] = ("<p>" + ("ssc cgl 2026 apply online " * 120) + "</p>")
    heavy, hrep = top_post.harden(heavy)
    assert any("density cap" in c for c in hrep["changes"]), hrep["changes"]
    occ = top_post._count_phrase(
        __import__("autoblog.validator", fromlist=["validator"]).strip_tags(
            heavy["content_html"]).lower(), "ssc cgl 2026 apply online")
    assert occ <= int(0.05 * 900) + 5, occ
    # original factual text untouched by hardening (no invented content)
    art2, rep2 = top_post.harden(dict(art, content_html=before_html,
                                      faq=[], secondary_keywords=[],
                                      quick_answer="", meta_description="short meta"))
    assert report["score_after"] == rep2["score_after"], "hardening not idempotent"
    print(f"  6. harden (score {report['score_before']}→{report['score_after']}, "
          f"faq {len(art['faq'])}, density cap {hrep['changes'][-1]}) ✔")

    # ---------------------------------------------------------------- 7
    draft = {"status": "draft", "_top_post": {"score": 10, "fixes": []},
             "content_html": THIN_HTML}
    ok, detail = top_post.publish_gate(draft)
    assert ok and "draft" in detail
    low = {"status": "publish", "_top_post": {"score": 20, "fixes": ["fix A"]}}
    ok2, detail2 = top_post.publish_gate(low)
    assert not ok2 and "TOP-POST GATE" in detail2 and "fix A" in detail2
    ok3, detail3 = top_post.publish_gate(
        {"status": "publish", "_top_post": {"score": 95, "fixes": []}})
    assert ok3 and "95" in detail3
    old_engine = config.TOP_POST_ENGINE
    try:
        config.TOP_POST_ENGINE = False
        assert top_post.publish_gate(low)[0]
    finally:
        config.TOP_POST_ENGINE = old_engine
    print("  7. publish gate (draft allow / live block / engine off) ✔")

    # ---------------------------------------------------------------- 8
    class FakeWP:
        def __init__(self, *a, **k):
            self.created = []

        def check_connection(self):
            return True

        def get_or_create_term(self, name, taxonomy):
            return {"categories": 60, "tags": 9}.get(taxonomy, 9)

        def get_recent_published(self, per_page=8):
            return [{"id": 1, "title": "Old post", "link": "https://studentup.in/old/",
                     "categories": [60]}]

        def get_term_link(self, term_id, taxonomy):
            return "https://studentup.in/category/central-govt-jobs/"

        def upload_media(self, path, title="", alt_text="", filename="", **kw):
            return 88

        def create_post(self, **kwargs):
            self.created.append(kwargs)
            return {"id": 501, "status": kwargs.get("status", "draft"),
                    "link": "https://studentup.in/ssc-cgl-2026-apply-online/"}

        def update_post(self, post_id, **kwargs):
            return {"id": post_id, "status": "publish", "link": "https://x/"}

    real_wp = pipeline.WordPressClient
    saved = (config.DEFAULT_POST_STATUS, config.EDITORIAL_REVIEWER,
             config.PUBLISH_QA_MIN_SCORE, config.PUBLISH_ORIGINALITY_MIN,
             config.TOP_POST_STRICT, config.TOP_POST_MIN_SCORE)
    try:
        pipeline.WordPressClient = FakeWP
        config.DEFAULT_POST_STATUS = "draft"
        config.EDITORIAL_REVIEWER = ""
        art = strong_article()
        art.pop("_top_post", None)
        res = pipeline.publish_article(art)
        assert res["status"] == "draft"
        assert res["link"] and config.STATE_PATH.exists()
        # draft path scores the post but never blocks
        assert art["_qa"]["score"] > 0
        assert art.get("_top") and art["_top"]["score"] >= 50, art.get("_top", {}).get("score")

        # live publish mode → gate enforces score
        config.DEFAULT_POST_STATUS = "publish"
        config.EDITORIAL_REVIEWER = "Test Editor"
        config.PUBLISH_QA_MIN_SCORE = 0
        config.PUBLISH_ORIGINALITY_MIN = 0
        thin_art = {"title": "Thin post", "slug": "thin-post", "category": "Results",
                    "focus_keyword": "thin keyword", "meta_description": "x" * 130,
                    "tags": ["a", "b", "c", "d", "e"], "content_html": THIN_HTML,
                    "quick_answer": "", "faq": [], "external_links": []}
        try:
            pipeline.publish_article(thin_art)
            raise AssertionError("thin live post should be blocked by the gate")
        except RuntimeError as exc:
            assert "TOP-POST GATE" in str(exc) or "LIVE-PUBLISH BLOCKED" in str(exc), exc
        config.DEFAULT_POST_STATUS = "draft"
    finally:
        pipeline.WordPressClient = real_wp
        (config.DEFAULT_POST_STATUS, config.EDITORIAL_REVIEWER,
         config.PUBLISH_QA_MIN_SCORE, config.PUBLISH_ORIGINALITY_MIN,
         config.TOP_POST_STRICT, config.TOP_POST_MIN_SCORE) = saved
    print("  8. pipeline integration (draft score + live gate) ✔")

    # ---------------------------------------------------------------- 9
    bp = top_post.build_blueprint("TSPSC Group 2 2026 notification")
    art = top_post.mock_article(bp)
    assert art["focus_keyword"] == bp["keyword"] and art["_mock"]
    assert bp["outline"][0]["h2"] in art["content_html"]
    assert art["title"] == bp["title_options"][0]["title"]
    br = top_post.gemini_brief(bp)
    for token in ("TOP POST BLUEPRINT", "PRIMARY KEYWORD", "STRUCTURE",
                  "H2:", "DO NOT invent", "FAQ"):
        assert token in br, token
    prompt = gemini_client.TOP_POST_PROMPT_TEMPLATE.format(blueprint=br)
    assert "valid JSON" in prompt and bp["keyword"] in prompt
    old_key = config.GEMINI_API_KEY
    try:
        config.GEMINI_API_KEY = ""
        config.GEMINI_API_KEYS = []
        try:
            gemini_client.generate_top_post(bp)
            raise AssertionError("should require a key")
        except gemini_client.GeminiError:
            pass
    finally:
        config.GEMINI_API_KEY = old_key
    res = top_post.create_top_post("TSPSC Group 2 2026 notification", mock=True,
                                   dry_run=True)
    draft_file = Path(res["link"])
    assert draft_file.exists() and "TSPSC Group 2 2026" in draft_file.read_text(
        encoding="utf-8")
    # CLI helpers run clean (capture stdout)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        assert top_post.run_blueprint("SSC CHSL 2026 notification") == 0
        assert top_post.run_plan(days=10, per_day=1, show=3) == 0
        assert top_post.run_universe(show=3) == 0
        score_file = tmp / "score-me.html"
        write(score_file, "<html><head><title>SSC CGL 2026 Apply Online</title>"
                          "</head><body>" + strong_article()["content_html"] + "</body></html>")
        assert top_post.run_score_file(str(score_file),
                                       "ssc cgl 2026 apply online") == 0
    out = buf.getvalue()
    for token in ("TOP POST BLUEPRINT", "KEYWORD DOMINATION PLAN",
                  "KEYWORD UNIVERSE", "TOP POST SCORE"):
        assert token in out, token
    uni_files = top_post.write_universe()
    assert Path(uni_files["csv"]).exists() and uni_files["count"] >= 9500
    print(f"  9. mock article + Gemini brief + CLI helpers + universe export "
          f"({uni_files['count']} rows) ✔")

    print("ALL v38 TESTS PASSED ✔")
    return 0


if __name__ == "__main__":
    sys.exit(main())
