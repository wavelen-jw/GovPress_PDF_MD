from __future__ import annotations

import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import tarfile
from unittest import mock


REPOSITORY_ROOT = Path(__file__).parents[1]
DEPLOY_SCRIPT = REPOSITORY_ROOT / "deploy" / "wsl" / "bin" / "deploy_web_direct.sh"
MATERIALIZER_PATH = REPOSITORY_ROOT / "deploy" / "common" / "materialize-web-source.py"


def _load_materializer():
    spec = importlib.util.spec_from_file_location("materialize_web_source", MATERIALIZER_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


materializer = _load_materializer()


class _FakeResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        self.close()


def _write_asset_tree(root: Path, marker: str) -> None:
    (root / "ui").mkdir(parents=True, exist_ok=True)
    (root / "mobile" / "dist" / "_expo").mkdir(parents=True, exist_ok=True)
    (root / "ui" / "landing.html").write_text(f"<html>{marker}-landing</html>\n", encoding="utf-8")
    (root / "mobile" / "dist" / "index.html").write_text(
        f'<html><div id="root">{marker}-app</div></html>\n',
        encoding="utf-8",
    )
    (root / "mobile" / "dist" / "_expo" / "bundle.js").write_text(marker, encoding="utf-8")


def _write_source(root: Path, marker: str) -> None:
    _write_asset_tree(root, marker)
    (root / "mobile" / "package.json").write_text('{"name":"fixture"}\n', encoding="utf-8")
    (root / "mobile" / "package-lock.json").write_text(
        '{"name":"fixture","lockfileVersion":3,"packages":{}}\n',
        encoding="utf-8",
    )


def _run_deployer(source: Path, serve: Path, state: Path, sha: str, *arguments: str, local_url: str = ""):
    env = {
        **os.environ,
        "GOVPRESS_WEB_SOURCE_DIR": str(source),
        "GOVPRESS_WEB_EXPECT_SHA": sha,
        "GOVPRESS_WEB_SERVE_ROOT": str(serve),
        "GOVPRESS_WEB_STATE_ROOT": str(state),
        "GOVPRESS_WEB_HELPER": str(MATERIALIZER_PATH),
        "GOVPRESS_WEB_SKIP_BUILD": "1",
        "GOVPRESS_WEB_LOCAL_URL": local_url,
        "GOVPRESS_WEB_PUBLIC_URL": "",
    }
    return subprocess.run(
        [str(DEPLOY_SCRIPT), *(arguments or ("deploy", "web"))],
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )


def test_resolve_commit_uses_exact_github_sha() -> None:
    sha = "a" * 40
    payload = _FakeResponse(json.dumps({"sha": sha}).encode())
    with mock.patch.object(materializer.urllib.request, "urlopen", return_value=payload) as urlopen:
        assert materializer.resolve_commit("wavelen-jw/GovPress_PDF_MD", "web") == sha

    request = urlopen.call_args.args[0]
    assert request.full_url.endswith("/repos/wavelen-jw/GovPress_PDF_MD/commits/web")


def test_materialize_source_requires_expected_web_files(tmp_path: Path) -> None:
    sha = "b" * 40
    archive_path = tmp_path / "fixture.tar.gz"
    with tarfile.open(archive_path, "w:gz") as archive:
        for relative, content in {
            "repo/mobile/package.json": "{}\n",
            "repo/mobile/package-lock.json": "{}\n",
            "repo/ui/landing.html": "<html></html>\n",
        }.items():
            payload = content.encode()
            info = tarfile.TarInfo(relative)
            info.size = len(payload)
            archive.addfile(info, io.BytesIO(payload))

    def copy_archive(repository: str, resolved_sha: str, output: Path) -> None:
        assert repository == "wavelen-jw/GovPress_PDF_MD"
        assert resolved_sha == sha
        output.write_bytes(archive_path.read_bytes())

    destination = tmp_path / "source"
    with mock.patch.object(materializer, "_download_archive", side_effect=copy_archive):
        materializer.materialize_source("wavelen-jw/GovPress_PDF_MD", sha, destination)

    assert (destination / ".govpress-source-sha").read_text().strip() == sha
    assert (destination / "ui" / "landing.html").is_file()


def test_direct_deploy_activates_rolls_back_and_restores_on_failed_smoke(tmp_path: Path) -> None:
    serve = tmp_path / "serve"
    state = tmp_path / "state"
    source = tmp_path / "source"
    _write_asset_tree(serve, "old")
    _write_source(source, "first")

    first_sha = "1" * 40
    first = _run_deployer(source, serve, state, first_sha)
    assert first.returncode == 0, first.stderr
    assert "deploy_status=success" in first.stdout
    assert "first-landing" in (serve / "ui" / "landing.html").read_text()
    assert (state / "current.sha").read_text().strip() == first_sha

    _write_source(source, "second")
    second_sha = "2" * 40
    second = _run_deployer(source, serve, state, second_sha)
    assert second.returncode == 0, second.stderr
    assert "second-landing" in (serve / "ui" / "landing.html").read_text()

    rolled_back = _run_deployer(source, serve, state, second_sha, "rollback")
    assert rolled_back.returncode == 0, rolled_back.stderr
    assert "first-landing" in (serve / "ui" / "landing.html").read_text()
    assert (state / "current.sha").read_text().strip() == first_sha

    _write_source(source, "third")
    failed = _run_deployer(
        source,
        serve,
        state,
        "3" * 40,
        local_url="http://127.0.0.1:9",
    )
    assert failed.returncode != 0
    assert "previous release restored" in failed.stderr
    assert "first-landing" in (serve / "ui" / "landing.html").read_text()
    assert (state / "current.sha").read_text().strip() == first_sha
