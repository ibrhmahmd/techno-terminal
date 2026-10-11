# Techno Terminal

> **Backend API for STEM Education Center Management**  
> FastAPI · SQLModel · PostgreSQL · Supabase Auth

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         API Layer (FastAPI)                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────┐  │
│  │     Routers     │  │     Schemas     │  │       Middleware        │  │
│  │  (per module)   │  │  (Pydantic DTOs)│  │ (Auth/CORS/Logging)     │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
┌─────────────────────────────────────────────────────────────────────────┐
│                    Service Layer (11 Business Modules)                   │
│  ┌─────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌─────────────────┐ │
│  │   CRM   │ │ Academics│ │  Finance │ │    HR    │ │  Notifications  │ │
│  ├─────────┤ ├──────────┤ ├──────────┤ ├──────────┤ ├─────────────────┤ │
│  │Students │ │ Courses  │ │ Receipts │ │Employees │ │  WhatsApp/SMS   │ │
│  │ Parents │ │  Groups  │ │ Payments │ │  Users   │ │     Email       │ │
│  │ History │ │ Sessions │ │Reporting │ │Attendance│ │   Templates     │ │
│  └─────────┘ └──────────┘ └──────────┘ └──────────┘ └─────────────────┘ │
│  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌──────────────────────────┐  │
│  │Enrollments│ │ Attendance│ │Competition│ │      Analytics         │  │
│  └───────────┘ └───────────┘ └───────────┘ └──────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
┌─────────────────────────────────────────────────────────────────────────┐
│                         Data Layer (SQLModel)                            │
│  ┌────────────────┐  ┌──────────────────┐  ┌────────────────────────┐ │
│  │  Repositories  │  │   PostgreSQL 15+ │  │    Supabase Auth     │ │
│  │  (Pure SQL)    │  │  (16 tables,     │  │   (JWT validation)   │ │
│  │                │  │   20+ views)     │  │                      │ │
│  └────────────────┘  └──────────────────┘  └────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Framework** | FastAPI | REST API with auto-generated OpenAPI docs |
| **ORM** | SQLModel | Type-safe SQLAlchemy + Pydantic hybrid |
| **Database** | PostgreSQL 15+ | Relational data with complex views |
| **Auth** | Supabase | JWT-based authentication & user management |
| **Validation** | Pydantic v2 | Request/response DTOs |
| **Testing** | pytest | unit, characterization and architecture suites |
| **Hosting** | FastAPI Cloud | Deploys via root `main.py` |

---

## Project Structure

```
project_root/
├── app/
│   ├── api/                      # Shared HTTP code only
│   │   ├── main.py               # create_app(): routers, handlers, Notifier wiring
│   │   ├── deps.py               # get_uow / UoW, get_current_user, role guards
│   │   ├── exceptions.py         # Global exception handlers
│   │   ├── schemas/common.py     # Response envelope (ApiResponse, ErrorResponse)
│   │   └── middleware/           # Request/response logging
│   ├── modules/                  # 11 business modules, bottom to top:
│   │   │                         #   auth, hr, crm, academics, enrollments, attendance,
│   │   │                         #   competitions, finance, tasks, notifications, analytics
│   │   └── <module>/
│   │       ├── __init__.py       # Facade: the only thing other modules may import
│   │       ├── api/              # Router, HTTP schemas, deps
│   │       ├── services/         # Business rules
│   │       ├── repositories/     # SQLModel queries
│   │       ├── schemas/          # DTOs
│   │       └── models/           # ORM models
│   ├── db/
│   │   ├── connection.py         # Engine & session factory
│   │   └── uow.py                # UnitOfWork, unit_of_work()
│   ├── core/                     # Settings, Supabase clients
│   ├── shared/                   # Cross-module utilities and exceptions
│   └── observability/            # Logfire setup and business metrics
├── db/
│   ├── schema.sql                # Base DDL (modular files in db/schema/)
│   └── migrations/               # Plain SQL, applied by hand in chronological order
├── tests/                        # Unit, characterization and architecture tests
├── docs/adr/                     # Architecture decision records (the target shape)
├── specs/                        # Feature specs (Speckit)
├── dashboard/ + audit_dashboard.py  # Internal Streamlit audit dashboard (not part of the API)
├── pyproject.toml
├── main.py                       # FastAPI Cloud entrypoint
└── run_api.py                    # Dev server with hot reload
```

The module rules (module order, facades, one unit of work per use case) are in
[`AGENTS.md`](AGENTS.md) and [`docs/adr/`](docs/adr/).

---

## API Endpoints (210)

The authoritative list is the OpenAPI document (see **API Documentation** below);
`tests/snapshots/openapi.json` pins it. Endpoints per tag:

| Tag | Endpoints |
|-----|-----------|
| Academics — Courses | 6 |
| Academics — Group Details | 5 |
| Academics — Group Directory | 3 |
| Academics — Group Lifecycle | 7 |
| Academics — Groups | 8 |
| Academics — Sessions | 7 |
| Admin Auth | 8 |
| Analytics — Academic | 4 |
| Analytics — BI | 8 |
| Analytics — Competition | 1 |
| Analytics — Dashboard | 1 |
| Analytics — Financial | 6 |
| Attendance | 2 |
| Authentication | 15 |
| CRM — Parents | 5 |
| CRM — Students | 21 |
| Competitions | 8 |
| Enrollments | 7 |
| Finance | 8 |
| Finance — Reporting | 2 |
| HR | 9 |
| Health | 2 |
| Notifications | 28 |
| Receipts | 5 |
| Student History | 10 |
| Tasks | 11 |
| Teams | 13 |

