# AGENTS.md — Techno Terminal

## Quick Commands

| Task | Command |
|------|---------|
| Run API (dev) | `python run_api.py` |
| Run API (prod) | `gunicorn app.api.main:app -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000 --workers 2` |
| Run all tests | `pytest tests/ -v` |
| Run single test | `pytest tests/test_crm.py::test_student_list -v` |
| Run test with coverage | `pytest tests/ -v --cov=app --cov-report=term-missing` |
| Database init | `psql -U postgres -d techno_kids -f db/schema.sql` |

## Environment Setup

```env
# Required
DATABASE_URL=postgresql://user:pass@localhost:5432/techno_kids
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
```

## Architecture

### Layer Pattern: Router → Service → Repository

- **Routers** (`app/api/routers/`): FastAPI endpoints, Pydantic validation, Depends() injection
- **Services** (`app/modules/*/services/`): Business logic, transaction boundaries (UnitOfWork)
- **Repositories** (`app/modules/*/repositories/`): Pure SQL via SQLModel/select(), no business logic

### Entry Points

- **API App**: `app.api.main:app` (via `create_app()`)
- **Dev Server**: `run_api.py` adds project root to PYTHONPATH (required — imports depend on this)
- **Production**: Gunicorn on port 8000 (hardcoded in Dockerfile)

### Key Files

| File | Purpose |
|------|---------|
| `app/api/main.py` | App factory, router registration (order matters), lifespan |
| `app/api/dependencies.py` | DI factories, auth guards |
| `app/db/connection.py` | Engine + session factory (singleton engine, SSL required) |
| `app/core/supabase_clients.py` | Supabase client config |
| `app/shared/exceptions.py` | Domain exceptions → HTTP status mapping |
| `db/schema.sql` | Schema orchestrator (apply before migrations) |
| `db/migrations/*.sql` | Incremental schema changes (numbered, apply in order) |

### Schema Files Order

`00_extensions` → `01_enums` → `02_core` → `03_crm` → `04_academics` → `05_enrollments` → `06_finance` → `07_competitions` → `08_notifications` → `09_history` → `10_supabase` → indexes → views → functions → triggers → constraints → seed_data

## Authentication & Authorization

### JWT Auth Flow

1. Client sends `Authorization: Bearer <jwt>` header
2. `get_current_user()` in `dependencies.py` validates via Supabase
3. `get_user_by_supabase_uid()` maps to local `User` model
4. Role guards (`require_admin`, `require_any`) check permissions

### Roles

`admin` / `system_admin` - Full access

### Service Instantiation Pattern

```python
# Each request gets fresh service instance (stateless)
def get_student_crud_service() -> StudentCrudService:
    with StudentUnitOfWork() as uow:
        activity_svc = StudentActivityService(uow)
        return StudentCrudService(uow, activity_svc=activity_svc)
```

## Testing

### Fixtures (`tests/conftest.py`)

- `client` — FastAPI TestClient (function-scoped, fresh per test)
- `admin_token` — Real Supabase JWT (expires ~1 hour)
- `admin_headers` — `{"Authorization": "Bearer <token>"}`
- `db_session` — DB session (auto-rollback on exception)
- `system_admin_token` / `system_admin_headers` — Mock JWT via `tests/utils/jwt_mocks.py`

### Token Regeneration

Real JWT expires ~1 hour. Regenerate with:

```bash
python scripts/get_test_jwt.py
```

Then update `admin_token` in `tests/conftest.py`.

## Common Patterns & Gotchas

### Router Registration Order

`group_directory_router` **MUST** come before `groups_router` — otherwise `/{group_id}` shadows `/enriched`:

```python
app.include_router(group_directory_router, prefix="/api/v1")  # first
app.include_router(groups_router, prefix="/api/v1")           # second
```

### Response Envelope

All responses use standard format:

```json
{"success": true, "data": ..., "message": "..."}
{"success": false, "error": "NotFoundError", "message": "..."}
```

### Domain Exceptions → HTTP Status

`app/shared/exceptions.py`: `NotFoundError` → 404 | `ValidationError` → 422 | `BusinessRuleError` → 409 | `ConflictError` → 409 | `AuthError` → 401

### Middleware Order (app/api/main.py)

1. Logging middleware (outermost)
2. CORS middleware
3. Exception handlers
4. Routers

## API Documentation

- **Swagger UI**: `http://localhost:8000/api/v1/docs`
- **ReDoc**: `http://localhost:8000/api/v1/redoc`
- **OpenAPI JSON**: `http://localhost:8000/api/v1/openapi.json`

## Deployment

- **Platform**: Leapcell (configured via `railpack.json`)
- **Health checks**: `/health` and `/kaithhealthcheck` endpoints
