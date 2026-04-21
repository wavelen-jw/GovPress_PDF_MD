#!/usr/bin/env python3
from __future__ import annotations

import argparse
import inspect
import json
import os
from pathlib import Path
import sys


def _parse_version(raw: str) -> tuple[int, ...]:
    parts: list[int] = []
    for token in raw.replace("-", ".").split("."):
        if token.isdigit():
            parts.append(int(token))
        else:
            break
    return tuple(parts)


def _version_lt(left: str, right: str) -> bool:
    return _parse_version(left) < _parse_version(right)


def _normalize_version(raw: str | None) -> str:
    value = (raw or "").strip()
    if value.startswith("v"):
        return value[1:]
    return value


def _is_site_installed(module_path: Path) -> bool:
    return any(part in {"site-packages", "dist-packages"} for part in module_path.parts)


def _classify_backend(module_path: Path, distribution_version: str | None) -> str:
    path = module_path.as_posix()
    if _is_site_installed(module_path) and distribution_version:
        return "package"
    if "gov-md-converter" in path:
        return "local-root"
    if "packages/govpress-converter" in path:
        return "bundled-root"
    if distribution_version:
        return "package"
    return "unknown"


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify installed govpress_converter runtime contract")
    parser.add_argument("--min-version", help="Fail if the installed package version is older than this")
    parser.add_argument("--expected-version", help="Fail unless the installed package version exactly matches this version")
    parser.add_argument("--require-private-engine", action="store_true", help="Fail unless a private engine package is installed")
    parser.add_argument("--require-package-backend", action="store_true", help="Fail unless the runtime imports from an installed package backend")
    args = parser.parse_args()

    try:
        from importlib import metadata
        import govpress_converter
    except Exception as exc:
        if args.require_private_engine:
            raise SystemExit(f"govpress_converter import failed: {exc}") from exc
        print(json.dumps({"available": False, "reason": str(exc)}, ensure_ascii=False))
        return 0

    module_path = Path(getattr(govpress_converter, "__file__", "")).resolve()
    version = _normalize_version(getattr(govpress_converter, "__version__", "0.0.0"))
    dist_version = None
    try:
        dist_version = _normalize_version(metadata.version("govpress-converter"))
        if dist_version:
            version = dist_version
    except metadata.PackageNotFoundError:
        pass

    hwpx_signature = str(inspect.signature(govpress_converter.convert_hwpx))
    pdf_signature = str(inspect.signature(govpress_converter.convert_pdf))
    backend = _classify_backend(module_path, dist_version)
    is_private_engine = backend != "bundled-root"

    if args.require_private_engine and not is_private_engine:
        raise SystemExit(
            f"Expected private govpress_converter package, but imported contract stub at {module_path}"
        )
    if args.require_package_backend and backend != "package":
        raise SystemExit(
            f"Expected installed package backend, but runtime backend was {backend} at {module_path}"
        )
    if args.min_version and _version_lt(version, args.min_version):
        raise SystemExit(f"Installed govpress_converter version {version} is older than required {args.min_version}")
    if args.expected_version and _normalize_version(version) != _normalize_version(args.expected_version):
        raise SystemExit(
            f"Installed govpress_converter version {version} does not match expected {_normalize_version(args.expected_version)}"
        )

    payload = {
        "available": True,
        "version": version,
        "distribution_version": dist_version,
        "module_path": str(module_path),
        "backend": backend,
        "private_engine": is_private_engine,
        "convert_hwpx_signature": hwpx_signature,
        "convert_pdf_signature": pdf_signature,
        "converter_spec": os.environ.get("GOVPRESS_CONVERTER_SPEC", ""),
        "converter_allow_local_fallback": os.environ.get("GOVPRESS_CONVERTER_ALLOW_LOCAL_FALLBACK", ""),
        "converter_min_version": os.environ.get("GOVPRESS_CONVERTER_MIN_VERSION", ""),
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
