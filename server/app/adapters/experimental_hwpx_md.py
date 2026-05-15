from __future__ import annotations

import os
from pathlib import Path
import subprocess


DEFAULT_PYTHON = "/opt/govpress-hwpx-md-venv/bin/python"


def _python_bin() -> str:
    return os.environ.get("GOVPRESS_HWPX_MD_PYTHON", DEFAULT_PYTHON).strip()


def runtime_summary() -> dict[str, object]:
    python_bin = _python_bin()
    if not python_bin:
        return {"available": False, "version": "", "backend": "unavailable"}
    script = (
        "import importlib.metadata as metadata\n"
        "try:\n"
        "    version = metadata.version('govpress-hwpx-md')\n"
        "except metadata.PackageNotFoundError:\n"
        "    try:\n"
        "        import govpress_converter\n"
        "        version = getattr(govpress_converter, '__version__', '') or ''\n"
        "    except Exception:\n"
        "        version = ''\n"
        "print(version)\n"
    )
    try:
        result = subprocess.run(
            [python_bin, "-c", script],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except Exception:
        return {"available": False, "version": "", "backend": "unavailable"}
    version = (result.stdout or "").strip().lstrip("v")
    return {
        "available": result.returncode == 0 and bool(version),
        "version": version,
        "backend": "subprocess" if result.returncode == 0 else "unavailable",
    }


def convert_hwpx(path: str | Path) -> str:
    python_bin = _python_bin()
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
