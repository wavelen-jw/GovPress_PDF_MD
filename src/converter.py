from __future__ import annotations

from dataclasses import dataclass
import importlib
from pathlib import Path
import os
import re
import shutil
import subprocess
import sys
import tempfile
import shutil as shutil_lib

from .json_extractor import extract_text_from_json
from .markdown_postprocessor import postprocess_markdown


class DependencyError(RuntimeError):
    """Raised when runtime dependencies are not available."""


class ConversionError(RuntimeError):
    """Raised when PDF conversion fails."""


@dataclass
class DependencyStatus:
    java_ok: bool
    opendataloader_ok: bool
    java_detail: str
    opendataloader_detail: str
    java_version: int | None = None
    java_command: str | None = None

    @property
    def is_ready(self) -> bool:
        return self.java_ok and self.opendataloader_ok


def _check_command(command: list[str]) -> tuple[bool, str]:
    try:
        result = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except FileNotFoundError:
        return False, "명령을 찾을 수 없습니다."
    except OSError as exc:
        return False, str(exc)

    detail = (result.stderr or result.stdout).strip() or f"return code={result.returncode}"
    return result.returncode == 0, detail


def _application_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def _resolve_java_command() -> str | None:
    bundled_candidates = [
        _application_root() / "runtime" / "java" / "bin" / "java.exe",
        _application_root() / "runtime" / "java" / "bin" / "java",
        _application_root() / "java" / "bin" / "java.exe",
        _application_root() / "java" / "bin" / "java",
    ]
    for candidate in bundled_candidates:
        if candidate.exists():
            return str(candidate)

    direct = shutil_lib.which("java")
    if direct:
        return direct
    return None


def _load_opendataloader_convert():
    module = importlib.import_module("opendataloader_pdf")
    return module.convert


def _parse_java_major_version(version_output: str) -> int | None:
    match = re.search(r'version "(?P<version>\d+(?:\.\d+)*)', version_output)
    if not match:
        return None

    raw_version = match.group("version")
    if raw_version.startswith("1."):
        parts = raw_version.split(".")
        return int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else None

    major = raw_version.split(".", 1)[0]
    return int(major) if major.isdigit() else None


def _runtime_environment(java_command: str | None = None) -> dict[str, str]:
    env = dict(**shutil_lib.os.environ)
    if java_command:
        java_bin = str(Path(java_command).resolve().parent)
        env["PATH"] = java_bin + shutil_lib.os.pathsep + env.get("PATH", "")
        env["JAVA_HOME"] = str(Path(java_command).resolve().parent.parent)
    return env


class _RuntimeEnvironmentContext:
    def __init__(self, java_command: str | None) -> None:
        self._java_command = java_command
        self._original: dict[str, str | None] = {}

    def __enter__(self) -> None:
        updates = _runtime_environment(self._java_command)
        for key, value in updates.items():
            self._original.setdefault(key, os.environ.get(key))
            os.environ[key] = value

    def __exit__(self, exc_type, exc, tb) -> None:
        for key, original_value in self._original.items():
            if original_value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = original_value


def check_runtime_dependencies() -> DependencyStatus:
    """Check whether the required local runtime dependencies are installed."""
    java_command = _resolve_java_command()
    if java_command:
        java_ok, java_detail = _check_command([java_command, "-version"])
    else:
        java_ok, java_detail = False, "명령을 찾을 수 없습니다."
    try:
        convert = _load_opendataloader_convert()
        odl_ok = callable(convert)
        odl_detail = "Python module loaded"
    except ModuleNotFoundError:
        odl_ok, odl_detail = False, "명령을 찾을 수 없습니다."
    except Exception as exc:
        odl_ok, odl_detail = False, str(exc)
    java_version = _parse_java_major_version(java_detail) if java_ok else None
    java_ok = java_ok and java_version is not None and java_version >= 11
    if java_version is not None and java_version < 11:
        java_detail = f"지원되지 않는 Java 버전입니다: {java_version}. Java 11+가 필요합니다."
    return DependencyStatus(
        java_ok=java_ok,
        opendataloader_ok=odl_ok,
        java_detail=java_detail,
        opendataloader_detail=odl_detail,
        java_version=java_version,
        java_command=java_command,
    )


def _find_markdown_file(output_dir: Path, source_path: Path) -> Path:
    candidates = sorted(output_dir.rglob("*.md"))
    if not candidates:
        raise ConversionError("변환 결과에서 Markdown 파일을 찾지 못했습니다.")

    exact_matches = [path for path in candidates if path.stem == source_path.stem]
    if exact_matches:
        return exact_matches[0]

    prefixed_matches = [path for path in candidates if source_path.stem in path.stem]
    if prefixed_matches:
        return prefixed_matches[0]

    return candidates[0]


def _find_json_file(output_dir: Path, source_path: Path) -> Path:
    candidates = sorted(output_dir.rglob("*.json"))
    if not candidates:
        raise ConversionError("변환 결과에서 JSON 파일을 찾지 못했습니다.")

    exact_matches = [path for path in candidates if path.stem == source_path.stem]
    if exact_matches:
        return exact_matches[0]

    prefixed_matches = [path for path in candidates if source_path.stem in path.stem]
    if prefixed_matches:
        return prefixed_matches[0]

    return candidates[0]


def convert_pdf_to_markdown(
    pdf_path: str | Path,
    timeout_seconds: int = 180,
    keep_temp_dir: bool = False,
) -> str:
    """Convert a PDF into normalized markdown text."""
    source_path = Path(pdf_path)
    if not source_path.exists():
        raise FileNotFoundError(f"PDF 파일을 찾을 수 없습니다: {source_path}")
    if source_path.suffix.lower() != ".pdf":
        raise ValueError("PDF 파일만 변환할 수 있습니다.")

    status = check_runtime_dependencies()
    if not status.is_ready:
        raise DependencyError(
            "PDF 변환에 필요한 Java 11+ 또는 opendataloader-pdf가 준비되지 않았습니다.\n"
            f"java={status.java_detail}\n"
            f"opendataloader={status.opendataloader_detail}"
        )

    temp_root = Path(tempfile.mkdtemp(prefix="pdf_to_md_"))
    try:
        convert = _load_opendataloader_convert()
        try:
            with _RuntimeEnvironmentContext(status.java_command):
                convert(
                    input_path=[str(source_path)],
                    output_dir=str(temp_root),
                    format="markdown,json",
                    quiet=True,
                )
        except Exception as exc:
            raise ConversionError(
                "PDF 변환에 실패했습니다.\n"
                f"source={source_path}\n"
                f"temp_dir={temp_root}\n"
                f"error={exc}"
            ) from exc

        try:
            json_path = _find_json_file(temp_root, source_path)
            raw_text = extract_text_from_json(json_path)
        except ConversionError:
            markdown_path = _find_markdown_file(temp_root, source_path)
            raw_text = markdown_path.read_text(encoding="utf-8", errors="replace")

        return postprocess_markdown(raw_text)
    finally:
        if not keep_temp_dir:
            shutil.rmtree(temp_root, ignore_errors=True)
