"""v15/v16 tests: district radar + sources grid + channel watch + thumbnails.

Sections:
  1. District lists (TS 33 + AP 26, unique, key names)
  2. Google News RSS parse (synthetic XML + garbage-safe)
  3. Education relevance filter
  4. URL queue dedupe (state + file)
  5. District rotation (fake fetch — batches disjoint, queue grows)
  6. Watch sources: t.me page + RSS feed + HTML links (fake fetch)
  7. v15/v16 PRO thumbnails: 3 variants render, distinct, auto-rotation
  8. v16.1 sources grid: 105 sources, daily tier + rotation batch
  9. Topics queue: dedupe, pending, mark_done
"""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from autoblog import config, news_radar, research, sources, state  # noqa: E402


def main():
    print("v15/v16 RADAR TESTS:")
    tmp = Path(tempfile.mkdtemp(prefix="radar_test_"))
    config.OUTPUT_DIR = tmp
    config.STATE_PATH = tmp / "state.db"
    config.SOURCES_QUEUE_PATH = tmp / "sources_queue.txt"
    state.init(config.STATE_PATH)

    # ---- 1. districts ----
    assert len(news_radar.TS_DISTRICTS) == 33, len(news_radar.TS_DISTRICTS)
    assert len(news_radar.AP_DISTRICTS) == 26, len(news_radar.AP_DISTRICTS)
    assert len(news_radar.ALL_DISTRICTS) == 59
    for d in ("Khammam", "Nalgonda", "Yadadri Bhuvanagiri", "Guntur",
              "YSR Kadapa", "Sri Sathya Sai", "Medchal Malkajgiri"):
        assert any(d in x for x, _ in news_radar.ALL_DISTRICTS), d
    assert len(set(news_radar.TS_DISTRICTS)) == 33
    assert len(set(news_radar.AP_DISTRICTS)) == 26
    print("  1. districts TS 33 + AP 26 (unique, key names) ✔")

    # ---- 2. RSS parse ----
    xml = (
        '<?xml version="1.0"?><rss><channel>'
        '<item><title>SSC CGL 2026 Notification — Khammam</title>'
        '<link>https://a.example/n1</link><pubDate>Mon, 01 Jan 2026</pubDate></item>'
        '<item><title>IPL final Hyderabad</title><link>https://a.example/n2</link></item>'
        '<item><title>AP DSC results out in Guntur district</title>'
        '<link>https://a.example/n3</link></item>'
        '</channel></rss>')
    items = news_radar._parse_feed(xml, 10)
    assert len(items) == 3, items
    assert items[0]["link"] == "https://a.example/n1"
    assert "SSC" in items[0]["title"]
    assert news_radar._parse_feed("garbage-not-xml", 5) == []
    print("  2. RSS parse (3 items, garbage-safe) ✔")

    # ---- 3. education filter ----
    assert news_radar._edu_relevant("SSC CGL exam notification released")
    assert news_radar._edu_relevant("గ్రూప్ 2 ఫలితాలు జారీ")
    assert not news_radar._edu_relevant("IPL cricket match highlights today")
    assert not news_radar._edu_relevant("movie trailer released")
    assert news_radar._edu_relevant(
        "PM Kisan installment and farmer welfare update", "Current Affairs"
    )
    assert news_radar._edu_relevant(
        "Government notification on student scholarship", "Current Affairs"
    )
    assert not news_radar._edu_relevant(
        "Cabinet political speech and movie event", "Current Affairs"
    )
    print("  3. education + practical current-affairs relevance filter ✔")

    # ---- 4. URL queue dedupe ----
    assert news_radar._queue_url("https://a.example/n1") is True
    assert news_radar._queue_url("https://a.example/n1") is False  # seen
    assert news_radar._queue_url("not-a-url") is False
    lines = [l for l in config.SOURCES_QUEUE_PATH.read_text().splitlines() if l]
    assert lines == ["https://a.example/n1"], lines
    assert news_radar._opportunity_key(
        "Latest SSC GD Constable Recruitment 2026 — Apply Online"
    ) == "constable gd ssc 2026"
    assert news_radar._opportunity_key("SSC GD Constable Recruitment 2027") != \
        news_radar._opportunity_key("SSC GD Constable Recruitment 2026")
    assert news_radar._opportunity_key(
        "SSC GD Constable 2026: 25 vacancies, last date 15 April"
    ) == news_radar._opportunity_key(
        "Constable GD SSC 2026 — 500 posts, apply online"
    )
    # Two publisher URLs for the same vacancy must produce one queue item.
    assert news_radar._queue_url(
        "https://jobs.example.com/ssc-gd", "SSC GD Constable Recruitment 2026"
    ) is True
    assert news_radar._queue_url(
        "https://mirror.example.org/ssc-gd-notice", "SSC GD Constable Recruitment 2026"
    ) is False
    duplicate_events = state.recent_radar_events(config.STATE_PATH, 20)
    assert any(e["event_type"] == "duplicate_opportunity" for e in duplicate_events)
    # A failed source remains retryable and does not poison the opportunity key.
    sources.mark_done_and_clean("https://jobs.example.com/ssc-gd", completed=False,
                                failure_type="fetch_failure", details="HTTP 503")
    assert any(e["event_type"] == "fetch_failure"
               for e in state.recent_radar_events(config.STATE_PATH, 20))
    assert news_radar._queue_url(
        "https://mirror.example.org/ssc-gd-notice", "SSC GD Constable Recruitment 2026"
    ) is True
    print("  4. URL + cross-source opportunity dedupe, audit, retry ✔")

    # ---- 5. district rotation ----
    def fake_fetch(query, limit=5):
        fake_fetch.n = getattr(fake_fetch, "n", 0) + 1
        return [{"title": f"{query} exam notification 2026 released",
                 "link": f"https://news.example.com/r5/{fake_fetch.n}",
                 "pub": ""}]

    orig_fetch = news_radar.fetch_google_news
    news_radar.fetch_google_news = fake_fetch
    try:
        first = news_radar.radar_districts(per_run=3)
        second = news_radar.radar_districts(per_run=3)
        assert len(first) == 3 and len(second) == 3, (first, second)
        d1 = {it["district"] for it in first}
        d2 = {it["district"] for it in second}
        assert not (d1 & d2), (d1, d2)
        assert all(it["state"] in ("TS", "AP") for it in first)
        assert len([l for l in config.SOURCES_QUEUE_PATH.read_text().splitlines()
                    if l]) >= 6
    finally:
        news_radar.fetch_google_news = orig_fetch
    print("  5. district rotation (disjoint batches, queue grows) ✔")

    # ---- 6. watch sources: telegram + RSS + HTML ----
    page = (
        '<div class="tgme_widget_message_text js-message_text" dir="auto">'
        'SSC GD Constable 2026 notification released — apply online before '
        'deadline, hall ticket updates</div>\n'
        '<div class="tgme_widget_message_text js-message_text" dir="auto">'
        'Today cricket match score in Hyderabad stadium</div>')
    feed = (
        '<?xml version="1.0"?><rss><channel>'
        '<item><title>AP EAPCET counselling 2026 schedule out</title>'
        '<link>https://news.example.com/ap/eapcet</link></item>'
        '</channel></rss>')
    html_page = ('<html><a href="https://jobs.example.com/latest/'
                 'ssc-gd-notification-2026">SSC GD full notification</a>'
                 '<a href="https://jobs.example.com/latest/about-us">About us '
                 'company page</a></html>')

    def fake_text(url, timeout=20):
        if "t.me" in url:
            return page
        if "feed" in url or "rss" in url:
            return feed
        return html_page

    orig_text, orig_watch = news_radar._fetch_text, config.WATCH_SOURCES
    news_radar._fetch_text = fake_text
    config.WATCH_SOURCES = ("https://t.me/s/testchan, "
                            "https://jobs.example.com/feed, "
                            "https://jobs.example.com/latest")
    try:
        n = news_radar.watch_channels()
        assert n >= 3, n
        topics = news_radar.pending_topics(20)
        assert any("SSC GD Constable 2026" in t for t in topics), topics
        assert not any("cricket" in t.lower() for t in topics)
        urls = config.SOURCES_QUEUE_PATH.read_text()
        assert "ap/eapcet" in urls                       # RSS flow
        assert "ssc-gd-notification-2026" in urls          # HTML flow
        assert "about-us" not in urls                      # non-edu label skip
    finally:
        news_radar._fetch_text = orig_text
        config.WATCH_SOURCES = orig_watch
    print("  6. watch channels: t.me + RSS + HTML (edu filter) ✔")

    # ---- 7. thumbnails: 3 pro variants ----
    from autoblog import image_gen
    from PIL import Image

    blobs = {}
    for v in ("bottom", "center", "top"):
        out = tmp / f"thumb_{v}.jpg"
        r = image_gen.generate_featured_image(
            "SSC CGL 2026 Notification Apply Online", "Central Govt Jobs",
            out, variant=v)
        assert r and out.exists() and out.stat().st_size > 5000, v
        with Image.open(out) as im:
            assert im.size == (config.IMAGE_WIDTH, config.IMAGE_HEIGHT), im.size
            # v24 CROP-PROOF: all bright text pixels inside center 60% band
            rgb = im.convert("RGB")
            px = rgb.load()
            W, H = rgb.size
            minx, maxx = W, 0
            for yy in range(0, H, 3):
                for xx in range(0, W, 3):
                    cr, cg, cb = px[xx, yy]
                    if cr > 228 and cg > 228 and cb > 228:
                        minx, maxx = min(minx, xx), max(maxx, xx)
            assert minx > 0.19 * W and maxx < 0.81 * W, (v, minx / W, maxx / W)
        blobs[v] = out.read_bytes()
    assert blobs["bottom"] != blobs["center"] != blobs["top"]
    before = image_gen._LAST_VARIANT["i"]
    assert image_gen.generate_featured_image("Rotation Check Banner",
                                             "Results", tmp / "rot.jpg")
    assert image_gen._LAST_VARIANT["i"] != before
    print("  7. pro thumbnails: 3 variants render, distinct, auto-rotate ✔")

    # ---- 8. official sources grid (v16.1) ----
    from autoblog import sources_grid

    grid = sources_grid.SOURCES_GRID
    assert len(grid) >= 100, len(grid)
    cats = {e["cat"] for e in grid}
    assert {"Central Govt Jobs", "TS Govt Jobs", "AP Govt Jobs", "Scholarships",
             "Private Jobs", "Software Jobs", "Walkin Jobs", "Internships",
             "Part Time Jobs", "Online Education", "Results",
             "Hall Tickets"} <= cats
    # v50: the bot's wp.ensure_categories() creates any missing category on the
    # live site (get_or_create_term), so the grid may use the new pillars too.
    LIVE = {"Scholarships", "Central Govt Jobs", "TS Govt Jobs", "AP Govt Jobs",
            "Private Jobs", "Software Jobs", "Part Time Jobs", "Walkin Jobs",
            "Hall Tickets", "Results", "Internships", "Online Education",
            "Outsourcing Jobs", "Current Affairs", "Exam Tips", "Upcoming Exams",
            "Abroad Jobs", "Success Stories",
            "Uncategorized"}
    assert cats <= LIVE, cats - LIVE
    names = " ".join(e["name"] for e in grid)
    for official in ("TSPSC", "APPSC", "SSC", "SBI", "NSP", "Jnanabhumi",
                     "ePASS", "TCS NQT", "LIC", "RBI", "IBPS", "UPSC", "NEET",
                     "AIIMS", "TGRTC", "APSRTC", "Singareni", "Employment News",
                     "Cognizant", "Capgemini", "Zoho", "ISRO", "DRDO", "NTPC",
                     "Agniveer", "NABARD", "FCI", "JIPMER", "HMWSSB",
                     "Adda247 Telugu", "Eenadu Pratibha", "Sakshi Education",
                     "Job Updates Telugu", "Telugu Careers", "Telugu Jobs Point",
                     "NaaJob", "FreeJobAlert", "FreshersNow", "Jobs.com"):
        assert official in names, official
    assert len({e["name"] for e in grid}) == len(grid)
    assert len({e["q"] for e in grid}) == len(grid)
    daily = [e for e in grid if e.get("daily")]
    assert len(daily) >= 12, len(daily)

    def fake_gnews(query, limit=5):
        fake_gnews.n = getattr(fake_gnews, "n", 0) + 1
        return [{"title": f"{query} exam notification 2026 released {fake_gnews.n}",
                 "link": (f"https://news.example.com/g/{fake_gnews.n}/"
                          + query.replace(" ", "-")),
                 "pub": ""}]

    orig = news_radar.fetch_google_news
    news_radar.fetch_google_news = fake_gnews
    orig_per_run = config.RADAR_SOURCES_PER_RUN
    try:
        config.RADAR_SOURCES_PER_RUN = 4
        b1 = sources_grid.radar_sources()
        b2 = sources_grid.radar_sources()
        daily_names = {e["name"] for e in daily}
        assert len(b1) == len(daily) + 4, len(b1)
        assert all("source_name" in it and "category_hint" in it for it in b1)
        seen1 = {it["source_name"] for it in b1}
        seen2 = {it["source_name"] for it in b2}
        # Daily discovery is scanned again, but cross-source opportunity
        # dedupe intentionally prevents the same vacancy being returned twice.
        assert daily_names <= seen1 and not (daily_names & seen2)
        assert len(b2) == 4, b2
        assert (seen1 - daily_names) & (seen2 - daily_names) == set()
    finally:
        news_radar.fetch_google_news = orig
        config.RADAR_SOURCES_PER_RUN = orig_per_run
    print(f"  8. official sources grid ({len(grid)} sources, daily + rotation) ✔")

    # ---- 9. topics queue ----
    t_txt = "TS Inter 2026 results published — public colleges toppers list"
    assert news_radar._queue_topic(t_txt) is True
    assert news_radar._queue_topic(t_txt) is False       # dedupe
    assert news_radar._queue_topic("cricket score") is False  # too short/non-edu
    pending = news_radar.pending_topics(1)
    assert pending, pending
    news_radar.mark_topic_done(pending[0])
    assert pending[0] not in news_radar.pending_topics(20)
    print("  9. topics queue dedupe + mark_done ✔")

    # ---- 10. text alert -> official/Telugu source candidates ----
    old_search = research.search_web
    research.search_web = lambda query, max_results=10: [
        {"url": "https://random.example/x", "title": "Random"},
        {"url": "https://sakshi.com/jobs/x", "title": "Telugu report"},
        {"url": "https://www.adda247.com/te/jobs/x", "title": "Adda Telugu"},
        {"url": "https://upsc.gov.in/notice/x", "title": "Official notice"},
        {"url": "https://www.studentup.in/own", "title": "Own"},
    ]
    old_site = config.WP_SITE
    config.WP_SITE = "https://studentup.in"
    try:
        candidates = research.topic_source_candidates("UPSC jobs", limit=5)
        assert candidates[0]["url"].startswith("https://upsc.gov.in")
        assert "adda247.com" in candidates[1]["url"]
        assert candidates[2]["url"].startswith("https://sakshi.com")
        assert not any("studentup.in" in x["url"] for x in candidates)
    finally:
        research.search_web = old_search
        config.WP_SITE = old_site
    main_src = Path(__file__).resolve().parent.parent / "autoblog" / "main.py"
    orchestration = main_src.read_text(encoding="utf-8")
    assert "topic_source_candidates" in orchestration
    assert orchestration.count("force_draft=True") >= 2
    assert "AUTO_SOURCE_ONLY" in orchestration
    print("  10. official/Telugu-first candidates + forced draft orchestration ✔")

    print("ALL v15/v16 RADAR TESTS PASSED ✔")
    return 0


if __name__ == "__main__":
    sys.exit(main())
