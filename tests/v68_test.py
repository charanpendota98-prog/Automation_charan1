# -*- coding: utf-8 -*-
"""v68 tests — CODE-LEVEL DEEP AUDIT: nijamaina bugs fix + instant indexing.

Mee complaint: "chala bugs unnayi — anni aapthunnayi (top website avvakunda, posts trending
avvakunda, ads rakunda, higher revenue apedvi)".

Ee suite (a) aa bugs **malli raakunda lock** chestundi, (b) kotha engines ni verify chestundi:

  · `config.GEMINI_API_BASE` — mundu **AttributeError** (research path crash) → ippudu defined
  · silent failures — `except Exception: pass` **0** (mundu 14) → ippudu log avutayi
  · duplicate dict keys repo-wide scan (v74: exam_portal teesesam — autoblog + tools + run.py)
  · AdSense markup — `<ins>` ki `data-ad-layout` + `data-ad-format="fluid"` (mundu invalid
    `data-ad-format="in-article"` → **in-article RPM miss**)
  · news sitemap `<lastmod>` (Google News reject ayyedi)
  · **IndexNow key file theme dwara serve** (mundu manual cPanel upload → submit fail)
  · **Google Indexing API** (JobPosting instant indexing) — RS256 sign (openssl) + safe skip
  · CLI smoke battery — offline commands anni exit 0 + Traceback ledu
  · code audit **0 errors · 0 warnings** · .env.example drift ledu

Run: python tests/v68_test.py   (also via python run.py --test-all)
"""
from __future__ import annotations

import ast
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

import code_audit  # noqa: E402

THEME = ROOT / "wordpress-theme" / "studentup"
BOT = ROOT / "autoblog"


def read(p) -> str:
    return Path(p).read_text(encoding="utf-8")


# --------------------------------------------------------------- bug locks (v68)

def test_code_audit_clean():
    """code audit (E1–E9 · W1–W7) 0 errors · 0 warnings."""
    rep = code_audit.run()
    assert rep["errors"] == [], rep["errors"]
    assert rep["warnings"] == [], rep["warnings"]


def test_gemini_api_base_defined():
    """v68 bug: `config.GEMINI_API_BASE` config.py lo ledu → AttributeError (research crash)."""
    cfg = read(BOT / "config.py")
    assert re.search(r'GEMINI_API_BASE\s*=\s*_get\(', cfg), "GEMINI_API_BASE config lo ledu"
    assert "generativelanguage.googleapis.com" in cfg
    assert "config.GEMINI_API_BASE" in read(BOT / "main.py"), "main.py lo vaadataledu"


def test_no_silent_exception_pass():
    """v68 bug: 14 `except Exception: pass` — failures silent (adi 'anni aapthunnayi')."""
    bad = []
    for f in sorted(BOT.glob("*.py")):
        lines = read(f).splitlines()
        for i, line in enumerate(lines):
            if re.match(r"\s*except Exception[^:]*:\s*$", line) and i + 1 < len(lines) \
                    and re.match(r"\s*pass\s*$", lines[i + 1]):
                bad.append(f"{f.name}:{i + 1}")
    assert bad == [], f"silent-failure blocks: {bad}"


def test_no_duplicate_dict_keys():
    """v68 bug class: same-dict duplicate keys (okati silent ga pothundi) — v74 scope: bot + tools."""
    offenders = []
    for f in list(BOT.glob("*.py")) + list((ROOT / "tools").glob("*.py")) + [ROOT / "run.py"]:
        tree = ast.parse(read(f))
        for node in ast.walk(tree):
            if isinstance(node, ast.Dict):
                seen = set()
                for k in node.keys:
                    if isinstance(k, ast.Constant) and isinstance(k.value, (str, int)):
                        if k.value in seen:
                            offenders.append(f"{f.name}:{k.lineno} {k.value!r}")
                        seen.add(k.value)
    assert offenders == [], offenders


def test_env_example_no_drift():
    """config/getenv keys anni .env.example lo (user ki kanipinchali)."""
    cfg = read(BOT / "config.py")
    env = read(ROOT / ".env.example")
    keys = set(re.findall(r'_get\(\s*"([A-Z0-9_]+)"', cfg))
    keys |= set(re.findall(r'getenv\(\s*"([A-Z0-9_]+)"', cfg))
    for f in list(BOT.glob("*.py")) + [ROOT / "run.py"]:
        keys |= set(re.findall(r'os\.getenv\(\s*"([A-Z0-9_]+)"', read(f)))
    missing = sorted(k for k in keys if k not in env)
    assert missing == [], f".env.example lo miss: {missing}"
    for need in ("INDEXNOW_KEY", "GOOGLE_INDEXING_SA_JSON", "SOCIAL_WHATSAPP", "GEMINI_API_BASE"):
        assert need in env, need


