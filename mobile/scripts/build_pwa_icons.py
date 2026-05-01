#!/usr/bin/env python3
"""Generate PWA icon assets from the canonical logo PNG."""
from __future__ import annotations

from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = ROOT.parent
SOURCE_LOGO = PROJECT_ROOT / "assets" / "icons" / "logo.png"
ICON_DIR = ROOT / "public" / "icons"


def _load_logo() -> Image.Image:
    if not SOURCE_LOGO.exists():
        raise FileNotFoundError(f"Missing source logo: {SOURCE_LOGO}")
    return _crop_empty_margin(Image.open(SOURCE_LOGO).convert("RGBA"))


def _crop_empty_margin(source: Image.Image) -> Image.Image:
    rgb = source.convert("RGB")
    width, height = rgb.size
    background = rgb.getpixel((0, 0))
    mask = Image.new("L", rgb.size, 0)
    rgb_pixels = rgb.load()
    mask_pixels = mask.load()
    threshold = 18

    for y in range(height):
        for x in range(width):
            pixel = rgb_pixels[x, y]
            if max(abs(pixel[index] - background[index]) for index in range(3)) > threshold:
                mask_pixels[x, y] = 255

    bbox = mask.getbbox()
    if not bbox:
        return source

    left, top, right, bottom = bbox
    margin = round(max(right - left, bottom - top) * 0.015)
    left = max(0, left - margin)
    top = max(0, top - margin)
    right = min(width, right + margin)
    bottom = min(height, bottom + margin)
    return source.crop((left, top, right, bottom))


def _contain_square(source: Image.Image, size: int, *, padding: int = 0) -> Image.Image:
    canvas = Image.new("RGBA", (size, size), (255, 255, 255, 0))
    target = max(1, size - padding * 2)
    image = source.copy()
    image.thumbnail((target, target), Image.Resampling.LANCZOS)
    x = (size - image.width) // 2
    y = (size - image.height) // 2
    canvas.alpha_composite(image, (x, y))
    return canvas


def _save_png(source: Image.Image, name: str, size: int, *, padding_ratio: float = 0) -> None:
    padding = round(size * padding_ratio)
    icon = _contain_square(source, size, padding=padding)
    icon.save(ICON_DIR / name, format="PNG", optimize=True)


def render() -> None:
    ICON_DIR.mkdir(parents=True, exist_ok=True)
    source = _load_logo()

    _save_png(source, "icon-512.png", 512)
    _save_png(source, "icon-192.png", 192)
    _save_png(source, "icon-512-maskable.png", 512)
    _save_png(source, "icon-192-maskable.png", 192)
    _save_png(source, "apple-touch-icon.png", 180)
    _save_png(source, "favicon-32.png", 32)

    _contain_square(source, 256).save(
        PROJECT_ROOT / "assets" / "icons" / "govpress.ico",
        format="ICO",
        sizes=[(16, 16), (32, 32), (48, 48), (256, 256)],
    )


if __name__ == "__main__":
    render()
    for path in sorted(ICON_DIR.glob("*.png")):
        print(f"wrote {path}")
