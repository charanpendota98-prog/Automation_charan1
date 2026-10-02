# -*- coding: utf-8 -*-
"""v182 — BACKLINK / AUTHORITY ENGINE (white-hat only).

Nijam: rankings ki **links + brand mentions** kavali. Mee daggara inka ee loop
ledu — adi pedda gap. Ee module link *kone* pani cheyyadu (adi Google policy
violation — site ni index nunchi teeseskovachu). Idi chesedi:

  1. **Link-worthy assets** (mee own data nunchi) — ivvikalu manam generate
     cheyyagalige, insanlu link cheyyadam ishta padalsina pages:
     · live job/scholarship tracker (roju update avutundi)
     · deadline calendar (.ics + page)
     · district-wise opportunity map
     · free calculators (age/fee/score/resume — theme lo already unnayi)
     · original stats/data stories (mee state.db + GSC nunchi)
  2. **Outreach targets** — evariki pampali (college placement cells, libraries,
     student Telegram/WhatsApp groups, local news desks, YouTube educators,
     coaching blogs, Quora/Reddit answers) + search strings evari contact kosam.
  3. **Pipeline tracking** — stages + next follow-up + forecast (link count).
  4. **Ready message templates** (Telugu/English) — asset link pampi mention
     adagadam, honest ga ("free resource, mee students ki use avutundi").

Rules (code lo hard):
  * No paid links · no PBN · no link exchange spam · no auto-blast messaging.
    Messages meeru chusi pampali — tool plan + template + reminder istundi.
  * No guarantees: link earning time + editor batti untundi.

CLI:
    python run.py --backlink                              # plan + assets + forecast
    python run.py --backlink-assets                       # link-worthy asset ideas
    python run.py --backlink-targets                      # evarini contact cheyyali
    python run.py --backlink-add "Sri College Placement Cell|college|Hyd|mail@x|/jobs-tracker/"
    python run.py --backlink-update "Sri College Placement Cell|outreach|pampamu|2026-10-05"
    python run.py --backlink-notify
"""
from __future__ import annotations

import json
import logging
from datetime import date, timedelta
from pathlib import Path
from typing import Dict, List, Optional

from . import config

log = logging.getLogger("autoblog.backlink_engine")

STAGES: Dict[str, float] = {
    "idea": 0.05, "asset_ready": 0.15, "outreach": 0.35,
    "mentioned": 0.70, "linked": 1.00, "lost": 0.0, "paused": 0.0,
}
OPEN_STAGES = ("idea", "asset_ready", "outreach", "mentioned")

# Target types — evariki outreach (all white-hat, organic)
TARGET_TYPES = [
    ("college", "College placement cells / student clubs — free resource link"),
    ("library", "Public/college libraries — exam resources page"),
    ("teacher", "School/college teachers — Telugu study resource groups"),
    ("newsdesk", "Local news desks — data story (exam seasons lo)"),
    ("youtuber", "Telugu edu YouTubers — description lo resource link"),
    ("coaching", "Coaching institutes — free tools page (no payment for link)"),
    ("community", "Student Telegram/WhatsApp/Discord groups — resource share"),
    ("forum", "Quora/Reddit answers — genuinely helpful replies with source"),
    ("govt", "District education offices / MeeSeva help desks — info pages"),
    ("blog", "Telugu education blogs — guest data contribution"),
]


def _path(path: Optional[Path] = None) -> Path:
    return Path(path or config.BACKLINK_PIPELINE_PATH)


def load(path: Optional[Path] = None) -> Dict:
    p = _path(path)
    if not p.exists():
        return {"updated": "", "targets": [], "activity": []}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        data.setdefault("targets", [])
        data.setdefault("activity", [])
        return data
    except (OSError, ValueError):
        return {"updated": "", "targets": [], "activity": []}


def save(data: Dict, path: Optional[Path] = None) -> Path:
    p = _path(path)
    data["updated"] = date.today().isoformat()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    return p


def _find(data: Dict, name: str) -> Optional[Dict]:
    key = (name or "").strip().lower()
    for row in data["targets"]:
        if (row.get("name", "") or "").strip().lower() == key:
            return row
    return None


