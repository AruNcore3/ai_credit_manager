# Usage API Contract

## Endpoint
- `POST /v1/usage/record`

## API Endpoint Map
- `POST /v1/payments/topup-intent`
- `GET /v1/credits/balance`
- `GET /v1/credits/ledger`
- `POST /v1/webhooks/stripe`
- `POST /v1/usage/record`

Legacy compatibility (deprecated, temporary until `Tue, 24 Jun 2026 00:00:00 GMT`):
- `POST /payments/topup-intent`
- `GET /credits/balance`
- `GET /credits/ledger`
- `POST /webhooks/stripe`

## Authentication
- Header: `X-API-Key: <api_key>`
- Missing API key: `401` with `{"detail":"missing API key"}`
- Invalid API key: `401` with `{"detail":"invalid API key"}`

## Request Body
```json
{
  "event_id": "evt_123",
  "model": "gpt-4.1-mini",
  "input_token": 1200,
  "output_token": 600
}
```

## Success Response (`200`)
```json
{
  "event_id": "evt_123",
  "debited_credits": 3,
  "remaining_balance": 97,
  "topup_required": false
}
```

## Behavior Guarantees
- Idempotent by `event_id` per authenticated user.
- Duplicate `event_id` does not create additional spend ledger entries.
- Zero-token usage does not debit credits.
- Insufficient balance returns `topup_required=true` and no spend ledger row is written.

## Error Schema
Current error format is FastAPI default:
```json
{
  "detail": "<message>"
}
```

Common status codes:
- `400` invalid usage payload values (for example negative token counts)
- `401` missing or invalid API key
- `403` inactive user
- `422` request validation error

## Request Tracing
- Every response includes `X-Request-Id`.
- Clients can send their own `X-Request-Id` value; otherwise server generates one.
