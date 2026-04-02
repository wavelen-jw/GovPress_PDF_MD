from __future__ import annotations

import logging
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile

from ..core.rate_limit import SlidingWindowRateLimiter
from ..core.security import require_edit_token
from ..core.turnstile import verify_turnstile_token
from ..schemas.jobs import JobCreateResponse, JobResponse, JobStatusResponse


def build_router(job_service, settings, verify_api_key) -> APIRouter:
    router = APIRouter(prefix="/v1/jobs", tags=["jobs"])
    logger = logging.getLogger("govpress.turnstile")
    upload_rate_limiter = SlidingWindowRateLimiter(
        max_requests=settings.upload_rate_limit_count,
        window_seconds=settings.upload_rate_limit_window_seconds,
    )

    @router.post("", response_model=JobCreateResponse)
    async def create_job(
        request: Request,
        file: UploadFile = File(...),
        source: str = Form("mobile"),
        client_request_id: str | None = Form(None),
        turnstile_response: str | None = Form(None, alias="cf-turnstile-response"),
        _authorized: None = Depends(verify_api_key),
    ) -> JobCreateResponse:
        remote_ip = request.headers.get("CF-Connecting-IP") or (request.client.host if request.client else None) or "unknown"
        rate_key = f"{remote_ip}|{request.headers.get('user-agent', '')[:120]}"
        if not upload_rate_limiter.allow(rate_key):
            raise HTTPException(status_code=429, detail="Too many upload requests. Please try again later.")
        job_service.cleanup_jobs(older_than_hours=settings.job_ttl_hours, statuses=("completed", "failed"))
        if settings.turnstile_secret_key:
            if not turnstile_response:
                logger.warning("Turnstile missing token remote_ip=%s host=%s", remote_ip, request.headers.get("host"))
                raise HTTPException(status_code=403, detail="Turnstile verification failed")
            success, verify_result = verify_turnstile_token(settings.turnstile_secret_key, turnstile_response, remote_ip)
            if not success:
                logger.warning(
                    "Turnstile verification failed remote_ip=%s host=%s result=%s",
                    remote_ip,
                    request.headers.get("host"),
                    verify_result,
                )
                raise HTTPException(status_code=403, detail="Turnstile verification failed")
        file_name = file.filename or "document.pdf"
        _ALLOWED_EXTENSIONS = {".pdf", ".hwpx"}
        if Path(file_name).suffix.lower() not in _ALLOWED_EXTENSIONS:
            raise HTTPException(status_code=400, detail="PDF 또는 HWPX 파일만 지원합니다.")
        try:
            record = await job_service.create_job_from_upload(
                file_name=file_name,
                upload=file,
                max_upload_bytes=settings.max_upload_bytes,
                source=source,
                client_request_id=client_request_id,
            )
        except ValueError as exc:
            detail = str(exc)
            if detail == "Uploaded file exceeds the maximum allowed size":
                raise HTTPException(status_code=413, detail=detail) from exc
            raise HTTPException(status_code=400, detail=detail) from exc
        return JobCreateResponse(
            job_id=record.job_id,
            edit_token=record.edit_token,
            status=record.status,
            file_name=record.file_name,
            created_at=record.created_at,
        )

    @router.get("/{job_id}", response_model=JobStatusResponse)
    def get_job(
        job_id: str,
        edit_token: str = Depends(require_edit_token),
        _authorized: None = Depends(verify_api_key),
    ) -> JobStatusResponse:
        record = job_service.get_job(job_id, edit_token)
        if record is None:
            raise HTTPException(status_code=404, detail="Job not found")
        return JobStatusResponse(
            job_id=record.job_id,
            status=record.status,
            file_name=record.file_name,
            created_at=record.created_at,
            updated_at=record.updated_at,
            progress=record.progress,
            error_code=record.error_code,
            error_message=record.error_message,
        )

    @router.post("/{job_id}/retry", response_model=JobStatusResponse)
    def retry_job(
        job_id: str,
        edit_token: str = Depends(require_edit_token),
        _authorized: None = Depends(verify_api_key),
    ) -> JobStatusResponse:
        try:
            record = job_service.retry_job(job_id, edit_token)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="Job not found") from exc
        return JobStatusResponse(
            job_id=record.job_id,
            status=record.status,
            file_name=record.file_name,
            created_at=record.created_at,
            updated_at=record.updated_at,
            progress=record.progress,
            error_code=record.error_code,
            error_message=record.error_message,
        )

    return router
