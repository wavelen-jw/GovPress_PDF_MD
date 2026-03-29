from __future__ import annotations

import logging
from ..adapters import opendataloader
from ..repositories import JobRepository
from ..services.storage_service import StorageService


class ConverterWorker:
    def __init__(
        self,
        *,
        jobs: JobRepository,
        storage: StorageService,
        logger: logging.Logger | None = None,
    ) -> None:
        self._jobs = jobs
        self._storage = storage
        self._logger = logger or logging.getLogger(__name__)

    def enqueue(self, job_id: str) -> None:
        # Jobs are now consumed by the polling worker from persistent storage.
        return None

    def stop(self) -> None:
        return None

    def process(self, job_id: str, *, claimed: bool = False) -> None:
        record = self._jobs.get(job_id)
        if record is None or record.artifacts is None:
            return

        if not claimed:
            self._jobs.update_status(job_id, status="processing", progress=25)
        try:
            markdown = opendataloader.convert_pdf(str(record.artifacts.original_pdf_path))
            self._jobs.update_status(job_id, status="processing", progress=80)
            html_preview = opendataloader.render_preview_html(markdown)
            title, department = opendataloader.extract_metadata(markdown)
            final_path = self._storage.save_generated_markdown(job_id, markdown)
            self._jobs.save_result(
                job_id,
                markdown=markdown,
                html_preview=html_preview,
                title=title,
                department=department,
                final_markdown_path=final_path,
            )
        except Exception as exc:  # pragma: no cover - exact exceptions vary by runtime
            self._logger.exception("Conversion failed for job %s", job_id)
            self._jobs.update_status(
                job_id,
                status="failed",
                progress=100,
                error_code="CONVERSION_FAILED",
                error_message=str(exc),
            )
