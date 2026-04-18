from __future__ import annotations

import importlib
import inspect
import os
from functools import lru_cache
from pathlib import Path
import sys
from typing import Callable


def _call_convert_hwpx(
    fn: Callable[..., str],
    path: str,
    *,
    table_mode: str,
) -> str:
    try:
        signature = inspect.signature(fn)
    except (TypeError, ValueError):
        signature = None
    if signature is not None and "table_mode" in signature.parameters:
        return fn(path, table_mode=table_mode)
    if table_mode != "text":
        raise RuntimeError(
            "Configured GovPress conversion engine does not support table_mode; "
            "install a newer converter package build."
        )
    return fn(path)


def _call_convert_pdf(
    fn: Callable[..., str],
    path: str,
    *,
    timeout: int,
) -> str:
    try:
        signature = inspect.signature(fn)
    except (TypeError, ValueError):
        signature = None
    if signature is not None:
        if "timeout" in signature.parameters:
            return fn(path, timeout=timeout)
        if "timeout_seconds" in signature.parameters:
            return fn(path, timeout_seconds=timeout)
    return fn(path)


@lru_cache(maxsize=1)
def _load_backend() -> tuple[str, Callable[..., str], Callable[..., str]]:
    try:
        package = importlib.import_module("govpress_converter")
        convert_hwpx = getattr(package, "convert_hwpx")
        convert_pdf = getattr(package, "convert_pdf")
        return ("package", convert_hwpx, convert_pdf)
    except Exception as exc:
        package_exc = exc

    gov_md_root = os.environ.get("GOV_MD_CONVERTER_ROOT")
    search_roots: list[Path] = []
    if gov_md_root:
        root = Path(gov_md_root)
        search_roots.extend([root, root / "src"])

    for root in search_roots:
        if not root.exists():
            continue
        root_str = str(root)
        if root_str not in sys.path:
            sys.path.insert(0, root_str)
        try:
            package = importlib.import_module("govpress_converter")
            convert_hwpx = getattr(package, "convert_hwpx")
            convert_pdf = getattr(package, "convert_pdf")
            return ("local-root", convert_hwpx, convert_pdf)
        except Exception:
            continue

    raise RuntimeError(
        "GovPress conversion engine is not configured. "
        "Install the private converter package and set "
        "`GOVPRESS_CONVERTER_SPEC` for builds/deployments. "
        f"Details: package backend unavailable: {package_exc}"
    ) from package_exc


def reset_backend_cache() -> None:
    _load_backend.cache_clear()


def backend_name() -> str:
    backend, _, _ = _load_backend()
    return backend


def convert_hwpx(path: str | Path, *, table_mode: str = "text") -> str:
    _, convert, _ = _load_backend()
    return _call_convert_hwpx(convert, str(path), table_mode=table_mode)


def convert_pdf(path: str | Path, *, timeout: int = 300) -> str:
    _, _, convert = _load_backend()
    return _call_convert_pdf(convert, str(path), timeout=timeout)
