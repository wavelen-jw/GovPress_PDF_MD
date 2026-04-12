from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from server.app.adapters.policy_briefing_qc import run_local_hwpx_qc_pipeline


class LocalHwpxQcPipelineTests(unittest.TestCase):
    repo_root = Path(__file__).resolve().parents[1]

    def test_run_local_hwpx_qc_pipeline_wraps_batch_and_qc_results(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_root = Path(tmpdir) / "exports"
            qc_root = Path(tmpdir) / "qc_root"
            qc_root.mkdir(parents=True, exist_ok=True)

            def fake_batch_runner(**_: object) -> dict[str, object]:
                return {
                    "command": "batch-local",
                    "returncode": 0,
                    "stdout": "",
                    "stderr": "",
                    "payload": {
                        "candidate_count": 1,
                        "candidates": [
                            {
                                "sample_id": "sample-a",
                                "source_path": "/tmp/source-a.hwpx",
                                "pdf_path": "/tmp/source-a.pdf",
                                "risk_score": 17,
                                "reasons": ["complex_table x2"],
                                "doc_type": "report",
                            }
                        ],
                    },
                }

            def fake_command_runner(*, command: str, **_: object) -> dict[str, object]:
                payloads = {
                    "regression": [{"sample_id": "sample-a", "passed": False, "findings": [{"id": "x"}]}],
                    "triage": {"summary": {"review_required_count": 1}, "entries": [{"sample_id": "sample-a", "review_required": True}]},
                    "suggest-fix": {"proposal_count": 1, "proposals": [{"defect_class": "complex_table"}]},
                    "patch-template": {"template_count": 1},
                    "fix-plan": {"plan_count": 1},
                    "apply-fix-hint": {"hint_count": 1},
                    "auto-patch-draft": {"draft_count": 1, "drafts": [{"defect_class": "complex_table"}]},
                }
                return {
                    "command": command,
                    "returncode": 0,
                    "stdout": "",
                    "stderr": "",
                    "output_path": None,
                    "payload": payloads[command],
                }

            report = run_local_hwpx_qc_pipeline(
                target_date=__import__("datetime").date(2026, 4, 12),
                output_root=output_root,
                gov_md_converter_root="/tmp/gov-md-converter",
                qc_root=qc_root,
                source_root="/tmp/source-root",
                limit=1,
                batch_runner=fake_batch_runner,
                command_runner=fake_command_runner,
            )

            self.assertEqual(report["export"]["source_kind"], "local_hwpx_corpus")
            self.assertEqual(report["summary"]["exported_count"], 1)
            self.assertEqual(report["summary"]["review_required_count"], 1)
            self.assertEqual(report["summary"]["proposal_count"], 1)
            self.assertEqual(report["summary"]["draft_count"], 1)
            self.assertEqual(report["qc_commands"][0]["command"], "batch-local")

    def test_cli_writes_pipeline_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            source_root = Path(tmpdir) / "source"
            source_root.mkdir(parents=True)
            (source_root / "sample.hwpx").write_bytes(b"hwpx")
            qc_root = Path(tmpdir) / "qc"
            qc_root.mkdir(parents=True)

            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/run_local_hwpx_qc_pipeline.py",
                    "--date",
                    "2026-04-12",
                    "--output-root",
                    str(Path(tmpdir) / "exports"),
                    "--gov-md-converter-root",
                    str((self.repo_root / ".." / "gov-md-converter").resolve()),
                    "--qc-root",
                    str(qc_root),
                    "--source-root",
                    str(source_root),
                    "--limit",
                    "1",
                    "--json",
                ],
                cwd=self.repo_root,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["date"], "2026-04-12")
            self.assertIn("export", payload)


if __name__ == "__main__":
    unittest.main()
