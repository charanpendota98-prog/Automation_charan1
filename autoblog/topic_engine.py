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
