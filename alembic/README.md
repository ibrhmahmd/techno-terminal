# Alembic

- **Config:** [../alembic.ini](../alembic.ini)
- **Env:** loads `DATABASE_URL` from [app/core/config.py](../app/core/config.py) (`.env`).

## Baseline

Revision `001_baseline_v33` is intentionally empty: full DDL lives in [db/schema.sql](../db/schema.sql). After applying that file to an empty database:

```bash
alembic stamp 001_baseline_v33
```

## New changes

Prefer `alembic revision -m "description"` and edit the generated file, or use autogenerate against a dev database that matches head.

See [db/README.md](../db/README.md) for when to use hand-written SQL under `db/migrations/` instead.
