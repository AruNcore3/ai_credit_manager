from __future__ import annotations

import os
import threading
import time
from collections import defaultdict, deque


class Observability:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._counters: dict[str, int] = defaultdict[str, int](int)
        self._latency_sum_ms: dict[str, float] = defaultdict[str, float](float)
        self._latency_count: dict[str, int] = defaultdict[str, int](int)
        self._event_windows: dict[str, deque[float]] = defaultdict[str, deque[float]](deque)

        self._thresholds = {
            "rate_limit_exceeded": int(os.getenv("ALERT_429_PER_MINUTE", "100")),
            "stripe_webhook_invalid_signature": int(os.getenv("ALERT_WEBHOOK_SIG_FAIL_PER_MINUTE", "5")),
            "topup_intent_stripe_error": int(os.getenv("ALERT_STRIPE_FAILURES_PER_MINUTE", "5")),
            "reconciliation_attempt_error": int(os.getenv("ALERT_RECONCILIATION_ERRORS_PER_MINUTE", "3")),
        }

    def observe_request(self, *, method: str, path: str, status: int, latency_ms: float) -> None:
        key = f'{method} {path} {status}'
        latency_key = f'{method} {path}'
        with self._lock:
            self._counters[f"requests_total|{key}"] += 1
            self._latency_sum_ms[latency_key] += latency_ms
            self._latency_count[latency_key] += 1

    def increment_event(self, name: str) -> bool:
        now = time.time()
        with self._lock:
            self._counters[f"events_total|{name}"] += 1
            window = self._event_windows[name]
            window.append(now)
            cutoff = now - 60
            while window and window[0] < cutoff:
                window.popleft()
            threshold = self._thresholds.get(name)
            return threshold is not None and len(window) >= threshold

    def render_prometheus(self) -> str:
        lines: list[str] = []
        with self._lock:
            lines.append("# TYPE billbridge_requests_total counter")
            for raw_key, value in sorted(self._counters.items()):
                metric_name, key = raw_key.split("|", 1)
                if metric_name != "requests_total":
                    continue
                method, path, status = key.split(" ", 2)
                lines.append(
                    f'billbridge_requests_total{{method="{method}",path="{path}",status="{status}"}} {value}'
                )

            lines.append("# TYPE billbridge_events_total counter")
            for raw_key, value in sorted(self._counters.items()):
                metric_name, key = raw_key.split("|", 1)
                if metric_name != "events_total":
                    continue
                lines.append(f'billbridge_events_total{{event="{key}"}} {value}')

            lines.append("# TYPE billbridge_request_latency_ms_avg gauge")
            for key, total in sorted(self._latency_sum_ms.items()):
                count = self._latency_count[key]
                avg = total / count if count else 0
                method, path = key.split(" ", 1)
                lines.append(
                    f'billbridge_request_latency_ms_avg{{method="{method}",path="{path}"}} {avg:.2f}'
                )
        return "\n".join(lines) + "\n"


observability = Observability()
