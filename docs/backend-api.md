# Backend API

## What This Service Is
- FastAPI application mounted in `main.py`.
- Routers are split by domain in `endpoints/`.
- Data is read/written directly in endpoint handlers through PostgreSQL.

## Current Route Groups
- Health checks: `endpoints/health.py`
- Users: `endpoints/users.py`
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

## Change Guidance
- Reuse existing schema patterns before adding new schema files.
- Keep SQL parameterized (`%s` placeholders with value tuples).
- For new endpoints, follow current structure: auth check, query execution, commit/rollback, close connection.
