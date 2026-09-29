# -*- coding: utf-8 -*-
"""v153 — static instant search index (no REST query per keystroke)."""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

THEME = ROOT / "wordpress-theme" / "studentup"
IDX = THEME / "inc" / "searchindex.php"
CMDK = THEME / "assets" / "js" / "studentup-cmdk.js"


def test_index_is_cached_and_invalidated():
    src = IDX.read_text(encoding="utf-8")
    assert "get_transient" in src and "set_transient" in src, "cache ledu"
    for hook in ("save_post", "deleted_post", "untrash_post"):
        assert f"add_action( '{hook}', 'studentup_flush_search_index' )" in src, f"{hook} flush ledu"
    print("      index cached in a transient and flushed on content change ✔")


def test_index_endpoint_is_safe():
    src = IDX.read_text(encoding="utf-8")
    assert "X-Robots-Tag: noindex" in src, "index JSON Google ki index avvakoodadu"
    assert "application/json" in src
    assert "post_status'         => 'publish'" in src.replace("  ", "  "), "published posts matrame"
    assert "wp_json_encode" in src and "esc_url_raw" in src
    assert "no_found_rows" in src, "shared hosting perf guard ledu"
    print("      endpoint: noindex, published posts only, escaped ✔")


def test_index_size_is_bounded():
    src = IDX.read_text(encoding="utf-8")
    body = src.split("function studentup_index_limit")[1][:400]
    assert "20" in body and "1000" in body, "index size clamp ledu"
    print("      index size clamped (20-1000 posts) ✔")


def test_palette_searches_locally_first():
    js = CMDK.read_text(encoding="utf-8")
    assert "localHits" in js and "INDEX_KEY" in js
    search = js.split("function search(q)")[1][:700]
    assert search.index("localHits") < search.index("fetch("), \
        "local index kanna mundu REST call cheyyakoodadu"
    assert "localStorage.setItem(INDEX_KEY" in js, "index browser lo cache avvali"
    assert "STUDENTUP.indexVer" in js, "version stamp ledu — stale index vastundi"
    print("      palette searches the cached index before any network call ✔")


def test_palette_still_has_a_fallback():
    js = CMDK.read_text(encoding="utf-8")
    assert "STUDENTUP.rest" in js, "REST fallback poyindi"
    assert js.count(".catch(function") >= 2, "network fail ayithe kuda result ivvali"
    print("      REST + quick-link fallback kept (offline safe) ✔")


def test_wired_into_theme():
    fns = (THEME / "functions.php").read_text(encoding="utf-8")
    assert "inc/searchindex.php" in fns
    opts = (THEME / "inc" / "options.php").read_text(encoding="utf-8")
    assert "'static_search'" in opts and "'index_limit'" in opts
    assert re.search(r"STUDENTUP\.indexUrl", IDX.read_text(encoding="utf-8"))
    print("      wired: require + admin toggles + front-end config ✔")


TESTS = [
    ("cache", test_index_is_cached_and_invalidated),
    ("endpoint", test_index_endpoint_is_safe),
    ("bounded", test_index_size_is_bounded),
    ("local first", test_palette_searches_locally_first),
    ("fallback", test_palette_still_has_a_fallback),
    ("wiring", test_wired_into_theme),
]


def main() -> int:
    bad = 0
    for name, fn in TESTS:
        try:
            fn()
            print(f"  {name} ✔")
        except Exception as exc:  # noqa: BLE001
            bad += 1
            print(f"  {name} ✘ {type(exc).__name__}: {exc}")
    print("-" * 70)
    print("ALL v153 TESTS PASSED ✔" if not bad else f"{bad} TEST(S) FAILED ✘")
    return int(bool(bad))


if __name__ == "__main__":
    raise SystemExit(main())
