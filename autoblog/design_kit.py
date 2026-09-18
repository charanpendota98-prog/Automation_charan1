"""v24/v29 — Site-wide Design Kit + progressive reader UI: makes studentup.in look like a top news site
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

# v29: interaction and accessibility layer. It is deliberately dependency-free
# so it works on classic and block themes alike.
ADVANCED_CSS = """
.su-reading-progress{position:fixed;z-index:99999;inset:0 0 auto 0;height:4px;background:transparent;pointer-events:none}
.su-reading-progress i{display:block;height:100%;width:0;background:linear-gradient(90deg,var(--su-navy),var(--su-accent));transition:width .08s linear}
.su-site-tools{display:flex;gap:8px;align-items:center;justify-content:flex-end;max-width:1180px;margin:0 auto;padding:6px 16px;font-size:13px}
.su-tool-btn,.su-share-btn{appearance:none;border:1px solid #DCE5F0;background:#fff;color:var(--su-navy);border-radius:999px;padding:7px 12px;font:inherit;font-weight:600;cursor:pointer}
.su-tool-btn:hover,.su-share-btn:hover{background:var(--su-navy);color:#fff}
.su-article-shell{max-width:860px;margin-inline:auto}
.su-reading-badge{display:inline-flex;gap:5px;align-items:center;color:var(--su-soft);background:#F5F8FC;border:1px solid #E5EBF3;border-radius:999px;padding:6px 11px;font-size:13px}
.su-quick-answer-card{border:1px solid #C9DCF5;border-left:5px solid var(--su-accent);border-radius:0 14px 14px 0;background:linear-gradient(135deg,#F4F8FF,#FFF9F1);padding:16px 18px;margin:18px 0 24px;box-shadow:0 5px 18px rgba(18,53,107,.07)}
.su-quick-answer-card h2{margin-top:0!important;border-left:0!important;padding-left:0!important}
.su-toc{background:#F7F9FC;border:1px solid #E4EAF2;border-radius:14px;padding:12px 18px;margin:20px 0}
.su-toc summary{color:var(--su-navy);font-weight:700;cursor:pointer}
.su-toc ul{margin:8px 0 0 20px}
.su-byline{display:flex;flex-wrap:wrap;gap:6px;align-items:center;color:var(--su-soft);font-size:14px;border-bottom:1px solid #EDF1F6;padding-bottom:10px}
.su-breadcrumbs{display:flex;flex-wrap:wrap;gap:7px;align-items:center;color:var(--su-soft);font-size:13px;margin:4px 0 14px}
.su-breadcrumbs a{font-weight:600;color:var(--su-navy);border:0}
.su-breadcrumbs .su-crumb-current{color:var(--su-ink);font-weight:500}
.su-deadline{box-shadow:0 4px 14px rgba(18,53,107,.06)}
.su-facts-card{border:1px solid #E1E8F2;border-radius:14px;padding:12px 14px;margin:18px 0;background:#fff}
.su-facts-card h2{margin:0 0 10px!important;border:0!important;padding:0!important;font-size:18px!important}
.su-facts-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px;margin:0}
.su-fact{border:1px solid #EDF1F6;border-radius:9px;padding:8px 10px;background:#FBFCFE}
.su-fact dt{font-size:11px;color:var(--su-soft);font-weight:700;text-transform:uppercase;letter-spacing:.04em}
.su-fact dd{margin:3px 0 0;color:var(--su-ink);font-weight:600;overflow-wrap:anywhere}
.su-trust-box{border:1px solid #DCE5F0;background:#FBFCFE;border-radius:14px;padding:14px 16px;margin-top:28px;font-size:14px}
.su-related,.su-official-links{background:#FAFBFD;border-radius:14px;padding:4px 16px 12px;margin-top:22px}
.su-table-scroll{overflow-x:auto;max-width:100%;margin:18px 0;border-radius:10px}
.su-service-hero{background:linear-gradient(135deg,#12356B 0%,#1D4D91 62%,#E8842B 160%);color:#fff;border-radius:20px;padding:26px 24px;margin:10px 0 28px;box-shadow:0 12px 34px rgba(18,53,107,.18)}
.su-service-hero h1,.su-service-hero p{color:#fff}.su-service-kicker{font-size:12px;letter-spacing:.12em;font-weight:700;opacity:.86}.su-service-lead{font-size:18px;line-height:1.7;max-width:800px}
.su-service-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px}.su-service-card{border:1px solid #E2EAF4;border-radius:16px;padding:16px;background:#fff;box-shadow:0 5px 18px rgba(18,53,107,.06)}
.su-service-card h3{margin-top:0}.su-service-card a{font-size:13px}.su-service-actions{display:flex;flex-wrap:wrap;gap:10px;align-items:center;margin-top:18px}.su-service-cta{display:inline-block;border:1px solid rgba(255,255,255,.55);border-radius:999px;padding:10px 16px;color:#fff!important;background:rgba(255,255,255,.12);font-weight:700;text-decoration:none!important}.su-service-cta.primary{background:#E8842B;border-color:#E8842B}.su-service-config-note{font-size:13px;opacity:.86}.su-service-process,.su-service-safety,.su-service-faq,.su-service-final-cta{border:1px solid #E3EAF3;border-radius:16px;padding:16px 18px;margin:22px 0;background:#FBFCFE}.su-service-safety{border-left:5px solid #E8842B}.su-service-faq h3{font-size:17px;margin-bottom:4px}.su-service-faq p{margin-top:0}.su-service-final-cta{background:#FFF8EE;border-color:#F2D5AE}
body.su-dark .su-service-card,body.su-dark .su-service-process,body.su-dark .su-service-safety,body.su-dark .su-service-faq,body.su-dark .su-service-final-cta{background:#182235;color:#E8EEF7;border-color:#33445E}
@media (max-width:900px){.su-service-grid{grid-template-columns:repeat(2,minmax(0,1fr))}}
.su-table-scroll table{margin:0;min-width:560px}
.su-share-bar{display:flex;flex-wrap:wrap;gap:8px;align-items:center;border-top:1px solid #E9EEF5;border-bottom:1px solid #E9EEF5;padding:10px 0;margin:16px 0}
.su-share-label{font-size:13px;color:var(--su-soft);font-weight:600;margin-right:3px}
.su-skip-link{position:fixed;left:8px;top:8px;z-index:100000;background:var(--su-navy);color:#fff!important;padding:10px 14px;border-radius:8px;transform:translateY(-160%);transition:transform .15s}
.su-skip-link:focus{transform:translateY(0)}
body.su-dark{--su-navy:#9FC2FF;--su-accent:#FFB15E;--su-ink:#E8EEF7;--su-soft:#B9C5D6;background:#111827;color:#E8EEF7}
body.su-dark .site,body.su-dark main,body.su-dark article,body.su-dark .su-quick-answer-card,body.su-dark .su-toc,body.su-dark .su-trust-box,body.su-dark .su-related,body.su-dark .su-official-links,body.su-dark .su-tool-btn,body.su-dark .su-share-btn{background:#182235;color:#E8EEF7;border-color:#33445E}
body.su-dark .entry-content p,body.su-dark .entry-content li,body.su-dark .entry-content td{color:#E8EEF7}
body.su-dark .entry-content th{background:#294E88}
body.su-dark .entry-content tr:nth-child(even) td{background:#202F46}
body.su-dark .su-reading-badge{background:#202F46;border-color:#33445E}
@media (max-width:640px){.su-site-tools{padding:5px 10px}.su-tool-btn,.su-share-btn{padding:6px 9px;font-size:12px}.su-article-shell{width:100%}.su-quick-answer-card{padding:13px 14px}.su-table-scroll{margin-inline:-2px}}
@media (prefers-reduced-motion:reduce){*,*::before,*::after{scroll-behavior:auto!important;transition:none!important}}
"""

# No analytics, cookies, or external libraries: this only adds local reading,
# accessibility, sharing, and preference controls.
UI_JS = r"""
(function(){
  "use strict";
  var d=document,b=d.body;
  if(!b||b.getAttribute("data-su-ui29")) return;
  b.setAttribute("data-su-ui29","1");
  var main=d.querySelector(".entry-content,.entry-content-wrap,.post-content,article .content");
  var reduce=window.matchMedia&&window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  function el(tag, cls, text){var x=d.createElement(tag);if(cls)x.className=cls;if(text)x.textContent=text;return x;}
  var skip=el("a","su-skip-link","Skip to article content");skip.href="#su-main-content";b.insertBefore(skip,b.firstChild);
  if(main&&!main.id) main.id="su-main-content";
  var bar=el("div","su-reading-progress");bar.setAttribute("aria-hidden","true");bar.appendChild(el("i"));b.appendChild(bar);
  function progress(){var max=d.documentElement.scrollHeight-window.innerHeight;bar.firstChild.style.width=(max>0?Math.min(100,Math.max(0,window.scrollY/max*100)):0)+"%";}
  window.addEventListener("scroll",progress,{passive:true});progress();
  var tools=el("div","su-site-tools");tools.setAttribute("aria-label","StudentUp display tools");
  var theme=el("button","su-tool-btn", "☾ Dark mode");theme.type="button";theme.setAttribute("aria-pressed","false");
  var top=el("button","su-tool-btn","↑ Top");top.type="button";top.addEventListener("click",function(){window.scrollTo({top:0,behavior:reduce?"auto":"smooth"});});
  function setDark(on){b.classList.toggle("su-dark",on);theme.textContent=on?"☀ Light mode":"☾ Dark mode";theme.setAttribute("aria-pressed",String(on));try{localStorage.setItem("su-theme",on?"dark":"light");}catch(e){}}
  var saved="";try{saved=localStorage.getItem("su-theme")||"";}catch(e){}
  theme.addEventListener("click",function(){setDark(!b.classList.contains("su-dark"));});tools.appendChild(theme);tools.appendChild(top);
  var header=d.querySelector("header,.site-header,.wp-site-blocks");if(header&&header.parentNode) header.parentNode.insertBefore(tools,header.nextSibling);else b.insertBefore(tools,b.firstChild);
  if(saved==="dark") setDark(true);
  if(main){
    main.querySelectorAll("table").forEach(function(t){if(t.parentElement.classList.contains("su-table-scroll"))return;var w=el("div","su-table-scroll");t.parentNode.insertBefore(w,t);w.appendChild(t);});
    [["#quick-answer","su-quick-answer-card"],["#table-of-contents","su-toc"],["#related-articles","su-related"],["#official-links","su-official-links"],["#about-this-article","su-trust-box"]].forEach(function(pair){var x=main.querySelector(pair[0]);if(x)x.classList.add(pair[1]);});
    if(!main.querySelector(".su-share-bar")){
      var share=el("div","su-share-bar");share.appendChild(el("span","su-share-label","Share this guide:"));
      var wa=el("a","su-share-btn","WhatsApp");wa.target="_blank";wa.rel="noopener";wa.href="https://wa.me/?text="+encodeURIComponent(d.title+" "+location.href);share.appendChild(wa);
      var copy=el("button","su-share-btn","Copy link");copy.type="button";copy.addEventListener("click",function(){if(navigator.clipboard)navigator.clipboard.writeText(location.href).then(function(){copy.textContent="Copied ✓";setTimeout(function(){copy.textContent="Copy link";},1600);});});share.appendChild(copy);main.insertBefore(share,main.firstChild);
    }
  }
})();
"""


def build_css() -> str:
    return f'<style id="su-design-kit">/*{MARKER}*/{CSS}{ADVANCED_CSS}</style>'


def build_widget_html() -> str:
    return build_css() + f'<script id="su-design-ui">/*{MARKER}*/{UI_JS}</script>'


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
    except Exception as exc:  # noqa: BLE001 — best-effort (silent kaadu)
        log.debug("design_kit._save_id skip: %s", exc)


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

    payload = build_widget_html()
    if dry:
        return "planned", "footer text-widget lo responsive UI + design CSS/JS inject"
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

    enc = urlencode({"title": "", "text": payload, "filter": ""})
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
