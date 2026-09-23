"""v35 deep quality, structured-data and public-audit safeguards."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from autoblog import config, google_audit, monetize, seo  # noqa: E402


def main():
    print("v35 DEEP QUALITY + GOOGLE POLICY TESTS:")

    # v99: FAQPage emit avutundi kaani 2+ real Q&A unte matrame.
    # Ikkada 1 question matrame → thin → FAQPage raadu (correct).
    schema = seo.schema_jsonld(
        "SSC CGL 2026 Guide", "Useful description", 
        [{"question": "Q?", "answer": "A."}], "2026-09-13", "ssc-cgl-2026"
    )
    assert "FAQPage" not in schema and "SpeakableSpecification" not in schema
    scripts = [json.loads(x) for x in __import__("re").findall(
        r'<script type="application/ld\+json">(.*?)</script>', schema, __import__("re").S
    )]
    assert any(item["@type"] == "Article" for item in scripts)
    print("  1. deprecated FAQ/speakable schema blocked; Article retained ✔")

    # A canonical must point to the audited URL and JSON-LD must parse.
    html = """<html lang="te"><head>
      <title>SSC CGL 2026 Complete Guide</title>
      <meta name="description" content="SSC CGL 2026 application, eligibility and official steps explained clearly for students.">
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <meta property="og:title" content="SSC CGL Guide">
      <link rel="canonical" href="https://studentup.in/ssc-cgl-2026/">
      <script type="application/ld+json">{"@type":"Article"}</script>
    </head><body><h1>SSC CGL 2026</h1></body></html>"""
    rows = google_audit.html_checks("https://studentup.in/ssc-cgl-2026/", html)
    by_label = {row["label"]: row for row in rows}
    assert by_label["Canonical"]["status"] == "PASS"
    assert by_label["JSON-LD"]["status"] == "PASS"
    assert by_label["HTML language"]["status"] == "PASS"
    bad = google_audit.html_checks(
        "https://studentup.in/ssc-cgl-2026/", html.replace(
            'href="https://studentup.in/ssc-cgl-2026/"',
            'href="https://studentup.in/other/"')
        .replace('<script type="application/ld+json">{"@type":"Article"}</script>',
                 '<script type="application/ld+json">{bad}</script>')
    )
    bad_by_label = {row["label"]: row for row in bad}
    assert bad_by_label["Canonical"]["status"] == "WARN"
    assert bad_by_label["JSON-LD"]["status"] == "WARN"
    print("  2. canonical/indexability/OG/language/JSON-LD checks ✔")

    # Sponsored HTML must identify the relationship; unsafe owner markup is off.
    old = config.FEATURED_CTA_HTML
    try:
        config.FEATURED_CTA_HTML = '<a href="https://example.test/offer">Offer</a>'
        assert monetize.featured_block() == ""
        config.FEATURED_CTA_HTML = (
            '<a href="https://example.test/offer" rel="sponsored nofollow">Offer</a>'
        )
        assert "Sponsored" in monetize.featured_block()
    finally:
        config.FEATURED_CTA_HTML = old
    assert config.PUBLISH_QA_MIN_SCORE >= 70
    assert config.PUBLISH_ORIGINALITY_MIN >= 70
    print("  3. sponsored rel gate + live quality thresholds ✔")

    print("ALL v35 TESTS PASSED ✔")


if __name__ == "__main__":
    main()
