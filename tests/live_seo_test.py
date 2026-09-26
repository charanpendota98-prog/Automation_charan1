"""Offline regression test: live SEO audit never promotes estimates to Rank Math."""
from autoblog import live_seo


def main():
    class FakeWP:
        def get_post(self, post_id):
            return {"id": post_id, "link": "https://studentup.in/test-post/", "status": "publish"}

        def read_rankmath_state(self, post_id):
            return {
                "ok": True,
                "rank_math_ui_score": None,
                "score_note": "read-only test: unavailable",
                "fields": {
                    "rank_math_focus_keyword": "SSC Recruitment 2026",
                    "rank_math_title": "SSC Recruitment 2026 Complete Guide",
                    "rank_math_description": "SSC Recruitment 2026 eligibility and apply online details for students.",
                },
            }

    old = live_seo._fetch_public
    live_seo._fetch_public = lambda url: {
        "status": 200,
        "final_url": url,
        "error": "",
        "html": """<html><head><title>SSC Recruitment 2026 Complete Guide</title>
        <meta name='description' content='SSC Recruitment 2026 eligibility and apply online details for students. Check the official notice before applying.'>
        <link rel='canonical' href='https://studentup.in/test-post/'>
        <meta property='og:title' content='SSC Recruitment 2026 Complete Guide'>
        <meta property='og:description' content='SSC Recruitment 2026 details'>
        <meta property='og:image' content='https://studentup.in/image.jpg'>
        <script type='application/ld+json'>{"@type":"Article"}</script>
        </head><body><main><h1>SSC Recruitment 2026</h1><p>SSC Recruitment 2026 details are here.</p>
        <p>Eligibility, dates, documents, selection, fee and application instructions are explained in this article.</p>
        <a href='/privacy-policy/'>Policy</a></main></body></html>""",
    }
    try:
        report = live_seo.audit(55, wp=FakeWP())
        assert report["rank_math_actual_score"] is None
        assert report["rank_math_actual_100"] is False
        assert report["status"] == "review"
        assert report["public_seo_coverage"] is not None
        print("live SEO verification checks: PASS")
    finally:
        live_seo._fetch_public = old
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
