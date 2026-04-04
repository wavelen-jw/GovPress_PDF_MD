from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class ResultMeta(BaseModel):
    title: str | None = None
    department: str | None = None
    source_file_name: str


class ResultVariant(BaseModel):
    markdown: str | None = None
    html_preview: str | None = None


class ResultTableVariants(BaseModel):
    text: ResultVariant
    html: ResultVariant


class ResultResponse(BaseModel):
    job_id: str
    status: str
    markdown: str | None = None
    html_preview: str | None = None
    table_variants: ResultTableVariants
    meta: ResultMeta


class ResultUpdateRequest(BaseModel):
    markdown: str


class ResultUpdateResponse(BaseModel):
    job_id: str
    status: str
    saved_at: datetime | None = None
