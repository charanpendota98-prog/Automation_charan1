# -*- coding: utf-8 -*-
"""v181 — ON-SITE SEARCH DEMAND → content gap queue.

Enduku idi (top sites ee loop ni naduputunnayi):

    Mee site lo students **em search chestunnaro** telisthe, adi Google keyword
    tools kanna nijamaina demand signal — aa query vachindi ante aa topic ki
    demand undi, aa kshanam mee daggara answer ledu ani artham.

Ee module 2 panulu:
  1. `fetch_live()` — WordPress theme (inc/searchlog.php) nunchi anonymous
     search-term log ni REST dwara teesukovadam (term + count + zero-result flag
     matrame; IP/user eppudu store avvadu).
  2. `analyze()` — ee terms ni mee posts tho polchi **content gaps** (search ki
     result ledu / dedicated post ledu) ni queue ga marchadam. Ee queue ni
     human-reviewed pipeline chaduvutundi — **ee module eppudu auto-publish
     cheyyadu** (scaled-content rule: demand signal ≠ auto bulk page).

CLI:
    python run.py --search-demand                  # live WP log → report + queue
    python run.py --search-demand --import F.json  # offline/demo (same shape)
    python run.py --search-demand --notify         # Telegram summary kuda
"""
from __future__ import annotations

import csv
import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

import requests

from . import config, state

log = logging.getLogger("autoblog.search_demand")

REST_PATH = "/wp-json/studentup/v1/search-log"
_WORD = re.compile(r"[a-zA-Z\u0C00-\u0C7F]{3,}")
_STOP = {"the", "and", "for", "with", "from", "how", "what", "when", "best",
         "telugu", "complete", "details", "latest", "guide", "online", "2026",
         "2027", "కి", "లో", "ఈ", "ఏ", "ఎలా", "ఏమిటి"}


# --------------------------------------------------------------- term utils

def norm_term(term: str) -> str:
    """Case/space normalize — dedupe ki (Telugu safe)."""
    return re.sub(r"\s+", " ", (term or "").strip().lower())


def _tokens(text: str) -> set:
    return {w for w in _WORD.findall((text or "").lower()) if w not in _STOP}


def novel_tokens(term: str, titles: Iterable[str]) -> int:
    """Term lo unna tokens lo ee post title kuda cover cheyyani vi (coverage gap)."""
    want = _tokens(term)
    if not want:
        return 0
    covered = set()
    for title in titles:
        hover = _tokens(title)
        covered |= (want & hover)
    return len(want - covered)


# ------------------------------------------------------------------ sources

def parse_import(path: str) -> List[Dict]:
    """JSON (`{"terms":[{term,count,zero}]}`) leda CSV (`term,count,zero`) → list."""
    p = Path(path)
    raw = p.read_text(encoding="utf-8")
    if p.suffix.lower() == ".json":
        data = json.loads(raw)
        rows = data.get("terms", data) if isinstance(data, dict) else data
        out = []
        for r in rows:
            if isinstance(r, dict) and r.get("term"):
                out.append({"term": norm_term(str(r["term"])),
                            "count": int(r.get("count", 1) or 1),
                            "zero": bool(r.get("zero", False))})
    else:
        out = []
        for row in csv.DictReader(raw.splitlines()):
            term = row.get("term") or row.get("query") or row.get("q") or ""
            if not norm_term(term):
                continue
            zero = str(row.get("zero", row.get("no_results", "0"))).strip().lower()
            out.append({"term": norm_term(term),
                        "count": int(float(row.get("count", 1) or 1)),
                        "zero": zero in ("1", "true", "yes", "y")})
    if not out:
        raise ValueError("search demand import lo usable terms levu")
    return out


def fetch_live(timeout: int = 30) -> Tuple[List[Dict], Dict]:
    """Theme REST log ni teesukovadam (auth: WP app password — admin-only GET)."""
    if not config.WP_APP_PASSWORD:
        raise RuntimeError("WP_APP_PASSWORD ledu — .env lo pettandi (theme GET admin-only)")
    url = (config.WP_SITE or "").rstrip("/") + REST_PATH
    resp = requests.get(url, auth=(config.WP_USERNAME, config.WP_APP_PASSWORD),
                        timeout=timeout, params={"limit": config.SEARCH_DEMAND_MAX_TERMS})
    if resp.status_code in (401, 403):
        raise PermissionError("search-log GET ki permission ledu (admin app password kavali)")
    resp.raise_for_status()
    data = resp.json()
    terms = [{"term": norm_term(str(t.get("term", ""))),
              "count": int(t.get("count", 1) or 1),
              "zero": bool(t.get("zero", False))}
             for t in (data.get("terms") or []) if t.get("term")]
    return terms, {"total": int(data.get("total", 0) or 0),
                   "updated": str(data.get("updated", ""))}


# ----------------------------------------------------------------- analysis

def analyze(terms: List[Dict], titles: List[str], zero_ratio: float = 0.0) -> Dict:
    """Terms → popular / gaps (zero-result first) / weak coverage."""
    popular = sorted(terms, key=lambda t: t["count"], reverse=True)
    gaps, weak = [], []
    for t in popular:
        if t["zero"]:
            gaps.append({**t, "reason": "no-results", "priority": 1,
                         "novel_tokens": max(1, len(_tokens(t["term"])))})
        else:
            novel = novel_tokens(t["term"], titles)
            if novel >= 2:
                weak.append({**t, "reason": "weak-coverage", "priority": 2,
                             "novel_tokens": novel})
    gaps.sort(key=lambda t: (-t["priority"], -t["count"], -t["novel_tokens"]))
    weak.sort(key=lambda t: (-t["count"], -t["novel_tokens"]))
    return {
        "total_terms": len(terms),
        "total_searches": sum(t["count"] for t in terms),
        "popular": popular[:15],
        "gaps": gaps[:40],
        "weak": weak[:40],
        "zero_share": round(len([t for t in terms if t["zero"]]) / max(1, len(terms)), 3),
    }


