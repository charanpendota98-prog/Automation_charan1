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
