from __future__ import annotations

import time


def monotonic_ns() -> int:
    """Monotonic timestamp for latency intervals."""
    return time.monotonic_ns()


def realtime_ns() -> int:
    """Wall-clock timestamp for logs. Do not use for latency intervals."""
    return time.time_ns()
