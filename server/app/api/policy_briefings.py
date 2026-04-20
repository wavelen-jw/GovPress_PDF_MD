from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
import os
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse

from ..adapters.policy_briefing_qc import ensure_dashboard_assets, resolve_dashboard_asset_path
from ..schemas.policy_briefings import (
    PolicyBriefingCacheResetResponse,
    PolicyBriefingImportRequest,
    PolicyBriefingImportResponse,
    PolicyBriefingItemResponse,
    PolicyBriefingListResponse,
    PolicyBriefingRecentListResponse,
)

_UPSTREAM_POLICY_BRIEFING_TIMEOUT_DETAIL = (
    "정책브리핑 제공기관 API 응답이 지연되거나 장애 상태입니다. 잠시 후 다시 시도해 주세요."
)


def _describe_policy_briefing_error(exc: Exception) -> str:
    message = str(exc).strip() or exc.__class__.__name__
    lowered = message.lower()
    if (
        "timed out" in lowered
        or "timeout" in lowered
        or "load failed" in lowered
        or "failed to fetch" in lowered
        or "bad gateway" in lowered
        or "network" in lowered
        or "signal is aborted" in lowered
    ):
        return _UPSTREAM_POLICY_BRIEFING_TIMEOUT_DETAIL
    return message


def _default_curated_qc_root() -> Path:
    env_root = os.environ.get("GOVPRESS_CURATED_QC_ROOT")
    if env_root:
        return Path(env_root).resolve()
    gov_md_root = os.environ.get("GOV_MD_CONVERTER_ROOT")
    if gov_md_root:
        return (Path(gov_md_root).resolve() / "tests" / "qc_samples").resolve()
    return (Path(__file__).resolve().parents[4] / "gov-md-converter" / "tests" / "qc_samples").resolve()


