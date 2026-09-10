"""Rank Math writing-trick tests: slug optimizer, internal-link fallback,
validator v2 checks (title first-half, number, density window, paragraphs)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from autoblog import config, seo, validator  # noqa: E402


def main():
    print("RANK MATH WRITING TRICK TESTS:")

    # ---- 1. slug optimizer ----
    # keyword tokens injected into slug (keyword-in-URL check)
    s1 = seo.optimize_slug("complete-guide-telugu", focus_keyword="SSC CGL 2026 గైడ్")
    assert s1.startswith("ssc-cgl-2026-") and "complete-guide" in s1, s1
    # stopwords stripped
    s2 = seo.optimize_slug("how-to-apply-and-check-the-result-online", "")
    assert s2 == "apply-check-result-online", s2
    # already has tokens -> no duplication
    s3 = seo.optimize_slug("ssc-cgl-2026-guide", focus_keyword="SSC CGL 2026")
    assert s3 == "ssc-cgl-2026-guide", s3
    # empty slug + english keyword
    s4 = seo.optimize_slug("", focus_keyword="NSP Scholarship 2026")
    assert s4 == "nsp-scholarship-2026", s4
    # max length respected
    s5 = seo.optimize_slug("a" * 100, focus_keyword="")
    assert len(s5) <= 60
    print("  1. optimize_slug (keyword tokens + stopwords + caps) ✔")

    # ---- 2. validator v2: title first-half + number + paragraphs ----
    good = {
        "title": "SSC CGL 2026 Complete Guide Telugu lo",
        "focus_keyword": "SSC CGL 2026",
        "content_html": (
            "<p>SSC CGL 2026 apply process simple and clear here friends.</p>"
            "<h2>SSC CGL 2026 Eligibility</h2><p>x</p>"
            "<h2>Process</h2><ol><li>one</li><li>two</li></ol>"
            "<table><tr><td>t</td></tr></table>"
            '<p><a href="https://studentup.in/other/">related</a></p>'
        ),
        "meta_description": "SSC CGL 2026 complete guide " + "x" * 120,
        "tags": ["a", "b", "c", "d", "e"],
        "faq": [{"question": "q", "answer": "a"}] * 3,
        "external_links": [{"text": "o", "url": "https://ssc.gov.in"}],
        "quick_answer": "SSC CGL 2026 answer for snippet test block here.",
        "secondary_keywords": ["s1", "s2", "s3"],
    }
    qa = validator.validate_article(good, good["content_html"])
    assert not any("first-half" in i for i in qa["issues"]), qa["issues"]
    assert not any("number" in i for i in qa["issues"]), qa["issues"]
    assert not any("internal links ledu" in i for i in qa["issues"]), qa["issues"]
    assert not any("too long" in i for i in qa["issues"]), qa["issues"]

    # title WITHOUT keyword/number -> those checks fail
    bad_title = dict(good, title="Complete Guide Telugu lo")
    qa2 = validator.validate_article(bad_title, good["content_html"])
    assert any("first-half" in i or "title lo ledu" in i for i in qa2["issues"])
    assert any("number" in i for i in qa2["issues"])

    # long paragraph flagged
    long_para = "<p>" + ("word " * 200) + "</p>"
    qa3 = validator.validate_article(dict(good, content_html=long_para), long_para)
    assert any("too long" in i or "structure weak" in i for i in qa3["issues"])
    print("  2. validator v2 (first-half, number, internal, paragraphs) ✔")

    # ---- 3. internal-link fallback (pipeline logic smoke) ----
    from autoblog.wordpress_client import WordPressClient

    assert hasattr(WordPressClient, "get_term_link")
    print("  3. get_term_link available (category fallback) ✔")

    # ---- 4. v10: visible-date fix + read-also block + E-E-A-T schema ----
    html_out = seo.enhance(
        "<p>body text ok</p>", focus_keyword="SSC CGL 2026",
        internal_links=[{"link": "https://studentup.in/a/", "title": "Related A"},
                        {"link": "https://studentup.in/b/", "title": "Related B"}],
        external_links=[], quick_answer="Quick answer here friends.",
        faq=[{"question": "q", "answer": "a"}],
        date_str="2026-01-10", date_modified="2026-09-07",
        slug="ssc-cgl-2026", title="SSC CGL 2026 Guide",
        description="desc", category="Govt Jobs")
    # visible badge = modified date (NOT old published)
    assert "Last Updated: 2026-09-07" in html_out
    assert "Last Updated: 2026-01-10" not in html_out
    # schema dates: published preserved, modified updated
    assert '"datePublished": "2026-01-10"' in html_out
    assert '"dateModified": "2026-09-07"' in html_out
    # read-also block at end
    assert "వీటిని కూడా చదవండి" in html_out
    assert 'href="https://studentup.in/a/"' in html_out
    # E-E-A-T author
    assert '"@type": "Person"' in html_out and "Editorial Team" in html_out
    assert '"editor"' in html_out
    # publisher logo: set -> present; empty -> absent
    config.SITE_LOGO_URL = "https://studentup.in/logo.png"
    html_logo = seo.schema_jsonld("T", "d", [], "2026-01-10", "t")
    assert '"logo"' in html_logo
    config.SITE_LOGO_URL = ""
    html_nologo = seo.schema_jsonld("T", "d", [], "2026-01-10", "t")
    assert '"logo"' not in html_nologo
    print("  4. v10 fixes (visible date, read-also, E-E-A-T, logo gate) ✔")


    # ================= v18: honest Rank Math strict + multi-key + refine =================
    import hashlib
    import json as _json
    import tempfile
    import types

    from autoblog import gemini_client as gc
    from autoblog import image_gen, pipeline, state

    KW = "SSC CGL 2026 Notification"
    SECS = ["Overview Key Dates", "Eligibility Criteria", "Age Limit Details",
            "Vacancy Category Wise", "Apply Online Steps", "Application Fee",
            "Exam Pattern 2026", "Syllabus Subject Wise", "Preparation Tips",
            "Cut Off Trends", "Document Verification", "Selection Process",
            "Salary Pay Scale", "Negative Marking Rules", "Why Apply SSC CGL",
            "Important Links 2026"]

    def _good_html():
        parts = [f"<p>{KW} Telugu lo complete ga ee article lo chaduvandi. "
                 "కానీ చాలా మంది students ki details clear kaadu.</p>"]
        for i, sec in enumerate(SECS, 1):
            head = f"{KW}: {sec}" if i % 5 == 1 else sec + " (2026)"
            parts.append(f"<h2>{head}</h2>")
            for j in range(4):
                parts.append(
                    f"<p>{KW} — {sec} వివరాలు ఇక్కడ ఉన్నాయి. "
                    "అందువల్ల అభ్యర్థிகள் దృష్టి పెట్టాలి. మరోవైపు simple ga "
                    "artham ayypothundi. అలాగే official notice check cheyandi. "
                    "చివరగా apply mundu documents ready pettandi.</p>")
            if i == 2:
                parts.append("<table><tr><td>Post</td><td>Count</td></tr>"
                             "<tr><td>PA</td><td>3796</td></tr></table>")
            if i == 3:
                parts.append("<ul><li>Fee Rs 1000 only</li>"
                             "<li>Mode is online</li></ul>")
            if i == 4:
                parts.append(f"<h3>{KW} fee enduku?</h3>"
                             "<p>Fee Rs 1000. కానీ SC/ST students ki "
                             "levu. అందువల్ల benefit teesukondi.</p>")
        parts.append('<a href="https://ssc.nic.in">Official SSC</a>')
        parts.append('<a href="https://studentup.in/best-govt-jobs-2026/">More Jobs</a>')
        return "".join(parts)

    good_html = _good_html()
    good_art = {
        "title": f"{KW}: Apply Online - Complete Guide",
        "focus_keyword": KW,
        "meta_description": (f"{KW} Telugu lo: apply online steps, eligibility, fee, "
                             "vacancy and exam date full details 2026 aspirants kosam."),
        "slug": "ssc-cgl-2026-notification",
        "content_html": good_html,
        "faq": [{"question": "a", "answer": "b"}] * 3,
    }
    rm = validator.rankmath_strict(good_art, good_html)
    assert rm["score"] <= 100 and rm["words"] >= 1500, rm
    assert rm["score"] >= 70, f"good article low: {rm['issues']}"
    qa = validator.validate_article(good_art, good_html)
    assert qa["score"] <= 100, "QA inflation raavadu (max 100)"
    bad = {"title": "Job News", "focus_keyword": "SSC CGL 2026 Notification",
           "meta_description": "short", "slug": "news",
           "content_html": "<p>Ee article ki vasthe chanum. OK.</p>"}
    rb = validator.rankmath_strict(bad)
    assert rb["score"] < 45 and rb["fixes"], rb
    assert any("title" in f for f in rb["fixes"])
    print(f"  5. rankmath_strict honest score (good {rm['score']} vs bad {rb['score']}, capped 100) ✔")

    # ---- 6. multi-key rotation (429 -> next key, dead-flag day lock) ----
    tmpdb = Path(tempfile.mkdtemp()) / "state.db"
    state.init(tmpdb)
    k1, k2 = "keyaaaaaaaaaaaa01", "keybbbbbbbbbbbb02"
    oldsp, oldkeys, oldkey = config.STATE_PATH, config.GEMINI_API_KEYS, config.GEMINI_API_KEY
    config.STATE_PATH, config.GEMINI_API_KEYS, config.GEMINI_API_KEY = tmpdb, [k1, k2], ""
    ok_json = _json.dumps({"title": "Rot", "slug": "rot",
                           "meta_description": "m" * 40,
                           "content_html": "<p>x</p>", "tags": []})
    used, sleepless = [], types.SimpleNamespace(sleep=lambda s: None)
    real_call, real_models, real_time = gc._call_model, gc._models, gc.time
    gc._models = lambda: ["gemini-2.5-flash"]
    gc.time = sleepless

    def rot_call(model, prompt, key=None):
        used.append(key)
        if key == k1:
            raise gc.GeminiError("QUOTA_KEY:deadbeef:429")
        return ok_json

    gc._call_model = rot_call
    try:
        art = gc._generate_core("prompt x", "Central Govt Jobs")
        assert art["title"] == "Rot" and used[0] == k1 and k2 in used
        today = __import__("datetime").date.today().isoformat()
        h1 = hashlib.sha1(k1.encode()).hexdigest()[:8]
        h2 = hashlib.sha1(k2.encode()).hexdigest()[:8]
        assert state.meta_get(tmpdb, f"gemkey:dead:{h1}:{today}") == "QUOTA_KEY"
        assert state.meta_get(tmpdb, f"gemkey:cnt:{h2}:{today}") == "1"
        assert gc._usable_keys() == [k2], "dead key skip avvali"
        print("  6. multi-key rotation (429 -> next key, dead-key day skip) ✔")

        # ---- 7. refine prompt (fixes verbatim + slug identity keep) ----
        cap = {}

        def fake_core(prompt, category="", source=None, strict_category=False):
            cap["p"] = prompt
            cap["cat"] = category
            return {"title": "Better", "slug": "", "meta_description": "m",
                    "content_html": "<p>fixed</p>", "tags": [], "category": category}

        real_core = gc._generate_core
        gc._generate_core = fake_core
        try:
            out = gc.refine_article(
                {"title": "Old T", "slug": "keep-me", "focus_keyword": "kw",
                 "meta_description": "md", "content_html": "<p>draft body here</p>",
                 "category": "Results"},
                ["title lo keyword add", "li 12+ words fix"])
        finally:
            gc._generate_core = real_core
        assert "title lo keyword add" in cap["p"] and "draft body here" in cap["p"]
        assert out["slug"] == "keep-me" and cap["cat"] == "Results"
        print("  7. refine_article (fixes -> prompt, slug preserved) ✔")
    finally:
        gc._call_model, gc._models, gc.time = real_call, real_models, real_time
        config.STATE_PATH, config.GEMINI_API_KEYS, config.GEMINI_API_KEY = oldsp, oldkeys, oldkey

    # ---- 8. pipeline Rank Math gate: refine-adopt / keep-better / mock skip ----
    cfg_key = config.GEMINI_API_KEY
    config.GEMINI_API_KEY = "gate-test"
    low = {"score": 55, "issues": ["x"], "fixes": ["f1", "f2"], "words": 900}
    high = {"score": 93, "issues": [], "fixes": [], "words": 1700}
    rv, rr = validator.rankmath_strict, gc.refine_article
    try:
        n = []

        def strict_once(a, h=""):
            n.append(1)
            return low if len(n) == 1 else high

        validator.rankmath_strict = strict_once
        gc.refine_article = lambda a, f: {**a, "title": "Better Title"}
        art1 = {"content_html": "<p>draft</p>", "title": "Old", "category": "X",
                "focus_keyword": "kw", "meta_description": "m", "slug": "s"}
        res = pipeline._rankmath_gate(dict(art1), "X")
        assert res.get("refined") and res["title"] == "Better Title"
        assert res["_rm_pre"] == 55 and res["_rm"]["score"] == 93

        validator.rankmath_strict = lambda a, h="": low
        gc.refine_article = lambda a, f: {**a, "title": "Worse?"}
        res2 = pipeline._rankmath_gate(dict(art1), "X")
        assert not res2.get("refined") and res2["title"] == "Old"

        res3 = pipeline._rankmath_gate({**art1, "_mock": True}, "X")
        assert not res3.get("refined")
        print("  8. _rankmath_gate (adopt better, keep when no-help, mock skip) ✔")
    finally:
        validator.rankmath_strict, gc.refine_article = rv, rr
        config.GEMINI_API_KEY = cfg_key

    # ---- 9. SEO: TOC/list truncate + mobile clamp CSS + read-also short ----
    h_long = "<h2>" + " ".join(f"step{i}" for i in range(12)) + "</h2><p>" + "word " * 20 + "</p>"
    out_html = seo.enhance(h_long, "focus kw test",
                           [{"link": "https://studentup.in/x/",
                             "title": " ".join(["t"] * 12)}], [])
    assert "\u2026" in out_html, "TOC/read-also truncate rawalsi"
    assert "<style>" in out_html and "clamp(" in out_html, "mobile CSS"
    assert seo._short_title("a b c d e f g h i j k") == "a b c d e f g h …"
    config.MOBILE_HEADLINE_TUNE = False
    try:
        out2 = seo.enhance("<p>plain para words here</p>" * 3, "kw", [], [])
        assert "<style>" not in out2
    finally:
        config.MOBILE_HEADLINE_TUNE = True
    print("  9. SEO (TOC truncate, mobile clamp CSS, toggle off) ✔")

    # ---- 10. thumbnail labels (crop-safe) + AdSense CLI wiring ----
    assert image_gen._pill_label("Central Govt Jobs") == "GOVT JOBS"
    assert image_gen._pill_label("TS Govt Jobs") == "TS GOVT JOBS"
    assert image_gen._pill_label("Totally Unknown Category Here") == "TOTALLY UNKNOWN"
    from autoblog import main as ab_main
    from autoblog.wordpress_client import WordPressClient
    assert hasattr(ab_main, "ensure_adsense") and len(ab_main.ADSENSE_PAGES) == 5
    slugs = [pg[1] for pg in ab_main.ADSENSE_PAGES]
    assert slugs == ["privacy-policy", "about-us", "contact-us",
              "corrections-policy", "editorial-policy"]
    assert hasattr(WordPressClient, "page_exists") and hasattr(WordPressClient, "create_page")
    assert "ORIG_HARD_FLOOR" in Path("autoblog/pipeline.py").read_text(encoding="utf-8")
    print("  10. thumbs labels + AdSense pages CLI + hard floor wired ✔")

    print("ALL RANK MATH TRICK TESTS PASSED ✔")


if __name__ == "__main__":
    main()
