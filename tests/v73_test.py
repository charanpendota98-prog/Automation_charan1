# -*- coding: utf-8 -*-
"""v73 tests — ENGLISH UI PASS + HERO BLOCK REMOVAL ("idi avasram ledu").

Mee brief (2026-09-18): "antha ilaga telugu lo kkadu english lo cheyu" · hero block
(eyebrow · h1 · lede · CTA · live countdown card · tiles) remove cheyali.
Scope (mee choice): UI/labels/headings/chips/notes/footer = English;
Telugu mattrame job/article content lo (post titles · summaries · quiz questions).

Ee suite ee contract ni lock chestundi — malli Telugu UI loki tirigi pokoodadu:
  * preview index: slim hero, countdown ledu, head English, chrome Telugu-free
  * preview pages (6): antha English (0 Telugu chars)
  * theme: Telugu mattrame `studentup_qual_keywords()` (post tag detection)
  * bot: MOST_USED + ad chrome English, deadline plumbing poyindi
  * PWA: sw bump + manifest/iswEnglish copy
  * docs: v73 sections + suite counts

Run: python tests/v73_test.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

PREVIEW = ROOT / "preview"
THEME = ROOT / "wordpress-theme" / "studentup"
BOT = ROOT / "autoblog"

TE = re.compile(r"[\u0C00-\u0C7F]")


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def telugu(s: str) -> int:
    return len(TE.findall(s))


def strip_scripts(html: str) -> str:
    return re.sub(r"<script.*?</script>", "", html, flags=re.S)


# ------------------------------------------------------------- preview index

def test_preview_head_is_english():
    html = read(PREVIEW / "index.html")
    assert '<html lang="en">' in html, "html lang=en kaadu"
    assert 'og:locale" content="en_IN"' in html, "og:locale en_IN ledu"
    assert '"inLanguage": "en-IN"' in html, "ld inLanguage en-IN ledu"
    assert 'og:locale" content="te_IN"' not in html, "pata te_IN og:locale inka undi"


def test_slim_hero_and_no_countdown():
    html = read(PREVIEW / "index.html")
    assert 'class="hero hero-slim"' in html, "slim hero ledu"
    h1 = re.search(r'<section class="hero hero-slim">.*?<h1>(.*?)</h1>', html, re.S)
    assert h1, "hero h1 ledu"
    assert not TE.search(h1.group(1)), "hero h1 lo Telugu undi"
    assert len(h1.group(1)) > 20
    for gone in ('id="cd-box"', 'id="cd-live"', 'id="cd-none"', "data-deadline",
                 "deadline.json", "cd-note", "class=\"hcard", "new Date(2026,9,15"):
        assert gone not in html, f"countdown vestige inka undi: {gone}"
    # honest line nijamaina notification ki point cheyali
    assert "official notification" in html, "honest deadline line ledu"


def test_ui_chrome_telugu_free():
    """Telugu antha grid cards (content) + quiz bank lo mattrame undali."""
    html = read(PREVIEW / "index.html")
    for block, name in ((re.search(r"<header.*?</header>", html, re.S), "header"),
                        (re.search(r"<footer.*?</footer>", html, re.S), "footer")):
        assert block, name + " ledu"
        assert not TE.search(block.group(0)), f"{name} lo Telugu undi"
    # chrome-shape blocks: mobile panel · used strip · qualification heads · ads · join box
    for pat, name in ((r'<div class="mpanel".*?</div>\s*<!--', "mpanel"),
                      (r'<section class="usedwrap".*?</section>', "usedwrap"),
                      (r'<aside class="su-ad".*?</aside>', "su-ad"),
                      (r'<section class="joinbox".*?</section>', "joinbox")):
        m = re.search(pat, html, re.S)
        if m:
            assert not TE.search(m.group(0)), f"{name} lo Telugu undi"
    # nav labels English (menu = UI)
    nav = re.search(r'<nav class="nav".*?</nav>', html, re.S)
    assert nav and not TE.search(nav.group(0)), "nav lo Telugu undi"
    # Telugu content: grid cards + quiz bank
    assert TE.search(html.split('id="grid"')[1].split('id="nores"')[0]), "grid content Telugu kaadu"
    assert re.search(r"var QUIZ\s*=\s*\[", html), "quiz bank ledu"
    quiz = html[html.index("var QUIZ"):]
    assert TE.search(quiz[:4000]), "quiz bank Telugu kaadu (content scope)"


def test_pwa_shell_english():
    sw = read(PREVIEW / "sw.js")
    assert "su-v73-1" in sw, "sw VERSION bump ledu"
    assert TE.search(sw) is None, "sw.js lo Telugu undi"
    assert "offline" in sw.lower()
    man = json.loads(read(PREVIEW / "manifest.webmanifest"))
    txt = json.dumps(man, ensure_ascii=False)
    assert not TE.search(txt), "manifest lo Telugu undi"
    for s in man.get("shortcuts", []):
        assert s.get("name"), "shortcut name ledu"


# ------------------------------------------------------------- preview pages

def test_all_pages_english():
    pages = sorted((PREVIEW / "pages").glob("*.html"))
    assert len(pages) == 6, [p.name for p in pages]
    for p in pages:
        html = read(p)
        n = telugu(html)
        assert n == 0, f"{p.name} lo Telugu undi ({n} chars)"
        assert '<html lang="en">' in html, p.name + " lang=en kaadu"
        assert "SPONSORED" in html, p.name + " lo SPONSORED label ledu"


# ------------------------------------------------------------------- theme

def test_theme_telugu_only_in_detection_keywords():
    """Telugu mattrame `studentup_qual_keywords()` block lo (post auto-tag)."""
    qf = read(THEME / "inc" / "qual-filter.php")
    m = re.search(r"function studentup_qual_keywords\(\)\s*\{(.*?)\n\}", qf, re.S)
    assert m, "studentup_qual_keywords() ledu"
    assert TE.search(m.group(1)), "telugu detection keywords levu (auto-tag works avvadu)"
    rest = qf.replace(m.group(1), "")
    assert not TE.search(rest), "qual-filter.php lo detection bayata Telugu undi"
    for f in THEME.rglob("*"):
        if f.is_file() and f.suffix in (".php", ".js", ".css", ".txt", ".json", ".pot"):
            if f.name == "qual-filter.php":
                continue
            assert not TE.search(read(f)), f"{f.relative_to(THEME)} lo Telugu undi"


def test_theme_surfaces_english():
    fp = read(THEME / "front-page.php")
    assert "hero hero-slim" in fp, "theme slim hero ledu"
    assert "data-deadline" not in fp and "studentup_deadline" not in fp, "theme lo countdown inka undi"
    terms = read(THEME / "inc" / "qual-filter.php")
    for want in ("'10th'", "'Inter (10+2)'", "'ITI'", "'Diploma'", "'Degree'", "'PG'", "'B.Tech'"):
        assert want in terms, "qual label miss: " + want
    foot = read(THEME / "footer.php")
    assert "Download App" in foot, "footer lo English app button ledu"
    for eng in ("Most searched by students", "SPONSORED"):
        pass
    assert "Most searched by students" in fp, "used-strip heading English ledu"


def test_bot_labels_and_no_deadline_plumbing():
    sys.path.insert(0, str(ROOT))
    from autoblog import breaking  # noqa: PLC0415

    for m in breaking.most_used():
        assert not TE.search(m["label"] + m["hint"]), m
    assert breaking.most_used_cats()[:2] == ["ts-jobs", "ap-jobs"]
    sync = read(BOT / "wp_theme_sync.py")
    assert "write_preview_deadline" not in sync, "preview deadline writer inka undi"
    assert "studentup_deadline" not in read(THEME / "inc" / "template.php")
    env = read(ROOT / ".env.example")
    assert "POST_DEADLINE" not in env, ".env lo POST_DEADLINE inka undi"
    for rel in ("autoblog/main.py", "run.py"):
        txt = read(ROOT / rel)
        assert "write_preview_deadline" not in txt, rel + " lo deadline step inka undi"
    # theme most-used labels == bot labels (site/bot parity)
    labels = [m["label"] for m in breaking.most_used()]
    theme = re.findall(r"'slug' => '[a-z-]+', 'label' => '([^']+)'", read(THEME / "functions.php"))
    assert theme == labels, (theme, labels)


def test_ad_chrome_english():
    am = read(BOT / "ad_manager.py")
    assert not TE.search(am), "ad_manager.py lo Telugu chrome undi (ads public UI)"
    assert "not a paid" in am and "Sponsored content" in am


# -------------------------------------------------------------------- docs

def test_docs_claims():
    readme = read(ROOT / "README.md")
    manual = read(ROOT / "MANUAL_ADVANCED_CHECKLIST.md")
    assert "v73" in readme and "ENGLISH UI" in readme.upper()
    assert "PART 33" in manual and "v73" in manual
    suites = len(list((ROOT / "tests").glob("*_test.py")))
    jsdom = read(ROOT / "tests" / "runtime" / "jsdom_runtime_test.js")
    n = int(re.search(r"EXPECTED_CHECKS\s*=\s*(\d+)", jsdom).group(1))
    for name, txt in (("README", readme), ("MANUAL", manual),
                      ("GO_LIVE", read(ROOT / "GO_LIVE_CHECKLIST.md"))):
        assert f"{suites}/{suites}" in txt, f"{name} lo suites claim ledu ({suites})"
        assert f"{n}/{n}" in txt, f"{name} lo jsdom claim ledu ({n})"
    assert "su-v73-1" in read(ROOT / "DEPLOY_MILESWEB.md"), "deploy doc lo sw version stale"


TESTS = [
    ("preview head English (lang · og:locale · ld)", test_preview_head_is_english),
    ("preview slim hero + countdown poyindi", test_slim_hero_and_no_countdown),
    ("preview: Telugu mattrame content lo (UI kaadu)", test_ui_chrome_telugu_free),
    ("PWA shell English + sw bump", test_pwa_shell_english),
    ("6 preview pages English", test_all_pages_english),
    ("theme: Telugu mattrame detection keywords lo", test_theme_telugu_only_in_detection_keywords),
    ("theme surfaces English (hero · footer · qual labels)", test_theme_surfaces_english),
    ("bot labels English + deadline plumbing poyindi", test_bot_labels_and_no_deadline_plumbing),
    ("ad chrome English (public ads)", test_ad_chrome_english),
    ("docs: v73 section + PART 33 + counts", test_docs_claims),
]


def main() -> int:
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
    print("-" * 68)
    if failed:
        print(f"  {failed} TEST(S) FAILED ✘")
        return 1
    print(f"ALL v73 ENGLISH-UI TESTS PASSED ✔  ({len(TESTS)} checks)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
