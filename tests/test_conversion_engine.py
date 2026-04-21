from __future__ import annotations

import os
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

from server.app.adapters import conversion_engine


class ConversionEngineTests(unittest.TestCase):
    def tearDown(self) -> None:
        conversion_engine.reset_backend_cache()
        sys.modules.pop("govpress_converter", None)

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
            with self.assertRaisesRegex(RuntimeError, "local-root fallback is disabled"):
                conversion_engine.convert_hwpx("/tmp/sample.hwpx")

    def test_raises_when_local_root_fallback_is_disabled(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            module_dir = root / "src" / "govpress_converter"
            module_dir.mkdir(parents=True)
            (module_dir / "__init__.py").write_text(
                "def convert_hwpx(path, table_mode='text'):\n    return path\n"
                "def convert_pdf(path, timeout=300):\n    return path\n",
                encoding="utf-8",
            )
            with patch.dict(
                os.environ,
                {
                    "GOV_MD_CONVERTER_ROOT": str(root),
                    "GOVPRESS_CONVERTER_ALLOW_LOCAL_FALLBACK": "0",
                },
                clear=False,
            ):
                with patch(
                    "server.app.adapters.conversion_engine.importlib.import_module",
                    side_effect=ModuleNotFoundError("missing"),
                ):
                    conversion_engine.reset_backend_cache()
                    with self.assertRaisesRegex(RuntimeError, "local-root fallback is disabled"):
                        conversion_engine.convert_hwpx("/tmp/sample.hwpx")

    def test_uses_local_root_when_fallback_is_enabled(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            module_dir = root / "src" / "govpress_converter"
            module_dir.mkdir(parents=True)
            (module_dir / "__init__.py").write_text(
                "def convert_hwpx(path, table_mode='text'):\n    return f'local:{path}:{table_mode}'\n"
                "def convert_pdf(path, timeout=300):\n    return f'localpdf:{path}:{timeout}'\n",
                encoding="utf-8",
            )
            real_import_module = conversion_engine.importlib.import_module
            attempts = {"count": 0}

            def fake_import(name: str, package: str | None = None):
                if name == "govpress_converter":
                    attempts["count"] += 1
                    if attempts["count"] == 1:
                        raise ModuleNotFoundError("missing")
                return real_import_module(name, package)

            with patch.dict(
                os.environ,
                {
                    "GOV_MD_CONVERTER_ROOT": str(root),
                    "GOVPRESS_CONVERTER_ALLOW_LOCAL_FALLBACK": "1",
                },
                clear=False,
            ):
                sys.modules.pop("govpress_converter", None)
                with patch("server.app.adapters.conversion_engine.importlib.import_module", side_effect=fake_import):
                    conversion_engine.reset_backend_cache()
                    self.assertEqual(
                        conversion_engine.convert_hwpx("/tmp/sample.hwpx", table_mode="html"),
                        "local:/tmp/sample.hwpx:html",
                    )
                    self.assertEqual(conversion_engine.backend_name(), "local-root")

    def test_text_mode_supports_legacy_hwpx_signature_without_table_mode(self) -> None:
        fake = types.SimpleNamespace(
            convert_hwpx=lambda path: f"legacy:{path}",
            convert_pdf=lambda path, timeout=300: f"pkgpdf:{path}:{timeout}",
        )
        with patch.dict(sys.modules, {"govpress_converter": fake}, clear=False):
            conversion_engine.reset_backend_cache()
            self.assertEqual(conversion_engine.convert_hwpx("/tmp/sample.hwpx"), "legacy:/tmp/sample.hwpx")
            with self.assertRaisesRegex(RuntimeError, "does not support table_mode"):
                conversion_engine.convert_hwpx("/tmp/sample.hwpx", table_mode="html")

    def test_pdf_timeout_seconds_signature_is_supported(self) -> None:
        fake = types.SimpleNamespace(
            convert_hwpx=lambda path, table_mode="text": f"pkg:{path}:{table_mode}",
            convert_pdf=lambda path, timeout_seconds=300: f"pkgpdf:{path}:{timeout_seconds}",
        )
        with patch.dict(sys.modules, {"govpress_converter": fake}, clear=False):
            conversion_engine.reset_backend_cache()
            self.assertEqual(
                conversion_engine.convert_pdf("/tmp/sample.pdf", timeout=120),
                "pkgpdf:/tmp/sample.pdf:120",
            )


if __name__ == "__main__":
    unittest.main()
