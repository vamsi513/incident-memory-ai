import logging
import time
from collections.abc import Iterator
from contextlib import contextmanager

logger = logging.getLogger(__name__)


@contextmanager
def traced_span(name: str) -> Iterator[None]:
    """
    Log wall-clock duration for a pipeline stage.

    Not a real tracer -- no distributed context propagation, no exporter, no
    sampling, just a timed log line. Grep production logs for 'stage_timing'
    to derive per-stage p50/p95 without adding a tracing dependency. Swap
    this for real OpenTelemetry/LangSmith tracer.start_as_current_span(name)
    wiring if/when an actual observability backend is configured -- this was
    previously a placeholder that discarded `name` and did nothing, giving
    the appearance of instrumentation while producing zero data.
    """
    start = time.perf_counter()
    try:
        yield
    finally:
        duration_ms = (time.perf_counter() - start) * 1000
        logger.info("stage_timing stage=%s duration_ms=%.1f", name, duration_ms)
