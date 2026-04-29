from __future__ import annotations

import pytest
from redis.exceptions import RedisError

from app.rate_limit import RedisRateLimiter


class _ScriptOk:
    def __init__(self, values: list[tuple[int, int]]):
        self.values = values
        self.calls: list[tuple[list[str], list[int]]] = []

    def __call__(self, *, keys, args):  # noqa: ANN001
        self.calls.append((keys, args))
        return self.values.pop(0)


class _ScriptError:
    def __call__(self, *, keys, args):  # noqa: ANN001
        raise RedisError("redis unavailable")


class _FakeRedis:
    def __init__(self, script):
        self._script = script

    def register_script(self, script_text: str):  # noqa: ARG002
        return self._script


def test_redis_limiter_blocks_after_limit():
    script = _ScriptOk(values=[(1, 60), (2, 59), (3, 58)])
    limiter = RedisRateLimiter(client=_FakeRedis(script), limit=2, window_seconds=60, fail_open=True)

    first = limiter.check("k1")
    second = limiter.check("k1")
    third = limiter.check("k1")

    assert first.allowed is True
    assert first.remaining == 1
    assert second.allowed is True
    assert second.remaining == 0
    assert third.allowed is False
    assert third.remaining == 0
    assert third.reset_after == 58


def test_redis_limiter_uses_scoped_key():
    script = _ScriptOk(values=[(1, 60)])
    limiter = RedisRateLimiter(client=_FakeRedis(script), limit=5, window_seconds=60, fail_open=True)

    limiter.check("api_key_123", scope="/v1/credits/balance", now=120.0)
    called_key = script.calls[0][0][0]
    assert called_key == "rl:api_key_123:/v1/credits/balance:2"


def test_redis_limiter_fail_open_when_redis_unavailable():
    limiter = RedisRateLimiter(client=_FakeRedis(_ScriptError()), limit=3, window_seconds=60, fail_open=True)
    decision = limiter.check("k1")
    assert decision.allowed is True
    assert decision.remaining == 3


def test_redis_limiter_fail_closed_when_redis_unavailable():
    limiter = RedisRateLimiter(client=_FakeRedis(_ScriptError()), limit=3, window_seconds=60, fail_open=False)
    with pytest.raises(RedisError):
        limiter.check("k1")
