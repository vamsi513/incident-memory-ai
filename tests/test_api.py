import pytest


@pytest.mark.asyncio
async def test_search_endpoint_returns_parent_results(async_client):
    response = await async_client.post(
        "/v1/search",
        json={"query": "What fixed the checkout timeout incident?", "top_k": 3},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["query"] == "What fixed the checkout timeout incident?"
    assert payload["results"]
    assert payload["results"][0]["parent_id"] == "incident_2025_01_checkout_timeout"
