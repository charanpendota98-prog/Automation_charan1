# -*- coding: utf-8 -*-
"""Reader-first language and anti-filler audit.

SEO checks must never turn an article into repetitive keyword padding.  This
module performs conservative terminology cleanup and measures duplicated or
empty prose.  It does not invent facts and it never rewrites numbers/dates.
"""
from __future__ import annotations

import re
from typing import Dict, List, Tuple

from . import validator

# Common education/job terms readers normally see in English. Longest first.
TERM_MAP = (
    ("అప్లికేషన్ ఫీజు", "Application Fee"),
    ("దరఖాస్తు ఫీజు", "Application Fee"),
    ("ఎంపిక ప్రక్రియ", "Selection Process"),
    ("సెలక్షన్ ప్రాసెస్", "Selection Process"),
    ("అధికారిక వెబ్‌సైట్", "Official Website"),
    ("ఆఫీషియల్ వెబ్‌సైట్", "Official Website"),
    ("ముఖ్యమైన తేదీలు", "Important Dates"),
    ("వయోపరిమితి", "Age Limit"),
    ("హాల్ టికెట్", "Hall Ticket"),
    ("డైరెక్ట్ లింక్", "Direct Link"),
    ("ఎలిజిబిలిటీ", "Eligibility"),
    ("నోటిఫికేషన్", "Notification"),
    ("వేకెన్సీలు", "Vacancies"),
    ("వేకెన్సీ", "Vacancy"),
)

# Empty promotional sentences which add no answer or action. The audit only
# blocks repeated use; one natural occurrence remains acceptable.
FILLER_PATTERNS = (
    r"చివరి వరకు (?:చదవండి|చూడండి)",
    r"పూర్తి వివరాలు తెలుసుకుందాం",
    r"ఈ విషయం చాలా ముఖ్యమైనది",
    r"ప్రతి ఒక్కరూ తెలుసుకోవాలి",
    r"మీకు చాలా ఉపయోగపడుతుంది",
    r"మరింత సమాచారం కోసం ఈ కథనాన్ని చదవండి",
    r"ఈ పోస్ట్‌లో పూర్తిగా ఇచ్చాము",
    r"కింది విభాగాల్లో ఒక్కొక్కటిగా ఇచ్చాము",
    r"ఈ (?:article|post|కథనం) మీకు నచ్చితే (?:share|షేర్)",
    r"మీ friends(?:తో|కి)? (?:share|షేర్) చేయండి",
    r"మీ doubts (?:comments|కామెంట్స్)లో",
    r"ఇలాంటి updates కోసం (?:follow|subscribe)",
    r"కష్టపడితే విజయం తప్పకుండా",
    r"మీ కలలను సాకారం చేసుకోండి",
    r"ప్రతిష్టాత్మకమైన",
    r"సువర్ణావకాశం",
    r"గొప్ప కెరీర్ అవకాశం",
    r"సమగ్రంగా వివరిస్తుంది",
    r"జాగ్రత్తగా పరిశీలించి",
    r"చివరి నిమిషం రద్దీని నివారించ",
    r"ఈ (?:notification|నోటిఫికేషన్) లాంటి updates",
)


def _replace_visible_text(html: str, protected: str = "") -> str:
    """Replace terminology only outside HTML tags/scripts/styles.

    A Telugu-script phrase used as the exact focus keyword is protected so the
    cleanup cannot accidentally break Rank Math keyword placement.
    """
    chunks = re.split(r"(<[^>]+>)", html or "")
    in_script = False
    out: List[str] = []
    for chunk in chunks:
        if chunk.startswith("<"):
            tag = chunk.lower()
            if tag.startswith("<script") or tag.startswith("<style"):
                in_script = True
            out.append(chunk)
            if tag.startswith("</script") or tag.startswith("</style"):
                in_script = False
            continue
        if not in_script:
            for old, new in TERM_MAP:
                if old not in (protected or ""):
                    chunk = chunk.replace(old, new)
        out.append(chunk)
    return "".join(out)


def _norm(sentence: str) -> str:
    sentence = re.sub(r"[^\w\u0c00-\u0c7f ]+", " ", sentence.lower())
    return re.sub(r"\s+", " ", sentence).strip()


def audit(html: str) -> Dict:
    plain = re.sub(r"\s+", " ", validator.strip_tags(html or "")).strip()
    sentences = [_norm(x) for x in re.split(r"(?<=[.!?\u0964])\s+", plain)]
    sentences = [x for x in sentences if len(x.split()) >= 6]
    seen, duplicates = set(), []
    for sentence in sentences:
        if sentence in seen:
            duplicates.append(sentence[:140])
        seen.add(sentence)

    paras = [_norm(validator.strip_tags(x)) for x in
             re.findall(r"<p[^>]*>(.*?)</p>", html or "", re.S | re.I)]
    para_seen, duplicate_paras = set(), []
    for para in (p for p in paras if len(p.split()) >= 12):
        if para in para_seen:
            duplicate_paras.append(para[:140])
        para_seen.add(para)

    filler = []
    for pattern in FILLER_PATTERNS:
        count = len(re.findall(pattern, plain, re.I))
        if count:
            filler.append({"phrase": pattern, "count": count})
    filler_hits = sum(x["count"] for x in filler)
    duplicate_ratio = len(duplicates) / max(1, len(sentences))
    english_labels = sum(plain.lower().count(term.lower()) for term in (
        "notification", "eligibility", "age limit", "application fee",
        "important dates", "selection process", "apply online",
        "official website", "vacancy", "salary", "documents", "direct link",
    ))

    flags: List[str] = []
    if duplicate_paras:
        flags.append(f"DUPLICATE-PARAGRAPHS {len(duplicate_paras)}")
    if duplicate_ratio > 0.08:
        flags.append(f"REPEATED-SENTENCES {duplicate_ratio:.0%}")
    if filler_hits:
        flags.append(f"FILLER-PHRASES {filler_hits}")

    score = 100
    score -= min(35, len(duplicate_paras) * 15)
    score -= min(30, round(duplicate_ratio * 100))
    score -= min(30, filler_hits * 10)
    if english_labels < 4:
        score -= 10
    score = max(0, score)
    return {
        "score": score,
        "flags": flags,
        "sentences": len(sentences),
        "duplicate_sentences": duplicates[:10],
        "duplicate_paragraphs": duplicate_paras[:10],
        "filler": filler,
        "filler_hits": filler_hits,
        "english_labels": english_labels,
    }


def polish_and_audit(html: str, focus_keyword: str = "") -> Tuple[str, Dict]:
    polished = _replace_visible_text(html, protected=focus_keyword)
    return polished, audit(polished)
