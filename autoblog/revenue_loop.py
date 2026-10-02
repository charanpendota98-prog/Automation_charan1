# -*- coding: utf-8 -*-
"""v182 — REVENUE LOOP: AdSense page data → content + slot strategy.

`--rpm-report` (v151) cheptundi "ye page entha earn chestondo".
`--slot-lab` (v162) cheptundi "ye ad unit variant better".
Ee module aa rendu **nunchi strategy** teestundi:

  1. **Category RPM** — mee 18 categories lo ye vi per-1000-views ekkuva isthunnayi.
     → calendar aa categories ki priority isthundi (`revenue-insights.json`).
  2. **Money pages** — high RPM × high impressions (ivi protect cheyyali:
     internal links, freshness, hub links).
  3. **Revenue leaks** — impressions baaga unnayi kaani RPM site average kanna
     takkuva → aa pages ki slots/interlinks/publish-date fix cheyyali.
  4. **High-RPM topic tokens** — top-earning pages lo common words (e.g. "salary",
     "bank", "software") → kotha content lo aa angle add cheyyali.

Data source: AdSense → Reports → **Pages** export (CSV) leda GA4 page report.
**Emi guess cheyyadu:** sample chinna ga unte (min impressions) report "inka data
saripodhu" ani cheptundi; ee module ads code ni / WordPress ni touch cheyyadu.

CLI:
    python run.py --revenue-loop adsense-pages.csv [--revenue-notify]
"""
from __future__ import annotations

import csv
import json
import logging
import re
from datetime import datetime
from pathlib import Path
from statistics import median
from typing import Dict, List, Optional
from urllib.parse import urlsplit

from . import config

log = logging.getLogger("autoblog.revenue_loop")

_TOKEN = re.compile(r"[a-z]{4,}")
_STOP = {"https", "www", "studentup", "com", "html", "php", "the", "and", "for",
         "with", "from", "this", "that", "2026", "2025", "post", "page"}


def _num(v) -> float:
    raw = str(v or "").strip().replace(",", "").replace("₹", "").replace("$", "")
    raw = raw.replace("%", "")
    try:
        return float(raw)
    except ValueError:
        return 0.0


def _header(v: str) -> str:
    return re.sub(r"[^a-z]", "", (v or "").strip().lower())


def _slug(url: str) -> str:
    try:
        path = urlsplit(url).path
    except ValueError:
        path = url
    parts = [p for p in path.split("/") if p]
    return parts[-1].lower() if parts else ""


def parse_csv(path: str) -> List[Dict]:
    """AdSense/GA Pages CSV → rows (flexible header names, honest parsing)."""
    p = Path(path)
    with p.open(newline="", encoding="utf-8-sig", errors="replace") as fh:
        rows = list(csv.reader(fh))
    if not rows:
        raise ValueError("empty CSV")
    hdr = [_header(x) for x in rows[0]]

    def find(*names):
        for i, h in enumerate(hdr):
            if h in names:
                return i
        return None

    page_i = find("page", "pages", "url", "topages", "toppages", "landingpage")
    rpm_i = find("pagerpm", "rpm", "pagerevenueper1000impressions", "rpmpage")
    impr_i = find("impressions", "pageviews", "views", "adimpressions")
    earn_i = find("estimatedearnings", "earnings", "revenue", "totalrevenue")
    click_i = find("clicks", "adclicks")
    if page_i is None or (rpm_i is None and earn_i is None):
        raise ValueError("CSV lo 'Page' + ('Page RPM' leda 'Estimated earnings') "
                         "columns kavali (AdSense → Reports → Pages → Export)")
    out = []
    for row in rows[1:]:
        if len(row) <= page_i:
            continue
        url = (row[page_i] or "").strip()
        if not url:
            continue
        views = _num(row[impr_i]) if impr_i is not None and len(row) > impr_i else 0.0
        earn = _num(row[earn_i]) if earn_i is not None and len(row) > earn_i else 0.0
        rpm = _num(row[rpm_i]) if rpm_i is not None and len(row) > rpm_i else 0.0
        if rpm <= 0 and views > 0 and earn > 0:
            rpm = earn / views * 1000.0
        if views <= 0 and rpm <= 0:
            continue
        out.append({"url": url, "slug": _slug(url), "views": int(views),
                    "earnings": round(earn, 2), "rpm": round(rpm, 2),
                    "clicks": int(_num(row[click_i])) if click_i is not None
                             and len(row) > click_i else 0})
    if not out:
        raise ValueError("usable rows levu")
    return out


