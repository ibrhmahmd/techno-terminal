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
| Apply migrations | `psql -U postgres -d techno_kids -f db/migrations/*.sql` |

## Environment Setup

```env
# Required
DATABASE_URL=postgresql://user:pass@localhost:5432/techno_kids
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# Optional
PDF_LOGO_PATH=/path/to/logo.png
```

## Architecture

### Layer Pattern: Router → Service → Repository

```
┌─────────────────────────────────────────────────────────────┐
│ Routers (app/api/routers/)                                 │
│   - 21 router files, 209 endpoints                         │
│   - FastAPI Depends() injection                            │
│   - Request validation via Pydantic schemas                │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ Services (app/modules/*/services/)                          │
│   - Business logic encapsulation                           │
│   - Transaction boundaries (UnitOfWork)                    │
│   - Activity logging integration                           │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ Repositories (app/modules/*/repositories/)                  │
│   - Pure SQL queries via SQLModel/select()                  │
│   - No business logic                                      │
└─────────────────────────────────────────────────────────────┘
```

### Key Directories

| Directory | Purpose |
|-----------|---------|
| `app/api/main.py` | FastAPI app factory, router registration, lifespan |
| `app/api/dependencies.py` | DI factories for services, auth guards |
| `app/api/routers/` | 21 router files organized by domain |
| `app/api/schemas/` | Pydantic DTOs for request/response |
| `app/api/exceptions.py` | Domain exception → HTTP status mapping |
| `app/modules/` | 11 business modules (auth, crm, academics, finance, etc.) |
| `app/db/connection.py` | SQLModel engine + session factory |
| `app/core/supabase_clients.py` | Supabase client instances |
| `db/schema.sql` | Modular schema orchestrator (33 tables) |
| `db/migrations/` | Incremental schema changes |

### Entry Points

- **API App**: `app.api.main:app` (via `create_app()`)
- **Dev Server**: `run_api.py` adds project root to PYTHONPATH
- **Production**: Gunicorn on port 8000 (hardcoded in Dockerfile)

## Database Schema

### Core Tables (33 total)

| Domain | Tables |
|--------|--------|
| **Core** | `employees`, `users`, `parents` |
| **CRM** | `students`, `student_parents`, `student_activity_log` |
| **Academics** | `courses`, `groups`, `sessions`, `group_levels` |
| **Enrollments** | `enrollments`, `attendance`, `enrollment_level_history` |
| **Finance** | `receipts`, `payments`, `payment_allocations`, `receipt_templates` |
| **Competitions** | `competitions`, `competition_categories`, `teams`, `team_members` |
| **Notifications** | `notification_logs`, `notification_templates`, `admin_notification_settings` |

### Key Views

| View | Purpose |
|------|---------|
| `v_students` | Student + primary parent info |
| `v_enrollment_balance` | Real-time balance per enrollment |
| `v_unpaid_enrollments` | Outstanding debt tracking |
| `v_daily_collections` | Daily revenue aggregation |
| `v_student_payment_history` | Complete payment timeline |
| `v_student_activity_timeline` | Chronological student activity |

### Schema Files Order

Apply in this order: `00_extensions` → `01_enums` → `02_core` → `03_crm` → `04_academics` → `05_enrollments` → `06_finance` → `07_competitions` → `08_notifications` → `09_history` → `10_supabase` → indexes → views → functions → triggers → constraints → seed_data

## Authentication & Authorization

### JWT Auth Flow

1. Client sends `Authorization: Bearer <jwt>` header
2. `get_current_user()` in `dependencies.py` validates via Supabase
3. `get_user_by_supabase_uid()` maps to local `User` model
4. Role guards (`require_admin`, `require_any`) check permissions

### Roles (from `app/modules/auth/constants.py`)

- `admin` / `system_admin` - Full access
- `manager` - Management operations
- `instructor` - Teaching operations
- `accountant` - Finance operations

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

