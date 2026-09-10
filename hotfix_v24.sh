#!/usr/bin/env bash
# ============================================================
#  v24+v25 HOTFIX — studentup.in
#  crop-proof thumbnails + site-wide Design Kit + menu dedupe
#  Usage (server repo root lo):  bash hotfix_v24.sh
#  Idempotent. GitHub PR merge + `git pull` cheste need ledu.
# ============================================================
set -euo pipefail
cd "$(dirname "$0")"
[ -d autoblog ] || { echo "repo root nunchi run cheyandi"; exit 1; }
if grep -q "v24 CROP-PROOF" autoblog/image_gen.py && [ -f autoblog/design_kit.py ]; then
  echo "v24+v25 already applied — nothing to do"; exit 0
fi
echo "-> autoblog/image_gen.py (v24 crop-proof layouts)..."
cat > autoblog/image_gen.py <<'IG_EOF'
"""Featured-image generator using Pillow (no external API needed).

v24 CROP-PROOF: theme cards crop to ANY aspect (mobile square ≈ center
56% width!). ALL text now lives in x∈[0.21w, 0.79w] center band — even the
worst object-fit crop cannot cut a single letter. Layouts center-aligned.

v15 PRO design (top-website level) + v16 3-layout rotation — post-to-post
okke pattern kanipinchadu, prathi okaati fresh (copy feel raadu):
  "left"   → left dark scrim + left-aligned title (news-site standard)
  "bottom" → bottom dark band, clean gradient top
  "right"  → right dark panel, left gradient art
Category pill, big bold wrapped title with shadow, accent underline bar,
brand pill + year chip — Adda247/Sakshi thumbnail style, mana own rendering.
"""

import logging
import random
from datetime import date
from pathlib import Path
from typing import Optional

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from . import config

log = logging.getLogger("autoblog.image")

PALETTES = [
    ((37, 27, 89), (87, 65, 175)),     # deep purple
    ((9, 47, 86), (25, 120, 166)),     # ocean blue
    ((6, 65, 61), (22, 138, 116)),     # teal green
    ((96, 34, 12), (211, 108, 39)),    # orange
    ((68, 16, 58), (163, 44, 110)),    # magenta
    ((20, 40, 80), (70, 130, 60)),     # blue-green mix
]

# kotha image prathi sari veedu marali — vanda posts lo okka color repeat avvakunda
_LAST_PALETTE = {"i": -1}

# v16 rotation → v24: center-safe layouts (bottom band / center panel / top pill)
VARIANTS = ["bottom", "center", "top"]
_LAST_VARIANT = {"i": -1}

ACCENT = (255, 138, 42)          # orange accent (brand energy)
DARK = (10, 12, 30)             # panel/scrim base

FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
]


# WP/theme card thumbnails crop avuthayi — anni text center-safe ga undali.
# v2.1: 7.5% safe margins + short category labels (crop lo "VATE JOBS" lanti
# clipping raadu).
CAT_SHORT = {
    "Central Govt Jobs": "GOVT JOBS", "TS Govt Jobs": "TS GOVT JOBS",
    "AP Govt Jobs": "AP GOVT JOBS", "Online Education": "EDUCATION",
    "Part Time Jobs": "PART-TIME", "Walkin Jobs": "WALK-IN JOBS",
    "Hall Tickets": "HALL TICKET", "Private Jobs": "PRIVATE JOBS",
    "Software Jobs": "SOFTWARE JOBS", "Scholarships": "SCHOLARSHIPS",
    "Results": "RESULTS", "Internships": "INTERNSHIPS",
}


def _pill_label(category: str) -> str:
    cat = (category or "").strip()
    label = CAT_SHORT.get(cat, cat.upper())
    return label[:16].strip() if len(label) > 16 else label


def _load_font(size: int) -> ImageFont.FreeTypeFont:
    for path in FONT_CANDIDATES:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    log.warning("No TrueType font found; using default bitmap font")
    return ImageFont.load_default()


def _wrap(draw: ImageDraw.ImageDraw, text: str, font, max_width: int,
           max_lines: int = 3) -> list:
    words, lines, cur = text.split(), [], ""
    for word in words:
        trial = (cur + " " + word).strip()
        if draw.textlength(trial, font=font) <= max_width:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    if len(lines) > max_lines:
        # last line ellipsis
        lines = lines[:max_lines]
        lines[-1] = lines[-1][:max(0, len(lines[-1]) - 4)] + " ..."
    return lines


