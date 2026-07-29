from __future__ import annotations

import importlib.util
import hashlib
from pathlib import Path
import sys
import unittest
from unittest import mock


SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "deploy"
    / "mcp-converter-fixed"
    / "preflight.py"
)
SPEC = importlib.util.spec_from_file_location("converter_image_preflight", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class ConverterImagePreflightTests(unittest.TestCase):
    def test_normalize_version(self) -> None:
        self.assertEqual(MODULE.normalize_version("v0.4.7"), "0.4.7")
        self.assertEqual(MODULE.normalize_version("0.4.7"), "0.4.7")

    @mock.patch.object(MODULE.subprocess, "run")
    @mock.patch.object(MODULE.metadata, "version", return_value="0.4.7")
    def test_inspect_runtime_requires_all_versions(
        self,
        _distribution_version: mock.Mock,
        run: mock.Mock,
    ) -> None:
        run.return_value.stdout = "govpress-hwpx-md 0.4.7\n"
        fake_module = mock.Mock(__version__="0.4.7")
        wheel_sha256 = hashlib.sha256(SCRIPT.read_bytes()).hexdigest()
        with (
            mock.patch.dict(
                MODULE.os.environ,
                {
                    "GOVPRESS_HWPX_MD_PYTHON": sys.executable,
                    "GOVPRESS_HWPX_MD_WHEEL": str(SCRIPT),
                    "GOVPRESS_HWPX_MD_WHEEL_SHA256": wheel_sha256,
                },
                clear=False,
            ),
            mock.patch.dict(sys.modules, {"govpress_converter": fake_module}),
        ):
            result = MODULE.inspect_runtime("0.4.7")
        self.assertEqual(result["distribution_version"], "0.4.7")
        self.assertEqual(result["module_version"], "0.4.7")
        self.assertEqual(result["cli_version"], "0.4.7")

    @mock.patch.object(MODULE.subprocess, "run")
    @mock.patch.object(MODULE.metadata, "version", return_value="0.4.5")
    def test_inspect_runtime_rejects_mismatch(
        self,
        _distribution_version: mock.Mock,
        run: mock.Mock,
    ) -> None:
        run.return_value.stdout = "govpress-hwpx-md 0.4.7\n"
        fake_module = mock.Mock(__version__="0.4.7")
        wheel_sha256 = hashlib.sha256(SCRIPT.read_bytes()).hexdigest()
        with (
            mock.patch.dict(
                MODULE.os.environ,
                {
                    "GOVPRESS_HWPX_MD_PYTHON": sys.executable,
                    "GOVPRESS_HWPX_MD_WHEEL": str(SCRIPT),
                    "GOVPRESS_HWPX_MD_WHEEL_SHA256": wheel_sha256,
                },
                clear=False,
            ),
            mock.patch.dict(sys.modules, {"govpress_converter": fake_module}),
        ):
            with self.assertRaisesRegex(SystemExit, "distribution_version=0.4.5"):
                MODULE.inspect_runtime("0.4.7")


if __name__ == "__main__":
    unittest.main()
