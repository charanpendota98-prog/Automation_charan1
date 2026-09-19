"""v43 AD MANAGER — owner ads (college banners, shop, services).

Covers: inventory load/active/date-filter, selection (category match, cap,
AdSense cap tighten, determinism), UTM tagging, rendering (label + rel + XSS
escape + CLS + unsafe-link drop), injection (top/mid/bottom slots, no-op,
link-adjacency skip), demo page + CLI. No network, no WP.
"""
import sys
import json
import tempfile
from pathlib import Path
from datetime import date

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from autoblog import config, ad_manager  # noqa: E402

HERE = Path(__file__).resolve().parent.parent
# v48: rotation bookkeeping follows ADS_INVENTORY_PATH — keep it out of the repo
config.ADS_INVENTORY_PATH = str(Path(tempfile.mkdtemp(prefix="v43-ads-")) / "inventory.json")


def _inv(ads, policy=None):
    return {"version": 1, "policy": policy or {}, "ads": ads}


def _ad(**kw):
    base = {
        "id": "a1", "name": "N", "type": "college_banner", "layout": "banner",
        "active": True, "title": "T", "description": "D", "cta": "Go",
        "link": "https://college.example.edu/apply",
        "categories": "Admissions", "start": "2020-01-01", "end": "2099-12-31",
    }
    base.update(kw)
    return base


def _article(cat="Admissions", title="Sample"):
    return {"category": cat, "title": title,
            "content_html": _sample_content()}


def _sample_content():
    return (
        '<section class="su-quick-answer-card"><h2 id="quick-answer">QA</h2>'
        "<p class=\"su-qa\"><strong>answer here</strong></p></section>"
        "<p>" + ("useful long paragraph with enough words to count as a real "
                 "meaningful opening block for the placement engine. " * 3) + "</p>"
        "<h2>Eligibility</h2><p>eligibility text</p>"
        "<h2>Documents</h2><p>documents text</p>"
        '<h2 id="related-articles">Related</h2><p>related links here</p>'
    )


def test_inventory_load_default():
    # real repo inventory (rotation override below must not hide it)
    inv = ad_manager.load_inventory(HERE / "ads" / "inventory.json")
    assert isinstance(inv, dict) and "ads" in inv
    assert len(inv["ads"]) >= 1
    # missing / broken path → safe empty inventory (never raises)
    empty = ad_manager.load_inventory(Path("/nonexistent/nope.json"))
    assert empty["ads"] == []


def test_active_ads_date_filter():
    inv = _inv([_ad(id="ok"),
                _ad(id="inactive", active=False),
                _ad(id="past", end="2020-01-01"),
                _ad(id="future", start="2099-01-01")])
    active = {a["id"] for a in ad_manager.active_ads(inv, date(2026, 6, 1))}
    assert active == {"ok"}


def test_selection_category_cap_and_dedupe():
    inv = _inv([_ad(id="admit", categories="Admissions"),
                _ad(id="jobs", categories="Govt Jobs"),
                _ad(id="admit2", categories="Admissions")])
    picked = ad_manager.select_ads(_article("Admissions"), inv)
    ids = {a["id"] for a in picked}
    # only Admissions-eligible, capped at 2, no dupes
    assert ids <= {"admit", "admit2"} and len(picked) == 2
    # category with no match: v48 default = never-miss fallback (fair rotation)
    try:
        old_flag = getattr(config, "AD_FALLBACK_ALWAYS", True)
        config.AD_FALLBACK_ALWAYS = True
        assert len(ad_manager.select_ads(_article("Results"), inv, record=False)) == 2
        config.AD_FALLBACK_ALWAYS = False
        assert ad_manager.select_ads(_article("Results"), inv, record=False) == []
    finally:
        config.AD_FALLBACK_ALWAYS = old_flag


