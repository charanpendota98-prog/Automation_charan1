# -*- coding: utf-8 -*-
"""v97 — REAL-TIME KEYWORD VERIFICATION (dummy keyword list kaadu).

PROBLEM (mee brief: "real time lo keyword verify cheyali, dummy vaddu"):
  Ippati varaku `focus_keyword` ni **LLM invent** chestundi, leda title nunchi
  derive avutundi (`pipeline._hygiene`). Adi nijamga **evaru search chese
  phrase aa** ani verify chese code **ekkada ledu**. Result: "TSPSC Group 2
  Notification Complete Details Telugu" lanti keyword — chudadaniki bagunna,
  daaniki **search demand ZERO**. Aa post ki Rank Math 100 vachina Google lo
  traffic raadu, endukante aa phrase ni evaru type cheyyaru.

SOLUTION — Google Autocomplete = LIVE demand proof:
  Google Suggest lo oka phrase kanipinchindi ante, aa phrase ni **nijamaina
  users type chestunnaru** (Google aa data ni real queries nunchi build
  chestundi). Kabatti:

    1) VERIFY  — focus keyword prefix ni Suggest ki pampi, aa keyword (leda
                 daani close variant) return avutunda ani chustam.
    2) RANK    — Suggest lo position = demand proxy (1st = highest).
    3) REPLACE — verify fail ayithe, ade topic ki **Suggest lo nijamga unna**
                 best phrase ni pick chesi focus keyword ni replace chestam.

  Idi **real-time** (prathi post ki live call, cache TTL tho), **free** (API
  key avasaram ledu) mariyu **deterministic ga testable** (fetcher inject).

HONEST LIMITS (ivi chadavandi):
  · Suggest **exact monthly search volume** ivvadu. Volume kavali ante paid
    API (DataForSEO / Keywords Everywhere / Ahrefs) kavali. Idi *demand
    exists / doesn't exist* ane **binary + ordinal** signal mattrame — aina
    invented keyword kanna infinitely better.
  · Network lekapote **verdict "unknown"** — post block avvadu (fail-open).
    Fake "verified" stamp eppudu veyyamu.
  · Suggest lo undadam ante "rank avutam" ani kaadu. Demand undi ani mattrame.

CLI:
  python run.py --verify-keyword "tspsc group 2 notification"
  python run.py --keyword-audit          # live WP posts focus kws audit
"""
from __future__ import annotations

import json
import logging
import re
import time
from typing import Callable, Dict, List, Optional, Tuple

from . import config

log = logging.getLogger("autoblog.kwverify")

#: Suggest endpoints (client=firefox → clean JSON array, no API key).
#: Modatidi fail ayithe (DNS/SSL/region block) rendodi try chestam — okate
#: data, rendu Google endpoints. Rendu fail ⇒ verdict "unknown" (fail-open).
SUGGEST_URLS = (
    "https://suggestqueries.google.com/complete/search"
    "?client=firefox&hl={hl}&gl={gl}&q={q}",
    "https://www.google.com/complete/search"
    "?client=firefox&hl={hl}&gl={gl}&q={q}",
)
#: Back-compat (v97 modati draft) — modati endpoint.
SUGGEST_URL = SUGGEST_URLS[0]

#: In-process cache: {(prefix, hl): (epoch, [phrases])}. Prathi post ki
#: same prefix malli malli fetch avvakunda (Google ni hammer cheyyakudadu).
_CACHE: Dict[Tuple[str, str], Tuple[float, List[str]]] = {}

#: Verdicts.
VERIFIED = "verified"      # Suggest lo exact/near-exact ga undi
WEAK = "weak"              # topic related suggestions unnayi, exact ledu
DEAD = "dead"              # aa prefix ki suggestions ye levu → demand ledu
UNKNOWN = "unknown"        # network/offline → judge cheyyalemu (fail-open)

