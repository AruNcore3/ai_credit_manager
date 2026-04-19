# AI Credit Billing API - Product Roadmap

## 1) Product Vision
Build a developer-facing billing API for AI SaaS products that enables:
- Mid-cycle credit top-ups
- Real-time usage deduction
- Preventing service block when monthly plan limits are hit

This product should feel like Stripe/OpenAI APIs:
- API-key based
- Versioned endpoints
- Clear docs + predictable responses
- Strong idempotency and webhook reliability

## 2) Core Value Proposition
For AI SaaS teams:
- Do not build billing/metering from scratch
- Plug into one API for top-up, ledger, balance, and usage charging
- Recover revenue from over-usage instead of hard-blocking users

## 3) Target Users
- AI chatbot SaaS founders
- Internal AI platform teams
- Multi-tenant AI tools (agents, image generation, copilots)

## 4) MVP Scope (Must-Have)
### A. Wallet + Top-up
- `POST /v1/topups/intents`
- `POST /v1/webhooks/stripe`
- `GET /v1/wallets/{account_id}`
- `GET /v1/ledger`

### B. Usage Metering
- `POST /v1/usage/record`
- Atomic credit deduction
- Insufficient credit response (`topup_required=true`)
- Idempotent usage events (`event_id`)

### C. Security + Tenant Model
- API key auth
- Account/workspace isolation
- Request-level rate limiting

## 5) Current Status (Based on Existing Project)
Done:
- Top-up intent flow works
- Stripe webhook endpoint exists
- Balance and ledger endpoints exist
- Wallet and ledger models are implemented

Not done / partial:
- API-key auth + tenant isolation
- Usage metering endpoint (`/usage/record`)
- Reconciliation worker for missed webhook events
- Migration workflow (Alembic)
- Production-grade docs/SDKs

## 6) Milestone Plan
### Milestone 1 - Stable Private Beta API
- Add auth (API keys)
- Add usage record + idempotent debit
- Add migrations
- Add integration tests and CI

### Milestone 2 - Developer Productization
- API versioning (`/v1`)
- Public API docs + quickstart
- Webhook retry visibility
- Better error schema + request IDs

### Milestone 3 - Commercial Readiness
- Plans/quotas
- Dashboard for balances and events
- Invoice/export support
- Monitoring/alerts and SLOs

## 7) Non-Functional Requirements
- Idempotency on all write endpoints
- 99.9% API uptime target
- Auditable ledger invariants
- Secure secret handling and no credential leakage in logs

## 8) Definition of MVP Done
MVP is done only when:
1. Any client SaaS can add credits via API and Stripe webhook safely.
2. Usage events can deduct credits in real time, exactly once.
3. API keys can isolate accounts securely.
4. Tests cover payment, webhook, and usage idempotency.
5. Integration guide lets a new developer go live in under 1 hour.

## 9) Immediate Next Direction
Build `POST /v1/usage/record` next.  
This is the missing core capability that converts your project from "wallet top-up system" to "full AI billing API platform."

