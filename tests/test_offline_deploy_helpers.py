from __future__ import annotations

import importlib.util
import io
import hashlib
import tarfile
from pathlib import Path


def _load_helper(name: str, filename: str):
    path = Path(__file__).parents[1] / "deploy" / "common" / filename
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


materialize = _load_helper("materialize_github_spec", "materialize-github-spec.py")
materialize_rhwp = _load_helper("materialize_rhwp_release", "materialize-rhwp-release.py")
sync_source = _load_helper("sync_source_archive", "sync-source-archive.py")


def test_parse_github_spec_with_token_and_ref() -> None:
    repository, ref, token = materialize.parse_spec(
        "git+https://x-access-token:secret-value@github.com/wavelen-jw/converter.git@v1.2.3"
    )

    assert repository == "wavelen-jw/converter"
    assert ref == "v1.2.3"
    assert token == "secret-value"


def test_sync_archive_preserves_runtime_exports(tmp_path: Path) -> None:
    source_archive = tmp_path / "source.tar.gz"
    destination = tmp_path / "checkout"
    (destination / ".git").mkdir(parents=True)
    (destination / ".git" / "HEAD").write_text("ref: refs/heads/main\n")
    (destination / "exports").mkdir()
    (destination / "exports" / "result.json").write_text("{}")
    (destination / "stale.py").write_text("stale")

    with tarfile.open(source_archive, "w:gz") as archive:
        for relative, content in {
            "repository-main/pyproject.toml": "[project]\nname='converter'\n",
            "repository-main/package/__init__.py": "",
        }.items():
            payload = content.encode()
            info = tarfile.TarInfo(relative)
            info.size = len(payload)
            archive.addfile(info, io.BytesIO(payload))

    sync_source.sync_archive(source_archive, destination)

    assert (destination / ".git" / "HEAD").exists()
    assert (destination / "exports" / "result.json").exists()
    assert not (destination / "stale.py").exists()
    assert (destination / "package" / "__init__.py").exists()



def test_rhwp_release_archive_validation_and_checksum(tmp_path: Path) -> None:
    archive_path = tmp_path / "rhwp.tar.gz"
    with tarfile.open(archive_path, "w:gz") as archive:
        payload = b"binary"
        info = tarfile.TarInfo("rhwp/rhwp")
        info.size = len(payload)
        archive.addfile(info, io.BytesIO(payload))

    checksum = hashlib.sha256(archive_path.read_bytes()).hexdigest()
    materialize_rhwp._verify_checksum(archive_path, checksum)
    materialize_rhwp._validate_archive(archive_path)
