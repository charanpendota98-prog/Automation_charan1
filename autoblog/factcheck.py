# -*- coding: utf-8 -*-
"""v161 — Draft ↔ source fact cross-check.

Jobs/results site ki అతి pedda risk: **tappu date, tappu vacancy count, tappu
fee**. Student aa date nammi apply cheyyakapothe, adi manaki traffic loss
kaadu — aa student ki nijamaina nashtam. Google ki kuda adi YMYL content,
inaccuracy ni kashtanga chustundi.

Ee module draft lo cheppina hard facts ni **cited source text tho** compare
chestundi:

    MATCH      — source lo exact ga undi
    CONFLICT   — source lo veru value undi  (idi publish blocker)
    NOT FOUND  — source lo ee fact ledu     (verify cheyandi / source marchandi)

Idi LLM kaadu, guess kaadu — plain text comparison. Source text lo ledante
"tappu" ani cheppadu, "nenu confirm cheyyalekapoయాను" ani cheptundi. Adi
nijayathi.

CLI:  python run.py --factcheck draft.html --against source.txt
"""
from __future__ import annotations

import html as _html
import re
from pathlib import Path
from typing import Dict, List, Optional

_TAG = re.compile(r"<[^>]+>")
_WS = re.compile(r"\s+")

MONTHS = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}

_DATE_PATTERNS = (
    re.compile(r"\b(20\d{2})-(\d{2})-(\d{2})\b"),
    re.compile(r"\b(\d{1,2})[ /-]([A-Za-z]{3,9})[ /-](20\d{2})\b"),
    re.compile(r"\b([A-Za-z]{3,9})[ ]+(\d{1,2}),?[ ]+(20\d{2})\b"),
)

_MONEY = re.compile(r"(?:Rs\.?|INR|₹)\s?(\d[\d,]*)", re.I)
_VACANCY = re.compile(r"\b(\d{1,3}(?:,\d{3})+|\d{2,6})\s*(?:posts?|vacanc\w*)", re.I)


def text_of(html: str) -> str:
    return _WS.sub(" ", _html.unescape(_TAG.sub(" ", html))).strip()


def _norm_num(raw: str) -> int:
    return int(raw.replace(",", ""))


def dates(text: str) -> List[str]:
    """Normalised ISO dates found in text (order preserved, deduped)."""
    out: List[str] = []
    for pat in _DATE_PATTERNS:
        for m in pat.finditer(text):
            g = m.groups()
            try:
                if pat is _DATE_PATTERNS[0]:
                    y, mo, d = int(g[0]), int(g[1]), int(g[2])
                elif pat is _DATE_PATTERNS[1]:
                    d, mo, y = int(g[0]), MONTHS.get(g[1][:3].lower(), 0), int(g[2])
                else:
                    mo, d, y = MONTHS.get(g[0][:3].lower(), 0), int(g[1]), int(g[2])
            except (ValueError, TypeError):
                continue
            if not (1 <= mo <= 12 and 1 <= d <= 31):
                continue
            iso = f"{y:04d}-{mo:02d}-{d:02d}"
            if iso not in out:
                out.append(iso)
    return out


def amounts(text: str) -> List[int]:
    seen: List[int] = []
    for m in _MONEY.finditer(text):
        val = _norm_num(m.group(1))
        if val not in seen:
            seen.append(val)
    return seen


def vacancies(text: str) -> List[int]:
    seen: List[int] = []
    for m in _VACANCY.finditer(text):
        val = _norm_num(m.group(1))
        if val not in seen:
            seen.append(val)
    return seen


NEAR_DAYS = 45          # ee lopu unna date = same fact, tappu ga raasaru
NEAR_RATIO = 0.15       # ee lopu unna number = same fact, digit tappu


def _near(claimed, candidate, kind: str) -> bool:
    """Rendu values *oke fact* ni cheptunnaya ani reasonable guess.

    Notification lo chala dates untayi (start, last, exam, result) — andhuke
    "source lo vere date undi" ante conflict kaadu. Kani claimed date source
    lo unna date ki chala daggara unte, adi same fact ni tappuga raasinattu
    (15 vs 20 October) — adi ne nijamaina conflict.
    """
    if kind == "date":
        from datetime import date as _d
        try:
            a = _d(*[int(x) for x in claimed.split("-")])
            b = _d(*[int(x) for x in candidate.split("-")])
        except (ValueError, TypeError):
            return False
        return 0 < abs((a - b).days) <= NEAR_DAYS
    try:
        a, b = float(claimed), float(candidate)
    except (TypeError, ValueError):
        return False
    if a == 0 or b == 0:
        return False
    return 0 < abs(a - b) / max(a, b) <= NEAR_RATIO


