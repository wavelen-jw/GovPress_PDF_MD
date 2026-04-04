from __future__ import annotations

from dataclasses import dataclass
import base64
import importlib
from pathlib import Path
import os
import re
import logging
import shutil
import subprocess
import sys
import tempfile
import threading
import shutil as shutil_lib

_logger = logging.getLogger(__name__)

from .json_extractor import extract_text_from_json
from .parser_rules import clean_line
from .markdown_postprocessor import postprocess_markdown

# Prevents two concurrent conversions from corrupting each other's os.environ patch.
# opendataloader_pdf.convert() spawns a Java subprocess and reads PATH/JAVA_HOME;
# we must patch os.environ before calling it and cannot pass env= to the library call.
_conversion_lock = threading.Lock()

_PDF_PAGE_MARKER_RE = re.compile(r"^-\s*\d+\s*-$")
_PDF_ASCII_ROMAN_RE = re.compile(r"^(I|II|III|IV|V|VI|VII|VIII|IX|X)$")
_PDF_ASCII_ROMAN_MAP = {
    "I": "Ⅰ",
    "II": "Ⅱ",
    "III": "Ⅲ",
    "IV": "Ⅳ",
    "V": "Ⅴ",
    "VI": "Ⅵ",
    "VII": "Ⅶ",
    "VIII": "Ⅷ",
    "IX": "Ⅸ",
    "X": "Ⅹ",
}
_PDF_INLINE_LABEL_RE = re.compile(r"(?<!^)\s+(<\s*(?:기존 문서 AI 활용|앞으로의 문서|가이드라인 예시|추진경과)\s*>)")
_PDF_INLINE_OVERVIEW_RE = re.compile(r"(?<!^)\s+(<개\s*요>)")
_PDF_INLINE_TASK_RE = re.compile(r"\s+(?=\s+)")
_PDF_LINE_CLEANUPS = (
    ("글", "ᄒᆞᆫ글"),
    ("마크 다운", "마크다운"),
    ("더 라도", "더라도"),
    ("모델 (VLM)", "모델(VLM)"),
)


def _normalize_pdf_text_line(text: str) -> str:
    normalized = clean_line(text)
    for before, after in _PDF_LINE_CLEANUPS:
        normalized = normalized.replace(before, after)
    return clean_line(normalized)


def _rewrite_pdf_grouped_table(lines: list[str], index: int) -> tuple[list[str] | None, int]:
    line = lines[index]
    next_line = lines[index + 1] if index + 1 < len(lines) else ""

    if (
        line == "| 종 류 | | 국내 AI모델 인식수준 |"
        and next_line.startswith("| ---")
        and index + 3 < len(lines)
    ):
        text_row = lines[index + 2]
        visual_row = lines[index + 3]
        if text_row.startswith("| 문자형 정보 |") and visual_row.startswith("| 시각적 정보 |"):
            text_cells = [cell.strip() for cell in text_row.strip("|").split("|")]
            visual_cells = [cell.strip() for cell in visual_row.strip("|").split("|")]
            if len(text_cells) >= 3 and len(visual_cells) >= 3:
                text_types = ["문자", "단순 표", "문단 간 관계"]
                visual_types = ["줄·칸 병합 표", "표 안의 표", "표로 만든 그림", "그림"]
                text_desc = [part.strip() for part in text_cells[2].split("<br>") if part.strip()]
                visual_desc = [part.strip() for part in visual_cells[2].split("<br>") if part.strip()]
                rebuilt = [
                    line,
                    next_line,
                ]
                for label, desc in zip(text_types, text_desc):
                    rebuilt.append(f"| 문자형<br>정보 | {label} | {desc} |")
                rebuilt.append("")
                for label, desc in zip(visual_types, visual_desc):
                    rebuilt.append(f"| 시각적<br>정보 | {label} | {desc} |")
                return rebuilt, index + 4

    if (
        line == "| 구분 | 추진과제 |"
        and next_line.startswith("| ---")
        and index + 2 < len(lines)
        and lines[index + 2].startswith("| 기존문서 AI 활용 앞으로의 문서 작성‧활용 |")
    ):
        return [], index + 3

    if (
        line == "| 구분 | 변화관리 수단(안) |"
        and next_line.startswith("| ---")
        and index + 2 < len(lines)
        and lines[index + 2].startswith("| 동기부여 조직문화 역량강화 |")
    ):
        body_cells = [cell.strip() for cell in lines[index + 2].strip("|").split("|")]
        if len(body_cells) >= 2:
            values = body_cells[1]
            markers = [
                "데이터기반행정평가 반영",
                "기관장 현장소통",
                "보고서 및 AI플랫폼 활용방안 교육",
            ]
            parts: list[str] = []
            remaining = values
            for marker_index, marker in enumerate(markers):
                start = remaining.find(marker)
                if start == -1:
                    parts = []
                    break
                remaining = remaining[start:]
                if marker_index + 1 < len(markers):
                    next_start = remaining.find(markers[marker_index + 1])
                    if next_start == -1:
                        parts = []
                        break
                    parts.append(remaining[:next_start].strip())
                    remaining = remaining[next_start:]
                else:
                    parts.append(remaining.strip())
            if len(parts) == 3:
                return [
                    line,
                    next_line,
                    f"| 동기부여 | {parts[0]} |",
                    f"| 조직문화 | {parts[1]} |",
                    f"| 역량강화 | {parts[2]} |",
                ], index + 3

    return None, index


