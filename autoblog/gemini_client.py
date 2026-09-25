"""Gemini API client — generates Telugu blog articles via REST (no SDK).

Uses the generateContent REST endpoint with a strict JSON response schema.
Automatically falls back to older model names if the primary one 404s,
and retries with backoff on rate limits.
"""

import json
import logging
import re
import time
from typing import Dict, List, Optional

import requests

from . import config

log = logging.getLogger("autoblog.gemini")

API_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

RESPONSE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "title": {"type": "STRING"},
        "slug": {"type": "STRING"},
        "meta_description": {"type": "STRING"},
        "tags": {"type": "ARRAY", "items": {"type": "STRING"}},
        "banner_text": {"type": "STRING"},
        "content_html": {"type": "STRING"},
        "focus_keyword": {"type": "STRING"},
        "secondary_keywords": {"type": "ARRAY", "items": {"type": "STRING"}},
        "seo_title": {"type": "STRING"},
        "quick_answer": {"type": "STRING"},
        "list_items": {"type": "ARRAY", "items": {"type": "STRING"}},
        "update_notes": {"type": "STRING"},
        "recruitment": {
            "type": "OBJECT",
            "properties": {
                "org_name": {"type": "STRING"},
                "org_url": {"type": "STRING"},
                "identifier": {"type": "STRING"},
                "apply_end": {"type": "STRING"},
                "salary_min": {"type": "INTEGER"},
                "salary_max": {"type": "INTEGER"},
                "location": {"type": "STRING"},
            },
        },
        "faq": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {"question": {"type": "STRING"}, "answer": {"type": "STRING"}},
                "required": ["question", "answer"],
            },
        },
        "external_links": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {"text": {"type": "STRING"}, "url": {"type": "STRING"}},
                "required": ["text", "url"],
            },
        },
    },
    "required": ["title", "slug", "meta_description", "tags", "banner_text", "content_html"],
}

# Real, well-known reference points so the model stays grounded and does not
# invent fake notifications with made-up deadlines / vacancy counts.
CATEGORY_SEEDS = {
    "Scholarships": (
        "National Scholarship Portal (NSP), Central Sector CSSS, PM YASASVI, "
        "AICTE Pragati & Saksham, Vidyalakshmi education loan portal, "
        "Telangana ePASS / TS scholarships, AP Jnanabhumi / JVD schemes, "
        "NMMS, state minority & BC scholarships"
    ),
    "Abroad Jobs": (
        "Gulf jobs for Indians (UAE, Saudi, Qatar, Kuwait, Oman, Bahrain), eMigrate/MEA "
        "protector of emigrants rules, overseas recruitment drives, IELTS/PTE/TOEFL test "
        "dates and score requirements, study abroad + work visa updates (Canada express "
        "entry, UK skilled worker, Germany opportunity card, Australia skilled migration, "
        "Japan/Korea care work), passport & visa appointment process, NRI student guidance"
    ),
    "Govt Jobs": (
        "SSC CGL/CHSL/MTS/GD, RRB NTPC & Group D, UPSC Civil Services, "
        "TSPSC & APPSC Group exams, TS/AP Police SI & Constable, "
        "IBPS PO & Clerk, SBI PO & Clerk, India Post GDS, Anganwadi, court recruitments"
    ),
    "Education News": (
        "NEP 2020 changes, digital learning platforms (SWAYAM, DIKSHA, NPTEL), "
        "board exam policy updates, skill development programs, "
        "study abroad trends, education app/technology news"
    ),
    "Exam Updates": (
        "exam pattern changes, admit card download process, answer key & "
        "objection process, result checking process, cut-off trends, "
        "re-verification/recounting procedures for SSC/UPSC/TSPSC/APPSC/RRB/banks"
    ),
    "Admissions": (
        "TS EAMCET, AP EAPCET, DOST degree admissions, ICET/ECET/PGECET, "
        "CPGET, JoSAA/CSAB engineering counselling, Intermediate admissions, "
        "MBA/MCA counselling, hostel & fee reimbursement process"
    ),
    "Results": (
        "how to check results on official portals (Manabadi-style guidance), "
        "SSC/Intermediate results process, supplementary exams, "
        "revaluation procedure, grade vs marks explanation"
    ),
    "Internships": (
        "AICTE internship portal, NITI Aayog internship, Google/Microsoft/Amazon "
        "internship preparation, startup internships, resume tips, "
        "AP & Telangana government internship schemes"
    ),
    "Study Tips": (
        "timetable planning, revision techniques, mock tests, "
        "memory techniques, online free resources (NPTEL, SWAYAM, DIKSHA), "
        "exam stress management, English & aptitude improvement"
    ),
    # --- live-site categories (v14; exact names = existing terms reuse) ---
    "Central Govt Jobs": (
        "SSC CGL/CHSL/MTS/GD, RRB NTPC & Group D, UPSC Civil Services, "
        "IBPS PO & Clerk, SBI PO & Clerk, India Post GDS, Agniveer army "
        "rally, Supreme/High Court recruitments, central teacher schemes"
    ),
    "TS Govt Jobs": (
        "TSPSC Group 1/2/3/4, TS Police SI & Constable, TS GENCO/TRANSCO, "
        "Telangana Gurukul (TGPSC) teachers, TS High Court, municipal "
        "recruitments, Hyderabad Metro, TGWRDC"
    ),
    "AP Govt Jobs": (
        "APPSC Group 1/2, AP Police SI & Constable, APSRTC recruitments, "
        "AP GENCO/TRANSCO, AP DSC teachers, ward volunteer, AP Grama "
        "Sachivalayam, AP High Court"
    ),
    "Private Jobs": (
        "TCS NQT, Infosys, Wipro, HCL, Cognizant, Accenture, Amazon, "
        "Deloitte fresher hiring, off-campus drives, salary bands, "
        "service bond details, background verification process"
    ),
    "Software Jobs": (
        "frontend/backend/full-stack developer roles, IT services vs "
        "product companies, data analyst & data science roles, testing, "
        "DevOps, system engineer drives, coding interview process"
    ),
    "Part Time Jobs": (
        "work-from-home jobs for students, freelancing platforms, data "
        "entry, content writing, online tutoring, delivery & weekend jobs, "
        "scam-vs-genuine part time job checks"
    ),
    "Walkin Jobs": (
        "walk-in interview venues, dates & timings, direct hiring drives, "
        "document checklist, resume preparation, HR round tips, "
        "same-day offer process"
    ),
    "Hall Tickets": (
        "admit card download process for SSC/TSPSC/APPSC/RRB/exams, "
        "registration number recovery, exam day guidelines & reporting "
        "time, scribe rules, ID proof requirements"
    ),
    "Success Stories": (
        "documented UPSC/SSC/TSPSC/APPSC/university achiever journeys, verified "
        "result and identity, preparation timeline, obstacles, practical lessons; "
        "never invented quotes, marks, ranks, income or first-person experience"
    ),
    "Outsourcing Jobs": (
        "TS/AP outsourcing & contract-basis recruitment, CRC (Commissionerate "
        "of Rural Development) outsourcing, TSSPDCL/TGSPDCL outsourced posts, "
        "guest faculty & honorarium roles, eligibility, pay scales, renewal "
        "and document verification steps"
    ),
    "Current Affairs": (
        "daily current affairs for competitive exams — national & Telugu-state "
        "schemes, appointments, awards, sports, economy basics; every fact must "
        "come from an official press release (PIB/state government) and stay "
        "exam-relevant (no hype, no rumour)"
    ),
    "Upcoming Exams": (
        "upcoming exam & recruitment calendar — TSPSC/APPSC/SSC/RRB/NTA "
        "tentative schedules, application windows, fee dates, expected "
        "vacancy counts, how to verify dates on the official calendar"
    ),
    "Exam Tips": (
        "exam preparation plans for Telugu students — subject-wise strategy, "
        "revision cycles, previous-paper practice, time management, "
        "score-improvement habits, exam-day checklist (no false promises)"
    ),
    "Online Education": (
        "online MBA & degrees, IGNOU distance programs, upskilling "
        "platforms, AICTE-approved certifications, course fees & EMI/loan "
        "options, admissions counselling (EAMCET/DOST/ICET) guidance"
    ),
}