| Fixture | Purpose |
|---------|---------|
| `client` | FastAPI TestClient (function-scoped) |
| `app` | FastAPI application instance |
| `admin_token` | Real Supabase JWT (expires ~1 hour) |
| `admin_headers` | `{"Authorization": "Bearer <token>"}` |
| `db_session` | DB session with transaction rollback |

### Test Isolation

- Tests use `db_session` fixture which auto-rollbacks
- Each test runs in its own transaction
- Real Supabase JWT in `admin_token` expires ~1 hour

### Regenerate Expired Token

```bash
python scripts/get_test_jwt.py
```

Then update the `admin_token` fixture in `tests/conftest.py`.

### Running Tests

```bash
# All tests with verbose output
pytest tests/ -v

# Single test file
pytest tests/test_crm.py -v

# Single test
pytest tests/test_crm.py::test_student_list -v

# With coverage
pytest tests/ --cov=app --cov-report=term-missing
```

## Common Patterns & Gotchas

### Router Registration Order

```python
# Group directory router MUST come before groups_router
# to prevent /{group_id} shadowing /enriched
app.include_router(group_directory_router, prefix="/api/v1")
app.include_router(groups_router, prefix="/api/v1")
```

### Response Envelope

All responses follow standard format:
```python
{"success": true, "data": ..., "message": ...}
{"success": false, "error": "NotFoundError", "message": "..."}
```

### Domain Exceptions

Defined in `app/shared/exceptions.py`:
- `NotFoundError` → 404
- `ValidationError` → 422
- `BusinessRuleError` → 409
- `ConflictError` → 409
- `AuthError` → 401

### Activity Logging

Services integrate with `StudentActivityService` for audit trails:
- Payment events
- Registration events
- Status changes

### Middleware Order (app/api/main.py)

1. Logging middleware (outermost)
2. CORS middleware
3. Exception handlers
4. Routers

## Module Breakdown

| Module | Purpose | Key Services |
|--------|---------|--------------|
| `auth` | JWT validation, user lookup | `AuthService` |
| `crm` | Students, Parents, Activity | `StudentCrudService`, `ParentCrudService`, `SearchService` |
| `academics` | Courses, Groups, Sessions | `CourseService`, `GroupCoreService`, `SessionService` |
| `enrollments` | Student enrollments | `EnrollmentService`, `EnrollmentMigrationService` |
| `attendance` | Session attendance | `AttendanceService` |
| `finance` | Receipts, Payments, Balance | `ReceiptService`, `RefundService`, `BalanceService` |
| `competitions` | Competition/Team management | `CompetitionService`, `TeamService` |
| `hr` | Employees, Staff accounts | `EmployeeCrudService`, `StaffAccountService` |
| `analytics` | Reporting, BI, Dashboard | `AcademicAnalyticsService`, `FinancialAnalyticsService`, `DashboardService` |
| `notifications` | WhatsApp, SMS, Email | `NotificationService` |

## API Documentation

- **Swagger UI**: `http://localhost:8000/api/v1/docs`
- **ReDoc**: `http://localhost:8000/api/v1/redoc`
- **OpenAPI JSON**: `http://localhost:8000/api/v1/openapi.json`

## Deployment

- **Platform**: Leapcell (configured via `railpack.json`)
- **Docker**: `Dockerfile` uses Python 3.11-slim, installs deps via `pip install -e .`
- **Health checks**: `/health` and `/kaithhealthcheck` endpoints

## Important Files

| File | Purpose |
|------|---------|
| `app/api/main.py` | App factory, router registration, lifespan |
| `app/api/dependencies.py` | DI, auth, service factories |
| `app/db/connection.py` | Engine & session management |
| `app/core/supabase_clients.py` | Supabase client config |
| `app/shared/exceptions.py` | Domain exceptions |
| `db/schema.sql` | Schema orchestrator |
| `tests/conftest.py` | Test fixtures |
| `pyproject.toml` | Dependencies |
| `Dockerfile` | Production build |
| `railpack.json` | Leapcell deployment config |