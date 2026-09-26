"""Re-fetch source evidence immediately before an article is drafted.

Search results and an earlier research fetch are discovery inputs, not a
publishing licence.  This small helper is deliberately fail-closed: if a
source cannot be fetched again, the caller keeps the work out of the draft
workflow instead of silently drafting from stale text.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable, List, Tuple

from . import sources


def refresh(source_set: Iterable[object]) -> Tuple[object, List[object], str]:
    """Re-fetch every source and return fresh primary/secondary evidence.

    The first item is treated as the primary source.  A failed fetch or a
    response with no useful text raises, so callers cannot accidentally pass
    stale research into generation.
    """
    source_list = list(source_set or [])
    if not source_list:
        raise ValueError("SOURCE RECHECK FAILED: no source evidence was supplied")

    fresh = []
    for index, item in enumerate(source_list):
        url = str(getattr(item, "url", "") or (item.get("url", "") if isinstance(item, dict) else "")).strip()
        if not sources.is_valid_source_url(url):
            raise ValueError(f"SOURCE RECHECK FAILED: invalid source URL at position {index + 1}")
        checked = sources.fetch_source(url)
        text = str(getattr(checked, "text", "") or "")
        status = int(getattr(checked, "status_code", 200) or 0)
        if status >= 400 or len(text.strip()) < 120:
            raise ValueError(
                f"SOURCE RECHECK FAILED: source unavailable or too thin ({url[:120]})"
            )
        fresh.append(checked)

    return fresh[0], fresh[1:], datetime.now(timezone.utc).isoformat()
