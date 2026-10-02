# -*- coding: utf-8 -*-
"""v182 — EDITORIAL CALENDAR (90-day plan) — "inka ekkuva blogs, kaani plan tho".

Enduku: roju okka topic random ga theesukovadam valla (a) clusters build avvavu,
(b) high-value keywords miss avutayi, (c) same category rojantha repeat avutundi.
Top sites **calendar** naduputayi: pillar → cluster → support posts, season ki
match ayye order lo.

Ee engine 5 signal sources ni kalipi next N days ki **slots** plan chestundi:

  1. `output/search-demand-queue.json`  — readers nijamga adigina queries (v181)
  2. `output/refresh-queue.json`        — traffic padutunna pages (v181)
  3. `output/trend_queue.json`          — trending/seasonal topics (v17)
  4. keyword matrix gaps                — 12k+ keywords lo inka cover cheyyani vi
  5. `output/revenue-insights.json`     — high-RPM categories/tokens (v182 revenue loop)

Balancing rules (spam pattern ni avoid cheyyadaniki):
  * okate day lo okate category ki max 2 slots, okate cluster ki max 1 slot
  * roju 1 refresh slot (purana post improve) + migilinavi kotha posts
  * thin/duplicate topics auto skip (title dedupe against existing posts)
  * **auto-publish ledu** — ee engine plan queue loki velthundi, generation +
    human approval gates appude jarugutayi (`--calendar-apply` → topics_queue.txt)

CLI:
    python run.py --calendar                          # 90-day plan (print + files)
    python run.py --calendar --calendar-days 30 --calendar-per-day 3
    python run.py --calendar-apply                    # next topics ni queue loki
    python run.py --calendar --calendar-notify        # Telegram summary
"""
from __future__ import annotations

import json
import logging
import re
from collections import Counter, defaultdict
from datetime import date, timedelta
from pathlib import Path
from typing import Dict, List, Optional

from . import config, state

log = logging.getLogger("autoblog.editorial_calendar")

MAX_PER_CATEGORY_DAY = 2
MAX_PER_CLUSTER_DAY = 1
_TOKEN = re.compile(r"[a-zA-Z\u0C00-\u0C7F]{4,}")


# ------------------------------------------------------------------ sources

def _load_json(path: Path) -> Dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _norm(text: str) -> str:
    return " ".join((text or "").lower().split())


def _tokens(text: str) -> set:
    return {t.lower() for t in _TOKEN.findall(text or "")}


def demand_candidates(path: Optional[Path] = None) -> List[Dict]:
    """Readers' searches (v181). Zero-result = highest intent, inka content ledu."""
    data = _load_json(Path(path or config.SEARCH_DEMAND_QUEUE))
    out = []
    for row in data.get("queue", []):
        term = (row.get("term") or "").strip()
        if len(term) < 6:
            continue
        zero = row.get("reason") == "no-results"
        out.append({
            "title": term.title(), "source": "demand",
            "score": 100 + (15 if zero else 0) + int(row.get("count", 0)) * 2,
            "reason": f"{row.get('count', 0)} searches" + (" · result ledu" if zero else ""),
            "type": "new", "category": "", "cluster": term.split()[0].lower(),
        })
    return out


def refresh_candidates(path: Optional[Path] = None) -> List[Dict]:
    """Traffic padutunna pages (v181) — kotha post kaadu, purana post improve."""
    data = _load_json(Path(path or config.RANK_REFRESH_QUEUE))
    out = []
    for row in data.get("queue", []):
        url = row.get("url") or ""
        if not url:
            continue
        delta = int(row.get("clicks_delta", 0))
        out.append({
            "title": f"REFRESH: {url}", "source": "refresh", "url": url,
            "score": 90 + min(30, abs(delta)),
            "reason": f"clicks {row.get('clicks_before')}→{row.get('clicks')} "
                      f"({delta:+d}) · pos {row.get('position_before')}→{row.get('position')}",
            "type": "refresh", "category": "", "cluster": "refresh",
        })
    return out


def trend_candidates(path: Optional[Path] = None) -> List[Dict]:
    """Trending / seasonal topics (v17 queue) — freshness ki."""
    data = _load_json(Path(path or config.OUTPUT_DIR / "trend_queue.json"))
    rows = data.get("queue") or data.get("topics") or []
    out = []
    for row in rows if isinstance(rows, list) else []:
        text = row if isinstance(row, str) else (row.get("topic") or row.get("title") or "")
        text = (text or "").strip()
        if len(text) < 8:
            continue
        out.append({"title": text, "source": "trend", "score": 78,
                    "reason": "trending now", "type": "new", "category": "",
                    "cluster": text.split()[0].lower()})
    return out


