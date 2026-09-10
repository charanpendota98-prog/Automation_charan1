"""v20 playbook tests: hub pages (authority cluster), real bylines for
Google News/E-E-A-T, AdSense-safe ad placement (first meaningful paragraph
+ how-to anchor), disclosed featured-listing CTA, editorial policy page,
weekly auto-rebuild wiring."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from autoblog import config, hubs, monetize, seo  # noqa: E402
from autoblog.wordpress_client import WordPressClient  # noqa: E402

POSTS = [
    {"title": "SSC CGL 2026 Notification Apply Online",
     "link": "https://studentup.in/ssc-cgl-2026-notification/",
     "date": "2026-09-01T10:00:00"},
    {"title": "SSC CGL Mains Result 2026 Declared",
     "link": "https://studentup.in/ssc-cgl-mains-result-2026/",
     "date": "2026-09-05T10:00:00"},
    {"title": "SSC CGL Cut Off Trends 2024 2025",
     "link": "https://studentup.in/ssc-cgl-cut-off/", "date": "2026-09-07"},
]


class FakeWP:
    def __init__(self, hits=None, upserts=None):
        self.hits = hits or {}
        self.upserts = upserts if upserts is not None else []

    def search_posts(self, term, per_page=12):
        return self.hits.get(term, [])

    def upsert_page(self, title, html, slug):
        self.upserts.append({"title": title, "slug": slug, "html": html})
        return {"id": 99, "link": f"{config.WP_SITE}/{slug}/"}


def main():
    print("v20 HUBS + BYLINES + PLACEMENT TESTS:")

    # ---- 1. hub builder: links, cross-hub cluster, no self-link, honest ----
    h = hubs.build_hub_html("SSC CGL", POSTS, 2026,
                            ["SSC CGL", "TET", "RRB ALP"])
    assert h.count("<tr><td><a href=") == 3, "3 post rows"
    assert "tet-hub" in h and "rrb-alp-hub" in h
    assert 'href="' + config.WP_SITE.rstrip("/") + '/ssc-cgl-hub/"' not in h
    assert "mailto:" in h and "Last updated" in h
    assert "2026-09-01" in h
    # thin hub content can't exist: builder never emits empty shelf (guarded
    # upstream by <2 skip) and links are <=12 rows
    h_big = hubs.build_hub_html("X", POSTS * 6, 2026, ["X", "Y"])
    assert h_big.count("<tr><td><a href=") == 12

    # ---- 2. rebuild_hubs: thin-exam skip + idempotent upsert ----
    real_cls = hubs.WordPressClient
    fake = FakeWP(hits={"SSC CGL": POSTS, "TET": POSTS[:1]})
    hubs.WordPressClient = lambda *a, **k: fake
    old_exams = config.HUB_EXAMS
    config.HUB_EXAMS = ["SSC CGL", "TET", "Ghost Exam"]
    try:
        rows = hubs.rebuild_hubs()
    finally:
        hubs.WordPressClient = real_cls
        config.HUB_EXAMS = old_exams
    assert [r["exam"] for r in rows] == ["SSC CGL"], rows  # thin/0 skipped
    assert len(fake.upserts) == 1
    assert fake.upserts[0]["slug"] == "ssc-cgl-hub"
    assert "2026 Hub" in fake.upserts[0]["title"]

    # ---- 3. upsert_page: PUT when exists, POST when new ----
    calls = []

    class T(WordPressClient):
        def __init__(self):
            pass

        def get_page_by_slug(self, slug):
            return {"id": 5, "link": "x"} if slug == "old-hub" else None

        def _request(self, method, path, **kw):
            calls.append((method, path))

            class R:
                ok = True
                status_code = 200

                def raise_for_status(self):
                    pass

                def json(self):
                    return {"id": 5, "link": "y"}
            return R()

    t = T()
    t.upsert_page("A", "<p>x</p>", "old-hub")
    t.upsert_page("A", "<p>x</p>", "new-hub")
    assert calls == [("PUT", "pages/5"), ("POST", "pages")], calls
    print("  1-3. hubs (build/skip-thin/upsert PUT+POST) ✔")

    # ---- 4. real bylines: deterministic rotation + schema + visible ----
    a1 = seo.author_for_slug("ssc-cgl-2026")
    assert a1 == seo.author_for_slug("ssc-cgl-2026")
    seen = {seo.author_for_slug(f"s{i}")[0] for i in range(40)}
    assert len(seen) >= 2, seen
    out = seo.enhance("<p>" + "word " * 300 + "</p>", "kw", [], [],
                      slug="byline-test", title="T", description="d" * 140,
                      date_str="2026-09-10")
    assert "\u270d\ufe0f" in out and "Editorial review: 2026-09-10" in out
    assert '"jobTitle"' in out and '"newsMaterialCategory"' in out
    print(f"  4. real bylines rotate ({len(seen)} authors) + schema ✔")

    # ---- 5. ad placement playbook: first MEANINGFUL para + apply-H2 anchor --
    short = "<p>tiny para.</p>" * 6
    i = seo.insert_ad_shortcodes(short, "[ad]", max_ads=2)
    assert i.count("[ad]") <= 2 and i.index("[ad]") > i.index("<p>")
    long1 = ("<p>" + "filler word " * 60 + "</p>"
             "<p>" + "more filler " * 40 + "</p>")
    j = seo.insert_ad_shortcodes(long1, "[ad]", max_ads=1)
    first_end = j.index("</p>")
    assert j[first_end + 4:].startswith('\n<div style="min-height:280px">[ad]'), \
        j[first_end:first_end + 60]
    k = ("<h2>SSC CGL Overview</h2><p>" + "a " * 10 + "</p>"
         "<h2>How to Apply Online?</h2><p>" + "b " * 10 + "</p>"
         "<p>" + "c " * 10 + "</p><p>" + "d " * 10 + "</p>")
    m = seo.insert_ad_shortcodes(k, "[ad]", max_ads=3)
    assert m.count("[ad]") >= 1
    pos_apply = k.index("How to Apply")
    # ad placed right after apply-section's first para → in output it comes
    # after that H2 position (approx; insert shifts indexes)
    seg = m[pos_apply:pos_apply + 400]
    assert "[ad]" in seg, "apply H2 tarvata ad unali"
    print("  5. ad placement (first meaningful para + how-to anchor) ✔")

    # ---- 6. featured listing (disclosed) + editorial policy page ----
    old_c = config.FEATURED_CTA_HTML
    config.FEATURED_CTA_HTML = '<a href="https://x.co">Coaching offer</a>'
    try:
        fb = monetize.featured_block()
        assert "Sponsored" in fb and "x.co" in fb
        html2 = monetize.append_blocks("<p>body</p>", {"title": "t",
                                                       "category": "c"})
        assert "Sponsored" in html2
    finally:
        config.FEATURED_CTA_HTML = old_c
    assert not monetize.featured_block()  # unset → clean
    from autoblog import main as ab_main
    titles = [pg[0] for pg in ab_main.ADSENSE_PAGES]
    assert "Editorial Policy" in titles
    assert "guessing banned" in ab_main.EDITORIAL_HTML
    assert "human editorial review" in ab_main.EDITORIAL_HTML
    print("  6. featured CTA disclosure + editorial policy page ✔")

    # ---- 7. weekly auto wiring + search fields ----
    src = (Path(__file__).resolve().parent.parent / "autoblog"
           / "main.py").read_text(encoding="utf-8")
    assert "hubweek:" in src and "--rebuild-hubs" in src
    assert "Google News" in src and "Auto Ads audit" in src
    wsrc = (Path(__file__).resolve().parent.parent / "autoblog"
            / "wordpress_client.py").read_text(encoding="utf-8")
    assert "search_posts" in wsrc and "_fields" in wsrc
    print("  7. weekly hub auto-rebuild + GNews checklist wired ✔")

    print("ALL v20 TESTS PASSED \u2714")


if __name__ == "__main__":
    main()
