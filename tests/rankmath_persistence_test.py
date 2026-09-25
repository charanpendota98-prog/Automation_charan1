"""Regression tests for Rank Math field delivery, not just local scoring.

These tests deliberately model the two WordPress read paths:
- wp/v2 can omit registered Rank Math meta;
- the StudentUp bridge is the authenticated source of truth.
"""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from autoblog import config, pipeline, seo  # noqa: E402
from autoblog.wordpress_client import WordPressClient  # noqa: E402


class Response:
    def __init__(self, status_code, data):
        self.status_code = status_code
        self._data = data
        self.content = b"{}"
        self.text = str(data)

    def json(self):
        return self._data


class Session:
    def __init__(self):
        self.calls = []

    def post(self, url, json, timeout):
        self.calls.append((url, json))
        if "rankmath/v1" in url:
            return Response(404, {"code": "rest_no_route"})
        saved = {
            key: ", ".join(value) if isinstance(value, list) else str(value)
            for key, value in json["meta"].items()
        }
        return Response(200, {"ok": True, "saved": saved})


def test_all_rank_math_fields_are_written_and_bridge_readback_counts():
    original_site = config.WP_SITE
    original_discover = config.DISCOVER_META_ENABLED
    config.WP_SITE = "https://studentup.in"
    config.DISCOVER_META_ENABLED = True
    try:
        meta = seo.rankmath_meta(
            focus_keyword="Infor Recruitment 2026",
            description="Infor Recruitment 2026 eligibility and apply online details for students.",
            seo_title="Infor Recruitment 2026 Complete Guide",
            secondary_keywords=["Infor jobs 2026", "Infor apply online"],
            slug="infor-recruitment-2026",
        )
        expected = {
            "rank_math_focus_keyword", "rank_math_description", "rank_math_title",
            "rank_math_facebook_title", "rank_math_facebook_description",
            "rank_math_twitter_title", "rank_math_twitter_description",
            "rank_math_twitter_use_open_graph", "rank_math_canonical_url",
            "rank_math_robots",
        }
        assert expected <= set(meta), sorted(set(meta))

        client = WordPressClient.__new__(WordPressClient)
        client.site = config.WP_SITE
        client.session = Session()
        assert client.write_seo_meta(77, meta) is True
        bridge_call = client.session.calls[-1]
        assert bridge_call[1]["meta"].keys() == meta.keys()

        # Core REST hides the fields, but the bridge has them. The new verifier
        # must report persistence instead of a false missing-field warning.
        client.get_post = lambda post_id: {"meta": {}}
        client.read_rankmath_state = lambda post_id: {
            "ok": True,
            "fields": {key: (", ".join(value) if isinstance(value, list) else str(value))
                        for key, value in meta.items()},
            "rank_math_ui_score": None,
        }
        landed = client.verify_rankmath_meta(77, list(meta))
        assert all(landed.values()), landed
    finally:
        config.WP_SITE = original_site
        config.DISCOVER_META_ENABLED = original_discover


def test_source_preflight_rejects_unverified_claims_before_wordpress():
    source_text = (
        "SSC Recruitment 2026 has 100 posts. The application deadline is "
        "15 October 2026. Apply at https://ssc.gov.in/notice. "
        "The notice explains eligibility, documents, selection stages, registration, "
        "fee payment, correction instructions, helpdesk details and the official "
        "application process for eligible candidates. Read the complete notice "
        "before submitting the form and keep the acknowledgement for records."
    )
    article = {
        "title": "SSC Recruitment 2026 Complete Details",
        "content_html": (
            "<p>SSC Recruitment 2026 has 100 posts. Apply before 15 October 2026.</p>"
        ),
        "source_url": "https://ssc.gov.in/notice",
        "_source_urls": [
            "https://ssc.gov.in/notice",
            "https://board.gov.in/notice",
            "https://university.edu.in/notice",
        ],
        "_deep_sources": [
            {"url": url, "title": "Notice", "text": source_text}
            for url in [
                "https://ssc.gov.in/notice",
                "https://board.gov.in/notice",
                "https://university.edu.in/notice",
            ]
        ],
        "_target_year": 2026,
    }
    old = config.SOURCE_PREFLIGHT_REQUIRED
    config.SOURCE_PREFLIGHT_REQUIRED = True
    try:
        report = pipeline._strict_source_preflight(article)
        assert report["ok"], report
        assert article["_source_audit"]["official_count"] == 3
    finally:
        config.SOURCE_PREFLIGHT_REQUIRED = old

    article["content_html"] = "<p>SSC Recruitment 2026 has 99999 posts.</p>"
    config.SOURCE_PREFLIGHT_REQUIRED = True
    try:
        try:
            pipeline._strict_source_preflight(article)
        except RuntimeError as exc:
            assert "SOURCE PREFLIGHT FAILED" in str(exc)
        else:
            raise AssertionError("unsupported numeric claim was not rejected")
    finally:
        config.SOURCE_PREFLIGHT_REQUIRED = old


if __name__ == "__main__":
    test_all_rank_math_fields_are_written_and_bridge_readback_counts()
    test_source_preflight_rejects_unverified_claims_before_wordpress()
    print("Rank Math + source preflight regression passed")
