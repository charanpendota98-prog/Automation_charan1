# -*- coding: utf-8 -*-
"""v197 — ENGAGE + MENU + DAILY BOT pack (owner ask, 2026-10-03).

Owner screenshot bug + ask: "fix cheyu anni perfectgaa quiz polls daily
advancedga bot tho draft chesi post chesthu vundali anni perfectga advanced
menu build cheyu".

Ee suite aa naalugu ni permanent gate ga marchindi:

  C1  bug fix   — theme toggle `textContent = '<svg…>'` (raw markup text ga
                  kanipinchina bug) malli raakoodadu: preview files lo
                  textContent ki SVG eppudu assign avvakudadu.
  C2  mega menu — theme: inc/megamenu.php (cleaned, 404-free), header.php
                  mobile accordion, style/worldclass CSS, menu JS (keyboard +
                  aria + touch), functions.php wiring + option toggle.
  C3  preview menu parity — preview pages + home lo **same** mega markup
                  (classes/attrs identical) → pin-to-pin.
  C4  quiz      — server-rendered (no-JS path), Quiz schema, streak/share,
                  front-page + template wiring, real page in firstrun, page
                  works without JS (form POST + nonce).
  C5  polls     — REST route, admin-post (no-JS), one-vote dedupe (hashed
                  voter, never raw IP), counts autoload OFF, no personal data,
                  renderer + shortcode wiring, option fields.
  C6  daily bot — auto-publish lane gates (source + words + Rank Math + fresh
                  + hygiene) + config knobs + CLI flags + daily flow steps.
  C7  daily engage — quiz + poll push module, weekly poll bank, idempotent.
  C9  deploy verify
  C8  preview assets — daily-quiz page exists (English, SPONSORED, no Telugu),
                  sprite generated from theme icons (no blank boxes), offline
                  bundle has the new tab + no dead .html links.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
THEME = ROOT / "wordpress-theme" / "studentup"
PREVIEW = ROOT / "preview"
TE = re.compile(r"[\u0C00-\u0C7F]")


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="ignore")


# ------------------------------------------------------------------ C1 bug fix
def test_c1_no_raw_svg_in_textcontent() -> None:
    """Screenshot bug: `<svg>` string ni textContent ki ivvadam (raw markup text)."""
    bad = re.compile(r"textContent\s*=\s*[^\n;]*<svg")
    offenders = []
    for p in list(PREVIEW.rglob("*.html")) + list(THEME.rglob("*.js")) + list(THEME.rglob("*.php")):
        text = read(p)
        for m in bad.finditer(text):
            offenders.append(f"{p.relative_to(ROOT)}:{text[:m.start()].count(chr(10)) + 1}")
    assert not offenders, "raw SVG textContent ki assign avutundi: " + ", ".join(offenders)

    # toggle nijamga innerHTML vaadutundi (fix in the shipped demo + standalone)
    for rel in ("preview/worldclass/index.html", "preview/worldclass/standalone.html"):
        s = read(ROOT / rel)
        assert "btn.innerHTML = b.classList.contains('dark')" in s, rel + ": fix poyindi"
    # theme side eppudu correct ga unde
    js = read(THEME / "assets" / "js" / "studentup.js")
    assert "themeBtn.innerHTML = dark ? SUN : MOON;" in js, "theme toggle innerHTML ledu"
    print("  C1. theme toggle: raw SVG text ga kanipinchadu (innerHTML) + regression gate ✔")


# ----------------------------------------------------------------- mega menu
def test_c2_mega_menu_theme() -> None:
    """Theme mega menu: data module · cleaned · renderer · mobile accordion."""
    mega = THEME / "inc" / "megamenu.php"
    assert mega.exists(), "inc/megamenu.php ledu"
    s = read(mega)
    assert re.search(r"defined\(\s*'ABSPATH'\s*\)", s), "ABSPATH guard ledu"
    assert "function studentup_mega_groups(" in s, "groups ledu"
    assert "function studentup_mega_ready(" in s, "clean/ready ledu"
    assert "function studentup_mega_render(" in s, "renderer ledu"
    assert "function studentup_mega_mobile_accordion(" in s, "mobile accordion ledu"
    # 404-free rule: prathi item real term/page/anchor nunchi vastundi
    assert "get_page_by_path(" in s and "'publish' === get_post_status(" in s, "page existence check ledu"
    assert "studentup_used_term(" in s, "alias-aware term resolver ledu"
    assert "apply_filters( 'studentup_mega_groups'" in s, "filter ledu"
    # 5 groups: Jobs · Exams · Scholarships · Tools · More
    for label in ("'label'   => 'Jobs'", "'label'   => 'Exams'", "'label'   => 'Scholarships'",
                  "'label'   => 'Tools'", "'label'   => 'More'"):
        assert label in s or label.replace("   ", " ") in s, f"group ledu: {label}"
    # renderer v93 contract ni kaapadali (CSS + audits depend on it)
    assert '<ul class="sub-menu" id="su-mega-%s"' in s, "sub-menu markup ledu"
    assert 'aria-haspopup="true" aria-expanded="false"' in s, "aria ledu"
    assert 'class="su-mega-col menu-item"' in s and 'class="su-mega-feat menu-item"' in s, "columns/feature ledu"

    # wiring: require + option toggle in the fallback
    fns = read(THEME / "functions.php")
    assert "inc/megamenu.php" in fns, "functions.php lo require ledu"
    assert "studentup-menu.js" in fns and "wp_enqueue_script" in fns, "menu JS enqueue ledu"
    tpl = read(THEME / "inc" / "template.php")
    fb = tpl[tpl.index("function studentup_menu_fallback"):]
    fb = fb[:fb.index("\nfunction ", 10)]
    assert "studentup_mega_ready()" in fb and "studentup_mega_render(" in fb, "fallback mega path ledu"
    assert "'mega_menu'" in fb, "mega_menu option toggle ledu"
    # v93 literals kaapadali (purana CSS/tests)
    assert "menu-item-has-children" in fb and 'ul class="sub-menu"' in fb, "v93 markup poyindi"

    # header.php mobile accordion + page link
    hdr = read(THEME / "header.php")
    assert "studentup_mega_mobile_accordion(" in hdr, "mobile accordion call ledu"
    assert "details class=\"mgroup\"" in read(mega), "mgroup markup ledu"
    assert "Daily Quiz &amp; Polls" in hdr, "mobile panel quiz link ledu"
    print("  C2. mega menu (theme): 5 groups · cleaned · renderer · mobile accordion · a11y ✔")


def test_c2b_menu_js_behaviour() -> None:
    """Menu JS: keyboard · aria sync · touch · accordion · no jQuery."""
    js = read(THEME / "assets" / "js" / "studentup-menu.js")
    for needle, why in (
        ('aria-expanded', "aria sync"),
        ('"ArrowDown"', "arrow keys"),
        ('"Escape"', "escape close"),
        ("focusout", "focus-out close"),
        ("matchMedia(\"(hover: none)\")", "touch device detection"),
        ("details.mgroup", "mobile accordion"),
        ("su-head-small", "sticky shrink"),
    ):
        assert needle in js, f"menu JS lo {why} ledu"
    assert "jQuery" not in js and "$(" not in js, "jQuery dependency vaddhu"
    assert "passive: true" in js, "scroll listener passive kaadu"
    print("  C2b. menu JS: keyboard · aria · touch · accordion · passive scroll ✔")


# --------------------------------------------------------- preview parity
def test_c3_preview_mega_parity() -> None:
    """Preview mega markup = theme markup (pin-to-pin classes/attrs)."""
    home = read(PREVIEW / "worldclass" / "index.html")
    for needle in ('class="menu-primary su-has-mega"', 'class="menu-item menu-item-has-children su-mega-li"',
                   'class="sub-menu" id="su-mega-', 'data-su-mega', 'class="su-mega-col menu-item"',
                   'class="su-mega-list"', 'class="su-mega-feat menu-item"', 'class="su-mega-cta"'):
        assert needle in home, f"preview home lo mega markup ledu: {needle}"
    # every preview page (policy shell) uses the same builder output
    page = read(PREVIEW / "pages" / "daily-quiz.html")
    assert 'class="menu-primary su-has-mega"' in page and 'data-su-mega' in page, "policy shell mega ledu"
    # CSS: theme stylesheet lo mega styles (preview links the SAME css file)
    css = read(THEME / "assets" / "css" / "worldclass.css")
    for rule in (".nav .sub-menu[data-su-mega]", ".nav .su-mega-feat", ".mpanel .mgroup>summary",
                 ".su-quiz-card", ".su-poll-opt", ".su-poll-bar"):
        assert rule in css, f"CSS rule ledu: {rule}"
    # preview loads the theme menu JS (no copy — single source of truth)
    assert "studentup-menu.js" in page, "preview menu JS link ledu"
    assert "studentup-menu.js" in home, "home lo menu JS link ledu"
    print("  C3. preview nav = theme mega markup + same CSS/JS (pin-to-pin) ✔")


# -------------------------------------------------------------------- quiz
def test_c4_quiz_engine() -> None:
    """Quiz: server-rendered · no-JS path · schema · streak/share · wiring."""
    s = read(THEME / "inc" / "quiz.php")
    assert re.search(r"defined\(\s*'ABSPATH'\s*\)", s), "ABSPATH guard ledu"
    # v123 dead-code bug: function ippudu nijamga render avvali
    assert "function studentup_daily_quiz(" in s, "renderer ledu"
    fp = read(THEME / "front-page.php")
    assert "studentup_daily_quiz(" in fp, "front-page lo quiz call ledu (v123 bug tirigi vachindi)"
    assert "studentup_daily_poll(" in fp, "front-page lo poll call ledu"
    # no-JS: nonce verify + server grading
    assert "wp_verify_nonce( $nonce, 'su_quiz_submit' )" in s, "quiz form nonce ledu"
    assert "wp_nonce_field( 'su_quiz_submit'" in s, "quiz nonce field ledu"
    assert "function studentup_quiz_answers_from_post(" in s, "no-JS grading ledu"
    # server-rendered questions + explanation + source
    assert 'class="su-q"' in s and "data-c=" in s and "su-why" in s, "server-rendered question markup ledu"
    assert "studentup_quiz_schema(" in s and "'@type'         => 'Quiz'" in s, "Quiz schema ledu"
    assert "suggestedAnswer" in s and "acceptedAnswer" in s, "schema answers ledu"
    # bank shape: 25+ questions, cat + src (E-E-A-T)
    bank = s[s.index("function studentup_quiz_bank("):s.index("function studentup_quiz_today(")]
    assert bank.count("'q' =>") >= 25, "question bank chinnadi"
    assert bank.count("'src' =>") >= 25, "source line ledu (E-E-A-T)"
    assert "apply_filters( 'studentup_quiz_bank'" in s, "bank filter ledu"
    # JS enhancement
    js = read(THEME / "assets" / "js" / "studentup-engage.js")
    assert "su_quiz_streak" in js and "localStorage" in js, "streak ledu"
    assert "navigator.share" in js, "native share ledu"
    assert "data-su-quiz-form" in js, "quiz JS wiring ledu"
    # page template + setup
    page = read(THEME / "page-quiz.php")
    assert re.search(r"defined\(\s*'ABSPATH'\s*\)", page), "page ABSPATH guard ledu"
    assert "studentup_daily_quiz(" in page and "studentup_daily_poll(" in page, "quiz page blocks ledu"
    firstrun = read(THEME / "inc" / "firstrun.php")
    assert "'daily-quiz'       => 'Daily Quiz & Polls'" in firstrun, "setup page ledu"
    assert "'daily-quiz'      => 'page-quiz.php'" in firstrun, "template assign ledu"
    print("  C4. quiz: server-rendered · no-JS · Quiz schema · streak/share · page ✔")


# -------------------------------------------------------------------- polls
def test_c5_polls_engine() -> None:
    """Polls: REST + no-JS · one vote · hashed voter · no personal data."""
    p = THEME / "inc" / "polls.php"
    assert p.exists(), "inc/polls.php ledu"
    s = read(p)
    assert re.search(r"defined\(\s*'ABSPATH'\s*\)", s), "ABSPATH guard ledu"
    # REST with permission_callback (audit rule)
    assert "register_rest_route(" in s and "'permission_callback' => '__return_true'" in s, "REST route/permission ledu"
    assert "'/poll'" in s, "poll route ledu"
    # no-JS form path
    assert "admin_post_nopriv_studentup_poll_vote" in s, "no-JS vote handler ledu"
    assert "wp_verify_nonce( $nonce, 'su_poll_vote' )" in s, "vote nonce verify ledu"
    assert "admin_url( 'admin-post.php' )" in s, "form action ledu"
    # privacy: hashed voter, raw IP never stored
    assert "studentup_poll_voter()" in s and "wp_hash( $raw )" in s, "hashed voter ledu"
    assert "INET_ATON" not in s and "REMOTE_ADDR" in s, "IP handling ledu"
    assert "update_option( $key, $counts, false )" in s, "counts autoload OFF kaadu"
    assert "su_poll_seen_" in s, "one-vote dedupe ledu"
    assert "set_transient( $rl, 1, 20 )" in s, "rate limit ledu"
    # honest + safe render
    assert "not a scientific survey" in s, "honesty line ledu"
    assert "studentup_poll_schema(" in s and "'aggregateVotes'" in s, "poll schema ledu"
    assert "apply_filters( 'studentup_poll_bank'" in s, "poll bank filter ledu"
    # wiring: require + options + page
    assert "inc/polls.php" in read(THEME / "functions.php"), "require ledu"
    opts = read(THEME / "inc" / "options.php")
    for key in ("'polls'", "'poll_question'", "'poll_opts'", "'poll_note'", "'poll_id'", "'mega_menu'"):
        assert key in opts, f"option field ledu: {key}"
    print("  C5. polls: REST + no-JS vote · hashed voter · rate limit · schema ✔")


# ----------------------------------------------------------------- daily bot
def test_c6_auto_publish_lane() -> None:
    """Auto-publish lane: every gate present + config + CLI + daily flow."""
    lane = ROOT / "autoblog" / "publish_lane.py"
    assert lane.exists(), "autoblog/publish_lane.py ledu"
    s = read(lane)
    assert "studentup_source_url" in s, "source-proof gate ledu"
    assert "read_rankmath_state" in s, "Rank Math readback gate ledu"
    assert "AUTO_PUBLISH_MIN_SCORE" in s and "AUTO_PUBLISH_MIN_WORDS" in s, "thresholds ledu"
    assert "AUTO_PUBLISH_MAX_AGE_DAYS" in s, "freshness gate ledu"
    assert "BAD_TEXT" in s and "placeholder" in s, "hygiene gate ledu"
    assert "set_post_status" in s and "readback" in s, "publish + readback ledu"
    assert "dry" in s, "dry-run ledu"
    # client support
    wc = read(ROOT / "autoblog" / "wordpress_client.py")
    assert "def list_drafts(" in wc, "list_drafts ledu"
    assert "def set_theme_options(" in wc, "set_theme_options ledu"
    # config knobs
    cfg = read(ROOT / "autoblog" / "config.py")
    for key in ("AUTO_PUBLISH_DAILY", "AUTO_PUBLISH_MIN_SCORE", "AUTO_PUBLISH_MIN_WORDS",
                "AUTO_PUBLISH_MAX", "AUTO_PUBLISH_MAX_AGE_DAYS", "DAILY_ENGAGE"):
        assert key in cfg, f"config knob ledu: {key}"
    # CLI + daily flow
    main = read(ROOT / "autoblog" / "main.py")
    assert '"--auto-publish"' in main and '"--auto-publish-dry"' in main, "CLI flags ledu"
    assert '"--daily-engage"' in main, "engage flag ledu"
    assert "[4/5] AUTO-PUBLISH" in main, "daily flow lo publish step ledu"
    assert "[3/5] DAILY ENGAGE" in main, "daily flow lo engage step ledu"
    assert "publish_lane.run(" in main and "engage_push.run(" in main, "handlers ledu"
    print("  C6. auto-publish lane: source + words + RankMath + fresh + hygiene + readback ✔")


def test_c7_daily_engage() -> None:
    """Daily engage: quiz push + poll push (idempotent, offline-safe)."""
    mod = ROOT / "autoblog" / "engage_push.py"
    assert mod.exists(), "autoblog/engage_push.py ledu"
    s = read(mod)
    assert "POLL_BANK" in s and s.count('("') >= 7, "poll bank ledu"
    assert "def poll_for(" in s and "def push_poll(" in s and "def push_quiz(" in s, "engage API ledu"
    assert "set_theme_options(" in s, "theme options push ledu"
    assert "daily_quiz.run(" in s, "quiz post existing module tho kaadu"
    assert "poll_id" in s, "idempotent poll id ledu"
    # offline safe: WP fail aithe daily run aagakudadu
    assert "never crash the daily run" in s or "skip" in s.lower(), "offline-safe note ledu"

    # a real run with no network must not raise (report only)
    import importlib
    import sys
    sys.path.insert(0, str(ROOT))
    mod_obj = importlib.import_module("autoblog.engage_push")
    payload = mod_obj.poll_for()
    assert payload["poll_question"] and len(payload["poll_opts"].splitlines()) >= 3, "poll payload ledu"
    assert payload["poll_id"].startswith("d"), "poll id format ledu"
    print("  C7. daily engage: quiz + poll push · idempotent · offline-safe ✔")


# --------------------------------------------------------------- preview art
def test_c8_preview_artifacts() -> None:
    """Preview: quiz page (English, SPONSORED) · sprite generated · offline tabs."""
    page = PREVIEW / "pages" / "daily-quiz.html"
    assert page.exists(), "preview/pages/daily-quiz.html ledu"
    html = read(page)
    assert '<html lang="en">' in html, "lang=en ledu"
    assert not TE.search(html), "quiz page lo Telugu undi (v73 rule)"
    assert "SPONSORED" in html, "SPONSORED label ledu"
    assert "data-su-quiz-form" in html and "data-su-poll" in html, "quiz/poll markup ledu"
    assert '<script type="application/ld+json">' in html, "schema ledu"

    # sprite generator: theme icons → preview (no blank icon boxes)
    spr = ROOT / "tools" / "build_sprite.py"
    assert spr.exists(), "tools/build_sprite.py ledu"
    for rel in ("preview/worldclass/index.html", "preview/pages/daily-quiz.html"):
        doc = read(ROOT / rel)
        sprite = re.search(r'<svg class="su-sprite"[^>]*>(.*?)</svg>', doc, re.S)
        assert sprite, rel + ": sprite ledu"
        keys = set(re.findall(r'id="su-i-([a-z0-9_-]+)"', sprite.group(1)))
        used = set(re.findall(r'href="#su-i-([a-z0-9_-]+)"', doc))
        missing = sorted(used - keys)
        assert not missing, f"{rel}: sprite lo ikkaví icons: {missing}"

    # offline single-file preview: new tab + no dead .html links
    off = read(PREVIEW / "OFFLINE_PREVIEW.html")
    assert 'data-t="quiz"' in off, "offline bundle lo quiz tab ledu"
    leftover = sorted(set(re.findall(r'href="([^"]*\.html[^"]*)"', off)))
    assert not leftover, "offline bundle lo dead .html links: " + ", ".join(leftover[:5])

    # sitemap count (18 → 19 locs: quiz page)
    sm = read(PREVIEW / "sitemap.xml")
    assert sm.count("<loc>") == 19, f"sitemap locs {sm.count('<loc>')} (19 kaavali)"
    assert "daily-quiz.html" in sm, "sitemap lo quiz page ledu"
    print("  C8. preview: quiz page · sprite complete · 20-tab offline bundle · sitemap 19 ✔")


# ------------------------------------------------------- C9 deploy verify
def test_c9_deploy_verify() -> None:
    """`run.py --verify-deploy` — live proof + exact next step (offline tests)."""
    import sys
    sys.path.insert(0, str(ROOT))
    from autoblog import deploy_verify as dv

    assert hasattr(dv, "verify") and hasattr(dv, "run_cli"), "verify API ledu"
    assert dv.THEME_MIN == "1.9.42", "theme min pin ledu"

    GOOD_HOME = """
      <html><body>
      <nav class="nav"><ul id="primary-menu" class="menu-primary su-has-mega">
        <li class="menu-item menu-item-has-children su-mega-li">
          <a href="/" aria-haspopup="true" aria-expanded="false" aria-controls="su-mega-jobs">Jobs</a>
          <ul class="sub-menu" id="su-mega-jobs" data-su-mega>
            <li class="su-mega-feat menu-item"><b>x</b></li></ul></li></ul></nav>
      <svg class="su-sprite" style="display:none"><symbol id="su-i-bank" viewBox="0 0 24 24"></symbol>
        <symbol id="su-i-check" viewBox="0 0 24 24"></symbol></svg>
      <section class="su-quiz" id="daily-quiz">
        <form data-su-quiz-form><input type="hidden" name="su_quiz_nonce" value="x">
        <fieldset class="su-q">q</fieldset><p data-su-why>why</p></form></section>
      <script type="application/ld+json">{"@type": "Quiz"}</script>
      <section class="su-poll" data-su-poll>
        <label class="su-poll-opt"></label><label class="su-poll-opt"></label>
        <label class="su-poll-opt"></label></section>
      <svg class="su-uicon"><use href="#su-i-bank"/></svg>
      </body></html>"""
    CSS = ".su-mega-col{a:1}.su-quiz-card{a:1}.su-poll-opt{a:1}"
    JS_OK = "aria-expanded su_quiz_streak"

    class Fake:
        QUIZ_PAGE = ('<html><body><section class="su-quiz" data-su-quiz-form>x</section>'
                     '<section class="su-poll" data-su-poll>x</section></body></html>')

        def __init__(self, home=GOOD_HOME, version="1.9.42", css=CSS, js=JS_OK,
                     quiz_missing=False, sitemap="<loc>https://x/daily-quiz/</loc>",
                     poll_rest='{"question":"q","options":["a"]}', raise_on=None):
            self.home, self.version, self.css, self.js = home, version, css, js
            self.quiz_page = None if quiz_missing else self.QUIZ_PAGE
            self.sitemap, self.poll_rest, self.raise_on = sitemap, poll_rest, raise_on

        def get(self, url):
            if self.raise_on and self.raise_on in url:
                raise RuntimeError("boom")
            if url.endswith("style.css"):
                return 200, "/*\nTheme Name: StudentUp\nVersion: %s\n*/" % self.version, {}
            if url.endswith("worldclass.css"):
                return 200, self.css, {}
            if url.endswith("studentup-menu.js") or url.endswith("studentup-engage.js"):
                return 200, self.js, {}
            if url.endswith("studentup.js"):
                return 200, "themeBtn.innerHTML = dark ? SUN : MOON;", {}
            if url.endswith("/daily-quiz/"):
                if self.quiz_page is None:
                    return 404, "Not found", {}
                return 200, self.quiz_page, {}
            if url.endswith("page-sitemap.xml"):
                return 200, self.sitemap, {}
            if url.endswith("/wp-json/studentup/v1/poll"):
                return 200, self.poll_rest, {}
            return 200, self.home, {}

    rep = dv.verify("https://studentup.in", fetcher=Fake())
    assert rep["counts"]["fail"] == 0, [c for c in rep["checks"] if c["status"] == "fail"]
    assert rep["verdict"] == "LIVE ✔" and rep["score"] == 100, rep["verdict"]
    assert not rep["next_steps"], rep["next_steps"]

    # zip upload pending → fail + exact instruction.
    # (Purana version ni pieces nunchi construct chestunnam — tools/pin_sync.py
    #  literal "1.9.x" strings ni current version ki rewrite chestundi.)
    pending_ver = "1." + "9." + "38"
    r2 = dv.verify("https://studentup.in", fetcher=Fake(version=pending_ver))
    v1 = [c for c in r2["checks"] if c["id"] == "V1"][0]
    assert v1["status"] == "fail" and any("Upload Theme" in s for s in r2["next_steps"]), r2["next_steps"]

    # setup not run → /daily-quiz/ 404 → fail + Run setup now
    r3 = dv.verify("https://studentup.in", fetcher=Fake(quiz_missing=True))
    v6 = [c for c in r3["checks"] if c["id"] == "V6"][0]
    assert v6["status"] == "fail" and any("Run setup now" in s for s in r3["next_steps"]), r3["next_steps"]

    # blank icon guard: sprite missing an icon the page uses
    r4 = dv.verify("https://studentup.in", fetcher=Fake(
        home=GOOD_HOME.replace('<use href="#su-i-bank"/>', '<use href="#su-i-wallet"/>')))
    v8 = [c for c in r4["checks"] if c["id"] == "V8"][0]
    assert v8["status"] == "fail" and "wallet" in v8["detail"], v8

    # offline / SSL → clean report, no traceback, exit 2
    r5 = dv.verify("https://studentup.in", fetcher=Fake(raise_on="/"))
    assert r5["verdict"] == "UNREACHABLE" and r5["theme_min"] == "1.9.42", r5
    assert dv.report_text(rep).count("✅") >= 10, "report text icons ledu"
    print("  C9. deploy verify: live proof · zip pending · setup pending · offline-safe ✔")


ALL = [v for k, v in sorted(globals().items())
       if k.startswith("test_") and callable(v)]

if __name__ == "__main__":
    print("=" * 74)
    print("  v197 — ENGAGE + MENU + DAILY BOT")
    print("=" * 74)
    for fn in ALL:
        fn()
    print("-" * 74)
    print(f"  v197: {len(ALL)}/{len(ALL)} checks passed ✔")
