# -*- coding: utf-8 -*-
"""AdSense APPROVAL READINESS audit — pre-application gate.

Enduku: "posts publish cheste AdSense approval ki problem leda?" — ee prashna ki
okka chota, nijamaina jawabu kavali. Ee module Google AdSense approve cheyye
**mundu** veetini check chestundi (Google's own published policy areas):

  1. Policy pages (Privacy · About · Contact · Disclaimer · Editorial) + footer links
  2. Content depth (thin content = #1 rejection reason) + volume (enough posts)
  3. Originality (copied/scraped content = rejection)
  4. Navigation clarity (readers + crawlers content ni easy ga reach avvali)
  5. Technical (HTTPS · robots · sitemap · mobile viewport · no placeholder pages)
  6. Trust surface (author/E-E-A-T box · corrections email · contact route)
  7. Ad safety (density cap · SPONSORED labelling · consent/CMP for EEA)
  8. Prohibited-content scan (adult · hate · hack/crack · misleading claims)

**Honesty rule (important):** AdSense approval, ranking mariyu revenue **Google +
mee account + time** batti untayi. Ee audit kevalam "ee technical/content
requirements loki nenu ready ga unnanu" ani cheptundi — guarantee ivvadu.
Anduke prathi row lo `fix` line undi, mariyu verdict lo "Google decides" ani
explicit ga untundi.

Run: python run.py --adsense-ready
     (audit only — ide module ni tests kuda vaadutayi)
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import List, Tuple

from . import config

ROOT = Path(config.BASE_DIR)
PREVIEW = ROOT / "preview"
THEME = ROOT / "wordpress-theme" / "studentup"
PAGES = PREVIEW / "pages"

# Google's guidance: apply once the site has a solid base of substantive pages.
MIN_POSTS_RECOMMENDED = 20
MIN_WORDS_RECOMMENDED = 900


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:  # noqa: BLE001
        return ""


def _row(rows: List[dict], group: str, cid: str, ok: bool, detail: str,
         fix: str = "", warn_only: bool = False) -> None:
    rows.append({
        "group": group, "id": cid, "ok": bool(ok),
        "warn_only": bool(warn_only), "detail": detail, "fix": "" if ok else fix,
    })


# --------------------------------------------------------------------------- 1
def _check_policy_pages(rows: List[dict]) -> None:
    """AdSense ki Privacy Policy mandatory; About/Contact trust ki kavali."""
    required = {
        "privacy": "Privacy policy (AdSense ki MANDATORY)",
        "about": "About / editorial team (E-E-A-T)",
        "contact": "Contact (readers reach avvali)",
    }
    recommended = {
        "disclaimer": "Disclaimer (exam/job info accuracy)",
        "editorial-policy": "Editorial policy (how we verify)",
    }
    for slug, label in required.items():
        p = PAGES / f"{slug}.html"
        ok = p.exists() and len(_read(p)) > 1200
        _row(rows, "POLICY", f"page_{slug}", ok,
             f"{label}: {'built (' + str(len(_read(p)) // 1024) + ' KB)' if ok else 'ledu/thin'}",
             "python tools/build_policy_pages.py")
    for slug, label in recommended.items():
        p = PAGES / f"{slug}.html"
        ok = p.exists() and len(_read(p)) > 800
        _row(rows, "POLICY", f"page_{slug}", ok, f"{label}: {'built' if ok else 'ledu'}",
             "python tools/build_policy_pages.py", warn_only=True)
    # Privacy policy lo Google/third-party ads disclosure undali (AdSense rule)
    priv = _read(PAGES / "privacy.html").lower()
    # NOTE: ee checks lo "synonyms" **any-of** ga chudali (all-of kaadu) — okkati
    # unte chaalu, enduku ante okkate correct wording (adi nijamga jarigina bug).
    need = {
        "google ads dat": (["google"], ["ad", "adsense"]),
        "cookies": (["cookie"], []),
        "third-party vendors": (["third-party vendor", "third party vendor",
                                "third-party vendors", "third party vendors"], []),
        "opt-out link": (["opt out", "opt-out"], ["settings/google", "adsettings",
                                                   "google.com/settings", "aboutads"]),
    }
    for label, (any_of, also_any) in need.items():
        ok = any(n in priv for n in any_of) and (not also_any or any(n in priv for n in also_any))
        _row(rows, "POLICY", "privacy_" + label.replace(" ", "_"), ok,
             f"privacy lo {label}: {'undi' if ok else 'LEDU'}",
             "privacy policy lo Google/third-party vendors + cookies + opt-out link add cheyandi")
    # footer lo policy links (readers + Google crawl)
    footer = _read(THEME / "footer.php")
    linked = sum(1 for s in ("privacy", "about", "contact", "disclaimer") if s in footer.lower())
    _row(rows, "POLICY", "footer_links", linked >= 2,
         f"footer lo policy links: {linked}",
         "footer.php lo privacy/about/contact/disclaimer links pettandi", warn_only=True)


# --------------------------------------------------------------------------- 2
def _published_count() -> Tuple[int, bool]:
    """state.db lo publish ayyina posts (live site lo nijamaina content count).

    Returns (count, ok). `ok=False` ante DB read fail ayyindi — aa case lo count ni
    "0" ani cheppi, audit ni "volume fail" ani chupinchadam **tappu** (silent fail).
    Anduke caller ee flag ni chusi "count teleedu" ani cheptundi.

    NOTE: config attribute `STATE_PATH` (config.DB_PATH ledu — v68 code-audit E1
    rule idi pattukundi; mundu try/except silent ga 0 return cheyyadam valla
    audit lo kanipinchaledu).
    """
    try:
        from . import state

        db = Path(getattr(config, "STATE_PATH", ROOT / "state.db"))
        with state._connect(db) as conn:  # noqa: SLF001
            row = conn.execute(
                "SELECT COUNT(*) FROM posts WHERE status = 'publish'"
            ).fetchone()
            return (int(row[0]) if row else 0), True
    except Exception:  # noqa: BLE001 — DB fail = score kaadu, report lo cheptamu
        return 0, False


def _check_content(rows: List[dict]) -> None:
    """Thin content + low volume = AdSense rejection lo #1 reason."""
    n, db_ok = _published_count()
    _row(rows, "CONTENT", "volume", n >= MIN_POSTS_RECOMMENDED,
         (f"published posts: {n} (recommended ≥{MIN_POSTS_RECOMMENDED})" if db_ok
          else "published posts: count teleedu (state.db read fail)"),
         "roju posts publish cheyandi (radar + top-post engine) — 20+ substantive posts tarvata apply cheyandi"
         if db_ok else "python run.py --status (state.db check)")
    # depth gate config
    depth_ok = False
    gate = _read(ROOT / "autoblog" / "post_gate.py")
    m = re.search(r"words\s*>=\s*(\d+)", gate)
    if m:
        depth_ok = int(m.group(1)) >= MIN_WORDS_RECOMMENDED
    _row(rows, "CONTENT", "depth_gate", depth_ok,
         f"writing gate min words: {m.group(1) if m else '?'} (recommended ≥{MIN_WORDS_RECOMMENDED})",
         "post_gate.py lo word floor penchandi")
    # originality gate
    orig = _read(ROOT / "autoblog" / "config.py")
    mo = re.search(r"(?:PUBLISH_)?ORIGINALITY_MIN\s*=\s*float\([^)]*?([0-9.]+)['\"]?\s*\)", orig)
    if not mo:
        mo = re.search(r"(?:PUBLISH_)?ORIGINALITY_MIN\s*=\s*([0-9.]+)", orig)
    val = float(mo.group(1)) if mo else 0.0
    _row(rows, "CONTENT", "originality", val >= 70.0,
         f"originality floor: {val:.0f}% (recommended ≥70%)",
         "ORIGINALITY_MIN ni 70+ ki penchandi (copied content = rejection)")
    # human review + QA gate
    _row(rows, "CONTENT", "qa_gate", "QA_MIN" in orig or "qa" in gate.lower(),
         "live QA gate (publish ki quality floor) undi",
         "QA gate add cheyandi")


