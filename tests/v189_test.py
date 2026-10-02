# -*- coding: utf-8 -*-
"""v189 — DAILY MORNING SEND tests (offline).

User ask: "daily mrng pampinchali okaynaa" — roju udayam list automatic ga
Telegram + WhatsApp ki vellali (owner group/status ki forward cheyyadaniki ready).

Cover:
  1. wa_to_html: WhatsApp `*bold*` → Telegram `<b>` · links clickable · injection safe
  2. wa_clickto: wa.me click-to-forward link (truncated, encoded)
  3. send_morning_list: chunking (Telegram ≤3800, WhatsApp ≤820) + channel reporting
  4. run_morning rc paths: WP fail 2 · empty list 1 · ok 0 (+file saved) ·
     no-channels warning 0 · channels anni fail 3
  5. cron + docs wiring (morning line, README/MANUAL/GO_LIVE)
"""
from __future__ import annotations

import sys
import tempfile
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from autoblog import config, forward_list as fl, notifier as nt  # noqa: E402

TODAY = date(2026, 10, 2)

WA_TEXT = """📋 *StudentUp — నేటి ఉద్యోగాల లిస్ట్*
🗓 శుక్రవారం, 02 అక్టోబర్ 2026 · 🌐 https://studentup.in

🇮🇳 *కేంద్ర ప్రభుత్వ ఉద్యోగాలు* (1 ఉద్యోగం)

1) 🆕 *SSC CHSL 2026 ఉద్యోగాలు* — 2,000+ పోస్టులు
🔗 https://studentup.in/ssc-chsl-2026/
"""

ROWS = [{"id": 1, "title": "SSC CHSL 2026 Notification – Apply Online",
         "link": "https://studentup.in/ssc-chsl-2026/", "date": "2026-10-02",
         "category_slugs": ["central-jobs"], "last_date": "2026-10-20",
         "vacancies": "2000+", "salary": ""}]


def test_wa_to_html():
    html = nt.wa_to_html(WA_TEXT)
    assert "<b>StudentUp — నేటి ఉద్యోగాల లిస్ట్</b>" in html
    assert "<b>SSC CHSL 2026 ఉద్యోగాలు</b>" in html
    assert '<a href="https://studentup.in/ssc-chsl-2026/">' in html
    # injection safe: user text lo tags escape avutayi
    dirty = nt.wa_to_html('<script>alert(1)</script> & *bold* <b>no</b>')
    assert "<script>" not in dirty and "&lt;script&gt;" in dirty
    assert "&amp; <b>bold</b>" in dirty and "&lt;b&gt;no&lt;/b&gt;" in dirty
    assert nt.wa_to_html("") == ""
    print("  1. wa_to_html (bold · links · injection safe) ✔")


def test_wa_clickto():
    link = nt.wa_clickto(WA_TEXT)
    assert link.startswith("https://wa.me/?text="), link
    assert "%2A" in link, "asterisk encode avvaledu"
    long_text = "x" * 5000
    assert len(nt.wa_clickto(long_text)) <= len("https://wa.me/?text=") + 1400 * 3 + 50
    assert nt.wa_clickto("") == ""
    print("  2. wa_clickto (encoded · truncated) ✔")


def test_send_morning_list_chunks():
    sent = {"tg": [], "wa": []}
    old = (nt.send_telegram, nt.send_whatsapp,
           config.TELEGRAM_BOT_TOKEN, config.WHATSAPP_CALLMEBOT_URL)
    try:
        nt.send_telegram = lambda text, **kw: sent["tg"].append(text) or True
        nt.send_whatsapp = lambda text: sent["wa"].append(text) or True
        config.TELEGRAM_BOT_TOKEN = "test-token"
        config.WHATSAPP_CALLMEBOT_URL = "https://api.callmebot.com/whatsapp.php?phone=+91&apikey=x"
        res = nt.send_morning_list(WA_TEXT)
        assert res == {"telegram": True, "whatsapp": True, "channels": 2}, res
        assert len(sent["tg"]) == 1 and len(sent["wa"]) == 1
        assert all(len(t) <= 3800 for t in sent["tg"])
        assert all(len(t) <= 830 for t in sent["wa"])
        assert "<b>SSC CHSL 2026 ఉద్యోగాలు</b>" in sent["tg"][0], "Telegram HTML ledu"
        assert "*SSC CHSL" not in sent["tg"][0], "WhatsApp asterisks Telegram ki poyayi"
        # peddha list chunking
        big = "\n".join(f"{i}) *Post {i}* — ఉద్యోగాలు\n🔗 https://studentup.in/p-{i}/"
                        for i in range(60))
        sent["tg"].clear(); sent["wa"].clear()
        nt.send_morning_list(big)
        assert len(sent["tg"]) >= 2 and all(len(t) <= 3800 for t in sent["tg"])
        assert len(sent["wa"]) >= 4 and all(len(t) <= 830 for t in sent["wa"])
        # channels ledu → emi send cheyyadu
        config.TELEGRAM_BOT_TOKEN = ""
        config.WHATSAPP_CALLMEBOT_URL = ""
        sent["tg"].clear(); sent["wa"].clear()
        assert nt.send_morning_list(WA_TEXT) == {"telegram": False, "whatsapp": False,
                                                "channels": 0}
        assert sent["tg"] == [] and sent["wa"] == []
    finally:
        (nt.send_telegram, nt.send_whatsapp,
         config.TELEGRAM_BOT_TOKEN, config.WHATSAPP_CALLMEBOT_URL) = old
    print("  3. send_morning_list (chunking · channel report) ✔")


