# -*- coding: utf-8 -*-
"""v67: POT generator — theme strings ni `languages/studentup.pot` ki extract cheyyadam.

Enduku: top-tier WordPress themes anni translation-ready (i18n). Ee tool theme lo
`__( 'string', 'studentup' )` / `esc_html__()` / `_e()` / `_n()` / `_x()` calls ni
vetiki standard `.pot` file rastundi → theme review/standards + future languages.

Run: python tools/build_pot.py            (writes wordpress-theme/studentup/languages/studentup.pot)
     tools/build_wp_theme.py lo auto (build lo regenerate avutundi)
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
THEME = ROOT / "wordpress-theme" / "studentup"
DOMAIN = "studentup"

# (function-name, string-arg-index)
CALLS = (
    ("__", 0), ("_e", 0), ("esc_html__", 0), ("esc_html_e", 0), ("esc_attr__", 0),
    ("esc_attr_e", 0), ("_x", 0), ("_n", 0), ("_nx", 0),
)
STRING = r"((?:'(?:[^'\\]|\\.)*'|\"(?:[^\"\\]|\\.)*\"))"
PATTERN = re.compile(
    r"\b(" + "|".join(name for name, _ in CALLS) + r")\s*\(\s*" + STRING + r"\s*,\s*(?:" + STRING + r"\s*,\s*)?['\"]"
    + DOMAIN + r"['\"]")


def _unquote(raw: str) -> str:
    return raw[1:-1].replace("\\'", "'").replace('\\"', '"').replace("\\\\", "\\")


def extract() -> list:
    found = {}
    for path in sorted(THEME.rglob("*.php")):
        text = path.read_text(encoding="utf-8")
        rel = path.relative_to(THEME).as_posix()
        for m in PATTERN.finditer(text):
            string = _unquote(m.group(2))
            plural = _unquote(m.group(3)) if m.group(3) else ""
            if not string.strip():
                continue
            line = text[: m.start()].count("\n") + 1
            key = (string, plural)
            row = found.setdefault(key, {"refs": []})
            row["refs"].append(f"{rel}:{line}")
    return sorted(found.items(), key=lambda kv: kv[0][0].lower())


def render(entries: list) -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M+0000")
    out = [
        '# Copyright (C) 2026 StudentUp',
        '# This file is distributed under the GNU GPL v2 or later.',
        'msgid ""',
        'msgstr ""',
        '"Project-Id-Version: StudentUp 1.3.0\\n"',
        '"Report-Msgid-Bugs-To: https://studentup.in/\\n"',
        f'"POT-Creation-Date: {stamp}\\n"',
        '"MIME-Version: 1.0\\n"',
        '"Content-Type: text/plain; charset=UTF-8\\n"',
        '"Content-Transfer-Encoding: 8bit\\n"',
        '"Language-Team: Telugu (te_IN)\\n"',
        '"X-Generator: tools/build_pot.py\\n"',
        '',
    ]
    for (string, plural), row in entries:
        for ref in row["refs"][:8]:
            out.append(f"#: {ref}")
        out.append(f'msgid "{string}"')
        if plural:
            out.append('msgid_plural "' + plural + '"')
            out.append('msgstr[0] ""')
            out.append('msgstr[1] ""')
        else:
            out.append('msgstr ""')
        out.append("")
    return "\n".join(out)


def build() -> dict:
    entries = extract()
    dest = THEME / "languages" / "studentup.pot"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(render(entries), encoding="utf-8")
    return {"path": str(dest.relative_to(ROOT)), "strings": len(entries),
            "refs": sum(len(r["refs"]) for _, r in entries)}


def main() -> int:
    rep = build()
    print("=" * 70)
    print("  🌐 POT GENERATOR (v67) — theme strings → languages/studentup.pot")
    print("=" * 70)
    print(f"  strings: {rep['strings']} · references: {rep['refs']}")
    print(f"  file: {rep['path']}")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
