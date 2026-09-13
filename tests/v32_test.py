"""v32 existing-post audit tests; audit must remain read-only."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from autoblog import content_audit  # noqa: E402


class Resp:
    def __init__(self, payload):
        self._payload = payload
        self.status_code = 200
        self.ok = True
        self.headers = {}

    def json(self):
        return self._payload


class FakeWP:
    def __init__(self):
        self.calls = []
        body = ("<p>SSC CGL 2026 guide details and eligibility information.</p>"
                "<h2>Eligibility</h2><p>Eligibility details.</p>"
                "<h2>How to Apply</h2><p>Apply steps.</p>"
                "<h2>FAQ</h2><p>Frequently asked questions and answers.</p>"
                "<table><tr><th>Fee</th><td>Official notice</td></tr></table>"
                '<p><a href="https://studentup.in/jobs">Internal</a> '
                '<a href="https://ssc.gov.in">Official</a></p>')
        self.post = {"id": 4, "link": "https://studentup.in/ssc/",
                     "title": {"rendered": "SSC CGL 2026 Complete Guide"},
                     "content": {"rendered": body}, "modified": "2026-09-13"}

    def check_connection(self):
        return {"roles": ["administrator"]}

    def _request(self, method, path, **kwargs):
        self.calls.append((method, path, kwargs))
        if kwargs.get("params", {}).get("page") == 2:
            return Resp([])
        return Resp([self.post])


def test_audit_score_and_fetch_are_read_only():
    wp = FakeWP()
    rows = content_audit.audit_posts(wp, limit=10)
    assert len(rows) == 1
    assert rows[0]["score"] >= 78
    assert rows[0]["action"] in ("keep", "small-fix")
    assert not [call for call in wp.calls if call[0] in ("POST", "PUT", "DELETE")]

    thin = content_audit.audit_post({
        "id": 9, "title": {"rendered": "Bad"},
        "content": {"rendered": "<p>tiny</p>"},
    })
    assert thin["action"] == "priority-refresh"
    assert "thin-content" in thin["issues"]


def main():
    test_audit_score_and_fetch_are_read_only()
    print("  existing-post audit score/actions + read-only REST ✔")
    print("ALL v32 TESTS PASSED ✔")


if __name__ == "__main__":
    main()