---

## Design Patterns

### 1. Repository Pattern
Pure data access without business logic:
```python
# app/modules/crm/repositories/student_repository.py
def get_student_by_id(session: Session, student_id: int) -> Student | None:
    return session.get(Student, student_id)

def list_students(session: Session, filters: StudentFilter) -> list[Student]:
    query = select(Student).where(Student.is_active == True)
    if filters.name:
        query = query.where(Student.full_name.ilike(f"%{filters.name}%"))
    return session.exec(query).all()
```

### 2. Service Layer with Dependency Injection
Business logic encapsulated, dependencies injected:
```python
# app/modules/crm/services/student_service.py
class StudentService:
    def __init__(self, repo: StudentRepository, auth_svc: AuthService):
        self._repo = repo
        self._auth = auth_svc
    
    def enroll_student(self, dto: EnrollStudentDTO) -> Enrollment:
        # Business logic here
        pass

# Factory for DI
@lru_cache
def get_student_service():
    return StudentService(
        repo=StudentRepository(),
        auth_svc=get_auth_service()
    )
```

### 3. DTO Pattern with Pydantic
All API I/O typed with Pydantic:
```python
# app/modules/crm/schemas/ (DTOs) and app/modules/crm/api/schemas/ (HTTP)
class StudentPublic(BaseModel):
    id: int
    full_name: str
    date_of_birth: date | None
    gender: Literal["male", "female"] | None
    phone: str | None
    is_active: bool
    created_at: datetime

class StudentCreateInput(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100)
    date_of_birth: date | None = None
    gender: Literal["male", "female"] | None = None
    phone: str | None = Field(None, pattern=r"^\d{10,15}$")
    parent_ids: list[int] = []
```

### 4. Standardized Response Envelope
Every response wrapped consistently:
```python
# app/api/schemas/common.py
class ApiResponse(BaseModel, Generic[T]):
    success: bool = True
    data: T | None = None
    message: str | None = None

class ErrorResponse(BaseModel):
    success: bool = False
    error: str          # "NotFoundError", "ValidationError", etc.
    message: str        # Human-readable detail
```

### 5. Exception Mapping
Domain exceptions map to HTTP responses:
```python
# app/api/exceptions.py
@app.exception_handler(NotFoundError)
async def not_found_handler(request: Request, exc: NotFoundError):
    return JSONResponse(
        status_code=404,
        content={"success": False, "error": "NotFoundError", "message": str(exc)}
    )
```

---

## Database Schema

### Base Tables (16)
| Table | Purpose |
|-------|---------|
| `parents` | Parent/guardian contact info |
| `students` | Student profiles |
| `student_parents` | Many-to-many junction |
| `employees` | Staff records |
| `users` | Login accounts (Supabase-linked) |
| `courses` | Course catalog |
| `groups` | Course groups/sections |
| `sessions` | Individual class sessions |
| `enrollments` | Student-group enrollments |
| `attendance` | Session attendance records |
| `receipts` | Payment receipts |
| `payments` | Individual payment transactions |
| `competitions` | Competition events |
| `competition_categories` | Competition divisions |
| `teams` | Competition teams |
| `team_members` | Team roster |

### Key Views
| View | Purpose |
|------|---------|
| `v_students` | Student + primary parent info |
| `v_enrollment_balance` | Real-time balance calculation |
| `v_unpaid_enrollments` | Outstanding debt tracking |
| `v_student_payment_history` | Complete payment timeline |
| `v_daily_collections` | Daily revenue aggregation |
| `v_group_session_count` | Session statistics per group |

---

## Setup & Development

### 1. Environment Setup
```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -e .
```

### 2. Configuration
Create `.env` from `.env.example`:
```env
DATABASE_URL=postgresql://user:pass@localhost:5432/techno_kids
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
```

### 3. Database Initialization
```bash
psql -U postgres -c "CREATE DATABASE techno_kids;"
psql -U postgres -d techno_kids -f db/schema.sql
```

### 4. Run API
```bash
# Development (hot reload)
python run_api.py

# Production
uvicorn app.api.main:app --host 0.0.0.0 --port 8000
```

### 5. Run Tests
```bash
pytest tests/ -v --tb=short
```

---

## API Documentation

- **Swagger UI**: `http://localhost:8000/api/v1/docs`
- **ReDoc**: `http://localhost:8000/api/v1/redoc`
- **OpenAPI JSON**: `http://localhost:8000/api/v1/openapi.json`

---

## Testing

See [`AGENTS.md`](AGENTS.md) for the test commands and the environment ladder.
The local gate is `pytest -m "not supabase"` against a throwaway Postgres
(`scripts/local_test_db.sh up`); `pytest tests/architecture` checks the module rules and the API snapshot.
