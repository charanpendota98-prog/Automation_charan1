"""Shared publish pipeline — run.py & Telegram approval bot okari okaru vadatam.

publish_article(): SEO enhance + internal links + featured image +
Rank Math meta + WP create + state + notification.
create_from_source(url): fetch source -> Gemini 100% original rewrite -> publish.
"""

import hashlib
import json
import logging
import re
from datetime import date
from pathlib import Path
from typing import Dict, Optional
from urllib.parse import urlparse

from . import (config, content_quality, gemini_client, google_quality, image_gen,
               notifier, post_gate, qual, research, rm100, seo, sources, state,
               validator)
from .notifier import esc, send_telegram
from .wordpress_client import WordPressClient

log = logging.getLogger("autoblog.pipeline")


def _save_provenance(article: Dict) -> None:
    """Store source URLs and hashes, never raw/private source text."""
    urls = list(article.get("_source_urls") or [])
    texts = list(article.get("_source_texts") or [])
    if not urls:
        return
    records = []
    for index, url in enumerate(urls):
        text = texts[index] if index < len(texts) else ""
        records.append({
            "id": f"S{index + 1}",
            "url": url,
            "sha256": hashlib.sha256(text.encode("utf-8", "ignore")).hexdigest(),
            "characters": len(text),
        })
    path = config.OUTPUT_DIR / "provenance"
    path.mkdir(parents=True, exist_ok=True)
    (path / f"{article.get('slug', 'post')}.json").write_text(
        json.dumps({
            "title": article.get("title", ""),
            "created": date.today().isoformat(),
            "notebooklm_claims": article.get("_notebooklm_claims", 0),
            "sources": records,
        }, ensure_ascii=False, indent=2), encoding="utf-8")


# ---------------------------------------------------------------- auto category

CATEGORY_RULES = [
    # live-site categories (v14) — specific rules first (tie-break priority)
    # v58: విదేశీ ఉద్యోగాలు — Gulf/abroad jobs, visa, IELTS/PTE, NRI.
    # List MODATI rule (telugu "ఉద్యోగాలు" generic word Central ki vellakudadu;
    # "గల్ఫ్ ఉద్యోగాలు" → Abroad Jobs). Phrases ki 2x weight, Telugu ki 2x.
    ("Abroad Jobs", ["gulf job", "gulf jobs", "abroad job", "abroad jobs",
                     "overseas job", "overseas jobs", "work visa", "visa slot",
                     "visa appointment", "study abroad", "ielts exam", "ielts test",
                     "pte exam", "toefl", "green card", "h1b", "h-1b", "e-migrate",
                     "గల్ఫ్ ఉద్యోగాలు", "విదేశీ ఉద్యోగాలు", "విదేశీ ఉద్యోగ",
                     "దుబాయ్", "సౌదీ", "కువైట్", "ఖతార్", "ఒమన్", "బహ్రెయిన్",
                     "abroad", "overseas", "gulf", "dubai", "abu dhabi", "saudi",
                     "qatar", "kuwait", "oman", "bahrain", "uae", "sharjah",
                     "singapore", "malaysia", "japan", "south korea", "germany",
                     "canada", "australia", "uk ", "usa ", "ielts", "pte",
                     "emigrate", "nri", "passport", "oci", "visa",
                     "విదేశీ", "గల్ఫ్", "వీసా", "ఐఎల్‌టీఎస్", "ప్రవాస"]),
    ("TS Govt Jobs", ["tspsc", "telangana", "ts police", "ts genco", "transco",
                      "తెలంగాణ", "gurukul", "tgpsc"]),
    ("AP Govt Jobs", ["appsc", "andhra", "ap police", "apsrtc", "ap genco",
                      "ఆంధ్రప్రదేశ్", "ap dsc", "grama sachivalayam"]),
    ("Central Govt Jobs", ["ssc", "upsc", "rrb", "ibps", "sbi po", "sbi clerk",
                           "india post", "agniveer", "job", "vacancy",
                           "recruitment", "bharti", "notification", "posts",
                           "ఉద్యోగ", "నియామక", "ఖాళీల", "si ", "constable"]),
    ("Software Jobs", ["software", "developer", "engineer", "it jobs",
                       "coding", "full stack", "data analyst", "devops",
                       "testing"]),
    ("Private Jobs", ["tcs", "infosys", "wipro", "hcl", "cognizant",
                      "accenture", "fresher", "off campus", "private", "mnc"]),
    ("Part Time Jobs", ["part time", "part-time", "work from home",
                        "freelance", "data entry", "tutor"]),
    ("Walkin Jobs", ["walkin", "walk-in", "walk in", "direct interview"]),
    ("Outsourcing Jobs", ["outsourcing", "contract basis", "contractual",
                          "కాంట్రాక్ట్", "అవుట్‌సోర్సింగ్", "crc", "outsourced",
                          "guest faculty", "honorarium"]),
    ("Success Stories", ["success story", "success stories", "achiever", "topper",
                         "ranker", "selected candidate", "selected students",
                         "విజయగాథ", "సాధించిన", "టాపర్"]),
    ("Current Affairs", ["current affairs", "జాతీయ", "ప్రస్తుతాంశాలు",
                         "pib", "press release", "news today", "daily news",
                         "government order", "government notification", "scheme",
                         "welfare", "budget", "pm kisan", "kisan", "farmer",
                         "agriculture", "rythu", "women welfare", "mahila",
                         "self help", "pension", "subsidy", "job fair",
                         "కరెంట్ అఫైర్స్", "studytoday news", "పథకం", "రైతు",
                         "మహిళ", "వ్యవసాయం"]),
    ("Upcoming Exams", ["upcoming exam", "exam calendar", "notification coming",
                        "రానున్న పరీక్షలు", "exam schedule", "tentative schedule",
                        "recruitment calendar", "పరీక్షల క్యాలెండర్"]),
    ("Exam Tips", ["exam tips", "preparation strategy", "study plan", "revision",
                   "పరీక్షా చిట్కాలు", "సన్నద్ధత", "how to prepare", "time table",
                   "model paper", "previous papers", "mock test"]),
    ("Hall Tickets", ["admit card", "hall ticket", "హాల్ టికెట్", "call letter"]),
    ("Scholarships", ["scholarship", "fellowship", "nsp", "fee reimbursement",
                      "స్కాలర్", "రుసుము", "pragati", "saksham", "yasasvi"]),
    ("Results", ["result", "ఫలిత", "marks list", "manabadi", "grade",
                 "cutoff", "cut-off", "answer key"]),
    ("Internships", ["internship", "ఇంటర్న్"]),
    ("Online Education", ["admission", "counselling", "counseling", "web options",
                          "dost", "eamcet", "eapcet", "icet", "pgecet", "ప్రవేశ",
                          "online mba", "online degree", "course", "syllabus",
                          "preparation", "study plan", "exam date", "పరీక్ష"]),
]


# Generic job words are deliberately *not* enough to decide a taxonomy. A
# headline containing only "job", "vacancy" or "notification" must never
# become Central Govt Jobs. That was the source of the Software → Central bug.
_RULE_GENERIC = {"job", "jobs", "vacancy", "vacancies", "posts", "notification",
                 "recruitment", "bharti", "hiring", "apply", "apply online"}

# These are organisation/exam signals, not generic words. Keep this list
# conservative: a false Central/State label is worse than a manual review.
_CENTRAL_SIGNALS = (
    "ssc", "upsc", "rrb", "railway", "ibps", "sbi po", "sbi clerk",
    "india post", "agniveer", "drdo", "isro", "esic", "epfo", "lic",
    "air force", "airforce", "army", "navy", "coast guard", "defence",
    "central government", "central govt", "కేంద్ర ప్రభుత్వం", "కేంద్ర ఉద్యోగ",
)
_TS_SIGNALS = (
    "tspsc", "telangana", "ts police", "tg police", "ts genco", "tstransco",
    "transco", "gurukul", "tgpsc", "telangana government", "ts govt",
    "తెలంగాణ", "టీఎస్పీఎస్సీ", "తెలంగాణ ప్రభుత్వం",
)
_AP_SIGNALS = (
    "appsc", "andhra pradesh", "andhra", "ap police", "apsrtc", "ap genco",
    "aptransco", "ap dsc", "grama sachivalayam", "ap govt", "ఆంధ్రప్రదేశ్",
    "ఏపీపీఎస్సీ", "ఆంధ్రప్రదేశ్ ప్రభుత్వం",
)
_SOFTWARE_SIGNALS = (
    "software developer", "software engineer", "frontend", "front-end",
    "backend", "back-end", "full stack", "full-stack", "web developer",
    "data analyst", "data scientist", "machine learning", "devops", "qa tester",
    "software testing", "automation tester", "programmer", "coding job",
    "it job", "it jobs", "python developer", "java developer", "android developer",
    "ఫుల్ స్టాక్", "డెవలపర్", "సాఫ్ట్‌వేర్ ఉద్యోగ",
)
_PRIVATE_SIGNALS = (
    "tcs", "infosys", "wipro", "hcl", "cognizant", "accenture", "amazon",
    "deloitte", "microsoft", "google careers", "private company", "private job",
    "mnc", "off campus", "campus hiring", "fresher hiring",
)
_JOB_CONTEXT = (
    "job", "jobs", "vacancy", "vacancies", "recruitment", "notification",
    "hiring", "career", "careers", "opening", "role", "roles", "apply",
    "salary", "walk-in", "walkin", "భర్తీ", "ఉద్యోగ", "నియామక", "ఖాళీ",
)


def _has_any(blob: str, signals: tuple[str, ...]) -> bool:
    return any(signal.lower() in blob for signal in signals)


def _rule_weight(word: str) -> float:
    """Keyword specificity for the conservative fallback scorer."""
    w = word.strip().lower()
    if w in _RULE_GENERIC:
        return 0.25
    if " " in w or "-" in w:
        return 2.0
    if not w.isascii():
        return 2.0
    return 1.0


