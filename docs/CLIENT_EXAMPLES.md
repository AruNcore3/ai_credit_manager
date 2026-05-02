## Node.js

```js
const BASE_URL = process.env.BASE_URL || "http://localhost:8000";
const API_KEY = process.env.API_KEY;
const IDEMPOTENCY_KEY = process.env.IDEMPOTENCY_KEY || `topup_${Date.now()}`;

if (!API_KEY) {
  throw new Error("Missing API_KEY environment variable");
}

async function api(path, { method = "GET", body, headers = {} } = {}) {
  const res = await fetch(`${BASE_URL}${path}`, {
    method,
    headers: {
      "Content-Type": "application/json",
      "X-API-Key": API_KEY,
      ...headers,
    },
    body: body ? JSON.stringify(body) : undefined,
  });

  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(`HTTP ${res.status}: ${JSON.stringify(data)}`);
  }
  return data;
}

async function recordUsage(payload) {
  return api("/v1/usage/record", { method: "POST", body: payload });
}

async function createTopupIntent(credits, idempotencyKey = IDEMPOTENCY_KEY) {
  return api("/v1/payments/topup-intent", {
    method: "POST",
    body: { credits },
    headers: { "Idempotency-Key": idempotencyKey },
  });
}

async function getBalance() {
  return api("/v1/credits/balance");
}

async function getLedger() {
  return api("/v1/credits/ledger");
}

// Example
async function run() {
  const balance = await getBalance();
  console.log("Balance:", balance);

  const usage = await recordUsage({
    event_id: `evt_${Date.now()}`,
    model: "gpt-4.1-mini",
    input_token: 1200,
    output_token: 600,
  });
  console.log("Usage result:", usage);

  if (usage.topup_required) {
    const topup = await createTopupIntent(5000);
    console.log("Top-up intent:", topup);
  }

  console.log("Ledger:", await getLedger());
}

run().catch((err) => {
  console.error(err.message);
  process.exit(1);
});
```

Request example (`recordUsage`):

```json
{
  "event_id": "evt_001",
  "model": "gpt-4.1-mini",
  "input_token": 1200,
  "output_token": 600
}
```

Success response example:

```json
{
  "event_id": "evt_001",
  "debited_credits": 3,
  "remaining_balance": 97,
  "topup_required": false
}
```

Basic error handling examples:

- `401 invalid key`

```json
{
  "detail": "invalid API key"
}
```

- `400 bad payload / Stripe error`

```json
{
  "detail": "credits must be > 0"
}
```

```json
{
  "detail": "stripe error: <stripe-message>"
}
```

- `429 rate limit exceeded`

```json
{
  "detail": "rate limit exceeded"
}
```

Mini flow:
- `getBalance()` -> `recordUsage()` -> if `topup_required` then `createTopupIntent()` -> `getBalance()` -> `getLedger()`

## Python

```python
import os
import time
import requests

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
API_KEY = os.getenv("API_KEY")
IDEMPOTENCY_KEY = os.getenv("IDEMPOTENCY_KEY", f"topup_{int(time.time())}")

if not API_KEY:
    raise RuntimeError("Missing API_KEY environment variable")


def api(path: str, method: str = "GET", body: dict | None = None, headers: dict | None = None):
    req_headers = {
        "Content-Type": "application/json",
        "X-API-Key": API_KEY,
    }
    if headers:
        req_headers.update(headers)

    response = requests.request(
        method=method,
        url=f"{BASE_URL}{path}",
        json=body,
        headers=req_headers,
        timeout=30,
    )

    try:
        data = response.json()
    except ValueError:
        data = {}

    if not response.ok:
        raise RuntimeError(f"HTTP {response.status_code}: {data}")
    return data


def record_usage(event_id: str, model: str, input_token: int, output_token: int):
    return api(
        "/v1/usage/record",
        method="POST",
        body={
            "event_id": event_id,
            "model": model,
            "input_token": input_token,
            "output_token": output_token,
        },
    )


def create_topup_intent(credits: int, idempotency_key: str = IDEMPOTENCY_KEY):
    return api(
        "/v1/payments/topup-intent",
        method="POST",
        body={"credits": credits},
        headers={"Idempotency-Key": idempotency_key},
    )


def get_balance():
    return api("/v1/credits/balance")


def get_ledger():
    return api("/v1/credits/ledger")


if __name__ == "__main__":
    balance = get_balance()
    print("Balance:", balance)

    usage = record_usage(
        event_id=f"evt_{int(time.time())}",
        model="gpt-4.1-mini",
        input_token=1200,
        output_token=600,
    )
    print("Usage result:", usage)

    if usage.get("topup_required"):
        topup = create_topup_intent(credits=5000)
        print("Top-up intent:", topup)

    print("Balance after flow:", get_balance())
    print("Ledger:", get_ledger())
```

Request example (`record_usage`):

```json
{
  "event_id": "evt_001",
  "model": "gpt-4.1-mini",
  "input_token": 1200,
  "output_token": 600
}
```

Success response example:

```json
{
  "event_id": "evt_001",
  "debited_credits": 3,
  "remaining_balance": 97,
  "topup_required": false
}
```

Basic error handling examples:

- `401 invalid key`

```json
{
  "detail": "invalid API key"
}
```

- `400 bad payload / Stripe error`

```json
{
  "detail": "credits must be > 0"
}
```

```json
{
  "detail": "stripe error: <stripe-message>"
}
```

- `429 rate limit exceeded`

```json
{
  "detail": "rate limit exceeded"
}
```

Mini flow:
- `get_balance()` -> `record_usage()` -> if `topup_required` then `create_topup_intent()` -> `get_balance()` -> `get_ledger()`
