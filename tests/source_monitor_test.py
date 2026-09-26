"""Offline source-freshness monitor checks."""
import tempfile
from pathlib import Path
from types import SimpleNamespace

from autoblog import config, source_monitor


def main():
    old_state = config.SOURCE_MONITOR_STATE
    old_enabled = config.SOURCE_MONITOR_ENABLED
    tmp = Path(tempfile.mkdtemp()) / "source-monitor.json"
    payload = {"text": "official notice fee 100", "title": "Notice", "url": "https://gov.example/notice"}

    class FakeWP:
        def published_opportunities(self, **kwargs):
            return [{"id": 7, "link": "https://studentup.in/post", "title": "Notice", "source_url": payload["url"]}]

    try:
        config.SOURCE_MONITOR_STATE = tmp
        config.SOURCE_MONITOR_ENABLED = True
        original = source_monitor.sources.fetch_source
        source_monitor.sources.fetch_source = lambda url: SimpleNamespace(text=payload["text"])
        first = source_monitor.scan(wp=FakeWP())
        assert first["scanned"] == 1 and not first["changed"]
        payload["text"] = "official notice fee 125"
        second = source_monitor.scan(wp=FakeWP())
        assert len(second["changed"]) == 1
        assert second["changed"][0]["post_id"] == 7
        print("source monitor checks: PASS")
    finally:
        source_monitor.sources.fetch_source = original
        config.SOURCE_MONITOR_STATE = old_state
        config.SOURCE_MONITOR_ENABLED = old_enabled
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
