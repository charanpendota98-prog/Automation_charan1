"""v26 — Daily Quiz Engine: exam-style interactive quizzes on studentup.in.

Two parts:
1) SERVER-SIDE (this file): Gemini generates bilingual (Telugu+English)
   question sets -> we build a safe HTML quiz block + SEO answer key +
   Quiz JSON-LD -> published as a normal WP post (category "Daily Quiz").
2) SITE-WIDE (widget): the interactive exam UI (timer, question palette,
   negative marking, streaks, explanations, WhatsApp share) ships as ONE
   <style>+<script> text-widget — installed like design_kit, idempotent.
   Post content only carries `<div class="su-quiz" data-quiz='...'>`, so it
   survives even if WP kses filters post HTML.

Difficulty ramp (auto mode): Mon L1 Basics -> Tue L2 -> Wed L3 -> Thu L2 ->
Fri L3 -> Sat L4 -> Sun L4 (20Q Weekly Mega Mock). User can pin QUIZ_LEVEL=1-4.
"""
from __future__ import annotations

import hashlib
import html
import json
import logging
import re
from datetime import date, timedelta
from typing import Dict, List, Optional, Tuple

log = logging.getLogger("autoblog.quiz")

MARKER = "suquiz26"            # widget marker (design-kit style)
QUIZ_START = "<!--suq:start-->"
QUIZ_END = "<!--suq:end-->"

LEVEL_NAMES = {
    1: "Basics",
    2: "Intermediate",
    3: "Advanced",
    4: "Top Level",
}
LEVEL_NAMES_TE = {
    1: "బేసిక్స్",
    2: "ఇంటర్మీడియట్",
    3: "అడ్వాన్స్‌డ్",
    4: "టాప్ లెవల్",
}

# Weekly rotation: (english topic, telugu label, level). Sun = mega mock.
QUIZ_WEEK = [
    ("Current Affairs & GK", "కరెంట్ అఫైర్స్ & జనరల్ నాలెడ్జ్", 1),   # Mon
    ("Scholarships & Education Schemes", "స్కాలర్‌షిప్‌లు & పథకాలు", 2),  # Tue
    ("Govt Exam Prep: Maths & Reasoning", "మ్యాథ్స్ & రీజనింగ్", 3),  # Wed
    ("AP & Telangana State GK", "ఆంధ్రప్రదేశ్ & తెలంగాణ జనరల్ నాలెడ్జ్", 2),  # Thu
    ("Banking Awareness & English Vocabulary", "బ్యాంకింగ్ & ఇంగ్లీష్ వొకాబ్యులరీ", 3),  # Fri
    ("Science & Technology GK", "సైన్స్ & టెక్నాలజీ", 4),            # Sat
    ("Weekly Mega Mock: Full GK", "వీక్లీ మెగా మాక్: ఫుల్ జీకే", 4),   # Sun
]


def pick_daily_topic(day: Optional[date] = None) -> Tuple[str, str, int, int]:
    """(topic_en, topic_te, level, n_questions) for the given day."""
    from . import config

    day = day or date.today()
    topic_en, topic_te, level = QUIZ_WEEK[day.weekday()]
    lvl = getattr(config, "QUIZ_LEVEL", "auto")
    if str(lvl).strip() not in ("", "auto"):
        try:
            level = max(1, min(4, int(lvl)))
        except ValueError:
            pass
    n = config.QUIZ_SUNDAY_QUESTIONS if day.weekday() == 6 else config.QUIZ_QUESTIONS
    return topic_en, topic_te, level, n


# ------------------------------------------------------------------ validation

def validate_quiz(quiz: Dict, expected_n: int) -> List[str]:
    """Returns list of problems (empty = valid). Gemini JSON quality gate."""
    problems: List[str] = []
    qs = quiz.get("questions") or []
    if not isinstance(qs, list):
        return ["questions is not a list"]
    if len(qs) < max(5, expected_n - 1):
        problems.append(f"only {len(qs)} questions (need {expected_n})")
    seen: List[set] = []
    for i, q in enumerate(qs[:expected_n]):
        if not isinstance(q, dict):
            problems.append(f"q{i}: not an object")
            continue
        text = str(q.get("q") or "").strip()
        if len(text) < 8:
            problems.append(f"q{i}: question text missing")
        opts = q.get("options") or []
        if not isinstance(opts, list) or len(opts) != 4 or \
                any(not str(o).strip() for o in opts):
            problems.append(f"q{i}: needs exactly 4 non-empty options")
        a = q.get("a")
        if not isinstance(a, int) or not 0 <= a <= 3:
            problems.append(f"q{i}: answer index a must be 0-3")
        if len(str(q.get("x") or "").strip()) < 10:
            problems.append(f"q{i}: explanation (x) too short")
        toks = frozenset(re.findall(r"[a-z0-9ఀ-౿]{3,}", text.lower()))
        for prev in seen:
            union = toks | prev
            if union and len(toks & prev) / len(union) > 0.7:
                problems.append(f"q{i}: duplicate of an earlier question")
        seen.append(toks)
    return problems


