"""Lifecycle monitor for published student opportunities.

This is deliberately a review queue, not an auto-editor.  It checks the
public official/application URLs for dead links, redirects, PDF replacement or
content-type changes, missing application links, and deadline state.  A notice
is never silently marked closed or rewritten because a network probe can be
wrong and an official site can temporarily rate-limit a request.
"""
from __future__ import annotations

import html
import json
import logging
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Callable, Dict, List, Optional
from urllib.parse import urlparse

import requests

from . import config, sources
from .notifier import send_telegram
from .wordpress_client import WordPressClient

log = logging.getLogger("autoblog.opportunity_monitor")

Probe = Callable[[str], Dict]


def _today() -> date:
    try:
        from zoneinfo import ZoneInfo

        return datetime.now(ZoneInfo(config.TIMEZONE)).date()
    except Exception:
        return date.today()


def _load(path: Path) -> Dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
        return value if isinstance(value, dict) else {}
    except (OSError, ValueError):
        log.exception("opportunity monitor state could not be read")
        return {}


def _save(path: Path, value: Dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


def _safe_iso(value: object) -> str:
    raw = str(value or "").strip()
    if len(raw) != 10:
        return ""
    try:
        datetime.strptime(raw, "%Y-%m-%d")
    except ValueError:
        return ""
    return raw


def _same_url(left: str, right: str) -> bool:
    """Compare URLs without treating a harmless trailing slash as a change."""
    def normalize(value: str) -> str:
        parsed = urlparse(str(value or "").strip())
        return parsed._replace(fragment="", path=parsed.path.rstrip("/") or "/").geturl()

    return bool(normalize(left)) and normalize(left) == normalize(right)


def probe(url: str) -> Dict:
    """Perform a bounded public URL probe without downloading the document body."""
    result = {
        "url": url,
        "final_url": url,
        "status": 0,
        "content_type": "",
        "is_pdf": False,
        "etag": "",
        "last_modified": "",
        "redirects": [],
        "error": "",
    }
    try:
        response = requests.get(
            url,
            headers={
                "User-Agent": "StudentUp-OpportunityMonitor/1.0 (+https://studentup.in)",
                "Accept": "text/html,application/pdf;q=0.9,*/*;q=0.1",
            },
            timeout=min(int(getattr(config, "HTTP_TIMEOUT", 30)), 30),
            allow_redirects=True,
            stream=True,
        )
        result["status"] = int(response.status_code)
        result["final_url"] = str(response.url or url)
        result["content_type"] = str(response.headers.get("content-type", "")).split(";", 1)[0].strip().lower()
        result["is_pdf"] = "pdf" in result["content_type"] or urlparse(result["final_url"]).path.lower().endswith(".pdf")
        result["etag"] = str(response.headers.get("etag", ""))[:180]
        result["last_modified"] = str(response.headers.get("last-modified", ""))[:180]
        result["redirects"] = [str(item.url) for item in response.history[-5:]] + [result["final_url"]]
        response.close()
    except Exception as exc:  # noqa: BLE001 — one dead notice must not stop the scan
        result["error"] = str(exc)[:240]
        log.warning("opportunity URL probe failed for %s: %s", url[:120], exc)
    return result


def _issue(post: Dict, kind: str, message: str, **extra) -> Dict:
    item = {
        "key": f"{post.get('id') or post.get('link') or post.get('title')}:{kind}",
        "kind": kind,
        "post_id": post.get("id"),
        "title": str(post.get("title") or "")[:180],
        "post_link": str(post.get("link") or ""),
        "source_url": str(post.get("source_url") or ""),
        "message": message[:400],
    }
    item.update(extra)
    return item


def _classify_probe(post: Dict, current: Dict, previous: Dict, label: str = "source") -> List[Dict]:
    issues: List[Dict] = []
    status = int(current.get("status") or 0)
    source_url = str(post.get("source_url") or "")
    final_url = str(current.get("final_url") or source_url)
    noun = "official application link" if label == "application" else "official source"
    prefix = "application" if label == "application" else "source"
    if status == 0:
        issues.append(_issue(post, f"{prefix}_unreachable", f"{noun.title()} could not be reached.", error=current.get("error", "")))
    elif status >= 400:
        kind = f"{prefix}_dead" if status in (404, 410) else f"{prefix}_unverified"
        issues.append(_issue(post, kind, f"{noun.title()} returned HTTP {status}; editorial review is required.", status=status))
    if status and not _same_url(source_url, final_url):
        old_final = str(previous.get("final_url") or "")
        kind = f"{prefix}_replaced" if old_final and not _same_url(old_final, final_url) else f"{prefix}_redirected"
        issues.append(_issue(post, kind, f"{noun.title()} redirects to a different URL; confirm that it is the intended notice/PDF.", final_url=final_url))
    old_pdf = previous.get("is_pdf")
    if old_pdf is not None and bool(old_pdf) != bool(current.get("is_pdf")):
        issues.append(_issue(post, f"{prefix}_type_changed", f"{noun.title()} changed between HTML and PDF (or PDF and HTML); re-check the evidence.", final_url=final_url))
    return issues


def scan(
    wp: Optional[WordPressClient] = None,
    limit: Optional[int] = None,
    notify: bool = False,
    probe_fn: Optional[Probe] = None,
) -> Dict:
    """Scan published opportunities and persist a safe editorial review queue."""
    if not getattr(config, "OPPORTUNITY_MONITOR_ENABLED", True):
        return {"ok": True, "disabled": True, "scanned": 0, "issues": [], "new_issues": [], "errors": []}
    client = wp or WordPressClient()
    max_posts = max(1, int(limit or getattr(config, "OPPORTUNITY_MONITOR_MAX_POSTS", 180)))
    rows = client.published_opportunities(
        max_pages=max(1, (max_posts + 99) // 100), per_page=100,
    )[:max_posts]
    state_path = Path(getattr(config, "OPPORTUNITY_MONITOR_STATE", Path("logs/opportunity-monitor.json")))
    state = _load(state_path)
    entries = state.get("entries") if isinstance(state.get("entries"), dict) else {}
    queue = state.get("review_queue") if isinstance(state.get("review_queue"), list) else []
    existing_open = {
        str(item.get("key")): item for item in queue
        if isinstance(item, dict) and item.get("status", "open") == "open"
    }
    known_open_keys = set(existing_open)
    checker = probe_fn or probe
    today = _today()
    near_days = max(0, int(getattr(config, "OPPORTUNITY_MONITOR_NEAR_DAYS", 3)))
    issues: List[Dict] = []
    errors: List[Dict] = []
    scanned = 0

    for row in rows:
        post_id = str(row.get("id") or row.get("link") or "").strip()
        if not post_id:
            continue
        source_url = str(row.get("source_url") or "").strip()
        entry_key = post_id
        previous = entries.get(entry_key) if isinstance(entries.get(entry_key), dict) else {}
        current_probe = {}
        row_issues: List[Dict] = []
        last_date = _safe_iso(row.get("last_date"))
        if last_date:
            deadline = datetime.strptime(last_date, "%Y-%m-%d").date()
            days = (deadline - today).days
            if days < 0:
                row_issues.append(_issue(row, "deadline_expired", f"Verified deadline passed on {last_date}; remove from active circulation after editorial review.", last_date=last_date))
            elif days <= near_days:
                row_issues.append(_issue(row, "deadline_near", f"Verified deadline is in {days} day(s); confirm the official notice before forwarding.", last_date=last_date, days_left=days))

        if not source_url or not sources.is_valid_source_url(source_url):
            if not source_url:
                row_issues.append(_issue(row, "source_missing", "Published opportunity has no registered official source URL."))
        else:
            scanned += 1
            try:
                current_probe = checker(source_url) or {}
                row_issues.extend(_classify_probe(row, current_probe, previous.get("probe", {})))
            except Exception as exc:  # noqa: BLE001
                errors.append({"post_id": row.get("id"), "source_url": source_url, "error": str(exc)[:240]})

        application_url = str(row.get("application_url") or "").strip()
        current_application_probe = {}
        if application_url and sources.is_valid_source_url(application_url):
            scanned += 1
            try:
                current_application_probe = checker(application_url) or {}
                app_row = dict(row)
                app_row["source_url"] = application_url
                row_issues.extend(_classify_probe(app_row, current_application_probe, previous.get("application_probe", {}), label="application"))
            except Exception as exc:  # noqa: BLE001
                errors.append({"post_id": row.get("id"), "source_url": application_url, "error": str(exc)[:240]})
        if not application_url:
            row_issues.append(_issue(row, "application_link_missing", "No validated official application URL is registered; keep the Apply action out until verified."))
        elif not sources.is_valid_source_url(application_url):
            row_issues.append(_issue(row, "application_link_invalid", "The registered application URL is not a valid HTTP(S) link; do not expose it as an Apply action."))

        entries[entry_key] = {
            "post_id": row.get("id"),
            "title": row.get("title", ""),
            "source_url": source_url,
            "last_date": last_date,
            "checked": today.isoformat(),
            "probe": current_probe or previous.get("probe", {}),
            "application_url": application_url,
            "application_probe": current_application_probe or previous.get("application_probe", {}),
        }
        for item in row_issues:
            item["detected"] = today.isoformat()
            item["status"] = "open"
            issues.append(item)
            if item["key"] not in existing_open:
                queue.append(item)
                existing_open[item["key"]] = item
            else:
                existing_open[item["key"]].update({
                    "detected": existing_open[item["key"]].get("detected", today.isoformat()),
                    "last_seen": today.isoformat(),
                    "message": item.get("message", ""),
                })

    # Bound runtime state and preserve the newest queue rows first.
    queue = sorted(queue, key=lambda item: str(item.get("detected", "")), reverse=True)[:1000]
    state.update({
        "version": 1,
        "checked": datetime.now().astimezone().isoformat(),
        "entries": entries,
        "review_queue": queue,
    })
    _save(state_path, state)
    # Notify only on a new queue key. Existing open findings may be observed
    # on every daily scan, but they must not spam the owner every morning.
    new_issues = [item for item in issues if item.get("key") not in known_open_keys]
    result = {
        "ok": not errors,
        "disabled": False,
        "scanned": scanned,
        "posts": len(rows),
        "issues": issues,
        "new_issues": new_issues,
        "errors": errors,
        "queue": str(state_path),
    }
    if notify and new_issues:
        lines = ["⚠️ <b>Opportunity review queue</b>", "Official links/deadlines need editorial review; nothing was auto-edited."]
        for item in new_issues[:14]:
            lines.append(f"• <b>{html.escape(str(item.get('kind', 'review')))}</b> — {html.escape(str(item.get('title', ''))[:90])}")
            if item.get("post_link"):
                lines.append(f"  <a href=\"{html.escape(str(item['post_link']), quote=True)}\">Open article</a>")
            lines.append(f"  {html.escape(str(item.get('message', ''))[:180])}")
        send_telegram("\n".join(lines))
    return result


def run_cli(notify: bool = False) -> int:
    result = scan(notify=notify)
    print("=" * 68)
    print("  OPPORTUNITY LIFECYCLE MONITOR — review queue only")
    print("=" * 68)
    if result.get("disabled"):
        print("  disabled: OPPORTUNITY_MONITOR_ENABLED=0")
        return 0
    print(f"  published posts scanned : {result.get('posts', 0)}")
    print(f"  official URLs probed    : {result.get('scanned', 0)}")
    print(f"  open review findings    : {len(result.get('issues', []))}")
    print(f"  new findings            : {len(result.get('new_issues', []))}")
    print(f"  fetch/probe errors      : {len(result.get('errors', []))}")
    for item in result.get("issues", [])[:20]:
        print(f"  ⚠️ {item.get('kind')}: {item.get('title', '')[:90]}")
    print("  No post, deadline, or application link was auto-edited.")
    print(f"  Queue: {result.get('queue', '')}")
    print("=" * 68)
    return 0 if not result.get("errors") else 1
