"""1000x STRESS AUDIT — fuzz every core function with random/edge inputs.

Silent failure = revenue loss. Idi deploy mundu battery:
  - optimize_slug: 300 random inputs (unicode/empty/long/keyword edge)
  - insert_ad_shortcodes: 200 random HTML structures
  - schema_jsonld: 100 random payloads -> JSON.parse must succeed
  - validate_article: 200 random dicts -> no crash, score 0-100
  - sanitize_html: XSS payload battery
  - topic pickers: 1000 iterations (literal 1000x)
  - full mock pipeline: 5 runs end-to-end
"""

import json
import random
import re
import string
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from autoblog import monetize, seo, topic_engine, validator  # noqa: E402

random.seed(20260907)


def rand_text(n=20, telugu=False):
    if telugu:
        pool = "అఆఇఈఉఊఎఏఐఒఔకగచజటడణతదనపఫబభమయరలవశషసహ0123456789 "
    else:
        pool = string.ascii_letters + string.digits + " -_.<>\"'\\/&?!తెలుగు\n\t"
    return "".join(random.choice(pool) for _ in range(random.randint(0, n)))


def main():
    print("1000x STRESS AUDIT:")
    fails = []

    # ---- 1. optimize_slug fuzz (300x) ----
    for i in range(300):
        raw = rand_text(40, telugu=random.random() < 0.3)
        kw = rand_text(30, telugu=random.random() < 0.4)
        out = seo.optimize_slug(raw, kw)
        assert isinstance(out, str) and out, (i, raw, kw, out)
        assert len(out) <= 60, (i, out)
        assert not out.startswith("-") and not out.endswith("-"), (i, out)
        assert "--" not in out, (i, out)
        if out != "studentup-post":
            # ascii-safe (Telugu slugs via _safe_slug upstream; direct call
            # with ascii input must give ascii slug)
            if raw.isascii():
                assert re.fullmatch(r"[a-z0-9-]+", out), (i, raw, out)
    print("  1. optimize_slug fuzz 300x ✔ (non-empty, <=60, no --, charset)")

    # ---- 2. insert_ad_shortcodes fuzz (200x) ----
    for i in range(200):
        paras = "".join(f"<p>{rand_text(30)}</p>" for _ in range(random.randint(0, 10)))
        tables = "".join("<table><tr><td>x</td></tr></table>"
                         for _ in range(random.randint(0, 3)))
        faq = "<h2>FAQ</h2><p>q</p>" if random.random() < 0.5 else ""
        html = paras + tables + faq
        max_ads = random.randint(1, 5)
        cls = random.random() < 0.5
        out = seo.insert_ad_shortcodes(html, "[AD]", max_ads=max_ads, cls_safe=cls)
        n = out.count("[AD]")
        assert n <= max_ads, (i, n, max_ads)
        assert out.count("<p>") == html.count("<p>"), (i, "content lost!")
        if cls and n:
            assert out.count('min-height:280px') == n, (i, "wrapper mismatch")
            assert out.count("<div") == out.count("</div>") == n, (i, "unbalanced div")
        # shortcode never inside a tag
        for m in re.finditer(r"<[^>]*\[AD\][^<]*>", out):
            fails.append((i, f"shortcode inside tag: {m.group(0)[:50]}"))
    assert not fails, fails[:3]
    print("  2. insert_ad_shortcodes fuzz 200x ✔ (cap, content intact, balanced)")

    # ---- 3. schema_jsonld JSON validity (100x) ----
    for i in range(100):
        title = rand_text(50) or "t"
        desc = rand_text(60) or "d"
        faq = [{"question": rand_text(30), "answer": rand_text(40)}
               for _ in range(random.randint(0, 4))]
        html = seo.schema_jsonld(title, desc, faq, "2026-01-10", "slug-x",
                                 date_modified=rand_text(10) or "2026-09-07")
        for m in re.finditer(r'<script type="application/ld\+json">(.*?)</script>',
                             html, flags=re.S):
            json.loads(m.group(1))  # must parse — no exceptions
    print("  3. schema JSON-LD validity 100x ✔ (quotes/newlines/unicode parse)")

    # ---- 4. validate_article fuzz (200x) ----
    for i in range(200):
        article = {
            "title": rand_text(40),
            "focus_keyword": rand_text(20) if random.random() < 0.7 else "",
            "content_html": "".join(f"<p>{rand_text(60)}</p>"
                                    for _ in range(random.randint(0, 6))),
            "meta_description": rand_text(80),
            "tags": [rand_text(6) for _ in range(random.randint(0, 10))],
            "faq": [{"question": "q", "answer": "a"}
                    for _ in range(random.randint(0, 5))],
            "external_links": [{"text": "t", "url": "https://x.in"}]
            if random.random() < 0.5 else [],
            "quick_answer": rand_text(30),
            "secondary_keywords": [rand_text(10) for _ in range(random.randint(0, 5))],
        }
        qa = validator.validate_article(article, article["content_html"])
        assert 0 <= qa["score"] <= 100, (i, qa["score"])
        assert qa["words"] >= 0
    print("  4. validate_article fuzz 200x ✔ (no crash, score bounded)")

    # ---- 5. sanitize_html XSS battery ----
    payloads = [
        '<p onclick="alert(1)">x</p>',
        "<p onerror=alert(2)>x</p>",
        '<a href="javascript:alert(3)">x</a>',
        "<a href='JAVASCRIPT:alert(4)'>x</a>",
        '<a href="data:text/html,<script>alert(5)</script>">x</a>',
        '<h2 onmouseover="hack()">t</h2>',
        '<td onload="x()">c</td>',
        '<a href="vbscript:evil()">x</a>',
    ]
    for p in payloads:
        out = validator.sanitize_html(p)
        low = out.lower()
        assert "alert" not in low and "hack" not in low and "evil" not in low, (p, out)
        assert "javascript:" not in low and "vbscript:" not in low, (p, out)
        assert "onerror" not in low and "onclick" not in low, (p, out)
    print("  8. sanitize_html XSS battery ✔ (8/8 payloads neutralized)")

    # ---- 6. topic pickers 1000x (literal) ----
    import tempfile

    tmp = Path(tempfile.mkdtemp()) / "s.db"
    from autoblog import state as st

    st.init(tmp)
    for i in range(1000):
        cat = topic_engine.pick_category(tmp)
        assert isinstance(cat, str) and cat, (i, cat)
        idea = topic_engine.pick_listicle_idea([])
        assert isinstance(idea, str) and idea, (i, idea)
        posts = [{"title": rand_text(30), "link": "l"} for _ in range(5)]
        ordered = monetize.prioritize_money_pages(posts)
        assert len(ordered) == 5, (i, "lost posts!")
    tmp.unlink(missing_ok=True)
    print("  6. pickers 1000x ✔ (category/idea/money-page always valid)")

    # ---- 7. full mock pipeline 5x end-to-end ----
    for i in range(5):
        r = subprocess.run(
            [str(Path(".venv/bin/python")), "run.py", "--dry-run", "--mock", "--force"],
            capture_output=True, text=True, timeout=120,
            env={"PATH": "/usr/bin:/bin", "PYTHONUNBUFFERED": "1",
                 "OUTPUT_DIR": "/tmp/stress_out", "STATE_PATH": "/tmp/stress_state.db"})
        assert r.returncode == 0, (i, r.stdout[-400:], r.stderr[-400:])
        assert "DRY-RUN" in r.stdout or "mock" in r.stdout.lower(), (i, r.stdout[-200:])
    print("  7. full mock pipeline 5x end-to-end ✔ (exit 0, drafts simulated)")

    # ---- 8. --gsc Search Console opportunities ----
    import csv as _csv

    gsc = Path("/tmp/stress_gsc.csv")
    with gsc.open("w", newline="") as f:
        w = _csv.writer(f)
        w.writerow(["Top queries", "Clicks", "Impressions", "CTR", "Position"])
        w.writerow(["nsp scholarship status", "30", "5100", "0.59%", "6.1"])
        w.writerow(["ap eamcet notification", "5", "800", "0.63%", "14.7"])
        w.writerow(["brand query", "900", "2000", "45.00%", "1.2"])   # excluded
        w.writerow(["tiny query", "0", "40", "0%", "10.0"])           # excluded
    r2 = subprocess.run(
        [str(Path(".venv/bin/python")), "run.py", "--gsc", str(gsc)],
        capture_output=True, text=True, timeout=60, env={"PATH": "/usr/bin:/bin"})
    assert r2.returncode == 0 and "2 striking-distance" in r2.stdout, r2.stdout
    assert "nsp scholarship status" in r2.stdout
    assert "brand query" not in r2.stdout and "tiny query" not in r2.stdout
    print("  8. --gsc striking-distance finder ✔ (filter + ranking correct)")

    print("ALL 1000x STRESS AUDIT TESTS PASSED ✔"
          " (300+200+100+200+8+3000+5 calls)")


if __name__ == "__main__":
    main()
