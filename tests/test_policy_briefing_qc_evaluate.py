from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

GOV_MD_ROOT = Path(__file__).resolve().parents[2] / "gov-md-converter"
if str(GOV_MD_ROOT) not in sys.path:
    sys.path.insert(0, str(GOV_MD_ROOT))

from src.qc_report import build_markdown_summary, evaluate_report


class PolicyBriefingQcEvaluateTests(unittest.TestCase):
    repo_root = Path(__file__).resolve().parents[1]

    def test_evaluate_report_fails_on_review_required_and_regression(self) -> None:
        report = {
            "date": "2026-04-09",
            "summary": {
                "exported_count": 2,
                "scaffolded_count": 2,
                "review_required_count": 1,
                "proposal_count": 1,
                "draft_count": 1,
            },
            "qc_commands": [
                {
                    "command": "regression",
                    "returncode": 1,
                    "payload": [
                        {"sample_id": "a", "passed": False},
                        {"sample_id": "b", "passed": True},
                    ],
                    "output_path": "/tmp/regression.json",
                }
            ],
        }

        exit_code, reasons = evaluate_report(report)

        self.assertEqual(exit_code, 1)
        self.assertIn("review_required_count=1", reasons)
        self.assertIn("regression_returncode=1", reasons)
        self.assertIn("regression_failed_samples=1", reasons)

    def test_build_markdown_summary_lists_commands(self) -> None:
        markdown = build_markdown_summary(
            {
                "date": "2026-04-09",
                "summary": {
                    "exported_count": 1,
                    "scaffolded_count": 1,
                    "review_required_count": 0,
                    "proposal_count": 0,
                    "draft_count": 0,
                },
                "qc_commands": [
                    {
                        "command": "triage",
                        "returncode": 0,
                        "output_path": "/tmp/triage_report.json",
                    }
                ],
            }
        )

        self.assertIn("# Policy Briefing QC Summary", markdown)
        self.assertIn("`triage`", markdown)
        self.assertIn("/tmp/triage_report.json", markdown)

    def test_cli_writes_markdown_and_returns_nonzero_on_failures(self) -> None:
        report = {
            "date": "2026-04-09",
            "summary": {
                "exported_count": 1,
                "scaffolded_count": 1,
                "review_required_count": 1,
                "proposal_count": 1,
                "draft_count": 1,
            },
            "qc_commands": [
                {
                    "command": "triage",
                    "returncode": 0,
                    "payload": {"summary": {"review_required_count": 1}},
                    "output_path": "/tmp/triage_report.json",
                }
            ],
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            report_path = Path(tmpdir) / "pipeline.json"
            summary_path = Path(tmpdir) / "summary.md"
            report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

            result = subprocess.run(
                [
                    sys.executable,
                    str(GOV_MD_ROOT / "scripts" / "evaluate_policy_briefing_qc_report.py"),
                    str(report_path),
                    "--summary-markdown",
                    str(summary_path),
                ],
                cwd=self.repo_root,
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 1)
            self.assertTrue(summary_path.exists())
            self.assertIn("QC evaluation FAIL", result.stdout)


if __name__ == "__main__":
    unittest.main()
