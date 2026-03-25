from __future__ import annotations

from html import escape
from pathlib import Path
import re

from PySide6.QtWidgets import QTextBrowser, QWidget, QVBoxLayout

try:
    import markdown as markdown_lib
except ImportError:  # pragma: no cover
    markdown_lib = None


HORIZONTAL_RULE_PATTERN = re.compile(r"^ {0,3}([-*_])(?:\s*\1){2,}\s*$")
BULLET_PATTERN = re.compile(r"^\s*[-+*]\s+")
NUMBERED_LIST_PATTERN = re.compile(r"^\s*\d+\.\s+")


def normalize_preview_markdown(markdown_text: str) -> str:
    lines = markdown_text.splitlines()
    normalized: list[str] = []

    for line in lines:
        stripped = line.strip()
        previous_nonempty = next((item.strip() for item in reversed(normalized) if item.strip()), "")

        if HORIZONTAL_RULE_PATTERN.match(line):
            if normalized and normalized[-1].strip():
                normalized.append("")
            normalized.append(stripped)
            normalized.append("")
            continue

        if BULLET_PATTERN.match(line) and previous_nonempty:
            if not (
                BULLET_PATTERN.match(previous_nonempty)
                or NUMBERED_LIST_PATTERN.match(previous_nonempty)
                or previous_nonempty.startswith(">")
                or previous_nonempty.startswith("#")
            ):
                normalized.append("")

        normalized.append(line)

    deduped: list[str] = []
    blank_streak = 0
    for line in normalized:
        if line.strip():
            blank_streak = 0
            deduped.append(line)
            continue
        blank_streak += 1
        if blank_streak <= 2:
            deduped.append("")

    return "\n".join(deduped)


class MarkdownPreviewWidget(QWidget):
    def __init__(self, css_path: Path | None = None, parent=None) -> None:
        super().__init__(parent)
        self.browser = QTextBrowser(self)
        self.browser.setOpenExternalLinks(False)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.browser)
        self._css = css_path.read_text(encoding="utf-8") if css_path and css_path.exists() else ""

    def render_markdown(self, markdown_text: str) -> None:
        """Render markdown text into the preview browser."""
        self.browser.setHtml(self._to_html(markdown_text))

    def _to_html(self, markdown_text: str) -> str:
        normalized_markdown = normalize_preview_markdown(markdown_text)
        if markdown_lib is None:
            body = f"<pre>{escape(normalized_markdown)}</pre>"
        else:
            body = markdown_lib.markdown(
                normalized_markdown,
                extensions=["tables", "fenced_code", "nl2br", "sane_lists"],
            )
        return (
            "<html><head><meta charset='utf-8'>"
            f"<style>{self._css}</style></head><body>{body}</body></html>"
        )
