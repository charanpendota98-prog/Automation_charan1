"""Offline checks for live-validation result semantics."""
from autoblog import live_validation


def main():
    original_get = live_validation._get
    original_user = live_validation.config.WP_USERNAME
    original_pass = live_validation.config.WP_APP_PASSWORD

    def fake_get(url):
        if url.endswith("/wp-json/"):
            return {"status_code": 200, "final_url": url, "content_type": "application/json", "text": '{"namespaces":["wp/v2","studentup/v1"]}'}
        if url.endswith("/privacy-policy/"):
            return {"status_code": 404, "final_url": url, "content_type": "text/html", "text": ""}
        return {"status_code": 200, "final_url": url, "content_type": "text/html", "text": "ok"}

    try:
        live_validation._get = fake_get
        live_validation.config.WP_USERNAME = ""
        live_validation.config.WP_APP_PASSWORD = ""
        report = live_validation.validate("https://example.test")
        assert report["counts"]["pass"] >= 1
        assert report["counts"]["review"] >= 1
        assert report["production_ready"] is False
        print("live validation checks: PASS")
    finally:
        live_validation._get = original_get
        live_validation.config.WP_USERNAME = original_user
        live_validation.config.WP_APP_PASSWORD = original_pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
