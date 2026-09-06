"""Topic engine: picks the next category to write about.

Strategy: least-recently-used categories first, with a bit of randomness,
so all site sections get steady coverage.

Also provides a mock generator so the full pipeline can be tested
without a Gemini API key (see `run.py --mock`).
"""

import random
import sqlite3
from collections import Counter
from pathlib import Path
from typing import List

from . import config

MOCK_TOPICS = [
    ("Scholarships", "NSP Scholarship 2026 – National Scholarship Portal lo Apply elaa cheyali"),
    ("Govt Jobs", "SSC MTS 2026 – Complete Preparation Guide Telugu lo"),
    ("Exam Updates", "Admit Card Download elaa cheyali – Step by Step Guide"),
    ("Admissions", "TS EAMCET 2026 Counselling – Web Options Priority Tips"),
    ("Study Tips", "Revision Time Table Plan – Exam Mundu 30 Rojulu"),
    ("Internships", "AICTE Internship Portal 2026 – Students ki Free Opportunities"),
    ("Results", "Revaluation vs Recounting – Difference emito Telugu lo"),
    ("Education News", "SWAYAM & NPTEL Free Courses – Certificate Value emito"),
]

# Trending listicle ("stories") ideas — Adda247 style, rotate avtayi
LISTICLE_IDEAS = [
    "Top 10 Central Government Jobs",
    "Top 10 Sarkari Jobs Without Exam",
    "Top 7 Scholarships for Telugu Students",
    "Top 8 Government Internships for Students",
    "Top 5 Railway Jobs for 12th Pass",
    "Top 10 Work From Home Jobs for Students",
    "Top 7 Free Online Courses with Certificates",
    "Top 9 Highest Paying Government Jobs",
    "Top 6 Bank Jobs After Degree",
    "Top 5 Defence Jobs After Intermediate",
    "Top 8 Study Apps for Competitive Exams",
    "Top 7 Websites for Free Government Job Alerts",
    "Top 10 Skills Students ki 2026 lo Necessity",
    "Top 6 Part Time Jobs for College Students",
    "Top 5 SSC Exams After Degree",
    "Top 7 Telangana Government Schemes for Students",
]


def pick_listicle_idea(recent_titles=None) -> str:
    recent = set(t.lower() for t in (recent_titles or []))
    for _ in range(len(LISTICLE_IDEAS) * 3):
        idea = random.choice(LISTICLE_IDEAS)
        if not any(idea.lower() in t for t in recent):
            return idea
    return random.choice(LISTICLE_IDEAS)


def mock_listicle(topic: str, index: int = 0) -> dict:
    items = [
        ("SSC CGL", "Level-6 pay, graduation tho apply"),
        ("IBPS PO", "Banking lo top job"),
        ("RRB NTPC", "Railway central jobs"),
        ("UPSC CSE", "Top civil service"),
        ("LIC AAO", "Insurance sector"),
    ]
    sections = "".join(
        f"<h2>{i}. {name} – {hook}</h2><p>{name} gurinchi details para. "
        f"Eligibility and process ikkada untundi.</p>"
        f"<ul><li>Qualification: Degree</li><li>Pay: {hook}</li></ul>"
        for i, (name, hook) in enumerate(items, 1)
    )
    return {
        "title": f"{topic} 2026 – Complete List Telugu lo (Top 5)",
        "slug": "test-listicle-" + str(index),
        "meta_description": f"{topic} 2026 — Telugu lo complete top list, salary, eligibility antha oke chote.",
        "tags": ["Top 10", "2026", "Govt Jobs", "Telugu", "Students", "List"],
        "banner_text": "Top Jobs 2026 List",
        "content_html": (
            f"<p>{topic} 2026 gurinchi mana complete list — Telugu students ki "
            "ekkuva useful ga untundi.</p><p>Ee list lo prathi item details "
            "ikkaada unnayi.</p>" + sections +
            "<h2>Comparison Table</h2><table><thead><tr><th>Job</th><th>Pay</th></tr></thead>"
            "<tbody><tr><td>SSC CGL</td><td>Level-6</td></tr></tbody></table>"
            "<h2>FAQ</h2><h3>Q1?</h3><p>A1</p><h3>Q2?</h3><p>A2</p>"
            "<h3>Q3?</h3><p>A3</p>"
        ),
        "category": "Govt Jobs",
        "model": "mock",
        "focus_keyword": topic,
        "secondary_keywords": [topic + " list", "top jobs telugu"],
        "quick_answer": f"{topic} 2026 — mana top list lo best options ikkada.",
        "faq": [{"question": "Q1?", "answer": "A1"}, {"question": "Q2?", "answer": "A2"}],
        "external_links": [{"text": "SSC Official", "url": "https://ssc.gov.in"}],
        "article_type": "listicle",
        "list_items": [name for name, _ in items],
    }

MOCK_ARTICLE_HTML = """<p>EE article lo manam {topic} gurinchi complete ga telusukuntamu. Students ki ee information chala useful ga untundi — mundu basics nunchi start cheddam.</p>
<h2>Key Details</h2>
<ul><li><strong>Eligibility:</strong> Indian students ki apply cheyochu.</li><li><strong>Process:</strong> motham online lo jarugutundi.</li><li><strong>Fee:</strong> chala schemes lo application free.</li></ul>
<h2>Elaa Apply Cheyali</h2>
<ol><li>Official website open cheyandi.</li><li>Registration form fill cheyandi.</li><li>Documents upload cheyandi.</li><li>Submit chesi acknowledgement save cheyandi.</li></ol>
<h2>Important Tips</h2>
<p><strong>Tip:</strong> official notificationcarefully chadivi, deadline mundu apply cheyandi. Ee information meeku useful ga undi ante, meе friends tho share cheyandi.</p>
<h3>FAQ 1: Ee process elaa start cheyali?</h3>
<p>Mundhe cheppinattu official website lo registration cheyali.</p>
<h3>FAQ 2: Documents em kavali?</h3>
<p>Aadhaar, marksheets, bank details mainly kavali.</p>
<h3>FAQ 3: Help em kavali ayite?</h3>
<p>Comments lo adagandi — mana team reply chestaru.</p>"""


def pick_category(db_path: Path) -> str:
    """Pick next category weighted towards least-used ones."""
    try:
        conn = sqlite3.connect(str(db_path))
        rows = conn.execute(
            "SELECT category, COUNT(*) c FROM posts GROUP BY category"
        ).fetchall()
        conn.close()
        counts = Counter({r[0]: r[1] for r in rows})
    except sqlite3.Error:
        counts = Counter()

    weighted: List[str] = []
    for cat in config.CATEGORIES:
        # fewer posts -> more tickets; +1 so new categories appear immediately
        tickets = max(1, 20 - min(19, counts.get(cat, 0)))
        weighted.extend([cat] * tickets)
    return random.choice(weighted)


def mock_article(category: str, index: int) -> dict:
    """Offline article generator for testing (no API key needed)."""
    cat, topic = MOCK_TOPICS[index % len(MOCK_TOPICS)]
    category = category or cat
    title = f"{topic} – {category} Guide 2026"
    slug = "test-" + category.lower().replace(" ", "-") + "-" + str(index)
    return {
        "title": title,
        "slug": slug,
        "meta_description": f"{category} gurinchi Telugu lo complete guide 2026. Steps, eligibility, tips antha oke chote.",
        "tags": [category, "2026", "Students", "Telugu", "Guide"],
        "banner_text": f"{category} 2026 Guide",
        "content_html": MOCK_ARTICLE_HTML.format(topic=topic),
        "category": category,
        "model": "mock",
    }
