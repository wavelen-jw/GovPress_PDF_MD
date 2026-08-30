from __future__ import annotations

import importlib.util
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).parents[1]
ASSEMBLER_PATH = REPOSITORY_ROOT / "deploy" / "cloudflare" / "assemble_pages_artifact.py"


def _load_assembler():
    spec = importlib.util.spec_from_file_location("assemble_pages_artifact", ASSEMBLER_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


assembler = _load_assembler()


def _write(path: Path, content: str = "fixture") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _fixture(root: Path) -> None:
    _write(
        root / "mobile/dist/index.html",
        '<head><title>읽힘 — 정부문서를 사람도 AI도 읽게 한다</title></head>\n<body></body>',
    )
    _write(root / "mobile/dist/_expo/bundle.js", "bundle")
    _write(root / "mobile/dist/metadata.json", "{}")
    _write(root / "mobile/dist/manifest.webmanifest", "{}")
    _write(root / "mobile/dist/sw.js", "worker")
    _write(root / "mobile/dist/icons/icon.png", "icon")
    _write(root / "ui/landing.html", "<body>landing</body>")
    _write(root / "ui/assets/social-preview.png", "image")
    for source_name, _ in assembler.STATIC_PAGES:
        content = "<body>page</body>" if source_name.endswith(".html") else "data"
        _write(root / source_name, content)
    for source_name, _ in assembler.COMPARISON_DOWNLOADS:
        _write(root / source_name, "download")


def test_assemble_pages_artifact_matches_site_layout(tmp_path: Path) -> None:
    source = tmp_path / "source"
    destination = tmp_path / "artifact"
    _fixture(source)

    count, total, largest, largest_size = assembler.assemble(source, destination)

    assert count > 10
    assert total > 0
    assert largest.is_file()
    assert largest_size > 0
    assert (destination / "index.html").is_file()
    assert (destination / "app/index.html").is_file()
    assert (destination / "app/_expo/bundle.js").is_file()
    assert not (destination / "_expo").exists()
    assert (destination / "comparison-goilyuga/downloads/156754095.hwpx").is_file()
    assert "static.cloudflareinsights.com" in (destination / "index.html").read_text()
    assert 'property="og:title"' in (destination / "app/index.html").read_text()
    assert "immutable" in (destination / "_headers").read_text()


def test_validate_rejects_oversized_file(tmp_path: Path) -> None:
    root = tmp_path / "artifact"
    _write(root / "index.html")
    _write(root / "app/index.html")
    _write(root / "app/_expo/bundle.js")
    _write(root / "large.bin")

    original = assembler.MAX_FILE_BYTES
    assembler.MAX_FILE_BYTES = 0
    try:
        try:
            assembler.validate_artifact(root)
        except RuntimeError as error:
            assert "25 MiB" in str(error)
        else:
            raise AssertionError("oversized file was accepted")
    finally:
        assembler.MAX_FILE_BYTES = original
