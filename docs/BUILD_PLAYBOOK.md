# Billbridge API - Build Playbook

Use this as your execution checklist whenever you resume work.

## Week 1: Foundation Hardening
1. Add API key auth middleware/dependency. [Done]
2. Introduce `Account` (tenant) model and map users to account. [Done]
3. Remove `X-User-Id` trust model for external API consumers. [Done]
4. Add Alembic and create first migration set.
5. Normalize env/config loading and startup validation.

Exit criteria:
- Protected endpoints reject requests without valid API key.
- Database schema is migration-managed.

## Week 2: Usage Metering (Most Important)
1. Create `POST /v1/usage/record`. [Done]
2. Request payload should include:
- `account_id`
- `event_id` (idempotency key)
- `provider`, `model`
- `input_tokens`, `output_tokens`
3. Add pricing table/service for token -> cost -> credits conversion.
4. Debit wallet atomically and write ledger entry (`entry_type="spend"`).
5. Return structured insufficient-credit response.

Exit criteria:
- Duplicate `event_id` never double-debits.
- Credits decrease correctly for new usage events.

## Week 3: Billing Reliability
1. Improve webhook processing:
- signature verified
- safe metadata parsing
- idempotent processing
2. Add reconciliation job for stuck `initiated` attempts.
3. Add operational logging:
- request id
- account id
- event id
- topup attempt id

Exit criteria:
- Missed webhook events can be recovered safely.
- Billing events are traceable end-to-end.

## Week 4: Developer Experience
1. Version all endpoints under `/v1`. [Done]
2. Write API docs for:
- top-up flow
- usage flow
- webhook setup
3. Provide Postman collection or curl examples.
4. Add integration quickstart in README.

Exit criteria:
- A new developer can integrate in < 1 hour.
- Legacy unversioned endpoints remain temporarily available with deprecation headers until `Tue, 24 Jun 2026 00:00:00 GMT`.

## Week 5: Production Readiness
1. Add rate limiting and abuse controls.
2. Add background workers (retry/reconciliation).
3. Add dashboards/alerts for failed webhooks and payment errors.
4. Add CI pipeline:
- lint
- tests
- migration check

Exit criteria:
- Safe enough for pilot customers.

## Engineering Checklist (Always On)
- Keep secrets in env only.
- Add tests for each endpoint before refactor.
- Add idempotency to all write operations.
- Never mutate ledger history; append-only model.
- Use clear error messages (`400/401/404/409/422/500`).

## Test Checklist Before Every Release
1. Top-up intent success + minimum amount validation.
2. Webhook success credits once.
3. Webhook replay does not double-credit.
4. Balance endpoint reflects latest state.
5. Ledger endpoint returns complete event history.
6. Usage record deducts expected credits. [Done]
7. Duplicate usage event does not double-deduct. [Done]
8. Invalid API key denied. [Done]

## What To Build Next (Single Priority)
Implement Alembic migrations and migration scripts for all current models.  
This unblocks safe schema evolution and production deployment workflows.
