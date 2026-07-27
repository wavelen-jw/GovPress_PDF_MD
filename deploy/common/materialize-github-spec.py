#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import re
import tarfile
import tempfile
import urllib.parse
import urllib.request
from pathlib import Path


SPEC_PATTERN = re.compile(r"^(?P<url>git\+https://.+\.git)@(?P<ref>[^#\s]+)$")


def parse_spec(spec: str) -> tuple[str, str, str | None]:
    match = SPEC_PATTERN.fullmatch(spec.strip())
    if not match:
        raise SystemExit("unsupported GitHub converter spec")

    parsed = urllib.parse.urlsplit(match.group("url").removeprefix("git+"))
    if parsed.hostname != "github.com":
        raise SystemExit("converter spec is not hosted on github.com")

    repository = parsed.path.strip("/").removesuffix(".git")
    if repository.count("/") != 1:
        raise SystemExit("converter spec repository path is invalid")

    token = parsed.password or parsed.username
    if token in {None, "", "git", "x-access-token"}:
        token = None
    elif parsed.password:
        token = urllib.parse.unquote(parsed.password)
    else:
        token = urllib.parse.unquote(token)
    return repository, match.group("ref"), token


def download_archive(spec: str, output: Path) -> None:
    repository, ref, token = parse_spec(spec)
    encoded_repository = "/".join(urllib.parse.quote(part, safe="") for part in repository.split("/"))
    encoded_ref = urllib.parse.quote(ref, safe="")
    url = f"https://api.github.com/repos/{encoded_repository}/tarball/{encoded_ref}"
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "govpress-offline-deploy",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    output.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(prefix=f".{output.name}.", dir=output.parent)
    os.close(fd)
    temporary = Path(temporary_name)
    try:
        request = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(request, timeout=120) as response, temporary.open("wb") as target:
            while chunk := response.read(1024 * 1024):
                target.write(chunk)
        with tarfile.open(temporary, mode="r:gz") as archive:
            names = archive.getnames()
            if not names or not any(
                name.endswith(("/pyproject.toml", "/setup.py", "/setup.cfg")) for name in names
            ):
                raise SystemExit("downloaded archive does not contain a Python project")
        temporary.replace(output)
    finally:
        temporary.unlink(missing_ok=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Download a GitHub git spec through the API.")
    parser.add_argument("--spec", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    download_archive(args.spec, args.output)
    print(args.output)


if __name__ == "__main__":
    main()
