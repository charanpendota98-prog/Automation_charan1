"""v17: Keyword Dominance Engine — "SSC 2026 ante mana post top lo".

3 parts:
1. KEYWORD MATRIX — 66 exams × 14 search intents = 900+ exact search
   phrases (notification, apply online, hall ticket, results, cut off...).
   Coverage systematic ga unte Google lo maname top queries ki available.
2. GOOGLE AUTOCOMPLETE HARVESTER — suggestqueries endpoint (FREE, no API
   key): students actually type chese queries harvest chesi targets ga
   māruchestam. (Google "mana post ni suggest" cheyadaniki ise real lever —
   aa queries ni mana cover chestam.)
3. GAP ANALYSIS — live WP posts vs matrix: em miss aina → topics_queue.
Roju radar run lo 1 saari (kw:last guard). CLI: run.py --keywords
"""

import logging
import re
from datetime import date
from typing import Dict, List

import requests

from . import config, state

log = logging.getLogger("autoblog.keyword")

SUGGEST_URL = "https://suggestqueries.google.com/complete/search"

# --------------------------------------------------------------- matrix data
# (exam name, category) — exam names = students type chese exact phrases
EXAMS: List[tuple] = [
    # ---- Central govt exams / banks / defence ----
    ("SSC CGL", "Central Govt Jobs"), ("SSC CHSL", "Central Govt Jobs"),
    ("SSC MTS", "Central Govt Jobs"), ("SSC GD", "Central Govt Jobs"),
    ("SSC Stenographer", "Central Govt Jobs"), ("SSC JE", "Central Govt Jobs"),
    ("SSC CPO", "Central Govt Jobs"),
    ("UPSC CSE", "Central Govt Jobs"), ("UPSC CDS", "Central Govt Jobs"),
    ("UPSC NDA", "Central Govt Jobs"), ("UPSC EPFO", "Central Govt Jobs"),
    ("RRB NTPC", "Central Govt Jobs"), ("RRB Group D", "Central Govt Jobs"),
    ("RRB ALP", "Central Govt Jobs"), ("RRB JE", "Central Govt Jobs"),
    ("IBPS PO", "Central Govt Jobs"), ("IBPS Clerk", "Central Govt Jobs"),
    ("IBPS SO", "Central Govt Jobs"), ("IBPS RRB Officer", "Central Govt Jobs"),
    ("IBPS RRB Assistant", "Central Govt Jobs"),
    ("SBI PO", "Central Govt Jobs"), ("SBI Clerk", "Central Govt Jobs"),
    ("SBI SO", "Central Govt Jobs"), ("LIC AAO", "Central Govt Jobs"),
    ("LIC Assistant", "Central Govt Jobs"), ("RBI Grade B", "Central Govt Jobs"),
    ("RBI Assistant", "Central Govt Jobs"), ("NABARD Grade A", "Central Govt Jobs"),
    ("India Post GDS", "Central Govt Jobs"),
    ("Army Agniveer", "Central Govt Jobs"), ("Navy SSR Agniveer", "Central Govt Jobs"),
    ("Air Force Agniveer", "Central Govt Jobs"), ("Coast Guard", "Central Govt Jobs"),
    # ---- Telangana ----
    ("TSPSC Group 1", "TS Govt Jobs"), ("TSPSC Group 2", "TS Govt Jobs"),
    ("TSPSC Group 3", "TS Govt Jobs"), ("TSPSC Group 4", "TS Govt Jobs"),
    ("TGPSC Gurukul", "TS Govt Jobs"), ("TG DSC SGT", "TS Govt Jobs"),
    ("TG DSC School Assistant", "TS Govt Jobs"), ("TG DSC", "TS Govt Jobs"),
    ("TSLPRB SI", "TS Govt Jobs"), ("TSLPRB Constable", "TS Govt Jobs"),
    ("TGRTC", "TS Govt Jobs"), ("Singareni", "TS Govt Jobs"),
    ("TSSPDCL", "TS Govt Jobs"), ("TS EAMCET", "Online Education"),
    ("TS Polycet", "Online Education"), ("TS ICET", "Online Education"),
    ("Osmania University", "Online Education"), ("JNTUH", "Results"),
    # ---- Andhra Pradesh ----
    ("APPSC Group 1", "AP Govt Jobs"), ("APPSC Group 2", "AP Govt Jobs"),
    ("APPSC Group 3", "AP Govt Jobs"), ("AP DSC SGT", "AP Govt Jobs"),
    ("AP DSC School Assistant", "AP Govt Jobs"), ("AP DSC", "AP Govt Jobs"),
    ("AP Police", "AP Govt Jobs"), ("APSRTC", "AP Govt Jobs"),
    ("Grama Sachivalayam", "AP Govt Jobs"), ("AP EAPCET", "Online Education"),
    ("AP Polycet", "Online Education"), ("AP ICET", "Online Education"),
    ("Jnanabhumi", "Scholarships"),
    # ---- Central education + scholarships ----
    ("NEET UG", "Online Education"), ("JEE Main", "Online Education"),
    ("CUET UG", "Online Education"), ("IGNOU", "Online Education"),
    ("NSP Scholarship", "Scholarships"), ("PM YASASVI", "Scholarships"),
]

