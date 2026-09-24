# -*- coding: utf-8 -*-
"""v63 tests — MISTAKE-FREE SEO + POST EDIT: Rank Math REST bridge + meta verification.

Enduku idi (nijamaina problem fix):
  WordPress default ga custom meta ni REST lo accept cheyyadu. Bot
  `rank_math_focus_keyword`/`title`/`description` pampiste 400 → bot **meta lekunda**
  post pettedi → SEO fields khali (silent mistake!). Ippudu:
    1) theme `inc/seo-bridge.php` aa meta keys ni REST ki register chestundi
    2) bot publish/update tarvata **verify** chestundi (land avvaledu ante Telegram warn)
    3) `--update <id>` (+ auto_refresh) tho existing posts ni edit/refresh cheyyadam ok
       (URL/slug same — SEO safe)

Checks (offline only):
  * seo-bridge.php: register_post_meta · show_in_rest · auth_callback · 10 keys ·
    functions.php lo include · theme-info endpoint (bridge seal)
  * WordPressClient.verify_meta(): dict[bool] — land/ledu correct ga cheptundi
  * update_post(): slug/URL safe + meta fail ayithe retry (meta leni)
  * pipeline: create + update rendu chotla verify + missing list + Telegram warn
  * readiness: seo_bridge + post_edit checks pass · pending lo CMP + GSC/GA4
  * packager: zip lo seo-bridge.php undi

Run: python tests/v63_test.py   (also via python run.py --test-all)
"""
from __future__ import annotations

import re
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from autoblog import readiness, wordpress_client  # noqa: E402

THEME = ROOT / "wordpress-theme" / "studentup"
PIPELINE = ROOT / "autoblog" / "pipeline.py"
WP = ROOT / "autoblog" / "wordpress_client.py"


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def test_seo_bridge_file():
    bridge = THEME / "inc" / "seo-bridge.php"
    assert bridge.exists(), "inc/seo-bridge.php undali"
    text = read(bridge)
    for needle in ("register_post_meta", "'show_in_rest'  => true", "auth_callback",
                   "current_user_can( 'edit_post'", "rest_pre_insert_value",
                   "studentup/v1", "/theme-info", "studentup_write_rankmath_meta",
                   "update_post_meta", "/posts/(?P<id>"):
        assert needle in text, needle
    keys = re.findall(r"'(rank_math_[a-z_]+)'", text)
    assert len(set(keys)) >= 8, keys
    for k in ("rank_math_title", "rank_math_description", "rank_math_focus_keyword",
              "rank_math_robots"):
        assert k in keys, k
    fn = read(THEME / "functions.php")
    assert "inc/seo-bridge.php" in fn, "functions.php lo include avvali"
    assert "ABSPATH" in text, "guard"


def test_verify_meta_logic():
    keys = ["rank_math_focus_keyword", "rank_math_title", "rank_math_description"]

    class Fake:
        def get_post(self, post_id):
            return {"meta": {"rank_math_focus_keyword": "tspsc group 2",
                             "rank_math_title": "TSPSC Group 2 — Guide",
                             "rank_math_description": ""}}

    res = wordpress_client.WordPressClient.verify_meta(Fake(), 7, keys)
    assert res == {"rank_math_focus_keyword": True, "rank_math_title": True,
                   "rank_math_description": False}, res

    class Boom:
        def get_post(self, post_id):
            raise wordpress_client.WordPressError("nope")

    res2 = wordpress_client.WordPressClient.verify_meta(Boom(), 7, keys)
    assert res2 == {k: False for k in keys}, res2

    class ListVal:
        def get_post(self, post_id):
            return {"meta": {"rank_math_robots": ["index, follow, max-image-preview:large"]}}

    res3 = wordpress_client.WordPressClient.verify_meta(ListVal(), 7, ["rank_math_robots"])
    assert res3["rank_math_robots"] is True, res3


def test_update_post_is_url_safe_and_meta_safe():
    text = read(WP)
    assert "URL/slug same untundi — SEO safe" in text
    assert 'payload.pop("meta", None)' in text, "meta reject ayithe meta leni retry"
    assert "def update_post(" in text and "def verify_meta(" in text
    assert "def write_seo_meta(" in text and "def set_post_status(" in text
    assert "rankmath/v1/updateMeta" in text, "native Rank Math endpoint fallback"


