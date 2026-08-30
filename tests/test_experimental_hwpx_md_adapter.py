from __future__ import annotations

import os
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch

from server.app.adapters import experimental_hwpx_md


class ExperimentalHwpxMdAdapterTests(unittest.TestCase):
    def test_convert_hwpx_passes_metadata_json_to_cli(self) -> None:
        captured: dict[str, object] = {}

        def fake_run(command, **kwargs):
            captured["command"] = command
            return subprocess.CompletedProcess(command, 0, stdout="ok", stderr="")

        with patch.dict(os.environ, {"GOVPRESS_HWPX_MD_PYTHON": "/tmp/python"}, clear=False):
            with patch("server.app.adapters.experimental_hwpx_md.subprocess.run", side_effect=fake_run):
                markdown = experimental_hwpx_md.convert_hwpx(
                    Path("/tmp/source.hwpx"),
                    document_metadata={"issuer_agency": "행정안전부"},
                )

        self.assertEqual(markdown, "ok")
        command = captured["command"]
        self.assertIsInstance(command, list)
        self.assertIn("--metadata-json", command)
        metadata_index = command.index("--metadata-json") + 1
        self.assertIn('"issuer_agency": "행정안전부"', command[metadata_index])

    def test_convert_document_passes_hwp_path_to_converter_cli(self) -> None:
        captured: dict[str, object] = {}

        def fake_run(command, **kwargs):
            captured["command"] = command
            return subprocess.CompletedProcess(command, 0, stdout="# HWP", stderr="")

        with patch.dict(os.environ, {"GOVPRESS_HWPX_MD_PYTHON": "/tmp/python"}, clear=False):
            with patch("server.app.adapters.experimental_hwpx_md.subprocess.run", side_effect=fake_run):
                markdown = experimental_hwpx_md.convert_document(Path("/tmp/source.hwp"))

        self.assertEqual(markdown, "# HWP")
        self.assertEqual(captured["command"][:4], ["/tmp/python", "-m", "govpress_converter", "/tmp/source.hwp"])

    def test_runtime_summary_reports_rhwp_availability(self) -> None:
        def fake_run(command, **kwargs):
            if command == ["/opt/rhwp", "--version"]:
                return subprocess.CompletedProcess(command, 0, stdout="rhwp v0.8.4\n", stderr="")
            return subprocess.CompletedProcess(command, 0, stdout="0.4.10\n", stderr="")

        with patch.dict(
            os.environ,
            {
                "GOVPRESS_HWPX_MD_PYTHON": "/tmp/python",
                "GOVPRESS_RHWP_BIN": "/opt/rhwp",
            },
            clear=False,
        ):
            with patch("server.app.adapters.experimental_hwpx_md.subprocess.run", side_effect=fake_run):
                summary = experimental_hwpx_md.runtime_summary()

        self.assertTrue(summary["available"])
        self.assertTrue(summary["hwp_available"])
        self.assertEqual(summary["rhwp"]["version"], "rhwp v0.8.4")

    def test_convert_hwpx_raises_timeout_with_diagnostics(self) -> None:
        def fake_run(command, **kwargs):
            raise subprocess.TimeoutExpired(command, timeout=600)

        with patch.dict(
            os.environ,
            {
                "GOVPRESS_HWPX_MD_PYTHON": "/tmp/python",
                "GOVPRESS_HWPX_MD_TIMEOUT_SECONDS": "600",
            },
            clear=False,
        ):
            with patch("server.app.adapters.experimental_hwpx_md.subprocess.run", side_effect=fake_run):
                with patch("server.app.adapters.experimental_hwpx_md._document_diagnostics", return_value="section_count=198"):
                    with self.assertRaises(experimental_hwpx_md.HwpxMdConversionTimeout) as context:
                        experimental_hwpx_md.convert_hwpx(Path("/tmp/source.hwpx"))

        self.assertEqual(context.exception.timeout_seconds, 600)
        self.assertEqual(context.exception.diagnostics, "section_count=198")


if __name__ == "__main__":
    unittest.main()
