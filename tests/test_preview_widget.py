import unittest

from src.preview_widget import normalize_preview_markdown


class PreviewWidgetTests(unittest.TestCase):
    def test_normalize_preview_markdown_adds_spacing_before_horizontal_rule(self) -> None:
        markdown = "# 제목\n---\n다음 문장"
        normalized = normalize_preview_markdown(markdown)
        self.assertIn("# 제목\n\n---\n\n다음 문장", normalized)

    def test_normalize_preview_markdown_adds_spacing_before_first_bullet(self) -> None:
        markdown = "문단 마지막 줄\n- 첫 항목\n- 둘째 항목"
        normalized = normalize_preview_markdown(markdown)
        self.assertIn("문단 마지막 줄\n\n- 첫 항목\n- 둘째 항목", normalized)
