"""Offline tests for the read-only opportunity lifecycle queue."""
import tempfile
from datetime import date, timedelta
from pathlib import Path

from autoblog import config, opportunity_monitor


def main():
    old_path = config.OPPORTUNITY_MONITOR_STATE
    old_enabled = config.OPPORTUNITY_MONITOR_ENABLED
    old_near = config.OPPORTUNITY_MONITOR_NEAR_DAYS
    tmp = Path(tempfile.mkdtemp()) / "opportunity-monitor.json"
    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    rows = [
        {
            "id": 11,
            "title": "Official notice with a missing apply link",
            "link": "https://studentup.in/notice",
            "source_url": "https://gov.example/notice.pdf",
            "last_date": tomorrow,
            "application_url": "",
        },
        {
            "id": 12,
            "title": "Expired notice",
            "link": "https://studentup.in/expired",
            "source_url": "https://gov.example/expired",
            "last_date": yesterday,
            "application_url": "https://gov.example/apply",
        },
    ]

    class FakeWP:
        def published_opportunities(self, **kwargs):
            return rows

    probes = {
        "https://gov.example/notice.pdf": {
            "status": 200, "url": "https://gov.example/notice.pdf",
            "final_url": "https://gov.example/notice.pdf", "is_pdf": True,
        },
        "https://gov.example/expired": {
            "status": 404, "url": "https://gov.example/expired",
            "final_url": "https://gov.example/expired", "is_pdf": False,
        },
        "https://gov.example/apply": {
            "status": 200, "url": "https://gov.example/apply",
            "final_url": "https://gov.example/apply", "is_pdf": False,
        },
    }

    try:
        config.OPPORTUNITY_MONITOR_STATE = tmp
        config.OPPORTUNITY_MONITOR_ENABLED = True
        config.OPPORTUNITY_MONITOR_NEAR_DAYS = 3
        first = opportunity_monitor.scan(wp=FakeWP(), probe_fn=lambda url: probes[url])
        kinds = {item["kind"] for item in first["issues"]}
        assert {"deadline_near", "application_link_missing", "deadline_expired", "source_dead"} <= kinds
        assert len(first["new_issues"]) == len(first["issues"])

        second = opportunity_monitor.scan(wp=FakeWP(), probe_fn=lambda url: probes[url])
        assert second["issues"]
        assert not second["new_issues"], "open findings must not spam on every scan"
        print("opportunity lifecycle monitor checks: PASS")
    finally:
        config.OPPORTUNITY_MONITOR_STATE = old_path
        config.OPPORTUNITY_MONITOR_ENABLED = old_enabled
        config.OPPORTUNITY_MONITOR_NEAR_DAYS = old_near
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
