"""Static checks for the active-opportunity finder and trust controls."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
THEME = ROOT / "wordpress-theme" / "studentup"


def main():
    php = (THEME / "inc" / "opportunities.php").read_text(encoding="utf-8")
    page = (THEME / "page-opportunities.php").read_text(encoding="utf-8")
    js = (THEME / "assets" / "js" / "studentup-opportunities.js").read_text(encoding="utf-8")
    tools = (THEME / "inc" / "student-tools.php").read_text(encoding="utf-8")
    css = (THEME / "style.css").read_text(encoding="utf-8")

    for token in (
        "studentup_apply_url", "studentup_qual", "data-su-op-days",
        "data-su-op-section", "data-su-op-title", "Official Apply",
        "Updated",
    ):
        assert token in php, token
    for token in (
        "data-su-op-search", "data-su-op-section-filter", "data-su-op-deadline",
        "data-su-op-no-results", "active updates",
    ):
        assert token in page, token
    for token in (
        "data-su-opportunities", "data-su-op-card",
        "querySelectorAll(\".su-op-section\")",
    ):
        assert token in js, token
    for token in ("Closing in 7 days", "Date not announced"):
        assert token in page, token
    assert "studentup-opportunities" in tools
    assert ".su-op-filters" in css and ".su-op-apply" in css
    print("opportunity board finder checks: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
