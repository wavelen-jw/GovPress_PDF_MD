#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import tarfile
import tempfile
import urllib.request


DEFAULT_VERSION = "0.8.4"
DEFAULT_SHA256 = "d2f015447147a840b3a587e8e9bedd75973fb2e0a60eac37b08cad9e34cdac54"


def _headers(*, accept: str) -> dict[str, str]:
    headers = {
        "Accept": accept,
        "User-Agent": "govpress-offline-deploy",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _release_asset(version: str) -> tuple[int, str]:
    tag = version if version.startswith("v") else f"v{version}"
    request = urllib.request.Request(
        f"https://api.github.com/repos/edwardkim/rhwp/releases/tags/{tag}",
        headers=_headers(accept="application/vnd.github+json"),
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        payload = json.load(response)
    expected_name = f"rhwp-{tag}-linux-x86_64.tar.gz"
    for asset in payload.get("assets", []):
        if asset.get("name") == expected_name:
            return int(asset["id"]), expected_name
    raise SystemExit(f"RHWP release asset not found: {expected_name}")


def _validate_archive(path: Path) -> None:
    with tarfile.open(path, mode="r:gz") as archive:
        names = set(archive.getnames())
    if "rhwp/rhwp" not in names:
        raise SystemExit("RHWP archive does not contain rhwp/rhwp")


def _verify_checksum(path: Path, expected: str) -> None:
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual != expected.lower():
        raise SystemExit(f"RHWP checksum mismatch: expected {expected}, got {actual}")


def download_release(version: str, sha256: str, output: Path) -> None:
    asset_id, _ = _release_asset(version)
    request = urllib.request.Request(
        f"https://api.github.com/repos/edwardkim/rhwp/releases/assets/{asset_id}",
        headers=_headers(accept="application/octet-stream"),
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(prefix=f".{output.name}.", dir=output.parent)
    os.close(fd)
    temporary = Path(temporary_name)
    try:
        with urllib.request.urlopen(request, timeout=120) as response, temporary.open("wb") as target:
            while chunk := response.read(1024 * 1024):
                target.write(chunk)
        _verify_checksum(temporary, sha256)
        _validate_archive(temporary)
        temporary.replace(output)
    finally:
        temporary.unlink(missing_ok=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Download a pinned RHWP Linux release through GitHub API.")
    parser.add_argument("--version", default=DEFAULT_VERSION)
    parser.add_argument("--sha256", default=DEFAULT_SHA256)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    download_release(args.version, args.sha256, args.output)
    print(args.output)


if __name__ == "__main__":
    main()