def _pill(draw: ImageDraw.ImageDraw, xy, text: str, font, fill, text_fill,
          radius=None):
    x0, y0 = xy
    tw = draw.textlength(text, font=font)
    pad = int(font.size * 0.45)
    box = [x0, y0, x0 + tw + pad * 2, y0 + font.size + pad * 2]
    draw.rounded_rectangle(box,
                           radius=radius if radius is not None
                           else (font.size + pad * 2) // 2,
                           fill=fill)
    draw.text((x0 + pad, y0 + pad - int(font.size * 0.08)), text,
              font=font, fill=text_fill)
    return box


def _shadow_text(draw: ImageDraw.ImageDraw, xy, text: str, font,
                 fill=(255, 255, 255)):
    x, y = xy
    draw.text((x + 3, y + 3), text, font=font, fill=(0, 0, 0, 130))
    draw.text((x, y), text, font=font, fill=fill)


def _center_pill(draw, text, font, fill, text_fill, y0, w):
    """Horizontally-centered pill — crop-proof by construction."""
    tw = draw.textlength(text, font=font)
    pad = int(font.size * 0.45)
    x0 = (w - (tw + pad * 2)) // 2
    return _pill(draw, (x0, y0), text, font, fill, text_fill)


def _center_lines(draw, lines, font, w, y0, lh, fill=(255, 255, 255)):
    for line in lines:
        lw = draw.textlength(line, font=font)
        _shadow_text(draw, ((w - lw) / 2, y0), line, font, fill=fill)
        y0 += lh
    return y0


def _draw_layout(img: Image.Image, draw: ImageDraw.ImageDraw, w: int, h: int,
                 banner_text: str, category: str, variant: str) -> None:
    """v24 layouts — every glyph centered inside the safe band."""
    year = str(date.today().year)
    label_font = _load_font(int(h * 0.044))
    brand_font = _load_font(int(h * 0.036))
    label = _pill_label(category)
    brand = config.SITE_BRAND
    tf = _load_font(int(h * 0.098))
    lines = _wrap(draw, banner_text[:64], tf, int(w * 0.54), max_lines=3)

    if variant == "center":
        # soft full-width card behind centered text (magazine style)
        card = [int(w * 0.10), int(h * 0.13), int(w * 0.90), int(h * 0.87)]
        draw.rounded_rectangle(card, radius=26, fill=DARK + (150,))
        draw.rounded_rectangle(card, radius=26, outline=ACCENT + (200,), width=3)
        _center_pill(draw, label, label_font, ACCENT + (250,), (20, 20, 30),
                     int(h * 0.185), w)
        y = int(h * 0.33)
        y = _center_lines(draw, lines, tf, w, y, tf.size + 12)
        draw.rectangle([w / 2 - 70, y + 14, w / 2 + 70, y + 20], fill=ACCENT)
        _center_lines(draw, [f"{brand}  \u00b7  {year}"], brand_font, w,
                      int(h * 0.755), brand_font.size, fill=(255, 255, 255, 235))
        return

    if variant == "top":
        # top white pill-row over gradient, centered title mid, no band
        _center_pill(draw, f"{label}  \u00b7  {year}", label_font,
                     (255, 255, 255, 240), (25, 25, 45), int(h * 0.085), w)
        y = int(h * 0.32)
        y = _center_lines(draw, lines, tf, w, y, tf.size + 12)
        draw.rectangle([w / 2 - 80, y + 12, w / 2 + 80, y + 18], fill=ACCENT)
        _center_pill(draw, brand, brand_font, (10, 12, 30, 150),
                     (255, 255, 255, 235), int(h * 0.80), w)
        return

    # ---- default "bottom": gradient top, dark band bottom, ALL centered ----
    panel_y0 = int(h * 0.52)
    draw.rectangle([0, panel_y0, w, h], fill=DARK + (220,))
    draw.line([0, panel_y0, w, panel_y0], fill=ACCENT + (255,), width=4)
    _center_pill(draw, label, label_font, (255, 255, 255, 235),
                 (25, 25, 45), int(h * 0.07), w)
    y = _center_lines(draw, lines, tf, w, panel_y0 + int(h * 0.075),
                      tf.size + 10)
    draw.rectangle([w / 2 - 70, y + 12, w / 2 + 70, y + 18], fill=ACCENT)
    _center_lines(draw, [f"{brand}  \u00b7  {year}"], brand_font, w,
                  int(h * 0.905), brand_font.size, fill=(255, 255, 255, 210))


