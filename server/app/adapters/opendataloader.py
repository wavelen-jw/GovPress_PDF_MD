from __future__ import annotations

from html import escape
import re
import subprocess
import sys

try:
    import markdown as markdown_lib
except ImportError:  # pragma: no cover
    markdown_lib = None  # type: ignore[assignment]

from .preview_widget import decorate_preview_html, normalize_preview_markdown


TITLE_RE = re.compile(r"^#\s+(.+)$", re.MULTILINE)
DEPARTMENT_RE = re.compile(r"^- ([^\n]+?(?:과|팀|실|관|국|센터))\b", re.MULTILINE)


def convert_pdf(pdf_path: str, *, timeout_seconds: int | None = None) -> str:
    try:
        result = subprocess.run(
            [sys.executable, "-m", "server.app.adapters.opendataloader_cli", pdf_path],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"PDF conversion timed out after {timeout_seconds}s")
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip() or f"return code={result.returncode}"
        raise RuntimeError(f"PDF conversion subprocess failed: {detail}")
    return result.stdout


def render_preview_html(markdown_text: str) -> str:
    normalized = normalize_preview_markdown(markdown_text)
    if markdown_lib is None:
        return f"<pre>{escape(normalized)}</pre>"
    body = markdown_lib.markdown(
        normalized,
        extensions=["tables", "fenced_code", "nl2br", "sane_lists"],
    )
    return decorate_preview_html(body)


def extract_metadata(markdown_text: str) -> tuple[str | None, str | None]:
    title_match = TITLE_RE.search(markdown_text)
    department_match = DEPARTMENT_RE.search(markdown_text)
    title = title_match.group(1).strip() if title_match else None
    department = department_match.group(1).strip() if department_match else None
    return title, department
