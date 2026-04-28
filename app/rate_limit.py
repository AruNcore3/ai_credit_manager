from __future__ import annotations

import os
import threading
import time
from dataclasses import dataclass


@dataclass
class RateLimitDecision:
    allowed: bool
    limit: int
    remaining: int
    reset_after: int


class InMemoryRateLimiter:
    def __init__(self, *, limit: int, window_seconds: int):
        self.limit = max(1, limit)
        self.window_seconds = max(1, window_seconds)
        self._lock = threading.Lock()
        self._buckets: dict[str, tuple[float, int]] = {}

    def check(self, key: str, now: float | None = None) -> RateLimitDecision:
        current = time.time() if now is None else now

        with self._lock:
            start, count = self._buckets.get(key, (current, 0))

            if current - start >= self.window_seconds:
                start = current
                count = 0

            if count >= self.limit:
                reset_after = max(1, int(self.window_seconds - (current - start)))
                return RateLimitDecision(
                    allowed=False,
                    limit=self.limit,
                    remaining=0,
                    reset_after=reset_after,
                )

            count += 1
            self._buckets[key] = (start, count)
            remaining = self.limit - count
            reset_after = max(1, int(self.window_seconds - (current - start)))

            return RateLimitDecision(
                allowed=True,
                limit=self.limit,
                remaining=remaining,
                reset_after=reset_after,
            )

    def reset(self) -> None:
        with self._lock:
            self._buckets.clear()


def build_rate_limiter() -> InMemoryRateLimiter:
    limit = int(os.getenv("RATE_LIMIT_MAX_REQUESTS", "60"))
    window_seconds = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))
    return InMemoryRateLimiter(limit=limit, window_seconds=window_seconds)