def add(name: str, ttype: str = "", city: str = "", contact: str = "",
        asset: str = "", path: Optional[Path] = None) -> Dict:
    if not (name or "").strip():
        raise ValueError("target name khali")
    data = load(path)
    if _find(data, name):
        raise ValueError(f"'{name}' already undi — --backlink-update vaadandi")
    row = {"name": name.strip(), "type": (ttype or "").strip().lower(),
           "city": (city or "").strip(), "contact": (contact or "").strip(),
           "asset": (asset or "").strip(), "stage": "asset_ready" if asset else "idea",
           "created": date.today().isoformat(),
           "next_followup": date.today().isoformat(), "notes": ""}
    data["targets"].append(row)
    data["activity"].append({"date": row["created"], "name": row["name"],
                             "stage": row["stage"], "note": "added"})
    save(data, path)
    return row


def update(name: str, stage: str = "", note: str = "", followup: str = "",
           asset: str = "", path: Optional[Path] = None) -> Dict:
    data = load(path)
    row = _find(data, name)
    if not row:
        raise ValueError(f"'{name}' pipeline lo ledu — --backlink-add cheyandi")
    if stage:
        st = stage.strip().lower()
        if st not in STAGES:
            raise ValueError(f"stage tappu: {stage} (ok: {', '.join(STAGES)})")
        row["stage"] = st
    if asset:
        row["asset"] = asset.strip()
        if row["stage"] == "idea":
            row["stage"] = "asset_ready"
    if note:
        row["notes"] = (row.get("notes", "") + " | " + note.strip()).strip(" |")
    if followup:
        date.fromisoformat(followup)
        row["next_followup"] = followup
    elif stage in ("outreach", "mentioned"):
        row["next_followup"] = (date.today() +
                                timedelta(days=config.BACKLINK_FOLLOWUP_DAYS)).isoformat()
    data["activity"].append({"date": date.today().isoformat(), "name": row["name"],
                             "stage": row["stage"], "note": note or stage or "update"})
    data["activity"] = data["activity"][-500:]
    save(data, path)
    return row


def assets() -> List[Dict]:
    """Link-worthy assets — mee data nunchi generate cheyyagalige vi."""
    try:
        from . import config as cfg

        cats = len(cfg.CATEGORIES)
    except Exception:  # noqa: BLE001
        cats = 18
    return [
        {"kind": "tracker", "title": "Live Govt Job Tracker (TS · AP · Central)",
         "why": "Roju update avutundi → journalists/colleges/bookmark link cheyyadaniki "
                "best asset (link-worthy by nature).",
         "how": "`run.py --rebuild-hubs` + category archives; 'updated daily' stamp.",
         "effort": "low", "links": "high"},
        {"kind": "calendar", "title": "Exam & Deadline Calendar 2026 (+ .ics export)",
         "why": "Libraries/teachers groups lo share avutundi; .ics file downloads = "
                "natural mentions.",
         "how": "theme `inc/remind.php` .ics + calendar page (already wired).",
         "effort": "low", "links": "medium"},
        {"kind": "data", "title": f"TS/AP Recruitment & Scholarship Trends — original stats",
         "why": "Original data = kotha information → news desks/data writers cite "
                "chestharu (adi mee strongest link magnet).",
         "how": "state.db post counts + `--revenue-loop`/GSC numbers → yearly data story.",
         "effort": "medium", "links": "high"},
        {"kind": "tool", "title": "Free calculators bundle (age · fee · score · resume)",
         "why": "Tools ni colleges/coaching pages embed/link chestayi "
                "(theme lo already unnayi: agecalc/feecalc/scorecalc/resumemaker).",
         "how": "one /tools/ landing page listing all calculators + embed snippet.",
         "effort": "low", "links": "medium"},
        {"kind": "map", "title": "District-wise Opportunity Map (59 districts)",
         "why": "Local relevance → district blogs/colleges link chestayi.",
         "how": "`run.py --district-hubs` pages + map section.",
         "effort": "medium", "links": "medium"},
        {"kind": "guide", "title": f"Definitive guides — {cats} pillars ki okka okka 'best' page",
         "why": "Comprehensive guides ni forums/answers lo reference chestaru; "
                "internal hub authority perugutundi.",
         "how": "`--top-post` engine + hub cross-links (pillar → cluster).",
         "effort": "high", "links": "high"},
    ]