def _verdict(claimed, found_in_source: List, kind: str) -> Dict:
    """One claim vs the whole source list."""
    if claimed is None:
        return {"kind": kind, "claimed": None, "status": "ABSENT",
                "note": "draft lo ee fact ledu"}
    if claimed in found_in_source:
        return {"kind": kind, "claimed": claimed, "status": "MATCH",
                "note": "source lo same value undi"}

    near = [c for c in found_in_source if _near(claimed, c, kind)]
    if near:
        return {"kind": kind, "claimed": claimed, "status": "CONFLICT",
                "note": f"source lo daggarlo unnadi: {near[:3]} — okati tappu"}

    return {"kind": kind, "claimed": claimed, "status": "NOT_FOUND",
            "note": "source text lo ee value ledu — verify cheyandi"}


def check(draft_html: str, source_html: str) -> Dict:
    d_text, s_text = text_of(draft_html), text_of(source_html)

    d_dates, s_dates = dates(d_text), dates(s_text)
    d_money, s_money = amounts(d_text), amounts(s_text)
    d_vac, s_vac = vacancies(d_text), vacancies(s_text)

    rows: List[Dict] = []
    # Draft lo cheppina prati date/amount/vacancy ni check chestam - okati
    # matrame kaadu, endukante tappu okate chotla undakapovachu.
    for value in d_dates:
        rows.append(_verdict(value, s_dates, "date"))
    for value in d_money:
        rows.append(_verdict(value, s_money, "amount"))
    for value in d_vac:
        rows.append(_verdict(value, s_vac, "vacancies"))

    if not rows:
        rows.append({"kind": "any", "claimed": None, "status": "ABSENT",
                     "note": "draft lo checkable hard fact ye ledu"})

    conflicts = [r for r in rows if r["status"] == "CONFLICT"]
    unverified = [r for r in rows if r["status"] == "NOT_FOUND"]
    matched = [r for r in rows if r["status"] == "MATCH"]

    return {
        "rows": rows,
        "conflicts": conflicts,
        "unverified": unverified,
        "matched": matched,
        "publishable": not conflicts,
        "source_empty": len(s_text) < 200,
    }


def run_cli(draft: str, against: str = "") -> int:
    d = Path(draft)
    if not d.exists():
        print(f"  ❌ draft dorakaledu: {draft}")
        return 1
    if not against:
        print("  ❌ --against <source file> ivvandi (official notification text/html)")
        return 1
    s = Path(against)
    if not s.exists():
        print(f"  ❌ source dorakaledu: {against}")
        return 1

    rep = check(d.read_text(encoding="utf-8", errors="ignore"),
                s.read_text(encoding="utf-8", errors="ignore"))

    print("=" * 74)
    print(f"  FACT CROSS-CHECK — {d.name}  ↔  {s.name}")
    print("=" * 74)
    if rep["source_empty"]:
        print("  ⚠️  source text chala chinnadi — PDF extract sariga avvaledemo.")
    icon = {"MATCH": "✅", "CONFLICT": "❌", "NOT_FOUND": "⚠️", "ABSENT": "·"}
    for r in rep["rows"]:
        print(f"  {icon[r['status']]} {r['kind']:10s} {str(r['claimed']):<14} {r['note']}")
    print("-" * 74)
    print(f"  matched {len(rep['matched'])} · unverified {len(rep['unverified'])} "
          f"· conflicts {len(rep['conflicts'])}")
    if rep["conflicts"]:
        print("  ❌ PUBLISH VADDU — source tho conflict unna facts unnayi.")
        return 1
    if rep["unverified"]:
        print("  ⚠️  Publish cheyyochu, kani unverified facts manually confirm cheyandi.")
        return 0
    print("  ✅ Draft lo unna hard facts anni source lo confirm ayyayi.")
    return 0
