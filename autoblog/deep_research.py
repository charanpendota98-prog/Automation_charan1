"""v44 — DEEP POST ENGINE: source tiering + deep fact extraction +
cross-source verification + deep analysis section + perfect-post gate.

Goal: posts that are PERFECT — every date/number cross-checked across
sources, conflicts visible (never silently picked), gaps declared,
confidence measured. Feeds the same research sources the pipeline
already fetches (no extra network needed at publish time).

Layers:
  source_tier()          — T1 official (.gov.in/.edu.in/boards) > T2 major
                           media > T3 other. Deep analysis is T1-weighted.
  extract_facts()        — dates (2 formats, normalized), vacancies, fees,
                           ages, salaries, official links — each with
                           source + context snippet.
  verify_facts()         — cross-source matrix: confirmed / official /
                           single-source / CONFLICT (dates only — number
                           conflicts are usually category variants).
  build_report()         — sources + facts + matrix + gaps + confidence
                           (0–100) + optional NotebookLM brief merge.
  deep_analysis_html()   — visible "In-Depth Analysis" post section
                           (verified facts table + conflict + gap boxes).
  gate_post()/publish_gate() — PERFECT gate: conflicts & date
                           inconsistency & stale years BLOCK live publish;
                           drafts get flags for Telegram review.

CLI: run.py --deep-research "topic" [--research-urls FILE]
        [--research-limit N] [--research-year Y] [--notebooklm-brief FILE]
NotebookLM loop: --research-brief (existing) creates the evidence bundle +
5-pass prompt; --deep-research --deep adds passes 6–8 (year-over-year,
ELI-12, gap priority). Owner runs NotebookLM, saves cited brief, re-runs
with --notebooklm-brief FILE → merged into the deep report.
"""
from __future__ import annotations

import html as _html
import json
import re
from datetime import date
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple
from urllib.parse import urlparse

from . import config
from .sources import SourceArticle

REPO_ROOT = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------- tiering

TIER1_SUFFIXES = (".gov.in", ".nic.in", ".edu.in", ".go.in")
TIER1_HOSTS = {
    "tspsc.gov.in", "appsc.gov.in", "upsc.gov.in", "ssccgl.gov.in",
    "ssc.gov.in", "upsc.nic.in", "nsp.gov.in", "scholarships.gov.in",
    "tsdsc.gov.in", "apdsc.gov.in", "tsbie.ac.in", "apscrb.gov.in",
    "tsgovtjobs.in", "ap.gov.in", "ts.gov.in", "iascsenior.com",
}
TIER2_HOSTS = {
    "tv9telugu.com", "tv9.com", "sakti.com", "telusuko.io", "abplive.com",
    "deccanchronicle.com", "thehindu.com", "indianexpress.com",
    "oneindia.com", "ndtv.com", "economictimes.com", "timesofindia.com",
    "lokmattimes.com", "sakshi.com", "eetelangana.com", "sainikam.com",
}

_MONTHS = {
    "jan": 1, "january": 1, "feb": 2, "february": 2, "mar": 3, "march": 3,
    "apr": 4, "april": 4, "may": 5, "jun": 6, "june": 6, "jul": 7,
    "july": 7, "aug": 8, "august": 8, "sep": 9, "sept": 9, "september": 9,
    "oct": 10, "october": 10, "nov": 11, "november": 11, "dec": 12,
    "december": 12,
}

DATE_LABELS = [
    ("last-date-apply", r"last\s+date|closing\s+date|deadline|apply\s+before|"
                        r"applications?\s+(?:close|closing)|"
                        r"దరఖాస్తు.*?(?:చివర|లిమిట్)"),
    ("exam", r"exam\s*(?:date|will\s+be|to\s+be\s+held)|exam\s+held|"
             r"పరీక్ష.*?తేదీ"),
    ("result", r"result\s*(?:date|declared|will\s+be)|result\s+out|"
               r"ఫలితం"),
    ("interview", r"interview"),
    ("admit", r"admit\s*card|hall\s*ticket"),
    ("counselling", r"counselling|counseling|reporting"),
]

