# -*- coding: utf-8 -*-
"""v158 — AEO (Answer Engine Optimisation) engine.

Google AI Overviews, featured snippets, Bing Copilot and ChatGPT browsing all
lift the *same* three things out of a page:

  1. a short, self-contained answer near the top (40-55 words is the band that
     actually gets pulled into a snippet),
  2. a clean ordered "how to apply" step list,
  3. hard numbers (vacancies, salary, fee, last date) stated as plain text.

This module audits a post for those three, and builds HowTo JSON-LD from the
step list when - and only when - real steps exist.

Important: it never invents a step, a number or an answer. If the post does
not contain them, it reports them missing so the writer/bot adds them. A
fabricated HowTo is a schema violation and a lie to the reader.

CLI:  python run.py --aeo [path/to/post.html]
"""
from __future__ import annotations

import html as _html
import json
import re
from pathlib import Path
from typing import Dict, List, Optional

ROOT = Path(__file__).resolve().parent.parent

SNIPPET_MIN_WORDS = 40
SNIPPET_MAX_WORDS = 55
MIN_STEPS = 3
MAX_STEPS = 12

_TAG = re.compile(r"<[^>]+>")
_WS = re.compile(r"\s+")

# Headings that introduce the application procedure.
_APPLY_HEAD = re.compile(
    r"(how\s+to\s+apply|apply\s+online|application\s+process|"
    r"దరఖాస్తు|అప్లై)", re.I)

# Every pattern carries its own *context word*. Without that, "Rs 200" (the
# application fee) gets reported as the salary and a stray "2026" gets
# reported as the last date - a wrong fact is worse than a missing one.
_MONTH = r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*"
_RS = r"(?:Rs\.?|INR|₹)\s?\d[\d,]{3,}"

_FACT_PATTERNS = {
    "vacancies": re.compile(
        r"\b(?:\d{1,3}(?:,\d{3})+|\d{2,6})\s*(?:posts?|vacanc\w*|ఖాళీ)", re.I),
    "salary": re.compile(
        r"(?:salary|pay\s*scale|payscale|stipend|జీతం)[^.]{0,40}?" + _RS
        + r"|" + _RS + r"[^.]{0,25}?(?:per\s*month|p\.?m\.?|salary)", re.I),
    "fee": re.compile(
        r"(?:fee|ఫీజు)[^.]{0,40}?"
        r"(?:(?:Rs\.?|INR|₹)\s?\d[\d,]*|free|no\s+fee|nil)", re.I),
    "last_date": re.compile(
        r"(?:last\s*date|deadline|closes?\s*on|apply\s*(?:on|by|before|upto|until)|"
        r"varaku|చివరి\s*తేదీ)[^.]{0,40}?"
        r"(?:20\d{2}-\d{2}-\d{2}|\d{1,2}\s+" + _MONTH + r"\s+20\d{2}|"
        + _MONTH + r"\s+\d{1,2},?\s*20\d{2})", re.I),
}


def _text(html: str) -> str:
    return _WS.sub(" ", _html.unescape(_TAG.sub(" ", html))).strip()


def _words(text: str) -> int:
    return len([w for w in text.split() if w.strip()])


# ---------------------------------------------------------------- answer ---
def quick_answer(html: str) -> Dict:
    """First substantial paragraph = the snippet candidate."""
    for m in re.finditer(r"<p[^>]*>(.*?)</p>", html, re.S | re.I):
        body = _text(m.group(1))
        if _words(body) >= 12:
            n = _words(body)
            return {
                "found": True,
                "text": body,
                "words": n,
                "snippet_ready": SNIPPET_MIN_WORDS <= n <= SNIPPET_MAX_WORDS,
            }
    return {"found": False, "text": "", "words": 0, "snippet_ready": False}


# ----------------------------------------------------------------- steps ---
def extract_steps(html: str) -> List[str]:
    """Ordered steps that sit under a 'how to apply' heading.

    Returns [] when the post has no such section - callers must treat that as
    'no HowTo schema', never as 'make one up'.
    """
    heads = list(re.finditer(r"<h([2-4])[^>]*>(.*?)</h\1>", html, re.S | re.I))
    for i, h in enumerate(heads):
        if not _APPLY_HEAD.search(_text(h.group(2))):
            continue
        end = heads[i + 1].start() if i + 1 < len(heads) else len(html)
        block = html[h.end():end]
        ol = re.search(r"<ol[^>]*>(.*?)</ol>", block, re.S | re.I)
        source = ol.group(1) if ol else block
        items = [_text(x) for x in re.findall(r"<li[^>]*>(.*?)</li>", source, re.S | re.I)]
        items = [x for x in items if len(x) >= 8]
        if len(items) >= MIN_STEPS:
            return items[:MAX_STEPS]
        return []
    return []


