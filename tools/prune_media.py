# -*- coding: utf-8 -*-
"""v49 — keep hosting storage in check (MilesWeb/cPanel disk quota).

What it does (safe by default):
  * lists local generated images (output/ thumbs + media cache) and DB sizes
  * --days N   → deletes local image files older than N days (default 30)
  * --db-vacuum → VACUUMs SQLite state DBs (shrinks them after deletes)
  * dry-run unless --apply is passed

Published WordPress media is NEVER touched — only local working copies.

Usage:
  python tools/prune_media.py                 # report only
  python tools/prune_media.py --days 30 --apply
  python tools/prune_media.py --db-vacuum --apply
"""
from __future__ import annotations

import argparse
import os
import sqlite3
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MEDIA_GLOBS = ("output/**/*.jpg", "output/**/*.jpeg", "output/**/*.png",
               "output/**/*.webp", "media/**/*.jpg", "media/**/*.png")
DB_FILES = ("state.db", "service_center.db")  # v74: live-exam db poyindi (portal ledu)


def human(n: float) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return "%.1f %s" % (n, unit)
        n /= 1024.0
    return "%.1f GB" % n


def media_files() -> list[Path]:
    seen: dict[str, Path] = {}
    for pattern in MEDIA_GLOBS:
        for p in ROOT.glob(pattern):
            if p.is_file():
                seen[str(p)] = p
    return sorted(seen.values())


def report() -> None:
    files = media_files()
    total = sum(p.stat().st_size for p in files)
    print("=" * 66)
    print("  STUDENTUP STORAGE REPORT")
    print("=" * 66)
    print("  local images        : %4d files · %s" % (len(files), human(total)))
    for name in DB_FILES:
        p = ROOT / name
        if p.exists():
            print("  %-19s : %s" % (name, human(p.stat().st_size)))
    site = ROOT / "preview"
    if site.exists():
        site_bytes = sum(f.stat().st_size for f in site.rglob("*") if f.is_file())
        print("  public site (preview): %s" % human(site_bytes))
    print("-" * 66)
    print("  A 1200x675 JPEG post image ≈ 150–250 KB.")
    print("  1 post/day  → ~6 MB/month local · ~75 MB/year (thumbnails extra).")
    print("  MilesWeb base cPanel plan ≈ 50 GB disk → years of headroom;")
    print("  inodes (file count) matter more than size → prune old locals.")
    print("=" * 66)


def prune(days: int, apply: bool) -> int:
    cutoff = time.time() - days * 86400
    files = [p for p in media_files() if p.stat().st_mtime < cutoff]
    freed = sum(p.stat().st_size for p in files)
    print("  older than %d days: %d files · %s %s"
          % (days, len(files), human(freed), "(deleting)" if apply else "(dry-run)"))
    if apply:
        for p in files:
            try:
                p.unlink()
            except OSError as exc:
                print("    skip %s (%s)" % (p.name, exc))
    return len(files)


def vacuum(apply: bool) -> None:
    for name in DB_FILES:
        p = ROOT / name
        if not p.exists():
            continue
        before = p.stat().st_size
        if apply:
            try:
                with sqlite3.connect(str(p)) as conn:
                    conn.execute("VACUUM")
            except sqlite3.Error as exc:
                print("  %s: vacuum skip (%s)" % (name, exc))
                continue
        after = p.stat().st_size
        print("  %-18s %s → %s %s" % (name, human(before), human(after),
                                      "(vacuumed)" if apply else "(dry-run)"))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Prune local media / vacuum DBs")
    ap.add_argument("--days", type=int, default=30, help="delete images older than N days")
    ap.add_argument("--db-vacuum", action="store_true", help="VACUUM sqlite state DBs")
    ap.add_argument("--apply", action="store_true", help="actually delete/write (default: dry-run)")
    args = ap.parse_args(argv)

    report()
    if args.days > 0:
        prune(args.days, args.apply)
    if args.db_vacuum:
        vacuum(args.apply)
    if not args.apply:
        print("  (dry-run) add --apply to really delete/vacuum")
    return 0


if __name__ == "__main__":
    sys.exit(main())