def classify_category(slug: str) -> str:
    """Slug → mee live categories. Mundu bot classifier (pipeline.classify_category),
    adi fail aithe token match — so revenue numbers content engine tho match avutayi."""
    text = slug.replace("-", " ")
    try:
        from . import pipeline as _pl

        cat = _pl.classify_category(text)
        if cat:
            return cat
    except Exception as exc:  # noqa: BLE001 — classifier unavailable
        log.debug("pipeline classifier unavailable: %s", exc)
    for cat in config.CATEGORIES:
        words = [w for w in cat.lower().split() if w not in ("jobs", "job")]
        if any(w in text for w in words):
            return cat
    return "Unclassified"


def analyze(rows: List[Dict], min_impressions: int = 50) -> Dict:
    """RPM by category/token + money pages + leaks + concentration."""
    total_views = sum(r["views"] for r in rows)
    total_earn = sum(r["earnings"] for r in rows)
    site_rpm = (total_earn / total_views * 1000.0) if total_views else 0.0
    ready = total_views >= min_impressions

    by_cat: Dict[str, Dict[str, float]] = {}
    tokens: Dict[str, Dict[str, float]] = {}
    for r in rows:
        cat = classify_category(r["slug"])
        c = by_cat.setdefault(cat, {"views": 0, "earnings": 0.0, "pages": 0})
        c["views"] += r["views"]
        c["earnings"] += r["earnings"]
        c["pages"] += 1
        for t in {w for w in _TOKEN.findall(r["slug"].replace("-", " ")) if w not in _STOP}:
            tk = tokens.setdefault(t, {"views": 0, "earnings": 0.0})
            tk["views"] += r["views"]
            tk["earnings"] += r["earnings"]
    cat_rpm = {k: round(v["earnings"] / v["views"] * 1000.0, 1)
               for k, v in by_cat.items() if v["views"] > 0}
    # high-RPM tokens: site RPM kanna 25%+ ekkuva + min 100 views
    high_tokens = {t: round(v["earnings"] / v["views"] * 1000.0, 1)
                   for t, v in tokens.items()
                   if v["views"] >= 100 and site_rpm > 0
                   and v["earnings"] / v["views"] * 1000.0 >= site_rpm * 1.25}
    top_n = max(1, int(len(rows) * 0.1))
    top_pages = sorted(rows, key=lambda r: r["earnings"], reverse=True)
    top_share = (sum(r["earnings"] for r in top_pages[:top_n]) / total_earn
                 if total_earn else 0.0)
    med_views = median([r["views"] for r in rows]) if rows else 0
    leaks = [r for r in rows
             if r["views"] >= max(min_impressions, med_views) and site_rpm > 0
             and r["rpm"] < site_rpm * 0.6]
    leaks.sort(key=lambda r: r["views"] * (site_rpm - r["rpm"]), reverse=True)
    # money pages = site RPM kanna ekkuva isthunna top earners (protect cheyyali)
    money = [r for r in rows if r["rpm"] >= site_rpm and r["views"] >= min_impressions]
    money.sort(key=lambda r: r["earnings"], reverse=True)
    return {
        "at": datetime.now().isoformat(timespec="seconds"),
        "pages": len(rows), "total_views": total_views,
        "total_earnings": round(total_earn, 2), "site_rpm": round(site_rpm, 2),
        "ready": ready, "min_impressions": min_impressions,
        "category_rpm": dict(sorted(cat_rpm.items(), key=lambda kv: kv[1], reverse=True)),
        "high_rpm_tokens": dict(sorted(high_tokens.items(), key=lambda kv: kv[1],
                                       reverse=True)[:25]),
        "top_share": round(top_share, 3),
        "money_pages": money[:15],
        "leaks": leaks[:15],
    }