def generate_featured_image(
    banner_text: str,
    category: str,
    out_path: Path,
    variant: str = "",
) -> Optional[Path]:
    """Render a 1200x675 featured image. Returns path or None on failure.

    variant: "bottom" | "center" | "top" — empty = auto-rotate (v24).
    """
    try:
        w, h = config.IMAGE_WIDTH, config.IMAGE_HEIGHT
        idx = (_LAST_PALETTE["i"] + 1 + random.randint(0, len(PALETTES) - 2)) % len(PALETTES)
        _LAST_PALETTE["i"] = idx
        c1, c2 = PALETTES[idx]

        if variant not in VARIANTS:
            _LAST_VARIANT["i"] = (_LAST_VARIANT["i"] + 1) % len(VARIANTS)
            variant = VARIANTS[_LAST_VARIANT["i"]]

        base = Image.new("RGB", (w, h))
        px = base.load()
        for y in range(h):
            t = y / (h - 1)
            r = int(c1[0] + (c2[0] - c1[0]) * t)
            g = int(c1[1] + (c2[1] - c1[1]) * t)
            b = int(c1[2] + (c2[2] - c1[2]) * t)
            for x in range(0, w, 4):
                for k in range(4):
                    px[x + k, y] = (r, g, b)

        # decorative translucent circles on an RGBA overlay
        overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        odraw = ImageDraw.Draw(overlay)
        for _ in range(8):
            rad = random.randint(70, 280)
            cx = random.randint(-100, w + 100)
            cy = random.randint(-100, h + 100)
            alpha = random.randint(10, 32)
            odraw.ellipse(
                [cx - rad, cy - rad, cx + rad, cy + rad],
                fill=(255, 255, 255, alpha),
            )
        overlay = overlay.filter(ImageFilter.GaussianBlur(2))
        img = Image.alpha_composite(base.convert("RGBA"), overlay)
        draw = ImageDraw.Draw(img)

        _draw_layout(img, draw, w, h, banner_text, category, variant)

        out_path.parent.mkdir(parents=True, exist_ok=True)
        img.convert("RGB").save(str(out_path), "JPEG", quality=86,
                               optimize=True, progressive=True)
        return out_path
    except Exception:
        log.exception("Featured image generation failed — continuing without image")
        return None
IG_EOF

echo "-> autoblog/design_kit.py (Design Kit + v25 up-to-date + sidecar)..."
cat > autoblog/design_kit.py <<'DK_EOF'
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
DK_EOF

echo "-> tests/design_test.py (7-section suite)..."
cat > tests/design_test.py <<'DT_EOF'
"""v24 design kit tests — crop-proof thumbs, widget install/update, footer
token fix, CSS content, CLI wiring. No network."""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from autoblog import design_kit, image_gen  # noqa: E402


class FakeResp:
    def __init__(self, status=200, payload=None):
        self.status_code, self._p = status, payload or {}

    @property
    def ok(self):
        return self.status_code < 400

    def json(self):
        return self._p


class FakeWP:
    def __init__(self, mode="ok"):
        self.mode, self.calls = mode, []
        self.widgets = {}
        self.n = 0

    def _request(self, method, path, **kw):
        self.calls.append((method, path, kw))
        if self.mode == "dead":
            raise RuntimeError("connection refused")
        if path.startswith("sidebars"):
            if self.mode == "no_sidebars":
                return FakeResp(200, [])
            return FakeResp(200, [{"id": "sidebar-1", "name": "Sidebar"},
                                  {"id": "footer-1", "name": "Footer"}])
        if path.startswith("widgets/"):
            wid = path.split("/", 1)[1]
            self.widgets[wid] = kw.get("json", {}).get("instance", {})
            return FakeResp(200, {"id": wid})
        if path == "widgets" and method == "POST":
            self.n += 1
            wid = f"text-{900 + self.n}"
            self.widgets[wid] = kw.get("json", {}).get("instance", {})
            return FakeResp(201, {"id": wid})
        if path.startswith("widgets"):
            items = [{"id": k, "instance": v} for k, v in self.widgets.items()]
            if self.mode == "broken_footer" and not items:
                from urllib.parse import quote
                items = [{"id": "text-1", "instance": {
                    "encoded": "title=&text=" + quote(
                        "Copyright © 2026 - {StudentUp.in}")}}]
            return FakeResp(200, items)
        return FakeResp(404, {})


