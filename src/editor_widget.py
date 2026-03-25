from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QPlainTextEdit


class MarkdownEditor(QPlainTextEdit):
    markdown_changed = Signal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setPlaceholderText("Markdown 내용이 여기에 표시됩니다.")
        self.textChanged.connect(self._emit_markdown_changed)

    def _emit_markdown_changed(self) -> None:
        self.markdown_changed.emit(self.toPlainText())

    def set_markdown(self, markdown: str) -> None:
        self.blockSignals(True)
        self.setPlainText(markdown)
        self.blockSignals(False)

    def get_markdown(self) -> str:
        return self.toPlainText()
