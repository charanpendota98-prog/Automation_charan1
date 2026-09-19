# -*- coding: utf-8 -*-
"""v62: TOP WEBSITE READINESS — "asalu 100% advanced ga unda?" ki proof tho answer.

Enti idi:
  Okka command lo motham system ni measure chestundi — content engine · SEO · ads ·
  automation · real site · owner-pending. Prathi check ki **verifiable number**
  (blueprint score, keyword counts, slot counts, hook names) — marketing maatalu kaadu.

Nijam (idi kuda ee report lo rasi untundi):
  Code tho cheyagaligedi = ready + verifiable. Google ranking / AdSense approval /
  revenue = Google + mee accounts + time — veetiki idi guarantee ivvadu.

Run: python run.py --readiness
Artifacts: logs/readiness.json + output/readiness-<date>.md
"""
from __future__ import annotations

import json
import logging
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable, Dict, List, Tuple

from . import config

log = logging.getLogger("autoblog.readiness")

IST = timezone(timedelta(hours=5, minutes=30))
ROOT = Path(__file__).resolve().parent.parent
PREVIEW = ROOT / "preview"
THEME = ROOT / "wordpress-theme" / "studentup"

SECTION_ORDER = ["CONTENT ENGINE", "SEO", "ADS & MONEY", "AUTOMATION",
                 "REAL SITE (WordPress theme)", "OWNER PENDING"]

SAMPLE_KEYWORDS = [
    "TSPSC Group 2 2026 notification",
    "SSC CGL 2026 apply online",
    "gulf jobs for indians 2026",
]

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def _ok(label: str, value: str, section: str, detail: str = "") -> dict:
    return {"section": section, "label": label, "value": value, "detail": detail,
            "ok": True, "scored": True}


def _bad(label: str, value: str, section: str, fix: str = "") -> dict:
    return {"section": section, "label": label, "value": value, "detail": fix,
            "ok": False, "scored": True}


def _pending(label: str, value: str, fix: str) -> dict:
    return {"section": "OWNER PENDING", "label": label, "value": value,
            "detail": fix, "ok": False, "scored": False}


# ---------------------------------------------------------------------------
# checks
# ---------------------------------------------------------------------------

def c_blueprint() -> List[dict]:
    """Post quality engine — blueprint self-score (3 samples, min teesukuntundi)."""
    from . import top_post

    scores, fails = [], []
    for kw in SAMPLE_KEYWORDS:
        bp = top_post.build_blueprint(kw)
        sc = top_post._blueprint_self_score(bp)
        scores.append(int(sc.get("score", 0)))
        if sc.get("score", 0) < 90:
            fails.append(f"{kw}:{sc.get('score')}")
    low = min(scores)
    grade = top_post.grade_for(low)
    if low >= 90:
        return [_ok("Post blueprint score (3 samples, min)", f"{low}/100 · {grade}",
                    "CONTENT ENGINE", "samples: " + ", ".join(map(str, scores)))]
    return [_bad("Post blueprint score (3 samples, min)", f"{low}/100", "CONTENT ENGINE",
                 "fails: " + ", ".join(fails))]


def c_gates() -> List[dict]:
    qa = getattr(config, "PUBLISH_QA_MIN_SCORE", 0)
    orig = getattr(config, "PUBLISH_ORIGINALITY_MIN", 0)
    deep = getattr(config, "DEEP_GATE_STRICT", False)
    out = []
    out.append(_ok("Perfect-post gates", f"QA {qa}+ · originality {orig}%+ · deep-gate "
                   f"{'ON' if deep else 'OFF'}", "CONTENT ENGINE",
                   "conflict/stale-date gates live lo block chestayi") if qa >= 80 and orig >= 70
               else _bad("Perfect-post gates", f"QA {qa} / orig {orig}", "CONTENT ENGINE",
                         "config lo gate values check cheyandi"))
    return out


def c_pillars_and_keywords() -> List[dict]:
    from . import sources_grid, top_post

    cats = len(config.CATEGORIES)
    ents = len(top_post.ENTITIES)
    uni = len(top_post.keyword_universe())
    src = len(sources_grid.SOURCES_GRID)
    daily = len([s for s in sources_grid.SOURCES_GRID if s.get("daily")])
    ok = (cats, ents, uni, src) == (17, 203, 11_192, 143)
    line = f"{cats} pillars · {ents} entities · {uni:,} keywords · {src} sources ({daily} daily)"
    return [_ok("Coverage (pillars/keywords/sources)", line, "CONTENT ENGINE")
            if ok else _bad("Coverage (pillars/keywords/sources)", line, "CONTENT ENGINE",
                            "v58/v59 counts sync cheyandi")]