def classify_category(title: str, text: str = "") -> str:
    """Return one canonical live-site category for a title/source.

    Classification is intent-first, not keyword-count-first:
    - software roles stay in Software Jobs unless an explicit government
      organisation/exam proves that the post belongs in TS/AP/Central;
    - Central Govt Jobs requires an actual central exam/organisation signal;
    - generic words such as *notification* and *vacancy* never create a
      government category by themselves;
    - exam status (calendar, result, hall ticket) and scholarships outrank a
      broad jobs label where that is the reader's real task.
    """
    blob = re.sub(r"\\s+", " ", f"{title} {title} {text[:900]}".lower()).strip()
    has_job = _has_any(blob, _JOB_CONTEXT)
    has_software = _has_any(blob, _SOFTWARE_SIGNALS)
    has_central = _has_any(blob, _CENTRAL_SIGNALS)
    has_ts = _has_any(blob, _TS_SIGNALS)
    has_ap = _has_any(blob, _AP_SIGNALS)

    # High-precision non-job intents first. This avoids an "SSC calendar"
    # becoming Central Govt Jobs and an "NSP last date" becoming a job post.
    if _has_any(blob, ("gulf", "abroad", "overseas", "work visa", "visa appointment",
                       "ielts", "pte", "toefl", "emigrate", "nri", "passport",
                       "saudi", "uae", "dubai", "qatar", "kuwait", "oman",
                       "bahrain", "విదేశీ", "గల్ఫ్", "వీసా")):
        return "Abroad Jobs"
    # A press release/current-affairs story about a scholarship is not a
    # scholarship application guide. Keep the six daily-current streams in
    # Current Affairs; actual eligibility/apply/last-date pieces go below.
    if _has_any(blob, ("current affairs", "daily news", "press release", "pib",
                       "government order", "budget", "ప్రస్తుతాంశాలు", "కరెంట్ అఫైర్స్")) and not has_job:
        return "Current Affairs"
    if _has_any(blob, ("scholarship", "fellowship", "nsp", "pragati", "saksham",
                       "yasasvi", "fee reimbursement", "epass", "e-pass", "స్కాలర్")):
        return "Scholarships"
    if _has_any(blob, ("success story", "success stories", "achiever", "topper",
                       "ranker", "selected candidate", "విజయగాథ", "టాపర్")):
        return "Success Stories"
    if _has_any(blob, ("outsourcing", "contract basis", "contractual", "outsourced",
                       "guest faculty", "honorarium", "అవుట్‌సోర్సింగ్", "కాంట్రాక్ట్")):
        return "Outsourcing Jobs"
    if _has_any(blob, ("walk-in", "walk in", "walkin", "direct interview", "వాక్-ఇన్")):
        return "Walkin Jobs"
    if _has_any(blob, ("part time", "part-time", "work from home", "freelance",
                       "data entry", "online tutor")):
        return "Part Time Jobs"
    if _has_any(blob, ("upcoming exam", "upcoming exams", "exam calendar",
                       "exam schedule", "recruitment calendar", "tentative schedule",
                       "రానున్న పరీక్షలు", "పరీక్షల క్యాలెండర్")):
        return "Upcoming Exams"
    if _has_any(blob, ("exam tips", "preparation strategy", "study plan", "revision",
                       "previous papers", "mock test", "how to prepare", "time table",
                       "పరీక్షా చిట్కాలు", "సన్నద్ధత")) and not has_software:
        return "Exam Tips"
    if _has_any(blob, ("hall ticket", "hall tickets", "admit card", "call letter",
                       "హాల్ టికెట్", "అడ్మిట్ కార్డ్")):
        # Recruitment-board admit cards can stay with the state/central jobs
        # archive (the existing site contract); generic exam/university cards
        # use the dedicated Hall Tickets archive.
        if has_ts and _has_any(blob, ("tspsc", "tgpsc", "ts police", "gurukul")):
            return "TS Govt Jobs"
        if has_ap and _has_any(blob, ("appsc", "ap police", "ap dsc", "apsrtc")):
            return "AP Govt Jobs"
        if has_central and _has_any(blob, ("ssc", "upsc", "rrb", "ibps", "sbi", "railway")):
            return "Central Govt Jobs"
        return "Hall Tickets"
    if _has_any(blob, ("result", "results", "scorecard", "merit list", "answer key",
                       "cut-off", "cutoff", "ఫలిత")):
        return "Results"
    if _has_any(blob, ("internship", "internships", "apprenticeship", "ఇంటర్న్")):
        return "Internships"

    # A software role is its own job intent. Government signals are allowed to
    # override it only when the organisation/exam is explicit (e.g. DRDO
    # Software Engineer), never because the text says "notification".
    if has_software and (has_central or has_ts or has_ap) and has_job:
        if has_ts and not has_ap and not has_central:
            return "TS Govt Jobs"
        if has_ap and not has_ts and not has_central:
            return "AP Govt Jobs"
        if has_central and not has_ts and not has_ap:
            return "Central Govt Jobs"
    if has_software and has_job:
        return "Software Jobs"

    # Generic government employment is classified only by a verifiable
    # organisation/exam or an explicit state/central label.
    if has_ts and has_job and not has_ap:
        return "TS Govt Jobs"
    if has_ap and has_job and not has_ts:
        return "AP Govt Jobs"
    if has_central and has_job:
        return "Central Govt Jobs"
    if _has_any(blob, ("current affairs", "daily news", "press release", "pib",
                       "government order", "scheme", "welfare", "budget", "farmer",
                       "agriculture", "women welfare", "ప్రస్తుతాంశాలు", "కరెంట్ అఫైర్స్",
                       "పథకం", "రైతు", "మహిళ")) and not has_job:
        return "Current Affairs"
    if has_job and _has_any(blob, _PRIVATE_SIGNALS):
        return "Private Jobs"

    # Conservative compatibility fallback for older sources. It cannot select
    # Central Govt Jobs from generic words because those were removed from the
    # central rule above.
    best, best_score = "Online Education", 0.0
    for cat, words in CATEGORY_RULES:
        if cat == "Central Govt Jobs":
            words = [w for w in words if w not in _RULE_GENERIC and w not in
                     {"si ", "constable"}]
        score = sum(_rule_weight(w) for w in words if w in blob)
        if score > best_score:
            best, best_score = cat, score
    return best


def reconcile_category(article: Dict) -> Dict:
    """Repair a model/category mismatch before taxonomy terms are created.

    A requested source-grid category is authoritative and is handled by the
    caller. For model-generated articles we use the title/focus/source title as
    the classification evidence. In particular, a software role must not be
    silently filed under Central Govt Jobs merely because its title contains
    "notification" or "vacancy".
    """
    proposed = str(article.get("category") or "").strip()
    probe = " ".join(str(article.get(k) or "") for k in
                     ("title", "focus_keyword", "source_title"))
    inferred = classify_category(probe)
    if not proposed:
        article["category"] = inferred
        return article
    if inferred not in config.CATEGORIES:
        article["category"] = proposed
        return article
    if proposed not in config.CATEGORIES:
        # Migrate only known legacy labels; preserve a deliberate custom term
        # instead of inventing a new WordPress archive.
        legacy = {
            "govt jobs": "Central Govt Jobs",
            "education news": "Current Affairs",
            "exam updates": "Upcoming Exams",
            "admissions": "Online Education",
            "study tips": "Exam Tips",
        }
        alias = legacy.get(proposed.lower())
        if alias:
            article["category"] = inferred if inferred != "Online Education" else alias
        return article
    employment_categories = {
        "Central Govt Jobs", "TS Govt Jobs", "AP Govt Jobs",
        "Software Jobs", "Private Jobs",
    }
    if proposed in employment_categories and inferred in employment_categories:
        # Strong organisation/role evidence wins in either direction. This is
        # what prevents a Software article from carrying a Central category,
        # and also prevents SSC/UPSC articles from carrying Software tags.
        article["category"] = inferred
    return article


# v15 tag hygiene: brand/junk tags create cheyakudadu (SEO value undadu)
JUNK_TAGS = {"studentup", "studentup.in", "studentupin", "news", "latest",
             "update", "updates", "breaking", "breaking news", "viral",
             "trending", "2026", "2025", "students", "telugu news"}


def suggest_tags(article: Dict) -> list:
    """v78: keyword-derived auto-tags (5-8 guarantee ki base).

    LLM tags marchipoina/2-3 iste: focus_keyword + secondary + category +
    title acronyms (TSPSC/APPSC/SI...) nunchi build. Junk/dedupe/cap =
    _hygiene tarvata handle (existing rules — no junk tags).
    """
    tags = [str(t).strip() for t in (article.get("tags") or []) if str(t).strip()]
    cands = []
    if article.get("focus_keyword"):
        cands.append(str(article["focus_keyword"]).strip())
    cands += [str(k).strip() for k in (article.get("secondary_keywords") or [])[:4]]
    if article.get("category"):
        cands.append(str(article["category"]).strip())
    title = str(article.get("title") or "")
    cands += re.findall(r"\b[A-Z]{2,}(?:\s*\d+)?\b", title)
    cands += re.findall(r"\b(?:Group|Grade|Level)\s+\d+\b", title, flags=re.I)
    for c in cands:
        if c and c not in tags:
            tags.append(c)
    return tags


def _hygiene(article: Dict) -> Dict:
    """Chinna chinna quality fixes publish mundhe."""
    reconcile_category(article)
    article["tags"] = suggest_tags(article)  # v78 auto-tags (hygiene dedupes)
    # title too long -> seo_title use cheyi (Rank Math 60-75 chars ideal)
    title = article.get("title", "")
    seo_title = article.get("seo_title", "")
    if len(title) > 85 and seo_title and 20 <= len(seo_title) <= 85:
        article["title"] = seo_title
    # tags: remove a different canonical category tag (e.g. Central Govt Jobs
    # accidentally returned for a Software Jobs article), then dedupe/cap.
    # Category and tags serve different jobs: keep the selected category tag,
    # but never create a second contradictory archive signal.
    category = str(article.get("category") or "").strip().lower()
    canonical_categories = {str(c).strip().lower() for c in config.CATEGORIES}
    conflicting_categories = canonical_categories - ({category} if category else set())
    seen, tags = set(), []
    for t in article.get("tags", []):
        t = str(t).strip()[:32]
        low = t.lower()
        if (not t or low in JUNK_TAGS or low in seen or
                (low in conflicting_categories and category in canonical_categories)):
            continue
        seen.add(low)
        tags.append(t)
    if not tags:
        tags = [article.get("category", "Students"), str(date.today().year)]
    article["tags"] = tags[:8]
    # v87: focus_keyword empty (LLM omit) → title nunchi derive
    # (lekapothe 41-score draft + rm100 kw-fixers anni skip!)
    if not (article.get("focus_keyword") or "").strip():
        toks = [t for t in re.sub(r"[^a-zA-Z0-9 ]", " ", title).split()
                if len(t) > 2][:4]
        article["focus_keyword"] = " ".join(toks) or title[:60]
    # v97: REAL-TIME keyword verification. LLM invent chesina keyword ki
    # (e.g. "... complete details telugu") search demand undakapovachu —
    # Google Autocomplete tho live verify chesi, demand unna phrase tho
    # replace chestam. Network ledu ⇒ verdict "unknown", post block avvadu.
    if getattr(config, "KW_VERIFY", False):
        try:
            from . import keyword_verify

            keyword_verify.verify_and_fix(article)
        except Exception as exc:  # noqa: BLE001 — advisory, never blocks
            log.debug("kw verify skip: %s", exc)
    # Senior-editor SEO hygiene: keep a useful 5–8 phrase keyword family even
    # when Gemini returns too few phrases. These are query intents, not claims,
    # and are never inserted into the article as repetitive filler.
    focus = (article.get("focus_keyword") or "").strip()
    secondary = []
    seen_secondary = set()
    for value in article.get("secondary_keywords") or []:
        phrase = " ".join(str(value).split()).strip()
        key = phrase.casefold()
        if phrase and key != focus.casefold() and key not in seen_secondary:
            seen_secondary.add(key)
            secondary.append(phrase[:90])
    if focus:
        for suffix in ("eligibility", "apply online", "official notification",
                       "documents", "selection process"):
            phrase = f"{focus} {suffix}".strip()
            key = phrase.casefold()
            if len(secondary) >= 8:
                break
            if key not in seen_secondary:
                seen_secondary.add(key)
                secondary.append(phrase[:90])
    article["secondary_keywords"] = secondary[:8]
    # meta description fallback: quick_answer or first para nunchi
    md = (article.get("meta_description") or "").strip()
    if len(md) < 120:
        base = article.get("quick_answer") or validator.strip_tags(
            article.get("content_html", ""))
        base = " ".join(base.split())
        article["meta_description"] = (base[:155].rsplit(" ", 1)[0]) if base else md
    return article


_PG_PUBLISH_TIME_CHECKS = {
    "media", "media_size", "media_alt", "content_image", "img_host",
    "ad_present", "house_ratio",
    "ad_after_para", "ads_txt", "internal_links", "external_auth", "sponsored_label",
    "schema_article", "schema_breadcrumb", "schema_job", "schema_org_link",
    "no_duplicate", "indexnow", "deadline_valid",
}


