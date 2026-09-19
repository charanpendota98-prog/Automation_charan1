# -*- coding: utf-8 -*-
"""v48 tests — public policy pages + SEO files + "never miss an ad" guarantee.

Offline only. Run: python tests/v48_test.py   (also via python run.py --test-all)
"""
from __future__ import annotations

import json
import os
import re
import sys
import tempfile
from datetime import date, timedelta
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

PREVIEW = ROOT / "preview"
PAGES = PREVIEW / "pages"
POLICY_PAGES = ["about", "contact", "privacy", "disclaimer", "editorial-policy"]
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta",
        "param", "source", "track", "wbr"}


class _Struct(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack, self.errs = [], []

    def handle_starttag(self, tag, attrs):
        if tag not in VOID:
            self.stack.append((tag, self.getpos()[0]))

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        if not self.stack:
            self.errs.append("stray </%s> line %d" % (tag, self.getpos()[0]))
            return
        if self.stack[-1][0] == tag:
            self.stack.pop()
            return
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                self.errs.append("unclosed <%s> (line %d)" % (self.stack[-1][0], self.stack[-1][1]))
                del self.stack[i:]
                return
        self.errs.append("stray </%s> line %d" % (tag, self.getpos()[0]))


def _t(name: str) -> str:
    return (PAGES / (name + ".html")).read_text(encoding="utf-8")


def test_policy_pages_exist_and_are_well_formed():
    for slug in POLICY_PAGES:
        p = PAGES / (slug + ".html")
        assert p.exists(), "missing page: " + slug
        html = p.read_text(encoding="utf-8")
        chk = _Struct()
        chk.feed(html)
        assert not chk.stack and not chk.errs, (slug, chk.stack[:3], chk.errs[:3])
        # v73: English UI — pages lang="en" + og:locale en_IN (+ ld inLanguage en-IN)
        assert '<html lang="en">' in html, slug + " lang=en kaadu"
        assert 'property="og:locale" content="en_IN"' in html, slug + " og:locale ledu"
        assert '"inLanguage":"en-IN"' in html, slug + " ld inLanguage ledu"
        assert "<h1>" in html and "</h1>" in html
        assert 'rel="canonical"' in html and "studentup.in" in html
    print("  policy pages: 5 exist, valid HTML, lang=en + og:locale, canonical ✔")


def test_policy_pages_are_english_and_link_back():
    """v73: mee brief — UI antha English (Telugu mattrame article content lo)."""
    for slug in POLICY_PAGES:
        html = _t(slug)
        telugu = len(re.findall(r"[\u0C00-\u0C7F]", html))
        assert telugu == 0, (slug, telugu)  # v73: pages antha English
        assert 'href="../index.html"' in html, slug + ": no back-home link"
        for other in POLICY_PAGES:
            assert (other + ".html") in html, "%s missing link to %s" % (slug, other)
    print("  policy pages: English (0 Telugu chars) + cross-linked ✔")


def test_contact_page_has_real_channels():
    html = _t("contact")
    assert "studentupinformative@gmail.com" in html
    assert "mailto:" in html and "t.me/studentup_in" in html
    assert "OTP" in html and "Aadhaar" in html, "fraud warning must be present"
    print("  contact page: email + Telegram + no-OTP fraud warning ✔")


def test_privacy_and_disclaimer_cover_required_points():
    priv = _t("privacy")
    for point in ["AdSense", "cookie", "poll", "data"]:
        assert point in priv, "privacy missing: " + point
    disc = _t("disclaimer")
    for point in ["government website", "never guaranteed", "SPONSORED",
                  "sponsored nofollow", "fraud"]:
        assert point in disc, "disclaimer missing: " + point
    print("  privacy: cookies/poll/AdSense · disclaimer: no-guarantee/fraud/sponsored ✔")


def test_editorial_policy_lists_five_gates():
    html = _t("editorial-policy")
    for gate in ["Source check", "cross-verification", "72%", "Human review", "SPONSORED"]:
        assert gate in html, "editorial policy missing gate: " + gate
    assert "24" in html, "correction turnaround missing"
    print("  editorial policy: 5 gates + correction window + ad independence ✔")


def test_seo_files_present_and_consistent():
    robots = (PREVIEW / "robots.txt").read_text(encoding="utf-8")
    assert "Sitemap: https://studentup.in/sitemap.xml" in robots
    assert "Mediapartners-Google" in robots, "AdSense crawler must be allowed"
    assert "Disallow: /admin" in robots
    sm = (PREVIEW / "sitemap.xml").read_text(encoding="utf-8")
    locs = re.findall(r"<loc>([^<]+)</loc>", sm)
    assert len(locs) >= 6, locs
    for loc in locs:
        rel = loc.replace("https://studentup.in/", "").strip("/") or "index.html"
        target = PREVIEW / (rel if rel.endswith(".html") else rel + "/index.html")
        assert target.exists(), "sitemap url has no file: %s" % loc
    fav = (PREVIEW / "favicon.svg").read_text(encoding="utf-8")
    assert fav.startswith("<svg") and "#0f2e62" in fav
    print("  robots.txt + sitemap.xml (all urls exist) + favicon.svg ✔")


def test_index_links_real_pages_not_dead_anchors():
    html = (PREVIEW / "index.html").read_text(encoding="utf-8")
    for slug in POLICY_PAGES:
        assert ("pages/%s.html" % slug) in html, "index does not link " + slug
    dead = re.findall(r'href="#trust">(?:Editorial|Corrections|Privacy)', html)
    assert not dead, "policy links still dead-end on #trust: %d" % len(dead)
    assert 'rel="icon"' in html and "favicon.svg" in html
    for slug in POLICY_PAGES:
        target = PAGES / (slug + ".html")
        assert target.exists()
    print("  index: 5 real page links (13 places), no dead policy anchors, favicon ✔")


def test_every_public_page_carries_a_labeled_ad_slot():
    files = [PREVIEW / "index.html"] + [PAGES / (s + ".html") for s in POLICY_PAGES]
    for f in files:
        html = f.read_text(encoding="utf-8")
        assert "SPONSORED" in html, f.name + ": no labeled ad slot"
        assert 'aria-label="Sponsored content"' in html or "su-ad-kicker" in html
        if f.name != "index.html":
            assert 'rel="sponsored"' in html, f.name + ": ad link not rel=sponsored"
    print("  every public page carries a clearly-labelled SPONSORED slot ✔")


# ---------------------------------------------------------- ads never missed

def _inv_file(ads) -> Path:
    d = Path(tempfile.mkdtemp(prefix="v48-ads-"))
    p = d / "inventory.json"
    p.write_text(json.dumps({"version": 1,
                             "policy": {"label": "SPONSORED", "max_personal_ads_per_post": 2},
                             "ads": ads}, ensure_ascii=False), encoding="utf-8")
    os.environ["ADS_INVENTORY_PATH"] = str(p)
    # config reads env at import time — reload it so every module sees the temp file
    import importlib
    if "autoblog.config" in sys.modules:
        importlib.reload(sys.modules["autoblog.config"])
    for extra in ("rotation.json",):
        try:
            (d / extra).unlink()
        except FileNotFoundError:
            pass
    return p


def _ad(i, cats="", active=True, demo=False):
    return {"id": i, "name": i, "title": "ప్రకటన " + i, "type": "shop", "layout": "card",
            "link": "https://example.com/" + i, "categories": cats, "active": active,
            "demo": demo, "start": "2020-01-01", "end": "2030-12-31"}


def test_no_category_match_still_shows_an_ad():
    from autoblog import ad_manager
    _inv_file([_ad("college-ad-1", cats="Admissions")])
    art = {"title": "SSC ఫలితాలు విడుదల", "category": "Results"}
    picked = ad_manager.select_ads(art, ad_manager.load_inventory(), record=False)
    assert [a["id"] for a in picked] == ["college-ad-1"], \
        "category miss must fall back, not drop the ad"
    print("  guarantee: category miss → ad still placed (no silent miss) ✔")


def test_all_inactive_means_no_ads_honestly():
    from autoblog import ad_manager
    _inv_file([_ad("off-ad", active=False)])
    picked = ad_manager.select_ads({"title": "x", "category": "Jobs"},
                                   ad_manager.load_inventory(), record=False)
    assert picked == [], "inactive ads must never be forced in"
    print("  guarantee: nothing active → clean empty (no fake ads) ✔")


def test_rotation_shows_every_ad_in_turn():
    from autoblog import ad_manager
    _inv_file([_ad("ad-1"), _ad("ad-2"), _ad("ad-3")])
    inv = ad_manager.load_inventory()
    day = date(2026, 9, 18)
    seen = []
    for i in range(12):  # 12 posts over 12 days, cap=2 per post
        picked = ad_manager.select_ads({"title": "post %d" % i, "category": "Jobs"},
                                       inv, today=day + timedelta(days=i), record=True)
        seen.extend(a["id"] for a in picked)
    assert set(seen) == {"ad-1", "ad-2", "ad-3"}, "not every ad got its turn: %s" % set(seen)
    rot = json.loads((Path(os.environ["ADS_INVENTORY_PATH"]).parent / "rotation.json")
                     .read_text(encoding="utf-8"))
    assert all(k in rot for k in ("ad-1", "ad-2", "ad-3")), rot
    print("  guarantee: fair rotation — every active ad gets shown (%d picks) ✔" % len(seen))


def test_real_ads_beat_demo_ads():
    from autoblog import ad_manager
    _inv_file([_ad("demo-college", demo=True), _ad("real-shop")])
    picked = ad_manager.select_ads({"title": "t", "category": "Jobs"},
                                   ad_manager.load_inventory(), record=False)
    assert picked[0]["id"] == "real-shop", "paying/real ad must outrank demo placeholder"
    print("  guarantee: real partner ad outranks demo placeholder ✔")


def test_cap_and_policy_still_respected():
    from autoblog import ad_manager
    _inv_file([_ad("a-%d" % i) for i in range(6)])
    inv = ad_manager.load_inventory()
    picked = ad_manager.select_ads({"title": "t", "category": "Jobs"}, inv, record=False)
    assert len(picked) == 2, "policy cap (2/post) must hold: %d" % len(picked)
    inv["policy"]["max_personal_ads_per_post"] = 4
    picked4 = ad_manager.select_ads({"title": "t", "category": "Jobs"}, inv, record=False)
    assert len(picked4) == 2, "config MAX_PERSONAL_AD_SLOTS (env) is the hard cap: %d" % len(picked4)
    from autoblog import config as cfg
    old_cap = getattr(cfg, "MAX_PERSONAL_AD_SLOTS", 2)
    try:
        cfg.MAX_PERSONAL_AD_SLOTS = 4
        picked_env = ad_manager.select_ads({"title": "t", "category": "Jobs"}, inv, record=False)
        assert len(picked_env) == 4, len(picked_env)
    finally:
        cfg.MAX_PERSONAL_AD_SLOTS = old_cap
    print("  guarantee: caps hold — policy 2, env hard cap, owner can raise to 4 ✔")


def test_plan_does_not_consume_rotation():
    from autoblog import ad_manager
    _inv_file([_ad("p-1")])
    before = (Path(os.environ["ADS_INVENTORY_PATH"]).parent / "rotation.json")
    ad_manager.plan({"title": "t", "category": "Jobs"})
    assert not before.exists(), "dry plan must not mark ads as shown"
    print("  guarantee: --ads plan is read-only (rotation untouched) ✔")


def test_inject_end_to_end_with_fallback():
    from autoblog import ad_manager
    _inv_file([_ad("only-ad", cats="Scholarships")])
    html = "<html><body><article><h1>Post</h1><p>%s</p></article></body></html>" % ("word " * 300)
    out, report = ad_manager.inject(html, {"title": "TSPSC నోటిఫికేషన్", "category": "Jobs"},
                                    inv=ad_manager.load_inventory())
    assert "only-ad" in out or "SPONSORED" in out.upper(), report
    assert out != html, "ad was not injected despite an active ad"
    assert "sponsored" in out.lower(), "rel=sponsored missing"
    print("  guarantee: inject() places the ad even on a category miss ✔")


def main() -> None:
    test_policy_pages_exist_and_are_well_formed()
    test_policy_pages_are_english_and_link_back()
    test_contact_page_has_real_channels()
    test_privacy_and_disclaimer_cover_required_points()
    test_editorial_policy_lists_five_gates()
    test_seo_files_present_and_consistent()
    test_index_links_real_pages_not_dead_anchors()
    test_every_public_page_carries_a_labeled_ad_slot()
    test_no_category_match_still_shows_an_ad()
    test_all_inactive_means_no_ads_honestly()
    test_rotation_shows_every_ad_in_turn()
    test_real_ads_beat_demo_ads()
    test_cap_and_policy_still_respected()
    test_plan_does_not_consume_rotation()
    test_inject_end_to_end_with_fallback()
    print("ALL v48 POLICY-PAGE + ADS-GUARANTEE TESTS PASSED ✔")


if __name__ == "__main__":
    main()
