# -*- coding: utf-8 -*-
"""v77 tests — ORIGINAL CONTENT ENGINE + HIGH-ADS READINESS.

Enduku idi:
  "100% scores dummy aa, Google accept chestunda?" — doubt ki answer:
  (1) URL flow ippudu source lopala official links kuda gather chestundi
  (related facts richest); (2) rewrite-distance = REAL copy % (donor vs
  final); (3) update = news-sitemap re-entry (trending); (4) ads page-to-page
  fresh rotation; (5) networks apply kit ready.

Checks (offline only):
  * outbound rank: official-first · same-site last · social out
  * fetch outbound: article HTML nunchi links extract (synthetic DOM)
  * research follows official outbound (local HTTP, search mocked off)
  * rewrite_distance: copy→copy-risk · fresh→fresh (REAL numbers)
  * pipeline _originality wired (FakeWP publish, copy + fresh cases)
  * news-sitemap: publish OR modified 48h (update re-entry)
  * rotation smart: hour-base + slot offset + no-repeat (v61 rebase hold)
  * ad automation: auto-head gated · in-article auto · density cap ·
    consent gate · AdSense refresh ledu (policy)
  * update freshness chain: modified + indexnow + badge + upd: handler
  * docs: README v77 + MANUAL PART 36 + 71/71 + networks kit

Run: python tests/v77_test.py   (also via python run.py --test-all)
"""
from __future__ import annotations

import functools
import http.server
import sys
import tempfile
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from autoblog import config, pipeline, research, sources, state, validator  # noqa: E402
from autoblog.sources import SourceArticle  # noqa: E402

PREVIEW = ROOT / "preview"
THEME = ROOT / "wordpress-theme" / "studentup"


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


LONG_A = ("TSPSC Group 2 notification vachindi. Apply online link active. "
          "Fee details official site lo unnayi. Syllabus PDF download. "
          "Exam date December. Hall tickets November. Vacancies 500. "
          "Eligibility degree pass. Age limit 18-44. Selection written test. "
          "Documents aadhaar marksheets photos. Last date check cheyandi. "
          "Official website tspsc gov in. Preparation books list. "
          "Previous papers practice. Cutoff marks analysis. Result date. "
          "Counselling schedule district wise. Certificate verification slots. "
          "Helpline numbers working hours. Grievance portal complaint status. ")
LONG_B = ("Vaanakalam lo rytu bazar rates perigayi. Tomato kilo 40 rupees. "
          "Onion stocks thaggayi market lo. Weather report prakaram varsham. "
          "Cricket match Sunday stadium lo. Cinema tickets online booking. "
          "Bus timings marayi city lo. Park renovation complete ayyindi. "
          "Library books kothavi vachayi. School holidays extend ayyayi. "
          "Hospital camp free checkup. Bank loan mela Saturday. "
          "Traffic diversion main road. Festival shopping offers. "
          "Museum entry tickets weekend rush. Zoo safari timings revised. "
          "Stadium parking tokens online sale. Auditorium shows booking open. ")


# ------------------------------------------------- 1-3. outbound gather

def test_outbound_rank_official_first():
    links = ["https://blog.example.com/post", "https://tspsc.gov.in/abc",
             "https://x.com/share", "https://scholarships.gov.in/x",
             "https://same.example.com/other"]
    ranked = sources.rank_outbound(links, "https://same.example.com/page")
    assert ranked[0] == "https://tspsc.gov.in/abc", ranked
    assert ranked[1] == "https://scholarships.gov.in/x", ranked
    assert "https://x.com/share" not in ranked, "social out avvali"
    assert ranked[-1] == "https://same.example.com/other", "same-site last"
    print("  outbound rank: official-first · same-site last · social out ✔")


def test_fetch_outbound_from_dom():
    from bs4 import BeautifulSoup

    html = ("<html><body><article><p>" + "x" * 40 + "</p>"
            '<a href="https://tspsc.gov.in/notif">notif</a>'
            '<a href="/relative/page">rel</a>'
            '<a href="https://facebook.com/s">fb</a>'
            '<a href="#frag">skip</a></article>'
            "<nav><a href='https://nav.example.com/'>nav</a></nav></body></html>")
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["nav"]):
        tag.decompose()
    links = sources._page_links(soup.find("article"), "https://a.example.org/p")
    assert "https://tspsc.gov.in/notif" in links, links
    assert "https://a.example.org/relative/page" in links, links
    assert not any("facebook.com" in u for u in links), links
    assert not any("nav.example.com" in u for u in links), links
    print("  fetch outbound: extract + absolute + social/nav out ✔")


def _serve(root: Path):
    handler = functools.partial(http.server.SimpleHTTPRequestHandler,
                                directory=str(root))
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


