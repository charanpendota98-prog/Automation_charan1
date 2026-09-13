"""v36 NotebookLM-ready evidence bundle tests."""

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from autoblog import research_brief, validator  # noqa: E402
from autoblog.sources import SourceArticle  # noqa: E402


def main():
    print("v36 NOTEBOOKLM SOURCE-GROUNDING TESTS:")
    articles = [
        SourceArticle(
            url="https://official.gov.in/notice",
            title="Official notification",
            site_name="Official Portal",
            meta_description="Official details",
            text=("The last date is 15 October 2026. The fee is Rs 100. "
                   "Candidates must check the official eligibility notice."),
        ),
        SourceArticle(
            url="https://university.example/guide",
            title="Student guide",
            site_name="University",
            text=("The application process includes document verification. "
                  "The official portal should be checked for current updates."),
        ),
    ]
    bundle = research_brief.build_source_bundle("Test notification", articles)
    assert "S1" in bundle and "S2" in bundle
    assert "15 October 2026" in bundle and "official.gov.in" in bundle
    prompt = research_brief.notebooklm_prompt("Test notification", articles)
    for phrase in ("source map", "fact ledger", "conflict", "gap", "Claim ID",
                   "Do not copy", "open every citation"):
        assert phrase.lower() in prompt.lower(), phrase
    assert "private NotebookLM" not in prompt
    valid_brief = ("## Fact ledger\nClaim ID C1 — date — S1 citation\n"
                   "Claim ID C2 — process — S2 citation\n"
                   "## Conflict audit\nNo unresolved conflicts.\n" + "verified context " * 50)
    check = research_brief.validate_editor_brief(
        valid_brief, [item.url for item in articles])
    assert check["ok"] and check["claims"] == 2, check
    assert not research_brief.validate_editor_brief("uncited summary", ["a", "b"])["ok"]
    copied = "This exact sentence has enough words to trigger the long phrase guard in the source."
    assert validator.verbatim_overlaps(copied, [copied])
    print("  1. labelled source bundle + five-pass cited prompt + copy guard ✔")

    with tempfile.TemporaryDirectory() as tmp:
        result = research_brief.write_bundle("Test notification", articles, Path(tmp))
        for key in ("bundle", "prompt", "manifest"):
            assert Path(result[key]).exists(), key
        manifest = json.loads(Path(result["manifest"]).read_text(encoding="utf-8"))
        assert manifest["notebooklm_required"] is True
        assert len(manifest["sources"]) == 2
    print("  2. ignored bundle files + manifest written safely ✔")
    print("ALL v36 TESTS PASSED ✔")


if __name__ == "__main__":
    main()