def normalize_quiz(quiz: Dict, n: int) -> Dict:
    """Trim to n questions + escape-safe strings (call AFTER validate)."""
    qs = []
    for q in (quiz.get("questions") or [])[:n]:
        qs.append({
            "q": str(q.get("q", "")).strip(),
            "qt": str(q.get("qt") or "").strip(),          # Telugu script line
            "options": [str(o).strip() for o in q["options"]],
            "a": int(q["a"]),
            "x": str(q.get("x", "")).strip(),
        })
    return {
        "topic": str(quiz.get("topic") or "").strip(),
        "topic_te": str(quiz.get("topic_te") or "").strip(),
        "questions": qs,
    }


# ------------------------------------------------------------------ mock mode

MOCK_BANK = [
    ("Which scheme provides scholarship to minority community students?",
     "మైనారిటీ విద్యార్థులకు స్కాలర్‌షిప్ ఇచ్చే పథకం ఏది?",
     ["Pre-Matric Scholarship", "PM Kisan", "MGNREGA", "Ayushman Bharat"], 0,
     "Pre-Matric Scholarship minority students ki class 1-10 fees + stipend istundi. Apply: scholarships.gov.in"),
    ("SSC CGL exam is conducted for recruitment to which type of posts?",
     "SSC CGL పరీక్ష దేనికి నిర్వహిస్తారు?",
     ["Group B & C posts in Central Ministries", "State police", "Army officer",
      "Teaching posts"], 0,
     "SSC CGL through Central Government ministries lo Group B & C posts bharti jarugutundi."),
    ("What is the minimum age to apply for most government bank jobs?",
     "చాలా బ్యాంక్ ఉద్యోగాలకు కనీస వయసు ఎంత?",
     ["20 years", "21 years", "18 years", "25 years"], 1,
     "IBPS/SBI notifications lo general category ki minimum age 20-21 years untundi (post batti)."),
    ("Which is the largest bank in India by branches?",
     "భారతదేశంలో అతిపెద్ద బ్యాంక్ ఏది?",
     ["State Bank of India", "HDFC Bank", "Punjab National Bank", "ICICI Bank"], 0,
     "SBI ki 22,000+ branches unnayi — India lo no.1 public sector bank."),
    ("'Article 46' of Indian Constitution deals with?",
     "భారత రాజ్యాంగంలోని ఆర్టికల్ 46 దేని గురించి?",
     ["Educational & economic interests of SC/ST", "Right to property",
      "Election commission", "Emergency powers"], 0,
     "Article 46 SC/ST & weaker sections educational, economic interests ni protect cheyali ani cheptundi."),
    ("Telangana state was formed in which year?",
     "తెలంగాణ రాష్ట్రం ఏ సంవత్సరంలో ఏర్పడింది?",
     ["2014", "2000", "2010", "2016"], 0,
     "2 June 2014 na Telangana India lo 29th state ga aavirbhavinchindi."),
    ("What does 'GDP' stand for?",
     "GDP అంటే ఏమిటి?",
     ["Gross Domestic Product", "General Development Plan", "Gross Demand Price",
      "Government Data Portal"], 0,
     "GDP = Gross Domestic Product — oka desa lo untpatti motham value."),
    ("National Scholarship Portal website is?",
     "నేషనల్ స్కాలర్‌షిప్ పోర్టల్ వెబ్‌సైట్ ఏది?",
     ["scholarships.gov.in", "naukri.com", "digilocker.gov.in", "nsp.com"], 0,
     "Central/state scholarships anni scholarships.gov.in (NSP) lo apply cheyali."),
    ("Which exam is conducted for IBPS Clerk recruitment?",
     "IBPS క్లర్క్ నియామకానికి ఏ పరీక్ష?",
     ["IBPS CWE Clerk", "NEET", "GATE", "TET"], 0,
     "IBPS Clerk recruitment ki IBPS CWE Clerk (Prelims + Mains) jarugutundi."),
    ("Photosynthesis in plants produces which gas?",
     "కిరణజన్య సంయోగక్రియలో ఏ వాయువు విడుదలవుతుంది?",
     ["Oxygen", "Carbon dioxide", "Nitrogen", "Hydrogen"], 0,
     "Plants sunlight tho CO2 + water ni glucose ga marchutu oxygen release chestayi."),
    ("AP state capital (administrative) is?",
     "ఆంధ్రప్రదేశ్ రాజధాని ఏది?",
     ["Amaravati", "Visakhapatnam", "Kurnool", "Vijayawada"], 0,
     "AP ki Amaravati administrative capital (Visakhapatnam executive capital ga develop avutondi)."),
    ("'Repo Rate' is decided by which institution?",
     "రెపో రేటు ఏ సంస్థ నిర్ణయిస్తుంది?",
     ["Reserve Bank of India", "SEBI", "NITI Aayog", "Finance Ministry"], 0,
     "RBI Monetary Policy Committee repo rate ni decide chestundi — loans interest meeda effect."),
    ("How many fundamental duties are in the Indian Constitution?",
     "భారత రాజ్యాంగంలో ప్రాథమిక విధులు ఎన్ని?",
     ["11", "9", "12", "7"], 0,
     "Article 51A lo 11 Fundamental Duties unnayi (86th amendment tho education duty add ayyindi)."),
    ("Digital India mission was launched in which year?",
     "డిజిటల్ ఇండియా ఏ సంవత్సరంలో ప్రారంభమైంది?",
     ["2015", "2014", "2016", "2018"], 0,
     "July 2015 lo Digital India launch ayyindi — e-governance, broadband villages ki."),
    ("Which subject does 'Quantitative Aptitude' in bank exams test?",
     "బ్యాంక్ పరీక్షల్లో 'క్వాంటిటేటివ్ ఆప్టిట్యూడ్' అంటే?",
     ["Numerical/Maths ability", "English grammar", "General knowledge",
      "Computer skills"], 0,
     "QA section lo percentages, ratios, series, DI lanti maths topics test avutayi."),
    ("PM-YASASVI scholarship is for which students?",
     "PM-YASASVI స్కాలర్‌షిప్ ఎవరి కోసం?",
     ["OBC/SC/ST students (class 9 & 11)", "Only engineering students",
      "Foreign students", "Only girls"], 0,
     "PM YASASVI: OBC/SC/ST/DNT students ki class 9 & 11 ki scholarships (NSP dwara)."),
    ("'HTTP' used in websites stands for?",
     "వెబ్‌సైట్లలో వాడే HTTP అంటే?",
     ["HyperText Transfer Protocol", "High Tech Transfer Process",
      "HyperTool Text Program", "Home Text Transfer Page"], 0,
     "HTTP browser ki server ki pages transfer cheye protocol (HTTPS = secure)."),
    ("TSPSC conducts recruitment for which state?",
     "TSPSC ఏ రాష్ట్ర నియామకాలను నిర్వహిస్తుంది?",
     ["Telangana", "Andhra Pradesh", "Karnataka", "Tamil Nadu"], 0,
     "Telangana State Public Service Commission — Group 1/2/3/4 posts ki exams."),
    ("Simple interest on Rs.1000 at 10% for 2 years is?",
     "రూ.1000 కి 10% వడ్డీతో 2 సంవత్సరాలకు సాధారణ వడ్డీ ఎంత?",
     ["Rs.200", "Rs.100", "Rs.210", "Rs.150"], 0,
     "SI = P×T×R/100 = 1000×2×10/100 = ₹200."),
    ("Which portal issues 'Ayushman Bharat' health cards?",
     "ఆయుష్మాన్ భారత్ కార్డులు ఏ పోర్టల్ ద్వారా వస్తాయి?",
     ["pmjay.gov.in", "passportindia.gov.in", "scholarships.gov.in", "irdai.gov.in"], 0,
     "PM-JAY (Ayushman Bharat) ki pmjay.gov.in — ₹5 lakh health cover per family."),
]