def howto_schema(title: str, steps: List[str], url: str = "") -> Optional[Dict]:
    """HowTo JSON-LD - only with >= MIN_STEPS real steps."""
    if len(steps) < MIN_STEPS:
        return None
    node = {
        "@context": "https://schema.org",
        "@type": "HowTo",
        "name": title.strip()[:110] or "How to apply",
        "step": [
            {"@type": "HowToStep", "position": i + 1, "text": s[:300]}
            for i, s in enumerate(steps)
        ],
    }
    if url:
        node["@id"] = url.rstrip("/") + "#howto"
    return node


# ----------------------------------------------------------------- facts ---
def key_facts(html: str) -> Dict[str, Optional[str]]:
    """Hard numbers actually present in the text. Missing -> None, not a guess."""
    text = _text(html)
    out: Dict[str, Optional[str]] = {}
    for name, pat in _FACT_PATTERNS.items():
        m = pat.search(text)
        out[name] = m.group(0).strip() if m else None
    return out


# ----------------------------------------------------------------- audit ---
def audit(html: str, title: str = "", url: str = "") -> Dict:
    qa = quick_answer(html)
    steps = extract_steps(html)
    facts = key_facts(html)
    present = [k for k, v in facts.items() if v]
    missing = [k for k, v in facts.items() if not v]

    issues: List[str] = []
    if not qa["found"]:
        issues.append("no opening paragraph to use as the snippet answer")
    elif not qa["snippet_ready"]:
        issues.append(
            f"opening answer is {qa['words']} words - snippets favour "
            f"{SNIPPET_MIN_WORDS}-{SNIPPET_MAX_WORDS}")
    if not steps:
        issues.append(f"no 'how to apply' ordered list with >= {MIN_STEPS} steps -> no HowTo schema")
    for key in missing:
        issues.append(f"key fact missing in the text: {key}")

    scored = 0
    scored += 40 if qa["snippet_ready"] else (15 if qa["found"] else 0)
    scored += 30 if steps else 0
    scored += int(30 * len(present) / max(1, len(facts)))

    return {
        "score": scored,
        "quick_answer": qa,
        "steps": steps,
        "howto": howto_schema(title, steps, url),
        "facts": facts,
        "facts_present": present,
        "facts_missing": missing,
        "issues": issues,
    }


# ------------------------------------------------------------------- cli ---
_SAMPLE = """
<p>TSPSC Group 2 notification 2026 released 783 posts ki. Degree complete ayina
candidates October 15 varaku online apply cheyyochu, application fee Rs 200,
and starting salary Rs 40,000 per month untundi ee posts ki andariki.</p>
<h2>How to apply online</h2>
<ol><li>Official website tspsc.gov.in open cheyandi</li>
<li>One Time Registration complete cheyandi</li>
<li>Group 2 notification link click chesi form fill cheyandi</li>
<li>Fee Rs 200 pay chesi submit cheyandi</li></ol>
"""


def run_cli(path: str = "") -> int:
    if path:
        p = Path(path)
        if not p.exists():
            print(f"  ❌ file dorakaledu: {path}")
            return 1
        html = p.read_text(encoding="utf-8", errors="ignore")
        title = p.stem.replace("-", " ").title()
        label = str(p)
    else:
        html, title, label = _SAMPLE, "TSPSC Group 2 2026", "built-in sample"

    rep = audit(html, title)
    print("=" * 70)
    print(f"  AEO AUDIT (AI Overviews / featured snippets) — {label}")
    print("=" * 70)
    qa = rep["quick_answer"]
    mark = "✅" if qa["snippet_ready"] else "⚠️"
    print(f"  {mark} quick answer: {qa['words']} words "
          f"(target {SNIPPET_MIN_WORDS}-{SNIPPET_MAX_WORDS})")
    print(f"  {'✅' if rep['steps'] else '⚠️'} apply steps: {len(rep['steps'])}")
    for k, v in rep["facts"].items():
        print(f"  {'✅' if v else '⚠️'} {k}: {v or 'text lo ledu'}")
    if rep["issues"]:
        print("-" * 70)
        for i in rep["issues"]:
            print(f"    → {i}")
    if rep["howto"]:
        print("-" * 70)
        print("  HowTo JSON-LD (real steps nunchi ne):")
        print(json.dumps(rep["howto"], ensure_ascii=False)[:400] + " …")
    print("-" * 70)
    print(f"  AEO score: {rep['score']}/100")
    print("  Note: idi markup readiness. Ranking Google decide chestundi.")
    return 0
