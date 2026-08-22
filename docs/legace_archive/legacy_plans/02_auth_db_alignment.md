# Plan: Auth finalization, schema alignment, and `db/` organization (completed)

## Objectives

1. **Roles:** Canonical values `admin`, `instructor`, `system_admin` with a single Python source of truth and a documented path to add roles later (Python + DB CHECK + migration).
2. **Auth module:** Stable service API for lookups, `last_login`, staff linking, Supabase password reset; safe public JSON for `/me` (no `supabase_uid` exposure).
3. **Schema:** `db/schema.sql` aligned with SQLModel models (notably `users` + JSONB `metadata` columns on several tables).
4. **DB layout (hybrid):** Hand-written SQL under `db/migrations/` for ops-style upgrades; **Alembic** at repo root for revision history; `db/README.md` explains bootstrap vs stamp.

## Task order (executed)

| # | Focus | Key deliverables |
|---|--------|------------------|
| 1 | HR import fix | `Employee` imported from `hr_models` in `hr_repository.py` |
| 2 | Role contract | `app/modules/auth/role_types.py` (`UserRole`, `is_valid_role`) + validation on `UserBase` |
| 3 | Supabase clients | `app/core/supabase_clients.py` — lazy anon/admin factories |
| 4 | Schema + models | `db/schema.sql` v3.3 `users`; ORM JSONB fields mapped (e.g. `profile_metadata` → column `metadata`) |
| 5 | SQL migrations | `db/migrations/002_users_supabase_roles_v33.sql`, `db/migrations/README.md` |
| 6 | Alembic | `alembic.ini`, `alembic/env.py`, `alembic/versions/001_baseline_schema_v33.py` (empty upgrade; baseline = SQL file) |
| 7 | Auth service | `get_users_for_employee`, `force_reset_password`, `link_employee_to_new_user`; repo `get_users_by_employee_id` |
| 8 | FastAPI | `HTTPBearer`, `UserPublic` on `GET /api/v1/auth/me`, 403 inactive user, logging on auth failures |
| 9 | Login | `update_last_login` after successful Streamlit login |
| 10 | Schemas cleanup | `auth_schemas.py` reduced to placeholder DTOs (e.g. `PasswordResetBody`) |
| 11 | Employee UI | `employee_form` / `directory` / `detail` wired to `hr_service` + `auth_service` functions; roles from `UserRole` |

## Shared constants

- `MIN_PASSWORD_LENGTH` in `app/shared/constants.py` (used by HR + auth flows).

## References

- [db/README.md](../../db/README.md) — bootstrap paths, env vars, when to use SQL vs Alembic.
- [alembic/README.md](../../alembic/README.md) — stamp baseline after `psql -f db/schema.sql`.
- [MEMORY_BANK.md](../MEMORY_BANK.md) — operational summary for agents.
