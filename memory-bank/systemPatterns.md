# System Patterns — Architecture Decisions

## Layered Architecture
```
*_models.py     → SQLModel ORM (table=True)
repository.py   → Pure data access (Session in, ORM out)
service.py      → Business logic (get_session(), validation, orchestration)
```

## API Patterns
- **Router Organization:** Split by domain (`analytics/`, `academics/`, `crm/`)
- **DTOs:** Pydantic models for all request/response (no raw dicts)
- **Dependency Injection:** `Depends()` factories in `dependencies.py`
- **Error Handling:** Standardized envelope `{success, error, message}`
- **Auth:** Supabase JWT with `require_admin` / `require_any` guards

## Database Patterns
- **Connection:** `get_session()` context manager
  - Auto-commit on success
  - Auto-rollback on exception
  - `expire_on_commit=False`
- **Schema:** Hybrid workflow
  - `db/schema.sql` — greenfield canonical DDL
  - `db/migrations/*.sql` — operational upgrades
  - Alembic for revision tracking only

## Testing Patterns
- **Fixtures:** `client`, `admin_headers`, `db_session` in `conftest.py`
- **Isolation:** Transaction rollback per test
- **JWT:** Real Supabase token (regenerate hourly)
- **Structure:** Class-based by endpoint category

## Key Naming Conventions
- `level_number` (not `current_level`) — Group's active level
- `employee_metadata`, `profile_metadata` — JSONB columns (avoid SQLAlchemy `metadata` reserved word)
- `enrollment.level_number` — Snapshot at enrollment time
- `require_any` — Any authenticated user
- `require_admin` — Admin or system_admin role