def test_selection_adsense_cap_tightens():
    inv = _inv([_ad(id="a", categories=""), _ad(id="b", categories="")])
    try:
        old = getattr(config, "ADSENSE_APPROVED", False)
        config.ADSENSE_APPROVED = False
        assert len(ad_manager.select_ads(_article(), inv)) == 2
        config.ADSENSE_APPROVED = True
        assert len(ad_manager.select_ads(_article(), inv)) == 1
    finally:
        config.ADSENSE_APPROVED = old


def test_selection_deterministic():
    # unique ids + clean rotation so this test never depends on test order
    rot = ad_manager._rotation_path()
    try:
        rot.unlink()
    except FileNotFoundError:
        pass
    inv = _inv([_ad(id="rot-a", categories=""), _ad(id="rot-b", categories=""),
                _ad(id="rot-c", categories="")])
    # read-only (record=False): same day+category → same order, no state touched
    a1 = [x["id"] for x in ad_manager.select_ads(_article(), inv, record=False)]
    a2 = [x["id"] for x in ad_manager.select_ads(_article(), inv, record=False)]
    assert a1 == a2, (a1, a2)
    # v48 rotation: real calls record "last shown", so the next post gets the
    # ad that waited longest — every active ad gets its turn (never missed).
    pick1 = [x["id"] for x in ad_manager.select_ads(_article(), inv)]
    pick2 = [x["id"] for x in ad_manager.select_ads(_article(), inv)]
    unseen = ({"rot-a", "rot-b", "rot-c"} - set(pick1)).pop()
    assert pick2[0] == unseen, (pick1, pick2)  # the ad waiting longest runs next


def test_utm_tagging_and_existing_query():
    pol = ad_manager.policy_of(_inv([]))
    u = ad_manager.utm_url("https://x.edu/apply", "camp1", "top", pol)
    assert "utm_source=studentup.in" in u and "utm_medium=sponsored" in u
    assert "utm_campaign=camp1" in u and "utm_content=top" in u
    u2 = ad_manager.utm_url("https://x.edu/apply?ref=old", "c", "mid", pol)
    assert "ref=old" in u2 and "utm_campaign=c" in u2
    # unsafe (no netloc) → returned unchanged (caller renders empty)
    assert ad_manager.utm_url("not-a-url", "c", "top", pol) == "not-a-url"


def test_render_label_rel_and_xss():
    inv = _inv([])
    pol = ad_manager.policy_of(inv)
    evil = _ad(id="evil", title="<script>alert(1)</script>",
               link="https://college.example.edu",
               description='x"onload="y')
    html = ad_manager.render_ad(evil, "top", pol)
    assert "<script>alert(1)" not in html          # escaped, not injected
    assert "alert(1)" in html                      # text kept, safe
    assert "rel=\"sponsored nofollow noopener\"" in html
    assert "target=\"_blank\"" in html
    assert "SPONSORED" in html.upper()             # visible label
    assert "su-ad" in html                         # CLS-safe block class
    # unsafe link → empty (block dropped entirely)
    assert ad_manager.render_ad(_ad(link="javascript:alert(1)"), "top", pol) == ""
    assert ad_manager.render_ad(_ad(link=""), "top", pol) == ""
    # card layout renders compact
    assert "su-ad-card" in ad_manager.render_ad(_ad(layout="card"), "mid", pol)


def test_inject_slots_and_noop():
    inv = _inv([_ad(id="a", categories=""), _ad(id="b", categories="")])
    html, report = ad_manager.inject(_sample_content(), _article(), inv)
    assert len(report) == 2
    slots = {r["slot"] for r in report}
    assert slots == {"top", "mid"}
    # top ad sits after quick-answer, before the long paragraph
    qa_end = html.find("</section>")
    first_ad = html.find('class="su-ad')
    assert qa_end < first_ad < html.find("useful long paragraph")
    # exactly one injected CSS block (unique CSS-only sentinel, appears once)
    assert html.count(".su-ad{margin:22px 0;") == 1
    # empty inventory → no-op (html unchanged, empty report)
    h2, r2 = ad_manager.inject(_sample_content(), _article(), _inv([]))
    assert h2 == _sample_content() and r2 == []
    # disabled → no-op
    try:
        old = config.AD_MANAGER_ENABLED
        config.AD_MANAGER_ENABLED = False
        h3, r3 = ad_manager.inject(_sample_content(), _article(), inv)
        assert h3 == _sample_content() and r3 == []
    finally:
        config.AD_MANAGER_ENABLED = old


