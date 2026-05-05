# Hosted Quickstart

Base URL: `https://api.yourdomain.com/v1`

## 1) Signup
```bash
curl -X POST https://api.yourdomain.com/v1/onboarding/signup \
  -H "Content-Type: application/json" \
  -d '{"account_name":"acme","username":"owner","email":"owner@acme.com","password":"replace-me-123"}'
```

## 2) Check balance
```bash
curl https://api.yourdomain.com/v1/credits/balance \
  -H "X-API-Key: $AI_CREDIT_API_KEY"
```

## 3) Record usage
```bash
curl -X POST https://api.yourdomain.com/v1/usage/record \
  -H "X-API-Key: $AI_CREDIT_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"event_id":"evt_001","model":"gpt-4.1","input_token":1200,"output_token":600}'
```

## Postman
Import `docs/reference/postman_collection.json`.
