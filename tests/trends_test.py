"""v9 Google-native tests: Trends RSS parse + filter, schema date preservation,
Discover robots meta, --trends CLI graceful failure."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from autoblog import config, seo, topic_engine  # noqa: E402

FAKE_RSS = """<?xml version="1.0"?>
<rss version="2.0" xmlns:ht="https://trends.google.com/trending/rss">
<channel><title>Daily Trending Searches</title>
<item>
  <title>SSC GD Constable Result 2026</title>
  <ht:approx_traffic>200K+</ht:approx_traffic>
  <ht:news_item><ht:news_item_title>SSC GD result declared, direct link here</ht:news_item_title></ht:news_item>
</item>
<item>
  <title>India vs Australia Match</title>
  <ht:approx_traffic>500K+</ht:approx_traffic>
  <ht:news_item><ht:news_item_title>Cricket score updates live</ht:news_item_title></ht:news_item>
</item>
<item>
  <title>NSP Scholarship Payment Status</title>
  <ht:approx_traffic>50K+</ht:approx_traffic>
  <ht:news_item><ht:news_item_title>Payment released for lakhs of students</ht:news_item_title></ht:news_item>
</item>
</channel></rss>"""


class FakeResp:
    text = FAKE_RSS
    status_code = 200

    def raise_for_status(self):
        pass


def main():
    print("GOOGLE-NATIVE v9 TESTS:")

    # ---- 1. Trends RSS parse (network monkeypatch) ----
    import requests as _rq

    orig_get = _rq.get
    _rq.get = lambda *a, **k: FakeResp()
    try:
        topics = topic_engine.fetch_trending_topics()
    finally:
        _rq.get = orig_get
    assert len(topics) == 3, topics
    assert topics[0]["title"] == "SSC GD Constable Result 2026"
    assert topics[0]["traffic"] == "200K+"
    assert "SSC GD result" in topics[0]["news_title"]
    print("  1. Trends RSS parse (title/traffic/news_title) ✔")

    # ---- 2. education filter ----
    edu = topic_engine.filter_edu_trends(topics)
    titles = [t["title"] for t in edu]
    assert "SSC GD Constable Result 2026" in titles
    assert "NSP Scholarship Payment Status" in titles
    assert "India vs Australia Match" not in titles
    print("  2. education filter (cricket out, SSC/NSP in) ✔")

    # ---- 3. network fail -> empty (bot continues) ----
    def boom(*a, **k):
        raise ConnectionError("no net")

    _rq.get = boom
    try:
        assert topic_engine.fetch_trending_topics() == []
    finally:
        _rq.get = orig_get
    print("  3. network fail safe (empty list) ✔")

    # ---- 4. schema: datePublished preserve + dateModified update ----
    html = seo.schema_jsonld(
        "Test Post", "desc", [{"question": "q", "answer": "a"}],
        "2026-01-10", "test-post", date_modified="2026-09-07")
    assert '"datePublished": "2026-01-10"' in html
    assert '"dateModified": "2026-09-07"' in html
    # default: modified == published
    html2 = seo.schema_jsonld(
        "T", "d", [], "2026-01-10", "t")
    assert '"dateModified": "2026-01-10"' in html2
    print("  4. schema dates (published preserved, modified updates) ✔")

    # ---- 5. Discover robots meta (Rank Math) ----
    config.DISCOVER_META_ENABLED = True
    meta = seo.rankmath_meta(focus_keyword="ssc cgl 2026",
                             description="d" * 130, seo_title="SSC CGL 2026 Guide")
    assert meta.get("rank_math_robots") == ["index, follow, max-image-preview:large"]
    config.DISCOVER_META_ENABLED = False
    meta2 = seo.rankmath_meta(focus_keyword="x", description="d" * 130, seo_title="t")
    assert "rank_math_robots" not in meta2
    config.DISCOVER_META_ENABLED = True
    print("  5. Discover max-image-preview meta (config gate) ✔")

    # ---- 6. --trends CLI graceful failure (invalid RSS host) ----
    import subprocess

    env = {"PATH": "/usr/bin:/bin", "TRENDS_RSS": "http://127.0.0.1:9/x",
           "PYTHONUNBUFFERED": "1"}
    r = subprocess.run([str(Path(".venv/bin/python")), "run.py", "--trends"],
                       capture_output=True, text=True, timeout=60, env=env)
    assert "GOOGLE TRENDS" in r.stdout and "fetch fail" in r.stdout
    assert r.returncode == 1  # graceful, not crash
    print("  6. --trends command (graceful offline) ✔")

    print("ALL GOOGLE-NATIVE TESTS PASSED ✔")


if __name__ == "__main__":
    main()