def _story_brief(topic: str) -> str:
    """Return a strict reader-task brief; never manufacture a success story."""
    value = (topic or "").lower()
    if any(x in value for x in ("hall ticket", "admit card")):
        return """
CONTENT TYPE: HALL TICKET / ADMIT CARD
- First say whether it is officially RELEASED or NOT RELEASED, based only on an official source.
- Give the official Direct Link, required login details, exact download steps, exam date/time,
  reporting time, venue checks, valid ID proof, photo/signature checks and correction/helpdesk path.
- Never write 'released' from a search headline alone. Do not invent a link or exam-day rule.
"""
    if any(x in value for x in ("result", "merit list", "scorecard", "cut off")):
        return """
CONTENT TYPE: RESULT / MERIT LIST
- First say the verified Result status and official board/recruiter source.
- Give the official Direct Link, credentials needed, exact checking steps, scorecard fields,
  cut-off/merit-list meaning, revaluation or objection route, supplementary next step and helpdesk.
- Never predict marks, rank, cut-off or release time. Clearly label a pending Result as pending.
"""
    if any(x in value for x in ("success story", "selected candidate", "ranker", "topper",
                                "inspiring journey")):
        return """
CONTENT TYPE: VERIFIED SUCCESS STORY
- Publish only a real, named person's documented story supported by attributable sources.
- Separate verified biography, timeline, preparation method, obstacles, result and practical lessons.
- Never fabricate first-person experience, interview quotes, rank, salary, marks or emotional scenes.
- If identity and achievement cannot be independently verified, refuse the story instead of composing it.
"""
    if any(x in value for x in ("job", "recruit", "vacancy", "notification", "walk-in",
                                "internship", "apprentice")):
        return """
CONTENT TYPE: JOB / RECRUITMENT
- Put the actionable answer first. Cover only verified Organization, Post names, Vacancy,
  Eligibility, Age Limit, relaxation, Salary/pay, Application Fee, Important Dates, Selection
  Process, Documents, Apply Online steps, official Notification PDF, Direct Link and warnings.
- Distinguish permanent/contract/outsourcing roles and gross pay/stipend. Never guarantee selection.
"""
    return """
CONTENT TYPE: EDUCATION SERVICE ARTICLE
- Answer the reader's task first, then include only facts and steps that change what they should do.
"""


PROMPT_TEMPLATE = """You are an expert Telugu education-content writer for the website studentup.in (Telugu students audience: scholarships, govt jobs, exam updates, admissions, study tips).

CATEGORY: {category}

TASK: Write ONE original, SEO-friendly blog post for this category. Choose a fresh, specific topic yourself (for example: "{seed_hint}" an issue, scheme, process, or guide related to the category). The current year is {year} — you may use it in the title when relevant.

{avoid_block}

LANGUAGE STYLE (very important):
- Write in easy, conversational Telugu for ordinary students and parents; this must NOT read like formal, pure, translated, or literary Telugu.
- Keep familiar education/job words in ENGLISH script: Notification, Eligibility, Age Limit, Application Fee, Important Dates, Selection Process, Apply Online, Official Website, Last Date, Vacancy, Salary, Exam Pattern, Documents, Result, Hall Ticket and Direct Link. Do not transliterate these words into Telugu script.
- Explain every uncommon term immediately in simple Telugu. Use short sentences and clear labels so even a first-time applicant can follow it.
- Title: catchy, Telugu + English mix, SEO friendly, roughly 40-70 characters. Include the year {year} if the topic suits it.

ACCURACY RULES (very important):
- Mention only REAL, well-known exams/schemes/portals. Do NOT invent new scheme names, fake vacancy numbers, fake dates or fake deadlines.
- Do NOT state specific application dates or deadlines. Instead write guidance like "official website lo latest notification check cheyandi" (in Telugu).
- Structure the post as a helpful evergreen guide/update that stays useful.
- Include fee/salary/stipend/loan/cost details only when verified and genuinely useful to the reader. Never add commercial details to attract ads or inflate word count.

ARTICLE STRUCTURE (HTML):
- 2-3 intro paragraphs (no heading).
- Then <h2> sections covering: overview/key details, eligibility, benefits/important points, step-by-step "how to apply / how to check" as <ul><li> lists, useful tips.
- Use <strong> for key phrases; include one simple <table> (3-5 rows) if a comparison or summary table fits naturally.
- Add an FAQ only for real follow-up questions not already answered in the article.
- Do NOT add a generic conclusion, motivational ending, share/comment CTA, repeated summary, history lesson, or word-count padding.
- Stop as soon as the reader can safely complete the task; completeness matters, length does not. Use ONLY these HTML tags: h2 h3 p ul ol li strong em table thead tbody tr th td a blockquote pre code. No <html>/<head>/<body>, no markdown, no code fences.

ALSO RETURN:
- slug: English kebab-case URL slug for this post ( transliterate the topic, e.g. "ssc-cgl-preparation-guide" ), max 60 chars, lowercase, hyphens only.
- meta_description: 140-160 characters Telugu summary for SEO (focus keyword MUST be in it).
- tags: 5 to 8 tags, mix of Telugu and English keywords.
- banner_text: short ENGLISH text (max 6 words) suitable for a featured image banner, e.g. "Scholarships 2026 Apply Online".
- focus_keyword: ONE main SEO keyword phrase (Telugu + English mix). It must appear: in the title, in the FIRST paragraph, in at least 2 <h2> headings, and naturally 5-8 times in the body (density ~1%).
- secondary_keywords: 3-5 related keyword phrases people also search (mix Telugu/English).
- seo_title: SEO title with focus keyword at the START, under 60 characters, include the year and a power word (Complete/Guide/Best) and a number if natural.
- quick_answer: 40-60 word direct answer in Telugu summarizing the article (featured snippet bait). Must contain the focus keyword.
- faq: 4-6 objects with "question" and "answer" string fields — "People Also Ask" style questions (Telugu) with short 2-3 sentence answers.
- external_links: 1-3 REAL official websites related to the topic (e.g. https://ssc.gov.in) with short Telugu anchor text. ONLY well-known official portals — never invent URLs.

Return ONLY valid JSON matching the schema."""