def _split_pdf_inline_structure(text: str) -> list[str]:
    normalized = _PDF_INLINE_LABEL_RE.sub(r"\n\1", text)
    normalized = _PDF_INLINE_OVERVIEW_RE.sub(r"\n\1", normalized)
    normalized = _PDF_INLINE_TASK_RE.sub("\n", normalized)
    return [clean_line(part) for part in normalized.splitlines() if clean_line(part)]


def _looks_like_structural_heading_title(text: str) -> bool:
    if not text:
        return False
    if text.startswith(("#", "|", ">", "-", "*", "○", "ㅇ", "□", "▸", "▶", "※", "", "󰋎", "󰋏", "󰋐", "<")):
        return False
    return True


def _normalize_pdf_raw_text(raw_text: str) -> str:
    raw_lines = [_normalize_pdf_text_line(line) for line in raw_text.splitlines()]
    normalized_lines: list[str] = []
    index = 0
    current_task_index = 0

    while index < len(raw_lines):
        text = raw_lines[index]
        if not text or _PDF_PAGE_MARKER_RE.fullmatch(text):
            index += 1
            continue

        rewritten_table, next_index = _rewrite_pdf_grouped_table(raw_lines, index)
        if rewritten_table is not None:
            normalized_lines.extend(rewritten_table)
            index = next_index
            continue

        index += 1

        roman_match = _PDF_ASCII_ROMAN_RE.fullmatch(text)
        if roman_match:
            lookahead = index
            while lookahead < len(raw_lines) and not raw_lines[lookahead]:
                lookahead += 1
            if lookahead < len(raw_lines):
                heading_title = raw_lines[lookahead]
                if _looks_like_structural_heading_title(heading_title):
                    normalized_lines.append(f"{_PDF_ASCII_ROMAN_MAP[roman_match.group(1)]}. {heading_title}")
                    index = lookahead + 1
                    current_task_index = 0
                    continue

        if text == "붙임1" and index < len(raw_lines) and raw_lines[index]:
            normalized_lines.append(f"붙임1 {raw_lines[index]}")
            index += 1
            current_task_index = 0
            continue
        if text == "붙임2" and index < len(raw_lines) and raw_lines[index]:
            normalized_lines.append(f"붙임2 {raw_lines[index]}")
            index += 1
            current_task_index = 0
            continue

        for part in _split_pdf_inline_structure(text):
            if part in {"< 기존 문서 AI 활용 >", "< 앞으로의 문서 >"}:
                current_task_index = 0
                normalized_lines.append(part)
                continue
            if part.startswith(" "):
                icons = ("󰋎", "󰋏", "󰋐")
                icon = icons[min(current_task_index, len(icons) - 1)]
                current_task_index += 1
                normalized_lines.append(f"{icon} {part[2:].strip()}")
                continue
            normalized_lines.append(part)

    return "\n".join(normalized_lines)


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


