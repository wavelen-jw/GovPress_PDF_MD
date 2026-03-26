import unittest

from src.preview_widget import (
    MarkdownPreviewWidget,
    decorate_preview_html,
    inject_cursor_highlight,
    normalize_preview_markdown,
)


class PreviewWidgetTests(unittest.TestCase):
    def test_normalize_preview_markdown_adds_spacing_before_horizontal_rule(self) -> None:
        markdown = "# 제목\n---\n다음 문장"
        normalized = normalize_preview_markdown(markdown)
        self.assertIn("# 제목\n\n<hr />\n\n다음 문장", normalized)

    def test_normalize_preview_markdown_adds_spacing_before_first_bullet(self) -> None:
        markdown = "문단 마지막 줄\n- 첫 항목\n- 둘째 항목"
        normalized = normalize_preview_markdown(markdown)
        self.assertIn("문단 마지막 줄\n\n- 첫 항목\n- 둘째 항목", normalized)

    def test_normalize_preview_markdown_breaks_quote_before_top_level_bullet(self) -> None:
        markdown = "> 인용문\n- 다음 항목"
        normalized = normalize_preview_markdown(markdown)
        self.assertIn("> 인용문\n\n- 다음 항목", normalized)

    def test_normalize_preview_markdown_expands_nested_bullet_indent(self) -> None:
        markdown = "- 상위 항목\n  - 하위 항목"
        normalized = normalize_preview_markdown(markdown)
        self.assertIn("- 상위 항목\n    - 하위 항목", normalized)

    def test_normalize_preview_markdown_adds_spacing_before_nested_quote_after_bullet(self) -> None:
        markdown = "- 상위 항목\n  > 참고 문장"
        normalized = normalize_preview_markdown(markdown)
        self.assertIn("- 상위 항목\n\n    > 참고 문장", normalized)

    def test_decorate_preview_html_does_not_add_rule_below_headings(self) -> None:
        html = "<h1>제목</h1><p>본문</p><h2>소제목</h2>"
        decorated = decorate_preview_html(html)
        self.assertNotIn('class="heading-rule"', decorated)

    def test_decorate_preview_html_makes_markdown_rule_explicit(self) -> None:
        html = "<p>앞문단</p><hr><p>뒷문단</p>"
        decorated = decorate_preview_html(html)
        self.assertIn('class="md-rule"', decorated)
        self.assertIn("border-top:2px solid #000000", decorated)

    def test_decorate_preview_html_replaces_blockquote_with_table_bar(self) -> None:
        html = "<blockquote><p>인용문</p></blockquote>"
        decorated = decorate_preview_html(html)
        self.assertIn('class="quote-block"', decorated)
        self.assertIn("background:#000000", decorated)

    def test_inject_cursor_highlight_marks_matching_plain_line(self) -> None:
        markdown = "첫 줄\n둘째 줄"
        highlighted = inject_cursor_highlight(markdown, "둘째 줄")
        self.assertIn("GOVPRESS_CURSOR_HIGHLIGHT_TOKEN둘째 줄", highlighted)

    def test_inject_cursor_highlight_preserves_bullet_prefix(self) -> None:
        markdown = "- 첫 항목"
        highlighted = inject_cursor_highlight(markdown, "- 첫 항목")
        self.assertEqual(highlighted, "- GOVPRESS_CURSOR_HIGHLIGHT_TOKEN첫 항목")

    def test_preview_html_styles_h4_slightly_larger_than_body(self) -> None:
        widget = MarkdownPreviewWidget()
        html = widget._to_html("#### 소제목", None)
        self.assertIn("<h4>소제목</h4>", html)
