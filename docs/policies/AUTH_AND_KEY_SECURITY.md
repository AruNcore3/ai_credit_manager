# Auth and API Key Security

## Header
- Send API key in `X-API-Key`.

## Environment Variables
- Server-side apps should load keys from env vars:
  - `AI_CREDIT_API_KEY`
  - `AI_CREDIT_BASE_URL` (default `https://api.yourdomain.com/v1`)

## Storage
- Never hardcode keys in source control.
- Use secret managers for production (AWS Secrets Manager, GCP Secret Manager, Vault).
- Restrict key visibility to runtime only.

## Rotation
- Rotate every 90 days or immediately on suspected leak.
- Recommended sequence:
  1. Create new key.
  2. Deploy new key.
  3. Verify traffic on new key.
  4. Revoke old key.

## Incident Handling
- If exposed, revoke key immediately and issue replacement.
- Audit access logs for abnormal usage windows.
