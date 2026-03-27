from __future__ import annotations

from pathlib import Path
import shutil

from .markdown_postprocessor import postprocess_markdown
from .pymupdf_extractor import extract_text_from_pdf_with_pymupdf


class ConversionError(RuntimeError):
    """Raised when PDF conversion fails."""


def _stage_input_pdf_for_conversion(source_path: Path, temp_root: Path) -> Path:
    staged_path = temp_root / "input.pdf"
    shutil.copy2(source_path, staged_path)
    return staged_path


def convert_pdf_to_markdown(
    pdf_path: str | Path,
    timeout_seconds: int = 180,
    keep_temp_dir: bool = False,
    backend: str = "pymupdf",
) -> str:
    """Convert a PDF into normalized markdown text with the PyMuPDF backend."""
    del timeout_seconds
    del keep_temp_dir

    source_path = Path(pdf_path)
    if not source_path.exists():
        raise FileNotFoundError(f"PDF 파일을 찾을 수 없습니다: {source_path}")
    if source_path.suffix.lower() != ".pdf":
        raise ValueError("PDF 파일만 변환할 수 있습니다.")
    if backend != "pymupdf":
        raise ValueError(f"지원하지 않는 backend입니다: {backend}")

    try:
        raw_text = extract_text_from_pdf_with_pymupdf(source_path)
    except Exception as exc:  # pragma: no cover
        raise ConversionError(f"PDF 텍스트 추출에 실패했습니다: {source_path}") from exc

    return postprocess_markdown(raw_text)