def _rankmath_gate(article: dict, category: str) -> dict:
    """v64: Rank Math 100 gate — DETERMINISTIC rm100 fixes + LLM refine rounds.

    Flow: rm100.apply (title/meta/slug/TOC/table/FAQ/links/density/transitions)
       → score check → RM_REFINE_ROUNDS varaku LLM refine (content depth, list items)
       → prathi refine tarvata rm100 malli (rewrite structure break cheyyakunda)
       → final score article["_rm100"] lo private preflight ga store chestamu.
         WordPress Rank Math score ni eppudu fabricate/write cheyyamu.

    Mock/no-key flows skip (silently) — score inka compute avutundi.
    """
    if article.get("_mock"):
        article["_rm100"] = rm100.apply(article) if not article.get("_no_rm100") else None
        return article
    # v65: iterative deterministic passes (score → fix → score) — real-time check
    opt = rm100.optimize(article, target=int(getattr(config, "RM_TARGET", 100) or 100),
                         max_passes=2)
    res = {"after": opt["score"], "before": opt["before"],
           "applied": (opt["passes"][-1]["applied"] if opt["passes"] else [])}
    article["_rm100"] = {"score": res["after"], "before": res["before"],
                         "applied": res["applied"], "passes": len(opt["passes"])}
    article["_rm_pre"] = res["before"]
    target = int(getattr(config, "RM_TARGET", 100) or 100)
    rounds = int(getattr(config, "RM_REFINE_ROUNDS", 2) or 0)
    strict = analyze_rm(article)
    if not (config.GEMINI_API_KEY or getattr(config, "GEMINI_API_KEYS", [])):
        # key ledu → LLM refine ledu; deterministic rm100 score mattrame
        article["_rm"] = strict
        return article
    for rnd in range(1, rounds + 1):
        if strict["score"] >= target and not strict["fixes"]:
            break
        facts_before: list = []
        if getattr(config, "FACT_STRICT", True) and article.get("_source_texts"):
            facts_before = validator.fact_guard(
                article.get("content_html", ""), article["_source_texts"])
            if facts_before:
                log.warning("FACT GUARD: %d unverified data item(s): %s",
                            len(facts_before), "; ".join(str(x) for x in facts_before[:3]))
        # SUSPECT (data accuracy) fixes eppudu mundu — v66 gate hints venaka
        fixes = [f"SUSPECT data remove/verify cheyandi — {x}" for x in facts_before] + \
                list(strict["fixes"])
        # v66: pin-gate (68 checks) failures ni kuda refine hint ga ivvadam —
        # "blog rasthunnapudu inka chala check cheyali" → writing loop lo ne fix avvali.
        try:
            from . import post_gate as _pg

            early = _pg.run(article)
            hints: list = []
            for row in early["rows"]:
                if (row["ok"] or not row["fix"] or row["scored"] is False
                        or row["id"] in _PG_PUBLISH_TIME_CHECKS):
                    continue
                if row["group"] in ("CONTENT", "SEMANTIC", "SEO"):
                    hints.append(f"GATE {row['id']}: {row['fix']}")
            fixes = fixes[:10] + hints[:4]
        except Exception as exc:  # noqa: BLE001 — gate hint best-effort (publish aapadu)
            log.debug("post_gate early hints skip: %s", exc)
        if not fixes:
            break
        log.info("RankMath %d/100 (target %d) — refine round %d/%d (%d fixes)",
                 strict["score"], target, rnd, rounds, len(fixes))
        try:
            improved = gemini_client.refine_article(article, fixes[:12])
        except Exception as exc:  # noqa: BLE001 — refine best-effort, publish aapadu
            log.warning("Refine round %d failed (%s)", rnd, exc)
            break
        # v85: anti-truncation — improved <70% length = sections lost
        # (refine context cut valla) → reject, original keep.
        # Threshold 2000: real drafts 9000+ chars; test fixtures ~1000
        # (tiny fake-refines legit — guard real-posts ke).
        orig_len = len(article.get("content_html", "") or "")
        new_len = len(improved.get("content_html", "") or "")
        if orig_len > 2000 and new_len < orig_len * 0.7:
            log.warning("Refine truncated (%d → %d chars) — original keep",
                        orig_len, new_len)
            article["_fact"] = facts_before
            break
        rm2 = validator.rankmath_strict(improved, improved.get("content_html", ""))
        facts_after = (validator.fact_guard(improved.get("content_html", ""),
                                            article["_source_texts"])
                       if facts_before else [])
        facts_fixed = bool(facts_before) and not facts_after
        if not (rm2["score"] > strict["score"] or facts_fixed):
            log.info("Refine helped ledu (%s/100 vs %s/100) — original draft keep",
                     rm2["score"], strict["score"])
            article["_fact"] = facts_before
            break
        for k in ("title", "banner_text", "meta_description", "content_html",
                  "tags", "focus_keyword", "seo_title"):
            if improved.get(k):
                article[k] = improved[k]
        article["refined"] = True
        article["_fact"] = facts_after
        log.info("Refine helped: %s -> %s/100 (facts fixed: %s)",
                 strict["score"], rm2["score"], facts_fixed)
        # v64: rewrite tarvata structure malli — TOC/title/meta/links intact
        res2 = rm100.optimize(article, target=target, max_passes=2)
        strict = analyze_rm(article)
        article["_rm100"] = {"score": strict["score"], "before": res["before"],
                             "applied": (res2["passes"][-1]["applied"]
                                         if res2.get("passes") else []),
                             "rounds": rnd}
        log.info("Round %d tarvata: %d/100", rnd, strict["score"])
    article["_rm"] = strict
    return article


def analyze_rm(article: dict) -> dict:
    return validator.rankmath_strict(article, article.get("content_html", ""))


