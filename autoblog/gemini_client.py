"""Gemini API client — generates Telugu blog articles via REST (no SDK).

Uses the generateContent REST endpoint with a strict JSON response schema.
Automatically falls back to older model names if the primary one 404s,
and retries with backoff on rate limits.
"""

import json
import logging
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
}

PROMPT_TEMPLATE = """You are an expert Telugu education-content writer for the website studentup.in (Telugu students audience: scholarships, govt jobs, exam updates, admissions, study tips).

CATEGORY: {category}

TASK: Write ONE original, SEO-friendly blog post for this category. Choose a fresh, specific topic yourself (for example: "{seed_hint}" an issue, scheme, process, or guide related to the category). The current year is {year} — you may use it in the title when relevant.

{avoid_block}

LANGUAGE STYLE (very important):
- Write the article in TELUGU SCRIPT, naturally mixing common English terms (scholarship, application, official website, eligibility, deadline, online, link, etc.) exactly like Telugu news/education sites do.
- Title: catchy, Telugu + English mix, SEO friendly, roughly 40-70 characters. Include the year {year} if the topic suits it.

ACCURACY RULES (very important):
- Mention only REAL, well-known exams/schemes/portals. Do NOT invent new scheme names, fake vacancy numbers, fake dates or fake deadlines.
- Do NOT state specific application dates or deadlines. Instead write guidance like "official website lo latest notification check cheyandi" (in Telugu).
- Structure the post as a helpful evergreen guide/update that stays useful.
- COMMERCIAL DEPTH (important): wherever natural, include fee/salary/stipend/loan/cost details and comparison angles — this commercial information attracts relevant high-value ads and reader interest.

ARTICLE STRUCTURE (HTML):
- 2-3 intro paragraphs (no heading).
- Then <h2> sections covering: overview/key details, eligibility, benefits/important points, step-by-step "how to apply / how to check" as <ul><li> lists, useful tips.
- Use <strong> for key phrases; include one simple <table> (3-5 rows) if a comparison or summary table fits naturally.
- End with a short conclusion paragraph and then an FAQ section: 3 <h3> questions each followed by a short answer paragraph.
- Final paragraph: a friendly call-to-action in Telugu asking readers to share the article and ask doubts in comments.
- Total length: roughly 800-1200 words. Use ONLY these HTML tags: h2 h3 p ul ol li strong em table thead tbody tr th td a. No <html>/<head>/<body>, no markdown, no code fences.

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
- Do NOT copy any sentence, phrase structure, or paragraph from the source.
- Use ONLY the FACTS/information from the source (scheme names, eligibility, process, numbers).
- Everything must be freshly written by you in a completely different structure and wording.
- Write it as if you are an independent expert explaining the topic from scratch.

IMPROVE & EXPAND (advanced content — very important):
- ADD extra valuable sections the source may not have: detailed step-by-step process, required documents list, common mistakes to avoid, pro tips, comparison table, extra background context.
- Total length: 1800-2500 words — richer and more useful than the source.
- LANGUAGE: TELUGU SCRIPT with natural English terms mixed (scholarship, apply, eligibility, official website...) like Telugu news sites.

ACCURACY RULES:
- Keep only facts from the source + well-known real information. Do NOT invent dates/deadlines/vacancy numbers beyond what the source states.
- Official website links: mention only well-known real portals.

ARTICLE STRUCTURE (HTML only — h2 h3 p ul ol li strong em table thead tbody tr th td a):
- 2-3 intro paragraphs (focus keyword in FIRST paragraph).
- <h2> sections: overview, eligibility/details, benefits, step-by-step how to apply/check (as lists), documents required, tips & common mistakes, one <table> summary.
- Conclusion paragraph + FAQ section (4 <h3> questions with answers).
- End with a Telugu call-to-action (share + comment).

ALSO RETURN (same JSON schema):
- title: SEO Telugu+English title, 50-70 chars, focus keyword at start, year {year} if relevant.
- slug, meta_description (keyword included, 140-160 chars), tags (5-8), banner_text (English, max 6 words).
- focus_keyword: ONE main keyword phrase — in title, first para, 2+ h2 headings, ~1% density.
- seo_title: keyword at start, under 60 chars, year + power word.
- external_links: 1-3 real official portals for this topic with Telugu anchor text.

Return ONLY valid JSON."""


