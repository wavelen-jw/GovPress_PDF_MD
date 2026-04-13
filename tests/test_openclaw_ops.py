from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
import subprocess
import sys
import unittest
from unittest import mock

from scripts.openclaw_ops import (
    _format_codex_stream_line,
    _load_session_state,
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
        self.assertEqual(primary_key, "serverH")
        self.assertEqual(presets[0].key, "serverH")
        self.assertEqual(presets[0].url, "https://api.govpress.cloud")

    def test_build_server_status_reports_failover_candidate(self) -> None:
        with mock.patch("scripts.openclaw_ops._fetch_health") as mocked_fetch:
            mocked_fetch.side_effect = [
                {"ok": True, "status": 200, "endpoint": "https://api.govpress.cloud/health", "body": "ok"},
                {"ok": False, "status": 502, "endpoint": "https://api4.govpress.cloud/health", "error": "bad gateway"},
                {"ok": True, "status": 200, "endpoint": "https://api2.govpress.cloud/health", "body": "ok"},
            ]
            payload = build_server_status()
        self.assertEqual(payload["primary_key"], "serverH")
        self.assertTrue(payload["primary_healthy"])
        self.assertFalse(payload["mismatch"])
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

            def fake_run(command, *, cwd):
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

            def fake_run(command, *, cwd):
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

            def fake_run(command, *, cwd):
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

            with mock.patch("scripts.openclaw_ops._rewrite_sample_review") as mocked_rewrite, \
                 mock.patch("scripts.openclaw_ops._run_subprocess", side_effect=fake_run), \
                 mock.patch("scripts.openclaw_ops._run_codex_with_streaming", side_effect=fake_codex_stream):
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
            self.assertIn("pid", payload)

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

            def fake_run(command, *, cwd):
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

            def fake_run(command, *, cwd):
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


if __name__ == "__main__":
    unittest.main()
