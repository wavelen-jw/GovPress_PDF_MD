from __future__ import annotations

import logging
from pathlib import Path
import sys


LOGGER_NAME = "GovPress_PDF_MD"


def configure_logging(log_path: Path | None = None) -> logging.Logger:
    """Create and configure the shared application logger."""
    logger = logging.getLogger(LOGGER_NAME)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    if log_path:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_path, encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def ensure_utf8_text(text: str) -> str:
    """Normalize text into UTF-8-safe string data."""
    return text.encode("utf-8", errors="ignore").decode("utf-8")


def save_markdown_file(path: Path, markdown: str) -> None:
    """Write markdown content to disk with UTF-8 encoding."""
    path.write_text(markdown, encoding="utf-8")


def resolve_resource_path(*parts: str) -> Path:
    """Resolve bundled asset paths for source runs and PyInstaller builds."""
    if getattr(sys, "_MEIPASS", None):
        return Path(sys._MEIPASS).joinpath(*parts)
    return Path(__file__).resolve().parent.parent.joinpath(*parts)
