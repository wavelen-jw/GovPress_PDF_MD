from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from scripts.openclaw_ops import (
    build_server_status,
    dispatch_telegram_message,
    parse_server_presets,
    parse_telegram_command,
    qc_failures,
    qc_status,
)


class OpenClawOpsTests(unittest.TestCase):
    repo_root = Path(__file__).resolve().parents[1]

    def _write_report(self, root: Path, day: str, payload: dict[str, object]) -> Path:
        day_dir = root / day
        day_dir.mkdir(parents=True, exist_ok=True)
        path = day_dir / "pipeline_report.json"
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return path

    def test_qc_status_reads_latest_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            self._write_report(
                root,
                "2026-04-11",
                {
                    "date": "2026-04-11",
                    "summary": {"exported_count": 1, "review_required_count": 0, "proposal_count": 0, "draft_count": 0},
                    "qc_commands": [],
                },
            )
            self._write_report(
                root,
                "2026-04-12",
                {
                    "date": "2026-04-12",
                    "summary": {"exported_count": 2, "review_required_count": 1, "proposal_count": 1, "draft_count": 1},
                    "qc_commands": [
                        {"command": "triage", "payload": {"entries": [{"sample_id": "sample-a", "review_required": True, "risk_score": 9, "sample_status": "scratch"}]}},
                        {"command": "suggest-fix", "payload": {"proposals": [{"defect_class": "complex_table", "suggested_files": ["src/table.py"]}]}},
                    ],
                },
            )
            payload = qc_status(root, "latest", dashboard_url="https://example.test/dashboard")
            self.assertEqual(payload["date"], "2026-04-12")
            self.assertEqual(payload["summary"]["review_required_count"], 1)
            self.assertEqual(payload["top_defects"][0]["defect_class"], "complex_table")
            self.assertEqual(payload["dashboard_url"], "https://example.test/dashboard")

    def test_qc_failures_collects_review_and_regression(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            self._write_report(
                root,
                "2026-04-12",
                {
                    "date": "2026-04-12",
                    "summary": {},
                    "qc_commands": [
                        {"command": "triage", "payload": {"entries": [{"sample_id": "sample-a", "review_required": True, "risk_score": 8, "sample_status": "scratch"}]}},
                        {"command": "regression", "payload": [{"sample_id": "sample-a", "passed": False, "findings": [{"id": "x"}]}]},
                        {"command": "suggest-fix", "payload": {"proposals": [{"defect_class": "complex_table", "suggested_files": ["src/table.py"]}]}},
                    ],
                },
            )
            payload = qc_failures(root, "latest")
            self.assertEqual(len(payload["review_required"]), 1)
            self.assertEqual(len(payload["regression_failures"]), 1)
            self.assertEqual(payload["proposals"][0]["defect_class"], "complex_table")

    def test_parse_telegram_command_supports_qc_and_server_commands(self) -> None:
        self.assertEqual(parse_telegram_command("/qc today"), ("qc-status", ["latest"]))
        self.assertEqual(parse_telegram_command("/qc rerun 2026-04-12"), ("qc-rerun", ["2026-04-12"]))
        self.assertEqual(parse_telegram_command("/server status"), ("server-status", []))

    def test_dispatch_rejects_group_scope(self) -> None:
        payload = dispatch_telegram_message(
            "/qc today",
            chat_scope="group",
            export_root=Path("/tmp/none"),
            gov_md_root=Path("/tmp/gov-md"),
            qc_root=Path("/tmp/qc"),
        )
        self.assertFalse(payload["ok"])
        self.assertIn("direct Telegram DMs", payload["message"])

    def test_parse_server_presets_reads_mobile_constants(self) -> None:
        presets, primary_key = parse_server_presets(self.repo_root / "mobile" / "src" / "constants.ts")
        self.assertEqual(primary_key, "serverW")
        self.assertEqual(presets[0].key, "serverW")
        self.assertEqual(presets[0].url, "https://api4.govpress.cloud")

    def test_build_server_status_reports_failover_candidate(self) -> None:
        with mock.patch("scripts.openclaw_ops._fetch_health") as mocked_fetch:
            mocked_fetch.side_effect = [
                {"ok": False, "status": 502, "endpoint": "https://api4.govpress.cloud/health", "error": "bad gateway"},
                {"ok": True, "status": 200, "endpoint": "https://api.govpress.cloud/health", "body": "ok"},
                {"ok": True, "status": 200, "endpoint": "https://api2.govpress.cloud/health", "body": "ok"},
            ]
            payload = build_server_status()
        self.assertEqual(payload["primary_key"], "serverW")
        self.assertFalse(payload["primary_healthy"])
        self.assertTrue(payload["mismatch"])
        self.assertEqual(payload["recommended_url"], "https://api.govpress.cloud")

    def test_cli_telegram_dispatch_prints_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            self._write_report(
                root,
                "2026-04-12",
                {
                    "date": "2026-04-12",
                    "summary": {"exported_count": 2, "review_required_count": 1, "proposal_count": 1, "draft_count": 0},
                    "qc_commands": [],
                },
            )
            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/openclaw_ops.py",
                    "--export-root",
                    str(root),
                    "telegram-dispatch",
                    "--chat-scope",
                    "dm",
                    "--message",
                    "/qc today",
                ],
                cwd=self.repo_root,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertIn("[QC] 2026-04-12", result.stdout)
            self.assertIn("regression_failures=0", result.stdout)

    def test_cli_qc_failures_explains_review_queue_when_regression_is_clean(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            self._write_report(
                root,
                "2026-04-12",
                {
                    "date": "2026-04-12",
                    "summary": {"exported_count": 2, "review_required_count": 1, "proposal_count": 0, "draft_count": 0},
                    "qc_commands": [
                        {"command": "triage", "payload": {"entries": [{"sample_id": "sample-a", "review_required": True, "risk_score": 9, "sample_status": "scratch"}]}},
                        {"command": "regression", "payload": [{"sample_id": "sample-a", "passed": True}]},
                    ],
                },
            )
            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/openclaw_ops.py",
                    "--export-root",
                    str(root),
                    "qc-failures",
                    "--date",
                    "latest",
                ],
                cwd=self.repo_root,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertIn("regression_failures=0", result.stdout)
            self.assertIn("scratch-sample review", result.stdout)


if __name__ == "__main__":
    unittest.main()