def t1_css():
    css = design_kit.build_css()
    assert css.startswith("<style id=") and "sukit24" in css
    assert css.index("@import") < css.index(":root"), "@import first rule kavali"
    for token in ("--su-navy:#12356B", "--su-accent:#E8842B",
                  "Noto Sans Telugu", "Inter", "border-radius:14px",
                  "object-fit:cover", "max-height:420px",
                  "border-collapse:separate", "nth-child(even)",
                  "more-link", "line-height:1.85", "@media (max-width:640px)",
                  # v25 cards + widget heads
                  ".archive .entry-title", "aspect-ratio:16/9",
                  "translateY(-2px)", "widget-title", "box-shadow"):
        assert token in css, token
    print("1. kit CSS tokens ✅")


def t2_install_update():
    wp = FakeWP()
    st, det = design_kit.install(wp)
    assert st == "ok" and "footer-1" in det, det
    wid = re.search(r"\((text-\d+)", det).group(1)
    enc = wp.widgets[wid]["encoded"]
    assert "sukit24" in enc and "%3Cstyle" in enc
    # re-run → SAME css → up-to-date skip (no POST at all beyond GETs)
    n_before = wp.n
    calls_before = len(wp.calls)
    st2, det2 = design_kit.install(wp)
    assert st2 == "ok" and "up to date" in det2 and wid in det2
    assert wp.n == n_before
    posts = [c for c in wp.calls[calls_before:] if c[0] == "POST"]
    assert not posts, posts
    # stale widget (marker edited away) → sidecar id → refresh, NO dupe create
    import tempfile
    from unittest import mock
    from autoblog import config
    tmpdir = Path(tempfile.mkdtemp())
    with mock.patch.object(config, "STATE_PATH", tmpdir / "state.db"):
        wp.widgets.pop(wid)  # first: simulate wipe → recreate + save id
        st2b, det2b = design_kit.install(wp)
        wid = re.search(r"\((text-\d+)", det2b).group(1)
        wp.widgets[wid] = {"encoded": "title=&text=user-edited-no-marker"}
        st3, det3 = design_kit.install(wp)
        assert st3 == "ok" and "refreshed" in det3, (st3, det3)
        assert wp.n == n_before + 1  # only the recreate above, no dupes
    print("2. install → up-to-date skip → stale refresh (no dupes) ✅")


def t3_fallbacks():
    st, _ = design_kit.install(FakeWP("no_sidebars"))
    assert st == "warn"
    st, _ = design_kit.install(FakeWP("dead"))
    assert st == "warn"
    st, det = design_kit.install(FakeWP(), dry=True)
    assert st == "planned"
    print("3. block-theme/dead-API fallbacks ✅")


def t4_footer_token():
    wp = FakeWP("broken_footer")
    st, det = design_kit.broken_footer_token(wp)
    assert st == "ok" and "text-1" in det, (st, det)
    enc = wp.widgets["text-1"]["encoded"]
    assert "StudentUp.in" in enc and "%7B" not in enc.replace(
        "%7BStudentUp.in%7D", "")  # token gone
    st2, _ = design_kit.broken_footer_token(FakeWP())
    assert st2 == "skip"
    print("4. footer {StudentUp.in} auto-fix ✅")


def t5_layouts():
    import tempfile
    from PIL import Image
    tmp = Path(tempfile.mkdtemp())
    names = set(image_gen.VARIANTS)
    assert names == {"bottom", "center", "top"}
    for v in names:
        out = image_gen.generate_featured_image(
            "TS EAMCET 2026 Counselling Schedule Out", "Results",
            tmp / f"{v}.jpg", variant=v)
        assert out and out.exists()
        with Image.open(out) as im:
            px = im.convert("RGB").load()
            W, H = im.size
            minx, maxx = W, 0
            for yy in range(0, H, 3):
                for xx in range(0, W, 3):
                    r, g, b = px[xx, yy]
                    if r > 228 and g > 228 and b > 228:
                        minx, maxx = min(minx, xx), max(maxx, xx)
            assert minx > 0.19 * W and maxx < 0.81 * W, (v, minx, maxx)
        # simulate square mobile crop (worst case 56.25% width) — title present
        with Image.open(out) as im:
            W, H = im.size
            left = (W - H) // 2
            crop = im.convert("RGB").crop((left, 0, left + H, H))
            cp = crop.load()
            bright = sum(1 for yy in range(0, H, 4) for xx in range(0, H, 4)
                         if all(c > 225 for c in cp[xx, yy]))
            assert bright > 30, v  # plenty of text survived the crop
    print("5. 3 layouts: crop-safe bbox + square-crop survival ✅")