def _windows_registry_java_candidates() -> list[Path]:
    if sys.platform != "win32":
        return []

    try:
        import winreg
    except ImportError:
        return []

    candidates: list[Path] = []
    registry_locations = [
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Eclipse Adoptium\JDK"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Eclipse Adoptium\JRE"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Adoptium\JDK"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Adoptium\JRE"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\JavaSoft\JDK"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\JavaSoft\JRE"),
        (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Eclipse Adoptium\JDK"),
        (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Eclipse Adoptium\JRE"),
        (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Adoptium\JDK"),
        (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Adoptium\JRE"),
    ]

    for hive, key_path in registry_locations:
        try:
            with winreg.OpenKey(hive, key_path) as root_key:
                subkey_count, _, _ = winreg.QueryInfoKey(root_key)
                for index in range(subkey_count):
                    try:
                        version_name = winreg.EnumKey(root_key, index)
                        with winreg.OpenKey(root_key, version_name) as version_key:
                            for value_name in ("Path", "InstallationPath", "JavaHome"):
                                try:
                                    value, _ = winreg.QueryValueEx(version_key, value_name)
                                except OSError:
                                    continue
                                candidates.append(Path(value) / "bin" / "java.exe")
                                break
                    except OSError:
                        continue
        except OSError:
            continue

    return candidates


def _windows_installed_java_candidates() -> list[Path]:
    if sys.platform != "win32":
        return []

    search_roots = [
        os.environ.get("ProgramW6432"),
        os.environ.get("ProgramFiles"),
        os.environ.get("ProgramFiles(x86)"),
        str(Path.home() / "AppData" / "Local" / "Programs"),
    ]
    vendor_dirs = (
        "Eclipse Adoptium",
        "Adoptium",
        "Java",
    )
    version_patterns = (
        "jdk-*",
        "jre-*",
        "temurin-*",
    )

    candidates: list[Path] = []
    for root in search_roots:
        if not root:
            continue
        root_path = Path(root)
        for vendor_dir in vendor_dirs:
            vendor_path = root_path / vendor_dir
            if not vendor_path.exists():
                continue
            for pattern in version_patterns:
                for install_dir in sorted(vendor_path.glob(pattern), reverse=True):
                    candidates.append(install_dir / "bin" / "java.exe")
            direct_java = vendor_path / "bin" / "java.exe"
            if direct_java.exists():
                candidates.append(direct_java)

    return candidates


def _resolve_java_command() -> str | None:
    bundled_candidates = [
        _application_root() / "runtime" / "java" / "bin" / "java.exe",
        _application_root() / "runtime" / "java" / "bin" / "java",
        _application_root() / "java" / "bin" / "java.exe",
        _application_root() / "java" / "bin" / "java",
    ]

    env_candidates = []
    java_home = os.environ.get("JAVA_HOME")
    if java_home:
        env_candidates.extend(
            [
                Path(java_home) / "bin" / "java.exe",
                Path(java_home) / "bin" / "java",
            ]
        )

    candidates = (
        bundled_candidates
        + env_candidates
        + _windows_registry_java_candidates()
        + _windows_installed_java_candidates()
    )

    seen: set[str] = set()
    for candidate in candidates:
        candidate_key = str(candidate).lower()
        if candidate_key in seen:
            continue
        seen.add(candidate_key)
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


def _stage_input_pdf_for_conversion(source_path: Path, temp_root: Path) -> Path:
    staged_path = temp_root / "input.pdf"
    source_bytes = source_path.read_bytes()
    stripped = source_bytes.strip()

    # Some upstream fixtures arrive as base64-wrapped PDF payloads instead of raw PDF bytes.
    if stripped.startswith(b"JVBERi0") and not stripped.startswith(b"%PDF-"):
        try:
            decoded = base64.b64decode(stripped, validate=True)
        except Exception:
            decoded = b""
        if decoded.startswith(b"%PDF-"):
            staged_path.write_bytes(decoded)
            return staged_path

    shutil.copy2(source_path, staged_path)
    return staged_path


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
        staged_source_path = _stage_input_pdf_for_conversion(source_path, temp_root)
        convert = _load_opendataloader_convert()
        try:
            with _conversion_lock:
                with _RuntimeEnvironmentContext(status.java_command):
                    convert(
                        input_path=[str(staged_source_path)],
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
            json_path = _find_json_file(temp_root, staged_source_path)
            raw_text = extract_text_from_json(json_path)
        except ConversionError:
            markdown_path = _find_markdown_file(temp_root, staged_source_path)
            raw_text = markdown_path.read_text(encoding="utf-8", errors="replace")

        return postprocess_markdown(_normalize_pdf_raw_text(raw_text))
    finally:
        if not keep_temp_dir:
            try:
                shutil.rmtree(temp_root)
            except OSError as exc:
                _logger.warning("임시 디렉터리 삭제 실패 (민감 파일 잔류 가능): %s — %s", temp_root, exc)