REWRITE_PROMPT_TEMPLATE = """You are an expert Telugu education-content writer for studentup.in.

TASK: Below is a REFERENCE ARTICLE from another website. Write a COMPLETELY NEW, 100% ORIGINAL article in your own words about the same topic for studentup.in.

=============== REFERENCE ARTICLE (facts only — do NOT copy) ===============
SOURCE URL: {url}
SOURCE SITE: {site}
SOURCE TITLE: {src_title}
SOURCE CONTENT:
{src_text}
============================================================================

STRICT ORIGINALITY RULES (copyright safe — very important):
- Do NOT copy any sentence, phrase structure, paragraph, title hook, or section order from the source.
- Use ONLY the FACTS/information from the source (scheme names, eligibility, process, numbers); separate facts from the source's expression before writing.
- First plan a new reader journey for StudentUp, then write it. Do not translate, lightly paraphrase, or mechanically walk through the source paragraph by paragraph.
- Everything must be freshly written by you in a completely different structure and wording, with a distinct opening and distinct H2/H3 phrasing.
- Write it as if you are an independent expert explaining the topic from scratch.
- When the facts support it, aim for 700-1000 useful words; never repeat a fact or add generic text just to hit a length target.
- The published article must read as StudentUp's own article. Do not mention the reference website, source site, automation, AI, evidence score, editorial workflow or "source-backed draft" in the article body.
- Do not add a byline/review-pending line, reading-time badge, methodology block, or "Best Guide" title suffix.

IMPROVE & EXPAND (advanced content — very important):
- ADD extra valuable sections the source may not have: detailed step-by-step process, required documents list, common mistakes to avoid, pro tips, comparison table, extra background context.
- Make it complete only where the source and official context support it; do not inflate the article to beat a word count.
- LANGUAGE: easy spoken Telugu + familiar ENGLISH-script labels (Notification, Eligibility, Age Limit, Application Fee, Important Dates, Selection Process, Apply Online, Official Website, Documents, Direct Link). Never use formal/pure translated Telugu or transliterate these standard terms.

ACCURACY RULES:
- Keep only facts from the source + well-known real information. Do NOT invent dates/deadlines/vacancy numbers beyond what the source states.
- Official website links: mention only well-known real portals.

ARTICLE STRUCTURE (HTML only — h2 h3 p ul ol li strong em table thead tbody tr th td a blockquote pre code):
- 2-3 intro paragraphs (focus keyword in FIRST paragraph).
- <h2> sections: overview, eligibility/details, benefits, step-by-step how to apply/check (as lists), documents required, tips & common mistakes, one <table> summary.
- FAQ only for unanswered applicant questions supported by evidence.
- No generic conclusion, share/comment CTA, repeated summary, motivation, or padding.

ALSO RETURN (same JSON schema):
- title: SEO Telugu+English title, 50-70 chars, focus keyword at start, year {year} if relevant.
- slug, meta_description (keyword included, 140-160 chars), tags (5-8), banner_text (English, max 6 words).
- focus_keyword: ONE main keyword phrase — in title, first para, 2+ h2 headings, ~1% density.
- seo_title: keyword at start, under 60 chars, year + power word.
- external_links: 1-3 real official portals for this topic with Telugu anchor text.

Return ONLY valid JSON."""


RESEARCH_PROMPT_TEMPLATE = """You are a top-level Telugu SEO content strategist for studentup.in (education/jobs/scholarships site).

TASK: Below are MULTIPLE research sources about the SAME topic/notification. Use them to create ONE definitive, 100% ORIGINAL, people-first article that answers the reader's real questions and adds source-backed context. Do not write for rankings, ads, or word count.

=============== PRIMARY SOURCE (user's URL — main base) ===============
URL: {url} | SITE: {site}
TITLE: {src_title}
CONTENT:
{src_text}
=======================================================================
{extra_sources_block}
STRICT ORIGINALITY RULES (copyright safe — very important):
- Do NOT copy any sentence, phrase, title hook, section order, or distinctive structure from ANY source. Facts only, fresh original writing.
- First build an independent outline around the reader's decision or next step; do not merge or translate the source paragraphs in order.
- Write as an independent expert explaining the topic from scratch, with a distinct opening and your own H2/H3 wording.
- When the evidence supports it, aim for 700-1000 useful words; never pad, repeat facts, or add generic SEO prose to reach a count.
- The final post must sound like StudentUp's own blog. Never print source names, source counts, automation/AI notes, evidence confidence, editorial workflow, "Sources checked", "source-backed draft" or review-pending labels in the article.
- If sources CONFLICT on a number/date, use the most repeated/official value and phrase it as "notification prakaram" (as per notification).
- Do not add a byline, reading-time badge, methodology block, generic "Best Guide" suffix, or unrelated related-topic links.

RESEARCH AND VALUE STRATEGY (very important):
- Start from the PRIMARY source's facts, then add only useful, source-backed context that helps a reader act safely (eligibility, fee details, selection stages, documents, dates mentioned).
- Resolve conflicts by naming the official source and flagging uncertainty; never silently choose a convenient number or deadline.
- Include overview, eligibility, benefits/salary, application steps, documents, fee, selection process, common mistakes, and a comparison table only when each section is genuinely useful.
- Include salary/fee/stipend/loan/cost figures only when verified and relevant. Never add commercial details to attract ads, inflate word count, or target high CPC.
- Prefer concise, complete answers over a fixed word count. Do not add generic introductions, conclusions, repeated summaries, motivation, share/comment requests, or SEO padding.
- LANGUAGE: easy spoken Telugu + familiar ENGLISH-script labels (Notification, Eligibility, Age Limit, Application Fee, Important Dates, Selection Process, Apply Online, Official Website, Vacancy, Documents, Direct Link). Write for ordinary students/parents, not highly educated readers; avoid formal/pure Telugu.

ARTICLE STRUCTURE (HTML only — h2 h3 p ul ol li strong em table thead tbody tr th td a blockquote pre code):
- 2-3 intro paragraphs (focus keyword in FIRST paragraph).
- <h2> sections for each major area + step-by-step process as lists + at least one <table>.
- FAQ only when useful (<h3> questions must match the faq JSON); no generic conclusion or CTA.

ALSO RETURN (same JSON schema):
- title: 50-75 chars, focus keyword at start, year {year}, power word + number if natural.
- slug (English kebab-case), meta_description (140-160 chars, keyword included), tags (6-8), banner_text (English, max 6 words).
- focus_keyword: main keyword — in title, first para, 2+ h2s, ~1% density.
- secondary_keywords: 3-5 related search phrases (Telugu+English).
- seo_title: keyword at start, under 60 chars, year + power word + number.
- quick_answer: 40-60 word Telugu direct answer (featured snippet bait) with keyword.
- faq: 5-6 objects with "question" and "answer" string fields — People-Also-Ask style.
- external_links: 1-3 real official portals with Telugu anchor text.

Return ONLY valid JSON."""


def _format_extra_sources(extras) -> str:
    if not extras:
        return ""
    blocks = []
    for i, s in enumerate(extras, 1):
        blocks.append(
            f"--------------- RESEARCH SOURCE {i} ---------------\n"
            f"URL: {s.url} | SITE: {s.site_name}\n"
            f"TITLE: {s.title}\n"
            f"CONTENT:\n{s.text[:3000]}\n"
        )
    return (
        "=======================================================================\n"
        "ADDITIONAL EVIDENCE SOURCES (use for corroboration and gap checking):\n"
        + "\n".join(blocks)
        + "======================================================================="
    )