def write_queue(analysis: Dict, path: Optional[Path] = None) -> Path:
    """Gap topics ni queue file lo merge (dedupe + first_seen preserve).

    Ee file ni insanlu chusi topic select chestaru — auto-publish ledu.
    """
    path = Path(path or config.SEARCH_DEMAND_QUEUE)
    existing: Dict[str, Dict] = {}
    if path.exists():
        try:
            for row in json.loads(path.read_text(encoding="utf-8")).get("queue", []):
                existing[norm_term(row.get("term", ""))] = row
        except (OSError, ValueError):
            existing = {}
    today = datetime.now().strftime("%Y-%m-%d")
    for item in analysis["gaps"] + analysis["weak"]:
        key = norm_term(item["term"])
        row = existing.get(key)
        if row:
            row["count"] = max(int(row.get("count", 0)), int(item["count"]))
            row["last_seen"] = today
            row["reason"] = item["reason"]
        else:
            existing[key] = {"term": item["term"], "reason": item["reason"],
                             "count": item["count"], "novel_tokens": item["novel_tokens"],
                             "first_seen": today, "last_seen": today, "status": "new"}
    path.parent.mkdir(parents=True, exist_ok=True)
    queue = sorted(existing.values(), key=lambda r: (-int(r.get("count", 0)), r["term"]))
    path.write_text(json.dumps({"updated": datetime.now().isoformat(timespec="seconds"),
                                "queue": queue}, ensure_ascii=False, indent=1),
                    encoding="utf-8")
    return path


def report_text(analysis: Dict, queue_path: Optional[Path] = None) -> str:
    lines = ["<b>🔎 ON-SITE SEARCH DEMAND</b>",
             f"searches: {analysis['total_searches']} · terms: {analysis['total_terms']} "
             f"· zero-result share: {analysis['zero_share'] * 100:.0f}%", ""]
    if analysis["gaps"]:
        lines.append("<b>Content gaps (search ki result ledu):</b>")
        for g in analysis["gaps"][:8]:
            lines.append(f"  • {g['term']} — {g['count']}× (no results)")
    if analysis["weak"]:
        lines.append("<b>Weak coverage (dedicated post ledu):</b>")
        for w in analysis["weak"][:8]:
            lines.append(f"  • {w['term']} — {w['count']}×")
    if not analysis["gaps"] and not analysis["weak"]:
        lines.append("Gaps levu — prathi search ki content undi 👏")
    if queue_path:
        lines.append("")
        lines.append(f"queue: {queue_path} (human review — auto-publish ledu)")
    return "\n".join(lines)


# --------------------------------------------------------------------- CLI

def run_cli(import_path: str = "", notify: bool = False, queue: bool = True,
            top: int = 10) -> int:
    print("=" * 74)
    print("  🔎 SEARCH DEMAND LOOP (v181) — readers em adigaro → content gaps")
    print("=" * 74)
    src = "import"
    try:
        if import_path:
            terms = parse_import(import_path)
            meta = {"total": sum(t["count"] for t in terms), "updated": ""}
        else:
            terms, meta = fetch_live()
            src = "live-WP"
    except (OSError, ValueError, RuntimeError, PermissionError, requests.RequestException) as exc:
        print(f"  ⚠️  data teesukolekapoyam: {exc}")
        print("  Fix: inc/searchlog.php deploy ayyaka (theme upload) malli run cheyandi,")
        print("       leda offline: python run.py --search-demand --import sample.json")
        return 1
    if not terms:
        print("  ℹ️  Inka search log khali — students search chesaka automatic ga nindutundi.")
        return 0

    titles = []
    try:
        titles = state.recent_titles(config.STATE_PATH, limit=400)
    except Exception as exc:  # noqa: BLE001 — titles lekapote coverage check skip
        log.info("recent_titles skip: %s", exc)

    analysis = analyze(terms, titles)
    print(f"  source: {src} · terms: {analysis['total_terms']} · "
          f"searches: {analysis['total_searches']} · "
          f"zero-result: {analysis['zero_share'] * 100:.0f}%")
    print("-" * 74)
    if analysis["gaps"]:
        print("  ⛔ CONTENT GAPS (search chesaru — manaki answer ledu):")
        for g in analysis["gaps"][:top]:
            print(f"     {g['count']:>4}×  {g['term']}")
    if analysis["weak"]:
        print("  ⚠️  WEAK COVERAGE (dedicated post ledu):")
        for w in analysis["weak"][:top]:
            print(f"     {w['count']:>4}×  {w['term']}")
    if not analysis["gaps"] and not analysis["weak"]:
        print("  ✅ Prathi search term ki content undi — gaps levu.")
    qp = write_queue(analysis) if queue else None
    if qp:
        print("-" * 74)
        print(f"  📝 queue: {qp}")
        print("     (ee list nunchi topics select chesi --top-post / --url tho rasi,")
        print("      human review tarvata publish — auto bulk generation ledu)")
    if notify:
        from . import notifier

        ok = notifier.send_telegram(report_text(analysis, qp))
        print(f"  📨 Telegram: {'pampamu' if ok else 'skip (token/chat ledu)'}")
    return 0
