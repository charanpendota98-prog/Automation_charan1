# -*- coding: utf-8 -*-
"""v102 — GSC PAGE DATA -> evidence-based refresh priority.

Old posts ni oldest-first update cheyyadam blind strategy. Search Console page
export tho already-impression unna, page 1/2 edge lo unna, CTR low unna pages
first improve cheyyali — real opportunity, not keyword imagination.

Accepted CSV: Search Console Performance > Pages > Export, with columns like:
  Top pages/Page, Clicks, Impressions, CTR, Position

Query-only export intentionally rejected: query ki matching URL teliyadu, so
wrong post ni refresh cheyyadam kanna no priority better.
"""
from __future__ import annotations

import csv
import json
import logging
import re
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit
from typing import Dict, List

from . import config, state

log = logging.getLogger("autoblog.gsc_refresh")
KEY = "gsc:refresh-priority:v1"


def _header(v: str) -> str:
    return re.sub(r"[^a-z]", "", (v or "").strip().lower())


def _url(url: str) -> str:
    raw = (url or "").strip()
    if not raw:
        return ""
    if raw.startswith("/"):
        raw = (getattr(config, "WP_SITE", "") or "").rstrip("/") + raw
    try:
        p = urlsplit(raw)
        if p.scheme not in ("http", "https") or not p.netloc:
            return ""
        path = p.path.rstrip("/") or "/"
        return urlunsplit((p.scheme.lower(), p.netloc.lower(), path, "", ""))
    except ValueError:
        return ""


def _num(v: str, default: float = 0.0) -> float:
    try:
        return float((v or "").strip().replace(",", "").rstrip("%"))
    except (TypeError, ValueError):
        return default


def score(impressions: float, clicks: float, ctr: float, position: float) -> float:
    """Opportunity score, not a ranking prediction.

    High impressions + position 4..20 + below-expected CTR = high priority.
    CTR is capped defensively because exports can contain malformed values.
    """
    if impressions <= 0 or position <= 0:
        return 0.0
    ctr = max(0.0, min(1.0, ctr))
    # approximate CTR ceiling: position 1 ~ 0.28, position 20 ~ 0.01.
    expected = max(0.01, min(0.28, 0.30 / (position ** 0.65)))
    ctr_gap = max(0.05, min(1.0, 1.0 - (ctr / expected)))
    distance = max(0.05, min(1.0, (22.0 - position) / 18.0))
    return round(impressions * ctr_gap * distance, 2)


def parse(csv_path: str) -> List[Dict]:
    path = Path(csv_path)
    with path.open(encoding="utf-8-sig", errors="replace", newline="") as fh:
        rows = list(csv.reader(fh))
    if not rows:
        raise ValueError("empty GSC export")
    headers = [_header(x) for x in rows[0]]
    page_i = next((i for i, h in enumerate(headers)
                   if h in ("toppages", "page", "pages", "url")), None)
    click_i = next((i for i, h in enumerate(headers) if h == "clicks"), None)
    impr_i = next((i for i, h in enumerate(headers) if h == "impressions"), None)
    ctr_i = next((i for i, h in enumerate(headers) if h == "ctr"), None)
    pos_i = next((i for i, h in enumerate(headers) if h == "position"), None)
    if None in (page_i, click_i, impr_i, ctr_i, pos_i):
        raise ValueError("GSC Pages export kavali: Page, Clicks, Impressions, CTR, Position")

    out = {}
    for row in rows[1:]:
        if len(row) <= max(page_i, click_i, impr_i, ctr_i, pos_i):
            continue
        url = _url(row[page_i])
        if not url:
            continue
        clicks = _num(row[click_i])
        impressions = _num(row[impr_i])
        ctr = _num(row[ctr_i]) / 100.0
        position = _num(row[pos_i])
        item = {"url": url, "clicks": int(clicks), "impressions": int(impressions),
                "ctr": round(ctr, 5), "position": round(position, 2),
                "score": score(impressions, clicks, ctr, position)}
        # Duplicate URL rows can occur in grouped exports: retain aggregate.
        if url in out:
            old = out[url]
            old["clicks"] += item["clicks"]
            old["impressions"] += item["impressions"]
            old["ctr"] = round(old["clicks"] / max(1, old["impressions"]), 5)
            old["score"] = score(old["impressions"], old["clicks"], old["ctr"],
                                  min(old["position"], item["position"]))
        else:
            out[url] = item
    if not out:
        raise ValueError("GSC Pages export lo usable URL rows levu")
    return sorted(out.values(), key=lambda x: x["score"], reverse=True)


def ingest(csv_path: str) -> List[Dict]:
    rows = parse(csv_path)
    payload = {"source": "gsc-pages-csv", "rows": rows}
    state.meta_set(config.STATE_PATH, KEY, json.dumps(payload, ensure_ascii=False))
    return rows


def load() -> Dict[str, Dict]:
    try:
        raw = state.meta_get(config.STATE_PATH, KEY) or "{}"
        data = json.loads(raw)
        return {r["url"]: r for r in data.get("rows", []) if r.get("url")}
    except (OSError, ValueError, TypeError, KeyError):
        return {}


def run_cli(csv_path: str) -> int:
    try:
        rows = ingest(csv_path)
    except (OSError, ValueError) as exc:
        print(f"❌ GSC Pages CSV: {exc}")
        print("   Search Console > Performance > Pages > Export CSV use cheyandi")
        return 1
    print("=" * 74)
    print(f"  GSC REFRESH PRIORITY: {len(rows)} pages ingested")
    print("=" * 74)
    print("  URL".ljust(52) + " IMPR    POS    CTR   SCORE")
    for r in rows[:20]:
        print(f"  {r['url'][:48].ljust(48)} {r['impressions']:>5} "
              f"{r['position']:>6.1f} {r['ctr']*100:>6.2f}% {r['score']:>7.1f}")
    print("-" * 74)
    print("  ✅ Saved. Next auto-refresh first evidence-based GSC opportunity ni pick chestundi.")
    print("  Note: score priority matrame — title/content change publish mundu freshness + QA gates run avutayi.")
    return 0
