"""v44 DEEP POST ENGINE — source tiering, deep fact extraction,
cross-source verification, deep analysis HTML, perfect-post gate.

Offline: synthetic SourceArticle objects, no network, no WP.
"""
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from autoblog import config, deep_research as dr  # noqa: E402
from autoblog.sources import SourceArticle  # noqa: E402


def _sa(url, title, text):
    return SourceArticle(url=url, title=title, text=text,
                         site_name=url.split("/")[2] if url.count("/") > 2 else "")


def test_source_tiering():
    assert dr.source_tier("https://tspsc.gov.in/notification") == 1
    assert dr.source_tier("https://www.ssc.gov.in/cgl") == 1
    assert dr.source_tier("https://tsbie.ac.in/results") == 1
    assert dr.source_tier("https://tv9telugu.com/jobs") == 2
    assert dr.source_tier("https://deccanchronicle.com/news") == 2
    assert dr.source_tier("https://random-blog.example.com/post") == 3
    assert dr.source_tier("not-a-url") == 3


def test_date_extraction_and_normalization():
    a = _sa("https://tspsc.gov.in/g2", "TSPSC G2",
            "Applications close on 15 October 2026. The exam will be held "
            "on 5 January 2027 at 10:00 AM.")
    b = _sa("https://tv9telugu.com/g2", "G2 news",
            "Last date to apply is 15/10/2026 according to the notice.")
    facts = dr.extract_facts([("S1", a.url, 1, a.text),
                              ("S2", b.url, 2, b.text)])
    dates = [f for f in facts if f["kind"] == "date"]
    norms = {f["norm"] for f in dates}
    assert "2026-10-15" in norms and "2027-01-05" in norms
    # label detection
    labels = {(f["label"], f["norm"]) for f in dates}
    assert ("last-date-apply", "2026-10-15") in labels
    assert ("exam", "2027-01-05") in labels


def test_number_extraction():
    a = _sa("https://ssc.gov.in/cgl", "SSC CGL",
            "There are 17727 vacancies in Group B posts. The application "
            "fee is ₹550 for general candidates. Maximum age is 32 years. "
            "Salary of ₹18000-56900 is applicable.")
    facts = dr.extract_facts([("S1", a.url, 1, a.text)])
    kinds = {(f["kind"], f["value"]) for f in facts}
    assert ("vacancy", "17727") in kinds
    assert ("fee", "550") in kinds
    assert ("age", "32") in kinds
    assert any(f["kind"] == "salary" for f in facts)


def test_verification_matrix():
    a = _sa("https://tspsc.gov.in/g2", "TSPSC G2 official",
            "Last date to apply is 15 October 2026. 2230 vacancies are "
            "sanctioned.")
    b = _sa("https://tv9telugu.com/g2", "G2 coverage",
            "The last date to apply remains 15 October 2026 for all "
            "candidates.")
    c = _sa("https://random.example.com/g2", "G2 blog",
            "Heard the fee is ₹1000 this year.")
    matrix = dr.verify_facts(dr.extract_facts(
        [("S1", a.url, 1, a.text), ("S2", b.url, 2, b.text),
         ("S3", c.url, 3, c.text)]))
    by_key = {(v["kind"], v["label"], v["norm"]): v for v in matrix["verified"]}
    # same date from 2 sources → confirmed
    assert by_key[("date", "last-date-apply", "2026-10-15")]["status"] == \
        "confirmed"
    # official single → official
    assert by_key[("vacancy", "vacancy", "2230")]["status"] == "official"
    # single T3 → single
    assert by_key[("fee", "fee", "1000")]["status"] == "single"
    assert matrix["conflicts"] == []


def test_conflict_detection():
    a = _sa("https://tspsc.gov.in/g2", "Official",
            "Last date to apply is 15 October 2026.")
    b = _sa("https://tv9telugu.com/g2", "Media",
            "Last date to apply extended to 20 October 2026.")
    matrix = dr.verify_facts(dr.extract_facts(
        [("S1", a.url, 1, a.text), ("S2", b.url, 2, b.text)]))
    assert len(matrix["conflicts"]) == 1
    c = matrix["conflicts"][0]
    assert c["label"] == "last-date-apply"
    assert sorted(c["values"]) == ["2026-10-15", "2026-10-20"]
    assert set(c["sources"]) == {"S1", "S2"}