def build_router(
    job_service,
    policy_briefing_client,
    policy_briefing_catalog,
    policy_briefing_cache,
    qc_export_root,
    verify_api_key,
    verify_admin_api_key,
) -> APIRouter:
    router = APIRouter(prefix="/v1/policy-briefings", tags=["policy-briefings"])

    def _serialize_policy_briefing_item(resolved_date: date, item) -> PolicyBriefingItemResponse:
        return PolicyBriefingItemResponse(
            date=resolved_date,
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
            items=[_serialize_policy_briefing_item(resolved_date, item) for item in catalog_result.items],
        )

    @router.get("/recent", response_model=PolicyBriefingRecentListResponse)
    def get_recent_policy_briefings(
        days: int = Query(default=15, ge=1, le=60),
        end_date: date | None = Query(default=None, alias="endDate"),
        _authorized: None = Depends(verify_api_key),
    ) -> PolicyBriefingRecentListResponse:
        if not policy_briefing_client.configured:
            raise HTTPException(status_code=503, detail="정책브리핑 API 서비스키가 설정되지 않았습니다.")

        resolved_end_date = end_date or date.today()
        target_dates = [resolved_end_date - timedelta(days=offset) for offset in range(days)]
        all_items: list[PolicyBriefingItemResponse] = []
        refresh_times: list[str] = []
        served_stale = False
        warnings: list[str] = []

        for target_day in target_dates:
            try:
                day_result = policy_briefing_catalog.list_cached_items_with_status(
                    target_date=target_day,
                    ensure_fresh=(target_day == date.today()),
                )
                if not day_result.items and target_day != date.today():
                    day_result = policy_briefing_catalog.list_cached_items_with_status(
                        target_date=target_day,
                        ensure_fresh=True,
                    )
            except Exception as exc:
                if not all_items:
                    raise HTTPException(status_code=502, detail=_describe_policy_briefing_error(exc)) from exc
                warnings.append(_describe_policy_briefing_error(exc))
                continue

            if day_result.served_stale:
                served_stale = True
                warnings.append(_describe_policy_briefing_error(RuntimeError(day_result.stale_reason or "stale cache")))
            if day_result.last_refreshed_at:
                refresh_times.append(day_result.last_refreshed_at)
            all_items.extend(_serialize_policy_briefing_item(target_day, item) for item in day_result.items)

        deduped_items = list({item.news_item_id: item for item in all_items}.values())
        deduped_items.sort(key=lambda item: (item.date, item.approve_date, item.news_item_id), reverse=True)
        warning = warnings[0] if warnings else None

        return PolicyBriefingRecentListResponse(
            start_date=target_dates[-1],
            end_date=resolved_end_date,
            days=days,
            last_refreshed_at=sorted(refresh_times).at(-1) if refresh_times else None,
            served_stale=served_stale,
            warning=warning,
            items=deduped_items,
        )

    @router.post("/import", response_model=PolicyBriefingImportResponse)
    def import_today_policy_briefing(
        payload: PolicyBriefingImportRequest,
        _authorized: None = Depends(verify_api_key),
    ) -> PolicyBriefingImportResponse:
        if not policy_briefing_client.configured:
            raise HTTPException(status_code=503, detail="정책브리핑 API 서비스키가 설정되지 않았습니다.")
        try:
            item = policy_briefing_catalog.get_cached_item(payload.news_item_id, target_date=payload.date)
            if item is None:
                resolved_date = payload.date or date.today()
                policy_briefing_catalog.refresh_today(resolved_date)
                item = policy_briefing_catalog.get_cached_item(payload.news_item_id, target_date=resolved_date)
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
        pdf_attachment = item.primary_pdf
        if pdf_attachment is not None:
            try:
                downloaded_pdf = policy_briefing_client.download_attachment(item, pdf_attachment)
            except Exception:
                downloaded_pdf = None
            if downloaded_pdf is not None:
                job_service.attach_original_artifact(
                    job_id=record.job_id,
                    file_name=pdf_attachment.file_name,
                    content=downloaded_pdf.content,
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

    @router.get("/qc/dashboard")
    def get_policy_briefing_qc_dashboard() -> FileResponse:
        html_path = resolve_dashboard_asset_path(qc_export_root, "index.html")
        if not html_path.exists():
            try:
                html_path, _ = ensure_dashboard_assets(qc_export_root)
            except Exception:
                raise HTTPException(status_code=404, detail="QC dashboard is not available yet.")
        if not html_path.exists():
            raise HTTPException(status_code=404, detail="QC dashboard is not available yet.")
        return FileResponse(html_path, media_type="text/html; charset=utf-8")

    @router.get("/qc/dashboard.json")
    def get_policy_briefing_qc_dashboard_json() -> FileResponse:
        json_path = resolve_dashboard_asset_path(qc_export_root, "dashboard.json")
        if not json_path.exists():
            try:
                _, json_path = ensure_dashboard_assets(qc_export_root)
            except Exception:
                raise HTTPException(status_code=404, detail="QC dashboard JSON is not available yet.")
        if not json_path.exists():
            raise HTTPException(status_code=404, detail="QC dashboard JSON is not available yet.")
        return FileResponse(json_path, media_type="application/json; charset=utf-8")

    @router.get("/qc/curated/{sample_id}/{asset_name}")
    def get_policy_briefing_qc_curated_rendered(sample_id: str, asset_name: str) -> FileResponse:
        if Path(sample_id).name != sample_id:
            raise HTTPException(status_code=404, detail="Curated sample not found.")
        sample_dir = (_default_curated_qc_root() / sample_id).resolve()
        if not sample_dir.exists() or not sample_dir.is_dir():
            raise HTTPException(status_code=404, detail="Curated sample not found.")
        if Path(asset_name).name != asset_name:
            raise HTTPException(status_code=404, detail="Curated sample asset not found.")
        rendered_path = sample_dir / asset_name
        if not rendered_path.exists():
            raise HTTPException(status_code=404, detail="Curated sample asset is not available.")
        media_type = "application/json; charset=utf-8" if rendered_path.suffix == ".json" else "text/markdown; charset=utf-8"
        return FileResponse(rendered_path, media_type=media_type)

    return router
