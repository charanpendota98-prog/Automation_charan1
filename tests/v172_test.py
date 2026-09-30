# -*- coding: utf-8 -*-
"""v172 — STUDENTUP COMMAND CENTER (My Workspace) tests.

Enti check chestundi:
  * inc/workspace.php — option gate · shortcode · assets (enqueue guard +
    localize) · data embedding (esc_attr(wp_json_encode)) · page resolver
  * assets/js/studentup-workspace.js — vanilla only · storage keys · profile
    persistence hooks · matching/deadline hooks · XSS-safe esc
  * wiring — functions.php require + defer, firstrun page, mobile menu link,
    command palette link, hero action, CSS classes
  * version parity 1.9.24 (style.css ↔ functions.php ↔ readme)
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
THEME = ROOT / "wordpress-theme" / "studentup"


def read(rel: str) -> str:
    return (THEME / rel).read_text(encoding="utf-8")


def test_module_structure_and_gate():
    src = read("inc/workspace.php")
    assert "ABSPATH" in src, "ABSPATH guard ledu"
    assert "function studentup_workspace_on()" in src, "feature gate ledu"
    assert "studentup_opt( 'workspace', '1' )" in src, "default-on option gate ledu"
    assert not re.search(r"<\?php\s+echo\s+\$", src), "escape cheyyani echo $ (XSS)"
    print("      module structure + gate ✔")


def test_shortcode_and_data_embedding():
    src = read("inc/workspace.php")
    assert "add_shortcode( 'studentup_workspace'" in src, "shortcode register ledu"
    assert "studentup_smart_dataset" in src, "smart dataset reuse ledu (REST vaddu)"
    assert "esc_attr( wp_json_encode( $data ) )" in src, "data attr safe encode ledu"
    for hook in ("data-su-ws=", "data-su-ws-form", "data-su-ws-qual", "data-su-ws-age",
                 "data-su-ws-state", "data-su-ws-matches", "data-su-ws-pipe", "data-su-ws-radar"):
        assert hook in src, f"markup hook ledu: {hook}"
    assert "studentup_workspace_shortcode" in src, "render fn ledu"
    print("      shortcode + embedded data hooks ✔")


def test_assets_enqueued_only_on_workspace_page():
    src = read("inc/workspace.php")
    assert "function studentup_workspace_assets()" in src
    assert "studentup_workspace_active()" in src, "narrow enqueue gate ledu"
    assert "is_admin()" in src, "admin guard ledu"
    assert re.search(r"'studentup-workspace',[^;]+STUDENTUP_VERSION,\s*true", src), "footer load ledu"
    assert "wp_localize_script" in src and "STUDENTUP_WS" in src, "localize object ledu"
    assert "'savedOn'" in src, "saved-module interop flag ledu"
    assert "STUDENTUP_SAVED_STORE" in src, "saved store reuse ledu (split state bug)"
    print("      conditional assets + localize ✔")


def test_workspace_js_behaviour_hooks():
    code = read("assets/js/studentup-workspace.js")
    assert not re.search(r"\bjQuery\s*\(|\$\(document", code), "jQuery use undi (vaddu)"
    assert code.count('"use strict"') >= 1
    assert "localStorage" in code, "localStorage use ledu"
    for key in ("su_profile_v1", "studentup_apply_v1"):
        assert key in code, f"store key ledu: {key}"
    assert "function esc(" in code, "XSS-safe esc helper ledu"
    assert "function daysLeft(" in code, "deadline math ledu"
    assert "function verdict(" in code, "eligibility verdict ledu"
    assert "data-su-save" in code, "saved-module interop (save buttons) ledu"
    assert 'addEventListener("storage"' in code, "cross-tab sync ledu"
    assert "requestAnimationFrame" not in code  # no scroll work here — just renders
    print("      JS hooks: profile · matching · radar · interop ✔")


def test_wiring_functions_defer_firstrun_menus():
    fn = read("functions.php")
    assert "inc/workspace.php" in fn, "functions.php require ledu (dead module)"
    assert "'studentup-workspace'" in fn, "defer list lo workspace ledu"
    assert "'1.9.24'" in fn, "version 1.9.24 ledu"

    first = read("inc/firstrun.php")
    assert "'workspace'        => 'My Workspace'" in first, "firstrun page entry ledu"
    assert "studentup_setup_workspace_body" in first, "workspace body fn ledu"
    assert "[studentup_workspace]" in first, "firstrun page lo shortcode ledu"

    header = read("header.php")
    assert "studentup_workspace_url()" in header, "mobile menu link ledu"

    speed = read("inc/speed.php")
    assert "My Workspace" in speed, "command palette link ledu"

    premium = read("inc/premium.php")
    assert "su-t-ink" in premium, "hero action ledu"
    print("      wiring: require · defer · firstrun · menu · palette · hero ✔")


def test_css_and_critical_layer():
    css = read("assets/css/premium.css")
    for cls in (".su-ws-card", ".su-ws-tile", ".su-ws-job", ".su-ws-chip",
                ".su-ws-radar-item", ".su-ws-elig", "body.dark .su-ws-elig.yes"):
        assert cls in css, f"CSS class ledu: {cls}"
    assert "@media(max-width:980px)" in css and ".su-ws-grid" in css, "responsive rules ledu"
    tool = (ROOT / "tools" / "build_critical_css.py").read_text(encoding="utf-8")
    assert '".su-ws"' in tool, "critical extractor lo workspace prefix ledu (FOUC risk)"
    print("      CSS + critical-layer coverage ✔")


def test_version_parity_1923():
    assert "Version: 1.9.24" in read("style.css"), "style.css version"
    readme = read("readme.txt")
    assert "Stable tag: 1.9.24" in readme, "readme stable tag"
    assert "= 1.9.23 =" in readme, "readme changelog entry"
    print("      version parity 1.9.24 ✔")
