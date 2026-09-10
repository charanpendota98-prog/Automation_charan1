"""v24 — Site-wide Design Kit: makes studentup.in look like a top news site
WITHOUT touching theme files.

Mechanism: WP's legacy `text` widget can carry raw HTML — a <style> block in
any sidebar-rendered area (footer preferred) applies to EVERY page, including
the homepage (which our per-post CSS can't reach). Installed/updated via the
core REST /wp/v2/widgets endpoint (admin app-password). Idempotent + zero
destructive edits.

Palette: brand navy + energy orange (matches the StudentUp logo), Noto Sans
Telugu + Inter, rounded cards, zebra tables, pill Read-More — the visual
language of Adda247/ABP Ananda class sites.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

log = logging.getLogger("autoblog.design")

MARKER = "sukit24"          # ASCII-only — survives URL-encoding in widget data

CSS = """@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Noto+Sans+Telugu:wght@400;600;700&display=swap');
:root{--su-navy:#12356B;--su-accent:#E8842B;--su-ink:#22303F;--su-soft:#5A6472}
body{font-family:'Inter','Noto Sans Telugu',system-ui,-apple-system,'Segoe UI',sans-serif;-webkit-font-smoothing:antialiased}
h1,h2,h3,h4,.entry-title{font-family:'Noto Sans Telugu','Inter',sans-serif;color:var(--su-navy);letter-spacing:-.015em}
.entry-content p{font-size:16.5px;line-height:1.85;color:var(--su-ink)}
.entry-content a{color:var(--su-navy);text-decoration:none;border-bottom:1px solid rgba(18,53,107,.18);font-weight:600}
.entry-content a:hover{color:var(--su-accent);border-color:currentColor}
.entry-content h2{border-left:4px solid var(--su-accent);padding-left:12px;margin:34px 0 14px}
.entry-content li{line-height:1.75;margin-bottom:6px}
.entry-content img,.wp-post-image{border-radius:14px}
body.single .post-thumbnail img,body.single figure.wp-post-image,body.single .wp-post-image{width:100%;max-height:420px;object-fit:cover}
.entry-content table{width:100%;border-collapse:separate;border-spacing:0;font-size:15px;border:1px solid #E4E9F1;border-radius:10px;overflow:hidden;margin:18px 0}
.entry-content th{background:var(--su-navy);color:#fff;text-align:left;padding:10px 12px}
.entry-content td{padding:9px 12px;border-bottom:1px solid #EDF1F6;color:var(--su-ink)}
.entry-content tr:last-child td{border-bottom:0}
.entry-content tr:nth-child(even) td{background:#F7F9FC}
blockquote{border-left:4px solid var(--su-accent);background:#FAF7F2;padding:12px 16px;border-radius:0 10px 10px 0}
.more-link,a.more,a[rel=more],.read-more a,.btn-primary{background:var(--su-navy)!important;color:#fff!important;border-radius:999px!important;padding:9px 20px!important;font-weight:600;font-size:14px;display:inline-block}
.more-link:hover,a.more:hover{background:var(--su-accent)!important}
.pagination,.nav-links{clear:both;padding:24px 0}
.pagination a,.pagination span.current,.nav-links .page-numbers{border-radius:8px!important;margin:0 3px;font-weight:600}
.site-footer,.footer{font-size:14px}
.archive .entry-title,.blog .entry-title,.wp-block-post-template .wp-block-post-title{font-size:clamp(19px,4.6vw,24px)!important;line-height:1.35;margin:.2em 0 .4em}
.archive .wp-post-image,.blog .wp-post-image,.wp-block-post-template .wp-block-post-featured-image img{width:100%;aspect-ratio:16/9;object-fit:cover;border-radius:0}
.archive article,.blog article,.wp-block-post-template>li{border:1px solid #EAEFF6;border-radius:16px;overflow:hidden;background:#fff;transition:box-shadow .18s ease,transform .18s ease}
.archive article:hover,.blog article:hover,.wp-block-post-template>li:hover{box-shadow:0 10px 28px rgba(18,53,107,.10);transform:translateY(-2px)}
.archive .entry-summary,.archive .entry-meta,.archive .entry-footer{padding-left:16px;padding-right:16px}
.widget-title,.widgettitle,aside .wp-block-heading{font-size:15px;text-transform:uppercase;letter-spacing:.08em;color:var(--su-navy);border-bottom:2px solid var(--su-accent);padding-bottom:6px}
@media (max-width:640px){
.entry-content p{font-size:15.5px;line-height:1.8}
.entry-content table{font-size:13.5px}
.entry-content th,.entry-content td{padding:7px 8px}
.entry-content h2{padding-left:9px}
}
"""


def build_css() -> str:
    return f'<style id="su-design-kit">/*{MARKER}*/{CSS}</style>'


def _sidecar():
    """widget id memory next to state.db — survives marker edits (no dupes)."""
    from . import config
    return Path(config.STATE_PATH).with_name("design_kit.json")


def _load_id() -> Optional[str]:
    try:
        import json
        return json.loads(_sidecar().read_text(encoding="utf-8")).get("widget_id")
    except Exception:
        return None


def _save_id(wid: str) -> None:
    try:
        import json
        f = _sidecar()
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(json.dumps({"widget_id": wid}), encoding="utf-8")
    except Exception:
        pass


def _find_widget(wp) -> Tuple[Optional[str], List[Dict]]:
    """Existing kit widget id (by marker in encoded instance) + all text widgets."""
    try:
        r = wp._request("GET", "widgets", params={"base": "text",
                                                   "per_page": 100})
        items = r.json() if r.ok else []
    except Exception:
        items = []
    for it in items:
        enc = str(((it.get("instance") or {}).get("encoded"))
                  or it.get("id") or "")
        if MARKER in enc:
            return it.get("id"), items
    # GET widgets may omit instance payload on some WP builds → try known id
    return None, items


def install(wp, dry: bool = False) -> Tuple[str, str]:
    """Returns (status, detail). status: ok | planned | warn.

    WP widgets REST stores instance as URL-encoded form data (`encoded`) —
    we build that exact string so the classic text widget renders our CSS."""
    from urllib.parse import urlencode

    css = build_css()
    if dry:
        return "planned", "footer text-widget lo site-wide design CSS inject"
    try:
        r = wp._request("GET", "sidebars")
        sidebars = r.json() if r.ok else []
    except Exception as exc:  # noqa: BLE001
        return "warn", f"sidebars API ledu ({str(exc)[:60]})"
    if not sidebars:
        return "warn", "widget areas levu (block theme?) — kit per-post CSS lo matrame"
    sid = ""
    for sb in sidebars:
        if "footer" in (sb.get("id", "") + sb.get("name", "")).lower():
            sid = sb["id"]
            break
    if not sid:
        sid = sidebars[0]["id"]

    enc = urlencode({"title": "", "text": css, "filter": ""})
    existing, items = _find_widget(wp)
    if not existing:
        # marker missing (user edited widget?) → sidecar-remembered id still ours
        known = _load_id()
        if known and any(i.get("id") == known for i in items):
            existing = known
    try:
        if existing:
            cur = next((i for i in items if i.get("id") == existing), None)
            enc_old = str(((cur or {}).get("instance") or {})
                          .get("encoded") or "")
            if enc_old == enc:
                return "ok", f"design kit up to date ({existing})"
            r = wp._request("POST", f"widgets/{existing}",
                            json={"instance": {"encoded": enc},
                                  "sidebar_id": sid})
            if r.ok:
                _save_id(existing)
                return "ok", f"design kit refreshed ({existing} @ {sid})"
            return "warn", f"widget update fail: {r.status_code}"
        r = wp._request("POST", "widgets",
                        json={"id_base": "text", "sidebar_id": sid,
                              "instance": {"encoded": enc}})
        if r.ok:
            nid = r.json().get("id", "?")
            _save_id(nid)
            return "ok", f"design kit installed ({nid} @ {sid})"
        return "warn", f"widget create fail: {r.status_code}"
    except Exception as exc:  # noqa: BLE001
        return "warn", f"widgets API error: {str(exc)[:90]}"


def broken_footer_token(wp) -> Tuple[str, str]:
    """Detect theme footer showing raw '{StudentUp.in}' token — best-effort fix
    if it lives in a text widget; else returns admin instruction."""
    try:
        r = wp._request("GET", "widgets", params={"base": "text",
                                                  "per_page": 100})
        items = r.json() if r.ok else []
    except Exception:
        return "skip", "widgets read kaDU"
    for it in items:
        enc = str((it.get("instance") or {}).get("encoded") or "")
        if "%7BStudentUp.in%7D" in enc or "{StudentUp.in}" in enc:
            wid = it.get("id")
            fixed = enc.replace("%7BStudentUp.in%7D", "StudentUp.in") \
                       .replace("{StudentUp.in}", "StudentUp.in")
            try:
                from urllib.parse import parse_qs, unquote

                fields = parse_qs(fixed)
                text = unquote(fields.get("text", [""])[0]) \
                    if fields.get("text") else ""
                title = unquote(fields.get("title", [""])[0]) \
                    if fields.get("title") else ""
                if text:
                    from urllib.parse import urlencode

                    rr = wp._request("POST", f"widgets/{wid}", json={
                        "instance": {"encoded": urlencode(
                            {"title": title, "text": text, "filter": ""})}})
                    if rr.ok:
                        return "ok", f"footer '{wid}' — {{StudentUp.in}} fix ayindi"
            except Exception as exc:  # noqa: BLE001
                return "warn", str(exc)[:80]
            return "warn", "widget find ayyindi kaani update fail"
    return "skip", "footer token widget lo ledu — theme option lo fix kavali "\
        "(Appearance→Customize→Footer text: 'Copyright © 2026 StudentUp.in')"
