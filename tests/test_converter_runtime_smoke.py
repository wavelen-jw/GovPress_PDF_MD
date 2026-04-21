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
            root = Path(tmpdir) / "gov-md-converter"
            root.mkdir()
            module_dir = root / "govpress_converter"
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
                env={**os.environ, "PYTHONPATH": str(root)},
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertIn('"private_engine": true', result.stdout.lower())
            self.assertIn('"backend": "local-root"', result.stdout.lower())
            self.assertIn('"version": "0.2.0"', result.stdout)

    def test_script_rejects_local_root_when_package_backend_is_required(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "gov-md-converter"
            root.mkdir()
            module_dir = root / "govpress_converter"
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
                [sys.executable, "scripts/check_converter_runtime.py", "--require-package-backend"],
                cwd=self.repo_root,
                check=False,
                capture_output=True,
                text=True,
                env={**os.environ, "PYTHONPATH": str(root)},
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Expected installed package backend", result.stderr)

    def test_script_rejects_version_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "gov-md-converter"
            root.mkdir()
            module_dir = root / "govpress_converter"
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
                [sys.executable, "scripts/check_converter_runtime.py", "--expected-version", "0.1.18"],
                cwd=self.repo_root,
                check=False,
                capture_output=True,
                text=True,
                env={**os.environ, "PYTHONPATH": str(root)},
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("does not match expected 0.1.18", result.stderr)

    def test_script_masks_converter_spec_token(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "gov-md-converter"
            root.mkdir()
            module_dir = root / "govpress_converter"
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
            env = {
                **os.environ,
                "PYTHONPATH": str(root),
                "GOVPRESS_CONVERTER_SPEC": "git+https://gho_secret123@github.com/wavelen-jw/gov-md-converter.git@v0.1.18",
            }
            result = subprocess.run(
                [sys.executable, "scripts/check_converter_runtime.py"],
                cwd=self.repo_root,
                check=False,
                capture_output=True,
                text=True,
                env=env,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertIn('"converter_spec": "git+https://***@github.com/wavelen-jw/gov-md-converter.git@v0.1.18"', result.stdout)
            self.assertNotIn("gho_secret123", result.stdout)


if __name__ == "__main__":
    unittest.main()
