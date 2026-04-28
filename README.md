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
│  │   (21 files)    │  │  (Pydantic DTOs)│  │ (Auth/CORS/Logging)     │  │
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
| **Testing** | pytest | 26 test modules, 160+ tests |
| **Container** | Docker | Deployment with Gunicorn + Uvicorn |

---

## Project Structure

```
project_root/
├── app/
│   ├── api/
│   │   ├── routers/              # 21 router modules (209 endpoints)
│   │   │   ├── auth_router.py              # 6 endpoints
│   │   │   ├── crm/
│   │   │   │   ├── students_router.py      # 22 endpoints
│   │   │   │   ├── parents_router.py       # 5 endpoints
│   │   │   │   └── students_history_router.py # 8 endpoints
│   │   │   ├── academics/
│   │   │   │   ├── courses_router.py       # 7 endpoints
│   │   │   │   ├── groups_router.py        # 17 endpoints
│   │   │   │   ├── sessions_router.py      # 7 endpoints
│   │   │   │   ├── group_lifecycle_router.py # 12 endpoints
│   │   │   │   ├── group_competitions_router.py # 7 endpoints
│   │   │   │   └── group_details_router.py # 5 endpoints
│   │   │   ├── attendance_router.py        # 2 endpoints
│   │   │   ├── enrollments_router.py        # 6 endpoints
│   │   │   ├── finance/
│   │   │   │   ├── receipt_router.py       # 8 endpoints
│   │   │   │   ├── finance_router.py       # 8 endpoints
│   │   │   │   └── reporting_router.py     # 2 endpoints
│   │   │   ├── competitions/
│   │   │   │   ├── competitions_router.py  # 14 endpoints
│   │   │   │   └── teams_router.py         # 14 endpoints
│   │   │   ├── hr_router.py                # 7 endpoints
│   │   │   ├── analytics/
│   │   │   │   ├── academic.py             # 4 endpoints
│   │   │   │   ├── financial.py            # 6 endpoints
│   │   │   │   ├── competition.py          # 1 endpoint
│   │   │   │   ├── bi.py                   # 8 endpoints
│   │   │   │   └── dashboard.py            # 1 endpoint
│   │   │   └── notifications/
│   │   │       ├── notifications_router.py # 4 endpoints
│   │   │       ├── templates_router.py     # 6 endpoints
│   │   │       ├── admin_settings_router.py # 8 endpoints
│   │   │       └── bulk_router.py          # 4 endpoints
│   │   ├── schemas/              # Pydantic DTOs
│   │   │   ├── common.py         # ApiResponse, PaginatedResponse
│   │   │   ├── auth.py           # Login/Token schemas
│   │   │   ├── crm/              # Student/Parent DTOs
│   │   │   ├── academics/        # Course/Group/Session DTOs
│   │   │   ├── finance/          # Receipt/Payment DTOs
│   │   │   ├── hr/               # Employee DTOs
│   │   │   └── analytics/        # Report DTOs
│   │   ├── dependencies.py       # DI factories & auth guards
│   │   ├── exceptions.py           # Global exception handlers
│   │   └── middleware/
│   │       └── logging_middleware.py  # Request/response logging
│   ├── modules/                  # 11 business modules
│   │   ├── auth/                 # User auth, JWT validation
│   │   ├── crm/                  # Students, Parents, History
│   │   ├── academics/            # Courses, Groups, Sessions
│   │   ├── enrollments/          # Student enrollments
│   │   ├── attendance/           # Session attendance
│   │   ├── finance/              # Receipts, Payments, Allocations
│   │   ├── competitions/         # Competitions, Teams, Categories
│   │   ├── hr/                   # Employees, Staff accounts
│   │   ├── analytics/            # Reporting aggregations
│   │   ├── notifications/        # WhatsApp/SMS/Email service
│   │   └── shared/               # Utilities, exceptions, mappers
│   ├── db/
│   │   ├── connection.py         # Engine & session factory
│   │   └── init_db.py            # Schema initialization
│   └── core/
│       └── supabase_clients.py   # Supabase client configuration
├── db/
│   ├── schema.sql                # Base DDL (16 tables, 5 views)
│   └── migrations/               # 44 migration files
├── tests/                        # 26 test modules
├── docs/                         # API documentation
├── memory-bank/                  # Architecture decisions
├── Dockerfile
├── pyproject.toml
├── requirements.txt
└── run_api.py                    # Entry point
```

