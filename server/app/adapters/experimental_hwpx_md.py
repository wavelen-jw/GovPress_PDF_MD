from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess


DEFAULT_PYTHON = "/opt/govpress-hwpx-md-venv/bin/python"


def _python_bin() -> str:
    return os.environ.get("GOVPRESS_HWPX_MD_PYTHON", DEFAULT_PYTHON).strip()


def runtime_summary() -> dict[str, object]:
    python_bin = _python_bin()
    if not python_bin:
        return {
            "available": False,
            "version": "",
            "backend": "unavailable",
            "python": "",
            "reason": "GOVPRESS_HWPX_MD_PYTHON is not configured",
        }
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
    except Exception as exc:
        return {
            "available": False,
            "version": "",
            "backend": "unavailable",
            "python": python_bin,
            "reason": str(exc),
        }
    version = (result.stdout or "").strip().lstrip("v")
    detail = (result.stderr or result.stdout or "").strip()
    return {
        "available": result.returncode == 0 and bool(version),
        "version": version,
        "backend": "subprocess" if result.returncode == 0 else "unavailable",
        "python": python_bin,
        "reason": "" if result.returncode == 0 and version else detail[:1000],
    }


def convert_hwpx(path: str | Path, *, document_metadata: dict[str, object] | None = None) -> str:
    python_bin = _python_bin()
    if not python_bin:
        raise RuntimeError("GOVPRESS_HWPX_MD_PYTHON is not configured")
    timeout = int(os.environ.get("GOVPRESS_HWPX_MD_TIMEOUT_SECONDS", "300"))
    command = [python_bin, "-m", "govpress_converter", str(path)]
    if document_metadata:
        command.extend(["--metadata-json", json.dumps(document_metadata, ensure_ascii=False)])
    result = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()
        raise RuntimeError(f"govpress-hwpx-md failed: {detail or result.returncode}")
    return result.stdout