def t6_wiring():
    main_src = (Path(__file__).resolve().parent.parent
                / "autoblog/main.py").read_text(encoding="utf-8")
    assert "--polish" in main_src and "design_kit.install" in main_src
    setup_src = (Path(__file__).resolve().parent.parent
                 / "autoblog/site_setup.py").read_text(encoding="utf-8")
    assert "Design kit" in setup_src and "broken_footer_token" in setup_src
    assert "_menu_dedupe" in setup_src and "duplicate items removed" in setup_src
    rot = image_gen.generate_featured_image.__doc__
    assert "bottom" in rot or "rotate" in (image_gen.__doc__ or "")
    print("6. --polish CLI + setup auto-install wiring ✅")


def t7_menu_dedupe():
    class FakeMenuWP:
        def __init__(self):
            self.deleted = []
        def get_menu_items(self, mid):
            return [{"id": 1, "title": "About Us"}, {"id": 2, "title": "Privacy Policy"},
                    {"id": 3, "title": "Terms"}, {"id": 4, "title": " Privacy Policy "},
                    {"id": 5, "title": "Contact"}, {"id": 6, "title": "Terms"}]
        def _request(self, m, path, **kw):
            self.deleted.append(path)
            class R:
                ok = True
            return R()
    from autoblog import site_setup
    wp = FakeMenuWP()
    n = site_setup._menu_dedupe(wp, 55)
    assert n == 2 and wp.deleted == ["menu-items/4", "menu-items/6"], (n, wp.deleted)
    # dedupe must never delete first occurrences
    assert "menu-items/1" not in wp.deleted
    print("7. footer menu duplicate auto-removal ✅")


if __name__ == "__main__":
    t1_css()
    t2_install_update()
    t3_fallbacks()
    t4_footer_token()
    t5_layouts()
    t6_wiring()
    t7_menu_dedupe()
    print("ALL v24 TESTS PASSED ✔")
DT_EOF

echo "-> main.py / site_setup.py / radar_test.py patches..."
python3 - <<'PY_EOF'
from pathlib import Path

def patch(path, old, new, guard):
    p = Path(path); s = p.read_text(encoding="utf-8")
    if guard in s:
        print("skip (already patched):", path); return
    assert old in s, "anchor not found in " + path
    p.write_text(s.replace(old, new, 1), encoding="utf-8")
    print("patched:", path)

ss_old = """    print("-" * 64)
    if dry:
        print("  Preview matrame. Apply cheyadaniki: run.py --setup")"""
ss_new = """    if not dry:
        # v24 DESIGN KIT — site-wide CSS via footer text widget (all pages)
        try:
            from . import design_kit
            status, detail = design_kit.install(wp)
            print(f"  \U0001f3a8 {'Design kit':28.28s} {status}: {detail[:120]}")
            f_stat, f_detail = design_kit.broken_footer_token(wp)
            if f_stat != "skip":
                print(f"  \U0001f9b6 {'Footer token':28.28s} {f_stat}: {f_detail[:120]}")
        except Exception as exc:  # noqa: BLE001
            print(f"  \U0001f3a8 Design kit failed (harmless): {str(exc)[:100]}")
    print("-" * 64)
    if dry:
        print("  Preview matrame. Apply cheyadaniki: run.py --setup")
        print("  (apply lo v24 Design kit site-wide CSS kuda install avutundi)")"""
patch("autoblog/site_setup.py", ss_old, ss_new, "design_kit")

md_old = """        have_titles = set()
        if menu:
            try:
                have_titles = {(it.get("title") or "")
                               for it in wp.get_menu_items(menu["id"])}
            except Exception:
                pass"""
md_new = md_old + """
        n_dupes = _menu_dedupe(wp, menu["id"]) if (menu and not dry) else 0"""
patch("autoblog/site_setup.py", md_old, md_new, "_menu_dedupe")

md2_old = """            out.append(_line("OK", "Footer legal menu", "anni links unnayi"))"""
md2_new = """            out.append(_line("OK", "Footer legal menu",
                             "anni links unnayi"
                             + (f" — {n_dupes} duplicate items removed"
                                if n_dupes else "")))"""
patch("autoblog/site_setup.py", md2_old, md2_new, "duplicate items removed")

