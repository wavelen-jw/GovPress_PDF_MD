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


if __name__ == "__main__":
    unittest.main()
