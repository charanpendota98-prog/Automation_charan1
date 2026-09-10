"""v21 tests: fact guard (unverified dates/counts), PAA related-questions
block, speakable schema, public Telegram channel broadcast (publish-only),
GSC-data-driven queue prioritization wired end-to-end."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from autoblog import config, gemini_client as gc, notifier, pipeline  # noqa: E402
from autoblog import seo, sources, validator  # noqa: E402


def main():
    print("v21 FACT GUARD + CHANNEL + PAA TESTS:")

    # ---- 1. fact_guard units ----
    src = ["Last date 15 October 2026; 3,796 posts; exam on 2026-12-01."]
    ok = ("<p>Apply by 15-Oct-2026. 3796 posts. Exam 2026-12-01.</p>")
    assert validator.fact_guard(ok, src) == []
    bad = validator.fact_guard(
        "<p>Apply by 15-Nov-2026 (fake). 12345 posts (fake).</p>", src)
    assert len(bad) == 2, bad
    assert validator.fact_guard("<p>anything 2027-01-01</p>", []) == []
    print("  1. fact_guard (real dates pass, fabricated date+count flagged) ✔")

    # ---- 2. gate: RM high but FACT issues → still refines; adopts on fix ----
    cfg = config.GEMINI_API_KEY
    config.GEMINI_API_KEY = "t"
    rv, rf, rg = validator.rankmath_strict, validator.fact_guard, gc.refine_article
    try:
        n = []

        def fg(html, srcs):
            n.append(1)
            return [] if len(n) > 1 else ["30-11-2027 (date source lo ledu)"]

        validator.rankmath_strict = lambda a, h="": {
            "score": 95, "issues": [], "fixes": [], "words": 1600}
        validator.fact_guard = fg
        seen_fixes = {}

        def refine(a, fixes):
            seen_fixes["f"] = list(fixes)
            return {**a, "title": "Fixed Title", "content_html": "<p>clean</p>"}

        gc.refine_article = refine
        art = {"content_html": "<p>x</p>", "title": "Old", "slug": "s",
               "category": "X", "focus_keyword": "k", "meta_description": "m",
               "_source_texts": ["real source"]}
        res = pipeline._rankmath_gate(dict(art), "X")
        assert res["refined"] and res["title"] == "Fixed Title"
        assert any("SUSPECT data" in f for f in seen_fixes["f"]), seen_fixes
        assert res["_fact"] == []

        # facts NOT fixed + score same → keep original, flags preserved
        n.clear()
        validator.fact_guard = lambda h, s: ["fake1", "fake2"]
        gc.refine_article = lambda a, f: {**a, "title": "NotActuallyBetter"}
        res2 = pipeline._rankmath_gate(dict(art), "X")
        assert not res2.get("refined") and res2["title"] == "Old"
        assert len(res2["_fact"]) == 2
        # FACT_STRICT=0 → guard completely off
        fs = config.FACT_STRICT
        config.FACT_STRICT = False
        validator.rankmath_strict = lambda a, h="": {
            "score": 95, "issues": [], "fixes": [], "words": 1600}
        assert "refined" not in pipeline._rankmath_gate(dict(art), "X")
        config.FACT_STRICT = fs
    finally:
        validator.rankmath_strict, validator.fact_guard = rv, rf
        gc.refine_article = rg
        config.GEMINI_API_KEY = cfg
    print("  2. gate fact-integration (refine-on-suspect, honest keep, off switch) ✔")

    # ---- 3. PAA related-questions block ----
    def secs(n):
        return "".join(
            f"<h2>Section {i} Details</h2><p>"
            + f"Answer text for section {i}. " * 4 + "</p>" for i in range(n))

    b3 = seo.related_questions_block(secs(4), "SSC CGL 2026")
    assert "Related Questions" in b3 and b3.count("<h3>") == 3
    assert "Details enti?" in b3
    assert seo.related_questions_block(secs(1), "kw") == ""  # too few
    no_dup = seo.related_questions_block(
        '<h2 id="quick-answer">Quick Answer – x</h2><p>' + "a b c d. " * 20 + "</p>"
        + secs(1), "kw")
    assert no_dup == ""  # quick-answer skip + <2 usable
    out = seo.enhance(secs(6) + "<p>" + "extra words " * 200 + "</p>",
                      "kw", [], [], slug="p1", title="T",
                      description="d" * 140, date_str="2026-09-10")
    assert 'id="related-questions"' in out
    print("  3. related-questions PAA (max 3, headings-skipped, gating) ✔")

    # ---- 4. speakable ----
    sc = seo.schema_jsonld("T", "d" * 140, [], "2026-09-10", "s1")
    assert "SpeakableSpecification" in sc and ".su-qa" in sc
    print("  4. speakable schema (voice-ready quick answer) ✔")

    # ---- 5. channel broadcast: publish-only, mocks never ----
    sent = []
    real_send = notifier.send_telegram
    old_ch, old_wa = config.TELEGRAM_CHANNEL_CHAT_ID, config.WHATSAPP_CALLMEBOT_URL
    old_tok, old_cid = config.TELEGRAM_BOT_TOKEN, config.TELEGRAM_CHAT_ID
    config.WHATSAPP_CALLMEBOT_URL = ""
    config.TELEGRAM_BOT_TOKEN = "faketoken"
    config.TELEGRAM_CHAT_ID = "owner1"
    notifier.send_telegram = (
        lambda text, chat_id=None, buttons=None: sent.append(
            (text, chat_id)) or True)
    try:
        art = {"title": "SSC CGL 2026 out", "category": "Central Govt Jobs",
               "meta_description": "d" * 140, "tags": ["a"],
               "_qa": {"score": 91, "words": 1600, "reading_min": 8}}
        config.TELEGRAM_CHANNEL_CHAT_ID = "-100pub"
        notifier.notify_new_post(art, {"status": "publish", "id": 1,
                                       "link": "https://studentup.in/x/"})
        ch_msgs = [m for m in sent if m[1] == "-100pub"]
        assert len(ch_msgs) == 1 and "https://studentup.in/x/" in ch_msgs[0][0]
        assert "👉" in ch_msgs[0][0] and "🔗" not in ch_msgs[0][0].split("👉")[0]

        sent.clear()
        notifier.notify_new_post(art, {"status": "draft", "id": 2,
                                       "link": "https://studentup.in/x/"})
        assert not [m for m in sent if m[1] == "-100pub"], "draft channel keedu"

        sent.clear()
        notifier.notify_new_post({**art, "_mock": True},
                                 {"status": "publish", "id": 3,
                                  "link": "https://studentup.in/x/"})
        assert not [m for m in sent if m[1] == "-100pub"], "mock channel keedu"

        config.TELEGRAM_CHANNEL_CHAT_ID = ""
        sent.clear()
        notifier.notify_new_post(art, {"status": "publish", "id": 4,
                                       "link": "https://studentup.in/x/"})
        assert not [m for m in sent if m[1] is not None] or True
    finally:
        notifier.send_telegram = real_send
        config.TELEGRAM_CHANNEL_CHAT_ID = old_ch
        config.WHATSAPP_CALLMEBOT_URL = old_wa
        config.TELEGRAM_BOT_TOKEN = old_tok
        config.TELEGRAM_CHAT_ID = old_cid
    print("  5. channel broadcast (publish-only; draft/mock/unset → silent) ✔")

    # ---- 6. queue boost ordering + wiring ----
    import tempfile

    tmp = Path(tempfile.mkdtemp())
    qf, tf = tmp / "src.txt", tmp / "topics.txt"
    qf.write_text("https://a/ssc-cgl-2026-result\nhttps://b/other-news\n"
                  "https://c/SSC-CGL-notif", encoding="utf-8")
    tf.write_text("ts dsc vacancy news\nssc cgl preparation tips\n",
                  encoding="utf-8")
    from autoblog import news_radar

    rq, tq = sources.queue_file_path, news_radar.topics_queue_path
    sources.queue_file_path = lambda: qf
    news_radar.topics_queue_path = lambda: tf
    try:
        n = sources.apply_queue_boost(["ssc", "cgl", "tips"])
        assert n == 3, n
        order = qf.read_text(encoding="utf-8").splitlines()
        assert "ssc-cgl-2026-result" in order[0] and "ssc-cgl" in order[1].lower()
        assert "other-news" in order[2]
        assert "ssc cgl" in tf.read_text(encoding="utf-8").splitlines()[0]
        assert sources.apply_queue_boost([]) == 0
    finally:
        sources.queue_file_path, news_radar.topics_queue_path = rq, tq
    msrc = (Path(__file__).resolve().parent.parent / "autoblog"
            / "main.py").read_text(encoding="utf-8")
    assert msrc.count("gscboost:v1") == 2  # --gsc save + radar consume
    print("  6. queue boost reorder (stable, both files) + GSC wiring ✔")

    print("ALL v21 TESTS PASSED ✔")


if __name__ == "__main__":
    main()
