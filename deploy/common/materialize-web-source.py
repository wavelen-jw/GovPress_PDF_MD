#!/usr/bin/env python3
"""Resolve and materialize an exact GovPress web source revision from GitHub."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import shutil
import tarfile
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request


DEFAULT_REPOSITORY = "wavelen-jw/GovPress_PDF_MD"
REPOSITORY_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
SHA_PATTERN = re.compile(r"^[0-9a-f]{40}$")
REQUIRED_PATHS = ("mobile/package.json", "mobile/package-lock.json", "ui/landing.html")


def _headers() -> dict[str, str]:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "govpress-serverw-web-deploy",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _validate_repository(repository: str) -> str:
    if not REPOSITORY_PATTERN.fullmatch(repository):
        raise ValueError(f"invalid GitHub repository: {repository}")
    return repository


def _open(request: urllib.request.Request, *, timeout: int):
    last_error: Exception | None = None
    for attempt in range(3):
        try:
            return urllib.request.urlopen(request, timeout=timeout)
        except (OSError, urllib.error.URLError) as exc:
            last_error = exc
            if attempt < 2:
                time.sleep(2**attempt)
    assert last_error is not None
    raise last_error


def resolve_commit(repository: str, ref: str) -> str:
    repository = _validate_repository(repository)
    encoded_repository = "/".join(urllib.parse.quote(part, safe="") for part in repository.split("/"))
    encoded_ref = urllib.parse.quote(ref, safe="")
    request = urllib.request.Request(
        f"https://api.github.com/repos/{encoded_repository}/commits/{encoded_ref}",
        headers=_headers(),
    )
    with _open(request, timeout=30) as response:
        payload = json.load(response)
    sha = str(payload.get("sha", "")).lower()
    if not SHA_PATTERN.fullmatch(sha):
        raise RuntimeError("GitHub did not return a valid commit SHA")
    return sha


def _download_archive(repository: str, sha: str, output: Path) -> None:
    encoded_repository = "/".join(urllib.parse.quote(part, safe="") for part in repository.split("/"))
    request = urllib.request.Request(
        f"https://api.github.com/repos/{encoded_repository}/tarball/{sha}",
        headers=_headers(),
    )
    with _open(request, timeout=120) as response, output.open("wb") as target:
        while chunk := response.read(1024 * 1024):
            target.write(chunk)


def materialize_source(repository: str, sha: str, destination: Path) -> None:
    repository = _validate_repository(repository)
    if not SHA_PATTERN.fullmatch(sha):
        raise ValueError(f"invalid commit SHA: {sha}")
    if destination.exists() and any(destination.iterdir()):
        raise RuntimeError(f"destination is not empty: {destination}")
    destination.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="govpress-web-source-", dir=destination.parent) as temporary_name:
        temporary = Path(temporary_name)
        archive_path = temporary / "source.tar.gz"
        extracted = temporary / "extracted"
        extracted.mkdir()
        _download_archive(repository, sha, archive_path)
        with tarfile.open(archive_path, mode="r:gz") as archive:
            archive.extractall(extracted, filter="data")
        roots = [path for path in extracted.iterdir() if path.is_dir()]
        if len(roots) != 1:
            raise RuntimeError("GitHub source archive must contain one root directory")
        source_root = roots[0]
        missing = [relative for relative in REQUIRED_PATHS if not (source_root / relative).is_file()]
        if missing:
            raise RuntimeError(f"GitHub source archive is missing: {', '.join(missing)}")
        for entry in source_root.iterdir():
            shutil.move(str(entry), destination / entry.name)
    (destination / ".govpress-source-sha").write_text(f"{sha}\n", encoding="ascii")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", default=DEFAULT_REPOSITORY)
    parser.add_argument("--ref", default="web")
    parser.add_argument("--destination", type=Path)
    parser.add_argument("--resolve-only", action="store_true")
    args = parser.parse_args()

    sha = resolve_commit(args.repository, args.ref)
    if args.resolve_only:
        print(sha)
        return
    if args.destination is None:
        parser.error("--destination is required unless --resolve-only is used")
    materialize_source(args.repository, sha, args.destination)
    print(sha)


if __name__ == "__main__":
    main()
