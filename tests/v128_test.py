# -*- coding: utf-8 -*-
"""v128 regression checks for verified Breaking News + Success Stories UI."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
THEME = ROOT / "wordpress-theme" / "studentup"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_success_stories_is_after_software_in_all_surfaces():
    functions = read(THEME / "functions.php")
    bot = read(ROOT / "autoblog" / "breaking.py")
    preview = read(ROOT / "preview" / "index.html")
    used_functions = functions.split("function studentup_most_used()", 1)[1].split("function studentup_cat_aliases", 1)[0]
    assert used_functions.index("software-jobs") < used_functions.index("success-stories")
    assert bot.index('"cat": "software"') < bot.index('"cat": "success-stories"')
    assert preview.index('data-goto-cat="software" data-count-cat="software"') < preview.index(
        'data-goto-cat="success-stories" data-count-cat="success-stories"')
    assert 'data-cat="success-stories"' in preview
    assert "🏆" in preview
    assert "function studentup_seed_categories" in functions
    assert "after_switch_theme" in functions and "admin_init" in functions
    assert "studentup_category_seed_version" in functions


def test_breaking_surface_is_honest_and_motion_safe():
    php = read(THEME / "inc" / "breaking.php")
    css = read(THEME / "style.css")
    preview = read(ROOT / "preview" / "index.html")
    fixture = json.loads(read(ROOT / "preview" / "data" / "breaking.json"))
    assert "Breaking News" in php and "Verified source feed" in php
    assert "No new verified breaking updates right now" in php
    assert "stale feed" in php and "36 * HOUR_IN_SECONDS" in php
    assert "verified" in php and "source_verified" in php
    breaking = read(ROOT / "autoblog" / "breaking.py")
    assert "def verify_candidates" in breaking and "build_items(verify_candidates(raw))" in breaking
    assert "prefers-reduced-motion:reduce" in css
    assert "@keyframes breaking-in" in css and "@keyframes breaking-item-in" in css
    assert 'id="breaking"' in preview and "Live source check" in preview
    assert fixture["items"] == []
    assert "invent" not in preview.lower()


def test_source_recheck_and_review_gate_are_wired():
    pipeline = read(ROOT / "autoblog" / "pipeline.py")
    helper = read(ROOT / "autoblog" / "reverification.py")
    assert "reverification.refresh([src] + extras)" in pipeline
    assert "reverification.refresh(extras)" in pipeline
    assert "immediately before drafting" in pipeline
    assert "SOURCE RECHECK FAILED" in helper
    assert "publish_article(article)" in pipeline
    assert "force_draft" in pipeline


if __name__ == "__main__":
    tests = [value for name, value in globals().items() if name.startswith("test_")]
    for test in tests:
        test()
    print(f"v128: {len(tests)}/{len(tests)} checks passed")
