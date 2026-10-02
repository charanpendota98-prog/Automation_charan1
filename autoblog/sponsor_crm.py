# -*- coding: utf-8 -*-
"""v181 — SPONSOR PIPELINE (direct-sales loop — highest revenue lever).

Nijam: ads-only revenue views ki proportion; kaani **highest** revenue direct
sales nunchi vastundi (colleges/coaching/books/hostels banners + sponsored
articles + leads). Adi code tho automatic kaadu — kaani **systematic** cheyyachu:

  * prospect list + stages (new → contacted → replied → negotiating → won/lost)
  * roju **N outreach targets** (default 2 — playbook lo cheppinattu)
  * overdue follow-ups (deals follow-up lekunda chachipotayi)
  * pipeline ₹ value + expected value (stage probabilities tho) — forecast
  * ready-to-send Telugu/English message templates (rate card nunchi)

Ee module **emi pampadu** (mee WhatsApp/email nunchi meeru pampali) — kaani
evariki, enti, eppudu ani cheppadam aapadu. Telegram lo roju summary vastundi.

CLI:
    python run.py --sponsor-crm                       # today's plan + forecast
    python run.py --sponsor-add "Sri Coaching|coaching|Hyderabad|98480xxxxx|8000"
    python run.py --sponsor-update "Sri Coaching|contacted|call chesam|2026-10-05"
    python run.py --sponsor-crm --notify              # plan → Telegram
    python run.py --sponsor-targets                   # prospect types + search strings
"""
from __future__ import annotations

import json
import logging
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

from . import config, rate_card

log = logging.getLogger("autoblog.sponsor_crm")

STAGES: Dict[str, float] = {
    "new": 0.05,
    "contacted": 0.15,
    "replied": 0.35,
    "negotiating": 0.60,
    "won": 1.00,
    "lost": 0.0,
    "paused": 0.0,
}
OPEN_STAGES = ("new", "contacted", "replied", "negotiating")

TARGET_TYPES = [
    ("college", "Junior/Degree colleges — admissions season lo banner + sponsored article"),
    ("coaching", "SSC/Banking/Groups coaching institutes — course promotion"),
    ("hostel", "Student hostels & PG — city-wise ads"),
    ("bookshop", "Competitive exam books/shorts publishers — affiliate + ads"),
    ("online-course", "Online courses / test series apps — lead sales (high value)"),
    ("bank-loan", "Education loan desks (banks/NBFCs) — scholarship-season targeting"),
    ("hospital", "Student health/eye clinics — campus area targeting"),
    ("shop", "Local student shops (xerox, stationery, mobiles) — cheap entry deals"),
]


def _path(path: Optional[Path] = None) -> Path:
    return Path(path or config.SPONSOR_PIPELINE_PATH)


def load(path: Optional[Path] = None) -> Dict:
    """Pipeline file (ledu ante khali skeleton — fake prospects create cheyyamu)."""
    p = _path(path)
    if not p.exists():
        return {"updated": "", "prospects": [], "activity": []}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        data.setdefault("prospects", [])
        data.setdefault("activity", [])
        return data
    except (OSError, ValueError):
        return {"updated": "", "prospects": [], "activity": []}


def save(data: Dict, path: Optional[Path] = None) -> Path:
    p = _path(path)
    data["updated"] = datetime.now().isoformat(timespec="seconds")
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    return p


def _find(data: Dict, name: str) -> Optional[Dict]:
    key = (name or "").strip().lower()
    for row in data["prospects"]:
        if (row.get("name", "") or "").strip().lower() == key:
            return row
    return None


def add(name: str, ptype: str = "", city: str = "", contact: str = "",
        value: int = 0, path: Optional[Path] = None) -> Dict:
    """Kotha prospect (stage=new). Duplicate name → error."""
    if not (name or "").strip():
        raise ValueError("prospect name khali")
    data = load(path)
    if _find(data, name):
        raise ValueError(f"'{name}' already undi — --sponsor-update vaadandi")
    row = {"name": name.strip(), "type": (ptype or "").strip().lower(),
           "city": (city or "").strip(), "contact": (contact or "").strip(),
           "stage": "new", "value": int(value or 0),
           "next_followup": date.today().isoformat(), "notes": "",
           "created": date.today().isoformat()}
    data["prospects"].append(row)
    data["activity"].append({"date": date.today().isoformat(), "name": row["name"],
                             "stage": "new", "note": "added"})
    save(data, path)
    return row


