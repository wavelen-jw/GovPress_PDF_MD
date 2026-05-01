#!/usr/bin/env python3
"""Render PWA icon assets for the web app."""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
ICON_DIR = ROOT / "public" / "icons"

INK = (18, 34, 31, 255)
INK_MUTED = (58, 74, 70, 255)
PAPER = (250, 248, 241, 255)
PAPER_EDGE = (231, 225, 214, 255)
ACCENT = (183, 94, 31, 255)
ACCENT_DARK = (126, 56, 24, 255)
BG_TOP = (23, 53, 48)
BG_BOTTOM = (10, 29, 27)


def _lerp(a: int, b: int, t: float) -> int:
    return round(a + (b - a) * t)


def _rounded_mask(size: int, radius: int) -> Image.Image:
    mask = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle((0, 0, size, size), radius=radius, fill=255)
    return mask


def _background(size: int) -> Image.Image:
    scale = size / 512
    image = Image.new("RGBA", (size, size))
    px = image.load()
    for y in range(size):
        t = y / max(1, size - 1)
        row = tuple(_lerp(BG_TOP[i], BG_BOTTOM[i], t) for i in range(3)) + (255,)
        for x in range(size):
            px[x, y] = row

    draw = ImageDraw.Draw(image, "RGBA")
    draw.rounded_rectangle(
        (round(44 * scale), round(42 * scale), round(468 * scale), round(470 * scale)),
        radius=round(106 * scale),
        outline=(255, 255, 255, 18),
        width=max(1, round(2 * scale)),
    )
    return image


def _draw_icon(size: int, *, maskable: bool) -> Image.Image:
    scale = size / 512
    image = _background(size)
    draw = ImageDraw.Draw(image, "RGBA")

    if maskable:
        doc_box = (
            round(122 * scale),
            round(78 * scale),
            round(390 * scale),
            round(426 * scale),
        )
    else:
        doc_box = (
            round(108 * scale),
            round(70 * scale),
            round(404 * scale),
            round(436 * scale),
        )

    x0, y0, x1, y1 = doc_box
    radius = round(42 * scale)
    fold = round(58 * scale)

    shadow = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow, "RGBA")
    shadow_draw.rounded_rectangle(doc_box, radius=radius, fill=(0, 0, 0, 110))
    shadow = shadow.filter(ImageFilter.GaussianBlur(max(1, round(13 * scale))))
    image.alpha_composite(shadow, (0, round(12 * scale)))
    draw = ImageDraw.Draw(image, "RGBA")

    draw.rounded_rectangle(doc_box, radius=radius, fill=PAPER)
    draw.polygon(
        [(x1 - fold, y0), (x1, y0), (x1, y0 + fold)],
        fill=PAPER_EDGE,
    )
    draw.line(
        [(x1 - fold + round(8 * scale), y0 + fold), (x1, y0 + fold)],
        fill=(194, 187, 176, 130),
        width=max(1, round(2 * scale)),
    )

    line_h = max(1, round(18 * scale))
    line_radius = max(1, round(8 * scale))
    left = x0 + round(72 * scale)
    top = y0 + round(98 * scale)
    raw_widths = [round(168 * scale), round(200 * scale), round(160 * scale), round(124 * scale)]
    max_line_width = x1 - left - round(42 * scale)
    widths = [min(width, max_line_width) for width in raw_widths]
    colors = [INK, INK, INK_MUTED, INK_MUTED]
    for index, width in enumerate(widths):
        y = top + round(index * 58 * scale)
        draw.rounded_rectangle(
            (left, y, left + width, y + line_h),
            radius=line_radius,
            fill=colors[index],
        )

    cursor_x = x0 + round(48 * scale)
    cursor_top = top - round(20 * scale)
    cursor_bottom = top + round(88 * scale)
    draw.rounded_rectangle(
        (
            cursor_x,
            cursor_top,
            cursor_x + round(15 * scale),
            cursor_bottom,
        ),
        radius=max(1, round(7 * scale)),
        fill=ACCENT,
    )
    draw.rounded_rectangle(
        (
            cursor_x + round(25 * scale),
            top + round(39 * scale),
            cursor_x + round(82 * scale),
            top + round(53 * scale),
        ),
        radius=max(1, round(7 * scale)),
        fill=ACCENT_DARK,
    )

    check = [
        (x0 + round(96 * scale), y1 - round(86 * scale)),
        (x0 + round(133 * scale), y1 - round(49 * scale)),
        (x0 + round(213 * scale), y1 - round(122 * scale)),
    ]
    draw.line(check, fill=ACCENT, width=max(2, round(27 * scale)), joint="curve")
    draw.line(check, fill=ACCENT_DARK, width=max(1, round(9 * scale)), joint="curve")

    return image


def _save_icon(source: Image.Image, name: str, size: int) -> None:
    resample = Image.Resampling.LANCZOS
    icon = source.resize((size, size), resample)
    if name == "apple-touch-icon.png":
        mask = _rounded_mask(size, round(size * 0.225))
        bg = Image.new("RGBA", (size, size), BG_TOP + (255,))
        bg.alpha_composite(icon)
        icon = Image.composite(bg, Image.new("RGBA", (size, size), (0, 0, 0, 0)), mask)
    icon.save(ICON_DIR / name, format="PNG", optimize=True)


def render() -> None:
    ICON_DIR.mkdir(parents=True, exist_ok=True)
    any_icon = _draw_icon(1024, maskable=False)
    maskable_icon = _draw_icon(1024, maskable=True)

    _save_icon(any_icon, "icon-512.png", 512)
    _save_icon(any_icon, "icon-192.png", 192)
    _save_icon(maskable_icon, "icon-512-maskable.png", 512)
    _save_icon(maskable_icon, "icon-192-maskable.png", 192)
    _save_icon(any_icon, "apple-touch-icon.png", 180)
    _save_icon(any_icon, "favicon-32.png", 32)


if __name__ == "__main__":
    render()
    for path in sorted(ICON_DIR.glob("*.png")):
        print(f"wrote {path}")
