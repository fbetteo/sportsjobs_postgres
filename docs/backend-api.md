# Backend API

## What This Service Is
- FastAPI application mounted in `main.py`.
- Routers are split by domain in `endpoints/`.
- Data is read/written directly in endpoint handlers through PostgreSQL.

## Current Route Groups
- Health checks: `endpoints/health.py`
- Users: `endpoints/users.py`
- Stripe entitlement webhooks: `endpoints/stripe.py`
- Alerts: `endpoints/alerts.py`
- Jobs: `endpoints/jobs.py`
- Blog and webhook: `endpoints/blog.py`
- Companies aggregate: `endpoints/companies.py`
- Newsletter signups: `endpoints/newsletter.py`
- Testimonials collection and moderation: `endpoints/testimonials.py`
- Pending job draft creation and publishing: `endpoints/jobs.py`

## API Conventions Used Here
- Many read operations are `POST` endpoints with a request body for filters/sort/limit.
- Pydantic schemas live in `models/schemas.py`.
- Most endpoints return plain dict/list structures from SQL row mapping.
- Route handlers own query construction and execution.
- `POST /pending_job_postings` stores a job draft and returns its `pending_job_id`.
- `POST /pending_job_postings/{pending_job_id}/publish` publishes a draft once and returns its `job_id`.
- `POST /users/signup_funnel` creates/updates a pre-auth user row by normalized email and stores signup funnel answers on both `users` and `user_profiles`.
- `PATCH /users/signup_funnel/paid-product-acknowledgement` stores the paid-product acknowledgement timestamp by normalized email.
- `POST /users/signup_funnel/claim` links the paid pre-auth row to the Auth0 user by checkout session, signup funnel ID, or Stripe IDs and returns the full profile shape.
- `GET /users/me?auth0_sub=...` returns the Auth0-linked user profile or `404`.
- `GET /users/billing?auth0_sub=...` returns billing identifiers for authenticated server-side subscription operations. It matches only by `auth0_sub`, includes email as a legacy Stripe fallback field, and returns `404` when the user does not exist.
- `POST /users/ensure` idempotently creates/updates an Auth0-linked free user and returns the profile shape. It may also attach pre-auth fields: `signupFunnelAnswers`, `signupFunnelCompletedAt`, and `paidProductAcknowledgedAt`.
- `PATCH /users/me/onboarding` stores onboarding answers and returns the profile shape. Required onboarding keys are `sportsInterests`, `jobSearchDuration`, `hardestPart`, `roleInterests`, and `roleUnsure`; `country` is optional.
- `POST /stripe/webhook` syncs Stripe checkout/subscription events to user entitlement state.

## Change Guidance
- Reuse existing schema patterns before adding new schema files.
- Keep SQL parameterized (`%s` placeholders with value tuples).
- For new endpoints, follow current structure: auth check, query execution, commit/rollback, close connection.
