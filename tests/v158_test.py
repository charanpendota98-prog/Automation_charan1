# -*- coding: utf-8 -*-
"""v158 — AEO engine + theme key-facts / HowTo schema."""
from __future__ import annotations

from pathlib import Path

from autoblog import aeo

ROOT = Path(__file__).resolve().parents[1]
THEME = ROOT / "wordpress-theme" / "studentup"

POST = """
<p>TSPSC Group 2 notification 2026 lo motham 783 posts unnayi ee sari. Degree
complete ayina candidates andaru online apply cheyyochu, application fee Rs 200
matrame, starting salary Rs 40,000 per month untundi, last date 15 October 2026
varaku time undi.</p>
<h2>How to apply online</h2>
<ol><li>Official website tspsc.gov.in open cheyandi</li>
<li>One Time Registration complete cheyandi</li>
<li>Group 2 notification link click chesi form fill cheyandi</li>
<li>Fee pay chesi final submit cheyandi</li></ol>
"""


def test_facts_need_context_words():
    facts = aeo.key_facts(POST)
    assert facts["vacancies"] == "783 posts"
    assert "40,000" in facts["salary"], f"fee ni salary ga teesindi: {facts['salary']}"
    assert "200" in facts["fee"]
    assert "October 2026" in facts["last_date"]
    print("      vacancies/salary/fee/last date correctly separated ✔")


def test_missing_facts_are_reported_not_invented():
    facts = aeo.key_facts("<p>Just a plain sentence with no numbers.</p>")
    assert all(v is None for v in facts.values()), facts
    rep = aeo.audit("<p>Just a plain sentence with no numbers here at all.</p>", "T")
    assert rep["howto"] is None, "steps lekunda HowTo schema build chesindi"
    assert any("missing" in i for i in rep["issues"])
    print("      missing facts reported, nothing invented ✔")


def test_howto_only_with_real_steps():
    steps = aeo.extract_steps(POST)
    assert len(steps) == 4, steps
    node = aeo.howto_schema("TSPSC Group 2 2026", steps)
    assert node["@type"] == "HowTo" and len(node["step"]) == 4
    assert [s["position"] for s in node["step"]] == [1, 2, 3, 4]
    assert aeo.howto_schema("t", steps[:2]) is None, "2 steps ki kuda schema ichindi"
    assert aeo.extract_steps("<h2>Salary</h2><ol><li>aaaaaaaa</li><li>bbbbbbbb</li><li>cccccccc</li></ol>") == []
    print("      HowTo schema only from a real apply-step list ✔")


def test_snippet_word_band():
    qa = aeo.quick_answer(POST)
    assert qa["found"] and qa["snippet_ready"], qa
    short = aeo.quick_answer("<p>" + "word " * 20 + "</p>")
    assert not short["snippet_ready"]
    print("      quick answer measured against the 40-55 word band ✔")


def test_theme_keyfacts_is_meta_gated():
    php = (THEME / "inc" / "keyfacts.php").read_text(encoding="utf-8")
    assert "count( $facts ) < 2" in php, "facts lekapoina strip print chestundi"
    assert "'' === $val" in php and "continue" in php, "empty meta skip cheyyatledu"
    assert "count( $steps ) < 3" in php, "fake HowTo risk"
    assert "esc_html( $f['value'] )" in php, "unescaped output"
    single = (THEME / "single.php").read_text(encoding="utf-8")
    assert "studentup_keyfacts_box();" in single
    funcs = (THEME / "functions.php").read_text(encoding="utf-8")
    assert "inc/keyfacts.php" in funcs
    opts = (THEME / "inc" / "options.php").read_text(encoding="utf-8")
    assert "'keyfacts'" in opts, "option toggle ledu"
    print("      theme strip + schema render only when real meta exists ✔")


def test_cli_flag_documented():
    for name in ("README.md", "MANUAL_ADVANCED_CHECKLIST.md", "GO_LIVE_CHECKLIST.md"):
        assert "--aeo" in (ROOT / name).read_text(encoding="utf-8"), name
    main = (ROOT / "autoblog" / "main.py").read_text(encoding="utf-8")
    assert '"--aeo"' in main and "args.aeo is not None" in main
    print("      --aeo wired in the CLI and documented in all 3 docs ✔")
