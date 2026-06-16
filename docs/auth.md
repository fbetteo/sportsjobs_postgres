# Auth

## Current Model
- Most write and data endpoints use Bearer token authentication via `Authorization` header.
- Main token: `HEADER_AUTHORIZATION` environment variable.
- Blog webhook token: `OUTRANK_HEADER_AUTHORIZATION` environment variable.
- Stripe webhook signature secret: `STRIPE_WEBHOOK_SECRET` environment variable.

## Current Behavior
- If header is missing or invalid, endpoints usually return `403 Unauthorized`.
- Webhook endpoint returns `401 Invalid access token` for token failures.
- Health endpoints are public (`/health`, `/db-health`).
- Testimonials submit/read endpoints are public (`POST /testimonials`, `GET /testimonials`), while moderation endpoints are protected (`/admin/testimonials*`).
- Pending job draft creation and publishing endpoints are protected with the main token.
- Auth0 user/profile endpoints are protected with the main token; this backend trusts the frontend-provided `auth0Sub` only behind that shared bearer auth.
- Stripe entitlement webhook uses Stripe signature verification and does not use the main bearer token.

## Protected Endpoint Pattern
- Read `Authorization` header from request.
- Validate against expected `Bearer <token>` value.
- Fail early before database operations.

## Change Guidance
- Keep auth checks explicit at endpoint level unless a deliberate refactor is requested.
- If status codes are standardized, update all endpoints consistently.
- Document any new token variable here.