def publish_article(article: Dict, day: Optional[date] = None) -> Dict:
    """Full publish flow for a generated article dict. Returns WP result."""
    wp = WordPressClient()
    wp.check_connection()

    is_quiz = article.get("article_type") == "quiz"
    # --- QA step 1: HTML sanitize (Gemini bad tags strip) ---
    if is_quiz:
        # v26: quiz block ni memu build chesam (escaped) — sanitize only around it
        from . import quiz_engine as _qe
        article["content_html"] = _qe.sanitize_quiz_content(article["content_html"])
        article = _hygiene(article)
    else:
        article["content_html"] = validator.sanitize_html(article["content_html"])
        article = _hygiene(article)
        # v38: TOP POST hardening (structural only — kotha facts ledu):
        # keyword meta/slug, snippet answer, FAQ extraction, density cap.
        try:
            from . import top_post as _tp
            article, _tp_report = _tp.harden(article)
        except Exception:  # noqa: BLE001 — hardening never blocks publishing
            log.exception("Top-post hardening skipped (safe)")
        # v18: Rank Math STRICT gate (actual panel checks) — low ante refine round
        article = _rankmath_gate(article, article.get("category") or "")

    category_id = wp.get_or_create_term(article["category"], "categories")
    tag_ids = [wp.get_or_create_term(t, "tags") for t in article["tags"]]

    # --- SEO: quick answer + internal links + TOC + schema ---
    recent = wp.get_recent_published(per_page=8)
    same_cat = [p for p in recent if category_id in p.get("categories", [])]
    internal = (same_cat or recent)[:4]
    # Money-page strategy: traffic posts nunchi high-CPC posts ki link priority
    from . import monetize as _mz

    internal = _mz.prioritize_money_pages(internal)[:4]
    # Internal-link fallback: kotha site lo published posts levu ->
    # category archive links istundi (Rank Math internal-link check pass)
    if len(internal) < 2:
        cat_link = wp.get_term_link(category_id, "categories")
        if cat_link:
            internal.append({"link": cat_link,
                             "title": f"{article['category']} – Latest Articles"})
        if len(internal) < 2:
            internal.append({"link": f"{config.WP_SITE}/", "title": "studentup.in – Home"})
    today_str = (day or date.today()).isoformat()
    if is_quiz:
        from . import quiz_engine as _qe
        article["_link"] = ""   # real link publish tarvata telustundi; share bar
        final_html = _qe.finalize_html(   # fallback = site home
            article, internal_links=[
                {"link": p["link"], "title": p["title"]} for p in internal],
            site_url=config.WP_SITE + "/")
    else:
        final_html = seo.enhance(
            article["content_html"],
            focus_keyword=article.get("focus_keyword", ""),
            internal_links=[{"link": p["link"], "title": p["title"]} for p in internal],
            external_links=article.get("external_links", []),
            quick_answer=article.get("quick_answer", ""),
            faq=article.get("faq", []),
            date_str=today_str,
            slug=article["slug"],
            title=article["title"],
            description=article["meta_description"],
            category=article.get("category", ""),
            source_domains=article.get("_source_domains"),
            list_items=article.get("list_items") if article.get("article_type") == "listicle" else None,
            recruitment=article.get("recruitment"),
        )
    # In-content ad hard gate: before AdSense approval no ad spaces are added,
    # even if an old shortcode remains in .env by mistake.
    if config.AD_SHORTCODE and getattr(config, "ADSENSE_APPROVED", False):
        final_html = seo.insert_ad_shortcodes(
            final_html, config.AD_SHORTCODE,
            max_ads=config.MAX_AD_SLOTS, cls_safe=config.AD_CLS_WRAPPER)
    # revenue blocks: affiliate section + channel CTA (schema mundu insert)
    from . import monetize

    if not is_quiz:
        final_html = monetize.append_blocks(final_html, article)
        # v43: AD MANAGER — owner ads (college banners, shop, services).
        # Runs AFTER monetize blocks so the bottom slot + link-adjacency
        # safety check see every real <a> that exists. No-op when inventory
        # empty/missing or AD_MANAGER_ENABLED=0 (publishing never blocked).
        try:
            from . import ad_manager as _admgr
            final_html, _ad_report = _admgr.inject(final_html, article)
            article["_ads"] = _ad_report
        except Exception:  # noqa: BLE001 — owner ads must never block publish
            log.exception("Ad manager inject skipped (safe)")
            article["_ads"] = []

    # v44: DEEP POST ENGINE — cross-source verification + private report;
    # optional visible analysis is reserved for internal/debug exports.
    if not is_quiz and getattr(config, "DEEP_POST_ENABLED", True):
        try:
            from . import deep_research as _dr

            deep_sources = article.get("_deep_sources") or []
            if len(deep_sources) >= int(getattr(config, "DEEP_MIN_SOURCES", 2)):
                _report = _dr.build_report(
                    article.get("title", ""), deep_sources,
                    notebooklm_brief=article.get("_notebooklm_brief", ""),
                    target_year=article.get("_target_year"))
                # Cross-source analysis is retained for gates and the private
                # ledger. It is not printed as a confidence/source table in a
                # normal StudentUp article.
                if not getattr(config, "PUBLIC_EDITORIAL_CLEAN", True):
                    final_html = _dr.inject_deep(final_html, _report)
                article["_deep"] = _report
                _hard, _warn = _dr.gate_post(final_html, _report, live=False)
                article["_deep_flags"] = ([f"DEEP: {h}" for h in _hard] +
                                          [f"DEEP?: {w}" for w in _warn])
                log.info("v44 deep: confidence %s/100 · conflicts=%d · gaps=%d",
                         _report.get("confidence"),
                         len(_report.get("conflicts", [])),
                         len(_report.get("gaps", [])))
        except Exception:  # noqa: BLE001 — deep layer must never block publish
            log.exception("Deep post engine skipped (safe)")
            article["_deep"] = None

    # Source audit is explicit even when research failed; no vague "verified"
    # claim without a count of independent domains and official sources.
    try:
        from . import deep_research as _dr_source

        article["_source_audit"] = _dr_source.audit_source_set(article)
        log.info("Source audit: %s", _dr_source.format_source_audit(
            article["_source_audit"]))
    except Exception:
        log.exception("source audit failed")
        article["_source_audit"] = {"applicable": bool(article.get("source_url")),
                                    "ok": False, "flags": ["SOURCE-AUDIT-FAILED"]}

    # Public article surface: keep the writing, useful SEO structure and
    # verified links, but remove automation/source-count wrappers. The source
    # URLs and hashes remain in the private provenance ledger.
    if getattr(config, "PUBLIC_EDITORIAL_CLEAN", True):
        final_html = seo.clean_public_article(final_html)

    # --- reader-first language + anti-filler audit ---
    # Standard job/exam terms stay in English script; repeated/sodi prose is
    # measured separately from SEO so keyword padding can never look "good".
    final_html, article["_content_quality"] = content_quality.polish_and_audit(
        final_html, article.get("focus_keyword", ""))
    log.info("Reader quality %s/100 · filler=%s · flags=%s",
             article["_content_quality"]["score"],
             article["_content_quality"]["filler_hits"],
             article["_content_quality"]["flags"] or "none")

    # --- QA step 2: validation score + originality proof ---
    qa = validator.validate_article(article, final_html)
    article["_qa"] = qa
    article["_rm"] = validator.rankmath_strict(article, final_html)
    if not article.get("_source_texts") and article.get("_deep_sources"):
        # v78: rewrite path (_deep_sources) nunchi kuda _orig score —
        # live originality gate publish + rewrite rendu ki uniform (None kaadu).
        _st = []
        for _s in article["_deep_sources"]:
            _t = getattr(_s, "text", None)
            if _t is None and isinstance(_s, dict):
                _t = _s.get("text", "")
            if _t:
                _st.append(_t)
        article["_source_texts"] = _st
    if article.get("_source_texts"):
        article["_orig"] = validator.originality_score(
            final_html, article["_source_texts"])
    # v104: claim provenance + original practical value ledger. This does not
    # reward word count; it records source support and user-helpful signals.
    try:
        from . import editorial_value as _ev

        _ledger = _ev.build_ledger(article, final_html,
                                   article.get("_deep_sources") or [])
        article["_editorial_value"] = _ledger
        article["_editorial_flags"] = _ev.gate(
            _ledger, minimum=int(getattr(config, "EDITORIAL_VALUE_MIN", 55)))
        log.info("Editorial value %s/100 (%s) · flags=%s",
                 _ledger["score"], _ledger["grade"],
                 article["_editorial_flags"] or "none")
    except Exception:  # noqa: BLE001 — ledger advisory; other gates remain
        log.exception("editorial value ledger skipped (safe)")

    article["_google_quality"] = google_quality.audit(article, final_html, live=False)
    log.info("Google people-first self-assessment %s/100 · flags=%s",
             article["_google_quality"]["score"],
             article["_google_quality"]["flags"] or "none")
    # Deficient drafts remain available for correction; the live gate below is
    # strict. This preserves evidence instead of silently discarding research.

    # v38: TOP POST SCORE — measurable on-page quality (30+ weighted checks).
    # Quiz posts ki skip (interactive format different rules tho untundi).
    if not is_quiz:
        try:
            from . import top_post as _tp
            article["_top"] = _tp.score_top_post(article, html=final_html)
            log.info("Top Post Score %s/100 %s — failed: %s",
                     article["_top"]["score"], article["_top"]["grade"],
                     ", ".join(article["_top"]["failed"][:4]) or "none")
        except Exception:  # noqa: BLE001
            log.exception("Top-post scoring failed (safe)")
    log.info("QA score %s/100 (words=%d) originality=%s%% issues=%s",
             qa["score"], qa["words"], article.get("_orig", "n/a"),
             qa["issues"][:3] or "none")
    # v35: never let an unreviewed/under-validated article go straight live.
    # Drafts remain available for a human to fix; only direct publish is blocked.
    live_status = str(article.get("_force_status") or
                      getattr(config, "DEFAULT_POST_STATUS", "draft")).lower()
    if (getattr(config, "AUTOMATION_DRAFT_ONLY", True)
            and live_status == "publish"
            and not article.get("_manual_publish_approved")):
        log.warning("AUTOMATION_DRAFT_ONLY: automatic publish downgraded to review draft")
        article["_force_status"] = "draft"
        live_status = "draft"
    if live_status == "publish":
        reviewer = (getattr(config, "EDITORIAL_REVIEWER", "") or "").strip()
        if not reviewer:
            raise RuntimeError(
                "LIVE-PUBLISH BLOCKED: EDITORIAL_REVIEWER is empty; "
                "a named human must review the draft and official source first")
        article["_google_quality"] = google_quality.audit(
            article, final_html, live=True)
        if article["_google_quality"]["flags"]:
            raise RuntimeError(
                "LIVE-PUBLISH BLOCKED: Google people-first self-assessment — "
                + "; ".join(article["_google_quality"]["flags"][:5]))
        min_qa = max(0, min(100, int(getattr(config, "PUBLISH_QA_MIN_SCORE", 80))))
        if qa["score"] < min_qa:
            raise RuntimeError(
                f"LIVE-PUBLISH BLOCKED: local QA {qa['score']}/100 < {min_qa}; "
                "save as draft, fix the listed issues, then review manually")
        if article.get("_orig") is not None:
            min_orig = float(getattr(config, "PUBLISH_ORIGINALITY_MIN", 72))
            if float(article["_orig"]) < min_orig:
                raise RuntimeError(
                    f"LIVE-PUBLISH BLOCKED: originality {article['_orig']}% < "
                    f"{min_orig:g}% — source-backed rewrite needs editorial work")
        reader = article.get("_content_quality") or {}
        if (getattr(config, "CONTENT_QUALITY_BLOCK", True)
                and reader.get("flags")):
            raise RuntimeError(
                "LIVE-PUBLISH BLOCKED: repetitive/filler language — "
                + "; ".join(reader["flags"][:4]))
        source_audit = article.get("_source_audit") or {}
        if (getattr(config, "SOURCE_AUDIT_BLOCK", True)
                and source_audit.get("applicable") and not source_audit.get("ok")):
            raise RuntimeError(
                "LIVE-PUBLISH BLOCKED: source verification — "
                + "; ".join(source_audit.get("flags", [])[:5]))
        # v108: media duplicate/licence ledger flags live review too.
        if article.get("_media_flags"):
            raise RuntimeError(
                "LIVE-PUBLISH BLOCKED: media asset review — "
                + "; ".join(article["_media_flags"][:3]))
        # v104: a source summary with unsupported claims or no practical value
        # is not enough for live publishing. Draft review still receives flags.
        if (getattr(config, "EDITORIAL_VALUE_BLOCK", True)
                and article.get("_editorial_flags")):
            raise RuntimeError(
                "LIVE-PUBLISH BLOCKED: editorial provenance/value review — "
                + "; ".join(article["_editorial_flags"][:4]))
        # v38: Top Post gate — on-page quality measured, not claimed.
        if article.get("_top") is not None:
            from . import top_post as _tp

            ok_live, detail = _tp.publish_gate(article, live=True)
            if not ok_live:
                raise RuntimeError(
                    f"LIVE-PUBLISH BLOCKED: {detail}. Draft ga save chesi "
                    "fix cheyyandi (run.py --score-post <file>)")
            log.info("Top-post gate ✔ %s", detail)
        # v41: site-audit root-cause gate — junk HTML, unregistered shortcode,
        # duplicate TOC anchors, PII, stale dates, Govt/Private category mismatch,
        # empty title/excerpt, featured image — ivi live publish block chestayi.
        from . import site_audit as _sa

        ok_site, detail_site = _sa.article_gate(
            article, html=final_html, category=article.get("category", ""), live=True)
        if not ok_site:
            raise RuntimeError(
                f"LIVE-PUBLISH BLOCKED: {detail_site}")
        log.info("v41 site gate ✔ %s", detail_site)
        # v44: DEEP GATE — source conflicts / date inconsistency / stale
        # years block live publish (drafts carry the flags for review).
        from . import deep_research as _dr

        ok_deep, detail_deep = _dr.publish_gate(article, html=final_html,
                                                live=True)
        if not ok_deep:
            raise RuntimeError(
                f"LIVE-PUBLISH BLOCKED: {detail_deep}. Draft ga save chesi "
                "official source tho fix cheyyandi (run.py --deep-research)")
        log.info("v44 deep gate ✔ %s", detail_deep)
    try:
        _save_provenance(article)
    except OSError:
        log.warning("Provenance sidecar could not be saved", exc_info=True)
    try:  # v19: dup-guard memory (scaled-content protection for FUTURE posts)
        state.save_fingerprint(config.STATE_PATH, article["slug"],
                               validator.fingerprint_tokens(final_html))
    except Exception as exc:  # noqa: BLE001 — best-effort (silent kaadu)
        log.debug("publish_article skip: %s", exc)

    # --- featured image (alt text lo focus keyword) ---
    image_path = Path(config.OUTPUT_DIR / "images" / f"{article['slug']}.webp")
    media_id = None
    if config.IMAGE_ENABLED:
        fk = article.get("focus_keyword") or article["banner_text"]
        year = article.get("year", date.today().year)
        if image_gen.generate_featured_image(article["banner_text"], article["category"], image_path):
            alt_text = seo.image_alt(fk, article.get("category", ""), year)
            # v96: SEO thumbnail FILE NAME (keyword-category-year.webp) —
            # slug-only name kanna Google Images/Discover ki better context.
            img_name = seo.image_filename(fk, article.get("slug", ""),
                                          article.get("category", ""), year,
                                          ext=image_path.suffix.lstrip(".") or "webp")
            article["_media_filename"] = img_name
            media_id = wp.upload_media(
                image_path,
                title=article["title"],
                alt_text=alt_text,
                filename=img_name,
            )
            # v38: Top Post Score image-alt check ee alt text ni verify chestundi
            if media_id:
                article["_media_alt"] = alt_text
            # v94: Article JSON-LD ki `image` (REQUIRED for Google Article rich
            # results + Discover large card). Schema upload ki MUNDU generate
            # ayyindi, anduke ippudu patch chestunnamu (idempotent + safe).
            if media_id and getattr(wp, "last_media_url", ""):
                try:
                    final_html = seo.attach_schema_image(
                        final_html, wp.last_media_url, 1200, 675)
                    log.info("v94 schema image attach: %s", wp.last_media_url)
                except Exception:  # noqa: BLE001 — schema patch fail publish aapadu
                    log.exception("v94 schema image attach skip (publish safe)")
            # v95: content LOPALA image (keyword alt) — Rank Math "Focus Keyword
            # in Image Alt" + Discover in-article image + engagement. Idempotent
            # (html lo <img> unte no-op), CLS-safe (width/height), lazy load.
            if media_id and getattr(wp, "last_media_url", ""):
                try:
                    final_html = seo.attach_inline_image(
                        final_html, wp.last_media_url, alt_text,
                        caption=article.get("title", "")[:120], width=1200, height=675)
                    log.info("v95 inline figure attach: %s", wp.last_media_url)
                except Exception:  # noqa: BLE001 — figure fail publish aapadu
                    log.exception("v95 inline figure skip (publish safe)")

            # v108: image provenance/licence/hash ledger before local cleanup.
            # Generated-local asset ki kuda evidence undali; duplicate hash ayithe
            # live gate review ki flag chestam.
            try:
                from . import media_ledger as _ml

                _asset = _ml.record(
                    image_path, article.get("slug", ""), alt_text,
                    media_id=media_id, url=getattr(wp, "last_media_url", ""),
                )
                _dup = _ml.duplicate_hash(_asset["sha256"], article.get("slug", ""))
                if _dup:
                    article["_media_flags"] = [f"DUPLICATE-MEDIA: {_dup}"]
                article["_media_ledger"] = _asset
            except Exception:  # noqa: BLE001 — image ledger fail is review flag
                log.exception("media ledger skip (publish gate review)")
                article["_media_flags"] = ["MEDIA-LEDGER-UNAVAILABLE"]

            # disk full avvakunda — upload ayyaka local file delete
            if media_id and not config.KEEP_IMAGES:
                image_path.unlink(missing_ok=True)

    # --- Rank Math meta (plugin active unte) ---
    meta = None
    if config.RANK_MATH_META_ENABLED:
        meta = seo.rankmath_meta(
            focus_keyword=article.get("focus_keyword", article["title"][:60]),
            description=article["meta_description"],
            seo_title=article.get("seo_title") or article["title"],
            secondary_keywords=article.get("secondary_keywords", []),
            slug=article.get("slug", ""),
        )
        # Keep the exact delivery manifest with the candidate. This is not
        # rendered in the article; it lets the create/update path and tests
        # prove which fields were intended for WordPress.
        article["_rankmath_meta"] = dict(meta)

    # --- v72: qualification auto-tag (site filter: 10th · 10+2 · డిగ్రీ · పీజీ) ---
    if meta is not None:
        try:
            qmeta = qual.post_meta(article)
            if qmeta:
                meta.update(qmeta)
                log.info("v72 qual tag → %s", qual.describe(article))
        except Exception:  # noqa: BLE001 — tag fail publish aapadu (theme kuda auto detects)
            log.exception("v72 qual tag skip (publish safe)")
    # --- v77 ORIGINALITY: donor sources vs final article (REAL copy %, not claim) ---
    try:
        _srcs = []
        for _s in (article.get("_deep_sources") or []):
            _t = getattr(_s, "text", None)
            if _t is None and isinstance(_s, dict):
                _t = _s.get("text", "")
            if _t:
                _srcs.append(_t)
        article["_originality"] = validator.rewrite_distance(final_html, _srcs) \
            if _srcs else {"overlap": 0.0, "fresh": 1.0, "verdict": "no-sources"}
        log.info("ORIGINALITY fresh=%s overlap=%s (%s)",
                 article["_originality"]["fresh"], article["_originality"]["overlap"],
                 article["_originality"]["verdict"])
    except Exception:  # noqa: BLE001 — score fail publish aapadu
        log.exception("originality skip (publish safe)")
        article["_originality"] = {"overlap": 0.0, "fresh": 1.0,
                                   "verdict": "skip"}
    # --- v65 PIN-TO-PIN GATE: certificate + critical block (live publish mattrame) ---
    is_live = live_status == "publish"
    gate = ({"score": 0, "passed": 0, "total": 0, "critical_fails": [], "block": False,
             "cert_id": "mock", "rows": [], "words": 0, "rankmath": 0,
             "title": article.get("title", ""), "slug": article.get("slug", ""),
             "date": date.today().isoformat()}
            if article.get("_mock") else
            post_gate.run(article, final_html, media_id=media_id, image_path=image_path))
    article["_gate"] = gate
    try:
        paths = post_gate.write_certificate(gate) if not article.get("_mock") else {}
        article["_cert"] = paths.get("md", "")
        log.info("PIN GATE %s/100 · %s/%s checks · critical: %s", gate["score"],
                 gate["passed"], gate["total"], gate["critical_fails"] or "none")
    except Exception:  # noqa: BLE001 — certificate fail publish aapadu
        log.exception("certificate write skip (publish safe)")
    try:
        state.meta_set(config.STATE_PATH, "last_cert",
                       f"{gate['cert_id']}:{gate['score']}")
    except Exception as exc:  # noqa: BLE001 — best-effort (silent kaadu)
        log.debug("publish_article skip: %s", exc)
    if gate["critical_fails"] and gate["block"] and is_live and not article.get("_mock"):
        msg = (f"⛔ PIN GATE BLOCK — {article.get('title', '')[:60]}\n"
               f"critical: {', '.join(gate['critical_fails'])}\n"
               "(fix chesi malli run cheyandi · PIN_GATE_BLOCK=0 tho off)")
        log.error("PIN GATE BLOCK: %s", ", ".join(gate["critical_fails"]))
        try:
            send_telegram(msg)
        except Exception as exc:  # noqa: BLE001 — best-effort (silent kaadu)
            log.debug("publish_article skip: %s", exc)
        return {"error": "pin_gate", "detail": msg, "gate": gate}
    # Two-phase live publish: first create a private draft, verify that the
    # official Rank Math fields really landed, and only then make it public.
    # A missing/outdated SEO bridge can no longer produce another live 23/100
    # post with empty Focus Keyword / SEO title / Description fields.
    requested_status = str(article.get("_force_status") or
                           getattr(config, "DEFAULT_POST_STATUS", "draft")).lower()
    stage_for_seo = requested_status == "publish"
    result = wp.create_post(
        title=article["title"],
        content_html=final_html,
        slug=article["slug"],
        category_id=category_id,
        tag_ids=tag_ids,
        excerpt=article["meta_description"],
        media_id=media_id,
        status="draft" if stage_for_seo else requested_status,
        meta=meta,
    )
    # v63: SEO fields nijamainaa land ayyaya? (silent-fail pattadam — "mistake lekunda")
    if stage_for_seo and not meta:
        result["seo_meta_missing"] = ["Rank Math meta generation disabled"]
        log.error("Live publish blocked: RANK_MATH_META_ENABLED is off")
    if meta and result.get("id"):
        try:
            required_seo = [k for k in meta if k.startswith("rank_math_")]
            # verify_meta is the legacy/core read; verify_rankmath_meta adds
            # bridge readback so a hidden REST field is not reported as empty.
            landed = wp.verify_rankmath_meta(result["id"], required_seo)
            missing = [k for k, ok in landed.items() if not ok]
            if missing and not article.get("_mock"):
                # Generic wp/v2 meta schema failed: use the narrow authenticated
                # theme bridge, then read back from WordPress for proof. The
                # bridge read is important because some Rank Math versions do
                # not expose registered meta in the normal post response.
                wp.write_seo_meta(result["id"], meta)
                landed = wp.verify_rankmath_meta(result["id"], required_seo)
                missing = [k for k, ok in landed.items() if not ok]
            article["_rankmath_landed"] = dict(landed)
            result["seo_meta_persisted"] = not missing
            result["seo_meta_keys"] = required_seo
            if missing:
                log.warning("Rank Math meta land avvaledu: %s (id=%s) — theme seo-bridge "
                            "activate cheyandi (wordpress-theme/studentup/inc/seo-bridge.php)",
                            ", ".join(missing), result["id"])
                result["seo_meta_missing"] = missing
                try:
                    notifier.send_telegram(
                        "⚠️ <b>SEO meta WAR</b> — post %s lo %s land avvaledu.\n"
                        "Fix: WP theme (StudentUp) active undo chudandi (SEO bridge)."
                        % (result["id"], ", ".join(missing)))
                except Exception as exc:  # noqa: BLE001 — best-effort (silent kaadu)
                    log.debug("publish_article skip: %s", exc)
            else:
                log.info("Rank Math meta verified ✔ (id=%s)", result["id"])
                if stage_for_seo:
                    result.update(wp.set_post_status(result["id"], "publish"))
                    log.info("SEO-verified draft promoted to publish ✔ (id=%s)",
                             result["id"])
        except Exception:
            # In two-phase mode the post is still a draft, so a bridge/readback
            # failure is safe and cannot trigger the public-channel notification.
            log.exception("meta verify failed; staged post remains draft")
    if result.get("id") and hasattr(wp, "read_rankmath_state"):
        try:
            rankmath_state = wp.read_rankmath_state(result["id"])
            result["rank_math_ui_score"] = rankmath_state.get("rank_math_ui_score")
            article["_rank_math_state"] = rankmath_state
            if result["rank_math_ui_score"] is None:
                log.info("Official Rank Math stored UI score unavailable; no estimate reported")
            else:
                log.info("Rank Math stored UI score (read-only): %s/100",
                         result["rank_math_ui_score"])
        except Exception:
            log.exception("Rank Math read-only state unavailable")
    state.record_post(config.STATE_PATH, article["title"], article["slug"],
                      article["category"], result["link"], result["status"],
                      qa_score=(article.get("_qa") or {}).get("score"),
                      orig_score=article.get("_orig"), wp_id=result.get("id"))
    state.bump_today_count(config.STATE_PATH, day or date.today())
    if article.get("source_url"):
        state.mark_source_done(config.STATE_PATH, article["source_url"], result.get("id"))
    try:
        state.meta_cleanup(config.STATE_PATH)  # purana rojuvella keys tidy
    except Exception as exc:  # noqa: BLE001 — best-effort (silent kaadu)
        log.debug("publish_article skip: %s", exc)

    log.info("POST CREATED ✔ id=%s status=%s link=%s",
             result.get("id"), result.get("status"), result.get("link"))
    if result.get("status") == "publish":
        _after_publish_push(article, result)
    try:
        notifier.notify_new_post(article, result)
    except Exception:
        log.exception("Notification failed (post safe ga save ayyindi)")
    return result


