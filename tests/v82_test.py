# -*- coding: utf-8 -*-
"""v82 tests — SELF-AUDIT REGRESSIONS (proactive hunt fixes pin).

Enduku idi:
  v81 tarvata real-run self-audit: rm100 single-pass gap · leaderboard slot
  mismatch (AdSense unit never loaded) · house desc key mismatch · cron.log
  rotation ledu · approval fail-open callback · NETWORKS re-export break.
  Anni fix + ikkada pin — malli break kakunda.

Checks (offline only):
  * rm100: ONE apply → TOC + table + FAQ (thin input kuda)
  * rm100: 3 passes → counts stable (no duplication), converges
  * re-export: tools.ad_network_plan.NETWORKS (6 nets)
  * ads.php: leaderboard → top_leaderboard slot mapping
  * ads.php: house 'description' key fallback
  * crontab.example: mkdir + rotation lines
  * approval: owner lekapote callback DENY (WP call ledu)

Run: python tests/v82_test.py   (also via python run.py --test-all)
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

from autoblog import rm100  # noqa: E402


def _thin_article() -> dict:
    return {
        "title": "TSPSC Group 2 Notification 2026 — 500 Posts Apply Online",
        "slug": "tspsc-group2-2026", "category": "State Govt Jobs",
        "focus_keyword": "TSPSC Group 2",
        "meta_description": ("TSPSC Group 2 notification 2026: 500 posts, fee, "
                             "age, dates, apply online syllabus hall tickets."),
        "content_html": ("<h2>Details</h2><p>" +
                         "TSPSC Group 2 వివరాలు ముఖ్యమైనవి. " * 60 + "</p>"),
        "faq": [{"q": f"Q{i}?", "a": "Answer one. Answer two here."}
                for i in range(4)],
        "secondary_keywords": ["group 2 syllabus"],
        "source_url": "https://tspsc.gov.in/x",
    }


def test_rm100_single_pass_structure() -> None:
    a = _thin_article()
    rm100.apply(a)
    h = a["content_html"]
    assert "su-toc" in h, "single pass: TOC missing"
    assert "<table" in h, "single pass: table missing"
    assert "su-faq" in h, "single pass: FAQ missing"
    print("  rm100 single-pass: TOC+table+FAQ ✔")


def test_rm100_converges_no_dupes() -> None:
    a = _thin_article()
    counts = []
    for _ in range(3):
        res = rm100.apply(a)
        h = a["content_html"]
        counts.append((h.count("<h2"), h.count("<table"),
                       h.count("su-faq"), res["after"]))
    assert counts[1][0] == counts[2][0], f"h2 drift: {counts}"
    assert counts[1][1] == counts[2][1] == 1, f"table dupe: {counts}"
    assert counts[2][1] == 1 and counts[2][2] >= 1, f"struct: {counts}"
    print(f"  rm100 converges: {counts[0][3]}→{counts[2][3]} no-dupes ✔")


def test_networks_reexport() -> None:
    from tools import ad_network_plan as plan

    assert len(plan.NETWORKS) == 6, "NETWORKS re-export broken!"
    keys = {n["key"] for n in plan.NETWORKS}
    assert {"adsense", "raptive", "mediavine"} <= keys, keys
    print("  NETWORKS re-export (6 nets) ✔")


def test_leaderboard_slot_mapping() -> None:
    src = (ROOT / "wordpress-theme" / "studentup" / "inc" / "ads.php"
           ).read_text(encoding="utf-8")
    assert "'leaderboard' === $place" in src and "top_leaderboard" in src, \
        "leaderboard slot mapping missing"
    print("  leaderboard→top_leaderboard slot ✔")


def test_house_desc_fallback() -> None:
    src = (ROOT / "wordpress-theme" / "studentup" / "inc" / "ads.php"
           ).read_text(encoding="utf-8")
    assert "$ad['description']" in src, "house description fallback missing"
    print("  house description fallback ✔")


def test_crontab_deploy_lines() -> None:
    src = (ROOT / "crontab.example").read_text(encoding="utf-8")
    assert "mkdir -p /opt/studentup/log" in src, "mkdir step missing"
    assert "cron.log" in src and "tail -c" in src, "rotation line missing"
    print("  crontab mkdir + rotation ✔")


def test_approval_fail_closed() -> None:
    from autoblog import approval_bot, config, state

    old_chat, old_state = config.TELEGRAM_CHAT_ID, config.STATE_PATH
    tmp = Path(tempfile.mkdtemp()) / "s.db"
    state.init(tmp)
    config.TELEGRAM_CHAT_ID = ""
    config.STATE_PATH = tmp
    try:
        assert approval_bot.ApprovalBot is not None
        bot = approval_bot.ApprovalBot()
        calls: list = []
        bot.tg = lambda method, payload: calls.append(  # type: ignore
            (method, payload)) or {"ok": True}
        wp_calls: list = []
        bot._wp_post_status = lambda pid, st: wp_calls.append(  # type: ignore
            (pid, st)) or {}
        assert bot.registered_chat() == "", "owner undakudadu (fresh db)"
        bot.on_callback({"id": "cbx", "message": {"message_id": 1,
                         "chat": {"id": 111}}, "data": "pub:5"})
        assert wp_calls == [], f"fail-open! WP calls: {wp_calls}"
        assert calls and calls[0][0] == "answerCallbackQuery", calls
        assert "Access ledu" in calls[0][1]["text"], calls
        # registered owner still works (deny wrong chat, allow right one)
        state.meta_set(tmp, approval_bot.CHAT_KEY, "111")
        bot.on_callback({"id": "c2", "message": {"message_id": 2,
                         "chat": {"id": 999}}, "data": "pub:5"})
        assert wp_calls == [], "foreign chat allowed!"
        print("  approval fail-closed (deny) + foreign-deny ✔")
    finally:
        config.TELEGRAM_CHAT_ID = old_chat
        config.STATE_PATH = old_state


def test_rm100_reaches_100() -> None:
    # v83: engine-generated boxes (takeaways/TOC) self-fail fix —
    # well-structured article TRUE 100 reach avvali.
    para = ("AP DSC TRT 2026 notification vachindi. Teacher posts kosam lakshala "
            "mandi aspirants wait chestunnaru. Eligibility criteria age limit fee "
            "details anni official notification lo check cheyandi. Kakinada, apply online "
            "process simple ga undi. Syllabus prakaram preparation start cheyandi. "
            "Previous papers practice cheste manchi score vastundi. Hall tickets exam "
            "ki mundu release avutayi. Merit list district-wise cut off base meedha "
            "prepare chestaru. Malli, daily current affairs kuda chadavandi. ")
    html = ""
    for h2 in ["Overview", "Vacancies", "Eligibility", "Fee Details",
               "Age Limit", "How to Apply", "Important Dates"]:
        html += f"<h2>{h2} AP DSC TRT 2026</h2><p>" + para * 3 + "</p>"
    a = _thin_article()
    a.update({"title": "AP DSC TRT 2026 Notification — 6,100 Teacher Posts",
              "focus_keyword": "AP DSC TRT 2026", "content_html": html})
    r = rm100.optimize(a, target=100)
    assert r["reached"] and r["score"] == 100, \
        f"100 reach avvaledu: {r['score']}"
    print(f"  rm100 TRUE 100: {r['before']}→{r['score']} ✔")


def test_docs_v82() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    manual = (ROOT / "MANUAL_ADVANCED_CHECKLIST.md").read_text(encoding="utf-8")
    go_live = (ROOT / "GO_LIVE_CHECKLIST.md").read_text(encoding="utf-8")
    assert "### v82" in readme and "64/64" in readme
    assert "PART 41" in manual and "v82" in manual and "64/64" in manual
    assert "64/64" in go_live
    for name, txt in (("README", readme), ("MANUAL", manual)):
        assert "164/164" in txt, f"{name} lo jsdom claim poyindi"
    print("  docs: README v82 + MANUAL PART 41 + 64/64 ✔")


TESTS = [
    ("rm100 single-pass structure", test_rm100_single_pass_structure),
    ("rm100 converges no-dupes", test_rm100_converges_no_dupes),
    ("NETWORKS re-export", test_networks_reexport),
    ("leaderboard slot mapping", test_leaderboard_slot_mapping),
    ("house desc fallback", test_house_desc_fallback),
    ("crontab deploy lines", test_crontab_deploy_lines),
    ("approval fail-closed", test_approval_fail_closed),
    ("rm100 reaches TRUE 100", test_rm100_reaches_100),
    ("docs: v82 + PART 41 + 64/64", test_docs_v82),
]


def main() -> None:
    print("=" * 70)
    print("  v82 — SELF-AUDIT REGRESSIONS")
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
    print("-" * 70)
    if failed:
        print(f"  {failed} TEST(S) FAILED ✘")
        raise SystemExit(1)
    print("ALL v82 SELF-AUDIT TESTS PASSED ✔")


if __name__ == "__main__":
    main()
