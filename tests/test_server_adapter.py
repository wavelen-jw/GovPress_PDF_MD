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

    def test_extract_metadata_reads_press_label_department(self) -> None:
        markdown = (
            "# 「스마트도시 조성・확산 사업」 운영 실태 점검\n\n"
            "국무조정실 보도자료 /\n"
            "보도시점: 배포 후 즉시사용 / 배포 2026. 5. 21.(목) 09:00\n"
        )

        title, department = opendataloader.extract_metadata(markdown)

        self.assertEqual(title, "「스마트도시 조성・확산 사업」 운영 실태 점검")
        self.assertEqual(department, "국무조정실")

    def test_extract_metadata_reads_other_press_label_types(self) -> None:
        markdown = "# 제목\n\n국토교통부 보도참고자료 /\n본문\n"

        _, department = opendataloader.extract_metadata(markdown)

        self.assertEqual(department, "국토교통부")

    def test_extract_metadata_keeps_api_joint_department_name(self) -> None:
        markdown = "# 제목\n\n관계부처 합동 보도자료 /\n본문\n"

        _, department = opendataloader.extract_metadata(markdown)

        self.assertEqual(department, "관계부처 합동")


if __name__ == "__main__":
    unittest.main()
