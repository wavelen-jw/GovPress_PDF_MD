from __future__ import annotations

import inspect
import os
import platform
import re
from functools import partial
from importlib import metadata
from pathlib import Path

from fastapi import APIRouter, Depends


def _normalize_version(raw: str | None) -> str | None:
    value = (raw or "").strip()
    if not value:
        return None
    if value.startswith("v"):
        return value[1:]
    return value


def _classify_backend(module_path: Path, distribution_version: str | None) -> str:
    if any(part in {"site-packages", "dist-packages"} for part in module_path.parts) and distribution_version:
        return "package"
    path = module_path.as_posix()
    if "gov-md-converter" in path:
        return "local-root"
    if "packages/govpress-converter" in path:
        return "bundled-root"
    if distribution_version:
        return "package"
    return "unknown"


def _mask_converter_spec(raw: str | None) -> str:
    value = (raw or "").strip()
    if not value:
        return ""
    return re.sub(r"://([^/@]+)@", "://***@", value)


def build_router(settings, verify_admin_api_key) -> APIRouter:
    router = APIRouter(prefix="/v1/admin/runtime", tags=["admin-runtime"])

    @router.get("/converter")
    def get_converter_runtime(
        _authorized: None = Depends(partial(verify_admin_api_key, settings)),
    ) -> dict[str, object]:
        try:
            import govpress_converter
        except Exception as exc:
            return {
                "available": False,
                "reason": str(exc),
                "converter_spec": _mask_converter_spec(os.environ.get("GOVPRESS_CONVERTER_SPEC", "")),
                "converter_allow_local_fallback": os.environ.get(
                    "GOVPRESS_CONVERTER_ALLOW_LOCAL_FALLBACK",
                    "",
                ),
                "converter_min_version": os.environ.get("GOVPRESS_CONVERTER_MIN_VERSION", ""),
            }

        module_path = Path(getattr(govpress_converter, "__file__", "")).resolve()
        version = _normalize_version(getattr(govpress_converter, "__version__", "0.0.0")) or "0.0.0"
        try:
            dist_version = _normalize_version(metadata.version("govpress-converter"))
            if dist_version:
                version = dist_version
        except metadata.PackageNotFoundError:
            dist_version = None
        backend = _classify_backend(module_path, dist_version)

        return {
            "available": True,
            "version": version,
            "distribution_version": dist_version,
            "module_path": str(module_path),
            "backend": backend,
            "private_engine": backend != "bundled-root",
            "python_version": platform.python_version(),
            "platform": platform.platform(),
            "convert_hwpx_signature": str(inspect.signature(govpress_converter.convert_hwpx)),
            "convert_pdf_signature": str(inspect.signature(govpress_converter.convert_pdf)),
            "converter_spec": _mask_converter_spec(os.environ.get("GOVPRESS_CONVERTER_SPEC", "")),
            "converter_allow_local_fallback": os.environ.get(
                "GOVPRESS_CONVERTER_ALLOW_LOCAL_FALLBACK",
                "",
            ),
            "converter_min_version": os.environ.get("GOVPRESS_CONVERTER_MIN_VERSION", ""),
        }

    return router
