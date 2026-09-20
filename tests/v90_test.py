# -*- coding: utf-8 -*-
"""v90 tests — NOTIFICATIONS (theme 1.9.1).

Brief: bot/site ki okka STANDARD alert surface kavali — guardian/radar alerts
WP Admin lo notices ga kanipinchali, CRITICAL aithe readers ki site-wide
banner ga reach avutundi. Telegram owner alerts (notifier.py) replace kaadu —
theme-side surface add (v91 Telegram tools tho bridge: --tg-alert).

Checks (offline source audits + bot imports):
  * inc/notify.php: ABSPATH guard + no raw echo (XSS gate)
  * queue API: push/all/clear + severities whitelist + dedupe + cap 20
  * option storage `studentup_notify_queue` + banner option field
  * admin notices (per-user dismiss meta + AJAX nonce endpoint)
  * REST studentup/v1/notify — GET/POST/DELETE manage_options only
  * public banner: header call-site + critical-only gate + CSS + JS dismiss
  * php-lint parse + theme zip lo notify.php undi
  * changelog "= 1.9.1" + functions.php require

Run: python tests/v90_test.py   (also via python run.py --test-all)
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

THEME = ROOT / "wordpress-theme" / "studentup"


def read(rel: Path | str) -> str:
    return Path(rel).read_text(encoding="utf-8")


def test_notify_file_safety() -> None:
    f = THEME / "inc" / "notify.php"
    assert f.exists(), "inc/notify.php ledu"
    text = read(f)
    assert "if ( ! defined( 'ABSPATH' ) )" in text, "ABSPATH guard ledu"
    assert not re.search(r"<\?php\s+echo\s+\$", text), "escape cheyyani echo $ undi"
    # messages render time esc_html — push time tags strip
    assert "wp_strip_all_tags" in text, "message sanitize ledu"
    assert "esc_html( $item['message'] )" in text, "public render escape ledu"


def test_queue_api() -> None:
    text = read(THEME / "inc" / "notify.php")
    for fn in ("function studentup_notify_all", "function studentup_notify_push",
               "function studentup_notify_clear", "function studentup_notify_severities"):
        assert fn in text, fn + " ledu"
    # severities whitelist — info/warn/critical matrame
    for sev in ("'info'", "'warn'", "'critical'"):
        assert sev in text, sev + " severity ledu"
    assert "$severity = 'info'" in text, "whitelist miss fallback ledu"
    # code-wise dedupe + FIFO cap
    assert "$item['code'] !== $code" in text, "dedupe logic ledu"
    assert "STUDENTUP_NOTIFY_MAX" in text and "20" in text, "queue cap ledu"
    assert "sanitize_key" in text, "code sanitize ledu"


def test_option_storage() -> None:
    text = read(THEME / "inc" / "notify.php")
    assert "studentup_notify_queue" in text, "queue option name ledu"
    opts = read(THEME / "inc" / "options.php")
    assert "notify_banner" in opts, "banner option field ledu (options.php)"
    assert "'1'" in opts.split("'notify_banner'")[1][:80], "banner default ON kaadu"


def test_admin_surface() -> None:
    text = read(THEME / "inc" / "notify.php")
    assert "add_action( 'admin_notices', 'studentup_notify_admin_notices' )" in text
    assert "add_action( 'wp_ajax_su_notify_dismiss', 'studentup_notify_ajax_dismiss' )" in text
    # per-user dismiss — user meta, global option kaadu
    assert "studentup_notify_dismissed" in text and "update_user_meta" in text
    assert "check_ajax_referer( 'su_notify_dismiss'" in text, "AJAX nonce ledu"
    assert "current_user_can( 'manage_options' )" in text, "admin gate ledu"


def test_rest_route() -> None:
    text = read(THEME / "inc" / "notify.php")
    assert "register_rest_route(" in text and "'/notify'" in text
    assert "'studentup/v1'" in text, "namespace tappu"
    # GET/POST/DELETE anni permission-gated
    assert text.count("current_user_can( 'manage_options' )") >= 4, \
        "REST permissions ledu (GET/POST/DELETE + admin notices)"
    assert "'methods'             => 'DELETE'" in text, "clear endpoint ledu"
    assert "code+message required" in text, "POST validation ledu"


def test_public_banner() -> None:
    notify = read(THEME / "inc" / "notify.php")
    assert "function studentup_notify_public_banner" in notify
    assert "'critical' !== $item['severity']" in notify, "critical-only gate ledu"
    assert "studentup_opt( 'notify_banner', '1' )" in notify, "option gate ledu"
    header = read(THEME / "header.php")
    assert "studentup_notify_public_banner()" in header, "header call-site ledu"
    assert header.index("wp_body_open()") < header.index("studentup_notify_public_banner()"), \
        "banner wp_body_open tarvata render avvali"
    css = read(THEME / "style.css")
    assert ".su-notify" in css and ".su-notify-critical" in css and ".su-notify-close" in css
    js = read(THEME / "assets" / "js" / "studentup.js")
    assert "su-notify-close" in js and "suNotifyHidden_" in js, "JS dismiss ledu"
    assert "localStorage.setItem" in js, "localStorage persist ledu"


def test_php_lint_and_zip() -> None:
    out = subprocess.run(["node", str(ROOT / "tools" / "php_lint.js")],
                         capture_output=True, text=True, cwd=str(ROOT))
    assert out.returncode == 0, out.stdout[-300:]
    assert "files OK" in out.stdout
    with zipfile.ZipFile(ROOT / "wordpress-theme" / "studentup-theme.zip") as zf:
        names = zf.namelist()
    assert "studentup/inc/notify.php" in names, "zip lo notify.php ledu"


def test_wiring_and_changelog() -> None:
    fn = read(THEME / "functions.php")
    assert "require_once get_template_directory() . '/inc/notify.php'" in fn
    readme = read(THEME / "readme.txt")
    assert "= 1.9.1" in readme, "changelog 1.9.1 entry ledu"
    assert "notify" in readme.lower()
    # bot side: v91 tools ki bridge endpoint name match
    tools = read(ROOT / "autoblog" / "telegram_tools.py")
    assert "studentup/v1/notify" in tools, "v91 bridge endpoint mismatch"


TESTS = [
    ("notify file safety", test_notify_file_safety),
    ("queue API", test_queue_api),
    ("option storage", test_option_storage),
    ("admin surface", test_admin_surface),
    ("REST route", test_rest_route),
    ("public banner", test_public_banner),
    ("php lint + zip", test_php_lint_and_zip),
    ("wiring + changelog", test_wiring_and_changelog),
]


def main() -> None:
    os.chdir(ROOT)
    print("=" * 70)
    print("v90 NOTIFICATIONS — regression tests (theme 1.9.1)")
    print("=" * 70)
    failed = 0
    for name, fn in TESTS:
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
        raise SystemExit(1)
    print("ALL v90 NOTIFICATION TESTS PASSED ✔")


if __name__ == "__main__":
    main()
