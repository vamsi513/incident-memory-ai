"""API key authentication on the query and search endpoints.

The key lives on the cached ``Settings`` singleton, so these tests set the
attribute directly rather than the environment, which is what the running apps
read too.
"""

from unittest.mock import patch

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.main import app as query_app
from core import rate_limit
from core.auth import require_api_key, verify_production_config
from core.config import settings

KEY = "incident-memory-test-key"


@pytest.fixture(autouse=True)
def _reset_rate_counters():
    rate_limit._rate_counters.clear()
    yield
    rate_limit._rate_counters.clear()


# --------------------------------------------------------------- the dependency


def test_a_request_is_allowed_when_no_key_is_configured(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(settings, "api_key", "")
    assert require_api_key(None) is None


def test_the_configured_key_is_accepted(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(settings, "api_key", KEY)
    assert require_api_key(KEY) is None


def test_a_wrong_key_is_rejected(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(settings, "api_key", KEY)
    with pytest.raises(HTTPException) as exc_info:
        require_api_key("not-the-key")
    assert exc_info.value.status_code == 401


def test_a_key_that_is_a_prefix_of_the_real_one_is_rejected(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(settings, "api_key", KEY)
    with pytest.raises(HTTPException) as exc_info:
        require_api_key(KEY[:-1])
    assert exc_info.value.status_code == 401


def test_a_missing_header_is_rejected_when_a_key_is_configured(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(settings, "api_key", KEY)
    with pytest.raises(HTTPException) as exc_info:
        require_api_key(None)
    assert exc_info.value.status_code == 401


def test_a_non_ascii_header_is_rejected_rather_than_raising(monkeypatch: pytest.MonkeyPatch):
    """compare_digest on str raises TypeError here, so the bytes are compared."""
    monkeypatch.setattr(settings, "api_key", KEY)
    with pytest.raises(HTTPException) as exc_info:
        require_api_key("token-with-an-accent-é")
    assert exc_info.value.status_code == 401


# ------------------------------------------------------------ the startup check


def test_production_without_a_key_refuses_to_start(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(settings, "app_env", "production")
    monkeypatch.setattr(settings, "api_key", "")
    with pytest.raises(RuntimeError, match="api_key"):
        verify_production_config()


def test_production_with_a_key_starts(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(settings, "app_env", "production")
    monkeypatch.setattr(settings, "api_key", KEY)
    assert verify_production_config() is None


def test_development_without_a_key_starts(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(settings, "app_env", "dev")
    monkeypatch.setattr(settings, "api_key", "")
    assert verify_production_config() is None


# ----------------------------------------------------------------- /query (app)


def test_query_is_rejected_without_the_key(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(settings, "api_key", KEY)
    client = TestClient(query_app)
    response = client.post("/query", json={"query": "what caused the checkout timeout?"})
    assert response.status_code == 401


def test_query_accepts_the_configured_key(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(settings, "api_key", KEY)
    chunks = [{"text": "Database failover caused the outage.", "source": "incident-42"}]
    client = TestClient(query_app)
    with (
        patch("app.main.run_retrieval", return_value=chunks),
        patch("app.main.generate_answer", return_value="Mocked answer."),
    ):
        response = client.post(
            "/query",
            json={"query": "what caused the checkout timeout?"},
            headers={"X-API-Key": KEY},
        )
    assert response.status_code == 200, response.text


def test_query_health_stays_open_when_a_key_is_configured(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(settings, "api_key", KEY)
    client = TestClient(query_app)
    assert client.get("/health").status_code == 200


# ------------------------------------------------------- /v1/search and /facets


@pytest.mark.asyncio
async def test_search_is_rejected_without_the_key(async_client, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(settings, "api_key", KEY)
    response = await async_client.post("/v1/search", json={"query": "checkout", "top_k": 3})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_facets_is_rejected_without_the_key(async_client, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(settings, "api_key", KEY)
    response = await async_client.get("/v1/facets")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_facets_accepts_the_configured_key(async_client, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(settings, "api_key", KEY)
    response = await async_client.get("/v1/facets", headers={"X-API-Key": KEY})
    assert response.status_code == 200, response.text


@pytest.mark.asyncio
async def test_api_health_stays_open_when_a_key_is_configured(
    async_client, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr(settings, "api_key", KEY)
    response = await async_client.get("/health")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_endpoints_stay_open_when_no_key_is_configured(
    async_client, monkeypatch: pytest.MonkeyPatch
):
    """The development default: a caller that sends no key is unaffected."""
    monkeypatch.setattr(settings, "api_key", "")
    response = await async_client.get("/v1/facets")
    assert response.status_code == 200, response.text