def test_gaps_and_confidence():
    rich = [_sa("https://tspsc.gov.in/g2", "Official",
                "Last date to apply is 15 October 2026. 2230 vacancies. "
                "The application fee is ₹500. Maximum age 32 years. "
                "Apply online at https://tspsc.gov.in/apply. The exam will "
                "be held on 5 January 2027."),
            _sa("https://tv9telugu.com/g2", "Media",
                "Last date to apply is 15 October 2026 for TSPSC Group 2.")]
    report = dr.build_report("TSPSC Group 2 2026", rich, target_year=2026)
    assert report["confidence"] >= 75
    assert not any("last date" in g for g in report["gaps"])
    poor = [_sa("https://random.example.com/x", "Blog",
                "Something happened in 2024 and experts say more is coming.")]
    report2 = dr.build_report("Mystery topic", poor)
    assert report2["confidence"] < report["confidence"]
    assert any("last date" in g for g in report2["gaps"])
    assert any("official" in g.lower() for g in report2["gaps"])


def test_deep_html_safety_and_labels():
    a = _sa("https://tspsc.gov.in/g2", "Official",
            "Last date to apply is 15 October 2026. 2230 vacancies. "
            "Apply at https://tspsc.gov.in/apply.")
    b = _sa("https://evil.example.com/x", "Blog",
            'Last date to apply is 20 October 2026 <script>alert(1)</script>')
    report = dr.build_report("TSPSC Group 2", [a, b], target_year=2026)
    html = dr.deep_analysis_html(report)
    assert "<script>alert(1)" not in html
    assert "alert(1)" in html  # escaped text, never executed
    assert "In-Depth Analysis" in html
    assert "⛔" in html  # conflict box present
    assert "javascript:" not in html
    assert "su-deep" in html
    assert "tspsc.gov.in" in html
    # table row cap
    assert html.count("<tr><td>") <= 8 + 1  # header + max 8
    assert 'rel="noopener"' in html


def test_gate_rules():
    a = _sa("https://tspsc.gov.in/g2", "Official",
            "Last date to apply is 15 October 2026.")
    b = _sa("https://tv9telugu.com/g2", "Media",
            "Last date to apply extended to 20 October 2026.")
    report = dr.build_report("T", [a, b])
    hard, warn = dr.gate_post("<p>apply before deadline</p>", report)
    assert any("conflict" in h for h in hard)
    # two different last dates inside the article → hard
    clean = _sa("https://tspsc.gov.in/g2", "Official",
                "Last date to apply is 15 October 2026. 2230 vacancies. "
                "The application fee is ₹500. Maximum age 32 years. "
                "Apply at https://tspsc.gov.in/apply. Exam on 5 January 2027.")
    ok_report = dr.build_report("T", [clean])
    hard2, _ = dr.gate_post(
        '<p>Last date: 15/10/2026</p><p>last date to apply is 20 October 2026</p>',
        ok_report)
    assert any("2 different" in h or "canonical" in h for h in hard2)
    # stale years (only 2023 dates) → hard
    stale = _sa("https://old.example.com/x", "Old",
                "Last date to apply is 10 January 2023.")
    stale_report = dr.build_report("T", [stale])
    hard3, _ = dr.gate_post("<p>...</p>", stale_report)
    assert any("stale" in h for h in hard3)
    # clean + current → no hard
    current = _sa("https://tspsc.gov.in/g2", "Official",
                  f"Last date to apply is 10 {date.today().strftime('%B')} "
                  f"{date.today().year}. 100 vacancies. "
                  "Apply at https://tspsc.gov.in/apply.")
    clean_report = dr.build_report("T", [current])
    hard4, _ = dr.gate_post("<p>ok</p>", clean_report)
    assert hard4 == []


def test_publish_gate_lifecycle():
    a = _sa("https://tspsc.gov.in/g2", "Official",
            "Last date to apply is 15 October 2026.")
    b = _sa("https://tv9telugu.com/g2", "Media",
            "Last date to apply extended to 20 October 2026.")
    report = dr.build_report("T", [a, b])
    article = {"_deep": report, "status": "draft"}
    ok, detail = dr.publish_gate(article, html="<p>x</p>", live=None)
    assert ok and "draft" in detail
    # live with conflicts → block
    article_live = {"_deep": report, "status": "publish"}
    ok_live, detail_live = dr.publish_gate(article_live, html="<p>x</p>",
                                           live=None)
    assert not ok_live and "DEEP GATE" in detail_live
    # no _deep → pass
    ok2, _ = dr.publish_gate({}, html="<p>x</p>", live=True)
    assert ok2
    # strict off → pass
    try:
        old = config.DEEP_GATE_STRICT
        config.DEEP_GATE_STRICT = False
        ok3, _ = dr.publish_gate(article_live, html="<p>x</p>", live=True)
        assert ok3
    finally:
        config.DEEP_GATE_STRICT = old


