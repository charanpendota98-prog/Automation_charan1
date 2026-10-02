# -*- coding: utf-8 -*-
"""v187 — MULTI-LINK INTAKE (oka list lo unna links → **prathi okkati veru draft**).

Mee use case: WhatsApp/notes nunchi ila oka list paste chestaru —

    1. **ECIL (310 ITI Trade Apprentice Posts)**
       - [https://www.ecil.co.in](https://www.ecil.co.in)
    2. **IIT Hyderabad (Project Associate Positions)**
       - [https://www.iith.ac.in/careers](https://www.iith.ac.in/careers)

Ippati varaku bot okka URL ni okka draft ga chesedi (`run.py <url>`), leda
topics queue lo text ni research chesi draft chesedi. Ee module **oka file/line
lo unna anni links ni** teesukoni, **prathi link ki veru veru draft** chestundi:

    python run.py --links-file links.txt        # file nunchi (markdown/plain)
    python run.py --links "https://a.com/x, https://b.com/y"

Niyamalu (doctrine):
  * Prathi draft aa **oka source URL** meeda ne build avutundi — copy ledu
    (pipeline no-copy + fact gates same), kanukaleka poye source skip (honest).
  * Same source URL malli isthe pipeline **refresh** chestundi (duplicate post ledu).
  * Run ki max `--links-limit` (default `LINK_INTAKE_MAX=10`) — roju 100 links
    vesthe spam pattern avutundi, so throttle built-in.
  * Label (list lo unna peru) report lo mattrame vadutamu — article title ni
    bot ne SEO + keyword matrix nunchi vastundi (guess ledu).
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Tuple

URL_RE = re.compile(r"https?://[^\s\)\]\>,;\"'<>]+")
LABEL_SKIP_RE = re.compile(r"^\s*(?:[-*•]|\d+[.)])\s*$")


def clean_url(url: str) -> str:
    """Trailing punctuation / markdown balam teesi, canonical URL ni return."""
    url = (url or "").strip().rstrip(").,;:'\"")
    return url


def parse_links(text: str) -> List[Tuple[str, str]]:
    """Text nunchi (label, url) pairs — markdown/plain/WhatsApp paste anni support.

    Label = URL mundu unna line (e.g. "1. **ECIL (310 posts)**"), lekapote "".
    Okate URL rendu sari unte okkatiki trim chestamu (order preserve).
    """
    out: List[Tuple[str, str]] = []
    seen = set()
    last_label = ""
    for raw_line in (text or "").splitlines():
        line = raw_line.rstrip()
        urls = URL_RE.findall(line)
        if not urls:
            candidate = re.sub(r"[*_`#]", "", line).strip()
            candidate = re.sub(r"^\d+[.)]\s*", "", candidate).strip()
            if candidate and not LABEL_SKIP_RE.match(line):
                last_label = candidate[:120]
            continue
        for url in urls:
            url = clean_url(url)
            if not url or url in seen:
                continue
            seen.add(url)
            # Label priority: same line text (markdown link text) → previous line
            label = ""
            m = re.search(r"\[([^\]]{3,120})\]\(", line)
            md_text = re.sub(r"[*_`]", "", m.group(1)).strip() if m else ""
            if md_text and "http" not in md_text.lower():
                label = md_text            # markdown link text nijamaina peru aithe
            elif last_label:
                label = last_label          # lekapote mundu line lo unna peru
            out.append((label[:120], url))
        last_label = ""
    return out


def load_links(source: str = "", file_path: str = "") -> List[Tuple[str, str]]:
    """`--links` string leda `--links-file` nunchi pairs (rendu kalipi ivvachu)."""
    chunks: List[str] = []
    if file_path:
        p = Path(file_path)
        if not p.exists():
            raise FileNotFoundError(f"links file dorakaledu: {file_path}")
        chunks.append(p.read_text(encoding="utf-8"))
    if source:
        chunks.append(source)
    pairs: List[Tuple[str, str]] = []
    seen = set()
    for chunk in chunks:
        for label, url in parse_links(chunk):
            if url in seen:
                continue
            seen.add(url)
            pairs.append((label, url))
    return pairs


def intake(pairs: Iterable[Tuple[str, str]], limit: int = 10, dry_run: bool = False,
           creator: Callable[..., Dict] | None = None) -> Dict:
    """Prathi link ki veru draft. Returns {created, refreshed, failed, skipped, items}.

    `creator` inject cheyyachu (tests lo fake) — default `pipeline.create_from_source`.
    """
    items: List[Dict] = []
    created = refreshed = failed = skipped = 0
    todo = list(pairs)
    over_limit = max(0, len(todo) - max(1, int(limit)))
    if over_limit:
        todo = todo[: max(1, int(limit))]
    if dry_run:
        return {"created": 0, "refreshed": 0, "failed": 0, "skipped": over_limit,
                "dry_run": True,
                "items": [{"label": l, "url": u, "status": "planned"} for l, u in todo]}

    if creator is None:
        from . import pipeline

        def creator(url, **_kw):  # type: ignore[misc]
            return pipeline.create_from_source(url, force_draft=True)

    for label, url in todo:
        try:
            result = creator(url)
        except Exception as exc:  # noqa: BLE001 — okka link fail aithe migilinavi continue
            failed += 1
            items.append({"label": label, "url": url, "status": "failed",
                          "detail": f"{exc.__class__.__name__}: {exc}"[:200]})
            continue
        status = str((result or {}).get("status") or "").lower()
        link = (result or {}).get("link", "")
        if status in ("refresh", "updated") or (result or {}).get("refreshed"):
            refreshed += 1
            kind = "refreshed"
        else:
            created += 1
            kind = "created"
        items.append({"label": label, "url": url, "status": kind, "post": link})
    return {"created": created, "refreshed": refreshed, "failed": failed,
            "skipped": over_limit, "dry_run": False, "items": items}


def report_text(rep: Dict, limit: int = 10) -> str:
    icon = {"created": "✅", "refreshed": "♻️", "failed": "❌", "planned": "🧪"}
    lines = [f"🔗 MULTI-LINK INTAKE — {rep['created']} kotha draft · "
             f"{rep['refreshed']} refresh · {rep['failed']} fail"
             + (f" · {rep['skipped']} skip (limit {limit}/run)" if rep.get("skipped") else "")]
    for row in rep.get("items", []):
        head = row.get("label") or row.get("url", "")
        note = row.get("post") or row.get("detail", "")
        lines.append(f"   {icon.get(row['status'], '•')} [{row['status']}] {head[:70]}"
                     + (f" — {note[:70]}" if note else ""))
    if rep.get("dry_run"):
        lines.append("   ℹ️ dry-run — eem create cheyyaledu (plan mattrame)")
    return "\n".join(lines)


def run_cli(links: str = "", file_path: str = "", limit: int = 0, dry_run: bool = False,
            notify: bool = False) -> int:
    from . import config

    if not limit:
        limit = int(getattr(config, "LINK_INTAKE_MAX", 10) or 10)
    try:
        pairs = load_links(links, file_path)
    except FileNotFoundError as exc:
        print(f"  ❌ {exc}")
        return 2
    if not pairs:
        print("  ❌ links dorakaledu — `--links \"https://...\"` leda "
              "`--links-file links.txt` ivvandi (oka line okka link).")
        return 2
    print(f"  🔗 {len(pairs)} links dorikayi · limit {limit}/run")
    rep = intake(pairs, limit=limit, dry_run=dry_run)
    print(report_text(rep, limit))
    out = Path(getattr(config, "LINK_INTAKE_REPORT",
                       config.OUTPUT_DIR / "link-intake.json"))
    try:
        import json

        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(rep, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"  📄 {out}")
    except OSError as exc:
        print(f"  ⚠️ report save fail: {exc}")
    if notify:
        try:
            from . import notifier

            notifier.send_telegram(
                f"🔗 <b>Link intake</b> — {rep['created']} drafts · "
                f"{rep['refreshed']} refresh · {rep['failed']} fail")
        except Exception as exc:  # noqa: BLE001 — notify fail intake ni aapadu
            print(f"  ⚠️ notify fail: {exc}")
    if dry_run:
        return 0
    return 0 if rep["created"] or rep["refreshed"] else 1
