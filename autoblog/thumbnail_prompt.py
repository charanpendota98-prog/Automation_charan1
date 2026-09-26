# -*- coding: utf-8 -*-
"""Prompt builder for an optional Gemini/image-capable thumbnail model.

The model creates only the visual background/subject. Exact Telugu/English
headline, vacancy count, date and logo are rendered by StudentUp after the
image returns; image models frequently misspell small text and must not be
allowed to invent a deadline or organisation mark.
"""
from __future__ import annotations

import html
import re
from typing import Dict

STYLE = """Create a premium 16:9 editorial news thumbnail background for StudentUp,
1200 by 675 pixels, made for a Telugu student jobs website. Use a bold modern
Indian news-card composition: deep navy and royal blue base, controlled saffron
and red accents, bright white contrast, strong depth, clean lighting, crisp
subject separation, subtle glass panels, and safe empty space for a headline
overlay. Make it energetic and trustworthy, not sensational or clickbait.
Use one relevant realistic subject or a tasteful 2-3 element collage, with the
main subject on the right or left according to the composition. Keep faces,
uniforms, buildings and documents natural and sharp. No watermark, no random
website name, no fake government seal, no fake number, no invented date, no
competitor logo, no tiny unreadable text, and no text baked into the image.
The returned image must be clean because StudentUp will render the verified
headline and facts in a separate safe overlay."""

CATEGORY_SCENES = {
    "TS Govt Jobs": "Telangana government employment theme: Hyderabad civic/administrative building, official-looking document folder, subtle Telangana-inspired color accent; do not invent a seal.",
    "AP Govt Jobs": "Andhra Pradesh government employment theme: professional administrative building, official-looking application document and student-ready desk; no invented seal or text.",
    "Central Govt Jobs": "Indian central government recruitment theme: disciplined uniformed public-service candidate or railway/office recruitment scene, Indian tricolour accent used subtly; no invented insignia.",
    "Software Jobs": "Modern software recruitment theme: confident young developer at a clean workstation, code glow kept abstract and unreadable, laptop and cloud/data visual cues, premium blue-cyan lighting.",
    "Private Jobs": "Private-sector recruitment theme: diverse young professionals in a modern office, interview or onboarding atmosphere, premium corporate blue and orange lighting.",
    "Walkin Jobs": "Walk-in interview theme: organised interview desk, candidate holding a resume, simple venue sign with no readable text, friendly professional atmosphere.",
    "Scholarships": "Scholarship theme: focused student with books and application folder, education campus/library setting, hopeful but realistic, blue and gold accents.",
    "Results": "Exam results theme: happy student checking a result on a laptop, abstract score/result sheet with all text unreadable, celebratory but trustworthy.",
    "Hall Tickets": "Hall-ticket theme: student holding an admit-card document near an exam centre, document text intentionally unreadable, calm blue academic setting.",
    "Current Affairs": "Daily current-affairs theme: newspaper, globe, public-policy desk and competitive-exam notebook, clean editorial newsroom lighting.",
}


def _clean(value: object, limit: int = 180) -> str:
    text = html.unescape(re.sub(r"<[^>]+>", " ", str(value or "")))
    return re.sub(r"\s+", " ", text).strip()[:limit]


def build_prompt(article: Dict) -> str:
    """Build a safe, evidence-neutral visual prompt from article metadata."""
    article = article or {}
    category = _clean(article.get("category") or "Student Jobs", 50)
    scene = CATEGORY_SCENES.get(category, "clean student opportunity and education-news scene")
    title = _clean(article.get("title") or "StudentUp opportunity", 140)
    # These are context hints for composition only; exact facts are overlaid
    # after generation from the structured, verified article object.
    return (
        f"{STYLE}\n\nCATEGORY SCENE:\n{scene}\n\n"
        f"ARTICLE CONTEXT FOR VISUAL MOOD ONLY (do not render text): {title}\n"
        f"CATEGORY LABEL FOR MOOD ONLY: {category}\n\n"
        "COMPOSITION: reserve a wide uncluttered central safe band and a clean "
        "lower panel area for post-processing. Avoid faces or important objects "
        "in the central text-safe area. No letters, words, dates, vacancy counts "
        "or logos should be generated inside the artwork."
    )
