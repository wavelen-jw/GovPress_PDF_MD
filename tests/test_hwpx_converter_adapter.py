from __future__ import annotations

import os
from pathlib import Path
import tempfile
import textwrap
import unittest

from server.app.adapters import hwpx_converter


class HwpxConverterAdapterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.previous_timeout = os.environ.get("GOVPRESS_HWPX_CONVERSION_TIMEOUT_SECONDS")
        self.previous_pythonpath = os.environ.get("PYTHONPATH")
        self.addCleanup(self._restore_env)

    def _restore_env(self) -> None:
        if self.previous_timeout is None:
            os.environ.pop("GOVPRESS_HWPX_CONVERSION_TIMEOUT_SECONDS", None)
        else:
            os.environ["GOVPRESS_HWPX_CONVERSION_TIMEOUT_SECONDS"] = self.previous_timeout
        if self.previous_pythonpath is None:
            os.environ.pop("PYTHONPATH", None)
        else:
            os.environ["PYTHONPATH"] = self.previous_pythonpath

    def test_convert_hwpx_subprocess_times_out(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            package_dir = Path(temp_dir) / "govpress_converter"
            package_dir.mkdir()
            (package_dir / "__init__.py").write_text(
                textwrap.dedent(
                    """
                    import time

                    def convert_hwpx(path, *, table_mode="text"):
                        time.sleep(5)
                        return "unreachable"

                    def convert_pdf(path, *, timeout=300):
                        return "pdf"
                    """
                ),
                encoding="utf-8",
            )
            sample = Path(temp_dir) / "sample.hwpx"
            sample.write_bytes(b"PK\\x03\\x04")
            os.environ["PYTHONPATH"] = temp_dir
            os.environ["GOVPRESS_HWPX_CONVERSION_TIMEOUT_SECONDS"] = "1"

            with self.assertRaises(TimeoutError):
                hwpx_converter.convert_hwpx(sample)


if __name__ == "__main__":
    unittest.main()
