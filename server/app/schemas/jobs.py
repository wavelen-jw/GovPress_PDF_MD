from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class JobResponse(BaseModel):
    job_id: str
    status: str
    file_name: str
    created_at: datetime
    updated_at: datetime | None = None


class JobCreateResponse(JobResponse):
    edit_token: str


class JobStatusResponse(JobResponse):
    progress: int = Field(default=0, ge=0, le=100)
    error_code: str | None = None
    error_message: str | None = None