---

## API Endpoint Inventory (209 Endpoints)

### Authentication (`/api/v1/auth`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/login` | Supabase login with email/password |
| POST | `/refresh` | Refresh JWT token |
| POST | `/logout` | Invalidate session |
| GET | `/me` | Get current user |
| POST | `/users` | Create login user (admin only) |
| POST | `/users/{id}/reset-password` | Force password reset |

### CRM — Students (`/api/v1/students/*`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/students` | List all students |
| POST | `/students` | Create student |
| GET | `/students/{id}` | Get student by ID |
| PUT | `/students/{id}` | Update student |
| DELETE | `/students/{id}` | Soft delete student |
| GET | `/students/{id}/parents` | Get student parents |
| POST | `/students/{id}/parents` | Link parent to student |
| GET | `/students/{id}/enrollments` | Get student enrollments |
| GET | `/students/{id}/payments` | Get payment history |
| GET | `/students/{id}/attendance` | Get attendance summary |
| GET | `/students/filter` | Advanced filter & search |
| POST | `/students/bulk-delete` | Bulk soft delete |

### CRM — Parents (`/api/v1/parents/*`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/parents` | List parents |
| POST | `/parents` | Create parent |
| GET | `/parents/{id}` | Get parent with students |
| PUT | `/parents/{id}` | Update parent |
| DELETE | `/parents/{id}` | Delete parent |

### CRM — Student History (`/api/v1/students-history/*`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/students-history/{id}` | Full activity timeline |
| GET | `/students/{id}/history` | Enrollment history |
| GET | `/students/{id}/activity-log` | Audit trail |
| GET | `/students/{id}/financial-summary` | Financial overview |

### Academics — Courses (`/api/v1/courses/*`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/courses` | List courses |
| POST | `/courses` | Create course |
| GET | `/courses/{id}` | Get course details |
| PUT | `/courses/{id}` | Update course |
| DELETE | `/courses/{id}` | Delete course |
| GET | `/courses/{id}/groups` | Get course groups |
| GET | `/courses/{id}/stats` | Course statistics |

### Academics — Groups (`/api/v1/groups/*`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/groups` | List groups |
| POST | `/groups` | Create group |
| GET | `/groups/{id}` | Get group details |
| PUT | `/groups/{id}` | Update group |
| DELETE | `/groups/{id}` | Archive group |
| GET | `/groups/{id}/students` | Get enrolled students |
| GET | `/groups/{id}/sessions` | Get group sessions |
| POST | `/groups/{id}/students` | Enroll student |
| GET | `/groups/active` | List active groups |
| POST | `/groups/{id}/complete-level` | Level progression |
| GET | `/groups/{id}/attendance` | Attendance report |

### Academics — Sessions (`/api/v1/sessions/*`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/sessions` | List sessions |
| POST | `/sessions` | Create session |
| GET | `/sessions/{id}` | Get session |
| PUT | `/sessions/{id}` | Update session |
| DELETE | `/sessions/{id}` | Cancel session |
| GET | `/sessions/daily-schedule` | Day schedule view |
| POST | `/sessions/{id}/mark-attendance` | Bulk attendance |

### Academics — Group Lifecycle (`/api/v1/group-lifecycle/*`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/groups/{id}/archive` | Archive group |
| POST | `/groups/{id}/reactivate` | Reactivate group |
| POST | `/groups/{id}/cancel-session` | Cancel with renumbering |
| GET | `/groups/{id}/timeline` | Lifecycle history |

### Finance — Receipts (`/api/v1/receipts/*`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/receipts` | List receipts |
| POST | `/receipts` | Create receipt |
| GET | `/receipts/{id}` | Get receipt |
| PUT | `/receipts/{id}` | Update receipt |
| DELETE | `/receipts/{id}` | Void receipt |
| GET | `/receipts/{id}/pdf` | Download PDF |
| POST | `/receipts/{id}/send` | Email receipt |
| GET | `/receipts/daily` | Daily collections |

