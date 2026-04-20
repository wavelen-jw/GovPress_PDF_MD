from __future__ import annotations

from contextlib import asynccontextmanager
from functools import partial
import logging
import os
from pathlib import Path

from .api import jobs as jobs_api
from .api import policy_briefings as policy_briefings_api
from .api import results as results_api
from .adapters.policy_briefing import PolicyBriefingCache, PolicyBriefingCatalog, PolicyBriefingClient
from .adapters.policy_briefing_qc import resolve_qc_export_root
from .core.config import load_settings
from .core.security import verify_admin_api_key, verify_api_key
from .repositories import SQLiteJobRepository
from .services.job_service import JobService
from .services.result_service import ResultService
from .services.storage_service import StorageService
from .workers.converter_worker import ConverterWorker
from .workers.poller import PollingWorker

_SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
}


def create_app(
    storage_root: Path | None = None,
    *,
    run_worker: bool = False,
    policy_briefing_client: PolicyBriefingClient | None = None,
):
    try:
        from fastapi import FastAPI
        from fastapi.middleware.cors import CORSMiddleware
        from starlette.middleware.base import BaseHTTPMiddleware
        from starlette.requests import Request as StarletteRequest
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            "FastAPI is not installed. Install server dependencies from requirements.txt first."
        ) from exc

    settings = load_settings()
    logger = logging.getLogger("govpress.server")
    if settings.using_policy_briefing_service_key_fallback:
        logger.warning(
            "Using built-in policy briefing service key fallback; "
            "set GOVPRESS_POLICY_BRIEFING_SERVICE_KEY on every server before disabling the fallback."
        )
    resolved_storage_root = storage_root or Path(
        os.environ.get("GOVPRESS_STORAGE_ROOT", Path(__file__).resolve().parents[2] / "storage")
    )
    storage = StorageService(resolved_storage_root)
    repository = SQLiteJobRepository(storage.root / "jobs.sqlite3")
    worker = ConverterWorker(jobs=repository, storage=storage, logger=logging.getLogger("govpress.server"))
    poller = PollingWorker(jobs=repository, converter=worker, logger=logging.getLogger("govpress.worker"))
    job_service = JobService(repository=repository, storage=storage, worker=worker)
    result_service = ResultService(repository=repository, storage=storage)
    policy_client = policy_briefing_client or PolicyBriefingClient(service_key=settings.policy_briefing_service_key)
    policy_catalog = PolicyBriefingCatalog(
        client=policy_client,
        cache_path=storage.root / "policy_briefing_catalog.json",
    )
    policy_cache = PolicyBriefingCache(
        client=policy_client,
        cache_dir=storage.root / "policy_briefing_cache",
    )
    qc_export_root = Path(
        os.environ.get(
            "GOVPRESS_QC_EXPORT_ROOT",
            str(resolve_qc_export_root(storage_root=resolved_storage_root)),
        )
    ).resolve()
    job_service.recover_incomplete_jobs()
    job_service.cleanup_jobs(older_than_hours=settings.job_ttl_hours, statuses=("completed", "failed"))

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        if run_worker:
            poller.start()
        try:
            yield
        finally:
            poller.stop()
            worker.stop()

    app = FastAPI(title="GovPress Mobile API", version="0.1.0", lifespan=lifespan)

    class SecurityHeadersMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request: StarletteRequest, call_next):
            response = await call_next(request)
            for header, value in _SECURITY_HEADERS.items():
                response.headers[header] = value
            return response

    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allow_origins,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    auth_dependency = partial(verify_api_key, settings)
    admin_auth_dependency = partial(verify_admin_api_key, settings)
    app.include_router(jobs_api.build_router(job_service, settings, auth_dependency))
    app.include_router(results_api.build_router(result_service, auth_dependency))
    app.include_router(
        policy_briefings_api.build_router(
            job_service,
            policy_client,
            policy_catalog,
            policy_cache,
            qc_export_root,
            auth_dependency,
            admin_auth_dependency,
        )
    )

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.head("/health")
    def health_head() -> None:
        return None

    app.state.job_service = job_service
    app.state.result_service = result_service
    app.state.worker = worker
    app.state.poller = poller
    app.state.settings = settings
    app.state.policy_briefing_client = policy_client
    app.state.policy_briefing_catalog = policy_catalog
    app.state.policy_briefing_cache = policy_cache
    app.state.qc_export_root = qc_export_root
    return app


app = None

try:  # pragma: no cover
    _run_worker = os.environ.get("GOVPRESS_RUN_WORKER", "").lower() in ("1", "true", "yes")
    app = create_app(run_worker=_run_worker)
except RuntimeError:
    pass
