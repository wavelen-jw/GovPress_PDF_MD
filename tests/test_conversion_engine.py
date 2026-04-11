from __future__ import annotations

import os
import sys
import types
import unittest
from unittest.mock import patch

from server.app.adapters import conversion_engine


class ConversionEngineTests(unittest.TestCase):
    def tearDown(self) -> None:
        conversion_engine.reset_backend_cache()

    def test_prefers_installed_package_backend(self) -> None:
        fake = types.SimpleNamespace(
            convert_hwpx=lambda path, table_mode="text": f"pkg:{path}:{table_mode}",
            convert_pdf=lambda path, timeout=300: f"pkgpdf:{path}:{timeout}",
        )
        with patch.dict(sys.modules, {"govpress_converter": fake}, clear=False):
            with patch.dict(os.environ, {}, clear=False):
                conversion_engine.reset_backend_cache()
                self.assertEqual(
                    conversion_engine.convert_hwpx("/tmp/sample.hwpx", table_mode="html"),
                    "pkg:/tmp/sample.hwpx:html",
                )
                self.assertEqual(
                    conversion_engine.convert_pdf("/tmp/sample.pdf", timeout=120),
                    "pkgpdf:/tmp/sample.pdf:120",
                )
                self.assertEqual(conversion_engine.backend_name(), "package")

    def test_raises_when_no_backend_available(self) -> None:
        with patch("server.app.adapters.conversion_engine.importlib.import_module", side_effect=ModuleNotFoundError("missing")):
            conversion_engine.reset_backend_cache()
            with self.assertRaisesRegex(RuntimeError, "GovPress conversion engine is not configured"):
                conversion_engine.convert_hwpx("/tmp/sample.hwpx")


if __name__ == "__main__":
    unittest.main()
