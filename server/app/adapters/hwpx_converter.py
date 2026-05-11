"""Compatibility adapter around the configured GovPress conversion engine."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import tempfile

from .conversion_engine import convert_hwpx as _convert_hwpx

__all__ = ["convert_hwpx"]


def _conversion_timeout_seconds() -> int:
    raw = os.environ.get("GOVPRESS_HWPX_CONVERSION_TIMEOUT_SECONDS", "45").strip()
    try:
        return int(raw)
    except ValueError:
        return 45


def _convert_hwpx_in_subprocess(path: str, *, table_mode: str, timeout: int) -> str:
    script = """
from pathlib import Path
import sys

from server.app.adapters.conversion_engine import convert_hwpx

markdown = convert_hwpx(sys.argv[1], table_mode=sys.argv[2])
Path(sys.argv[3]).write_text(markdown, encoding="utf-8")
"""
    with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as handle:
        output_path = Path(handle.name)
    try:
        result = subprocess.run(
            [sys.executable, "-c", script, path, table_mode, str(output_path)],
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if result.returncode != 0:
            detail = (result.stderr or result.stdout or "").strip()
            if len(detail) > 1000:
                detail = detail[-1000:]
            raise RuntimeError(detail or f"HWPX conversion failed: exit {result.returncode}")
        return output_path.read_text(encoding="utf-8")
    except subprocess.TimeoutExpired as exc:
        raise TimeoutError(f"HWPX conversion timed out after {timeout} seconds") from exc
    finally:
        output_path.unlink(missing_ok=True)


def convert_hwpx(path: str | Path, *, table_mode: str = "text") -> str:
    timeout = _conversion_timeout_seconds()
    if timeout <= 0:
        return _convert_hwpx(path, table_mode=table_mode)
    return _convert_hwpx_in_subprocess(str(path), table_mode=table_mode, timeout=timeout)