# --------------------------------------------------------------------------- 3
def _check_navigation(rows: List[dict]) -> None:
    """Navigation clear ga lekapote Google 'low value' ga chudochu."""
    tpl = _read(THEME / "inc" / "template.php")
    _row(rows, "NAVIGATION", "menu", "studentup_menu_fallback" in tpl,
         "primary menu (fallback kuda) undi", "menu fallback add cheyandi")
    _row(rows, "NAVIGATION", "menu_grouped",
         "menu-item-has-children" in tpl and "sub-menu" in tpl,
         "menu grouped dropdowns (clean, 1-line)",
         "menu ni grouped cheyandi (v93 fix)")
    # breadcrumbs + search help discovery
    _row(rows, "NAVIGATION", "breadcrumbs", "studentup_breadcrumbs" in tpl,
         "breadcrumbs undi (users + crawlers)", "breadcrumbs add cheyandi")
    hdr = _read(THEME / "header.php")
    _row(rows, "NAVIGATION", "search", 'type="search"' in hdr or "searchform" in hdr,
         "site search undi", "search pettandi")
    # category coverage
    cats = len(re.findall(r"'slug' => '([a-z-]+)'", _read(THEME / "functions.php")))
    _row(rows, "NAVIGATION", "categories", cats >= 5,
         f"category sections: {cats}", "categories add cheyandi")