def _after_publish_push(article: Dict, result: Dict) -> None:
    """Publish ayyaka instant traffic/indexing push (best-effort)."""
    # 1) Instant indexing: IndexNow (Bing/Yandex) + Google Indexing API (JobPosting)
    try:
        from . import indexing

        idx = indexing.submit_published(article, result.get("link", ""))
        article["_indexing"] = idx
        article["_indexnow"] = bool(idx.get("indexnow"))
        if idx.get("google"):
            log.info("Google Indexing API ✔ (JobPosting) %s", result.get("link", ""))
    except Exception as exc:  # noqa: BLE001 — indexing best-effort (publish aapadu)
        log.warning("Indexing push fail: %s", exc)
    # 2) Telegram channel auto-post (instant traffic + social signal)
    try:
        if config.TELEGRAM_CHANNEL_CHAT_ID:
            qa = article.get("_qa") or {}
            gq = article.get("_google_quality") or {}
            send_telegram(
                f"🆕 <b>{esc(article['title'])}</b>\n\n"
                f"{esc((article.get('meta_description') or '')[:180])}\n\n"
                f"🔗 {esc(result.get('link', ''))}\n"
                f"📊 QA {qa.get('score', '-')}/100 · People-first "
                f"{gq.get('score', '-')}/100 · ~{qa.get('reading_min', '-')} min read",
                chat_id=config.TELEGRAM_CHANNEL_CHAT_ID,
            )
    except Exception:
        log.exception("Channel auto-post failed")


def _append_official_sources(article: dict) -> None:
    """Provenance → visible official links (v86 gated).

    Article independently written; links let a student verify a date/fee
    instead of trusting an AI summary. ONLY official domains → external
    links ("అధికారిక లింక్స్"); news/blog sources stay out (su-source +
    trust-box already give provenance, mislabel kakunda).
    """
    from .sources import is_official_domain
    # v87: None-safe (update-path articles lo key missing/None untundi)
    article["external_links"] = article.get("external_links") or []
    source_hosts = {urlparse(u).netloc.lower().replace("www.", "")
                    for u in (article.get("_source_urls") or []) if u}
    # A model may echo the research blog as an "official link". Keep the
    # private provenance, but do not publish that duplicate attribution block;
    # genuine authority/company links supplied separately remain available.
    filtered = []
    for item in article["external_links"]:
        if not isinstance(item, dict):
            continue
        u = str(item.get("url", "")).strip()
        host = urlparse(u).netloc.lower().replace("www.", "") if u else ""
        if host and host in source_hosts and not is_official_domain(host):
            continue
        filtered.append(item)
    article["external_links"] = filtered
    known_links = {str(item.get("url", "")).rstrip("/")
                   for item in article["external_links"] if isinstance(item, dict)}
    for source_url in (article.get("_source_urls") or [])[:6]:
        host = urlparse(source_url).netloc
        if source_url.rstrip("/") in known_links or not is_official_domain(host):
            continue
        known_links.add(source_url.rstrip("/"))
        article["external_links"].append({
            "text": f"Official Notice — {host.replace('www.', '')}",
            "url": source_url,
        })


def _source_evidence_context(report: Dict) -> str:
    """Compact verified-fact ledger supplied to a correction pass."""
    rows = []
    for fact in (report or {}).get("verified", [])[:40]:
        value = fact.get("value", "")
        if not value or fact.get("kind") == "official_link":
            continue
        sources = ", ".join(fact.get("sources", [])[:4])
        rows.append(f"{fact.get('kind', 'fact')}: {value} [{fact.get('status', 'unknown')}; {sources}]")
    return "\n".join(rows) or "No verified numeric/date facts; do not add any."


def _correct_source_claims(article: Dict) -> None:
    """Make a bounded factual correction pass before the hard preflight.

    The first model output is never trusted blindly. If dates/counts are not
    supported by the fetched source text, or the deep report finds a conflict,
    ask the model to remove/correct those claims using only the evidence ledger.
    A failed correction is left for the hard gate to reject.
    """
    if article.get("_mock") or not config.gemini_configured():
        return
    from . import deep_research as _dr

    sources_text = [
        getattr(source, "text", "") or (source.get("text", "") if isinstance(source, dict) else "")
        for source in (article.get("_deep_sources") or [])
    ]
    report = _dr.build_report(
        article.get("title", ""), article.get("_deep_sources") or [],
        notebooklm_brief=article.get("_notebooklm_brief", ""),
        target_year=article.get("_target_year"),
    )
    fact_flags = validator.fact_guard(article.get("content_html", ""), sources_text)
    hard, _warnings = _dr.gate_post(article.get("content_html", ""), report, live=True)
    fixes = fact_flags + hard
    if not fixes:
        return
    log.warning("Source correction pass: %d unsupported/conflicting item(s)", len(fixes))
    try:
        evidence = _source_evidence_context(report)
        improved = gemini_client.refine_article(
            article, fixes[:12], source_evidence=evidence)
        for key in ("title", "meta_description", "seo_title", "content_html",
                    "focus_keyword", "secondary_keywords", "tags", "faq",
                    "quick_answer"):
            if improved.get(key):
                article[key] = improved[key]
        corrected_html = article.get("content_html", "")
        overlaps = validator.verbatim_overlaps(corrected_html, sources_text)
        originality = validator.originality_score(corrected_html, sources_text)
        floor = float(getattr(config, "ORIG_HARD_FLOOR", 72))
        if overlaps or originality < floor:
            raise RuntimeError(
                "SOURCE CORRECTION REJECTED: rewrite copy-risk remains "
                f"(originality={originality:.1f}%, overlaps={len(overlaps)})")
    except RuntimeError:
        raise
    except Exception as exc:  # noqa: BLE001 — preflight remains the hard gate
        log.warning("Source correction pass unavailable: %s", exc)


