#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v157 — Core Web Vitals + accessibility static auditor.

PageSpeed can only be run on a live site, so this checks the things that
*cause* bad CWV/a11y scores and can be verified right here in the repo:

  CLS   - <img>/<iframe> without width+height (or aspect-ratio CSS)
  LCP   - the hero/first image must not be lazy-loaded; fonts need font-display
  INP   - no synchronous render-blocking scripts in <head>
  A11y  - images without alt, buttons/links without an accessible name,
          form inputs without a label, duplicate element ids
  SEO   - one <h1>, meta description present, heading order not skipped

It only reports what it can prove from the markup. It never claims a
PageSpeed score - that number belongs to the live site.
"""
from __future__ import annotations

import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from typing import Dict, List

ROOT = Path(__file__).resolve().parents[1]
PREVIEW = ROOT / "preview"


class Auditor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.ids: Dict[str, int] = {}
        self.h1 = 0
        self.headings: List[int] = []
        self.imgs = 0
        self.first_img_seen = False
        self.in_head = True
        self.labels_for: set = set()
        self.inputs: List[Dict[str, str]] = []
        self._open_named: List[str] = []
        self._text_stack: List[str] = []
        self._line = 0

    # --- helpers -------------------------------------------------------
    def _a(self, attrs) -> Dict[str, str]:
        return {k.lower(): (v if v is not None else "") for k, v in attrs}

    def handle_starttag(self, tag, attrs):
        a = self._a(attrs)
        line = self.getpos()[0]

        if "id" in a and a["id"]:
            self.ids[a["id"]] = self.ids.get(a["id"], 0) + 1

        if tag == "img":
            self.imgs += 1
            has_dims = ("width" in a and "height" in a)
            styled = "aspect-ratio" in a.get("style", "")
            if not has_dims and not styled:
                self.errors.append(f"line {line}: <img> without width+height (CLS risk) src={a.get('src','')[:48]}")
            if "alt" not in a:
                self.errors.append(f"line {line}: <img> without alt attribute (a11y) src={a.get('src','')[:48]}")
            if not self.first_img_seen:
                self.first_img_seen = True
                if a.get("loading", "") == "lazy":
                    self.warnings.append(f"line {line}: first image is loading=lazy - LCP delay")

        if tag == "iframe":
            if not ("width" in a and "height" in a) and "aspect-ratio" not in a.get("style", ""):
                self.errors.append(f"line {line}: <iframe> without width+height (CLS risk)")
            if a.get("loading", "") != "lazy":
                self.warnings.append(f"line {line}: <iframe> should be loading=lazy")

        if tag == "script" and self.in_head:
            if "src" in a and "async" not in a and "defer" not in a and a.get("type", "") != "module":
                self.errors.append(f"line {line}: render-blocking <script> in <head> - add defer")

        if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            level = int(tag[1])
            self.headings.append(level)
            if tag == "h1":
                self.h1 += 1

        if tag == "label" and "for" in a:
            self.labels_for.add(a["for"])

        if tag in ("input", "select", "textarea"):
            kind = a.get("type", "text")
            decorative = a.get("aria-hidden", "") == "true" or "hidden" in a
            if kind not in ("hidden", "submit", "button", "reset") and not decorative:
                self.inputs.append({
                    "id": a.get("id", ""),
                    "aria": a.get("aria-label", "") or a.get("aria-labelledby", "") or a.get("title", ""),
                    "line": str(line),
                })

        if tag in ("a", "button"):
            self._open_named.append(tag)
            self._text_stack.append("")
            self._line = line
            aria = a.get("aria-label", "") or a.get("aria-labelledby", "") or a.get("title", "")
            # aria-hidden="true" (with tabindex="-1") is the standard pattern for a
            # decorative duplicate link/button: it is removed from the accessibility
            # tree on purpose, so demanding a name there would be a false positive.
            if aria or a.get("aria-hidden", "") == "true" or "hidden" in a:
                self._text_stack[-1] += "x"
            if tag == "a" and a.get("href", "").strip() in ("", "#"):
                self.warnings.append(f"line {line}: <a> without a real href")

    def handle_data(self, data):
        if self._text_stack and data.strip():
            self._text_stack[-1] += data.strip()

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag):
        if tag == "head":
            self.in_head = False
        if tag in ("a", "button") and self._open_named:
            opened = self._open_named.pop()
            text = self._text_stack.pop() if self._text_stack else ""
            if opened == tag and not text.strip():
                self.errors.append(f"line {self._line}: <{tag}> with no accessible name (a11y)")

    # --- summary -------------------------------------------------------
    def finish(self, html: str) -> None:
        for el_id, count in self.ids.items():
            if count > 1:
                self.errors.append(f"duplicate id used {count}x: #{el_id}")
        for field in self.inputs:
            if not field["aria"] and field["id"] not in self.labels_for:
                self.errors.append(f"line {field['line']}: form field without a label (a11y)")
        if self.h1 == 0:
            self.warnings.append("no <h1> on the page")
        elif self.h1 > 1:
            self.warnings.append(f"{self.h1} <h1> elements - keep one")
        if not re.search(r'<meta[^>]+name=["\']description["\']', html, re.I):
            self.warnings.append("no meta description")
        if "font-display" not in html and "@font-face" in html:
            self.warnings.append("@font-face without font-display:swap")


def audit_file(path: Path) -> Dict:
    html = path.read_text(encoding="utf-8", errors="ignore")
    a = Auditor()
    a.feed(html)
    a.finish(html)
    return {"file": str(path.relative_to(ROOT)), "errors": a.errors,
            "warnings": a.warnings, "images": a.imgs}


def main() -> int:
    targets = sorted(PREVIEW.rglob("*.html"))
    print("=" * 74)
    print(f"  CWV + A11Y STATIC AUDIT · {len(targets)} pages")
    print("=" * 74)
    total_e = total_w = 0
    for path in targets:
        rep = audit_file(path)
        total_e += len(rep["errors"])
        total_w += len(rep["warnings"])
        if rep["errors"] or rep["warnings"]:
            print(f"\n  {rep['file']}  ({rep['images']} images)")
            for e in rep["errors"][:12]:
                print(f"    ❌ {e}")
            for w in rep["warnings"][:8]:
                print(f"    ⚠️  {w}")
    print("-" * 74)
    print(f"  errors {total_e} · warnings {total_w}")
    if total_e == 0:
        print("  ✅ No CLS/a11y blockers in the markup.")
    print("  Note: real PageSpeed/CWV numbers come from the live site only.")
    return 1 if total_e else 0


if __name__ == "__main__":
    sys.exit(main())