# --------------------------------------------------------------------------- 4
def _check_technical(rows: List[dict]) -> None:
    """HTTPS · robots · sitemap · mobile viewport · no placeholder pages."""
    robots = _read(PREVIEW / "robots.txt")
    _row(rows, "TECHNICAL", "robots",
         "Sitemap:" in robots and "Disallow: /admin" in robots,
         "robots.txt: sitemap + admin block",
         "python tools/build_policy_pages.py")
    sm = _read(PREVIEW / "sitemap.xml")
    urls = sm.count("<loc>")
    _row(rows, "TECHNICAL", "sitemap", "<urlset" in sm and urls >= 5,
         f"sitemap.xml: {urls} URLs", "sitemap build cheyandi")
    hdr = _read(THEME / "header.php")
    _row(rows, "TECHNICAL", "viewport", "width=device-width" in hdr,
         "mobile viewport meta undi", "viewport meta add cheyandi")
    sec = _read(THEME / "inc" / "security.php")
    _row(rows, "TECHNICAL", "https_headers",
         "X-Content-Type-Options" in sec and "Referrer-Policy" in sec,
         "security headers (nosniff · referrer · frame)",
         "security headers add cheyandi", warn_only=True)
    # placeholder / "under construction" text eppudu public lo undakoodadu
    bad = []
    for f in PREVIEW.rglob("*.html"):
        t = _read(f).lower()
        for needle in ("lorem ipsum", "under construction", "coming soon page", "demo site"):
            if needle in t:
                bad.append(f"{f.name}:{needle}")
    _row(rows, "TECHNICAL", "no_placeholders", not bad,
         "placeholder/under-construction text ledu" if not bad else "; ".join(bad[:3]),
         "placeholder text teeseyandi")


# --------------------------------------------------------------------------- 5
def _check_trust(rows: List[dict]) -> None:
    """AdSense 'valuable inventory' + E-E-A-T signals."""
    _row(rows, "TRUST", "author_box", (THEME / "inc" / "author-box.php").exists(),
         "author/E-E-A-T box undi", "author box add cheyandi")
    single = _read(THEME / "single.php")
    _row(rows, "TRUST", "trust_note", "studentup_trust_note" in single,
         "post kindha verification/trust note undi",
         "trust note add cheyandi")
    tpl = _read(THEME / "inc" / "template.php")
    _row(rows, "TRUST", "corrections",
         "correct it within" in tpl or "corrections" in tpl.lower(),
         "corrections contact line undi", "corrections line add cheyandi", warn_only=True)
    _row(rows, "TRUST", "sources", "studentup_source" in tpl or "su-source" in _read(THEME / "style.css"),
         "source/citation block undi", "source block add cheyandi", warn_only=True)


