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

## Migrating local PostgreSQL → Supabase (one schema file + all data)

### Single file for schema (DDL)

Use **[schema.sql](schema.sql)** as the **only** file needed to recreate tables, indexes, views, triggers, and functions in a **new** empty database. It is kept in sync with numbered migrations under `migrations/`; you do **not** need to run those files on a greenfield Supabase DB if `schema.sql` is current.

### Before you start

1. Install **PostgreSQL client tools** on your machine (`psql`, `pg_dump`, `pg_restore`). On Windows, use the [PostgreSQL EDB installer](https://www.postgresql.org/download/windows/) or `choco install postgresql`.
2. In Supabase: **Project Settings → Database** — copy the **URI** (use **Session pooler** if your network needs IPv4; use **Direct** for `pg_restore` if the pooler rejects it). Append `?sslmode=require` if not present.
3. **Auth vs `public.users`:** This app maps **Supabase Auth** (`auth.users`) to **`public.users`** via **`users.supabase_uid`**. Rows you copy into `public.users` must use UUIDs that **exist in Supabase Auth** for those people to log in. After moving data, either create Auth users first, then load `public.users` with matching `supabase_uid`, or load data and then create/link accounts and **update** `public.users.supabase_uid`.

### Path A — Recommended: schema first, then data only

**1. Create the empty schema on Supabase**

```bash
psql "postgresql://postgres.[PROJECT_REF]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres?sslmode=require" -f db/schema.sql
```

(Use your real URI; port **5432** with the **direct** host `db.[PROJECT_REF].supabase.co` is fine if you prefer.)

**2. Export only the data from your local database**

```bash
set PGPASSWORD=your_local_password
pg_dump "postgresql://USER@localhost:5432/LOCAL_DBNAME" --data-only --format=custom --no-owner --no-acl -f techno_data.dump
```

**3. Import the data into Supabase**

```bash
set PGPASSWORD=your_supabase_password
pg_restore -d "postgresql://postgres.[PROJECT_REF]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres?sslmode=require" --data-only --no-owner --no-acl --single-transaction techno_data.dump
```

If the pooler rejects `pg_restore`, switch the target URI to the **direct** connection (port **5432**).

**4. Fix sequences if needed**

```sql
SELECT setval(pg_get_serial_sequence('guardians', 'id'), (SELECT MAX(id) FROM guardians));
-- repeat for other tables as needed
```

**5. Point the app at Supabase**

Set **`DATABASE_URL`** in `.env` to the connection string the app should use (often the **pooler** for many concurrent connections).

### Path B — One-shot full dump (empty target `public` only)

If the Supabase database has **no** conflicting objects in `public`:

```bash
pg_dump "postgresql://USER@localhost:5432/LOCAL_DB" --format=custom --no-owner --no-acl -f full.dump
pg_restore -d "postgresql://...@...supabase...?sslmode=require" --no-owner --no-acl full.dump
```

Avoid this if Supabase already has `schema.sql` applied — use Path A instead.

### What not to migrate

- Do **not** manually replace Supabase’s **`auth`** schema; manage login users via Supabase Auth + **`public.users`**.
- Do **not** run `db/migrations/supabase_auth_patch.sql` on a DB that already matches **`db/schema.sql`** v3.3 (legacy upgrades only).

## Adding a new `users.role`

1. Add the value to `app/modules/auth/role_types.py` (`UserRole` + `ALL_ROLE_VALUES`).
2. Update `CHECK (role IN (...))` in `db/schema.sql` and add a new numbered file under `db/migrations/`.
3. Add an Alembic revision if you use Alembic to alter constraints in deployed environments.
