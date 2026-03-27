from __future__ import annotations

from html import escape
from pathlib import Path
import re

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QTextBrowser, QWidget, QVBoxLayout

try:
    import markdown as markdown_lib
except ImportError:  # pragma: no cover
    markdown_lib = None


HORIZONTAL_RULE_PATTERN = re.compile(r"^ {0,3}([-*_])(?:\s*\1){2,}\s*$")
BULLET_PATTERN = re.compile(r"^\s*[-+*]\s+")
NUMBERED_LIST_PATTERN = re.compile(r"^\s*\d+\.\s+")
BLOCKQUOTE_PATTERN = re.compile(r"<blockquote>(.*?)</blockquote>", re.IGNORECASE | re.DOTALL)
HR_PATTERN = re.compile(r"<hr\s*/?>", re.IGNORECASE)
H4_OPEN_PATTERN = re.compile(r"<h4\b[^>]*>", re.IGNORECASE)
H4_CLOSE_PATTERN = re.compile(r"</h4>", re.IGNORECASE)
HIGHLIGHT_TOKEN = "GOVPRESS_CURSOR_HIGHLIGHT_TOKEN"


def _normalize_indented_markdown_line(line: str) -> str:
    leading_width = len(line) - len(line.lstrip(" "))
    if leading_width <= 0:
        return line

    stripped = line.lstrip(" ")
    if not (
        BULLET_PATTERN.match(stripped)
        or NUMBERED_LIST_PATTERN.match(stripped)
        or stripped.startswith(">")
    ):
        return line

    nesting_level = leading_width // 2
    if nesting_level <= 0:
        return line
    return f"{' ' * (nesting_level * 4)}{stripped}"


