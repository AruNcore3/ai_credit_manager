# Production Readiness Checklist

## 1) Public API Domain + TLS
- Terminate TLS at Cloudflare/AWS ALB.
- Route `api.yourdomain.com` -> FastAPI service.
- Keep only `/v1` as stable public surface.

## 2) Self-Serve Onboarding
- Implemented: `POST /v1/onboarding/signup` creates account, user, and first API key.

## 3) API Key Management
- Implemented: create/list/rotate/revoke under `/v1/api-keys`.

## 4) Versioning + Deprecation
- See `docs/policies/API_VERSIONING_POLICY.md`.

## 5) OpenAPI Quality
- Public: `/openapi.json`, `/docs`, `/reference`.

## 6-7) SDKs + Interface
- Node scaffold in `sdks/node`.
- Python scaffold in `sdks/python`.
- Interface groups: `usage`, `payments`, `credits`.

## 8) Auth Docs
- See `docs/policies/AUTH_AND_KEY_SECURITY.md`.

## 9-10) API Reference Site + Hosted Quickstart
- Reference page: `docs/reference/index.html`.
- Hosted quickstart: `docs/HOSTED_QUICKSTART.md`.
- Postman collection: `docs/reference/postman_collection.json`.

## 11-12) Tenant Quotas + Admin Controls
- Quota enforcement added in usage flow via account plan fields.
- Admin endpoints: list/update account, adjust credits, key oversight.

## 13) Reconciliation Worker
- Existing runner: `scripts/run_reconciliation.py`.
- Production requirement: scheduled job (cron/Cloud Run job/K8s CronJob), retry and metrics.

## 14) Webhooks Reliability
- Current signature verification and idempotent application exists.
- Add DLQ + replay queue in infra (SQS/Rabbit + replay endpoint).

## 15-16) Observability + Alerts
- Add OTEL traces + centralized logs + metrics dashboards.
- Alert on Stripe failures, webhook signature failures, reconciliation errors, and 429 spikes.

## 17) Security Hardening
- Add managed secrets, strict CORS allow-list, tenant+key rate limits, audit events table.

## 18) CI/CD Gates
- Added baseline CI workflow in `.github/workflows/ci.yml`.
- Extend with lint + migration check + release workflow.
- Implemented:
  - compile/import gate (`python -m compileall ...`)
  - migration gate (`alembic upgrade head`)
  - automated SDK build checks (Python wheel/sdist + `twine check`)
  - tag-based SDK publish workflow (`.github/workflows/publish-sdks.yml`)

## 19) Contract/Integration Tests
- Existing integration-like API tests in `tests/test_api_flow.py`.
- Implemented deployed-environment smoke workflow:
  - `.github/workflows/deployed-contract-tests.yml`
  - `tests/test_deployed_contract.py`
  - Requires secrets: `DEPLOYED_BASE_URL`, optional `DEPLOYED_API_KEY`

## 20) Legal/Product Readiness
- Publish Terms, Pricing, SLA, and Support policy pages before GA.
