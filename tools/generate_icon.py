from __future__ import annotations

import binascii
import struct
import zlib
from pathlib import Path


ICON_SIZE = 256


def _write_chunk(handle, chunk_type: bytes, data: bytes) -> None:
    handle.write(struct.pack(">I", len(data)))
    handle.write(chunk_type)
    handle.write(data)
    crc = zlib.crc32(chunk_type)
    crc = zlib.crc32(data, crc)
    handle.write(struct.pack(">I", crc & 0xFFFFFFFF))


def _make_png_bytes(size: int) -> bytes:
    width = height = size
    rows = bytearray()
    for y in range(height):
        rows.append(0)
        for x in range(width):
            r, g, b, a = _pixel(x, y, width, height)
            rows.extend((r, g, b, a))

    png = bytearray(b"\x89PNG\r\n\x1a\n")
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    compressed = zlib.compress(bytes(rows), 9)
    from io import BytesIO

    with BytesIO() as buffer:
        buffer.write(png)
        _write_chunk(buffer, b"IHDR", ihdr)
        _write_chunk(buffer, b"IDAT", compressed)
        _write_chunk(buffer, b"IEND", b"")
        return buffer.getvalue()


def _pixel(x: int, y: int, width: int, height: int) -> tuple[int, int, int, int]:
    teal = (14, 116, 144, 255)
    teal_dark = (8, 77, 96, 255)
    cream = (250, 252, 250, 255)
    fold = (223, 231, 234, 255)
    ink = (20, 42, 58, 255)
    mint = (21, 128, 61, 255)

    bg = teal if (x + y) % 2 == 0 else teal_dark
    color = bg

    doc_left = int(width * 0.19)
    doc_top = int(height * 0.11)
    doc_right = int(width * 0.79)
    doc_bottom = int(height * 0.89)
    fold_size = int(width * 0.14)
    radius = int(width * 0.06)

    if _inside_round_rect(x, y, doc_left, doc_top, doc_right, doc_bottom, radius):
        color = cream
        if x > doc_right - fold_size and y < doc_top + fold_size:
            if x + y > doc_right + doc_top:
                color = fold

        if doc_left + 24 < x < doc_right - 24:
            if doc_top + 40 < y < doc_top + 56:
                color = ink
            if doc_top + 68 < y < doc_top + 86:
                color = ink
            if doc_top + 104 < y < doc_top + 114 and doc_left + 28 < x < doc_right - 28:
                color = (116, 136, 148, 255)
            if doc_top + 132 < y < doc_top + 142 and doc_left + 28 < x < doc_right - 44:
                color = (116, 136, 148, 255)
            if doc_top + 160 < y < doc_top + 170 and doc_left + 28 < x < doc_right - 62:
                color = (116, 136, 148, 255)

        hash_left = doc_left + 28
        hash_top = doc_top + 32
        if hash_left < x < hash_left + 40 and hash_top < y < hash_top + 56:
            if x in (hash_left + 10, hash_left + 24) or y in (hash_top + 14, hash_top + 32):
                color = mint

        arrow_left = doc_left + 32
        arrow_top = doc_top + 178
        if arrow_top < y < arrow_top + 26:
            dy = y - arrow_top
            if arrow_left + dy < x < arrow_left + 12 + dy:
                color = mint
            if arrow_left + 12 < x < arrow_left + 72:
                if arrow_top + 10 < y < arrow_top + 18:
                    color = mint

    return color


def _inside_round_rect(
    x: int, y: int, left: int, top: int, right: int, bottom: int, radius: int
) -> bool:
    if left + radius <= x <= right - radius and top <= y <= bottom:
        return True
    if left <= x <= right and top + radius <= y <= bottom - radius:
        return True

    corners = (
        (left + radius, top + radius),
        (right - radius, top + radius),
        (left + radius, bottom - radius),
        (right - radius, bottom - radius),
    )
    for cx, cy in corners:
        if (x - cx) ** 2 + (y - cy) ** 2 <= radius**2:
            return True
    return False


def write_ico(output_path: Path) -> None:
    png_bytes = _make_png_bytes(ICON_SIZE)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("wb") as handle:
        handle.write(struct.pack("<HHH", 0, 1, 1))
        handle.write(
            struct.pack(
                "<BBBBHHII",
                0,
                0,
                0,
                0,
                1,
                32,
                len(png_bytes),
                6 + 16,
            )
        )
        handle.write(png_bytes)


if __name__ == "__main__":
    target = Path(__file__).resolve().parent.parent / "assets" / "icons" / "govpress.ico"
    write_ico(target)
    print(f"created {target}")
