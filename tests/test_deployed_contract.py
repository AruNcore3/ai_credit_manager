from __future__ import annotations

import os

import pytest
import requests


BASE_URL = os.getenv("DEPLOYED_BASE_URL")
API_KEY = os.getenv("DEPLOYED_API_KEY")


@pytest.mark.skipif(not BASE_URL, reason="DEPLOYED_BASE_URL is not configured")
def test_openapi_and_docs_are_public():
    openapi = requests.get(f"{BASE_URL}/openapi.json", timeout=20)
    assert openapi.status_code == 200
    schema = openapi.json()
    assert schema.get("openapi")
    assert schema.get("paths")
    assert "/v1/usage/record" in schema["paths"]

    docs = requests.get(f"{BASE_URL}/docs", timeout=20)
    assert docs.status_code == 200


@pytest.mark.skipif(not BASE_URL, reason="DEPLOYED_BASE_URL is not configured")
def test_v1_endpoint_requires_api_key():
    response = requests.get(f"{BASE_URL}/v1/credits/balance", timeout=20)
    assert response.status_code == 401


@pytest.mark.skipif(not BASE_URL or not API_KEY, reason="DEPLOYED_BASE_URL or DEPLOYED_API_KEY is not configured")
def test_v1_balance_with_api_key():
    response = requests.get(
        f"{BASE_URL}/v1/credits/balance",
        headers={"X-API-Key": API_KEY},
        timeout=20,
    )
    assert response.status_code == 200
    body = response.json()
    assert "balance" in body
