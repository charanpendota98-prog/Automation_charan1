"""v122 safe AI-thumbnail prompt checks."""
from autoblog.thumbnail_prompt import build_prompt

prompt = build_prompt({
    "title": "SSC CGL 2026 – 1200+ Vacancies – Apply Online",
    "category": "Central Govt Jobs",
})
assert "1200+" in prompt
assert "no text baked into the image" in prompt.lower()
assert "no invented date" in prompt.lower()
assert "Indian central government recruitment theme" in prompt
print("thumbnail prompt tests: PASS")