def update(name: str, stage: str = "", note: str = "", followup: str = "",
           value: Optional[int] = None, path: Optional[Path] = None) -> Dict:
    """Stage/note/follow-up/value update + activity log."""
    data = load(path)
    row = _find(data, name)
    if not row:
        raise ValueError(f"'{name}' pipeline lo ledu — --sponsor-add cheyandi")
    if stage:
        st = stage.strip().lower()
        if st not in STAGES:
            raise ValueError(f"stage tappu: {stage} (ok: {', '.join(STAGES)})")
        row["stage"] = st
    if note:
        row["notes"] = (row.get("notes", "") + " | " + note.strip()).strip(" |")
    if followup:
        date.fromisoformat(followup)          # validate
        row["next_followup"] = followup
    elif stage in ("contacted", "replied", "negotiating"):
        row["next_followup"] = (date.today() +
                                timedelta(days=config.SPONSOR_FOLLOWUP_STALE_DAYS)).isoformat()
    if value is not None:
        row["value"] = int(value)
    data["activity"].append({"date": date.today().isoformat(), "name": row["name"],
                             "stage": row["stage"], "note": note or stage or "update"})
    data["activity"] = data["activity"][-500:]
    save(data, path)
    return row


def today_plan(limit: Optional[int] = None, path: Optional[Path] = None) -> Dict:
    """Roju cheyyalsina sales pani: kotha outreach N + overdue follow-ups."""
    limit = limit or config.SPONSOR_OUTREACH_PER_DAY
    data = load(path)
    today = date.today().isoformat()
    fresh = [r for r in data["prospects"] if r.get("stage") == "new"]
    fresh.sort(key=lambda r: r.get("created", ""))
    followups = [r for r in data["prospects"]
                 if r.get("stage") in OPEN_STAGES and r.get("next_followup")
                 and r["next_followup"] <= today and r.get("stage") != "new"]
    followups.sort(key=lambda r: r.get("next_followup", ""))
    return {"outreach": fresh[:limit], "followups": followups,
            "pipeline": data["prospects"]}


def forecast(path: Optional[Path] = None) -> Dict:
    data = load(path)
    open_rows = [r for r in data["prospects"] if r.get("stage") in OPEN_STAGES]
    won = [r for r in data["prospects"] if r.get("stage") == "won"]
    pipeline_value = sum(int(r.get("value", 0)) for r in open_rows)
    expected = sum(int(r.get("value", 0)) * STAGES.get(r.get("stage", "new"), 0)
                   for r in open_rows)
    won_value = sum(int(r.get("value", 0)) for r in won)
    lost = len([r for r in data["prospects"] if r.get("stage") == "lost"])
    closed = len(won) + lost
    return {"prospects": len(data["prospects"]), "open": len(open_rows),
            "pipeline_value": pipeline_value, "expected_value": round(expected),
            "won_value": won_value, "won": len(won), "lost": lost,
            "win_rate": round(len(won) / closed, 2) if closed else 0.0}


def outreach_message(prospect: Dict) -> str:
    """Ready-to-send template (Telugu + English mix) — rates rate_card nunchi."""
    pkg = rate_card.full_package_price()
    slot = rate_card.highest_ticket()
    name = prospect.get("name", "")
    ptype = prospect.get("type", "")
    hook = {
        "college": "admissions season lo mee college courses ni TS/AP students ki chupinchadaniki",
        "coaching": "mee coaching batch/course ni exam-prep students ki reach cheyyadaniki",
        "hostel": "city ki vachhe students ki mee hostel rooms chupinchadaniki",
        "bookshop": "exam books/material ni students ki direct ga chupinchadaniki",
        "online-course": "mee test series/course ki qualified student leads kosam",
        "bank-loan": "education loan ni scholarship-season students ki reach cheyyadaniki",
        "hospital": "student health checkups/campus offers promote cheyyadaniki",
        "shop": "campus area students ki mee shop offers chupinchadaniki",
    }.get(ptype, "mee services ni studentup.in readers ki reach cheyyadaniki")
    return (
        f"Namaste {name} garu 🙏\n\n"
        f"studentup.in — Telangana/AP students kosam jobs, scholarships, results, "
        f"exam updates publish chese site. Roju kotha posts + Telegram channel tho "
        f"active student audience undi.\n\n"
        f"{hook}, manam ee options chudagalam:\n"
        f"• Sponsored article (mee gurinchi full guide) — ₹{slot:,}+\n"
        f"• Banner slots (home + category) — packages ₹{pkg:,} nunchi\n"
        f"• Qualified student leads (interest unna vallu, direct contact) — per-lead deal\n\n"
        f"Meeru cheppandi — okka call/WhatsApp lo details pampistanu. "
        f"Mediation ki SPONSORED label + policy-safe formats matrame vaadatham.\n\n"
        f"— studentup.in team"
    )