# --------------------------------------------------------------------------- 6
def _check_ads_safety(rows: List[dict]) -> None:
    """Ad policy safety — approval ayyaka ban avvakunda."""
    ads = _read(THEME / "inc" / "ads.php")
    _row(rows, "AD SAFETY", "sponsored", "SPONSORED" in ads,
         "SPONSORED labelling undi (house ads)", "SPONSORED label add cheyandi")
    maxads = 0
    opts = _read(THEME / "inc" / "options.php")
    m = re.search(r"'max_ads'.*?'(\d+)'", opts, re.S)
    if m:
        maxads = int(m.group(1))
    _row(rows, "AD SAFETY", "density", 0 < maxads <= 5,
         f"ad density cap: {maxads or '?'} per page (≤5 safe)",
         "density cap 3–5 madhya pettandi")
    _row(rows, "AD SAFETY", "cls", "min-height" in ads or "su-ad-lazy" in _read(THEME / "style.css"),
         "ads CLS-safe (reserved space)", "ad wrapper ki reserved height pettandi")
    _row(rows, "AD SAFETY", "consent", (THEME / "inc" / "consent.php").exists(),
         "consent mode module undi (EEA/UK)", "consent module add cheyandi", warn_only=True)
    _row(rows, "AD SAFETY", "policy_pages_no_ads",
         "'ads_on_policy'" in opts,
         "legal pages ki ads OFF option undi (AdSense policy)",
         "policy pages ad toggle add cheyandi")


# --------------------------------------------------------------------------- 7
def _check_prohibited(rows: List[dict]) -> None:
    """Prohibited content scan — generated drafts + templates lo."""
    patterns = {
        # NOTE: bare "xxx" vaadakoodadu — `ca-pub-xxx` lanti placeholders false
        # positive isthayi (ee audit lo adi nijamga jarigindi). Specific terms matrame.
        "adult": r"\b(porn|adult video|escort service|nsfw)\b",
        "hacking": r"\b(crack|keygen|hacked apk|mod apk)\b",
        "misleading": r"\b(guaranteed job|100% job guarantee|get job instantly)\b",
        "gambling": r"\b(betting|casino|satta|rummy real money)\b",
    }
    hits: List[str] = []
    scan_dirs = [ROOT / "output", THEME]
    for d in scan_dirs:
        if not d.exists():
            continue
        for f in d.rglob("*"):
            if not f.is_file() or f.suffix.lower() not in (".html", ".php", ".json", ".md"):
                continue
            t = _read(f).lower()
            for name, pat in patterns.items():
                if re.search(pat, t):
                    hits.append(f"{name}@{f.name}")
    _row(rows, "PROHIBITED", "scan", not hits,
         "prohibited-content scan clean" if not hits else "; ".join(sorted(set(hits))[:4]),
         "aa content teeseyandi (AdSense ban risk)")


# --------------------------------------------------------------------------- 8
def _check_discover(rows: List[dict]) -> None:
    """Google Discover / News eligibility (large image + freshness signals)."""
    # NOTE: ee check theme antha scan cheyyali — `functions.php` mattrame kaadu.
    # (v94 lo add_image_size `inc/discover.php` ki move ayyindi; check aa file ni
    # miss chesthe "LEDU" ani tappu ga cheppedi — adi nijamga jarigina bug.)
    theme_php = "".join(_read(p) for p in THEME.rglob("*.php"))
    sizes = re.findall(r"add_image_size\(\s*'([\w-]+)',\s*(\d+),\s*(\d+)", theme_php)
    big = [s for s in sizes if int(s[1]) >= 1200]
    _row(rows, "DISCOVER", "image_size", bool(big),
         f"≥1200px image size: {big[0][0] + ' (' + big[0][1] + 'px)' if big else 'LEDU'} (Discover large card)",
         "add_image_size( 'studentup-discover', 1200, 675, true ) add cheyandi")
    _row(rows, "DISCOVER", "og_dims",
         "og:image:width" in theme_php and "og:image:height" in theme_php,
         "og:image width/height tags", "og:image:width/height emit cheyandi", warn_only=True)
    _row(rows, "DISCOVER", "news_sitemap", (THEME / "inc" / "news-sitemap.php").exists(),
         "news sitemap module undi", "news sitemap add cheyandi", warn_only=True)
    _row(rows, "DISCOVER", "max_preview",
         "max-image-preview" in _read(ROOT / "autoblog" / "seo.py")
         or "max-image-preview" in theme_php,
         "max-image-preview:large robots directive",
         "rank_math_robots lo max-image-preview:large pettandi")


