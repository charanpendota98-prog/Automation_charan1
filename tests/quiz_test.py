"""v26 Daily Quiz Engine tests — topic rotation, mock quizzes, validation,
HTML block escaping, sanitize-around-quiz, JSON-LD, widget install (FakeWP),
pipeline.create_quiz end-to-end (mock, WP patched). No network."""
import json
import re
import sys
from datetime import date
from pathlib import Path
from urllib.parse import parse_qs, unquote

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from autoblog import config, pipeline, quiz_engine, state, validator  # noqa: E402


# ------------------------------------------------------------------ 1. rotation
def t1_rotation():
    # Monday 2026-09-07 -> Current Affairs L1; Sunday 2026-09-13 -> Mega Mock L4
    te, tte, lvl, n = quiz_engine.pick_daily_topic(date(2026, 9, 7))
    assert "Current Affairs" in te and lvl == 1 and n == config.QUIZ_QUESTIONS, (te, lvl, n)
    assert tte  # Telugu label undi
    sun = quiz_engine.pick_daily_topic(date(2026, 9, 13))
    assert sun[2] == 4 and sun[3] == config.QUIZ_SUNDAY_QUESTIONS, sun
    # Saturday = Top level
    assert quiz_engine.pick_daily_topic(date(2026, 9, 12))[2] == 4
    # all 7 days valid
    for d in range(7):
        q = quiz_engine.pick_daily_topic(date(2026, 9, 7 + d))
        assert 1 <= q[2] <= 4 and q[3] >= 5
    print("  1. weekly rotation + Sunday mega mock ✔")


# ------------------------------------------------------------------ 2. mock quiz
def t2_mock_quiz():
    q1 = quiz_engine.mock_quiz("Current Affairs & GK", "జీకే", 1, 10, date(2026, 9, 7))
    q1b = quiz_engine.mock_quiz("Current Affairs & GK", "జీకే", 1, 10, date(2026, 9, 7))
    q2 = quiz_engine.mock_quiz("Current Affairs & GK", "జీకే", 1, 10, date(2026, 9, 8))
    assert q1 == q1b, "mock must be deterministic for same day+topic"
    assert q1 != q2, "different day -> different quiz"
    assert len(q1["questions"]) == 10
    for q in q1["questions"]:
        assert len(q["options"]) == 4 and 0 <= q["a"] <= 3
        assert q["x"] and q["q"] and q["qt"]
        assert q["options"][q["a"]]  # correct option non-empty
    print("  2. mock quiz deterministic + shape ✔")


# ------------------------------------------------------------------ 3. validation
def t3_validation():
    stems = ["Capital of France is which city",
             "Largest planet in our solar system",
             "Who wrote the Indian national anthem",
             "Chemical symbol for gold stands for",
             "Year when Telangana state was formed",
             "Full form of the abbreviation GDP"]
    good = {"questions": [
        {"q": stems[i] + "?", "qt": f"ప్రశ్న {i}",
         "options": ["3", "4", "5", "6"],
         "a": i % 4, "x": f"Explanation for question {i} is here."}
        for i in range(6)]}
    assert quiz_engine.validate_quiz(good, 6) == []
    bad_ans = {"questions": [dict(good["questions"][0], a=9)]}
    assert quiz_engine.validate_quiz(bad_ans, 1)
    bad_opts = {"questions": [dict(good["questions"][0], options=["a", "b"])]}
    assert quiz_engine.validate_quiz(bad_opts, 1)
    no_x = {"questions": [dict(good["questions"][0], x="")]}
    assert quiz_engine.validate_quiz(no_x, 1)
    too_few = {"questions": good["questions"][:2]}
    assert quiz_engine.validate_quiz(too_few, 10)
    # near-duplicate (same words, different punctuation) must be flagged
    dup = {"questions": [good["questions"][0],
                         dict(good["questions"][0],
                              q=good["questions"][0]["q"].replace(" ", "  "))]}
    assert quiz_engine.validate_quiz(dup, 2), "near-duplicate must be flagged"
    print("  3. validate_quiz catches bad shapes ✔")


