from __future__ import annotations

from contextlib import asynccontextmanager
from functools import partial
import logging
import os
from pathlib import Path

from .api import jobs as jobs_api
from .api import results as results_api
from .core.config import load_settings
from .core.security import verify_api_key
from .repositories import SQLiteJobRepository
from .services.job_service import JobService
from .services.result_service import ResultService
from .services.storage_service import StorageService
from .workers.converter_worker import ConverterWorker
from .workers.poller import PollingWorker


def create_app(storage_root: Path | None = None, *, run_worker: bool = False):
    try:
        from fastapi import FastAPI
        from fastapi.middleware.cors import CORSMiddleware
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            "FastAPI is not installed. Install server dependencies from requirements.txt first."
        ) from exc

    settings = load_settings()
    resolved_storage_root = storage_root or Path(
        os.environ.get("GOVPRESS_STORAGE_ROOT", Path(__file__).resolve().parents[2] / "storage")
    )
    storage = StorageService(resolved_storage_root)
    repository = SQLiteJobRepository(storage.root / "jobs.sqlite3")
    worker = ConverterWorker(jobs=repository, storage=storage, logger=logging.getLogger("govpress.server"))
    poller = PollingWorker(jobs=repository, converter=worker, logger=logging.getLogger("govpress.worker"))
    job_service = JobService(repository=repository, storage=storage, worker=worker)
    result_service = ResultService(repository=repository, storage=storage)
    job_service.recover_incomplete_jobs()

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
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    auth_dependency = partial(verify_api_key, settings)
    app.include_router(jobs_api.build_router(job_service, settings, auth_dependency))
    app.include_router(results_api.build_router(result_service, auth_dependency))

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    app.state.job_service = job_service
    app.state.result_service = result_service
    app.state.worker = worker
    app.state.poller = poller
    app.state.settings = settings
    return app


app = None

try:  # pragma: no cover
    app = create_app()
except RuntimeError:
    pass
