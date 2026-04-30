#!/usr/bin/env python3
"""Render the social preview image used for Telegram / OG link previews."""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "ui" / "assets" / "social-preview.png"

WIDTH, HEIGHT = 1200, 630
INK = (13, 13, 13)
PAPER = (248, 248, 245)
GREEN = (34, 197, 94)

FONT_BOLD = "/usr/share/fonts/truetype/nanum/NanumSquareB.ttf"
FONT_REG = "/usr/share/fonts/truetype/nanum/NanumSquareR.ttf"


def _font(path: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(path, size=size)


def _measure(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont):
    return draw.textbbox((0, 0), text, font=font, anchor="lt")


def _draw_centered(draw: ImageDraw.ImageDraw, y: int, text: str, font: ImageFont.FreeTypeFont, fill, *, tracking: int = 0) -> None:
    if tracking == 0:
        bbox = _measure(draw, text, font)
        w = bbox[2] - bbox[0]
        x = (WIDTH - w) // 2 - bbox[0]
        draw.text((x, y), text, font=font, fill=fill)
        return

    widths = []
    for ch in text:
        bbox = _measure(draw, ch, font)
        widths.append(bbox[2] - bbox[0])
    total = sum(widths) + tracking * max(0, len(text) - 1)
    x = (WIDTH - total) // 2
    for ch, w in zip(text, widths):
        bbox = _measure(draw, ch, font)
        draw.text((x - bbox[0], y), ch, font=font, fill=fill)
        x += w + tracking


def _draw_check(draw: ImageDraw.ImageDraw, center: tuple[int, int], color, *, size: int = 18, weight: int = 5) -> None:
    cx, cy = center
    half = size // 2
    p1 = (cx - half, cy + 1)
    p2 = (cx - half // 3, cy + half - 2)
    p3 = (cx + half + 2, cy - half)
    draw.line([p1, p2], fill=color, width=weight)
    draw.line([p2, p3], fill=color, width=weight)


def render() -> None:
    canvas = Image.new("RGB", (WIDTH, HEIGHT), INK)
    draw = ImageDraw.Draw(canvas, "RGBA")

    eyebrow_font = _font(FONT_BOLD, 22)
    title_font = _font(FONT_BOLD, 220)
    tag_main_font = _font(FONT_BOLD, 38)
    tag_sub_font = _font(FONT_REG, 30)
    flow_font = _font(FONT_BOLD, 24)

    eyebrow_y = 78
    _draw_centered(draw, eyebrow_y, "GOVERNMENT DOCUMENT CONVERTER",
                   eyebrow_font, (*PAPER, 110), tracking=6)

    title = "읽힘"
    title_bbox = _measure(draw, title, title_font)
    title_w = title_bbox[2] - title_bbox[0]
    title_h = title_bbox[3] - title_bbox[1]
    title_x = (WIDTH - title_w) // 2 - title_bbox[0]
    title_y = 152
    draw.text((title_x, title_y), title, font=title_font, fill=PAPER)
    title_baseline = title_y + title_h + title_bbox[1]

    tag_y = title_baseline + 30
    _draw_centered(draw, tag_y, "정부문서가 막힌 곳에서,",
                   tag_sub_font, (*PAPER, 165))
    _draw_centered(draw, tag_y + 50, "사람과 AI 모두 통하게 한다.",
                   tag_main_font, PAPER)

    flow_y = HEIGHT - 78
    pad_x_chip = 22
    box_h = 56
    gap = 14

    parts = [
        ("chip", ".hwpx"),
        ("plus", "+"),
        ("chip", ".pdf"),
        ("plus", "+"),
        ("chip", "HTML API"),
        ("arrow", "→"),
        ("result", ".md"),
    ]

    sized = []
    for kind, text in parts:
        bbox = _measure(draw, text, flow_font)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        if kind in ("chip", "result"):
            box_w = w + pad_x_chip * 2
            if kind == "result":
                box_w += 30  # extra room for the check mark
        else:
            box_w = w
        sized.append((kind, text, bbox, w, h, box_w))

    total_w = sum(s[5] for s in sized) + gap * (len(sized) - 1)
    cursor = (WIDTH - total_w) // 2

    for kind, text, bbox, w, h, box_w in sized:
        if kind == "chip":
            y = flow_y - box_h // 2
            draw.rounded_rectangle(
                (cursor, y, cursor + box_w, y + box_h),
                radius=10,
                outline=(*PAPER, 80),
                width=2,
            )
            tx = cursor + (box_w - w) // 2 - bbox[0]
            ty = y + (box_h - h) // 2 - bbox[1]
            draw.text((tx, ty), text, font=flow_font, fill=(*PAPER, 220))
        elif kind == "result":
            y = flow_y - box_h // 2
            draw.rounded_rectangle(
                (cursor, y, cursor + box_w, y + box_h),
                radius=10,
                fill=GREEN,
            )
            content_w = w + 22
            content_x = cursor + (box_w - content_w) // 2
            tx = content_x - bbox[0]
            ty = y + (box_h - h) // 2 - bbox[1]
            draw.text((tx, ty), text, font=flow_font, fill=INK)
            check_cx = content_x + w + 14
            check_cy = y + box_h // 2 + 1
            _draw_check(draw, (check_cx, check_cy), INK, size=18, weight=5)
        elif kind == "plus":
            tx = cursor - bbox[0]
            ty = flow_y - h // 2 - bbox[1]
            draw.text((tx, ty), text, font=flow_font, fill=(*PAPER, 130))
        elif kind == "arrow":
            tx = cursor - bbox[0]
            ty = flow_y - h // 2 - bbox[1]
            draw.text((tx, ty), text, font=flow_font, fill=(*PAPER, 160))
        cursor += box_w + gap

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(OUTPUT, format="PNG", optimize=True)


if __name__ == "__main__":
    render()
    print(f"wrote {OUTPUT}")
