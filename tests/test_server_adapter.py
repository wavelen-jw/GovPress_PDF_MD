from __future__ import annotations

import subprocess
import unittest
from unittest.mock import patch

from server.app.adapters import opendataloader


class OpendataloaderAdapterTests(unittest.TestCase):
    def test_convert_pdf_runs_in_subprocess(self) -> None:
        completed = subprocess.CompletedProcess(
            args=["python", "-m", "server.app.adapters.opendataloader_cli", "/tmp/sample.pdf"],
            returncode=0,
            stdout="# 제목\n\n본문",
            stderr="",
        )
        with patch("server.app.adapters.opendataloader.subprocess.run", return_value=completed) as mock_run:
            markdown = opendataloader.convert_pdf("/tmp/sample.pdf")

        self.assertEqual(markdown, "# 제목\n\n본문")
        command = mock_run.call_args.args[0]
        self.assertEqual(command[1:3], ["-m", "server.app.adapters.opendataloader_cli"])
        self.assertEqual(command[-1], "/tmp/sample.pdf")

    def test_convert_pdf_raises_when_subprocess_fails(self) -> None:
        failed = subprocess.CompletedProcess(
            args=["python", "-m", "server.app.adapters.opendataloader_cli", "/tmp/sample.pdf"],
            returncode=1,
            stdout="",
            stderr="boom",
        )
        with patch("server.app.adapters.opendataloader.subprocess.run", return_value=failed):
            with self.assertRaisesRegex(RuntimeError, "boom"):
                opendataloader.convert_pdf("/tmp/sample.pdf")


if __name__ == "__main__":
    unittest.main()
