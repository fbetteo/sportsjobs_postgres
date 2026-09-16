# SportsJobs backend and database: guide for coding agents

This repository is the FastAPI and PostgreSQL backend for SportsJobs.online. Keep changes small, explicit, and compatible with the clients and job producers that use this API. Start from the current route and schema before introducing a new abstraction.

## Related repositories

The SportsJobs project also has two sibling repositories under `C:\Users\franb\projects\sportsjobs\`:

- Frontend: `C:\Users\franb\projects\sportsjobs\sportsjobs-frontend` (Next.js app). Read its `AGENTS.md` and the relevant `docs/` page before changing its API calls or UI.
- Scraper: `C:\Users\franb\projects\sportsjobs\sportsjobs` (job collection and enrichment). Read its `AGENTS.md` and `run_scripts.sh` before changing job ingestion or fields the scraper writes.

For a feature spanning repositories, identify each owner before editing: this repo owns API behavior, persistence, and database scripts; the frontend owns browser UI and interactions; the scraper owns collecting jobs. Coordinate request/response fields, authentication, and database fields across affected repos. A CV collection feature may involve frontend uploads and backend storage/access without needing any scraper change. Decide where CV files and metadata belong, who may access them, and the API contract before adding code; keep the implementation as simple as those requirements allow.

## Start here

- `main.py` creates the FastAPI app and includes routers from `endpoints/`. Register a new router there only when a new domain actually needs one.
- `endpoints/` contains API handlers by domain: `jobs.py`, `users.py`, `alerts.py`, `stripe.py`, `newsletter.py`, `blog.py`, `companies.py`, `testimonials.py`, and `health.py`. Begin with the closest existing endpoint. Most handlers execute SQL directly and return plain JSON-compatible dicts or lists.
- `models/schemas.py` contains Pydantic request/response models. Reuse its existing patterns and keep names and defaults compatible with current callers.
- `database/connection.py` provides `get_db_connection()` using `DB_NAME`, `DB_USER`, `DB_PASSWORD`, and `DB_HOST`. Table creation, migrations, and maintenance scripts live in `database/`; historical backups live in `database_backups/` and are not normal feature files.
- Topic guides are in `docs/`: `backend-api.md` for routes, `auth.md` for protected endpoints, `frontend.md` for client contracts, and `data-and-ops.md` for database scripts and deployment order. Use them as a map, verify behavior against current code, and update only the relevant pages when behavior changes.

## Adding a feature

1. Trace the existing frontend call or scraper write, the endpoint, the Pydantic model, and the table fields involved. Define the smallest request and response change that meets the feature need.
2. Add the handler to the closest router in `endpoints/` and the necessary model to `models/schemas.py`. Follow nearby authorization, validation, SQL, response, and error-handling patterns. Avoid a new service layer or generic framework for a single feature.
3. If persistence must change, add a focused script in `database/` that makes the schema change explicit. Check existing table/create/migrate scripts and the data already stored. Explain the deployment order when an API change depends on a schema change; do not run a migration against a live database as routine validation.
4. Keep SQL values parameterized with `%s` placeholders. For dynamic identifiers or ordering, use a fixed allowlist or safe SQL composition; placeholders do not protect SQL identifiers. Commit successful writes, roll back failed writes, and close connections.
5. Keep existing API shapes and authentication behavior stable where possible. If a contract changes, update the relevant backend docs and coordinate the frontend or scraper caller in the same feature work.

## Style, tests, and operational care

- Python `^3.12` and Poetry are declared in `pyproject.toml` and `poetry.lock`; keep Poetry as the environment and dependency manager. Prefer small functions, clear names, explicit data flow, and narrow exception handling.
- Protected routes commonly check `Authorization: Bearer <HEADER_AUTHORIZATION>` before database access; `endpoints/stripe.py` verifies Stripe webhook signatures. Read `docs/auth.md` and the nearby handler before changing authentication. User/profile identity also involves Auth0 subjects and Stripe IDs, so preserve established lookup and idempotency behavior.
- Do not put credentials, tokens, CV contents, or other personal data in code, tests, logs, or documentation. `.env`, Stripe, Airtable, object storage, and PostgreSQL may point to live services.
- Prefer focused tests with mocked connections or local fixtures for validation, SQL decisions, and response contracts. Do not call real write endpoints, payment webhooks, email workflows, or database migration scripts merely to test a code change.
- Before finishing a feature, check the affected API/schema boundary and update the relevant `docs/*.md`. Keep the documentation short; report any required migration or deployment ordering clearly.
