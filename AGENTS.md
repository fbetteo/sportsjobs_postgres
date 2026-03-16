# AGENTS

Purpose: fast map for agents working in this repository.

## Scope
- This repository is a FastAPI + PostgreSQL backend.
- There is no frontend app in this codebase.
- Prefer minimal, targeted changes.

## Where To Look
- API routes and request flow: `docs/backend-api.md`
- Authentication and protected endpoints: `docs/auth.md`
- Frontend integration expectations: `docs/frontend.md`
- Database shape, migrations, and scripts: `docs/data-and-ops.md`

## Working Rules
- Start from existing endpoint patterns in `endpoints/` before introducing new abstractions.
- Keep SQL explicit and parameterized.
- Do not change authentication behavior without updating `docs/auth.md`.
- Keep docs short; update only the section affected by your change.

## Source Priority
When guidance conflicts, apply this order:
1. Direct user request in current task.
2. This file (`AGENTS.md`).
3. Topic docs in `docs/`.
4. Existing code behavior.
