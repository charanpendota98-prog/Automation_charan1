"""v28 tests: safe plugin stack, read-only theme audit, and AdSense kit.

All REST calls are faked. Nothing here contacts WordPress or Google.
"""
import re
import sys
import tempfile
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from autoblog import adsense_kit, config, site_setup  # noqa: E402
from autoblog.wordpress_client import WordPressClient  # noqa: E402


class Resp:
    def __init__(self, status=200, payload=None):
        self.status_code = status
        self._payload = payload if payload is not None else {}
        self.content = b"{}"
        self.text = ""

    @property
    def ok(self):
        return self.status_code < 400

    def json(self):
        return self._payload


class WidgetWP:
    def __init__(self):
        self.widgets = {}
        self.created = 0
        self.calls = []

    def _request(self, method, path, **kwargs):
        self.calls.append((method, path, kwargs))
        if path == "sidebars":
            return Resp(200, [{"id": "footer-1", "name": "Footer"}])
        if path == "widgets" and method == "GET":
            return Resp(200, [{"id": wid, "instance": instance}
                              for wid, instance in self.widgets.items()])
        if path == "widgets" and method == "POST":
            self.created += 1
            wid = f"text-{self.created}"
            self.widgets[wid] = kwargs["json"]["instance"]
            return Resp(201, {"id": wid})
        if path.startswith("widgets/") and method == "POST":
            self.widgets[path.split("/", 1)[1]] = kwargs["json"]["instance"]
            return Resp(200, {"id": path.split("/", 1)[1]})
        return Resp(404, {})


def status(report, part):
    for row in report:
        if part.lower() in row[1].lower():
            return row
    raise AssertionError((part, report))


def test_config_validation_and_markup():
    assert adsense_kit.normalize_client_id("ca-pub-123456") == "ca-pub-123456"
    assert adsense_kit.normalize_client_id("pub-123456") is None
    assert adsense_kit.normalize_client_id('ca-pub-123" onerror="x') is None
    with mock.patch.object(config, "ADSENSE_AUTO_ADS", True), \
         mock.patch.object(config, "ADSENSE_APPROVED", True):
        html = adsense_kit.build_widget_html("ca-pub-1234567890123456")
    assert "suads28" in html
    assert "pagead/js/adsbygoogle.js?client=ca-pub-1234567890123456" in html
    assert adsense_kit.build_widget_html("bad-id") == ""
    assert adsense_kit.ads_txt_line("ca-pub-123456") == (
        "google.com, pub-123456, DIRECT, f08c47fec0942fa0")
    with mock.patch.object(config, "ADSENSE_CLIENT_ID", "ca-pub-123456"), \
         mock.patch.object(config, "ADSENSE_AUTO_ADS", True), \
         mock.patch.object(config, "ADSENSE_APPROVED", False):
        assert adsense_kit.build_widget_html() == ""


def test_adsense_widget_is_idempotent():
    wp = WidgetWP()
    with mock.patch.object(config, "STATE_PATH", Path(tempfile.mkdtemp()) / "state.db"), \
         mock.patch.object(config, "ADSENSE_CLIENT_ID", "ca-pub-1234567890123456"), \
         mock.patch.object(config, "ADSENSE_ENABLED", True), \
         mock.patch.object(config, "ADSENSE_AUTO_ADS", True), \
         mock.patch.object(config, "ADSENSE_APPROVED", True):
        st, detail = adsense_kit.install(wp)
        assert st == "ok" and "installed" in detail
        assert wp.created == 1
        wid = next(iter(wp.widgets))
        encoded = wp.widgets[wid]["encoded"]
        assert "suads28" in encoded and "%3Cscript" in encoded
        st2, detail2 = adsense_kit.install(wp)
        assert st2 == "ok" and "up to date" in detail2
        assert wp.created == 1, "re-run must not create a duplicate widget"


def test_theme_audit_and_plugin_apply():
    class Fake:
        def __init__(self):
            self.themes = [{"slug": "twentytwentyfour", "name": "Twenty Twenty-Four",
                            "status": "active"}]
            self.plugins = []
            self.installs = []
            self.activations = []

        # Minimal surface for the full site setup audit.
        def public_get_status(self, path):
            if path == "/robots.txt":
                return 200, "User-agent: *\\n"
            return 200, ""

        def get_recent_published(self, per_page=1):
            return [{"link": "https://example.test/post/"}]

        def rest_namespaces(self):
            return ["wp/v2", "rankmath/v1"]

        def get_settings(self):
            return {"description": "Telugu", "timezone_string": "Asia/Kolkata",
                    "default_comment_status": "closed", "posts_per_page": 10,
                    "site_icon_url": "https://example.test/icon.png"}

        def get_page_by_slug(self, slug):
            return {"id": 1, "link": "https://example.test/" + slug + "/"}

        def get_menus(self):
            return [{"id": 1, "name": "studentup-legal"}]

        def get_menu_items(self, menu_id):
            return []

        def get_locations(self):
            return [{"name": "Footer", "location": "footer"}]

        def add_menu_item(self, menu_id, object_id, title, obj="page"):
            return True

        def update_menu(self, menu_id, payload):
            return True

        def list_categories(self):
            return []

        def list_themes(self):
            return self.themes

        def list_plugins(self):
            return list(self.plugins)

        def install_plugin(self, slug, activate=True):
            item = {"slug": slug, "plugin": f"{slug}/{slug}.php",
                    "status": "active" if activate else "inactive"}
            self.plugins.append(item)
            self.installs.append(slug)
            return item

        def activate_plugin(self, plugin_id):
            self.activations.append(plugin_id)
            for item in self.plugins:
                if item["plugin"] == plugin_id:
                    item["status"] = "active"
                    return item
            raise AssertionError(plugin_id)

    fake = Fake()
    dry = site_setup.audit_and_fix(fake, dry=True)
    assert status(dry, "Theme audit")[0] == "WARN"
    assert status(dry, "Plugin stack")[0] == "FIX?"
    assert not fake.installs
    site_setup.audit_and_fix(fake, dry=False)
    assert set(fake.installs) == {"rank-math", "redirection", "updraftplus", "wp-super-cache"}
    assert all(p["status"] == "active" for p in fake.plugins)
    assert fake.themes[0]["slug"] == "twentytwentyfour", "theme was not switched"


def test_wordpress_client_normalizes_routes_and_activation():
    wp = WordPressClient(site="https://example.test", username="u", password="p")
    calls = []
    responses = [
        Resp(200, [{"plugin": "rank-math/rank-math.php", "name": "Rank Math",
                   "status": "inactive", "slug": "rank-math"}]),
        Resp(201, {"plugin": "redirection/redirection.php", "status": "inactive"}),
        Resp(200, {"plugin": "redirection/redirection.php", "status": "active"}),
    ]

    def request(method, path, **kwargs):
        calls.append((method, path, kwargs))
        return responses.pop(0)

    wp._request = request
    plugins = wp.list_plugins()
    assert plugins[0]["slug"] == "rank-math"
    installed = wp.install_plugin("redirection", activate=True)
    assert installed["status"] == "active"
    assert calls[-1][0:2] == ("POST", "plugins/redirection/redirection.php")


def main():
    tests = [test_config_validation_and_markup,
             test_adsense_widget_is_idempotent,
             test_theme_audit_and_plugin_apply,
             test_wordpress_client_normalizes_routes_and_activation]
    for test in tests:
        test()
        print(f"  {test.__name__} ✔")
    print("ALL v28 TESTS PASSED ✔")


if __name__ == "__main__":
    main()
