from __future__ import annotations

import os
from pathlib import Path
import zipfile

from ..models import JobQueue


def _int_env(name: str, default: int) -> int:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    try:
        return max(0, int(raw))
    except ValueError:
        return default


def classify_job_queue(file_path: Path) -> JobQueue:
    suffix = file_path.suffix.lower()
    if suffix == ".hwp":
        bytes_threshold = _int_env("GOVPRESS_LARGE_HWP_BYTES", 15_000_000)
        try:
            if bytes_threshold and file_path.stat().st_size >= bytes_threshold:
                return "large"
        except OSError:
            pass
        return "default"
    if suffix != ".hwpx":
        return "default"

    zip_bytes_threshold = _int_env("GOVPRESS_LARGE_HWPX_ZIP_BYTES", 15_000_000)
    xml_bytes_threshold = _int_env("GOVPRESS_LARGE_HWPX_XML_BYTES", 80_000_000)
    section_count_threshold = _int_env("GOVPRESS_LARGE_HWPX_SECTION_COUNT", 80)

    try:
        zip_bytes = file_path.stat().st_size
        if zip_bytes_threshold and zip_bytes >= zip_bytes_threshold:
            return "large"

        xml_uncompressed_bytes = 0
        section_count = 0
        with zipfile.ZipFile(file_path) as archive:
            for info in archive.infolist():
                name = info.filename
                if name.startswith("Contents/section") and name.endswith(".xml"):
                    section_count += 1
                if name.endswith(".xml"):
                    xml_uncompressed_bytes += info.file_size

        if section_count_threshold and section_count >= section_count_threshold:
            return "large"
        if xml_bytes_threshold and xml_uncompressed_bytes >= xml_bytes_threshold:
            return "large"
    except (OSError, zipfile.BadZipFile):
        return "default"

    return "default"
