"""API key authentication for the query and search endpoints.

Both endpoints run real embedding and cross encoder inference per request, and
the EC2 origin is reachable directly rather than only through the Vercel
frontend, so an open endpoint is an open door to someone else's compute bill.

Authentication is opt in. With ``api_key`` empty the checks pass and the
endpoints are open, which is how they have always run locally and in CI.
Setting ``app_env=production`` without a key is treated as a mistake rather
than a choice, and the app refuses to start.
"""

from __future__ import annotations

import hmac
from typing import Annotated

from fastapi import Header, HTTPException, status

from core.config import settings

ApiKeyHeader = Annotated[str | None, Header(alias="X-API-Key")]

PRODUCTION = "production"


def require_api_key(x_api_key: ApiKeyHeader = None) -> None:
    """Reject a request that does not carry the configured API key.

    Comparison goes through :func:`hmac.compare_digest` on the encoded bytes so
    a wrong key takes the same time to reject whatever its contents, and so a
    header byte above 127 cannot raise ``TypeError`` out of the comparison.
    Starlette decodes headers as latin-1, so that is a reachable input, not a
    theoretical one. The length of the supplied key still leaks, which is
    inherent to comparing strings of different sizes.
    """
    expected = settings.api_key
    if not expected:
        return
    if x_api_key is not None and hmac.compare_digest(
        x_api_key.encode("utf-8"), expected.encode("utf-8")
    ):
        return
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="A valid X-API-Key header is required on this endpoint.",
    )


def verify_production_config() -> None:
    """Refuse to serve production traffic without a key.

    Called from each app's startup, so the failure happens where it is visible
    rather than on the first unauthenticated request.
    """
    if settings.app_env.strip().lower() == PRODUCTION and not settings.api_key:
        raise RuntimeError(
            "api_key is not set while app_env=production. Set API_KEY, or leave app_env at "
            "its default to run the open development configuration."
        )