### Finance — Payments (`/api/v1/finance/*`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/payments` | List payments |
| POST | `/payments` | Record payment |
| GET | `/payments/{id}` | Get payment |
| POST | `/payments/{id}/refund` | Process refund |
| GET | `/payments/{id}/allocations` | View allocations |
| GET | `/finance/balances` | Student balances |
| POST | `/finance/calculate-balance` | Recalculate balance |
| GET | `/finance/unpaid-enrollments` | Outstanding debts |

### Finance — Reporting (`/api/v1/finance-reporting/*`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/finance-reporting/summary` | Financial summary |
| GET | `/finance-reporting/collections` | Collection report |

### Competitions (`/api/v1/competitions/*`, `/api/v1/teams/*`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/competitions` | List competitions |
| POST | `/competitions` | Create competition |
| GET | `/competitions/{id}` | Get details |
| PUT | `/competitions/{id}` | Update |
| DELETE | `/competitions/{id}` | Delete |
| GET | `/competitions/{id}/categories` | List categories |
| POST | `/competitions/{id}/register` | Register student |
| GET | `/competitions/{id}/teams` | List teams |
| POST | `/teams` | Create team |
| GET | `/teams/{id}` | Get team |
| PUT | `/teams/{id}` | Update team |
| DELETE | `/teams/{id}` | Delete team |
| POST | `/teams/{id}/members` | Add member |
| DELETE | `/teams/{id}/members/{student_id}` | Remove member |

### HR (`/api/v1/hr/*`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/hr/employees` | List employees |
| POST | `/hr/employees` | Create employee |
| GET | `/hr/employees/{id}` | Get employee |
| PUT | `/hr/employees/{id}` | Update employee |
| GET | `/hr/staff-accounts` | List staff accounts |
| POST | `/hr/attendance/log` | Log attendance |
| POST | `/hr/employees/{id}/create-account` | Create login |

### Notifications (`/api/v1/notifications/*`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/notifications/absence` | Send absence alert |
| POST | `/notifications/receipt/{id}` | Send receipt notification |
| GET | `/notifications/logs` | Notification logs |
| GET | `/notifications/logs/parent/{id}` | Parent logs |
| GET | `/notification-templates` | List templates |
| POST | `/notification-templates` | Create template |
| PUT | `/notification-templates/{id}` | Update template |
| GET | `/notification-settings` | Admin settings |
| PUT | `/notification-settings` | Update settings |
| POST | `/notifications/bulk` | Bulk send |

### Analytics (`/api/v1/analytics/*`, `/api/v1/dashboard/*`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/analytics/academic/student-progress` | Progress report |
| GET | `/analytics/academic/group-performance` | Group metrics |
| GET | `/analytics/financial/revenue` | Revenue analytics |
| GET | `/analytics/financial/outstanding` | Outstanding balances |
| GET | `/analytics/bi/enrollment-trends` | Enrollment trends |
| GET | `/analytics/bi/attendance-patterns` | Attendance stats |
| GET | `/dashboard/summary` | Dashboard KPIs |
| GET | `/dashboard/activities` | Recent activities |

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
# app/api/schemas/crm/student.py
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
pip install -r requirements.txt
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

## Docker

```bash
docker build -t techno-terminal .
docker run -p 8000:8000 --env-file .env techno-terminal
```

---

## API Documentation

- **Swagger UI**: `http://localhost:8000/api/v1/docs`
- **ReDoc**: `http://localhost:8000/api/v1/redoc`
- **OpenAPI JSON**: `http://localhost:8000/api/v1/openapi.json`

---

## Testing

| Metric | Value |
|--------|-------|
| Test Modules | 26 |
| Total Tests | 160+ |
| Endpoint Coverage | 94% |
| Auth Tests | 6/6 |
| CRM Tests | 9/9 |
| Finance Tests | 8/8 |
| Academics Tests | 14/14 |

---

## Development Phases

| Phase | Status | Domain |
|-------|--------|--------|
| Phase 1 | ✅ Complete | Core Foundation (Auth, DB) |
| Phase 2 | ✅ Complete | CRM (Students, Parents) |
| Phase 3 | ✅ Complete | Operations (Enrollments, Attendance) |
| Phase 4 | ✅ Complete | Finance (Receipts, Payments) |
| Phase 5 | ✅ Complete | Competitions & Teams |
| Phase 6 | ✅ Complete | Analytics & Reporting |
| Phase 7 | ✅ Complete | Notifications (WhatsApp, SMS, Email) |
