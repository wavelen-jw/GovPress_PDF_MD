"""Lightweight Markdown syntax highlighter for the editor pane."""
from __future__ import annotations

import re

from PySide6.QtGui import QColor, QFont, QSyntaxHighlighter, QTextCharFormat


def _fmt(
    color: str | None = None,
    bold: bool = False,
    italic: bool = False,
    bg: str | None = None,
    family: str | None = None,
) -> QTextCharFormat:
    fmt = QTextCharFormat()
    if color:
        fmt.setForeground(QColor(color))
    if bold:
        fmt.setFontWeight(QFont.Weight.Bold)
    if italic:
        fmt.setFontItalic(True)
    if bg:
        fmt.setBackground(QColor(bg))
    if family:
        fmt.setFontFamilies([family, "Consolas", "monospace"])
    return fmt


_RULES: list[tuple[re.Pattern[str], QTextCharFormat]] = [
    # Headings  (match full line)
    (re.compile(r"^#{1,6}\s+.+"), _fmt("#1a56db", bold=True)),
    # Horizontal rule
    (re.compile(r"^(?:-{3,}|\*{3,}|_{3,})\s*$"), _fmt("#adb5bd")),
    # Blockquote marker
    (re.compile(r"^>+\s?"), _fmt("#6c757d", italic=True)),
    # Bullet / ordered list marker
    (re.compile(r"^(\s*)[-*+]\s"), _fmt("#0f766e", bold=True)),
    (re.compile(r"^(\s*)\d+\.\s"), _fmt("#0f766e", bold=True)),
    # Bold  **…** or __…__
    (re.compile(r"\*\*[^*\n]+\*\*|__[^_\n]+__"), _fmt(bold=True)),
    # Italic  *…* or _…_  (must come after bold)
    (re.compile(r"(?<!\*)\*(?!\*)[^*\n]+\*(?!\*)|(?<!_)_(?!_)[^_\n]+_(?!_)"), _fmt(italic=True)),
    # Inline code
    (re.compile(r"`[^`\n]+`"), _fmt("#d63384", bg="#f8f9fa", family="Consolas")),
    # Link text
    (re.compile(r"\[([^\]\n]+)\]\([^)\n]+\)"), _fmt("#0d6efd")),
    # Image
    (re.compile(r"!\[[^\]\n]*\]\([^)\n]+\)"), _fmt("#6f42c1")),
    # Fenced code fence (``` or ~~~)
    (re.compile(r"^(`{3,}|~{3,}).*$"), _fmt("#6c757d", family="Consolas")),
]


class MarkdownHighlighter(QSyntaxHighlighter):
    """Single-pass per-block Markdown highlighter."""

    def highlightBlock(self, text: str) -> None:  # noqa: N802 (Qt API name)
        for pattern, fmt in _RULES:
            for m in pattern.finditer(text):
                self.setFormat(m.start(), m.end() - m.start(), fmt)
