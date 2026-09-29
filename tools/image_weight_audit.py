#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v159 — Image weight audit.

Mobile PageSpeed lo image bytes ye ekkuva sarlu #1 problem. Ee tool preview
lo unna prati image ni chusi cheptundi:

  * file size budget dhaati unda (hero 200 KB, card 120 KB, icon 30 KB),
  * intrinsic width markup lo cheppina display width kanna 2x kanna
    peddadaa (= wasted bytes, "properly size images" audit),
  * modern format (webp/avif) unda,
  * page motham image weight enta.

Guess ledu: prati number file nunchi ne vastundi.

CLI:  python3 tools/image_weight_audit.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Dict, List

ROOT = Path(__file__).resolve().parents[1]
PREVIEW = ROOT / "preview"

BUDGETS_KB = {"hero": 200, "card": 120, "icon": 30, "other": 150}
PAGE_BUDGET_KB = 900          # total image weight per page
OVERSIZE_FACTOR = 2.0         # intrinsic vs display width
MODERN = {".webp", ".avif"}

_IMG = re.compile(r"<img\b[^>]*>", re.I)
_ATTR = re.compile(r'([a-zA-Z-]+)\s*=\s*"([^"]*)"')


def _kind(path: Path) -> str:
    name = path.name.lower()
    if "hero" in name or "og" in name:
        return "hero"
    if "card" in name or "thumb" in name:
        return "card"
    if "icon" in name or "logo" in name or "favicon" in name:
        return "icon"
    return "other"


def _png_jpg_size(path: Path):
    """Intrinsic pixel size without Pillow (PNG/JPEG/GIF headers)."""
    data = path.read_bytes()
    try:
        if data[:8] == b"\x89PNG\r\n\x1a\n":
            return int.from_bytes(data[16:20], "big"), int.from_bytes(data[20:24], "big")
        if data[:2] == b"\xff\xd8":
            i = 2
            while i < len(data) - 9:
                if data[i] != 0xFF:
                    i += 1
                    continue
                marker, seg = data[i + 1], int.from_bytes(data[i + 2:i + 4], "big")
                if marker in (0xC0, 0xC1, 0xC2, 0xC3):
                    h = int.from_bytes(data[i + 5:i + 7], "big")
                    w = int.from_bytes(data[i + 7:i + 9], "big")
                    return w, h
                i += 2 + seg
        if data[:6] in (b"GIF87a", b"GIF89a"):
            return (int.from_bytes(data[6:8], "little"),
                    int.from_bytes(data[8:10], "little"))
    except Exception:  # noqa: BLE001 - a malformed header must not crash the audit
        return None, None
    return None, None


def audit_page(page: Path) -> Dict:
    html = page.read_text(encoding="utf-8", errors="ignore")
    rows: List[Dict] = []
    total = 0
    # Oke file ni page lo 3 sarlu vaadithe browser okka sari ne download
    # chestundi - andhuke unique file per page ne lekka.
    counted: set = set()
    for tag in _IMG.findall(html):
        attrs = dict(_ATTR.findall(tag))
        src = attrs.get("src", "")
        if not src or src.startswith(("http://", "https://", "data:")):
            continue
        target = (page.parent / src).resolve()
        if not target.exists():
            rows.append({"src": src, "missing": True})
            continue
        kb = target.stat().st_size / 1024.0
        if target in counted:
            continue
        counted.add(target)
        total += kb
        w_attr = attrs.get("width", "")
        iw, ih = _png_jpg_size(target)
        problems = []
        kind = _kind(target)
        if kb > BUDGETS_KB[kind]:
            problems.append(f"{kb:.0f} KB > {BUDGETS_KB[kind]} KB budget ({kind})")
        if w_attr.isdigit() and iw and iw > int(w_attr) * OVERSIZE_FACTOR:
            problems.append(f"intrinsic {iw}px vs display {w_attr}px - oversized")
        if target.suffix.lower() not in MODERN and kb > 40:
            problems.append(f"{target.suffix} - webp/avif lo chinnadi avutundi")
        rows.append({"src": src, "kb": kb, "w": iw, "h": ih,
                     "kind": kind, "problems": problems, "missing": False})
    return {"page": str(page.resolve().relative_to(ROOT)), "images": rows, "total_kb": total}


def main() -> int:
    pages = sorted(PREVIEW.rglob("*.html"))
    print("=" * 74)
    print(f"  IMAGE WEIGHT AUDIT · {len(pages)} pages")
    print("=" * 74)
    issues = 0
    heaviest = []
    for page in pages:
        rep = audit_page(page)
        bad = [r for r in rep["images"] if r.get("missing") or r["problems"]]
        heaviest.append((rep["total_kb"], rep["page"]))
        over = rep["total_kb"] > PAGE_BUDGET_KB
        if bad or over:
            print(f"\n  {rep['page']} — {rep['total_kb']:.0f} KB images")
            if over:
                issues += 1
                print(f"    ❌ page image weight {rep['total_kb']:.0f} KB > {PAGE_BUDGET_KB} KB")
            for r in bad:
                issues += 1
                if r.get("missing"):
                    print(f"    ❌ {r['src']} — file dorakaledu")
                else:
                    print(f"    ⚠️  {r['src']} ({r['kb']:.0f} KB)")
                    for p in r["problems"]:
                        print(f"         → {p}")
    print("-" * 74)
    heaviest.sort(reverse=True)
    for kb, name in heaviest[:3]:
        print(f"  {kb:7.0f} KB  {name}")
    print("-" * 74)
    print(f"  findings: {issues}")
    if not issues:
        print("  ✅ Anni images budget lo unnayi.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
