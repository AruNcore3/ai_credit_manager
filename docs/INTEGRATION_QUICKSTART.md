# Integration Quickstart

This guide is for SaaS developers integrating this service as a mid-cycle credit billing API.

## 1) Prerequisites

- Python 3.11+
- PostgreSQL
- Redis (local Docker is supported)
- Stripe account and Stripe CLI

## 2) Configure environment

Copy `.env.example` to `.env` and set values:

```env
STRIPE_SECRET_KEY=sk_test_REPLACE_ME
STRIPE_WEBHOOK_SECRET=whsec_REPLACE_ME
DATABASE_URL=postgresql://postgres:password@localhost:5432/ai_credit_db
REDIS_URL=redis://localhost:6379/0
API_KEY_HASH_SECRET=replace_with_long_random_secret

RATE_LIMIT_BACKEND=redis
RATE_LIMIT_MAX_REQUESTS=60
RATE_LIMIT_WINDOW_SECONDS=60
RATE_LIMIT_FAIL_OPEN=true
RATE_LIMIT_INCLUDE_PATH=false
```

Notes:
- `API_KEY_HASH_SECRET` is required for API key hashing/validation.
- `STRIPE_WEBHOOK_SECRET` comes from Stripe webhook endpoint setup (step 8).
- Ensure each key is on its own clean line in `.env` (no inline pasted artifacts).

## 3) Install dependencies

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## 4) Start Redis

```bash
docker compose -f docker-compose.redis.yml up -d
```

If Docker daemon is not running (common local issue), use in-memory rate limit temporarily:

```env
RATE_LIMIT_BACKEND=inmemory
```

Then restart the API server after updating `.env`.

## 5) Run DB migrations

```bash
alembic upgrade head
```

## 6) Start API server

```bash
uvicorn app.main:app --reload --port 8000
```

Health check:

```bash
curl http://localhost:8000/
```

Expected:

```json
{"message":"Hello, World!"}
```

## 7) One-time bootstrap: create first API key

`POST /v1/api-keys` is protected by `X-API-Key`, so you need one initial key first.

Run this once to create:
- one account (if missing)
- one user (if missing)
- one API key

```powershell
.venv\Scripts\python.exe scripts\bootstrap_tenant.py `
  --account-name "default-account" `
  --username "owner" `
  --email "owner@example.com" `
  --key-name "bootstrap-key"
```

Save the printed key as `OWNER_API_KEY`.

## 8) Configure Stripe webhook

Expose local server and forward Stripe events:

```bash
stripe listen --forward-to localhost:8000/v1/webhooks/stripe
```

Copy the webhook signing secret (`whsec_...`) from CLI output into `.env` as `STRIPE_WEBHOOK_SECRET`, then restart the API server.

## 9) Core integration flow (copy/paste)

Set variables (PowerShell):

```bash
$env:BASE_URL="http://localhost:8000"
$env:API_KEY="<OWNER_API_KEY>"
```

### 9.1 Create another API key for your app/service

```bash
$body = @{ name = "production-app-key" } | ConvertTo-Json
Invoke-RestMethod -Method Post `
  -Uri "$env:BASE_URL/v1/api-keys" `
  -Headers @{ "X-API-Key" = $env:API_KEY } `
  -ContentType "application/json" `
  -Body $body
```

Response includes:
- `api_key` (show once; store securely)
- `key_prefix`
- `id`

### 9.2 Record model usage from your SaaS app

```bash
$body = @{
  event_id = "evt_001"
  model = "gpt-4.1-mini"
  input_token = 1200
  output_token = 600
} | ConvertTo-Json
Invoke-RestMethod -Method Post `
  -Uri "$env:BASE_URL/v1/usage/record" `
  -Headers @{ "X-API-Key" = $env:API_KEY } `
  -ContentType "application/json" `
  -Body $body
```

Expected response shape:

```json
{
  "event_id": "evt_001",
  "debited_credits": 3,
  "remaining_balance": 97,
  "topup_required": false
}
```

### 9.3 Create a top-up PaymentIntent (mid-cycle billing)

```bash
$body = @{ credits = 5000 } | ConvertTo-Json
Invoke-RestMethod -Method Post `
  -Uri "$env:BASE_URL/v1/payments/topup-intent" `
  -Headers @{
    "X-API-Key" = $env:API_KEY
    "Idempotency-Key" = "topup-evt-001"
  } `
  -ContentType "application/json" `
  -Body $body
```

Response includes:
- `attempt_id`
- `client_secret` (use this in frontend with Stripe.js)
- `amount_cents`
- `idempotency_key`

### 9.4 Check wallet balance

```bash
Invoke-RestMethod -Method Get `
  -Uri "$env:BASE_URL/v1/credits/balance" `
  -Headers @{ "X-API-Key" = $env:API_KEY }
```

### 9.5 Check credit ledger

```bash
Invoke-RestMethod -Method Get `
  -Uri "$env:BASE_URL/v1/credits/ledger" `
  -Headers @{ "X-API-Key" = $env:API_KEY }
```

## 10) 5-minute smoke test checklist

1. `GET /` returns `200`.
2. `POST /v1/usage/record` returns `200` with `topup_required` boolean.
3. `POST /v1/payments/topup-intent` returns `200` with `client_secret`.
4. Stripe webhook endpoint receives forwarded events and returns `{"received": true}`.
5. `GET /v1/credits/balance` and `GET /v1/credits/ledger` return `200`.

## 11) Endpoint map (v1)

- `POST /v1/api-keys`
- `GET /v1/api-keys`
- `POST /v1/api-keys/{key_id}/revoke`
- `POST /v1/api-keys/{key_id}/rotate`
- `POST /v1/usage/record`
- `POST /v1/payments/topup-intent`
- `POST /v1/webhooks/stripe`
- `GET /v1/credits/balance`
- `GET /v1/credits/ledger`

Legacy non-versioned routes are deprecated and currently sunset on `Tue, 24 Jun 2026 00:00:00 GMT`.

## 12) SDK-style client snippets

For ready-to-run Node.js and Python helper functions (`recordUsage`, `createTopupIntent`, `getBalance`, `getLedger`) plus error examples, see:

- [CLIENT_EXAMPLES.md](C:\Users\ASUS\ai-credit-system\docs\CLIENT_EXAMPLES.md)

## 13) OpenAPI export (Postman/client import)

Once the server is running on `http://localhost:8000`, use:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- OpenAPI JSON: `http://localhost:8000/openapi.json`

Import into Postman:
1. Open Postman -> `Import`.
2. Choose `Link` and paste `http://localhost:8000/openapi.json` (or upload exported JSON file).
3. Set collection auth/header `X-API-Key` for protected endpoints.

Optional export to file:

```bash
curl http://localhost:8000/openapi.json -o openapi.json
```

## 14) Production deployment

For production env checklist, migrations, webhook configuration, process layout, and release checks, see:

- [DEPLOYMENT_GUIDE.md](C:\Users\ASUS\ai-credit-system\docs\DEPLOYMENT_GUIDE.md)
