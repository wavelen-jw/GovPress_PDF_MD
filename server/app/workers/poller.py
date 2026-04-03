from __future__ import annotations

import logging
import socket
import threading
import time

from ..core.notify import send_telegram
from ..repositories import JobRepository
from .converter_worker import ConverterWorker

_LONG_WAIT_MINUTES = 5   # 이 시간 이상 대기 중인 작업이 있으면 알림
_CHECK_EVERY_N = 20      # N번 폴링마다 장시간 대기 점검 (3s × 20 ≈ 60s)


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
        self._poll_count = 0

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

    def _check_long_wait(self) -> None:
        try:
            from ..models import utcnow
            threshold = _LONG_WAIT_MINUTES * 60
            jobs = self._jobs.list_page(limit=10, status="queued")[0]
            for job in jobs:
                waited = (utcnow() - job.created_at).total_seconds()
                if waited >= threshold:
                    send_telegram(
                        f"⏳ GovPress 장시간 대기\n"
                        f"파일: {job.file_name}\n"
                        f"대기 시간: {int(waited // 60)}분"
                    )
                    break
        except Exception:
            pass

    def _run(self, worker_id: str) -> None:
        while not self._stop_event.is_set():
            processed = self.run_once(worker_id)
            self._poll_count += 1
            if self._poll_count % _CHECK_EVERY_N == 0:
                self._check_long_wait()
            if processed:
                continue
            self._stop_event.wait(self._poll_interval_seconds)
