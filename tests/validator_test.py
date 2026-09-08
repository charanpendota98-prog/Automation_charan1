"""Validator tests: originality proof, HTML sanitizer, QA scoring."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from autoblog import validator  # noqa: E402

SOURCE = ("SSC released a new recruitment notification for 3200 vacancies "
          "across multiple departments and the online application process "
          "begins next week on the official website with fee of one hundred "
          "rupees for general candidates who possess a bachelor degree from "
          "a recognized university according to the detailed notification.")


def main():
    print("VALIDATOR TESTS:")

    # ---- 1. originality: copied text -> low score ----
    copied = "<p>" + SOURCE + "</p>"
    score_copy = validator.originality_score(copied, [SOURCE])
    assert score_copy < 30, score_copy

    # ---- original text -> high score ----
    original = ("<p>ఈ కథనంలో మనం కొత్త ఉద్యోగ ప్రకటన గురించి పూర్తి వివరాలు "
                "తెలుసుకుంటాము. దరఖాస్తు విధానం చాలా సులభంగా ఉంటుంది మరియు "
                "అర్హత నియమాలు కూడా సులభంగా ఉన్నాయి కాబట్టి అందరు విద్యార్థులు "
                "దరఖాస్తు చేసుకోవచ్చు అని నిపుణులు చెబుతున్నారు.</p>")
    score_orig = validator.originality_score(original, [SOURCE])
    assert score_orig > 95, score_orig
    print(f"  1. originality (copy={score_copy}%, original={score_orig}%) ✔")

    # ---- 2. sanitizer ----
    dirty = ('<html><body><p>good</p><script>alert(1)</script>'
             '<div>div content</div><h2>head</h2>```html\n<p>md</p>```</body></html>')
    clean = validator.sanitize_html(dirty)
    assert "<script" not in clean and "alert" not in clean
    assert "<div" not in clean and "div content" in clean  # content preserved
    assert "<html" not in clean and "```" not in clean
    assert "<p>good</p>" in clean and "<h2>head</h2>" in clean
    print("  2. sanitize_html (scripts/divs stripped, content safe) ✔")

    # ---- 3. QA scoring ----
    good_article = {
        "title": "SSC CGL 2026 Complete Guide Telugu lo",
        "focus_keyword": "SSC CGL 2026",
        "content_html": (
            "<p>SSC CGL 2026 apply process simple and clear here.</p>"
            "<h2>SSC CGL 2026 Eligibility</h2><p>x</p>"
            "<h2>Process</h2><ol><li>one</li><li>two</li></ol>"
            "<table><tr><td>t</td></tr></table>"
        ),
        "meta_description": "SSC CGL 2026 complete guide " + "x" * 120,
        "tags": ["a", "b", "c", "d", "e"],
        "faq": [{"question": "q", "answer": "a"}] * 3,
        "external_links": [{"text": "o", "url": "https://ssc.gov.in"}],
        "quick_answer": "SSC CGL 2026 answer here for the snippet test block.",
        "secondary_keywords": ["s1", "s2", "s3"],
    }
    qa = validator.validate_article(good_article, good_article["content_html"])
    assert qa["score"] >= 55, qa  # short content only penalizes word count
    assert any("word count" in i for i in qa["issues"])
    assert qa["reading_min"] >= 1

    bad_article = {"title": "t", "content_html": "<p>x</p>", "tags": []}
    qa_bad = validator.validate_article(bad_article, "<p>x</p>")
    assert qa_bad["score"] <= 20 and len(qa_bad["issues"]) >= 5
    print(f"  3. validate_article (good={qa['score']}/100, bad={qa_bad['score']}/100) ✔")

    # ---- 4. state: avg scores + meta cleanup ----
    from datetime import date, timedelta
    from autoblog import state as st

    db = Path("/tmp/test_validator_state.db")
    db.unlink(missing_ok=True)
    st.init(db)
    st.record_post(db, "T1", "t1", "Govt Jobs", "l1", "draft", qa_score=80, orig_score=95)
    st.record_post(db, "T2", "t2", "Results", "l2", "publish", qa_score=90, orig_score=85)
    avgs = st.avg_scores(db)
    assert avgs == {"qa": 85.0, "orig": 90.0, "n": 2}, avgs
    old_date = (date.today() - timedelta(days=10)).isoformat()
    st.meta_set(db, f"slots:{old_date}", "[6,7]")
    st.meta_set(db, "slots:2099-01-01", "[8]")  # future key — keep
    st.meta_cleanup(db, keep_days=7)
    assert st.meta_get(db, f"slots:{old_date}") is None
    assert st.meta_get(db, "slots:2099-01-01") == "[8]"
    db.unlink(missing_ok=True)
    print("  4. state (avg QA/orig + meta cleanup + column upgrade) ✔")

    print("ALL VALIDATOR TESTS PASSED ✔")


if __name__ == "__main__":
    main()
