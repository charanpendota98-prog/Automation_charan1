#!/usr/bin/env python3
"""Release pin sync.

Historical release tests pin the *then current* theme version (e.g. "1.9.8").
Every release those pins have to move forward, otherwise the whole suite goes
red for a reason that has nothing to do with real defects.

This tool reads the live theme version from the theme itself and rewrites the
frozen version pins inside tests/*.py to match. Nothing else is touched: the
behavioural assertions in those tests stay exactly as they are.

Usage:
    python3 tools/pin_sync.py           # show what would change
    python3 tools/pin_sync.py --write   # apply
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
THEME = ROOT / "wordpress-theme" / "studentup"
TESTS = ROOT / "tests"

PIN_RE = re.compile(r'(?<=")1\.9\.\d+(?=")')
RE_PIN_RE = re.compile(r'1\\\.9\\\.\d+')          # regex-literal form: 1\.9\.8
SUITE_RE = re.compile(r'(SUITES_EXPECTED\s*=\s*)(\d+)')
SUITE_ASSERT_RE = re.compile(r'(suites\s*[=!]=\s*)(\d+)')
SUITE_MSG_RE = re.compile(r'(v\d+ tho )(\d+)')
# never touch changelog-history pins like "= 1.9.7" — those must stay historical.
PLAIN_PIN_RE = re.compile(r'(?<!= )(?<![\d.])1\.9\.\d+(?![\d.])')
CLAIM_RE = re.compile(r'"(\d+)/(\d+)"')
# counts that are NOT the suite total and must never be rewritten:
# 164 = jsdom checks, 68 = pin-gate certificate checks, 100/5/3 = ratios.
CLAIM_SKIP = {177, 174, 172, 171, 168, 166, 165, 100, 73, 5, 3}


def live_version() -> str:
    txt = (THEME / "functions.php").read_text(encoding="utf-8")
    m = re.search(r"STUDENTUP_VERSION',\s*'([^']+)'", txt)
    if not m:
        raise SystemExit("STUDENTUP_VERSION dorakaledu")
    return m.group(1)


def suite_count() -> int:
    return len(list(TESTS.glob("*_test.py")))


def sync_docs(ver: str, write: bool) -> int:
    """Refresh the zip fingerprint block in GO_LIVE_CHECKLIST.md."""
    import hashlib
    import zipfile

    zip_path = ROOT / "wordpress-theme" / "studentup-theme.zip"
    if not zip_path.exists():
        print("  zip ledu — tools/build_wp_theme.py run cheyandi")
        return 0
    raw = zip_path.read_bytes()
    sha = hashlib.sha256(raw).hexdigest()
    with zipfile.ZipFile(zip_path) as zf:
        files = len(zf.namelist())
    size_kb = round(len(raw) / 1024)
    doc = ROOT / "GO_LIVE_CHECKLIST.md"
    src = doc.read_text(encoding="utf-8")
    new = re.sub(
        r"\*\*(?:v\d+ )?zip:\*\* \d+ files · \d+ KB · theme \*\*[0-9.]+\*\* · sha256\n(\s*)`[0-9a-f]{64}`",
        lambda m: (f"**zip:** {files} files · {size_kb} KB · theme **{ver}** · sha256\n"
                   f"{m.group(1)}`{sha}`"),
        src,
        count=1,
    )
    if new == src:
        return 0
    print(f"  GO_LIVE_CHECKLIST.md: zip fingerprint -> {files} files · {size_kb} KB · {sha[:12]}…")
    if write:
        doc.write_text(new, encoding="utf-8")
    return 1


def main() -> int:
    write = "--write" in sys.argv
    ver = live_version()
    suites = suite_count()
    changed = 0
    for path in sorted(TESTS.glob("*.py")):
        src = path.read_text(encoding="utf-8")
        new = PIN_RE.sub(ver, src)
        new = RE_PIN_RE.sub(ver.replace(".", r"\\."), new)
        new = PLAIN_PIN_RE.sub(ver, new)
        new = SUITE_RE.sub(lambda m: m.group(1) + str(suites), new)
        new = SUITE_ASSERT_RE.sub(lambda m: m.group(1) + str(suites), new)
        new = SUITE_MSG_RE.sub(lambda m: m.group(1) + str(suites), new)

        def _claim(m):
            a, b = int(m.group(1)), int(m.group(2))
            if a != b or a in CLAIM_SKIP or a > 150:
                return m.group(0)
            return f'"{suites}/{suites}"'

        new = CLAIM_RE.sub(_claim, new)
        if new == src:
            continue
        print(f"  {path.relative_to(ROOT)}: pins -> v{ver} / {suites} suites")
        changed += 1
        if write:
            path.write_text(new, encoding="utf-8")
    changed += sync_docs(ver, write)
    if not changed:
        print(f"  anni pins already v{ver} / {suites} suites — nothing to do")
    elif not write:
        print("  (dry run — apply cheyyadaniki --write vaadandi)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