# ------------------------------------------------------------------ 4. HTML block
def t4_build_html():
    quiz = quiz_engine.mock_quiz("Topic", "టాపిక్", 2, 6, date(2026, 9, 8))
    content, uid = quiz_engine.build_quiz_html(quiz, "Topic", "టాపిక్", 2, 6,
                                               date(2026, 9, 8))
    assert quiz_engine.QUIZ_START in content and quiz_engine.QUIZ_END in content
    assert 'class="su-quiz"' in content and f'id="suq-{uid}"' in content
    # data-quiz attribute must be parseable JSON after unescape
    m = re.search(r'data-quiz="(.*?)"', content, flags=re.S)
    assert m, "data-quiz attribute missing"
    payload = json.loads(m.group(1).replace("&quot;", '"').replace("&amp;", "&"))
    assert payload["level"] == 2 and len(payload["questions"]) == 6
    assert payload["settings"]["negative"] == config.QUIZ_NEGATIVE_MARK
    # answer key present with all questions
    assert "Answer Key" in content
    assert content.count("<li><strong>Q") == 6
    # intro table present
    assert "<table>" in content and "L2" in content
    # no raw unescaped quotes leaking out of the attribute
    inner = content.split('data-quiz="', 1)[1].split('"', 1)[0]
    assert '"' not in inner
    print("  4. quiz block escaping + answer key ✔")


# ------------------------------------------------------------------ 5. sanitize
def t5_sanitize():
    quiz = quiz_engine.mock_quiz("T", "టి", 1, 5, date(2026, 9, 9))
    content, _ = quiz_engine.build_quiz_html(quiz, "T", "టి", 1, 5, date(2026, 9, 9))
    dirty = ('<script>alert(1)</script><div onclick="x">junk</div>'
             + content + '<iframe src="x"></iframe>')
    clean = quiz_engine.sanitize_quiz_content(dirty)
    assert "<script>alert" not in clean and "<iframe" not in clean
    assert 'onclick' not in clean.split(quiz_engine.QUIZ_START)[0]
    # quiz block survived intact
    assert quiz_engine.QUIZ_START in clean and 'class="su-quiz"' in clean
    block = clean.split(quiz_engine.QUIZ_START)[1].split(quiz_engine.QUIZ_END)[0]
    assert block == content.split(quiz_engine.QUIZ_START)[1].split(quiz_engine.QUIZ_END)[0]
    # plain validator would have destroyed it (regression proof)
    destroyed = validator.sanitize_html(content)
    assert 'class="su-quiz"' not in destroyed
    print("  5. sanitize-around-quiz keeps block, kills junk ✔")


# ------------------------------------------------------------------ 6. finalize
def t6_finalize():
    quiz = quiz_engine.mock_quiz("T", "టి", 3, 5, date(2026, 9, 10))
    content, _ = quiz_engine.build_quiz_html(quiz, "T", "టి", 3, 5, date(2026, 9, 10))
    article = {"title": "Daily Quiz – Test", "meta_description": "d" * 130,
               "content_html": content, "_quiz": quiz, "_quiz_level": 3,
               "_link": "https://studentup.in/daily-quiz-test/"}
    final = quiz_engine.finalize_html(article, internal_links=[
        {"link": "https://studentup.in/a", "title": "Post A"}])
    assert "wa.me" in final and "Related Articles" in final
    m = re.search(r'<script type="application/ld\+json">(.*?)</script>', final, re.S)
    assert m, "Quiz JSON-LD missing"
    data = json.loads(m.group(1).replace("<\\/", "</"))
    assert data["@type"] == "Quiz" and len(data["hasPart"]) == 5
    assert data["hasPart"][0]["acceptedAnswer"]["@type"] == "Answer"
    print("  6. finalize: share bar + related + Quiz JSON-LD ✔")


# ------------------------------------------------------------------ 7. widget
class FakeResp:
    def __init__(self, status=200, payload=None):
        self.status_code, self._p = status, payload or {}

    @property
    def ok(self):
        return self.status_code < 400

    def json(self):
        return self._p


class FakeWP:
    def __init__(self):
        self.widgets, self.n = {}, 0

    def _request(self, method, path, **kw):
        if path.startswith("sidebars"):
            return FakeResp(200, [{"id": "footer-1", "name": "Footer"}])
        if path == "widgets" and method == "GET":
            items = [{"id": k, "instance": v} for k, v in self.widgets.items()]
            return FakeResp(200, items)
        if path == "widgets" and method == "POST":
            self.n += 1
            wid = f"text-{700 + self.n}"
            self.widgets[wid] = kw.get("json", {}).get("instance", {})
            return FakeResp(201, {"id": wid})
        if path.startswith("widgets/"):
            wid = path.split("/", 1)[1]
            self.widgets[wid] = kw.get("json", {}).get("instance", {})
            return FakeResp(200, {"id": wid})
        return FakeResp(404, {})


