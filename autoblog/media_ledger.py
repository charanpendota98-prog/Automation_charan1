# -*- coding: utf-8 -*-
"""v108 — featured image originality, naming and licence ledger."""
from __future__ import annotations
import hashlib
import json
from datetime import date
from pathlib import Path
from typing import Dict
from . import config


def _root() -> Path:
    p = Path(config.OUTPUT_DIR) / "media_ledger"
    p.mkdir(parents=True, exist_ok=True)
    return p


def record(path: Path, slug: str, alt: str, media_id=None, url: str = "",
           source: str = "generated-local", licence: str = "original-generated") -> Dict:
    data = path.read_bytes()
    width = height = None
    try:
        from PIL import Image
        with Image.open(path) as im:
            width, height = im.size
    except Exception:  # noqa: BLE001
        pass
    item = {
        "version": "v108", "checked_at": date.today().isoformat(),
        "slug": slug, "filename": path.name, "sha256": hashlib.sha256(data).hexdigest(),
        "bytes": len(data), "width": width, "height": height,
        "alt": alt, "media_id": media_id, "url": url,
        "source": source, "licence": licence,
        "duplicate_safe": True,
    }
    out = _root() / f"{slug or 'image'}.json"
    out.write_text(json.dumps(item, ensure_ascii=False, indent=2), encoding="utf-8")
    return item


def duplicate_hash(sha256: str, exclude_slug: str = "") -> str:
    for p in _root().glob("*.json"):
        if p.stem == exclude_slug:
            continue
        try:
            if json.loads(p.read_text(encoding="utf-8")).get("sha256") == sha256:
                return p.stem
        except (OSError, ValueError):
            continue
    return ""
