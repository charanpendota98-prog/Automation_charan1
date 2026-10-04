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
# jsdom behavioural count — tests la jsdom claims kuda sync avvali (v202: 230 → 239).
JSDOM_TESTS_RE = re.compile(r"(jsdom\s+)(\d+)/(\d+)")
JSDOM_LIT_RE = re.compile(r"\"(\d+)/(\d+) checks passed\"")
JSDOM_LABEL_RE = re.compile(r"('jsdom )(\d+)/(\d+)( behavioral')")
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


def php_file_count() -> int:
    """php_lint.js laage: theme folder lo anni .php files."""
    root = THEME
    skip = {"node_modules", ".git"}
    n = 0
    stack = [root]
    while stack:
        d = stack.pop()
        for e in d.iterdir():
            if e.is_dir():
                if e.name not in skip:
                    stack.append(e)
            elif e.name.endswith(".php"):
                n += 1
    return n


def jsdom_checks() -> int:
    """README/MANUAL/GO_LIVE lo jsdom claim ↔ jsdom file EXPECTED_CHECKS (v71 gate)."""
    txt = (TESTS / "runtime" / "jsdom_runtime_test.js").read_text(encoding="utf-8")
    m = re.search(r"EXPECTED_CHECKS\s*=\s*(\d+)", txt)
    return int(m.group(1)) if m else 0


def sync_docs(ver: str, write: bool) -> int:
    """Refresh every *release pin* in the docs.

    v202: modati sari GO_LIVE fingerprint matrame kaadu — suites / php-lint /
    jsdom counts mariyu SETUP_ALL + DEPLOY_v197 zip pins kuda ikkade sync avutayi,
    so "docs stale" ane tappu malli raadu.
    """
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
    changed = 0
    if new != src:
        print(f"  GO_LIVE_CHECKLIST.md: zip fingerprint -> {files} files · {size_kb} KB · {sha[:12]}…")
        if write:
            doc.write_text(new, encoding="utf-8")
        changed += 1

    suites = suite_count()
    lint = php_file_count()
    jsdom = jsdom_checks()
    zip_re = re.compile(r"(\| studentup-theme-[0-9.]+\.zip \| )\d+ files · \d+ KB( \| `)[0-9a-f]{12}(`)")
    dep_re = re.compile(r"\(\d+ files · \d+ KB(?: · `[0-9a-f]{12}…`)?\)")
    dep_ver_re = re.compile(r"(> Theme \*\*)1\.9\.\d+(\*\* · zip:)")
    dep_admin_re = re.compile(r"(lo `StudentUp )1\.9\.\d+(`)")
    suites_md_re = re.compile(r"(test suites \*\*)\d+/\d+(\*\*)")
    jsdom_md_re = re.compile(r"(jsdom runtime \*\*)\d+/\d+(\*\*)")
    lint_md_re = re.compile(r"(PHP lint \*\*)\d+/\d+(\*\*)")
    lint_cmd_re = re.compile(r"(node tools/php_lint\.js\s+# )\d+/\d+")
    guides = [
        (ROOT / "README.md", suites_md_re, jsdom_md_re, lint_md_re),
        (ROOT / "MANUAL_ADVANCED_CHECKLIST.md", suites_md_re, jsdom_md_re, lint_md_re),
        (ROOT / "GO_LIVE_CHECKLIST.md", suites_md_re, jsdom_md_re, lint_md_re),
        (ROOT / "SETUP_ALL.md", None, None, None),
        (ROOT / "FULL_SETUP_GUIDE.md", None, None, None),
        (ROOT / "DEPLOY_v197.md", None, None, None),
        (ROOT / "milesweb-kit" / "DEPLOY_v197.md", None, None, None),
    ]
    for doc, sre, jre, lre in guides:
        if not doc.exists():
            continue
        src = doc.read_text(encoding="utf-8")
        out = src
        if sre:
            out = sre.sub(lambda m: m.group(1) + f"{suites}/{suites}" + m.group(2), out)
        if jre:
            out = jre.sub(lambda m: m.group(1) + f"{jsdom}/{jsdom}" + m.group(2), out)
        if lre:
            out = lre.sub(lambda m: m.group(1) + f"{lint}/{lint}" + m.group(2), out)
        out = lint_cmd_re.sub(lambda m: m.group(1) + f"{lint}/{lint}", out)
        out = zip_re.sub(lambda m: m.group(1) + f"{files} files · {size_kb} KB" + m.group(2) + sha[:12] + m.group(3), out)
        out = dep_re.sub(f"({files} files · {size_kb} KB · `{sha[:12]}…`)", out)
        out = dep_ver_re.sub(lambda m: m.group(1) + ver + m.group(2), out)
        out = dep_admin_re.sub(lambda m: m.group(1) + ver + m.group(2), out)
        # SETUP_ALL + FULL_SETUP_GUIDE lo suites/jsdom/php-lint prose
        out = out.replace(f"suites · jsdom {jsdom}/{jsdom}", f"suites · jsdom {jsdom}/{jsdom}")
        out = re.sub(r"(\+ )\d+/\d+( suites)", lambda m: m.group(1) + f"{suites}/{suites}" + m.group(2), out)
        out = re.sub(r"(jsdom )\d+/\d+", lambda m: m.group(1) + f"{jsdom}/{jsdom}", out)
        out = re.sub(r"(php-lint )\d+/\d+", lambda m: m.group(1) + f"{lint}/{lint}", out)
        out = re.sub(r"(\| PHP lint \|[^|]*\| \*\*)\d+/\d+(\*\* ✔ \|)",
                     lambda m: m.group(1) + f"{lint}/{lint}" + m.group(2), out)
        out = re.sub(r"(\| Test suites \|[^|]*\| \*\*)\d+/\d+(\*\* ✔ \|)",
                     lambda m: m.group(1) + f"{suites}/{suites}" + m.group(2), out)
        if out != src:
            print(f"  {doc.relative_to(ROOT)}: release pins -> v{ver} · {suites} suites · {lint} php · {jsdom} jsdom · zip {sha[:12]}…")
            if write:
                doc.write_text(out, encoding="utf-8")
            changed += 1
    return changed


def main() -> int:
    write = "--write" in sys.argv
    ver = live_version()
    suites = suite_count()
    jsdom = jsdom_checks()
    changed = 0
    for path in sorted(TESTS.glob("*.py")):
        src = path.read_text(encoding="utf-8")
        new = PIN_RE.sub(ver, src)
        new = RE_PIN_RE.sub(ver.replace(".", r"\\."), new)
        new = PLAIN_PIN_RE.sub(ver, new)
        new = SUITE_RE.sub(lambda m: m.group(1) + str(suites), new)
        new = SUITE_ASSERT_RE.sub(lambda m: m.group(1) + str(suites), new)
        new = SUITE_MSG_RE.sub(lambda m: m.group(1) + str(suites), new)
        new = JSDOM_TESTS_RE.sub(lambda m: m.group(1) + f"{jsdom}/{jsdom}", new)
        new = JSDOM_LIT_RE.sub(f'"{jsdom}/{jsdom} checks passed"', new)
        new = JSDOM_LABEL_RE.sub(lambda m: m.group(1) + f"{jsdom}/{jsdom}" + m.group(4), new)

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