def gap_candidates(titles: List[str], limit: int = 400) -> List[Dict]:
    """Keyword matrix lo inka cover cheyyani vi (12k+ universe)."""
    try:
        from . import keyword_engine as ke
    except Exception as exc:  # noqa: BLE001
        log.debug("keyword_engine unavailable: %s", exc)
        return []
    try:
        gaps = ke.keyword_gaps(titles, limit=limit)
    except Exception as exc:  # noqa: BLE001
        log.debug("keyword_gaps fail: %s", exc)
        return []
    out = []
    for g in gaps:
        pr = float(g.get("priority", 50) or 50)
        comp = (g.get("competition") or "medium").lower()
        penalty = {"high": -12, "medium": 0, "low": 8}.get(comp, 0)
        out.append({
            "title": g.get("title") or g.get("kw", ""), "source": "gap",
            "score": 40 + pr * 0.45 + penalty,
            "reason": f"uncovered · demand {g.get('demand', '?')} · comp {comp}",
            "type": "new", "category": g.get("cat", ""), "cluster": g.get("exam", ""),
            "intent": g.get("intent", ""),
        })
    return out


def revenue_boost() -> Dict:
    """High-RPM category/token signals (v182 revenue loop) — money-first ordering."""
    data = _load_json(config.REVENUE_INSIGHTS_PATH)
    return {"categories": data.get("category_rpm", {}) or {},
            "tokens": {t: v for t, v in (data.get("high_rpm_tokens", {}) or {}).items()}}


def _apply_revenue_boost(cands: List[Dict], boost: Dict) -> None:
    cats = boost.get("categories") or {}
    tokens = boost.get("tokens") or {}
    if not cats and not tokens:
        return
    for c in cands:
        cat = c.get("category") or ""
        if cat and cat in cats:
            c["score"] += min(25, float(cats[cat]) / 4.0)
            c["reason"] += f" · ₹{cats[cat]:.0f}/1k views"
        if tokens:
            hit = _tokens(c["title"]) & set(tokens)
            if hit:
                c["score"] += 10
                c["reason"] += " · high-RPM topic"


# ------------------------------------------------------------------- planning

def collect(titles: List[str], use_universe: bool = True) -> List[Dict]:
    cands = (demand_candidates() + refresh_candidates() + trend_candidates())
    if use_universe:
        cands += gap_candidates(titles)
    _apply_revenue_boost(cands, revenue_boost())
    # dedupe: same normalized title (highest score winna)
    best: Dict[str, Dict] = {}
    seen_titles = {_norm(t) for t in titles}
    for c in cands:
        key = _norm(c["title"])
        if not key or key in seen_titles:
            continue
        if key not in best or c["score"] > best[key]["score"]:
            best[key] = c
    return sorted(best.values(), key=lambda c: c["score"], reverse=True)


def plan(days: int = 90, per_day: int = 3, use_universe: bool = True,
         start: Optional[date] = None) -> Dict:
    """Next N days ki balanced slots (category/cluster caps + refresh slot)."""
    today = start or date.today()
    try:
        titles = state.recent_titles(config.STATE_PATH, limit=1000)
    except Exception as exc:  # noqa: BLE001
        log.debug("recent_titles skip: %s", exc)
        titles = []
    cands = collect(titles, use_universe=use_universe)
    refreshes = [c for c in cands if c["type"] == "refresh"]
    news = [c for c in cands if c["type"] != "refresh"]

    schedule, used = [], Counter()
    ri = 0
    for d in range(days):
        day = today + timedelta(days=d)
        slots: List[Dict] = []
        day_cat: Counter = Counter()
        day_cluster: set = set()
        # 1) refresh slot (roju okati — decay fix; weekly Sunday rendu)
        want_refresh = 1 + (1 if day.weekday() == 6 else 0)
        while ri < len(refreshes) and len([s for s in slots if s["type"] == "refresh"]) < want_refresh:
            slots.append({**refreshes[ri], "date": day.isoformat(), "slot": len(slots) + 1})
            ri += 1
        # 2) kotha posts — category/cluster balance tho
        for c in news:
            if len(slots) >= per_day:
                break
            if used.get(_norm(c["title"]), 0):
                continue
            cat = c.get("category") or "General"
            cluster = c.get("cluster") or cat
            if day_cat[cat] >= MAX_PER_CATEGORY_DAY or cluster in day_cluster:
                continue
            used[_norm(c["title"])] += 1
            day_cat[cat] += 1
            day_cluster.add(cluster)
            slots.append({**c, "date": day.isoformat(), "slot": len(slots) + 1})
        if slots:
            schedule.append({"date": day.isoformat(), "weekday": day.strftime("%a"),
                             "slots": slots})
    counts = Counter(s["source"] for row in schedule for s in row["slots"])
    return {
        "generated": today.isoformat(), "days": len(schedule), "per_day": per_day,
        "total_slots": sum(len(r["slots"]) for r in schedule),
        "by_source": dict(counts),
        "schedule": schedule,
        "candidates": len(cands),
        "note": "plan queue matrame — generation + human approval gates appude "
                "jarugutayi (auto-publish ledu)",
    }


