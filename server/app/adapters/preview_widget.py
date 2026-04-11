from __future__ import annotations

from html import escape
import re

try:
    import markdown as markdown_lib
except ImportError:  # pragma: no cover
    markdown_lib = None  # type: ignore[assignment]


HORIZONTAL_RULE_PATTERN = re.compile(r"^ {0,3}([-*_])(?:\s*\1){2,}\s*$")
BULLET_PATTERN = re.compile(r"^\s*[-+*]\s+")
NUMBERED_LIST_PATTERN = re.compile(r"^\s*\d+\.\s+")
HR_PATTERN = re.compile(r"<hr\s*/?>", re.IGNORECASE)
H4_OPEN_PATTERN = re.compile(r"<h4\b[^>]*>", re.IGNORECASE)
H4_CLOSE_PATTERN = re.compile(r"</h4>", re.IGNORECASE)
TRAILING_BR_PATTERN = re.compile(r"<br\s*/?>\s*</p>", re.IGNORECASE)
HIGHLIGHT_TOKEN = "GOVPRESS_CURSOR_HIGHLIGHT_TOKEN"
BLOCKQUOTE_PARAGRAPH_PATTERN = re.compile(r"(<blockquote>\s*<p>)(.*?)(</p>\s*</blockquote>)", re.IGNORECASE | re.DOTALL)
_UNSAFE_TAG_PATTERN = re.compile(
    r"<script[\s\S]*?</script\s*>"
    r"|<iframe[\s\S]*?(?:</iframe\s*>|/>)"
    r"|<object[\s\S]*?(?:</object\s*>|/>)"
    r"|<embed\b[^>]*>"
    r"|<form\b[^>]*>|</form>",
    re.IGNORECASE,
)
_UNSAFE_ATTR_PATTERN = re.compile(r"""\bon\w+\s*=\s*(?:"[^"]*"|'[^']*'|\S+)""", re.IGNORECASE)
_UNSAFE_URL_ATTR_PATTERN = re.compile(
    r"""((?:href|src|action)\s*=\s*["']?)\s*(?:javascript|data|vbscript)\s*:""",
    re.IGNORECASE,
)


def _strip_unsafe_html(html: str) -> str:
    html = _UNSAFE_TAG_PATTERN.sub("", html)
    html = _UNSAFE_ATTR_PATTERN.sub("", html)
    html = _UNSAFE_URL_ATTR_PATTERN.sub(r"\1#", html)
    return html


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
            normalized.append("<hr />")
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
            if previous_nonempty_stripped.startswith("|") and normalized and normalized[-1].strip():
                normalized.append("")
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


def decorate_preview_html(html: str) -> str:
    html = _strip_unsafe_html(html)
    html = HR_PATTERN.sub(
        '<hr class="md-rule" style="display:block;border:0;border-top:2px solid #000000;height:0;margin:8px 0 10px 0;" />',
        html,
    )
    html = H4_OPEN_PATTERN.sub(
        '<p class="md-h4" style="font-size:22px;font-weight:700;line-height:1.34;margin:0.95em 0 0.42em 0;color:#2f2f2f;">',
        html,
    )
    html = H4_CLOSE_PATTERN.sub("</p>", html)
    html = TRAILING_BR_PATTERN.sub("</p>", html)
    return _expand_blockquote_paragraphs(html)


def _expand_blockquote_paragraphs(html: str) -> str:
    def repl(match: re.Match[str]) -> str:
        body = re.sub(r"<br\s*/?>", "</p><p>", match.group(2), flags=re.IGNORECASE)
        return f"{match.group(1)}{body}{match.group(3)}"

    return BLOCKQUOTE_PARAGRAPH_PATTERN.sub(repl, html)


def render_preview_html(markdown_text: str) -> str:
    normalized = normalize_preview_markdown(markdown_text)
    if markdown_lib is None:
        return f"<pre>{escape(normalized)}</pre>"
    body = markdown_lib.markdown(
        normalized,
        extensions=["tables", "fenced_code", "nl2br", "sane_lists"],
    )
    return decorate_preview_html(body)
