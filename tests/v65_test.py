# -*- coding: utf-8 -*-
"""v65 tests — PIN-TO-PIN GATE + GOOGLE VISIBILITY (Trends/Suggest) ENGINE.

Enduku (v65 lo pattukunna bug + mee requirement):
  1) `seo.jobposting_obj` lo `rec["salary_min"]` KeyError — salary keys lekapote
     publish path lo **crash** (500). Ippudu safe int() + regression test.
  2) "Pin to pin check chesi rasetappudu real time ga anni perfect ga undala" →
     `autoblog/post_gate.py` = 67 checks (v65 lo 47 · v66 lo +20) (content/SEO/schema/media/links/ads/
     freshness/Google readiness) + prathi post ki certificate file + critical
     fail unte publish block (PIN_GATE_BLOCK).
  3) "Google suggest cheyali + trending lo undali" → `autoblog/trends.py` =
     Google Trends RSS + Suggest capture → niche filter → topic queue (demand signal).

Checks (offline only):
  * trends: ET parse + regex fallback (unbound prefix) + suggest + niche filter
  * trends: queue dedupe/consume/next + keep_days cleanup + capture(fetcher=...)
  * trends offline-safe: fetch fail → [] (bot crash avvadu)
  * post_gate: self_test 100/100 · 0 critical · 8 groups · row contract
  * post_gate: dev text → critical + block · missing title/meta → critical
  * post_gate: certificate files (json + md) write avutayi
  * pipeline: gate create+update paths · critical block path · notifier line
  * rm100.optimize: trace + reached + idempotent
  * seo: jobposting salary crash regression + JSON-LD @id graph linkage
  * readiness: pin_gate + trends checks · score 100 · ≥25 system checks
  * docs: MANUAL PART 24 + README v65 + GO_LIVE

Run: python tests/v65_test.py   (also via python run.py --test-all)
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from autoblog import config, post_gate, readiness, rm100, seo, trends  # noqa: E402

FAKE_RSS = ("<rss xmlns:ht='https://trends.google.com/trending/rss'><channel>"
            "<item><title>TSPSC Group 2 notification 2026</title>"
            "<ht:approx_traffic>50000+</ht:approx_traffic>"
            "<ht:news_item><ht:news_item_title>TSPSC notification out</ht:news_item_title>"
            "</ht:news_item></item>"
            "<item><title>Bigg Boss elimination</title></item>"
            "</channel></rss>")
FAKE_RSS_BADPREFIX = ("<rss><channel><item><title>AP DSC hall ticket 2026</title>"
                      "<ht:approx_traffic>20K+</ht:approx_traffic></item></channel></rss>")
FAKE_SUGGEST = '["tspsc",["tspsc group 2 syllabus","ap dsc hall ticket","movie review"]]'


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def _tmp_queue() -> Path:
    return Path(config.OUTPUT_DIR) / "trend_queue_v65_test.json"


# ---------------------------------------------------------------- trends

def test_trends_parsers():
    rows = trends.parse_trends_rss(FAKE_RSS)
    assert len(rows) == 2, rows
    assert rows[0]["title"].startswith("TSPSC") and rows[0]["traffic"] == "50000+"
    assert "TSPSC notification out" in rows[0]["news"], rows[0]
    # regex fallback (unbound prefix — real feeds lo vastundi)
    fb = trends.parse_trends_rss(FAKE_RSS_BADPREFIX)
    assert len(fb) == 1 and "AP DSC" in fb[0]["title"], fb
    assert trends.parse_trends_rss("") == [] and trends.parse_trends_rss("<rss/>") == []
    sugg = trends.parse_suggest(FAKE_SUGGEST)
    assert sugg[:2] == ["tspsc group 2 syllabus", "ap dsc hall ticket"], sugg
    assert trends.parse_suggest("not json") == []


def test_trends_niche_filter_and_score():
    rows = trends.parse_trends_rss(FAKE_RSS)
    picked = trends.relevant(rows)
    assert len(picked) == 1 and "TSPSC" in picked[0]["title"], picked
    assert trends.is_niche("పోలీస్ కానిస్టేబుల్ నోటిఫికేషన్") is True
    assert trends.is_niche("movie review") is False
    high = trends.score_topic("TSPSC Group 2 notification 2026 apply online")
    low = trends.score_topic("some random thing")
    assert high > low and 0 <= low <= 100 and 0 <= high <= 100, (high, low)


def test_trends_queue_lifecycle():
    path = _tmp_queue()
    rss = trends.relevant(trends.parse_trends_rss(FAKE_RSS))
    sugg = [s for s in trends.parse_suggest(FAKE_SUGGEST) if trends.is_niche(s)]
    q1 = trends.queue_topics(rss, sugg, path=path, keep_days=1)
    assert q1["added"] >= 3, q1
    q2 = trends.queue_topics(rss, sugg, path=path, keep_days=1)
    assert q2["added"] == 0, "dedupe pani cheyyaledu"
    top = trends.next_topics(limit=3, path=path)
    assert top and all(int(t["score"]) >= 0 for t in top)
    assert trends.consume(str(top[0]["title"]), path=path) is True
    after = trends.next_topics(limit=10, path=path)
    assert str(top[0]["title"]).lower() not in [str(t["title"]).lower() for t in after]
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["used"], "used list maintain avvali"
    path.unlink()


def test_trends_capture_and_offline_safety():
    def fake_get(url):
        return FAKE_RSS if "trending" in url else FAKE_SUGGEST

    res = trends.capture(queue=False, fetcher=fake_get)
    assert res["trends"] == 1 and res["suggest"] >= 2, res
    # offline: fetch fail → empty, crash ledu
    assert trends.capture(queue=False, fetcher=lambda url: "")["trends"] == 0
    assert trends.fetch_trends(fetcher=lambda url: "") == []
    assert trends.fetch_suggest("x", fetcher=lambda url: "") == []
    src = read(ROOT / "autoblog" / "trends.py")
    assert "NICHE_WORDS" in src and "google-suggest" in src and "google-trends" in src


# ---------------------------------------------------------------- post_gate

def test_pin_gate_self_test():
    res = post_gate.self_test()
    assert res["score"] == 100, res["score"]
    assert res["passed"] == res["total"] and res["total"] >= 45, res["total"]
    assert res["critical_fails"] == [], res["critical_fails"]
    assert res["rankmath"] == 100
    groups = {r["group"] for r in res["rows"]}
    assert groups == set(post_gate.GROUPS), groups
    for r in res["rows"]:
        assert {"id", "group", "label", "ok", "weight", "critical", "scored",
                "detail"} <= set(r), r


def test_pin_gate_critical_and_block():
    art = rm100.sample_article()
    rm100.apply(art)
    art["title"] = ""                      # title ledu → critical
    art["meta_description"] = ""           # meta ledu → critical
    art["content_html"] += "<p>lorem ipsum dolor sit amet</p>"   # dev text → critical
    art["_fact"] = ["30-11-2027 (source lo ledu)"]               # unverified → critical
    res = post_gate.run(art)
    crit = set(res["critical_fails"])
    for want in ("title_kw", "meta_ok", "no_dev_text", "facts_clean"):
        assert want in crit, (want, crit)
    assert res["block"] is True and res["score"] < 100
    old = config.PIN_GATE_BLOCK
    try:
        config.PIN_GATE_BLOCK = False
        assert post_gate.run(art)["block"] is False
    finally:
        config.PIN_GATE_BLOCK = old


def test_pin_gate_certificate_files():
    res = post_gate.self_test()
    paths = post_gate.write_certificate(res, out_dir=Path(config.OUTPUT_DIR) / "certificates")
    for key in ("json", "md"):
        p = Path(paths[key])
        assert p.exists() and p.stat().st_size > 400, paths
    md = Path(paths["md"]).read_text(encoding="utf-8")
    assert "Pin-to-pin certificate" in md and "| CONTENT |" in md and "100/100" in md
    data = json.loads(Path(paths["json"]).read_text(encoding="utf-8"))
    assert data["cert_id"] == res["cert_id"] and len(data["rows"]) == res["total"]
    Path(paths["json"]).unlink()
    Path(paths["md"]).unlink()


def test_pin_gate_text():
    txt = post_gate.certificate_text(post_gate.self_test())
    assert "PIN-TO-PIN CERTIFICATE" in txt and "GOOGLE READINESS" in txt
    assert "critical ok" in txt


# ---------------------------------------------------------------- pipeline

def test_pipeline_and_optimize_wiring():
    pipe = read(ROOT / "autoblog" / "pipeline.py")
    assert pipe.count("post_gate.run(") >= 2, "create + update rendu paths"
    assert "write_certificate" in pipe and '"error": "pin_gate"' in pipe
    assert "rm100.optimize(" in pipe, "iterative (real-time) optimize"
    assert "PIN GATE BLOCK" in pipe
    notifier = read(ROOT / "autoblog" / "notifier.py")
    assert "Pin-to-pin" in notifier and "_gate" in notifier
    art = rm100.sample_article()
    opt = rm100.optimize(art, target=100, max_passes=3)
    assert opt["score"] == 100 and opt["reached"] is True
    assert opt["passes"] and "score" in opt["passes"][0]
    opt2 = rm100.optimize(art, target=100, max_passes=3)
    assert opt2["score"] == 100 and len(opt2["passes"]) == 1, opt2["passes"]


def test_seo_jobposting_crash_regression():
    # v65 bug: salary keys lekapote KeyError → crash. Ippudu safe.
    no_salary = {"org_name": "TSPSC", "apply_end": "2026-12-31"}
    obj = seo.jobposting_obj(no_salary, "TSPSC Group 2", "x" * 160, "2026-09-18")
    assert obj and "baseSalary" not in obj, obj
    with_salary = dict(no_salary, salary_min="25000", salary_max="45000")
    obj2 = seo.jobposting_obj(with_salary, "TSPSC Group 2", "x" * 160, "2026-09-18")
    assert obj2["baseSalary"]["value"]["minValue"] == 25000, obj2
    bad = dict(no_salary, salary_min="abc", salary_max="")
    assert seo.jobposting_obj(bad, "T", "x" * 160, "2026-09-18") is not None
    expired = {"org_name": "TSPSC", "apply_end": "2020-01-01"}
    assert seo.jobposting_obj(expired, "T", "x" * 160, "2026-09-18") is None
    src = read(ROOT / "autoblog" / "seo.py")
    assert 'rec["salary_min"]' not in src, "KeyError pattern malli raakudadu"


def test_seo_graph_linkage():
    html = seo.schema_jsonld(title="TSPSC Group 2 2026 — Complete Details",
                             description="x" * 140, faq=[],
                             date_published="2026-09-18", slug="tspsc-group-2")
    assert "#org" in html and "#website" in html, "Organization/WebSite @id linkage"
    assert '"isPartOf"' in html and "worksFor" in html


# ---------------------------------------------------------------- readiness

def test_readiness_v65():
    names = [n for n, _ in readiness.CHECKS]
    for want in ("pin_gate", "trends", "rm100", "theme_v64", "php_lint"):
        assert want in names, want
    assert readiness.c_pin_gate()[0]["ok"], readiness.c_pin_gate()[0]
    assert readiness.c_trends()[0]["ok"], readiness.c_trends()[0]
    rep = readiness.run_report()
    assert rep["score"] == 100, rep["score"]
    assert rep["total"] >= 25, rep["total"]


def test_docs_v65():
    manual = read(ROOT / "MANUAL_ADVANCED_CHECKLIST.md")
    assert "PART 24" in manual and "post_gate" in manual and "trends" in manual
    assert re.search(r"Last updated: v6[5-9]|Last updated: v[7-9]\d", manual), "footer"
    readme = read(ROOT / "README.md")
    assert "v65" in readme and "post_gate" in readme
    go = read(ROOT / "GO_LIVE_CHECKLIST.md")
    assert "PIN_GATE_BLOCK" in go or "pin-to-pin" in go.lower()
    env = read(ROOT / ".env.example")
    assert "PIN_GATE_BLOCK" in env and "TRENDS_GEO" in env
    main_src = read(ROOT / "autoblog" / "main.py")
    assert "--pin-check" in main_src and "--trends-queue" in main_src


def main():
    print("=" * 70)
    print("  v65 — PIN-TO-PIN GATE (47 checks + certificate) + TRENDS/SUGGEST ENGINE")
    print("=" * 70)
    tests = [
        ("trends: RSS parse (ET + regex fallback) + suggest", test_trends_parsers),
        ("trends: niche filter + demand score", test_trends_niche_filter_and_score),
        ("trends: queue dedupe/consume/next lifecycle", test_trends_queue_lifecycle),
        ("trends: capture + offline safety (crash ledu)", test_trends_capture_and_offline_safety),
        ("pin gate: self-test 100/100 · 8 groups · row contract", test_pin_gate_self_test),
        ("pin gate: critical detection + PIN_GATE_BLOCK", test_pin_gate_critical_and_block),
        ("pin gate: certificate json+md files", test_pin_gate_certificate_files),
        ("pin gate: printable certificate text", test_pin_gate_text),
        ("pipeline: gate create/update + block + optimize", test_pipeline_and_optimize_wiring),
        ("seo: jobposting salary KeyError regression", test_seo_jobposting_crash_regression),
        ("seo: JSON-LD @id graph (brand/E-E-A-T)", test_seo_graph_linkage),
        ("readiness: pin_gate + trends · 100/100 · 25+ checks", test_readiness_v65),
        ("docs: MANUAL PART 24 + README v65 + GO_LIVE + env", test_docs_v65),
    ]
    failed = 0
    for name, fn in tests:
        try:
            fn()
            print(f"  {name} ✔")
        except AssertionError as exc:
            failed += 1
            print(f"  {name} ✘  {exc}")
        except Exception as exc:  # noqa: BLE001
            failed += 1
            print(f"  {name} ✘  {type(exc).__name__}: {exc}")
    print("-" * 70)
    if failed:
        print(f"  {failed} TEST(S) FAILED ✘")
        return 1
    print("ALL v65 PIN-TO-PIN + GOOGLE-VISIBILITY TESTS PASSED ✔")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
