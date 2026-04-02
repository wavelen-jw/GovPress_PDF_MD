from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal


JobStatus = Literal["queued", "processing", "completed", "failed"]


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class JobResult:
    markdown: str | None = None
    html_preview: str | None = None
    title: str | None = None
    department: str | None = None
    edited_markdown: str | None = None
    saved_at: datetime | None = None


@dataclass
class JobArtifacts:
    original_file_path: Path
    final_markdown_path: Path | None = None
    edited_markdown_path: Path | None = None


@dataclass
class JobRecord:
    job_id: str
    edit_token: str
    file_name: str
    source: str
    status: JobStatus
    created_at: datetime = field(default_factory=utcnow)
    updated_at: datetime = field(default_factory=utcnow)
    progress: int = 0
    error_code: str | None = None
    error_message: str | None = None
    client_request_id: str | None = None
    result_version: int = 0
    result: JobResult = field(default_factory=JobResult)
    artifacts: JobArtifacts | None = None