def test_research_follows_official():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "off.html").write_text(
            "<html><head><title>Official Memo</title></head><body><article><p>"
            + LONG_A + "</p></article></body></html>", encoding="utf-8")
        srv = _serve(root)
        srv2 = _serve(root)
        try:
            base = f"http://127.0.0.1:{srv.server_address[1]}"
            off = f"http://127.0.0.1:{srv2.server_address[1]}"
            primary = SourceArticle(url=base + "/main", title="Group 2",
                                    text=LONG_A, outbound=[off + "/off.html"])
            old_search = research.search_web
            research.search_web = lambda *a, **k: []
            try:
                extras, _titles = research.research_topic(primary, 3)
            finally:
                research.search_web = old_search
            assert len(extras) == 1, f"official follow avvaledu: {extras}"
            assert "Official Memo" in extras[0].title, extras[0].title
        finally:
            srv.shutdown()
            srv2.shutdown()
    print("  research: official outbound follow (search off kuda) ✔")


# ------------------------------------------------- 4-5. originality

def test_rewrite_distance_real_numbers():
    same = validator.rewrite_distance(f"<p>{LONG_A}</p>", [LONG_A])
    assert same["overlap"] > 0.85 and same["verdict"] == "copy-risk", same
    fresh = validator.rewrite_distance(f"<p>{LONG_B}</p>", [LONG_A])
    assert fresh["fresh"] > 0.70 and fresh["verdict"] == "fresh", fresh
    short = validator.rewrite_distance("<p>hi</p>", [LONG_A])
    assert short["verdict"] == "short", short
    print(f"  rewrite_distance: copy {same['overlap']} · fresh {fresh['fresh']} ✔")


class _FakeWP:
    def check_connection(self):
        return True

    def get_or_create_term(self, name, taxonomy):
        return 60 if taxonomy == "categories" else 9

    def get_recent_published(self, per_page=8):
        return []

    def get_term_link(self, term_id, taxonomy):
        return "https://studentup.in/c/"

    def upload_media(self, path, title="", alt_text="", filename="", **kw):
        return 88

    def create_post(self, **kwargs):
        return {"id": 1, "status": kwargs.get("status", "draft"),
                "link": "https://studentup.in/x/"}

    def update_post(self, post_id, **kwargs):
        return {"id": post_id, "status": "publish", "link": "https://x/"}

    def verify_meta(self, post_id, keys):
        return {k: True for k in keys}


def _art(content: str, slug: str, srcs) -> dict:
    return {"title": f"Test {slug} guide", "slug": slug, "category": "Results",
            "focus_keyword": "test keyword", "meta_description": "x" * 130,
            "tags": ["a", "b", "c", "d", "e"], "content_html": content,
            "quick_answer": "qa", "faq": [], "external_links": [],
            "banner_text": "Test banner", "_deep_sources": srcs}


def test_pipeline_originality_wired():
    real_wp, real_state = pipeline.WordPressClient, config.STATE_PATH
    saved = (config.DEFAULT_POST_STATUS, config.EDITORIAL_REVIEWER,
             config.PUBLISH_QA_MIN_SCORE, config.PUBLISH_ORIGINALITY_MIN,
             config.TOP_POST_STRICT)
    with tempfile.TemporaryDirectory() as td:
        try:
            pipeline.WordPressClient = _FakeWP
            config.STATE_PATH = Path(td) / "s.db"
            state.init(config.STATE_PATH)
            config.DEFAULT_POST_STATUS = "draft"
            config.EDITORIAL_REVIEWER = ""
            config.PUBLISH_QA_MIN_SCORE = 0
            config.PUBLISH_ORIGINALITY_MIN = 0
            config.TOP_POST_STRICT = False
            donor = SourceArticle(url="http://127.0.0.1/d", title="D",
                                  text=LONG_A)
            fresh = _art(f"<h2>A</h2><p>{LONG_B}</p><h2>B</h2><p>{LONG_B}</p>",
                         "v77-fresh-1", [donor])
            res = pipeline.publish_article(fresh)
            assert res["status"] == "draft", res
            assert fresh["_originality"]["verdict"] == "fresh", \
                fresh["_originality"]
            copy = _art(f"<h2>A</h2><p>{LONG_A}</p><h2>B</h2><p>{LONG_A}</p>",
                        "v77-copy-1", [donor])
            res2 = pipeline.publish_article(copy)
            assert res2["status"] == "draft", res2
            assert copy["_originality"]["verdict"] == "copy-risk", \
                copy["_originality"]
        finally:
            pipeline.WordPressClient = real_wp
            config.STATE_PATH = real_state
            (config.DEFAULT_POST_STATUS, config.EDITORIAL_REVIEWER,
             config.PUBLISH_QA_MIN_SCORE, config.PUBLISH_ORIGINALITY_MIN,
             config.TOP_POST_STRICT) = saved
    print("  pipeline _originality: fresh + copy-risk cases ✔")


# ------------------------------------------------- 6-7. sitemap + rotation

def test_news_sitemap_update_reentry():
    txt = read(THEME / "inc" / "news-sitemap.php")
    assert "'relation' => 'OR'" in txt
    assert "'column' => 'post_modified'" in txt
    assert txt.count("48 hours ago") >= 2
    print("  news-sitemap: publish OR modified 48h ✔")


