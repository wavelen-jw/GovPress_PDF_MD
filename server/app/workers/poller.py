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
        concurrency: int = 1,
        worker_id: str | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self._jobs = jobs
        self._converter = converter
        self._poll_interval_seconds = poll_interval_seconds
        self._worker_id = worker_id or f"{socket.gethostname()}-{threading.get_ident()}"
        self._concurrency = max(1, concurrency)
        self._logger = logger or logging.getLogger(__name__)
        self._stop_event = threading.Event()
        self._threads: list[threading.Thread] = []

    def start(self) -> None:
        if any(thread.is_alive() for thread in self._threads):
            return
        self._stop_event.clear()
        self._threads = []
        for index in range(self._concurrency):
            thread = threading.Thread(
                target=self._run,
                args=(f"{self._worker_id}-{index + 1}",),
                name=f"govpress-poller-{index + 1}",
                daemon=True,
            )
            thread.start()
            self._threads.append(thread)

    def stop(self) -> None:
        self._stop_event.set()
        for thread in self._threads:
            thread.join(timeout=2)
        self._threads = []

    def run_once(self, worker_id: str | None = None) -> bool:
        record = self._jobs.claim_next_queued_job(worker_id or self._worker_id)
        if record is None:
            return False
        self._logger.info("Claimed job %s", record.job_id)
        self._converter.process(record.job_id, claimed=True)
        return True

    def _run(self, worker_id: str) -> None:
        while not self._stop_event.is_set():
            processed = self.run_once(worker_id)
            if processed:
                continue
            self._stop_event.wait(self._poll_interval_seconds)
