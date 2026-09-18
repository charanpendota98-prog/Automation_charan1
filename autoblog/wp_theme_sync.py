# -*- coding: utf-8 -*-
"""v61: WordPress theme sync — bot data ni site theme ki push.

Enti idi:
  Mee website WordPress + StudentUp theme (v61) tho nadustundi. Theme ki data
  (బ్రేకింగ్ items · trust numbers · deadline countdown · house ads) bot nunchi
  vellali — appudu site eppudu fresh ga untundi, manual copy-paste ledu.

Endpoint (theme lo register ayyindi):
  POST {WP_BASE}/wp-json/studentup/v1/theme-data
  auth: WP_USERNAME + WP_APP_PASSWORD (Application Password), edit_posts chaalu.

Nijam: WP creds lekapote skip (silent fail ledu — clear message).
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

import requests

from . import config

log = logging.getLogger("autoblog.wp_theme")

REST_PATH = "/wp-json/studentup/v1/theme-data"


# ---------------------------------------------------------------------------
# payload builders (offline testable)
# ---------------------------------------------------------------------------

def build_payload(root: Optional[Path] = None,
                  include: Optional[List[str]] = None) -> Dict[str, object]:
    """Local files nunchi theme payload — breaking + house ads + proof + deadline."""
    root = Path(root or config.BASE_DIR)
    include = include or ["breaking", "house_ads", "proof", "deadline"]
    out: Dict[str, object] = {}

    if "breaking" in include:
        feed = root / "preview" / "data" / "breaking.json"
        try:
            data = json.loads(feed.read_text(encoding="utf-8"))
            items = [x for x in data.get("items", []) if isinstance(x, dict)]
            out["breaking"] = items[:8]
        except Exception as exc:  # noqa: BLE001
            log.debug("breaking feed read skip: %s", exc)

    if "house_ads" in include:
        house = root / "ads" / "house.json"
        try:
            data = json.loads(house.read_text(encoding="utf-8"))
            rows = data if isinstance(data, list) else data.get("ads", [])
            out["house_ads"] = [x for x in rows if isinstance(x, dict)][:6]
        except Exception as exc:  # noqa: BLE001
            log.debug("house ads read skip: %s", exc)

    if "proof" in include:
        try:
            from . import sources_grid, top_post

            out["proof"] = {
                "keywords": len(top_post.keyword_universe()),
                "entities": len(top_post.ENTITIES),
                "sources": len(sources_grid.SOURCES_GRID),
                "categories": len(config.CATEGORIES),
            }
        except Exception as exc:  # noqa: BLE001
            log.debug("proof build skip: %s", exc)

    if "deadline" in include:
        # .env / option driven: POST_DEADLINE_TITLE + POST_DEADLINE_ISO
        title = (getattr(config, "POST_DEADLINE_TITLE", "") or "").strip()
        iso = (getattr(config, "POST_DEADLINE_ISO", "") or "").strip()
        if title and iso:
            out["deadline"] = {"title": title, "date": iso}

    return out


# ---------------------------------------------------------------------------
# push
# ---------------------------------------------------------------------------

def push(payload: Optional[Dict[str, object]] = None, dry_run: bool = False,
         timeout: int = 20) -> Dict[str, object]:
    """Payload ni WP REST ki POST. Returns summary dict (never raises)."""
    payload = payload if payload is not None else build_payload()
    empty = {k: (len(v) if isinstance(v, list) else v) for k, v in payload.items()}
    if not payload:
        return {"ok": False, "sent": {}, "reason": "payload khali — push cheyyalsinadi ledu"}
    if dry_run:
        return {"ok": True, "dry_run": True, "sent": empty,
                "reason": "dry-run — network call cheyyaledu"}

    base = (getattr(config, "WP_SITE", "") or "").rstrip("/")
    user = getattr(config, "WP_USERNAME", "")
    app_pw = getattr(config, "WP_APP_PASSWORD", "")
    if not (base and user and app_pw):
        return {"ok": False, "sent": empty,
                "reason": "WP creds ledu (.env: WP_SITE/WP_USERNAME/WP_APP_PASSWORD)"}
    url = base + REST_PATH
    try:
        resp = requests.post(url, json=payload, auth=(user, app_pw), timeout=timeout)
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "sent": empty, "reason": f"{type(exc).__name__}: {exc}"}
    if resp.status_code != 200:
        return {"ok": False, "sent": empty,
                "reason": f"HTTP {resp.status_code}: {resp.text[:180]}"}
    try:
        data = resp.json()
    except ValueError:
        data = {}
    return {"ok": bool(data.get("ok", True)), "sent": empty,
            "updated": data.get("updated", []), "url": url}
