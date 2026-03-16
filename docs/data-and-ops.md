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

## Operational Conventions
- Open DB connection per request/script operation and close in `finally`.
- Use `conn.commit()` on success and `conn.rollback()` on exceptions.
- Avoid interpolating user input directly into SQL identifiers or clauses.

## Change Guidance
- Keep migration scripts explicit and reversible where practical.
- Do not modify backup files in `database_backups/` as part of normal feature work.
- If schema changes affect API responses, update both `docs/backend-api.md` and `docs/auth.md` as needed.
