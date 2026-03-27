from pathlib import Path
import unittest

from src.state import DocumentState


class DocumentStateTests(unittest.TestCase):
    def test_load_resets_dirty_state(self) -> None:
        state = DocumentState(is_dirty=True)
        state.load_markdown("# test\n", Path("sample.pdf"), Path("sample_images"))
        self.assertFalse(state.is_dirty)
        self.assertEqual(state.current_pdf_path, Path("sample.pdf"))
        self.assertEqual(state.current_image_dir, Path("sample_images"))

    def test_update_markdown_marks_dirty(self) -> None:
        state = DocumentState(current_markdown="a")
        state.update_markdown("b")
        self.assertTrue(state.is_dirty)

    def test_mark_saved_updates_display(self) -> None:
        state = DocumentState()
        state.mark_saved(Path("out.md"))
        self.assertEqual(state.display_name, "out.md")
        self.assertFalse(state.is_dirty)


if __name__ == "__main__":
    unittest.main()
