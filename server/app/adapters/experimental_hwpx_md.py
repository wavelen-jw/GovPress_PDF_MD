from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import zipfile


DEFAULT_PYTHON = "/opt/govpress-hwpx-md-venv/bin/python"


class HwpxMdConversionTimeout(TimeoutError):
    def __init__(self, *, timeout_seconds: int, diagnostics: str) -> None:
        super().__init__(f"govpress-hwpx-md timed out after {timeout_seconds} seconds")
        self.timeout_seconds = timeout_seconds
        self.diagnostics = diagnostics


def _python_bin() -> str:
    return os.environ.get("GOVPRESS_HWPX_MD_PYTHON", DEFAULT_PYTHON).strip()


def _rhwp_bin() -> str:
    return os.environ.get("GOVPRESS_RHWP_BIN", "rhwp").strip()


def _rhwp_summary() -> dict[str, object]:
    binary = _rhwp_bin()
    if not binary:
        return {"available": False, "binary": "", "version": "", "reason": "GOVPRESS_RHWP_BIN is empty"}
    try:
        result = subprocess.run(
            [binary, "--version"],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except Exception as exc:
        return {"available": False, "binary": binary, "version": "", "reason": str(exc)}
    version = (result.stdout or "").strip()
    detail = (result.stderr or result.stdout or "").strip()
    return {
        "available": result.returncode == 0 and bool(version),
        "binary": binary,
        "version": version,
        "reason": "" if result.returncode == 0 and version else detail[:1000],
    }


def _document_diagnostics(path: str | Path) -> str:
    try:
        file_path = Path(path)
        if file_path.suffix.lower() == ".hwp":
            return f"hwp_bytes={file_path.stat().st_size}"
        with zipfile.ZipFile(file_path) as archive:
            infos = archive.infolist()
            xml_infos = [item for item in infos if item.filename.endswith(".xml")]
            section_infos = [
                item
                for item in infos
                if item.filename.startswith("Contents/section") and item.filename.endswith(".xml")
            ]
            bindata_infos = [item for item in infos if item.filename.startswith("BinData/")]
            largest_sections = sorted(section_infos, key=lambda item: item.file_size, reverse=True)[:5]
            largest = ", ".join(f"{item.filename}:{item.file_size}" for item in largest_sections) or "-"
            return (
                f"zip_bytes={file_path.stat().st_size}; "
                f"entries={len(infos)}; "
                f"xml_uncompressed_bytes={sum(item.file_size for item in xml_infos)}; "
                f"section_count={len(section_infos)}; "
                f"section_uncompressed_bytes={sum(item.file_size for item in section_infos)}; "
                f"bindata_count={len(bindata_infos)}; "
                f"bindata_uncompressed_bytes={sum(item.file_size for item in bindata_infos)}; "
                f"largest_sections={largest}"
            )
    except Exception as exc:
        return f"diagnostics_unavailable={exc}"


def runtime_summary() -> dict[str, object]:
    python_bin = _python_bin()
    rhwp = _rhwp_summary()
    if not python_bin:
        return {
            "available": False,
            "version": "",
            "backend": "unavailable",
            "python": "",
            "hwp_available": False,
            "rhwp": rhwp,
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
            "hwp_available": False,
            "rhwp": rhwp,
            "reason": str(exc),
        }
    version = (result.stdout or "").strip().lstrip("v")
    detail = (result.stderr or result.stdout or "").strip()
    return {
        "available": result.returncode == 0 and bool(version),
        "version": version,
        "backend": "subprocess" if result.returncode == 0 else "unavailable",
        "python": python_bin,
        "hwp_available": result.returncode == 0 and bool(version) and bool(rhwp["available"]),
        "rhwp": rhwp,
        "reason": "" if result.returncode == 0 and version else detail[:1000],
    }


def convert_document(path: str | Path, *, document_metadata: dict[str, object] | None = None) -> str:
    python_bin = _python_bin()
    if not python_bin:
        raise RuntimeError("GOVPRESS_HWPX_MD_PYTHON is not configured")
    timeout = int(os.environ.get("GOVPRESS_HWPX_MD_TIMEOUT_SECONDS", "300"))
    command = [python_bin, "-m", "govpress_converter", str(path)]
    if document_metadata:
        command.extend(["--metadata-json", json.dumps(document_metadata, ensure_ascii=False)])
    try:
        result = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        diagnostics = _document_diagnostics(path)
        raise HwpxMdConversionTimeout(timeout_seconds=timeout, diagnostics=diagnostics) from exc
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()
        raise RuntimeError(f"govpress-hwpx-md failed: {detail or result.returncode}")
    return result.stdout


def convert_hwpx(path: str | Path, *, document_metadata: dict[str, object] | None = None) -> str:
    """Backward-compatible HWPX adapter."""

    return convert_document(path, document_metadata=document_metadata)