def write_insights(rep: Dict, path: Optional[Path] = None) -> Path:
    path = Path(path or config.REVENUE_INSIGHTS_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    return path


def report_text(rep: Dict) -> str:
    lines = ["<b>💰 REVENUE LOOP (v182)</b>",
             f"pages {rep['pages']} · views {rep['total_views']:,} · "
             f"₹{rep['total_earnings']:,} · site RPM ₹{rep['site_rpm']}"]
    if not rep["ready"]:
        lines.append("⚠️ Inka sample chinna — numbers trend ki vadhu, "
                     "min impressions varaku wait cheyandi.")
    if rep["category_rpm"]:
        lines.append("<b>Category RPM (₹/1k views):</b>")
        for cat, rpm in list(rep["category_rpm"].items())[:6]:
            lines.append(f"  • {cat}: ₹{rpm}")
    if rep["high_rpm_tokens"]:
        top = list(rep["high_rpm_tokens"].items())[:6]
        lines.append("<b>High-RPM topics:</b> " + ", ".join(f"{t} ₹{v}" for t, v in top))
    if rep["money_pages"]:
        lines.append(f"<b>Money pages ({len(rep['money_pages'])})</b> — protect: "
                     "internal links + freshness.")
    if rep["leaks"]:
        lines.append(f"<b>Revenue leaks ({len(rep['leaks'])})</b> — views unnayi, "
                     "RPM takkuva: slots/interlinks fix.")
    lines.append("Note: strategy input matrame — ad code ni ee tool marchadu.")
    return "\n".join(lines)


# --------------------------------------------------------------------- CLI

def run_cli(csv_path: str = "", notify: bool = False,
            min_impressions: Optional[int] = None, top: int = 8) -> int:
    print("=" * 74)
    print("  💰 REVENUE LOOP (v182) — ad data → content + slot strategy")
    print("=" * 74)
    if not csv_path:
        print("  Usage: python run.py --revenue-loop adsense-pages.csv")
        print("  AdSense → Reports → Pages → Export CSV (Page, Page RPM, Impressions,")
        print("  Estimated earnings). GA4 page report kuda work avutundi.")
        return 1
    try:
        rows = parse_csv(csv_path)
    except (OSError, ValueError) as exc:
        print(f"  ❌ CSV: {exc}")
        return 1
    rep = analyze(rows, min_impressions=min_impressions or config.REVENUE_LOOP_MIN_IMPRESSIONS)
    path = write_insights(rep)
    print(f"  pages {rep['pages']} · views {rep['total_views']:,} · "
          f"₹{rep['total_earnings']:,} · site RPM ₹{rep['site_rpm']}")
    print(f"  top 10% pages revenue share: {rep['top_share'] * 100:.0f}%")
    if not rep["ready"]:
        print(f"  ⚠️  sample chinna (< {rep['min_impressions']} views) — trend ga "
              f"vadakandi; inka data ravali.")
    print("-" * 74)
    if rep["category_rpm"]:
        print("  📊 CATEGORY RPM (₹/1000 views) — calendar ee order follow avutundi:")
        for cat, rpm in list(rep["category_rpm"].items())[:top]:
            print(f"     {cat:24s} ₹{rpm:>8.1f}")
    if rep["high_rpm_tokens"]:
        print("  💎 HIGH-RPM TOPICS: " +
              ", ".join(f"{t} (₹{v})" for t, v in
                        list(rep["high_rpm_tokens"].items())[:top]))
    if rep["money_pages"]:
        print(f"  🏆 MONEY PAGES ({len(rep['money_pages'])}) — protect these:")
        for r in rep["money_pages"][:top]:
            print(f"     ₹{r['earnings']:>7.2f} · RPM ₹{r['rpm']:>6.2f} · "
                  f"{r['views']:>5} views · {r['slug'][:44]}")
    if rep["leaks"]:
        print(f"  🩹 REVENUE LEAKS ({len(rep['leaks'])}) — views unnayi, RPM takkuva:")
        for r in rep["leaks"][:top]:
            print(f"     {r['views']:>5} views · RPM ₹{r['rpm']:>6.2f} "
                  f"(site ₹{rep['site_rpm']}) · {r['slug'][:40]}")
        print("     Fix: slots/in-content/interlinks + publish-date freshness.")
    print("-" * 74)
    print(f"  📄 insights: {path}  (calendar + revenue plan veetini chaduvutayi)")
    if notify:
        from . import notifier

        ok = notifier.send_telegram(report_text(rep))
        print(f"  📨 Telegram: {'pampamu' if ok else 'skip (token/chat ledu)'}")
    return 0
