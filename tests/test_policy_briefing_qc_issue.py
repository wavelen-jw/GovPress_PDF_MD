from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from scripts.build_policy_briefing_qc_issue import ISSUE_MARKER, build_issue_payload


class PolicyBriefingQcIssueTests(unittest.TestCase):
    repo_root = Path(__file__).resolve().parents[1]

    def test_build_issue_payload_includes_marker_and_samples(self) -> None:
        payload = build_issue_payload(
            {
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
                        "command": "regression",
                        "payload": [
                            {
                                "sample_id": "sample-a",
                                "passed": False,
                                "findings": [{"id": "x"}],
                                "flagged_slices": [
                                    {
                                        "assertion_id": "source_invariant.complex_table",
                                        "category": "tables",
                                        "flag_reason": "Source complex tables exist but markdown has no complex table block",
                                        "source_summary": "source_complex_tables=1, markdown_complex_tables=0",
                                        "markdown_slice": "# 제목\n\n표가 문단으로 무너진 본문 미리보기",
                                    }
                                ],
                                "secondary_signals": {
                                    "pdf_ratio": 0.4123,
                                    "runtime_error": "ValueError: table branch mismatch",
                                },
                            }
                        ],
                    },
                    {
                        "command": "triage",
                        "payload": {
                            "entries": [
                                {
                                    "sample_id": "sample-a",
                                    "review_required": True,
                                    "risk_score": 8,
                                    "sample_status": "scratch",
                                }
                            ]
                        },
                    },
                    {
                        "command": "suggest-fix",
                        "payload": {
                            "proposals": [
                                {
                                    "defect_class": "textbox_table_handling",
                                    "sample_ids": ["sample-a"],
                                    "suggested_files": ["src/table_transformer.py", "src/hwpx_postprocessor.py"],
                                    "suggested_actions": [
                                        "Classify complex tables before textbox/table cleanup collapses them into paragraphs.",
                                        "Add table-signature assertions for the failing complex-table shape.",
                                    ],
                                    "risk_notes": [
                                        "Complex table fixes can easily regress contact tables or appendix tables.",
                                    ],
                                }
                            ]
                        },
                    },
                    {
                        "command": "fix-plan",
                        "payload": {
                            "plans": [
                                {
                                    "defect_class": "textbox_table_handling",
                                    "sample_ids": ["sample-a"],
                                    "search_patterns": ["complex_table", "table_signature", "textbox", "table_transformer"],
                                    "inspect_commands": [
                                        "python3 scripts/run_hwpx_qc.py inspect tests/qc_samples/sample-a",
                                        "rg -n 'complex_table' 'table_signature' 'textbox' src/table_transformer.py src/hwpx_postprocessor.py",
                                    ],
                                    "validation_commands": [
                                        "python3 scripts/run_hwpx_qc.py regression --root tests/qc_samples",
                                    ],
                                    "implementation_notes": [
                                        "Classify complex tables before any cleanup that can flatten them into paragraphs.",
                                    ],
                                }
                            ]
                        },
                    },
                    {
                        "command": "apply-fix-hint",
                        "payload": {
                            "hints": [
                                {
                                    "defect_class": "textbox_table_handling",
                                    "command_sequence": [
                                        "python3 scripts/run_hwpx_qc.py inspect tests/qc_samples/sample-a",
                                        "python3 scripts/run_hwpx_qc.py suggest-fix --root tests/qc_samples",
                                        "python3 scripts/run_hwpx_qc.py patch-template --root tests/qc_samples",
                                        "python3 scripts/run_hwpx_qc.py fix-plan --root tests/qc_samples",
                                    ],
                                    "likely_edit_patterns": [
                                        "classify textbox-derived blocks before table flattening cleanup",
                                    ],
                                    "assertion_update_hints": [
                                        "add source/markdown table_signature assertions for the repaired table path",
                                    ],
                                }
                            ]
                        },
                    },
                    {
                        "command": "auto-patch-draft",
                        "payload": {
                            "drafts": [
                                {
                                    "defect_class": "textbox_table_handling",
                                    "target_modules": ["src/table_transformer.py", "src/hwpx_postprocessor.py"],
                                    "draft_changes": [
                                        "Classify complex tables before textbox/table cleanup collapses them into paragraphs.",
                                        "Route textbox-derived blocks and true table blocks through separate normalization paths.",
                                    ],
                                    "regression_targets": ["tests/test_hwpx_qc.py"],
                                    "post_patch_checks": [
                                        "python3 scripts/run_hwpx_qc.py regression --root tests/qc_samples",
                                    ],
                                }
                            ]
                        },
                    },
                ],
            },
            summary_markdown="# Summary\n",
        )

        self.assertEqual(payload["title"], "[QC] Policy briefing review required for 2026-04-09")
        self.assertIn(ISSUE_MARKER, payload["body"])
        self.assertIn("sample-a", payload["body"])
        self.assertIn("```md", payload["body"])
        self.assertIn("Flagged Slice Preview", payload["body"])
        self.assertIn("source_invariant.complex_table", payload["body"])
        self.assertIn("표가 문단으로 무너진 본문 미리보기", payload["body"])
        self.assertIn("Secondary Signals", payload["body"])
        self.assertIn("pdf_ratio", payload["body"])
        self.assertIn("Immediate Fix Targets", payload["body"])
        self.assertIn("src/table_transformer.py", payload["body"])
        self.assertIn("Patch Draft Summary", payload["body"])
        self.assertIn("Investigation Commands", payload["body"])
        self.assertIn("Copy-Paste Command Sequence", payload["body"])
        self.assertIn("`complex_table`", payload["body"])
        self.assertIn("python3 scripts/run_hwpx_qc.py inspect tests/qc_samples/sample-a", payload["body"])
        self.assertIn("python3 scripts/run_hwpx_qc.py regression --root tests/qc_samples", payload["body"])

    def test_cli_writes_payload_json(self) -> None:
        report = {
            "date": "2026-04-09",
            "summary": {
                "exported_count": 1,
                "scaffolded_count": 1,
                "review_required_count": 1,
                "proposal_count": 1,
                "draft_count": 1,
            },
            "qc_commands": [],
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            report_path = Path(tmpdir) / "pipeline.json"
            output_path = Path(tmpdir) / "issue_payload.json"
            report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/build_policy_briefing_qc_issue.py",
                    str(report_path),
                    "--output",
                    str(output_path),
                ],
                cwd=self.repo_root,
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr)
            payload = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["title"], "[QC] Policy briefing review required for 2026-04-09")


if __name__ == "__main__":
    unittest.main()