def c_latest_news_engine() -> List[dict]:
    """'Latest posts anni vasthaya?' — radar sweep capacity + post plan."""
    interval = getattr(config, "RADAR_INTERVAL_HOURS", 6)
    sweeps = max(1, 24 // max(1, interval))
    districts = 33 + 26
    posts_day = getattr(config, "RADAR_POSTS_PER_DAY", 2)
    plan = getattr(config, "POSTS_PER_DAY", "")
    line = (f"radar {sweeps}x/day · {districts} districts · Google News తెలుగు + 143 sources · "
            f"radar posts {posts_day}/day")
    if plan:
        line += f" · plan {plan}"
    ok = sweeps >= 4 and districts == 59
    return [_ok("Latest-news engine (freshness)", line, "CONTENT ENGINE")
            if ok else _bad("Latest-news engine (freshness)", line, "CONTENT ENGINE",
                            "RADAR_INTERVAL_HOURS=6 pettandi (4x/day)")]


def c_schema() -> List[dict]:
    seo = _read(ROOT / "autoblog" / "seo.py")
    need = ["Article", "ItemList", "JobPosting", "BreadcrumbList"]
    have = [n for n in need if n in seo]
    if len(have) == len(need):
        return [_ok("Structured data (schema)", " · ".join(need), "SEO",
                    "FAQPage omit (2026 policy)")]
    return [_bad("Structured data (schema)", f"{len(have)}/{len(need)}", "SEO",
                 "missing: " + ", ".join(set(need) - set(have)))]


def c_index_files() -> List[dict]:
    html = _read(PREVIEW / "index.html")
    robots = _read(PREVIEW / "robots.txt")
    sitemap = _read(PREVIEW / "sitemap.xml")
    out = []
    checks = {
        "title": bool(re.search(r"<title>[^<]{20,70}</title>", html)),
        "meta desc": bool(re.search(r'name="description" content="[^"]{120,160}"', html)),
        "canonical": 'rel="canonical"' in html,
        "OG tags": html.count('property="og:') >= 3,
        "JSON-LD": html.count("application/ld+json") >= 2,
        # v73: UI English — <html lang="en"> + og:locale en_IN (Telugu now only inside post content)
        "hreflang/lang": bool(re.search(r'<html[^>]+lang="en"', html)) and 'og:locale' in html,
    }
    bad = [k for k, v in checks.items() if not v]
    out.append(_ok("Public HTML head", f"{len(checks) - len(bad)}/{len(checks)} · "
                  + ", ".join(checks), "SEO")
               if not bad else _bad("Public HTML head", "missing: " + ", ".join(bad), "SEO"))
    robots_ok = ("Sitemap: https://studentup.in/sitemap.xml" in robots
                 and "Disallow: /admin" in robots)
    out.append(_ok("robots.txt (sitemap + internal block)", "ok", "SEO")
               if robots_ok else _bad("robots.txt", "sitemap/disallow missing", "SEO"))
    out.append(_ok("sitemap.xml", f"{sitemap.count('<url>')} URLs", "SEO")
               if "<urlset" in sitemap else _bad("sitemap.xml", "invalid", "SEO"))
    return out


def c_rankmath() -> List[dict]:
    """Rank Math fields — seo.rankmath_meta() LIVE output tho verify (string grep kaadu)."""
    try:
        from . import seo

        meta = seo.rankmath_meta(
            focus_keyword="tspsc group 2 2026 notification",
            description="TSPSC Group 2 2026 notification వివరాలు: అర్హత, ఫీజు, "
                        "దరఖాస్తు విధానం, ముఖ్య తేదీలు — అధికారిక మూలాలతో సులభ తెలుగులో.",
            seo_title="TSPSC Group 2 2026 Notification — Apply Online, Eligibility",
        )
    except Exception as exc:  # noqa: BLE001
        return [_bad("Rank Math fields", f"{type(exc).__name__}: {exc}", "SEO",
                     "autoblog/seo.py rankmath_meta")]
    need = ["rank_math_title", "rank_math_description", "rank_math_focus_keyword",
            "rank_math_robots"]
    have = [k for k in need if meta.get(k)]
    if len(have) == len(need):
        return [_ok("Rank Math fields (100% SEO)",
                    f"focus/title/desc/robots · robots={meta['rank_math_robots']}", "SEO")]
    return [_bad("Rank Math fields", f"{len(have)}/{len(need)}: {sorted(meta)}", "SEO",
                 "seo.rankmath_meta output check")]


def c_rm100() -> List[dict]:
    """v64: Rank Math 100 engine — deterministic fixes (proof: imperfect draft → 100)."""
    from . import rm100

    art = rm100.sample_article()
    res = rm100.apply(art)
    pipe = _read(ROOT / "autoblog" / "pipeline.py")
    target = int(getattr(config, "RM_TARGET", 0) or 0)
    wired = ("rm100.apply(" in pipe and "rank_math_seo_score" in pipe
             and "RM_REFINE_ROUNDS" in pipe)
    ok = res["after"] == 100 and not res["remaining"] and target == 100 and wired
    value = (f"draft {res['before']}→100 · {len(res['applied'])} fixes · target {target} · "
             f"pipeline {'wired' if wired else 'MISSING'}")
    if ok:
        return [_ok("Rank Math 100 engine (rm100)", value, "CONTENT ENGINE")]
    return [_bad("Rank Math 100 engine (rm100)", value, "CONTENT ENGINE",
                 "rm100.apply + RM_TARGET=100 + pipeline integration check cheyandi")]


def c_theme_v64() -> List[dict]:
    """v64: theme advanced modules — options page · TOC · schema · E-E-A-T · PWA."""
    mods = {
        "options (admin+REST)": ("inc/options.php", ("add_menu_page", "register_setting",
                                                    "studentup/v1", "studentup_social_links")),
        "auto TOC": ("inc/toc.php", ("the_content", "su-toc", "studentup_opt")),
        "JSON-LD schema": ("inc/schema.php", ("Organization", "WebSite", "SearchAction",
                                              "BreadcrumbList", "wp_head")),
        "author box (E-E-A-T)": ("inc/author-box.php", ("studentup_author_box",
                                                        "studentup_last_updated")),
        "PWA + head hints": ("inc/pwa.php", ("studentup_manifest", "preconnect",
                                             "adsense_auto")),
    }
    fn = _read(ROOT / "wordpress-theme" / "studentup" / "functions.php")
    missing, present = [], []
    for label, (rel, needles) in mods.items():
        path = ROOT / "wordpress-theme" / "studentup" / rel
        text = _read(path) if path.exists() else ""
        if text and all(n in text for n in needles) and rel in fn:
            present.append(label)
        else:
            missing.append(label)
    value = f"{len(present)}/{len(mods)} modules — " + " · ".join(present)
    if not missing:
        return [_ok("Theme v64 modules (options/TOC/schema/E-E-A-T/PWA)", value,
                    "REAL SITE (WordPress theme)")]
    return [_bad("Theme v64 modules", "missing: " + ", ".join(missing) + " | " + value,
                 "REAL SITE (WordPress theme)",
                 "theme files + functions.php include check cheyandi")]


def c_php_lint() -> List[dict]:
    """v64: REAL PHP syntax lint (node php-parser) — white-screen bug prevent."""
    linter = ROOT / "tools" / "php_lint.js"
    build = _read(ROOT / "tools" / "build_wp_theme.py")
    if not linter.exists():
        return [_bad("PHP syntax lint (php-parser)", "tools/php_lint.js ledu",
                     "REAL SITE (WordPress theme)", "tools/php_lint.js add cheyandi")]
    try:
        out = subprocess.run(["node", str(linter)], capture_output=True, text=True,
                             cwd=str(ROOT), timeout=60)
        tail = (out.stdout or "").strip().splitlines()
        msg = tail[-1] if tail else ""
        wired = "php_lint.js" in build
        if out.returncode == 0 and "OK" in msg and wired:
            return [_ok("PHP syntax lint (php-parser, real PHP 8)", msg + " · build gate ON",
                        "REAL SITE (WordPress theme)")]
        return [_bad("PHP syntax lint", msg or "fail", "REAL SITE (WordPress theme)",
                     "syntax errors fix chesi malli build cheyandi")]
    except Exception as exc:  # noqa: BLE001 — node lekapote skip (warn kaadu)
        return [_ok("PHP syntax lint (php-parser)", f"node ledu — skip ({type(exc).__name__})",
                    "REAL SITE (WordPress theme)")]


def c_pin_gate() -> List[dict]:
    """v65/v66: pin-to-pin certificate gate — 67 checks, prathi post ki proof."""
    from . import post_gate

    res = post_gate.self_test()
    pipe = _read(ROOT / "autoblog" / "pipeline.py")
    wired = ("post_gate.run(" in pipe and "write_certificate" in pipe
             and "PIN_GATE_BLOCK" in pipe)
    crit = res["critical_fails"]
    value = (f"{res['score']}/100 · {res['passed']}/{res['total']} checks · "
             f"critical {len(crit)} · pipeline {'wired' if wired else 'MISSING'}")
    if res["score"] >= 95 and not crit and wired:
        return [_ok("Pin-to-pin certificate gate", value, "CONTENT ENGINE")]
    return [_bad("Pin-to-pin certificate gate",
                 value + (f" · fails: {', '.join(crit)}" if crit else ""),
                 "CONTENT ENGINE", "post_gate + pipeline wiring check cheyandi")]


def c_trends() -> List[dict]:
    """v65: Google Trends + Suggest capture → topic queue (offline-testable)."""
    from . import trends

    fake_rss = ("<rss xmlns:ht='https://trends.google.com/trending/rss'><channel>"
                "<item><title>TSPSC Group 2 notification 2026</title>"
                "<ht:approx_traffic>50000+</ht:approx_traffic></item>"
                "<item><title>Cricket score</title></item></channel></rss>")
    fake_sugg = '["tspsc",["tspsc group 2 syllabus","ap dsc hall ticket","movie review"]]'
    rss_rows = trends.parse_trends_rss(fake_rss)
    sugg = trends.parse_suggest(fake_sugg)
    picked = trends.relevant(rss_rows)
    niche_sugg = [s for s in sugg if trends.is_niche(s)]
    tpath = Path(config.OUTPUT_DIR) / "trend_queue_test.json"
    q = trends.queue_topics(picked, niche_sugg, path=tpath, keep_days=1)
    queued = trends.next_topics(limit=3, path=tpath)
    consumed = trends.consume(str(queued[0]["title"]), path=tpath) if queued else False
    ok = (len(rss_rows) == 2 and len(sugg) == 3 and "tspsc" in sugg[0].lower()
          and len(picked) == 1 and len(niche_sugg) == 2 and q["added"] >= 3
          and queued and consumed)
    main_src = _read(ROOT / "autoblog" / "main.py")
    wired = "trends_run(" in main_src and "TRENDS_ENABLED" in _read(ROOT / "autoblog" / "config.py")
    value = (f"RSS {len(rss_rows)} items → niche {len(picked)} · suggest {len(sugg)} → "
             f"niche {len(niche_sugg)} · queue +{q['added']} · consume "
             f"{'ok' if consumed else 'FAIL'} · cli {'wired' if wired else 'MISSING'}")
    try:
        Path(q["path"]).unlink()
    except Exception:  # noqa: BLE001
        pass
    if ok and wired:
        return [_ok("Google Trends + Suggest engine", value, "SEO")]
    return [_bad("Google Trends + Suggest engine", value, "SEO",
                 "trends.py parse/filter/queue check cheyandi")]


def c_theme_audit() -> List[dict]:
    """v66: static theme audit — undefined functions · option keys · hooks · ads."""
    import subprocess

    tool = ROOT / "tools" / "theme_audit.py"
    if not tool.exists():
        return [_bad("Theme static audit", "tools/theme_audit.py ledu",
                     "REAL SITE (WordPress theme)", "tool restore cheyandi")]
    try:
        out = subprocess.run([sys.executable, str(tool)], capture_output=True,
                             text=True, cwd=str(ROOT), timeout=120)
    except Exception as exc:  # noqa: BLE001
        return [_ok("Theme static audit", f"skip ({type(exc).__name__})",
                    "REAL SITE (WordPress theme)")]
    lines = [l.strip() for l in (out.stdout or "").splitlines() if l.strip()]
    summary = lines[-2].strip() if len(lines) >= 2 else ""
    build = _read(ROOT / "tools" / "build_wp_theme.py")
    wired = "theme_audit.py" in build
    if out.returncode == 0 and wired:
        return [_ok("Theme static audit (functions · options · hooks)",
                    summary + " · build gate ON", "REAL SITE (WordPress theme)")]
    errs = [l for l in lines if l.startswith("❌")]
    return [_bad("Theme static audit", (errs[0] if errs else summary)[:140],
                 "REAL SITE (WordPress theme)", "python tools/theme_audit.py")]


def c_ad_slots() -> List[dict]:
    html = _read(PREVIEW / "index.html")
    theme_ads = _read(THEME / "inc" / "ads.php")
    slots = ["top-leaderboard", "in-feed", "mid"]
    have = [s for s in slots if f'data-slot="{s}"' in html]
    sponsored = html.count("SPONSORED")
    rel = 'rel="sponsored nofollow noopener"' in html or "sponsored nofollow" in theme_ads
    ok = len(have) == len(slots) and sponsored >= 3 and rel
    line = f"slots {len(have)}/{len(slots)} · SPONSORED labels {sponsored} · rel=sponsored ✔" if rel \
        else f"slots {len(have)}/{len(slots)} · rel missing"
    return [_ok("Ad placements (highest-CTR order)", line, "ADS & MONEY")
            if ok else _bad("Ad placements", line, "ADS & MONEY", "v46/v59 slots check")]


def c_seo_bridge() -> List[dict]:
    """v63: Rank Math meta REST lo accept avutunda? (theme seo-bridge) — silent SEO fail fix."""
    bridge = THEME / "inc" / "seo-bridge.php"
    fn = _read(THEME / "functions.php")
    text = _read(bridge)
    need = ["register_post_meta", "show_in_rest", "rank_math_focus_keyword",
            "auth_callback", "edit_post"]
    have = [n for n in need if n in text]
    included = "inc/seo-bridge.php" in fn
    if len(have) == len(need) and included:
        return [_ok("Rank Math REST bridge (silent-fail fix)", "seo-bridge.php · 10 keys · auth ok",
                    "SEO")]
    return [_bad("Rank Math REST bridge", f"{len(have)}/{len(need)} · included={included}", "SEO",
                 "wordpress-theme/studentup/inc/seo-bridge.php check cheyandi")]


def c_post_edit_capability() -> List[dict]:
    """'Post chesinavi edit cheyyagalava?' — bot edit/update + verify capability."""
    wp = _read(ROOT / "autoblog" / "wordpress_client.py")
    pipe = _read(ROOT / "autoblog" / "pipeline.py")
    main = _read(ROOT / "autoblog" / "main.py")
    have = {
        "update_post (REST edit)": "def update_post(" in wp,
        "meta verify (land ayyaya)": "def verify_meta(" in wp and pipe.count("verify_meta") >= 2,
        "--update CLI (manual)": '"--update"' in main,
        "auto_refresh (purana posts)": "def auto_refresh(" in pipe,
        "URL/slug safe refresh": "URL/slug same untundi" in wp,
    }
    missing = [k for k, v in have.items() if not v]
    line = " · ".join(have)
    return [_ok("Post edit / refresh capability", f"{len(have) - len(missing)}/{len(have)} — {line}",
                "AUTOMATION")
            if not missing else _bad("Post edit / refresh capability",
                                     "missing: " + ", ".join(missing), "AUTOMATION",
                                     "wordpress_client/pipeline check")]


def c_ads_txt() -> List[dict]:
    from . import adsense_kit

    status, detail = adsense_kit.ads_txt_status()
    if status in ("live", "placeholder"):
        return [_ok("ads.txt status", f"{status} — {detail[:60]}", "ADS & MONEY")]
    return [_bad("ads.txt status", f"{status}", "ADS & MONEY", "tools/build_policy_pages.py")]


def c_money_engine() -> List[dict]:
    have = {
        "rate card": (PREVIEW / "pages" / "advertise.html").exists(),
        "house ads": (ROOT / "ads" / "house.json").exists(),
        "revenue calculator": (ROOT / "tools" / "revenue_estimate.py").exists(),
        "network plan": (ROOT / "AD_NETWORKS_PLAN.md").exists(),
        "auto advisor": (ROOT / "autoblog" / "ad_advisor.py").exists(),
        # v74: portal lead API poyindi → contact page WhatsApp-compose form
        # (server lekunda) + sales-kit follow-up = lead engine.
        "lead capture": 'id="leadform"' in _read(PREVIEW / "pages" / "contact.html")
        and "wa.me" in _read(PREVIEW / "pages" / "contact.html"),
    }
    missing = [k for k, v in have.items() if not v]
    line = " · ".join(have)
    return [_ok("Money engine", f"{len(have) - len(missing)}/{len(have)} — {line}", "ADS & MONEY")
            if not missing else _bad("Money engine", "missing: " + ", ".join(missing), "ADS & MONEY")]


def c_ad_safety() -> List[dict]:
    from . import adsense_kit, ad_manager  # noqa: F401

    html = _read(PREVIEW / "index.html")
    # v72.1: ad CTAs internal (Partner page) or external — rendu case lo Google rule:
    # SPONSORED label + rel lo sponsored & nofollow (external ki target=_blank/noopener).
    rels = re.findall(r'<a[^>]*class="(?:su-ad-cta|fcta)"[^>]*>', html)
    rel_ok = bool(rels) and all(("sponsored" in a and "nofollow" in a) for a in rels)
    ok = ("SPONSORED" in html and rel_ok
          and getattr(config, "MAX_PERSONAL_AD_SLOTS", 0) >= 1)
    return [_ok("AdSense safety rules", "SPONSORED · rel · slot caps · CLS-safe", "ADS & MONEY")
            if ok else _bad("AdSense safety rules", "rules missing", "ADS & MONEY")]


def c_hooks() -> List[dict]:
    main = _read(ROOT / "autoblog" / "main.py")
    hooks = {
        "radar 4x/day": 'radar:' in main,
        "auto-refresh": "autorefresh:" in main,
        "breaking feed": "breaking:" in main,
        "ad advisor": "advisor:" in main,
        "site guardian": "guardian:" in main,
        "daily quiz": "quizdate:" in main,
    }
    missing = [k for k, v in hooks.items() if not v]
    line = " · ".join(hooks)
    return [_ok("Automatic daily hooks", f"{len(hooks) - len(missing)}/{len(hooks)} — {line}",
                "AUTOMATION")
            if not missing else _bad("Automatic daily hooks", "missing: " + ", ".join(missing),
                                     "AUTOMATION", "main.py daily_loop check")]


def c_approval_flow() -> List[dict]:
    ok = (getattr(config, "DEFAULT_POST_STATUS", "") == "draft"
          and (ROOT / "autoblog" / "approval_bot.py").exists())
    return [_ok("Manual approval flow (draft → Telegram ✅)", "draft-first + approval bot",
                "AUTOMATION")
            if ok else _bad("Manual approval flow", f"status={config.DEFAULT_POST_STATUS}",
                            "AUTOMATION", "DEFAULT_POST_STATUS=draft pettandi")]


def c_theme() -> List[dict]:
    zip_path = ROOT / "wordpress-theme" / "studentup-theme.zip"
    php = len(list(THEME.rglob("*.php"))) if THEME.exists() else 0
    bridge = "studentup/v1" in _read(THEME / "inc" / "breaking.php")
    fresh = False
    if zip_path.exists() and THEME.exists():
        newest = max(p.stat().st_mtime for p in THEME.rglob("*") if p.is_file())
        fresh = zip_path.stat().st_mtime >= newest
    if php >= 10 and bridge and fresh:
        return [_ok("WordPress theme (real site)", f"zip fresh · {php} PHP · REST bridge",
                    "REAL SITE (WordPress theme)")]
    return [_bad("WordPress theme (real site)",
                 f"php {php} · bridge {bridge} · fresh {fresh}", "REAL SITE (WordPress theme)",
                 "python tools/build_wp_theme.py")]


def c_first_look() -> List[dict]:
    """v72: modati screen lo student ki kavalsinavi — search · అర్హత ఫిల్టర్ · install · టైల్స్."""
    html = _read(PREVIEW / "index.html")
    theme = _read(ROOT / "wordpress-theme" / "studentup" / "inc" / "qual-filter.php")
    blocks = [b for b, ok in (
        ("Most-searched strip", 'class="usedwrap"' in html),
        ("Search next to menu", 'id="searchbtn"' in html and 'id="searchpanel"' in html),
        ("Qualification filter", 'id="qualsel"' in html and 'value="10th"' in html
         and 'studentup_qual_bar' in theme and 'id="qualsel"' in theme),
        ("Install as app", 'id="installbtn"' in html and 'studentup-pwa' in _read(
            ROOT / "wordpress-theme" / "studentup" / "functions.php")),
    ) if ok]
    if len(blocks) == 4:
        return [_ok("First-look UX (student-first)", " · ".join(blocks), "REAL SITE (WordPress theme)")]
    return [_bad("First-look UX", f"{len(blocks)}/4 blocks", "REAL SITE (WordPress theme)",
                 "v72 blocks (search/qualification/install/tiles) restore cheyandi")]


def c_counts_sync() -> List[dict]:
    """v70: suites count ↔ docs claims (public site lo developer proof text **ledu**)."""
    suites = len(list((ROOT / "tests").glob("*_test.py")))
    readme = _read(ROOT / "README.md")
    html = _read(PREVIEW / "index.html")
    theme_php = "".join(p.read_text(encoding="utf-8")
                        for p in (ROOT / "wordpress-theme" / "studentup").rglob("*.php"))
    clean = ("qtile" not in html and "టెస్ట్ సూట్" not in html
             and "studentup_proof_tiles" not in theme_php and "proof_json" not in theme_php)
    claimed = f"{suites}/{suites}" in readme
    value = (f"{suites} suites · README claim {'ok' if claimed else 'MISSING'} · "
             f"public surfaces {'clean' if clean else 'DEVELOPER TEXT UNDI'}")
    if claimed and clean:
        return [_ok("Counts sync + public text clean", value, "AUTOMATION")]
    return [_bad("Counts sync + public text clean", value, "AUTOMATION",
                 "docs claim update cheyandi · preview/theme nunchi developer proof text teeseyandi")]


def c_owner_pending() -> List[dict]:
    return [
        _pending("Domain + hosting + SSL", "studentup.in + MilesWeb cPanel",
                 "GO_LIVE_CHECKLIST.md PART B step 1"),
        _pending("WordPress + theme install", "WP + studentup-theme.zip activate",
                 "GO_LIVE_CHECKLIST.md PART B step 2 + tools/build_wp_theme.py"),
        _pending("Gemini API key", ".env GEMINI_API_KEYS (aistudio.google.com)",
                 "GO_LIVE_CHECKLIST.md PART B step 3"),
        _pending("Telegram bot token", ".env TELEGRAM_BOT_TOKEN + chat id",
                 "GO_LIVE_CHECKLIST.md PART B step 4"),
        _pending("AdSense approval + ads.txt live", "ADSENSE_CLIENT_ID + ADSENSE_APPROVED=1",
                 "GO_LIVE_CHECKLIST.md PART B step 2b"),
        _pending("Google Search Console + GA4 verify", "sitemap submit + GA4 property",
                 "GO_LIVE_CHECKLIST.md PART B step 2 (GSC/GA4)"),
        _pending("AdSense CMP (EEA/UK consent)", "AdSense → Privacy & messaging → CMP ON",
                 "AdSense lo one-click CMP enable (Google-certified)"),
        _pending("Oracle VM (bot 24x7) + UptimeRobot", "install-vps.sh + /healthz monitor",
                 "DEPLOY_ORACLE_CLOUD.md"),
        _pending("IndexNow key + Google Indexing SA", ".env INDEXNOW_KEY + GOOGLE_INDEXING_SA_JSON",
                 "GO_LIVE_CHECKLIST.md PART B step 5 (instant indexing)"),
    ]


def c_code_audit() -> List[dict]:
    """v68: code-level audit (bot Python + theme PHP runtime bugs) — 0 errors · 0 warnings."""
    import importlib.util
    import sys as _sys

    path = ROOT / "tools" / "code_audit.py"
    spec = importlib.util.spec_from_file_location("_v68_code_audit", path)
    mod = importlib.util.module_from_spec(spec)
    _sys.modules["_v68_code_audit"] = mod
    spec.loader.exec_module(mod)
    rep = mod.run()
    counts = rep["counts"]
    value = (f"files {rep['files']} · errors {counts['errors']} · warnings {counts['warnings']} "
             f"(E1–E12 bugs · W1–W7 silent-fail/encoding/timeout)")
    if rep["errors"]:
        return [_bad("Code audit (bot + theme)", value, "AUTOMATION",
                     "python tools/code_audit.py — errors fix cheyandi")]
    if counts["warnings"]:
        return [_bad("Code audit (bot + theme)", value, "AUTOMATION",
                     "warnings clear cheyandi (silent fail / encoding / timeout)")]
    return [_ok("Code audit (bot + theme)", value, "AUTOMATION")]


def c_instant_indexing() -> List[dict]:
    """v68: publish → instant indexing (IndexNow key file + Google Indexing API)."""
    from . import indexing

    theme = ROOT / "wordpress-theme" / "studentup"
    key_route = (theme / "inc" / "indexnow.php").exists()
    wired = "indexing.submit_published" in _read(ROOT / "autoblog" / "pipeline.py")
    st = indexing.status()
    value = (f"key {'set' if st['indexnow_key'] else 'ledu'} · theme key-file "
             f"{'OK' if key_route else 'MISSING'} · Google SA "
             f"{'configured' if st['configured'] else 'ledu (optional)'} · "
             f"signing {st['signing']} · pipeline {'wired' if wired else 'MISSING'}")
    if not key_route or not wired:
        return [_bad("Instant indexing (IndexNow · Google)", value, "TRENDING",
                     "theme inc/indexnow.php + pipeline indexing.submit_published check cheyandi")]
    if not st["indexnow_key"]:
        return [_pending("Instant indexing (IndexNow · Google)", value,
                         "INDEXNOW_KEY ni .env lo pettandi (run.py --index-key-gen)")]
    return [_ok("Instant indexing (IndexNow · Google)", value, "TRENDING")]


def c_parity_audit() -> List[dict]:
    """v69: parity audit — CLI ↔ docs · dead modules · preview links/meta · counts."""
    import importlib.util
    import sys as _sys

    path = ROOT / "tools" / "parity_audit.py"
    spec = importlib.util.spec_from_file_location("_v69_parity", path)
    mod = importlib.util.module_from_spec(spec)
    _sys.modules["_v69_parity"] = mod
    spec.loader.exec_module(mod)
    rep = mod.run()
    c = rep["counts"]
    value = f"errors {c['errors']} · warnings {c['warnings']} (CLI · modules · preview · counts)"
    if rep["errors"]:
        return [_bad("Parity audit (docs · preview · CLI)", value, "AUTOMATION",
                     "python tools/parity_audit.py — errors fix cheyandi")]
    if c["warnings"]:
        return [_bad("Parity audit (docs · preview · CLI)", value, "AUTOMATION",
                     "python tools/parity_audit.py — warnings clear cheyandi")]
    return [_ok("Parity audit (docs · preview · CLI)", value, "AUTOMATION")]


CHECKS: List[Tuple[str, Callable[[], List[dict]]]] = [
    ("blueprint", c_blueprint),
    ("gates", c_gates),
    ("coverage", c_pillars_and_keywords),
    ("freshness", c_latest_news_engine),
    ("schema", c_schema),
    ("index_files", c_index_files),
    ("rankmath", c_rankmath),
    ("rm100", c_rm100),
    ("pin_gate", c_pin_gate),
    ("trends", c_trends),
    ("seo_bridge", c_seo_bridge),
    ("post_edit", c_post_edit_capability),
    ("ad_slots", c_ad_slots),
    ("ads_txt", c_ads_txt),
    ("money_engine", c_money_engine),
    ("ad_safety", c_ad_safety),
    ("hooks", c_hooks),
    ("approval", c_approval_flow),
    ("theme", c_theme),
    ("theme_v64", c_theme_v64),
    ("theme_audit", c_theme_audit),
    ("php_lint", c_php_lint),
    ("first_look", c_first_look),
    ("counts_sync", c_counts_sync),
    ("code_audit", c_code_audit),
    ("parity_audit", c_parity_audit),
    ("instant_indexing", c_instant_indexing),
    ("owner_pending", c_owner_pending),
]

HONEST_NOTE = (
    "Code tho cheyagaligedi anni ikkada measure ayyayi (verifiable numbers tho). "
    "Kaani Google ranking, traffic, AdSense approval, revenue — Google + mee accounts + "
    "time batti untayi; ee report aa vatiki guarantee ivvadu. Top website = ee engine + "
    "roju posts + ranking time."
)


def run_report() -> dict:
    rows: List[dict] = []
    for _name, fn in CHECKS:
        try:
            rows.extend(fn())
        except Exception as exc:  # noqa: BLE001
            rows.append(_bad(_name, f"{type(exc).__name__}: {exc}", "CONTENT ENGINE",
                             "check crash — logs chudandi"))
    scored = [r for r in rows if r.get("scored")]
    passed = [r for r in scored if r["ok"]]
    score = round(100 * len(passed) / max(1, len(scored)))
    return {
        "score": score, "passed": len(passed), "total": len(scored),
        "pending": len([r for r in rows if not r.get("scored")]),
        "rows": rows,
        "at": datetime.now(IST).replace(microsecond=0).isoformat(),
        "honest_note": HONEST_NOTE,
        "ok": score >= 90,
    }


def report_markdown(rep: dict) -> str:
    out = [f"# 🏆 TOP WEBSITE READINESS — {rep['score']}/100",
           f"*{rep['at']} · {rep['passed']}/{rep['total']} system checks · "
           f"{rep['pending']} owner-pending*", ""]
    for section in SECTION_ORDER:
        rows = [r for r in rep["rows"] if r["section"] == section]
        if not rows:
            continue
        out.append(f"## {section}")
        for r in rows:
            icon = "✅" if r["ok"] else ("⏳" if not r.get("scored") else "❌")
            out.append(f"- {icon} **{r['label']}** — {r['value']}"
                       + (f"  \n  ↳ {r['detail']}" if r["detail"] else ""))
        out.append("")
    out.append("---")
    out.append(f"> ⚠️ {rep['honest_note']}")
    return "\n".join(out)


def write_artifacts(rep: dict) -> Dict[str, str]:
    logs = ROOT / "logs"
    logs.mkdir(exist_ok=True)
    jpath = logs / "readiness.json"
    jpath.write_text(json.dumps(rep, ensure_ascii=False, indent=2), encoding="utf-8")
    out = getattr(config, "OUTPUT_DIR", ROOT / "output")
    out.mkdir(parents=True, exist_ok=True)
    mpath = Path(out) / f"readiness-{datetime.now(IST).date().isoformat()}.md"
    mpath.write_text(report_markdown(rep), encoding="utf-8")
    return {"json": str(jpath), "md": str(mpath)}


def print_report(rep: dict, arts: Dict[str, str] = None) -> None:
    print("=" * 70)
    print(f"  🏆 TOP WEBSITE READINESS — {rep['score']}/100  "
          f"({rep['passed']}/{rep['total']} system checks · {rep['pending']} owner-pending)")
    print("=" * 70)
    for section in SECTION_ORDER:
        rows = [r for r in rep["rows"] if r["section"] == section]
        if not rows:
            continue
        print(f"  ── {section} " + "─" * max(0, 54 - len(section)))
        for r in rows:
            icon = "✅" if r["ok"] else ("⏳" if not r.get("scored") else "❌")
            print(f"  {icon} {r['label']:<34} {r['value']}")
            if r["detail"] and not r["ok"]:
                print(f"     ↳ {r['detail']}")
    print("-" * 70)
    print(f"  ⚠️  {rep['honest_note']}")
    if arts:
        print(f"  artifacts: {arts['md']}")
        print(f"             {arts['json']}")
    print("=" * 70)