UPDATE_PROMPT_TEMPLATE = """You are a top-level Telugu SEO content editor for studentup.in.

TASK: Below is an ALREADY-PUBLISHED article and NEW RESEARCH SOURCES with fresh information. Produce an IMPROVED, UPDATED version of the article that keeps the same topic and structure but integrates ALL new useful facts.

=============== EXISTING ARTICLE (currently published) ===============
TITLE: {title}
FOCUS KEYWORD: {focus_keyword}
CONTENT:
{existing_text}
=======================================================================

=============== NEW RESEARCH SOURCES (fresh information) ==============
{extra_sources_block}
=======================================================================

UPDATE RULES (very important):
- KEEP the same title and topic (minor polish ok, meaning must not change).
- Integrate every NEW fact from the research sources that the existing article is MISSING (new dates, fee changes, vacancy updates, extra steps, documents, official links). Do NOT remove existing correct information.
- If sources conflict with the existing article, prefer the newer/official info.
- The existing article may contain helper sections like "విషయ సూచిక (Table of Contents)", "Quick Answer", "About This Article", "Related Articles", "Official Links", "Reading Time" — EXCLUDE all of them from your output. Produce ONLY the main article body.
- LANGUAGE: improve into easy spoken Telugu + standard English labels. Avoid pure/formal Telugu even if the old article uses it.
- Length: keep or improve (2200-3000 words). Short paragraphs, lists, one table.

ALSO RETURN (same JSON schema):
- title: SAME as existing title (or lightly polished, under 75 chars).
- slug: "keep" (do not change the URL).
- meta_description, tags, banner_text: same as existing style.
- focus_keyword / secondary_keywords / quick_answer / faq: same as existing, updated only if the new info changes them.
- update_notes: 2-4 short Telugu bullets summarizing WHAT NEW INFO was added (e.g. "• Fee details add chesayi • New exam date update").

Return ONLY valid JSON."""


LISTICLE_PROMPT_TEMPLATE = """You are a top Telugu viral-content writer for studentup.in (education/jobs portal like Adda247 style).

TASK: Write a TRENDING listicle ("story" style) article: {topic} {year} edition.

LISTICLE RULES (very important):
- NUMBERED <h2> sections — one per item: "<h2>1. Item Name – short hook</h2>" etc.
- Each item: 2-3 paragraphs (what it is, eligibility/salary/details, why students love it) + a <ul> quick-facts list where natural.
- Catchy intro (2 paragraphs) explaining WHY this list matters to Telugu students.
- After the numbered items: one comparison <table> (item, eligibility, salary/scope).
- A "Evariki Best?" (who should choose what) short section.
- Conclusion + FAQ (4-5 <h3> questions).
- TOTAL: 2000-3000 words. Only REAL, well-known jobs/schemes/apps — no invented data, no fake salary numbers beyond well-known pay levels (use pay matrix levels like "Level-4 (25,500-81,100)").
- LANGUAGE: easy spoken Telugu + standard ENGLISH-script labels; ordinary students/parents must understand it. No pure/formal Telugu; use short paragraphs and strong hooks.
- focus_keyword: the list topic itself (e.g. "Central Government Jobs 2026") — in title, first para, 2+ h2s.
- list_items: return the N item names as an array (same as your h2 items, short names).
- Title format: "Top N {topic} 2026 – Complete List Telugu lo" style, 55-80 chars, number included.
- tags/banner_text/seo_title/quick_answer/faq/external_links: same rules as before.

Return ONLY valid JSON."""


def generate_listicle(topic: str, recent_titles: List[str], year: int) -> Dict:
    """Trending listicle article (Top 10 jobs lanti stories)."""
    if not config.gemini_configured():
        raise GeminiError("GEMINI_API_KEY not set")
    avoid_block = ""
    if recent_titles:
        sample = "\n".join(f"- {t}" for t in recent_titles[:30])
        avoid_block = ("Your TITLE must be different from these already published:\n" + sample)
    prompt = LISTICLE_PROMPT_TEMPLATE.format(topic=topic, year=year)
    if avoid_block:
        prompt += "\n" + avoid_block
    article = _generate_with_retries(prompt)
    article["article_type"] = "listicle"
    return article


# ---------------------------------------------------------------- v38
TOP_POST_PROMPT_TEMPLATE = """You are the senior editor of studentup.in (Telugu students portal, AP/TS focus).
Write ONE "top post" (category-defining, best-on-the-internet) article for the search phrase below,
following the editor blueprint EXACTLY. Facts must be true and verifiable — for notifications use the
official notice values; NEVER invent dates, fees, vacancy counts or salary figures.

BLUEPRINT (editor already planned this — follow the structure, write in your own Telugu voice):
{blueprint}

ARTICLE RULES:
- Easy spoken Telugu + ENGLISH-script terms (Notification, Eligibility, Apply Online, Cut Off, Hall Ticket, Age Limit, Fee, Important Dates). Never formal/pure Telugu.
- H1/title must be the blueprint's title style: exact keyword FIRST HALF + year + power word, 40-62 chars.
- Every H2 from the blueprint (same order); each H2 gets 2-4 short paragraphs (2-3 sentences) plus the
  planned H3 subtopics and a table/list where the blueprint asks for one.
- The first 40 words must fully answer the query (snippet + WhatsApp forward friendly).
- Keyword usage: exact phrase in first paragraph, 2+ H2s, 8-15 times total (1-2% density) — NEVER stuff.
- Include every secondary/question keyword naturally at least once (no keyword lists, no stuffing).
- Tables: only real data (dates, fee slabs, vacancy breakup, pay levels). Cells 2-6 words.
- List items: complete in <= 10 words.
- Visible FAQ: 5+ <h3> question headings in student language with honest 1-2 sentence answers.
- Add "mana site related topic" anchor phrases (internal links) and 1-2 official website names.
- E-E-A-T: "official notification prakaram" phrasing; say clearly when something is not yet announced.
- If any required fact is not known/verifiable, write: "అధికారిక నోటిఫికేషన్‌లో ధృవీకరించుకోండి" —
  never guess.
- Do NOT copy any competitor text; write independently from facts.

Return ONLY valid JSON with exactly these keys:
{{"title": "...", "slug": "...", "meta_description": "...", "seo_title": "...",
 "focus_keyword": "...", "secondary_keywords": ["...", "..."],
 "quick_answer": "...", "banner_text": "...", "tags": ["..."],
 "external_links": [{{"text": "...", "url": "https://..."}}],
 "content_html": "<p>...</p><h2>...</h2>...",
 "faq": [{{"question": "...", "answer": "..."}}]}}"""


def generate_top_post(blueprint: Dict, year: int = 0) -> Dict:
    """v38: blueprint-driven top-post generation (top_post.build_blueprint output).

    Blueprint ni prompt ga istham — MODEL facts invent cheyyakudadu;
    structure/on-page plan matrame blueprint nunchi vastundi.
    """
    if not config.gemini_configured():
        raise GeminiError("GEMINI_API_KEY not set")
    from . import top_post as _tp

    prompt = TOP_POST_PROMPT_TEMPLATE.format(blueprint=_tp.gemini_brief(blueprint))
    article = _generate_with_retries(prompt, blueprint.get("category", ""))
    article["article_type"] = "top-post"
    article.setdefault("year", year or blueprint.get("year"))
    return article


QUIZ_PROMPT_TEMPLATE = """You are a senior exam-content setter for studentup.in (Telugu education portal). Create a top-quality {level_name} level (L{level}) MCQ quiz for Telugu students on: {topic} ({topic_te}).

Return ONLY valid JSON — exactly this schema:
{{
  "topic": "{topic}",
  "topic_te": "{topic_te}",
  "questions": [
    {{
      "q": "question in English (natural Telugu terms like 'ప్రభుత్వ ఉద్యోగాలు' allowed inside)",
      "qt": "same question fully in Telugu script (accurate translation)",
      "options": ["option A", "option B", "option C", "option D"],
      "a": 0,
      "x": "1-2 sentence explanation in Telugu+English mix (why the answer is correct)"
    }}
  ]
}}

HARD RULES:
- EXACTLY {n} questions. All 4 options non-empty, plausible, unambiguous.
- "a" = index (0-3) of the correct option. VARY positions — never all 0.
- Difficulty L{level} ({level_name}): {level_hint}
- Questions must be FACTUALLY CORRECT, well-known, verifiable knowledge (current affairs {year}, schemes, exams, science, AP/TS state facts). NEVER invent dates, amounts or fake schemes. When unsure, use evergreen facts.
- Every question different angle — no near-duplicates.
- "x" explanation: crisp, teaches one fact (Telugu script + English terms mix).
- No question text longer than 220 characters; options under 90 chars each.
- LANGUAGE: questions bilingual (q English-first, qt Telugu script); explanations Telugu-mix like Adda247 Telugu.

Return ONLY the JSON object."""