def save_plan(rep: Dict, path: Optional[Path] = None) -> tuple:
    path = Path(path or config.EDITORIAL_CALENDAR_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    md = path.with_suffix(".md")
    lines = [f"# StudentUp editorial calendar — {rep['generated']}",
             f"{rep['days']} days · {rep['total_slots']} slots · "
             f"sources: {', '.join(f'{k}={v}' for k, v in sorted(rep['by_source'].items()))}",
             ""]
    for row in rep["schedule"]:
        lines.append(f"## {row['date']} ({row['weekday']})")
        for s in row["slots"]:
            lines.append(f"- **{s['title']}**  \n  `{s['source']}` · {s['reason']} "
                         f"· cat {s.get('category') or '—'} · score {s['score']:.0f}")
        lines.append("")
    md.write_text("\n".join(lines), encoding="utf-8")
    return path, md


def apply_to_queue(rep: Dict, limit: int = 12) -> Dict:
    """Next kotha-post topics ni pipeline queue (`topics_queue.txt`) loki.

    Ee queue ni radar/keyword pipeline chaduvutundi — so calendar nijamga
    generation ni drive chestundi. Dedupe + edu filter automatic
    (`news_radar._queue_topic` tho same path). Refresh slots queue loki
    vellavu — avi `--update` ki (gsc priority store lo already unnayi).
    """
    try:
        from . import news_radar as nr
    except Exception as exc:  # noqa: BLE001
        return {"queued": 0, "error": f"news_radar unavailable: {exc}"}
    queued, skipped = 0, 0
    for row in rep["schedule"]:
        for s in row["slots"]:
            if queued >= limit:
                break
            if s["type"] != "new":
                continue
            text = f"{s['title']} — {s.get('reason', '')}".strip(" —")
            if nr._queue_topic(text):
                queued += 1
            else:
                skipped += 1
        if queued >= limit:
            break
    return {"queued": queued, "skipped": skipped,
            "file": str(nr.topics_queue_path())}


def report_text(rep: Dict) -> str:
    lines = ["<b>🗓 EDITORIAL CALENDAR (v182)</b>",
             f"{rep['days']} days · {rep['total_slots']} slots · "
             f"candidates {rep['candidates']}",
             " ".join(f"{k}:{v}" for k, v in sorted(rep["by_source"].items())), ""]
    for row in rep["schedule"][:3]:
        lines.append(f"<b>{row['date']}</b> ({row['weekday']})")
        for s in row["slots"]:
            lines.append(f"  • [{s['source']}] {s['title'][:70]}")
    lines.append("")
    lines.append("Plan queue → topics_queue.txt (`--calendar-apply`); generation + "
                 "approval gates appude.")
    return "\n".join(lines)


# --------------------------------------------------------------------- CLI

def run_cli(days: int = 90, per_day: int = 3, notify: bool = False,
            apply: bool = False, apply_limit: int = 12,
            universe: bool = True) -> int:
    print("=" * 74)
    print("  🗓 EDITORIAL CALENDAR (v182) — 90-day plan (pillar · cluster · season)")
    print("=" * 74)
    rep = plan(days=days, per_day=per_day, use_universe=universe)
    if not rep["total_slots"]:
        print("  ⚠️  Signals levu — mundu run cheyandi:")
        print("      python run.py --search-demand   (readers em adigaro)")
        print("      python run.py --rank-trend      (GSC decay)")
        print("      python run.py --keywords        (matrix gaps)")
        return 1
    print(f"  candidates {rep['candidates']} · {rep['days']} days · "
          f"{rep['total_slots']} slots · per day {rep['per_day']}")
    print(f"  sources: " + " · ".join(f"{k} {v}" for k, v in sorted(rep["by_source"].items())))
    path, md = save_plan(rep)
    print("-" * 74)
    for row in rep["schedule"][:7]:
        print(f"  {row['date']} ({row['weekday']})")
        for s in row["slots"]:
            print(f"     {s['slot']}. [{s['source']:7s}] {s['title'][:58]}")
            print(f"        {s['reason'][:66]} · score {s['score']:.0f}")
    print("-" * 74)
    print(f"  📄 plan: {path}")
    print(f"  📄 readable: {md}")
    if apply:
        res = apply_to_queue(rep, limit=apply_limit)
        if res.get("error"):
            print(f"  ⚠️  queue: {res['error']}")
        else:
            print(f"  ✅ queue: {res['queued']} topics → {res['file']} "
                  f"(skipped {res['skipped']})")
    else:
        print("  Next: python run.py --calendar-apply   (topics → pipeline queue)")
    if notify:
        from . import notifier

        ok = notifier.send_telegram(report_text(rep))
        print(f"  📨 Telegram: {'pampamu' if ok else 'skip (token/chat ledu)'}")
    return 0
