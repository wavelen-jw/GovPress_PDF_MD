from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from server.app.adapters.policy_briefing_qc import (
    find_storage_job_by_title,
    run_storage_backed_qc_pipeline,
    scaffold_storage_qc_jobs,
)


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

    def test_scaffold_storage_qc_jobs_uses_recent_updated_at_order(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            storage_root = tmp / "storage"
            originals = storage_root / "originals"
            results = storage_root / "results"
            golden = storage_root / "golden"
            originals.mkdir(parents=True)
            results.mkdir(parents=True)
            golden.mkdir(parents=True)

            (originals / "job_old-older.hwpx").write_bytes(b"old")
            (originals / "job_new-newer.hwpx").write_bytes(b"new")
            (results / "job_old.md").write_text("# old\n", encoding="utf-8")
            (results / "job_new.md").write_text("# new\n", encoding="utf-8")

            import sqlite3

            conn = sqlite3.connect(storage_root / "jobs.sqlite3")
            conn.execute(
                """
                CREATE TABLE jobs (
                    job_id TEXT PRIMARY KEY,
                    edit_token TEXT NOT NULL,
                    file_name TEXT NOT NULL,
                    source TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    progress INTEGER NOT NULL DEFAULT 0,
                    error_code TEXT,
                    error_message TEXT,
                    client_request_id TEXT UNIQUE,
                    result_version INTEGER NOT NULL DEFAULT 0,
                    hwpx_table_mode TEXT NOT NULL DEFAULT 'text',
                    original_pdf_path TEXT NOT NULL,
                    final_markdown_path TEXT,
                    edited_markdown_path TEXT,
                    markdown TEXT,
                    html_preview TEXT,
                    markdown_text TEXT,
                    markdown_html TEXT,
                    html_preview_text TEXT,
                    html_preview_html TEXT,
                    title TEXT,
                    department TEXT,
                    edited_markdown TEXT,
                    saved_at TEXT,
                    claimed_by TEXT
                )
                """
            )
            conn.execute(
                "INSERT INTO jobs (job_id, edit_token, file_name, source, status, created_at, updated_at, original_pdf_path, final_markdown_path, title) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                ("job_old", "t1", "older.hwpx", "storage", "done", "2026-04-10T00:00:00Z", "2026-04-10T00:00:00Z", "job_old.pdf", "job_old.md", "Old"),
            )
            conn.execute(
                "INSERT INTO jobs (job_id, edit_token, file_name, source, status, created_at, updated_at, original_pdf_path, final_markdown_path, title) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                ("job_new", "t2", "newer.hwpx", "storage", "done", "2026-04-11T00:00:00Z", "2026-04-12T00:00:00Z", "job_new.pdf", "job_new.md", "New"),
            )
            conn.commit()
            conn.close()

            qc_root = tmp / "qc_root"
            qc_root.mkdir(parents=True)
            seen: list[str] = []

            def fake_scaffold_runner(**kwargs: object) -> str:
                sample_id = str(kwargs["sample_id"])
                seen.append(sample_id)
                sample_dir = qc_root / sample_id
                sample_dir.mkdir(parents=True, exist_ok=True)
                (sample_dir / "meta.json").write_text(
                    json.dumps({"source": "local-file", "sample_status": "scratch"}, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
                return str(sample_dir)

            result = scaffold_storage_qc_jobs(
                gov_md_converter_root="/tmp/gov-md-converter",
                qc_root=qc_root,
                storage_root=storage_root,
                limit=2,
                scaffold_runner=fake_scaffold_runner,
            )

            self.assertEqual(result["scaffolded_count"], 2)
            self.assertEqual(seen, ["storage_job_new", "storage_job_old"])

    def test_scaffold_storage_qc_jobs_filters_requested_job_ids(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            storage_root = tmp / "storage"
            originals = storage_root / "originals"
            results = storage_root / "results"
            golden = storage_root / "golden"
            originals.mkdir(parents=True)
            results.mkdir(parents=True)
            golden.mkdir(parents=True)

            (originals / "job_old-older.hwpx").write_bytes(b"old")
            (originals / "job_new-newer.hwpx").write_bytes(b"new")
            (results / "job_old.md").write_text("# old\n", encoding="utf-8")
            (results / "job_new.md").write_text("# new\n", encoding="utf-8")

            qc_root = tmp / "qc_root"
            qc_root.mkdir(parents=True)
            seen: list[str] = []

            def fake_scaffold_runner(**kwargs: object) -> str:
                sample_id = str(kwargs["sample_id"])
                seen.append(sample_id)
                sample_dir = qc_root / sample_id
                sample_dir.mkdir(parents=True, exist_ok=True)
                (sample_dir / "meta.json").write_text(
                    json.dumps({"source": "local-file", "sample_status": "scratch"}, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
                return str(sample_dir)

            result = scaffold_storage_qc_jobs(
                gov_md_converter_root="/tmp/gov-md-converter",
                qc_root=qc_root,
                storage_root=storage_root,
                limit=1,
                job_ids=["job_old"],
                scaffold_runner=fake_scaffold_runner,
            )

            self.assertEqual(result["job_ids"], ["job_old"])
            self.assertEqual(result["selected_count"], 1)
            self.assertEqual(result["scaffolded_count"], 1)
            self.assertEqual(seen, ["storage_job_old"])

    def test_find_storage_job_by_title_matches_normalized_title(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            storage_root = tmp / "storage"
            originals = storage_root / "originals"
            results = storage_root / "results"
            golden = storage_root / "golden"
            originals.mkdir(parents=True)
            results.mkdir(parents=True)
            golden.mkdir(parents=True)

            (originals / "job_a19baebca8c1-source.hwpx").write_bytes(b"hwpx")
            (results / "job_a19baebca8c1.md").write_text("# rendered\n", encoding="utf-8")

            import sqlite3

            conn = sqlite3.connect(storage_root / "jobs.sqlite3")
            conn.execute(
                """
                CREATE TABLE jobs (
                    job_id TEXT PRIMARY KEY,
                    edit_token TEXT NOT NULL,
                    file_name TEXT NOT NULL,
                    source TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    progress INTEGER NOT NULL DEFAULT 0,
                    error_code TEXT,
                    error_message TEXT,
                    client_request_id TEXT UNIQUE,
                    result_version INTEGER NOT NULL DEFAULT 0,
                    hwpx_table_mode TEXT NOT NULL DEFAULT 'text',
                    original_pdf_path TEXT NOT NULL,
                    final_markdown_path TEXT,
                    edited_markdown_path TEXT,
                    markdown TEXT,
                    html_preview TEXT,
                    markdown_text TEXT,
                    markdown_html TEXT,
                    html_preview_text TEXT,
                    html_preview_html TEXT,
                    title TEXT,
                    department TEXT,
                    edited_markdown TEXT,
                    saved_at TEXT,
                    claimed_by TEXT
                )
                """
            )
            conn.execute(
                "INSERT INTO jobs (job_id, edit_token, file_name, source, status, created_at, updated_at, original_pdf_path, final_markdown_path, title) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    "job_a19baebca8c1",
                    "t1",
                    "sample.hwpx",
                    "storage",
                    "done",
                    "2026-04-10T00:00:00Z",
                    "2026-04-12T00:00:00Z",
                    "job_a19baebca8c1.pdf",
                    "job_a19baebca8c1.md",
                    "주민이 직접 가꾸는 살고 싶은 농촌 농식품부 클린농촌 만들기 본격 가동",
                ),
            )
            conn.commit()
            conn.close()

            artifact = find_storage_job_by_title(
                storage_root=storage_root,
                query="주민이 직접 가꾸는 '살고 싶은 농촌' 농식품부, '클린농촌 만들기' 본격 가동",
            )

            self.assertIsNotNone(artifact)
            assert artifact is not None
            self.assertEqual(artifact.job_id, "job_a19baebca8c1")


if __name__ == "__main__":
    unittest.main()
