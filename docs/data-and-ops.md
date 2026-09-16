# Data And Ops

## Database Access
- Connection helper: `database/connection.py` (`get_db_connection`).
- Driver: `psycopg2`.
- Environment variables: `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`.

## Data Model And Scripts
- Table creation/migration scripts are in `database/`.
- Historical SQL dumps are in `database_backups/`.
- Several scripts handle initial import/migration from Airtable and maintenance tasks.
- Testimonials table bootstrap script: `database/testimonials_create_table.py`.
- Pending job postings bootstrap script: `database/pending_job_postings_create_table.py`.
- Auth0 user refactor and future user-feature tables script: `database/users_refactor_2026.py`.
- Testimonial request tracking migration: `database/testimonial_request_tracking.py`. Run it before enabling the scraper repo's daily `testimonial_request_sequence.py`. It adds `users.testimonial_request_sent_at` and does not send email.

## Operational Conventions
- Open DB connection per request/script operation and close in `finally`.
- Use `conn.commit()` on success and `conn.rollback()` on exceptions.
- Avoid interpolating user input directly into SQL identifiers or clauses.
- Run `python database/pending_job_postings_create_table.py` before deploying the pending job publishing endpoints.
- Run `python database/users_refactor_2026.py` before deploying Auth0 profile/onboarding or Stripe entitlement endpoints.
- Configure `STRIPE_MONTHLY_PRICE_ID`, `STRIPE_YEARLY_PRICE_ID`, `STRIPE_LIFETIME_PRICE_ID`, and `STRIPE_WEBHOOK_SECRET` for Stripe entitlement sync.

## Change Guidance
- Keep migration scripts explicit and reversible where practical.
- Do not modify backup files in `database_backups/` as part of normal feature work.
- If schema changes affect API responses, update both `docs/backend-api.md` and `docs/auth.md` as needed.
