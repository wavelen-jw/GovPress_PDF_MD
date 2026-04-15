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

from src.qc_dashboard import build_dashboard_payload, write_dashboard


class PolicyBriefingQcDashboardTests(unittest.TestCase):
    repo_root = Path(__file__).resolve().parents[1]

    def test_build_dashboard_payload_aggregates_runs(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            state_root = root / "state"
            auto_dir = state_root / "auto_batch_reports"
            auto_dir.mkdir(parents=True)
            (auto_dir / "latest.json").write_text(
                json.dumps(
                    {
                        "batch_id": "batch-1",
                        "started_at": "2026-04-15T22:00:00",
                        "finished_at": "2026-04-15T22:05:00",
                        "samples": [
                            {
                                "sample_id": "sample-auto-1",
                                "title": "자동 샘플 1",
                                "outcome": "awaiting_user",
                                "attempts": 2,
                                "total_duration_ms": 120000,
                                "inspect_total_ms": 10000,
                                "fix_total_ms": 90000,
                                "judge_total_ms": 20000,
                                "bottleneck_stage": "fix",
                                "latest_decision": "pass",
                            }
                        ],
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
            for index, day in enumerate(["2026-04-09", "2026-04-10"], start=1):
                day_dir = root / day
                day_dir.mkdir(parents=True)
                (day_dir / "pipeline_report.json").write_text(
                    json.dumps(
                        {
                            "date": day,
                            "summary": {
                                "exported_count": index,
                                "review_required_count": index - 1,
                                "proposal_count": index,
                                "draft_count": index,
                            },
                            "qc_commands": [
                                {
                                    "command": "triage",
                                    "payload": {
                                        "entries": [
                                            {
                                                "sample_id": f"sample-{index}",
                                                "review_required": index > 1,
                                                "risk_score": 7 + index,
                                                "sample_status": "scratch",
                                            }
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
                        ensure_ascii=False,
                        indent=2,
                    ),
                    encoding="utf-8",
                )

            payload = build_dashboard_payload(root, openclaw_state_root=state_root)
            self.assertEqual(payload["run_count"], 2)
            self.assertEqual(payload["latest_date"], "2026-04-10")
            self.assertEqual(payload["top_defects"][0]["defect_class"], "textbox_table_handling")
            self.assertEqual(payload["auto_qc"]["summary"]["sample_count"], 1)
            self.assertEqual(payload["auto_qc"]["summary"]["slowest_stage"], "fix")

    def test_cli_writes_dashboard_assets(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "exports"
            state_root = Path(tmpdir) / "state"
            auto_dir = state_root / "auto_batch_reports"
            auto_dir.mkdir(parents=True)
            (auto_dir / "latest.json").write_text(
                json.dumps(
                    {
                        "batch_id": "batch-2",
                        "started_at": "2026-04-15T23:00:00",
                        "finished_at": "2026-04-15T23:03:00",
                        "samples": [
                            {
                                "sample_id": "sample-auto-2",
                                "title": "자동 샘플 2",
                                "outcome": "deferred",
                                "attempts": 5,
                                "total_duration_ms": 180000,
                                "inspect_total_ms": 30000,
                                "fix_total_ms": 100000,
                                "judge_total_ms": 50000,
                                "bottleneck_stage": "fix",
                                "latest_decision": "defer",
                            }
                        ],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            day_dir = root / "2026-04-09"
            day_dir.mkdir(parents=True)
            (day_dir / "pipeline_report.json").write_text(
                json.dumps({"date": "2026-04-09", "summary": {}, "qc_commands": []}, ensure_ascii=False),
                encoding="utf-8",
            )
            html_path = Path(tmpdir) / "dashboard" / "index.html"
            json_path = Path(tmpdir) / "dashboard" / "dashboard.json"
            payload = write_dashboard(root, output_html=html_path, output_json=json_path, openclaw_state_root=state_root)
            self.assertEqual(payload["run_count"], 1)
            self.assertTrue(html_path.exists())
            self.assertTrue(json_path.exists())
            self.assertIn("Auto QC Latest Batch", html_path.read_text(encoding="utf-8"))

            result = subprocess.run(
                [
                    sys.executable,
                    str(GOV_MD_ROOT / "scripts" / "build_policy_briefing_qc_dashboard.py"),
                    "--root",
                    str(root),
                    "--output-html",
                    str(html_path),
                    "--output-json",
                    str(json_path),
                    "--openclaw-state-root",
                    str(state_root),
                ],
                cwd=self.repo_root,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)


if __name__ == "__main__":
    unittest.main()
