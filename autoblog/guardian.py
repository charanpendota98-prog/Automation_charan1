# -*- coding: utf-8 -*-
"""v60: SITE GUARDIAN — "eppatiki advanced ga, best ga" automatic keeper.

Enti idi:
  Roju okkasari (GUARDIAN_HOUR tarvata) bot motham system ni check chestundi —
  site files · tiles/counts sync (jaari poyaya?) · menu/first-look UI blocks ·
  robots/sitemap/ads.txt · breaking feed freshness · ad inventory validity ·
  keyword/pillar lock · storage · .env readiness. Edaina padipoyindi/desynca
  aithe: Telegram alert + logs/guardian.json lo status + exact fix line.

Enduku idi:
  "Chala advanced ga untu undali" ante manual ga gurthupettukovadam kaadu —
  guard raatiki okkasari chusi, problem unte cheppali. Silent ga jarigipoye
  regressions (tile number tappu, menu item poyindi, feed aagipoyindi,
  ads.txt poyindi) ivi roju teliyali.

Nijam: idi READ-ONLY audit (fix cheyyadu) — self-heal kaadu. Repairs tests +
builder nunchi vasthai; guard matrame cheptundi, mee approva tho fix avutundi.
"""
from __future__ import annotations

import json
import logging
import os
import re
import shutil
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable, Dict, List, Optional

from . import config

log = logging.getLogger("autoblog.guardian")

IST = timezone(timedelta(hours=5, minutes=30))
ROOT = Path(__file__).resolve().parent.parent
PREVIEW = ROOT / "preview"
STATE_FILE = ROOT / "logs" / "guardian.json"

# Tile regexes — site (preview/index.html) nunchi live numbers teesukuntayi
TILE_RE = re.compile(r'<div class="qtile"><b>([^<]+)</b>')
UI_BLOCKS = [
    ('id="tickerwrap"', "బ్రేకింగ్ టికర్"),
    ('class="usedwrap"', "విద్యార్థులు ఎక్కువగా వెతికేవి"),
    ('id="brklist"', "బ్రేకింగ్ న్యూస్ section"),
    ("fetch(\"data/breaking.json\"", "feed fetch"),
    ('class="navbrk"', "menu బ్రేకింగ్ లింక్"),
]


def _now() -> datetime:
    return datetime.now(IST)


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def _status_file(path: Path = None) -> Path:
    return Path(path or getattr(config, "GUARDIAN_STATE", STATE_FILE))


# ---------------------------------------------------------------------------
# individual checks — each returns (ok: bool, detail: str, fix: str)
# ---------------------------------------------------------------------------

def check_site_files() -> tuple:
    need = ["index.html", "robots.txt", "sitemap.xml", "favicon.svg", "ads.txt",
            "pages/about.html", "pages/contact.html", "pages/privacy.html",
            "pages/disclaimer.html", "pages/editorial-policy.html",
            "pages/advertise.html", "data/breaking.json"]
    missing = [f for f in need if not (PREVIEW / f).exists()]
    if missing:
        return False, "missing: " + ", ".join(missing), "python tools/build_policy_pages.py"
    return True, f"{len(need)} files ready", ""


def check_first_look_ui() -> tuple:
    html = _read(PREVIEW / "index.html")
    if not html:
        return False, "index.html chadavalekapoyindi", "preview/index.html check cheyandi"
    gone = [label for needle, label in UI_BLOCKS if needle not in html]
    if gone:
        return False, "poyayi: " + ", ".join(gone), "v59 first-look blocks malli add cheyandi (git log v59)"
    order_ok = html.index('id="tickerwrap"') < html.index('class="usedwrap"') < html.index('class="hero"')
    if not order_ok:
        return False, "order marindi (ticker → used → hero kaadu)", "v59 order restore cheyandi"
    return True, "ticker → most-used → hero order intact", ""


