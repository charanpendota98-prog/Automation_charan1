"""v33 Google-facing public audit tests; all HTTP is faked."""
import sys
from unittest import mock
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from autoblog import google_audit  # noqa: E402


HTML = '''<!doctype html><html><head><title>SSC CGL 2026 Complete Guide</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="A complete official guide for SSC CGL 2026 applications, eligibility, fee and documents for students in Telugu.">
<link rel="canonical" href="https://studentup.in/ssc-cgl-2026/">
<script type="application/ld+json">{}</script></head><body><h1>SSC CGL 2026</h1><img src="x.jpg" alt="SSC guide"></body></html>'''


class Resp:
    status_code = 200
    text = HTML

    def json(self):
        return {"lighthouseResult": {
            "categories": {"performance": {"score": .95}, "accessibility": {"score": .91},
                            "best-practices": {"score": .96}, "seo": {"score": .94}},
            "audits": {"largest-contentful-paint": {"displayValue": "1.8 s"},
                       "cumulative-layout-shift": {"displayValue": "0.02"},
                       "interaction-to-next-paint": {"displayValue": "120 ms"}},
        }}


def test_html_and_psi():
    rows = google_audit.html_checks("https://studentup.in/ssc-cgl-2026/", HTML)
    assert not [r for r in rows if r["status"] == "FAIL"]
    assert next(r for r in rows if r["label"] == "Canonical")["status"] == "PASS"
    assert next(r for r in rows if r["label"] == "Image alt text")["status"] == "PASS"
    with mock.patch.object(google_audit.requests, "get", return_value=Resp()):
        rows = google_audit.audit_url("https://studentup.in/ssc-cgl-2026/")
    assert any("PageSpeed mobile Performance" == r["label"] and r["status"] == "PASS" for r in rows)
    assert any(r["label"] == "PageSpeed mobile LCP" for r in rows)


def main():
    test_html_and_psi()
    print("  public HTML + PageSpeed mobile/desktop audit ✔")
    print("ALL v33 TESTS PASSED ✔")


if __name__ == "__main__":
    main()
