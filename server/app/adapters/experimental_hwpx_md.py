from __future__ import annotations

import os
from pathlib import Path
import subprocess


DEFAULT_PYTHON = "/opt/govpress-hwpx-md-venv/bin/python"


def convert_hwpx(path: str | Path) -> str:
    python_bin = os.environ.get("GOVPRESS_HWPX_MD_PYTHON", DEFAULT_PYTHON).strip()
    if not python_bin:
        raise RuntimeError("GOVPRESS_HWPX_MD_PYTHON is not configured")
    timeout = int(os.environ.get("GOVPRESS_HWPX_MD_TIMEOUT_SECONDS", "300"))
    result = subprocess.run(
        [python_bin, "-m", "govpress_converter", str(path)],
        check=False,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()
        raise RuntimeError(f"govpress-hwpx-md failed: {detail or result.returncode}")
    return result.stdout
