# -*- coding: utf-8 -*-
"""v97 — REAL-TIME KEYWORD VERIFICATION tests.

Mee brief lo migilina pedda item: "real time lo keyword verify cheyali,
dummy keyword list vaddu".

Ee suite proof istundi:
  1. Autocomplete parse + cache + endpoint fallback pani chestundi
  2. "complete details telugu" lanti INVENTED keyword ni catch chestundi
  3. Verify fail ayithe LIVE phrase tho replace avutundi (topic drift lekunda)
  4. Network ledu ⇒ "unknown" (fake "verified" stamp EPPUDU veyyadu) +
     post BLOCK avvadu (fail-open)
  5. Pipeline + CLI + config + docs wired

Offline-safe: anni tests lo fetcher inject chestam — network ki velladu.
Checks (12).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from autoblog import keyword_verify as kv  # noqa: E402

SUITES_EXPECTED = 91


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="ignore")


def fake(phrases, echo="seed"):
    """client=firefox shape tho deterministic fetcher."""
    return lambda url: json.dumps([echo, list(phrases)])


TSPSC = ["tspsc group 2 notification 2026", "tspsc group 2 hall ticket",
         "tspsc group 2 results", "tspsc group 2 syllabus pdf"]


# ------------------------------------------------------------------ 1 parse

def test_parse_and_prefix() -> None:
    assert kv.parse_suggest(json.dumps(["q", ["a", "b"]])) == ["a", "b"]
    for junk in ("", "not json", "{}", json.dumps(["q"]), json.dumps("x")):
        assert kv.parse_suggest(junk) == [], junk
    # prefix = modati 3 words (full keyword pampithe Google echo chestundi →
    # verification meaningless avutundi)
    assert kv._prefix("tspsc group 2 hall ticket download") == "tspsc group 2"
    assert kv._prefix("ap dsc") == "ap dsc"
    assert kv.normalise("  TSPSC  Group-2!! ") == "tspsc group 2"
    print("      parse junk-safe · prefix 3-word · normalise ✔")


# ------------------------------------------------------------- 2 verified

def test_verified_keyword_gets_rank() -> None:
    r = kv.verify("tspsc group 2 hall ticket", fetcher=fake(TSPSC))
    assert r["verdict"] == kv.VERIFIED, r
    assert r["rank"] == 1, r["rank"]          # 0-based → Suggest lo #2
    assert r["matched"] == "tspsc group 2 hall ticket"
    assert not r["fluff"]
    # subset match: word order/extra words unna pattukovali
    r2 = kv.verify("hall ticket tspsc group 2", fetcher=fake(TSPSC))
    assert r2["verdict"] == kv.VERIFIED, r2
    print("      verified: exact + subset match · rank = demand proxy ✔")


# ---------------------------------------------------------------- 3 fluff

def test_invented_keyword_detected() -> None:
    """LLM invent chese phrases — humans ila search cheyyaru."""
    for bad in ("tspsc group 2 notification complete details telugu",
                "ap dsc 2026 full details",
                "ts police complete guide",
                "ssc cgl everything you need"):
        assert kv.has_fluff(bad), bad
    for ok in ("tspsc group 2 notification 2026", "ap dsc hall ticket",
               "ts police constable results"):
        assert not kv.has_fluff(ok), ok
    r = kv.verify("tspsc group 2 notification complete details telugu",
                  fetcher=fake(TSPSC))
    assert r["verdict"] == kv.WEAK and r["fluff"], r
    print("      fluff detector: invented keywords caught ✔")


# -------------------------------------------------------------- 4 replace

def test_weak_keyword_replaced_with_live_phrase() -> None:
    art = {"focus_keyword": "tspsc group 2 notification complete details telugu"}
    rep = kv.verify_and_fix(art, fetcher=fake(TSPSC))
    assert rep["replaced"] is True, rep
    assert art["focus_keyword"] == "tspsc group 2 notification 2026", art
    assert rep["original"] != art["focus_keyword"]
    assert art["_kw_verify"]["keyword"] == art["focus_keyword"]
    # already-good keyword ni touch cheyyakudadu
    good = {"focus_keyword": "tspsc group 2 results"}
    rep2 = kv.verify_and_fix(good, fetcher=fake(TSPSC))
    assert rep2["replaced"] is False and good["focus_keyword"] == "tspsc group 2 results"
    print("      weak → live phrase replace · verified untouched ✔")


# ----------------------------------------------------------- 5 drift guard

def test_alternative_never_drifts_topic() -> None:
    """TS post ki AP keyword raakudadu — topic drift = wrong-intent traffic."""
    mixed = ["ap police constable notification", "ap dsc 2026 notification"]
    alt = kv.best_alternative("ts police constable recruitment",
                              fetcher=fake(mixed))
    assert alt == "", f"drift jarigindi: {alt!r}"
    # fluff unna suggestion ni alternative ga theesukోkudadu
    junky = ["tspsc group 2 complete details", "tspsc group 2 results"]
    assert kv.best_alternative("tspsc group 2 xyz",
                               fetcher=fake(junky)) == "tspsc group 2 results"
    # chala podugu phrase (>8 words) reject
    longp = ["tspsc group 2 a b c d e f g h i j notification"]
    assert kv.best_alternative("tspsc group 2 xyz", fetcher=fake(longp)) == ""
    print("      alternative: no topic drift · no fluff · length cap ✔")


# ------------------------------------------------------------- 6 fail-open

def test_offline_is_unknown_never_fake_verified() -> None:
    """Network ledu ⇒ 'unknown'. Fake 'verified' stamp EPPUDU veyyakudadu."""
    off = kv.verify("tspsc group 2 notification", fetcher=lambda u: "")
    assert off["verdict"] == kv.UNKNOWN, off
    assert off["rank"] == -1 and off["suggestions"] == []
    # article block avvakudadu + keyword marchakudadu (fail-open)
    art = {"focus_keyword": "tspsc group 2 notification complete details"}
    rep = kv.verify_and_fix(art, fetcher=lambda u: "")
    assert rep["replaced"] is False
    assert art["focus_keyword"] == "tspsc group 2 notification complete details"
    assert art["_kw_verify"]["verdict"] == kv.UNKNOWN
    assert kv.verify("")["verdict"] == kv.UNKNOWN
    print("      offline → unknown · fail-open · no fake stamp ✔")


# ---------------------------------------------------------------- 7 cache

def test_cache_avoids_hammering_google() -> None:
    kv._CACHE.clear()
    calls = {"n": 0}

    def counting(url):
        calls["n"] += 1
        return json.dumps(["seed", TSPSC])

    import autoblog.keyword_verify as mod
    real = mod._http_get
    mod._http_get = counting
    try:
        a = kv.suggestions("tspsc group 2")
        b = kv.suggestions("tspsc group 2")
        assert a == b == TSPSC
        assert calls["n"] == 1, f"cache pani cheyyaledu ({calls['n']} calls)"
        # TTL 0 → malli fetch
        kv.suggestions("tspsc group 2", ttl=0)
        assert calls["n"] == 2
    finally:
        mod._http_get = real
        kv._CACHE.clear()
    print("      cache: same prefix 1 call · TTL honoured ✔")


# ------------------------------------------------------------- 8 fallback

def test_endpoint_fallback() -> None:
    """Modati endpoint fail ayithe rendo Google endpoint try cheyali."""
    assert len(kv.SUGGEST_URLS) >= 2
    assert all("{q}" in u and "client=firefox" in u for u in kv.SUGGEST_URLS)
    seen = []

    def flaky(url):
        seen.append(url)
        return "" if "suggestqueries" in url else json.dumps(["s", TSPSC])

    import autoblog.keyword_verify as mod
    real = mod._http_get
    mod._http_get = flaky
    kv._CACHE.clear()
    try:
        assert kv.suggestions("tspsc group 2") == TSPSC
        assert len(seen) == 2, seen
    finally:
        mod._http_get = real
        kv._CACHE.clear()
    print("      endpoint fallback: 1st fail → 2nd works ✔")


# ---------------------------------------------------------------- 9 audit

def test_audit_summary() -> None:
    rep = kv.audit(["tspsc group 2 results",              # verified
                    "tspsc group 2 zzz nonsense",          # weak
                    "tspsc group 2 notification 2026"],    # verified
                   fetcher=fake(TSPSC))
    assert rep["total"] == 3 and rep["judged"] == 3
    assert rep["counts"][kv.VERIFIED] == 2 and rep["counts"][kv.WEAK] == 1
    assert rep["verified_pct"] == 66.7, rep["verified_pct"]
    # offline: judged 0 → pct 0 (misleading 100% chupinchakudadu)
    off = kv.audit(["a b c"], fetcher=lambda u: "")
    assert off["judged"] == 0 and off["verified_pct"] == 0.0
    print("      audit: counts · pct only on judged rows ✔")


# ------------------------------------------------------------- 10 pipeline

def test_pipeline_wired() -> None:
    src = read(ROOT / "autoblog" / "pipeline.py")
    hyg = src[src.index("def _hygiene"):src.index("_PG_PUBLISH_TIME_CHECKS")]
    assert "keyword_verify" in hyg, "hygiene lo kw verify ledu"
    assert "verify_and_fix" in hyg
    assert "KW_VERIFY" in hyg, "config flag gate ledu"
    # focus_keyword derive TARVATA run avvali (lekapothe khali kw verify)
    assert hyg.index('article["focus_keyword"] = " ".join(toks)') < \
        hyg.index("verify_and_fix"), "verify derive ki mundu run avutondi"
    # advisory — publish ni block cheyyakudadu
    seg = hyg[hyg.index("keyword_verify"):]
    assert "except Exception" in seg, "verify crash ayithe publish aagipotundi"
    from autoblog import config
    assert hasattr(config, "KW_VERIFY") and hasattr(config, "KW_VERIFY_TTL")
    print("      pipeline: derive → verify → advisory try/except ✔")


# ------------------------------------------------------------------ 11 CLI

def test_cli_and_env() -> None:
    main = read(ROOT / "autoblog" / "main.py")
    for flag in ("--verify-keyword", "--keyword-audit"):
        assert flag in main, flag
    assert "keyword_verify" in main and "run_cli" in main
    env = read(ROOT / ".env.example")
    for key in ("KW_VERIFY=", "KW_VERIFY_TTL="):
        assert key in env, f".env.example lo {key} ledu (owner ki teliyadu)"
    assert hasattr(kv, "run_cli")
    print("      CLI flags + .env.example keys ✔")


# ----------------------------------------------------------------- 12 docs

def test_docs_and_suites() -> None:
    suites = len(list((ROOT / "tests").glob("*_test.py")))
    assert suites == SUITES_EXPECTED, f"suites {suites} (v97 tho 77)"
    readme = read(ROOT / "README.md")
    manual = read(ROOT / "MANUAL_ADVANCED_CHECKLIST.md")
    assert "### v97" in readme and "77/77" in readme
    assert "PART 54" in manual and "77/77" in manual
    for name, txt in (("README", readme), ("MANUAL", manual)):
        assert "--verify-keyword" in txt, f"{name} lo CLI ledu"
    # honest limit documented (volume ivvadu ani cheppali)
    low = readme.lower()
    assert "volume" in low, "README lo 'volume ivvadu' honest note ledu"
    print("      docs: README v97 · PART 54 · 77/77 · honest limit ✔")


TESTS = [
    ("suggest parse + prefix", test_parse_and_prefix),
    ("verified keyword rank", test_verified_keyword_gets_rank),
    ("invented keyword detector", test_invented_keyword_detected),
    ("weak → live replace", test_weak_keyword_replaced_with_live_phrase),
    ("alternative drift guard", test_alternative_never_drifts_topic),
    ("offline fail-open", test_offline_is_unknown_never_fake_verified),
    ("cache", test_cache_avoids_hammering_google),
    ("endpoint fallback", test_endpoint_fallback),
    ("audit summary", test_audit_summary),
    ("pipeline wiring", test_pipeline_wired),
    ("CLI + env", test_cli_and_env),
    ("docs + suite count", test_docs_and_suites),
]


def main() -> int:
    failed = 0
    for name, fn in TESTS:
        try:
            fn()
            print(f"  {name} ✔")
        except Exception as exc:  # noqa: BLE001
            failed += 1
            print(f"  {name} ✘  {type(exc).__name__}: {exc}")
    print("-" * 70)
    if failed:
        print(f"  {failed} TEST(S) FAILED ✘")
        return 1
    print("ALL v97 REAL-TIME KEYWORD VERIFICATION TESTS PASSED ✔")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