def test_run_morning_paths():
    real_gather = fl.gather
    old_cfg = (config.FORWARD_LIST_PATH, config.FORWARD_LIST_STATE_PATH,
               config.TELEGRAM_BOT_TOKEN, config.WHATSAPP_CALLMEBOT_URL,
               nt.send_morning_list)
    try:
        with tempfile.TemporaryDirectory() as tmp:
            config.FORWARD_LIST_PATH = Path(tmp) / "forward-list.txt"
            config.FORWARD_LIST_STATE_PATH = Path(tmp) / "state.json"
            config.TELEGRAM_BOT_TOKEN = ""        # channels ledu → warning 0
            config.WHATSAPP_CALLMEBOT_URL = ""

            def boom(**kw):
                raise RuntimeError("WP offline (test)")
            fl.gather = boom
            assert fl.run_morning(today=TODAY) == 2, "WP fail ki rc 2 ravali"

            fl.gather = lambda **kw: []
            assert fl.run_morning(today=TODAY) == 1, "empty list ki rc 1"

            fl.gather = lambda **kw: ROWS
            assert fl.run_morning(today=TODAY) == 0
            saved = config.FORWARD_LIST_PATH.read_text(encoding="utf-8")
            assert "SSC CHSL 2026 ఉద్యోగాలు" in saved and "🔗 https://studentup.in/" in saved

            # channels configure ayyi anni fail → rc 3 (honest failure)
            config.TELEGRAM_BOT_TOKEN = "tok"
            config.WHATSAPP_CALLMEBOT_URL = "https://x/?phone=1&apikey=1"
            nt.send_morning_list = lambda *a, **k: {"telegram": False, "whatsapp": False,
                                                    "channels": 2}
            assert fl.run_morning(today=TODAY) == 3

            # okka channel ok aithe rc 0
            nt.send_morning_list = lambda *a, **k: {"telegram": True, "whatsapp": False,
                                                    "channels": 2}
            assert fl.run_morning(today=TODAY) == 0

            # no-send mode: save mattrame
            assert fl.run_morning(today=TODAY, send=False) == 0
    finally:
        fl.gather = real_gather
        (config.FORWARD_LIST_PATH, config.FORWARD_LIST_STATE_PATH,
         config.TELEGRAM_BOT_TOKEN, config.WHATSAPP_CALLMEBOT_URL,
         nt.send_morning_list) = old_cfg
        stray = ROOT / "output" / "forward-list-state.json"
        if stray.exists():
            stray.unlink()
    print("  4. run_morning rc paths (2/1/0/3 · no-send) ✔")


def test_cron_and_docs():
    cron = (ROOT / "crontab.example").read_text(encoding="utf-8")
    # v190: morning line ippudu `--daily` (adi lopala --forward-morning run chestundi);
    # rendu okkataina 6:30 ki undali
    line = [l for l in cron.splitlines()
            if ("--forward-morning" in l or "--daily" in l)
            and "--daily-quiz" not in l and not l.strip().startswith("#")]
    assert line, "crontab lo morning line (--daily/--forward-morning) ledu"
    assert any(l.strip().startswith(("30 6", "0 7")) for l in line), \
        f"morning time ledu: {line}"
    for name in ("README.md", "MANUAL_ADVANCED_CHECKLIST.md", "MILESWEB_GO_LIVE.md"):
        doc = (ROOT / name).read_text(encoding="utf-8")
        assert "--forward-morning" in doc, f"{name} lo --forward-morning ledu"
    print("  5. cron (morning line) + docs ✔")


def main() -> None:
    print("=" * 70)
    print("  v189 — DAILY MORNING SEND (Telegram + WhatsApp + click-to-forward)")
    print("=" * 70)
    test_wa_to_html()
    test_wa_clickto()
    test_send_morning_list_chunks()
    test_run_morning_paths()
    test_cron_and_docs()
    print("-" * 70)
    print("ALL v189 MORNING SEND TESTS PASSED ✔")


if __name__ == "__main__":
    main()
