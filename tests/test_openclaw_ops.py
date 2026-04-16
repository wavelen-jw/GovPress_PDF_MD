from __future__ import annotations

import json
import os
import tempfile
from datetime import date
from pathlib import Path
import subprocess
import sys
import unittest
from unittest import mock

from scripts.openclaw_ops import (
    PolicyQueueEntry,
    SampleRecord,
    _drain_qc_command_queue,
    _enqueue_qc_command,
    _ensure_qc_work_branch,
    _format_codex_stream_line,
    _load_session_state,
    _run_auto_current,
    _sample_record,
    build_server_status,
    dispatch_telegram_message,
    format_human,
    parse_server_presets,
    parse_telegram_command,
    qc_failures,
    qc_status,
)


class OpenClawOpsTests(unittest.TestCase):
    repo_root = Path(__file__).resolve().parents[1]

    def _init_git_repo(self, root: Path) -> None:
        subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True, text=True)
        subprocess.run(["git", "config", "user.name", "QC Test"], cwd=root, check=True, capture_output=True, text=True)
        subprocess.run(["git", "config", "user.email", "qc@example.com"], cwd=root, check=True, capture_output=True, text=True)
        (root / "README.md").write_text("init\n", encoding="utf-8")
        subprocess.run(["git", "add", "README.md"], cwd=root, check=True, capture_output=True, text=True)
        subprocess.run(["git", "commit", "-m", "init"], cwd=root, check=True, capture_output=True, text=True)

    def test_format_codex_stream_line_ignores_event_noise(self) -> None:
        self.assertIsNone(_format_codex_stream_line("codex event: turn.started"))
        self.assertIsNone(_format_codex_stream_line('{"type":"thread.started","thread_id":"thread-123"}'))
        self.assertIsNone(
            _format_codex_stream_line(
                '{"type":"item.completed","item":{"type":"tool_call","text":"hidden"}}'
            )
        )
        self.assertEqual(
            _format_codex_stream_line(
                '{"type":"item.completed","item":{"type":"agent_message","text":"중간 메시지"}}'
            ),
            "중간 메시지",
        )

    def test_format_codex_stream_line_ignores_router_errors_and_plaintext_noise(self) -> None:
        self.assertIsNone(
            _format_codex_stream_line(
                '2026-04-12T17:17:00.395491Z ERROR codex_core::tools::router: error=apply_patch verification failed'
            )
        )
        self.assertIsNone(_format_codex_stream_line('Failed to find expected lines in /tmp/file.py:'))
        self.assertIsNone(_format_codex_stream_line('Command exited with code 1'))
        self.assertIsNone(_format_codex_stream_line('if text.startswith("※"):'))

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
            remote_qc_root=Path("/tmp/remote-qc"),
            state_root=Path("/tmp/state"),
        )
        self.assertFalse(payload["ok"])
        self.assertIn("direct Telegram DMs", payload["message"])

    def test_parse_server_presets_reads_mobile_constants(self) -> None:
        presets, primary_key = parse_server_presets(self.repo_root / "mobile" / "src" / "constants.ts")
        self.assertEqual(primary_key, "serverW")
        self.assertEqual(presets[0].key, "serverH")
        self.assertEqual(presets[0].url, "https://api.govpress.cloud")

    def test_ensure_qc_work_branch_creates_and_reuses_daily_branch(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            gov_md_root = Path(tmpdir) / "gov-md"
            state_root = Path(tmpdir) / "state"
            gov_md_root.mkdir(parents=True)
            self._init_git_repo(gov_md_root)

            branch = _ensure_qc_work_branch(
                gov_md_root=gov_md_root,
                state_root=state_root,
                sender_id="6475698942",
            )
            current = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=gov_md_root,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
            self.assertEqual(branch, current)
            self.assertEqual(branch, f"qc/{date.today().isoformat()}")

            branch2 = _ensure_qc_work_branch(
                gov_md_root=gov_md_root,
                state_root=state_root,
                sender_id="6475698942",
            )
            self.assertEqual(branch2, branch)
            state = _load_session_state(state_root, "6475698942")
            self.assertEqual(state["qc_work_branch"], branch)

    def test_build_server_status_reports_failover_candidate(self) -> None:
        with mock.patch("scripts.openclaw_ops._fetch_health") as mocked_fetch:
            mocked_fetch.side_effect = [
                {"ok": True, "status": 200, "endpoint": "https://api.govpress.cloud/health", "body": "ok"},
                {"ok": False, "status": 502, "endpoint": "https://api4.govpress.cloud/health", "error": "bad gateway"},
                {"ok": True, "status": 200, "endpoint": "https://api2.govpress.cloud/health", "body": "ok"},
            ]
            payload = build_server_status()
        self.assertEqual(payload["primary_key"], "serverW")
        self.assertFalse(payload["primary_healthy"])
        self.assertTrue(payload["mismatch"])
        self.assertEqual(payload["recommended_url"], "https://api.govpress.cloud")

    def test_cli_telegram_dispatch_suppresses_stdout_for_dm(self) -> None:
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
            self.assertEqual(result.stdout.strip(), "")

    def test_cli_telegram_dispatch_dm_with_sender_suppresses_stdout(self) -> None:
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
                    'Conversation info (untrusted metadata): {"message_id":"12","sender_id":"6475698942"}\n/qc today',
                ],
                cwd=self.repo_root,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertEqual(result.stdout.strip(), "")

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

    def test_remote_qc_job_list_and_open(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            remote_root = Path(tmpdir) / "storage_batch"
            state_root = Path(tmpdir) / "state"
            gov_md_root = Path(tmpdir) / "gov-md"
            (gov_md_root / "scripts").mkdir(parents=True, exist_ok=True)
            sample_dir = remote_root / "storage_job_abc123"
            sample_dir.mkdir(parents=True)
            (sample_dir / "source.hwpx").write_bytes(b"hwpx")
            (sample_dir / "rendered.md").write_text("rendered", encoding="utf-8")
            (sample_dir / "review.md").write_text("review", encoding="utf-8")
            (sample_dir / "golden.md").write_text("golden", encoding="utf-8")
            (sample_dir / "meta.json").write_text(
                json.dumps({"sample_status": "scratch", "source_hwpx": "job_abc123.hwpx"}, ensure_ascii=False),
                encoding="utf-8",
            )

            queue_entry = PolicyQueueEntry(
                sample=SampleRecord(
                    sample_id="storage_job_abc123",
                    sample_dir=sample_dir,
                    status="scratch",
                    source_name="job_abc123.hwpx",
                    has_golden=True,
                    has_review=True,
                ),
                title="샘플 제목",
                approve_date="2026-04-16 12:00",
                news_item_id="job_abc123",
                review_required=True,
                risk_score=8,
                finding_count=2,
                hard_finding_count=1,
                defect_classes=("complex_table",),
            )
            with mock.patch("scripts.openclaw_ops._scaffold_latest_policy_queue", return_value=[queue_entry]):
                payload = dispatch_telegram_message(
                    'Conversation info (untrusted metadata): {"message_id":"11","sender_id":"6475698942"}\njob 목록 보여줘',
                    chat_scope="dm",
                    export_root=Path(tmpdir),
                    gov_md_root=gov_md_root,
                    qc_root=Path(tmpdir),
                    remote_qc_root=remote_root,
                    state_root=state_root,
                )
            self.assertEqual(payload["command"], "remote-qc-list")
            self.assertEqual(payload["samples"][0]["sample_id"], "storage_job_abc123")
            self.assertEqual(payload["source_kind"], "policy_briefing_latest")

            def fake_run(command, *, cwd, extra_env=None):
                if command[:3] == ["openclaw", "message", "send"]:
                    return {
                        "returncode": 0,
                        "stdout": '{"payload":{"ok":true,"messageId":"m1"}}',
                        "stderr": "",
                        "command": command,
                    }
                return {
                    "returncode": 0,
                    "stdout": str(sample_dir),
                    "stderr": "",
                    "command": command,
                }

            with mock.patch("scripts.openclaw_ops._run_subprocess", side_effect=fake_run):
                opened = dispatch_telegram_message(
                    'Conversation info (untrusted metadata): {"message_id":"12","sender_id":"6475698942"}\nstorage_job_abc123 열어줘',
                    chat_scope="dm",
                    export_root=Path(tmpdir),
                    gov_md_root=gov_md_root,
                    qc_root=Path(tmpdir),
                    remote_qc_root=remote_root,
                    state_root=state_root,
                )
            self.assertEqual(opened["command"], "remote-qc-open")
            self.assertEqual(opened["refresh"]["returncode"], 0)
            self.assertIn("scaffold-local", " ".join(opened["refresh"]["command"]))
            self.assertEqual(len(opened["results"]), 4)
            self.assertTrue(all(item["ok"] for item in opened["results"]))
            state = _load_session_state(state_root, "6475698942")
            self.assertEqual(state["selected_sample_id"], "storage_job_abc123")

    def test_remote_qc_open_auto_scaffolds_missing_storage_sample(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            remote_root = Path(tmpdir) / "storage_batch"
            state_root = Path(tmpdir) / "state"
            gov_md_root = Path(tmpdir) / "gov-md"
            (gov_md_root / "scripts").mkdir(parents=True, exist_ok=True)
            sample_dir = remote_root / "storage_job_abc123"

            def fake_scaffold(**kwargs: object) -> dict[str, object]:
                self.assertEqual(kwargs["job_ids"], ["job_abc123"])
                sample_dir.mkdir(parents=True, exist_ok=True)
                (sample_dir / "source.hwpx").write_bytes(b"hwpx")
                (sample_dir / "rendered.md").write_text("rendered", encoding="utf-8")
                (sample_dir / "review.md").write_text("review", encoding="utf-8")
                (sample_dir / "meta.json").write_text(
                    json.dumps({"sample_status": "scratch", "source_hwpx": "job_abc123.hwpx"}, ensure_ascii=False),
                    encoding="utf-8",
                )
                return {
                    "limit": 1,
                    "job_ids": ["job_abc123"],
                    "selected_count": 1,
                    "scaffolded_count": 1,
                    "items": [{"news_item_id": "job_abc123", "scaffold_sample_dir": str(sample_dir)}],
                }

            def fake_run(command, *, cwd, extra_env=None):
                if command[:3] == ["openclaw", "message", "send"]:
                    return {
                        "returncode": 0,
                        "stdout": '{"payload":{"ok":true,"messageId":"m1"}}',
                        "stderr": "",
                        "command": command,
                    }
                return {
                    "returncode": 0,
                    "stdout": str(sample_dir),
                    "stderr": "",
                    "command": command,
                }

            with mock.patch("scripts.openclaw_ops.scaffold_storage_qc_jobs", side_effect=fake_scaffold) as mocked_scaffold, \
                 mock.patch("scripts.openclaw_ops._run_subprocess", side_effect=fake_run):
                opened = dispatch_telegram_message(
                    'Conversation info (untrusted metadata): {"message_id":"12","sender_id":"6475698942"}\nstorage_job_abc123 열어줘',
                    chat_scope="dm",
                    export_root=Path(tmpdir),
                    gov_md_root=gov_md_root,
                    qc_root=Path(tmpdir),
                    remote_qc_root=remote_root,
                    state_root=state_root,
                )
            self.assertEqual(opened["command"], "remote-qc-open")
            self.assertEqual(opened["sample_id"], "storage_job_abc123")
            self.assertEqual(len(opened["results"]), 3)
            mocked_scaffold.assert_called_once()

    def test_remote_qc_open_by_policy_briefing_title(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            remote_root = Path(tmpdir) / "storage_batch"
            state_root = Path(tmpdir) / "state"
            gov_md_root = Path(tmpdir) / "gov-md"
            (gov_md_root / "scripts").mkdir(parents=True, exist_ok=True)
            sample_dir = remote_root / "policy_briefing_2026_04_13_156754285"
            sample_dir.mkdir(parents=True, exist_ok=True)
            (sample_dir / "source.hwpx").write_bytes(b"hwpx")
            (sample_dir / "rendered.md").write_text("rendered", encoding="utf-8")
            (sample_dir / "review.md").write_text("review", encoding="utf-8")
            (sample_dir / "meta.json").write_text(
                json.dumps({"sample_status": "scratch", "source_hwpx": "policy.hwpx"}, ensure_ascii=False),
                encoding="utf-8",
            )

            def fake_run(command, *, cwd, extra_env=None):
                if command[:3] == ["openclaw", "message", "send"]:
                    return {
                        "returncode": 0,
                        "stdout": '{"payload":{"ok":true,"messageId":"m1"}}',
                        "stderr": "",
                        "command": command,
                    }
                return {
                    "returncode": 0,
                    "stdout": '{"ok":true}',
                    "stderr": "",
                    "command": command,
                }

            with mock.patch(
                "scripts.openclaw_ops._maybe_export_policy_briefing_sample",
                return_value=_sample_record(sample_dir),
            ), \
                 mock.patch("scripts.openclaw_ops._run_subprocess", side_effect=fake_run):
                opened = dispatch_telegram_message(
                    'Conversation info (untrusted metadata): {"message_id":"12","sender_id":"6475698942"}\n국정브리핑 보도자료 \'주민이 직접 가꾸는 \'살고 싶은 농촌\' 농식품부, \'클린농촌 만들기\' 본격 가동\' 를 job으로 열어줘',
                    chat_scope="dm",
                    export_root=Path(tmpdir),
                    gov_md_root=gov_md_root,
                    qc_root=Path(tmpdir),
                    remote_qc_root=remote_root,
                    state_root=state_root,
                )
            self.assertEqual(opened["command"], "remote-qc-open")
            self.assertEqual(opened["sample_id"], "policy_briefing_2026_04_13_156754285")
            self.assertNotIn("telegram_notification", opened)

    def test_remote_qc_open_by_policy_briefing_title_exports_when_storage_misses(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            remote_root = Path(tmpdir) / "storage_batch"
            state_root = Path(tmpdir) / "state"
            gov_md_root = Path(tmpdir) / "gov-md"
            export_root = Path(tmpdir) / "exports"
            (gov_md_root / "scripts").mkdir(parents=True, exist_ok=True)
            sample_dir = remote_root / "policy_briefing_2026_04_13_156700001"

            fake_item = mock.Mock(news_item_id="156700001", approve_date="04/13/2026 09:00:00")

            def fake_export(**kwargs: object) -> dict[str, object]:
                self.assertEqual(kwargs["news_item_ids"], ["156700001"])
                sample_dir.mkdir(parents=True, exist_ok=True)
                (sample_dir / "source.hwpx").write_bytes(b"hwpx")
                (sample_dir / "rendered.md").write_text("rendered", encoding="utf-8")
                (sample_dir / "review.md").write_text("review", encoding="utf-8")
                (sample_dir / "meta.json").write_text(
                    json.dumps({"sample_status": "scratch", "source_hwpx": "policy.hwpx"}, ensure_ascii=False),
                    encoding="utf-8",
                )
                return {
                    "scaffolded_count": 1,
                    "items": [{"news_item_id": "156700001", "scaffold_sample_dir": str(sample_dir)}],
                }

            def fake_run(command, *, cwd, extra_env=None):
                if command[:3] == ["openclaw", "message", "send"]:
                    return {
                        "returncode": 0,
                        "stdout": '{"payload":{"ok":true,"messageId":"m1"}}',
                        "stderr": "",
                        "command": command,
                    }
                return {
                    "returncode": 0,
                    "stdout": str(sample_dir),
                    "stderr": "",
                    "command": command,
                }

            with mock.patch("scripts.openclaw_ops.find_storage_job_by_title", return_value=None), \
                 mock.patch("scripts.openclaw_ops.find_cached_policy_briefing_by_title", return_value=fake_item), \
                 mock.patch("scripts.openclaw_ops.export_policy_briefings_for_qc", side_effect=fake_export), \
                 mock.patch("scripts.openclaw_ops._run_subprocess", side_effect=fake_run):
                opened = dispatch_telegram_message(
                    'Conversation info (untrusted metadata): {"message_id":"12","sender_id":"6475698942"}\n국정브리핑 보도자료 \'없는 storage 제목\' 를 job으로 열어줘',
                    chat_scope="dm",
                    export_root=export_root,
                    gov_md_root=gov_md_root,
                    qc_root=Path(tmpdir),
                    remote_qc_root=remote_root,
                    state_root=state_root,
                )
            self.assertEqual(opened["command"], "remote-qc-open")
            self.assertEqual(opened["sample_id"], "policy_briefing_2026_04_13_156700001")
            self.assertNotIn("telegram_notification", opened)

    def test_remote_qc_open_by_bare_policy_briefing_title(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            remote_root = Path(tmpdir) / "storage_batch"
            state_root = Path(tmpdir) / "state"
            gov_md_root = Path(tmpdir) / "gov-md"
            export_root = Path(tmpdir) / "exports"
            (gov_md_root / "scripts").mkdir(parents=True, exist_ok=True)
            sample_dir = remote_root / "policy_briefing_2026_04_12_156754095"

            fake_item = mock.Mock(news_item_id="156754095", approve_date="04/12/2026 09:00:00")

            def fake_export(**kwargs: object) -> dict[str, object]:
                self.assertEqual(kwargs["news_item_ids"], ["156754095"])
                sample_dir.mkdir(parents=True, exist_ok=True)
                (sample_dir / "source.hwpx").write_bytes(b"hwpx")
                (sample_dir / "rendered.md").write_text("rendered", encoding="utf-8")
                (sample_dir / "review.md").write_text("review", encoding="utf-8")
                (sample_dir / "meta.json").write_text(
                    json.dumps({"sample_status": "scratch", "source_hwpx": "policy.hwpx"}, ensure_ascii=False),
                    encoding="utf-8",
                )
                return {
                    "scaffolded_count": 1,
                    "items": [{"news_item_id": "156754095", "scaffold_sample_dir": str(sample_dir)}],
                }

            def fake_run(command, *, cwd, extra_env=None):
                if command[:3] == ["openclaw", "message", "send"]:
                    return {
                        "returncode": 0,
                        "stdout": '{"payload":{"ok":true,"messageId":"m1"}}',
                        "stderr": "",
                        "command": command,
                    }
                return {
                    "returncode": 0,
                    "stdout": str(sample_dir),
                    "stderr": "",
                    "command": command,
                }

            with mock.patch("scripts.openclaw_ops.find_storage_job_by_title", return_value=None), \
                 mock.patch("scripts.openclaw_ops.find_cached_policy_briefing_by_title", return_value=fake_item), \
                 mock.patch("scripts.openclaw_ops.export_policy_briefings_for_qc", side_effect=fake_export), \
                 mock.patch("scripts.openclaw_ops._run_subprocess", side_effect=fake_run):
                opened = dispatch_telegram_message(
                    'Conversation info (untrusted metadata): {"message_id":"12","sender_id":"6475698942"}\n고유가 피해지원금 4월 27일 지급 시작',
                    chat_scope="dm",
                    export_root=export_root,
                    gov_md_root=gov_md_root,
                    qc_root=Path(tmpdir),
                    remote_qc_root=remote_root,
                    state_root=state_root,
                )
            self.assertEqual(opened["command"], "remote-qc-open")
            self.assertEqual(opened["sample_id"], "policy_briefing_2026_04_12_156754095")
            self.assertNotIn("telegram_notification", opened)

    def test_remote_qc_open_existing_policy_briefing_title_reuses_existing_sample(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            remote_root = Path(tmpdir) / "storage_batch"
            state_root = Path(tmpdir) / "state"
            gov_md_root = Path(tmpdir) / "gov-md"
            export_root = Path(tmpdir) / "exports"
            sample_dir = remote_root / "policy_briefing_2026_04_12_156754095"
            sample_dir.mkdir(parents=True)
            (sample_dir / "source.hwpx").write_bytes(b"PK\x03\x04fake")
            (sample_dir / "rendered.md").write_text("rendered", encoding="utf-8")
            (sample_dir / "review.md").write_text("review", encoding="utf-8")
            (sample_dir / "meta.json").write_text(
                json.dumps({"sample_status": "scratch", "source_hwpx": "source.hwpx"}, ensure_ascii=False),
                encoding="utf-8",
            )

            fake_item = mock.Mock(news_item_id="156754095", approve_date="04/12/2026 09:00:00")

            def fake_run(command, *, cwd, extra_env=None):
                if command[:3] == ["openclaw", "message", "send"]:
                    return {
                        "returncode": 0,
                        "stdout": '{"payload":{"ok":true,"messageId":"m1"}}',
                        "stderr": "",
                        "command": command,
                    }
                return {
                    "returncode": 0,
                    "stdout": '{"ok":true}',
                    "stderr": "",
                    "command": command,
                }

            with mock.patch("scripts.openclaw_ops.find_storage_job_by_title", return_value=None), \
                 mock.patch("scripts.openclaw_ops.find_cached_policy_briefing_by_title", return_value=fake_item), \
                 mock.patch("scripts.openclaw_ops.export_policy_briefings_for_qc") as mocked_export, \
                 mock.patch("scripts.openclaw_ops._run_subprocess", side_effect=fake_run):
                opened = dispatch_telegram_message(
                    'Conversation info (untrusted metadata): {"message_id":"12","sender_id":"6475698942"}\n국정브리핑 보도자료 \'고유가 피해지원금 4월 27일 지급 시작\' 를 job으로 열어줘',
                    chat_scope="dm",
                    export_root=export_root,
                    gov_md_root=gov_md_root,
                    qc_root=Path(tmpdir),
                    remote_qc_root=remote_root,
                    state_root=state_root,
                )
            self.assertEqual(opened["command"], "remote-qc-open")
            self.assertEqual(opened["sample_id"], "policy_briefing_2026_04_12_156754095")
            self.assertEqual(opened["refresh"]["command"][0], "skip-policy-briefing-refresh")
            self.assertNotIn("telegram_notification", opened)
            mocked_export.assert_not_called()

    def test_remote_qc_reopen_policy_briefing_sample_skips_refresh(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            remote_root = Path(tmpdir) / "storage_batch"
            state_root = Path(tmpdir) / "state"
            gov_md_root = Path(tmpdir) / "gov-md"
            sample_dir = remote_root / "policy_briefing_2026_04_13_156754285"
            sample_dir.mkdir(parents=True)
            (sample_dir / "source.hwpx").write_bytes(b"PK\x03\x04fake")
            (sample_dir / "rendered.md").write_text("rendered", encoding="utf-8")
            (sample_dir / "review.md").write_text("review", encoding="utf-8")
            (sample_dir / "meta.json").write_text(
                json.dumps({"sample_status": "scratch", "source_hwpx": "policy.hwpx"}, ensure_ascii=False),
                encoding="utf-8",
            )

            def fake_run(command, *, cwd, extra_env=None):
                if command[:3] == ["openclaw", "message", "send"]:
                    return {
                        "returncode": 0,
                        "stdout": '{"payload":{"ok":true,"messageId":"m1"}}',
                        "stderr": "",
                        "command": command,
                    }
                return {
                    "returncode": 0,
                    "stdout": '{"ok":true}',
                    "stderr": "",
                    "command": command,
                }

            with mock.patch("scripts.openclaw_ops._run_subprocess", side_effect=fake_run):
                opened = dispatch_telegram_message(
                    'Conversation info (untrusted metadata): {"message_id":"12","sender_id":"6475698942"}\npolicy_briefing_2026_04_13_156754285 열어줘',
                    chat_scope="dm",
                    export_root=Path(tmpdir),
                    gov_md_root=gov_md_root,
                    qc_root=Path(tmpdir),
                    remote_qc_root=remote_root,
                    state_root=state_root,
                )
            self.assertEqual(opened["command"], "remote-qc-open")
            self.assertEqual(opened["refresh"]["command"][0], "skip-policy-briefing-refresh")
            self.assertNotIn("telegram_notification", opened)

    def test_remote_qc_golden_text_uses_existing_golden_and_queues_fix(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            remote_root = Path(tmpdir) / "storage_batch"
            state_root = Path(tmpdir) / "state"
            gov_md_root = Path(tmpdir) / "gov-md"
            sample_dir = remote_root / "policy_briefing_2026_04_13_156754285"
            sample_dir.mkdir(parents=True)
            (sample_dir / "source.hwpx").write_bytes(b"PK\x03\x04fake")
            (sample_dir / "rendered.md").write_text("rendered", encoding="utf-8")
            (sample_dir / "review.md").write_text("review", encoding="utf-8")
            (sample_dir / "golden.md").write_text("# golden\n", encoding="utf-8")
            (sample_dir / "meta.json").write_text(
                json.dumps({"sample_status": "scratch", "source_hwpx": "policy.hwpx"}, ensure_ascii=False),
                encoding="utf-8",
            )
            session_dir = state_root / "telegram_qc_sessions"
            session_dir.mkdir(parents=True, exist_ok=True)
            (session_dir / "6475698942.json").write_text(
                json.dumps({"selected_sample_id": sample_dir.name}, ensure_ascii=False),
                encoding="utf-8",
            )
            with mock.patch("scripts.openclaw_ops._rewrite_sample_review"), \
                 mock.patch(
                     "scripts.openclaw_ops._spawn_background_fix",
                     return_value={"command": "remote-qc-fix-queued", "ok": True},
                 ) as mocked_fix:
                payload = dispatch_telegram_message(
                    "golden",
                    chat_scope="dm",
                    export_root=Path(tmpdir),
                    gov_md_root=gov_md_root,
                    qc_root=Path(tmpdir),
                    remote_qc_root=remote_root,
                    state_root=state_root,
                )

            self.assertEqual(payload["command"], "remote-qc-fix-queued")
            self.assertTrue(payload["used_existing_golden"])
            mocked_fix.assert_called_once()

    def test_remote_qc_recent_job_generation_uses_storage_pipeline(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            remote_root = Path(tmpdir) / "storage_batch"
            state_root = Path(tmpdir) / "state"
            gov_md_root = Path(tmpdir) / "gov-md"
            sample_one = remote_root / "policy_briefing_2026_04_15_156755813"
            sample_two = remote_root / "policy_briefing_2026_04_15_156755814"
            entries = [
                PolicyQueueEntry(
                    sample=SampleRecord(
                        sample_id=sample_one.name,
                        sample_dir=sample_one,
                        status="scratch",
                        source_name="sample1.hwpx",
                        has_golden=False,
                        has_review=True,
                    ),
                    title="최근 1",
                    approve_date="2026-04-15 11:00",
                    news_item_id="156755813",
                    review_required=True,
                    risk_score=7,
                    finding_count=1,
                    hard_finding_count=0,
                    defect_classes=(),
                ),
                PolicyQueueEntry(
                    sample=SampleRecord(
                        sample_id=sample_two.name,
                        sample_dir=sample_two,
                        status="scratch",
                        source_name="sample2.hwpx",
                        has_golden=False,
                        has_review=True,
                    ),
                    title="최근 2",
                    approve_date="2026-04-15 12:00",
                    news_item_id="156755814",
                    review_required=True,
                    risk_score=9,
                    finding_count=2,
                    hard_finding_count=1,
                    defect_classes=("contact_table",),
                ),
            ]
            with mock.patch("scripts.openclaw_ops._scaffold_latest_policy_queue", return_value=entries) as mocked_scaffold:
                payload = dispatch_telegram_message(
                    'Conversation info (untrusted metadata): {"message_id":"18","sender_id":"6475698942"}\n국정브리핑 보도자료 최근 10건을 검토할 job으로 생성해줘',
                    chat_scope="dm",
                    export_root=Path(tmpdir),
                    gov_md_root=gov_md_root,
                    qc_root=Path(tmpdir),
                    remote_qc_root=remote_root,
                    state_root=state_root,
                )
            self.assertEqual(payload["command"], "remote-qc-generate-recent-jobs")
            self.assertEqual(payload["scaffolded_count"], 2)
            mocked_scaffold.assert_called_once()
            self.assertEqual(payload["source_kind"], "policy_briefing_latest")
            self.assertIn("recent=10", format_human(payload))

    def test_remote_qc_search_job_numbers_by_partial_title(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            remote_root = Path(tmpdir) / "storage_batch"
            state_root = Path(tmpdir) / "state"
            gov_md_root = Path(tmpdir) / "gov-md"
            sample_dir = remote_root / "policy_briefing_2026_04_15_156755813"
            sample_dir.mkdir(parents=True, exist_ok=True)

            class FakeItem:
                def __init__(self, news_item_id: str, title: str, approve_date: str, department: str = "") -> None:
                    self.news_item_id = news_item_id
                    self.title = title
                    self.approve_date = approve_date
                    self.department = department

            class FakeCatalog:
                def iter_cached_items(self) -> list[object]:
                    return [
                        FakeItem("156755813", "법무부, 의료관광 비자 개선을 통해 지역 특화 웰니스 관광 산업 활성화 가동", "2026-04-15 11:00:00"),
                        FakeItem("156755814", "국민 성장 기금 2,000억원 추가 조성", "2026-04-15 10:00:00"),
                    ]

            with mock.patch("scripts.openclaw_ops._build_policy_catalog", return_value=FakeCatalog()):
                payload = dispatch_telegram_message(
                    'Conversation info (untrusted metadata): {"message_id":"20","sender_id":"6475698942"}\njob 번호 의료관광 비자 찾아줘',
                    chat_scope="dm",
                    export_root=Path(tmpdir),
                    gov_md_root=gov_md_root,
                    qc_root=Path(tmpdir),
                    remote_qc_root=remote_root,
                    state_root=state_root,
                )

            self.assertEqual(payload["command"], "remote-qc-search-jobs")
            self.assertEqual(payload["match_count"], 1)
            self.assertEqual(payload["matches"][0]["news_item_id"], "156755813")
            self.assertEqual(payload["matches"][0]["sample_id"], "policy_briefing_2026_04_15_156755813")
            self.assertTrue(payload["matches"][0]["sample_exists"])

    def test_remote_qc_partial_title_open_creates_job(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            remote_root = Path(tmpdir) / "policy_briefings"
            state_root = Path(tmpdir) / "state"
            gov_md_root = Path(tmpdir) / "gov-md"
            gov_md_root.mkdir(parents=True, exist_ok=True)
            sample_dir = remote_root / "policy_briefing_2026_04_15_156755813"

            def fake_export(*args, **kwargs):
                sample_dir.mkdir(parents=True, exist_ok=True)
                (sample_dir / "source.hwpx").write_bytes(b"hwpx")
                (sample_dir / "rendered.md").write_text("rendered", encoding="utf-8")
                (sample_dir / "review.md").write_text("review", encoding="utf-8")
                (sample_dir / "meta.json").write_text(
                    json.dumps(
                        {
                            "sample_status": "scratch",
                            "title": "법무부, 의료관광 비자 개선을 통해 지역 특화 웰니스 관광 산업 활성화 가동",
                            "approve_date": "2026-04-15 11:00:00",
                            "news_item_id": "156755813",
                            "source_hwpx": "source.hwpx",
                        },
                        ensure_ascii=False,
                    ),
                    encoding="utf-8",
                )
                return {"scaffolded_count": 1}

            class FakeItem:
                news_item_id = "156755813"
                title = "법무부, 의료관광 비자 개선을 통해 지역 특화 웰니스 관광 산업 활성화 가동"
                approve_date = "2026-04-15 11:00:00"
                department = "법무부"

            class FakeCatalog:
                def iter_cached_items(self) -> list[object]:
                    return [FakeItem()]

                def get_cached_item(self, news_item_id: str):
                    return FakeItem() if news_item_id == "156755813" else None

            with mock.patch("scripts.openclaw_ops.PolicyBriefingCatalog", return_value=FakeCatalog()), \
                 mock.patch("scripts.openclaw_ops.export_policy_briefings_for_qc", side_effect=fake_export), \
                 mock.patch("scripts.openclaw_ops.run_gov_md_scaffold"), \
                 mock.patch("scripts.openclaw_ops._run_subprocess") as mocked_run:
                mocked_run.return_value = {
                    "returncode": 0,
                    "stdout": str(sample_dir),
                    "stderr": "",
                    "command": ["python3", "scaffold-local"],
                }
                payload = dispatch_telegram_message(
                    'Conversation info (untrusted metadata): {"message_id":"21","sender_id":"6475698942"}\n국정브리핑 보도자료 의료관광 비자 개선 열어줘',
                    chat_scope="dm",
                    export_root=Path(tmpdir),
                    gov_md_root=gov_md_root,
                    qc_root=Path(tmpdir),
                    remote_qc_root=remote_root,
                    state_root=state_root,
                )

            self.assertEqual(payload["command"], "remote-qc-open")
            self.assertEqual(payload["sample_id"], "policy_briefing_2026_04_15_156755813")

    def test_qc_command_drain_processes_queued_open_sample(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            remote_root = Path(tmpdir) / "storage_batch"
            state_root = Path(tmpdir) / "state"
            gov_md_root = Path(tmpdir) / "gov-md"
            gov_md_root.mkdir(parents=True, exist_ok=True)
            sample_dir = remote_root / "storage_job_abc123"
            sample_dir.mkdir(parents=True, exist_ok=True)
            (sample_dir / "source.hwpx").write_bytes(b"hwpx")
            (sample_dir / "rendered.md").write_text("rendered", encoding="utf-8")
            (sample_dir / "review.md").write_text("review", encoding="utf-8")
            (sample_dir / "meta.json").write_text(
                json.dumps({"sample_status": "scratch", "source_hwpx": "job_abc123.hwpx"}, ensure_ascii=False),
                encoding="utf-8",
            )

            command_id = _enqueue_qc_command(
                state_root=state_root,
                sender_id="6475698942",
                message_id="19",
                chat_scope="dm",
                command_type="open_sample",
                sample_id="storage_job_abc123",
                payload={"sample_id": "storage_job_abc123"},
                dedupe_key="test-open-sample",
            )

            with mock.patch("scripts.openclaw_ops._run_subprocess") as mocked_run:
                mocked_run.return_value = {
                    "returncode": 0,
                    "stdout": str(sample_dir),
                    "stderr": "",
                    "command": ["python3", "scaffold-local"],
                }
                payload = _drain_qc_command_queue(
                    state_root=state_root,
                    export_root=Path(tmpdir),
                    gov_md_root=gov_md_root,
                    qc_root=Path(tmpdir),
                    remote_qc_root=remote_root,
                    sender_id="6475698942",
                    max_commands=5,
                )

            self.assertEqual(payload["command"], "remote-qc-command-drain")
            self.assertEqual(payload["processed_count"], 1)
            self.assertEqual(payload["results"][0]["id"], command_id)
            state = _load_session_state(state_root, "6475698942")
            self.assertEqual(state["selected_sample_id"], "storage_job_abc123")

    def test_qc_command_enqueue_dedupes_same_message_and_command(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            state_root = Path(tmpdir) / "state"
            first_id = _enqueue_qc_command(
                state_root=state_root,
                sender_id="6475698942",
                message_id="42",
                chat_scope="dm",
                command_type="open_sample",
                sample_id="storage_job_abc123",
                payload={"sample_id": "storage_job_abc123"},
                dedupe_key="6475698942:42:open_sample",
            )
            second_id = _enqueue_qc_command(
                state_root=state_root,
                sender_id="6475698942",
                message_id="42",
                chat_scope="dm",
                command_type="open_sample",
                sample_id="storage_job_abc123",
                payload={"sample_id": "storage_job_abc123"},
                dedupe_key="6475698942:42:open_sample",
            )

            self.assertEqual(first_id, second_id)

    def test_remote_qc_rejects_unsupported_freeform_in_strict_mode(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            payload = dispatch_telegram_message(
                'Conversation info (untrusted metadata): {"message_id":"77","sender_id":"6475698942"}\n안녕',
                chat_scope="dm",
                export_root=Path(tmpdir),
                gov_md_root=Path(tmpdir),
                qc_root=Path(tmpdir),
                remote_qc_root=Path(tmpdir) / "storage_batch",
                state_root=Path(tmpdir) / "state",
            )
        self.assertEqual(payload["command"], "remote-qc-unsupported")
        self.assertFalse(payload["ok"])

    def test_remote_qc_falls_back_to_default_sender_when_metadata_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            remote_root = Path(tmpdir) / "storage_batch"
            state_root = Path(tmpdir) / "state"
            sample_dir = remote_root / "storage_job_abc123"
            sample_dir.mkdir(parents=True)
            (sample_dir / "source.hwpx").write_bytes(b"hwpx")
            (sample_dir / "rendered.md").write_text("rendered", encoding="utf-8")
            (sample_dir / "review.md").write_text("review", encoding="utf-8")
            (sample_dir / "meta.json").write_text(
                json.dumps({"sample_status": "scratch", "source_hwpx": "job_abc123.hwpx"}, ensure_ascii=False),
                encoding="utf-8",
            )

            with mock.patch.dict(os.environ, {"GOVPRESS_QC_DEFAULT_SENDER_ID": "6475698942"}):
                from importlib import reload
                import scripts.openclaw_ops as openclaw_ops
                reload(openclaw_ops)
                payload = openclaw_ops.dispatch_telegram_message(
                    "job 목록 보여줘",
                    chat_scope="dm",
                    export_root=Path(tmpdir),
                    gov_md_root=Path(tmpdir),
                    qc_root=Path(tmpdir),
                    remote_qc_root=remote_root,
                    state_root=state_root,
                )
            self.assertEqual(payload["command"], "remote-qc-list")

    def test_remote_qc_falls_back_to_single_session_file_when_sender_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            remote_root = Path(tmpdir) / "storage_batch"
            state_root = Path(tmpdir) / "state"
            sample_dir = remote_root / "storage_job_abc123"
            sample_dir.mkdir(parents=True)
            (sample_dir / "source.hwpx").write_bytes(b"hwpx")
            (sample_dir / "rendered.md").write_text("rendered", encoding="utf-8")
            (sample_dir / "review.md").write_text("review", encoding="utf-8")
            (sample_dir / "meta.json").write_text(
                json.dumps({"sample_status": "scratch", "source_hwpx": "job_abc123.hwpx"}, ensure_ascii=False),
                encoding="utf-8",
            )
            session_dir = state_root / "telegram_qc_sessions"
            session_dir.mkdir(parents=True, exist_ok=True)
            (session_dir / "6475698942.json").write_text(
                json.dumps({"selected_sample_id": "storage_job_abc123"}, ensure_ascii=False),
                encoding="utf-8",
            )

            payload = dispatch_telegram_message(
                "job 목록 보여줘",
                chat_scope="dm",
                export_root=Path(tmpdir),
                gov_md_root=Path(tmpdir),
                qc_root=Path(tmpdir),
                remote_qc_root=remote_root,
                state_root=state_root,
            )
            self.assertEqual(payload["command"], "remote-qc-list")

    def test_remote_qc_file_send_uses_openclaw_message_send(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            remote_root = Path(tmpdir) / "storage_batch"
            state_root = Path(tmpdir) / "state"
            sample_dir = remote_root / "storage_job_abc123"
            sample_dir.mkdir(parents=True)
            (sample_dir / "source.hwpx").write_bytes(b"hwpx")
            (sample_dir / "rendered.md").write_text("rendered", encoding="utf-8")
            (sample_dir / "review.md").write_text("review", encoding="utf-8")
            (sample_dir / "meta.json").write_text(json.dumps({"sample_status": "scratch"}, ensure_ascii=False), encoding="utf-8")
            state_root.mkdir(parents=True, exist_ok=True)
            (state_root / "telegram_qc_sessions").mkdir(parents=True, exist_ok=True)
            (state_root / "telegram_qc_sessions" / "6475698942.json").write_text(
                json.dumps({"selected_sample_id": "storage_job_abc123", "selected_sample_dir": str(sample_dir)}, ensure_ascii=False),
                encoding="utf-8",
            )

            with mock.patch("scripts.openclaw_ops._run_subprocess") as mocked_run:
                mocked_run.return_value = {"returncode": 0, "stdout": "ok", "stderr": "", "command": ["openclaw"]}
                payload = dispatch_telegram_message(
                    'Conversation info (untrusted metadata): {"message_id":"13","sender_id":"6475698942"}\nreview 보내줘',
                    chat_scope="dm",
                    export_root=Path(tmpdir),
                    gov_md_root=Path(tmpdir),
                    qc_root=Path(tmpdir),
                    remote_qc_root=remote_root,
                    state_root=state_root,
                )
            self.assertEqual(payload["command"], "remote-qc-send-files")
            self.assertEqual(len(payload["results"]), 1)
            self.assertIn("--media", mocked_run.call_args.args[0])

    def test_remote_qc_fix_takes_priority_over_source_keyword(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            remote_root = Path(tmpdir) / "storage_batch"
            state_root = Path(tmpdir) / "state"
            gov_md_root = Path(tmpdir) / "gov-md"
            gov_md_root.mkdir(parents=True)
            self._init_git_repo(gov_md_root)
            sample_dir = remote_root / "storage_job_abc123"
            sample_dir.mkdir(parents=True)
            (sample_dir / "source.hwpx").write_bytes(b"hwpx")
            (sample_dir / "rendered.md").write_text("rendered", encoding="utf-8")
            (sample_dir / "review.md").write_text("review", encoding="utf-8")
            (sample_dir / "meta.json").write_text(json.dumps({"sample_status": "scratch"}, ensure_ascii=False), encoding="utf-8")
            (state_root / "telegram_qc_sessions").mkdir(parents=True, exist_ok=True)
            (state_root / "telegram_qc_sessions" / "6475698942.json").write_text(
                json.dumps({"selected_sample_id": "storage_job_abc123", "selected_sample_dir": str(sample_dir)}, ensure_ascii=False),
                encoding="utf-8",
            )

            def fake_run(command, *, cwd, extra_env=None):
                if command[:3] == ["openclaw", "message", "send"]:
                    return {
                        "returncode": 0,
                        "stdout": '{"payload":{"ok":true,"messageId":"m1"}}',
                        "stderr": "",
                        "command": command,
                    }
                raise AssertionError("unexpected command")

            def fake_codex_stream(command, *, cwd, on_update=None):
                output_index = command.index("-o") + 1
                Path(command[output_index]).write_text(
                    "ground rule\nscope\nimplementation result\nremaining diff",
                    encoding="utf-8",
                )
                return {
                    "returncode": 0,
                    "stdout": '{"type":"thread.started","thread_id":"thread-123"}',
                    "stderr": "",
                    "command": command,
                }

            with mock.patch("scripts.openclaw_ops._run_subprocess", side_effect=fake_run), \
                 mock.patch("scripts.openclaw_ops._run_codex_with_streaming", side_effect=fake_codex_stream):
                payload = dispatch_telegram_message(
                    'Conversation info (untrusted metadata): {"message_id":"99","sender_id":"6475698942"}\n수정: 원문에서 한줄이므로 분리하면 안됨',
                    chat_scope="dm",
                    export_root=Path(tmpdir),
                    gov_md_root=gov_md_root,
                    qc_root=Path(tmpdir),
                    remote_qc_root=remote_root,
                    state_root=state_root,
                )
            self.assertEqual(payload["command"], "remote-qc-fix-queued")

    def test_remote_qc_golden_upload_triggers_fix_flow(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            remote_root = Path(tmpdir) / "storage_batch"
            state_root = Path(tmpdir) / "state"
            gov_md_root = Path(tmpdir) / "gov-md"
            gov_md_root.mkdir(parents=True)
            self._init_git_repo(gov_md_root)
            sample_dir = remote_root / "storage_job_abc123"
            sample_dir.mkdir(parents=True)
            (sample_dir / "source.hwpx").write_bytes(b"hwpx")
            (sample_dir / "rendered.md").write_text("rendered", encoding="utf-8")
            (sample_dir / "review.md").write_text("review", encoding="utf-8")
            (sample_dir / "meta.json").write_text(json.dumps({"sample_status": "scratch"}, ensure_ascii=False), encoding="utf-8")
            (state_root / "telegram_qc_sessions").mkdir(parents=True, exist_ok=True)
            (state_root / "telegram_qc_sessions" / "6475698942.json").write_text(
                json.dumps({"selected_sample_id": "storage_job_abc123", "selected_sample_dir": str(sample_dir)}, ensure_ascii=False),
                encoding="utf-8",
            )
            uploaded = Path(tmpdir) / "uploaded.md"
            uploaded.write_text("# golden", encoding="utf-8")

            def fake_run(command, *, cwd, extra_env=None):
                if command[:3] == ["openclaw", "message", "send"]:
                    return {
                        "returncode": 0,
                        "stdout": '{"payload":{"ok":true,"messageId":"m1"}}',
                        "stderr": "",
                        "command": command,
                    }
                raise AssertionError("unexpected command")

            with mock.patch("scripts.openclaw_ops._rewrite_sample_review") as mocked_rewrite, \
                 mock.patch("scripts.openclaw_ops._run_subprocess", side_effect=fake_run), \
                 mock.patch("scripts.openclaw_ops._spawn_background_fix") as mocked_fix:
                mocked_fix.return_value = {"command": "remote-qc-fix-queued", "ok": True, "pid": 123}
                payload = dispatch_telegram_message(
                    f'[media attached: {uploaded}]\nConversation info (untrusted metadata): {{"message_id":"14","sender_id":"6475698942"}}',
                    chat_scope="dm",
                    export_root=Path(tmpdir),
                    gov_md_root=gov_md_root,
                    qc_root=Path(tmpdir),
                    remote_qc_root=remote_root,
                    state_root=state_root,
                )
            self.assertEqual(payload["command"], "remote-qc-fix-queued")
            self.assertEqual(payload["golden_upload"]["command"], "remote-qc-upload-golden")
            self.assertEqual((sample_dir / "golden.md").read_text(encoding="utf-8"), "# golden")
            mocked_rewrite.assert_called_once()
            mocked_fix.assert_called_once()

    def test_remote_qc_pass_uses_promote(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            remote_root = Path(tmpdir) / "storage_batch"
            state_root = Path(tmpdir) / "state"
            sample_dir = remote_root / "storage_job_abc123"
            sample_dir.mkdir(parents=True)
            (sample_dir / "source.hwpx").write_bytes(b"hwpx")
            (sample_dir / "rendered.md").write_text("rendered", encoding="utf-8")
            (sample_dir / "review.md").write_text("review", encoding="utf-8")
            (sample_dir / "meta.json").write_text(json.dumps({"sample_status": "scratch"}, ensure_ascii=False), encoding="utf-8")
            (state_root / "telegram_qc_sessions").mkdir(parents=True, exist_ok=True)
            (state_root / "telegram_qc_sessions" / "6475698942.json").write_text(
                json.dumps({"selected_sample_id": "storage_job_abc123", "selected_sample_dir": str(sample_dir)}, ensure_ascii=False),
                encoding="utf-8",
            )

            with mock.patch("scripts.openclaw_ops.qc_promote") as mocked_promote:
                mocked_promote.return_value = {"command": "qc-promote", "sample_id": "storage_job_abc123", "returncode": 0, "stdout": "ok", "stderr": ""}
                payload = dispatch_telegram_message(
                    'Conversation info (untrusted metadata): {"message_id":"15","sender_id":"6475698942"}\n통과',
                    chat_scope="dm",
                    export_root=Path(tmpdir),
                    gov_md_root=Path(tmpdir),
                    qc_root=Path(tmpdir),
                    remote_qc_root=remote_root,
                    state_root=state_root,
                )
            self.assertEqual(payload["command"], "remote-qc-pass")
            self.assertIn("storage_job_abc123", format_human(payload))

    def test_remote_qc_fix_handoff_uses_worker_agent(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            remote_root = Path(tmpdir) / "storage_batch"
            state_root = Path(tmpdir) / "state"
            gov_md_root = Path(tmpdir) / "gov-md"
            sample_dir = remote_root / "storage_job_abc123"
            sample_dir.mkdir(parents=True)
            (sample_dir / "source.hwpx").write_bytes(b"hwpx")
            (sample_dir / "rendered.md").write_text("rendered", encoding="utf-8")
            (sample_dir / "review.md").write_text("review", encoding="utf-8")
            (sample_dir / "golden.md").write_text("golden", encoding="utf-8")
            (sample_dir / "meta.json").write_text(json.dumps({"sample_status": "scratch"}, ensure_ascii=False), encoding="utf-8")
            (state_root / "telegram_qc_sessions").mkdir(parents=True, exist_ok=True)
            (state_root / "telegram_qc_sessions" / "6475698942.json").write_text(
                json.dumps({"selected_sample_id": "storage_job_abc123", "selected_sample_dir": str(sample_dir)}, ensure_ascii=False),
                encoding="utf-8",
            )

            def fake_run(command, *, cwd, extra_env=None):
                if command[:3] == ["openclaw", "message", "send"]:
                    return {
                        "returncode": 0,
                        "stdout": '{"payload":{"ok":true,"messageId":"m1"}}',
                        "stderr": "",
                        "command": command,
                    }
                raise AssertionError("unexpected command")

            with mock.patch("scripts.openclaw_ops._run_subprocess", side_effect=fake_run) as mocked_run, \
                 mock.patch(
                     "scripts.openclaw_ops._spawn_background_fix",
                     return_value={"command": "remote-qc-fix-queued", "sample_id": "storage_job_abc123", "pid": 12345, "ok": True},
                 ) as mocked_spawn:
                payload = dispatch_telegram_message(
                    'Conversation info (untrusted metadata): {"message_id":"16","sender_id":"6475698942"}\n수정: 표가 깨짐',
                    chat_scope="dm",
                    export_root=Path(tmpdir),
                    gov_md_root=gov_md_root,
                    qc_root=Path(tmpdir),
                    remote_qc_root=remote_root,
                    state_root=state_root,
                )
            self.assertEqual(payload["command"], "remote-qc-fix-queued")
            self.assertEqual(payload["pid"], 12345)
            mocked_spawn.assert_called_once()
            mocked_run.assert_not_called()

    def test_remote_qc_fix_handoff_resumes_existing_batch_session(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            remote_root = Path(tmpdir) / "storage_batch"
            state_root = Path(tmpdir) / "state"
            gov_md_root = Path(tmpdir) / "gov-md"
            gov_md_root.mkdir(parents=True)
            self._init_git_repo(gov_md_root)
            sample_dir = remote_root / "storage_job_abc123"
            sample_dir.mkdir(parents=True)
            (sample_dir / "source.hwpx").write_bytes(b"hwpx")
            (sample_dir / "rendered.md").write_text("rendered", encoding="utf-8")
            (sample_dir / "review.md").write_text("review", encoding="utf-8")
            (sample_dir / "meta.json").write_text(json.dumps({"sample_status": "scratch"}, ensure_ascii=False), encoding="utf-8")
            (state_root / "telegram_qc_sessions").mkdir(parents=True, exist_ok=True)
            (state_root / "telegram_qc_sessions" / "6475698942.json").write_text(
                json.dumps(
                    {
                        "selected_sample_id": "storage_job_abc123",
                        "selected_sample_dir": str(sample_dir),
                        "active_batch_id": "2026-04-13:storage_batch",
                        "codex_thread_id": "thread-123",
                        "batch_turn_count": 1,
                        "batch_sample_ids": ["storage_job_abc123"],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            def fake_run(command, *, cwd, extra_env=None):
                if command[:3] == ["openclaw", "message", "send"]:
                    return {
                        "returncode": 0,
                        "stdout": '{"payload":{"ok":true,"messageId":"m1"}}',
                        "stderr": "",
                        "command": command,
                    }
                raise AssertionError("unexpected command")

            def fake_codex_stream(command, *, cwd, on_update=None):
                output_index = command.index("-o") + 1
                Path(command[output_index]).write_text(
                    "ground rule\nscope\nimplementation result\nremaining diff",
                    encoding="utf-8",
                )
                if on_update is not None:
                    on_update("codex event: resumed")
                return {
                    "returncode": 0,
                    "stdout": "",
                    "stderr": "",
                    "command": command,
                }

            with mock.patch("scripts.openclaw_ops._run_subprocess", side_effect=fake_run) as mocked_run, \
                 mock.patch("scripts.openclaw_ops._run_codex_with_streaming", side_effect=fake_codex_stream):
                payload = dispatch_telegram_message(
                    'Conversation info (untrusted metadata): {"message_id":"17","sender_id":"6475698942"}\n수정: 다시 봐줘',
                    chat_scope="dm",
                    export_root=Path(tmpdir),
                    gov_md_root=gov_md_root,
                    qc_root=Path(tmpdir),
                    remote_qc_root=remote_root,
                    state_root=state_root,
                )
            self.assertEqual(payload["command"], "remote-qc-fix-queued")
            self.assertIn("pid", payload)

    def test_remote_qc_auto_start_builds_review_required_queue(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            remote_root = Path(tmpdir) / "policy"
            state_root = Path(tmpdir) / "state"
            gov_md_root = Path(tmpdir) / "gov-md"
            gov_md_root.mkdir(parents=True)
            self._init_git_repo(gov_md_root)
            s1 = remote_root / "policy_briefing_2026_04_15_1"
            s2 = remote_root / "policy_briefing_2026_04_15_2"
            s1.mkdir(parents=True)
            s2.mkdir(parents=True)
            for sample_dir in (s1, s2):
                (sample_dir / "source.hwpx").write_bytes(b"hwpx")
                (sample_dir / "review.md").write_text("review", encoding="utf-8")
                (sample_dir / "rendered.md").write_text("rendered", encoding="utf-8")
                (sample_dir / "meta.json").write_text(json.dumps({"sample_status": "scratch"}, ensure_ascii=False), encoding="utf-8")

            entries = [
                mock.Mock(
                    sample=_sample_record(s2),
                    news_item_id="2",
                    review_required=True,
                    risk_score=9,
                    finding_count=4,
                    hard_finding_count=1,
                    defect_classes=("title",),
                    title="둘째 제목",
                ),
                mock.Mock(
                    sample=_sample_record(s1),
                    news_item_id="1",
                    review_required=True,
                    risk_score=7,
                    finding_count=2,
                    hard_finding_count=0,
                    defect_classes=("table",),
                    title="첫째 제목",
                ),
            ]
            with mock.patch("scripts.openclaw_ops._auto_queue_entries", return_value=entries), \
                 mock.patch(
                     "scripts.openclaw_ops._spawn_background_auto_run",
                     return_value={"command": "remote-qc-auto-queued", "pid": 222, "ok": True},
                 ):
                payload = dispatch_telegram_message(
                    'Conversation info (untrusted metadata): {"message_id":"20","sender_id":"6475698942"}\n최근 10건 job 뽑아서 qc 시작',
                    chat_scope="dm",
                    export_root=Path(tmpdir),
                    gov_md_root=gov_md_root,
                    qc_root=remote_root,
                    remote_qc_root=remote_root,
                    state_root=state_root,
                )
            self.assertEqual(payload["command"], "remote-qc-auto-start")
            self.assertEqual(payload["queue_count"], 2)
            self.assertEqual(payload["current_sample_id"], "policy_briefing_2026_04_15_2")
            self.assertEqual(payload["qc_work_branch"], f"qc/{date.today().isoformat()}")
            self.assertEqual(payload["queue_preview"][0]["title"], "둘째 제목")
            state = _load_session_state(state_root, "6475698942")
            self.assertTrue(state["auto_mode"])
            self.assertEqual(state["auto_queue_sample_ids"][0], "policy_briefing_2026_04_15_2")
            self.assertEqual(state["qc_work_branch"], payload["qc_work_branch"])

    def test_remote_qc_auto_status_reports_current_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            state_root = Path(tmpdir) / "state"
            (state_root / "telegram_qc_sessions").mkdir(parents=True, exist_ok=True)
            (state_root / "telegram_qc_sessions" / "6475698942.json").write_text(
                json.dumps(
                    {
                        "auto_mode": True,
                        "auto_batch_id": "batch-1",
                        "auto_queue_sample_ids": ["policy_briefing_2026_04_15_1"],
                        "auto_queue_index": 0,
                        "auto_current_sample_id": "policy_briefing_2026_04_15_1",
                        "auto_current_attempt": 2,
                        "auto_current_status": "awaiting_user",
                        "auto_results": [],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            payload = dispatch_telegram_message(
                'Conversation info (untrusted metadata): {"message_id":"21","sender_id":"6475698942"}\n현재 qc 상태',
                chat_scope="dm",
                export_root=Path(tmpdir),
                gov_md_root=Path(tmpdir),
                qc_root=Path(tmpdir),
                remote_qc_root=Path(tmpdir),
                state_root=state_root,
            )
            self.assertEqual(payload["command"], "remote-qc-auto-status")
            self.assertEqual(payload["current_status"], "awaiting_user")
            self.assertIn("pass=0", format_human(payload))
            self.assertIn("awaiting_user", format_human(payload))

    def test_remote_qc_auto_run_current_stops_on_ai_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            remote_root = Path(tmpdir) / "policy"
            state_root = Path(tmpdir) / "state"
            gov_md_root = Path(tmpdir) / "gov-md"
            gov_md_root.mkdir(parents=True)
            self._init_git_repo(gov_md_root)
            sample_dir = remote_root / "policy_briefing_2026_04_15_1"
            sample_dir.mkdir(parents=True)
            (sample_dir / "source.hwpx").write_bytes(b"hwpx")
            (sample_dir / "review.md").write_text("review", encoding="utf-8")
            (sample_dir / "rendered.md").write_text("rendered", encoding="utf-8")
            (sample_dir / "meta.json").write_text(json.dumps({"sample_status": "scratch"}, ensure_ascii=False), encoding="utf-8")
            (state_root / "telegram_qc_sessions").mkdir(parents=True, exist_ok=True)
            (state_root / "telegram_qc_sessions" / "6475698942.json").write_text(
                json.dumps(
                    {
                        "auto_mode": True,
                        "auto_batch_id": "batch-1",
                        "auto_queue_sample_ids": [sample_dir.name],
                        "auto_queue_index": 0,
                        "auto_current_sample_id": sample_dir.name,
                        "auto_current_attempt": 0,
                        "auto_current_status": "queued",
                        "auto_max_attempts": 5,
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            with mock.patch("scripts.openclaw_ops._send_telegram_text") as mocked_send, \
                 mock.patch("scripts.openclaw_ops._send_requested_files", return_value=[]), \
                 mock.patch(
                     "scripts.openclaw_ops._handle_fix_request",
                     return_value={"worker_text": "implementation result", "returncode": 0},
                 ), \
                 mock.patch(
                     "scripts.openclaw_ops._run_hwpx_qc_inspect",
                     side_effect=[
                         {"returncode": 0, "payload": {"passed": False, "findings": [{"message": "title"}]}},
                         {"returncode": 0, "payload": {"passed": True, "findings": []}},
                     ],
                 ), \
                 mock.patch(
                     "scripts.openclaw_ops._run_auto_judge",
                     return_value={
                         "returncode": 0,
                         "judge": mock.Mock(
                             decision="pass",
                             confidence="high",
                             user_summary="AI pass",
                             next_fix_instruction="",
                             blocking_findings=(),
                         ),
                     },
                 ):
                payload = _run_auto_current(
                    sender_id="6475698942",
                    message_id="22",
                    export_root=Path(tmpdir),
                    gov_md_root=gov_md_root,
                    remote_qc_root=remote_root,
                    state_root=state_root,
                )
            self.assertEqual(payload["status"], "awaiting_user")
            state = _load_session_state(state_root, "6475698942")
            self.assertEqual(state["auto_current_status"], "awaiting_user")
            self.assertEqual(state["auto_current_attempt"], 1)
            report_path = Path(state["auto_batch_report_path"])
            self.assertTrue(report_path.exists())
            report = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual(report["samples"][0]["sample_id"], sample_dir.name)
            self.assertEqual(report["samples"][0]["outcome"], "awaiting_user")
            self.assertGreaterEqual(report["samples"][0]["fix_total_ms"], 0)
            joined_messages = "\n".join(call.kwargs.get("message", "") for call in mocked_send.call_args_list)
            self.assertIn("[QC Auto] 1/1", joined_messages)
            self.assertIn("deterministic gate: inspect=PASS", joined_messages)
            self.assertIn("[QC Auto Ready]", joined_messages)

    def test_remote_qc_auto_pass_advances_to_next_sample(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            remote_root = Path(tmpdir) / "policy"
            state_root = Path(tmpdir) / "state"
            gov_md_root = Path(tmpdir) / "gov-md"
            for sample_id in ("policy_briefing_2026_04_15_1", "policy_briefing_2026_04_15_2"):
                sample_dir = remote_root / sample_id
                sample_dir.mkdir(parents=True)
                (sample_dir / "source.hwpx").write_bytes(b"hwpx")
                (sample_dir / "review.md").write_text("review", encoding="utf-8")
                (sample_dir / "rendered.md").write_text("rendered", encoding="utf-8")
                (sample_dir / "meta.json").write_text(json.dumps({"sample_status": "scratch"}, ensure_ascii=False), encoding="utf-8")
            (state_root / "telegram_qc_sessions").mkdir(parents=True, exist_ok=True)
            (state_root / "telegram_qc_sessions" / "6475698942.json").write_text(
                json.dumps(
                    {
                        "auto_mode": True,
                        "auto_batch_id": "batch-1",
                        "auto_queue_sample_ids": ["policy_briefing_2026_04_15_1", "policy_briefing_2026_04_15_2"],
                        "auto_queue_index": 0,
                        "auto_current_sample_id": "policy_briefing_2026_04_15_1",
                        "auto_current_attempt": 2,
                        "auto_current_status": "awaiting_user",
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            with mock.patch("scripts.openclaw_ops.qc_promote") as mocked_promote, \
                 mock.patch(
                     "scripts.openclaw_ops._spawn_background_auto_run",
                     return_value={"command": "remote-qc-auto-queued", "pid": 777, "ok": True},
                 ):
                payload = dispatch_telegram_message(
                    'Conversation info (untrusted metadata): {"message_id":"23","sender_id":"6475698942"}\n통과',
                    chat_scope="dm",
                    export_root=Path(tmpdir),
                    gov_md_root=gov_md_root,
                    qc_root=remote_root,
                    remote_qc_root=remote_root,
                    state_root=state_root,
                )
            self.assertEqual(payload["command"], "remote-qc-auto-advance")
            mocked_promote.assert_called_once()
            state = _load_session_state(state_root, "6475698942")
            self.assertEqual(state["auto_queue_index"], 1)
            self.assertEqual(state["auto_current_sample_id"], "policy_briefing_2026_04_15_2")

    def test_remote_qc_auto_run_current_defers_missing_sample_and_continues(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            remote_root = Path(tmpdir) / "policy"
            state_root = Path(tmpdir) / "state"
            gov_md_root = Path(tmpdir) / "gov-md"
            gov_md_root.mkdir(parents=True)
            self._init_git_repo(gov_md_root)
            existing_sample = remote_root / "policy_briefing_2026_04_15_813"
            existing_sample.mkdir(parents=True)
            (existing_sample / "source.hwpx").write_bytes(b"hwpx")
            (existing_sample / "review.md").write_text("review", encoding="utf-8")
            (existing_sample / "rendered.md").write_text("rendered", encoding="utf-8")
            (existing_sample / "meta.json").write_text(json.dumps({"sample_status": "scratch"}, ensure_ascii=False), encoding="utf-8")
            (state_root / "telegram_qc_sessions").mkdir(parents=True, exist_ok=True)
            (state_root / "telegram_qc_sessions" / "6475698942.json").write_text(
                json.dumps(
                    {
                        "auto_mode": True,
                        "auto_batch_id": "batch-1",
                        "auto_queue_sample_ids": ["policy_briefing_2026_04_15_797", existing_sample.name],
                        "auto_queue_index": 0,
                        "auto_current_sample_id": "policy_briefing_2026_04_15_797",
                        "auto_current_attempt": 0,
                        "auto_current_status": "queued",
                        "auto_max_attempts": 5,
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            with mock.patch("scripts.openclaw_ops._send_telegram_text") as mocked_send, \
                 mock.patch(
                     "scripts.openclaw_ops._handle_fix_request",
                     return_value={"worker_text": "implementation result", "returncode": 0},
                 ), \
                 mock.patch(
                     "scripts.openclaw_ops._run_hwpx_qc_inspect",
                     side_effect=[
                         {"returncode": 0, "payload": {"passed": False, "findings": [{"message": "title"}]}},
                         {"returncode": 0, "payload": {"passed": True, "findings": []}},
                     ],
                 ), \
                 mock.patch(
                     "scripts.openclaw_ops._run_auto_judge",
                     return_value={
                         "returncode": 0,
                         "judge": mock.Mock(
                             decision="pass",
                             confidence="high",
                             user_summary="AI pass",
                             next_fix_instruction="",
                             blocking_findings=(),
                         ),
                     },
                 ), \
                 mock.patch("scripts.openclaw_ops._send_requested_files", return_value=[]), \
                 mock.patch("scripts.openclaw_ops.export_policy_briefings_for_qc", return_value={"scaffolded_count": 0}):
                payload = _run_auto_current(
                    sender_id="6475698942",
                    message_id="24",
                    export_root=Path(tmpdir),
                    gov_md_root=gov_md_root,
                    remote_qc_root=remote_root,
                    state_root=state_root,
                )

            self.assertEqual(payload["status"], "awaiting_user")
            state = _load_session_state(state_root, "6475698942")
            self.assertEqual(state["auto_results"][0]["sample_id"], "policy_briefing_2026_04_15_797")
            self.assertEqual(state["auto_results"][0]["outcome"], "deferred")
            self.assertEqual(state["auto_current_sample_id"], existing_sample.name)
            joined_messages = "\n".join(call.kwargs.get("message", "") for call in mocked_send.call_args_list)
            self.assertIn("[QC Auto Deferred] sample=policy_briefing_2026_04_15_797", joined_messages)
            self.assertIn(f"[QC Auto Ready] sample={existing_sample.name}", joined_messages)


if __name__ == "__main__":
    unittest.main()
