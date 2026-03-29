from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class ResultMeta(BaseModel):
    title: str | None = None
    department: str | None = None
    source_file_name: str


class ResultResponse(BaseModel):
    job_id: str
    status: str
    markdown: str | None = None
    html_preview: str | None = None
    meta: ResultMeta


class ResultUpdateRequest(BaseModel):
    markdown: str


class ResultUpdateResponse(BaseModel):
    job_id: str
    status: str
    saved_at: datetime | None = None

