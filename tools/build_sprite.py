#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v197 — SVG sprite GENERATOR (theme icons → preview pages).

Problem it kills: every preview page carried its own hand-copied `<symbol>` list,
so a new theme icon (megamenu, quiz, polls) silently rendered as a BLANK box on
the preview. Hand-copying is the bug; generation is the fix.

Source of truth:
  wordpress-theme/studentup/inc/icons.php   studentup_icon_paths()
  wordpress-theme/studentup/inc/options.php studentup_social_icon_paths()

Targets: every preview HTML that already contains a sprite block (never invents
new markup, never touches pages without one).

Run: python3 tools/build_sprite.py
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
THEME = ROOT / "wordpress-theme" / "studentup"
PREVIEW = ROOT / "preview"

# Two wrappers exist in the wild: the v192 demo (`class="su-sprite"`) and the
# policy-page shell (`style="display:none"`). Both are "one svg, many symbols".
SPRITE_RE = re.compile(
    r'<svg(?=[^>]*>(?:\s*<symbol\s+id="su-i-))[^>]*>.*?</svg>', re.S
)
# v197.1: extra containers lo unna icon symbols (merge tarvata migilevi)
SYMBOL_RE = re.compile(r'<symbol\s+id="su-i-[a-z0-9_-]+"[^>]*>.*?</symbol>', re.S)


def _php_paths(path: Path, func: str) -> dict[str, str]:
    """Read a `key => 'path'` PHP array out of one function."""
    src = path.read_text(encoding="utf-8")
    start = src.index("function %s(" % func)
    end = src.index("\n}", start)
    body = src[start:end]
    return dict(re.findall(r"'([a-z0-9_]+)'\s*=>\s*'([^']+)'", body))


def icon_paths() -> dict[str, str]:
    paths = _php_paths(THEME / "inc" / "icons.php", "studentup_icon_paths")
    social = _php_paths(THEME / "inc" / "options.php", "studentup_social_icon_paths")
    for key, val in social.items():
        paths.setdefault("social-" + key, val)
    return paths


def sprite_svg(paths: dict[str, str], keys: list[str] | None = None, social_paths: dict[str, str] | None = None) -> str:
    """<svg class="su-sprite"> block — same attributes the theme uses."""
    items = []
    for key in (keys or sorted(paths)):
        d = paths.get(key)
        if not d:
            continue
        items.append(
            '<symbol id="su-i-%s" viewBox="0 0 24 24"><path d="%s"/></symbol>' % (key, d)
        )
    if social_paths:
        for sk, sv in sorted(social_paths.items()):
            items.append(
                '<symbol id="su-s-%s" viewBox="0 0 24 24"><path d="%s"/></symbol>' % (sk, sv)
            )
    return (
        '<svg class="su-sprite" aria-hidden="true" focusable="false" style="display:none">'
        + "".join(items)
        + "</svg>"
    )


def used_icon_keys(html: str) -> list[str]:
    """Icons the page actually references (keeps the inline blob small)."""
    keys = set(re.findall(r'href="#su-i-([a-z0-9_-]+)"', html))
    keys |= set(re.findall(r"su-uicon-([a-z0-9_-]+)", html))
    return sorted(keys)


def main() -> int:
    social_dict = _php_paths(THEME / "inc" / "options.php", "studentup_social_icon_paths")
    paths = icon_paths()
    if len(paths) < 40:
        print(f"  ❌ icon source lo {len(paths)} icons mattrame — icons.php parse fail?")
        return 1

    targets = sorted(
        p for p in list(PREVIEW.rglob("*.html"))
        if SPRITE_RE.search(p.read_text(encoding="utf-8", errors="ignore"))
    )
    changed = 0
    for path in targets:
        html = path.read_text(encoding="utf-8")
        keys = used_icon_keys(html)
        # always keep the theme-toggle + nav basics even if JS adds them at runtime
        for extra in ("moon", "sun"):
            if extra not in keys:
                keys.append(extra)
        has_social_uses = bool(re.search(r'href="#su-s-', html))
        active_social = social_dict if has_social_uses else None
        block = sprite_svg(paths, sorted(set(keys)), active_social)
        # v197.1: page lo okkati kanna ekkuva icon containers unte (legacy
        # preview/index.html), motham okkate canonical block ki merge cheyyali —
        # lekapote same id rendu saarlu define ayyi duplicate-id audit fail avutundi.
        blocks = list(SPRITE_RE.finditer(html))
        if not blocks:
            continue
        parts, cursor = [], 0
        for idx, m in enumerate(blocks):
            parts.append(html[cursor:m.start()])
            if idx == 0:
                parts.append(block)                      # canonical block
            else:
                rest = SYMBOL_RE.sub("", m.group(0))     # extra block: icons drop
                parts.append(rest if "<symbol" in rest else "")
            cursor = m.end()
        parts.append(html[cursor:])
        new = "".join(parts)
        if new != html:
            path.write_text(new, encoding="utf-8")
            changed += 1
    print(f"  ✅ sprite: {len(paths)} icons · {len(targets)} pages scanned · {changed} refreshed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