def targets() -> Dict[str, List[str]]:
    return {
        "types": [f"{t} — {why}" for t, why in TARGET_TYPES],
        "search_strings": [
            "junior college placement cell Hyderabad email",
            "degree college library Telangana contact",
            "Telugu education YouTube channel contact email",
            "SSC coaching institute Vijayawada contact",
            "student telegram group Telangana jobs admin",
            "district education officer Warangal contact",
            "Telugu news desk education reporter email",
        ],
        "rules": [
            "No paid links / no PBN / no link exchange spam (Google policy).",
            "Each message personal + genuinely useful (no mass blast).",
            "Only free assets (trackers/tools/data) ni promote cheyyandi.",
            "Follow-up 1 week taruvata — okate reminder, spam ledu.",
        ],
    }


def today_plan(limit: int = 3, path: Optional[Path] = None) -> Dict:
    data = load(path)
    today = date.today().isoformat()
    fresh = [r for r in data["targets"] if r.get("stage") in ("idea", "asset_ready")]
    fresh.sort(key=lambda r: r.get("created", ""))
    followups = [r for r in data["targets"]
                 if r.get("stage") in ("outreach", "mentioned")
                 and r.get("next_followup") and r["next_followup"] <= today]
    followups.sort(key=lambda r: r.get("next_followup", ""))
    return {"outreach": fresh[:limit], "followups": followups, "all": data["targets"]}


def forecast(path: Optional[Path] = None) -> Dict:
    data = load(path)
    open_rows = [r for r in data["targets"] if r.get("stage") in OPEN_STAGES]
    linked = [r for r in data["targets"] if r.get("stage") == "linked"]
    lost = [r for r in data["targets"] if r.get("stage") == "lost"]
    closed = len(linked) + len(lost)
    return {"targets": len(data["targets"]), "open": len(open_rows),
            "expected_links": round(sum(STAGES.get(r.get("stage", "idea"), 0)
                                        for r in open_rows), 2),
            "linked": len(linked), "lost": len(lost),
            "success_rate": round(len(linked) / closed, 2) if closed else 0.0}


def message_template(target: Dict) -> str:
    """Outreach template — honest, useful-first, no link buying."""
    name = target.get("name", "")
    asset = target.get("asset") or "/"
    site = (getattr(config, "WP_SITE", "") or "https://studentup.in").rstrip("/")
    kind = target.get("type", "")
    opening = {
        "college": "mee college students ki use avutundi ani",
        "library": "mee library readers ki reference ga",
        "teacher": "mee students ki practice/resource ga",
        "newsdesk": "data story kosam source ga",
        "youtuber": "mee video description lo students ki resource ga",
        "coaching": "mee students ki free tools ga",
        "community": "group lo students ki share cheyyadaniki",
    }.get(kind, "mee students/readers ki use avutundi ani")
    return (
        f"Namaste {name} garu 🙏\n\n"
        f"Nenu studentup.in nunchi — Telangana/AP students kosam jobs, scholarships, "
        f"results, exam updates publish chestunnam (daily update).\n\n"
        f"{opening}, ee free resource ni share chestunnam:\n"
        f"👉 {site}{asset if asset.startswith('/') else '/' + asset}\n\n"
        f"Idi completely free — no ads-only promo, no payment. Mee students ki "
        f"useful anipisthe mee page/group/video lo link cheyyandi; leda maaku "
        f"suggestions cheppandi (content better cheyyadaniki).\n\n"
        f"Ee resource ni inka useful ga cheyyadaniki em add cheyyali? Cheppandi.\n\n"
        f"— studentup.in team"
    )


