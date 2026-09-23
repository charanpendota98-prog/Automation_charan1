# -*- coding: utf-8 -*-
"""v105 — update backup, diff and rollback evidence.

A safe refresh must be reversible. Before any WordPress PUT, persist the exact
old content/meta/title plus the new candidate and provenance ledger. This is a
local safety net in addition to WordPress revisions.
"""
from __future__ import annotations

import difflib
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict

from . import config

log = logging.getLogger("autoblog.update_safety")


def _dir() -> Path:
    p = Path(getattr(config, "OUTPUT_DIR", Path("output"))) / "update_backups"
    p.mkdir(parents=True, exist_ok=True)
    return p


def _safe_id(post_id) -> str:
    return "".join(ch for ch in str(post_id) if ch.isalnum() or ch in "-_") or "unknown"


def create_backup(post: Dict, new_html: str, new_meta: Dict | None = None,
                  ledger: Dict | None = None) -> Dict:
    """Persist old state + candidate before the remote write."""
    post_id = post.get("id") or post.get("wp_id") or "unknown"
    old_content = (post.get("content") or {}).get("raw", "") or \
        (post.get("content") or {}).get("rendered", "") or ""
    old_title = (post.get("title") or {}).get("raw", "") or \
        (post.get("title") or {}).get("rendered", "") or ""
    old_meta = post.get("meta") or {}
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = _dir() / f"post-{_safe_id(post_id)}-{stamp}.json"
    old_text = old_content.splitlines(keepends=True)
    new_text = (new_html or "").splitlines(keepends=True)
    diff = "".join(difflib.unified_diff(old_text, new_text,
                                         fromfile="before", tofile="candidate"))
    record = {
        "version": "v105", "created_at": stamp, "post_id": post_id,
        "link": post.get("link", ""), "before": {
            "title": old_title, "content_html": old_content, "meta": old_meta,
            "date": post.get("date", ""), "modified": post.get("modified", ""),
        },
        "candidate": {"content_html": new_html or "", "meta": new_meta or {}},
        "diff": diff[:500000], "ledger": ledger or {}, "rollback_ready": True,
    }
    path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"path": str(path), "post_id": post_id, "bytes": path.stat().st_size,
            "diff_lines": len(diff.splitlines())}


def latest(post_id: int | str) -> Dict | None:
    files = sorted(_dir().glob(f"post-{_safe_id(post_id)}-*.json"), reverse=True)
    if not files:
        return None
    try:
        return json.loads(files[0].read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def rollback(wp, post_id: int | str, backup_path: str = "") -> Dict:
    """Restore exact title/content/meta from a selected backup.

    Explicit path preferred; otherwise latest backup for this post. No silent
    rollback: caller receives the restored link and backup path.
    """
    path = Path(backup_path) if backup_path else None
    if not path:
        got = latest(post_id)
        if not got:
            raise FileNotFoundError(f"backup ledu: post {post_id}")
        data = got
    else:
        data = json.loads(path.read_text(encoding="utf-8"))
    before = data["before"]
    result = wp.update_post(int(post_id), content_html=before["content_html"],
                            title=before["title"], excerpt="",
                            meta=before.get("meta") or {})
    return {"post_id": post_id, "restored": True, "link": result.get("link", ""),
            "backup": str(path) if path else "latest"}
