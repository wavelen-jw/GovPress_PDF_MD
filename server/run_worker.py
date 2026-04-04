from __future__ import annotations

import argparse
import logging
import time
from pathlib import Path

from server.app.repositories import SQLiteJobRepository
from server.app.services.storage_service import StorageService
from server.app.workers.converter_worker import ConverterWorker
from server.app.workers.poller import PollingWorker


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the GovPress polling worker.")
    parser.add_argument("--storage-root", type=Path, default=Path(__file__).resolve().parents[1] / "storage")
    parser.add_argument("--poll-interval", type=float, default=1.0)
    parser.add_argument("--concurrency", type=int, default=1)
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    storage = StorageService(args.storage_root)
    jobs = SQLiteJobRepository(storage.root / "jobs.sqlite3")
    jobs.recover_incomplete_jobs()
    converter = ConverterWorker(jobs=jobs, storage=storage, logger=logging.getLogger("govpress.converter"))
    poller = PollingWorker(
        jobs=jobs,
        converter=converter,
        poll_interval_seconds=args.poll_interval,
        concurrency=args.concurrency,
        logger=logging.getLogger("govpress.poller"),
    )
    poller.start()
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        pass
    finally:
        poller.stop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
