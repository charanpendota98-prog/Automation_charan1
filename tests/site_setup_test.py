"""v22 site-setup tests: audit/fix logic against a fully fake WP admin client
(robots block, permalinks, sitemap, settings diff, footer menu create+assign,
category descriptions, idempotency, comment auto-close in create_post)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from autoblog import config  # noqa: E402
from autoblog import site_setup  # noqa: E402
from autoblog.wordpress_client import WordPressClient  # noqa: E402


class FakeWP:
    def __init__(self, *, robots="User-agent: *\n", sample_link=None,
                 sitemap=200, ns=("wp/v2", "rankmath/v1"), settings=None,
                 menus=None, cats=None, pages=None, locations=None):
        self.robots = robots
        self.sample_link = sample_link
        self.sitemap = sitemap
        self.ns = list(ns)
        self.settings = settings if settings is not None else {
            "description": "Just another site", "timezone_string": "UTC",
            "default_comment_status": "open", "posts_per_page": 10,
            "site_icon_url": ""}
        self.saved = {}
        self.menus = menus or []
        self.menu_items = {}
        self.next_menu_id = 100
        self.cats = cats or []
        self.updated_cats = []
        self.pages = pages or {}
        self.locations = locations or []
        self.created_pages = []

    # -- surface used by setup
    def check_connection(self):
        return True

    def public_get_status(self, path):
        if path == "/robots.txt":
            return (200, self.robots)
        if path.endswith("xml"):
            return (self.sitemap, "")
        return (404, "")

    def rest_namespaces(self):
        return self.ns

    def get_recent_published(self, per_page=8):
        return [{"link": self.sample_link}] if self.sample_link else []

    def get_settings(self):
        return dict(self.settings)

    def save_settings(self, payload):
        self.saved.update(payload)
        return True

    def get_menus(self):
        return list(self.menus)

    def create_menu(self, name, slug):
        self.next_menu_id += 1
        self.menus.append({"id": self.next_menu_id, "name": name})
        return self.next_menu_id

    def get_menu_items(self, menu_id):
        return list(self.menu_items.get(menu_id, []))

    def add_menu_item(self, menu_id, object_id, title, obj="page"):
        self.menu_items.setdefault(menu_id, []).append(
            {"title": title, "object_id": object_id})
        return True

    def update_menu(self, menu_id, payload):
        self.menu_items.setdefault(menu_id, [])
        self.assigned = payload.get("locations")
        return True

    def get_locations(self):
        return self.locations

    def list_categories(self):
        return list(self.cats)

    def update_category(self, cat_id, description):
        self.updated_cats.append((cat_id, description))
        return True

    def get_page_by_slug(self, slug):
        return self.pages.get(slug)

    def upload_media(self, *a, **k):
        return 77


def _status(rep, label_part):
    for st, label, detail in rep:
        if label_part.lower() in label.lower():
            return st, detail
    raise AssertionError(f"label '{label_part}' not in report: {[l for _, l, _ in rep]}")


def main():
    print("v22 SITE SETUP TESTS:")

    # ---- 1. blockers ----
    f = FakeWP(robots="User-agent: *\nDisallow: /\n")
    rep = site_setup.audit_and_fix(f, dry=True)
    st, det = _status(rep, "BLOCKED")
    assert st == "BLOCK" and "Reading" in det
    f2 = FakeWP(sample_link="https://x.com/?p=12")
    rep2 = site_setup.audit_and_fix(f2, dry=True)
    assert _status(rep2, "Permalinks")[0] == "BLOCK"
    assert site_setup.run_setup(dry=True, wp=f2) == 1  # exit code signals block
    print("  1. blockers (robots Disallow + ?p= permalinks → BLOCK/exit1) ✔")

    # ---- 2. warnings ----
    f3 = FakeWP(sitemap=404, ns=("wp/v2",))
    rep3 = site_setup.audit_and_fix(f3, dry=True)
    assert _status(rep3, "sitemap")[0] == "WARN"
    assert _status(rep3, "Rank Math")[0] == "WARN"
    assert _status(rep3, "Permalinks")[0] == "WARN"  # no sample post
    print("  2. warns (sitemap off, RankMath REST missing, no sample) ✔")

    # ---- 3. settings fix plan + apply + diff ----
    f4 = FakeWP(sample_link="https://studentup.in/ssc-cgl-2026/")
    rep4 = site_setup.audit_and_fix(f4, dry=True)
    st, det = _status(rep4, "General settings")
    assert st == "FIX?" and {"description", "timezone_string",
                             "default_comment_status"} <= set(det.split(", "))
    site_setup.audit_and_fix(f4, dry=False)
    assert f4.saved.get("description") == site_setup.TAGLINE
    assert f4.saved.get("timezone_string") == "Asia/Kolkata"
    assert f4.saved.get("default_comment_status") == "closed"
    # already-correct settings → nothing to write
    f5 = FakeWP(sample_link="https://studentup.in/x/", settings={
        "description": site_setup.TAGLINE, "timezone_string": "Asia/Kolkata",
        "default_comment_status": "closed", "posts_per_page": 10,
        "site_icon_url": "https://x/i.png"})
    rep5 = site_setup.audit_and_fix(f5, dry=True)
    assert _status(rep5, "General settings")[0] == "OK"
    assert _status(rep5, "Site icon")[0] == "OK"
    assert f5.saved == {}
    print("  3. settings: tagline/timezone/comments diff→fix, idempotent ✔")

    # ---- 4. footer legal menu: create + items + location ----
    pages = {sl: {"id": 10 + i, "link": f"https://studentup.in/{sl}/"}
             for i, sl in enumerate(
                 ["privacy-policy", "about-us", "contact-us",
                  "corrections-policy", "editorial-policy"])}
    f6 = FakeWP(sample_link="https://studentup.in/x/", pages=pages,
                locations=[{"name": "Footer", "location": "footer"}])
    f6.settings["site_icon_url"] = "x.png"
    site_setup.audit_and_fix(f6, dry=False)
    assert f6.menus, "menu create avvali"
    mid = f6.menus[0]["id"]
    titles = {it["title"] for it in f6.menu_items[mid]}
    assert {"Privacy Policy", "About Us", "Contact Us", "Corrections Policy",
            "Editorial Policy"} == titles
    assert getattr(f6, "assigned", None) == ["footer"]
    # idempotent: second run adds no items
    before = len(f6.menu_items[mid])
    site_setup.audit_and_fix(f6, dry=False)
    assert len(f6.menu_items[mid]) == before
    assert _status(site_setup.audit_and_fix(f6, dry=True),
                   "Footer legal menu")[0] == "OK"
    # no footer location → WARN with admin instruction
    f7 = FakeWP(sample_link="https://studentup.in/x/", pages=pages,
                locations=[])
    f7.settings["site_icon_url"] = "x.png"
    rep7 = site_setup.audit_and_fix(f7, dry=False)
    assert _status(rep7, "Footer menu location")[0] == "WARN"
    print("  4. footer menu (create+5 links+assign, idempotent, no-loc warn) ✔")

    # ---- 5. category descriptions: only-empty set + known map ----
    cats = [{"id": 1, "slug": "scholarships", "name": "Scholarships",
             "description": "", "count": 5},
            {"id": 2, "slug": "results", "name": "Results",
             "description": "already here", "count": 3},
            {"id": 3, "slug": "random", "name": "Random Cat",
             "description": "", "count": 1}]
    f8 = FakeWP(sample_link="https://x/y/", cats=cats)
    f8.settings["site_icon_url"] = "x.png"
    st8, det8 = _status(site_setup.audit_and_fix(f8, dry=True),
                        "Category descriptions")
    assert st8 == "FIX?" and "1 categories" in det8  # only Scholarships (mapped+empty)
    site_setup.audit_and_fix(f8, dry=False)
    assert f8.updated_cats == [(1, site_setup.CAT_DESCS["Scholarships"])]
    print("  5. category SEO copy (only empty+known set; existing untouched) ✔")

    # ---- 6. create_post payload: comments/pings closed on EVERY post ----
    captured = {}

    class T(WordPressClient):
        def __init__(self):
            self.site = "https://x"

        def _request(self, method, path, **kw):
            captured["p"] = kw.get("json")

            class R:
                status_code = 201
                ok = True

                def raise_for_status(self):
                    pass

                def json(self):
                    return {"id": 1, "link": "l", "status": "publish"}
            return R()

    t = T()
    t.create_post(title="T", content_html="<p>x</p>", slug="s",
                  category_id=None, tag_ids=[], excerpt="e", media_id=None)
    assert captured["p"]["comment_status"] == "closed"
    assert captured["p"]["ping_status"] == "closed"
    print("  6. new posts auto-closed comments+pings (spam/AdSense hygiene) ✔")

    # ---- 7. site icon auto-fix via SITE_LOGO_URL (network-mocked) ----
    f9 = FakeWP(sample_link="https://x/y/")  # site_icon_url "" → fix path

    def fake_get(url, timeout=None):
        class R:
            content = b"PNG"

            def raise_for_status(self):
                pass
        return R()

    import requests as _rq
    real_get = _rq.get
    _rq.get = fake_get
    try:
        old_logo = config.SITE_LOGO_URL
        config.SITE_LOGO_URL = "https://studentup.in/logo.png"

        def fake_upload(self, *a, **k):
            return 77

        f9.upload_media = lambda *a, **k: 77
        site_setup.audit_and_fix(f9, dry=False)
        assert f9.saved.get("site_icon") == 77
        config.SITE_LOGO_URL = old_logo
    finally:
        _rq.get = real_get
    print("  7. favicon auto-set from SITE_LOGO_URL (upload+settings) ✔")

    # ---- 8. clean site: everything OK, exit 0, zero writes ----
    clean = FakeWP(sample_link="https://studentup.in/good-post/",
                   settings={"description": site_setup.TAGLINE,
                             "timezone_string": "Asia/Kolkata",
                             "default_comment_status": "closed",
                             "posts_per_page": 10,
                             "site_icon_url": "https://x/i.png"},
                   menus=[{"id": 9, "name": "studentup-legal"}],
                   cats=[{"id": 1, "name": "Scholarships", "slug": "s",
                          "description": "x", "count": 1}])
    clean.menu_items = {9: [{"title": t0} for t0 in
                            ["Privacy Policy", "About Us", "Contact Us",
                             "Corrections Policy", "Editorial Policy"]]}
    clean.pages = {sl: {"id": 1, "link": "x"} for sl in
                   ["privacy-policy", "about-us", "contact-us",
                    "corrections-policy", "editorial-policy"]}
    rep = site_setup.audit_and_fix(clean, dry=False)
    bad = [r for r in rep if r[0] not in ("OK", "FIXED")]
    assert not bad, bad
    assert clean.saved == {}, "clean site lo settings write kaadu"
    assert site_setup.run_setup(dry=False, wp=clean) == 0
    print("  8. fully-clean site: 0 writes, all OK, exit 0 ✔")

    print("ALL v22 SITE SETUP TESTS PASSED ✔")


if __name__ == "__main__":
    main()
