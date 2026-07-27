#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
import tarfile
import tempfile
from pathlib import Path


PRESERVED_TOP_LEVEL = {".git", "exports"}


def sync_archive(archive_path: Path, destination: Path) -> None:
    with tempfile.TemporaryDirectory(prefix="govpress-source-") as temporary_name:
        temporary = Path(temporary_name)
        with tarfile.open(archive_path, mode="r:gz") as archive:
            archive.extractall(temporary, filter="data")
        roots = [path for path in temporary.iterdir() if path.is_dir()]
        if len(roots) != 1:
            raise SystemExit("source archive must contain one root directory")
        source = roots[0]

        destination.mkdir(parents=True, exist_ok=True)
        for existing in destination.iterdir():
            if existing.name in PRESERVED_TOP_LEVEL:
                continue
            if existing.is_dir() and not existing.is_symlink():
                shutil.rmtree(existing)
            else:
                existing.unlink()
        for entry in source.iterdir():
            target = destination / entry.name
            if entry.is_dir() and not entry.is_symlink():
                shutil.copytree(entry, target, dirs_exist_ok=True)
            else:
                shutil.copy2(entry, target, follow_symlinks=False)


def main() -> None:
    parser = argparse.ArgumentParser(description="Synchronize a GitHub source archive.")
    parser.add_argument("--archive", required=True, type=Path)
    parser.add_argument("--destination", required=True, type=Path)
    args = parser.parse_args()
    sync_archive(args.archive, args.destination)


if __name__ == "__main__":
    main()
