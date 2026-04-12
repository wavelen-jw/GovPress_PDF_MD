from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from server.app.adapters.policy_briefing_qc import run_storage_backed_qc_pipeline


class StorageQcPipelineTests(unittest.TestCase):
    repo_root = Path(__file__).resolve().parents[1]

    def test_run_storage_backed_qc_pipeline_attaches_results_and_golden(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            storage_root = tmp / "storage"
            originals = storage_root / "originals"
            results = storage_root / "results"
            golden = storage_root / "golden"
            originals.mkdir(parents=True)
            results.mkdir(parents=True)
            golden.mkdir(parents=True)

            hwpx_path = originals / "job_abc123-260410 즉시 보도.hwpx"
            pdf_path = originals / "job_abc123-260410 즉시 보도.pdf"
            result_path = results / "job_abc123.md"
            golden_path = golden / "job_abc123.preview.md"
            hwpx_path.write_bytes(b"hwpx")
            pdf_path.write_bytes(b"pdf")
            result_path.write_text("# rendered\n", encoding="utf-8")
            golden_path.write_text("# golden\n", encoding="utf-8")

            qc_root = tmp / "qc_root"
            qc_root.mkdir(parents=True)
            sample_dir = qc_root / "storage_job_abc123"

            def fake_scaffold_runner(**_: object) -> str:
                sample_dir.mkdir(parents=True, exist_ok=True)
                (sample_dir / "meta.json").write_text(
                    json.dumps({"source": "local-file", "sample_status": "scratch"}, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
                return str(sample_dir)

            def fake_command_runner(*, command: str, **_: object) -> dict[str, object]:
                payloads = {
                    "regression": [{"sample_id": "storage_job_abc123", "passed": True, "findings": []}],
                    "triage": {"summary": {"review_required_count": 0}, "entries": []},
                    "suggest-fix": {"proposal_count": 0, "proposals": []},
                    "patch-template": {"template_count": 0},
                    "fix-plan": {"plan_count": 0},
                    "apply-fix-hint": {"hint_count": 0},
                    "auto-patch-draft": {"draft_count": 0, "drafts": []},
                }
                return {
                    "command": command,
                    "returncode": 0,
                    "stdout": "",
                    "stderr": "",
                    "output_path": None,
                    "payload": payloads[command],
                }

            report = run_storage_backed_qc_pipeline(
                target_date=__import__("datetime").date(2026, 4, 12),
                output_root=tmp / "exports",
                gov_md_converter_root="/tmp/gov-md-converter",
                qc_root=qc_root,
                storage_root=storage_root,
                limit=1,
                scaffold_runner=fake_scaffold_runner,
                command_runner=fake_command_runner,
            )

            self.assertEqual(report["export"]["source_kind"], "storage_backed_corpus")
            self.assertEqual(report["summary"]["exported_count"], 1)
            self.assertTrue((sample_dir / "storage_rendered.md").exists())
            self.assertTrue((sample_dir / "golden.md").exists())
            bridge_payload = json.loads((sample_dir / "storage_bridge.json").read_text(encoding="utf-8"))
            self.assertEqual(bridge_payload["job_id"], "job_abc123")
            self.assertEqual(Path(bridge_payload["result_md_path"]).name, "job_abc123.md")
            self.assertEqual(Path(bridge_payload["golden_md_path"]).name, "job_abc123.preview.md")
            meta_payload = json.loads((sample_dir / "meta.json").read_text(encoding="utf-8"))
            self.assertEqual(meta_payload["source"], "govpress-storage")
            self.assertEqual(meta_payload["storage_job_id"], "job_abc123")

    def test_cli_help(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "scripts/run_storage_qc_pipeline.py",
                "--help",
            ],
            cwd=self.repo_root,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("storage-root", result.stdout)


if __name__ == "__main__":
    unittest.main()