def _strict_source_preflight(article: Dict, *, allow_mock: bool = False) -> Dict:
    """Validate evidence before a source-derived article reaches WordPress.""

    A source URL/search result is not permission to invent missing facts. This
    gate requires the fetched source set, an official source, the cross-source
    report, numeric/date fact support and the claim ledger. It deliberately
    runs before draft creation, not only before live publishing.
    """
    if allow_mock or article.get("article_type") == "quiz":
        return {"ok": True, "skipped": True}
    if not getattr(config, "SOURCE_PREFLIGHT_REQUIRED", True):
        return {"ok": True, "skipped": True, "reason": "disabled by config"}
    from . import deep_research as _dr
    from . import editorial_value as _ev

    deep_sources = list(article.get("_deep_sources") or [])
    report = _dr.build_report(
        article.get("title", ""), deep_sources,
        notebooklm_brief=article.get("_notebooklm_brief", ""),
        target_year=article.get("_target_year"),
    )
    article["_deep"] = report
    audit = _dr.audit_source_set(article)
    article["_source_audit"] = audit
    source_texts = []
    for source in deep_sources:
        text = source.get("text", "") if isinstance(source, dict) else getattr(source, "text", "")
        if text:
            source_texts.append(text)
    fact_flags = validator.fact_guard(article.get("content_html", ""), source_texts)
    article["_source_fact_flags"] = fact_flags
    ledger = _ev.build_ledger(article, article.get("content_html", ""), deep_sources)
    article["_editorial_value"] = ledger
    claim_flags = [
        f"{item.get('value', 'claim')}: source evidence missing"
        for item in ledger.get("unsupported_claims", [])[:8]
    ]
    article["_claim_flags"] = claim_flags
    hard, warnings = _dr.gate_post(article.get("content_html", ""), report, live=True)
    result = {
        "ok": not audit.get("flags") and not fact_flags and not claim_flags and not hard,
        "audit": audit, "fact_flags": fact_flags,
        "claim_flags": claim_flags, "deep_hard": hard, "warnings": warnings,
    }
    article["_source_preflight"] = result
    if not result["ok"]:
        parts = (audit.get("flags", []) + fact_flags + claim_flags + hard)[:8]
        raise RuntimeError(
            "SOURCE PREFLIGHT FAILED — article not created because evidence is incomplete: "
            + "; ".join(parts)
        )
    log.info("SOURCE PREFLIGHT PASS ✔ %s", _dr.format_source_audit(audit))
    return result


def create_from_source(url: str, mock: bool = False, category: str = "",
                       notebooklm_brief: str = "",
                       target_year: int | None = None,
                       force_draft: bool = False) -> Dict:
    """Vere site URL -> 100% original SEO article -> draft post.

    category empty aite auto-classify (Telugu+English keywords tho).
    """
    if not sources.is_valid_source_url(url):
        raise ValueError("URL valid kadu (http/https link ivvandi)")

    if state.source_done(config.STATE_PATH, url):
        raise ValueError("Ee URL already process chesayi — duplicate!")

    log.info("Source fetch chestunnanu: %s", url)
    src = sources.fetch_source(url)
    log.info("Source ready: %s (%d chars)", src.title[:60], len(src.text))
    if target_year is None:
        from .research_brief import target_year_from_text
        target_year = target_year_from_text(f"{src.title} {url} {notebooklm_brief[:4000]}")
    generation_year = target_year or date.today().year
    if target_year:
        log.info("Target-year mode enabled: %d — other-year claims require verification", target_year)

    # --- multi-source research: internet lo same topic articles ---
    extras, competitor_titles = [], []
    notebooklm_bundle = {}
    if config.RESEARCH_ENABLED and not mock:
        try:
            extras, competitor_titles = research.research_topic(
                src, config.RESEARCH_MAX_SOURCES)
            if extras:
                log.info("Research: +%d extra sources (MERGE & BEAT mode)", len(extras))
            else:
                log.info("Research: extra sources levu — primary source tho rewrite")
        except Exception:
            log.exception("Research step failed — primary source tho continue")
        if getattr(config, "NOTEBOOKLM_AUTO_BUNDLE", True):
            try:
                from . import research_brief as _rb

                notebooklm_bundle = _rb.write_bundle(
                    src.title, [src] + extras, target_year=target_year)
                log.info("NotebookLM bundle ready: %d sources → %s",
                         notebooklm_bundle.get("sources", 0),
                         notebooklm_bundle.get("bundle"))
            except Exception:
                # Bundle preparation is observable but never substitutes for
                # the strict fetched-source preflight below.
                log.exception("NotebookLM bundle preparation skipped")

    if mock:
        article = {
            "title": f"{src.title[:80]} – Complete Guide {generation_year} (Original)",
            "slug": "src-" + src.title.lower().replace(" ", "-")[:30],
            "meta_description": f"{src.title[:100]} — Telugu lo complete details.",
            "tags": [str(generation_year), "Students", "Telugu", "Guide", "News"],
            "banner_text": f"Students Guide {generation_year}",
            "content_html": (
                "<p>ఈ ఆర్టికల్‌లోని ముఖ్యమైన విషయాలను సులభమైన భాషలో "
                f"వివరించాము: {src.title}</p>"
                "<h2>Key Details</h2><ul><li>Point one</li><li>Point two</li></ul>"
                "<h2>Process</h2><ol><li>Step one</li><li>Step two</li></ol>"
                "<h2>FAQ</h2><h3>Question?</h3><p>Answer</p>"
            ),
            "category": category or classify_category(src.title, src.text),
            "model": "mock",
            "focus_keyword": f"test guide {generation_year}",
            "seo_title": f"Test Guide {generation_year} – Complete Details",
            "secondary_keywords": ["test guide details", f"{generation_year} guide telugu"],
            "quick_answer": (f"Test guide {generation_year} gurinchi menu thelisi untundi — "
                             "ee quick answer featured snippet test kosam."),
            "faq": [
                {"question": "Ee guide em gurinchi?", "answer": "Test guide gurinchi."},
                {"question": "Ela apply cheyali?", "answer": "Online lo apply cheyali."},
            ],
            "external_links": [{"text": "Official Site", "url": "https://www.gov.in"}],
            "source_url": url,
            "source_title": src.title,
        }
    else:
        recent = state.recent_titles(config.STATE_PATH, limit=30)
        article = gemini_client.generate_article_from_source(
            src, recent, generation_year, extras=extras,
            competitor_titles=competitor_titles,
            notebooklm_brief=notebooklm_brief,
        )
        if category:
            # Curated source-grid hints are authoritative; they were assigned
            # by the editor/source map, not guessed from generic headlines.
            article["category"] = category
        else:
            # Never trust the model's broad fallback (often Central Govt Jobs
            # for a software notification). Reclassify from the source title +
            # generated title with the canonical intent rules.
            article["category"] = classify_category(
                f"{src.title} {article.get('title', '')}", src.text)
        # --- originality guard: 70% kante takkuva aite OKKO regenerate ---
        source_texts = [src.text] + [e.text for e in extras]
        if notebooklm_brief:
            from . import research_brief as _rb
            source_urls = [src.url] + [e.url for e in extras]
            brief_check = _rb.validate_editor_brief(
                notebooklm_brief, source_urls, target_year=target_year)
            if not brief_check["ok"]:
                raise ValueError(
                    "NotebookLM brief validation failed: "
                    + "; ".join(brief_check["problems"]))
            article["_notebooklm_claims"] = brief_check["claims"]
            article["_notebooklm_sources"] = brief_check["source_ids"]
        article["content_html"] = validator.sanitize_html(article["content_html"])
        orig = validator.originality_score(article["content_html"], source_texts)
        overlaps = validator.verbatim_overlaps(article["content_html"], source_texts)
        if overlaps:
            log.warning("Exact source phrase overlap detected (%d runs) — regenerate", len(overlaps))
        if orig < 70.0 or overlaps:
            log.warning("Source similarity guard triggered (originality %.1f%%) — regenerate", orig)
            try:
                retry_article = gemini_client.generate_article_from_source(
                    src, recent, generation_year, extras=extras,
                    competitor_titles=competitor_titles,
                    notebooklm_brief=notebooklm_brief,
                )
                retry_article["content_html"] = validator.sanitize_html(
                    retry_article["content_html"])
                retry_orig = validator.originality_score(
                    retry_article["content_html"], source_texts)
                retry_overlaps = validator.verbatim_overlaps(
                    retry_article["content_html"], source_texts)
                # Prefer a clean rewrite over a numerically higher similarity
                # score; exact copied runs are never an acceptable tradeoff.
                better = (not retry_overlaps and bool(overlaps)) or (
                    len(retry_overlaps) < len(overlaps)
                    and retry_orig >= orig - 2.0
                ) or (not overlaps and retry_orig > orig)
                if better:
                    log.info("Regenerate better: %.1f%% -> %.1f%%; exact runs %d -> %d",
                             orig, retry_orig, len(overlaps), len(retry_overlaps))
                    article, orig, overlaps = retry_article, retry_orig, retry_overlaps
            except gemini_client.GeminiError:
                log.exception("Regenerate failed — first version e continue")
        if overlaps:
            raise RuntimeError(
                "SKIP-VERBATIM-OVERLAP: rewrite still shares exact long phrases "
                "with a source; source set needs editorial rewriting before use")
        # v18 HARD FLOOR: near-copy anipichte publish EEDU (AdSense rule #1 —
        # copied content unte site approve avakapote runtime lo ban risk)
        floor = getattr(config, "ORIG_HARD_FLOOR", 72)
        if orig < floor:
            raise RuntimeError(
                f"SKIP-NEAR-COPY: best originality {orig:.1f}% < hard floor "
                f"{floor}% — ee source ni skip chestunnam (AdSense risk). "
                f"Inko deep-rewrite source try cheyandi: {src.url}")

        # v103: local donors tho match avvakapoyina, internet lo unknown copied
        # phrase undochu. Distinctive sentences ni live exact-search chesi
        # returned pages fetch chesi verify chestam. Match = publish BLOCK.
        if getattr(config, "ORIG_LIVE_CHECK", True):
            try:
                from . import originality_live as _live

                _live_rep = _live.check(
                    article["content_html"],
                    own_domain=urlparse(config.WP_SITE).netloc,
                    max_phrases=getattr(config, "ORIG_LIVE_PHRASES", 3),
                )
                article["_live_originality"] = _live_rep
                log.info("%s", _live.format_report(_live_rep))
                if _live_rep.get("matches"):
                    raise RuntimeError(
                        "SKIP-LIVE-EXACT-OVERLAP: live web search found copied "
                        f"phrase(s) on {len(_live_rep['matches'])} page(s); "
                        "human rewrite/source attribution required")
                if (_live_rep.get("status") in ("partial", "error")
                        and getattr(config, "ORIG_LIVE_REQUIRED", False)):
                    raise RuntimeError(
                        "SKIP-LIVE-CHECK-UNAVAILABLE: required real-time "
                        "originality check did not complete")
            except RuntimeError:
                raise
            except Exception:  # noqa: BLE001 — report, never fake PASS
                log.exception("live originality check failed (local gates remain)")

    # v19: near-duplicate guard — Google "scaled content abuse" policy:
    # swapped-name/only-date-changed pages site-wide signal ni charchestayi.
    # Mana published posts tho ee level dup ante SKIP (AdSense + ranking both).
    try:
        ratio, match = validator.near_duplicate(
            article["title"], article["content_html"],
            state.load_fingerprints(config.STATE_PATH),
            config.DUP_JACCARD_SKIP)
        if ratio >= config.DUP_JACCARD_SKIP:
            raise RuntimeError(
                f"SKIP-NEAR-DUP: {ratio:.0%} overlap with existing post "
                f"'{match}' — different exam/notification topic pick cheyandi")
        elif ratio >= 0.40:
            log.warning("Near-dup warning: %.0f%% overlap with '%s' (ok, but watch)",
                        ratio, match)
    except RuntimeError:
        raise
    except Exception as exc:  # noqa: BLE001 — guard never blocks on infra error
        log.warning("Dup guard skipped (%s)", exc)

    if notebooklm_bundle:
        # Private provenance only; never render bundle paths or source labels in
        # the public article.
        article["_notebooklm_bundle"] = {
            key: str(value) for key, value in notebooklm_bundle.items()
        }
    if (getattr(config, "NOTEBOOKLM_REQUIRED", False)
            and not mock and not notebooklm_brief):
        raise RuntimeError(
            "NOTEBOOKLM BRIEF REQUIRED: import the private evidence bundle into "
            "NotebookLM and rerun with --notebooklm-brief <cited-brief.md>")

    # --- QA data (notification + trust box kosam) ---
    article["_source_texts"] = [src.text] + [e.text for e in extras]
    article["_deep_sources"] = [src] + extras  # v44: full objects (tiering)
    article["_target_year"] = target_year
    article["_notebooklm_brief"] = notebooklm_brief
    article["_source_urls"] = [src.url] + [e.url for e in extras]
    article["_source_domains"] = [
        d for d in [urlparse(src.url).netloc.replace("www.", "")]
        + [urlparse(e.url).netloc.replace("www.", "") for e in extras]
    ]

    # One bounded correction pass fixes source-detectable mistakes before the
    # strict preflight. Anything still unsupported/conflicting is rejected.
    _correct_source_claims(article)
    _append_official_sources(article)

    # Do not spend a WordPress draft slot on an article whose source facts or
    # claim evidence have not passed the strict source preflight.
    _strict_source_preflight(article, allow_mock=mock)

    # slug safe ga + Rank Math optimize (keyword tokens + stopwords)
    from .main import _safe_slug
    article["slug"] = seo.optimize_slug(
        _safe_slug(article.get("slug", ""), article["title"]),
        focus_keyword=article.get("focus_keyword", ""))
    article.setdefault("focus_keyword", "")
    article.setdefault("external_links", [])
    article.setdefault("secondary_keywords", [])
    article.setdefault("quick_answer", "")
    article.setdefault("faq", [])
    article.setdefault("seo_title", "")
    # Mock runs can assert the outbound payload, but they must never be
    # mistaken for proof that a real WordPress bridge persisted it.
    article["_mock"] = bool(mock)
    if force_draft:
        # Radar/orchestrator output always waits for owner review, irrespective
        # of the site's normal publishing default. It must also pass evidence
        # quality BEFORE consuming a WordPress draft slot or notifying Telegram.
        article["_force_status"] = "draft"
        if not mock:
            from . import deep_research as _pre

            article["_deep"] = _pre.build_report(
                article.get("title", src.title), [src] + extras,
                notebooklm_brief=notebooklm_brief,
                target_year=target_year)
            preflight = _pre.audit_source_set(article)
            article["_source_audit"] = preflight
            if not preflight.get("ok"):
                raise RuntimeError(
                    "DRAFT EVIDENCE REJECTED: "
                    + "; ".join(preflight.get("flags", [])[:5]))
            hard, _warnings = _pre.gate_post(
                article.get("content_html", ""), article["_deep"], live=True)
            if hard:
                raise RuntimeError("DRAFT FACT CONFLICT: " + "; ".join(hard[:4]))
            log.info("Evidence preflight ✔ %s", _pre.format_source_audit(preflight))

    return publish_article(article)


