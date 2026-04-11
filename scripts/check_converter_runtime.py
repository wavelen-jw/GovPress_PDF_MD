#!/usr/bin/env python3
from __future__ import annotations

import argparse
import inspect
import json
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


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify installed govpress_converter runtime contract")
    parser.add_argument("--min-version", help="Fail if the installed package version is older than this")
    parser.add_argument("--require-private-engine", action="store_true", help="Fail unless a private engine package is installed")
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
    version = getattr(govpress_converter, "__version__", "0.0.0")
    try:
        dist_version = metadata.version("govpress-converter")
        if dist_version:
            version = dist_version
    except metadata.PackageNotFoundError:
        pass

    hwpx_signature = str(inspect.signature(govpress_converter.convert_hwpx))
    pdf_signature = str(inspect.signature(govpress_converter.convert_pdf))
    is_private_engine = "packages/govpress-converter" not in module_path.as_posix()

    if args.require_private_engine and not is_private_engine:
        raise SystemExit(
            f"Expected private govpress_converter package, but imported contract stub at {module_path}"
        )
    if args.min_version and _version_lt(version, args.min_version):
        raise SystemExit(f"Installed govpress_converter version {version} is older than required {args.min_version}")

    payload = {
        "available": True,
        "version": version,
        "module_path": str(module_path),
        "private_engine": is_private_engine,
        "convert_hwpx_signature": hwpx_signature,
        "convert_pdf_signature": pdf_signature,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
