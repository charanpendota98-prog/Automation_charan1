# -*- coding: utf-8 -*-
"""v113 — deduplicated editorial operations alerts."""
from __future__ import annotations
import hashlib, json
from . import config, control_center, state

KEY="ops:control-alert:v1"

def _fingerprint(actions):
    return hashlib.sha256(json.dumps(sorted(actions),ensure_ascii=False).encode()).hexdigest()

def check_and_alert(send=True):
    report=control_center.collect(); actions=report.get("actions",[])
    fp=_fingerprint(actions)
    previous=state.meta_get(config.STATE_PATH,KEY) or ""
    changed=bool(actions) and fp!=previous
    sent=False
    if changed and send and getattr(config,"TELEGRAM_BOT_TOKEN","") and getattr(config,"TELEGRAM_CHAT_ID",""):
        from .notifier import send_telegram
        lines=["⚠️ <b>Editorial control action queue</b>"]+[f"• {x}" for x in actions[:8]]
        sent=bool(send_telegram("\n".join(lines)))
    state.meta_set(config.STATE_PATH,KEY,fp)
    return {"status":report["status"],"actions":actions,"changed":changed,"sent":sent,
            "telegram_configured":bool(getattr(config,"TELEGRAM_BOT_TOKEN","") and getattr(config,"TELEGRAM_CHAT_ID",""))}

def run_cli():
    r=check_and_alert(send=True)
    print("="*74);print(f"  OPS ALERT: status={r['status']} changed={r['changed']} sent={r['sent']}")
    print(f"  telegram configured: {r['telegram_configured']}")
    for x in r["actions"]: print("  • "+x)
    if not r["actions"]: print("  ✅ no action items")
    return 0
