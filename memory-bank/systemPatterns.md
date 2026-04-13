# System Patterns — Architecture Decisions

## Layered Architecture
```
*_models.py     → SQLModel ORM (table=True)
repository.py   → Pure data access (Session in, ORM out)
service.py      → Business logic (get_session(), validation, orchestration)
```

## Detailed Architecture Design

### N-Tier Architecture Stack
```
┌─────────────────────────────────────────────────────────┐
│  API Layer (FastAPI Routers)                            │
│  - Input validation (Pydantic DTOs)                     │
│  - Authentication/Authorization (JWT, role guards)    │
│  - Response envelope standardization                  │
├─────────────────────────────────────────────────────────┤
│  Service Layer (Business Logic)                         │
│  - Domain operations & orchestration                    │
│  - Validation rules                                     │
│  - Transaction coordination                             │
├─────────────────────────────────────────────────────────┤
│  Repository Layer (Data Access)                         │
│  - SQLModel ORM operations                              │
│  - Query optimization                                   │
│  - Pure functions (Session in, ORM out)               │
├─────────────────────────────────────────────────────────┤
│  Database Layer (PostgreSQL)                            │
│  - Tables, views, indexes                               │
│  - Triggers (balance calculation)                       │
│  - Check constraints                                    │
└─────────────────────────────────────────────────────────┘
```

### Design Patterns Implemented

#### 1. Repository Pattern
Pure data access functions with no business logic. Session parameter injected from service layer.
- **Examples:** `finance_repository.py`, `academics/repositories/group_repository.py`
- **Pattern:** `def get_by_id(session: Session, id: int) -> Model`

#### 2. Service Layer Pattern
Business logic encapsulation with state management per request.
- **Examples:** `finance_service.py`, `academics/services/group_service.py`
- **Pattern:** Service factories like `get_balance_service()` return fresh instances

#### 3. Dependency Injection (DI)
FastAPI `Depends()` for all external dependencies.
- **Role Guards:** `require_admin`, `require_any`, `require_instructor`
- **Database:** `get_db()` generator yields sessions
- **Services:** Factory functions injected per request

#### 4. DTO (Data Transfer Object) Pattern
Pydantic models for all API I/O. No raw dictionaries in API layer.
- **Request DTOs:** `BalanceAdjustmentRequest`, `CreateStudentRequest`
- **Response DTOs:** `StudentBalanceDTO`, `ApiResponse[T]`

#### 5. Factory Pattern
Service instantiation via factory functions for per-request state injection.
```python
def get_balance_service():
    return BalanceService()
# Used as: svc = Depends(get_balance_service)
```

#### 6. Strategy Pattern
Balance calculation strategies (materialized vs real-time), payment allocation algorithms.

### Modular Router Organization (15 Routers, 10 Domains)
```
app/api/routers/
├── academics/              # 6 router modules
│   ├── courses_router.py
│   ├── groups_router.py
│   ├── sessions_router.py
│   ├── group_lifecycle_router.py
│   ├── group_competitions_router.py
│   └── __init__.py
├── analytics/              # 4 router modules
│   ├── academic.py
│   ├── financial.py
│   ├── competition.py
│   └── bi.py
├── crm/                    # 4 router modules
│   ├── students_router.py
│   ├── parents_router.py
│   └── students_history_router.py
├── finance/                # 4 router modules
│   ├── balance_router.py
│   ├── receipt_router.py
│   └── finance_router.py
├── attendance_router.py    # standalone
├── auth_router.py          # standalone
├── competitions_router.py   # standalone
├── enrollments_router.py  # standalone
└── hr_router.py           # standalone
```

### Exception Hierarchy
```
AppError (base)
├── NotFoundError       → HTTP 404
├── ValidationError     → HTTP 422
├── BusinessRuleError   → HTTP 409
├── ConflictError       → HTTP 409
└── AuthError           → HTTP 401
```
Usage: Service layer raises → API layer catches → HTTP response

### Authentication & Authorization Pattern
- **JWT Verification:** Supabase tokens validated on every request via `HTTPBearer`
- **Local User Mapping:** Supabase UID → local User record (for role checking)
- **Role Guards:**
  - `require_any` - Any authenticated user
  - `require_admin` - Admin or system_admin role
  - `require_instructor` - Instructor, admin, or system_admin

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