def test_rotation_smart():
    ads = read(THEME / "inc" / "ads.php")
    assert "adsense_approved" in ads, "approval gate ledu (v84)"
    assert "gmdate( 'z' ) * 24" in ads and "gmdate( 'G' )" in ads
    assert "static $shown" in ads and "$place" in ads
    assert "studentup_rotate_house( studentup_house_ads(), $place )" in ads
    print("  rotation: hour-base + slot offset + no-repeat ✔")


# ------------------------------------------------- 8-9. ads auto + update chain

def test_ad_automation_proof():
    pwa = read(THEME / "inc" / "pwa.php")
    assert "studentup_opt( 'adsense_auto', '0' )" in pwa
    # v84: regex pwa lone kaadu — shared studentup_adsense_client()
    assert "studentup_adsense_client()" in pwa, "pwa gate bypass!"
    ads = read(THEME / "inc" / "ads.php")
    assert "add_filter( 'the_content', 'studentup_inject_in_article_ad', 20 )" in ads
    assert "'in_article_ad', '1'" in ads, "in-article default ON kaadu"
    assert "max_ads" in ads and "studentup_ad_count() >= $max" in ads
    assert "studentup_consent_ok()" in ads
    assert "setInterval" not in ads, "ad auto-refresh FORBIDDEN"
    js = read(THEME / "assets" / "js" / "studentup.js")
    assert js.count("setInterval") == 1 and "suCycleT" in js, \
        "setInterval = social rail only"
    kit = read(ROOT / "autoblog" / "adsense_kit.py")
    assert "ADSENSE_APPROVED" in kit and "normalize_client_id" in kit
    print("  ads auto: gated loader · in-article · cap · consent · no-refresh ✔")


def test_update_freshness_chain():
    pipe = read(ROOT / "autoblog" / "pipeline.py")
    assert "date_modified=date.today().isoformat()" in pipe
    assert "indexnow.submit(result.get(\"link\", \"\"))" in pipe
    seo = read(ROOT / "autoblog" / "seo.py")
    assert "Last Updated:" in seo
    bot = read(ROOT / "autoblog" / "approval_bot.py")
    assert 'action == "upd"' in bot and "run_update" in bot
    print("  update chain: modified + indexnow + badge + upd: ✔")


# ------------------------------------------------- 10. docs

def test_docs_v77():
    suites = len(list((ROOT / "tests").glob("*_test.py")))
    assert suites == 76, f"suites {suites} (v96 tho 76 expect)"
    readme = read(ROOT / "README.md")
    manual = read(ROOT / "MANUAL_ADVANCED_CHECKLIST.md")
    go_live = read(ROOT / "GO_LIVE_CHECKLIST.md")
    assert "### v77" in readme and "71/71" in readme
    assert "PART 36" in manual and "v77" in manual and "71/71" in manual
    assert "71/71" in go_live
    kit = read(ROOT / "AD_NETWORKS_APPLICATION_KIT.md")
    for needle in ("Ezoic", "Mediavine", "Media.net", "AdSense",
                   "APPLY FIRST", "Honest note"):
        assert needle in kit, f"kit needle ledu: {needle}"
    for name, txt in (("README", readme), ("MANUAL", manual),
                      ("GO_LIVE", go_live)):
        assert "164/164" in txt, f"{name} lo jsdom claim poyindi"
    print("  docs: README v77 + MANUAL PART 36 + 71/71 + kit ✔")


TESTS = [
    ("outbound rank official-first", test_outbound_rank_official_first),
    ("fetch outbound DOM", test_fetch_outbound_from_dom),
    ("research follows official", test_research_follows_official),
    ("rewrite_distance real numbers", test_rewrite_distance_real_numbers),
    ("pipeline _originality wired", test_pipeline_originality_wired),
    ("news-sitemap update re-entry", test_news_sitemap_update_reentry),
    ("rotation smart", test_rotation_smart),
    ("ad automation proof", test_ad_automation_proof),
    ("update freshness chain", test_update_freshness_chain),
    ("docs: v77 + PART 36 + 71/71 + kit", test_docs_v77),
]


def main() -> None:
    print("=" * 70)
    print("  v77 — ORIGINAL CONTENT ENGINE + HIGH-ADS READINESS")
    print("=" * 70)
    failed = 0
    for name, fn in TESTS:
        try:
            fn()  # fns print their own proof line on success
        except AssertionError as exc:
            failed += 1
            print(f"  {name} ✘  {exc}")
        except Exception as exc:  # noqa: BLE001
            failed += 1
            print(f"  {name} ✘  {type(exc).__name__}: {exc}")
    print("-" * 70)
    if failed:
        print(f"  {failed} TEST(S) FAILED ✘")
        raise SystemExit(1)
    print("ALL v77 ORIGINALITY + ADS TESTS PASSED ✔")


if __name__ == "__main__":
    main()
