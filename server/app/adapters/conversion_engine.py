from __future__ import annotations

import importlib
import inspect
import os
from functools import lru_cache
from importlib import metadata
from pathlib import Path
import sys
from typing import Callable


def _env_flag(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() not in {"0", "false", "no", "off", ""}


def _call_convert_hwpx(
    fn: Callable[..., str],
    path: str,
    *,
    table_mode: str,
    document_metadata: dict[str, object] | None = None,
) -> str:
    try:
        signature = inspect.signature(fn)
    except (TypeError, ValueError):
        signature = None
    if signature is not None and "table_mode" in signature.parameters:
        kwargs: dict[str, object] = {"table_mode": table_mode}
        if document_metadata is not None and "document_metadata" in signature.parameters:
            kwargs["document_metadata"] = document_metadata
        return fn(path, **kwargs)
    if table_mode != "text":
        raise RuntimeError(
            "Configured GovPress conversion engine does not support table_mode; "
            "install a newer converter package build."
        )
    if signature is not None and document_metadata is not None and "document_metadata" in signature.parameters:
        return fn(path, document_metadata=document_metadata)
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

    if not _env_flag("GOVPRESS_CONVERTER_ALLOW_LOCAL_FALLBACK", False):
        raise RuntimeError(
            "GovPress conversion engine package import failed and local-root fallback is disabled. "
            "Install the private converter package for this environment. "
            f"Details: package backend unavailable: {package_exc}"
        ) from package_exc

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


def _normalize_version(raw: str | None) -> str | None:
    value = (raw or "").strip()
    if not value:
        return None
    if value.startswith("v"):
        return value[1:]
    return value


def runtime_summary() -> dict[str, object]:
    try:
        backend, _, _ = _load_backend()
        package = importlib.import_module("govpress_converter")
        version = _normalize_version(getattr(package, "__version__", None))
        try:
            dist_version = _normalize_version(metadata.version("govpress-converter"))
        except metadata.PackageNotFoundError:
            dist_version = None
        return {
            "available": True,
            "version": dist_version or version or "0.0.0",
            "backend": backend,
        }
    except Exception:
        return {
            "available": False,
            "version": "",
            "backend": "unavailable",
        }


def convert_hwpx(
    path: str | Path,
    *,
    table_mode: str = "text",
    document_metadata: dict[str, object] | None = None,
) -> str:
    _, convert, _ = _load_backend()
    return _call_convert_hwpx(convert, str(path), table_mode=table_mode, document_metadata=document_metadata)


def convert_pdf(path: str | Path, *, timeout: int = 300) -> str:
    _, _, convert = _load_backend()
    return _call_convert_pdf(convert, str(path), timeout=timeout)
