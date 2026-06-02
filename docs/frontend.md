# Frontend

## Context For This Repo
- This repository does not contain frontend implementation code.
- It is a backend API consumed by external clients/frontends.

## Practical Frontend Contract
- API responses are plain JSON objects/lists mapped from SQL rows.
- Query-style reads often use POST bodies (`filters`, `sort_by`, `sort_direction`, `limit`).
- Authentication for protected routes uses `Authorization: Bearer <token>`.
- Create paid-posting drafts with `POST /pending_job_postings`; the response is `{ "pending_job_id": "<uuid>" }`.
- After checkout confirmation, publish with `POST /pending_job_postings/{pending_job_id}/publish` and `{ "stripe_session_id": "cs_..." }`; retries return the same `{ "job_id": 123 }`.

## If You Are Changing APIs
- Minimize response shape changes unless requested.
- Keep field names stable where possible.
- When breaking response contracts, call out impact in PR/task notes.

## About Next.js / Frontend Rules
- If a dedicated frontend repository has stricter rules (for example Next.js conventions), treat those as frontend-source-of-truth.
- In this backend repo, prioritize API stability, clear schema contracts, and predictable auth behavior.
