"""v30 production gate + revenue XSS-safety tests; no network."""
import sys
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from autoblog import config, monetize, production_audit  # noqa: E402


class FakeWP:
    def check_connection(self):
        return {"name": "admin", "roles": ["administrator"]}

    def public_get_status(self, path):
        if path == "/robots.txt":
            return 200, "User-agent: *\nDisallow:\n"
        if path in ("/sitemap_index.xml", "/ads.txt"):
            if path == "/ads.txt":
                return 200, "google.com, pub-1234567890123456, DIRECT, f08c47fec0942fa0"
            return 200, "sitemap"
        return 404, ""

    def list_plugins(self):
        return [{"slug": slug, "plugin": f"{slug}/{slug}.php", "status": "active"}
                for slug in ("rank-math", "redirection", "updraftplus", "wp-super-cache")]

    def list_themes(self):
        return [{"slug": "generatepress", "name": "GeneratePress", "status": "active"}]

    def get_page_by_slug(self, slug):
        return {"id": 1, "link": "https://studentup.in/" + slug + "/"}


def row(rows, label):
    return next(x for x in rows if x["label"] == label)


def test_full_gate_has_no_failures():
    values = {
        "WP_SITE": "https://studentup.in",
        "WP_USERNAME": "admin",
        "WP_APP_PASSWORD": "xxxx",
        "GEMINI_API_KEY": "AIza-test",
        "GEMINI_API_KEYS": ["AIza-test"],
        "FACT_STRICT": True,
        "ORIG_HARD_FLOOR": 72.0,
        "DEFAULT_POST_STATUS": "draft",
        "SUPPORT_EMAIL": "editor@studentup.in",
        "ADSENSE_ENABLED": True,
        "ADSENSE_APPROVED": True,
        "ADSENSE_CLIENT_ID": "ca-pub-1234567890123456",
        "ADSENSE_CONSENT_PROVIDER": "Google-certified-CMP",
        "GA4_ENABLED": False,
        "MAX_AD_SLOTS": 3,
        "AD_CLS_WRAPPER": True,
    }
    with mock.patch.multiple(config, **values):
        rows = production_audit.collect(FakeWP())
        assert not [x for x in rows if x["status"] == "FAIL"], rows
        assert row(rows, "ads.txt")["status"] == "PASS"
        assert production_audit.run(FakeWP(), connect=False) == 0


def test_gate_marks_missing_cmp_as_warning_not_fake_pass():
    with mock.patch.object(config, "ADSENSE_ENABLED", True), \
         mock.patch.object(config, "ADSENSE_APPROVED", True), \
         mock.patch.object(config, "ADSENSE_CLIENT_ID", "ca-pub-123456"), \
         mock.patch.object(config, "ADSENSE_CONSENT_PROVIDER", ""):
        rows = production_audit.local_checks()
    assert row(rows, "Consent/CMP")["status"] == "WARN"


def test_monetization_rejects_unsafe_markup():
    old_tg, old_aff, old_featured = (config.TELEGRAM_CHANNEL_URL,
                                      config.AFFILIATE_LINKS,
                                      config.FEATURED_CTA_HTML)
    try:
        config.TELEGRAM_CHANNEL_URL = 'javascript:alert(1)'
        assert monetize.telegram_cta_block() == ""
        config.AFFILIATE_LINKS = 'Bad|javascript:alert(1)|job\nGood|https://example.test/x|job'
        out = monetize.affiliate_block({"title": "Job guide", "category": "Jobs"})
        assert "javascript" not in out and "example.test/x" in out
        config.FEATURED_CTA_HTML = '<script>alert(1)</script><a href="https://x.test">Offer</a>'
        featured = monetize.featured_block()
        assert featured == ""  # missing rel=sponsored is rejected, not guessed
    finally:
        config.TELEGRAM_CHANNEL_URL = old_tg
        config.AFFILIATE_LINKS = old_aff
        config.FEATURED_CTA_HTML = old_featured


def main():
    test_full_gate_has_no_failures()
    print("  production gate pass/warn behavior ✔")
    test_gate_marks_missing_cmp_as_warning_not_fake_pass()
    print("  missing CMP is visible as WARN ✔")
    test_monetization_rejects_unsafe_markup()
    print("  monetization URL/HTML safety ✔")
    print("ALL v30 TESTS PASSED ✔")


if __name__ == "__main__":
    main()
