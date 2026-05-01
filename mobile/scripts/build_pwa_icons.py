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
    return Image.open(SOURCE_LOGO).convert("RGBA")


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
    _save_png(source, "icon-512-maskable.png", 512, padding_ratio=0.08)
    _save_png(source, "icon-192-maskable.png", 192, padding_ratio=0.08)
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