# ------------------------------------------------------------------ update flow

def update_post(post_id: int, new_source_urls=None, mock: bool = False) -> Dict:
    """Already-published/draft post ni kotha info tho IMPROVE chesi update.

    Same URL (slug preserve) — Google lo freshness boost + SEO juice safe.
    new_source_urls: user ichina kotha source URLs (optional).
    Levu ante post title meeda auto web research chestundi.
    """
    wp = WordPressClient()
    wp.check_connection()
    post = wp.get_post(post_id)
    title = (post.get("title") or {}).get("raw") or (post.get("title") or {}).get("rendered", "")
    existing_html = (post.get("content") or {}).get("raw", "") or (post.get("content") or {}).get("rendered", "")
    slug = post.get("slug", "")
    link = post.get("link", "")
    existing_text = validator.strip_tags(existing_html)
    log.info("Update mode: post %s '%s' (%d chars)", post_id, title[:50], len(existing_text))

    # --- kotha sources gather ---
    extras = []
    from .sources import SourceArticle as SA

    for u in (new_source_urls or []):
        try:
            extras.append(sources.fetch_source(u))
        except Exception as exc:
            log.warning("New source fetch fail (%s): %s", u[:60], exc)
    if config.RESEARCH_ENABLED and not mock and len(extras) < 2:
        try:
            pseudo = SA(url=link or f"{config.WP_SITE}/?p={post_id}",
                        title=title, site_name="studentup.in", text="")
            more, _unused = research.research_topic(pseudo, config.RESEARCH_MAX_SOURCES)
            extras.extend(more)
        except Exception:
            log.exception("Auto research fail — manual sources tho continue")
    if not extras and not mock:
        raise ValueError("Kotha information dorakaledu — source URL ivvandi "
                         "or konchem rojulu tarvata try cheyandi")

    # --- generate updated version ---
    if mock:
        article = {
            "title": title,
            "slug": slug or "keep",
            "meta_description": f"{title[:100]} — updated version.",
            "tags": ["2026", "Students", "Telugu", "Guide"],
            "banner_text": "Updated Guide",
            "content_html": (
                "<p>Ee updated test article — kotha info merge ayyindi.</p>"
                "<h2>Key Details</h2><ul><li>Old point</li><li>Kotha point add ayyindi</li></ul>"
                "<h2>Process</h2><ol><li>Step one</li><li>Step two</li></ol>"
                "<h2>FAQ</h2><h3>Q?</h3><p>A</p>"
            ),
            "category": "Education News",
            "model": "mock",
            "focus_keyword": "test guide 2026",
            "secondary_keywords": ["update test"],
            "quick_answer": "Updated quick answer for the test.",
            "faq": [{"question": "Q?", "answer": "A"}],
            "update_notes": "• Kotha fee details add chesayi (test)",
        }
    else:
        fk = ""
        try:
            fk = (post.get("meta") or {}).get("rank_math_focus_keyword", "") or ""
            fk = fk.split(",")[0].strip()
        except Exception as exc:  # noqa: BLE001 — best-effort (silent kaadu)
            log.debug("update_post skip: %s", exc)
        article = gemini_client.generate_update(
            title, existing_text, fk, extras, date.today().year,
        )

    # identity preserve — URL marakudadu
    article["title"] = title
    article["slug"] = slug
    article["content_html"] = validator.sanitize_html(article["content_html"])
    article = _hygiene(article)
    article.setdefault("update_notes", "")
    article["_deep_sources"] = list(extras)  # v77: update originality scoring
    # v87: update kuda official-source links (create-path parity — kotha
    # gov notice links updates lo poyevai!)
    article["_source_urls"] = [e.url for e in extras if getattr(e, "url", "")]
    _append_official_sources(article)
    _strict_source_preflight(article, allow_mock=mock)

    # v84: update kuda rm100 re-run (LLM rewrite structure degrade kakunda +
    # internal preflight fresh). Fail ayina update aagadu (advisory).
    try:
        if not article.get("_no_rm100"):
            _ures = rm100.optimize(
                article, target=int(getattr(config, "RM_TARGET", 100) or 100),
                max_passes=2)
            # v87: optimize returns "score" (not "after") — v84 key bug valla
            # update rm100 ALWAYS skip ayyedi (KeyError → advisory catch)!
            article["_rm100"] = {"score": _ures["score"],
                                 "before": _ures["before"]}
            log.info("Update rm100 %s→%s", _ures["before"], _ures["score"])
    except Exception:  # noqa: BLE001 — advisory (update safe)
        log.exception("update rm100 skip (post safe)")

    # v101 DECEPTIVE-FRESHNESS GUARD: Google Aug-2026 spam update
    # "dateModified bumped with no real change" ni target chestundi, mariyu
    # "a scheduled job doing it nightly turns a one-off into a pattern".
    # Mana auto_refresh roju nadustundi — so content nijamga marithe
    # MATRAME dateModified bump cheyali. Lekapothe fake freshness signal.
    # Fail-closed for the freshness *signal*: if the audit cannot run, the
    # content refresh may continue but dateModified must NOT be fabricated.
    _fresh = {"publish": True, "bump_date": False, "change_pct": 0.0,
              "reason": "guard unavailable — dateModified bump blocked"}
    try:
        from . import freshness as _freshness

        _fresh = _freshness.decide(existing_html, article["content_html"])
        article["_freshness"] = _fresh
        log.info("FRESHNESS change=%.1f%% bump=%s — %s",
                 _fresh["change_pct"], _fresh["bump_date"], _fresh["reason"])
    except Exception:  # noqa: BLE001 — guard fail refresh ni aapadu
        log.exception("freshness guard skip (refresh safe, bump allowed)")
    if not _fresh.get("publish", True):
        log.warning("UPDATE SKIPPED post %s: %s", post_id, _fresh["reason"])
        return {"skipped": True, "post_id": post_id,
                "reason": _fresh["reason"], "freshness": _fresh,
                "link": post.get("link", "")}

    # --- SEO re-enhance (fresh TOC/quick answer/schema) ---
    recent = wp.get_recent_published(per_page=8)
    internal = [p for p in recent if p.get("id") != post_id][:4]
    final_html = seo.enhance(
        article["content_html"],
        focus_keyword=article.get("focus_keyword", ""),
        internal_links=[{"link": p["link"], "title": p["title"]} for p in internal],
        external_links=article.get("external_links", []),
        quick_answer=article.get("quick_answer", ""),
        faq=article.get("faq", []),
        # Google freshness rule: original datePublished preserve, dateModified new
        date_str=(post.get("date") or date.today().isoformat())[:10],
        # v101: nijamaina change unte matrame kotha dateModified — lekapothe
        # original modified date ne uncham (fake freshness Google ki vaddu).
        date_modified=(date.today().isoformat() if _fresh.get("bump_date", True)
                       else (post.get("modified") or post.get("date")
                             or date.today().isoformat())[:10]),
        slug=slug,
        title=title,
        description=article["meta_description"],
        category=article.get("category", ""),
        source_domains=[e.site_name for e in extras],
        recruitment=article.get("recruitment"),
    )
    # v96 BUG FIX: refresh flow lo monetize blocks MISS ayyevi. `publish_article`
    # lo `monetize.append_blocks()` untundi, kaani update path lo ledu — so
    # auto-refresh (roju purana posts) ayina prathi post nunchi Telegram CTA,
    # affiliate section mariyu v96 join strip **poyevi**. Refresh ekkuva
    # ayina kొద్దీ site lo CTA-less posts perigevi (channel growth + RPM loss).
    try:
        from . import monetize as _mz_upd

        final_html = _mz_upd.append_blocks(final_html, article)
        try:
            from . import ad_manager as _admgr_upd

            final_html, _ad_report = _admgr_upd.inject(final_html, article)
            article["_ads"] = _ad_report
        except Exception:  # noqa: BLE001 — owner ads must never block a refresh
            log.exception("Update ad manager inject skipped (safe)")
    except Exception:  # noqa: BLE001 — CTA fail update aapadu
        log.exception("update monetize blocks skip (post safe)")

    try:
        from . import deep_research as _dr_update
        article["_source_audit"] = _dr_update.audit_source_set(article)
    except Exception:
        log.exception("update source audit failed")
        article["_source_audit"] = {"applicable": True, "ok": False,
                                    "flags": ["SOURCE-AUDIT-FAILED"]}
    if getattr(config, "PUBLIC_EDITORIAL_CLEAN", True):
        final_html = seo.clean_public_article(final_html)
    final_html, article["_content_quality"] = content_quality.polish_and_audit(
        final_html, article.get("focus_keyword", ""))
    try:
        from . import editorial_value as _ev_update
        article["_editorial_value"] = _ev_update.build_ledger(
            article, final_html, article.get("_deep_sources") or [])
    except Exception:
        log.exception("update editorial ledger failed")
        article["_editorial_value"] = {"score": 0,
                                       "unsupported_claims": ["ledger unavailable"]}
    article["_google_quality"] = google_quality.audit(article, final_html, live=True)
    if article["_google_quality"]["flags"] and not mock:
        return {"error": "google_quality", "post_id": post_id,
                "reason": "; ".join(article["_google_quality"]["flags"]),
                "link": post.get("link", "")}
    if (getattr(config, "CONTENT_QUALITY_BLOCK", True)
            and article["_content_quality"]["flags"] and not mock):
        return {"error": "content_quality", "post_id": post_id,
                "reason": "; ".join(article["_content_quality"]["flags"]),
                "link": post.get("link", "")}
    qa = validator.validate_article(article, final_html)
    article["_qa"] = qa
    log.info("Update QA %s/100 words=%d · reader=%s/100", qa["score"], qa["words"],
             article["_content_quality"]["score"])
    try:  # v77: update kuda originality proof (donor sources vs final)
        article["_originality"] = validator.rewrite_distance(
            final_html, [e.text for e in extras if getattr(e, "text", "")])
        log.info("ORIGINALITY (update) fresh=%s (%s)",
                 article["_originality"]["fresh"],
                 article["_originality"]["verdict"])
    except Exception:  # noqa: BLE001
        log.exception("update originality skip (post safe)")

    meta = None
    if config.RANK_MATH_META_ENABLED:
        meta = seo.rankmath_meta(
            focus_keyword=article.get("focus_keyword", title[:60]),
            description=article["meta_description"],
            seo_title=article.get("seo_title") or title,
            secondary_keywords=article.get("secondary_keywords", []),
            slug=article.get("slug", ""),
        )
        article["_rankmath_meta"] = dict(meta)

    try:  # v65: update ki kuda certificate (evidence)
        gate = post_gate.run(article, final_html)
        article["_gate"] = gate
        post_gate.write_certificate(gate)
        log.info("PIN GATE (update) %s/100 · critical: %s", gate["score"],
                 gate["critical_fails"] or "none")
    except Exception:
        log.exception("update gate skip (post safe)")
    # v105: exact rollback point BEFORE the remote PUT. WordPress revisions
    # alone are not enough — preserve source ledger + candidate diff locally.
    try:
        from . import update_safety as _us

        article["_update_backup"] = _us.create_backup(
            post, final_html, new_meta=meta,
            ledger=article.get("_editorial_value") or {},
        )
        log.info("Update backup ✔ %s (%d diff lines)",
                 article["_update_backup"]["path"],
                 article["_update_backup"]["diff_lines"])
    except Exception as exc:  # noqa: BLE001 — never update without logging
        log.exception("update backup failed — REFUSING remote update")
        return {"error": "update_backup", "post_id": post_id,
                "reason": str(exc), "link": post.get("link", "")}

    result = wp.update_post(
        post_id,
        content_html=final_html,
        title=title,  # same title enforce (URL + identity safe)
        excerpt=article["meta_description"],
        meta=meta,
    )
    # v111: transparent correction/update ledger after successful WP write.
    try:
        from . import corrections as _corr

        article["_correction_record"] = _corr.record(
            post_id, title, reason="research-backed refresh",
            sources=article.get("_source_urls") or [],
            backup=(article.get("_update_backup") or {}).get("path", ""),
            change_summary=(article.get("_freshness") or {}).get("reason", ""),
        )
    except Exception:  # noqa: BLE001 — update succeeded; ledger warning only
        log.exception("correction ledger write failed (post already updated)")
    log.info("POST UPDATED ✔ id=%s link=%s", post_id, result.get("link"))
    if meta:
        try:
            required_seo = [k for k in meta if k.startswith("rank_math_")]
            # The underlying verify_meta read remains part of the compatibility
            # path; verify_rankmath_meta supplements it with bridge readback.
            landed = wp.verify_rankmath_meta(post_id, required_seo)
            missing = [k for k, ok in landed.items() if not ok]
            if missing and not mock:
                wp.write_seo_meta(post_id, meta)
                landed = wp.verify_rankmath_meta(post_id, required_seo)
                missing = [k for k, ok in landed.items() if not ok]
            article["_rankmath_landed"] = dict(landed)
            result["seo_meta_persisted"] = not missing
            result["seo_meta_keys"] = required_seo
            if missing:
                log.warning("UPDATE %s: Rank Math meta missing %s", post_id, missing)
        except Exception:
            log.exception("update meta verify skip (safe)")
    article["source_url"] = None
    try:
        state.record_refresh(config.STATE_PATH, post_id)
    except Exception as exc:  # noqa: BLE001 — best-effort (silent kaadu)
        log.debug("update_post skip: %s", exc)
    try:
        from . import indexnow

        indexnow.submit(result.get("link", ""))
    except Exception as exc:  # noqa: BLE001 — best-effort (silent kaadu)
        log.debug("update_post skip: %s", exc)
    try:
        notifier.notify_updated_post(article, result)
    except Exception:
        log.exception("Update notification failed (post update safe)")
    return result


