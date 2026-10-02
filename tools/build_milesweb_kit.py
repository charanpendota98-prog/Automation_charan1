# -*- coding: utf-8 -*-
"""v175: MilesWeb (cPanel) deploy kit — zip upload chesi live cheyyadaniki ready bundle.

Enduku: MilesWeb lo "zip upload chesi live" anedi 3 chotla jarugutundi —
  1) WordPress theme      → WP Admin → Appearance → Themes → Upload  (studentup-theme-*.zip)
  2) Static preview site  → cPanel File Manager → public_html         (studentup-static-site.zip)
  3) Bot (cron)           → cPanel File Manager → ~/bot               (studentup-bot-cron.zip)
Ee tool aa moodu zips ni okate command tho build + verify chestundi
(reproducible: fixed timestamps ⇒ same sha256 prathi machine lo).

Usage:
    python3 tools/build_milesweb_kit.py            # build → milesweb-kit/
    python3 tools/build_milesweb_kit.py --out DIR  # vere folder
    python3 tools/build_milesweb_kit.py --list     # build cheyyakunda enti vastundo chudu

Tarvata: `milesweb-kit/MILESWEB-GO-LIVE.md` chudandi (step-by-step).
"""
from __future__ import annotations

import argparse
import hashlib
import re
import shutil
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUT = ROOT / "milesweb-kit"

# Reproducible artifacts: prathi entry ki same timestamp ⇒ same sha256.
FIXED = (2026, 1, 1, 0, 0, 0)
SKIP_DIRS = {"__pycache__", ".git", "node_modules", ".venv", "venv", ".mypy_cache",
             ".pytest_cache", "milesweb-kit"}
SKIP_SUFFIX = {".pyc", ".pyo", ".log", ".db", ".db-journal", ".db-shm", ".db-wal"}
SKIP_NAMES = {".env", "state.db", "push_keys.json", "adsense_kit.json",
              "design_kit.json", "quiz_kit.json", "service_center.db",
              "service_center.json", "sources_queue.txt"}

KIT_HELPERS = ("MILESWEB_GO_LIVE.md", "DEPLOY_MILESWEB.md", "GO_LIVE_CHECKLIST.md")


# ----------------------------------------------------------------- helpers

def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _skip(path: Path) -> bool:
    if any(part in SKIP_DIRS for part in path.parts):
        return True
    if path.name in SKIP_NAMES or path.suffix in SKIP_SUFFIX:
        return True
    return False


def _write_zip(out: Path, entries) -> tuple[int, int]:
    """Deterministic zip: fixed date_time + 0644 + sorted entries.

    `entries` = iterable of (arcname, source_file_path).
    """
    out.parent.mkdir(parents=True, exist_ok=True)
    rows = sorted(entries, key=lambda kv: kv[0])
    files = 0
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        for arcname, src in rows:
            info = zipfile.ZipInfo(arcname, date_time=FIXED)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            zf.writestr(info, src.read_bytes())
            files += 1
    return files, out.stat().st_size


def _tree(base: Path, prefix: str = "", skip: bool = True):
    """(arcname, path) pairs — `prefix` tho zip-lopala folder structure vastundi."""
    for p in sorted(base.rglob("*")):
        if p.is_dir():
            continue
        if skip and _skip(p.relative_to(ROOT)):
            continue
        yield prefix + p.relative_to(base).as_posix(), p


# ----------------------------------------------------------------- builds

def build_theme_zip(out_dir: Path) -> tuple[Path, int, int]:
    src = ROOT / "wordpress-theme" / "studentup-theme.zip"
    if not src.exists():
        raise SystemExit("⛔ theme zip ledu — mundu: python3 tools/build_wp_theme.py")
    ver = _theme_version()
    out = out_dir / f"studentup-theme-{ver}.zip"
    shutil.copyfile(src, out)
    with zipfile.ZipFile(out) as zf:
        names = zf.namelist()
    if "studentup/style.css" not in names or "studentup/functions.php" not in names:
        raise SystemExit("⛔ theme zip structure tappu (studentup/ root ledu)")
    return out, len(names), out.stat().st_size


def build_plugin_zip(out_dir: Path) -> tuple[Path, int, int]:
    src = ROOT / "wordpress-plugin" / "studentup-seo-bridge"
    php = src / "studentup-seo-bridge.php"
    if not php.exists():
        raise SystemExit("⛔ plugin source ledu (wordpress-plugin/studentup-seo-bridge)")
    m = re.search(r"Version:\s*(\S+)", php.read_text(encoding="utf-8"))
    ver = m.group(1) if m else "0.0.0"
    out = out_dir / f"studentup-seo-bridge-{ver}.zip"
    files, size = _write_zip(out, _tree(src, prefix="studentup-seo-bridge/"))
    return out, files, size


def build_static_zip(out_dir: Path) -> tuple[Path, int, int]:
    prev = ROOT / "preview"
    if not (prev / "index.html").exists():
        raise SystemExit("⛔ preview/index.html ledu")
    out = out_dir / "studentup-static-site.zip"
    # public_html loki direct extract avvali ⇒ zip root lo files ye (folder ledu)
    files, size = _write_zip(out, _tree(prev))
    with zipfile.ZipFile(out) as zf:
        names = set(zf.namelist())
    for need in ("index.html", "robots.txt", "sitemap.xml", "ads.txt",
                 "manifest.webmanifest", "sw.js", "data/breaking.json"):
        if need not in names:
            raise SystemExit(f"⛔ static zip lo '{need}' ledu")
    return out, files, size