# ---------------------------------------------------------------------------
def audit() -> Tuple[dict, List[dict]]:
    """Anni groups run chesi (summary, rows) return chestundi."""
    rows: List[dict] = []
    _check_policy_pages(rows)
    _check_content(rows)
    _check_navigation(rows)
    _check_technical(rows)
    _check_trust(rows)
    _check_ads_safety(rows)
    _check_prohibited(rows)
    _check_discover(rows)

    hard = [r for r in rows if not r["warn_only"]]
    passed = [r for r in hard if r["ok"]]
    blockers = [r for r in hard if not r["ok"]]
    warns = [r for r in rows if r["warn_only"] and not r["ok"]]
    score = round(len(passed) / len(hard) * 100) if hard else 0

    if blockers:
        verdict = "NOT READY"
        line = f"{len(blockers)} blocker(s) — ivi fix cheyyakunda apply cheyyakandi"
    elif warns:
        verdict = "READY (warnings tho)"
        line = "Mandatory items OK — warning items kuda set cheste better"
    else:
        verdict = "READY"
        line = "Anni technical/content requirements OK"

    _posts, _db_ok = _published_count()
    summary = {
        "score": score,
        "posts_db_ok": _db_ok,
        "verdict": verdict,
        "line": line,
        "passed": len(passed),
        "total": len(hard),
        "blockers": [{"id": r["id"], "detail": r["detail"], "fix": r["fix"]} for r in blockers],
        "warnings": [{"id": r["id"], "detail": r["detail"], "fix": r["fix"]} for r in warns],
        "posts": _posts,
        "posts_recommended": MIN_POSTS_RECOMMENDED,
    }
    return summary, rows


def report_path() -> Path:
    return ROOT / "output" / "adsense-ready.json"


def run(write: bool = True) -> int:
    """CLI entry — print report + JSON artifact rasi exit code istundi."""
    summary, rows = audit()
    print("=" * 72)
    print("  💰 ADSENSE APPROVAL READINESS (pre-application gate)")
    print("=" * 72)
    group = ""
    for r in rows:
        if r["group"] != group:
            group = r["group"]
            print(f"  ── {group} " + "─" * max(0, 60 - len(group)))
        if r["ok"]:
            icon = "✅"
        elif r["warn_only"]:
            icon = "⚠️ "
        else:
            icon = "⛔"
        print(f"  {icon} {r['id']:26s} {r['detail'][:78]}")
        if not r["ok"] and r["fix"]:
            print(f"      ↳ {r['fix'][:100]}")
    print("-" * 72)
    print(f"  Score: {summary['score']}% ({summary['passed']}/{summary['total']} mandatory)"
          f" · verdict: {summary['verdict']}")
    print(f"  {summary['line']}")
    print(f"  Posts: {summary['posts']} published (recommended ≥{summary['posts_recommended']} "
          "substantive posts before applying)")
    print()
    print("  ℹ️  HONEST LIMIT: AdSense approval, ad serving, ranking mariyu revenue")
    print("     Google + mee account + time batti untayi. Ee audit kevalam technical/")
    print("     content requirements ready aa leda ani cheptundi — approval guarantee ledu.")
    if write:
        try:
            report_path().parent.mkdir(parents=True, exist_ok=True)
            report_path().write_text(
                json.dumps({"summary": summary, "rows": rows}, indent=2, ensure_ascii=False),
                encoding="utf-8")
            print(f"  artifact: {report_path()}")
        except Exception as exc:  # noqa: BLE001
            print(f"  (artifact write skip: {exc})")
    return 0 if summary["verdict"] != "NOT READY" else 1
