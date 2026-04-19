#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path


TAG_PATTERN = re.compile(r"(?P<prefix>\.git@)(?P<tag>[^#\s]+)$")


def load_version(version_file: Path) -> str:
    value = version_file.read_text(encoding="utf-8").strip()
    if not value:
        raise SystemExit(f"converter version file is empty: {version_file}")
    return value


def normalize_spec(spec: str, version: str) -> str:
    raw = spec.strip()
    if not raw:
        return ""
    match = TAG_PATTERN.search(raw)
    if not match:
        return raw
    return f"{raw[:match.start('tag')]}{version}"


def main() -> None:
    parser = argparse.ArgumentParser(description="Normalize GovPress converter spec to tracked version.")
    parser.add_argument("--spec", required=True, help="Raw GOVPRESS_CONVERTER_SPEC value")
    parser.add_argument(
        "--version-file",
        required=True,
        help="Path to deploy/converter.version",
    )
    args = parser.parse_args()
    version = load_version(Path(args.version_file))
    print(normalize_spec(args.spec, version))


if __name__ == "__main__":
    main()
