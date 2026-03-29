from __future__ import annotations

from html import escape
import re

try:
    import markdown as markdown_lib
except ImportError:  # pragma: no cover
    markdown_lib = None  # type: ignore[assignment]

from src.converter import convert_pdf_to_markdown
from src.preview_widget import decorate_preview_html, normalize_preview_markdown


TITLE_RE = re.compile(r"^#\s+(.+)$", re.MULTILINE)
DEPARTMENT_RE = re.compile(r"^- ([^\n]+?(?:과|팀|실|관|국|센터))\b", re.MULTILINE)


def convert_pdf(pdf_path: str) -> str:
    return convert_pdf_to_markdown(pdf_path)


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

