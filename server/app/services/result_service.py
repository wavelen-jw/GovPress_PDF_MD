from __future__ import annotations

from ..adapters.opendataloader import render_preview_html
from ..models import JobRecord
from ..repositories import JobRepository
from .storage_service import StorageService


class ResultService:
    def __init__(self, *, repository: JobRepository, storage: StorageService) -> None:
        self._repository = repository
        self._storage = storage

    def get_result(self, job_id: str, edit_token: str) -> JobRecord | None:
        record = self._repository.get(job_id)
        if record is None or record.edit_token != edit_token:
            return None
        return record

    def update_markdown(self, job_id: str, edit_token: str, markdown: str) -> JobRecord:
        record = self.get_result(job_id, edit_token)
        if record is None:
            raise KeyError(job_id)
        path = self._storage.save_edited_markdown(job_id, markdown)
        self._repository.save_edited_markdown(
            job_id,
            markdown=markdown,
            edited_markdown_path=path,
        )
        refreshed = self._repository.get(job_id)
        assert refreshed is not None
        if refreshed.result.edited_markdown:
            refreshed.result.html_preview = render_preview_html(refreshed.result.edited_markdown)
        return refreshed
