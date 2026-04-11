from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from scripts.send_policy_briefing_qc_telegram import build_telegram_message


class PolicyBriefingQcTelegramTests(unittest.TestCase):
    repo_root = Path(__file__).resolve().parents[1]

    def test_build_telegram_message_includes_top_samples_and_targets(self) -> None:
        message = build_telegram_message(
            {
                "date": "2026-04-09",
                "summary": {
                    "exported_count": 3,
                    "review_required_count": 2,
                    "proposal_count": 1,
                    "draft_count": 1,
                },
                "qc_commands": [
                    {
                        "command": "triage",
                        "payload": {
                            "entries": [
                                {"sample_id": "sample-a", "review_required": True, "risk_score": 9, "sample_status": "scratch"}
                            ]
                        },
                    },
                    {
                        "command": "suggest-fix",
                        "payload": {
                            "proposals": [
                                {"defect_class": "textbox_table_handling", "suggested_files": ["src/table_transformer.py"]}
                            ]
                        },
                    },
                ],
            },
            dashboard_url="https://example.test/dashboard",
            issue_url="https://example.test/issue/1",
        )

        self.assertIn("[Policy Briefing QC] 2026-04-09", message)
        self.assertIn("sample-a", message)
        self.assertIn("textbox_table_handling", message)
        self.assertIn("https://example.test/dashboard", message)

    def test_cli_print_only_outputs_message(self) -> None:
        report = {
            "date": "2026-04-09",
            "summary": {"exported_count": 1, "review_required_count": 0, "proposal_count": 0, "draft_count": 0},
            "qc_commands": [],
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            report_path = Path(tmpdir) / "pipeline.json"
            report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/send_policy_briefing_qc_telegram.py",
                    str(report_path),
                    "--print-only",
                ],
                cwd=self.repo_root,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertIn("[Policy Briefing QC] 2026-04-09", result.stdout)


if __name__ == "__main__":
    unittest.main()
