# -*- coding: utf-8 -*-
"""v111 — transparent correction/update ledger with hash chaining."""
from __future__ import annotations
import hashlib, json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List
from . import config


def _path() -> Path:
    p=Path(config.OUTPUT_DIR)/"corrections";p.mkdir(parents=True,exist_ok=True)
    return p/"ledger.jsonl"

def _canonical(item: Dict) -> str:
    return json.dumps(item, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

def record(post_id, title: str, reason: str, sources: List[str],
           backup: str = "", change_summary: str = "", actor: str = "autoblog") -> Dict:
    path=_path(); previous=""
    if path.exists():
        lines=[x for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]
        if lines:
            try: previous=json.loads(lines[-1]).get("record_hash", "")
            except ValueError: previous=""
    item={"version":"v111", "timestamp":datetime.now(timezone.utc).isoformat(),
          "post_id":post_id, "title":title[:200], "reason":reason[:500],
          "sources":list(dict.fromkeys(sources or []))[:20], "backup":backup,
          "change_summary":change_summary[:1000], "actor":actor, "previous_hash":previous}
    item["record_hash"]=hashlib.sha256(_canonical(item).encode("utf-8")).hexdigest()
    with path.open("a",encoding="utf-8") as fh: fh.write(_canonical(item)+"\n")
    return item

def verify() -> Dict:
    path=_path(); previous=""; count=0; errors=[]
    if not path.exists(): return {"valid":True,"records":0,"errors":[]}
    for number,line in enumerate(path.read_text(encoding="utf-8").splitlines(),1):
        if not line.strip(): continue
        try: item=json.loads(line)
        except ValueError: errors.append(f"line {number}: invalid JSON");continue
        recorded=item.pop("record_hash","")
        if item.get("previous_hash","")!=previous: errors.append(f"line {number}: chain mismatch")
        expected=hashlib.sha256(_canonical(item).encode("utf-8")).hexdigest()
        if expected!=recorded: errors.append(f"line {number}: hash mismatch")
        previous=recorded;count+=1
    return {"valid":not errors,"records":count,"errors":errors}

def run_cli() -> int:
    r=verify();print("="*70);print(f"  CORRECTION LEDGER: {r['records']} records · valid={r['valid']}")
    for e in r["errors"][:10]: print("  ❌ "+e)
    return 0 if r["valid"] else 1
