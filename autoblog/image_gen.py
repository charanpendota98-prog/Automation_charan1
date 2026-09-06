"""Featured-image generator using Pillow (no external API needed).

Creates a clean gradient banner with decorative shapes, the category
label, short English banner text and the site brand — saved as JPEG.
"""

import logging
import random
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

FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
]


def _load_font(size: int) -> ImageFont.FreeTypeFont:
    for path in FONT_CANDIDATES:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    log.warning("No TrueType font found; using default bitmap font")
    return ImageFont.load_default()


def _wrap(draw: ImageDraw.ImageDraw, text: str, font, max_width: int) -> list:
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
    return lines


def generate_featured_image(
    banner_text: str,
    category: str,
    out_path: Path,
) -> Optional[Path]:
    """Render a 1200x675 featured image. Returns path or None on failure."""
    try:
        w, h = config.IMAGE_WIDTH, config.IMAGE_HEIGHT
        idx = (_LAST_PALETTE["i"] + 1 + random.randint(0, len(PALETTES) - 2)) % len(PALETTES)
        _LAST_PALETTE["i"] = idx
        c1, c2 = PALETTES[idx]

        base = Image.new("RGB", (w, h))
        px = base.load()
        for y in range(h):
            t = y / (h - 1)
            r = int(c1[0] + (c2[0] - c1[0]) * t)
            g = int(c1[1] + (c2[1] - c1[1]) * t)
            b = int(c1[2] + (c2[2] - c1[2]) * t)
            for x in range(0, w, 4):
                px[x, y] = (r, g, b)
                px[x + 1, y] = (r, g, b)
                px[x + 2, y] = (r, g, b)
                px[x + 3, y] = (r, g, b)

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

        # top-left category pill
        label_font = _load_font(int(h * 0.055))
        label = category.upper()
        tw = draw.textlength(label, font=label_font)
        pad = int(h * 0.02)
        x0, y0 = int(w * 0.05), int(h * 0.07)
        draw.rounded_rectangle(
            [x0, y0, x0 + tw + pad * 2, y0 + label_font.size + pad * 2],
            radius=(label_font.size + pad * 2) // 2,
            fill=(255, 255, 255, 230),
        )
        draw.text((x0 + pad, y0 + pad - 2), label, font=label_font, fill=(25, 25, 45))

        # centered banner text
        text_font = _load_font(int(h * 0.11))
        lines = _wrap(draw, banner_text[:60], text_font, int(w * 0.84))
        line_h = text_font.size + 14
        total_h = len(lines) * line_h
        y = (h - total_h) // 2
        for line in lines:
            lw = draw.textlength(line, font=text_font)
            x = (w - lw) / 2
            draw.text((x + 3, y + 3), line, font=text_font, fill=(0, 0, 0, 120))
            draw.text((x, y), line, font=text_font, fill=(255, 255, 255))
            y += line_h

        # bottom brand
        brand_font = _load_font(int(h * 0.04))
        brand = config.SITE_BRAND
        bw = draw.textlength(brand, font=brand_font)
        draw.text((w - bw - int(w * 0.04), h - brand_font.size - int(h * 0.05)),
                  brand, font=brand_font, fill=(255, 255, 255, 220))

        out_path.parent.mkdir(parents=True, exist_ok=True)
        img.convert("RGB").save(str(out_path), "JPEG", quality=88, optimize=True)
        return out_path
    except Exception:
        log.exception("Featured image generation failed — continuing without image")
        return None
