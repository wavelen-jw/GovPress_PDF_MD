from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from ..core.security import require_edit_token
from ..schemas.results import ResultMeta, ResultResponse, ResultUpdateRequest, ResultUpdateResponse


def build_router(result_service, verify_api_key) -> APIRouter:
    router = APIRouter(prefix="/v1/jobs", tags=["results"])

    @router.get("/{job_id}/result", response_model=ResultResponse)
    def get_result(
        job_id: str,
        edit_token: str = Depends(require_edit_token),
        _authorized: None = Depends(verify_api_key),
    ) -> ResultResponse:
        record = result_service.get_result(job_id, edit_token)
        if record is None:
            raise HTTPException(status_code=404, detail="Job not found")
        return ResultResponse(
            job_id=record.job_id,
            status=record.status,
            markdown=record.result.edited_markdown or record.result.markdown,
            html_preview=record.result.html_preview,
            meta=ResultMeta(
                title=record.result.title,
                department=record.result.department,
                source_file_name=record.file_name,
            ),
        )

    @router.patch("/{job_id}/result", response_model=ResultUpdateResponse)
    def update_result(
        job_id: str,
        payload: ResultUpdateRequest,
        edit_token: str = Depends(require_edit_token),
        _authorized: None = Depends(verify_api_key),
    ) -> ResultUpdateResponse:
        try:
            record = result_service.update_markdown(job_id, edit_token, payload.markdown)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="Job not found") from exc
        return ResultUpdateResponse(
            job_id=record.job_id,
            status=record.status,
            saved_at=record.result.saved_at,
        )

    return router
