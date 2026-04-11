from __future__ import annotations

from pathlib import Path
import os
import subprocess
import sys
import tempfile
import textwrap
import unittest


class ConverterRuntimeSmokeTests(unittest.TestCase):
    repo_root = Path(__file__).resolve().parents[1]

    def test_script_reports_unavailable_when_package_missing(self) -> None:
        result = subprocess.run(
            [sys.executable, "scripts/check_converter_runtime.py"],
            cwd=self.repo_root,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn('"available": false', result.stdout.lower())

    def test_script_accepts_private_engine_on_pythonpath(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            module_dir = Path(tmpdir) / "govpress_converter"
            module_dir.mkdir()
            (module_dir / "__init__.py").write_text(
                textwrap.dedent(
                    """
                    __version__ = "0.2.0"

                    def convert_hwpx(path, *, table_mode="text"):
                        return f"{path}:{table_mode}"

                    def convert_pdf(path, timeout=300):
                        return f"{path}:{timeout}"
                    """
                ).strip()
                + "\n",
                encoding="utf-8",
            )
            result = subprocess.run(
                [sys.executable, "scripts/check_converter_runtime.py", "--require-private-engine", "--min-version", "0.1.1"],
                cwd=self.repo_root,
                check=False,
                capture_output=True,
                text=True,
                env={**os.environ, "PYTHONPATH": tmpdir},
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertIn('"private_engine": true', result.stdout.lower())
            self.assertIn('"version": "0.2.0"', result.stdout)


if __name__ == "__main__":
    unittest.main()