# (intent, title template) — year-intent leni vi evergreen
INTENTS: List[tuple] = [
    ("notification", "{exam} {year} Notification – Vacancies, Dates, Apply Online Telugu lo", True),
    ("apply online", "{exam} {year} Apply Online – Eligibility, Fee & Steps Telugu lo", True),
    ("hall ticket", "{exam} {year} Hall Ticket Download – Direct Link & Steps", True),
    ("results", "{exam} {year} Results – Check Marks & Direct Link Telugu lo", True),
    ("answer key", "{exam} {year} Answer Key – Download & Objection Process", True),
    ("cut off", "{exam} {year} Cut Off – Expected & Previous Year Marks Analysis", True),
    ("syllabus", "{exam} Syllabus {year} – Complete Subject wise PDF Telugu lo", True),
    ("exam date", "{exam} {year} Exam Date – Complete Schedule Telugu lo", True),
    ("vacancies", "{exam} {year} Vacancies – Category-wise Total Posts", True),
    ("salary", "{exam} {year} Salary – Pay Scale, Allowances & Job Profile", True),
    ("selection process", "{exam} {year} Selection Process – Stages & Exam Pattern", True),
    ("previous papers", "{exam} Previous Papers – Free PDF Download & Solutions", False),
    ("best books", "{exam} {year} Best Books – Telugu Medium Strategy Complete", True),
    ("preparation tips", "{exam} {year} Preparation Tips – 90 Days Study Plan Telugu lo", True),
]

# students roju vesē hot intents (gap analysis ee variki priority)
HOT_INTENTS = {"notification", "apply online", "hall ticket", "results",
               "answer key", "cut off"}


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ",
                  re.sub(r"[^\w\d\u0c00-\u0c7f]+", " ", (text or "").lower())).strip()


def keyword_matrix() -> List[Dict]:
    """Exam × intent matrix → [{kw, title, cat, exam, intent, hot}]."""
    year = date.today().year
    out = []
    for exam, cat in EXAMS:
        for intent, tmpl, _with_year in INTENTS:
            title = tmpl.format(exam=exam, year=year)
            kw = _norm(f"{exam} {year if _with_year else ''} {intent}")
            out.append({"kw": kw, "title": title, "cat": cat,
                        "exam": exam, "intent": intent,
                        "hot": intent in HOT_INTENTS})
    return out


# ------------------------------------------------------------------ coverage

def is_covered(entry: Dict, title_norms: List[str]) -> bool:
    """Ee keyword eeka existing post title lo covered aa (word-boundary).

    Exam tokens anni + intent tokens anni okka title lo unte covered.
    """
    exam_t = _norm(entry["exam"]).split()
    intent_t = _norm(entry["intent"]).split()
    for tn in title_norms:
        padded = f" {tn} "
        if all(f" {w} " in padded for w in exam_t) \
                and all(f" {w} " in padded for w in intent_t):
            return True
    return False


