from __future__ import annotations

import hashlib
from pathlib import Path
import re


MAX_FILENAME_BYTES = 255


def safe_filename(file_name: str) -> str:
    """Remove path components and characters unsafe for stored artifacts."""
    name = Path(file_name).name
    name = re.sub(r"[^\w\s.\-()]", "_", name)
    return name or "document"


def _truncate_utf8(value: str, max_bytes: int) -> str:
    used = 0
    characters: list[str] = []
    for character in value:
        size = len(character.encode("utf-8"))
        if used + size > max_bytes:
            break
        characters.append(character)
        used += size
    return "".join(characters)


def prefixed_safe_filename(prefix: str, file_name: str, *, max_bytes: int = MAX_FILENAME_BYTES) -> str:
    prefix_text = f"{prefix}-"
    safe_name = safe_filename(file_name)
    candidate = f"{prefix_text}{safe_name}"
    if len(candidate.encode("utf-8")) <= max_bytes:
        return candidate

    suffix = Path(safe_name).suffix
    stem = safe_name[: -len(suffix)] if suffix else safe_name
    digest = hashlib.sha256(safe_name.encode("utf-8")).hexdigest()[:10]
    marker = f"-{digest}"
    reserved = len((prefix_text + marker + suffix).encode("utf-8"))
    if reserved >= max_bytes:
        raise ValueError("artifact filename prefix and extension exceed filesystem limit")
    stem_budget = max_bytes - reserved
    truncated_stem = _truncate_utf8(stem, stem_budget) or _truncate_utf8("document", stem_budget)
    if not truncated_stem:
        raise ValueError("artifact filename has no room for a basename")
    result = f"{prefix_text}{truncated_stem}{marker}{suffix}"
    if len(result.encode("utf-8")) > max_bytes:
        raise ValueError("artifact filename exceeds filesystem limit")
    return result
