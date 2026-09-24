#!/usr/bin/env python3
"""Offline checks for the Google people-first disclosure and publish audit."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from autoblog import config, google_quality  # noqa: E402


def fixture():
    article = {
        "article_type": "job",
        "_source_audit": {"ok": True, "independent_domains": 3,
                          "official_count": 1, "confidence": 92},
        "_deep_sources": [
            {"url": "https://example.gov.in/notice", "title": "Official notice"},
            {"url": "https://news.example.com/report", "title": "News report"},
            {"url": "https://jobs.example.org/guide", "title": "Applicant guide"},
        ],
        "_editorial_value": {"score": 80, "unsupported_claims": []},
        "_content_quality": {"flags": []},
    }
    body = ('<div class="su-takeaways">Quick answer</div>'
            '<table><tr><td>Eligibility</td></tr></table>'
            '<p>Documents and Apply Online steps.</p>')
    return article, body


def main():
    article, body = fixture()
    out = google_quality.inject_methodology(body, article)
    assert out.count('class="su-methodology"') == 1
    assert google_quality.inject_methodology(out, article) == out
    for label in ("Who:", "How:", "Why:", "Sources checked"):
        assert label in out
    assert out.count('rel="noopener"') == 3

    result = google_quality.audit(article, out)
    assert result["ok"], result
    assert result["score"] == 100, result

    bad = out + "<p>100% job guarantee</p>"
    result = google_quality.audit(article, bad)
    assert any(x.startswith("no_guarantees:") for x in result["flags"]), result

    old = getattr(config, "EDITORIAL_REVIEWER", "")
    try:
        config.EDITORIAL_REVIEWER = ""
        result = google_quality.audit(article, out, live=True)
        assert any(x.startswith("human_reviewer:") for x in result["flags"]), result
        config.EDITORIAL_REVIEWER = "Named Editor"
        reviewed_article, reviewed_body = fixture()
        reviewed = google_quality.inject_methodology(reviewed_body, reviewed_article)
        assert google_quality.audit(reviewed_article, reviewed, live=True)["ok"]
        unsafe = reviewed + '<p>Source-backed draft; verify the official notice. సుమారు 80 posts.</p>'
        checked = google_quality.audit(article, unsafe, live=True)
        assert any(x.startswith("review_state:") for x in checked["flags"]), checked
        assert any(x.startswith("no_estimated_critical_facts:")
                   for x in checked["flags"]), checked
    finally:
        config.EDITORIAL_REVIEWER = old
    print("google quality tests: PASS")


if __name__ == "__main__":
    main()
