from contextlib import contextmanager
from typing import Iterator


@contextmanager
def traced_span(name: str) -> Iterator[None]:
    """
    Placeholder for OpenTelemetry/LangSmith instrumentation.

    Replace this with real tracer.start_as_current_span(name) wiring once
    observability backends are configured.
    """

    _ = name
    yield