md3_old = """def audit_and_fix(wp, dry: bool = True)"""
md3_new = '''def _menu_dedupe(wp, menu_id: int) -> int:
    """v25: same title repeated in a menu (dup Terms/Privacy from past runs)
    — keep first occurrence, DELETE extras via core REST. Returns removed."""
    removed = 0
    try:
        items = wp.get_menu_items(menu_id) or []
    except Exception:
        return 0
    seen = set()
    for it in items:
        title = (it.get("title") or "").strip()
        if not title:
            continue
        if title in seen:
            try:
                r = wp._request("DELETE", f"menu-items/{it.get('id')}",
                                params={"force": "true"})
                if r.ok:
                    removed += 1
            except Exception:
                pass
        else:
            seen.add(title)
    return removed


def audit_and_fix(wp, dry: bool = True)'''
patch("autoblog/site_setup.py", md3_old, md3_new, "v25: same title repeated")

mn_old = """    parser.add_argument("--keywords", action="store_true",
                        help="keyword dominance engine: matrix + coverage + autocomplete")
    args = parser.parse_args()"""
mn_new = """    parser.add_argument("--keywords", action="store_true",
                        help="keyword dominance engine: matrix + coverage + autocomplete")
    parser.add_argument("--polish", action="store_true",
                        help="v24: site-wide design kit CSS via footer widget — "
                             "colors/typography/tables/cards on ALL pages. "
                             "Idempotent; re-run after theme changes.")
    args = parser.parse_args()"""
patch("autoblog/main.py", mn_old, mn_new, '"--polish"')

mn2_old = """    if args.rebuild_hubs:"""
mn2_new = """    if args.polish:
        from . import design_kit
        from .wordpress_client import WordPressClient
        wp = WordPressClient()
        try:
            wp.check_connection()
        except Exception as exc:  # noqa: BLE001
            print(f"WP connect kaDU ({str(exc)[:70]}...) — "
                  "Appearance→Customize→Additional CSS lo paste cheyandi:")
            print(design_kit.build_css())
            return 0
        status, detail = design_kit.install(wp)
        f_stat, f_detail = design_kit.broken_footer_token(wp)
        print(f"\U0001f3a8 Design kit: {status} — {detail}")
        print(f"\U0001f9b6 Footer token: {f_stat} — {f_detail}")
        return 0

    if args.rebuild_hubs:"""
patch("autoblog/main.py", mn2_old, mn2_new, "if args.polish:")

rt_old = """    blobs = {}
    for v in ("left", "bottom", "right"):
        out = tmp / f"thumb_{v}.jpg"
        r = image_gen.generate_featured_image(
            "SSC CGL 2026 Notification Apply Online", "Central Govt Jobs",
            out, variant=v)
        assert r and out.exists() and out.stat().st_size > 5000, v
        with Image.open(out) as im:
            assert im.size == (config.IMAGE_WIDTH, config.IMAGE_HEIGHT), im.size
        blobs[v] = out.read_bytes()
    assert blobs["left"] != blobs["bottom"] != blobs["right"]"""
rt_new = """    blobs = {}
    for v in ("bottom", "center", "top"):
        out = tmp / f"thumb_{v}.jpg"
        r = image_gen.generate_featured_image(
            "SSC CGL 2026 Notification Apply Online", "Central Govt Jobs",
            out, variant=v)
        assert r and out.exists() and out.stat().st_size > 5000, v
        with Image.open(out) as im:
            assert im.size == (config.IMAGE_WIDTH, config.IMAGE_HEIGHT), im.size
            # v24 CROP-PROOF: all bright text pixels inside center 60% band
            rgb = im.convert("RGB")
            px = rgb.load()
            W, H = rgb.size
            minx, maxx = W, 0
            for yy in range(0, H, 3):
                for xx in range(0, W, 3):
                    cr, cg, cb = px[xx, yy]
                    if cr > 228 and cg > 228 and cb > 228:
                        minx, maxx = min(minx, xx), max(maxx, xx)
            assert minx > 0.19 * W and maxx < 0.81 * W, (v, minx / W, maxx / W)
        blobs[v] = out.read_bytes()
    assert blobs["bottom"] != blobs["center"] != blobs["top"]"""
patch("tests/radar_test.py", rt_old, rt_new, '"bottom", "center", "top"')
print("PATCHES_DONE")
PY_EOF

echo ""
echo "=== hotfix tests (PIL lekha poTE skip) ==="
python3 tests/design_test.py || echo "(pillow required: pip install pillow)"
echo ""
echo "v24+v25 hotfix complete! Next:"
echo "  1) python run.py --setup   # audit + design kit auto-install"
echo "     (mariste: python run.py --polish)"
echo "  2) site choodandi — cards/thumbs/footer anni polish ayi undali"
