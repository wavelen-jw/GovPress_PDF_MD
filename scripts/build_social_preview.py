#!/usr/bin/env python3
"""Render the social preview image used for Telegram / OG link previews."""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "ui" / "assets" / "social-preview.png"

WIDTH, HEIGHT = 1200, 630
INK = (13, 13, 13)
PAPER = (248, 248, 245)
RED = (255, 59, 59)
GREEN = (34, 197, 94)

FONT_BOLD = "/usr/share/fonts/truetype/nanum/NanumSquareB.ttf"
FONT_REG = "/usr/share/fonts/truetype/nanum/NanumSquareR.ttf"


def _font(path: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(path, size=size)


def _radial_glow(size: tuple[int, int], center: tuple[int, int], radius: int, color: tuple[int, int, int], alpha: int) -> Image.Image:
    glow = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(glow)
    draw.ellipse(
        (center[0] - radius, center[1] - radius, center[0] + radius, center[1] + radius),
        fill=(*color, alpha),
    )
    return glow.filter(ImageFilter.GaussianBlur(radius // 2))


def _text_size(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont) -> tuple[int, int]:
    left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
    return right - left, bottom - top


def _chip(draw: ImageDraw.ImageDraw, xy: tuple[int, int], text: str, font: ImageFont.FreeTypeFont, *, filled: bool) -> int:
    pad_x, pad_y = 24, 14
    tw, th = _text_size(draw, text, font)
    box_w = tw + pad_x * 2
    box_h = th + pad_y * 2
    x, y = xy
    if filled:
        draw.rounded_rectangle((x, y, x + box_w, y + box_h), radius=8, fill=GREEN)
        draw.text((x + pad_x, y + pad_y - 4), text, font=font, fill=INK)
    else:
        draw.rounded_rectangle(
            (x, y, x + box_w, y + box_h),
            radius=8,
            outline=(*PAPER, 90),
            width=2,
        )
        draw.text((x + pad_x, y + pad_y - 4), text, font=font, fill=(*PAPER, 200))
    return box_w


def render() -> None:
    canvas = Image.new("RGB", (WIDTH, HEIGHT), INK)

    glow_green = _radial_glow((WIDTH, HEIGHT), (1020, 130), 360, GREEN, 70)
    glow_red = _radial_glow((WIDTH, HEIGHT), (90, 540), 320, RED, 55)
    canvas = Image.alpha_composite(canvas.convert("RGBA"), glow_green)
    canvas = Image.alpha_composite(canvas, glow_red).convert("RGB")

    draw = ImageDraw.Draw(canvas, "RGBA")

    draw.rectangle((0, 0, WIDTH, 12), fill=RED)

    pad_left = 92
    eyebrow_font = _font(FONT_BOLD, 28)
    title_font = _font(FONT_BOLD, 224)
    tagline_font = _font(FONT_BOLD, 40)
    sub_font = _font(FONT_REG, 28)
    chip_font = _font(FONT_BOLD, 26)
    domain_font = _font(FONT_BOLD, 24)

    eyebrow = "정부문서 PDF · HWPX 변환"
    draw.text((pad_left, 78), eyebrow, font=eyebrow_font, fill=(*PAPER, 140))

    title = "읽힘"
    draw.text((pad_left - 8, 132), title, font=title_font, fill=PAPER)

    title_w, title_h = _text_size(draw, title, title_font)
    underline_y = 132 + title_h + 4
    draw.rectangle(
        (pad_left, underline_y, pad_left + 96, underline_y + 6),
        fill=RED,
    )

    tagline = "정부문서를 사람도 AI도 읽게 한다."
    draw.text((pad_left, underline_y + 36), tagline, font=tagline_font, fill=PAPER)

    sub = "PDF·HWPX 보도자료를 흐름이 살아있는 Markdown으로."
    draw.text((pad_left, underline_y + 96), sub, font=sub_font, fill=(*PAPER, 175))

    chip_y = HEIGHT - 110
    cursor_x = pad_left
    cursor_x += _chip(draw, (cursor_x, chip_y), "PDF", chip_font, filled=False) + 14
    cursor_x += _chip(draw, (cursor_x, chip_y), "HWPX", chip_font, filled=False) + 22

    arrow_font = _font(FONT_BOLD, 36)
    aw, ah = _text_size(draw, "→", arrow_font)
    draw.text((cursor_x, chip_y + 8), "→", font=arrow_font, fill=(*PAPER, 175))
    cursor_x += aw + 22

    _chip(draw, (cursor_x, chip_y), "Markdown", chip_font, filled=True)

    domain = "govpress.cloud"
    dw, _ = _text_size(draw, domain, domain_font)
    draw.text((WIDTH - pad_left - dw, HEIGHT - 70), domain, font=domain_font, fill=(*PAPER, 130))

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(OUTPUT, format="PNG", optimize=True)


if __name__ == "__main__":
    render()
    print(f"wrote {OUTPUT}")