def keyword_gaps(existing_titles: List[str], limit: int = 20) -> List[Dict]:
    """Matrix lo inka cover avvalsithe — hot intents (7) mundu, then rest."""
    norms = [_norm(t) for t in existing_titles if t]
    uncovered = [e for e in keyword_matrix() if not is_covered(e, norms)]
    uncovered.sort(key=lambda e: (not e["hot"], e["exam"]))
    return uncovered[:limit]


def coverage_report(existing_titles: List[str]) -> Dict:
    norms = [_norm(t) for t in existing_titles if t]
    matrix = keyword_matrix()
    covered = [e for e in matrix if is_covered(e, norms)]
    return {"total": len(matrix), "covered": len(covered),
            "pct": round(100 * len(covered) / max(1, len(matrix)), 1),
            "existing_posts": len(norms)}


# ------------------------------------------------------------------ suggest

def harvest_suggest(seed: str, lang: str = "te") -> List[str]:
    """Google Autocomplete (free) — real ga students type chese queries."""
    try:
        r = requests.get(SUGGEST_URL,
                         params={"client": "firefox", "hl": lang,
                                 "gl": "in", "q": seed},
                         timeout=10)
        data = r.json()
        return [s for s in data[1] if isinstance(s, str)][:10]
    except Exception as exc:
        log.debug("suggest harvest fail (%s): %s", seed, exc)
        return []


def suggest_seeds() -> List[str]:
    """Daily autocomplete seeds: config override leda top exams × language."""
    year = date.today().year
    extra = [s.strip() for s in
             getattr(config, "KEYWORD_SUGGEST_SEEDS", "").split(",") if s.strip()]
    if extra:
        return extra
    return [f"{name} {year}" for name, _cat in EXAMS[:40]]


# ------------------------------------------------------------------ daily run

def daily_keyword_harvest(max_queue: int = 4, force: bool = False) -> Dict:
    """Radar run lo 1 saari: autocomplete queries + gap keywords → topics.

    queue ayye topics pending_topics() dwara normal pipeline lo generate
    avtayi (trend_topic flow — aa title exact search phrase ga untundi).
    """
    today = date.today().isoformat()
    if not force and state.meta_get(config.STATE_PATH, "kw:last") == today:
        return {"queued": 0, "skipped": "already ran today"}
    queued = 0
    # 1) autocomplete harvest (real queries) — edu relevant new ki queue
    for seed in suggest_seeds()[:10]:
        for sugg in harvest_suggest(seed):
            if len(sugg) < 8:
                continue
            if _is_edu(sugg) and _queue_topic_safe(sugg):
                queued += 1
            if queued >= max_queue:
                break
        if queued >= max_queue:
            break
        # English lang kuda (English lo search chese vrulu ekkuva)
        for sugg in harvest_suggest(seed, lang="en"):
            if len(sugg) < 8 or not _is_edu(sugg) or not _queue_topic_safe(sugg):
                continue
            queued += 1
            if queued >= max_queue:
                break
        if queued >= max_queue:
            break
    # 2) gap keywords (live posts tho compare) — hot-first queue
    if queued < max_queue:
        titles: List[str] = []
        try:
            from .wordpress_client import WordPressClient

            titles = [p.get("title", "") for p in
                      WordPressClient().get_recent_published(per_page=100)]
        except Exception as exc:
            log.warning("keyword gaps: live titles ravaledu (%s) — matrix matrame", exc)
        for gap in keyword_gaps(titles, limit=max_queue * 3):
            if queued >= max_queue:
                break
            if _queue_topic_safe(gap["title"]):
                queued += 1
    state.meta_set(config.STATE_PATH, "kw:last", today)
    log.info("KEYWORDS: %d new topics queued (harvest + gap analyse)", queued)
    return {"queued": queued}


def _is_edu(text: str) -> bool:
    from .news_radar import _edu_relevant

    return _edu_relevant(text)


def _queue_topic_safe(text: str) -> bool:
    from .news_radar import _queue_topic

    try:
        return _queue_topic(text)
    except Exception:
        return False
