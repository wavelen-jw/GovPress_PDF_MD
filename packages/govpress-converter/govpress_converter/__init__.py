"""Public contract for the GovPress converter package."""

from __future__ import annotations

from pathlib import Path
from typing import Literal, Union

TableMode = Literal["text", "html"]

def convert_hwpx(path: Union[str, Path], *, table_mode: TableMode = "text") -> str:
    raise RuntimeError(
        "This public repository only ships the govpress-converter interface contract. "
        "Install the private converter package build to use convert_hwpx()."
    )


def convert_pdf(path: Union[str, Path], timeout: int = 300) -> str:
    raise RuntimeError(
        "This public repository only ships the govpress-converter interface contract. "
        "Install the private converter package build to use convert_pdf()."
    )


__all__ = ["convert_hwpx", "convert_pdf", "TableMode"]
__version__ = "0.1.0"