_LEVEL_HINTS = {
    1: "direct, one-fact recall questions every student should know.",
    2: "concept + fact mix; 1-2 options close distractors.",
    3: "application & statement-based; tricky distractors, exam-grade.",
    4: "multi-statement, assertion-reason style, topper-level precision.",
}


def generate_quiz(topic: str, topic_te: str, level: int, n: int,
                  year: int) -> Dict:
    """Bilingual exam-grade MCQ set. Returns normalized quiz dict.
    Raises GeminiError after retries (validation feedback appended)."""
    if not config.gemini_configured():
        raise GeminiError("GEMINI_API_KEY not set")
    prompt = QUIZ_PROMPT_TEMPLATE.format(
        topic=topic, topic_te=topic_te, level=level, n=n, year=year,
        level_name=QUIZ_LEVEL_NAMES.get(level, "Mixed"),
        level_hint=_LEVEL_HINTS.get(level, _LEVEL_HINTS[2]),
    )
    last_err: Optional[Exception] = None
    for attempt in range(1, config.GEMINI_MAX_RETRIES + 1):
        for model in _models():
            for key in _usable_keys():
                try:
                    raw = _call_model(model, prompt, key)
                    quiz = _parse_json(raw)
                    problems = validate_quiz_shape(quiz, n)
                    if problems:
                        raise GeminiError("VALIDATION: " + "; ".join(problems[:4]))
                    _bump_key(key)
                    quiz = normalize_quiz_shape(quiz, n)
                    quiz["model"] = model
                    return quiz
                except GeminiError as exc:
                    msg = str(exc)
                    if msg.startswith("MODEL_NOT_FOUND"):
                        break
                    if msg.startswith(("QUOTA_KEY", "BAD_KEY")):
                        _mark_key_dead(key, msg.split(":")[0])
                        last_err = exc
                        continue
                    last_err = exc
                    if msg.startswith("VALIDATION") and attempt < config.GEMINI_MAX_RETRIES:
                        # feedback loop: tell the model exactly what to fix
                        prompt += ("\n\nPREVIOUS OUTPUT PROBLEMS (fix ALL — "
                                   + msg[11:200] + "). Return the FULL corrected JSON.")
                    break
                except (json.JSONDecodeError, ValueError) as exc:
                    last_err = GeminiError(f"Quiz JSON parse failed: {exc}")
                    break
        if attempt < config.GEMINI_MAX_RETRIES:
            time.sleep(min(30, 5 * (2 ** (attempt - 1))))
    raise GeminiError(f"Quiz generation failed: {last_err}")


# thin aliases so gemini_client stays decoupled from quiz_engine imports
QUIZ_LEVEL_NAMES = {1: "Basics", 2: "Intermediate", 3: "Advanced", 4: "Top Level"}


def validate_quiz_shape(quiz: Dict, n: int) -> List[str]:
    from . import quiz_engine
    return quiz_engine.validate_quiz(quiz, n)


def normalize_quiz_shape(quiz: Dict, n: int) -> Dict:
    from . import quiz_engine
    return quiz_engine.normalize_quiz(quiz, n)


def generate_update(
    existing_title: str,
    existing_text: str,
    focus_keyword: str,
    extras: List,
    year: int,
) -> Dict:
    """Published article + kotha research -> improved version (same URL)."""
    if not config.gemini_configured():
        raise GeminiError("GEMINI_API_KEY not set")
    prompt = UPDATE_PROMPT_TEMPLATE.format(
        title=existing_title,
        focus_keyword=focus_keyword or "(unknown)",
        existing_text=existing_text[:9000],
        extra_sources_block=_format_extra_sources(extras),
        year=year,
    )
    return _generate_with_retries(prompt)


class GeminiError(Exception):
    pass


def _models() -> List[str]:
    models = [config.GEMINI_MODEL] + [
        m for m in config.GEMINI_FALLBACK_MODELS if m != config.GEMINI_MODEL
    ]
    return models


# Rank Math writing rules — prathi prompt ki append (article write chesetappude
# score perugutundi: keyword placement, numbers, short paras, link anchors)
WRITING_RULES = """

RANK MATH WRITING RULES (follow exactly):
- Put the focus keyword in the FIRST HALF of the title and include a NUMBER (year/vacancies/count).
- Focus keyword: first paragraph lo + at least 2 <h2> subheadings lo + naturally 8-15 times total (1-2% density) — keyword stuffing cheyakudadu.
- Prathi paragraph 120 words kanna takkuva (2-4 sentences max).
- Consecutive sentences same word tho start cheyakudadu.
- At least 2-3 internal-link-friendly phrases (mana site related topics peru mention cheyandi - " SSC CGL notification", " scholarship guide" lanti anchors) and 1-2 official site names (text anchor kosam).
- Content lo table kavali + numbered/bulleted lists kavali (snippet eligibility).

NO-COPY RULE (absolute — copyright + Google safety):
- Vere website/article content nunchi SENTENCES, paragraph structure, headings order copy cheyakudadu.
- FACTS (names, numbers, dates, process) matrame teesukuni — 100% mana own words lo, mana structure lo ravadam.
- Source ki idi "rewrite" kaadu — idi "fresh expert article on the same facts". Duplicate-content penalty endukuadu.

PUBLIC ARTICLE VOICE:
- Article ni StudentUp tana readers kosam rasina normal blog laga rayandi; source website, competitor website, automation, AI, evidence score, editorial workflow, "source-backed draft", "Sources checked", reading time or review-pending text ni content lo mention cheyakandi.
- Byline ni article body lo inject cheyakandi. Title ki "Best Guide" / "— Best Guide" lanti artificial suffix vadakandi.
- Related links ante same topic/entity ki nijanga panikoche pages matrame; broad category lo unna unrelated jobs ni list cheyakandi.

10X CONTENT STRATEGY (top publisher standard — beat every competitor):
- Competitors ichina information ANNI + inka ekkuva ivvali: common mistakes section, pro tips, real numbers (pay matrix levels, fees, stipends — well-known values matrame), minimum 2 tables (info table + comparison table).
- Step-by-step process ul/ol lists ga (screenshots em cheyalo exact ga) — reader action-ready ga undali.
- Prathi section ki specific value: generic filler ("this is important") writing keellaadu — numbers, examples, caveats ivvali.
- 5+ FAQ questions "People Also Ask" style lo — real ga students adige prashnalu (apply ela, eligibility, negative marking, direct link emiti).
- E-E-A-T: official website link + "notification prakaram" phrasing + last-verified note — trust signals.

KEYWORD DOMINANCE (Google #1 target — students search chese exact phrases):
- Title FIRST words = focus keyword (exact search phrase, year tho — e.g. "SSC CGL 2026 Notification – ..."). Long hook tarvata.
- Focus keyword first 100 words lo rawali; H2 headings lo students vesē long-tail intent words pettandi (apply online, eligibility, hall ticket, cut off, salary, direct link...).
- Meta description focus keyword THO start (first 60 chars lo kanipinchali — SERP CTR).

NATURAL TELUGU STYLE (ordinary student/parent ki first read lo ardam avvali):
- Simple spoken Telugu only; granthika, formal, Sanskrit-heavy, word-for-word translated Telugu vaddu.
- Ee standard words ENGLISH script lo ne undali: Notification, Eligibility, Age Limit, Application Fee, Important Dates, Selection Process, Apply Online, Official Website, Last Date, Vacancy, Salary, Exam Pattern, Documents, Result, Hall Ticket, Cut Off, Direct Link. Telugu script loki transliterate cheyakudadu.
- Difficult term vaste ade sentence lo simple Telugu explanation ivvali. Reader already exam expert ani assume cheyakudadu.
- SODI/FILLER strict ban: "చివరి వరకు చదవండి", "ఈ విషయం చాలా ముఖ్యమైనది", "పూర్తి వివరాలు తెలుసుకుందాం" lanti empty lines vaddu. Prathi paragraph oka fact, answer, warning, example leda action ivvali.
- Oke point ni intro, body, conclusion lo repeat cheyakudadu. Word count/keyword density kosam paragraph add cheyakudadu.
- Okka sentence 15-20 words minchakudadu; paragraph 2-3 sentences. Natural connectives vadali, kaani readability score kosam robotic ga repeat cheyakudadu.
- H2 headings 4-8 words — familiar English label + clear benefit (e.g. "Eligibility & Age Limit వివరాలు", "Apply Online: Step-by-Step Process").
- Prathi <li> step 10 words lo complete avvali (Rank Math "short list items" check — long steps FAIL avthayi).
- Table cells lo words matrame (sentences kaadu); prathi cell 2-6 words.
- Title 40-60 chars — focus keyword MODALO + year + number + power word (Complete/Best/Easy/Top).

VALUE-ADD — source notice ni mirror cheyyakundu (Google scaled-content rule):
- Job/notification posts: recruitment object fill cheyandi — apply_end = notice lo unna EXACT last date (YYYY-MM-DD; lekapote khali vadi, GUESS cheyyakundu), org_name/org_url official, salary_min/max real pay-band matrame, identifier = notification number.
- H2s students phone lo adigina colloquial prashnalu laga: "Apply ela cheyali?", "Fee emiti?", "Eligibility enti?", "Selection ela?" (Telugu+English mix okati okka style).
- Salary/vacancy ki table; last date unte paragraph lo "ippude apply cheste" type urgency (bot countdown badge automatic ga add chesthundi).
- Prathi post ki value-add okkamaina undali: plain-language eligibility explain, important dates summary, related previous-exam links section — kevalam notice rephrase kaadu.
- Secondary keywords natural ga body lo (stuffing kaadu) — ee phrases Google lo related searches ga vastayi.
"""