RESEARCH_PROMPT_TEMPLATE = """You are a top-level Telugu SEO content strategist for studentup.in (education/jobs/scholarships site).

TASK: Below are MULTIPLE research sources about the SAME topic/notification. Merge ALL their facts and write ONE definitive, 100% ORIGINAL article that is BETTER and MORE COMPLETE than every single source — so it can outrank them all on Google.

=============== PRIMARY SOURCE (user's URL — main base) ===============
URL: {url} | SITE: {site}
TITLE: {src_title}
CONTENT:
{src_text}
=======================================================================
{extra_sources_block}
STRICT ORIGINALITY RULES (copyright safe — very important):
- Do NOT copy any sentence/phrase from ANY source. Facts only, fresh original writing.
- Write as an independent expert explaining the topic from scratch.
- If sources CONFLICT on a number/date, use the most repeated/official value and phrase it as "notification prakaram" (as per notification).

MERGE & BEAT STRATEGY (very important):
- Start from the PRIMARY source's facts, then ADD every useful fact the other sources have that primary misses (extra eligibility points, fee details, salary, selection stages, documents, dates mentioned).
- Include everything a reader could want: overview, eligibility, benefits/salary, application steps, documents, fee, selection process, important tips, common mistakes, comparison table, key dates table (only if in sources).
- Total length: 2200-3000 words. Short paragraphs (2-3 sentences), transition words — top readability.
- COMMERCIAL DEPTH: include salary/fee/stipend/loan/cost figures (only well-known real values, pay matrix levels) and comparison tables — attracts high-value relevant ads.
- LANGUAGE: TELUGU SCRIPT with natural English terms (scholarship, apply, eligibility, official website, vacancy, notification...) like Telugu news sites.

ARTICLE STRUCTURE (HTML only — h2 h3 p ul ol li strong em table thead tbody tr th td a):
- 2-3 intro paragraphs (focus keyword in FIRST paragraph).
- <h2> sections for each major area + step-by-step process as lists + at least one <table>.
- Conclusion + FAQ (<h3> questions — must match the faq JSON you return).

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
        "ADDITIONAL RESEARCH SOURCES (competitors — merge their EXTRA facts):\n"
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
- LANGUAGE: same TELUGU + English mix style as the existing article.
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
- LANGUAGE: TELUGU SCRIPT + natural English terms, Adda247/Telugu news style — engaging, short paragraphs, strong hooks.
- focus_keyword: the list topic itself (e.g. "Central Government Jobs 2026") — in title, first para, 2+ h2s.
- list_items: return the N item names as an array (same as your h2 items, short names).
- Title format: "Top N {topic} 2026 – Complete List Telugu lo" style, 55-80 chars, number included.
- tags/banner_text/seo_title/quick_answer/faq/external_links: same rules as before.

Return ONLY valid JSON."""


def generate_listicle(topic: str, recent_titles: List[str], year: int) -> Dict:
    """Trending listicle article (Top 10 jobs lanti stories)."""
    if not config.GEMINI_API_KEY:
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