BOT_DOCS = [
    "README.md", "START_HERE.md", "GO_LIVE_CHECKLIST.md", "DEPLOY.md",
    "DEPLOY_MILESWEB.md", "DEPLOY_ORACLE_CLOUD.md", "MANUAL_ADVANCED_CHECKLIST.md",
    "MILESWEB_GO_LIVE.md", "CONTENT_PLAN_DAILY.md", "AD_REVENUE_PLAYBOOK.md",
    "AD_STRATEGY_ADVANCED.md", "AD_NETWORKS_PLAN.md", "AD_NETWORKS_APPLICATION_KIT.md",
    "ACTIVE_OPPORTUNITIES.md", "SALES_KIT_ADVERTISERS.md", "SUCCESS_STORY_FORM.md",
    "THUMBNAIL_PROMPT.md", "WP_ADVANCED_CUSTOMIZATION.md",
]
BOT_TOP_FILES = ["run.py", "requirements.txt", "crontab.example", ".env.example",
                 "deploy.sh", "setup_oracle.sh", "hotfix_v24.sh"]
BOT_DIRS = ["autoblog", "tools", "ads", "deploy", "docs", "ci", "preview",
            "wordpress-theme", "wordpress-plugin"]
# tests/ teesestunnam (17 MB; CI/GitHub lo run avutayi) — ee zip cron bot ki.


def build_bot_zip(out_dir: Path) -> tuple[Path, int, int]:
    entries = []
    for name in BOT_TOP_FILES:
        p = ROOT / name
        if p.exists():
            entries.append((name, p))
    for doc in BOT_DOCS:
        p = ROOT / doc
        if p.exists():
            entries.append((doc, p))
    for d in BOT_DIRS:
        base = ROOT / d
        if base.exists():
            entries.extend(_tree(base, prefix=d + "/"))
    out = out_dir / "studentup-bot-cron.zip"
    files, size = _write_zip(out, entries)
    with zipfile.ZipFile(out) as zf:
        names = set(zf.namelist())
    for need in ("run.py", "requirements.txt", "autoblog/main.py", "autoblog/pipeline.py",
                 "tools/build_wp_theme.py", "preview/index.html",
                 "wordpress-theme/studentup/style.css", "crontab.example", ".env.example"):
        if need not in names:
            raise SystemExit(f"⛔ bot zip lo '{need}' ledu (cron/deploy-check fail avutundi)")
    return out, files, size


def _theme_version() -> str:
    css = (ROOT / "wordpress-theme" / "studentup" / "style.css").read_text(encoding="utf-8")
    m = re.search(r"^Version:\s*(\S+)", css, re.M)
    return m.group(1) if m else "0.0.0"


# ----------------------------------------------------------------- main

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="MilesWeb deploy kit builder (v175)")
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    ap.add_argument("--list", action="store_true", help="build cheyyakunda contents chudu")
    args = ap.parse_args(argv)
    out_dir = Path(args.out)

    print("=" * 70)
    print("  📦 MILESWEB DEPLOY KIT (cPanel · zip upload)")
    print("=" * 70)
    if args.list:
        print("  ee zips build avutayi:")
        print(f"    · studentup-theme-{_theme_version()}.zip      → WP Admin → Themes → Upload")
        print("    · studentup-seo-bridge-<ver>.zip    → WP Admin → Plugins → Upload")
        print("    · studentup-static-site.zip         → cPanel → public_html/ (static option)")
        print("    · studentup-bot-cron.zip            → cPanel → ~/bot (cron bot)")
        print("  + SHA256SUMS.txt · MILESWEB-GO-LIVE.md")
        return 0

    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    # 0) theme zip fresh-a? (stale zip = puratana theme live ki vellipovachu)
    try:
        from autoblog.theme_pack import stale_detail, theme_zip_stale_files

        stale = theme_zip_stale_files(ROOT / "wordpress-theme" / "studentup",
                                      ROOT / "wordpress-theme" / "studentup-theme.zip")
    except Exception as exc:  # noqa: BLE001
        stale, stale_detail = [], lambda _s: str(exc)  # type: ignore[assignment]
    if stale:
        print(f"  ⛔ theme zip stale ({stale_detail(stale)}) — mundu run cheyandi:")
        print("     python3 tools/build_wp_theme.py")
        return 1

    out_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    for label, fn in (("WordPress theme", build_theme_zip),
                      ("SEO bridge plugin", build_plugin_zip),
                      ("Static site (public_html)", build_static_zip),
                      ("Bot (cron, ~/bot)", build_bot_zip)):
        path, files, size = fn(out_dir)
        sha = _sha256(path)
        rows.append((label, path.name, files, size, sha))
        print(f"  ✅ {label:26s} {path.name:36s} {files:4d} files · {size/1024:7.0f} KB")

    # upload guide + checksums
    guide = ROOT / "MILESWEB_GO_LIVE.md"
    if guide.exists():
        shutil.copyfile(guide, out_dir / "MILESWEB_GO_LIVE.md")
    sums = out_dir / "SHA256SUMS.txt"
    with sums.open("w", encoding="utf-8") as fh:
        fh.write("# StudentUp — MilesWeb kit sha256 (upload verify cheyyadaniki)\n")
        for _, name, _, _, sha in sorted(rows, key=lambda r: r[1]):
            fh.write(f"{sha}  {name}\n")
        fh.write("# verify: sha256sum -c SHA256SUMS.txt   (leda: sha256sum <zip>)\n")

    print("-" * 70)
    print("  sha256 (upload tarvata verify cheyandi):")
    for _, name, _, _, sha in rows:
        print(f"    {sha[:16]}…  {name}")
    print("-" * 70)
    print(f"  📂 kit: {out_dir}")
    print("  📖 steps: milesweb-kit/MILESWEB-GO-LIVE.md")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
