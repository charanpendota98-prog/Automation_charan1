"""Production validation against a real public site and optional WordPress auth.

This command reports observed HTTP/REST/metadata state only. It never claims a
Rank Math score, indexing, ranking, analytics, or revenue result when the live
site cannot be reached, and it never changes WordPress content.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List
from urllib.parse import urljoin

import requests

from . import config

log = logging.getLogger("autoblog.live_validation")

PUBLIC_PATHS = (
    "/",
    "/robots.txt",
    "/wp-sitemap.xml",
    "/latest-jobs/",
    "/llms.txt",
    "/privacy-policy/",
    "/about-us/",
    "/contact-us/",
    "/corrections-policy/",
)


def _result(name: str, status: str, detail: str, **extra) -> Dict:
    row = {"name": name, "status": status, "detail": detail}
    row.update(extra)
    return row


def _get(url: str) -> Dict:
    try:
        response = requests.get(
            url,
            headers={"User-Agent": "StudentUp-LiveValidation/1.0"},
            timeout=min(int(getattr(config, "HTTP_TIMEOUT", 30)), 30),
            allow_redirects=True,
        )
        return {
            "status_code": int(response.status_code),
            "final_url": str(response.url or url),
            "content_type": str(response.headers.get("content-type", "")),
            "text": (response.text or "")[:12000],
        }
    except Exception as exc:  # noqa: BLE001 — report unavailable, never fake PASS
        return {"status_code": 0, "final_url": url, "content_type": "", "text": "", "error": str(exc)[:240]}


def _public_checks(site: str) -> List[Dict]:
    rows: List[Dict] = []
    for path in PUBLIC_PATHS:
        url = urljoin(site.rstrip("/") + "/", path.lstrip("/"))
        response = _get(url)
        code = response.get("status_code", 0)
        if code == 0:
            rows.append(_result(path, "unknown", f"request failed: {response.get('error', 'network error')}"))
        elif 200 <= code < 400:
            rows.append(_result(path, "pass", f"HTTP {code}", final_url=response.get("final_url", url)))
        else:
            # Policy pages/sitemap can legitimately be absent on an unconfigured
            # staging site, so this is a review item rather than a fabricated fail.
            rows.append(_result(path, "review", f"HTTP {code}", final_url=response.get("final_url", url)))
    return rows


def _rest_checks(site: str) -> List[Dict]:
    root = _get(urljoin(site.rstrip("/") + "/", "wp-json/"))
    if root.get("status_code") != 200:
        return [_result("WordPress REST root", "unknown", f"HTTP {root.get('status_code', 0)}; {root.get('error', 'REST unavailable')}")]
    try:
        payload = json.loads(root.get("text") or "{}")
        namespaces = payload.get("namespaces") or []
    except (TypeError, ValueError):
        namespaces = []
    required = {"wp/v2", "studentup/v1"}
    missing = sorted(required - set(namespaces))
    return [
        _result(
            "WordPress REST namespaces",
            "pass" if not missing else "review",
            "required namespaces present" if not missing else "missing: " + ", ".join(missing),
            namespaces=namespaces,
        )
    ]


def _auth_checks() -> List[Dict]:
    if not (config.WP_USERNAME and config.WP_APP_PASSWORD):
        return [_result("Authenticated WordPress checks", "unknown", "WP_USERNAME/WP_APP_PASSWORD not configured; public checks only")]
    try:
        from .wordpress_client import WordPressClient

        client = WordPressClient()
        identity = client.check_connection()
        roles = identity.get("roles") or []
        rows = [_result("WordPress authentication", "pass", f"connected as {identity.get('name') or identity.get('slug') or 'user'}", roles=roles)]
        opportunities = client.published_opportunities(max_pages=1, per_page=20)
        source_backed = sum(1 for item in opportunities if item.get("source_url"))
        rows.append(_result("Opportunity metadata readback", "pass", f"read {len(opportunities)} published rows; {source_backed} source-backed"))
        return rows
    except Exception as exc:  # noqa: BLE001 — auth is an observed review item
        return [_result("Authenticated WordPress checks", "unknown", f"live auth/readback failed: {type(exc).__name__}: {str(exc)[:180]}")]


def validate(site: str = "") -> Dict:
    site = (site or config.WP_SITE).rstrip("/")
    rows = _public_checks(site) + _rest_checks(site) + _auth_checks()
    counts = {key: sum(1 for row in rows if row.get("status") == key) for key in ("pass", "review", "unknown", "fail")}
    return {
        "site": site,
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "checks": rows,
        "counts": counts,
        "production_ready": counts["unknown"] == 0 and counts["review"] == 0 and counts["fail"] == 0,
        "note": "Observed live state only; no ranking, indexing, Rank Math 100 or revenue guarantee.",
    }


def run_cli(site: str = "") -> int:
    result = validate(site)
    out = Path(config.LOG_DIR) / "live-validation.json"
    try:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError:
        log.exception("could not persist live validation report")
    print("=" * 74)
    print("  LIVE VALIDATION — observed public/REST/auth state")
    print("=" * 74)
    print(f"  site: {result['site']}")
    for row in result["checks"]:
        icon = {"pass": "✅", "review": "⚠️ ", "unknown": "?  ", "fail": "❌"}.get(row["status"], "?  ")
        print(f"  {icon} {row['name']}: {row['detail']}")
    c = result["counts"]
    print("-" * 74)
    print(f"  {c['pass']} pass · {c['review']} review · {c['unknown']} unknown · {c['fail']} fail")
    print(f"  report: {out}")
    if result["production_ready"]:
        print("  ✅ Observed checks are clear. Manual browser/Rank Math/Search Console/analytics review is still required.")
        return 0
    print("  ⚠️  Not production-ready from observed checks; fix review/unknown items and run again.")
    return 1
