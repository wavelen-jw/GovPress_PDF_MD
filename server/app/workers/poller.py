from __future__ import annotations

import logging
import socket
import threading
import time

from ..repositories import JobRepository
from .converter_worker import ConverterWorker


class PollingWorker:
    def __init__(
        self,
        *,
        jobs: JobRepository,
        converter: ConverterWorker,
        poll_interval_seconds: float = 1.0,
        worker_id: str | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self._jobs = jobs
        self._converter = converter
        self._poll_interval_seconds = poll_interval_seconds
        self._worker_id = worker_id or f"{socket.gethostname()}-{threading.get_ident()}"
        self._logger = logger or logging.getLogger(__name__)
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, name="govpress-poller", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=2)

    def run_once(self) -> bool:
        record = self._jobs.claim_next_queued_job(self._worker_id)
        if record is None:
            return False
        self._logger.info("Claimed job %s", record.job_id)
        self._converter.process(record.job_id, claimed=True)
        return True

    def _run(self) -> None:
        while not self._stop_event.is_set():
            processed = self.run_once()
            if processed:
                continue
            self._stop_event.wait(self._poll_interval_seconds)
