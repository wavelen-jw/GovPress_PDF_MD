"""Tests for GovPressAPI – thread-safety, state management, and save UX."""
from __future__ import annotations

import os
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.webview_api import GovPressAPI
from src.converter import _RuntimeEnvironmentContext, _conversion_lock


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_api() -> GovPressAPI:
    api = GovPressAPI()
    api.window = MagicMock()
    api.window.evaluate_js = MagicMock()
    return api


# ---------------------------------------------------------------------------
# Thread-safety: _lock guards _state mutations
# ---------------------------------------------------------------------------

class TestStateLock(unittest.TestCase):
    def test_update_content_concurrent_no_exception(self):
        """Many threads calling update_content simultaneously must not raise."""
        api = _make_api()
        errors: list[Exception] = []

        def worker(text: str) -> None:
            try:
                api.update_content(text)
            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=worker, args=(f"# line {i}",)) for i in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(errors, [], f"Unexpected exceptions: {errors}")

    def test_do_convert_loads_state_before_js_callback(self):
        """After _do_convert, state is updated before evaluate_js fires."""
        api = _make_api()
        state_after_call: list = []

        def capture_js(code: str) -> None:
            if "onConversionSuccess" in code:
                state_after_call.append(api._state.current_pdf_path)

        api.window.evaluate_js = capture_js

        fake_path = MagicMock(spec=Path)
        fake_path.exists.return_value = True
        fake_path.name = "test.pdf"

        with patch("src.webview_api.convert_pdf_to_markdown", return_value="# Title"):
            with patch("src.webview_api.ensure_utf8_text", return_value="# Title"):
                api._do_convert(fake_path)

        self.assertTrue(state_after_call, "JS callback was never fired")
        self.assertIsNotNone(state_after_call[0], "_state.current_pdf_path should be set before JS fires")

    def test_api_has_lock(self):
        api = _make_api()
        self.assertTrue(hasattr(api, "_lock"))
        self.assertIsInstance(api._lock, type(threading.Lock()))


# ---------------------------------------------------------------------------
# Save: full path returned alongside basename
# ---------------------------------------------------------------------------

class TestSaveMarkdownResponse(unittest.TestCase):
    def test_saved_response_contains_full_path_and_name(self):
        api = _make_api()

        with tempfile.TemporaryDirectory() as tmp:
            save_path = Path(tmp) / "output.md"
            api.window.create_file_dialog = MagicMock(return_value=str(save_path))

            with patch("src.webview_api.save_markdown_file"):
                result = api.save_markdown("# hello")

        self.assertTrue(result.get("saved"), f"Expected saved=True, got {result}")
        self.assertIn("path", result)
        self.assertIn("name", result)
        self.assertEqual(result["name"], "output.md")
        # full path must be longer than bare filename
        self.assertGreater(len(result["path"]), len(result["name"]))
        self.assertTrue(result["path"].endswith("output.md"))

    def test_cancelled_save_returns_saved_false(self):
        api = _make_api()
        api.window.create_file_dialog = MagicMock(return_value=None)
        result = api.save_markdown("# hello")
        self.assertFalse(result.get("saved"))
        self.assertNotIn("path", result)

    def test_io_error_returns_error_key(self):
        api = _make_api()
        with tempfile.TemporaryDirectory() as tmp:
            save_path = Path(tmp) / "output.md"
            api.window.create_file_dialog = MagicMock(return_value=str(save_path))

            with patch("src.webview_api.save_markdown_file", side_effect=OSError("disk full")):
                result = api.save_markdown("# hello")

        self.assertFalse(result.get("saved"))
        self.assertIn("error", result)


# ---------------------------------------------------------------------------
# converter.py: _conversion_lock exists and env is restored
# ---------------------------------------------------------------------------

class TestConverterEnvLock(unittest.TestCase):
    def test_conversion_lock_is_module_level_lock(self):
        import src.converter as m
        self.assertTrue(hasattr(m, "_conversion_lock"), "_conversion_lock not found in converter module")
        self.assertIsInstance(m._conversion_lock, type(threading.Lock()))

    def test_runtime_env_context_restores_path_on_exit(self):
        original = os.environ.get("PATH", "")
        with _RuntimeEnvironmentContext("C:/fake/java.exe"):
            pass
        self.assertEqual(os.environ.get("PATH", ""), original, "PATH was not restored after context exit")

    def test_runtime_env_context_restores_java_home_on_exit(self):
        original = os.environ.get("JAVA_HOME")
        with _RuntimeEnvironmentContext("C:/fake/java.exe"):
            pass
        self.assertEqual(os.environ.get("JAVA_HOME"), original, "JAVA_HOME was not restored after context exit")

    def test_runtime_env_context_restores_on_exception(self):
        original_path = os.environ.get("PATH", "")
        try:
            with _RuntimeEnvironmentContext("C:/fake/java.exe"):
                raise RuntimeError("oops")
        except RuntimeError:
            pass
        self.assertEqual(os.environ.get("PATH", ""), original_path, "PATH not restored after exception inside context")


# ---------------------------------------------------------------------------
# _start_conversion: file-not-found guard fires JS error callback
# ---------------------------------------------------------------------------

class TestStartConversion(unittest.TestCase):
    def test_missing_file_calls_error_callback(self):
        api = _make_api()
        js_calls: list[str] = []
        api.window.evaluate_js = lambda code: js_calls.append(code)

        api._start_conversion(Path("/does/not/exist.pdf"))

        self.assertTrue(any("onConversionError" in c for c in js_calls),
                        f"Expected onConversionError in JS calls, got: {js_calls}")


if __name__ == "__main__":
    unittest.main()
