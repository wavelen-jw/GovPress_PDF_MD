from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QPlainTextEdit

from .syntax_highlighter import MarkdownHighlighter


class MarkdownEditor(QPlainTextEdit):
    markdown_changed = Signal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setPlaceholderText("PDF를 열거나 드래그하면 Markdown이 여기에 표시됩니다.")
        self._configure_font()
        self._highlighter = MarkdownHighlighter(self.document())
        self.textChanged.connect(self._emit_markdown_changed)

    def _configure_font(self) -> None:
        font = QFont()
        font.setFamilies(["D2Coding", "Consolas", "Fira Code", "Courier New", "monospace"])
        font.setPointSize(11)
        self.setFont(font)
        self.setTabStopDistance(28)  # ~4 spaces

    def _emit_markdown_changed(self) -> None:
        self.markdown_changed.emit(self.toPlainText())

    def set_markdown(self, markdown: str) -> None:
        self.blockSignals(True)
        self.setPlainText(markdown)
        self.blockSignals(False)

    def get_markdown(self) -> str:
        return self.toPlainText()

    def get_current_block_text(self) -> str:
        return self.textCursor().block().text()

    def get_current_block_number(self) -> int:
        return self.textCursor().blockNumber()

    def get_cursor_scroll_ratio(self) -> float:
        document = self.document()
        block_number = self.textCursor().blockNumber()
        total_blocks = document.blockCount()
        if total_blocks <= 1:
            return 0.0

        # Snap near the document edges so the preview can reach the true top/bottom.
        if block_number <= 2:
            return 0.0
        if block_number >= total_blocks - 3:
            return 1.0

        block_count = max(total_blocks - 1, 1)
        return min(max(block_number / block_count, 0.0), 1.0)