def generate_update(
    existing_title: str,
    existing_text: str,
    focus_keyword: str,
    extras: List,
    year: int,
) -> Dict:
    """Published article + kotha research -> improved version (same URL)."""
    if not config.GEMINI_API_KEY:
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
"""

def _call_model(model: str, prompt: str) -> str:
    payload = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.95,
            "topP": 0.95,
            "maxOutputTokens": 8192,
            "responseMimeType": "application/json",
            "responseSchema": RESPONSE_SCHEMA,
        },
    }
    url = API_URL.format(model=model)
    resp = requests.post(
        url,
        params={"key": config.GEMINI_API_KEY},
        json=payload,
        timeout=config.HTTP_TIMEOUT,
    )
    if resp.status_code == 404 or (resp.status_code == 400 and "not found" in resp.text.lower()):
        raise GeminiError(f"MODEL_NOT_FOUND:{model}")
    if resp.status_code == 429 or resp.status_code >= 500:
        raise GeminiError(f"RETRYABLE:{resp.status_code}:{resp.text[:200]}")
    if resp.status_code != 200:
        raise GeminiError(f"HTTP {resp.status_code}: {resp.text[:300]}")
    data = resp.json()
    try:
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError) as exc:
        raise GeminiError(f"Unexpected API response shape: {data}") from exc


def _parse_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        text = text.split("json", 1)[-1].strip()
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end != -1:
        text = text[start : end + 1]
    return json.loads(text)


def generate_article(
    category: str,
    recent_titles: List[str],
    year: int,
    avoid_extra: Optional[str] = None,
) -> Dict:
    """Generate one article dict. Raises GeminiError on failure."""
    if not config.GEMINI_API_KEY:
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

    models = _models()
    last_err: Optional[Exception] = None
    for attempt in range(1, config.GEMINI_MAX_RETRIES + 1):
        for model in models:
            try:
                raw = _call_model(model, prompt)
                article = _parse_json(raw)
                for field in ("title", "slug", "meta_description", "content_html"):
                    if not article.get(field):
                        raise GeminiError(f"Empty field in response: {field}")
                article["tags"] = [str(t).strip() for t in article.get("tags", []) if str(t).strip()][:8]
                article["category"] = category
                article["model"] = model
                return article
            except GeminiError as exc:
                msg = str(exc)
                if msg.startswith("MODEL_NOT_FOUND"):
                    log.warning("Model %s unavailable, trying fallback...", model)
                    continue
                last_err = exc
                break  # retryable error -> go to next attempt (with backoff)
            except (json.JSONDecodeError, ValueError) as exc:
                last_err = GeminiError(f"JSON parse failed: {exc}")
                break
        time.sleep(min(45, 5 * (2 ** (attempt - 1))))
    raise GeminiError(f"All attempts failed: {last_err}")


def _generate_with_retries(prompt: str, category: str = "", source=None) -> Dict:
    """Common retry loop for all prompts. Returns article dict."""
    prompt = prompt + WRITING_RULES
    models = _models()
    last_err: Optional[Exception] = None
    for attempt in range(1, config.GEMINI_MAX_RETRIES + 1):
        for model in models:
            try:
                raw = _call_model(model, prompt)
                article = _parse_json(raw)
                for field in ("title", "slug", "meta_description", "content_html"):
                    if not article.get(field):
                        raise GeminiError(f"Empty field in response: {field}")
                article["tags"] = [str(t).strip() for t in article.get("tags", []) if str(t).strip()][:8]
                article["category"] = category or article.get("category", "Education News")
                article["model"] = model
                if source is not None:
                    article["source_url"] = source.url
                    article["source_title"] = source.title
                return article
            except GeminiError as exc:
                msg = str(exc)
                if msg.startswith("MODEL_NOT_FOUND"):
                    log.warning("Model %s unavailable, trying fallback...", model)
                    continue
                last_err = exc
                break
            except (json.JSONDecodeError, ValueError) as exc:
                last_err = GeminiError(f"JSON parse failed: {exc}")
                break
        time.sleep(min(45, 5 * (2 ** (attempt - 1))))
    raise GeminiError(f"All attempts failed: {last_err}")


def generate_article_from_source(
    source,
    recent_titles: List[str],
    year: int,
    extras: Optional[List] = None,
    competitor_titles: Optional[List[str]] = None,
) -> Dict:
    """100% original rewrite from a SourceArticle (facts only, no copying).

    extras = additional research SourceArticles (internet lo dorikina
    same-topic competitor articles). Ivvi unte MERGE & BEAT prompt use
    avtundi — anni sources facts merge chesi super-complete article.
    """
    if not config.GEMINI_API_KEY:
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
    if avoid_block:
        prompt += "\n" + avoid_block
    if competitor_titles:
        prompt += (
            "\nKEYWORD INTELLIGENCE — Google lo ee topic meeda already top lo "
            "unna titles ivi (keyword research kosam — manam kante better "
            "title/keywords ravali):\n"
            + "\n".join(f"- {t}" for t in competitor_titles[:8])
            + "\n(Ee titles ni exact ga copy cheyakudadu — vatikante catchy & "
              "keyword-rich title manadi ravali.)"
        )
    return _generate_with_retries(prompt, source=source)
