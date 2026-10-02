# -*- coding: utf-8 -*-
"""Theme zip ↔ source parity (v175) — content-based freshness check.

Enduku content-based (mtime kaadu):
  Mundu "zip mtime >= newest source mtime" polika vadadam valla `--test-all`
  order-dependent ga fail ayyedi. Suites minify / critical CSS / POT ni
  regenerate chestayi — **content same**, kaani mtime kotha → "zip stale" false
  alarm (guardian + suites). Byte-to-byte polika nijamga "zip stale-a?" ki
  jawabu istundi: WP upload lo puratana theme vellipovadam aaputundi.

Rules `tools/build_wp_theme.py` `package()` tho **okate** (rendu ikkadi nunchi
import chestayi, drift ledu):
  · SKIP_DIRS  — __pycache__ / .git / node_modules
  · PACKAGE_SKIP — critical.css (build intermediate; zip lo critical.min.css ye)

Usage:
    from autoblog.theme_pack import theme_zip_stale_files, theme_zip_fresh

    stale = theme_zip_stale_files(theme_dir, zip_path)
"""
from __future__ import annotations

import zipfile
from pathlib import Path
from typing import List

# tools/build_wp_theme.py idi ikkadi nunchi import chestundi (single source).
SKIP_DIRS = {"__pycache__", ".git", "node_modules"}
PACKAGE_SKIP = {"critical.css"}  # v171: unminified intermediate — ship kaadu

ZIP_ROOT = "studentup"  # zip lo top-level folder (WP install structure)


def packaged_rel_paths(theme_dir: Path) -> List[str]:
    """Zip lo undalsina file paths (`studentup/...` prefix tho), build order lo."""
    out: List[str] = []
    for path in sorted(theme_dir.rglob("*")):
        if path.is_dir() or any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.name in PACKAGE_SKIP:
            continue
        out.append(f"{ZIP_ROOT}/" + path.relative_to(theme_dir).as_posix())
    return out


def theme_zip_stale_files(theme_dir: Path, zip_path: Path) -> List[str]:
    """Zip lo missing / different ga unna files (empty list = zip fresh).

    Corrupt zip ki `["<zip corrupt>"]` return chestundi — crash avvadu.
    """
    prefix = ZIP_ROOT + "/"
    try:
        with zipfile.ZipFile(zip_path) as zf:
            packed = set(zf.namelist())
            stale: List[str] = []
            for rel in packaged_rel_paths(theme_dir):
                src = theme_dir / rel[len(prefix):]
                if rel not in packed:
                    stale.append(rel)
                elif zf.read(rel) != src.read_bytes():
                    stale.append(rel)
            return stale
    except zipfile.BadZipFile:
        return ["<zip corrupt>"]


def theme_zip_fresh(theme_dir: Path, zip_path: Path) -> bool:
    """True = zip lo unna bytes anni ippati source tho same (rebuild avasaram ledu)."""
    return not theme_zip_stale_files(theme_dir, zip_path)


def stale_detail(stale_files: List[str], limit: int = 1) -> str:
    """Guardian/test messages ki short detail (`a.php (+3 more)`)."""
    if not stale_files:
        return ""
    head = stale_files[0]
    rest = len(stale_files) - limit
    return head + (f" (+{rest} more)" if rest > 0 else "")