def t7_widget():
    htmlblob = quiz_engine.build_widget_html()
    assert quiz_engine.MARKER in htmlblob
    assert "<script>" in htmlblob and "<style" in htmlblob
    assert "</script>" not in quiz_engine.QUIZ_JS, "JS must not contain </script>"
    # JS sanity: balanced-ish & key engine pieces present
    for token in ("suq-pal", "localStorage", "wa.me", "Exam Mode",
                  "Practice Mode", "suq_streak"):
        assert token in quiz_engine.QUIZ_JS, token
    wp = FakeWP()
    st1, d1 = quiz_engine.install(wp)
    assert st1 == "ok" and "installed" in d1, (st1, d1)
    st2, d2 = quiz_engine.install(wp)
    assert st2 == "ok" and "up to date" in d2, (st2, d2)  # idempotent
    assert wp.n == 1, "second install must not create another widget"
    enc = list(wp.widgets.values())[0]["encoded"]
    text = unquote(parse_qs(enc)["text"][0])
    assert quiz_engine.MARKER in text and "su-quiz" in text
    print("  7. widget install idempotent + engine payload ✔")


# ------------------------------------------------------------------ 8. gemini prompt
def t8_gemini_prompt():
    from autoblog import gemini_client
    p = gemini_client.QUIZ_PROMPT_TEMPLATE.format(
        topic="Scholarships", topic_te="స్కాలర్‌షిప్‌లు", level=2, n=10,
        year=2026, level_name="Intermediate",
        level_hint=gemini_client._LEVEL_HINTS[2])
    assert "EXACTLY 10 questions" in p and "L2" in p and "స్కాలర్" in p
    assert len(gemini_client._LEVEL_HINTS) == 4
    print("  8. gemini quiz prompt formats ✔")


# ------------------------------------------------------------------ 9. pipeline e2e
def t9_pipeline_mock():
    import tempfile

    db = Path(tempfile.mkdtemp()) / "qstate.db"
    orig_db = config.STATE_PATH
    orig_image = config.IMAGE_ENABLED
    config.STATE_PATH = db
    config.IMAGE_ENABLED = False
    state.init(db)
    captured = {}

    def fake_publish(article, day=None):
        captured.update(article)
        state.record_post(config.STATE_PATH, article["title"], article["slug"],
                          article["category"], "https://x/?p=123", "draft")
        return {"id": 123, "status": "draft", "link": "https://x/?p=123"}

    real_pub = pipeline.publish_article
    pipeline.publish_article = fake_publish
    try:
        res = pipeline.create_quiz(topic="", mock=True)
        assert res["id"] == 123
        assert captured["article_type"] == "quiz"
        assert captured["category"] == config.QUIZ_CATEGORY
        assert quiz_engine.QUIZ_START in captured["content_html"]
        assert "Answer Key" in captured["content_html"]
        assert captured["_quiz"]["questions"]
        assert len(captured["meta_description"]) >= 120
        # duplicate same-day quiz blocked
        try:
            pipeline.create_quiz(topic="", mock=True)
            raise AssertionError("duplicate quiz must raise")
        except ValueError:
            pass
        # custom Telugu topic works
        res2 = pipeline.create_quiz(topic="స్కాలర్‌షిప్‌ల మీద క్విజ్", level=3,
                                    questions=7, mock=True)
        assert res2["id"] == 123
        assert captured["title"].startswith("Quiz: స్కాలర్‌షిప్‌ల మీద క్విజ్")
        assert len(captured["_quiz"]["questions"]) == 7
        assert captured["_quiz_level"] == 3
    finally:
        pipeline.publish_article = real_pub
        config.STATE_PATH = orig_db
        config.IMAGE_ENABLED = orig_image
        db.unlink(missing_ok=True)
    print("  9. create_quiz e2e (mock, Telugu topic, dedupe) ✔")


# ------------------------------------------------------------------ 10. dry-run
def t10_dry_run():
    import tempfile

    db = Path(tempfile.mkdtemp()) / "q2.db"
    outdir = Path(tempfile.mkdtemp())
    orig_db, orig_out = config.STATE_PATH, config.OUTPUT_DIR
    config.STATE_PATH, config.OUTPUT_DIR = db, outdir
    state.init(db)
    try:
        res = pipeline.create_quiz(topic="", mock=True, dry_run=True)
        assert res["status"] == "dry-run" and Path(res["link"]).exists()
        html = Path(res["link"]).read_text(encoding="utf-8")
        assert "su-quiz" in html
    finally:
        config.STATE_PATH, config.OUTPUT_DIR = orig_db, orig_out
        db.unlink(missing_ok=True)
    print(" 10. quiz dry-run writes local preview ✔")


def main():
    print("QUIZ ENGINE (v26) TESTS")
    t1_rotation()
    t2_mock_quiz()
    t3_validation()
    t4_build_html()
    t5_sanitize()
    t6_finalize()
    t7_widget()
    t8_gemini_prompt()
    t9_pipeline_mock()
    t10_dry_run()
    print("ALL QUIZ TESTS PASSED ✔")


if __name__ == "__main__":
    main()
