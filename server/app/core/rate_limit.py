from __future__ import annotations

from collections import deque
import threading
import time


class SlidingWindowRateLimiter:
    def __init__(self, *, max_requests: int, window_seconds: int) -> None:
        self._max_requests = max_requests
        self._window_seconds = window_seconds
        self._events: dict[str, deque[float]] = {}
        self._lock = threading.Lock()

    def allow(self, key: str) -> bool:
        now = time.time()
        threshold = now - self._window_seconds
        with self._lock:
            queue = self._events.setdefault(key, deque())
            while queue and queue[0] < threshold:
                queue.popleft()
            if len(queue) >= self._max_requests:
                return False
            queue.append(now)
            return True
