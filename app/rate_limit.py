from __future__ import annotations

import os
import threading
import time
from dataclasses import dataclass
from typing import Protocol

from redis import Redis
from redis.exceptions import RedisError


@dataclass
class RateLimitDecision:
    allowed: bool
    limit: int
    remaining: int
    reset_after: int


class RateLimiter(Protocol):
    def check(self, key: str, *, scope: str | None = None, now: float | None = None) -> RateLimitDecision:
        ...

    def reset(self) -> None:
        ...


class InMemoryRateLimiter:
    def __init__(self, *, limit: int, window_seconds: int):
        self.limit = max(1, limit)
        self.window_seconds = max(1, window_seconds)
        self._lock = threading.Lock()
        self._buckets: dict[str, tuple[float, int]] = {}

    def check(self, key: str, *, scope: str | None = None, now: float | None = None) -> RateLimitDecision:
        current = time.time() if now is None else now
        bucket_key = f"{key}:{scope}" if scope else key

        with self._lock:
            start, count = self._buckets.get(bucket_key, (current, 0))

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
            self._buckets[bucket_key] = (start, count)
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


class RedisRateLimiter:
    _SCRIPT = """
local key = KEYS[1]
local window = tonumber(ARGV[1])
local count = redis.call('INCR', key)
if count == 1 then
  redis.call('EXPIRE', key, window)
end
local ttl = redis.call('TTL', key)
return {count, ttl}
"""

    def __init__(
        self,
        *,
        client: Redis,
        limit: int,
        window_seconds: int,
        fail_open: bool = True,
        key_prefix: str = "rl",
    ):
        self.client = client
        self.limit = max(1, limit)
        self.window_seconds = max(1, window_seconds)
        self.fail_open = fail_open
        self.key_prefix = key_prefix
        self._script = self.client.register_script(self._SCRIPT)

    def _window_slot(self, current: float) -> int:
        return int(current // self.window_seconds)

    def _build_key(self, key: str, scope: str | None, slot: int) -> str:
        if scope:
            return f"{self.key_prefix}:{key}:{scope}:{slot}"
        return f"{self.key_prefix}:{key}:{slot}"

    def _degraded_allow(self) -> RateLimitDecision:
        return RateLimitDecision(
            allowed=True,
            limit=self.limit,
            remaining=self.limit,
            reset_after=self.window_seconds,
        )

    def check(self, key: str, *, scope: str | None = None, now: float | None = None) -> RateLimitDecision:
        current = time.time() if now is None else now
        slot = self._window_slot(current)
        redis_key = self._build_key(key=key, scope=scope, slot=slot)

        try:
            count, ttl = self._script(keys=[redis_key], args=[self.window_seconds])
        except RedisError:
            if self.fail_open:
                return self._degraded_allow()
            raise

        request_count = int(count)
        ttl_seconds = max(1, int(ttl))
        if request_count > self.limit:
            return RateLimitDecision(
                allowed=False,
                limit=self.limit,
                remaining=0,
                reset_after=ttl_seconds,
            )

        return RateLimitDecision(
            allowed=True,
            limit=self.limit,
            remaining=self.limit - request_count,
            reset_after=ttl_seconds,
        )

    def reset(self) -> None:
        return None


def build_rate_limiter() -> RateLimiter:
    limit = int(os.getenv("RATE_LIMIT_MAX_REQUESTS", "60"))
    window_seconds = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))
    backend = os.getenv("RATE_LIMIT_BACKEND", "redis").strip().lower()
    fail_open = os.getenv("RATE_LIMIT_FAIL_OPEN", "true").strip().lower() in {"1", "true", "yes", "on"}

    if backend == "inmemory":
        return InMemoryRateLimiter(limit=limit, window_seconds=window_seconds)

    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    client = Redis.from_url(redis_url, decode_responses=True)
    return RedisRateLimiter(
        client=client,
        limit=limit,
        window_seconds=window_seconds,
        fail_open=fail_open,
    )