def check_tiles_sync() -> tuple:
    """Site tiles ↔ test files + jsdom literal — desync ayithe high alert."""
    html = _read(PREVIEW / "index.html")
    tiles = TILE_RE.findall(html)
    if not tiles:
        return False, "tiles kanipinchaledu", "trust section tiles check cheyandi"
    frac = [t for t in tiles if re.fullmatch(r"(\d+)/\1", t)]
    suite_files = len(list((ROOT / "tests").glob("*_test.py")))
    jsdom = _read(ROOT / "tests" / "runtime" / "jsdom_runtime_test.js")
    m = re.search(r'trust proof tiles: (\d+)/(\d+) \+ 11/11 \+ (\d+)/(\d+)', jsdom)
    problems = []
    if f"{suite_files}/{suite_files}" not in frac:
        problems.append(f"suite tile {frac} lo {suite_files}/{suite_files} ledu (test files {suite_files})")
    runtime_note = ""
    if m:
        n = int(m.group(3))
        if f"{n}/{n}" not in frac:
            problems.append(f"jsdom {n}/{n} tile lo ledu (tiles: {frac})")
        runtime_note = f" · jsdom {n}/{n}"
    if problems:
        return False, "; ".join(problems), "tiles + jsdom okate change lo bump cheyandi (v58 nunchi rule)"
    return True, f"suites {suite_files}/{suite_files} · tiles {frac}{runtime_note}", ""


def check_robots_sitemap() -> tuple:
    robots = _read(PREVIEW / "robots.txt")
    sitemap = _read(PREVIEW / "sitemap.xml")
    probs = []
    for needle in ("Sitemap: https://studentup.in/sitemap.xml", "Disallow: /admin",
                   "/keyword-universe-top200.csv"):
        if needle not in robots:
            probs.append("robots: " + needle)
    if "<urlset" not in sitemap or "https://studentup.in/" not in sitemap:
        probs.append("sitemap invalid")
    if probs:
        return False, "; ".join(probs), "python tools/build_policy_pages.py"
    return True, f"robots {len(robots.splitlines())} lines · sitemap URLs ok", ""


def check_ads_txt() -> tuple:
    try:
        from . import adsense_kit

        status, detail = adsense_kit.ads_txt_status()
    except Exception as exc:  # noqa: BLE001
        return False, f"status check fail: {exc}", "autoblog/adsense_kit.py check cheyandi"
    if status in ("live", "placeholder"):
        return True, f"{status} — {detail[:70]}", ""
    return False, f"{status} — {detail[:70]}", "python tools/build_policy_pages.py"


def check_breaking_feed(max_age_hours: float = None) -> tuple:
    max_age = float(max_age_hours or getattr(config, "GUARDIAN_FEED_MAX_AGE", 26))
    try:
        from . import breaking

        data = breaking.read_feed()
    except Exception as exc:  # noqa: BLE001
        return False, f"feed read fail: {exc}", "python run.py --breaking-feed"
    if not data.get("updated"):
        return False, "feed inka generate avvaledu", "python run.py --breaking-feed"
    try:
        when = datetime.fromisoformat(data["updated"])
    except ValueError:
        return False, f"updated timestamp tappu: {data['updated']}", "python run.py --breaking-feed"
    age = (_now() - when).total_seconds() / 3600
    if age > max_age:
        return False, f"feed stale ({age:.1f}h > {max_age}h)", "python run.py --breaking-feed (radar cron check)"
    return True, f"{data.get('count', 0)} items · {age:.1f}h mundu update", ""


def check_ads_inventory() -> tuple:
    probs, total = [], 0
    for name in ("inventory.json", "house.json"):
        path = ROOT / "ads" / name
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001
            probs.append(f"{name}: {type(exc).__name__}")
            continue
        rows = data if isinstance(data, list) else data.get("ads", data.get("items", []))
        for ad in rows or []:
            total += 1
            link = str(ad.get("link", ""))
            if link and not link.startswith("http"):
                probs.append(f"{name}:{ad.get('id', '?')} link http kaadu")
    if probs:
        return False, "; ".join(probs[:4]), "ads/*.json lo link/title/id check cheyandi"
    return True, f"{total} active ads valid", ""


