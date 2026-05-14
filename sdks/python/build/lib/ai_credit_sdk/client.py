import os
import requests


class _UsageApi:
    def __init__(self, client):
        self._client = client

    def record(self, payload: dict):
        return self._client._request("POST", "/usage/record", payload)


class _PaymentsApi:
    def __init__(self, client):
        self._client = client

    def create_topup_intent(self, payload: dict):
        return self._client._request("POST", "/payments/topup-intent", payload)


class _CreditsApi:
    def __init__(self, client):
        self._client = client

    def balance(self):
        return self._client._request("GET", "/credits/balance")

    def ledger(self):
        return self._client._request("GET", "/credits/ledger")


class AICreditClient:
    def __init__(self, api_key: str | None = None, base_url: str | None = None):
        self.api_key = api_key or os.getenv("AI_CREDIT_API_KEY")
        self.base_url = base_url or os.getenv("AI_CREDIT_BASE_URL", "https://api.yourdomain.com/v1")
        self.usage = _UsageApi(self)
        self.payments = _PaymentsApi(self)
        self.credits = _CreditsApi(self)

    def _request(self, method: str, path: str, payload: dict | None = None):
        response = requests.request(
            method,
            f"{self.base_url}{path}",
            headers={"X-API-Key": self.api_key},
            json=payload,
            timeout=30,
        )
        response.raise_for_status()
        return response.json()
