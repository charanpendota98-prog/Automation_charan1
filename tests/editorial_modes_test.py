#!/usr/bin/env python3
"""Strict no-filler and task-specific jobs/results/hall-ticket/story checks."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from autoblog import content_quality, gemini_client  # noqa: E402


def main():
    filler = content_quality.audit('<p>ఈ article మీకు నచ్చితే share చేయండి.</p>')
    assert filler["filler_hits"] == 1 and filler["flags"], filler
    live_sodi = content_quality.audit(
        '<p>ఇది ప్రతిష్టాత్మకమైన సువర్ణావకాశం. గొప్ప కెరీర్ అవకాశం.</p>')
    assert live_sodi["filler_hits"] == 3 and live_sodi["flags"], live_sodi

    modes = {
        "APPSC jobs notification": "JOB / RECRUITMENT",
        "TS Inter Result": "RESULT / MERIT LIST",
        "Group 2 Hall Ticket": "HALL TICKET / ADMIT CARD",
        "UPSC topper success story": "VERIFIED SUCCESS STORY",
    }
    for topic, marker in modes.items():
        brief = gemini_client._story_brief(topic)
        assert marker in brief, (topic, brief)
    story = gemini_client._story_brief("verified topper journey")
    assert "Never fabricate" in story and "refuse" in story

    source = Path("autoblog/gemini_client.py").read_text(encoding="utf-8")
    assert "End with a Telugu call-to-action" not in source
    assert "Final paragraph: a friendly call-to-action" not in source
    pipeline = Path("autoblog/pipeline.py").read_text(encoding="utf-8")
    env = Path(".env.example").read_text(encoding="utf-8")
    assert "AUTOMATION_DRAFT_ONLY" in pipeline
    assert "AUTOMATION_DRAFT_ONLY=1" in env
    print("editorial modes tests: PASS")


if __name__ == "__main__":
    main()