def check_keyword_pillar_lock() -> tuple:
    """Counts lock: 17 pillars · 203 entities · 11,192 kws · 143 sources."""
    try:
        from . import sources_grid, top_post

        cats = len(config.CATEGORIES)
        ents = len(top_post.ENTITIES)
        uni = len(top_post.keyword_universe())
        src = len(sources_grid.SOURCES_GRID)
        daily = len([s for s in sources_grid.SOURCES_GRID if s.get("daily")])
    except Exception as exc:  # noqa: BLE001
        return False, f"engine check fail: {exc}", "autoblog modules import check"
    want = (17, 203, 11_192, 143)
    got = (cats, ents, uni, src)
    if got != want:
        return False, f"counts marayi: {got} (expected {want})", "pillar/keyword counts sync cheyandi (v58/v59 docs)"
    return True, f"{cats} pillars · {ents} entities · {uni:,} kws · {src} sources ({daily} daily)", ""


def check_menu_wiring() -> tuple:
    html = _read(PREVIEW / "index.html")
    want = ["ts-jobs", "ap-jobs", "hallticket", "results", "walkin", "software"]
    probs = [c for c in want if f'data-goto-cat="{c}"' not in html]
    if probs:
        return False, "menu links poyayi: " + ", ".join(probs), "nav/mpanel markup check cheyandi"
    used = re.findall(r'<a class="usedcard[^"]*" href="#jobs" data-goto-cat="([a-z-]+)"', html)
    if len(used) != 8:
        return False, f"most-used tiles {len(used)} (8 undali)", "v59 used-strip restore cheyandi"
    return True, "menu + most-used 8 tiles intact", ""


def check_storage() -> tuple:
    total, used, free = shutil.disk_usage(str(ROOT))
    free_gb = free / 1024 ** 3
    db = ROOT / "state.db"
    db_kb = db.stat().st_size / 1024 if db.exists() else 0
    out = ROOT / "output"
    out_mb = sum(f.stat().st_size for f in out.rglob("*") if f.is_file()) / 1024 ** 2 if out.exists() else 0
    if free_gb < 0.5:
        return False, f"disk chala thakkuva: {free_gb:.2f} GB free", "python tools/prune_media.py --apply"
    detail = f"{free_gb:.1f} GB free · state.db {db_kb:.0f} KB · output {out_mb:.1f} MB"
    if out_mb > 200:
        return False, detail + " (output peddaga undi)", "python tools/prune_media.py --apply"
    return True, detail, ""


def check_wp_theme() -> tuple:
    """Real site theme (v61) — files + zip fresh (source marchi zip rebuild cheyyakapote)."""
    theme = ROOT / "wordpress-theme" / "studentup"
    zip_path = ROOT / "wordpress-theme" / "studentup-theme.zip"
    if not theme.exists():
        return False, "theme folder ledu (wordpress-theme/studentup)", "git pull / theme restore"
    if not zip_path.exists():
        return False, "theme zip ledu", "python tools/build_wp_theme.py"
    srcs = [p for p in theme.rglob("*") if p.is_file()]
    newest = max(p.stat().st_mtime for p in srcs)
    if zip_path.stat().st_mtime < newest:
        return False, "zip stale — source kante paata (WP upload lo puratana theme veltundi)", \
            "python tools/build_wp_theme.py"
    phps = len(list(theme.rglob("*.php")))
    return True, f"theme zip fresh · {phps} PHP · {len(srcs)} files", ""


def check_env_readiness() -> tuple:
    """Warn-only: mee .env lo em set cheyyali (deploy gate)."""
    have = []
    miss = []
    for flag, label in ((config.GEMINI_API_KEY or getattr(config, "GEMINI_API_KEYS", []), "Gemini"),
                        (config.WP_APP_PASSWORD, "WP creds"),
                        (config.TELEGRAM_BOT_TOKEN, "Telegram")):
        (have if flag else miss).append(label)
    if miss:
        return False, "set avvaledu: " + ", ".join(miss) + f" (set: {', '.join(have) or '—'})", \
            ".env lo owner creds pettandi (GO_LIVE_CHECKLIST.md PART A)"
    return True, "Gemini · WP · Telegram anni set", ""