# ------------------------------------------------------------------ listicles

def create_listicle(topic: str = "", mock: bool = False) -> Dict:
    """Trending listicle post (Top 10 jobs lanti 'stories')."""
    from . import topic_engine

    idea = topic or topic_engine.pick_listicle_idea(
        state.recent_titles(config.STATE_PATH, limit=30))
    log.info("Listicle idea: %s", idea)

    if mock:
        article = topic_engine.mock_listicle(idea,
                                             state.today_count(config.STATE_PATH, date.today()))
    else:
        if not config.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY ledu — listicle generate avvaledu")
        recent = state.recent_titles(config.STATE_PATH, limit=30)
        article = gemini_client.generate_listicle(idea, recent, date.today().year)

    from .main import _safe_slug
    article["slug"] = seo.optimize_slug(
        _safe_slug(article.get("slug", ""), article["title"]),
        focus_keyword=article.get("focus_keyword", "") or idea)
    for k, v in (("focus_keyword", idea), ("external_links", []),
                 ("secondary_keywords", []), ("quick_answer", ""),
                 ("faq", []), ("seo_title", ""), ("list_items", None)):
        article.setdefault(k, v)
    return publish_article(article)


# ------------------------------------------------------------------ daily quiz

def create_quiz(topic: str = "", level: int = 0, questions: int = 0,
                mock: bool = False, dry_run: bool = False) -> Dict:
    """v26: Daily Quiz post — exam-style interactive MCQ quiz.

    topic empty aithe roju automatic rotation (Mon GK ... Sun Mega Mock).
    Telugu lo topic ichhina work avutundi (Gemini bilingual prompt).
    """
    from . import quiz_engine

    now_day = date.today()
    if topic:
        # manual topic (Telugu ok) — level default 2, questions default
        topic_en = topic.strip()
        topic_te = topic.strip()
        # v87: manual level clamp (9 isthe LEVEL_NAMES KeyError crash!)
        lvl = max(1, min(4, level)) if level else 2
        # v87: questions clamp (500 adigithe LLM output truncate + cost!)
        n = max(1, min(30, questions)) if questions else config.QUIZ_QUESTIONS
    else:
        topic_en, topic_te, lvl, n = quiz_engine.pick_daily_topic(now_day)
        if questions:
            n = max(1, min(30, questions))
        if level:
            lvl = max(1, min(4, level))

    log.info("Quiz mode: '%s' (%s) — L%d, %d questions%s",
             topic_en, topic_te, lvl, n, " [MOCK]" if mock else "")
    # v87: duplicate guard GENERATE MUNDU (LLM call waste kakunda) —
    # title ki quiz object avasaram ledu (topic/lvl matrame).
    _dstr = now_day.strftime("%d %B %Y")
    _qtitle = (f"Daily Quiz – {_dstr} | {topic_en} Telugu "
               f"({quiz_engine.LEVEL_NAMES[lvl]})") if not topic else \
        f"Quiz: {topic_en} Telugu ({quiz_engine.LEVEL_NAMES[lvl]})"
    if state.title_exists(config.STATE_PATH, _qtitle):
        raise ValueError(f"Quiz already generated today: {_qtitle}")
    if mock:
        quiz = quiz_engine.mock_quiz(topic_en, topic_te, lvl, n, now_day)
    else:
        if not (config.GEMINI_API_KEY or getattr(config, "GEMINI_API_KEYS", [])):
            raise ValueError("GEMINI_API_KEY ledu — quiz generate avvaledu")
        recent = state.recent_titles(config.STATE_PATH, limit=20)
        quiz = gemini_client.generate_quiz(topic_en, topic_te, lvl, n,
                                           now_day.year)
        _ = recent  # future: question-level dedupe against old quizzes

    content_html, uid = quiz_engine.build_quiz_html(quiz, topic_en, topic_te,
                                                    lvl, n, now_day)
    dstr, title = _dstr, _qtitle  # v87: pre-computed (guard generate mundu)
    focus = "daily quiz telugu" if not topic else topic_en.lower()
    article = {
        "title": title,
        "seo_title": title,
        "slug": "",  # filled below
        "category": config.QUIZ_CATEGORY,
        "tags": ["Daily Quiz", "GK Quiz Telugu", topic_en, "Current Affairs Quiz",
                 str(now_day.year)][:8],
        "meta_description": (
            f"{dstr} Daily Quiz Telugu lo — {topic_en} మీద {n} exam-style "
            f"questions, timer + negative marking + explanations. "
            f"ఆడండి, నేర్చుకోండి! (studentup.in free quiz)"),
        "focus_keyword": focus,
        "secondary_keywords": [topic_en, "quiz telugu", "gk telugu"],
        "quick_answer": (f"ఈరోజు క్విజ్: {topic_en} — {n} questions, "
                         f"Level {lvl}. Start Quiz నొక్కి వెంటనే మొదలుపెట్టండి."),
        "banner_text": f"DAILY QUIZ\n{topic_en}\nLevel {lvl} • {quiz_engine.LEVEL_NAMES[lvl]}",
        "faq": [],
        "external_links": [],
        "article_type": "quiz",
        "content_html": content_html,
        "_quiz": quiz,
        "_quiz_level": lvl,
        "_mock": mock,
    }
    from .main import _safe_slug
    article["slug"] = seo.optimize_slug(
        _safe_slug("", article["title"]), focus_keyword=focus)
    log.info("Quiz ready: %s (uid=%s, %d questions)", title, uid,
             len(quiz["questions"]))
    if dry_run:
        out_dir = config.OUTPUT_DIR / "quiz-dry"
        out_dir.mkdir(parents=True, exist_ok=True)
        final = article["content_html"]
        fp = out_dir / f"{article['slug']}.html"
        fp.write_text(
            "<!doctype html><html><head><meta charset='utf-8'>"
            f"<title>{article['title']}</title></head><body>"
            f"<h1>{article['title']}</h1>{final}</body></html>",
            encoding="utf-8")
        log.info("QUIZ DRY-RUN saved to %s (state lo record cheyaledu)", fp)
        return {"id": 0, "status": "dry-run", "link": str(fp)}
    return publish_article(article)


# ------------------------------------------------------------------ auto refresh

def auto_refresh(limit: int = 1, older_days: int = None) -> list:
    """Purana published posts ni kotha research tho refresh (daily maintenance).

    Google freshness signal — rankings long-term lo stable.
    """
    older = older_days if older_days is not None else config.AUTO_REFRESH_MIN_AGE_DAYS
    targets = state.posts_to_refresh(config.STATE_PATH, older_days=older, limit=limit)
    if not targets:
        log.info("Auto-refresh: eligible posts levu (min %d days old)", older)
        return []
    results = []
    for t in targets:
        try:
            log.info("Auto-refresh: post %s '%s'", t["wp_id"], t["title"][:50])
            results.append(update_post(t["wp_id"]))
        except Exception:
            log.exception("Auto-refresh fail: post %s", t["wp_id"])
    # v87: owner summary (cron silent kakunda — updates jarigayo ledo teliyali)
    try:
        if results and config.TELEGRAM_BOT_TOKEN and config.TELEGRAM_CHAT_ID:
            from .notifier import esc as _esc, send_telegram as _tg
            lines = [f"🔄 <b>Auto-refresh: {len(results)} post(s)</b>"]
            for r in results[:5]:
                if isinstance(r, dict) and not r.get("error"):
                    lines.append(f"✔ {_esc(r.get('link', ''))}")
            _tg("\n".join(lines))
    except Exception:  # noqa: BLE001 — notify never breaks cron
        log.exception("auto-refresh summary skip (safe)")
    return results
