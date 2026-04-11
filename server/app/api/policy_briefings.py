from __future__ import annotations

from datetime import UTC, date, datetime

from fastapi import APIRouter, Depends, HTTPException, Query

from ..schemas.policy_briefings import (
    PolicyBriefingCacheResetResponse,
    PolicyBriefingImportRequest,
    PolicyBriefingImportResponse,
    PolicyBriefingItemResponse,
    PolicyBriefingListResponse,
)

_UPSTREAM_POLICY_BRIEFING_TIMEOUT_DETAIL = (
    "정책브리핑 제공기관 API 응답이 지연되거나 장애 상태입니다. 잠시 후 다시 시도해 주세요."
)


def _describe_policy_briefing_error(exc: Exception) -> str:
    message = str(exc).strip() or exc.__class__.__name__
    lowered = message.lower()
    if "timed out" in lowered or "timeout" in lowered:
        return _UPSTREAM_POLICY_BRIEFING_TIMEOUT_DETAIL
    return message


def build_router(
    job_service,
    policy_briefing_client,
    policy_briefing_catalog,
    policy_briefing_cache,
    verify_api_key,
    verify_admin_api_key,
) -> APIRouter:
    router = APIRouter(prefix="/v1/policy-briefings", tags=["policy-briefings"])

    @router.get("/today", response_model=PolicyBriefingListResponse)
    def get_today_policy_briefings(
        target_date: date | None = Query(default=None, alias="date"),
        _authorized: None = Depends(verify_api_key),
    ) -> PolicyBriefingListResponse:
        if not policy_briefing_client.configured:
            raise HTTPException(status_code=503, detail="정책브리핑 API 서비스키가 설정되지 않았습니다.")
        resolved_date = target_date or date.today()
        try:
            catalog_result = policy_briefing_catalog.list_cached_items_with_status(
                target_date=resolved_date,
                ensure_fresh=True,
            )
        except Exception as exc:
            raise HTTPException(status_code=502, detail=_describe_policy_briefing_error(exc)) from exc
        warning = None
        if catalog_result.served_stale:
            warning = _describe_policy_briefing_error(RuntimeError(catalog_result.stale_reason or "stale cache"))

        return PolicyBriefingListResponse(
            date=resolved_date,
            last_refreshed_at=catalog_result.last_refreshed_at,
            served_stale=catalog_result.served_stale,
            warning=warning,
            items=[
                PolicyBriefingItemResponse(
                    news_item_id=item.news_item_id,
                    title=item.title,
                    department=item.department,
                    approve_date=item.approve_date,
                    original_url=item.original_url,
                    file_name=item.primary_hwpx.file_name if item.primary_hwpx else "",
                    file_url=item.primary_hwpx.file_url if item.primary_hwpx else "",
                    has_appendix_hwpx=any(
                        attachment.is_hwpx and attachment.is_appendix for attachment in item.attachments
                    ),
                )
                for item in catalog_result.items
            ],
        )

    @router.post("/import", response_model=PolicyBriefingImportResponse)
    def import_today_policy_briefing(
        payload: PolicyBriefingImportRequest,
        _authorized: None = Depends(verify_api_key),
    ) -> PolicyBriefingImportResponse:
        if not policy_briefing_client.configured:
            raise HTTPException(status_code=503, detail="정책브리핑 API 서비스키가 설정되지 않았습니다.")
        try:
            item = policy_briefing_catalog.get_cached_item(payload.news_item_id)
            if item is None:
                resolved_date = payload.date or date.today()
                policy_briefing_catalog.refresh_today(resolved_date)
                item = policy_briefing_catalog.get_cached_item(payload.news_item_id)
            if item is None:
                raise KeyError(payload.news_item_id)
            cached = policy_briefing_cache.get(item.news_item_id)
            if cached is None or cached.original_content is None:
                cached = policy_briefing_cache.warm_item(item)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="캐시된 기사 목록에서 항목을 찾지 못했습니다.") from exc
        except Exception as exc:
            raise HTTPException(status_code=502, detail=_describe_policy_briefing_error(exc)) from exc
        record = job_service.create_completed_job(
            file_name=cached.file_name,
            markdown_text=cached.markdown_text,
            markdown_html=cached.markdown_html,
            html_preview_text=cached.html_preview_text,
            html_preview_html=cached.html_preview_html,
            title=cached.title,
            department=cached.department,
            original_content=cached.original_content,
            source="policy-briefing-cache",
        )
        return PolicyBriefingImportResponse(
            job_id=record.job_id,
            edit_token=record.edit_token,
            status=record.status,
            file_name=record.file_name,
            created_at=record.created_at,
            news_item_id=item.news_item_id,
            title=item.title,
            department=item.department,
            original_url=item.original_url,
        )

    @router.post("/cache/reset", response_model=PolicyBriefingCacheResetResponse)
    def reset_policy_briefing_cache(
        _authorized: None = Depends(verify_admin_api_key),
    ) -> PolicyBriefingCacheResetResponse:
        try:
            deleted_entries = policy_briefing_cache.reset()
        except Exception as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc

        return PolicyBriefingCacheResetResponse(
            deleted_entries=deleted_entries,
            reset_at=datetime.now(UTC),
        )

    return router
