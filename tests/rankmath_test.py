"""Rank Math writing-trick tests: slug optimizer, internal-link fallback,
validator v2 checks (title first-half, number, density window, paragraphs)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from autoblog import config, seo, validator  # noqa: E402


def main():
    print("RANK MATH WRITING TRICK TESTS:")

    # ---- 1. slug optimizer ----
    # keyword tokens injected into slug (keyword-in-URL check)
    s1 = seo.optimize_slug("complete-guide-telugu", focus_keyword="SSC CGL 2026 గైడ్")
    assert s1.startswith("ssc-cgl-2026-") and "complete-guide" in s1, s1
    # stopwords stripped
    s2 = seo.optimize_slug("how-to-apply-and-check-the-result-online", "")
    assert s2 == "apply-check-result-online", s2
    # already has tokens -> no duplication
    s3 = seo.optimize_slug("ssc-cgl-2026-guide", focus_keyword="SSC CGL 2026")
    assert s3 == "ssc-cgl-2026-guide", s3
    # empty slug + english keyword
    s4 = seo.optimize_slug("", focus_keyword="NSP Scholarship 2026")
    assert s4 == "nsp-scholarship-2026", s4
    # max length respected
    s5 = seo.optimize_slug("a" * 100, focus_keyword="")
    assert len(s5) <= 60
    print("  1. optimize_slug (keyword tokens + stopwords + caps) ✔")

    # ---- 2. validator v2: title first-half + number + paragraphs ----
    good = {
        "title": "SSC CGL 2026 Complete Guide Telugu lo",
        "focus_keyword": "SSC CGL 2026",
        "content_html": (
            "<p>SSC CGL 2026 apply process simple and clear here friends.</p>"
            "<h2>SSC CGL 2026 Eligibility</h2><p>x</p>"
            "<h2>Process</h2><ol><li>one</li><li>two</li></ol>"
            "<table><tr><td>t</td></tr></table>"
            '<p><a href="https://studentup.in/other/">related</a></p>'
        ),
        "meta_description": "SSC CGL 2026 complete guide " + "x" * 120,
        "tags": ["a", "b", "c", "d", "e"],
        "faq": [{"question": "q", "answer": "a"}] * 3,
        "external_links": [{"text": "o", "url": "https://ssc.gov.in"}],
        "quick_answer": "SSC CGL 2026 answer for snippet test block here.",
        "secondary_keywords": ["s1", "s2", "s3"],
    }
    qa = validator.validate_article(good, good["content_html"])
    assert not any("first-half" in i for i in qa["issues"]), qa["issues"]
    assert not any("number" in i for i in qa["issues"]), qa["issues"]
    assert not any("internal links ledu" in i for i in qa["issues"]), qa["issues"]
    assert not any("too long" in i for i in qa["issues"]), qa["issues"]

    # title WITHOUT keyword/number -> those checks fail
    bad_title = dict(good, title="Complete Guide Telugu lo")
    qa2 = validator.validate_article(bad_title, good["content_html"])
    assert any("first-half" in i or "title lo ledu" in i for i in qa2["issues"])
    assert any("number" in i for i in qa2["issues"])

    # long paragraph flagged
    long_para = "<p>" + ("word " * 200) + "</p>"
    qa3 = validator.validate_article(dict(good, content_html=long_para), long_para)
    assert any("too long" in i or "structure weak" in i for i in qa3["issues"])
    print("  2. validator v2 (first-half, number, internal, paragraphs) ✔")

    # ---- 3. internal-link fallback (pipeline logic smoke) ----
    from autoblog.wordpress_client import WordPressClient

    assert hasattr(WordPressClient, "get_term_link")
    print("  3. get_term_link available (category fallback) ✔")

    # ---- 4. v10: visible-date fix + read-also block + E-E-A-T schema ----
    html_out = seo.enhance(
        "<p>body text ok</p>", focus_keyword="SSC CGL 2026",
        internal_links=[{"link": "https://studentup.in/a/", "title": "Related A"},
                        {"link": "https://studentup.in/b/", "title": "Related B"}],
        external_links=[], quick_answer="Quick answer here friends.",
        faq=[{"question": "q", "answer": "a"}],
        date_str="2026-01-10", date_modified="2026-09-07",
        slug="ssc-cgl-2026", title="SSC CGL 2026 Guide",
        description="desc", category="Govt Jobs")
    # visible badge = modified date (NOT old published)
    assert "Last Updated: 2026-09-07" in html_out
    assert "Last Updated: 2026-01-10" not in html_out
    # schema dates: published preserved, modified updated
    assert '"datePublished": "2026-01-10"' in html_out
    assert '"dateModified": "2026-09-07"' in html_out
    # read-also block at end
    assert "వీటిని కూడా చదవండి" in html_out
    assert 'href="https://studentup.in/a/"' in html_out
    # E-E-A-T author
    assert '"@type": "Person"' in html_out and "Editorial Team" in html_out
    assert '"editor"' in html_out
    # publisher logo: set -> present; empty -> absent
    config.SITE_LOGO_URL = "https://studentup.in/logo.png"
    html_logo = seo.schema_jsonld("T", "d", [], "2026-01-10", "t")
    assert '"logo"' in html_logo
    config.SITE_LOGO_URL = ""
    html_nologo = seo.schema_jsonld("T", "d", [], "2026-01-10", "t")
    assert '"logo"' not in html_nologo
    print("  4. v10 fixes (visible date, read-also, E-E-A-T, logo gate) ✔")

    print("ALL RANK MATH TRICK TESTS PASSED ✔")


if __name__ == "__main__":
    main()