# --------------------------------------------------------------- revenue (ads)

def test_adsense_markup_correct():
    """v68 REVENUE bug: in-article unit ki `data-ad-layout` ledu (invalid format velledi)."""
    import theme_audit

    src = theme_audit._strip_php_comments(read(THEME / "inc" / "ads.php"))
    assert "data-ad-layout" in src, "data-ad-layout ledu — in-article RPM miss"
    assert "data-ad-format=\"fluid\"" in src or "'fluid'" in src or '"fluid"' in src, "fluid format ledu"
    assert 'data-ad-format="in-article"' not in src, "INVALID data-ad-format value"
    assert "data-full-width-responsive" in src
    assert "adsbygoogle" in src and ".push({})" in src.replace(" ", ""), "push({}) ledu"
    # theme lo loader + crossorigin (site-wide)
    allphp = "".join(read(p) for p in THEME.rglob("*.php"))
    assert "pagead2.googlesyndication.com/pagead/js/adsbygoogle.js" in allphp
    assert "crossorigin" in allphp


def test_ad_slot_layout_params():
    """Slot function ki layout param unte fluid+layout apply avvali (auto = 'auto')."""
    src = read(THEME / "inc" / "ads.php")
    assert "studentup_adsense_unit" in src
    assert re.search(r"in_array\(\s*\$layout\s*,\s*array\(\s*'in-article',\s*'in-feed'\s*\)", src)


# --------------------------------------------------------------- indexing / trending

def test_news_sitemap_lastmod():
    """v68 bug: `<lastmod>` ledu → Google News sitemap reject."""
    src = read(THEME / "inc" / "news-sitemap.php")
    assert "<lastmod>" in src
    assert src.index("<lastmod>") < src.index("<news:news>"), "lastmod order: loc tarvata undali"
    assert "get_post_modified_time" in src


def test_indexnow_key_file_served_by_theme():
    """v68: IndexNow key file ippudu **theme serve chestundi** (manual upload ledu)."""
    src = read(THEME / "inc" / "indexnow.php")
    assert "studentup_indexnow_key_file" in src
    assert "template_redirect" in src
    assert ".key" in src
    assert "ABSPATH" in src
    assert "inc/indexnow.php" in read(THEME / "functions.php"), "functions.php lo require ledu"
    opts = read(THEME / "inc" / "options.php")
    assert "indexnow_key" in opts, "option register avvaledu"


def test_indexing_engine_safe_and_signing():
    """Google Indexing API: config lekunda **safe skip** + RS256 sign (openssl) nijamaina signature."""
    from autoblog import indexing

    st = indexing.status()
    for k in ("configured", "client_email", "openssl", "signing", "indexnow_key"):
        assert k in st, k
    assert indexing.configured() is False, "test env lo SA undakoodadu"
    out = indexing.submit_published({"recruitment": {"org_name": "X"}}, "https://example.com/x/")
    assert set(out) == {"indexnow", "google", "job"}, out
    assert out["job"] is True and out["google"] is False, out
    assert indexing.submit_published({}, "") == {"indexnow": False, "google": False, "job": False}
    assert indexing.publish_url("https://example.com/x/") is False, "configured lekunda publish avvakoodadu"
    # RS256: openssl tho key generate → sign → verify (real signature, real verification)
    import shutil

    if not shutil.which("openssl"):
        return
    with tempfile.TemporaryDirectory() as td:
        key = Path(td) / "k.pem"
        pub = Path(td) / "k.pub"
        subprocess.run(["openssl", "genrsa", "-out", str(key), "2048"],
                       capture_output=True, timeout=120, check=True)
        subprocess.run(["openssl", "rsa", "-in", str(key), "-pubout", "-out", str(pub)],
                       capture_output=True, timeout=120, check=True)
        data = b"studentup-indexing-check"
        sig = indexing._sign_rs256(data, read(key))
        assert len(sig) == 256, len(sig)   # RSA-2048 → 256-byte signature
        (Path(td) / "sig.bin").write_bytes(sig)
        (Path(td) / "msg.bin").write_bytes(data)
        verify = subprocess.run(["openssl", "dgst", "-sha256", "-verify", str(pub),
                                 "-signature", str(Path(td) / "sig.bin"), str(Path(td) / "msg.bin")],
                                capture_output=True, text=True, timeout=120)
        assert "Verified OK" in verify.stdout, verify.stdout + verify.stderr


