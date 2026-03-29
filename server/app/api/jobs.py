from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Response, UploadFile

from ..schemas.jobs import CleanupResponse, JobListResponse, JobResponse, JobStatusResponse


def build_router(job_service, settings, verify_api_key) -> APIRouter:
    router = APIRouter(prefix="/v1/jobs", tags=["jobs"])

    @router.post("", response_model=JobResponse)
    async def create_job(
        file: UploadFile = File(...),
        source: str = Form("mobile"),
        client_request_id: str | None = Form(None),
        _authorized: None = Depends(verify_api_key),
    ) -> JobResponse:
        file_name = file.filename or "document.pdf"
        if not file_name.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Only PDF files are supported")
        content = await file.read()
        if not content:
            raise HTTPException(status_code=400, detail="Uploaded file is empty")
        if len(content) > settings.max_upload_bytes:
            raise HTTPException(status_code=413, detail="Uploaded file exceeds the maximum allowed size")
        record = job_service.create_job(
            file_name=file_name,
            content=content,
            source=source,
            client_request_id=client_request_id,
        )
        return JobResponse(
            job_id=record.job_id,
            status=record.status,
            file_name=record.file_name,
            created_at=record.created_at,
        )

    @router.get("", response_model=JobListResponse)
    def list_jobs(
        limit: int = Query(20, ge=1, le=100),
        status: str | None = Query(None),
        cursor: str | None = Query(None),
        _authorized: None = Depends(verify_api_key),
    ) -> JobListResponse:
        records, next_cursor = job_service.list_jobs(limit=limit, status=status, cursor=cursor)
        return JobListResponse(
            items=[
                JobResponse(
                    job_id=record.job_id,
                    status=record.status,
                    file_name=record.file_name,
                    created_at=record.created_at,
                    updated_at=record.updated_at,
                )
                for record in records
            ],
            next_cursor=next_cursor,
        )

    @router.get("/{job_id}", response_model=JobStatusResponse)
    def get_job(job_id: str, _authorized: None = Depends(verify_api_key)) -> JobStatusResponse:
        record = job_service.get_job(job_id)
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
    def retry_job(job_id: str, _authorized: None = Depends(verify_api_key)) -> JobStatusResponse:
        try:
            record = job_service.retry_job(job_id)
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

    @router.delete("/{job_id}", status_code=204)
    def delete_job(job_id: str, _authorized: None = Depends(verify_api_key)) -> Response:
        record = job_service.delete_job(job_id)
        if record is None:
            raise HTTPException(status_code=404, detail="Job not found")
        return Response(status_code=204)

    @router.post("/cleanup", response_model=CleanupResponse)
    def cleanup_jobs(
        older_than_days: int = Query(..., ge=1, le=3650),
        statuses: list[str] | None = Query(None),
        _authorized: None = Depends(verify_api_key),
    ) -> CleanupResponse:
        records = job_service.cleanup_jobs(
            older_than_days=older_than_days,
            statuses=tuple(statuses) if statuses else None,
        )
        return CleanupResponse(deleted_count=len(records))

    return router