def normalize_preview_markdown(markdown_text: str) -> str:
    lines = markdown_text.splitlines()
    normalized: list[str] = []

    for raw_line in lines:
        line = _normalize_indented_markdown_line(raw_line)
        stripped = line.strip()
        previous_nonempty = next((item for item in reversed(normalized) if item.strip()), "")
        previous_nonempty_stripped = previous_nonempty.strip()

        if HORIZONTAL_RULE_PATTERN.match(line):
            if normalized and normalized[-1].strip():
                normalized.append("")
            normalized.append("---")
            normalized.append("")
            continue

        if BULLET_PATTERN.match(line) and previous_nonempty_stripped:
            if not (
                BULLET_PATTERN.match(previous_nonempty_stripped)
                or NUMBERED_LIST_PATTERN.match(previous_nonempty_stripped)
                or previous_nonempty_stripped.startswith("#")
            ):
                normalized.append("")

        if stripped.startswith(">") and previous_nonempty_stripped:
            current_indent = len(line) - len(line.lstrip(" "))
            previous_indent = len(previous_nonempty) - len(previous_nonempty.lstrip(" "))
            if (
                current_indent > previous_indent
                and (
                    BULLET_PATTERN.match(previous_nonempty_stripped)
                    or NUMBERED_LIST_PATTERN.match(previous_nonempty_stripped)
                )
                and normalized[-1].strip()
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


def inject_cursor_highlight(markdown_text: str, cursor_line: str) -> str:
    if not cursor_line.strip():
        return markdown_text

    lines = markdown_text.splitlines()
    for index, line in enumerate(lines):
        if line != cursor_line:
            continue

        for prefix in ("# ", "## ", "### ", "- ", "* ", "> "):
            if line.startswith(prefix):
                lines[index] = f"{prefix}{HIGHLIGHT_TOKEN}{line[len(prefix):]}"
                return "\n".join(lines)

        lines[index] = f"{HIGHLIGHT_TOKEN}{line}"
        return "\n".join(lines)
    return markdown_text


def decorate_preview_html(html: str) -> str:
    html = HR_PATTERN.sub(
        '<hr class="md-rule" style="display:block;border:0;border-top:2px solid #000000;height:0;margin:8px 0 10px 0;" />',
        html,
    )
    html = H4_OPEN_PATTERN.sub(
        '<p class="md-h4" style="font-size:22px;font-weight:700;line-height:1.34;margin:0.95em 0 0.42em 0;color:#2f2f2f;">',
        html,
    )
    html = H4_CLOSE_PATTERN.sub("</p>", html)
    html = BLOCKQUOTE_PATTERN.sub(_replace_blockquote_with_callout_table, html)
    html = html.replace(
        HIGHLIGHT_TOKEN,
        '<span class="cursor-highlight" style="background:#fff8c6;padding:0 2px;border-radius:2px;">',
        1,
    )
    if '<span class="cursor-highlight"' in html:
        html = html.replace("</span>", "</span>", 1)
        html = _close_first_highlight_span(html)
    return html


def _replace_blockquote_with_callout_table(match: re.Match[str]) -> str:
    inner = match.group(1).strip()
    return (
        '<table class="quote-block" cellspacing="0" cellpadding="0" '
        'style="border-collapse:collapse;margin:12px 0 14px 0;width:100%;">'
        "<tr>"
        '<td style="width:5px;background:#000000;padding:0;margin:0;"></td>'
        '<td style="padding:2px 0 2px 14px;color:#555555;">'
        f"{inner}"
        "</td>"
        "</tr>"
        "</table>"
    )


def _close_first_highlight_span(html: str) -> str:
    marker = '<span class="cursor-highlight" style="background:#fff8c6;padding:0 2px;border-radius:2px;">'
    start = html.find(marker)
    if start == -1:
        return html
    start += len(marker)
    next_tag = html.find("<", start)
    if next_tag == -1:
        next_tag = len(html)
    return html[:next_tag] + "</span>" + html[next_tag:]


class MarkdownPreviewWidget(QWidget):
    def __init__(self, css_path: Path | None = None, parent=None) -> None:
        super().__init__(parent)
        self.browser = QTextBrowser(self)
        self.browser.setOpenExternalLinks(False)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.browser)
        self._css = css_path.read_text(encoding="utf-8") if css_path and css_path.exists() else ""

    def render_markdown(
        self,
        markdown_text: str,
        cursor_line: str | None = None,
        preserve_scroll: bool = False,
        target_ratio: float | None = None,
    ) -> None:
        """Render markdown text into the preview browser."""
        scroll_bar = self.browser.verticalScrollBar()
        previous_value = scroll_bar.value()
        previous_maximum = max(scroll_bar.maximum(), 1)
        self.browser.setHtml(self._to_html(markdown_text, cursor_line))
        if target_ratio is not None:
            QTimer.singleShot(0, lambda: self.scroll_to_ratio(target_ratio))
        elif preserve_scroll:
            QTimer.singleShot(
                0,
                lambda: self._restore_scroll_position(previous_value, previous_maximum),
            )

    def _restore_scroll_position(self, previous_value: int, previous_maximum: int) -> None:
        scroll_bar = self.browser.verticalScrollBar()
        current_maximum = scroll_bar.maximum()
        if current_maximum <= 0:
            scroll_bar.setValue(0)
            return
        if previous_maximum <= 0:
            scroll_bar.setValue(min(previous_value, current_maximum))
            return
        scroll_bar.setValue(min(previous_value, current_maximum))

    def scroll_to_ratio(self, ratio: float) -> None:
        scroll_bar = self.browser.verticalScrollBar()
        maximum = scroll_bar.maximum()
        clamped = min(max(ratio, 0.0), 1.0)
        if maximum <= 0:
            scroll_bar.setValue(0)
            return
        if clamped >= 0.999:
            scroll_bar.setValue(maximum)
            return
        scroll_bar.setValue(int(maximum * clamped))

    def _to_html(self, markdown_text: str, cursor_line: str | None = None) -> str:
        normalized_markdown = normalize_preview_markdown(markdown_text)
        if cursor_line:
            normalized_markdown = inject_cursor_highlight(normalized_markdown, cursor_line)
        if markdown_lib is None:
            body = f"<pre>{escape(normalized_markdown)}</pre>"
        else:
            body = markdown_lib.markdown(
                normalized_markdown,
                extensions=["tables", "fenced_code", "nl2br", "sane_lists"],
            )
            body = decorate_preview_html(body)
        return (
            "<html><head><meta charset='utf-8'>"
            f"<style>{self._css}</style></head><body>{body}</body></html>"
        )
