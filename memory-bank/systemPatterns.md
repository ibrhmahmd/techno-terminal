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

## Deployment Patterns

### Health Check Endpoint
```python
@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok", "service": "Techno Terminal API", "version": "1.0.0"}
```
- Simple, lightweight response
- No database queries (fast response)
- Used by Leapcell for container health monitoring

### Production Server Configuration
- **Platform:** Leapcell with `railpack.json`
- **Server:** Gunicorn with Uvicorn workers
- **Timeout:** 300s (slow startup for DB connections)
- **Workers:** 2 (memory-efficient for 4GB limit)
- **Temp Dir:** `/tmp` (avoids read-only filesystem)

### Environment Handling
- Database URL from env var (Supabase PostgreSQL)
- Supabase credentials for auth
- Graceful degradation if optional vars missing

## Key Naming Conventions
- `level_number` (not `current_level`) — Group's active level
- `employee_metadata`, `profile_metadata` — JSONB columns (avoid SQLAlchemy `metadata` reserved word)
- `enrollment.level_number` — Snapshot at enrollment time
- `require_any` — Any authenticated user
- `require_admin` — Admin or system_admin role