# (id, fn, warn_only) — warn_only = mee pani (owner creds), system break kaadu
CHECKS: List[tuple] = [
    ("site_files", check_site_files, False),
    ("first_look_ui", check_first_look_ui, False),
    ("tiles_sync", check_tiles_sync, False),
    ("robots_sitemap", check_robots_sitemap, False),
    ("ads_txt", check_ads_txt, False),
    ("breaking_feed", check_breaking_feed, False),
    ("ads_inventory", check_ads_inventory, False),
    ("keyword_pillar_lock", check_keyword_pillar_lock, False),
    ("menu_wiring", check_menu_wiring, False),
    ("storage", check_storage, False),
    ("wp_theme", check_wp_theme, False),
    ("env_readiness", check_env_readiness, True),
]


# ---------------------------------------------------------------------------
# runner
# ---------------------------------------------------------------------------

def run_checks() -> dict:
    results = []
    for name, fn, warn_only in CHECKS:
        t0 = time.time()
        try:
            ok, detail, fix = fn()
        except Exception as exc:  # noqa: BLE001
            ok, detail, fix = False, f"{type(exc).__name__}: {exc}", "manual check"
        results.append({"id": name, "ok": bool(ok), "warn_only": bool(warn_only),
                        "detail": str(detail)[:220], "fix": str(fix),
                        "ms": int((time.time() - t0) * 1000)})
    fails = [r for r in results if not r["ok"] and not r["warn_only"]]
    warns = [r for r in results if not r["ok"] and r["warn_only"]]
    return {"checked": len(results), "passed": len(results) - len(fails) - len(warns),
            "failed": len(fails), "warned": len(warns), "results": results,
            "at": _now().replace(microsecond=0).isoformat(),
            "ok": not fails}


def write_status(summary: dict, path: Path = None) -> Path:
    target = _status_file(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = dict(summary)
    history: list = []
    try:
        old = json.loads(target.read_text(encoding="utf-8"))
        history = list(old.get("history", []))[-13:]
    except Exception:  # noqa: BLE001
        history = []
    history.append({"at": summary["at"], "passed": summary["passed"],
                    "failed": summary["failed"], "warned": summary.get("warned", 0)})
    payload["history"] = history
    tmp = target.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, target)
    return target


def summary_text(summary: dict, telegram: bool = False) -> str:
    """Print + Telegram ki okate summary (rendu chotla ade maatalu)."""
    if telegram:
        head = (f"🛡 <b>SITE GUARDIAN</b> — {summary['passed']}/{summary['checked']} OK"
                f"{' ✅' if summary.get('ok') else ' ⚠️'}")
        lines = [head, f"<i>{summary['at']}</i>"]
        for r in summary["results"]:
            icon = "✅" if r["ok"] else ("⚠️" if r.get("warn_only") else "❌")
            lines.append(f"{icon} <b>{r['id']}</b>: {r['detail']}")
        for r in [x for x in summary["results"] if not x["ok"]]:
            lines.append(f"↳ fix: <code>{r['fix']}</code>")
        return "\n".join(lines)
    out = [f"  {summary['passed']}/{summary['checked']} checks OK · "
           f"{summary['warned']} owner-pending"
           f"{' ✅' if summary.get('ok') else ' ⚠️'}"]
    for r in summary["results"]:
        icon = "✅" if r["ok"] else ("⚠️" if r.get("warn_only") else "❌")
        out.append(f"  {icon} {r['id']:<20} {r['detail']}")
    for r in [x for x in summary["results"] if not x["ok"]]:
        out.append(f"     ↳ fix: {r['fix']}")
    return "\n".join(out)


def guard(notify: bool = False, print_out: bool = True) -> dict:
    summary = run_checks()
    path = write_status(summary)
    if print_out:
        print("=" * 66)
        print("  🛡 SITE GUARDIAN — system motham roju okkasari check (v60)")
        print("=" * 66)
        print(summary_text(summary))
        print(f"  status: {path}")
        print("=" * 66)
    if notify:
        try:
            from . import notifier

            notifier.send_telegram(summary_text(summary, telegram=True))
        except Exception:  # noqa: BLE001
            log.exception("guardian notify fail (non-fatal)")
    return summary