def mock_quiz(topic_en: str, topic_te: str, level: int, n: int,
              day: Optional[date] = None) -> Dict:
    """Deterministic offline quiz (--mock / tests kosam; no Gemini needed)."""
    day = day or date.today()
    seed = int(hashlib.md5(f"{day.isoformat()}{topic_en}".encode()).hexdigest(), 16)
    picks = []
    for i in range(min(n, len(MOCK_BANK))):
        picks.append(MOCK_BANK[(seed + i * 7) % len(MOCK_BANK)])
    qs = []
    for i, (q, qt, opts, a, x) in enumerate(picks):
        rot = (seed + i) % 4                      # options shuffle (deterministic)
        new_opts = opts[rot:] + opts[:rot]
        qs.append({"q": q, "qt": qt, "options": new_opts,
                   "a": new_opts.index(opts[a]), "x": x})
    return {"topic": topic_en, "topic_te": topic_te, "questions": qs}


# ------------------------------------------------------------------ HTML build

def build_quiz_block(quiz: Dict, level: int, n: int, uid: str) -> str:
    """`<div class="su-quiz" data-quiz='...'>` — engine JS (widget) renders it.

    Static fallback content inside (no-JS / SEO crawlers) = answer key link.
    All text is escaped; JSON lives in a double-quoted attribute."""
    from . import config

    payload = {
        "id": uid,
        "topic": quiz["topic"],
        "topic_te": quiz.get("topic_te", ""),
        "level": level,
        "levelName": LEVEL_NAMES.get(level, "Quiz"),
        "language": config.QUIZ_LANGUAGE,
        "settings": {
            "time_per_q": config.QUIZ_TIME_PER_Q,
            "negative": config.QUIZ_NEGATIVE_MARK,
            "marks_correct": 1,
            "marks_wrong": 0.25 if config.QUIZ_NEGATIVE_MARK else 0,
        },
        "questions": quiz["questions"][:n],
    }
    data = html.escape(json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
                       quote=True)
    return (f'<div class="su-quiz" id="suq-{uid}" data-quiz="{data}">'
            f'<p><strong>క్విజ్ లోడ్ కాలేదు?</strong> పేజీ రిఫ్రెష్ చేయండి — '
            f'జావాస్క్రిప్ట్ ఆన్ చేసి ఉండాలి. సమాధానాలు కింద '
            f'<em>Answer Key</em> లో ఉన్నాయి.</p></div>')