NUM_PATTERNS: List[Tuple[str, str]] = [
    ("vacancy", r"(\d[\d,]*)\s+(?:vacanc(?:y|ies)|posts?|positions?|seats?|"
                r"recruits?)"),
    ("fee", r"(?:application\s+)?fee[s]?\b[^0-9₹]{0,45}"
           r"(?:₹|rs\.?)\s?(\d[\d,\.]*)"),
    ("fee", r"(?:₹|rs\.?)\s?(\d[\d,\.]+)\s*(?:as\s+)?(?:application\s+)?fee"),
    ("age", r"(?:maximum\s+)?age\b[^0-9]{0,30}(\d{1,2}(?:\.\d)?)\s*(?:years?|"
            r"yrs?)"),
    ("salary", r"(?:salary|stipend|pay\s+scale)\b[^0-9₹]{0,45}"
               r"(?:₹|rs\.?)\s?(\d[\d,\.]+(?:\.\d+)?)"),
]


def source_tier(url: str) -> int:
    """1 = official, 2 = major media, 3 = other."""
    try:
        host = urlparse(url).netloc.lower().replace("www.", "")
    except ValueError:
        return 3
    if host in TIER1_HOSTS or any(host.endswith(s) for s in TIER1_SUFFIXES):
        return 1
    if host in TIER2_HOSTS:
        return 2
    return 3


def _domain(url: str) -> str:
    try:
        return urlparse(url).netloc.lower().replace("www.", "")
    except ValueError:
        return ""


# ---------------------------------------------------------------- extraction