# v85: JSON SCHEMA CONTRACT — prompts "return valid JSON" annayi kaani KEY
# NAMES eppudu cheppaledu (content_html guess → Empty-field fails!). Ippudu
# prathi generation prompt chivara ee contract veltundi (both call sites).
JSON_SCHEMA_CONTRACT = """
OUTPUT FORMAT — Return ONLY valid JSON (no markdown, no fences, no commentary).
EXACT keys (spellings marakudadu — bot idi parse chestundi):
{
  "title": "SEO Telugu+English title, 40-70 chars",
  "slug": "english-kebab-case-max-60-chars",
  "meta_description": "140-160 chars Telugu summary with focus keyword",
  "content_html": "FULL article HTML here (h2/h3/p/ul/ol/li/table/a only). THIS key holds the article body — 'content'/'html'/'body' vaddu, 'content_html' matrame.",
  "focus_keyword": "ONE exact search phrase",
  "secondary_keywords": ["related phrase 1", "related phrase 2", "related phrase 3"],
  "seo_title": "keyword-first title under 60 chars",
  "tags": ["tag1", "tag2", "tag3", "tag4", "tag5"],
  "banner_text": "ENGLISH banner max 6 words",
  "quick_answer": "40-60 word Telugu direct answer with focus keyword",
  "faq": [{"question": "Telugu question?", "answer": "2-3 sentence Telugu answer."}],
  "external_links": [{"url": "https://official-portal.gov.in", "text": "Telugu anchor"}],
  "recruitment": {"org_name": "ORG (ONLY if source states)", "org_url": "https://...", "apply_end": "YYYY-MM-DD or empty", "location": "city/state or empty"}
}
Rules: content_html KHALI vaddu (600+ useful words when the topic supports it). Do not pad, repeat or invent facts for length. faq 4+ items. recruitment facts source lo LEKAPOTE {"org_name": "", "apply_end": ""} — GUESS cheyyakundu.
"""

def _key_tag(key: str) -> str:
    import hashlib

    return hashlib.sha1((key or "none").encode()).hexdigest()[:6]


def _api_keys() -> List[str]:
    keys = list(getattr(config, "GEMINI_API_KEYS", []) or [])
    if config.GEMINI_API_KEY and config.GEMINI_API_KEY not in keys:
        keys.append(config.GEMINI_API_KEY)
    return keys


def _usable_keys() -> List[str]:
    """v18: RPD budget + daily dead-flag based key rotation (429 safe)."""
    keys = _api_keys()
    if len(keys) <= 1:
        # unset key (mock/tests) — loop kenanga [None] return (key or GEMINI_API_KEY)
        return keys or [None]
    import hashlib
    from datetime import date

    from . import state

    today = date.today().isoformat()
    out = []
    for k in keys:
        kh = hashlib.sha1(k.encode()).hexdigest()[:8]
        try:
            if state.meta_get(config.STATE_PATH, f"gemkey:dead:{kh}:{today}"):
                continue
            n = int(state.meta_get(config.STATE_PATH, f"gemkey:cnt:{kh}:{today}") or 0)
            if n < config.GEMINI_RPD_PER_KEY:
                out.append((n, k))
        except Exception:
            out.append((0, k))
    if not out:
        return keys  # anni exhausted — aa again try (counter broken aiy unchu)
    out.sort()  # usage takkuva key mundu
    return [k for _, k in out]


def _bump_key(key: str) -> None:
    import hashlib
    from datetime import date

    from . import state

    if not key:
        return
    kh = hashlib.sha1(key.encode()).hexdigest()[:8]
    today = date.today().isoformat()
    try:
        n = int(state.meta_get(config.STATE_PATH, f"gemkey:cnt:{kh}:{today}") or 0)
        state.meta_set(config.STATE_PATH, f"gemkey:cnt:{kh}:{today}", str(n + 1))
    except Exception as exc:  # noqa: BLE001 — best-effort (silent kaadu)
        log.debug("gemini_client._bump_key skip: %s", exc)


def _mark_key_dead(key: str, reason: str) -> None:
    import hashlib
    from datetime import date

    from . import state

    if not key:
        return
    kh = hashlib.sha1(key.encode()).hexdigest()[:8]
    today = date.today().isoformat()
    try:
        state.meta_set(config.STATE_PATH, f"gemkey:dead:{kh}:{today}",
                       reason[:80])
    except Exception as exc:  # noqa: BLE001 — best-effort (silent kaadu)
        log.debug("gemini_client._mark_key_dead skip: %s", exc)
    log.warning("Gemini key ..%s marked for cooldown today (%s)", kh, reason[:60])


