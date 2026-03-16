# Auth

## Current Model
- Most write and data endpoints use Bearer token authentication via `Authorization` header.
- Main token: `HEADER_AUTHORIZATION` environment variable.
- Blog webhook token: `OUTRANK_HEADER_AUTHORIZATION` environment variable.

## Current Behavior
- If header is missing or invalid, endpoints usually return `403 Unauthorized`.
- Webhook endpoint returns `401 Invalid access token` for token failures.
- Health endpoints are public (`/health`, `/db-health`).

## Protected Endpoint Pattern
- Read `Authorization` header from request.
- Validate against expected `Bearer <token>` value.
- Fail early before database operations.

## Change Guidance
- Keep auth checks explicit at endpoint level unless a deliberate refactor is requested.
- If status codes are standardized, update all endpoints consistently.
- Document any new token variable here.
