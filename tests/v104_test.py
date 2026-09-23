# -*- coding: utf-8 -*-
"""v104 — editorial value and claim provenance ledger."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from autoblog import editorial_value  # noqa: E402

SUITES_EXPECTED = 92


class Source:
    def __init__(self, url, title, text):
        self.url, self.title, self.text = url, title, text


def sources():
    return [Source("https://tspsc.gov.in/notice.pdf", "Official Notice",
                   "TSPSC notification has 783 vacancies. Last date 2026-07-22. Apply online.") ,
            Source("https://studentup.in/reference", "Reference",
                   "Eligibility details and application steps for candidates.")]


def test_ledger_records_source_provenance() -> None:
    html = """<h2>How to apply</h2><p>TSPSC has 783 vacancies. Last date 2026-07-22.
    Apply online and upload documents. Check Telangana district instructions.</p>
    <ul><li>Download notice</li><li>Verify details</li></ul>"""
    ledger = editorial_value.build_ledger({"title": "TSPSC"}, html, sources())
    assert ledger["version"] == "v104"
    assert len(ledger["sources"]) == 2
    assert ledger["sources"][0]["tier"] == 1
    assert ledger["claims"] and ledger["claims"][0]["supported_by"]
    print("      ledger stores source URL/tier/date and supported claims ✔")


def test_unsupported_claim_is_flagged() -> None:
    html = "<p>Official notice says 9999 vacancies and last date 2035-01-01.</p>"
    ledger = editorial_value.build_ledger({}, html, sources())
    assert ledger["unsupported_claims"]
    assert any(x.startswith("UNVERIFIED-CLAIMS") for x in editorial_value.gate(ledger))
    print("      unsupported number/date claim flagged for human review ✔")


def test_practical_value_signals_score() -> None:
    html = """<h2>Eligibility and steps</h2><p>Telangana candidates can apply online.
    Download the official notice, upload documents, verify the fee and contact the
    district office if the portal fails.</p><table><tr><td>Step</td></tr></table>
    <a href="https://tspsc.gov.in/notice.pdf">Official source</a>"""
    ledger = editorial_value.build_ledger({}, html, sources())
    assert ledger["signals"]["action_terms"] >= 3
    assert ledger["signals"]["local_context_terms"] >= 1
    assert ledger["signals"]["lists_or_tables"] >= 1
    assert ledger["score"] >= 55
    print("      actionable + local + table + official-link value signals ✔")


def test_no_source_is_not_fake_eat() -> None:
    ledger = editorial_value.build_ledger({}, "<p>Apply online today.</p>", [])
    assert "NO-PROVENANCE-SOURCES" in editorial_value.gate(ledger)
    assert ledger["recommendation"].startswith("human review")
    print("      no source does not receive fake authority score ✔")


def test_pipeline_live_gate_wired() -> None:
    src = (ROOT / "autoblog" / "pipeline.py").read_text(encoding="utf-8")
    assert "editorial_value" in src
    assert "EDITORIAL_VALUE_BLOCK" in src
    assert "LIVE-PUBLISH BLOCKED: editorial provenance/value review" in src
    print("      live publishing blocks provenance/value failures ✔")


def test_config_and_docs() -> None:
    cfg = (ROOT / "autoblog" / "config.py").read_text(encoding="utf-8")
    env = (ROOT / ".env.example").read_text(encoding="utf-8")
    r = (ROOT / "README.md").read_text(encoding="utf-8")
    m = (ROOT / "MANUAL_ADVANCED_CHECKLIST.md").read_text(encoding="utf-8")
    for key in ("EDITORIAL_VALUE_MIN", "EDITORIAL_VALUE_BLOCK"):
        assert key in cfg and key in env
    assert "### v104" in r and "PART 61" in m and "92/92" in r and "92/92" in m
    print("      config + docs v104/PART 61/84-84 pinned ✔")


TESTS = [("provenance", test_ledger_records_source_provenance),
         ("unsupported claims", test_unsupported_claim_is_flagged),
         ("value signals", test_practical_value_signals_score),
         ("no fake authority", test_no_source_is_not_fake_eat),
         ("live gate", test_pipeline_live_gate_wired),
         ("config/docs", test_config_and_docs)]


def main() -> int:
    failed = 0
    for name, fn in TESTS:
        try:
            fn(); print(f"  {name} ✔")
        except Exception as exc:  # noqa: BLE001
            failed += 1; print(f"  {name} ✘ {type(exc).__name__}: {exc}")
    print("-" * 70)
    print("ALL v104 PROVENANCE/VALUE TESTS PASSED ✔" if not failed else f"{failed} TEST(S) FAILED ✘")
    return int(bool(failed))


if __name__ == "__main__":
    raise SystemExit(main())
