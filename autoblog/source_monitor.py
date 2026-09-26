"""Read-only source freshness monitor for published source-backed posts.

It fingerprints the fetched source text and alerts the owner when a source
changes. It never rewrites a post automatically: a changed official notice is
queued for the existing in-place update workflow and human review.
"""
from __future__ import annotations

import hashlib
import json
import logging
from datetime import date
from pathlib import Path
from typing import Dict, List, Optional

from . import config, sources
from .notifier import send_telegram
from .wordpress_client import WordPressClient

log = logging.getLogger("autoblog.source_monitor")


def _load(path: Path) -> Dict[str, Dict]:
    try:
        data = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        log.exception("source monitor state could not be read")
        return {}


def _save(path: Path, data: Dict[str, Dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


def _fingerprint(text: str) -> str:
    normalized = " ".join((text or "").split())
    return hashlib.sha256(normalized.encode("utf-8", "ignore")).hexdigest()


def scan(
    wp: Optional[WordPressClient] = None,
    limit: Optional[int] = None,
    notify: bool = False,
) -> Dict:
    """Scan published source-backed posts and return change rows.

    First run records a baseline. A source that later changes becomes a
    ``changed`` row; no WordPress content is modified by this command.
    """
    if not getattr(config, "SOURCE_MONITOR_ENABLED", True):
        return {"ok": True, "disabled": True, "scanned": 0, "changed": [], "errors": []}
    client = wp or WordPressClient()
    rows = client.published_opportunities(
        max_pages=max(1, ((limit or config.SOURCE_MONITOR_MAX_POSTS) + 99) // 100),
        per_page=100,
    )
    rows = rows[: max(1, int(limit or config.SOURCE_MONITOR_MAX_POSTS))]
    state_path = getattr(config, "SOURCE_MONITOR_STATE", Path("logs/source-monitor.json"))
    state = _load(Path(state_path))
    changed: List[Dict] = []
    errors: List[Dict] = []
    scanned = 0

    for row in rows:
        url = str(row.get("source_url") or "").strip()
        if not url or not sources.is_valid_source_url(url):
            continue
        scanned += 1
        try:
            source = sources.fetch_source(url)
            current = _fingerprint(source.text)
            old = state.get(url) or {}
            state[url] = {
                "fingerprint": current,
                "checked": date.today().isoformat(),
                "post_id": row.get("id"),
                "post_link": row.get("link", ""),
                "title": row.get("title", ""),
            }
            if old.get("fingerprint") and old.get("fingerprint") != current:
                changed.append({
                    "post_id": row.get("id"), "title": row.get("title", ""),
                    "post_link": row.get("link", ""), "source_url": url,
                    "reason": "source content changed; review updated dates/fees/status",
                })
        except Exception as exc:  # noqa: BLE001 — one source must not stop the scan
            errors.append({"post_id": row.get("id"), "source_url": url, "error": str(exc)[:180]})
            log.warning("source monitor failed for %s: %s", url[:100], exc)

    _save(Path(state_path), state)
    result = {"ok": not errors, "disabled": False, "scanned": scanned,
              "changed": changed, "errors": errors, "state": str(state_path)}
    if notify and changed:
        lines = ["⚠️ <b>Source update review needed</b>",
                 "Official source text changed; no post was auto-edited."]
        for item in changed[:12]:
            lines.append(f"• #{item.get('post_id')} {item.get('title', '')[:80]}")
            lines.append(f"  Source: {item.get('source_url', '')}")
        send_telegram("\n".join(lines))
    return result


def run_cli(notify: bool = False) -> int:
    result = scan(notify=notify)
    print("=" * 62)
    print("  SOURCE FRESHNESS MONITOR — read-only")
    print("=" * 62)
    if result.get("disabled"):
        print("  disabled: SOURCE_MONITOR_ENABLED=0")
        return 0
    print(f"  source-backed posts scanned: {result['scanned']}")
    print(f"  changed sources: {len(result['changed'])}")
    print(f"  fetch errors: {len(result['errors'])}")
    for item in result["changed"]:
        print(f"  ⚠️ post {item.get('post_id')}: {item.get('title', '')[:80]}")
    print("  No post was auto-edited; review the source and run the in-place update flow.")
    print("=" * 62)
    return 0 if not result["errors"] else 1
