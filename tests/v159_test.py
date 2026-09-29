# -*- coding: utf-8 -*-
"""v159 — unfilled ad-slot collapse + image weight audit."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import image_weight_audit as iwa  # noqa: E402

THEME = ROOT / "wordpress-theme" / "studentup"
PREVIEW = ROOT / "preview"


def test_collapse_runs_only_on_adsense_status():
    php = (THEME / "inc" / "adfill.php").read_text(encoding="utf-8")
    assert "data-ad-status" in php, "AdSense fill status chudatledu"
    assert "'unfilled'" in php and "su-ad-empty" in php
    assert "studentup_adsense_client()" in php, "client lekunda kuda script velthundi"
    assert "collapse_unfilled" in php, "option gate ledu"
    # Policy: ad ni refresh/move/auto-click cheyyakudadu. Comments lo aa
    # maatalu undochu - code lo matrame undakudadu, andhuke comments teesi chustam.
    import re as _re
    code = _re.sub(r"/\*.*?\*/", "", php, flags=_re.S)
    code = "\n".join(l for l in code.splitlines() if not l.strip().startswith(("*", "//")))
    for banned in ("setInterval", "refresh(", "location.href", "window.open", ".click("):
        assert banned not in code, f"policy-risky pattern: {banned}"
    assert "disconnect()" in php, "MutationObserver leak avutundi"
    print("      collapse fires only on a real unfilled AdSense response ✔")


def test_collapse_is_wired_and_styled():
    funcs = (THEME / "functions.php").read_text(encoding="utf-8")
    assert "inc/adfill.php" in funcs
    css = (THEME / "style.css").read_text(encoding="utf-8")
    assert ".su-ad-empty" in css and "min-height:0" in css
    opts = (THEME / "inc" / "options.php").read_text(encoding="utf-8")
    assert "'collapse_unfilled'" in opts
    print("      wired in functions.php, options and CSS ✔")


def test_reserved_height_still_there_for_cls():
    ads = (THEME / "inc" / "ads.php").read_text(encoding="utf-8")
    assert "min-height:" in ads and "su-ad-reserved" in ads, \
        "reserve teesesthe CLS thirigi vastundi"
    print("      slots still reserve height while the ad loads (no CLS) ✔")


def test_audit_flags_oversize_and_dedupes():
    rep = iwa.audit_page(PREVIEW / "index.html")
    srcs = [r["src"] for r in rep["images"]]
    assert len(srcs) == len(set(srcs)), "oke file ni rendu sarlu lekka vestondi"
    assert rep["total_kb"] > 0
    print(f"      page image weight measured once per file ({rep['total_kb']:.0f} KB) ✔")


def test_preview_images_are_within_budget():
    bad = []
    for page in sorted(PREVIEW.rglob("*.html")):
        rep = iwa.audit_page(page)
        if rep["total_kb"] > iwa.PAGE_BUDGET_KB:
            bad.append((rep["page"], rep["total_kb"]))
        for r in rep["images"]:
            if r.get("missing") or r["problems"]:
                bad.append((r["src"], r.get("problems")))
    assert not bad, f"image findings: {bad[:4]}"
    print("      every preview image passes the weight audit ✔")


def test_cards_are_modern_format():
    html = (PREVIEW / "index.html").read_text(encoding="utf-8")
    assert ".webp" in html, "card images inka jpg"
    assert "card-tspsc.jpg" not in html
    assert not list((PREVIEW / "assets" / "img").glob("*.jpg")), "purathana jpg files migilipoయాయి"
    print("      card images shipped as webp ✔")
