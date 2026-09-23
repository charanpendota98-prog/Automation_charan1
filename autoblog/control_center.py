# -*- coding: utf-8 -*-
"""v112 — unified editorial/SEO operations control center.

Read-only aggregation of the independent safety systems. It never silently
publishes, merges, redirects or changes ads; it produces an action queue.
"""
from __future__ import annotations
import json
from pathlib import Path
from typing import Dict
from . import cannibalization, config, corrections, gsc_refresh


def _json_files(folder: str):
    p=Path(config.OUTPUT_DIR)/folder
    return sorted(p.glob("*.json"), key=lambda x:x.stat().st_mtime, reverse=True) if p.exists() else []

def collect() -> Dict:
    actions=[]
    corr=corrections.verify()
    if not corr["valid"]: actions.append("repair correction ledger hash chain")
    try:
        gsc_raw=json.loads(__import__('autoblog.state',fromlist=['state']).meta_get(config.STATE_PATH,"gsc:api-sync:v1") or "{}")
    except Exception: gsc_raw={}
    gsc_alerts=gsc_raw.get("alerts",[])
    if gsc_alerts: actions.append(f"review {len(gsc_alerts)} GSC position/CTR alerts")
    cann=cannibalization.analyze(cannibalization.load_state_posts(config.STATE_PATH))
    if cann["conflicts"]: actions.append(f"review {len(cann['conflicts'])} intent-cannibalization pairs")
    perf=_json_files("performance_audits")
    perf_review=0
    for p in perf:
        try:
            if json.loads(p.read_text(encoding="utf-8")).get("status")!="pass": perf_review+=1
        except (OSError,ValueError): actions.append(f"repair unreadable performance report {p.name}")
    if perf_review: actions.append(f"review {perf_review} performance/CWV reports")
    media=_json_files("media_ledger")
    media_missing=sum(1 for p in media if not p.exists())
    return {"version":"v112", "status":"action-required" if actions else "healthy",
            "actions":actions, "correction_ledger":corr,
            "gsc":{"alerts":len(gsc_alerts),"synced":bool(gsc_raw)},
            "cannibalization":{"pairs":len(cann["conflicts"]),"pages":cann["pages"]},
            "performance":{"reports":len(perf),"review":perf_review},
            "media":{"ledger_records":len(media),"missing":media_missing},
            "freshness":{"min_bump_pct":getattr(config,"FRESHNESS_MIN_CHANGE_PCT",8),
                         "min_publish_pct":getattr(config,"FRESHNESS_MIN_PUBLISH_PCT",2)}}

def run_cli()->int:
    r=collect();print("="*78);print(f"  EDITORIAL CONTROL CENTER v112 · {r['status']}");print("="*78)
    print(f"  corrections: {r['correction_ledger']['records']} records · valid={r['correction_ledger']['valid']}")
    print(f"  GSC: {r['gsc']['alerts']} alerts · synced={r['gsc']['synced']}")
    print(f"  cannibalization: {r['cannibalization']['pairs']} pairs / {r['cannibalization']['pages']} pages")
    print(f"  performance: {r['performance']['reports']} reports · review={r['performance']['review']}")
    print(f"  media ledger: {r['media']['ledger_records']} records")
    print(f"  freshness: {r['freshness']['min_bump_pct']}% bump / {r['freshness']['min_publish_pct']}% publish")
    print("-"*78)
    if r["actions"]:
        print("  ACTION QUEUE:");[print("   • "+x) for x in r["actions"]]
    else: print("  ✅ No recorded action items")
    return 0