def report_text(plan: Dict, fc: Dict) -> str:
    lines = ["<b>🤝 SPONSOR PIPELINE (roju pani)</b>",
             f"pipeline ₹{fc['pipeline_value']:,} · expected ₹{fc['expected_value']:,} "
             f"· won ₹{fc['won_value']:,} ({fc['won']} deals)",
             ""]
    if plan["outreach"]:
        lines.append(f"<b>Ippudu contact cheyyandi ({len(plan['outreach'])}):</b>")
        for r in plan["outreach"]:
            lines.append(f"  • {r['name']} ({r.get('type') or '—'}, "
                         f"{r.get('city') or '—'}) — {r.get('contact') or 'contact ledu'}")
    if plan["followups"]:
        lines.append(f"<b>Follow-up overdue ({len(plan['followups'])}):</b>")
        for r in plan["followups"]:
            lines.append(f"  • {r['name']} — stage {r['stage']} — due {r.get('next_followup')}")
    if not plan["outreach"] and not plan["followups"]:
        lines.append("Pipeline khali — `--sponsor-add` tho prospects add cheyandi "
                     "(`--sponsor-targets` list chudandi).")
    lines.append("")
    lines.append("Note: messages manual ga pampali — ee tool plan + templates istundi.")
    return "\n".join(lines)


# --------------------------------------------------------------------- CLI

def run_cli(notify: bool = False, limit: int = 0, templates: bool = False) -> int:
    print("=" * 74)
    print("  🤝 SPONSOR PIPELINE (v181) — direct sales = highest revenue lever")
    print("=" * 74)
    plan = today_plan(limit=limit or None)
    fc = forecast()
    print(f"  prospects {fc['prospects']} · open {fc['open']} · "
          f"pipeline ₹{fc['pipeline_value']:,} · expected ₹{fc['expected_value']:,}")
    print(f"  won ₹{fc['won_value']:,} ({fc['won']}) · lost {fc['lost']} · "
          f"win rate {fc['win_rate'] * 100:.0f}%")
    print("-" * 74)
    if plan["outreach"]:
        print(f"  📞 Ippudu contact cheyyandi ({len(plan['outreach'])}):")
        for r in plan["outreach"]:
            print(f"     • {r['name']} · {r.get('type') or '—'} · {r.get('city') or '—'}"
                  f" · {r.get('contact') or 'contact ledu'}")
            if templates:
                print("       --- message ---")
                for line in outreach_message(r).splitlines():
                    print("       " + line)
                print("       ----------------")
    if plan["followups"]:
        print(f"  ⏰ Follow-up overdue ({len(plan['followups'])}):")
        for r in plan["followups"]:
            print(f"     • {r['name']} — {r['stage']} — due {r.get('next_followup')}"
                  f" — {r.get('notes', '')[:60]}")
    if not plan["outreach"] and not plan["followups"]:
        print("  ℹ️  Pipeline khali. Start:")
        print("     1) python run.py --sponsor-targets      (evarini contact cheyyali)")
        print("     2) python run.py --sponsor-add \"Sri Coaching|coaching|Hyderabad|9848012345|8000\"")
        print("     3) python run.py --sponsor-crm --notify (roju Telegram plan)")
    print("-" * 74)
    print(f"  file: {config.SPONSOR_PIPELINE_PATH}")
    if notify:
        from . import notifier

        ok = notifier.send_telegram(report_text(plan, fc))
        print(f"  📨 Telegram: {'pampamu' if ok else 'skip (token/chat ledu)'}")
    return 0


def targets_cli() -> int:
    print("=" * 74)
    print("  🎯 SPONSOR TARGET TYPES (evarini contact cheyyali)")
    print("=" * 74)
    for ptype, why in TARGET_TYPES:
        print(f"  • {ptype:14s} {why}")
    print("-" * 74)
    print("  Search strings (Google Maps / JustDial lo veetini vethakandi):")
    for q in ("junior college admissions Hyderabad contact",
              "SSC coaching centre Vijayawada phone",
              "student hostel near Osmania University",
              "competitive exam books shop Telangana",
              "online test series for TSPSC contact"):
        print(f"    - {q}")
    print("-" * 74)
    print("  Add cheyyadam: python run.py --sponsor-add \"Name|type|city|contact|value\"")
    return 0