def test_inject_link_adjacency_skip():
    # a link sits right where the top slot would land → top skipped, not forced
    content = (
        '<section class="su-quick-answer-card"><h2 id="quick-answer">QA</h2>'
        '<p><a href="https://x.test">right here</a></p></section>'
        "<p>" + ("filler words for a real paragraph in the content " * 6) + "</p>"
        "<h2>H</h2><p>mid text</p>"
        '<h2 id="related-articles">R</h2><p>end</p>'
    )
    inv = _inv([_ad(id="a", categories="")])
    html, report = ad_manager.inject(content, _article(), inv)
    assert any(r["slot"] == "top" and r["status"] == "skipped" for r in report)
    # the ad must NOT be glued to that link
    assert 'right here</a></p></section>\n<section class="su-ad' not in html


def test_bottom_slot_before_related():
    inv = _inv([_ad(id="a", categories=""), _ad(id="b", categories=""),
                _ad(id="c", categories="")],
               policy={"max_personal_ads_per_post": 3})
    try:
        old = config.MAX_PERSONAL_AD_SLOTS
        config.MAX_PERSONAL_AD_SLOTS = 3
        html, report = ad_manager.inject(_sample_content(), _article(), inv)
        assert "bottom" in {r["slot"] for r in report}
        ad_bottom = html.rfind('data-slot="bottom"')
        related = html.find('<h2 id="related-articles"')
        assert ad_bottom < related  # bottom slot lands BEFORE related block
    finally:
        config.MAX_PERSONAL_AD_SLOTS = old


def test_demo_page_and_cli(tmp=None):
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "ads-preview.html"
        p = ad_manager.demo_page(ad_manager.load_inventory(), out)
        assert p == out and out.exists()
        txt = out.read_text(encoding="utf-8")
        assert "su-ad" in txt and "SPONSORED" in txt.upper()
        assert "Placement report" in txt
    # CLI status returns 0 and prints inventory
    assert ad_manager.run_cli("status") == 0


def test_pipeline_never_blocks_on_broken_inventory():
    # broken JSON on disk → inject is a no-op, publish path keeps working
    with tempfile.TemporaryDirectory() as td:
        bad = Path(td) / "bad.json"
        bad.write_text("{not valid json", encoding="utf-8")
        try:
            old = config.ADS_INVENTORY_PATH
            config.ADS_INVENTORY_PATH = str(bad)
            html, report = ad_manager.inject(_sample_content(), _article())
            assert html == _sample_content() and report == []
        finally:
            config.ADS_INVENTORY_PATH = old


def main():
    test_inventory_load_default()
    print("  inventory load + broken-file safety ✔")
    test_active_ads_date_filter()
    print("  active/date filter ✔")
    test_selection_category_cap_and_dedupe()
    print("  selection (category/cap/dedupe) ✔")
    test_selection_adsense_cap_tightens()
    print("  AdSense cap tighten ✔")
    test_selection_deterministic()
    print("  deterministic rotation ✔")
    test_utm_tagging_and_existing_query()
    print("  UTM tagging ✔")
    test_render_label_rel_and_xss()
    print("  render label+rel+XSS+CLS+unsafe-drop ✔")
    test_inject_slots_and_noop()
    print("  inject slots + no-op ✔")
    test_inject_link_adjacency_skip()
    print("  link-adjacency skip ✔")
    test_bottom_slot_before_related()
    print("  bottom slot before related ✔")
    test_demo_page_and_cli()
    print("  demo page + CLI ✔")
    test_pipeline_never_blocks_on_broken_inventory()
    print("  broken inventory never blocks publish ✔")
    print("ALL v43 AD MANAGER TESTS PASSED ✔")


if __name__ == "__main__":
    main()
