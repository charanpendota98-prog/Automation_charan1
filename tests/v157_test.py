# -*- coding: utf-8 -*-
"""v157 — CWV/a11y static auditor + the LCP fixes it found."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import cwv_audit  # noqa: E402

THEME = ROOT / "wordpress-theme" / "studentup"
PREVIEW = ROOT / "preview"


def _audit(html: str, tmp_path: Path) -> dict:
    f = tmp_path / "t.html"
    f.write_text(html, encoding="utf-8")
    a = cwv_audit.Auditor()
    a.feed(html)
    a.finish(html)
    return {"errors": a.errors, "warnings": a.warnings}


def test_flags_image_without_dimensions(tmp_path):
    rep = _audit('<html><body><img src="a.jpg" alt="x"></body></html>', tmp_path)
    assert any("width+height" in e for e in rep["errors"]), "CLS check pani cheyyatledu"
    print("      images without width/height flagged (CLS) ✔")


def test_flags_missing_alt_and_labels(tmp_path):
    rep = _audit('<html><body><img src="a.jpg" width="1" height="1">'
                 '<input type="text" id="x"></body></html>', tmp_path)
    assert any("alt" in e for e in rep["errors"])
    assert any("label" in e for e in rep["errors"])
    print("      missing alt and unlabelled fields flagged (a11y) ✔")


def test_decorative_elements_are_not_false_positives(tmp_path):
    rep = _audit('<html><body><a href="/x" tabindex="-1" aria-hidden="true">'
                 '<img src="a.jpg" width="1" height="1" alt=""></a>'
                 '<input type="text" class="hp" aria-hidden="true" tabindex="-1">'
                 '</body></html>', tmp_path)
    assert not rep["errors"], f"false positive: {rep['errors']}"
    print("      aria-hidden decorative markup is not flagged ✔")


def test_flags_render_blocking_head_script(tmp_path):
    rep = _audit('<html><head><script src="a.js"></script></head><body></body></html>', tmp_path)
    assert any("render-blocking" in e for e in rep["errors"])
    ok = _audit('<html><head><script src="a.js" defer></script></head><body></body></html>', tmp_path)
    assert not any("render-blocking" in e for e in ok["errors"])
    print("      render-blocking head scripts flagged, defer accepted ✔")


def test_flags_duplicate_ids(tmp_path):
    rep = _audit('<html><body><div id="a"></div><div id="a"></div></body></html>', tmp_path)
    assert any("duplicate id" in e for e in rep["errors"])
    print("      duplicate ids flagged ✔")


def test_preview_pages_are_clean():
    bad = []
    for path in sorted(PREVIEW.rglob("*.html")):
        if path.name in getattr(cwv_audit, "BUNDLES", set()):
            continue                      # v197.1: single-file bundle (20 docs)
        rep = cwv_audit.audit_file(path)
        if rep["errors"] or rep["warnings"]:
            bad.append((rep["file"], rep["errors"], rep["warnings"]))
    assert not bad, f"CWV/a11y issues: {bad[:3]}"
    print("      every preview page passes the audit ✔")


def test_first_card_image_is_not_lazy():
    tpl = (THEME / "inc" / "template.php").read_text(encoding="utf-8")
    assert "fetchpriority" in tpl and "'eager'" in tpl, "theme lo LCP image inka lazy"
    assert "0 === (int) $idx" in tpl, "first card matrame eager avvali"
    html = (PREVIEW / "index.html").read_text(encoding="utf-8")
    first_img = html.split("<img", 1)[1][:260]
    assert 'loading="lazy"' not in first_img, "preview lo first image inka lazy"
    print("      first (LCP) image loads eagerly, rest stay lazy ✔")


TESTS = [
    ("cls", test_flags_image_without_dimensions),
    ("a11y", test_flags_missing_alt_and_labels),
    ("no false positives", test_decorative_elements_are_not_false_positives),
    ("blocking js", test_flags_render_blocking_head_script),
    ("dup ids", test_flags_duplicate_ids),
    ("preview clean", test_preview_pages_are_clean),
    ("lcp", test_first_card_image_is_not_lazy),
]


def main() -> int:
    import tempfile
    bad = 0
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        for name, fn in TESTS:
            try:
                fn(tmp) if fn.__code__.co_argcount else fn()
                print(f"  {name} ✔")
            except Exception as exc:  # noqa: BLE001
                bad += 1
                print(f"  {name} ✘ {type(exc).__name__}: {exc}")
    print("-" * 70)
    print("ALL v157 TESTS PASSED ✔" if not bad else f"{bad} TEST(S) FAILED ✘")
    return int(bool(bad))


if __name__ == "__main__":
    raise SystemExit(main())
