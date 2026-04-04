"""govpress-converter: HWPX/PDF → Markdown conversion library for Korean government documents."""

from __future__ import annotations

from pathlib import Path
from typing import Union

from ._core.hwpx_converter import convert_hwpx as _convert_hwpx
from ._core.converter import convert_pdf_to_markdown as _convert_pdf


def convert_hwpx(path: Union[str, Path]) -> str:
    """Convert an HWPX file to Markdown.

    Args:
        path: Path to the .hwpx file.

    Returns:
        Markdown string.
    """
    return _convert_hwpx(Path(path))


def convert_pdf(path: Union[str, Path], timeout: int = 300) -> str:
    """Convert a PDF file to Markdown using OpenDataLoader (requires Java 11+).

    Args:
        path: Path to the .pdf file.
        timeout: Conversion timeout in seconds (default 300).

    Returns:
        Markdown string.

    Raises:
        RuntimeError: If Java or OpenDataLoader is not available.
        TimeoutError: If conversion exceeds ``timeout`` seconds.
    """
    return _convert_pdf(str(path), timeout_seconds=timeout)


__all__ = ["convert_hwpx", "convert_pdf"]
__version__ = "0.1.0"
