from __future__ import annotations

import asyncio
from datetime import timedelta
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from server.app.models import utcnow
from server.app.repositories import SQLiteJobRepository
from server.app.services.job_service import JobService
from server.app.services.result_service import ResultService
from server.app.services.storage_service import StorageService
from server.app.workers.converter_worker import ConverterWorker
from server.app.workers.poller import PollingWorker


class ServerServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.storage = StorageService(Path(self.temp_dir.name))
        self.repository = SQLiteJobRepository(self.storage.root / "jobs.sqlite3")
        self.worker = ConverterWorker(jobs=self.repository, storage=self.storage)
        self.job_service = JobService(
            repository=self.repository,
            storage=self.storage,
            worker=self.worker,
        )
        self.result_service = ResultService(
            repository=self.repository,
            storage=self.storage,
        )

    def test_create_job_persists_original_pdf_and_queues_work(self) -> None:
        with patch.object(self.worker, "enqueue") as mock_enqueue:
            record = self.job_service.create_job(
                file_name="sample.pdf",
                content=b"%PDF-1.4",
            )

        self.assertEqual(record.status, "queued")
        self.assertTrue(record.artifacts)
        assert record.artifacts is not None
        self.assertTrue(record.artifacts.original_pdf_path.exists())
        mock_enqueue.assert_called_once_with(record.job_id)

    def test_retry_job_requeues_failed_job(self) -> None:
        with patch.object(self.worker, "enqueue"):
            record = self.job_service.create_job(file_name="sample.pdf", content=b"%PDF-1.4")
        self.repository.update_status(
            record.job_id,
            status="failed",
            progress=100,
            error_code="FAIL",
            error_message="boom",
        )

        with patch.object(self.worker, "enqueue") as mock_enqueue:
            updated = self.job_service.retry_job(record.job_id, record.edit_token)

        self.assertEqual(updated.status, "queued")
        self.assertEqual(updated.progress, 0)
        self.assertIsNone(updated.error_code)
        mock_enqueue.assert_called_once_with(record.job_id)

    def test_create_job_returns_existing_record_for_duplicate_client_request_id(self) -> None:
        with patch.object(self.worker, "enqueue") as mock_enqueue:
            first = self.job_service.create_job(
                file_name="sample.pdf",
                content=b"%PDF-1.4",
                client_request_id="req-123",
            )
            second = self.job_service.create_job(
                file_name="sample.pdf",
                content=b"%PDF-1.4",
                client_request_id="req-123",
            )

        self.assertEqual(first.job_id, second.job_id)
        mock_enqueue.assert_called_once_with(first.job_id)

    def test_create_job_replaces_failed_duplicate_client_request_id(self) -> None:
        with patch.object(self.worker, "enqueue"):
            first = self.job_service.create_job(
                file_name="sample.pdf",
                content=b"%PDF-1.4",
                client_request_id="req-123",
            )
        self.repository.update_status(
            first.job_id,
            status="failed",
            progress=100,
            error_code="CONVERSION_FAILED",
            error_message="boom",
        )

        with patch.object(self.worker, "enqueue") as mock_enqueue:
            second = self.job_service.create_job(
                file_name="sample.pdf",
                content=b"%PDF-1.4",
                client_request_id="req-123",
            )

        self.assertNotEqual(first.job_id, second.job_id)
        self.assertEqual(second.status, "queued")
        self.assertIsNone(self.repository.get(first.job_id).client_request_id)
        mock_enqueue.assert_called_once_with(second.job_id)

    def test_worker_processes_job_and_saves_result(self) -> None:
        with patch.object(self.worker, "enqueue"):
            record = self.job_service.create_job(file_name="sample.pdf", content=b"%PDF-1.4")

        with patch("server.app.workers.converter_worker.opendataloader.convert_pdf", return_value="# 제목\n\n본문"), patch(
            "server.app.workers.converter_worker.opendataloader.render_preview_html",
            return_value="<h1>제목</h1><p>본문</p>",
        ), patch(
            "server.app.workers.converter_worker.opendataloader.extract_metadata",
            return_value=("제목", "홍보팀"),
        ):
            self.worker.process(record.job_id)

        updated = self.repository.get(record.job_id)
        assert updated is not None
        self.assertEqual(updated.status, "completed")
        self.assertEqual(updated.result.markdown, "# 제목\n\n본문")
        self.assertEqual(updated.result.title, "제목")
        self.assertTrue(updated.artifacts)
        assert updated.artifacts is not None
        self.assertTrue(updated.artifacts.final_markdown_path.exists())

    def test_result_service_saves_user_edit(self) -> None:
        with patch.object(self.worker, "enqueue"):
            record = self.job_service.create_job(file_name="sample.pdf", content=b"%PDF-1.4")
        self.repository.save_result(
            record.job_id,
            markdown="# 원본",
            html_preview="<h1>원본</h1>",
            title="원본",
            department="홍보팀",
            final_markdown_path=self.storage.save_generated_markdown(record.job_id, "# 원본"),
        )

        updated = self.result_service.update_markdown(record.job_id, record.edit_token, "# 수정본")

        self.assertEqual(updated.result.edited_markdown, "# 수정본")
        self.assertIsNotNone(updated.result.saved_at)
        self.assertTrue(updated.artifacts)
        assert updated.artifacts is not None
        self.assertTrue(updated.artifacts.edited_markdown_path.exists())

    def test_sqlite_repository_persists_across_instances(self) -> None:
        with patch.object(self.worker, "enqueue"):
            created = self.job_service.create_job(
                file_name="sample.pdf",
                content=b"%PDF-1.4",
                converter_engine="govpress-hwpx-md",
                document_metadata={"issuer_agency": "행정안전부"},
            )

        reloaded_repo = SQLiteJobRepository(self.storage.root / "jobs.sqlite3")
        fetched = reloaded_repo.get(created.job_id)

        assert fetched is not None
        self.assertEqual(fetched.job_id, created.job_id)
        self.assertEqual(fetched.file_name, "sample.pdf")
        self.assertEqual(fetched.converter_engine, "govpress-hwpx-md")
        self.assertEqual(fetched.document_metadata, {"issuer_agency": "행정안전부"})

    def test_worker_uses_experimental_hwpx_converter_when_selected(self) -> None:
        with patch.object(self.worker, "enqueue"):
            record = self.job_service.create_job(
                file_name="sample.hwpx",
                content=b"PK\x03\x04",
                converter_engine="govpress-hwpx-md",
                document_metadata={"issuer_agency": "행정안전부"},
            )

        with patch(
            "server.app.workers.converter_worker.experimental_hwpx_md.convert_hwpx",
            return_value="# 새 변환기\n\n본문",
        ) as mock_convert, patch(
            "server.app.workers.converter_worker.opendataloader.render_preview_html",
            return_value="<h1>새 변환기</h1><p>본문</p>",
        ), patch(
            "server.app.workers.converter_worker.opendataloader.extract_metadata",
            return_value=("새 변환기", "홍보팀"),
        ):
            self.worker.process(record.job_id)

        mock_convert.assert_called_once_with(
            str(record.artifacts.original_pdf_path),
            document_metadata={"issuer_agency": "행정안전부"},
        )
        updated = self.repository.get(record.job_id)
        assert updated is not None
        self.assertEqual(updated.status, "completed")
        self.assertEqual(updated.result.markdown_text, "# 새 변환기\n\n본문")
        self.assertEqual(updated.result.markdown_html, "# 새 변환기\n\n본문")

    def test_hwpx_jobs_use_new_converter_even_when_default_requested(self) -> None:
        with patch.object(self.worker, "enqueue"):
            record = self.job_service.create_job(
                file_name="sample.hwpx",
                content=b"PK\x03\x04",
                converter_engine="default",
                document_metadata={"issuer_agency": "행정안전부"},
            )

        self.assertEqual(record.converter_engine, "govpress-hwpx-md")
        with patch(
            "server.app.workers.converter_worker.experimental_hwpx_md.convert_hwpx",
            return_value="# 제목\n\n행정안전부 보도자료 /",
        ) as mock_convert, patch(
            "server.app.workers.converter_worker.opendataloader.render_preview_html",
            return_value="<h1>제목</h1>",
        ), patch(
            "server.app.workers.converter_worker.opendataloader.extract_metadata",
            return_value=("제목", "행정안전부"),
        ):
            self.worker.process(record.job_id)

        mock_convert.assert_called_once_with(
            str(record.artifacts.original_pdf_path),
            document_metadata={"issuer_agency": "행정안전부"},
        )

    def test_worker_reports_hwpx_timeout_as_large_document_failure(self) -> None:
        with patch.object(self.worker, "enqueue"):
            record = self.job_service.create_job(
                file_name="large-budget.hwpx",
                content=b"PK\x03\x04",
                converter_engine="govpress-hwpx-md",
            )

        from server.app.adapters.experimental_hwpx_md import HwpxMdConversionTimeout

        timeout = HwpxMdConversionTimeout(timeout_seconds=600, diagnostics="section_count=198")
        with patch(
            "server.app.workers.converter_worker.experimental_hwpx_md.convert_hwpx",
            side_effect=timeout,
        ):
            self.worker.process(record.job_id)

        updated = self.repository.get(record.job_id)
        assert updated is not None
        self.assertEqual(updated.status, "failed")
        self.assertEqual(updated.error_code, "CONVERSION_TIMEOUT")
        self.assertIn("문서 구조가 매우 크거나 복잡해", updated.error_message or "")
        error_log = self.storage.results_dir / f"{record.job_id}.error.log"
        self.assertIn("section_count=198", error_log.read_text(encoding="utf-8"))

    def test_list_jobs_returns_cursor_for_next_page(self) -> None:
        with patch.object(self.worker, "enqueue"):
            first = self.job_service.create_job(file_name="a.pdf", content=b"%PDF-1.4")
            second = self.job_service.create_job(file_name="b.pdf", content=b"%PDF-1.4")
            third = self.job_service.create_job(file_name="c.pdf", content=b"%PDF-1.4")

        page_one, next_cursor = self.job_service.list_jobs(limit=2)

        self.assertEqual(len(page_one), 2)
        self.assertIsNotNone(next_cursor)
        self.assertEqual(page_one[0].job_id, third.job_id)
        self.assertEqual(page_one[1].job_id, second.job_id)

        page_two, final_cursor = self.job_service.list_jobs(limit=2, cursor=next_cursor)
        self.assertEqual(len(page_two), 1)
        self.assertEqual(page_two[0].job_id, first.job_id)
        self.assertIsNone(final_cursor)

    def test_recover_incomplete_jobs_requeues_processing_job(self) -> None:
        with patch.object(self.worker, "enqueue"):
            record = self.job_service.create_job(file_name="sample.pdf", content=b"%PDF-1.4")
        self.repository.update_status(record.job_id, status="processing", progress=50)

        recovered = self.job_service.recover_incomplete_jobs()
        updated = self.repository.get(record.job_id)

        self.assertEqual(recovered, 1)
        assert updated is not None
        self.assertEqual(updated.status, "queued")
        self.assertEqual(updated.progress, 0)
        self.assertEqual(updated.error_code, "RECOVERED_AFTER_RESTART")

    def test_claim_next_queued_job_marks_job_processing(self) -> None:
        with patch.object(self.worker, "enqueue"):
            record = self.job_service.create_job(file_name="sample.pdf", content=b"%PDF-1.4")

        claimed = self.repository.claim_next_queued_job("worker-1")

        assert claimed is not None
        self.assertEqual(claimed.job_id, record.job_id)
        self.assertEqual(claimed.status, "processing")
        self.assertEqual(claimed.progress, 25)

    def test_polling_worker_processes_claimed_job(self) -> None:
        with patch.object(self.worker, "enqueue"):
            record = self.job_service.create_job(file_name="sample.pdf", content=b"%PDF-1.4")

        poller = PollingWorker(jobs=self.repository, converter=self.worker, poll_interval_seconds=0.01)
        with patch("server.app.workers.converter_worker.opendataloader.convert_pdf", return_value="# 제목\n\n본문"), patch(
            "server.app.workers.converter_worker.opendataloader.render_preview_html",
            return_value="<h1>제목</h1><p>본문</p>",
        ), patch(
            "server.app.workers.converter_worker.opendataloader.extract_metadata",
            return_value=("제목", "홍보팀"),
        ):
            processed = poller.run_once()

        self.assertTrue(processed)
        updated = self.repository.get(record.job_id)
        assert updated is not None
        self.assertEqual(updated.status, "completed")

    def test_save_original_pdf_stream_rejects_oversized_upload(self) -> None:
        class UploadStub:
            def __init__(self, chunks: list[bytes]) -> None:
                self._chunks = chunks

            async def read(self, size: int = -1) -> bytes:
                return self._chunks.pop(0) if self._chunks else b""

        with self.assertRaises(ValueError) as context:
            asyncio.run(
                self.storage.save_original_pdf_stream(
                    "job_stream",
                    "sample.pdf",
                    UploadStub([b"a" * 5, b"b" * 5]),
                    max_bytes=8,
                    chunk_size=4,
                )
            )

        self.assertEqual(str(context.exception), "Uploaded file exceeds the maximum allowed size")
        self.assertFalse((self.storage.originals_dir / "job_stream-sample.pdf").exists())

    def test_cleanup_jobs_removes_expired_completed_job(self) -> None:
        with patch.object(self.worker, "enqueue"):
            record = self.job_service.create_job(file_name="sample.pdf", content=b"%PDF-1.4")
        self.storage.save_original_file(record.job_id, "sample.hwpx", b"PK\x03\x04")
        self.repository.save_result(
            record.job_id,
            markdown="# 원본",
            html_preview="<h1>원본</h1>",
            title="원본",
            department="홍보팀",
            final_markdown_path=self.storage.save_generated_markdown(record.job_id, "# 원본"),
        )
        expired_at = (utcnow() - timedelta(days=4)).isoformat()
        with self.repository._connect() as conn:  # type: ignore[attr-defined]
            conn.execute("UPDATE jobs SET updated_at = ? WHERE job_id = ?", (expired_at, record.job_id))
            conn.commit()

        removed = self.job_service.cleanup_jobs(older_than_hours=72, statuses=("completed",))

        self.assertEqual([item.job_id for item in removed], [record.job_id])
        self.assertIsNone(self.repository.get(record.job_id))
        self.assertFalse((self.storage.results_dir / f"{record.job_id}.md").exists())
        self.assertEqual(list(self.storage.originals_dir.glob(f"{record.job_id}-*")), [])


class WatchdogScriptTests(unittest.TestCase):
    def test_watchdog_reconcile_references_existing_compose_script(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        script_path = repo_root / "deploy/wsl/bin/watchdog_reconcile.sh"
        compose_path = repo_root / "deploy/wsl/bin/compose.sh"
        content = script_path.read_text(encoding="utf-8")

        self.assertIn('COMPOSE_SH="$DEPLOY_DIR/bin/compose.sh"', content)
        self.assertIn('watchdog_reconcile=error reason=compose_missing', content)
        self.assertNotIn("/deploy/wsl/deploy/wsl/bin/compose.sh", content)
        self.assertTrue(compose_path.exists())