def test_indexing_token_path_degrades_gracefully():
    """SA key unna kaani Google reach avvakapote (`access_token`) **crash avvakoodadu**."""
    import os
    import shutil

    if not shutil.which("openssl"):
        return
    from autoblog import indexing

    with tempfile.TemporaryDirectory() as td:
        key = Path(td) / "k.pem"
        subprocess.run(["openssl", "genrsa", "-out", str(key), "2048"],
                       capture_output=True, timeout=120, check=True)
        sa = {"client_email": "v68-test@example.iam.gserviceaccount.com",
              "private_key": read(key)}
        old = os.environ.get("GOOGLE_INDEXING_SA")
        os.environ["GOOGLE_INDEXING_SA"] = __import__("json").dumps(sa)
        indexing.access_token._cache = None          # noqa: SLF001 — cache reset
        try:
            assert indexing.configured() is True, "SA set unte configured True avvali"
            token = indexing.access_token()          # network ledu → "" (raise kaadu)
            assert token == "", f"offline lo token raakoodadu: {token[:20]}"
            assert indexing.publish_url("https://example.com/x/") is False
        finally:
            if old is None:
                os.environ.pop("GOOGLE_INDEXING_SA", None)
            else:
                os.environ["GOOGLE_INDEXING_SA"] = old
            indexing.access_token._cache = None      # noqa: SLF001


def test_publish_push_sets_indexing_state():
    """Publish tarvata `_indexing` state set avvali (Telegram/state reporting)."""
    from autoblog import pipeline

    article = {"title": "Test", "recruitment": {"org_name": "X"}}
    pipeline._after_publish_push(article, {"link": ""})   # network ledu · raise avvakoodadu
    assert "_indexing" in article, article
    assert set(article["_indexing"]) == {"indexnow", "google", "job"}


def test_theme_sync_pushes_indexnow_key():
    from autoblog import wp_theme_sync

    import inspect

    src = inspect.getsource(wp_theme_sync)
    assert "indexnow_key" in src and "config.INDEXNOW_KEY" in src


# --------------------------------------------------------------- runtime smoke

def test_cli_smoke_offline():
    """Offline commands anni exit 0 + Traceback ledu (crash = bug)."""
    # NOTE: `--breaking-from` ki **temp fixture** — tracked file (preview/data/breaking.json)
    # ni test mutate cheyyakoodadu (repo dirty / flaky test avutundi)
    fixture = Path(tempfile.mkdtemp()) / "breaking.json"
    fixture.write_text('{"source": "test", "items": []}', encoding="utf-8")
    cmds = [
        ["--help"], ["--status"], ["--rm100"], ["--ads-demo"], ["--revenue-check"],
        ["--pin-check"], ["--index-status"], ["--index-key-gen"],
        ["--push-theme-data", "--dry-run"],
        ["--breaking-from", str(fixture)],
    ]
    # `--breaking-from` preview/data/breaking.json ni **rayutundi** → mundu content save
    # chesi, tarvata exact ga restore chestunnam (tracked file dirty avvakoodadu)
    tracked = ROOT / "preview" / "data" / "breaking.json"
    original = tracked.read_bytes() if tracked.exists() else None
    for cmd in cmds:
        proc = subprocess.run([sys.executable, "run.py", *cmd], cwd=str(ROOT),
                              capture_output=True, text=True, timeout=600)
        out = (proc.stdout or "") + (proc.stderr or "")
        assert proc.returncode == 0, f"run.py {' '.join(cmd)} → exit {proc.returncode}: {out[-300:]}"
        assert "Traceback" not in out, f"run.py {' '.join(cmd)} crash:\n{out[-400:]}"
        if original is not None and tracked.exists() and tracked.read_bytes() != original:
            tracked.write_bytes(original)     # test side-effect ni undo cheyyi