def _call_model(model: str, prompt: str, key: Optional[str] = None) -> str:
    key = key or config.GEMINI_API_KEY
    # v17.1: Telugu JSON 8192 tokens lo truncate avtundi — 2.5 models ki
    # 32k + thinking OFF; 2.0/1.5 flash max output 8192 (clamp — leda 400)
    max_out = config.GEMINI_MAX_OUTPUT_TOKENS
    if "2.5" in model:
        max_out = min(max_out, 65536)
    else:
        max_out = min(max_out, 8192)
    gen_config = {
        "temperature": 0.95,
        "topP": 0.95,
        "maxOutputTokens": max_out,
        "responseMimeType": "application/json",
        "responseSchema": RESPONSE_SCHEMA,
    }
    if "2.5" in model:
        # 2.5 thinking default ON — thinking tokens output budget tintayi -> OFF
        gen_config["thinkingConfig"] = {"thinkingBudget": 0}
    payload = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": gen_config,
    }
    url = API_URL.format(model=model)
    resp = requests.post(
        url,
        params={"key": key},
        json=payload,
        timeout=config.HTTP_TIMEOUT,
    )
    if resp.status_code == 429:
        raise GeminiError(f"QUOTA_KEY:{_key_tag(key)}:429")
    if resp.status_code in (400, 403) and (
            "quota" in resp.text.lower()
            or "resource has been exhausted" in resp.text.lower()):
        raise GeminiError(f"QUOTA_KEY:{_key_tag(key)}:{resp.status_code}")
    if resp.status_code in (400, 403) and (
            "api key not valid" in resp.text.lower()
            or "permission denied on resource project" in resp.text.lower()):
        raise GeminiError(f"BAD_KEY:{_key_tag(key)}")
    if resp.status_code == 404 or (resp.status_code == 400 and "not found" in resp.text.lower()):
        raise GeminiError(f"MODEL_NOT_FOUND:{model}")
    if resp.status_code == 429 or resp.status_code >= 500:
        raise GeminiError(f"RETRYABLE:{resp.status_code}:{resp.text[:200]}")
    if resp.status_code != 200:
        raise GeminiError(f"HTTP {resp.status_code}: {resp.text[:300]}")
    data = resp.json()
    try:
        cand = data["candidates"][0]
    except (KeyError, IndexError) as exc:
        raise GeminiError(f"Unexpected API response shape: {data}") from exc
    finish = cand.get("finishReason", "")
    if finish == "MAX_TOKENS":
        raise GeminiError("TRUNCATED:MAX_TOKENS (output cut — shorter retry kavali)")
    try:
        return cand["content"]["parts"][0]["text"]
    except (KeyError, IndexError, TypeError) as exc:
        raise GeminiError(f"Empty response (finishReason={finish}): {str(data)[:200]}") from exc


def _generate_core(prompt: str, category: str = "", source=None,
                   strict_category: bool = False) -> Dict:
    """v18 core: keys × models loop, v17.1 adaptive truncation retry."""
    models = _models()
    last_err: Optional[Exception] = None
    shorten = False
    for attempt in range(1, config.GEMINI_MAX_RETRIES + 1):
        for model in models:
            for key in _usable_keys():
                try:
                    raw = _call_model(model, prompt, key)
                    article = _parse_json(raw)
                    for field in ("title", "slug", "meta_description", "content_html"):
                        if not article.get(field):
                            raise GeminiError(f"Empty field in response: {field}")
                    article["tags"] = [str(t).strip() for t in
                                       article.get("tags", []) if str(t).strip()][:8]
                    if strict_category:
                        article["category"] = category or "Online Education"
                    else:
                        article["category"] = (category
                                               or article.get("category", "Education News"))
                    article["model"] = model
                    if source is not None:
                        article["source_url"] = source.url
                        article["source_title"] = source.title
                    _bump_key(key)
                    return article
                except GeminiError as exc:
                    msg = str(exc)
                    if msg.startswith("MODEL_NOT_FOUND"):
                        log.warning("Model %s unavailable, trying fallback...", model)
                        break  # ee model ki keys varapadam prakasam ledu
                    if msg.startswith(("QUOTA_KEY", "BAD_KEY")):
                        _mark_key_dead(key, msg.split(":")[0])
                        last_err = exc
                        continue  # next key!
                    last_err = exc
                    if msg.startswith("TRUNCATED"):
                        shorten = True
                    break  # retryable -> next attempt
                except (json.JSONDecodeError, ValueError) as exc:
                    last_err = GeminiError(f"JSON parse failed: {exc}")
                    if any(k in str(exc) for k in
                           ("Unterminated", "Expecting", "Out of range")):
                        shorten = True
                    break
        if shorten and "LENGTH OVERRIDE" not in prompt:
            prompt += (
                "\n\nLENGTH OVERRIDE (output token limit davvindi — vinipistu): "
                "article ni 1400-1800 words lo COMPLETE ga rayandi. "
                "Anni sections, tables, FAQ keep — kani prathi section crisp ga "
                "(2-3 paragraphs). JSON ni 100% complete ga close cheyadam "
                "guarantee."
            )
        if attempt < config.GEMINI_MAX_RETRIES:
            time.sleep(min(45, 5 * (2 ** (attempt - 1))))
    hint = ""
    if isinstance(last_err, GeminiError) and str(last_err).startswith(("QUOTA", "BAD_KEY")):
        hint = (" — GEMINI_API_KEYS lo inka keys add cheyandi "
                "(free tier quota ayyipoyindi; .env lo comma tho separator)")
    raise GeminiError(f"All attempts failed: {last_err}{hint}")



def _parse_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        text = text.split("json", 1)[-1].strip()
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end != -1:
        text = text[start : end + 1]
    try:
        obj = json.loads(text)
    except json.JSONDecodeError:
        # v85: light repair — trailing commas + raw control chars
        # (LLM frequent slips; full-retry waste kakunda).
        fixed = re.sub(r",\s*([}\]])", r"\1", text)
        fixed = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", fixed)
        obj = json.loads(fixed)
    if isinstance(obj, dict):
        _normalize_keys(obj)
    return obj


# v85: key aliases — schema contract unna, models marustayi
# ("content"/"html"/"body"). Parse-time normalize → Empty-field fails taggayi.
_KEY_ALIASES = {
    "content_html": ("content", "html", "body", "article_html", "article_body",
                     "article_content", "contentHtml"),
    "meta_description": ("meta", "description", "metaDescription", "excerpt",
                         "meta_description_text"),
    "focus_keyword": ("focus", "keyword", "focusKeyword", "main_keyword"),
    "seo_title": ("seoTitle", "seo"),
    "banner_text": ("banner", "bannerText", "image_text"),
    "quick_answer": ("quickAnswer", "summary_answer", "snippet"),
    "secondary_keywords": ("secondaryKeywords", "related_keywords"),
    "external_links": ("externalLinks", "links", "sources_links"),
}


def _normalize_keys(obj: dict) -> None:
    for canon, aliases in _KEY_ALIASES.items():
        if obj.get(canon):
            continue
        for a in aliases:
            if obj.get(a):
                obj[canon] = obj.pop(a)
                break
    # faq items: {q,a} ↔ {question,answer} unify
    faq = obj.get("faq")
    if isinstance(faq, list):
        norm = []
        for item in faq:
            if isinstance(item, dict):
                q = item.get("question") or item.get("q") or ""
                a = item.get("answer") or item.get("a") or ""
                if q and a:
                    norm.append({"question": q, "answer": a})
            elif isinstance(item, (list, tuple)) and len(item) >= 2:
                norm.append({"question": item[0], "answer": item[1]})
        obj["faq"] = norm


