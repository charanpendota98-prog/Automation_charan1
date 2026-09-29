# -*- coding: utf-8 -*-
"""v154/v155 — internal link engine + personalised picks."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

THEME = ROOT / "wordpress-theme" / "studentup"
AUTOLINK = THEME / "inc" / "autolink.php"
PREVIEW = ROOT / "preview" / "index.html"


def test_autolink_has_hard_brakes():
    src = AUTOLINK.read_text(encoding="utf-8")
    assert "studentup_autolink_max" in src
    body = src.split("function studentup_autolink_max")[1][:300]
    assert "6" in body and "0" in body, "max link clamp ledu"
    assert "$url === $self" in src, "post tanaki tane link cheyyakoodadu"
    assert "isset( $used[ $url ] )" in src, "oke post ki multiple links vaddu"
    print("      link budget, self-link and duplicate guards in place ✔")


def test_autolink_never_touches_protected_markup():
    src = AUTOLINK.read_text(encoding="utf-8")
    guard = src.split("$protected")[1][:400]
    for tag in ("<a", "<h[1-6]", "<script", "<style", "<code", "<pre"):
        assert tag in guard, f"{tag} protect avvaledu"
    print("      headings, existing links, code and scripts protected ✔")


def test_autolink_requires_specific_phrases():
    src = AUTOLINK.read_text(encoding="utf-8")
    assert "mb_strlen( $title ) < 14" in src, "chinna titles ki link cheste spam avutundi"
    assert "esc_url" in src and "esc_html" in src
    print("      only long, specific title phrases are linked ✔")


def test_autolink_reuses_the_cached_index():
    src = AUTOLINK.read_text(encoding="utf-8")
    assert "studentup_build_search_index" in src, "extra DB query vaddu — index reuse cheyali"
    assert "new WP_Query" not in src
    fns = (THEME / "functions.php").read_text(encoding="utf-8")
    assert "inc/autolink.php" in fns
    opts = (THEME / "inc" / "options.php").read_text(encoding="utf-8")
    assert "'autolink'" in opts and "'autolink_max'" in opts
    print("      reuses the cached index, zero extra queries ✔")


def test_personalised_strip_is_local_only():
    html = PREVIEW.read_text(encoding="utf-8")
    assert 'id="suyou"' in html and "studentup-profile-v1" in html
    block = html.split('/* v155: "your 5 today".')[1].split("</script>")[0]
    assert "fetch(" not in block and "XMLHttpRequest" not in block, "profile server ki pampakoodadu"
    assert "removeItem" in block, "reset option ledu"
    assert "su-you-why" in html, "prati row ki reason chupinchali"
    print("      personalised picks: local only, resettable, explained ✔")


def test_personalised_strip_hides_closed_jobs():
    html = PREVIEW.read_text(encoding="utf-8")
    block = html.split('/* v155: "your 5 today".')[1].split("</script>")[0]
    flat = block.replace(" ", "").replace("\n", "")
    assert "left<0)return" in flat, "closed jobs personalised list lo raakoodadu"
    print("      closed jobs never enter the personalised list ✔")


TESTS = [
    ("brakes", test_autolink_has_hard_brakes),
    ("protected", test_autolink_never_touches_protected_markup),
    ("specific", test_autolink_requires_specific_phrases),
    ("index reuse", test_autolink_reuses_the_cached_index),
    ("local only", test_personalised_strip_is_local_only),
    ("closed jobs", test_personalised_strip_hides_closed_jobs),
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
    print("ALL v154 TESTS PASSED ✔" if not bad else f"{bad} TEST(S) FAILED ✘")
    return int(bool(bad))


if __name__ == "__main__":
    raise SystemExit(main())
