from __future__ import annotations

import logging
from pathlib import Path
import traceback
from ..adapters import experimental_hwpx_md
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
            file_path = str(record.artifacts.original_pdf_path)
            ext = Path(file_path).suffix.lower()
            if ext == ".hwpx":
                markdown = experimental_hwpx_md.convert_hwpx(
                    file_path,
                    document_metadata=record.document_metadata,
                )
                html_preview = opendataloader.render_preview_html(markdown)
                title, department = opendataloader.extract_metadata(markdown)
                final_path = self._storage.save_generated_markdown(job_id, markdown)
                self._jobs.save_result(
                    job_id,
                    markdown=markdown,
                    html_preview=html_preview,
                    markdown_text=markdown,
                    markdown_html=markdown,
                    html_preview_text=html_preview,
                    html_preview_html=html_preview,
                    title=title,
                    department=department,
                    final_markdown_path=final_path,
                )
                return
            else:
                markdown = opendataloader.convert_pdf(file_path)
                markdown_text = markdown
                markdown_html = markdown
                self._jobs.update_status(job_id, status="processing", progress=80)
                html_preview = opendataloader.render_preview_html(markdown)
                html_preview_text = html_preview
                html_preview_html = html_preview
                title, department = opendataloader.extract_metadata(markdown)
                final_path = self._storage.save_generated_markdown(job_id, markdown)
                self._jobs.save_result(
                    job_id,
                    markdown=markdown,
                    html_preview=html_preview,
                    markdown_text=markdown_text,
                    markdown_html=markdown_html,
                    html_preview_text=html_preview_text,
                    html_preview_html=html_preview_html,
                    title=title,
                    department=department,
                    final_markdown_path=final_path,
                )
        except Exception as exc:  # pragma: no cover - exact exceptions vary by runtime
            traceback_text = traceback.format_exc()
            self._logger.exception("Conversion failed for job %s: %s", job_id, exc)
            error_code = "CONVERSION_FAILED"
            error_message = "변환 중 오류가 발생했습니다. 파일 형식을 확인하거나 다시 시도해 주세요."
            if isinstance(exc, experimental_hwpx_md.HwpxMdConversionTimeout):
                error_code = "CONVERSION_TIMEOUT"
                error_message = (
                    "문서 구조가 매우 크거나 복잡해 제한시간 안에 변환하지 못했습니다. "
                    "예산서·결산서처럼 표와 본문이 많은 HWPX는 처리 시간이 오래 걸릴 수 있습니다."
                )
                self._logger.warning(
                    "HWPX conversion timeout for job %s after %ss: %s",
                    job_id,
                    exc.timeout_seconds,
                    exc.diagnostics,
                )
            print(
                f"Conversion failed for job {job_id}: {exc}\n{traceback_text}",
                flush=True,
            )
            try:
                (self._storage.results_dir / f"{job_id}.error.log").write_text(
                    (
                        f"{exc}\n"
                        f"{getattr(exc, 'diagnostics', '')}\n"
                        f"{traceback_text}"
                    ),
                    encoding="utf-8",
                )
            except Exception:
                self._logger.exception("Failed to write conversion error log for job %s", job_id)
            self._jobs.update_status(
                job_id,
                status="failed",
                progress=100,
                error_code=error_code,
                error_message=error_message,
            )
