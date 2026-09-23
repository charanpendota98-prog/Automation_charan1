# -*- coding: utf-8 -*-
"""v106 — search-intent map and content-cannibalization audit.

Multiple pages targeting the same intent split signals and confuse users.
This is an audit/recommendation engine, never an automatic destructive merge.
"""
from __future__ import annotations

import re
import sqlite3
from pathlib import Path
from typing import Dict, List
from urllib.parse import urlparse

from . import config

_STOP = {"the", "and", "for", "with", "from", "how", "what", "2024", "2025", "2026", "2027",
         "telugu", "complete", "details", "latest", "guide", "online"}
_INTENTS = {
    "notification": ("notification", "recruitment", "vacancy", "jobs", "job"),
    "apply": ("apply", "application", "registration", "fee", "online"),
    "eligibility": ("eligibility", "qualification", "age", "criteria"),
    "syllabus": ("syllabus", "pattern", "subjects", "previous", "papers"),
    "hall-ticket": ("hall", "ticket", "admit", "card"),
    "result": ("result", "score", "merit", "cutoff", "cut-off"),
    "scholarship": ("scholarship", "stipend", "fellowship"),
    "current-affairs": ("current", "affairs", "today", "news"),
}


def tokens(text: str) -> set:
    return {x for x in re.findall(r"[a-z0-9\u0c00-\u0c7f]+", (text or "").lower())
            if len(x) > 2 and x not in _STOP}


def intent(title: str) -> str:
    t = (title or "").lower()
    # Explicit entity/topic words outrank generic action words such as
    # "apply" or "online" ("NSP Scholarship Apply Online" = scholarship).
    for strong in ("scholarship", "hall ticket", "admit card", "result", "syllabus"):
        if strong in t:
            return {"hall ticket": "hall-ticket", "admit card": "hall-ticket"}.get(strong, strong)
    hits = [(name, sum(1 for word in words if word in t)) for name, words in _INTENTS.items()]
    name, score = max(hits, key=lambda x: x[1])
    return name if score else "general"


def _similar(a: set, b: set) -> float:
    return round(len(a & b) / max(1, len(a | b)), 3)


def analyze(posts: List[Dict], threshold: float = 0.55) -> Dict:
    rows = []
    for p in posts or []:
        title = p.get("title", "")
        rows.append({"id": p.get("id") or p.get("wp_id"), "title": title,
                     "link": p.get("link", ""), "tokens": tokens(title),
                     "intent": intent(title)})
    conflicts = []
    for i, a in enumerate(rows):
        for b in rows[i + 1:]:
            sim = _similar(a["tokens"], b["tokens"])
            same_intent = a["intent"] == b["intent"] and a["intent"] != "general"
            if sim >= threshold or (same_intent and sim >= threshold * 0.72):
                if sim >= threshold or same_intent:
                    recommendation = ("merge_or_301" if sim >= 0.78 else
                                      "choose_pillar_and_canonical" if same_intent else
                                      "separate_intent_with_internal_links")
                    conflicts.append({"a": a["title"], "b": b["title"],
                                      "a_link": a["link"], "b_link": b["link"],
                                      "similarity": sim, "intent": a["intent"] if same_intent else "mixed",
                                      "recommendation": recommendation})
    clusters = {}
    for row in rows:
        clusters.setdefault(row["intent"], []).append(row["title"])
    return {"version": "v106", "pages": len(rows), "conflicts": conflicts,
            "clusters": clusters, "status": "review" if conflicts else "clean"}


def load_state_posts(db_path: Path) -> List[Dict]:
    if not Path(db_path).exists():
        return []
    with sqlite3.connect(str(db_path)) as conn:
        conn.row_factory = sqlite3.Row
        return [dict(r) for r in conn.execute(
            "SELECT wp_id, title, link FROM posts WHERE status='publish' AND wp_id IS NOT NULL"
        ).fetchall()]


def run_cli(threshold: float = 0.55) -> int:
    report = analyze(load_state_posts(config.STATE_PATH), threshold)
    print("=" * 74)
    print(f"  CONTENT CANNIBALIZATION AUDIT: {report['pages']} pages · {len(report['conflicts'])} review pairs")
    print("=" * 74)
    for c in report["conflicts"][:30]:
        print(f"  {c['similarity']:.0%} · {c['recommendation']} · {c['intent']}")
        print(f"    A: {c['a'][:100]}")
        print(f"    B: {c['b'][:100]}")
    if not report["conflicts"]:
        print("  ✅ No high-risk same-intent pairs found")
    else:
        print("  ⚠️ Recommendations only — no automatic merge/redirect is performed")
    print("-" * 74)
    print("  Intent clusters: " + ", ".join(f"{k}={len(v)}" for k, v in report["clusters"].items()))
    return 0
