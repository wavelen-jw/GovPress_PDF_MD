from __future__ import annotations

import inspect
import os
import platform
from functools import partial
from importlib import metadata
from pathlib import Path

from fastapi import APIRouter, Depends


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
                "converter_spec": os.environ.get("GOVPRESS_CONVERTER_SPEC", ""),
                "converter_allow_local_fallback": os.environ.get(
                    "GOVPRESS_CONVERTER_ALLOW_LOCAL_FALLBACK",
                    "",
                ),
                "converter_min_version": os.environ.get("GOVPRESS_CONVERTER_MIN_VERSION", ""),
            }

        module_path = Path(getattr(govpress_converter, "__file__", "")).resolve()
        version = getattr(govpress_converter, "__version__", "0.0.0")
        try:
            dist_version = metadata.version("govpress-converter")
            if dist_version:
                version = dist_version
        except metadata.PackageNotFoundError:
            dist_version = None

        return {
            "available": True,
            "version": version,
            "distribution_version": dist_version,
            "module_path": str(module_path),
            "private_engine": "packages/govpress-converter" not in module_path.as_posix(),
            "python_version": platform.python_version(),
            "platform": platform.platform(),
            "convert_hwpx_signature": str(inspect.signature(govpress_converter.convert_hwpx)),
            "convert_pdf_signature": str(inspect.signature(govpress_converter.convert_pdf)),
            "converter_spec": os.environ.get("GOVPRESS_CONVERTER_SPEC", ""),
            "converter_allow_local_fallback": os.environ.get(
                "GOVPRESS_CONVERTER_ALLOW_LOCAL_FALLBACK",
                "",
            ),
            "converter_min_version": os.environ.get("GOVPRESS_CONVERTER_MIN_VERSION", ""),
        }

    return router
