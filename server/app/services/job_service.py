from __future__ import annotations

import math
import secrets
import uuid

from ..core.notify import send_telegram
from ..models import JobRecord
from ..models import JobStatus
from ..models import HwpxTableMode
from ..repositories import JobRepository
from ..workers.converter_worker import ConverterWorker
from .storage_service import StorageService

_QUEUE_ALERT_THRESHOLD = 3  # 대기 작업이 이 수 이상이면 알림


class JobService:
    def __init__(
        self,
        *,
        repository: JobRepository,
        storage: StorageService,
        worker: ConverterWorker,
    ) -> None:
        self._repository = repository
        self._storage = storage
        self._worker = worker

    def create_job(
        self,
        *,
        file_name: str,
        content: bytes,
        source: str = "mobile",
        hwpx_table_mode: HwpxTableMode = "text",
        client_request_id: str | None = None,
    ) -> JobRecord:
        if client_request_id:
            existing = self._repository.get_by_client_request_id(client_request_id)
            if existing is not None:
                return existing

        job_id = f"job_{uuid.uuid4().hex[:12]}"
        edit_token = secrets.token_urlsafe(24)
        original_path = self._storage.save_original_file(job_id, file_name, content)
        record = self._repository.create(
            job_id=job_id,
            edit_token=edit_token,
            file_name=file_name,
            source=source,
            hwpx_table_mode=hwpx_table_mode,
            client_request_id=client_request_id,
            original_file_path=original_path,
        )
        if record.job_id == job_id:
            self._worker.enqueue(job_id)
            queued = self._repository.count_queued_jobs()
            if queued >= _QUEUE_ALERT_THRESHOLD:
                send_telegram(f"⚠️ GovPress 대기 작업 {queued}개\n파일: {file_name}")
        return record

    async def create_job_from_upload(
        self,
        *,
        file_name: str,
        upload,
        max_upload_bytes: int,
        source: str = "mobile",
        hwpx_table_mode: HwpxTableMode = "text",
        client_request_id: str | None = None,
    ) -> JobRecord:
        if client_request_id:
            existing = self._repository.get_by_client_request_id(client_request_id)
            if existing is not None:
                return existing

        job_id = f"job_{uuid.uuid4().hex[:12]}"
        edit_token = secrets.token_urlsafe(24)
        original_path = await self._storage.save_original_file_stream(
            job_id,
            file_name,
            upload,
            max_bytes=max_upload_bytes,
        )
        record = self._repository.create(
            job_id=job_id,
            edit_token=edit_token,
            file_name=file_name,
            source=source,
            hwpx_table_mode=hwpx_table_mode,
            client_request_id=client_request_id,
            original_file_path=original_path,
        )
        if record.job_id == job_id:
            self._worker.enqueue(job_id)
            queued = self._repository.count_queued_jobs()
            if queued >= _QUEUE_ALERT_THRESHOLD:
                send_telegram(f"⚠️ GovPress 대기 작업 {queued}개\n파일: {file_name}")
        return record

    def get_job(self, job_id: str, edit_token: str) -> JobRecord | None:
        record = self._repository.get(job_id)
        if record is None or record.edit_token != edit_token:
            return None
        return record

    def list_jobs(
        self,
        *,
        limit: int = 20,
        status: str | None = None,
        cursor: str | None = None,
    ) -> tuple[list[JobRecord], str | None]:
        return self._repository.list_page(limit=limit, status=status, cursor=cursor)  # type: ignore[arg-type]

    def retry_job(self, job_id: str, edit_token: str) -> JobRecord:
        record = self.get_job(job_id, edit_token)
        if record is None:
            raise KeyError(job_id)
        self._repository.update_status(
            job_id,
            status="queued",
            progress=0,
            error_code=None,
            error_message=None,
        )
        self._worker.enqueue(job_id)
        updated = self._repository.get(job_id)
        assert updated is not None
        return updated

    def recover_incomplete_jobs(self) -> int:
        return self._repository.recover_incomplete_jobs()

    def delete_job(self, job_id: str, edit_token: str) -> JobRecord | None:
        record = self.get_job(job_id, edit_token)
        if record is None:
            return None
        record = self._repository.delete(job_id)
        if record is not None:
            self._storage.delete_job_files(job_id, record.file_name)
        return record

    def cleanup_jobs(
        self,
        *,
        older_than_hours: int,
        statuses: tuple[JobStatus, ...] | None = None,
    ) -> list[JobRecord]:
        records = self._repository.cleanup_old_jobs(
            older_than_days=max(1, math.ceil(older_than_hours / 24)),
            statuses=statuses,
        )
        for record in records:
            self._storage.delete_job_files(record.job_id, record.file_name)
        return records
