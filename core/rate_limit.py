"""
core/rate_limit.py — Simple in-process per-IP rate limiter.

The /v1/search endpoint runs real embedding + cross-encoder inference per
request and is reachable directly (the Vercel frontend proxies to it, but
nothing stops a client from hitting the EC2 origin directly), so an
unlimited public endpoint is an open door to running up compute cost.

In-process only — correct for the current single-instance EC2 deployment.
A multi-replica deployment would need a shared store (Redis, etc.) for
this to mean anything across instances.
"""

import collections
import time

from fastapi import HTTPException, Request, status

_RATE_LIMIT = 20
_RATE_WINDOW = 60.0
_MAX_TRACKED_IPS = 2000
_rate_counters: dict[str, collections.deque] = {}


def _client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def check_rate_limit(request: Request) -> None:
    client_ip = _client_ip(request)
    now = time.monotonic()

    if client_ip not in _rate_counters:
        # Evict oldest entry when the table is full to bound memory usage.
        if len(_rate_counters) >= _MAX_TRACKED_IPS:
            _rate_counters.pop(next(iter(_rate_counters)))
        # maxlen bounds each deque to at most _RATE_LIMIT + 1 entries.
        _rate_counters[client_ip] = collections.deque(maxlen=_RATE_LIMIT + 1)

    timestamps = _rate_counters[client_ip]
    while timestamps and timestamps[0] < now - _RATE_WINDOW:
        timestamps.popleft()
    if len(timestamps) >= _RATE_LIMIT:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Max {_RATE_LIMIT} requests per minute.",
        )
    timestamps.append(now)