def report_text(plan: Dict, fc: Dict) -> str:
    lines = ["<b>🔗 BACKLINK / AUTHORITY (v182)</b>",
             f"targets {fc['targets']} · open {fc['open']} · linked {fc['linked']} "
             f"· expected links {fc['expected_links']}", ""]
    if plan["outreach"]:
        lines.append(f"<b>Reach out ({len(plan['outreach'])}):</b>")
        for r in plan["outreach"]:
            lines.append(f"  • {r['name']} ({r.get('type') or '—'}) → {r.get('asset') or 'asset select'}")
    if plan["followups"]:
        lines.append(f"<b>Follow-ups due ({len(plan['followups'])}):</b>")
        for r in plan["followups"]:
            lines.append(f"  • {r['name']} — {r['stage']} (due {r.get('next_followup')})")
    if not plan["outreach"] and not plan["followups"]:
        lines.append("Pipeline khali — `--backlink-assets` chusi asset select chesi "
                     "`--backlink-add` tho targets add cheyandi.")
    lines.append("")
    lines.append("Rules: no paid links · no PBN · messages manual (tool blast cheyyadu).")
    return "\n".join(lines)


# --------------------------------------------------------------------- CLI

def run_cli(notify: bool = False, limit: int = 3, templates: bool = False) -> int:
    print("=" * 74)
    print("  🔗 BACKLINK / AUTHORITY ENGINE (v182) — white-hat, honest")
    print("=" * 74)
    plan = today_plan(limit=limit)
    fc = forecast()
    print(f"  targets {fc['targets']} · open {fc['open']} · linked {fc['linked']} "
          f"· expected links {fc['expected_links']} · success {fc['success_rate'] * 100:.0f}%")
    print("-" * 74)
    if plan["outreach"]:
        print(f"  📞 Reach out ({len(plan['outreach'])}):")
        for r in plan["outreach"]:
            print(f"     • {r['name']} · {r.get('type') or '—'} · "
                  f"{r.get('contact') or 'contact ledu'} → {r.get('asset') or 'asset select'}")
            if templates:
                print("       --- message ---")
                for line in message_template(r).splitlines():
                    print("       " + line)
                print("       ----------------")
    if plan["followups"]:
        print(f"  ⏰ Follow-ups due ({len(plan['followups'])}):")
        for r in plan["followups"]:
            print(f"     • {r['name']} — {r['stage']} — due {r.get('next_followup')}")
    if not plan["outreach"] and not plan["followups"]:
        print("  ℹ️  Start:")
        print("     1) python run.py --backlink-assets   (link-worthy asset ideas)")
        print("     2) python run.py --backlink-targets  (evarini contact cheyyali)")
        print("     3) python run.py --backlink-add \"Sri College Placement Cell|college|Hyd|mail@x|/jobs-tracker/\"")
    print("-" * 74)
    print(f"  file: {config.BACKLINK_PIPELINE_PATH}")
    print("  honest: link earning time pattutundi; tool plan+templates+reminders istundi.")
    if notify:
        from . import notifier

        ok = notifier.send_telegram(report_text(plan, fc))
        print(f"  📨 Telegram: {'pampamu' if ok else 'skip (token/chat ledu)'}")
    return 0


def assets_cli() -> int:
    print("=" * 74)
    print("  🧲 LINK-WORTHY ASSETS (mee own data nunchi)")
    print("=" * 74)
    for a in assets():
        print(f"  • [{a['kind']:8s}] {a['title']}")
        print(f"      enduku: {a['why']}")
        print(f"      ela:    {a['how']}")
        print(f"      effort {a['effort']} · link potential {a['links']}")
    print("-" * 74)
    print("  Ee assets publish ayyaka `--backlink-add` tho targets add cheyyandi.")
    return 0


def targets_cli() -> int:
    data = targets()
    print("=" * 74)
    print("  🎯 OUTREACH TARGETS + SEARCH STRINGS")
    print("=" * 74)
    for t in data["types"]:
        print(f"  • {t}")
    print("-" * 74)
    print("  Search strings (Google lo veetini vethakandi):")
    for q in data["search_strings"]:
        print(f"    - {q}")
    print("-" * 74)
    print("  Rules (hard):")
    for r in data["rules"]:
        print(f"    ✋ {r}")
    return 0
