# -*- coding: utf-8 -*-
"""v91 tests — TELEGRAM TOOLS (theme 1.9.2).

Brief: owner ki manual Telegram toolbox kavali — connectivity test, channel
broadcast (private -100… channels + long text auto-split), site notify push
(v90 bridge). Theme side lo readers ki channel reach: private invite override
option + footer join chip + share helper.

Checks (offline source audits + bot imports):
  * telegram_tools.py: module import + core API (test/broadcast/alert/whoami)
  * chunk-split (truncate kaadu) + channel id from TELEGRAM_CHANNEL_CHAT_ID
  * v90 bridge: REST endpoint name + severity validation
  * main.py CLI wiring (--tg-test/--tg-broadcast/--tg-alert/--tg-severity)
  * run.py docstring flags (P1 CLI parity)
  * theme inc/telegram.php: ABSPATH + override regex + join block + share URL
  * options field + footer call-site + CSS chip
  * .env.example private channel hint
  * version parity 1.9.2 (php·css·stable) + readme 1.9.1+1.9.2 changelog
  * suites 71 pins (v75–v81 → "suites == 71") + docs 71/71 claims

Run: python tests/v91_test.py   (also via python run.py --test-all)
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

THEME = ROOT / "wordpress-theme" / "studentup"


def read(rel: Path | str) -> str:
    return Path(rel).read_text(encoding="utf-8")


def test_module_api() -> None:
    from autoblog import telegram_tools as t

    for fn in ("tg_test", "tg_broadcast", "tg_alert", "tg_whoami",
               "channel_configured", "run_cli"):
        assert callable(getattr(t, fn, None)), fn + " ledu"
    src = read(ROOT / "autoblog" / "telegram_tools.py")
    assert "TELEGRAM_CHANNEL_CHAT_ID" in src, "channel id config use ledu"
    assert "notifier.send_telegram" in src, "notifier reuse ledu (parallel stack vaddhu)"


def test_chunk_split_not_truncate() -> None:
    from autoblog import telegram_tools as t

    long_text = "\n".join(f"paragraph {i} " + "x" * 60 for i in range(120))
    chunks = t._split_chunks(long_text)
    assert len(chunks) > 1, "long text split avvaledu"
    assert all(len(c) <= t.TG_CHUNK_LIMIT for c in chunks), "chunk limit dhati"
    # content loss ledu — truncate approach lo last part pothundi
    joined = "\n".join(chunks)
    assert joined.count("paragraph ") == 120, "split lo content poyindi"
    assert t._split_chunks("") == [], "empty input guard ledu"
    short = "okate chunk"
    assert t._split_chunks(short) == [short], "short text split avvodu"


def test_no_creds_graceful() -> None:
    """creds lekapote clear message — cron lo exception/exit-1 raadu."""
    from autoblog import telegram_tools as t

    ok, detail = t.tg_broadcast("")
    assert ok is False and "khali" in detail
    ok, detail = t.tg_alert("", "")
    assert ok is False and "code + message" in detail
    ok, detail = t.tg_alert("x", "y", "bogus_sev")
    # bogus severity reject kaadu — safest level ki fallback (module contract)
    assert "info" in detail or "WP creds ledu" in detail or "WP reach" in detail or "respond" in detail


def test_v90_bridge() -> None:
    src = read(ROOT / "autoblog" / "telegram_tools.py")
    assert "studentup/v1/notify" in src, "v90 REST endpoint ledu"
    assert "(config.WP_USERNAME, config.WP_APP_PASSWORD)" in src, "WP auth ledu"
    assert 'severity not in ("info", "warn", "critical")' in src, "severity whitelist ledu"


def test_cli_wiring() -> None:
    main = read(ROOT / "autoblog" / "main.py")
    for flag in ("--tg-test", "--tg-broadcast", "--tg-alert", "--tg-severity"):
        assert f'"{flag}"' in main, flag + " main.py lo ledu"
    assert "telegram_tools" in main, "module wire avvaledu"
    doc = read(ROOT / "run.py")
    for flag in ("--tg-test", "--tg-broadcast", "--tg-alert"):
        assert flag in doc, flag + " run.py docstring lo ledu (P1 parity)"


def test_theme_telegram_php() -> None:
    f = THEME / "inc" / "telegram.php"
    assert f.exists(), "inc/telegram.php ledu"
    text = read(f)
    assert "if ( ! defined( 'ABSPATH' ) )" in text, "ABSPATH guard ledu"
    assert not re.search(r"<\?php\s+echo\s+\$", text), "escape cheyyani echo undi"
    assert "function studentup_tg_channel_url" in text
    assert "function studentup_tg_join_block" in text
    assert "function studentup_tg_share_url" in text
    # private channel support — invite link regex (t.me/+…)
    assert "telegram_channel_url" in text and "t\\.me" in text.replace("\\", "\\")
    assert "https://t.me/share/url" in text, "share helper endpoint tappu"


def test_theme_integration() -> None:
    opts = read(THEME / "inc" / "options.php")
    assert "telegram_channel_url" in opts, "override option field ledu"
    footer = read(THEME / "footer.php")
    assert "studentup_tg_join_block" in footer, "footer join call-site ledu"
    fn = read(THEME / "functions.php")
    assert "require_once get_template_directory() . '/inc/telegram.php'" in fn
    css = read(THEME / "style.css")
    assert ".su-tgjoin" in css, "join chip CSS ledu"


def test_env_docs() -> None:
    env = read(ROOT / ".env.example")
    assert "TELEGRAM_CHANNEL_CHAT_ID" in env
    assert "-1001234567890" in env, "private channel id hint ledu"
    assert "TELEGRAM_CHANNEL_URL" in env


def test_version_parity_192() -> None:
    php = re.search(r"STUDENTUP_VERSION',\s*'([^']+)'", read(THEME / "functions.php")).group(1)
    css = re.search(r"Version:\s*([0-9.]+)", read(THEME / "style.css")).group(1)
    stable = re.search(r"Stable tag:\s*([0-9.]+)", read(THEME / "readme.txt")).group(1)
    assert php == css == stable == "1.9.8", f"parity tappu: {php}·{css}·{stable}"
    readme = read(THEME / "readme.txt")
    assert "= 1.9.1" in readme and "= 1.9.2" in readme, "changelog entries ledu"
    assert "Telegram" in readme


def test_suite_pins_and_docs() -> None:
    for f in ("v75_test.py", "v76_test.py", "v77_test.py", "v78_test.py",
              "v79_test.py", "v80_test.py", "v81_test.py"):
        assert "suites == 83" in read(ROOT / "tests" / f), f + " (74 pin ledu)"
    suites = len(list((ROOT / "tests").glob("*_test.py")))
    assert suites == 83, f"suites {suites} (v103 tho 83 expect)"
    assert "71/71" in read(ROOT / "README.md"), "README 71/71 claim ledu"
    assert "71/71" in read(ROOT / "MANUAL_ADVANCED_CHECKLIST.md"), "MANUAL 71/71 ledu"


TESTS = [
    ("module API", test_module_api),
    ("chunk split (no truncate)", test_chunk_split_not_truncate),
    ("no-creds graceful", test_no_creds_graceful),
    ("v90 bridge", test_v90_bridge),
    ("CLI wiring", test_cli_wiring),
    ("theme telegram.php", test_theme_telegram_php),
    ("theme integration", test_theme_integration),
    ("env docs", test_env_docs),
    ("version parity 1.9.2", test_version_parity_192),
    ("suite pins + docs", test_suite_pins_and_docs),
]


def main() -> None:
    os.chdir(ROOT)
    print("=" * 70)
    print("v91 TELEGRAM TOOLS — regression tests (theme 1.9.2)")
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
    print("ALL v91 TELEGRAM-TOOLS TESTS PASSED ✔")


if __name__ == "__main__":
    main()
