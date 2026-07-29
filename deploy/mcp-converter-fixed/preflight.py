#!/usr/bin/env python3
"""Fail closed unless every HWPX converter version interface agrees."""

from __future__ import annotations

from importlib import metadata
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys


CLI_VERSION_RE = re.compile(r"^govpress-hwpx-md\s+(\S+)$")


def normalize_version(value: str) -> str:
    normalized = value.strip()
    return normalized[1:] if normalized.startswith("v") else normalized


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def inspect_runtime(expected: str) -> dict[str, str]:
    runtime_python = Path(
        os.environ.get(
            "GOVPRESS_HWPX_MD_PYTHON",
            "/opt/govpress-hwpx-md-venv/bin/python",
        )
    )
    expected_python = runtime_python.resolve()
    actual_python = Path(sys.executable)
    if actual_python.resolve() != expected_python:
        raise SystemExit(
            f"converter preflight failed: Python is {actual_python}, expected {expected_python}"
        )
    expected_prefix = runtime_python.parent.parent.resolve()
    actual_prefix = Path(sys.prefix).resolve()
    if actual_prefix != expected_prefix:
        raise SystemExit(
            f"converter preflight failed: Python prefix is {actual_prefix}, "
            f"expected {expected_prefix}"
        )

    wheel = Path(os.environ.get("GOVPRESS_HWPX_MD_WHEEL", ""))
    expected_wheel_sha256 = os.environ.get("GOVPRESS_HWPX_MD_WHEEL_SHA256", "")
    if not wheel.is_file() or not re.fullmatch(r"[0-9a-f]{64}", expected_wheel_sha256):
        raise SystemExit("converter preflight failed: immutable wheel contract is missing")
    wheel_sha256 = sha256_file(wheel)
    if wheel_sha256 != expected_wheel_sha256:
        raise SystemExit(
            f"converter preflight failed: wheel SHA-256={wheel_sha256}, "
            f"expected={expected_wheel_sha256}"
        )

    import govpress_converter

    distribution_version = normalize_version(metadata.version("govpress-converter"))
    module_version = normalize_version(str(govpress_converter.__version__))
    cli = runtime_python.with_name("govpress-hwpx-md")
    cli_output = subprocess.run(
        [str(cli), "--version"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    match = CLI_VERSION_RE.fullmatch(cli_output)
    if not match:
        raise SystemExit(f"converter preflight failed: unexpected CLI output: {cli_output!r}")
    cli_version = normalize_version(match.group(1))
    normalized_expected = normalize_version(expected)

    versions = {
        "expected_version": normalized_expected,
        "distribution_version": distribution_version,
        "module_version": module_version,
        "cli_version": cli_version,
        "python": str(actual_python),
        "python_prefix": str(actual_prefix),
        "wheel_sha256": wheel_sha256,
    }
    mismatched = {
        name: value
        for name, value in versions.items()
        if name.endswith("_version") and value != normalized_expected
    }
    if mismatched:
        raise SystemExit(
            "converter preflight failed: "
            + ", ".join(f"{name}={value}" for name, value in sorted(mismatched.items()))
            + f", expected={normalized_expected}"
        )
    return versions


def main() -> int:
    expected = os.environ.get("GOVPRESS_HWPX_MD_EXPECTED_VERSION", "").strip()
    if not expected:
        raise SystemExit("converter preflight failed: expected version is not set")
    versions = inspect_runtime(expected)
    print(json.dumps(versions, sort_keys=True))
    if sys.argv[1:] == ["--check-only"]:
        return 0
    if len(sys.argv) == 1:
        raise SystemExit("converter preflight passed but no command was provided")
    os.execvpe(sys.argv[1], sys.argv[1:], os.environ)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
