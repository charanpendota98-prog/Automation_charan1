"""v28 AdSense Auto Ads kit.

The kit installs only Google's publisher loader, not ad units or click-oriented
markup. It is delivered through one idempotent footer text widget so it can run
on posts, archives, and the homepage without editing theme files. A real,
validated ``ca-pub-...`` id is required; an empty or malformed id never reaches
WordPress.

This is intentionally not a fake AdSense approval/income guarantee. AdSense
approval, ads.txt, consent requirements, and ad serving remain Google-side
checks and are reported as manual follow-ups by the CLI.
"""
from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlencode

from . import config

log = logging.getLogger("autoblog.adsense")

MARKER = "suads28"
CLIENT_RE = re.compile(r"^ca-pub-(\d{6,20})$")


def normalize_client_id(value: str = "") -> Optional[str]:
    """Return a canonical client id, or None for unsafe/mistyped input."""
    value = (value or "").strip()
    return value if CLIENT_RE.fullmatch(value) else None


def publisher_id(client_id: str = "") -> Optional[str]:
    client_id = normalize_client_id(client_id)
    return client_id[7:] if client_id else None


def build_widget_html(client_id: str = "") -> str:
    """Build the loader only; never emit a script for an invalid id."""
    client_id = normalize_client_id(client_id or config.ADSENSE_CLIENT_ID)
    if (not client_id or not config.ADSENSE_AUTO_ADS
            or not getattr(config, "ADSENSE_APPROVED", False)):
        return ""
    return (
        f'<div id="su-adsense-loader"><!--{MARKER}-->'
        '<script async src="https://pagead2.googlesyndication.com/'
        f'pagead/js/adsbygoogle.js?client={client_id}" '
        'crossorigin="anonymous"></script></div>'
    )


def audit() -> Tuple[str, str]:
    """Local config audit, with actionable but honest status text."""
    if not config.ADSENSE_ENABLED:
        return "SKIP", "ADSENSE_ENABLED=0 — no ad code will be emitted"
    if not getattr(config, "ADSENSE_APPROVED", False):
        return "SKIP", "ADSENSE_APPROVED=0 — pre-approval mode; no ad spaces or loader"
    if not config.ADSENSE_CLIENT_ID:
        return "SKIP", "ADSENSE_CLIENT_ID empty — add ca-pub-... after AdSense approval"
    if not normalize_client_id(config.ADSENSE_CLIENT_ID):
        return "WARN", "ADSENSE_CLIENT_ID invalid — expected ca-pub- followed by digits"
    if not config.ADSENSE_AUTO_ADS:
        return "SKIP", "ADSENSE_AUTO_ADS=0 — loader disabled"
    return "READY", f"validated {config.ADSENSE_CLIENT_ID} (Auto Ads loader enabled)"


def _sidecar() -> Path:
    return Path(config.STATE_PATH).with_name("adsense_kit.json")


def _load_id() -> Optional[str]:
    try:
        return json.loads(_sidecar().read_text(encoding="utf-8")).get("widget_id")
    except Exception:
        return None


def _save_id(widget_id: str) -> None:
    try:
        f = _sidecar()
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(json.dumps({"widget_id": widget_id}), encoding="utf-8")
    except Exception:
        # The REST write succeeded; sidecar persistence is only dedupe help.
        log.debug("Could not save AdSense widget sidecar", exc_info=True)


def _find_widget(wp) -> Tuple[Optional[str], List[Dict]]:
    try:
        r = wp._request("GET", "widgets", params={"base": "text", "per_page": 100})
        items = r.json() if r.ok else []
    except Exception:
        return None, []
    for item in items:
        encoded = str(((item.get("instance") or {}).get("encoded")) or "")
        if MARKER in encoded:
            return item.get("id"), items
    return None, items


def _footer_sidebar(wp) -> Optional[str]:
    try:
        r = wp._request("GET", "sidebars")
        sidebars = r.json() if r.ok else []
    except Exception:
        return None
    if not sidebars:
        return None
    for sidebar in sidebars:
        joined = f"{sidebar.get('id', '')} {sidebar.get('name', '')}".lower()
        if "footer" in joined or "bottom" in joined:
            return sidebar.get("id")
    return sidebars[0].get("id")


def install(wp, dry: bool = False) -> Tuple[str, str]:
    """Install or refresh one footer widget; never creates duplicates."""
    status, detail = audit()
    if status in ("SKIP", "WARN"):
        return status.lower(), detail
    html = build_widget_html()
    if dry:
        return "planned", "validated AdSense loader -> footer text widget"
    sidebar_id = _footer_sidebar(wp)
    if not sidebar_id:
        return "warn", "sidebars REST unavailable (block theme?) — use Site Kit/manual header"

    encoded = urlencode({"title": "", "text": html, "filter": ""})
    existing, items = _find_widget(wp)
    if not existing:
        known = _load_id()
        if known and any(item.get("id") == known for item in items):
            existing = known
    try:
        if existing:
            current = next((item for item in items if item.get("id") == existing), None)
            old = str(((current or {}).get("instance") or {}).get("encoded") or "")
            if old == encoded:
                return "ok", f"AdSense loader up to date ({existing})"
            r = wp._request("POST", f"widgets/{existing}", json={
                "instance": {"encoded": encoded}, "sidebar_id": sidebar_id,
            })
            if r.ok:
                _save_id(existing)
                return "ok", f"AdSense loader refreshed ({existing} @ {sidebar_id})"
            return "warn", f"AdSense widget update failed: HTTP {r.status_code}"

        r = wp._request("POST", "widgets", json={
            "id_base": "text", "sidebar_id": sidebar_id,
            "instance": {"encoded": encoded},
        })
        if r.ok:
            widget_id = r.json().get("id", "?")
            _save_id(widget_id)
            return "ok", f"AdSense loader installed ({widget_id} @ {sidebar_id})"
        return "warn", f"AdSense widget create failed: HTTP {r.status_code}"
    except Exception as exc:  # noqa: BLE001
        return "warn", f"AdSense widgets REST error: {str(exc)[:100]}"


def ads_txt_status(path=None) -> Tuple[str, str]:
    """preview/ads.txt state → (status, detail): live | placeholder | warn | missing."""
    if path is None:
        path = Path(__file__).resolve().parents[1] / "preview" / "ads.txt"
    path = Path(path)
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return "missing", f"ads.txt ledu ({path}) — 'python tools/build_policy_pages.py' run cheyandi"
    line = next((ln.strip() for ln in text.splitlines()
                 if ln.strip().lower().startswith("google.com,")), "")
    if line and re.fullmatch(r"google\.com, pub-\d{10,20}, DIRECT, [0-9a-fA-F]{16}", line):
        mine = ads_txt_line()
        if mine and line.split(",")[1].strip() != mine.split(",")[1].strip():
            return "warn", f"ads.txt publisher id .env tho match avvatledu: {line}"
        return "live", line
    if "placeholder" in text.lower():
        return "placeholder", "ads.txt host-ready — approval + ADSENSE_CLIENT_ID tarvata auto line"
    return "warn", "ads.txt lo valid 'google.com, pub-..., DIRECT, ...' line ledu"


def ads_txt_line(client_id: str = "") -> Optional[str]:
    """Return the exact manual ads.txt line; WP root-file write is not faked."""
    pub = publisher_id(client_id or config.ADSENSE_CLIENT_ID)
    return f"google.com, pub-{pub}, DIRECT, f08c47fec0942fa0" if pub else None