#: Keyword lo undakudani fluff — ivi unte adi "invented" keyword ani artham.
#: (Nijamaina search queries lo evaru ivi type cheyyaru.)
FLUFF = (
    "complete details", "full details", "complete information", "all details",
    "everything you need", "step by step guide", "a to z", "detailed guide",
    "complete guide", "full guide", "sampurna", "samagra vivaralu",
    "here is", "know about", "all you need",
)


# --------------------------------------------------------------- normalise

def normalise(kw: str) -> str:
    """Compare cheyyadaniki: lower · punctuation teesi · single spaces."""
    kw = re.sub(r"[^\w\u0c00-\u0c7f]+", " ", (kw or "").lower())
    return re.sub(r"\s+", " ", kw).strip()


def _tokens(kw: str) -> List[str]:
    return [t for t in normalise(kw).split() if t]


def has_fluff(kw: str) -> bool:
    """Keyword lo human evaru type cheyani filler undaa?"""
    low = normalise(kw)
    return any(f in low for f in FLUFF)


def _prefix(kw: str, words: int = 3) -> str:
    """Suggest ki pampe prefix — modati konni words (Google mothham complete
    chestundi). Full keyword pampithe adi already "typed" ani Google
    echo chesthundi, so verification meaning poతుంది."""
    toks = _tokens(kw)
    if len(toks) <= words:
        return " ".join(toks)
    return " ".join(toks[:words])


# ------------------------------------------------------------------ fetch

def _http_get(url: str, timeout: int = 8) -> str:
    try:
        import requests

        r = requests.get(url, timeout=timeout,
                         headers={"User-Agent": "studentup-bot/1.0"})
        if r.status_code == 200:
            return r.text
        log.info("suggest HTTP %s", r.status_code)
    except Exception as exc:  # noqa: BLE001 — offline lo silent
        log.info("suggest skip (%s)", type(exc).__name__)
    return ""


def parse_suggest(text: str) -> List[str]:
    """client=firefox JSON → phrases. Junk vaste []."""
    if not text:
        return []
    try:
        data = json.loads(text)
    except Exception:  # noqa: BLE001
        return []
    if isinstance(data, list) and len(data) > 1 and isinstance(data[1], list):
        return [str(x).strip() for x in data[1] if str(x).strip()]
    return []


def suggestions(prefix: str, hl: str = "en",
                fetcher: Optional[Callable[[str], str]] = None,
                ttl: Optional[int] = None) -> List[str]:
    """Live autocomplete phrases for `prefix` (cached).

    `fetcher` inject cheste network ki velladu → tests deterministic.
    """
    prefix = normalise(prefix)
    if not prefix:
        return []
    ttl = int(getattr(config, "KW_VERIFY_TTL", 3600) if ttl is None else ttl)
    key = (prefix, hl)
    now = time.time()
    if fetcher is None and key in _CACHE:
        stamp, cached = _CACHE[key]
        if now - stamp < ttl:
            return list(cached)
    gl = (getattr(config, "TRENDS_GEO", "IN") or "IN").lower()
    q = re.sub(r"\s+", "+", prefix)
    get = fetcher or _http_get
    out: List[str] = []
    for tmpl in SUGGEST_URLS:
        out = parse_suggest(get(tmpl.format(hl=hl, gl=gl, q=q)))
        if out:
            break
        if fetcher is not None:
            break          # tests: okka call matrame (deterministic)
    if fetcher is None:
        _CACHE[key] = (now, list(out))
    return out


# ----------------------------------------------------------------- verify

def _match_rank(kw: str, phrases: List[str]) -> Tuple[int, str]:
    """Keyword ee suggestion tho match avutundo (0-based rank, phrase).

    Exact normalised match mundu; ade leకpothe "anni keyword tokens aa
    suggestion lo unnayi" ane subset match (word-boundary safe).
    Match ledu → (-1, "").
    """
    target = normalise(kw)
    norms = [normalise(p) for p in phrases]
    for i, n in enumerate(norms):
        if n == target:
            return i, phrases[i]
    toks = _tokens(kw)
    if toks:
        for i, n in enumerate(norms):
            padded = f" {n} "
            if all(f" {t} " in padded for t in toks):
                return i, phrases[i]
    return -1, ""


