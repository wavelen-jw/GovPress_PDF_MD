from __future__ import annotations

from html import escape
from pathlib import Path

from PySide6.QtWidgets import QTextBrowser, QWidget, QVBoxLayout

try:
    import markdown as markdown_lib
except ImportError:  # pragma: no cover
    markdown_lib = None


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
        if markdown_lib is None:
            body = f"<pre>{escape(markdown_text)}</pre>"
        else:
            body = markdown_lib.markdown(
                markdown_text,
                extensions=["tables", "fenced_code", "nl2br"],
            )
        return (
            "<html><head><meta charset='utf-8'>"
            f"<style>{self._css}</style></head><body>{body}</body></html>"
        )
