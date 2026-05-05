# API Versioning and Deprecation Policy

- Current major version: `v1`
- Base URL: `https://api.yourdomain.com/v1`

## Rules
- Breaking changes only ship in a new major version (`/v2`, `/v3`, ...).
- Non-breaking additions (new optional fields/endpoints) may ship in-place in `v1`.
- Every breaking change requires a minimum 90-day overlap window.
- Deprecated endpoints include `Deprecation: true` and `Sunset` headers.

## Timeline Contract
- Day 0: Deprecation notice published in changelog and status page.
- Day 0-90: Both old and new routes available.
- Day 90+: Old route may return `410 Gone`.

## SDK Policy
- SDK major version maps to API major version.
- SDK minor/patch versions are backward-compatible with current API major.