def verify(keyword: str, hl: str = "en",
           fetcher: Optional[Callable[[str], str]] = None) -> Dict:
    """Oka focus keyword ki LIVE demand verdict.

    Returns: {keyword, verdict, rank, matched, suggestions, fluff, reason}
      verdict = verified | weak | dead | unknown
      rank    = Suggest lo position (0 = top, -1 = match ledu)
    """
    kw = (keyword or "").strip()
    base = {"keyword": kw, "verdict": UNKNOWN, "rank": -1, "matched": "",
            "suggestions": [], "fluff": has_fluff(kw), "reason": ""}
    if not kw:
        base["reason"] = "khali keyword"
        return base
    phrases = suggestions(_prefix(kw), hl=hl, fetcher=fetcher)
    base["suggestions"] = phrases
    if not phrases:
        # Rendu artham: (a) network ledu, (b) aa prefix ki demand ledu.
        # Confuse cheyyakudadu — control seed tho tests chestam.
        base["verdict"] = UNKNOWN
        base["reason"] = ("suggestions raledu — offline kavachu leda "
                          "aa prefix ki demand ledu")
        return base
    rank, matched = _match_rank(kw, phrases)
    base["rank"], base["matched"] = rank, matched
    if rank >= 0:
        base["verdict"] = VERIFIED
        base["reason"] = f"Google Suggest lo #{rank + 1} ga undi"
    else:
        base["verdict"] = WEAK
        base["reason"] = ("prefix ki demand undi kaani ee exact phrase "
                          "Suggest lo ledu")
    return base


def best_alternative(keyword: str, hl: str = "en",
                     fetcher: Optional[Callable[[str], str]] = None,
                     must_include: str = "") -> str:
    """Verify fail ayithe — Suggest lo NIJAMGA unna best phrase.

    Rules: (1) fluff undakudadu, (2) `must_include` tokens undali (topic
    drift avvakudadu — "ts police" post ki "ap police" keyword raakudadu),
    (3) chala pొడugu vaddu (Rank Math focus kw ≤ 8 words).
    Edi దొరakapothe "" (caller original ne unchukovali).
    """
    phrases = suggestions(_prefix(keyword), hl=hl, fetcher=fetcher)
    need = _tokens(must_include) if must_include else _tokens(_prefix(keyword, 2))
    for p in phrases:
        n = normalise(p)
        if has_fluff(p) or len(n.split()) > 8 or len(n) < 8:
            continue
        padded = f" {n} "
        if need and not all(f" {t} " in padded for t in need):
            continue
        return p
    return ""


def verify_and_fix(article: Dict,
                   fetcher: Optional[Callable[[str], str]] = None) -> Dict:
    """Pipeline hook — article focus_keyword ni live verify + (needed ayithe) fix.

    Article ni **in place** update chestundi:
      article["focus_keyword"]      — verified/replaced phrase
      article["_kw_verify"]         — full report (meta.json + certificate lo)
    Post ni **eppudu block cheyyadu** (fail-open): keyword ki demand lekapothe
    kuda content value undochu; kaani report lo nijam raastundi.
    """
    kw = (article.get("focus_keyword") or "").strip()
    report = verify(kw, fetcher=fetcher)
    report["replaced"] = False
    report["original"] = kw
    if report["verdict"] in (WEAK, DEAD) or report["fluff"]:
        alt = best_alternative(kw, fetcher=fetcher)
        if alt and normalise(alt) != normalise(kw):
            article["focus_keyword"] = alt
            report["replaced"] = True
            report["keyword"] = alt
            report["reason"] += f" → live phrase tho replace: {alt!r}"
            log.info("KW VERIFY: %r → %r (live demand)", kw, alt)
    article["_kw_verify"] = report
    return report


