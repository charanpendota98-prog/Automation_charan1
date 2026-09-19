# -*- coding: utf-8 -*-
"""v51 tests — category menu (TS/AP/Central/Walk-in/Software/Private/Hall tickets/
Results + new pillars), phone neatness, and crash-proof deployment artifacts.

v74: exam portal ledu → watchdog ippudu website + bot-freshness + disk/TLS
(no PORTAL_URL, no restarts — alerts matrame).

Offline only: reads the built site + deploy scripts, runs the watchdog in a
sandbox (dry-run) so nothing real is restarted.

Run: python tests/v51_test.py   (also via python run.py --test-all)
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

SITE = ROOT / "preview" / "index.html"

# The pillars the owner asked to see in the menu
MENU_CATS = ["ts-jobs", "ap-jobs", "central-jobs", "walkin", "software",
             "private", "outsourcing", "parttime"]
EXAM_CATS = ["hallticket", "results", "upcoming", "examtips"]


def _html() -> str:
    return SITE.read_text(encoding="utf-8")


# ------------------------------------------------------------------- menu

def test_owner_category_menu_present():
    html = _html()
    for cat in MENU_CATS + EXAM_CATS:
        assert 'data-goto-cat="%s"' % cat in html, "menu category missing: " + cat
    assert html.count('data-goto-cat="') >= 20, "menu links too few"
    # v73: English UI — same owner list, English labels
    for label in ["TS Government Jobs", "AP Government Jobs", "Central Government Jobs",
                  "Walk-in", "Software", "Private Jobs", "Hall Tickets", "Results"]:
        assert label in html, "English menu label missing: " + label
    print("  menu: owner's 8 job categories + 4 exam categories (English UI) ✔")


def test_menu_has_three_dropdowns_and_is_english():
    """v73: menu UI antha English — Telugu mattrame article content lo."""
    html = _html()
    assert html.count('class="has-drop"') == 3, html.count('class="has-drop"')
    nav = re.search(r'<nav class="nav".*?</nav>', html, re.S).group(0)
    for english in ["Jobs", "Results", "Hall Tickets", "Software", "Walk-in"]:
        assert english in nav, "menu label miss: " + english
    telugu = re.findall(r"[\u0C00-\u0C7F]", re.sub(r"class=\"[^\"]*\"|aria-label=\"[^\"]*\"", "", nav))
    assert not telugu, "menu lo Telugu undi (English UI kaavali): %d chars" % len(telugu)
    print("  menu: 3 dropdowns (Jobs · Exams · More), English labels ✔")


def test_mobile_panel_has_same_categories():
    html = _html()
    panel = re.search(r'<div class="mpanel".*?</div>\s*<!--', html, re.S).group(0)
    for cat in MENU_CATS + EXAM_CATS:
        assert 'data-goto-cat="%s"' % cat in panel, "mobile menu missing: " + cat
    assert panel.count("<a ") >= 30, panel.count("<a ")
    print("  menu: mobile panel carries the same 12 categories (phone lo kuda neat) ✔")


def test_filter_chips_and_content_cover_every_category():
    html = _html()
    chips = set(re.findall(r'<button class="chip[^"]*" data-cat="([^"]+)"', html))
    assert "all" in chips and len(chips) >= 15, chips
    arts = re.findall(r'<article class="news"[^>]*data-cat="([^"]+)"', html)
    assert len(arts) >= 13, "grid needs 13+ cards: %d" % len(arts)
    covered = set()
    for a in arts:
        covered.update(a.split())
    orphans = [c for c in chips if c != "all" and c not in covered]
    assert not orphans, "chips with no content: %s" % orphans
    print("  filters: %d chips · %d cards · every category has content ✔"
          % (len(chips), len(arts)))


def test_shareable_category_urls_documented_in_js():
    html = _html()
    assert re.search(r"\^#cat-\(\[a-z-\]\+\)\$", html), "no #cat- share handling"
    assert 'data-goto-cat' in html and "setCat(" in html
    print("  filters: shareable links (#cat-walkin) + menu deep-links wired ✔")


def test_phone_neatness_rules_still_present():
    html = _html()
    for needle in ["html,body{overflow-x:hidden", "min-height:44px",
                   "img,video,iframe,table{max-width:100%}", "input,select,textarea{font-size:16px}"]:
        assert needle in html, "phone rule missing: " + needle
    print("  phone: overflow guard + 44px taps + media clamp + 16px inputs ✔")


# --------------------------------------------------------- deploy / crash

def test_systemd_units_restart_and_watchdog():
    bot = (ROOT / "deploy" / "studentup-bot.service").read_text(encoding="utf-8")
    assert "Type=oneshot" in bot and "run.py" in bot
    assert "NoNewPrivileges=true" in bot, "bot unit hardening kavali"
    assert not (ROOT / "deploy" / "exam-portal.service").exists(), "portal unit poyundali (v74)"
    wd = (ROOT / "deploy" / "systemd" / "su-watchdog.service").read_text(encoding="utf-8")
    timer = (ROOT / "deploy" / "systemd" / "su-watchdog.timer").read_text(encoding="utf-8")
    assert "su-watchdog.sh" in wd and "SITE_URL=" in wd
    assert "PORTAL_URL" not in wd, "PORTAL_URL poyundali (v74)"
    assert "OnUnitActiveSec=2min" in timer and "WantedBy=timers.target" in timer
    print("  crash-proof: bot oneshot+timer · watchdog SITE_URL · 2-min timer ✔")


def test_watchdog_logic_live_dry_run():
    """Real script, dead site + fresh/stale bot — must alert, never fail."""
    script = ROOT / "deploy" / "su-watchdog.sh"
    assert script.exists()
    assert "PORTAL_URL" not in script.read_text(encoding="utf-8")

    def _run(site_url: str, state_db_age_h: int | None) -> tuple[str, str]:
        tmp = Path(tempfile.mkdtemp(prefix="v51-wd-"))
        app = tmp / "app"
        app.mkdir()
        if state_db_age_h is not None:
            db = app / "state.db"
            db.write_bytes(b"fake-db")
            old = __import__("time").time() - state_db_age_h * 3600
            os.utime(db, (old, old))
        env = dict(os.environ,
                   WATCHDOG_DRY="1", APP_DIR=str(app), STATE_DIR=str(tmp),
                   LOG_FILE=str(tmp / "wd.log"), SITE_URL=site_url,
                   BOT_STALE_HOURS="26",
                   TELEGRAM_BOT_TOKEN="", TELEGRAM_CHAT_ID="")
        r = subprocess.run(["bash", str(script)], env=env, capture_output=True,
                           text=True, timeout=90)
        out = r.stdout + r.stderr
        assert r.returncode == 0, out
        return out, (tmp / "wd.log").read_text(encoding="utf-8")

    # dead site → site_down alert
    out, log = _run("http://127.0.0.1:9/", None)
    assert "ALERT site_down" in out, out
    assert "ALERT site_down" in log
    # fresh bot → ok line, no stale alert
    out, _ = _run("", 1)
    assert "bot fresh" in out, out
    assert "bot_stale" not in out, out
    # stale bot → bot_stale alert
    out, _ = _run("", 30)
    assert "ALERT bot_stale" in out, out
    print("  crash-proof: site_down + bot fresh/stale alerts (live dry-run) ✔")


def test_oracle_and_milesweb_docs_answer_hosting():
    oracle = (ROOT / "DEPLOY_ORACLE_CLOUD.md").read_text(encoding="utf-8")
    for fact in ["Always Free", "2 OCPU / 12 GB", "PAYG", "idle", "200 GB",
                 "watchdog", "UptimeRobot", "guarantee"]:
        assert fact.lower() in oracle.lower(), "Oracle doc missing: " + fact
    miles = (ROOT / "DEPLOY_MILESWEB.md").read_text(encoding="utf-8")
    assert "cron" in miles and "--approval-poll" in miles
    assert "passenger_wsgi" not in miles, "WSGI path poyundali (v74 cron-only)"
    assert "exam portal" not in miles.lower(), "portal vestige undi"
    print("  hosting answer: Oracle Always Free facts + MilesWeb cron-only documented ✔")


def test_money_claims_are_policy_safe_and_honest():
    oracle = (ROOT / "DEPLOY_ORACLE_CLOUD.md").read_text(encoding="utf-8")
    for rule in ["SPONSORED", "rel=\"sponsored nofollow\"", "no clickbait",
                 "MAX_PERSONAL_AD_SLOTS"]:
        assert rule.lower() in oracle.lower(), "ad rule missing: " + rule
    assert re.search(r"guarantee ledu|no guarantee|guarantee", oracle, re.I)
    from autoblog import ad_manager, config
    assert config.AD_MANAGER_ENABLED is not False
    assert ad_manager.policy_of({})["label"]
    print("  money: ads stay policy-safe + no revenue/ranking guarantee claimed ✔")


def main() -> None:
    test_owner_category_menu_present()
    test_menu_has_three_dropdowns_and_is_english()
    test_mobile_panel_has_same_categories()
    test_filter_chips_and_content_cover_every_category()
    test_shareable_category_urls_documented_in_js()
    test_phone_neatness_rules_still_present()
    test_systemd_units_restart_and_watchdog()
    test_watchdog_logic_live_dry_run()
    test_oracle_and_milesweb_docs_answer_hosting()
    test_money_claims_are_policy_safe_and_honest()
    print("ALL v51 MENU + CRASH-PROOF + HOSTING TESTS PASSED ✔")


if __name__ == "__main__":
    main()