def _sentence(text: str, start: int, end: int, width: int = 160) -> str:
    lo = max(0, start - width // 2)
    hi = min(len(text), end + width // 2)
    snippet = re.sub(r"\s+", " ", text[lo:hi]).strip()
    return (snippet[:157] + "…") if len(snippet) > 160 else snippet


def _label_of(text: str, pos: int) -> str:
    """Label from the CURRENT sentence only (previous sentences must not
    leak in — 'applications close on … . The exam will be held on <date>'
    must label as exam, not last-date)."""
    window = text[max(0, pos - 120): pos]
    for boundary in (". ", "! ", "? ", "\n", "। "):
        idx = window.rfind(boundary)
        if idx != -1:
            window = window[idx + len(boundary):]
    window = window.lower()
    for label, pattern in DATE_LABELS:
        if re.search(pattern, window):
            return label
    return "generic"


def _norm_date(day_s: str, mon: str, year_s: str) -> str:
    """Normalize a day + month (name OR number) + year → ISO date."""
    try:
        day = int(day_s)
        y = int(year_s)
    except (TypeError, ValueError):
        return ""
    m = _MONTHS.get(str(mon).lower().strip("."), 0)
    if not m:
        try:
            m = int(str(mon).strip())
        except ValueError:
            return ""
    if not (1 <= day <= 31 and 1 <= m <= 12 and 1990 <= y <= 2099):
        return ""
    try:
        return date(y, m, day).isoformat()
    except ValueError:
        return ""


def extract_facts(items: Sequence[Tuple[str, str, int, str]]
                  ) -> List[Dict]:
    """items = [(source_id, url, tier, text)] → fact list.

    Each fact: {kind, value, norm, label, source_id, tier, domain, snippet}
    """
    facts: List[Dict] = []
    for sid, url, tier, text in items:
        if not text:
            continue
        # dates: "15 October 2026" | "15 Oct 2026"
        for m in re.finditer(
                r"\b(\d{1,2})\s+([A-Za-z]{3,9})\.?\s+(20\d{2})\b", text):
            if m.group(2).lower() not in _MONTHS:
                continue
            norm = _norm_date(m.group(1), m.group(2), m.group(3))
            if not norm:
                continue
            facts.append({
                "kind": "date", "value": " ".join(m.groups()),
                "norm": norm, "label": _label_of(text, m.start()),
                "source_id": sid, "tier": tier, "domain": _domain(url),
                "snippet": _sentence(text, m.start(), m.end()),
            })
        # dates: 15/10/2026 | 15-10-2026
        for m in re.finditer(r"\b(\d{1,2})[/\-](\d{1,2})[/\-](20\d{2})\b",
                             text):
            d, mo, y = m.group(1), m.group(2), m.group(3)
            if "/" in m.group(0) and int(mo) > 12 and int(d) <= 12:
                d, mo = mo, d  # dd/mm vs mm/dd — prefer day-first (India)
            norm = _norm_date(d, str(int(mo)), y)
            if not norm:
                continue
            facts.append({
                "kind": "date", "value": m.group(0), "norm": norm,
                "label": _label_of(text, m.start()), "source_id": sid,
                "tier": tier, "domain": _domain(url),
                "snippet": _sentence(text, m.start(), m.end()),
            })
        # numbers
        for kind, pattern in NUM_PATTERNS:
            for m in re.finditer(pattern, text, re.I):
                facts.append({
                    "kind": kind, "value": m.group(1).replace(",", ""),
                    "norm": m.group(1).replace(",", ""),
                    "label": kind, "source_id": sid, "tier": tier,
                    "domain": _domain(url),
                    "snippet": _sentence(text, m.start(), m.end()),
                })
        # official links
        for m in re.finditer(r"https?://[^\s\"'<>)\]]+?\.(?:gov|nic|edu)\.in"
                             r"[^\s\"'<>)\]]*", text):
            link = m.group(0).rstrip(".,;:")
            facts.append({
                "kind": "official_link", "value": link[:200],
                "norm": link[:200], "label": "official",
                "source_id": sid, "tier": tier, "domain": _domain(url),
                "snippet": _sentence(text, m.start(), m.end(), 80),
            })
    return facts


# ---------------------------------------------------------------- verification

def verify_facts(facts: List[Dict]) -> Dict:
    """Cross-source matrix.

    dates  → confirmed (2+ sources) / official (1× T1) / single / CONFLICT
             (different normalized values under the same label group)
    numbers → confirmed / official / single (no conflict — category variants)
    links  → official
    """
    verified: List[Dict] = []
    conflicts: List[Dict] = []
    seen = set()

    for fact in facts:
        if fact["kind"] == "official_link":
            key = ("link", fact["norm"])
            if key in seen:
                continue
            seen.add(key)
            verified.append({**fact, "status": "official",
                             "sources": [fact["source_id"]]})
            continue
        key = (fact["kind"], fact["label"], fact["norm"])
        if key in seen:
            continue
        seen.add(key)
        same = [f for f in facts
                if (f["kind"], f["label"], f["norm"]) == key]
        srcs = sorted({f["source_id"] for f in same})
        tiers = {f["tier"] for f in same}
        if len(srcs) >= 2:
            status = "confirmed"
        elif 1 in tiers:
            status = "official"
        else:
            status = "single"
        verified.append({**fact, "status": status, "sources": srcs})

    # date conflicts: same label, different normalized values
    by_label: Dict[str, set] = {}
    for f in facts:
        if f["kind"] == "date" and f["label"] != "generic":
            by_label.setdefault(f["label"], set()).add(f["norm"])
    for label, values in sorted(by_label.items()):
        if len(values) > 1:
            members = [f for f in facts if f["kind"] == "date"
                       and f["label"] == label]
            conflicts.append({
                "label": label,
                "values": sorted(values),
                "sources": sorted({f["source_id"] for f in members}),
                "detail": " ".join(
                    f"{f['value']} ({f['source_id']})" for f in members[:4]),
            })
    return {"verified": verified, "conflicts": conflicts}


def confidence_score(matrix: Dict, sources: Sequence[Dict]) -> int:
    verified = matrix["verified"]
    dated = [v for v in verified if v["kind"] in ("date", "vacancy", "fee",
                                                  "age", "salary")]
    score = 40.0
    if sources:
        tier1 = sum(1 for s in sources if s["tier"] == 1)
        score += 20.0 * min(1.0, tier1 / 1.0) * (1.0 if tier1 else 0.0)
    if dated:
        strong = sum(1 for v in dated if v["status"] in ("confirmed", "official"))
        score += 25.0 * (strong / len(dated))
    else:
        score -= 10.0
    if any(v["kind"] == "official_link" for v in verified):
        score += 10.0
    score -= 15.0 * min(len(matrix["conflicts"]), 2)
    if len(sources) < 2:
        score -= 15.0
    return max(0, min(100, int(round(score))))


def detect_gaps(matrix: Dict) -> List[str]:
    have = {(v["kind"], v["label"]) for v in matrix["verified"]}
    gaps = []
    if not any(k == "date" and l == "last-date-apply" for k, l in have):
        gaps.append("apply window / last date not established by any source")
    if not any(k == "official_link" for k, l in have):
        gaps.append("no official (.gov.in/.edu.in) link found in sources")
    if not any(k == "fee" for k, l in have):
        gaps.append("fee not found in sources")
    if not any(k == "age" for k, l in have):
        gaps.append("eligibility age not found in sources")
    if not any(k == "date" and l in ("exam", "result") for k, l in have):
        gaps.append("exam/result date not found in sources")
    return gaps


# ---------------------------------------------------------------- report

def build_report(topic: str,
                 sources: Sequence,
                 notebooklm_brief: str = "",
                 target_year: Optional[int] = None) -> Dict:
    """sources: list[SourceArticle] (or dicts with url/title/text)."""
    norm: List[Dict] = []
    for i, s in enumerate(sources, 1):
        url = getattr(s, "url", None) or (s.get("url", "") if isinstance(s, dict) else "")
        title = getattr(s, "title", "") or (s.get("title", "") if isinstance(s, dict) else "")
        text = getattr(s, "text", "") or (s.get("text", "") if isinstance(s, dict) else "")
        tier = source_tier(url)
        norm.append({"id": f"S{i}", "url": url, "title": title,
                     "domain": _domain(url), "tier": tier, "text": text})
    items = [(s["id"], s["url"], s["tier"], s["text"]) for s in norm]
    facts = extract_facts(items)
    matrix = verify_facts(facts)
    gaps = detect_gaps(matrix)
    report: Dict = {
        "topic": topic,
        "created": date.today().isoformat(),
        "target_year": target_year,
        "sources": [{k: s[k] for k in ("id", "url", "title", "domain", "tier")}
                    for s in norm],
        "facts_total": len(facts),
        "verified": matrix["verified"],
        "conflicts": matrix["conflicts"],
        "gaps": gaps,
        "confidence": confidence_score(matrix, norm),
        "notebooklm": None,
    }
    if notebooklm_brief:
        from . import research_brief
        check = research_brief.validate_editor_brief(
            notebooklm_brief, [s["url"] for s in norm], target_year)
        report["notebooklm"] = check
    return report


# ---------------------------------------------------------------- HTML

def _esc(s: str, quote: bool = True) -> str:
    return _html.escape((s or "").strip(), quote=quote)


_STATUS_BADGE = {
    "confirmed": "✅ Verified (2+ sources)",
    "official": "🏛 Official source",
    "single": "⚠️ Single source — verify",
    "official_link": "🔗 Official link",
}


def deep_analysis_html(report: Dict, max_rows: int = 8) -> str:
    """Visible in-article Deep Analysis section. All text escaped;
    only http(s) links rendered. CLS-safe (static block, no min-height
    games — content height is deterministic)."""
    verified = report.get("verified", [])
    rows = []
    for v in verified:
        if v["kind"] == "official_link":
            continue  # links listed separately below the table
        if len(rows) >= max_rows:
            break
        badge = _STATUS_BADGE.get(v["status"], v["status"])
        srcs = ", ".join(f"S{i[1:]}" for i in v.get("sources", [])[:3])
        snippet = _esc(v.get("snippet", ""))[:180]
        rows.append(
            f'<tr><td title="{snippet}">' + _esc(v.get("value", "")) +
            (f" <em>· {_esc(v.get('label', ''))}</em>"
             if v.get("label") not in ("generic",) else "") +
            f"</td><td>{badge}</td><td>{_esc(srcs)}</td></tr>")
    body = ""
    conf = int(report.get("confidence", 0))
    conf_color = "#168451" if conf >= 75 else ("#b07d1e" if conf >= 50 else "#c23b3b")
    body += (
        '<section class="su-deep" aria-label="In-depth analysis">'
        '<h2 id="deep-analysis">In-Depth Analysis (Deep Analysis) 🔬</h2>'
        f'<p class="su-deep-conf" style="color:{conf_color}">'
        f'📊 Source confidence: <b>{conf}/100</b> — '
        f'{len(report.get("sources", []))} sources cross-checked'
        f'{" · NotebookLM brief merged" if report.get("notebooklm") else ""}'
        '</p>')
    conflicts = report.get("conflicts", [])
    if conflicts:
        items = "".join(
            f'<li><b>{_esc(c["label"])}</b>: ' +
            _esc(" vs ".join(c["values"])) +
            f' <span>({_esc(", ".join(c["sources"]))})</span></li>'
            for c in conflicts[:3])
        body += ('<div class="su-deep-conflict"><b>⛔ Sources disagree — '
                 'official portal lo matrame verify cheyyandi:</b>'
                 f'<ul>{items}</ul></div>')
    if rows:
        body += ('<table class="su-deep-table"><thead><tr><th>Fact</th>'
                 '<th>Status</th><th>Source</th></tr></thead><tbody>'
                 + "".join(rows) + "</tbody></table>")
    links = [v for v in verified if v["kind"] == "official_link"][:4]
    if links:
        items = ""
        for l in links:
            if l["value"].startswith(("http://", "https://")):
                items += (f'<a href="{_esc(l["value"], True)}" target="_blank" '
                          f'rel="noopener">{_esc(_domain(l["value"]))}</a>')
        if items:
            body += (f'<p class="su-deep-links">🏛 Official links: {items}</p>')
    gaps = report.get("gaps", [])
    if gaps:
        items = "".join(f"<li>{_esc(g)}</li>" for g in gaps[:4])
        body += ('<div class="su-deep-gaps"><b>❓ Sources lo ledu (official '
                 f'notification lo confirm cheyandi):</b><ul>{items}</ul></div>')
    nb = report.get("notebooklm")
    if nb:
        if nb.get("ok"):
            body += (f'<p class="su-deep-nb">🧠 NotebookLM cross-check: '
                     f'{nb.get("claims", 0)} cited claims — '
                     'citations editor ni verify chesindi.</p>')
        else:
            body += ('<p class="su-deep-nb">🧠 NotebookLM brief: '
                     + _esc("; ".join(nb.get("problems", []))[:200]) + "</p>")
    body += ("<p class=\"su-deep-disc\">Deep analysis = sources cross-check "
             "summary. Final dates/fees official notification lo verify "
             "cheyyandi — ee summary garunty kaadu.</p></section>")
    return body + DEEP_CSS


DEEP_CSS = """
<style>
.su-deep{margin:26px 0;border:1px solid #E4E9F1;border-left:5px solid #12356B;
  border-radius:14px;padding:16px 18px;background:#F7F9FC}
.su-deep h2{margin:0 0 8px;font-size:19px;color:#12356B}
.su-deep-conf{font-size:13px;margin:4px 0 10px}
.su-deep-table{width:100%;border-collapse:collapse;font-size:13px;
  margin:10px 0}
.su-deep-table th{background:#12356B;color:#fff;text-align:left;
  padding:8px 10px}
.su-deep-table td{padding:7px 10px;border-bottom:1px solid #EDF1F6;
  color:#22303F;vertical-align:top}
.su-deep-table tr:nth-child(even) td{background:#F2F6FB}
.su-deep-conflict{background:#FDF0EF;border:1px solid #F2C4C0;border-left:5px
  solid #C23B3B;border-radius:10px;padding:10px 14px;margin:10px 0;font-size:13px}
.su-deep-conflict ul{margin:6px 0 2px;padding-left:20px}
.su-deep-gaps{background:#F1F6FD;border:1px solid #C9DCF5;border-left:5px
  solid #2463B7;border-radius:10px;padding:10px 14px;margin:10px 0;font-size:13px}
.su-deep-gaps ul{margin:6px 0 2px;padding-left:20px}
.su-deep-links{font-size:13px}
.su-deep-links a{color:#2463B7;font-weight:700;margin-right:10px}
.su-deep-nb{font-size:12px;color:#5A6472}
.su-deep-disc{font-size:11px;color:#8B97A8;margin:8px 0 0}
@media(max-width:600px){.su-deep-table{display:block;overflow-x:auto}
  .su-deep-table table{width:100%}}
body.su-dark .su-deep{background:#182235;border-color:#33445E}
body.su-dark .su-deep h2{color:#E8EEF7}
body.su-dark .su-deep-table td{color:#B9C5D6;background:#202F46}
body.su-dark .su-deep-table tr:nth-child(even) td{background:#1C2E47}
body.su-dark .su-deep-links a{color:#6EA3E8}
</style>
"""


def _bottom_anchor(html: str) -> int:
    for marker in ('<h2 id="read-also"', '<h2 id="related-articles"',
                   '<h2 id="recommended-resources"',
                   '<h2 id="about-this-article"',
                   '<script type="application/ld+json"'):
        idx = html.find(marker)
        if idx != -1:
            return idx
    return len(html)


def inject_deep(html_in: str, report: Dict) -> str:
    """Insert the Deep Analysis section before related/about/JSON-LD."""
    if not report or report.get("facts_total", 0) == 0:
        return html_in
    block = deep_analysis_html(report)
    pos = _bottom_anchor(html_in)
    return html_in[:pos] + "\n" + block + "\n" + html_in[pos:]


# ---------------------------------------------------------------- gates

def gate_post(html: str, report: Dict, live: bool = True) -> Tuple[List[str], List[str]]:
    """(hard_problems, warnings) — the PERFECT post gate.

    hard (block live publish):
      * source conflicts on key dates
      * two different "last date" values inside the final article
      * stale article: date facts exist but none carry the current year
    warnings (flags for draft review):
      * many single-source facts
    """
    hard: List[str] = []
    warn: List[str] = []
    if not report:
        return hard, warn
    if report.get("conflicts"):
        for c in report["conflicts"]:
            hard.append(f"source conflict on '{c['label']}' ("
                        + " vs ".join(c["values"]) + ") — official verify chesi "
                        "fix cheyandi")
    # date consistency inside the final article
    last_dates = set()
    for m in re.finditer(r"last\s+date[^0-9]{0,60}?(\d{1,2}\s+[A-Za-z]{3,9}"
                         r"\s+20\d{2}|\d{1,2}[/\-]\d{1,2}[/\-]20\d{2})",
                         html, re.I):
        raw = m.group(1)
        norm = _norm_from_raw(raw)
        if norm:
            last_dates.add(norm)
    if len(last_dates) > 1:
        hard.append("article lo 2 different 'last date' values unna ("
                    + ", ".join(sorted(last_dates)) + ") — okka canonical date "
                    "matrame undali")
    dated = [v for v in report.get("verified", []) if v["kind"] == "date"]
    if dated:
        current = date.today().year
        if not any(str(current) in v["norm"] for v in dated):
            hard.append("stale dates — sources lo current year ("
                        f"{current}) dates levu; fresh official source ivvandi")
    singles = [v for v in report.get("verified", []) if v["status"] == "single"]
    if len(singles) > 4:
        warn.append(f"{len(singles)} single-source facts — review before "
                    "publish")
    nb = report.get("notebooklm")
    if nb and not nb.get("ok"):
        hard.append("NotebookLM brief validation failed: "
                    + "; ".join(nb.get("problems", []))[:200])
    return hard, warn


def _norm_from_raw(raw: str) -> str:
    m = re.match(r"(\d{1,2})\s+([A-Za-z]{3,9})\.?\s+(20\d{2})", raw.strip())
    if m:
        return _norm_date(m.group(1), m.group(2), m.group(3))
    m = re.match(r"(\d{1,2})[/\-](\d{1,2})[/\-](20\d{2})", raw.strip())
    if m:
        return _norm_date(m.group(1), m.group(2), m.group(3))
    return ""


def publish_gate(article: Dict, html: str = "", live: Optional[bool] = None
                 ) -> Tuple[bool, str]:
    """Live-publish gate for the Deep Post Engine (drafts always pass)."""
    report = article.get("_deep")
    if not report:
        return True, "deep engine off (sources <" \
            f" {getattr(config, 'DEEP_MIN_SOURCES', 2)})"
    if not getattr(config, "DEEP_GATE_STRICT", True):
        return True, "deep gate off"
    if live is None:
        live = (article.get("status") or
                getattr(config, "DEFAULT_POST_STATUS", "draft")) == "publish"
    if not live:
        return True, "draft — deep gate not enforced"
    hard, _warn = gate_post(html, report, live=True)
    if hard:
        return False, ("DEEP GATE: " + "; ".join(hard[:3]))
    return True, (f"deep gate ✔ confidence "
                  f"{report.get('confidence')}/100, "
                  f"{len(report.get('conflicts', []))} conflicts")


# ---------------------------------------------------------------- CLI

def run_cli(topic: str, url_file: str = "", limit: int = 6,
            target_year: Optional[int] = None,
            notebooklm_brief: str = "", deep_prompt: bool = False) -> int:
    from . import research_brief
    print("=" * 74)
    print("  🔬 DEEP POST ENGINE (v44) — deep analyse + cross-verification")
    print("=" * 74)
    try:
        used_year = target_year or research_brief.target_year_from_text(topic)
        query, articles = research_brief.collect_sources(
            topic, url_file=url_file, limit=limit,
            target_year=used_year or target_year)
    except Exception as exc:
        print(f"  ❌ Sources fetch fail: {exc}")
        print("     Official URLs file tho retry: --research-urls FILE")
        return 1
    print(f"  Topic   : {query}")
    print(f"  Sources : {len(articles)} (target year: {used_year or '—'})")
    for i, a in enumerate(articles, 1):
        tier = source_tier(a.url)
        print(f"   S{i} [T{tier}] {a.url[:70]}")
    brief_text = ""
    if notebooklm_brief:
        try:
            brief_text = Path(notebooklm_brief).read_text(encoding="utf-8")
        except OSError as exc:
            print(f"  ⚠️ NotebookLM brief read fail: {exc}")
    report = build_report(query, articles, notebooklm_brief=brief_text,
                          target_year=used_year)
    print("-" * 74)
    print(f"  Facts extracted : {report['facts_total']}")
    statuses: Dict[str, int] = {}
    for v in report["verified"]:
        statuses[v["status"]] = statuses.get(v["status"], 0) + 1
    print("  Verified        : " +
          (", ".join(f"{k}={v}" for k, v in sorted(statuses.items())) or "—"))
    print(f"  Conflicts       : {len(report['conflicts'])}")
    for c in report["conflicts"]:
        print(f"    ⛔ {c['label']}: {' vs '.join(c['values'])}")
    print(f"  Gaps            : {len(report['gaps'])}")
    for g in report["gaps"]:
        print(f"    ❓ {g}")
    print(f"  CONFIDENCE      : {report['confidence']}/100")
    out_dir = Path(getattr(config, "OUTPUT_DIR", REPO_ROOT / "output")) / "deep"
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = re.sub(r"[^a-z0-9]+", "-", query.lower()).strip("-")[:70]
    md = out_dir / f"{stem}-{report['created']}.md"
    js = out_dir / f"{stem}-{report['created']}.json"
    js.write_text(json.dumps(report, ensure_ascii=False, indent=2),
                  encoding="utf-8")
    lines = [f"# Deep Research — {query}",
             f"Created: {report['created']} · Confidence: "
             f"{report['confidence']}/100 · Sources: {len(articles)}", ""]
    lines.append("## Sources")
    for s in report["sources"]:
        lines.append(f"- {s['id']} [T{s['tier']}] {s['url']}")
    lines.append("\n## Verified facts")
    for v in report["verified"][:30]:
        lines.append(f"- [{v['status']}] {v['kind']}/{v['label']}: "
                     f"{v['value']} (S: {', '.join(v['sources'])})")
    lines.append("\n## Conflicts")
    lines += [f"- ⛔ {c['label']}: {' vs '.join(c['values'])}"
              for c in report["conflicts"]] or ["- none"]
    lines.append("\n## Gaps")
    lines += [f"- ❓ {g}" for g in report["gaps"]] or ["- none"]
    md.write_text("\n".join(lines), encoding="utf-8")
    print(f"\n  📄 Report : {md}")
    print(f"  📄 JSON   : {js}")
    if deep_prompt:
        prompt = research_brief.notebooklm_prompt(
            query, articles, used_year) + DEEP_PASSES
        pp = out_dir / f"{stem}-{report['created']}-deep-prompt.md"
        pp.write_text(prompt, encoding="utf-8")
        print(f"  🧠 Deep NotebookLM prompt (passes 6–8): {pp}")
    print("-" * 74)
    print("  Next: brief file save chesi `--notebooklm-brief FILE` tho re-run;")
    print("        publish flow lo deep section automatic ga add avutundi.")
    print("=" * 74)
    return 0


DEEP_PASSES = """

## Pass 6 — year-over-year comparison (deep)
Build a table: parameter (vacancies, fee, age limit, exam date, eligibility) ×
last 3 available years, one cell per year with source ID. Mark every missing
cell "not stated" — never carry a previous year's number forward.

## Pass 7 — explain like a 12th-grade student (deep)
Rewrite the three riskiest claims as a 2-sentence Telugu explanation a
confused student would understand, keeping Claim IDs. Flag any claim that
cannot be explained simply (those are usually too uncertain to publish).

## Pass 8 — gap priority + confidence (deep)
Rank the gap list by reader harm if wrong (deadline > fee > eligibility >
others). For each of the top 5, state the exact official URL or portal page
where a human should verify it before publishing. End with an overall
confidence (low/medium/high) and the single weakest claim.
"""
