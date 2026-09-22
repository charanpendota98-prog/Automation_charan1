# -*- coding: utf-8 -*-
"""v75 tests — CONTACT FINAL (+91 ledu) + PUBLISH SAFETY + DUMMY PURGE.

Enduku idi:
  owner number final (9182739312) — call links/display lo +91 undakoodadu,
  kaani wa.me buttons work avvali (country code link lo mandatory).
  Theme rendu handle chestundi (normalizer helpers). Same version lo:
  mock stubs live publish block + demo ads / dead links purge.

Checks (offline only):
  * tel: links + visible text lo +91 ledu (preview · builder · theme)
  * wa.me links anni country code tho (buttons work avvali)
  * theme studentup_wa_number/studentup_call_number helpers + defaults
  * --mock ante auto dry-run (main.run + top_post_run, behavioral proof)
  * demo inventory ads inactive (fake ads live posts loki ravu)
  * house ads >= 3 · anni http · dead #exam ledu · anchors site lo unnayi
  * wp_theme_sync inactive house ads filter (dead promo leak avvadu)
  * php-lint 32/32 + theme zip fresh + normalizers zip lo
  * docs: README v75 + MANUAL PART 34 + 57/57 claims

Run: python tests/v75_test.py   (also via python run.py --test-all)
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from autoblog import ad_manager, wp_theme_sync  # noqa: E402

PREVIEW = ROOT / "preview"
THEME = ROOT / "wordpress-theme" / "studentup"
MOBILE10 = "9182739312"
MOBILE12 = "919182739312"


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


# ------------------------------------------------- 1-2. +91 purge (visible)

def test_tel_links_have_no_country_code():
    for rel in ("index.html", "pages/contact.html"):
        html = read(PREVIEW / rel)
        tels = re.findall(r'href="(tel:[^"]+)"', html)
        assert tels, f"{rel} lo tel: link ledu"
        for t in tels:
            assert t == f"tel:{MOBILE10}", f"{rel}: {t} (10-digit expect)"


def test_no_visible_plus91_phone():
    for rel in ("index.html", "pages/contact.html", "pages/advertise.html"):
        html = read(PREVIEW / rel)
        visible = re.findall(r">([^<>]*\+91[^<>]*)<", html)
        assert not visible, f"{rel}: visible +91 text {visible[:2]}"
    builder = read(ROOT / "tools" / "build_policy_pages.py")
    m = re.search(r'^PHONE\s*=\s*"([^"]+)"', builder, re.M)
    assert m and m.group(1) == MOBILE10, "builder PHONE 10-digit kaadu"
    cta = read(THEME / "inc" / "cta.php")
    assert "studentup_call_number" in cta, "cta tel: helper vadatledu"


# ------------------------------------------------- 3. wa.me must work

def test_wa_me_links_keep_country_code():
    blobs = [read(PREVIEW / "index.html"), read(PREVIEW / "pages/contact.html"),
             read(PREVIEW / "pages/advertise.html"),
             read(ROOT / "tools" / "build_policy_pages.py"),
             read(THEME / "header.php")]
    nums = []
    for b in blobs:
        nums += re.findall(r"wa\.me/(\d+)", b)
    assert nums, "wa.me link okkati ledu?!"
    assert set(nums) == {MOBILE12}, f"wa.me numbers: {set(nums)}"


# ------------------------------------------------- 4. theme normalizers

def test_theme_phone_normalizers():
    opts = read(THEME / "inc" / "options.php")
    assert "function studentup_wa_number" in opts
    assert "function studentup_call_number" in opts
    assert "'91' . $d" in opts, "wa helper 91 prefix cheyyatledu"
    assert "substr( $d, 2 )" in opts, "call helper 91 strip cheyyatledu"
    assert opts.count(f"'{MOBILE10}'") >= 3, "defaults 10-digit kaavu"
    assert f"'{MOBILE12}'" not in opts, \
        "options.php default lo 12-digit undakoodadu"


# ------------------------------------------------- 5. mock publish guards

def test_mock_publish_guards():
    main_src = read(ROOT / "autoblog" / "main.py")
    assert main_src.count("auto dry-run ON") >= 2, "run + top_post guards levu"
    with tempfile.TemporaryDirectory() as td:
        env = {"PATH": "/usr/bin:/bin", "PYTHONUNBUFFERED": "1",
               "OUTPUT_DIR": td, "STATE_PATH": f"{td}/s.db"}
        proc = subprocess.run(
            [sys.executable, "run.py", "--mock", "--force"],
            capture_output=True, text=True, timeout=180, cwd=ROOT, env=env)
        out = (proc.stdout or "") + (proc.stderr or "")
        assert proc.returncode == 0, out[-300:]
        assert "auto dry-run" in out, "mock guard trigger avvaledu"
        assert "DRY-RUN saved" in out, "mock dry-run file ledu"
        assert "Traceback" not in out


# ------------------------------------------------- 6-7. dummy purge holds

def test_demo_inventory_never_live():
    inv = json.loads(read(ROOT / "ads" / "inventory.json"))
    for ad in inv.get("ads", []):
        if ad.get("demo"):
            assert ad.get("active") is False, f"demo live: {ad.get('id')}"
    live = ad_manager.active_ads(inv)
    assert live == [], f"sponsor ads live unnayi: {live}"


def test_house_links_alive():
    house = json.loads(read(ROOT / "ads" / "house.json"))
    ids = [a["id"] for a in house["ads"]]
    assert len(ids) >= 3, ids
    assert "house-jobs" in ids and not any("exam" in i for i in ids)
    index = read(PREVIEW / "index.html")
    for a in house["ads"]:
        link = a.get("link", "")
        assert link.startswith("http"), a
        assert a.get("house") is True and a.get("active") is True
        if "#" in link:
            frag = link.split("#", 1)[1]
            assert f'id="{frag}"' in index, f"anchor #{frag} site lo ledu"


def test_theme_sync_filters_inactive():
    with tempfile.TemporaryDirectory() as td:
        ads = Path(td) / "ads"
        ads.mkdir()
        (ads / "house.json").write_text(json.dumps({"ads": [
            {"id": "h-on", "title": "On", "link": "https://studentup.in/#jobs",
             "active": True},
            {"id": "h-off", "title": "Off", "link": "https://studentup.in/#quiz",
             "active": False},
            {"id": "h-nolink", "title": "NoLink", "active": True},
        ]}), encoding="utf-8")
        payload = wp_theme_sync.build_payload(root=Path(td),
                                              include=["house_ads"])
        got = [x["id"] for x in payload["house_ads"]]
        assert got == ["h-on"], got


# ------------------------------------------------- 8. php + zip

def test_php_and_zip_fresh():
    proc = subprocess.run(["node", str(ROOT / "tools" / "php_lint.js")],
                          capture_output=True, text=True, timeout=120)
    assert "files OK" in (proc.stdout or ""), proc.stdout + proc.stderr
    import zipfile

    zpath = ROOT / "wordpress-theme" / "studentup-theme.zip"
    newest = max(p.stat().st_mtime for p in THEME.rglob("*") if p.is_file())
    assert zpath.stat().st_mtime >= newest, "zip stale — rebuild cheyandi"
    names = zipfile.ZipFile(zpath).namelist()
    assert "studentup/inc/options.php" in names
    zopts = zipfile.ZipFile(zpath).read(
        "studentup/inc/options.php").decode("utf-8")
    assert "studentup_wa_number" in zopts, "zip lo normalizers levu (stale)"


# ------------------------------------------------- 9. docs

def test_docs_v75():
    suites = len(list((ROOT / "tests").glob("*_test.py")))
    assert suites == 75, f"suites {suites} (v94 tho 74 expect)"
    readme = read(ROOT / "README.md")
    manual = read(ROOT / "MANUAL_ADVANCED_CHECKLIST.md")
    go_live = read(ROOT / "GO_LIVE_CHECKLIST.md")
    assert "### v75" in readme and "71/71" in readme
    assert "PART 34" in manual and "v75" in manual and "71/71" in manual
    assert "71/71" in go_live
    for name, txt in (("README", readme), ("MANUAL", manual),
                      ("GO_LIVE", go_live)):
        assert "164/164" in txt, f"{name} lo jsdom claim poyindi"


TESTS = [
    ("tel: links +91 lekunda (10-digit)", test_tel_links_have_no_country_code),
    ("visible +91 text ledu", test_no_visible_plus91_phone),
    ("wa.me country code tho (buttons work)", test_wa_me_links_keep_country_code),
    ("theme phone normalizers + defaults", test_theme_phone_normalizers),
    ("mock = auto dry-run (behavioral)", test_mock_publish_guards),
    ("demo ads live loki ravu", test_demo_inventory_never_live),
    ("house links alive + anchors", test_house_links_alive),
    ("theme sync inactive filter", test_theme_sync_filters_inactive),
    ("php-lint + zip fresh + normalizers", test_php_and_zip_fresh),
    ("docs: README v75 + MANUAL PART 34 + 71/71", test_docs_v75),
]


def main() -> None:
    print("=" * 70)
    print("  v75 — CONTACT FINAL (+91 ledu) + PUBLISH SAFETY + DUMMY PURGE")
    print("=" * 70)
    failed = 0
    for name, fn in TESTS:
        try:
            fn()
        except AssertionError as exc:
            failed += 1
            print(f"  {name} ✘  {exc}")
        except Exception as exc:  # noqa: BLE001
            failed += 1
            print(f"  {name} ✘  {type(exc).__name__}: {exc}")
        else:
            print(f"  {name} ✔")
    print("-" * 70)
    if failed:
        print(f"  {failed} TEST(S) FAILED ✘")
        raise SystemExit(1)
    print("ALL v75 CONTACT-FINAL + SAFETY TESTS PASSED ✔")


if __name__ == "__main__":
    main()
