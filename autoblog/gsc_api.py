# -*- coding: utf-8 -*-
"""v107 — optional direct Google Search Console API sync + alerts.

CSV ingestion remains available. When a Google service-account JSON is
configured and the account has Search Console access, this module pulls real
page-level Search Analytics data, feeds the v102 priority store, and compares
against the previous sync for evidence-based drop alerts.
"""
from __future__ import annotations

import json
import logging
from datetime import date, timedelta
from pathlib import Path
from typing import Dict, List

import requests

from . import config, gsc_refresh, state

log = logging.getLogger("autoblog.gsc_api")
KEY = "gsc:api-sync:v1"
SCOPE = "https://www.googleapis.com/auth/webmasters.readonly"
ENDPOINT = "https://www.googleapis.com/webmasters/v3/sites/{site}/searchAnalytics/query"


def _token() -> str:
    """Service-account token, optional dependency and credentials by design."""
    raw = getattr(config, "GSC_SERVICE_ACCOUNT_JSON", "")
    path = getattr(config, "GSC_SERVICE_ACCOUNT_FILE", "")
    if not raw and path:
        raw = Path(path).read_text(encoding="utf-8")
    if not raw:
        raise RuntimeError("GSC credentials missing: set GSC_SERVICE_ACCOUNT_FILE")
    try:
        from google.oauth2 import service_account
        from google.auth.transport.requests import Request
    except ImportError as exc:
        raise RuntimeError("google-auth dependency missing: pip install google-auth") from exc
    info = json.loads(raw) if raw.lstrip().startswith("{") else raw
    creds = service_account.Credentials.from_service_account_info(info, scopes=[SCOPE]) \
        if isinstance(info, dict) else service_account.Credentials.from_service_account_file(info, scopes=[SCOPE])
    creds.refresh(Request())
    return creds.token


def _site() -> str:
    return getattr(config, "GSC_SITE_URL", "") or getattr(config, "WP_SITE", "")


def query(start: str, end: str, row_limit: int = 25000) -> List[Dict]:
    token = _token()
    site = _site()
    if not site:
        raise RuntimeError("GSC_SITE_URL or WP_SITE missing")
    body = {"startDate": start, "endDate": end,
            "dimensions": ["page"], "rowLimit": max(1, min(row_limit, 25000)),
            "dataState": "final"}
    resp = requests.post(ENDPOINT.format(site=site), headers={"Authorization": f"Bearer {token}"},
                         json=body, timeout=config.HTTP_TIMEOUT)
    if resp.status_code != 200:
        raise RuntimeError(f"GSC API HTTP {resp.status_code}: {resp.text[:300]}")
    return resp.json().get("rows", [])


def _rows_to_pages(rows: List[Dict]) -> List[Dict]:
    out = []
    for row in rows:
        keys = row.get("keys") or []
        if not keys:
            continue
        clicks = float(row.get("clicks", 0) or 0)
        impressions = float(row.get("impressions", 0) or 0)
        ctr = clicks / impressions if impressions else 0.0
        position = float(row.get("position", 0) or 0)
        out.append({"url": keys[0], "clicks": int(clicks),
                    "impressions": int(impressions), "ctr": round(ctr, 5),
                    "position": round(position, 2),
                    "score": gsc_refresh.score(impressions, clicks, ctr, position)})
    return sorted(out, key=lambda x: x["score"], reverse=True)


def _alerts(old: Dict[str, Dict], new: List[Dict]) -> List[Dict]:
    alerts = []
    for row in new:
        before = old.get(row["url"])
        if not before or before.get("impressions", 0) < 100:
            continue
        pos_drop = row["position"] - float(before.get("position", row["position"]))
        ctr_drop = float(before.get("ctr", row["ctr"])) - row["ctr"]
        if pos_drop >= 3 or ctr_drop >= 0.03:
            alerts.append({"url": row["url"], "position_drop": round(pos_drop, 2),
                           "ctr_drop": round(ctr_drop, 4), "before": before, "now": row})
    return sorted(alerts, key=lambda x: (x["position_drop"], x["ctr_drop"]), reverse=True)


def sync(start: str, end: str) -> Dict:
    rows = _rows_to_pages(query(start, end))
    raw = state.meta_get(config.STATE_PATH, KEY) or "{}"
    try:
        previous = json.loads(raw).get("rows", [])
    except (ValueError, TypeError):
        previous = []
    old = {r.get("url"): r for r in previous if r.get("url")}
    alerts = _alerts(old, rows)
    payload = {"source": "google-search-console-api", "start": start, "end": end,
               "rows": rows, "alerts": alerts}
    state.meta_set(config.STATE_PATH, KEY, json.dumps(payload, ensure_ascii=False))
    # Reuse the proven v102 selector store.
    state.meta_set(config.STATE_PATH, "gsc:refresh-priority:v1",
                   json.dumps({"source": "gsc-api", "rows": rows}, ensure_ascii=False))
    return {"rows": len(rows), "alerts": alerts, "start": start, "end": end}


def run_cli(days: int = 28) -> int:
    end = date.today() - timedelta(days=2)  # GSC final data lag
    start = end - timedelta(days=max(7, days) - 1)
    try:
        rep = sync(start.isoformat(), end.isoformat())
    except Exception as exc:  # noqa: BLE001
        print(f"❌ GSC API sync unavailable: {exc}")
        print("   Service account ni Search Console property owner ga add cheyandi.")
        print("   Credentials lekunte: python run.py --gsc-refresh pages.csv")
        return 1
    print("=" * 74)
    print(f"  GSC API SYNC: {rep['start']} → {rep['end']} · {rep['rows']} pages")
    print("=" * 74)
    if rep["alerts"]:
        print(f"  ⚠️ ranking/CTR alerts: {len(rep['alerts'])}")
        for a in rep["alerts"][:20]:
            print(f"  {a['url'][:60]} · pos +{a['position_drop']:.1f} · CTR -{a['ctr_drop']:.1%}")
    else:
        print("  ✅ No configured position/CTR drop alerts")
    print("  ✅ GSC priority store updated for next auto-refresh")
    return 0
