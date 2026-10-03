#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v152 — conservative CSS minifier for the theme build.

style.css + premium.css ship ~134 KB of render-blocking CSS on every page,
which is the single biggest Core Web Vitals drag left in the theme. This
produces `*.min.css` next to each source at build time; the theme enqueues the
minified file when it exists and falls back to the readable source otherwise,
so editing stays easy and nothing breaks if the build is skipped.

Deliberately conservative:

* string literals and url() contents are never touched (``content:" (" attr(href)``
  must survive intact),
* only `/* ... */` comments, redundant whitespace and the last semicolon in a
  block are removed,
* no colour/shorthand rewriting, no rule merging, no property reordering -
  those are where minifiers silently change rendering.

JS is left alone on purpose: a hand-rolled JS minifier is how production sites
break at 2am. gzip on the server already handles most of it.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
THEME = ROOT / "wordpress-theme" / "studentup"
TARGETS = [
    THEME / "style.css",
    THEME / "assets" / "css" / "premium.css",
    THEME / "assets" / "css" / "worldclass.css",  # v191: WorldClass v2 design layer
]


def _split_protected(css: str):
    """Yield (is_literal, chunk) so strings/urls are never rewritten."""
    pattern = re.compile(r"""("(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*'|url\([^)]*\))""")
    pos = 0
    for m in pattern.finditer(css):
        if m.start() > pos:
            yield False, css[pos:m.start()]
        yield True, m.group(0)
        pos = m.end()
    if pos < len(css):
        yield False, css[pos:]


def _strip_comments(css: str) -> str:
    out = []
    for literal, chunk in _split_protected(css):
        if literal:
            out.append(chunk)
        else:
            # keep /*! important */ banners (licence/theme header)
            chunk = re.sub(r"/\*(?!!).*?\*/", "", chunk, flags=re.S)
            out.append(chunk)
    return "".join(out)


def _squeeze(css: str) -> str:
    out = []
    for literal, chunk in _split_protected(css):
        if literal:
            out.append(chunk)
            continue
        chunk = re.sub(r"\s+", " ", chunk)
        chunk = re.sub(r"\s*([{};:,>~+])\s*", r"\1", chunk)
        chunk = chunk.replace(";}", "}")
        out.append(chunk)
    return "".join(out).strip()


def minify_css(css: str) -> str:
    """Minify while preserving the leading theme header comment."""
    header = ""
    stripped = css.lstrip()
    if stripped.startswith("/*"):
        end = css.find("*/")
        if end != -1:
            header = css[:end + 2].strip() + "\n"
            css = css[end + 2:]
    return header + _squeeze(_strip_comments(css)) + "\n"


def rule_count(css: str) -> int:
    """Cheap structural fingerprint used to prove nothing was dropped."""
    return css.count("{")


def build(targets=None, quiet: bool = False) -> int:
    targets = targets or TARGETS
    total_before = total_after = 0
    for src in targets:
        if not src.exists():
            print(f"  ⚠ missing: {src}")
            continue
        raw = src.read_text(encoding="utf-8")
        small = minify_css(raw)
        before, after = len(raw.encode()), len(small.encode())
        if rule_count(small) != rule_count(raw):
            print(f"  ❌ {src.name}: rule count changed "
                  f"({rule_count(raw)} → {rule_count(small)}) — minify aapesanu")
            return 1
        out = src.with_suffix(".min.css")
        out.write_text(small, encoding="utf-8")
        total_before += before
        total_after += after
        if not quiet:
            saved = 100 - (after * 100 // max(before, 1))
            print(f"  ✅ {out.relative_to(ROOT)}  {before // 1024} KB → {after // 1024} KB "
                  f"(-{saved}%)")
    if not quiet and total_before:
        saved = 100 - (total_after * 100 // total_before)
        print(f"  total: {total_before // 1024} KB → {total_after // 1024} KB (-{saved}%)")
    return 0


def main() -> int:
    print("=" * 70)
    print("  MINIFY THEME CSS (conservative — strings/urls untouched)")
    print("=" * 70)
    return build()


if __name__ == "__main__":
    sys.exit(main())