# ------------------------------------------------------------------ audit

def audit(keywords: List[str],
          fetcher: Optional[Callable[[str], str]] = None) -> Dict:
    """Chala keywords ni okesari verify → summary (CLI --keyword-audit)."""
    rows = [verify(k, fetcher=fetcher) for k in keywords if (k or "").strip()]
    counts = {VERIFIED: 0, WEAK: 0, DEAD: 0, UNKNOWN: 0}
    for r in rows:
        counts[r["verdict"]] = counts.get(r["verdict"], 0) + 1
    judged = counts[VERIFIED] + counts[WEAK] + counts[DEAD]
    return {
        "rows": rows,
        "counts": counts,
        "total": len(rows),
        "judged": judged,
        "verified_pct": round(100 * counts[VERIFIED] / judged, 1) if judged else 0.0,
        "fluff": sum(1 for r in rows if r["fluff"]),
    }


def run_cli(keyword: str = "", audit_live: bool = False, limit: int = 30) -> int:
    """CLI: single keyword verify leda live WP posts audit."""
    line = "=" * 70
    print(line)
    print("  🔎 REAL-TIME KEYWORD VERIFICATION (Google Autocomplete = live demand)")
    print(line)
    if keyword and not audit_live:
        r = verify(keyword)
        icon = {VERIFIED: "✅", WEAK: "⚠️ ", DEAD: "❌", UNKNOWN: "❔"}[r["verdict"]]
        print(f"  keyword : {r['keyword']}")
        print(f"  verdict : {icon} {r['verdict'].upper()} — {r['reason']}")
        if r["fluff"]:
            print("  fluff   : ⚠️  'complete details' lanti filler undi "
                  "(humans ila search cheyyaru)")
        if r["matched"]:
            print(f"  matched : {r['matched']}  (rank #{r['rank'] + 1})")
        if r["suggestions"]:
            print("  live suggestions (Google ippudu chupistunnavi):")
            for i, s in enumerate(r["suggestions"][:10], 1):
                print(f"     {i:2d}. {s}")
        else:
            print("  live suggestions: (raledu — offline kavachu)")
        if r["verdict"] != VERIFIED:
            alt = best_alternative(keyword)
            print(f"  better  : {alt or '(dorakaledu — original ne unchandi)'}")
        print(line)
        return 0

    kws: List[str] = []
    try:
        from .wordpress_client import WordPressClient

        wp = WordPressClient()
        for p in wp.get_recent_published(per_page=limit):
            k = (p.get("focus_keyword") or p.get("title") or "").strip()
            if k:
                kws.append(k)
    except Exception as exc:  # noqa: BLE001
        print(f"  ⚠️  live posts raledu ({type(exc).__name__}) — "
              "keyword matrix tho audit chestunnam")
    if not kws:
        from .keyword_engine import keyword_matrix

        kws = [e["kw"] for e in keyword_matrix()[:limit]]
    rep = audit(kws)
    for r in rep["rows"][:limit]:
        icon = {VERIFIED: "✅", WEAK: "⚠️ ", DEAD: "❌", UNKNOWN: "❔"}[r["verdict"]]
        extra = f" → {r['matched']}" if r["matched"] else ""
        print(f"  {icon} {r['keyword'][:52]:<52}{extra}")
    print("-" * 70)
    c = rep["counts"]
    print(f"  total {rep['total']} · verified {c[VERIFIED]} · weak {c[WEAK]} · "
          f"dead {c[DEAD]} · unknown {c[UNKNOWN]} · fluff {rep['fluff']}")
    if rep["judged"]:
        print(f"  live-demand coverage: {rep['verified_pct']}% "
              "(judge chesina vaatilo)")
    else:
        print("  ❔ network ledu — verdict ivvalemu (fake stamp veyyamu)")
    print(line)
    return 0