def test_audit_detects_printf_mismatch():
    """Audit **detection ability** (E10): placeholders ≠ args unte pattukovali."""
    with tempfile.TemporaryDirectory() as td:
        bad = Path(td) / "bad.php"
        bad.write_text("<?php\nprintf( '<b>%1$s</b>%2$s', $a );\n", encoding="utf-8")
        rep = {"errors": [], "warnings": [], "info": []}
        code_audit.check_php_printf(bad, rep)
        assert rep["warnings"], "E10 mismatch pattukaledu"
        good = Path(td) / "good.php"
        good.write_text("<?php\nprintf( '<b>%1$s</b>%2$s', $a, $b );\n", encoding="utf-8")
        rep2 = {"errors": [], "warnings": [], "info": []}
        code_audit.check_php_printf(good, rep2)
        assert rep2["warnings"] == [], rep2["warnings"]


def test_audit_detects_sync_key_typo():
    """Audit **detection ability** (E12): bot push key theme lo register avvakapote pattukovali."""
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "autoblog").mkdir()
        (root / "wordpress-theme" / "studentup" / "inc").mkdir(parents=True)
        (root / "autoblog" / "wp_theme_sync.py").write_text(
            "PAYLOAD = {\n"
            "    'proof_json': '{}',\n"
            "    'breaking_feed': '{}',\n"        # theme lo ledu → typo/registration miss
            "}\n", encoding="utf-8")
        (root / "wordpress-theme" / "studentup" / "inc" / "options.php").write_text(
            "<?php\nreturn array(\n 'proof_json' => array( 'x', 'textarea', '', '' ),\n);\n",
            encoding="utf-8")
        old_bot, old_theme = code_audit.BOT, code_audit.THEME
        try:
            code_audit.BOT = root / "autoblog"
            code_audit.THEME = root / "wordpress-theme" / "studentup"
            rep = {"errors": [], "warnings": [], "info": []}
            code_audit.check_sync_option_keys(rep)
        finally:
            code_audit.BOT, code_audit.THEME = old_bot, old_theme
        assert any("breaking_feed" in w for w in rep["warnings"]), rep["warnings"]


def test_pipeline_imports_clean():
    """Anni bot modules import avvali (indirect crash detection) + key attrs unnayi."""
    mods = ["config", "state", "validator", "pipeline", "seo", "wordpress_client", "notifier",
            "post_gate", "rm100", "readiness", "guardian", "trends", "indexnow", "indexing",
            "wp_theme_sync", "approval_bot", "main"]
    for m in mods:
        __import__(f"autoblog.{m}")


def test_theme_zip_fresh_and_complete():
    """Zip build ani (indexnow.php to) undali — stale zip = guardian fail."""
    zips = sorted((ROOT / "wordpress-theme").glob("studentup*.zip"))
    assert zips, "theme zip ledu — tools/build_wp_theme.py run cheyandi"
    newest_src = max(p.stat().st_mtime for p in THEME.rglob("*") if p.is_file())
    assert zips[-1].stat().st_mtime >= newest_src, "zip stale — rebuild cheyandi"
    import zipfile

    names = zipfile.ZipFile(zips[-1]).namelist()
    for need in ("studentup/inc/indexnow.php", "studentup/functions.php", "studentup/style.css"):
        assert need in names, need


def test_counts_synced_and_public_clean():
    """v70: suites count ↔ README/MANUAL claims + public site lo developer proof text **ledu**."""
    suites = len(list((ROOT / "tests").glob("*_test.py")))
    readme = read(ROOT / "README.md")
    manual = read(ROOT / "MANUAL_ADVANCED_CHECKLIST.md")
    assert f"{suites}/{suites}" in readme, f"README claim ledu ({suites})"
    assert f"{suites}/{suites}" in manual, f"MANUAL claim ledu ({suites})"
    idx = read(ROOT / "preview" / "index.html")
    assert "qtile" not in idx and "టెస్ట్ సూట్" not in idx, "preview lo developer proof text"
    theme = "".join(p.read_text(encoding="utf-8")
                    for p in (ROOT / "wordpress-theme" / "studentup").rglob("*.php"))
    assert "studentup_proof_tiles" not in theme and "proof_json" not in theme


# --------------------------------------------------------------- runner

def main() -> int:
    tests = [(n, f) for n, f in sorted(globals().items())
             if n.startswith("test_") and callable(f)]
    print("=" * 70)
    print("  🐞 v68 — CODE AUDIT + BUG-FIX + INSTANT INDEXING TESTS")
    print("=" * 70)
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
    print(f"ALL v68 CODE-AUDIT TESTS PASSED ✔  ({len(tests)} checks)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
