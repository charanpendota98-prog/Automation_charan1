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

ARTICLE STRUCTURE (HTML):
- 2-3 intro paragraphs (no heading).
- Then <h2> sections covering: overview/key details, eligibility, benefits/important points, step-by-step "how to apply / how to check" as <ul><li> lists, useful tips.
- Use <strong> for key phrases; include one simple <table> (3-5 rows) if a comparison or summary table fits naturally.
- End with a short conclusion paragraph and then an FAQ section: 3 <h3> questions each followed by a short answer paragraph.
- Final paragraph: a friendly call-to-action in Telugu asking readers to share the article and ask doubts in comments.
- Total length: roughly 800-1200 words. Use ONLY these HTML tags: h2 h3 p ul ol li strong em table thead tbody tr th td a. No <html>/<head>/<body>, no markdown, no code fences.

ALSO RETURN:
- slug: English kebab-case URL slug for this post ( transliterate the topic, e.g. "ssc-cgl-preparation-guide" ), max 60 chars, lowercase, hyphens only.
- meta_description: 140-160 characters Telugu summary for SEO.
- tags: 5 to 8 tags, mix of Telugu and English keywords.
- banner_text: short ENGLISH text (max 6 words) suitable for a featured image banner, e.g. "Scholarships 2026 Apply Online".

Return ONLY valid JSON matching the schema."""


class GeminiError(Exception):
    pass


def _models() -> List[str]:
    models = [config.GEMINI_MODEL] + [
        m for m in config.GEMINI_FALLBACK_MODELS if m != config.GEMINI_MODEL
    ]
    return models


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
