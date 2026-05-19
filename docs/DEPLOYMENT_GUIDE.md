# Deployment Guide (Production)

This guide covers deploying the API reliably for production use.

## 1) Required environment variables

Set these in your deployment platform secret manager:

```env
STRIPE_SECRET_KEY=sk_live_xxx
STRIPE_WEBHOOK_SECRET=whsec_xxx
DATABASE_URL=postgresql+psycopg2://user:password@host:5432/dbname
API_KEY_HASH_SECRET=<long-random-secret>

REDIS_URL=redis://<user>:<password>@<host>:6379/0
RATE_LIMIT_BACKEND=redis
RATE_LIMIT_MAX_REQUESTS=60
RATE_LIMIT_WINDOW_SECONDS=60
RATE_LIMIT_FAIL_OPEN=true
RATE_LIMIT_INCLUDE_PATH=false
ALERT_429_PER_MINUTE=100
ALERT_WEBHOOK_SIG_FAIL_PER_MINUTE=5
ALERT_STRIPE_FAILURES_PER_MINUTE=5
ALERT_RECONCILIATION_ERRORS_PER_MINUTE=3
```

Recommended:
- Keep `RATE_LIMIT_BACKEND=redis` in production.
- Use a managed PostgreSQL and managed Redis.
- Rotate `API_KEY_HASH_SECRET` with an explicit migration plan.

Render-specific checks:
- Do not use `localhost` for `DATABASE_URL` in Render.
- Use the Render Postgres connection string from your Render database service.
- Keep `DATABASE_URL` as an environment variable in Render dashboard (or Blueprint sync).

## 2) Install and run migrations

Run once per release before serving traffic:

```bash
alembic upgrade head
```

## 3) API process layout

Use a process manager or container orchestrator and run:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Behind a reverse proxy/load balancer:
- Terminate TLS at proxy/LB.
- Forward traffic to app on port `8000`.
- Preserve headers needed for tracing/logging.

Render production start command:
```bash
alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

This is already captured in `render.yaml`.

## 3.1) Render domain and DNS

For this project:
- Public API domain: `https://api.billbridge.in`
- Render origin: `bill-bridge-32mb.onrender.com`

DNS record in your domain provider:
- Type: `CNAME`
- Host/Name: `api`
- Target/Value: `bill-bridge-32mb.onrender.com`

After DNS propagation and cert issuance, verify:
1. `https://api.billbridge.in/openapi.json`
2. `https://api.billbridge.in/docs`
3. `https://api.billbridge.in/v1/credits/balance` with `X-API-Key`

## 4) Stripe webhook setup

Create webhook endpoint in Stripe dashboard:

- URL: `https://<your-domain>/v1/webhooks/stripe`
- Event: `payment_intent.succeeded`

Then set the returned signing secret as:
- `STRIPE_WEBHOOK_SECRET`

Validation:
1. Send a Stripe test event.
2. Confirm API returns `{"received": true}`.
3. Confirm credits are applied once (idempotent behavior).

## 5) Reconciliation job (recommended)

Purpose:
- Recover top-ups if webhook delivery was delayed/missed.

Current service function:
- `services.reconcilation_service.reconile_initiated_topups`

Run this periodically (for example every 5 minutes) using your scheduler/worker.
Use the provided runner script:

```bash
python scripts/run_reconciliation.py --older-than-minutes 5 --limit 100
```

Example cron (Linux, every 5 minutes):

```cron
*/5 * * * * cd /srv/ai-credit-system && /srv/ai-credit-system/.venv/bin/python scripts/run_reconciliation.py --older-than-minutes 5 --limit 100 >> /var/log/ai-credit-reconciliation.log 2>&1
```

Suggested schedule:
- Every 5 minutes
- `older_than_minutes=5`
- `limit=100` (tune as volume grows)

## 6) Health checks

Minimum checks:
1. Liveness: `GET /` returns `200`.
2. Readiness: application starts with valid env vars and DB connectivity.
3. Dependency checks:
- Redis reachable (if `RATE_LIMIT_BACKEND=redis`)
- Stripe reachable for payment-intent creation paths

## 7) Logging and alerts

Track and alert on:
1. `429` rate-limit spikes
2. webhook signature failures (`invalid webhook signature`)
3. Stripe request failures on top-up intent creation
4. reconciliation errors and backlog growth
5. unusually high `topup_required=true` responses

Event signals now emitted by service logs:
- `rate_limit_exceeded` (429 decisions)
- `topup_intent_rejected` and `topup_intent_stripe_error` (top-up failures)
- `stripe_webhook_invalid_signature` (webhook auth failures)
- `insufficient_credits` (usage request exceeded balance)
- `reconciliation_summary` and `reconciliation_attempt_error` (worker health/outliers)
- `alert_triggered type=...` (threshold-based critical alert signal)

Metrics endpoint:
- `GET /internal/metrics` (requires `X-Admin-Token`)
- Prometheus-style counters/gauges:
  - `billbridge_requests_total{method,path,status}`
  - `billbridge_events_total{event}`
  - `billbridge_request_latency_ms_avg{method,path}`

Alerting baseline:
1. `rate_limit_exceeded` above normal per minute.
2. `topup_intent_stripe_error` non-zero over rolling 5 minutes.
3. `stripe_webhook_invalid_signature` > 0 in production.
4. `reconciliation_attempt_error` > 0 or `summary.error > 0`.
5. sustained increase in `insufficient_credits` against baseline.
6. high `5xx` share derived from `billbridge_requests_total` by status.

## 8) Release checklist

1. Env vars set and verified.
2. `alembic upgrade head` applied successfully.
3. API healthy behind domain/TLS.
4. Stripe webhook configured to `/v1/webhooks/stripe`.
5. Reconciliation schedule enabled.
6. Smoke tests pass:
- `GET /`
- `POST /v1/usage/record`
- `POST /v1/payments/topup-intent`
- `GET /v1/credits/balance`
- `GET /v1/credits/ledger`
