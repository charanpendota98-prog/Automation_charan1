"""v121 active-opportunity board/digest checks."""
from datetime import date

from autoblog.opportunity_digest import (
    compact_site_link,
    display_title,
    group_rows,
    is_active,
    render_digest,
    render_digest_messages,
)

TODAY = date(2026, 9, 26)

assert is_active("2026-09-26", TODAY)
assert not is_active("2026-09-25", TODAY)
assert is_active("", TODAY), "missing date must not be treated as expired"

rows = [
    {"id": 1, "title": "TSPSC Group 2", "link": "https://studentup.in/long-tspsc/",
     "date": "2026-09-26T05:00:00", "last_date": "2026-10-02",
     "category_slugs": ["ts-govt-jobs"]},
    {"id": 2, "title": "Expired notice", "link": "https://studentup.in/expired/",
     "date": "2026-09-25T05:00:00", "last_date": "2026-09-25",
     "category_slugs": ["ts-govt-jobs"]},
    {"id": 3, "title": "Hyderabad Job Mela", "link": "https://studentup.in/mela/",
     "date": "2026-09-26T06:00:00", "last_date": "",
     "category_slugs": ["walkin-jobs"]},
]
groups = group_rows(rows, TODAY, per_section=8)
assert len(groups["ts"]) == 1
assert len(groups["job-melas"]) == 1
assert compact_site_link("https://studentup.in", rows[0]) == "https://studentup.in/?p=1"
message = render_digest("https://studentup.in", rows, TODAY, per_section=8)
assert "Expired notice" not in message
assert "Last date:" not in message
assert "Not announced" not in message
assert "https://studentup.in/?p=1" in message
assert "Complete Details" not in display_title("SSC CGL – 1200+ Vacancies – Complete Details")
assert "Apply Online" not in display_title("TS Police Recruitment – Apply Online")
messages = render_digest_messages("https://studentup.in", rows, TODAY, per_section=8)
assert all(len(part) <= 3800 for part in messages)
assert any("https://studentup.in/?p=1" in part for part in messages)
print("opportunity digest tests: PASS")
