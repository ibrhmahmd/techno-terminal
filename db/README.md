# Database layout (hybrid: SQL + Alembic)

## Contents

- **[schema.sql](schema.sql)** — Full PostgreSQL DDL (v3.3+). Source of truth for **table shapes** when creating a new environment with `psql`.
- **[migrations/](migrations/)** — Hand-written SQL for upgrading **existing** databases (CHECK changes, auth columns, DBA-reviewed scripts).
- **Alembic** (repo root: `alembic.ini`, `alembic/`) — Revision history for evolving the schema from Python; use when the team prefers autogenerate/migrate workflows.

## Environment variables

- `DATABASE_URL` — PostgreSQL connection string.
- `SUPABASE_URL`, `SUPABASE_ANON_KEY` — app + API JWT validation.
- `SUPABASE_SERVICE_ROLE_KEY` — staff provisioning, password reset, `app/db/seed.py` (optional for read-only dev).

## Bootstrap paths

### A. New database (SQL-first)

1. `psql "$DATABASE_URL" -f db/schema.sql`
2. Run the app once with `python run_ui.py` (or `python -m app.db.seed`) to map the admin user in Supabase to `users.supabase_uid`.
3. `alembic stamp head` so Alembic matches the baseline (no DDL run by Alembic if revisions are empty/pass-only).

### B. Existing database (upgrade)

1. Read [migrations/README.md](migrations/README.md) and apply required `.sql` files in order.
2. Backfill `users.supabase_uid` for every row before constraints enforce `NOT NULL`.
3. Stamp or upgrade Alembic per team convention (documented in `alembic/README.md` if present).

## Adding a new `users.role`

1. Add the value to `app/modules/auth/role_types.py` (`UserRole` + `ALL_ROLE_VALUES`).
2. Update `CHECK (role IN (...))` in `db/schema.sql` and add a new numbered file under `db/migrations/`.
3. Add an Alembic revision if you use Alembic to alter constraints in deployed environments.
