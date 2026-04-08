from __future__ import annotations

from datetime import date as date_type, datetime

from pydantic import BaseModel


class PolicyBriefingItemResponse(BaseModel):
    news_item_id: str
    title: str
    department: str
    approve_date: str
    original_url: str
    file_name: str
    file_url: str
    has_appendix_hwpx: bool = False


class PolicyBriefingListResponse(BaseModel):
    date: date_type
    items: list[PolicyBriefingItemResponse]


class PolicyBriefingImportRequest(BaseModel):
    news_item_id: str
    date: date_type | None = None


class PolicyBriefingImportResponse(BaseModel):
    job_id: str
    edit_token: str
    status: str
    file_name: str
    created_at: datetime
    news_item_id: str
    title: str
    department: str
    original_url: str
