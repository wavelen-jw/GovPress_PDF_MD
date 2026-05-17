from __future__ import annotations

from datetime import date as date_type, datetime

from pydantic import BaseModel, Field

from ..models import ConverterEngine


class PolicyBriefingAttachmentResponse(BaseModel):
    file_name: str
    file_url: str
    extension: str
    is_hwpx: bool = False
    is_pdf: bool = False
    is_appendix: bool = False


class PolicyBriefingItemResponse(BaseModel):
    date: date_type
    news_item_id: str
    title: str
    department: str
    approve_date: str
    original_url: str
    file_name: str
    file_url: str
    has_hwpx: bool = False
    has_appendix_hwpx: bool = False
    attachments: list[PolicyBriefingAttachmentResponse] = Field(default_factory=list)


class PolicyBriefingListResponse(BaseModel):
    date: date_type
    last_refreshed_at: str | None = None
    served_stale: bool = False
    warning: str | None = None
    items: list[PolicyBriefingItemResponse]


class PolicyBriefingRecentListResponse(BaseModel):
    start_date: date_type
    end_date: date_type
    days: int
    last_refreshed_at: str | None = None
    served_stale: bool = False
    warning: str | None = None
    items: list[PolicyBriefingItemResponse]


class PolicyBriefingImportRequest(BaseModel):
    news_item_id: str
    date: date_type | None = None
    file_url: str | None = None
    force_reprocess: bool = False
    converter_engine: ConverterEngine = "default"


class PolicyBriefingImportResponse(BaseModel):
    job_id: str
    edit_token: str
    status: str
    file_name: str
    created_at: datetime
    converter_engine: ConverterEngine = "default"
    news_item_id: str
    title: str
    department: str
    original_url: str


class PolicyBriefingCacheResetResponse(BaseModel):
    deleted_entries: int
    reset_at: datetime