def test_pipeline_verifies_meta_both_paths():
    text = read(PIPELINE)
    assert text.count("verify_meta") >= 2, "create + update rendu chotla verify"
    assert 'result["seo_meta_missing"] = missing' in text
    assert "SEO meta WAR" in text, "Telegram warning"
    assert "seo-bridge.php" in text, "warning lo fix pointer"
    assert "# Two-phase live publish" in text
    staged = text[text.index("# Two-phase live publish"):text.index("state.record_post")]
    assert 'status="draft" if stage_for_seo' in staged
    assert staged.index("verify_meta") < staged.index("set_post_status")
    assert "studentup_internal_seo_score" not in text
    assert "read_rankmath_state" in text and "rank_math_ui_score" in text
    assert 'meta["rank_math_seo_score"]' not in text
    # create path: verify tarvata state record (order correct)
    create_part = text[text.index("def publish_article("):text.index("def _after_publish_push(")]
    assert create_part.index("verify_meta") < create_part.index("state.record_post")


def test_readiness_includes_new_checks():
    ids = [n for n, _ in readiness.CHECKS]
    assert "seo_bridge" in ids and "post_edit" in ids
    rows = readiness.c_seo_bridge()
    assert rows[0]["ok"], rows[0]
    assert "10 keys" in rows[0]["value"]
    rows2 = readiness.c_post_edit_capability()
    assert rows2[0]["ok"], rows2[0]
    assert "5/5" in rows2[0]["value"]
    rep = readiness.run_report()
    assert rep["score"] == 100, rep["score"]
    assert rep["pending"] >= 8, rep["pending"]
    pending = " ".join(r["label"] for r in readiness.c_owner_pending())
    assert "AdSense CMP" in pending and "Search Console" in pending, pending


def test_zip_contains_bridge():
    out = subprocess.run([sys.executable, str(ROOT / "tools" / "build_wp_theme.py")],
                         capture_output=True, text=True, cwd=str(ROOT))
    assert out.returncode == 0, out.stdout[-300:]
    zip_path = ROOT / "wordpress-theme" / "studentup-theme.zip"
    with zipfile.ZipFile(zip_path) as zf:
        names = zf.namelist()
    assert "studentup/inc/seo-bridge.php" in names, names[:10]
    assert "studentup/functions.php" in names
    plugin_zip = ROOT / "wordpress-plugin" / "studentup-seo-bridge.zip"
    assert plugin_zip.exists(), "standalone SEO bridge plugin zip undali"
    with zipfile.ZipFile(plugin_zip) as plugin:
        pnames = plugin.namelist()
        source = plugin.read(
            "studentup-seo-bridge/studentup-seo-bridge.php").decode("utf-8")
    assert "studentup-seo-bridge/studentup-seo-bridge.php" in pnames
    assert "register_post_meta" in source and "update_post_meta" in source
    assert "current_user_can( 'edit_post'" in source
    assert "studentup_seo_plugin_read" in source
    assert "get_post_meta( $post_id, 'rank_math_seo_score'" in source
    assert "update_post_meta( $post_id, 'rank_math_seo_score'" not in source


def test_docs_v63():
    manual = (ROOT / "MANUAL_ADVANCED_CHECKLIST.md").read_text(encoding="utf-8")
    assert "PART 22" in manual and "seo-bridge" in manual
    go = (ROOT / "GO_LIVE_CHECKLIST.md").read_text(encoding="utf-8")
    assert "Privacy & messaging" in go or "CMP" in go, "AdSense CMP step"
    assert "Search Console" in go
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "seo-bridge" in readme


def main():
    print("=" * 66)
    print("  v63 — MISTAKE-FREE SEO: Rank Math REST bridge + meta verification + post edit")
    print("=" * 66)
    tests = [
        ("seo-bridge.php (REST meta register + auth + theme-info)", test_seo_bridge_file),
        ("verify_meta(): land/ledu + list value + error safe", test_verify_meta_logic),
        ("update_post: URL safe + meta reject retry", test_update_post_is_url_safe_and_meta_safe),
        ("pipeline: create + update rendu chotla verify + warn", test_pipeline_verifies_meta_both_paths),
        ("readiness: seo_bridge + post_edit + CMP/GSC pending", test_readiness_includes_new_checks),
        ("zip lo seo-bridge.php", test_zip_contains_bridge),
        ("docs: MANUAL PART 22 + GO_LIVE CMP/GSC + README", test_docs_v63),
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
    print("-" * 66)
    if failed:
        print(f"  {failed} TEST(S) FAILED ✘")
        return 1
    print("ALL v63 MISTAKE-FREE SEO TESTS PASSED ✔")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