def generate_article(
    category: str,
    recent_titles: List[str],
    year: int,
    avoid_extra: Optional[str] = None,
    trend_topic: str = "",
) -> Dict:
    """Generate one article dict. Raises GeminiError on failure.

    trend_topic: Google Trends nunchi vachina trending topic (optional) —
    aa topic meede article rastundi (fresh trending content).
    """
    if not config.gemini_configured():
        raise GeminiError("GEMINI_API_KEY not set")

    avoid_block = ""
    if recent_titles:
        sample = "\n".join(f"- {t}" for t in recent_titles[:40])
        avoid_block = (
            "DO NOT repeat any of these previously published titles or their topics "
            "(write about something DIFFERENT):\n" + sample
        )
    if avoid_extra:
        avoid_block = (avoid_block + "\n" + avoid_extra).strip()

    prompt = PROMPT_TEMPLATE.format(
        category=category,
        seed_hint=CATEGORY_SEEDS.get(category, "general education topics for Indian students"),
        year=year,
        avoid_block=avoid_block,
    )
    prompt += _story_brief(f"{category} {trend_topic}")
    if trend_topic:
        # Google Trends real-time topic — searches ekkuvuntayi, rank fast
        prompt += (
            "\n\nTRENDING NOW (Google Trends India): \"" + trend_topic + "\"\n"
            "Write THE article on this exact trending topic (mana style lo, "
            "Telugu+English mix, ee category: " + category + "). "
            "Trend context ni mana education angle tho connect cheyandi."
        )

    prompt = prompt + WRITING_RULES + JSON_SCHEMA_CONTRACT  # v85 schema
    return _generate_core(prompt, category, strict_category=True)


def _generate_with_retries(prompt: str, category: str = "", source=None) -> Dict:
    """Common retry loop for all prompts. Returns article dict."""
    prompt = prompt + WRITING_RULES + JSON_SCHEMA_CONTRACT  # v85 schema
    return _generate_core(prompt, category, source=source)


REFINE_PROMPT_TEMPLATE = """You are a top Telugu SEO editor for studentup.in. Rank Math content analysis FAILED on the draft below. Fix ONLY the failing items and return the IMPROVED article — same topic, same facts, 100% original, natural spoken Telugu + English terms.

=============== CURRENT DRAFT ===============
TITLE: {title}
FOCUS KEYWORD: {kw}
META DESCRIPTION: {meta}
CONTENT (HTML):
{content}
==============================================

MUST FIX (item-by-item — Rank Math and evidence checks):
{fixes}

VERIFIED SOURCE EVIDENCE (use only this evidence; do not infer beyond it):
{source_evidence}

REWRITE RULES:
- Keep the draft's verified facts, but rewrite any repaired section in a fresh StudentUp voice; never copy a source-like sentence or preserve a source paragraph order.
- Keep language easy spoken Telugu + familiar English labels (Eligibility, Age Limit, Fee, Important Dates, Selection Process, Apply Online, Official Website). Avoid pure/formal Telugu and explain unfamiliar terms simply.
- Title 40-60 chars: focus keyword FIRST words + year + number + power word (Complete/Best/Easy/Top).
- meta_description 110-156 chars, focus keyword THO start.
- Focus keyword exact phrase ga: first paragraph + 2+ H2s + 8-14 times in body (0.5-3% density).
- Prathi <li> 10 words lo complete avvali — pedda steps ni split cheyandi.
- Prathi paragraph 2-3 sentences (120 words eravaddu). 300+ words unna section ki kotha <h2> add cheyandi.
- Sentences lo connectives 30%+ (kaani/అందువల్ల/మరోవైపు/అలాగే/చివరగా).
- Table (+1 ayna good), FAQ 3+ questions — maintain cheyandi.
- Facts marchakundu. Never add a missing fee, eligibility, vacancy, date, salary or step from memory; remove unsupported claims or write that the source does not state it.
- recruitment object (org_name/apply_end/salary) unte source evidence tho matrame maintain cheyandi — dates GUESS cheyyakundu.
Return ONLY valid JSON (same schema)."""


def refine_article(
    article: Dict,
    fixes: List[str],
    source_evidence: str = "",
) -> Dict:
    """Correct SEO/evidence issues without inventing facts."""
    if not config.gemini_configured():
        raise GeminiError("GEMINI_API_KEY not set")
    prompt = REFINE_PROMPT_TEMPLATE.format(
        title=article.get("title", ""),
        kw=article.get("focus_keyword", ""),
        meta=article.get("meta_description", ""),
        # v85: 12000 → lengthy posts sections LLM chudakunda poyayi
        content=(article.get("content_html") or "")[:20000],
        fixes="\n".join(f"- {f}" for f in fixes[:12]),
        source_evidence=(source_evidence or "No extra source evidence supplied; remove any unsupported claim.")[:12000],
    )
    improved = _generate_core(prompt, article.get("category", ""),
                              strict_category=True)
    # identity stable ga undali — slug/url marchakudadu (internal links break avutayi)
    improved["slug"] = article.get("slug") or improved.get("slug", "")
    return improved


def generate_article_from_source(
    source,
    recent_titles: List[str],
    year: int,
    extras: Optional[List] = None,
    competitor_titles: Optional[List[str]] = None,
    notebooklm_brief: str = "",
) -> Dict:
    """100% original rewrite from a SourceArticle (facts only, no copying).

    extras = additional research SourceArticles. They are used only for
    source-backed context and fact checking; the model must not copy or
    mechanically combine competitor pages.
    """
    if not config.gemini_configured():
        raise GeminiError("GEMINI_API_KEY not set")

    avoid_block = ""
    if recent_titles:
        sample = "\n".join(f"- {t}" for t in recent_titles[:30])
        avoid_block = ("Also make sure your new TITLE is different from these "
                       "already-published titles:\n" + sample)

    if extras:
        prompt = RESEARCH_PROMPT_TEMPLATE.format(
            url=source.url,
            site=source.site_name,
            src_title=source.title,
            src_text=source.text or "(text extraction takkuva — title base ga rayandi)",
            extra_sources_block=_format_extra_sources(extras),
            year=year,
        )
    else:
        prompt = REWRITE_PROMPT_TEMPLATE.format(
            url=source.url,
            site=source.site_name,
            src_title=source.title,
            src_text=source.text or "(text extraction takkuva — title base ga rayandi)",
            year=year,
        )
    prompt += _story_brief(f"{source.title} {getattr(source, 'category', '')}")
    if avoid_block:
        prompt += "\n" + avoid_block
    if notebooklm_brief:
        prompt += (
            f"\nTARGET-YEAR DATE POLICY: This draft is for the {year} cycle. "
            f"Do not carry a date, fee, vacancy, eligibility rule or deadline "
            f"from another year into {year} unless a cited source explicitly "
            f"says it applies. If {year} information is not officially available, "
            "state that clearly instead of predicting it.\n"
            "EDITOR-VERIFIED NOTEBOOKLM BRIEF (use as a cited outline, not as "
            "copy):\n"
            + notebooklm_brief[:18000]
            + "\nKeep Claim IDs/citations available to the human editor. Verify "
              "each claim against the supplied source passages and rewrite "
              "everything in an independent Telugu voice.\n"
        )
    if competitor_titles:
        prompt += (
            "\nSEARCH-LANGUAGE REFERENCE — related result titles ivi; user language "
            "and intent understand cheyadaniki matrame use cheyandi:\n"
            + "\n".join(f"- {t}" for t in competitor_titles[:8])
            + "\n(Exact wording, structure or distinctive hook copy cheyakandi; "
              "reader-first independent title create cheyandi.)"
        )
    return _generate_with_retries(prompt, source=source)