def test_inject_deep_placement():
    a = _sa("https://tspsc.gov.in/g2", "Official",
            "Last date to apply is 15 October 2026. 100 vacancies. "
            "Apply at https://tspsc.gov.in/apply.")
    report = dr.build_report("T", [a])
    content = ("<p>Article body here with enough text to be real content "
               "for the placement engine to work with safely.</p>"
               '<h2 id="read-also">Read Also</h2><p>related</p>'
               '<script type="application/ld+json">{"@type":"Article"}</script>')
    html = dr.inject_deep(content, report)
    deep_pos = html.find('id="deep-analysis"')
    related_pos = html.find('<h2 id="read-also"')
    assert deep_pos != -1 and deep_pos < related_pos
    # no-op when no facts
    empty = dr.inject_deep(content, {"facts_total": 0})
    assert empty == content


def test_notebooklm_brief_merge():
    a = _sa("https://tspsc.gov.in/g2", "Official",
            "Last date to apply is 15 October 2026. 100 vacancies. "
            "Apply at https://tspsc.gov.in/apply.")
    good_brief = ("Claim ledger:\n"
                  "C1: Last date 15/10/2026 (S1).\n"
                  "C2: 100 vacancies (S1, S2).\n"
                  "Conflict audit: no unresolved disagreements found.\n"
                  + "Filler text to reach the minimum length threshold for "
                    "a usable cited brief from the editor. " * 3)
    report = dr.build_report("T", [a], notebooklm_brief=good_brief)
    assert report["notebooklm"] is not None
    bad = dr.build_report("T", [a], notebooklm_brief="short uncited text")
    assert bad["notebooklm"] is not None and not bad["notebooklm"]["ok"]
    hard, _ = dr.gate_post("<p>x</p>", bad)
    assert any("NotebookLM" in h for h in hard)


def test_pipeline_integration_shim():
    """Mirror of the pipeline.publish_article deep block (no WP needed)."""
    a = _sa("https://tspsc.gov.in/g2", "Official",
            "Last date to apply is 15 October 2026. 100 vacancies. "
            "Apply at https://tspsc.gov.in/apply.")
    b = _sa("https://tv9telugu.com/g2", "Media",
            "Last date to apply is 15 October 2026 for all candidates.")
    article = {"title": "TSPSC Group 2", "category": "TS Govt Jobs",
               "_deep_sources": [a, b], "_target_year": 2026,
               "_notebooklm_brief": ""}
    html = "<p>Body content for the article here with real words.</p>"
    deep_sources = article.get("_deep_sources") or []
    if len(deep_sources) >= int(getattr(config, "DEEP_MIN_SOURCES", 2)):
        report = dr.build_report(article["title"], deep_sources,
                                 notebooklm_brief=article.get("_notebooklm_brief", ""),
                                 target_year=article.get("_target_year"))
        html = dr.inject_deep(html, report)
        article["_deep"] = report
        hard, warn = dr.gate_post(html, report, live=False)
        article["_deep_flags"] = [f"DEEP: {h}" for h in hard]
    assert article.get("_deep") is not None
    assert "In-Depth Analysis" in html
    assert article["_deep"]["confidence"] > 0
    # below min sources → no deep
    article2 = {"title": "T", "_deep_sources": [a], "_target_year": None,
                "_notebooklm_brief": ""}
    if len(article2["_deep_sources"]) >= int(getattr(config, "DEEP_MIN_SOURCES", 2)):
        raise AssertionError("should not reach here")
    assert "_deep" not in article2


def test_deep_prompt_extension():
    assert "Pass 6" in dr.DEEP_PASSES
    assert "year-over-year" in dr.DEEP_PASSES.lower()
    assert "Pass 8" in dr.DEEP_PASSES


def main():
    test_source_tiering()
    print("  source tiering (T1 official / T2 media / T3) ✔")
    test_date_extraction_and_normalization()
    print("  date extraction + normalization + labels ✔")
    test_number_extraction()
    print("  number extraction (vacancy/fee/age/salary) ✔")
    test_verification_matrix()
    print("  verification matrix (confirmed/official/single) ✔")
    test_conflict_detection()
    print("  conflict detection ✔")
    test_gaps_and_confidence()
    print("  gaps + confidence scoring ✔")
    test_deep_html_safety_and_labels()
    print("  deep HTML safety (XSS/conflict box/cap/links) ✔")
    test_gate_rules()
    print("  perfect-post gate (conflict/2-dates/stale/clean) ✔")
    test_publish_gate_lifecycle()
    print("  publish gate lifecycle (draft/live/strict-off) ✔")
    test_inject_deep_placement()
    print("  injection placement (before related/JSON-LD) ✔")
    test_notebooklm_brief_merge()
    print("  NotebookLM brief merge + validation gate ✔")
    test_pipeline_integration_shim()
    print("  pipeline integration shim (min-sources no-op) ✔")
    test_deep_prompt_extension()
    print("  NotebookLM deep prompt (passes 6-8) ✔")
    print("ALL v44 DEEP RESEARCH TESTS PASSED ✔")


if __name__ == "__main__":
    main()