def build_intro_html(topic_en: str, topic_te: str, level: int, n: int,
                     day: date) -> str:
    """Quiz info table + motivating intro (allowed tags only)."""
    from . import config

    total_min = max(1, (config.QUIZ_TIME_PER_Q * n) // 60)
    marking = "+1, −0.25" if config.QUIZ_NEGATIVE_MARK else "+1, no negative"
    dstr = day.strftime("%d %B %Y")
    return (
        f"<p><strong>Daily Quiz ({dstr})</strong> — ఈరోజు <em>{topic_te}</em> "
        f"({topic_en}) మీద {n} ప్రశ్నల ఎగ్జామ్-స్టైల్ క్విజ్. ప్రతి ప్రశ్నకూ "
        f"వివరణ (explanation) ఉంటుంది — చదువుతూనే పరీక్ష ప్రాక్టీస్ అవుతుంది.</p>"
        f"<p>ఈ క్విజ్ {LEVEL_NAMES_TE[level]} ({LEVEL_NAMES[level]}) లెవెల్‌లో "
        f"ఉంటుంది. టైమర్, నెగటివ్ మార్కింగ్, ఆన్సర్ పాలెట్ — అసలు పరీక్ష "
        f"అనుభవం ఇంట్లోనే. స్కోరు చివరలో వివరంగా కనిపిస్తుంది.</p>"
        f"<table><thead><tr><th>Quiz Details</th><th>వివరాలు</th></tr></thead>"
        f"<tbody>"
        f"<tr><td>Topic / విషయం</td><td>{topic_en} ({topic_te})</td></tr>"
        f"<tr><td>Questions / ప్రశ్నలు</td><td>{n}</td></tr>"
        f"<tr><td>Level / స్థాయి</td><td>L{level} — {LEVEL_NAMES[level]}</td></tr>"
        f"<tr><td>Time / సమయం</td><td>~{total_min} minutes "
        f"({config.QUIZ_TIME_PER_Q} sec/question)</td></tr>"
        f"<tr><td>Marking / మార్కులు</td><td>{marking}</td></tr>"
        f"</tbody></table>"
        f"<p>👇 కింద <strong>Start Quiz</strong> నొక్కండి — మొదలుపెడదాం!</p>"
    )


def build_answer_key_html(quiz: Dict) -> str:
    """SEO + no-JS fallback: static answer key with explanations."""
    items = []
    for i, q in enumerate(quiz["questions"], 1):
        qt = f" <em>({html.escape(q['qt'])})</em>" if q.get("qt") else ""
        items.append(
            f"<li><strong>Q{i}:</strong>{qt} "
            f"<strong>Answer: {html.escape(q['options'][q['a']])}</strong> — "
            f"{html.escape(q['x'])}</li>")
    return ("<h2>📋 Answer Key & Explanations (సమాధానాలు)</h2>"
            "<ol>" + "".join(items) + "</ol>")


def build_quiz_html(quiz: Dict, topic_en: str, topic_te: str, level: int,
                    n: int, day: date) -> Tuple[str, str]:
    """Returns (content_html with markers, uid)."""
    uid = hashlib.md5(f"{day.isoformat()}{topic_en}".encode()).hexdigest()[:10]
    block = build_quiz_block(quiz, level, n, uid)
    content = (build_intro_html(topic_en, topic_te, level, n, day)
               + QUIZ_START + block + QUIZ_END
               + build_answer_key_html(quiz))
    return content, uid


def sanitize_quiz_content(content_html: str) -> str:
    """Sanitize everything EXCEPT the trusted quiz block we build ourselves."""
    from . import validator

    parts = re.split(r"(" + re.escape(QUIZ_START) + r".*?" + re.escape(QUIZ_END) + r")",
                     content_html, flags=re.S)
    out = []
    for i, part in enumerate(parts):
        if i % 2 == 1:
            out.append(part)                    # our block — already escaped
        else:
            out.append(validator.sanitize_html(part))
    return "".join(out)


def _quiz_jsonld(article: Dict) -> str:
    """schema.org Quiz (rich results + educational search)."""
    quiz = article.get("_quiz") or {}
    parts = []
    for q in quiz.get("questions", []):
        parts.append({
            "@type": "Question",
            "name": q.get("q", ""),
            "acceptedAnswer": {"@type": "Answer",
                               "text": q["options"][q["a"]] if q.get("options") else ""},
        })
    data = {
        "@context": "https://schema.org",
        "@type": "Quiz",
        "name": article.get("title", "Daily Quiz"),
        "description": article.get("meta_description", ""),
        "inLanguage": ["te", "en"],
        "educationalLevel": LEVEL_NAMES.get(article.get("_quiz_level", 1), ""),
        "hasPart": parts,
    }
    return ('<script type="application/ld+json">'
            + json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
            + "</script>")


def finalize_html(article: Dict, internal_links: Optional[List[Dict]] = None,
                  site_url: str = "") -> str:
    """Full quiz post HTML: content + share bar + related + Quiz JSON-LD."""
    pieces = [article.get("content_html", "")]
    # share bar (JS-free links; wa.me works without API keys)
    link = article.get("_link") or site_url
    share_txt = html.escape(f"నేను ఈరోజు Daily Quiz ఆడాను! 🎯 మీరూ ట్రై చేయండి: {link}")
    pieces.append(
        '<p class="suq-share" style="text-align:center">'
        f'<a href="https://wa.me/?text={html.escape(share_txt, quote=True)}" '
        'target="_blank" rel="noopener nofollow">📲 WhatsApp లో షేర్ చేయండి</a>'
        "</p>")
    if internal_links:
        lis = "".join(
            f'<li><a href="{html.escape(p.get("link", "#"), quote=True)}">'
            f"{html.escape(p.get('title', ''))}</a></li>"
            for p in internal_links[:4] if p.get("link"))
        if lis:
            pieces.append("<h2>📚 ఇవి కూడా చదవండి (Related Articles)</h2>"
                          "<ul>" + lis + "</ul>")
    pieces.append(_quiz_jsonld(article))
    return "\n".join(pieces)


# ------------------------------------------------------------------ widget kit
# Site-wide quiz CSS + exam engine JS, installed as ONE footer text widget
# (same proven mechanism as design_kit — raw HTML survives, applies to every
# quiz post, idempotent by marker).

QUIZ_CSS = """
.su-quiz{--suq-navy:var(--su-navy,#12356B);--suq-acc:var(--su-accent,#E8842B);--suq-ok:#1d8a4e;--suq-bad:#c9354a;font-family:'Inter','Noto Sans Telugu',system-ui,sans-serif;max-width:820px;margin:26px auto;border:1px solid #E4E9F1;border-radius:18px;background:#fff;overflow:hidden;box-shadow:0 8px 30px rgba(18,53,107,.08)}
.suq-head{background:var(--suq-navy);color:#fff;padding:14px 18px;display:flex;justify-content:space-between;align-items:center;gap:10px;flex-wrap:wrap}
.suq-head b{font-size:15px;letter-spacing:.02em}
.suq-chips{display:flex;gap:6px;flex-wrap:wrap}
.suq-chip{background:rgba(255,255,255,.14);border:1px solid rgba(255,255,255,.25);color:#fff;font-size:12px;padding:3px 10px;border-radius:999px;white-space:nowrap}
.suq-body{padding:18px}
.suq-timer{display:flex;align-items:center;gap:10px;margin-bottom:12px;font-weight:700;color:var(--suq-navy)}
.suq-tbar{flex:1;height:8px;background:#EDF1F6;border-radius:99px;overflow:hidden}
.suq-tbar i{display:block;height:100%;background:var(--suq-acc);width:100%;transition:width .9s linear}
.suq-qnum{font-size:13px;color:#5A6472;font-weight:700;margin:2px 0 6px}
.suq-q{font-size:17px;font-weight:600;color:#22303F;line-height:1.6;margin:0 0 4px}
.suq-qte{font-size:15px;color:#5A6472;line-height:1.6;margin:0 0 14px}
.suq-opts{display:grid;gap:9px}
.suq-opt{display:flex;align-items:center;gap:10px;width:100%;text-align:left;background:#F7F9FC;border:2px solid #E4E9F1;border-radius:12px;padding:11px 13px;font-size:15px;color:#22303F;cursor:pointer;transition:.15s;line-height:1.5}
.suq-opt:hover{border-color:var(--suq-navy);background:#fff}
.suq-opt .suq-letter{min-width:28px;height:28px;border-radius:50%;background:var(--suq-navy);color:#fff;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:13px}
.suq-opt.sel{border-color:var(--suq-acc);background:#FFF7EE}
.suq-opt.right{border-color:var(--suq-ok);background:#EFFAF3}
.suq-opt.right .suq-letter{background:var(--suq-ok)}
.suq-opt.wrong{border-color:var(--suq-bad);background:#FDF0F2}
.suq-opt.wrong .suq-letter{background:var(--suq-bad)}
.suq-opt.locked{cursor:default;opacity:.92}
.suq-expl{margin-top:12px;background:#FAF7F2;border-left:4px solid var(--suq-acc);border-radius:0 10px 10px 0;padding:10px 14px;font-size:14px;line-height:1.65;color:#3d4653}
.suq-nav{display:flex;justify-content:space-between;gap:8px;margin-top:16px;flex-wrap:wrap}
.suq-btn{background:var(--suq-navy);color:#fff;border:0;border-radius:999px;padding:10px 20px;font-size:14px;font-weight:600;cursor:pointer}
.suq-btn:hover{background:var(--suq-acc)}
.suq-btn.alt{background:#fff;color:var(--suq-navy);border:2px solid var(--suq-navy)}
.suq-btn.warn{background:var(--suq-bad)}
.suq-btn:disabled{opacity:.45;cursor:not-allowed}
.suq-pal{display:grid;grid-template-columns:repeat(auto-fill,minmax(34px,1fr));gap:6px;margin-top:16px}
.suq-pal button{height:34px;border-radius:9px;border:1px solid #D6DEE9;background:#fff;font-weight:700;font-size:13px;color:#3d4653;cursor:pointer}
.suq-pal button.cur{outline:2px solid var(--suq-acc)}
.suq-pal button.ans{background:var(--suq-navy);color:#fff;border-color:var(--suq-navy)}
.suq-pal button.flg{background:var(--suq-acc);color:#fff;border-color:var(--suq-acc)}
.suq-start{text-align:center;padding:14px 6px}
.suq-start h3{color:var(--suq-navy);margin:6px 0;font-size:20px}
.suq-start .suq-streak{font-size:13px;color:#5A6472;margin:8px 0 14px}
.suq-modes{display:flex;gap:10px;justify-content:center;flex-wrap:wrap;margin-top:8px}
.suq-res{text-align:center;padding:10px 4px}
.suq-res .suq-score{font-size:42px;font-weight:800;color:var(--suq-navy);line-height:1.1}
.suq-res .suq-grade{font-size:18px;font-weight:700;margin:6px 0 2px}
.suq-res .suq-chips{justify-content:center;margin:10px 0}
.suq-res .suq-chip{background:#F1F5FA;border-color:#D6DEE9;color:#3d4653}
.suq-review{text-align:left;margin-top:18px;border-top:1px dashed #D6DEE9;padding-top:12px}
.suq-review h4{color:var(--suq-navy);margin:0 0 10px}
.suq-ritem{border:1px solid #E4E9F1;border-radius:12px;padding:11px 13px;margin-bottom:9px;font-size:14px;line-height:1.6}
.suq-ritem b.ok{color:var(--suq-ok)}.suq-ritem b.bad{color:var(--suq-bad)}
.suq-hide{display:none!important}
@media (max-width:640px){.suq-q{font-size:15.5px}.suq-opt{font-size:14px}.suq-body{padding:13px}}
"""

QUIZ_JS = r"""
(function(){
"use strict";
if(window.__SUQ)return;window.__SUQ=1;
function esc(s){return String(s==null?"":s).replace(/[&<>"]/g,function(c){return{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]});}
function mmss(t){t=Math.max(0,t);var m=Math.floor(t/60),s=t%60;return(m<10?"0":"")+m+":"+(s<10?"0":"")+s;}
function streakGet(){try{return JSON.parse(localStorage.getItem("suq_streak")||"{}")||{}}catch(e){return{}}}
function streakBump(){var d=new Date(),k=d.toISOString().slice(0,10);var st=streakGet();
 var y=new Date(d);y.setDate(d.getDate()-1);var yk=y.toISOString().slice(0,10);
 var n=(st.d===yk)?((st.n||0)+1):(st.d===k?(st.n||1):1);
 try{localStorage.setItem("suq_streak",JSON.stringify({d:k,n:n}))}catch(e){}
 return n;}
function init(root){
 if(root.__suqInit)return;root.__suqInit=1;
 var cfg;try{cfg=JSON.parse(root.getAttribute("data-quiz")||"{}")}catch(e){return}
 var qs=cfg.questions||[];if(!qs.length)return;
 var st=cfg.settings||{},per=st.time_per_q||0,neg=!!st.negative,mkw=st.marks_wrong||0,mkc=st.marks_correct||1;
 var ans=[],flags=[],idx=0,mode="",left=(per||60)*qs.length,tid=null,done=false;
 function reset(){ans=[];flags=[];idx=0;done=false;for(var i=0;i<qs.length;i++){ans.push(-1);flags.push(0)}}
 reset();
 function h(html){var d=document.createElement("div");d.innerHTML=html;return d.firstChild}
 root.innerHTML="";
 var head=h('<div class="suq-head"><b>🎯 '+(esc(cfg.topic||"Quiz"))+'</b><div class="suq-chips"></div></div>');
 var chips=head.querySelector(".suq-chips");
 chips.appendChild(h('<span class="suq-chip">'+qs.length+' Qs</span>'));
 chips.appendChild(h('<span class="suq-chip">L'+(cfg.level||1)+' '+(esc(cfg.levelName||""))+'</span>'));
 chips.appendChild(h('<span class="suq-chip">'+(neg?"+1 / −"+mkw:"+1 marks")+'</span>'));
 if(per)chips.appendChild(h('<span class="suq-chip">⏱ '+mmss(per*qs.length)+'</span>'));
 root.appendChild(head);
 var body=h('<div class="suq-body"></div>');root.appendChild(body);
 function streakLine(){var st2=streakGet();return st2.n?('🔥 Streak: '+st2.n+' day'+(st2.n>1?"s":"")):'🔥 రోజూ ఆడితే streak పెరుగుతుంది!';}
 function start(){
  body.innerHTML='<div class="suq-start"><h3>'+(esc(cfg.topic||"Daily Quiz"))+'</h3>'+
   '<p class="suq-qte">'+(esc(cfg.topic_te||""))+'</p>'+
   '<div class="suq-streak">'+streakLine()+'</div>'+
   '<p>'+qs.length+' ప్రశ్నలు • '+(neg?'నెగటివ్ మార్కింగ్ (−'+mkw+')':'నెగటివ్ మార్కింగ్ లేదు')+
   (per?' • '+per+' సెకన్లు/ప్రశ్న':'')+'</p>'+
   '<div class="suq-modes"><button class="suq-btn" data-m="exam">📝 Exam Mode</button>'+
   '<button class="suq-btn alt" data-m="practice">🎯 Practice Mode</button></div></div>';
  body.querySelectorAll("[data-m]").forEach(function(b){b.addEventListener("click",function(){begin(b.getAttribute("data-m"))})});
 }
 function begin(m){mode=m;reset();
  if(mode==="exam"&&per>0){left=per*qs.length;tid=setInterval(tick,1000)}
  render();
 }
 function tick(){left--;var bar=root.querySelector(".suq-tbar i");
  if(bar)bar.style.width=(100*left/Math.max(1,per*qs.length))+"%";
  var tm=root.querySelector(".suq-tleft");if(tm)tm.textContent=mmss(left);
  if(left<=0)finish(true)}
 function render(){
  var q=qs[idx],L=["A","B","C","D"];
  var timer=(mode==="exam"&&per)?'<div class="suq-timer">⏱ <span class="suq-tleft">'+mmss(left)+'</span><div class="suq-tbar"><i style="width:'+(100*left/Math.max(1,per*qs.length))+'%"></i></div></div>':"";
  var opts="";
  for(var i=0;i<q.options.length;i++){
   var cls="suq-opt";
   if(mode==="practice"&&ans[idx]>-1){cls+=" locked"+(i===q.a?" right":(i===ans[idx]?" wrong":""))}
   else if(i===ans[idx]){cls+=" sel"}
   opts+='<button class="'+cls+'" data-i="'+i+'"><span class="suq-letter">'+L[i]+'</span><span>'+esc(q.options[i])+'</span></button>';
  }
  var expl=(mode==="practice"&&ans[idx]>-1)?'<div class="suq-expl">'+(ans[idx]===q.a?'✅ సరైన సమాధానం! ':'❌ తప్పు — సరైనది: <b>'+esc(q.options[q.a])+'</b>. ')+esc(q.x||"")+'</div>':"";
  var nav='<div class="suq-nav"><button class="suq-btn alt" data-act="prev"'+(idx===0?" disabled":"")+'>← Prev</button>'+
   (mode==="exam"?'<button class="suq-btn alt" data-act="flag">'+(flags[idx]?"🚩 Flagged":"🚩 Flag")+'</button>':"")+
   (idx<qs.length-1?'<button class="suq-btn" data-act="next">Next →</button>':
    '<button class="suq-btn '+(mode==="exam"?"warn":"")+'" data-act="fin">'+(mode==="exam"?"Submit ✔":"Finish ✔")+'</button>')+
   "</div>";
  var pal="";
  if(mode==="exam"){pal='<div class="suq-pal">';
   for(var p=0;p<qs.length;p++){pal+='<button data-p="'+p+'" class="'+(p===idx?"cur ":"")+(flags[p]?"flg":(ans[p]>-1?"ans":""))+'">'+(p+1)+"</button>"}
   pal+="</div>"}
  body.innerHTML=timer+'<div class="suq-qnum">Question '+(idx+1)+' / '+qs.length+(flags[idx]?' • 🚩':"")+"</div>"+
   '<p class="suq-q">'+esc(q.q)+"</p>"+(q.qt?'<p class="suq-qte">'+esc(q.qt)+"</p>":"")+
   '<div class="suq-opts">'+opts+"</div>"+expl+nav+pal;
  body.querySelectorAll(".suq-opt").forEach(function(b){b.addEventListener("click",function(){
   if(mode==="practice"&&ans[idx]>-1)return;
   ans[idx]=parseInt(b.getAttribute("data-i"),10);render()})});
  body.querySelectorAll("[data-act]").forEach(function(b){b.addEventListener("click",function(){
   var a=b.getAttribute("data-act");
   if(a==="prev"&&idx>0){idx--;render()}
   else if(a==="next"&&idx<qs.length-1){idx++;render()}
   else if(a==="flag"){flags[idx]=flags[idx]?0:1;render()}
   else if(a==="fin"){if(mode==="practice"){finish(false)}else{
    var un=0;for(var k=0;k<ans.length;k++){if(ans[k]<0)un++}
    if(un>0&&!confirm(un+" ప్రశ్నలు వదిలేసారు. ఇంకా సబ్మిట్ చేయాలా?"))return;
    finish(false)}}})});
  body.querySelectorAll("[data-p]").forEach(function(b){b.addEventListener("click",function(){idx=parseInt(b.getAttribute("data-p"),10);render()})});
 }
 function grade(pct){
  if(pct>=90)return["🏆","Topper Level! అద్భుతం!"];
  if(pct>=75)return["🌟","Excellent! చాలా బాగుంది!"];
  if(pct>=60)return["👍","Good! ఇంకా ప్రాక్టీస్ చేయండి"];
  if(pct>=40)return["📚","Keep practicing! మీరు దగ్గరలో ఉన్నారు"];
  return["💪","పర్వాలేదు — రేపు మళ్ళీ ట్రై చేయండి!"]}
 function finish(timeout){
  if(done)return;done=true;if(tid){clearInterval(tid);tid=null}
  var score=0,ok=0,bad=0,skip=0,max=qs.length*mkc;
  for(var i=0;i<qs.length;i++){
   if(ans[i]<0){skip++}
   else if(ans[i]===qs[i].a){ok++;score+=mkc}
   else{bad++;score-=mkw}}
  score=Math.max(0,Math.round(score*100)/100);
  var pct=Math.round(100*score/Math.max(1,max)),g=grade(pct),streak=streakBump();
  var rev="";
  for(var j=0;j<qs.length;j++){var q=qs[j],L=["A","B","C","D"];
   var you=ans[j]<0?'<b>వదిలేసారు</b>':esc(q.options[ans[j]]);
   var mark=ans[j]<0?'':(ans[j]===q.a?'<b class="ok">✔</b> ':'<b class="bad">✘</b> ');
   rev+='<div class="suq-ritem">'+mark+"<b>Q"+(j+1)+":</b> "+esc(q.q)+"<br>మీ సమాధానం: "+you+" • సరైనది: <b>"+esc(q.options[q.a])+"</b> ("+L[q.a]+")<br><em>"+esc(q.x||"")+"</em></div>"}
  var shareTxt="నేను "+(cfg.topic||"Daily Quiz")+" లో "+score+"/"+max+" స్కోర్ చేసాను! 🎯🔥 "+window.location.href;
  body.innerHTML='<div class="suq-res"><h3>'+(timeout?"⏰ టైమ్ అయిపోయంది!":"🎉 క్విజ్ పూర్తయింది!")+'</h3>'+
   '<div class="suq-score">'+score+" / "+max+'</div>'+
   '<div class="suq-grade">'+g[0]+" "+g[1]+'</div>'+
   '<div class="suq-chips"><span class="suq-chip">✔ సరైనవి: '+ok+'</span><span class="suq-chip">✘ తప్పు: '+bad+'</span>'+
   '<span class="suq-chip">వదిలేసినవి: '+skip+'</span><span class="suq-chip">🎯 '+pct+'%</span>'+
   '<span class="suq-chip">🔥 Streak: '+streak+'</span></div>'+
   '<div class="suq-modes"><button class="suq-btn" data-r="retry">🔁 మళ్ళీ ట్రై</button>'+
   '<a class="suq-btn alt" style="text-decoration:none" target="_blank" rel="noopener" href="https://wa.me/?text='+encodeURIComponent(shareTxt)+'">📲 WhatsApp లో షేర్</a></div>'+
   '<div class="suq-review"><h4>📖 పూర్తి వివరణలు (Review)</h4>'+rev+"</div></div>";
  body.querySelector("[data-r]").addEventListener("click",function(){begin(mode)});
 }
 start();
}
function run(){var roots=document.querySelectorAll(".su-quiz");
 for(var i=0;i<roots.length;i++){try{init(roots[i])}catch(e){}}}
if(document.readyState==="loading"){document.addEventListener("DOMContentLoaded",run)}else{run()}
})();
"""


def build_widget_html() -> str:
    return (f'<style id="su-quiz-kit">/*{MARKER}*/{QUIZ_CSS}</style>'
            f'<script>/*{MARKER}*/{QUIZ_JS}</script>')


def _sidecar():
    from . import config
    from pathlib import Path
    return Path(config.STATE_PATH).with_name("quiz_kit.json")


def _load_id() -> Optional[str]:
    try:
        return json.loads(_sidecar().read_text(encoding="utf-8")).get("widget_id")
    except Exception:
        return None


def _save_id(wid: str) -> None:
    try:
        f = _sidecar()
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(json.dumps({"widget_id": wid}), encoding="utf-8")
    except Exception:
        pass


def _find_widget(wp) -> Tuple[Optional[str], List[Dict]]:
    try:
        r = wp._request("GET", "widgets", params={"base": "text", "per_page": 100})
        items = r.json() if r.ok else []
    except Exception:
        items = []
    for it in items:
        enc = str(((it.get("instance") or {}).get("encoded")) or it.get("id") or "")
        if MARKER in enc:
            return it.get("id"), items
    return None, items


def install(wp, dry: bool = False) -> Tuple[str, str]:
    """Idempotent site-wide quiz engine (CSS+JS) install. Same mechanics as
    design_kit.install: footer text widget, marker-identified, zero dupes."""
    from urllib.parse import urlencode

    payload = build_widget_html()
    if dry:
        return "planned", "footer text-widget lo quiz engine (CSS+JS) inject"
    try:
        r = wp._request("GET", "sidebars")
        sidebars = r.json() if r.ok else []
    except Exception as exc:  # noqa: BLE001
        return "warn", f"sidebars API ledu ({str(exc)[:60]})"
    if not sidebars:
        return "warn", "widget areas levu (block theme?) — quiz posts lo static key matrame"
    sid = ""
    for sb in sidebars:
        if "footer" in (sb.get("id", "") + sb.get("name", "")).lower():
            sid = sb["id"]
            break
    if not sid:
        sid = sidebars[0]["id"]
    enc = urlencode({"title": "", "text": payload, "filter": ""})
    existing, items = _find_widget(wp)
    if not existing:
        known = _load_id()
        if known and any(i.get("id") == known for i in items):
            existing = known
    try:
        if existing:
            cur = next((i for i in items if i.get("id") == existing), None)
            enc_old = str(((cur or {}).get("instance") or {}).get("encoded") or "")
            if enc_old == enc:
                return "ok", f"quiz engine up to date ({existing})"
            r = wp._request("POST", f"widgets/{existing}",
                            json={"instance": {"encoded": enc}, "sidebar_id": sid})
            if r.ok:
                _save_id(existing)
                return "ok", f"quiz engine refreshed ({existing} @ {sid})"
            return "warn", f"widget update fail: {r.status_code}"
        r = wp._request("POST", "widgets",
                        json={"id_base": "text", "sidebar_id": sid,
                              "instance": {"encoded": enc}})
        if r.ok:
            nid = r.json().get("id", "?")
            _save_id(nid)
            return "ok", f"quiz engine installed ({nid} @ {sid})"
        return "warn", f"widget create fail: {r.status_code}"
    except Exception as exc:  # noqa: BLE001
        return "warn", f"widgets API error: {str(exc)[:90]}"
