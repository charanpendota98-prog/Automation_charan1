"""v19 playbook-adaptation tests: Google Jobs (JobPosting) schema, deadline
countdown badge, near-duplicate guard (scaled content abuse), corrections
E-E-A-T line, AdSense readiness (20+ posts) and recruitment extraction wiring.
"""

import sys
import tempfile
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from autoblog import config, gemini_client as gc, seo  # noqa: E402
from autoblog import state, validator  # noqa: E402

FUT = (date.today() + timedelta(days=30)).isoformat()
PAST = (date.today() - timedelta(days=4)).isoformat()
REC = {"org_name": "TSPSC", "org_url": "https://tspsc.gov.in",
       "apply_end": FUT, "salary_min": 23430, "salary_max": 75900,
       "identifier": "TSPSC-G2-2026", "location": "Hyderabad"}
DESC = ("Group 2 Services 2026 notification — eligibility, fee, vacancy "
        "details, exam pattern and Telugu explained steps on this page.")


def main():
    print("v19 PLAYBOOK TESTS:")

    # ---- 1. JobPosting: Google-required fields, honest guards ----
    j = seo.jobposting_obj(REC, "TSPSC Group 2 Notification 2026", DESC,
                           date.today().isoformat())
    assert j and j["@type"] == "JobPosting"
    for req in ("title", "description", "datePosted", "validThrough",
                "hiringOrganization", "jobLocation"):
        assert req in j, req
    assert j["validThrough"] == FUT + "T23:59:59+05:30"
    assert j["hiringOrganization"]["sameAs"] == "https://tspsc.gov.in"
    assert j["baseSalary"]["value"]["minValue"] == 23430
    assert j["directApply"] is False  # honest: apply official site lo
    assert seo.jobposting_obj({**REC, "apply_end": PAST}, "t", DESC, "") is None
    assert seo.jobposting_obj({**REC, "org_name": ""}, "t", DESC, "") is None
    assert seo.jobposting_obj(REC, "t", "tiny desc", "") is None
    cfg_off = config.JOB_SCHEMA_ENABLED
    config.JOB_SCHEMA_ENABLED = False
    assert seo.jobposting_obj(REC, "t", DESC, "") is None
    config.JOB_SCHEMA_ENABLED = cfg_off
    print("  1. JobPosting schema (required fields + expired/no-org/short-desc guards) ✔")

    # ---- 2. deadline countdown badge ----
    badge = seo.deadline_badge(FUT)
    assert "days left" in badge and "30 days left" in badge, badge
    assert "CLOSED" in seo.deadline_badge(PAST)
    assert seo.deadline_badge("") == "" and seo.deadline_badge("garbage") == ""
    assert seo.deadline_badge(FUT + "extra") != ""  # tolerant prefix parse
    print("  2. deadline badge (future countdown / past closed / no date none) ✔")

    # ---- 3. enhance wiring: badge visible + JobPosting in graph ----
    html = ("<p>TSPSC Group 2 2026 Notification details Telugu lo.</p>" * 30)
    out = seo.enhance(html, "TSPSC Group 2 2026 Notification", [], [],
                      title="TSPSC Group 2 Notification 2026 - Complete Guide",
                      description=DESC, slug="tspsc-group-2-2026",
                      date_str=date.today().isoformat(), recruitment=REC)
    assert "days left" in out, "countdown insert avvali"
    assert '"@type": "JobPosting"' in out, "JobPosting schema"
    assert "corrections-policy" in out and "mailto" in out, "E-E-A-T corrections"
    # expired deadline → no JobPosting (Google rule) but CLOSED badge shows
    out2 = seo.enhance(html, "kw", [], [], title="T", description=DESC,
                       slug="s", date_str=date.today().isoformat(),
                       recruitment={**REC, "apply_end": PAST})
    assert '"@type": "JobPosting"' not in out2 and "CLOSED" in out2
    print("  3. enhance (badge + JobPosting + corrections; expired → schema off) ✔")

    # ---- 4. near-duplicate guard (scaled content abuse) ----
    base = "ssc cgl notification apply online eligibility form fee exam admit card"
    body_a = " ".join(f"{base} {i} district hyderabad center updates"
                      for i in range(45))
    body_a2 = " ".join(f"{base} {i} district warangal center updates"
                       for i in range(45))   # swapped-name duplicate
    body_b = " ".join(f"ts pgtrb lecturer exam hall ticket download result "
                      f"counselling {i} web notification" for i in range(45))
    fps = [{"slug": "ssc-cgl-2026a",
            "t": validator.fingerprint_tokens("SSC CGL 2026 Notification A. " + body_a)}]
    r, m = validator.near_duplicate("SSC CGL 2026 Notification B", body_a2, fps, 0.62)
    assert r >= 0.62 and m == "ssc-cgl-2026a", (r, m)
    r2, _ = validator.near_duplicate("TSPSC Teacher Exam Update", body_b, fps, 0.62)
    assert r2 < 0.30, r2
    # short pages → never false-positive
    r3, _ = validator.near_duplicate("T", "ok", fps, 0.62)
    assert r3 == 0.0
    print(f"  4. near-dup guard (swap-name {r:.0%} skip, distinct {r2:.0%} pass) \u2714")

    # ---- 5. state fingerprint store: save/load/cap/dedupe ----
    tmp = Path(tempfile.mkdtemp()) / "state.db"
    state.init(tmp)
    old_sp = config.STATE_PATH
    config.STATE_PATH = tmp
    try:
        for i in range(130):
            state.save_fingerprint(tmp, f"slug-{i}", ["tok%d" % i] * 5)
        rows = state.load_fingerprints(tmp)
        assert len(rows) == 120, len(rows)          # capped
        assert rows[0]["slug"] == "slug-129"        # newest first
        state.save_fingerprint(tmp, "slug-129", ["new"] * 6)
        rows = state.load_fingerprints(tmp)
        assert rows[0]["t"] == ["new"] * 6 and len(rows) == 120  # replace, no dup
    finally:
        config.STATE_PATH = old_sp
    print("  5. fingerprint store (cap 120, newest-first, slug replace) ✔")

    # ---- 6. prompts: recruitment extraction + value-add rules ----
    assert "recruitment" in gc.RESPONSE_SCHEMA["properties"]
    props = gc.RESPONSE_SCHEMA["properties"]["recruitment"]["properties"]
    assert {"org_name", "apply_end", "salary_min", "org_url"} <= set(props)
    assert "GUESS cheyyakundu" in gc.WRITING_RULES
    assert "scaled-content rule" in gc.WRITING_RULES or "mirror" in gc.WRITING_RULES
    assert "recruitment" in gc.REFINE_PROMPT_TEMPLATE
    print("  6. Gemini schema+rules (recruitment fields, no-guess, value-add) ✔")

    # ---- 7. AdSense kit: corrections page + 20-post readiness ----
    from autoblog import main as ab_main
    slugs = [pg[1] for pg in ab_main.ADSENSE_PAGES]
    assert slugs == ["privacy-policy", "about-us", "contact-us",
                     "corrections-policy", "editorial-policy"]
    src = (Path(__file__).resolve().parent.parent
           / "autoblog" / "main.py").read_text(encoding="utf-8")
    assert "X-WP-Total" in src or "published_count" in src
    assert "low value" in src and "Human eye" in src
    from autoblog.wordpress_client import WordPressClient
    assert hasattr(WordPressClient, "published_count")

    class FakeResp:
        ok = True
        headers = {"X-WP-Total": "27"}

    class FakeWP:
        _request = lambda self, *a, **k: FakeResp()

    assert WordPressClient.published_count(FakeWP()) == 27
    print("  7. AdSense kit (4 pages incl corrections + 20+ posts readiness) ✔")

    # ---- 8. pipeline source-flow guard raises & scheduled flow safe ----
    src_p = (Path(__file__).resolve().parent.parent / "autoblog"
             / "pipeline.py").read_text(encoding="utf-8")
    assert "SKIP-NEAR-DUP" in src_p
    assert "SKIP-NEAR-COPY" in src_p
    assert "recruitment=article.get(\"recruitment\")" in src_p
    assert "save_fingerprint" in src_p
    print("  8. pipeline guards wired (dup skip + copy floor + fingerprint save) ✔")

    print("ALL v19 PLAYBOOK TESTS PASSED ✔")


if __name__ == "__main__":
    main()
