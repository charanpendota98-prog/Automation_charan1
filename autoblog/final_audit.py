# -*- coding: utf-8 -*-
"""v160 — Final go-live audit: okate command, anni gates.

Ee repo lo chala auditors unnayi (post gate, theme audit, deep audit, CWV,
image weight, AEO, parity, readiness). Deploy mundu vatini okoti okoti
gurthupettukoni run cheyyadam manishi chese pani kaadu — okati marchipothe
adi ne live lo bug avutundi.

Ee module anni ni **okate run** lo chesi, okate verdict istundi:

    python run.py --final-audit

Anni gates pass ayithe ne "GO" antundi. Edaina fail ayithe **GO ANNADU** —
enduku fail ayindo, ekkada fix cheyalo cheptundi. Score ni inflate cheyyadu:
prati line nijamaina tool output nunchi ne.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import List, Tuple

ROOT = Path(__file__).resolve().parent.parent
PY = sys.executable or "python3"

# (label, command, what a pass means)
GATES: List[Tuple[str, List[str], str]] = [
    ("Python test suites", [PY, "-m", "pytest", "tests", "-q"],
     "anni feature tests green"),
    ("Theme audit (escaping/security)", [PY, "tools/theme_audit.py"],
     "0 errors · 0 warnings"),
    ("Theme deep audit (queries/perf)", [PY, "tools/theme_audit_deep.py"],
     "0 errors · 0 warnings"),
    ("CWV + a11y markup audit", [PY, "tools/cwv_audit.py"],
     "no CLS/LCP/a11y blockers"),
    ("Image weight audit", [PY, "tools/image_weight_audit.py"],
     "anni images budget lo"),
    ("Preview ↔ theme parity", [PY, "tools/parity_audit.py"],
     "pin-to-pin match"),
    ("PHP lint", ["node", "tools/php_lint.js"],
     "prati PHP file parse avutundi"),
]


def _run(cmd: List[str]) -> Tuple[bool, str]:
    try:
        proc = subprocess.run(cmd, cwd=ROOT, capture_output=True,
                              text=True, timeout=1800)
    except FileNotFoundError:
        return False, f"tool dorakaledu: {cmd[0]}"
    except subprocess.TimeoutExpired:
        return False, "timeout"
    out = (proc.stdout or "") + (proc.stderr or "")
    tail = [ln for ln in out.strip().splitlines() if ln.strip()]
    return proc.returncode == 0, (tail[-1].strip() if tail else "")


def theme_zip() -> Tuple[Path, str]:
    """Built theme zip + a human size string (undakapothe empty)."""
    zip_path = ROOT / "wordpress-theme" / "studentup-theme.zip"
    if not zip_path.exists():
        return zip_path, ""
    kb = zip_path.stat().st_size / 1024.0
    return zip_path, f"{kb:.0f} KB"


def run_cli() -> int:
    print("=" * 74)
    print("  FINAL GO-LIVE AUDIT — anni gates okate saari")
    print("=" * 74)

    failed: List[str] = []
    for label, cmd, meaning in GATES:
        ok, last = _run(cmd)
        mark = "✅" if ok else "❌"
        print(f"  {mark} {label:34s} {last[:34]}")
        if not ok:
            failed.append(f"{label} — expected: {meaning}\n       run: {' '.join(cmd)}")

    zip_path, size = theme_zip()
    if size:
        print(f"  📦 Theme zip                        {zip_path.name} ({size})")
    else:
        failed.append("Theme zip build avvaledu — run: python3 tools/build_wp_theme.py")
        print("  ❌ Theme zip                        build cheyyandi")

    print("-" * 74)
    if failed:
        print(f"  ❌ NO-GO — {len(failed)} gate(s) fail ayyayi:\n")
        for f in failed:
            print(f"    • {f}")
        print("\n  Ivi fix ayyaka malli ee command run cheyandi.")
        return 1

    print("  ✅ GO — anni gates green.")
    print(f"     Upload: {zip_path.relative_to(ROOT)}")
    print("     WP → Appearance → Themes → Add New → Upload → Activate")
    print("-" * 74)
    print("  Note: ivi repo-side gates. Live PageSpeed, indexing, AdSense")
    print("  approval — avi site live ayyaka ne measure avutayi.")
    return 0
